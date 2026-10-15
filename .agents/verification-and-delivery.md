# Verification and delivery reference

Authority: [system architecture](../Business_Sales_Purchase_Forecasting_System_Architecture.pdf), sections 9–14; [development plan](../DEVELOPMENT_PLAN.md), sections 7–10. Read before adding verification, completing phases, changing dependencies or releasing.

## Seven-phase delivery

| Phase | Completion evidence |
| --- | --- |
| 1. Requirements and architecture | Traceable request lifecycle, responsibilities, contracts, statuses, decisions/risks and reproducible environment |
| 2. Ingestion and detection | Supported formats/sheets, safe reader limits, ranked evidence, ambiguity gate and override |
| 3. Preparation and diagnostics | Business-correct aggregation/duplicates/gaps, calendar series and eligibility evidence |
| 4. Forecasting and evaluation | Shared adapters, naive reference, chronological/fold metrics, quality selection/abstention and supported uncertainty |
| 5. Orchestration and response | Engine callable without Streamlit, complete typed statuses/provenance and consistent response/export |
| 6. Streamlit prototype | Thin confirmation/results UI, target-safe state and matching downloads |
| 7. Verification and handoff | Unit/integration/UI and failure checks, clean setup, measured limits, synthetic demos and accurate limitations |

Tests accompany each phase. Define contracts early, then exercise a minimal baseline engine request before expanding model/UI surface. Do not retain the earlier 12-phase schedule or mandatory final-test stage.

## Verification matrix

| Area | Required relevant cases |
| --- | --- |
| Readers | CSV/XLSX; XLS per recorded decision; corrupt/password-protected/unsupported/empty files; byte/row/column/worksheet caps; selected sheet and duplicate headers |
| Excel behavior | No macro/formula execution/external fetching; explicit policy for formulas/cached values and missing cached values |
| Detection | Synonyms/abbreviations, numeric/date evidence, numeric IDs, ambiguous `Amount`, low/close scores, manual override and separate sales/purchase roles |
| Preparation | Transactions versus summaries; legitimate repeated transactions; identity-aware duplicates; invalid dates/numbers; aggregation semantics; gaps/zeros/negative refunds; cadence/anchor |
| Leakage | Perturb future validation values and confirm earlier training transforms/fit inputs do not change; no cross-fold bin aggregation; no invented validation truth |
| Eligibility/models | Short/constant/sparse/irregular data, seasonal history, multiplicative positivity, exact index/length, finite outputs, unsupported intervals, fit/convergence/refit failures |
| Metrics | Hand-computed MAE/RMSE, units/sign, zero actuals, optional MASE invalid denominator and sMAPE edge policy |
| Selection | Identical folds/horizons, visible fold variability/failures, declared ranking/tie and adequacy rules, no hidden baseline fallback, no reliable forecast |
| Service | Confirmation before fit; success/caution/insufficient/no-eligible/quality-abstention outcomes; serializable provenance without UI imports |
| UI/exports | Display and download match engine response, safe exported text, target/source/sheet/policy invalidation, horizon-dependent evaluation, reset/failure recovery |
| Operations | Bounded parsing and fits, safe logs, session-memory lifecycle, no raw data in diagnostics, cleanup if temporary files exist |
| Release | Real lint/tests, clean locked installation, independent engine call, app launch and complete demo |

Use deterministic synthetic data and small hand-computable cases. Avoid exact optimizer coefficients, implementation-mirroring tests and real client uploads. Use justified numerical tolerances. Tests that need a verified optional reader/platform must be marked; report skips honestly rather than claiming support.

## Required integration demonstrations

1. Clean seasonal monthly transaction data with confirmed aggregation.
2. Daily or weekly nonseasonal history.
3. Separate sales/purchase datasets and both fields in one upload, with isolated target runs.
4. Multi-sheet XLSX selection and equivalent CSV semantics.
5. Ambiguous columns that stop for confirmation, followed by manual correction.
6. Short, sparse, irregular or poor-quality history with warnings/abstention.
7. A documented synthetic ARIMA win and a smoothing win under fixed settings, without generalizing winners to arbitrary data.
8. UI smoke test confirming forecast, metrics, warnings and CSV match the engine response.
9. All-candidate failure, quality rejection and selected-model refit failure with usable next steps.

## Limits, environment and handoff

Initial proposed caps are 10 MB, 50,000 rows, 100 columns, 20 sheets, 365 forecast periods, six configurations and five rolling folds; bound ARIMA orders/seasonal period too. These are policy candidates, not demonstrated capacity. Verify byte units, parser allocation behavior and actual enforcement; post-parse rejection alone does not bound memory. Measure stage timings/memory with hardware, versions, input shapes, candidates and folds recorded.

Choose/pin verified Python, pandas, Excel-reader, statsmodels, Streamlit and test versions. Check official APIs when implementation depends on uncertain/current behavior. NLP packages need demonstrated advantage over heuristics. Document actual install/run/lint/test commands once implemented, not assumed commands from this plan.

Before marking complete, review semantics, leakage, index alignment, state invalidation, privacy and bounded execution. Trace A1–A11 to evidence and satisfy both successful and no-forecast acceptance paths. Local prototype completion does not claim production readiness or hosted release.

Maintain one decision/progress ledger in DEVELOPMENT_PLAN.md. Record adopted thresholds/readers/formats, rationale, affected phases, changed files, actual checks/settings/versions, limitations and next action. Keep AGENTS.md within 250 lines and validate local references after documentation updates. On dependency upgrades, rerun regression cases and update documented numerical behavior; preserve verified releases and explain rollback when available.
