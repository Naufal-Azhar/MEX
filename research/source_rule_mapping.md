# Source–Rule Mapping — Telemetry Learning Rules (Draft)

**Status:** planning document. Rules listed here are **draft**, not `reviewed` and not `active`. No rule may be activated without documented human review.
**Related:** `research/telemetry_feature_spec.md`, `knowledge_base/source_documents/telemetry/`, `datasets/telemetry/manifest.json`.

| Rule | Antecedents (features/facts) | Conclusion | Source / evidence | Limitation |
|---|---|---|---|---|
| `TEL-R01` | `laps_aligned`, `valid_speed_A`, `valid_speed_B`, coverage >= 0.8 | `speed_comparison_available` | Data dictionary §2–3; feature spec §3.2 | Comparison availability is not a performance claim |
| `TEL-R02` | `speed_comparison_available`, `speed_delta_exceeds_tolerance` | `speed_profile_difference_observed` | Feature spec §3.2; engineering notes §1 | Tolerance is prototype configuration; alignment uncertainty applies |
| `TEL-R03` | `valid_brake_onsets`, `alignment_quality_sufficient`, `onset_delta_exceeds_uncertainty` | `relative_brake_onset_difference_observed` | Feature spec §3.3–3.4; data dictionary §4 | Brake indicator only; entering speed context required for interpretation |
| `TEL-R04` | `relative_brake_onset_difference_observed` | `braking_dynamics_learning_topic_relevant` | Engineering notes §2 | Topic relevance, not a diagnosis |
| `TEL-R05` | `goal_is_understeer_diagnosis`, steering/vehicle-response channel unavailable | `insufficient_evidence_for_understeer_diagnosis` | Feature spec §1 and §6; addendum §23 non-goals | Guardrail: missing data is not negative evidence |
| `TEL-R06` | `goal_is_drag_comparison`, aero/power context unavailable | `insufficient_evidence_for_drag_cause` | Engineering notes §5 | Drag cannot be inferred from speed alone |
| `TEL-R07` | tyre or track context unavailable | `flag_comparison_context_limitation` | Data dictionary §5; addendum §26.2 | Context limitation, not a verdict |
| `TEL-R08` | scientific evidence missing or unverified | `withhold_supported_engineering_interpretation` | `research/engineering_sources.md`; engineering notes §6 | Knowledge gate: absence of evidence must be reported |

## Mapping to the existing engine

- Rules TEL-R01..R04 can be evaluated with the existing `BackwardChainingEngine` using typed facts produced by the telemetry feature layer.
- Rules TEL-R05..R08 are sufficiency guardrails. They must be evaluated even when the main analytical goal fails.
- The existing three-valued semantics stay unchanged: `UNKNOWN` never becomes `FALSE`.
- Analytical statuses are separate from compliance statuses. `SATISFIED`/`VIOLATED` must not be used for performance conclusions.

## Open items before any rule review

1. Define the exact tolerance and uncertainty constants, and run sensitivity analysis.
2. Verify each rule against the feature implementation with independent unit tests.
3. Decide whether any external engineering source is strong enough to support `SUPPORTED_INTERPRETATION`; otherwise keep the status at `OBSERVED`.
4. Record a human reviewer before promoting any rule beyond `draft`.
