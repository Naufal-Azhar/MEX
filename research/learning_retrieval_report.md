# Learning Retrieval Evaluation

Generated: 2026-11-21T06:26:23.980361+00:00

Corpus: `knowledge_base/source_documents/telemetry/` (data dictionary + engineering notes).
Backend: TF-IDF with table-row chunks and intent-aware scoring.

## Aggregate

- Answerable cases: 9
- Hit@1: 0.8889
- Hit@3: 1.0
- MRR: 0.9259
- No-answer cases: 1
- No-answer abstention (top score < 0.2): 0.0

## By category

| Category | Cases | Hit@1 | Hit@3 | MRR |
| --- | ---: | ---: | ---: | ---: |
| definition_en | 1 | 1.0 | 1.0 | 1.0 |
| definition_id | 1 | 1.0 | 1.0 | 1.0 |
| paraphrase | 1 | 1.0 | 1.0 | 1.0 |
| theory_en | 4 | 1.0 | 1.0 | 1.0 |
| theory_id | 2 | 0.5 | 1.0 | 0.6667 |

## Per case

| Case | Category | Expected | Top article | Hit@1 | RR |
| --- | --- | --- | --- | --- | --- |
| LR01 | definition_en | 2. Channels (as observed in the cached files) | 2. Channels (as observed in the cached files) | True | 1.0 |
| LR02 | definition_id | 2. Channels (as observed in the cached files) | 2. Channels (as observed in the cached files) | True | 1.0 |
| LR03 | theory_en | 2. Braking | 2. Braking | True | 1.0 |
| LR04 | theory_id | 2. Braking | 2. Braking | True | 1.0 |
| LR05 | theory_en | 3. Throttle | 3. Throttle | True | 1.0 |
| LR06 | theory_en | 5. Drag and aero limits | 5. Drag and aero limits | True | 1.0 |
| LR07 | theory_en | 4. Interpretation rules | 4. Interpretation rules | True | 1.0 |
| LR08 | theory_id | 4. Interpretation rules | 2. Braking | False | 0.333333 |
| LR09 | paraphrase | 4. Interpretation rules | 4. Interpretation rules | True | 1.0 |
| LR10 | no_answer_id | (no answer) | 2. Channels (as observed in the cached files) | False | 0.0 |

## Limitations

- Small corpus and small query set; not a general benchmark.
- The no-answer check uses a fixed score threshold, not semantic entailment.
- Indonesian queries depend on the prototype term-expansion map.
