# Business Sales & Purchase Forecasting System — Development Plan

Status: Architecture-aligned implementation plan; no implementation completion is implied.
Revised: 2026-10-15
Source of truth: [Business_Sales_Purchase_Forecasting_System_Architecture.pdf](Business_Sales_Purchase_Forecasting_System_Architecture.pdf), all 15 pages.

## 1. Purpose, precedence, and correction

Build the local teaching prototype specified in the architecture: convert uploaded business records into a reviewable univariate sales or purchase series, compare eligible forecasting methods chronologically, and return forecasts with evidence, warnings, or an explicit reason to abstain.

This revision replaces the earlier plan based on an introductory teaching PDF. The actual architecture now governs product scope, module ownership, contracts, and implementation phases. Removed assumptions include CSV-only ingestion, purely manual mapping, the `time_series_app` package, and a mandatory separate final-test stage for every run. A final test can be added for release claims, but chronological holdout or rolling-origin validation is the architecture's required comparison protocol.

The architecture specifies a modular monolith, a UI-independent forecasting engine, assisted mapping, transaction-aware preparation, and abstention. Engineering details marked **proposed** below fill gaps in that specification; they are not additional claims about what the PDF requires. If a decision changes, record its rationale and affected requirements/phases here and update agent references. Do not silently widen scope or weaken acceptance gates.

Use this plan for implementation and progress tracking. Follow seven phases corresponding directly to architecture section 13. Read the relevant gates before coding; mark tasks complete only with recorded verification. At the time of this correction the inspected project contains documentation, not application code. Reinspect actual files before future work.

## 2. Architecture requirements and traceability

| ID | Architecture source | Required outcome | Phases |
| --- | --- | --- | --- |
| A1 | Sections 2–3, 9, 12 | CSV and Excel ingestion, worksheet selection, validated size/shape and parsing diagnostics | 1–2, 7 |
| A2 | Sections 5–7 | Ranked date/sales/purchase candidates with confidence evidence, alternatives, thresholds and manual correction; ambiguous critical mappings stop | 1–2, 5–7 |
| A3 | Sections 2.2, 3, 7.2 | One dataset and one sales or purchase target per run, separate preparation/selection for each; explicit transaction versus summary semantics | 1–3, 5–7 |
| A4 | Sections 7.2–7.4 | Explicit aggregation, duplicate and missing-period treatment, retained valid zeros/negative adjustments, confirmed cadence | 3, 5–7 |
| A5 | Sections 4–5, 12–13 | `src/forecasting_app/` engine owns rules; Streamlit calls one orchestrator and only collects/displays values | 1–7 |
| A6 | Sections 7.4, 8.1 | History/seasonality eligibility, bounded ARIMA and suitable exponential smoothing, reference baseline | 3–5, 7 |
| A7 | Sections 8.2–8.3 | Past-only holdout or rolling-origin evaluation; matching folds/horizons; MAE/RMSE, declared primary metric, visible failures/fold scores | 4–7 |
| A8 | Sections 5–6, 8.4–9 | Explicit confirmation, insufficient-history, no-eligible/weak-quality outcomes; configured adequacy rule; no unsupported forecast | 1, 4–7 |
| A9 | Sections 6, 8.4 | Full-history refit after selection; exact forecast dates; supported intervals only; provenance and configuration | 4–7 |
| A10 | Sections 9–10 | Local, in-session processing; no default durable storage; stage logs without raw business data; user-initiated CSV export | 1–2, 5–7 |
| A11 | Sections 11–13 | Unit/integration/UI checks, synthetic demos, reusable engine, reproducible setup and handoff | 1–7 |

Section/page references refer to the architecture PDF, not the superseded teaching notes. Requirements A1–A11 are shorthand for traceability, not replacements for reading the corresponding architecture sections.

## 3. Scope and user journey

### Initial release

- Local single-user Streamlit prototype; one uploaded dataset active at a time.
- CSV and Excel upload with sheet choice where relevant. The scope names CSV/XLSX while the component table also names XLS. Deliver CSV/XLSX as baseline; resolve legacy XLS explicitly in Phase 1. Support it with a verified reader and tests or document its intentional exclusion rather than claiming all Excel files work.
- Assisted date, sales, and purchase column detection using transparent heuristics and value/type evidence. Show evidence and permit override even for high-scoring candidates.
- One selected monetary target per run. If both sales and purchase columns exist, switching targets creates a separate preparation and selection path; no joint target model is implied.
- Transaction or already-periodic inputs, with explicit aggregation meaning, cadence, missingness and duplicate policies.
- History/regularity/trend/seasonality/value diagnostics; eligible naive reference, ARIMA, and exponential smoothing variants.
- Chronological validation; interpretable metrics and fold variability; configured selection/adequacy policy; explicit no-reliable-forecast behavior.
- Refit selected configuration on usable history and forecast a user-selected number of periods. Return intervals only where supported.
- Preview, confirmations, stage progress, charts, comparison, cautions, and user-initiated CSV download consistent with the engine result.

### Non-goals

No production multi-tenant SaaS, authentication/billing/organizations, permanent database, default upload retention, background job queue, distributed serving, deep learning, causal forecasting, external economic feeds, inventory optimization, or automatic business decisions. No promise that every upload yields a reliable forecast. Future hosting/API/persistence/additional models require explicit decisions after the core prototype is demonstrated.

### User journey

Upload → choose worksheet → preview and detection evidence → confirm/correct date and target → confirm transaction/summary meaning, aggregation and cadence → review preparation diagnostics/gaps → configure horizon/evaluation → assess eligibility → compare or abstain → refit and forecast → inspect evidence/limitations → export.

Unresolved critical inputs stop forecasting. Insufficient history and poor results are normal supported outcomes, not generic exceptions or empty charts.

## 4. Architecture and ownership

The app is one deployable modular application. Streamlit is a thin client. The reusable package owns ingestion, detection, preprocessing, analysis, evaluation, models, orchestration and serializable responses. No engine module imports Streamlit or depends on session objects.

```text
CSV / Excel bytes + sheet choice
              |
     ingestion -> UploadResult
              |
     detection -> ranked ColumnCandidates
              |
UI collects explicit mapping/semantic choices
              |
      service.forecast(request)
              |
preprocessing -> analysis -> eligibility
              |
chronological candidate evaluation + baseline
              |
       select / warn / abstain
              |
      full-history refit if accepted
              |
 ForecastResponse -> UI / CSV export
```

Ingestion and detection helpers can be called before the forecast request to collect confirmations. Forecast execution still crosses a single orchestration boundary. The service revalidates the submitted choices and returns confirmation requirements rather than trusting UI flags blindly.

### Package layout

```text
time-series-analysis-app/
  AGENTS.md
  .agents/
    architecture.md
    analytical-correctness.md
    verification-and-delivery.md
  Business_Sales_Purchase_Forecasting_System_Architecture.pdf
  DEVELOPMENT_PLAN.md
  README.md
  pyproject.toml
  <verified dependency lock>
  app.py
  src/forecasting_app/
    contracts.py                 # proposed support module
    config.py                    # proposed support module
    ingestion.py
    detection.py
    preprocessing.py
    analysis.py
    evaluation.py
    service.py
    exports.py                   # proposed pure serialization helper
    models/
      base.py
      baselines.py
      arima.py
      exponential_smoothing.py
  tests/
    fixtures/
    test_ingestion.py
    test_detection.py
    test_preprocessing.py
    test_analysis.py
    test_metrics.py
    test_models.py
    test_service.py
    test_exports.py
    test_app.py
  sample_data/
```

Use architecture sections 4.1 and 12 for module ownership; `.agents/architecture.md` provides a focused map. Support modules are proposals to keep shared types/configuration and export serialization out of UI code. Add files only when needed, not as empty scaffolding.

Use pandas, a verified Excel reader, statsmodels, Streamlit and pytest. NumPy and a charting library may be used where needed; the architecture does not mandate Plotly. Avoid NLP/semantic dependencies unless a tested case demonstrates benefit beyond transparent heuristics and confirmation. Verify compatible current APIs during implementation and lock tested versions; no package version has been selected by this plan.

### Contracts

| Object | Required information |
| --- | --- |
| UploadResult | Table, source name, columns, row count, parse warnings; add source fingerprint/sheet metadata for traceability |
| ColumnCandidate | Column name, role, confidence, evidence, alternatives; explain score semantics rather than calling a heuristic score a calibrated probability |
| ForecastRequest | Uploaded table/reference, confirmed date/target mapping, selected business target, transaction/summary semantics, aggregation and duplicate/gap policies, frequency/override, horizon, evaluation/adequacy configuration |
| SeriesData | Target, frequency, values and exact index, aggregation, missing periods, diagnostics and transformation provenance |
| EvaluationResult | Candidate/configuration, fold metrics, aggregate metrics, status and errors; include fold dates, warnings, baseline comparison |
| ForecastResponse | Explicit status, forecast rows, selected model or none, comparison, diagnostics, warnings, effective run configuration and provenance |

ForecastRequest and additional metadata elaborate architecture section 5.1; use small typed objects without overengineering. Preserve valid missingness in intermediate records; fit-ready series must meet each method's finite-input requirements. Raw uploaded rows remain distinct from derived series.

Statuses must distinguish success, success with cautions, needs confirmation, insufficient history, and no eligible model. **Proposed:** add `no_reliable_forecast` when candidates fit but none passes adequacy, plus controlled invalid-input/refit-failure outcomes. Do not collapse quality failure into model ineligibility. Forecast rows are absent with an explanation on blocked outcomes; diagnostics/comparison remain available where calculated.

## 5. Decisions to resolve and conservative implementation defaults

| Decision | Starting position / required action |
| --- | --- |
| Legacy XLS | Architecture names it in section 4.1; choose/test reader support or record justified exclusion. CSV/XLSX remain required. Reject macros/unsupported formats explicitly. |
| Multiple worksheets | List supported sheets and require selection; do not concatenate or silently select a sheet with different business meaning. |
| Mapping score and ambiguity | Proposed configurable normalized heuristic scores with named evidence; require confirmation below threshold or within a close-score margin. Determine thresholds with fixtures; never claim statistical calibration. |
| Date/numeric conventions | Detect ambiguity in date order, currency symbols and decimal/group separators; ask before conversion. Proposed initial timezone-naive business dates; reject/require explicit handling of timezone-bearing mixed data rather than stripping it. |
| Frequency support | Proposed daily, anchored weekly, month-start/month-end initially. Verify actual aliases and calendar semantics; request confirmation when spacing is mixed. Expand only with fixtures. |
| Aggregation | Ask transaction versus summary. Sum is a suggested monetary-flow rule, never an invisible default; define allowed alternatives and explain meaning. |
| Missing periods | Keep unknown initially; user confirms no activity (zero) versus missing reporting/unknown. Require a documented modeling policy; never auto-zero or invent validation truth. |
| Duplicate records | Use identifiers and business meaning where available. Equal amount/date alone is not evidence of duplicate transactions. Summary duplicates need explicit handling. |
| Primary metric | Proposed MAE with RMSE shown. Fix ranking/tie policy before evaluating. Optional MASE/sMAPE require explicit edge semantics. |
| Adequacy / abstention | Required configurable rule, resolved before selection release gate. Document minimum comparable history/folds, baseline reference, permitted warnings and any scale-aware error threshold. Do not invent a universal business error tolerance or equate winning a ranking with adequate quality. |
| Intervals | Return only verified supported intervals, with method and coverage. Decide whether one family may omit them; never manufacture equivalent bands. |
| Resource limits | Proposed starting caps: 10 MB upload, 50,000 rows, 100 columns, 20 worksheets, 365 horizon periods, six candidate configurations, five rolling folds; additionally bound ARIMA orders and seasonal period. Benchmark, revise, and document enforcement/units. These are not capacity claims. |
| Execution | Synchronous bounded local work first. Do not promise hard timeouts without enforcement. Workers/queues require an architecture decision. |
| Final test | Optional separate release-assessment window if sufficient history exists; not a mandatory extra product stage. Any such window must remain outside selection. |

Document adopted values and rationale in the decision log below. Resolve decisions when their phase needs them; do not stop all independent work for optional choices. The absence of measured performance or agreed business tolerance must remain visible.

## 6. Analytical and operational invariants

- Never randomize time order. Every validation prediction uses only preceding history, including fitted transformations and parameter choices.
- Confirm business meaning before aggregating. Do not double-count summaries, delete legitimate equal transactions, discard valid zeros, or clip refunds/negative adjustments by default.
- Infer cadence with calendar alignment and expose uncertainty; horizon units are periods, not automatically days. Keep forecast/actual indexes exact.
- Keep missing evaluation targets missing and block unsupported scoring. No zero-fill/forward-fill may fabricate validation truth. Explicitly confirmed zero activity is a business observation policy, not a generic imputer.
- Anchor bins and partitions to prevent aggregation windows crossing evaluation cut points. Fit any learned handling per training fold; no backward fill/interpolation from future validation values.
- Check sufficient history, positivity and seasonality before fitting. Proposed conservative seasonal eligibility: at least two complete training seasons, plus actual method constraints; this is not a universal adequacy guarantee.
- Compare candidates on matching folds/horizons. Preserve failures, warnings, and fold variability; never drop difficult dates/folds to improve ranking.
- Selection and adequacy are separate. Return no reliable forecast when quality rules fail. A baseline can be selected only under an explicit documented policy; do not silently substitute it for a failing requested method.
- Refit selected configuration on usable full history after evaluation. Refit failure must not silently produce a forecast from an old partial-history fit.
- Intervals are model-dependent estimates with assumptions, not guarantees. Negative data/predictions require explanation, not silent nonnegative clipping.
- Local session memory is the default data lifecycle. No raw business rows/values in logs. User-initiated exports may contain intended business results; do not persist them automatically.
- Changing source/sheet/target/mapping/preparation invalidates all downstream outputs. Changes to evaluation/quality rules invalidate comparison/selection/forecast. Horizon changes invalidate horizon-dependent evaluation as well as forecast where applicable.

## 7. Step-by-step implementation

### Phase 1 — Requirements and architecture

**Depends on:** Review of actual architecture, completed for this revision.

- [ ] Translate A1–A11 into acceptance cases and confirm initial use cases/non-goals.
- [ ] Resolve initial formats/readers, cadence, transaction/summary choices, parsing conventions and resource limits as needed for ingestion.
- [ ] Define typed contracts, statuses, confirmation gates and module ownership, including orchestration before UI work.
- [ ] Define selection/adequacy policy configuration and how unresolved thresholds block unsupported reliability claims.
- [ ] Establish isolated Python environment, package metadata, tested lockfile and executable lint/test/import commands.
- [ ] Add a minimal importable engine skeleton only as needed; no model/UI side effects on import.
- [ ] Record risks, decisions and request lifecycle; keep this plan and agent context consistent.

**Deliverables:** Reproducible foundation, agreed contracts, decision/risk log and acceptance checklist.

**Exit gate:** A student can trace upload → confirmation → preparation → evaluation → select/abstain → forecast response and identify every module's owner. No undefined status or critical semantic ambiguity is treated as success.

### Phase 2 — Ingestion and assisted detection

**Depends on:** Phase 1 contracts and environment.

- [ ] Implement bounded CSV and XLSX readers; handle XLS according to the recorded decision. Check bytes, extension/container compatibility, shape and worksheets, including safe failure on corrupt/password-protected/unsupported files.
- [ ] List workbook sheets and honor explicit selection. Read bounded previews before expensive full processing when supported; post-parse limits alone are not memory protection.
- [ ] Produce UploadResult with original column identities, warnings, source fingerprint and sheet metadata; handle empty/duplicate headers deliberately.
- [ ] Normalize names for detection while preserving display names. Configure synonyms/abbreviations for dates, sales and purchases.
- [ ] Score using name terminology, date parse proportion, numeric coverage, value/type plausibility and neighboring context. Avoid interpreting numeric IDs as dates merely because a parser accepts them.
- [ ] Return ranked ColumnCandidates, score evidence and alternatives for each role.
- [ ] Implement low-confidence/close-score confirmation requirements and manual override even for high scores. An ambiguous `Amount` field must not silently become sales or purchase.
- [ ] Add synthetic CSV/XLSX fixtures with multiple sheets, alternative labels, ambiguous amount fields, separate/combined targets, malformed input and limits.

**Deliverables:** Readers, preview/profile data, candidate ranking and engine-level confirmation metadata, without requiring Streamlit.

**Exit gate:** Supported inputs read reproducibly; invalid uploads fail safely; sheet choice is honored; ambiguity never auto-selects silently and every proposed mapping is explainable.

### Phase 3 — Preparation and diagnostics

**Depends on:** Phase 2 validated tables and confirmed mapping contracts.

- [ ] Parse dates and monetary numbers under explicit conventions; report invalid/excluded rows and require a documented exclusion policy rather than silently losing records.
- [ ] Confirm transaction versus summary semantics. Aggregate transactions by selected calendar period/rule; preserve summaries without double-counting.
- [ ] Define identity-aware duplicate handling; retain legitimate same-date/same-value transactions and valid zero/negative amounts.
- [ ] Infer candidate cadence and calendar anchors; request confirmation where mixed/irregular. Show before/after row/period counts and transformation provenance.
- [ ] Represent absent periods separately from known zero activity; record user policy and unresolved reporting gaps.
- [ ] Implement split-aware preparation interfaces so future evaluation does not learn from held-out values or aggregate across cut points.
- [ ] Produce SeriesData and diagnostics for history length, regularity, trend, seasonal evidence, variability, gaps, zero/negative values and candidate eligibility.
- [ ] Gate seasonal/multiplicative methods correctly; any optional decomposition is descriptive and must not claim independent economic-cycle measurement.

**Deliverables:** Transaction-aware preprocessing, clean/diagnostic series contracts and eligibility analysis.

**Exit gate:** Synthetic edge cases follow documented policies; every transformation is inspectable; aggregation/duplicate/gap decisions preserve business meaning and do not fabricate ground truth.

### Phase 4 — Forecasting and chronological evaluation

**Depends on:** Phase 3 and evaluation/adequacy contracts from Phase 1.

Implement incrementally: last-value baseline → optional eligible seasonal baseline → simple exponential smoothing/Holt/Holt-Winters → bounded ARIMA. Use a common eligibility/fit/predict/optional-interval interface.

- [ ] Verify library APIs, input constraints and forecast index behavior against installed versions.
- [ ] Implement finite predictions or structured candidate errors/warnings; failed candidates do not terminate all evaluation.
- [ ] Implement a documented single chronological holdout; add bounded rolling-origin folds for sufficient history. Use identical evaluation timestamps/horizons across compared candidates.
- [ ] Fit learned transformations inside each fold using preceding observations only. Reject missing/invalid evaluation truth and incomparable candidates explicitly.
- [ ] Compute hand-checkable MAE and RMSE; define error as actual minus prediction. Keep fold-level and aggregate metrics, sample counts and dates. Proposed aggregate: pooled point errors, with fold summaries also visible.
- [ ] If adding MASE, derive scale from training-only naive errors and report invalid zero denominators. If adding sMAPE, specify zero/near-zero semantics. Do not use MAPE alone.
- [ ] Apply declared primary metric/tie rule and separately apply configured adequacy/baseline policy. Preserve fit, convergence, weak-quality and no-eligible outcomes.
- [ ] After accepted selection, refit exact configuration on usable history, generate anchored future dates, and return supported intervals with method/coverage only.
- [ ] Test refit failure, non-finite output, insufficient history and quality-based abstention as first-class outcomes.

**Deliverables:** Common forecasters, traceable chronological comparisons, configured selection/abstention and dated forecast results.

**Exit gate:** No randomized split or future leakage; results reproduce under recorded settings; failed/inadequate candidates cannot become unsupported confident forecasts.

### Phase 5 — Orchestration and response

**Depends on:** Phases 2–4. Contract scaffolding may start earlier; completion requires working engine stages.

- [ ] Implement one `service.forecast(request)` boundary, validating mapping confirmations, semantics, policies, horizon and evaluation configuration.
- [ ] Sequence preparation, analysis, eligibility, evaluation, adequacy, refit and response assembly. No engine dependency on Streamlit session state.
- [ ] Return explicit confirmation requirements with evidence/options before fitting when critical choices remain unresolved.
- [ ] Preserve distinct success, caution, insufficient-history, no-eligible, no-reliable and controlled failure outcomes, including comparisons and actionable next steps.
- [ ] Add stage progress hooks/logging that expose run IDs, stage durations and error categories without raw rows/business values or unsafe tracebacks.
- [ ] Implement pure CSV serialization and optional JSON run-metadata export. Include target, exact dates, selected configuration, comparison, warnings and provenance in the response/export design.
- [ ] Verify schema/serialization stability and safe untrusted text handling; do not serialize fitted Python objects or require durable upload storage.

**Deliverables:** Independently callable engine and complete typed response, with pure export helpers.

**Exit gate:** Integration code can execute success, confirmation, insufficiency and abstention paths without importing Streamlit; exported values and diagnostics derive from the same response.

### Phase 6 — Streamlit prototype

**Depends on:** Phase 5 usable service; ingestion/detection preview helpers are already available.

- [ ] Build upload/sheet selection, preview, role-candidate evidence, target selection and manual correction controls.
- [ ] Collect transaction/summary meaning, aggregation, frequency, gap/duplicate policies, horizon and evaluation settings explicitly.
- [ ] Show preparation/eligibility diagnostics before fitting; submit all decisions through the engine rather than cleaning/selecting in UI callbacks.
- [ ] Present stage progress, candidate/fold scores, baseline comparison, forecast, supported uncertainty, warnings, assumptions and no-forecast next steps.
- [ ] Implement session-scoped reuse/invalidation keyed by source/sheet/target and effective settings. Prevent duplicate runs; reset stale results after changes.
- [ ] Sales and purchases use distinct run identities. Switching targets must not reuse another target's prepared series, scores or selected model.
- [ ] Provide readable charts, accessible controls, user-initiated CSV download and session reset; explain memory lifecycle and forecast limitations.
- [ ] Keep raw data private in local memory, prevent cross-session mutable caches and exclude sensitive data from UI exception details.

**Deliverables:** A thin UI demonstrating the complete engine workflow.

**Exit gate:** The displayed comparison, forecast, warnings and download match the response; unresolved choices stop correctly; no hidden UI cleaning/model-selection rules exist.

### Phase 7 — Verification and handoff

**Depends on:** Phase 6; tests accompany every prior phase.

- [ ] Run unit checks for readers/sheets/limits, detection ambiguity/override, parsing/aggregation/gaps/duplicates, zeros/negatives, eligibility, metrics and forecaster contracts.
- [ ] Run leakage and index regression checks, including held-out-value perturbation, anchor boundaries, invalid truth and identical folds.
- [ ] Run complete integration cases from architecture section 11.2: seasonal monthly transactions; daily/weekly nonseasonal data; separate/combined target fields; ambiguous mappings; short/sparse/irregular/poor data; no-forecast outcomes.
- [ ] Include deterministic synthetic cases demonstrating ARIMA winning and smoothing winning under documented configurations, seeds and tolerances. Do not hardcode winners for arbitrary datasets or game selection logic to satisfy fixtures.
- [ ] Verify UI smoke path and download parity, candidate/refit failure recovery, reset and state invalidation.
- [ ] Measure parse/fit/chart/runtime memory on representative files with recorded hardware/settings; tune/enforce caps and document limits. Do not claim hard cancellation without demonstrated enforcement.
- [ ] Run actual lint/tests, clean locked installation, independent-engine invocation and local app launch. Record skipped/unavailable checks honestly.
- [ ] Finish README: formats and XLS decision, sheet flow, mapping evidence, business semantics, setup/run/test commands, metrics/adequacy, intervals, data lifecycle, limits and troubleshooting.
- [ ] Provide synthetic `sample_data/` with expected confirmation/success/abstention demonstrations; no real client records.
- [ ] Version the local release, preserve prior verified release when available, and document rollback and library-upgrade regression checks.

**Deliverables:** Verified local prototype, setup documentation, synthetic demos, evidence and limitations.

**Exit gate:** A user can upload, confirm meaning, inspect diagnostics, evaluate chronologically, understand forecast/abstention and export consistently from a fresh documented environment. A hosted release is not implied; hosting needs the architecture section 10.2 decisions first.

## 8. Milestones and acceptance scenarios

The phase dependency chain is `1 → 2 → 3 → 4 → 5 → 6 → 7`. Tests/documentation grow alongside each phase. Define contracts early and exercise a minimal baseline request without UI before expanding models; do not defer all integration until the interface is built.

| Milestone | Demonstration |
| --- | --- |
| M1: Interpretable inputs, phases 1–2 | Read CSV/XLSX, choose sheet, show ranked evidence and stop ambiguous mappings |
| M2: Business-correct series, phase 3 | Confirm row semantics, aggregate safely, explain gaps/adjustments and eligibility |
| M3: Reusable forecast engine, phases 4–5 | Chronological comparison and adequacy, accepted full-history forecast or typed abstention without Streamlit |
| M4: Working prototype, phase 6 | Guided confirmation, matching charts/downloads, target-safe session lifecycle |
| M5: Verified handoff, phase 7 | Clean setup, synthetic demo matrix, passing checks and documented limitations |

### Primary success scenario

Use synthetic monthly sales/purchase transaction records spanning at least 72 complete months with known calendar alignment, enough positive seasonal history and documented seed. Include multiple legitimate transactions in a period and both target fields. User selects sales, confirms date/mapping, transaction semantics and sum aggregation, reviews gaps/diagnostics, compares eligible baseline/ARIMA/smoothing on declared later windows, passes the configured adequacy rule, refits on usable history and forecasts 12 periods. Repeat independently for purchases; target-specific mapping/settings/results remain distinct. Provide a multi-sheet XLSX equivalent to exercise sheet choice.

The 72-month/12-step settings are fixture design proposals, not minimum-history guarantees. No candidate winner is presumed in this main scenario.

### Confirmation and no-forecast scenarios

| Input/condition | Expected result |
| --- | --- |
| `Date`, `Amount`, `Cost` with unclear roles | Show candidate evidence/options and require confirmation; no fit |
| Low top score or near-tied date/target fields | Require correction/confirmation, with high-confidence override still available |
| Workbook with several sheets | Explicit sheet selection; no silent merge |
| Already-monthly summary | Preserve intended values; no duplicate aggregation |
| Equal-valued legitimate transactions | Retain unless identity/confirmed policy establishes duplicates |
| Missing reporting period | Diagnose and request/record policy; no automatic zero |
| Valid zero and negative refund | Preserve; exclude only incompatible model configurations |
| Short/sparse/irregular data | Specific confirmation, insufficient-history or no-eligible outcome |
| Missing validation truth | No fabricated score; explain required repair/window change |
| All candidates fail or inadequacy rule rejects them | No reliable forecast; retain errors/metrics/next steps |
| Selected model cannot refit | Controlled failure; no old-fit substitution |
| Mapping/sheet/target/policy changes | Invalidate all affected results and downloads |
| Corrupt/oversized/unsupported upload | Safe actionable rejection without partial silent read |

## 9. Risks and release definition of done

Principal risks are mistaken mapping, aggregation that changes business meaning, missingness confused with zero activity, leakage, unsupported seasonal estimation, weak winners presented as reliable, unbounded Excel parsing/fits, and a local demo mistaken for production software. Controls are the explicit confirmations, diagnostics, eligibility, adequacy rules, limits and verification above.

First release is complete only when A1–A11 are traceable to demonstrated behavior; the architecture's acceptance path and no-forecast paths pass; the engine is independent of Streamlit; selection and preprocessing are leakage-safe; export/UI parity holds; limits and versions are verified; and setup, provenance, privacy and limitations are documented. Do not weaken gates to mark phases complete.

Separate final-test evaluation may be used for release-level accuracy claims if independently reserved. If inspected test outcomes drive model changes, report exposure and avoid claiming an untouched test. This is an optional engineering protocol, not an additional required UI stage from the architecture.

## 10. Decisions, progress, and next session

### Decision log

| ID / date | Decision | Rationale / alternatives | Affected work |
| --- | --- | --- | --- |
| D001 / 2026-10-15 | Replace teaching-notes-based plan/context with actual architecture | Newly supplied 15-page architecture is authoritative; retaining the old scope would omit required ingestion, detection, business semantics and abstention | Entire plan and agent context |
| D002 / 2026-10-15 | Use architecture's seven phases, `forecasting_app` layout and conceptual contracts | Align implementation boundaries; prior package and mandatory final-test workflow are superseded | Phases 1–7 |

Other values in section 5 remain proposed until chosen and verified; do not treat this log as approval of unmeasured thresholds or capacity.

### Progress log

| Date | Phase | Completed work / files | Verification | Next action |
| --- | --- | --- | --- | --- |
| 2026-10-15 | Planning correction | Replaced DEVELOPMENT_PLAN.md, AGENTS.md and three `.agents` guides using actual architecture | Read all 15 PDF pages; documentation link/consistency checks recorded in completion response | Start Phase 1; resolve formats, contracts, initial policies and environment |

At each implementation session: read AGENTS.md and triggered references, inspect actual files, read the current phase and logs, select the earliest uncompleted dependency, implement a reviewable increment, run relevant checks, and update this log with changed files, versions/settings, evidence, limitations and next action. Do not duplicate status ledgers in `.agents` references.
