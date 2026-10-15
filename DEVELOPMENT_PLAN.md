# Time Series Analysis App — Development Plan

Status: Proposed implementation plan; development has not started.
Created: 2026-10-15
Primary source: `Time_Series_Analysis_and_Forecasting_Student_Notes.pdf` (all four pages).

## 1. Purpose and how to use this document

Build a student-friendly application that takes a time series from raw observations through exploration, model comparison, evaluation, and future forecasting. This document is intended to be reusable context for future development sessions.

The project currently contains only the source PDF. Despite the architecture description in the planning request, that PDF is an introductory teaching document, not a system architecture specification. It does not prescribe a user interface, deployment platform, API, database, authentication, or repository layout. The architecture and product decisions below are proposed defaults, not requirements attributed to the PDF. If another architecture document becomes available, reconcile it with this plan before implementation and record any changes.

Implement phases in order. At each phase, read the source requirements, implement the deliverables, verify the exit criteria, and record completion evidence. Do not treat a checkbox as complete merely because code exists. Update this document when scope or architecture changes; record the reason and affected phases.

## 2. Source requirements and traceability

| ID | Source | Required behavior or teaching principle | Delivery phases |
| --- | --- | --- | --- |
| R1 | Page 1, sections 1–2 | Treat observations as measurements indexed by time; explain forecasts as estimates | 2–3, 7–8 |
| R2 | Page 2, section 3 | Explain trend, seasonality, cycle, and random variation, including additive versus multiplicative patterns | 4, 8 |
| R3 | Page 3, ARIMA | Offer configurable ARIMA(p,d,q); explain each parameter and distinguish MA errors from rolling averages | 5, 8 |
| R4 | Page 3, exponential smoothing | Offer simple exponential smoothing, Holt, and Holt-Winters for appropriate series | 5, 8 |
| R5 | Page 4, workflow | Sort observations, establish date index/frequency, plot, split chronologically, fit, forecast held-out data, inspect errors | 3–6 |
| R6 | Page 4, evaluation | Compare models with MAE and RMSE on observations later than training data; never shuffle | 6 |
| R7 | Pages 3–4, examples | Treat ARIMA(1,1,1), monthly period 12, and final-year holdout as examples, not universally optimal settings | 3, 5–6, 8 |

Additional engineering requirements in this plan support safe, reproducible implementation; they are not claims that the source PDF specified them.

## 3. Product scope

### First complete release

A local, single-user web app with an ordered workflow:

1. Load a bundled example or upload a CSV.
2. Select timestamp and numeric target columns.
3. Review parsing, ordering, duplicates, gaps, and frequency.
4. Apply explicit, documented preparation choices.
5. Explore the series and optional seasonal decomposition.
6. Configure an evaluation window and candidate forecasting models.
7. Compare validation results and inspect errors.
8. Confirm a selected configuration on an untouched final test window.
9. Refit the selected configuration on all eligible history and forecast future dates.
10. Download observations, predictions, metrics, and a reproducibility manifest.

Support one target series per analysis, regular daily/weekly/monthly data, and CSV export. Column selection allows files to contain other columns, but the first release does not model those columns as predictors. Make the supported frequency aliases explicit during setup, including weekly anchors and month-start versus month-end dates.

### Deferred scope

Multi-user accounts, database persistence, cloud storage, live data connectors, grouped forecasting, exogenous variables, SARIMA, automated hyperparameter searches, neural networks, probabilistic comparisons across every model, scheduled retraining, and production business integrations are outside the first release. Do not introduce these as prerequisites for a working educational app.

### Intended user experience

Use a guided page with clear stages and visible progress. Explain unfamiliar terms beside controls. Show the active dataset, frequency, preparation settings, split boundaries, model settings, and warnings with results. A configuration change must invalidate dependent results; never display old metrics as if they belonged to new inputs.

## 4. Proposed architecture and decisions

### Application structure

Use Python with Streamlit for the interface, pandas and NumPy for data handling, statsmodels for model fitting/decomposition, Plotly for interactive charts, and pytest for domain tests. Keep analytical functions independent of the UI so they can later support an API or another frontend.

These choices favor a small educational application with a single Python runtime. A separate frontend, backend service, queue, and database are unnecessary for the initial scope. Record an architecture decision before replacing this structure.

Determine a mutually compatible Python/library version set during setup, verify the actual APIs against official documentation, and lock dependencies. This plan does not claim that any particular package version has been verified.

```text
CSV / bundled example
        |
        v
Parse and profile --> preparation specification --> canonical series
                                                    |
                         +--------------------------+------------------+
                         |                                             |
                         v                                             v
               exploration / decomposition                  chronological evaluation
                                                                      |
                                                         compare / select / final test
                                                                      |
                                                        refit on full eligible history
                                                                      |
                                                        future forecast / CSV exports
```

Session state stores the current in-memory analysis and references to results. The filesystem stores code and bundled synthetic examples only; uploaded data is not persisted by default. Start with synchronous, bounded model fitting. If measured runtimes require background jobs later, make that a separate architecture decision.

### Proposed repository layout

```text
time-series-analysis-app/
  Time_Series_Analysis_and_Forecasting_Student_Notes.pdf
  DEVELOPMENT_PLAN.md
  README.md
  pyproject.toml
  <dependency lockfile>
  .gitignore
  .streamlit/config.toml
  app.py
  src/time_series_app/
    config.py
    contracts.py
    ingestion.py
    preparation.py
    exploration.py
    models/
      base.py
      baselines.py
      arima.py
      exponential_smoothing.py
    evaluation.py
    forecasting.py
    exports.py
    ui/
      state.py
      upload.py
      explore.py
      evaluate.py
      forecast.py
  data/examples/
  tests/
    fixtures/
    test_ingestion.py
    test_preparation.py
    test_models.py
    test_evaluation.py
    test_forecasting.py
    test_exports.py
    test_workflow.py
```

Add modules as the corresponding phase needs them. Avoid empty placeholder files and unnecessary abstraction.

### Core data contracts

| Contract | Minimum contents and invariants |
| --- | --- |
| DatasetProfile | Source label/hash, column names, parsed row count, date range, invalid rows, duplicates, gaps, inferred frequency |
| PreparationSpec | Timestamp/target columns, date parsing choice, frequency/anchor, duplicate aggregation, missing-value policy, optional resampling aggregation |
| PreparedSeries | Unique ordered datetime index; numeric finite target; explicit frequency; provenance and transformation warnings |
| EvaluationSpec | Validation horizon, final test horizon, primary metric, optional rolling origins, candidate configurations |
| ModelSpec | Family, exact parameters, seasonal period if used, training constraints |
| ModelResult | Configuration, fit status/warnings, training boundaries, dated predictions, metrics, runtime; failure details when applicable |
| ForecastResult | Selected configuration, fit data range, exact future timestamps, point forecasts, optional model-supported intervals with method/coverage |
| RunManifest | Dataset fingerprint, effective settings, split boundaries, package versions, result statuses, selection metric, export schema version |

Use stable serializable representations for settings. Preserve original observations separately from derived views. Forecast and actual indexes must match exactly before scoring; do not rely on positional alignment to hide indexing errors.

## 5. Non-negotiable analytical rules

- Never shuffle the series for splitting or evaluation.
- Split original observations before any learned preprocessing. Fit imputers, scaling, model selection, and parameter tuning using training history only. Validation and test targets must not be fabricated.
- Parse and sort timestamps before modeling. Require an explicit decision on duplicates, irregular frequency, and aggregation; never silently discard or average observations.
- Reject missing or non-finite evaluation targets. Users may change the evaluation window or repair source data, but imputed evaluation targets must not become ground truth.
- For missing training values, default to stopping for a user choice. Offer bounded forward fill as an explicit causal policy; leading gaps remain invalid. Do not interpolate using future validation/test values.
- Resampling is opt-in and must explain its aggregation. Do not resample across split boundaries. The declared cadence and bin anchors determine evaluation boundaries.
- Disable unsupported configurations with an explanation. In particular, multiplicative components require strictly positive training values; seasonal models and decomposition need sufficient complete seasons.
- Do not describe decomposition residuals as a separately measured economic cycle. Standard decomposition will not independently identify all four conceptual components from page 2.
- Distinguish validation forecasts, final test forecasts, and future forecasts in labels, data contracts, charts, and exports.
- Make no guarantee that a model beats a baseline or that forecast accuracy remains constant over time.

## 6. Step-by-step implementation

### Phase 0 — Confirm scope and resolve the architecture gap

**Depends on:** Source review, completed for this plan.

- [ ] Confirm whether the provided teaching PDF is the intended source or a separate architecture document exists.
- [ ] Adopt or revise the local Streamlit architecture, initial frequency support, single-series scope, and export format.
- [ ] Record decisions in a short decision log, including intended local-only or shared deployment use.
- [ ] Choose initial resource limits: proposed 10 MB upload, 50,000 rows, 365 future steps, up to 6 candidates, and bounded ARIMA orders. Treat these as provisional caps to benchmark, not demonstrated capacity.
- [ ] Choose a primary default comparison metric (proposed MAE); show RMSE alongside it.

**Deliverable:** Agreed implementation assumptions and a requirements checklist.

**Exit criteria:** No missing source document or deployment requirement can invalidate the selected architecture without being explicitly recorded as unresolved. If no additional document is supplied, proceed using this plan's labeled defaults.

### Phase 1 — Establish the project foundation

**Depends on:** Phase 0.

- [ ] Inspect the target folder and applicable repository instructions before creating files; avoid altering sibling applications.
- [ ] Create an isolated Python environment, package configuration, compatible dependency lock, and development commands.
- [ ] Build a minimal launchable Streamlit shell with the planned workflow stages.
- [ ] Add domain configuration and contract definitions; implement session invalidation rules.
- [ ] Add linting and a minimal import/startup check. Initialize project version control if appropriate to the workspace; do not assume the parent folder is a Git repository.
- [ ] Document installation, launch, test, and lint commands with the actual verified versions.

**Deliverable:** A runnable shell and repeatable environment.

**Exit criteria:** A fresh environment can install locked dependencies and launch the app; domain modules import without importing Streamlit UI state.

### Phase 2 — Build ingestion and data profiling

**Depends on:** Phase 1.

- [ ] Add clearly labeled synthetic example datasets: nonseasonal trend, monthly seasonality, and data quality problems.
- [ ] Accept CSV uploads under the configured limits; handle encoding/parser failures with actionable messages.
- [ ] Let users select timestamp and target columns; preview rows before conversion.
- [ ] Detect ambiguous dates and require an explicit parsing choice. Reject mixed timezone conventions; initial scope uses consistently timezone-naive dates and explains that choice.
- [ ] Report invalid timestamps, nonnumeric/non-finite targets, duplicate dates, unsorted input, missing periods, inferred cadence, and date range.
- [ ] Separate warnings from blockers; never silently drop bad rows.
- [ ] Calculate a dataset fingerprint without logging raw uploaded values.

**Deliverable:** Validated upload/selection and a data quality report.

**Exit criteria:** Valid fixtures load reproducibly; malformed, oversized, empty, ambiguous, and invalid numeric inputs yield specific errors without crashing the session.

### Phase 3 — Implement preparation and chronological splits

**Depends on:** Phase 2.

- [ ] Sort timestamps and require a duplicate policy: reject by default, or user-selected sum/mean where meaningful.
- [ ] Confirm frequency, including monthly/weekly anchor semantics; display inferred frequency as a suggestion.
- [ ] Offer explicit regularization/resampling only where a documented aggregation is supplied. Show before/after counts and date range.
- [ ] Construct the canonical date grid and distinguish absent periods from existing null values.
- [ ] Implement missing-training-data policies with leakage-safe boundaries; prohibit scoring against imputed labels.
- [ ] Configure validation and final test sizes in periods, showing dates and sample counts before fitting.
- [ ] Reserve the final test window before candidate comparisons. The remaining development history supplies training and validation.
- [ ] Enforce enough remaining training data for candidate eligibility. The PDF's final 12-month holdout is a monthly example, not a global default.

**Deliverable:** Reproducible preparation pipeline and explicit split specification.

**Exit criteria:** Tests prove strict training < validation < final-test order, deterministic anchor handling, no cross-boundary filling/resampling, and rejection of missing evaluation truth.

### Phase 4 — Add exploratory analysis and teaching content

**Depends on:** Phase 3.

- [ ] Plot observations with interactive date navigation; show count, range, missingness, and summary statistics.
- [ ] Add optional rolling summaries with window sizes expressed in periods; label them as exploration, not forecasting models.
- [ ] Show trend/seasonality/residual decomposition when its assumptions and minimum history are satisfied.
- [ ] Default seasonal decomposition to additive; allow multiplicative only for positive data with an explanation.
- [ ] Explain that seasonal period is samples per repeating cycle: monthly/yearly = 12, daily/weekly = 7 where appropriate. Do not infer business meaning from cadence alone.
- [ ] Add concise explanations of trend, seasonality, cycles, irregular movement, and the difference between a pattern and a causal explanation.
- [ ] If displaying full-history exploration, label it descriptive. Use training-only diagnostic views for model selection and keep final-test values hidden from the selection workflow.

**Deliverable:** An exploration screen with explicit applicability limits.

**Exit criteria:** Valid series render correctly; short/constant/nonpositive data disables unsuitable analysis gracefully; exploration does not mutate modeling inputs.

### Phase 5 — Implement baselines and model adapters

**Depends on:** Phases 3–4.

Implement in this order so a working reference exists before more complex fitting:

1. Last-value naive forecast.
2. Seasonal naive forecast when sufficient seasonal history exists.
3. Simple exponential smoothing for level-only series.
4. Holt for trend.
5. Holt-Winters for trend and seasonality.
6. ARIMA(p,d,q), with configurable bounded nonnegative integer orders.

- [ ] Give each model the same fit/predict result contract and exact dated horizon.
- [ ] Expose only supported, understandable controls; use ARIMA(1,1,1) as an example preset, not an optimal automatic choice.
- [ ] Start with additive Holt/Holt-Winters; gate optional multiplicative components on positivity and data adequacy.
- [ ] Use an explicit conservative seasonal-history rule (at least two complete training seasons) and surface additional library constraints separately.
- [ ] Capture convergence warnings, exceptions, elapsed fitting time, and non-finite output. A failed candidate must not stop successful candidates.
- [ ] Bound expensive configurations before fitting. Verify whether the chosen runtime can enforce a hard timeout; do not promise cancellation from a synchronous UI if it cannot.
- [ ] Add ARIMA prediction intervals only if the selected API supports them correctly. Do not invent matching intervals for other models; label absent intervals and model assumptions.

**Deliverable:** A common model layer with transparent failure handling.

**Exit criteria:** Each eligible model returns exactly the requested number of future timestamps and finite predictions, or a structured failure. Baseline outputs match hand-computable cases. Source example configurations run on a suitable monthly fixture.

### Phase 6 — Build evaluation, comparison, and selection

**Depends on:** Phase 5.

- [ ] Evaluate candidates on the same validation timestamps, using only preceding training observations.
- [ ] Calculate MAE and RMSE from aligned finite observations. Explain units; avoid percentage metrics as the default because zeros are common.
- [ ] Show the metric table, candidate settings, baseline comparisons, actual/predicted chart, error-over-time plot, and mean error with its sign convention.
- [ ] Define error consistently as actual minus prediction and avoid claiming in-sample residuals equal out-of-sample errors.
- [ ] Rank successful candidates by the chosen primary metric; preserve failures and warnings in a separate visible status field. Use a deterministic tie rule and allow deliberate user selection.
- [ ] Offer bounded expanding-window validation after the single-window path works. Freeze fold boundaries and compare candidates on identical valid folds; do not silently omit difficult folds.
- [ ] Freeze the selected configuration before final test evaluation. Refit on training plus validation, then forecast the reserved test dates once.
- [ ] Label repeated test inspection/reselection as exploratory; a repeatedly used test window is no longer an untouched performance estimate.

**Deliverable:** Auditable model comparison and final test result.

**Exit criteria:** Hand-calculated MAE/RMSE fixtures pass; mismatched dates cannot score; final-test targets never enter selection; candidate failure does not silently change the comparison window.

### Phase 7 — Implement final forecasting and exports

**Depends on:** Phase 6.

- [ ] Refit the frozen model configuration on all eligible observed history, using the same documented preparation rules.
- [ ] Let users choose a bounded future horizon in periods. Construct exact future timestamps from the established cadence and anchor.
- [ ] Plot historical values and future point forecasts with a visible forecast boundary. Display intervals only when actually calculated and identify their method/coverage.
- [ ] Warn about long horizons and model assumptions without presenting point predictions as guarantees.
- [ ] Export prepared observations with provenance, per-candidate evaluation predictions, validation/final-test metrics, future forecasts, and a JSON run manifest.
- [ ] Include timestamp, actual where available, prediction, model/configuration ID, and evaluation segment in prediction exports; optional interval columns must be explicitly named.
- [ ] Make exports independent of chart display sampling. Do not serialize fitted Python objects or include raw uploads in server logs.

**Deliverable:** Complete future forecast and reproducible result bundle.

**Exit criteria:** Forecast dates correctly cross month/year boundaries; values match the displayed result; exported metrics can be recomputed from exported predictions; manifest captures effective settings and versions.

### Phase 8 — Integrate the guided workflow

**Depends on:** Phases 2–7.

- [ ] Connect upload, quality review, exploration, evaluation, final test, and future forecast stages with clear next actions.
- [ ] Implement invalidation: dataset/column/frequency/preparation changes clear all dependent analysis; split changes clear evaluation/selection/forecasts; candidate changes clear their comparisons; forecast-horizon changes clear only the future forecast.
- [ ] Distinguish runnable, running, successful, warning, and failed states. Disable duplicate submissions while fitting.
- [ ] Make labels readable, keyboard navigation usable, chart colors distinguishable, and errors actionable.
- [ ] Add reset/session cleanup and explain that refresh/restart may discard in-memory work.
- [ ] Complete model explanations and tooltips aligned with the source PDF, including the ARIMA MA versus rolling-average distinction.

**Deliverable:** Usable end-to-end local application.

**Exit criteria:** A user can complete the bundled example without developer help; changing settings never leaves stale outputs; a failed fit has a recovery path.

### Phase 9 — Verify correctness and operational limits

**Depends on:** Phase 8; domain tests are written alongside earlier phases.

- [ ] Run unit tests for ingestion, preparation, index handling, baseline math, eligibility rules, metrics, and exports.
- [ ] Run integration tests for seasonal and nonseasonal CSV-to-export workflows, invalid upload recovery, and all-model-failure recovery.
- [ ] Add leakage regression tests that alter held-out values and verify training transformations and validation selection remain unchanged as appropriate.
- [ ] Use synthetic signals to check plausible behavior without asserting every fitted model must beat the baseline.
- [ ] Run a UI smoke test for the main flow and state invalidation using supported Streamlit testing or a documented manual script.
- [ ] Measure upload, chart, fitting, and memory behavior on representative supported files. Record hardware, sample sizes, candidates, timings, and final resource limits.
- [ ] Verify logs exclude uploaded data; exports contain only intended analysis content; temporary data is cleaned if any was introduced.
- [ ] Run lint, tests, clean installation, and launch checks from the documented commands.

**Deliverable:** Verification evidence and known limitations.

**Exit criteria:** All required checks pass, the full demo succeeds, limits are measured and enforced, and no unresolved defect can produce misleading evaluation or forecast dates.

### Phase 10 — Package and release

**Depends on:** Phase 9.

- [ ] Finish README setup, CSV examples, interpretation guide, troubleshooting, architecture summary, and limitations.
- [ ] Document the tested Python/library versions, resource caps, supported date conventions, and data lifecycle.
- [ ] Add CI for lint/tests if a Git hosting repository is established; keep local checks runnable independently.
- [ ] Create the first versioned local release with a reproducible environment and release notes.
- [ ] If hosted deployment is requested, choose the platform and document secrets, upload handling, HTTPS, access restrictions, memory limits, and restart behavior before publishing. Shared hosting requires a review of session isolation and privacy.
- [ ] Verify the released environment with the same example workflow and exported-result checks; document rollback to the previous locked release.

**Deliverable:** Documented, tested application release. Hosted deployment is conditional on a deployment target being selected.

**Exit criteria:** Another user can install and operate the local app from its documentation; any chosen hosted environment passes smoke checks before being declared released.

### Phase 11 — Maintain and improve

**Depends on:** First release.

- [ ] Triage failures using reproducible settings and synthetic/minimized data rather than requesting sensitive uploads by default.
- [ ] Re-run regression tests when upgrading numerical libraries; compare tolerances and warning behavior before updating the lockfile.
- [ ] Track user confusion and slow operations; prioritize measured issues.
- [ ] Consider rolling validation improvements, persisted analyses, additional frequencies/models, or an API only after the initial workflow is reliable.
- [ ] Revisit architecture before introducing accounts, concurrent long jobs, persistent uploads, or business-critical forecasting.

**Deliverable:** A maintained backlog and repeatable upgrade process.

## 7. Dependency order and delivery milestones

The main dependency chain is:

`0 → 1 → 2 → 3 → 4 → 5 → 6 → 7 → 8 → 9 → 10 → 11`

Domain tests accompany their implementation phase. Documentation grows throughout. After the data contracts are stable, explanatory text and UI presentation can be developed independently of model adapters, but integration still waits for validated contracts.

| Milestone | Included work | Demonstration required |
| --- | --- | --- |
| M1: Reliable data foundation | Phases 0–3 | Upload CSV, understand quality issues, prepare a regular series, inspect chronological boundaries |
| M2: First complete analytical path | Phase 4, naive baseline portion of 5, minimal 6–7 | Explore sample, evaluate naive forecast, refit, export a dated future forecast |
| M3: Complete model comparison | Remaining 5–7 | Compare ARIMA and smoothing against baselines, evaluate frozen selection on final test, export reproducible results |
| M4: Release candidate | Phases 8–9 | Complete guided flow, correct invalidation, measured limits, passing verification |
| M5: First release | Phase 10 | Fresh install and documented local use; hosted smoke test if applicable |

Build M2 as a thin end-to-end implementation before expanding all model controls. Reuse the same contracts as more models arrive. Do not build every screen before verifying the data-to-forecast path.

No delivery dates are committed here: staffing, available time, and deployment requirements are unknown. Estimate each milestone after M1 establishes the actual data/UX complexity.

## 8. Acceptance scenario and test matrix

### Primary acceptance scenario

Use a deterministic synthetic monthly series with at least 72 complete positive observations, an additive trend, and seasonality of period 12. Declare month-start or month-end explicitly. Reserve the last 12 observations for final test and the preceding 12 for validation, leaving at least 48 for initial training.

The user loads the data, confirms quality/frequency, explores training patterns, compares naive/seasonal-naive/ARIMA/smoothing candidates, selects a configuration using validation metrics, views its final-test score, refits on all 72 observations, forecasts 12 future months, and downloads results. Every chart and export uses the same correct dates. This is a demonstration fixture, not a claim that 72 points is universally sufficient.

| Case | Expected behavior |
| --- | --- |
| Unsorted timestamps | Sort with an explicit summary; preserve values |
| Duplicate timestamps | Block until rejection or explicit aggregation is chosen |
| Ambiguous dates | Require parsing choice; show interpreted examples |
| Missing training periods | Show gaps; require documented causal handling or reject |
| Missing validation/test actuals | Block scoring; do not replace with imputed truth |
| Irregular cadence | Require regularization decision or reject modeling |
| Short seasonal history | Disable seasonal candidates/decomposition with reason |
| Zero/negative values | Allow eligible additive models; reject multiplicative configuration |
| Constant series | Return finite meaningful baseline metrics; handle unsuitable diagnostics |
| Invalid or oversized CSV | Reject with a recoverable message |
| ARIMA convergence/fitting failure | Surface status; retain other model results |
| Month-end/leap-year/weekly anchor | Generate exact expected boundaries and future dates |
| Dataset or preparation changed | Invalidate all dependent outputs |
| All candidates fail | Show reasons and allow correction; do not select a winner |
| Export replay | Recompute metrics from predictions; identify dataset and effective settings |

## 9. Risks and planned responses

| Risk | Response |
| --- | --- |
| A separate architecture document was intended | Resolve in Phase 0; preserve this plan's source/proposal distinction |
| Evaluation leakage | Split-first processing, hidden final test during selection, regression tests |
| Misleading cadence or seasonality | Explicit frequency anchors and user-confirmed seasonal period |
| Poor forecasts interpreted as reliable | Baseline comparison, held-out metrics, labeled uncertainty and limitations |
| Slow or unstable fits | Parameter/data/candidate caps, captured warnings, measured runtime; revisit execution architecture only if needed |
| Incorrect library assumptions | Verify official APIs during setup, lock tested versions, use small model integration fixtures |
| Scope grows into a production platform | Keep first-release boundaries; require an architecture decision for persistence/concurrency/accounts |
| Lost session work | Explain in-memory lifecycle and provide early exports; persistence is a later feature |

## 10. Overall definition of done

The first release is complete only when:

- All source requirements R1–R7 have a demonstrated implementation or an explicit documented interpretation.
- The primary acceptance scenario passes from a fresh environment.
- Candidate comparison, final test evaluation, and future forecasting remain distinct and leakage-safe.
- Invalid inputs, unsupported settings, failed fits, and stale results have correct visible handling.
- Exported predictions, metrics, and manifest are consistent and reproducible within documented numerical tolerances.
- Required automated checks and UI smoke verification pass.
- Installation, resource limits, data handling, supported frequencies, and limitations are documented.
- No unimplemented hosted deployment is presented as completed.

## 11. Development-session handoff checklist

At the start of each future implementation session:

1. Read this plan, the source PDF when needed, project instructions, README, and the latest decision/progress entries.
2. Inspect existing code and current checks; establish what is actually complete.
3. Select the earliest incomplete phase or a documented prerequisite defect.
4. Implement a reviewable increment without expanding first-release scope.
5. Run checks appropriate to the changed behavior.
6. Update phase checkboxes and the progress log with changed files, verification evidence, limitations, and next action.

Use this progress-log format:

| Date | Phase / milestone | Completed work | Verification | Open issue / next action |
| --- | --- | --- | --- | --- |
| 2026-10-15 | Planning | Reviewed all four PDF pages; created proposed end-to-end plan | Source requirements mapped to phases; no app code existed | Begin Phase 0 decisions, then foundation |

Use a decision-log entry with: decision ID, date, question, selected option, rationale, alternatives considered, and phases affected. Keep unresolved questions visible; do not silently change the source requirements or mark planning defaults as user-approved decisions.
