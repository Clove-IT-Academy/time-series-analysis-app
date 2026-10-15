# Agent instructions: Time Series Analysis App

## Role and source of truth

- Work as a senior Python developer and AI engineer. Make deliberate, reviewable choices and keep implementation and explanations approachable for students.
- Follow [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md): preserve v1 scope, module boundaries, contracts, phase dependencies, milestone exit criteria, and acceptance gates. Record justified changes in its decision/progress log rather than silently diverging.
- The source [Time_Series_Analysis_and_Forecasting_Student_Notes.pdf](Time_Series_Analysis_and_Forecasting_Student_Notes.pdf) is a four-page teaching guide, not a system architecture specification. It establishes time-series concepts, ARIMA, exponential smoothing, chronological evaluation, MAE, and RMSE. The plan proposes the application architecture; do not attribute those choices to the PDF or imply another architecture document was reviewed.
- Treat proposed stack, limits, layout, and settings as implementation defaults pending verification, not user-approved or benchmarked facts. Proceed with documented defaults when unblocked; record assumptions. Reconcile any newly supplied architecture document before affected implementation.
- Inspect actual files and checks at session start. At creation of these instructions, only the source PDF and development plan existed; this is historical context, not an evergreen assertion about implementation status.

## Read context efficiently

- Read this file and the plan's current phase, decisions/progress, and relevant exit criteria before implementation. Read the entire plan when first establishing scope; do not substitute these summaries for its acceptance gates.
- Read [architecture and contracts](.agents/architecture.md) before changing module boundaries, data contracts, session state, or exports.
- Read [analytical correctness](.agents/analytical-correctness.md) before changing ingestion, preparation, exploration, models, evaluation, or forecast dates.
- Read [verification and delivery](.agents/verification-and-delivery.md) before adding checks, completing phases, changing dependencies, or preparing a release.
- These references elaborate this file and the plan. Keep them consistent when decisions change; avoid copying full plan sections into multiple files. Consult the PDF for teaching semantics, not on every routine code change.

## Scope and application architecture

- Build a local, single-user Python/Streamlit app for one target series per analysis, initially with regular daily, weekly, and monthly data. Use pandas/NumPy for data, statsmodels for models, Plotly for charts, and pytest for domain tests, subject to verified compatible versions.
- Follow the guided path: upload/example → profile and prepare → explore → validation comparison → frozen final test → full-history refit → future forecast → exports.
- Keep domain modules independent of Streamlit. Use the plan's proposed `src/time_series_app/` layout and minimal `app.py`; add modules only when needed. No hidden fitting, downloads, data writes, or UI startup during imports.
- Start with bounded synchronous fitting and in-memory session state. Do not add a separate frontend/API, queue, database, persistent uploads, accounts, cloud connectors, grouped forecasting, exogenous predictors, SARIMA, neural networks, or automated search without new requirements and a recorded scope decision.
- Deliver a thin end-to-end naive-baseline path before expanding all model controls. Preserve phase dependencies and the plan's M1–M5 delivery order.

## Security and privacy

- Validate CSV bytes/size, decoded rows, column choices, timestamps, numeric values, configuration, and library outputs at boundaries. Handle invalid data with controlled, actionable errors. Do not silently drop rows or coerce invalid data into valid-looking results.
- Treat uploads, filenames, column labels, and exported text as untrusted data. Never execute them, interpolate them into shell commands, use them as unrestricted filesystem paths, or render them as unsafe HTML.
- Do not load uploaded pickle/joblib objects, execute expressions from CSV cells, or introduce unsafe deserialization. Export plain data and JSON metadata rather than fitted Python objects.
- Keep uploads in session memory by default. Do not put raw observations, CSV previews, secrets, or unnecessary personal data in logs, crash artifacts, telemetry, fixtures, or source control. Use synthetic examples and non-sensitive diagnostics.
- Keep caching scoped safely: avoid process-global mutable datasets/fitted models and caches that expose one session's data to another. Document temporary-file lifecycle if files become necessary; cleanup must be idempotent and preserve original failures.
- Handle spreadsheet formula injection in untrusted text fields of CSV exports with a documented safe policy; preserve genuine numeric predictions as numbers. Do not alter source observations silently.
- Review dependency provenance and minimize dependencies. Do not add new network services or hidden data transfers. Shared hosting requires an explicit review of upload privacy, session isolation, access, resource limits, and deployment requirements.

## Runtime efficiency and reliability

- Bound upload bytes, parsed rows, forecast horizon, candidate count, seasonal period, rolling folds, and ARIMA search/order settings before expensive work. The plan's initial caps are provisional, not demonstrated performance.
- Consider time and space complexity. Avoid repeated parsing, unnecessary full-data copies, unbounded result histories, and fitting every candidate on every Streamlit rerun. Cache only with complete input/settings keys and a safe lifecycle.
- Measure parse, preparation, fit, prediction, chart, and memory behavior on representative supported datasets before making responsiveness claims. Chart sampling must never change scored or exported data.
- Surface convergence warnings, exceptions, non-finite predictions, and all-candidate failure. Preserve successful candidates without concealing failed ones or changing evaluation windows to favor them.
- Do not promise hard timeouts or cancellation from synchronous fitting without verifying enforcement. If measurements justify workers, document bounded execution, ownership, cancellation, and cleanup before introducing them.
- Invalidate dependent outputs whenever data/settings change. Never display old scores or forecasts as results for new inputs; see the state dependency table in the architecture reference.

## Python engineering standards

- Use clear names, cohesive functions, type annotations at public boundaries, and docstrings for non-obvious semantics. Prefer standard-library features and simple interfaces over speculative abstraction.
- Keep parsing, preparation, split logic, metrics, adapters, date generation, and exports testable without a browser. Make mutation/copy ownership explicit; preserve raw observations separately from prepared series.
- Use explicit serializable contracts with exact date alignment, provenance, configuration, warnings, and statuses. Do not rely on pandas positional alignment or implicit frequency inference to conceal inconsistent dates.
- Validate configuration before fitting. Use structured minimal diagnostics and catch errors at meaningful boundaries; do not broadly suppress exceptions or continue with corrupted state.
- Check current official APIs when selecting versions or using uncertain library behavior; lock a verified compatible environment. Do not claim installation, platform, interval, or numerical support that has not been checked.
- Update README, plan, and relevant `.agents` references when behavior, setup, architecture, privacy, assumptions, limits, or supported inputs change. Do not invent commands for tooling that has not yet been created.

## Forecasting and evaluation invariants

- Never shuffle time-series observations. Use strictly chronological training, validation, and untouched final test windows; freeze model selection before final test evaluation.
- Learn preprocessing only from the appropriate training history. Prevent cross-boundary filling, interpolation, aggregation, or model tuning; never score against imputed validation/test targets.
- Require explicit decisions on ambiguous dates, duplicate aggregation, gaps, resampling, cadence anchors, and seasonality. Initial date scope is consistent timezone-naive input; reject mixed timezone conventions.
- Support naive and seasonal-naive baselines, simple exponential smoothing, Holt, Holt-Winters, and bounded ARIMA(p,d,q). Enforce model eligibility and expose warnings; example settings are not universal optima.
- Compare candidates on identical dated truth with MAE and RMSE. Define errors as actual minus prediction. Keep validation predictions, final-test predictions, in-sample residuals, and future forecasts distinct.
- Generate future dates from the confirmed frequency/anchor; require finite predictions with the exact requested index and length. Refit the frozen configuration on eligible full history only after evaluation.
- Label supported intervals with method/coverage; never fabricate intervals for consistency. Explain forecasts as estimates without promising superiority to baselines or guaranteed outcomes.
- Distinguish ARIMA's MA errors from rolling-average smoothing; do not claim standard trend/seasonal decomposition separately measures economic cycles.

## Verification, changes, and completion

- Follow the plan's appropriate unit, integration, leakage-regression, UI-smoke, resource, clean-install, and release checks. Use hand-computable baseline/metric cases and deterministic synthetic signals; avoid brittle exact assertions for fitted statistical models.
- Verify changed behavior and report actual evidence, skipped checks, and limitations. A successful fit or chart alone does not establish forecast correctness, usability, or release readiness.
- Review changes for scope expansion, leaked data, date/index errors, leakage, stale state, unbounded computation, and export inconsistencies before finishing.
- Mark phases complete only after their deliverables and exit gates pass. Record changed files, tested versions/settings, verification, limitations, and next action in the plan's progress log.
- Release locally only after documented installation and the complete example-to-export workflow pass. Hosted deployment is conditional on a selected target; do not imply it is delivered by a local release.
- Keep this `AGENTS.md` at or below 250 lines. Put additional focused context in `.agents/*.md`, link it above with explicit read triggers, and verify references and consistency after edits.
