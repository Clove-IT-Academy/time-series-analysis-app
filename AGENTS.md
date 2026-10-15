# Agent instructions: Business Sales & Purchase Forecasting System

## Role and authoritative context

- Work as a senior Python developer and AI engineer. Make deliberate, reviewable choices and keep the implementation understandable for students learning end-to-end applied ML.
- Follow [Business_Sales_Purchase_Forecasting_System_Architecture.pdf](Business_Sales_Purchase_Forecasting_System_Architecture.pdf), all 15 pages, and the architecture-aligned [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md). Preserve initial scope, module ownership, contracts, seven phases and acceptance gates. Record justified changes rather than silently diverging.
- These instructions replace the earlier teaching-notes-based context. The actual architecture requires Excel ingestion, assisted mapping, transaction-aware preparation, a service boundary and abstention. Do not revive CSV-only scope, manual-only mapping, the `time_series_app` layout or a mandatory separate final-test UI stage.
- Distinguish architecture requirements from proposed implementation defaults. Scores, reader support, adequacy thresholds, versions and resource caps require decisions/tests; do not present them as user-approved, statistically calibrated or benchmarked facts.
- Inspect actual files and checks at session start. This revision changes documentation, not application implementation. Do not treat planned artifacts or completed planning as completed development.

## Read context efficiently

- On first work, read the architecture and full plan. Subsequently read this file, the plan's current phase, decision/progress log and relevant acceptance gates before implementation.
- Read [architecture and contracts](.agents/architecture.md) before changing package structure, request/response types, orchestration, state or exports.
- Read [analytical correctness](.agents/analytical-correctness.md) before changing detection, business-data preparation, diagnostics, models, evaluation, selection or forecast dates.
- Read [verification and delivery](.agents/verification-and-delivery.md) before designing checks, completing phases, changing dependencies or releasing.
- These guides focus the architecture/plan; they do not replace acceptance criteria or create competing progress logs. Update them together when decisions change. Consult relevant PDF sections for unresolved semantics.

## Scope and module boundaries

- Build one local, single-user modular application: Streamlit presents and collects choices; a reusable Python engine owns forecasting rules. Process one uploaded dataset and one selected sales or purchase target per run.
- Support CSV/XLSX and worksheet selection. The architecture component table also names XLS: resolve/test legacy support or document justified exclusion; do not silently claim every Excel format works.
- Follow `src/forecasting_app/`: ingestion, detection, preprocessing, analysis, models, evaluation and `service.py`; keep `app.py` thin. Use small shared contracts/configuration and pure export helpers when needed. Add files as implemented, not empty scaffolding.
- The UI may call ingestion/detection helpers to gather confirmations, then submits explicit choices to one forecast orchestration function. It must not clean data, select models, decide adequacy or conceal preparation rules in callbacks.
- No engine import may depend on Streamlit/session objects or trigger UI, fitting, downloads or persistent data writes. A future API must be able to consume its request/response without UI state.
- Preserve architecture phases: requirements/contracts → ingestion/detection → preparation/diagnostics → forecasting/evaluation → orchestration/response → Streamlit → verification/handoff. Exercise a minimal baseline engine path before expanding controls.
- Do not add production tenancy, accounts/billing, permanent storage, queues/distributed serving, deep learning, causal/external-data forecasting, inventory optimization or automated business decisions without new requirements and a recorded design change.

## Mapping and business-data semantics

- Detect candidate date/sales/purchase fields using normalized names, configurable synonyms, parseability, numeric coverage, value/type evidence and context. Return ranked candidates, evidence and alternatives; confidence scores are assistance, not certainty.
- Low confidence or close plausible candidates require confirmation. An `Amount` column alone cannot establish sales versus purchase meaning. Permit manual correction even for high confidence; the engine enforces gates independently of UI flags.
- Confirm transaction versus periodic summary rows. Require explicit meaningful aggregation; do not double-count summaries, silently sum arbitrary values or delete equal-valued legitimate transactions.
- Preserve valid zeros, refunds and negative adjustments unless an explicit documented treatment is selected. Missing reporting periods are not zero activity by default; ask/record their meaning and expose unresolved gaps.
- Confirm frequency/anchors when inference is uncertain; horizon is measured in periods of that cadence. Report invalid/excluded records and every transformation. Ambiguous date/number conventions require a choice, not silent coercion.
- Sales and purchase runs have independent mapping, preparation, evaluation and selection. Never reuse the other target's series, scores or model merely because the upload is unchanged.

## Forecasting and analytical rules

- Never shuffle time order. Use chronological holdout or rolling-origin evaluation, with each prediction based only on preceding history. Fit learned transformations per training fold; no future-derived filling, tuning or cross-boundary aggregation.
- Never score against imputed/missing validation truth or omit difficult dates/folds silently. Match actual/predicted indexes, horizons and candidate folds explicitly.
- Check history, cadence, seasonality and zero/negative values before fitting. Use bounded ARIMA and suitable simple/Holt/Holt-Winters smoothing behind a shared eligibility/fit/predict/optional-interval interface, with an eligible naive reference.
- Multiplicative components require positive data. The plan's conservative two-season rule is a proposed eligibility guard plus actual library constraints, not proof of reliability. Example parameter settings are not universal optima.
- Declare primary metric and tie policy before evaluation; proposed default is MAE with RMSE alongside. Preserve fold-level metrics, variability, warnings and failures. Define error as actual minus prediction. Optional MASE/sMAPE need explicit denominator/zero handling; do not rely on MAPE alone.
- Ranking and adequacy are separate decisions. Configure/document the quality/baseline rule and return no reliable forecast if it fails. Do not convert the least-bad score into a reliability claim or silently replace a method with a baseline.
- Refit the accepted selected configuration on all usable history; generate exact anchored future dates and finite values. Refit failure returns an explained failure, not an old partial-history forecast.
- Return prediction intervals only when the method/implementation supports them; identify method/coverage and limitations. Never fabricate bands or silently clip forecasts. Do not promise forecasts for every upload.
- A separate untouched final test may support release claims if reserved independently; it is not a mandatory app stage. Do not tune on it while calling it untouched. Clearly distinguish validation predictions from future forecasts and in-sample residuals.

## Outcomes, state and exports

- Return typed, inspectable UploadResult, ColumnCandidate, SeriesData, EvaluationResult and ForecastResponse objects, with an explicit request contract. Preserve resolved mapping, target, frequency, aggregation/gap/duplicate policies, evaluation windows, metrics, selected configuration and software versions.
- Distinguish success, caution, needs confirmation, insufficient history, no eligible model and no reliable forecast; represent invalid inputs/refit failures explicitly. Never encode all failures as an unexplained empty forecast. Preserve useful comparison/errors on abstention.
- Invalidate downstream results after source/sheet/target/mapping/semantic/preparation changes. Changes to evaluation, candidates or adequacy invalidate affected comparison/selection/forecast. Horizon changes may invalidate horizon-dependent evaluation; do not assume forecast-only invalidation.
- Derive charts, warnings and CSV downloads from the same response. Chart display sampling must not change scored/exported values. Exports are user-initiated; optional metadata export does not replace the source data needed for reproduction.

## Security, privacy and runtime reliability

- Validate bytes/container/type, worksheet counts, row/column shape, mapping, numeric/date values, horizon/configuration and library results at trust boundaries. Handle corrupt, password-protected, malformed and oversized files safely; no partial silent read.
- Bound parsing and candidate work before expensive operations where supported; post-parse limits alone do not protect memory. Do not evaluate Excel formulas/macros, external links or arbitrary expressions. Require cached-value/formula handling to be explicit.
- Treat filenames, headers, sheet labels and exported text as untrusted. No unsafe HTML, shell interpolation, unrestricted file paths, uploaded pickle/joblib, dynamic code execution or fitted-object exports. Apply documented formula-injection protection to exported text while preserving true numeric values.
- Keep uploads/results session-scoped and in memory by default. No raw business rows/values, secrets or unnecessary personal data in logs, exceptions, fixtures, telemetry or source control. Use synthetic examples; technical diagnostics must also be sanitized.
- Log run IDs, safe error categories and stage durations/configuration without leaking sensitive labels or values. Show actionable user messages, not raw tracebacks. Temporary-file cleanup, if introduced, must be idempotent and preserve original failures.
- Bound upload size, rows/columns/sheets, horizon, seasonal period, candidate configurations, ARIMA orders and rolling folds. The plan's initial caps are proposed, not measured capacity. Measure actual runtime/memory and consider algorithmic complexity.
- Avoid repeated parsing/fitting on UI reruns, unnecessary copies and unbounded histories. Cache with complete source/sheet/target/settings keys and safe ownership; no global mutable user datasets/models or cross-session exposure.
- Capture candidate warnings/failures without suppressing broken contracts or discarding successful candidates. Do not claim hard timeouts/cancellation without enforcement. Introduce workers only after measured need and a decision on bounded execution, ownership and shutdown.
- Hosting changes trust boundaries: resolve access, isolation, retention/deletion, encryption, scanning, secrets, rate/resources, auditing and operations before claiming a hosted release. Initial deployment is local only.

## Engineering, verification and handoff

- Use clear cohesive functions, typed boundaries, standard-library facilities and small explicit objects. Preserve raw/derived separation and mutation ownership. Keep domain behavior testable without a browser.
- Use pandas, a verified Excel reader, statsmodels, Streamlit and pytest; add dependencies only for demonstrated needs. Transparent heuristics precede NLP packages. Check official APIs, pin compatible verified versions and document actual commands.
- Test readers/sheets/limits; candidate scoring/ambiguity/override; transaction versus summary aggregation; gaps, duplicates, zeros/negatives; chronological leakage; eligibility/metrics; failure/abstention; export and UI/engine parity.
- Include architecture section 11's integration cases, including separate/combined sales/purchase fields and deterministic synthetic demonstrations of ARIMA and smoothing wins under documented configurations. Do not hardcode selection to manufacture winners for arbitrary data.
- Run appropriate checks for changes, using hand-computable metrics/baselines and tolerances for fitted models. Distinguish actual passes, skips, manual evidence and unverified claims. No-forecast paths matter as much as happy paths.
- Before finishing, inspect changes for architecture drift, hidden UI logic, incorrect business semantics, leakage/date errors, stale target-specific state, data leakage in logs and unbounded work.
- Update plan progress/decision logs, README and relevant references after behavior/setup/policy changes. Mark phases complete only when deliverables and exit gates pass, recording files, settings/versions, evidence, limitations and next action.
- Release only after clean setup, independently callable engine, complete demo and required checks pass; document limitations and rollback. Keep this file at or below 250 lines; add focused linked references in `.agents` with read triggers when needed.
