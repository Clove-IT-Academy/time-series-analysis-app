# Verification and delivery reference

Read before designing tests, completing milestones, updating dependencies, or releasing. DEVELOPMENT_PLAN.md phases 0–11 and sections 7–11 remain the full schedule and acceptance source.

## Delivery sequence

| Milestone | Required outcome |
| --- | --- |
| M1, phases 0–3 | Record architecture assumptions; reproducible environment; profile/prepare CSV; explicit chronological boundaries |
| M2, thin portions of 4–7 | Explore a synthetic series, evaluate naive baseline, refit, export exact dated future predictions |
| M3, remaining 5–7 | Add seasonal baseline, smoothing, ARIMA; validation selection, frozen final test, reproducible exports |
| M4, phases 8–9 | Guided state-safe workflow, failure recovery, verification and measured limits |
| M5, phase 10 | Documented clean local installation and release; hosted delivery only if a target was selected |
| Maintenance, phase 11 | Regression-checked upgrades and evidence-based backlog |

Tests accompany implementation; Phase 9 consolidates verification rather than deferring correctness until the end. Do not create all planned modules or screens before the thin vertical path works.

## Verification matrix

| Change area | Required relevant evidence |
| --- | --- |
| Ingestion | Valid, empty, malformed, oversized, ambiguous dates, invalid numbers, duplicate columns/selection handling |
| Preparation | Unsorted/duplicate dates; gaps; leading missing history; explicit aggregation; chronological split and anchor semantics |
| Leakage | Alter held-out values: earlier training transforms/fit inputs must remain unchanged; alter final test: validation selection must remain unchanged |
| Baselines/metrics | Hand-computable naive/seasonal repetition, MAE/RMSE, sign conventions, exact index checks |
| Statistical adapters | Eligible synthetic data; expected index/length, finite output or structured failure, convergence warnings, positivity/history constraints |
| Evaluation | Identical candidate windows, failed-candidate/fold policy, frozen selection and test exposure, no fabricated truth |
| Future forecasts | Anchored dates over leap/year/month boundaries, correct horizon, full-history refit provenance |
| UI state | Data/settings changes invalidate correct outputs, duplicate submission handling, reset and all-candidate-failure recovery |
| Exports | Values match displayed run; recompute metrics from predictions; manifest settings/versions; safe text fields; no fitted-object deserialization |
| Integration | Seasonal and nonseasonal CSV-to-export workflows, invalid-upload recovery, primary monthly acceptance scenario |
| Operations | Measured parse/fit/chart/memory behavior, enforced limits, non-sensitive logging and cleanup |
| Release | Actual lint/tests, fresh locked installation, app launch and UI smoke test; hosted smoke check only if applicable |

Use deterministic synthetic fixtures without private user data. Choose justified numerical tolerances for fitted statistical outputs; avoid exact optimizer coefficients or tests that merely mirror implementation. Do not require network access or external live datasets for ordinary domain tests.

Use supported Streamlit testing where applicable or a documented manual UI script. Distinguish automated evidence, manual evidence, skipped checks, and unverified platform claims.

## Limits and dependencies

The plan proposes 10 MB upload, 50,000 rows, 365 future steps and up to six candidates; ARIMA orders and rolling folds must also be bounded. These are initial policy candidates. Benchmark on recorded hardware, verify upload byte units, and record chosen limits before claiming capacity.

Check current official Python/library APIs when selecting versions. Lock a compatible tested environment, document real setup/check commands, and rerun numerical regression fixtures on upgrades. Do not assume an unrelated sibling application's environment is compatible.

Performance reports identify sample size, horizon, candidate configurations, fold count, hardware, versions and measured runtime/memory. A successful small demo does not establish maximum supported capacity or a hard fitting timeout.

## Completion and handoff

Before completing a change, review source/settings flow for leakage, exact dates, stale results, excessive resource use, private data in outputs/logs, and accidental deferred-scope additions. Verify every local Markdown reference you add. Keep root AGENTS.md within 250 lines.

Update the plan's existing progress log with date, phase/milestone, completed work/changed files, actual verification, open issues and next action. For changed decisions, record ID, date, question, option, rationale, alternatives and affected phases. Do not create competing status ledgers in these references.

A release needs all R1–R7 requirements addressed, complete acceptance workflow, distinct validation/test/future outputs, controlled failure cases, reproducible exports, passing required checks, and accurate setup/data-lifecycle/limitations documentation. Preserve a previous verified release and document rollback when one exists. Publish no hosted-release claim without an implemented and checked deployment target.
