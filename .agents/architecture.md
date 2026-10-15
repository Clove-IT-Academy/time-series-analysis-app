# Architecture and contracts reference

Read before changing architecture, module interfaces, state, or exports. The authoritative proposal is DEVELOPMENT_PLAN.md sections 3–4; record changes there. Paths below are planned until implemented.

## Module ownership

All package paths are relative to `src/time_series_app/`.

| Path | Responsibility |
| --- | --- |
| `config.py` | Validated defaults, resource limits, supported frequencies and model controls |
| `contracts.py` | Shared serializable settings/results, statuses, provenance, index invariants |
| `ingestion.py` | CSV decoding/parsing, column mapping, source fingerprint and quality profile |
| `preparation.py` | Explicit duplicate/gap/resampling rules, regular date grid, split-aware transformations |
| `exploration.py` | Descriptive statistics, rolling summaries, eligible decomposition; no modeling input mutation |
| `models/base.py` | Common fit/predict contract and candidate failure/warning handling |
| `models/baselines.py` | Last-value and seasonal-naive adapters |
| `models/arima.py` | statsmodels ARIMA adapter and supported intervals |
| `models/exponential_smoothing.py` | Simple, Holt, Holt-Winters adapters and eligibility |
| `evaluation.py` | Chronological windows/folds, aligned metrics, selection and frozen final test |
| `forecasting.py` | Full-history refit of frozen configuration, future dates/horizon, forecast result |
| `exports.py` | Plain CSV/JSON outputs, schema consistency and export safety |
| `ui/state.py` | Session lifecycle, result keys, invalidation and reset |
| `ui/upload.py`, `explore.py`, `evaluate.py`, `forecast.py` | Guided controls/presentation; call domain functions |

`app.py` wires the UI. `data/examples/` contains synthetic fixtures. `tests/` holds domain and workflow checks. Keep environments, uploads, generated analyses, and large artifacts out of source control.

## Contract checklist

- **DatasetProfile:** source label/fingerprint, columns, parsed count, range, invalid rows, duplicates, gaps, inferred cadence.
- **PreparationSpec:** selected columns, date parsing, confirmed frequency/anchor, duplicate policy, gap policy and any resampling aggregation.
- **PreparedSeries:** unique sorted datetime index, explicit cadence, finite numeric modeling values, provenance and warnings. Preserve missing evaluation truth in validation information so it blocks scoring rather than disappearing.
- **EvaluationSpec:** validation/final-test horizons, primary metric, fixed fold boundaries when applicable, candidate configurations.
- **ModelSpec:** family, exact parameters, seasonal period, eligibility constraints.
- **ModelResult:** configuration identity, train boundaries, exact dated predictions, warnings/status/failure, metrics and runtime. Distinguish ineligible, failed, warning, and successful candidates.
- **ForecastResult:** frozen selected configuration, refit range, exact future index, finite points and optional supported intervals with method/coverage.
- **RunManifest:** dataset fingerprint, effective settings, split boundaries, package versions, result statuses, selection metric and export schema version.

Use one owner for date-grid creation and consistent adapter contracts; do not let every model independently invent timestamps. Match indexes explicitly before arithmetic. Use stable configuration fingerprints rather than mutable object identity to key results.

## Session invalidation

| Changed input | Invalidate |
| --- | --- |
| Dataset, columns, date parsing, cadence/anchor, duplicate/gap/resampling policy | Prepared data and every dependent exploration, evaluation, selection, test, forecast, export |
| Validation/test boundaries or rolling folds | Comparisons, selection, final test, forecasts and dependent exports |
| Candidate parameters/list or selection metric | Affected comparison/ranking, selection, final test, future forecasts and dependent exports |
| Selected configuration | Final-test and future results tied to the old selection |
| Future horizon | Future forecast and its exports only |
| Display-only chart controls | Presentation only; analytical/export values remain identical |

Include all effective upstream settings in reuse keys. In-memory final results and exports must reference the same immutable run specification. A new analytical run must not inherit a previous run's claim of untouched test evaluation.

## Exports and data lifecycle

Provide prepared observations with provenance, candidate validation/final-test predictions and metrics, future forecasts, and a JSON manifest. Prediction rows identify timestamp, actual where available, prediction, configuration ID and segment. Identify optional interval columns and coverage; do not fill absent intervals with invented values.

Keep dataset fingerprints for identification; they do not replace the source observations needed to reproduce a run. Document that a user must retain their own source CSV. Keep numerical tolerances and package versions explicit; do not promise byte-identical statistical fits across environments.

Synchronous execution is the first architecture. Persistent analyses, API services, multi-user deployment and background workers require a recorded decision with operational/data ownership implications, not incremental hidden additions.
