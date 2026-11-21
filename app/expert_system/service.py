"""Orchestration: validate input, run inference, and assemble a traceable report."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.config import PROCESSED_DIR
from app.expert_system.backward_chaining import BackwardChainingEngine
from app.expert_system.explanation import build_explanation
from app.expert_system.knowledge_base import DEFAULT_RULES_PATH, KnowledgeBase
from app.schemas.fact_specs import FACT_SPECS, FactBatchValidationError, FactValidationError, validate_and_normalize
from app.schemas.facts import (
    Fact,
    FactConflict,
    FactConflictError,
    FactInput,
    FactStore,
    MissingFact,
)
from app.schemas.results import (
    CheckReport,
    Citation,
    ConditionEvaluation,
    Diagnostic,
    DiagnosticCode,
    ExternalStatus,
    RuleEvaluation,
    TruthValue,
)
from app.schemas.rules import Condition, Operand, RuleSource, RuleStatus

LIMITATIONS = [
    "Sistem hanya memeriksa ketentuan yang telah dimodelkan (C2.3.1, C2.3.3, C2.3.5, C4.1, C4.2).",
    "Sistem tidak memverifikasi prosedur pengukuran, kondisi Legality Setup, atau kondisi fisik mobil.",
    "Nilai Nominal Tyre Mass tidak ditetapkan dalam regulasi; nilainya harus diberikan sebagai fakta.",
    "Hasil bukan pengganti pemeriksaan FIA technical delegate dan tidak mencakup seluruh Section C.",
]

DEMO_WARNING = (
    "Aturan yang dipakai berstatus 'reviewed' dan belum disetujui manusia. "
    "Hasil ini bersifat demo dan tidak boleh dianggap sebagai validasi FIA."
)


def normalize_text(text: str) -> str:
    """Normalize punctuation/whitespace for source-quote verification."""
    text = (
        text.replace("\u2212", "-")
        .replace("\u2013", "-")
        .replace("\u2014", "-")
        .replace("\u2019", "'")
        .replace("\u201c", '"')
        .replace("\u201d", '"')
    )
    return re.sub(r"\s+", " ", text).strip().lower()


def _operand_facts(operand: Operand | None) -> set[str]:
    if operand is None:
        return set()
    if operand.fact:
        return {operand.fact}
    if operand.expr:
        found: set[str] = set()
        for arg in operand.expr.args:
            found |= _operand_facts(arg)
        return found
    return set()


def _operand_goals(operand: Operand | None) -> set[str]:
    if operand is None:
        return set()
    if operand.goal_value:
        return {operand.goal_value}
    if operand.expr:
        found: set[str] = set()
        for arg in operand.expr.args:
            found |= _operand_goals(arg)
        return found
    return set()


def _operand_has_fact(operand: Operand | None, fact_name: str) -> bool:
    if operand is None:
        return False
    if operand.fact == fact_name:
        return True
    if operand.expr:
        return any(_operand_has_fact(arg, fact_name) for arg in operand.expr.args)
    return False


def _condition_facts(condition: Condition) -> set[str]:
    return _operand_facts(condition.left) | _operand_facts(condition.right)


class ComplianceService:
    def __init__(
        self,
        knowledge_base: KnowledgeBase | None = None,
        rules_path: Path | str | None = None,
        processed_dir: Path | str = PROCESSED_DIR,
        verify_sources: bool = True,
    ) -> None:
        self.kb = knowledge_base or KnowledgeBase.from_file(rules_path or DEFAULT_RULES_PATH)
        self.processed_dir = Path(processed_dir)
        self.verify_sources = verify_sources
        self._page_cache: dict[str, dict[int, str]] = {}

    # ------------------------------------------------------------------ facts
    def build_fact_store(self, items: list[FactInput]) -> FactStore:
        errors: list[FactValidationError] = []
        normalized: list[tuple[FactInput, Any, str | None]] = []
        for item in items:
            try:
                value, unit = validate_and_normalize(item.name, item.value, item.unit)
            except FactValidationError as exc:
                errors.append(exc)
                continue
            normalized.append((item, value, unit))
        if errors:
            raise FactBatchValidationError(errors)

        conflicts: list[FactConflict] = []
        store = FactStore()
        for item, value, unit in normalized:
            try:
                store.add(
                    Fact(
                        name=item.name,
                        value=value,
                        unit=unit,
                        origin=item.origin,
                        note=item.note,
                    )
                )
            except FactConflictError as exc:
                conflicts.extend(exc.conflicts)
        if conflicts:
            raise FactConflictError(conflicts)
        return store

    # ------------------------------------------------------------------ requirements
    def goal_facts(self, goal: str, _seen: set[str] | None = None) -> set[str]:
        """All input facts needed to prove a goal, including transitive value goals."""
        seen = _seen if _seen is not None else set()
        if goal in seen:
            return set()
        seen.add(goal)
        names: set[str] = set()
        for rule in self.kb.rules_for_goal(goal):
            for condition in list(rule.applies_if) + list(rule.conditions):
                names |= _condition_facts(condition)
                for operand in (condition.left, condition.right):
                    for subgoal in _operand_goals(operand):
                        names |= self.goal_facts(subgoal, seen)
            if rule.conclusion.expr is not None:
                conclusion_operand = Operand(expr=rule.conclusion.expr)
                names |= _operand_facts(conclusion_operand)
                for subgoal in _operand_goals(conclusion_operand):
                    names |= self.goal_facts(subgoal, seen)
        return names

    def requirements(self, goal: str) -> list[dict[str, Any]]:
        names = sorted(self.goal_facts(goal))
        requirements = []
        for name in names:
            spec = FACT_SPECS.get(name, {})
            requirements.append(
                {
                    "name": name,
                    "unit": self._expected_unit(goal, name) or spec.get("unit"),
                    "kind": spec.get("kind", "number"),
                    "allowed": spec.get("allowed"),
                    "min_value": spec.get("min_value"),
                    "description": spec.get("description"),
                }
            )
        return requirements

    def _expected_unit(self, goal: str, fact_name: str) -> str | None:
        stack = [goal]
        seen: set[str] = set()
        while stack:
            current = stack.pop()
            if current in seen:
                continue
            seen.add(current)
            for rule in self.kb.rules_for_goal(current):
                for condition in list(rule.applies_if) + list(rule.conditions):
                    if _operand_has_fact(condition.left, fact_name) or _operand_has_fact(
                        condition.right, fact_name
                    ):
                        return condition.unit
                    stack.extend(_operand_goals(condition.left))
                    stack.extend(_operand_goals(condition.right))
                if rule.conclusion.expr is not None:
                    operand = Operand(expr=rule.conclusion.expr)
                    if _operand_has_fact(operand, fact_name):
                        return rule.conclusion.unit
                    stack.extend(_operand_goals(operand))
        return None

    # ------------------------------------------------------------------ checking
    def check(
        self,
        goal: str,
        facts: FactStore,
        document_issue: str | None = None,
    ) -> CheckReport:
        diagnostics: list[Diagnostic] = []
        if document_issue and document_issue.strip() != self.kb.regulation_issue:
            return self._unsupported_report(
                goal,
                Diagnostic(
                    code=DiagnosticCode.VERSION_MISMATCH,
                    message=(
                        f"Requested issue {document_issue!r} is not the active ruleset issue "
                        f"{self.kb.regulation_issue!r}."
                    ),
                    details={"requested_issue": document_issue, "active_issue": self.kb.regulation_issue},
                ),
            )
        if not self.kb.has_goal(goal):
            return self._unsupported_report(
                goal,
                Diagnostic(
                    code=DiagnosticCode.UNSUPPORTED_GOAL,
                    message=f"Goal {goal!r} is outside the validated rule set.",
                    details={"supported_goals": self.kb.goals()},
                ),
            )

        engine = BackwardChainingEngine(self.kb, facts)
        result = engine.prove(goal)

        deciding = next((e for e in result.evaluations if e.rule_id == result.rule_id), None)
        if deciding is None and result.evaluations:
            deciding = result.evaluations[0]

        citations = self._build_citations(result.evaluations) if self.verify_sources else []
        deciding_citation = None
        if self.verify_sources:
            deciding_citation = next(
                (
                    citation
                    for citation in citations
                    if deciding
                    and citation.document_id == deciding.source.document_id
                    and deciding.source.article == citation.article
                    and deciding.source.page == citation.page
                ),
                None,
            )

        status = self._external_status(result)
        for citation in citations:
            if citation.verified:
                continue
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCode.SOURCE_MISSING,
                    message="A cited regulation quote could not be verified on the recorded page.",
                    details={
                        "document_id": citation.document_id,
                        "article": citation.article,
                        "page": citation.page,
                    },
                )
            )
        if deciding is not None and deciding_citation is not None and not deciding_citation.verified:
            if status in (ExternalStatus.SATISFIED, ExternalStatus.VIOLATED):
                status = ExternalStatus.INSUFFICIENT_DATA

        if deciding is not None and deciding.rule_status is RuleStatus.REVIEWED:
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCode.RULE_NOT_APPROVED,
                    message="The deciding rule is reviewed but not human-approved; result is demo-only.",
                    details={"rule_id": deciding.rule_id, "rule_status": deciding.rule_status.value},
                    rule_id=deciding.rule_id,
                )
            )

        all_evaluations = list(self._flatten_evaluations(result.evaluations))
        reviewed_rule_ids = sorted(
            {
                evaluation.rule_id
                for evaluation in all_evaluations
                if evaluation.rule_status is RuleStatus.REVIEWED
            }
        )
        for rule_id in reviewed_rule_ids:
            if deciding is not None and rule_id == deciding.rule_id:
                continue
            diagnostics.append(
                Diagnostic(
                    code=DiagnosticCode.RULE_NOT_APPROVED,
                    message="A rule used by this proof is reviewed but not human-approved; result is demo-only.",
                    details={"rule_id": rule_id, "rule_status": RuleStatus.REVIEWED.value},
                    rule_id=rule_id,
                )
            )

        used_names = self.goal_facts(goal)
        facts_used = {
            name: data for name, data in facts.as_public_dict().items() if name in used_names
        }

        rule_status = deciding.rule_status if deciding else None
        validation_warning = DEMO_WARNING if reviewed_rule_ids else None
        limitations = list(LIMITATIONS)
        if validation_warning:
            limitations.insert(0, validation_warning)

        report = CheckReport(
            goal_id=goal,
            status=status,
            internal_status=result.status,
            value=result.value,
            scope=self.kb.scope,
            explanation="",
            rule_id=result.rule_id or (deciding.rule_id if deciding else None),
            rule_name=deciding.rule_name if deciding else None,
            rule_status=rule_status,
            validation_warning=validation_warning,
            source=(deciding.source if deciding else None),
            applicability_conditions=list(deciding.applicability_conditions) if deciding else [],
            conditions=list(deciding.conditions) if deciding else [],
            missing_facts=self._dedupe_missing(result.missing_facts),
            conflicts=[],
            diagnostics=diagnostics,
            rules_evaluated=all_evaluations,
            citations=citations,
            facts_used=facts_used,
            proof_trace=result.trace,
            regulation=self.kb.regulation_metadata(),
            limitations=limitations,
            rule_conflict=any("Conflicting" in note for note in result.notes),
        )
        report.explanation = build_explanation(report)
        return report

    def check_all(self, facts: FactStore) -> list[CheckReport]:
        return [self.check(goal, facts) for goal in self.kb.goals() if self._is_compliance_goal(goal)]

    def _is_compliance_goal(self, goal: str) -> bool:
        return any(rule.conclusion.kind == "boolean" for rule in self.kb.rules_for_goal(goal))

    # ------------------------------------------------------------------ helpers
    @staticmethod
    def _external_status(result) -> ExternalStatus:
        if result.status is TruthValue.TRUE:
            return ExternalStatus.SATISFIED
        if result.status is TruthValue.FALSE:
            return ExternalStatus.VIOLATED
        if result.not_applicable:
            return ExternalStatus.NOT_APPLICABLE
        return ExternalStatus.INSUFFICIENT_DATA

    def _unsupported_report(self, goal: str, diagnostic: Diagnostic) -> CheckReport:
        report = CheckReport(
            goal_id=goal,
            status=ExternalStatus.UNSUPPORTED,
            internal_status=None,
            scope=self.kb.scope,
            explanation="",
            diagnostics=[diagnostic],
            regulation=self.kb.regulation_metadata(),
            limitations=list(LIMITATIONS),
        )
        report.explanation = build_explanation(report)
        return report

    def _pages(self, document_id: str) -> dict[int, str]:
        if document_id in self._page_cache:
            return self._page_cache[document_id]
        path = self.processed_dir / f"{document_id}.json"
        pages: dict[int, str] = {}
        if path.exists():
            import json

            document = json.loads(path.read_text(encoding="utf-8"))
            for page in document.get("pages", []):
                pages[int(page["page"])] = normalize_text(page.get("text") or "")
        self._page_cache[document_id] = pages
        return pages

    def _build_citations(self, evaluations: list[RuleEvaluation]) -> list[Citation]:
        seen: set[tuple[str, str, int | None, str]] = set()
        citations: list[Citation] = []
        for evaluation in self._walk_evaluations(evaluations):
            source = evaluation.source
            if source is None:
                continue
            key = (source.document_id, source.article, source.page, source.quote)
            if key in seen:
                continue
            seen.add(key)
            citations.append(self._citation(source))
        return citations

    def _walk_evaluations(self, evaluations: list[RuleEvaluation]):
        for evaluation in evaluations:
            yield evaluation
            for subgoal in evaluation.subgoal_results:
                yield from self._walk_evaluations(subgoal.evaluations)

    def _flatten_evaluations(self, evaluations: list[RuleEvaluation]) -> list[RuleEvaluation]:
        unique: dict[tuple[str, str], RuleEvaluation] = {}
        for evaluation in self._walk_evaluations(evaluations):
            unique.setdefault((evaluation.rule_id, evaluation.goal), evaluation)
        return list(unique.values())

    def _citation(self, source: RuleSource) -> Citation:
        pages = self._pages(source.document_id)
        verified = False
        if source.page is not None and source.page in pages:
            verified = normalize_text(source.quote) in pages[source.page]
        return Citation(
            document_id=source.document_id,
            document=source.document,
            issue=source.issue,
            article=source.article,
            page=source.page,
            quote=source.quote,
            verified=verified,
            evidence_span=source.evidence_span,
        )

    @staticmethod
    def _dedupe_missing(items: list[MissingFact]) -> list[MissingFact]:
        seen: set[tuple[str, str | None]] = set()
        out: list[MissingFact] = []
        for item in items:
            key = (item.fact, item.rule_id)
            if key not in seen:
                seen.add(key)
                out.append(item)
        return out
