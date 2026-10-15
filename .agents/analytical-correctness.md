# Analytical correctness reference

Authority: [system architecture](../Business_Sales_Purchase_Forecasting_System_Architecture.pdf), sections 5–9; [development plan](../DEVELOPMENT_PLAN.md), sections 5–8. Read before changing detection, preparation, eligibility, fitting, evaluation or selection.

## Assisted detection and confirmation

Combine normalized names/synonyms with date parseability, numeric coverage, value/type plausibility and surrounding context. Preserve original column identities and show the evidence behind each candidate. Numeric codes must not become dates solely because parsing succeeds. Monetary-looking numbers do not establish whether a field means sales or purchase cost.

Scores are heuristic unless calibrated and verified otherwise. Configure/test low-score threshold and close-candidate margin; unresolved ambiguity returns needs-confirmation, not a silent mapping. Manual override remains available even for high-scoring candidates. Keep score thresholds separate from forecast adequacy thresholds.

## Business-aware preparation

1. Parse dates/numbers under stated conventions; ambiguous date order, currency/group/decimal separators or mixed timezone data require explicit handling. Initial timezone-naive support is a proposed boundary, not a PDF mandate.
2. Report invalid/excluded records and preserve raw data. Do not silently coerce, discard or mask questionable rows.
3. Confirm transactions versus periodic summaries. Aggregate transaction flows using an explicit meaningful rule, often sum; do not reaggregate summaries into double-counted amounts.
4. Establish duplicates from identifiers/business meaning. Equal date/amount can represent legitimate separate transactions. Summary duplicates need an explicit policy too.
5. Retain known zeros and negative refunds/adjustments. Model incompatibility is not permission to clip or delete values.
6. Infer cadence using calendar alignment and spacing; confirm uncertainty. Distinguish daily, anchored weekly, month-start/month-end. A month is not 30 days; horizon counts periods.
7. Mark absent reporting separately from known zero activity. Only an explicit business decision can establish no activity; generic zero/forward fill must not fabricate ground truth.
8. Define folds/bins so no aggregation crosses a cut point. Learn transformations only from each training history; no backward fill/interpolation using later validation data. Reject missing/non-finite validation targets rather than scoring invented truth.

Series diagnostics cover usable history, regularity, trend/seasonality evidence, variability, gaps, zeros/negatives and eligibility. Decomposition, if added, is descriptive and does not separately measure an economic cycle. Do not show full-history diagnostic evidence as if available inside earlier folds.

## Candidate contracts

| Method | Essential checks |
| --- | --- |
| Last-value naive | Finite final available training value; repeat across requested horizon |
| Seasonal naive | Adequate seasonal history; repeat latest complete seasonal cycle in correct order for horizons beyond one cycle |
| Simple exponential smoothing | Suitable level-only option with actual library input constraints |
| Holt | Supported trend configurations and adequate training history |
| Holt-Winters | Supported seasonality/period; proposed two complete training seasons plus library constraints |
| ARIMA(p,d,q) | Bounded nonnegative integer orders and supported fit settings; report convergence/fit failures |

Multiplicative components require strictly positive inputs; additive candidates can support appropriate zero/negative series. Do not silently substitute another family, period or transformation. ARIMA's MA terms use past errors, not rolling-average smoothing. Common output contract requires exact future index/length and finite values or a structured failure.

## Evaluation, adequacy and uncertainty

- Use chronological holdout for eligible shorter history, or rolling-origin folds for sufficient history. State why comparison is supportable; insufficient evidence is a valid outcome.
- Fix primary metric, candidate settings, fold boundaries, horizons, aggregate calculation and tie policy before evaluation. Compare identical dates; never drop difficult folds or use positional alignment to conceal mismatches.
- Error is actual minus prediction. MAE = mean absolute error; RMSE = square root of mean squared error. Report units, fold scores, sample counts and variability. Distinguish held-out errors from fitted residuals.
- Proposed primary ranking is MAE, with RMSE alongside. If MASE is used, compute scale from training-only naive differences using a declared lag and flag zero/invalid denominators. For sMAPE, declare zero/near-zero behavior. MAPE alone is inappropriate near zeros.
- Capture candidate failures/warnings. Document whether warned fits may be selected; do not hide convergence warnings behind a clean success status.
- Apply a separate configured adequacy rule after ranking. Record baseline comparison, minimum evidence, permitted warning statuses and any user/domain error tolerance. No universal monetary threshold or rule that “best means reliable” is justified by the architecture.
- If no candidate is eligible, return that state. If candidates fit but none passes quality, return no reliable forecast with metrics/next steps. A baseline can be the selected result only under an explicit policy; no hidden fallback.
- Refit accepted configuration on usable full history; keep its historical evaluation metrics tied to their original folds. Refit failure must not be disguised by old fitted output.
- Return prediction intervals only where verified method/API support exists, with coverage and assumptions. Do not fabricate equivalent smoothing bands, promise guaranteed coverage or silently clip negative forecasts/intervals.

A separate final test is optional for independent release claims, not required in every app run. If used, freeze selection before inspecting it; repeated tuning makes it exploratory. Preserve the architecture's chronological-validation workflow without adding a mandatory three-way split for short histories.

## Target isolation and synthetic cases

Run sales and purchases independently, even in the same workbook. Mapping/aggregation and seasonal evidence can differ; switching targets invalidates the old target's downstream results.

The primary fixture proposes at least 72 monthly periods of synthetic transactions and a 12-period forecast; those are demo settings, not universal minimum data. Also build documented deterministic ARIMA-favorable and smoothing-favorable cases under fixed evaluation settings as requested by architecture section 11.2. Verify evidence under pinned versions; never encode model selection around fixture names or guarantee the same winner for arbitrary data.
