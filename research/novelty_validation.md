# Novelty Validation — Prior-Art Matrix

**Search date:** 21 November 2026
**Method:** targeted web searches plus direct reads of the linked abstracts/pages. This is not a systematic literature review.
**Rule:** "not found in the searches below" is not the same as "does not exist". Private products, non-indexed papers and non-English sources may exist.

## 1. Candidate claim (not yet proven)

> Evidence-gated telemetry-to-engineering learning: one flow that turns public F1 telemetry into measured facts, applies explicit rules for inference and evidence sufficiency, retrieves engineering literature through RAG, and presents learning material that separates facts, interpretations, citations and limitations for self-directed learners.

The claim is about **integration and target use**, not about inventing backward chaining, RAG, telemetry analysis or rule engines.

## 2. Matrix

| Entry | Date | Telemetry analysis | Education | Rule reasoning | Citation grounding | Insufficiency gate | Execution trace | Verification in this session |
|---|---|---|---|---|---|---|---|---|
| Farooq et al., *Harnessing AI forward and backward chaining with telemetry data for enhanced diagnostics and prognostics of smart devices*, Scientific Reports 15:7577. <https://doi.org/10.1038/s41598-025-89266-9> | 2025-03-04 | Yes — IoT telemetry (temperature, pressure, signal quality) | No — device maintenance | Yes — forward + backward chaining, rule base | No — alerts, not literature citations | No explicit evidence-sufficiency gate | Rule/alert engine described | **Abstract and full page read** |
| Thomas et al., *A hybrid RAG and rule-based reasoning framework for technical document analysis*, Frontiers in AI 9:1922508. <https://doi.org/10.3389/frai.2026.1922508> | 2026-09-17 | No | No — technical document QA | Yes — SAT, graph, geometric rule reasoning | Yes — constrained generation over retrieved rules | Partial — unsupported-query handling via geometric path | Yes — symbolic paths, auditability | **Abstract and substantial sections read** |
| AI Race Engineer — <https://airaceengineer.com/f1-race-engineer> | Accessed 2026-11-21 | Yes — sim-racing telemetry, corner coaching | For sim drivers, not public engineering learners | Not documented | Not documented | Not documented | Not documented | **Search result/snippet only; product not tested** |
| Formula Telemetry — <https://formula-telemetry.com/> | Accessed 2026-11-21 | Yes — speed/throttle/brake overlays | Visualization, not structured tutoring | No | No | No | No | **Snippet only** |
| The Field F1 — <https://www.thefieldf1.com/> | Accessed 2026-11-21 | Yes — telemetry analysis | Editorial/analysis, not adaptive tutoring | No | No | No | No | **Snippet only** |
| OpenF1ow — <https://www.openf1ow.com/> | Accessed 2026-11-21 | Yes — telemetry viewer | No | No | No | No | No | **Snippet only** |
| TracingInsights — <https://tracinginsights.com/data/> | Accessed 2026-11-21 | Yes — telemetry archive and visualization | No structured tutor | No | No | No | No | **Repository and README read; site not fully reviewed** |
| FastF1 — <https://docs.fastf1.dev/> | Accessed 2026-11-21 | Yes — data access library | No | No | No | No | No | **Documentation read** |
| Your Tech Director (official F1) | Reported in workspace snapshot §16 | Not reported | Yes — fan-facing regulation explanation | Not reported | Not reported | Not reported | Not reported | **Inherited from snapshot; not re-verified in this session** |
| Formula Rules RAG | Reported in workspace snapshot §16 | Not reported | No | No | RAG over regulations | No | No | **Inherited; not re-verified** |
| TechReg Analyst | Reported in workspace snapshot §16 | Not reported | Q&A for fans | No | RAG citations | No | No | **Inherited; not re-verified** |
| PercepLog-0 (EMNLP 2026 Findings) | Reported in workspace snapshot §16 | No | No | LLM-augmented backward chaining for legal reasoning | Not reported | Not reported | Not reported | **Inherited; not re-verified** |
| ARCCS / LegalGraphRAG | Reported in workspace snapshot §16 | No | No | Compliance reasoning | Yes | Partial | Not reported | **Inherited; not re-verified** |
| RC4PC (Inf. & Software Technology 2026) | Reported in workspace snapshot §16 | No | No | Requirement-change impact analysis | Not reported | Not reported | Not reported | **Inherited; not re-verified** |
| QuickSim / FSUK EV design study | Reported in workspace snapshot §16 | No | No | Motorsport rule checking | No | Not reported | Not reported | **Inherited; not re-verified** |

## 3. Search queries actually used

- `AI race engineer telemetry analysis Formula 1 LLM 2026`
- `telemetry learning tool students motorsport engineering education Formula 1 telemetry explain`
- `retrieval augmented generation telemetry engineering explanation citation grounding 2026`
- `hybrid expert system backward chaining RAG telemetry data rule-based evidence insufficiency`
- `public Formula 1 telemetry dataset speed throttle brake CSV github 2026`
- `F1 telemetry dataset Zenodo OR figshare OR huggingface lap speed brake throttle`

The education-specific query returned mostly irrelevant results. That is recorded as a gap in the search, not as evidence that no educational product exists.

## 4. What is clearly not novel

1. Backward chaining over telemetry (Farooq et al., 2025).
2. Hybrid RAG + rule-based reasoning for technical documents (Thomas et al., 2026).
3. Telemetry visualization and lap comparison (multiple products).
4. RAG with citation grounding (large literature).
5. Regulation Q&A for F1 fans (multiple products, inherited snapshot).

## 5. Remaining candidate gap

No single verified entry in this matrix combines **all** of the following:

1. public F1 telemetry as the data source;
2. deterministic feature extraction with units and uncertainty;
3. explicit rule-based inference plus an evidence-sufficiency gate;
4. RAG over engineering literature with citation validation;
5. a beginner/engineering learning presentation that separates observation, interpretation, citation and limitation;
6. an auditable execution trace for the rule and feature layer.

This is a candidate gap, not a proven novelty. It must be re-checked before publication and stated with the search date and scope.

## 6. Safe wording

> Berdasarkan pembanding publik yang diperiksa sampai 21 November 2026, kombinasi alur tersebut belum ditemukan terdokumentasi pada satu produk atau paper yang sama. Komponen-komponennya sudah ada secara terpisah.

Do not write "pertama di dunia", "algoritma baru", or "menggantikan race engineer".
