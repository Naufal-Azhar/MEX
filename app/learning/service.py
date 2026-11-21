"""Evidence-gated telemetry learning orchestration."""

from __future__ import annotations

from pathlib import Path

from app.config import ROOT
from app.expert_system.backward_chaining import BackwardChainingEngine
from app.expert_system.knowledge_base import KnowledgeBase
from app.learning.evidence_gate import evaluate_data_gate, evaluate_knowledge_gate
from app.schemas.analysis import AnalysisFinding, AnalysisStatus, TelemetryAnalysisReport
from app.schemas.facts import Fact, FactOrigin, FactStore
from app.schemas.results import TruthValue
from app.schemas.telemetry import LapPairAnalysis
from app.telemetry.service import TelemetryAnalysisService

TELEMETRY_RULES_PATH = ROOT / "knowledge_base" / "rules" / "telemetry_rules.json"
TELEMETRY_MANIFEST_PATH = ROOT / "datasets" / "telemetry" / "manifest.json"
KNOWLEDGE_CORPUS = [
    ROOT / "knowledge_base" / "source_documents" / "telemetry" / "data_dictionary.md",
    ROOT / "knowledge_base" / "source_documents" / "telemetry" / "engineering_fundamentals.md",
    ROOT / "research" / "engineering_sources.md",
]

OBSERVATIONAL_GOALS = {
    "speed_comparison_available",
    "speed_profile_difference_observed",
    "relative_brake_onset_difference_observed",
    "braking_dynamics_learning_topic_relevant",
}

GOAL_FACTS = {
    "speed_comparison_available": ["laps_aligned", "valid_speed_a", "valid_speed_b", "coverage_sufficient"],
    "speed_profile_difference_observed": ["speed_delta_exceeds_tolerance"],
    "relative_brake_onset_difference_observed": [
        "valid_brake_onsets",
        "alignment_quality_sufficient",
        "onset_delta_exceeds_uncertainty",
    ],
    "braking_dynamics_learning_topic_relevant": ["relative_brake_onset_difference_observed"],
    "insufficient_evidence_for_understeer_diagnosis": [
        "goal_is_understeer_diagnosis",
        "steering_or_vehicle_response_unavailable",
    ],
    "insufficient_evidence_for_drag_cause": [
        "goal_is_drag_comparison",
        "required_aero_power_context_unavailable",
    ],
    "flag_comparison_context_limitation": ["tyre_context_or_track_context_unavailable"],
    "withhold_supported_engineering_interpretation": ["scientific_evidence_missing_or_unverified"],
}

SPEED_DELTA_TOLERANCE_KM_H = 0.5


def _contains_any(text: str, words: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(word in lowered for word in words)


def build_facts(pair: LapPairAnalysis, question: str | None = None) -> dict[str, bool]:
    coverage = pair.speed_delta.coverage_ratio if pair.speed_delta is not None else 0.0
    delta_extremes = (
        max(abs(pair.speed_delta.min_km_h), abs(pair.speed_delta.max_km_h))
        if pair.speed_delta is not None
        else 0.0
    )
    missing_channels = any(quality.missing_channels for quality in pair.quality.values())
    question_text = question or ""
    return {
        "laps_aligned": pair.speed_delta is not None,
        "valid_speed_a": not missing_channels,
        "valid_speed_b": not missing_channels,
        "coverage_sufficient": coverage >= 0.8,
        "speed_delta_exceeds_tolerance": delta_extremes >= SPEED_DELTA_TOLERANCE_KM_H,
        "valid_brake_onsets": bool(pair.brake_onsets_a) and bool(pair.brake_onsets_b),
        "alignment_quality_sufficient": coverage >= 0.8,
        "onset_delta_exceeds_uncertainty": any(
            not comparison.within_alignment_uncertainty for comparison in pair.brake_onset_comparisons
        ),
        "goal_is_understeer_diagnosis": _contains_any(question_text, ("understeer", "oversteer")),
        "steering_or_vehicle_response_unavailable": True,
        "goal_is_drag_comparison": _contains_any(question_text, ("drag", "downforce", "aero")),
        "required_aero_power_context_unavailable": True,
        "tyre_context_or_track_context_unavailable": True,
        "scientific_evidence_missing_or_unverified": True,
    }


def _fact_store(facts: dict[str, bool]) -> FactStore:
    store = FactStore()
    for name, value in facts.items():
        store.add(Fact(name=name, value=value, origin=FactOrigin.DERIVED))
    return store


def _finding_status(goal: str, result) -> AnalysisStatus:
    if result.not_applicable:
        return AnalysisStatus.NOT_APPLICABLE
    if result.status is TruthValue.TRUE:
        if goal in OBSERVATIONAL_GOALS:
            return AnalysisStatus.OBSERVED
        return AnalysisStatus.INSUFFICIENT_DATA
    if result.status is TruthValue.FALSE:
        return AnalysisStatus.NOT_APPLICABLE
    return AnalysisStatus.INSUFFICIENT_DATA


class TelemetryLearningService:
    def __init__(
        self,
        telemetry: TelemetryAnalysisService,
        knowledge_base: KnowledgeBase,
        corpus_paths: list[Path | str] | None = None,
    ) -> None:
        self.telemetry = telemetry
        self.kb = knowledge_base
        self.corpus_paths = corpus_paths or KNOWLEDGE_CORPUS

    @classmethod
    def default(cls) -> "TelemetryLearningService":
        telemetry = TelemetryAnalysisService.from_manifest(TELEMETRY_MANIFEST_PATH)
        kb = KnowledgeBase.from_file(TELEMETRY_RULES_PATH, include_draft=True)
        return cls(telemetry, kb)

    @classmethod
    def for_session(cls, session_id: str) -> "TelemetryLearningService":
        telemetry = TelemetryAnalysisService.from_session(session_id)
        kb = KnowledgeBase.from_file(TELEMETRY_RULES_PATH, include_draft=True)
        return cls(telemetry, kb)

    def analyze(
        self,
        lap_a_id: str,
        lap_b_id: str,
        segment: tuple[float, float] | None = None,
        question: str | None = None,
        level: str = "beginner",
    ) -> TelemetryAnalysisReport:
        pair = self.telemetry.analyze(lap_a_id, lap_b_id, segment=segment)
        facts = build_facts(pair, question=question)
        engine = BackwardChainingEngine(self.kb, _fact_store(facts))

        findings: list[AnalysisFinding] = []
        traces = []
        fired_pairs = []
        for goal in self.kb.goals():
            result = engine.prove(goal)
            rules = self.kb.rules_for_goal(goal)
            rule = rules[0] if rules else None
            status = _finding_status(goal, result)
            findings.append(
                AnalysisFinding(
                    rule_id=rule.rule_id if rule else "UNKNOWN",
                    goal=goal,
                    description=rule.name if rule else goal,
                    status=status,
                    rule_status=rule.status.value if rule else "unknown",
                    fact_refs=GOAL_FACTS.get(goal, []),
                    source=rule.source if rule else None,
                    notes=list(result.notes),
                )
            )
            if result.trace is not None:
                traces.append(result.trace)
            if rule is not None and status is not AnalysisStatus.NOT_APPLICABLE:
                fired_pairs.append((rule, goal))

        data_gate = evaluate_data_gate(pair)
        knowledge_gate, evidence = evaluate_knowledge_gate(fired_pairs, self.corpus_paths)

        if not data_gate.passed:
            for finding in findings:
                if finding.status is AnalysisStatus.OBSERVED:
                    finding.status = AnalysisStatus.INSUFFICIENT_DATA
                    finding.notes.append("Withheld: data gate did not pass.")

        withheld = any(
            finding.goal == "withhold_supported_engineering_interpretation"
            and finding.status is AnalysisStatus.INSUFFICIENT_DATA
            for finding in findings
        )
        interpretation_status = (
            AnalysisStatus.INSUFFICIENT_DATA
            if withheld
            else AnalysisStatus.SUPPORTED_INTERPRETATION
        )

        missing_data = list(data_gate.missing) + list(knowledge_gate.missing)
        for finding in findings:
            if finding.status is AnalysisStatus.INSUFFICIENT_DATA and finding.goal in OBSERVATIONAL_GOALS:
                missing_data.append(f"{finding.goal}: facts insufficient")
        for finding in findings:
            if finding.status is AnalysisStatus.INSUFFICIENT_DATA and finding.goal not in OBSERVATIONAL_GOALS:
                missing_data.append(f"{finding.goal}: {finding.description}")

        limitations = list(pair.limitations)
        limitations.extend(
            [
                "Telemetry rules are draft-only; they are not reviewed or active.",
                "The knowledge gate verifies quote presence, not semantic entailment.",
                f"Explanation level requested: {level}; level changes wording, not facts or status.",
            ]
        )
        if not data_gate.passed:
            limitations.append("The data gate did not pass; conclusions are withheld.")
        if not knowledge_gate.passed:
            limitations.append("The knowledge gate did not pass; untraceable findings are reported as insufficient.")

        return TelemetryAnalysisReport(
            analysis_id=pair.analysis_id,
            data_kind=pair.data_kind,
            lap_a=pair.lap_a,
            lap_b=pair.lap_b,
            provenance=pair.provenance,
            quality=pair.quality,
            observed_facts=pair.observed_facts,
            findings=findings,
            trace=traces,
            evidence=evidence,
            missing_data=missing_data,
            limitations=limitations,
            data_gate=data_gate,
            knowledge_gate=knowledge_gate,
            engineering_interpretation_status=interpretation_status,
        )
