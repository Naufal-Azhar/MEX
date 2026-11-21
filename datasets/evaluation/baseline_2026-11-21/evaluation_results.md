# Evaluation Results

Generated: 2026-11-21T04:40:57.049928+00:00

Mode: `RAG + LLM extraction disabled + Backward Chaining`. LLM-only (A) and RAG+LLM (B) configurations have not been run yet; see `research/evaluation_plan.md`.
Rule validation status: `reviewed_demo_only`. Reviewed rules are demo-only until a human reviewer signs them off.

## Decision suite (backward chaining)

- Cases: 18
- Decision accuracy: 1.0
- Violation (FALSE) precision: 1.0
- Violation (FALSE) recall: 1.0
- Violation (FALSE) F1: 1.0
- Rule match accuracy: 1.0
- Article match accuracy: 1.0
- Citation accuracy: 1.0
- Citation verification rate: 1.0
- Missing-fact precision: 1.0
- Missing-fact recall: 1.0
- Explanation completeness: 1.0
- Backward-chaining trace consistency: 1.0
- Decision latency mean / p95 (ms): 5.98 / 97.13
- Failure rate: 0.0

### Split summary

| Split | Cases | Accuracy | F1 (VIOLATED) | Article match | Citation verified | Trace |
| --- | --- | --- | --- | --- | --- | --- |
| development | 12 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| heldout | 6 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

### Per-case results

| Case | Split | Goal | Expected | Actual | External | Expected rule | Actual rule | Article | Trace |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TC01 | development | wheelbase_compliance | TRUE | TRUE | SATISFIED | FIA26-C2.3.3-WHEELBASE | FIA26-C2.3.3-WHEELBASE | C2.3.3 | ok |
| TC02 | development | cockpit_position_compliance | TRUE | TRUE | SATISFIED | FIA26-C2.3.5-COCKPIT-POSITION | FIA26-C2.3.5-COCKPIT-POSITION | C2.3.5 | ok |
| TC04 | development | minimum_mass_compliance | TRUE | TRUE | SATISFIED | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC05 | development | mass_distribution_compliance | TRUE | TRUE | SATISFIED | FIA26-C4.2-MASS-DISTRIBUTION | FIA26-C4.2-MASS-DISTRIBUTION | C4.2 | ok |
| TC06 | development | wheelbase_compliance | FALSE | FALSE | VIOLATED | FIA26-C2.3.3-WHEELBASE | FIA26-C2.3.3-WHEELBASE | C2.3.3 | ok |
| TC08 | development | half_width_compliance | FALSE | FALSE | VIOLATED | FIA26-C2.3.1-HALF-WIDTH | FIA26-C2.3.1-HALF-WIDTH | C2.3.1 | ok |
| TC09 | development | minimum_mass_compliance | FALSE | FALSE | VIOLATED | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC10 | development | mass_distribution_compliance | FALSE | FALSE | VIOLATED | FIA26-C4.2-MASS-DISTRIBUTION | FIA26-C4.2-MASS-DISTRIBUTION | C4.2 | ok |
| TC11 | development | wheelbase_compliance | UNKNOWN | UNKNOWN | INSUFFICIENT_DATA | FIA26-C2.3.3-WHEELBASE | FIA26-C2.3.3-WHEELBASE | C2.3.3 | ok |
| TC13 | development | minimum_mass_compliance | UNKNOWN | UNKNOWN | INSUFFICIENT_DATA | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC15 | development | mass_distribution_compliance | UNKNOWN | UNKNOWN | NOT_APPLICABLE | FIA26-C4.2-MASS-DISTRIBUTION | FIA26-C4.2-MASS-DISTRIBUTION | C4.2 | ok |
| TC16 | development | minimum_mass_compliance | FALSE | FALSE | VIOLATED | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC03 | heldout | half_width_compliance | TRUE | TRUE | SATISFIED | FIA26-C2.3.1-HALF-WIDTH | FIA26-C2.3.1-HALF-WIDTH | C2.3.1 | ok |
| TC07 | heldout | cockpit_position_compliance | FALSE | FALSE | VIOLATED | FIA26-C2.3.5-COCKPIT-POSITION | FIA26-C2.3.5-COCKPIT-POSITION | C2.3.5 | ok |
| TC12 | heldout | cockpit_position_compliance | UNKNOWN | UNKNOWN | INSUFFICIENT_DATA | FIA26-C2.3.5-COCKPIT-POSITION | FIA26-C2.3.5-COCKPIT-POSITION | C2.3.5 | ok |
| TC14 | heldout | minimum_mass_compliance | UNKNOWN | UNKNOWN | INSUFFICIENT_DATA | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC17 | heldout | minimum_mass_compliance | TRUE | TRUE | SATISFIED | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |
| TC18 | heldout | minimum_mass_compliance | FALSE | FALSE | VIOLATED | FIA26-C4.1-MINIMUM-MASS | FIA26-C4.1-MINIMUM-MASS | C4.1 | ok |

### Confusion matrix

| Transition | Count |
| --- | --- |
| FALSE->FALSE | 7 |
| TRUE->TRUE | 6 |
| UNKNOWN->UNKNOWN | 5 |

## Retrieval suite

- Cases: 10
- k: 5
- Hit rate: 0.9
- Precision@k: 0.18
- Recall@k: 0.9
- MRR: 0.9
- Latency mean / p95 (ms): 102.06 / 328.44
- Index: {"backend": "sentence_transformers", "dimension": 384, "notes": []}

| Case | Query | Expected | Top retrieved | Hit | RR |
| --- | --- | --- | --- | --- | --- |
| RT01 | maximum wheelbase 3400 mm distance between planes XF and XR | C2.3.3 | C2.3.3 (p11), C2.3.4 (p11), C2.3.5 (p11), C3.18.10 (p56), C12.6.1 (p126) | 1.0 | 1.0 |
| RT02 | minimum mass 726 kg qualifying 724 kg other sessions nominal tyre mass | C4.1 | C4.1 (p59), C4.7 (p60), C4.2 (p59), C1 (p193), C4.5.2 (p60) | 1.0 | 1.0 |
| RT03 | front axle mass 0.44 rear axle mass 0.54 mass distribution | C4.2 | C10.1 (p106), C9.5.2 (p103), C10.2.2 (p106), C13.7.2 (p144), C5.5.6 (p71) | 0.0 | 0.0 |
| RT04 | 950 mm from plane Y=0 tyres wheel rims half width | C2.3.1 | C2.3.1 (p10), C10.6.1 (p112), C2.3.4 (p11), C13.10 (p146), C2.1.2 (p9) | 1.0 | 1.0 |
| RT05 | cockpit position XA XC 1830 mm 2030 mm | C2.3.5 | C2.3.5 (p11), C12.5 (p124), C12.6 (p125), C2.3.6 (p11), C2.3.4 (p11) | 1.0 | 1.0 |
| RT06 | heat hazard mass increase 5 kg TTCS | C4.6 | C4.6 (p60), C4.1 (p59), C5.5.2 (p70), C4.2 (p59), C9.5.2 (p103) | 1.0 | 1.0 |
| RT07 | nominal tyre mass measurement 50 tyres per axle dry weather tyres | C4.7 | C4.7 (p60), C4.2 (p59), C1 (p193), C4.1 (p59), C10.8.2 (p114) | 1.0 | 1.0 |
| RT08 | driver ballast density greater than 7500 kg/m3 | C4.3.2 | C4.3.2 (p59), C4.5.2 (p60), C4.5 (p60), C4.3 (p59), C5.5.8 (p71) | 1.0 | 1.0 |
| RT09 | rear bulkhead position distance XC XPU 360 mm | C2.3.6 | C2.3.6 (p11), C13.6.3 (p143), C3.18.2 (p53), C12.6.1 (p126), C3.18.13 (p57) | 1.0 | 1.0 |
| RT10 | front wheel position plane XF between XA 0 and 150 | C2.3.4 | C2.3.4 (p11), C2.3.3 (p11), C2.3.5 (p11), C2.1.3 (p9), C10.10.1 (p115) | 1.0 | 1.0 |

## Limitations

- The decision suite covers 5 modelled provisions only (C2.3.1, C2.3.3, C2.3.5, C4.1, C4.2).
- All rules are `reviewed`, not `active`; results are demo-only until human sign-off.
- The dataset is split into development (12) and held-out (6) cases; labels are synthetic and self-authored.
- Test inputs are fictional and derived from the regulation limits; they are not real team data.
- Latency includes lazy loading of processed source pages on the first case; it is not a production benchmark.
- Journal/methodology chunks are excluded from compliance search by default, but share the lexical index vocabulary.
- LLM-based fact extraction was not exercised because the LLM stage is intentionally deferred.
- No claim is made that Backward Chaining improves accuracy over an LLM-only baseline until that experiment is run.
