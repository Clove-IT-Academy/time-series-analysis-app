# Architecture and contracts reference

Authority: [system architecture](../Business_Sales_Purchase_Forecasting_System_Architecture.pdf), sections 4–6, 10, 12–13; [development plan](../DEVELOPMENT_PLAN.md), sections 3–5. This replaces the earlier teaching-app architecture context. Read before changing boundaries, orchestration, session state or exports.

## Module ownership

Package paths are relative to `src/forecasting_app/`, as specified in the architecture. Paths remain planned until implemented.

| Path | Owner of behavior |
| --- | --- |
| `ingestion.py` | CSV/Excel readers, worksheets, file/shape limits, UploadResult and parse diagnostics |
| `detection.py` | Ranked date/sales/purchase candidates, score evidence, ambiguity and confirmation metadata |
| `preprocessing.py` | Explicit parsing, transaction/summary semantics, duplicate/aggregation policy, calendar index, missing periods, provenance |
| `analysis.py` | History/regularity/trend/seasonality/variability/value diagnostics and eligibility evidence |
| `models/` | Common eligibility/fit/predict/optional-interval interface; baseline, ARIMA and smoothing adapters |
| `evaluation.py` | Past-only windows/folds, metrics, candidate comparison, selection/adequacy evidence and failure records |
| `service.py` | Request validation, confirmation gates, workflow sequencing, select/abstain, full-history refit and ForecastResponse |
| `contracts.py` (proposed) | Shared typed requests, domain results, statuses and serializable metadata |
| `config.py` (proposed) | Validated limits, heuristic thresholds, candidate/evaluation/adequacy policies |
| `exports.py` (proposed) | Pure response-to-CSV/metadata serialization and safe text handling |

Root `app.py` owns only Streamlit controls and display. `sample_data/` holds synthetic teaching inputs. `tests/` holds domain, integration and UI checks. Do not retain the superseded `src/time_series_app/` layout or move model-selection rules into UI helpers.

## Orchestration boundary

Preview can call engine ingestion/detection helpers; the forecast operation uses one explicit request to `service.forecast(request)`. The service verifies inputs/confirmations, prepares the selected target, analyzes eligibility, runs chronological evaluation, applies declared selection/quality rules, refits if accepted and assembles a response. Unresolved confirmation returns before model fitting.

No engine dependency on Streamlit, widgets, sessions or UI-side cleaning. Stage progress can be a UI-independent callback/event. Avoid circular ownership: analysis supplies eligibility evidence, adapters enforce method constraints, evaluation compares, service coordinates and returns the outcome.

## Contracts and statuses

| Object | Contract checklist |
| --- | --- |
| UploadResult | Table, original source/columns, row count and warnings; proposed fingerprint and selected-sheet metadata |
| ColumnCandidate | Original column identity, role, score/confidence semantics, evidence and alternatives; preserve duplicate-header identity deliberately |
| ForecastRequest | Validated table/reference, resolved date and selected sales/purchase target, confirmation decisions, row semantics, aggregation/duplicates/gaps, frequency, horizon, evaluation and adequacy settings |
| SeriesData | One target, frequency and anchors, values/exact index, aggregation, missing periods, diagnostics, exclusions/transformation provenance |
| EvaluationResult | Candidate/configuration, exact train/validation fold dates, fold/aggregate metrics, status, errors/warnings and baseline evidence |
| ForecastResponse | Explicit status, selected model or none, forecast rows, comparison, diagnostics, warnings, run configuration and versions |

The five architecture-named objects are UploadResult, ColumnCandidate, SeriesData, EvaluationResult and ForecastResponse. ForecastRequest elaborates architecture section 5.1. Use small dataclasses/typed classes or justified validation models; framework choice is not prescribed.

Keep distinct: success, success with cautions, needs confirmation, insufficient history, no eligible model. Proposed additional `no_reliable_forecast` identifies quality failure after fitting; invalid upload/request and refit failures need controlled explanations too. No forecast rows must not imply no diagnostics. Keep candidate errors inspectable and never mislabel “all fit but too poor” as “not eligible.”

Intermediate missingness must survive until resolved; only a fit-ready model input must be finite. Preserve raw rows separately. Stable settings include target and business semantics, not only model parameters. Fingerprints identify a source but cannot reconstruct missing source data.

## State invalidation

| Change | Invalidate |
| --- | --- |
| Upload or worksheet | Table-derived candidates, mappings/confirmations where no longer valid, preparation and all results/exports |
| Selected target/date/target column | Target-specific preparation, diagnostics, evaluation, selection and forecast |
| Row semantics, date/numeric conventions, duplicate/gap/aggregation rule, cadence/anchor | Every downstream prepared result, comparison, forecast and export |
| Candidates, folds, primary metric, adequacy threshold/policy | Affected evaluation, selection, forecast and export |
| Horizon | Forecast/export and evaluation if horizon determines fold windows or scoring |
| Display-only controls | Presentation only; underlying scored/exported values stay identical |

Run keys include source fingerprint, sheet, mapping, target, effective policies and evaluation settings. One dataset may support separate sales/purchase runs, but state must not cross their identities. Clearing a session clears in-memory user data/results; avoid process-global mutable caches.

## Exports and deployment

User-initiated CSV download is required; optional comparison/metadata downloads should reuse the same response. Forecast rows have exact timestamps, point values and optional verified interval columns; include target/units where known. Provenance includes mapping, frequency, aggregation, missing-period policy, windows, metric definitions, configuration and software versions.

Do not save uploads/forecasts automatically. No database, external service or background queue is required. Local memory is the initial design; future API/hosting/persistence requires documented decisions and privacy/operational controls. CSV serialization never exports executable/fitted Python objects.
