# Analytical correctness reference

Read before modifying data preparation, diagnostics, model fitting, evaluation, or forecast dates. DEVELOPMENT_PLAN.md sections 5–6 and 8 define the full acceptance requirements.

## Ingestion and preparation

1. Parse with explicit date semantics; show interpreted examples for ambiguous formats. Initially accept consistently timezone-naive dates and reject mixed timezone conventions. Never silently strip timezone information.
2. Profile invalid dates, nonnumeric/non-finite values, duplicates, gaps, and ordering before destructive transformations. Preserve the original data and report proposed changes.
3. Sort timestamps. Reject duplicates by default; require user-selected sum/mean only when semantically appropriate.
4. Confirm daily/weekly/monthly cadence and anchors. Monthly/yearly seasonality is 12 monthly samples; cadence alone does not establish seasonality. Do not equate a month with 30 days.
5. Make regularization/resampling opt-in with explicit aggregation and before/after counts. Assign raw observations to chronological partitions using declared bins/anchors; no aggregation bin may mix training and held-out observations.
6. Split before learned preprocessing. Default to blocking on missing training values pending a choice; optional bounded forward fill is causal and must not invent leading history. Never backfill/interpolate from held-out future values.
7. Validation/test observations must be finite actual values. Missing truth blocks scoring; do not drop hard dates, score fabricated targets, or change candidate windows silently.

A date grid or a configured deterministic transformation is not permission to learn from future values. For each fold/refit, state which history is available and fit transformations on that history only.

## Models and diagnostics

| Candidate | Eligibility and behavior |
| --- | --- |
| Last-value naive | Repeat the final available training value for every horizon step |
| Seasonal naive | Repeat the training series' latest complete seasonal cycle, continuing its correct position for horizons longer than one cycle |
| Simple exponential smoothing | Level-only option; do not imply trend/seasonality support |
| Holt | Trend option; expose only supported validated controls |
| Holt-Winters | Trend and seasonal option; at least two complete training seasons under the plan's conservative rule, plus actual library constraints |
| ARIMA(p,d,q) | Bounded nonnegative integer orders; explain differencing and past errors; example (1,1,1) is not optimal by definition |

Use strictly positive training values for multiplicative components/decomposition. Check history and configuration eligibility before fitting; do not silently substitute another model or seasonal period. Constant/short signals should produce useful baselines or clear ineligibility, not unexplained diagnostics failures.

Capture convergence warnings and non-finite output. Declare how warned fits participate in ranking; do not hide warnings behind a success badge. Never invent uncertainty bands. When supported, report interval coverage/method and assumptions and maintain the exact forecast index.

Decomposition is descriptive: standard trend/seasonal/residual components do not separately identify economic cycles. Label full-history charts as descriptive and keep final-test information out of selection diagnostics. ARIMA MA terms refer to forecast errors, not rolling-average smoothing.

## Evaluation and selection

- Reserve the final test first, then divide development history into earlier training and later validation. Require strict chronological boundaries and enough training history for every eligible candidate.
- Evaluate every compared candidate on identical actual timestamps and the same horizon. Require exact index and length equality; reject accidental pandas alignment gaps or positional scoring.
- Define error `e = actual - prediction`; MAE is `mean(abs(e))`, RMSE is `sqrt(mean(e**2))`. Show metric units and sign convention for mean error. Avoid percentage metrics as defaults with zeros.
- Proposed primary ranking is MAE, with RMSE also displayed. Verify a deterministic tie policy, permit deliberate selection, and distinguish failure from a poor score. Do not force complex models to beat baselines.
- If adding expanding-window validation, freeze common fold boundaries and enforce preprocessing independently inside each fold. A failed fold cannot disappear from the comparison without visible, justified handling.
- Freeze configuration before refitting training plus validation and forecasting final-test dates. Do not use final-test scores for tuning while calling them unbiased confirmation.
- If test inspection drives reselection, label subsequent claims exploratory and record test exposure; reserve new independent data before claiming a fresh final evaluation.
- Refit on eligible full observed history only for future forecasting after evaluation. Keep the final-test metrics tied to their original training boundaries; do not replace them with full-history fitted performance.

## Future dates and examples

Generate exact dates from the confirmed anchored cadence after the last observation. Test month-start/month-end, leap years, weekly anchors, and horizons exceeding a seasonal cycle. Do not treat the integer forecast step as a date.

The source PDF's 12-month test and ARIMA(1,1,1) are teaching examples. The plan's acceptance fixture is at least 72 complete positive monthly observations: 48 initial training, 12 validation, 12 final test, followed by a full-history refit and 12-step future forecast. These are fixture settings, not universal minimum-data guarantees.
