# Verification record — 2026-10-16

Environment: supplied project `venv`, Python 3.14.7, macOS 27.0.1 arm64. Exact package versions are in `requirements.lock`.

- 50 automated tests passed, including Streamlit AppTest, full sample CSV/XLSX-to-forecast flows, target invalidation, no-forecast/refit/all-candidate failure, leakage checks and exported metric recomputation.
- Ruff lint and formatting checks passed after implementation.
- `pip check`: no broken requirements. Local editable installation and engine wheel build succeeded using this venv. A separate fresh environment/platform installation has not been verified.
- Actual Streamlit server started on 127.0.0.1:8501; the browser loaded Business Forecast Studio and its input controls correctly. Automated AppTest covers running the synthetic example and changing targets. No manual live-file upload/download cycle or exhaustive responsive/accessibility audit is claimed.
- No production hosting, multi-user isolation certification or adversarial file-parser audit is claimed.

## Synthetic performance samples

Measured with `scripts/benchmark.py` on the above machine, one run each, tracemalloc enabled. Allocation peaks are Python-traced allocations, not total process RSS. Results are indicative, not throughput guarantees or a full limit-combination benchmark.

| Input | Candidates / folds | Parse | Engine | Peak traced allocation | Outcome |
| --- | --- | --- | --- | --- | --- |
| 168 monthly transaction rows / 4,372 bytes | All six / 1 | 0.009 s | 1.980 s | 49.42 MiB | Success with cautions |
| 50,000 daily summary rows / 750,011 bytes | Naive / 1 | 0.074 s | 0.297 s | 15.51 MiB | Success with cautions |

Chart/UI timing is not isolated here. Maximum-size Excel plus all models/folds has not been benchmarked. Caps are safety policy, not demonstrated capacity. No hard fit timeout/cancellation is implemented.

## Deterministic model-comparison cases

Tests use seed 9, three chronological six-period validation folds, and ARIMA(1,0,0):

- Autoregressive signal: 240 observations around level 100, AR coefficient 0.85, innovation standard deviation 2; ARIMA selected (observed MAE ≈ 2.854 versus naive ≈ 3.272).
- Linear signal: 120 observations, slope 3 and noise standard deviation 0.1; Holt selected (observed MAE ≈ 0.096 versus naive ≈ 10.558).

Selection has no fixture-specific code. These cases demonstrate model-dependent behavior under the locked versions, not universal winner claims.

## Remaining release work

A local working prototype is delivered. Formal clean-install testing on a separate environment, broader platform checks, worst-case fit/parser benchmarking and manual accessibility/download testing remain release-hardening work. No tagged production release or hosted service is implied.
