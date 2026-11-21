"""Goal-driven (backward chaining) inference engine.

Algorithm (goal-driven, depth-first):
1. Find validated rules whose conclusion establishes the goal.
2. Check each rule's applicability conditions.
3. Resolve the rule's conditions; a condition may reference ``value(subgoal)``,
   which recursively triggers a new proof for that subgoal.
4. Combine rule outcomes: a proven violation (FALSE) dominates, then TRUE,
   otherwise UNKNOWN. UNKNOWN is never collapsed into FALSE.
"""

from __future__ import annotations

from typing import Any

from app.expert_system.knowledge_base import KnowledgeBase
from app.expert_system.rule_engine import RuleEngine, render_expr
from app.schemas.facts import FactStore, MissingFact
from app.schemas.results import GoalResult, RuleEvaluation, TraceNode, TruthValue
from app.schemas.rules import Rule


class BackwardChainingEngine:
    MAX_DEPTH = 25

    def __init__(self, knowledge_base: KnowledgeBase, facts: FactStore) -> None:
        self.kb = knowledge_base
        self.facts = facts
        self.rule_engine = RuleEngine(facts)
        self.rule_engine.subgoal_resolver = self.prove
        self._cache: dict[str, GoalResult] = {}
        self._stack: list[str] = []
        self._node_counter = 0

    # ------------------------------------------------------------------ public API
    def prove(self, goal: str) -> GoalResult:
        if goal in self._cache:
            return self._cache[goal]
        if goal in self._stack:
            return GoalResult(
                goal=goal,
                status=TruthValue.UNKNOWN,
                notes=[f"Cycle detected while proving '{goal}'."],
            )
        if len(self._stack) >= self.MAX_DEPTH:
            return GoalResult(
                goal=goal,
                status=TruthValue.UNKNOWN,
                notes=[f"Maximum inference depth ({self.MAX_DEPTH}) exceeded."],
            )

        rules = self.kb.rules_for_goal(goal)
        if not rules:
            return GoalResult(
                goal=goal,
                status=TruthValue.UNKNOWN,
                notes=[f"No validated rule can establish goal '{goal}'."],
            )

        self._stack.append(goal)
        try:
            evaluations = [self.rule_engine.evaluate_rule(rule) for rule in rules]
        finally:
            self._stack.pop()

        result = self._combine(goal, evaluations, rules)
        self._cache[goal] = result
        return result

    # ------------------------------------------------------------------ internals
    def _combine(self, goal: str, evaluations: list[RuleEvaluation], rules: list[Rule]) -> GoalResult:
        is_value_goal = any(rule.conclusion.kind == "value" for rule in rules)
        applicable = [e for e in evaluations if e.applicable and e.applicability == TruthValue.TRUE]
        unknown_applicability = [
            e for e in evaluations if not e.applicable and e.applicability == TruthValue.UNKNOWN
        ]
        not_applicable = [e for e in evaluations if not e.applicable and e.applicability == TruthValue.FALSE]

        notes: list[str] = []
        if is_value_goal:
            status, value, deciding, conflict = self._combine_value(applicable, notes)
        else:
            status, value, deciding, conflict = self._combine_boolean(applicable, notes)

        if not applicable and not is_value_goal:
            notes.append(
                "No rule applies to the provided context"
                + (f" ({len(not_applicable)} rule(s) evaluated as not applicable)." if not_applicable else ".")
            )
        if unknown_applicability:
            notes.append(
                "Applicability of "
                + ", ".join(e.rule_id for e in unknown_applicability)
                + " could not be determined."
            )
        if deciding is None and evaluations:
            deciding = evaluations[0]
        if status == TruthValue.UNKNOWN and deciding is not None:
            for note in deciding.notes:
                if note not in notes:
                    notes.append(note)
        if conflict:
            notes.append("Conflicting conclusions were produced by different rules; the conservative result is reported.")

        not_applicable = bool(
            status == TruthValue.UNKNOWN
            and evaluations
            and all(
                (not evaluation.applicable) and evaluation.applicability == TruthValue.FALSE
                for evaluation in evaluations
            )
        )
        if not_applicable:
            notes.append("All candidate rules are definitively not applicable to the provided context.")

        missing = self._collect_missing(evaluations, applicable)
        result = GoalResult(
            goal=goal,
            status=status,
            value=value,
            rule_id=deciding.rule_id if deciding else None,
            missing_facts=missing,
            notes=notes,
            evaluations=evaluations,
            not_applicable=not_applicable,
        )
        result.trace = self._build_trace(result, deciding, is_value_goal)
        return result

    def _combine_boolean(
        self, applicable: list[RuleEvaluation], notes: list[str]
    ) -> tuple[TruthValue, bool | None, RuleEvaluation | None, bool]:
        false_rules = [e for e in applicable if e.status == TruthValue.FALSE]
        true_rules = [e for e in applicable if e.status == TruthValue.TRUE]
        unknown_rules = [e for e in applicable if e.status == TruthValue.UNKNOWN]

        if false_rules:
            conflict = bool(true_rules)
            return TruthValue.FALSE, False, false_rules[0], conflict
        if true_rules:
            return TruthValue.TRUE, True, true_rules[0], False
        deciding = unknown_rules[0] if unknown_rules else (applicable[0] if applicable else None)
        return TruthValue.UNKNOWN, None, deciding, False

    def _combine_value(
        self, applicable: list[RuleEvaluation], notes: list[str]
    ) -> tuple[TruthValue, Any, RuleEvaluation | None, bool]:
        produced = [
            e for e in applicable if e.status == TruthValue.TRUE and e.conclusion_value is not None
        ]
        if produced:
            first = produced[0]
            if all(self._values_equal(e.conclusion_value, first.conclusion_value) for e in produced[1:]):
                return TruthValue.TRUE, first.conclusion_value, first, False
            notes.append(
                "Multiple applicable value rules produced different values: "
                + ", ".join(f"{e.rule_id}={e.conclusion_value!r}" for e in produced)
                + "."
            )
            return TruthValue.UNKNOWN, None, first, True
        deciding = next((e for e in applicable if e.status == TruthValue.UNKNOWN), None)
        return TruthValue.UNKNOWN, None, deciding, False

    @staticmethod
    def _values_equal(a: Any, b: Any) -> bool:
        try:
            return abs(float(a) - float(b)) < 1e-9
        except (TypeError, ValueError):
            return a == b

    def _collect_missing(
        self, evaluations: list[RuleEvaluation], applicable: list[RuleEvaluation]
    ) -> list[MissingFact]:
        source = applicable if applicable else evaluations
        seen: set[tuple[str, str | None]] = set()
        missing: list[MissingFact] = []
        for evaluation in source:
            for item in evaluation.missing_facts:
                key = (item.fact, item.rule_id)
                if key not in seen:
                    seen.add(key)
                    missing.append(item)
        return missing

    def _build_trace(
        self, result: GoalResult, deciding: RuleEvaluation | None, is_value_goal: bool
    ) -> TraceNode:
        self._node_counter += 1
        children: list[TraceNode] = []
        seen_goals: set[str] = set()
        if deciding:
            for subgoal in deciding.subgoal_results:
                if subgoal.goal in seen_goals:
                    continue
                seen_goals.add(subgoal.goal)
                if subgoal.trace is not None:
                    children.append(subgoal.trace)

        expression = None
        if deciding and is_value_goal:
            rule = self.kb.get_rule(deciding.rule_id)
            if rule and rule.conclusion.expr is not None:
                expression = render_expr(rule.conclusion.expr)

        return TraceNode(
            node_id=f"{result.goal}#{self._node_counter}",
            goal=result.goal,
            kind="value_goal" if is_value_goal else "compliance_goal",
            status=result.status,
            value=result.value,
            rule_id=deciding.rule_id if deciding else None,
            rule_name=deciding.rule_name if deciding else None,
            expression=expression,
            source=deciding.source if deciding else None,
            conditions=(deciding.conditions or deciding.applicability_conditions) if deciding else [],
            children=children,
            notes=result.notes,
        )


def check_goal(
    knowledge_base: KnowledgeBase, facts: FactStore, goal: str
) -> GoalResult:
    engine = BackwardChainingEngine(knowledge_base, facts)
    return engine.prove(goal)
