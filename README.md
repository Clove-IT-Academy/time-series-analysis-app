# Business Forecast Studio

A local Streamlit application for exploring business records and forecasting **one sales or purchase target per run**. It provides CSV/XLSX ingestion, explainable column suggestions, explicit transaction/summary preparation, chronological model comparison, quality-based abstention, and user-initiated exports.

## Run using the existing venv

From `time-series-analysis-app/`:

```sh
venv/bin/python -m streamlit run app.py
```

Open http://127.0.0.1:8501. The configured server binds to localhost; upload data stays in session memory. The app starts with synthetic monthly transactions so you can try the complete workflow immediately.

Dependencies and the editable package have already been installed in the existing `venv`. To reproduce the tested dependencies in that environment:

```sh
venv/bin/python -m pip install -r requirements.lock
venv/bin/python -m pip install --no-build-isolation --no-deps -e .
```

Tested on macOS arm64 with Python 3.14.7, pandas 3.0.6, NumPy 2.5.4, statsmodels 0.15.0, Streamlit 1.66.0 and openpyxl 3.1.5. `requirements.lock` pins all installed dependencies and development tools; availability on other platforms/Python versions has not been verified. The repository, `app.py`, and `sample_data/` are needed for the interface; the built wheel contains the reusable engine only.

## Workflow

1. Use a synthetic example or upload UTF-8 CSV/XLSX. Select a worksheet for Excel.
2. Preview the records and column-detection evidence. Choose sales or purchases, then confirm the intended date/target columns. Scores are transparent heuristics, not probabilities.
3. Confirm transaction versus summary rows, aggregation, frequency, number/date conventions, and gap/invalid-row policies.
4. Choose future horizon, validation window, expanding-window fold count, seasonal period, candidates and quality tolerance.
5. Check the confirmation box, inspect prepared series/diagnostics, then choose **Compare and forecast**.
6. Inspect candidate and fold scores, warnings and the forecast or an explicit explanation of why forecasting is unavailable. Download forecast, comparison, validation predictions, prepared observations and run metadata as needed.

Changes to source, sheet, target or settings clear results and confirmation. Sales/purchase runs remain independent. Reset clears session state. Browser sessions are temporary; keep your original source file and user-initiated exports for reproducibility.

## Input conventions

- CSV: comma-delimited UTF-8, unique nonempty header row and consistent row widths. XLSX: explicit sheet selection, unique header row, values only. Legacy XLS, encrypted files, macros, external links and formula cells are rejected. Convert XLS to XLSX and paste spreadsheet formulas as values in a copy first.
- Dates: ISO dates/datetimes without timezone offsets, or explicit `day/month/year` / `month/day/year`. Numeric Excel serial codes and mixed timezone conventions are unsupported. Use actual Excel date cells or date strings.
- Numbers: `plain`, `comma thousands` (e.g. `$1,234.50`, `(25.00)`), or `decimal comma` (e.g. `1.234,50`). Parentheses denote negatives in the formatted modes. Valid zero/refund observations remain unchanged. Individual monetary magnitudes above 1e15 are rejected.
- Cadence: daily (`D`), weeks labeled by Monday/Sunday end (`W-MON`, `W-SUN`), month start/end (`MS`, `ME`). A horizon of 12 means 12 periods of that cadence. Seasonal period is samples per repeating cycle; do not assume every cadence is seasonal.
- Transactions: all legitimate rows are retained, including equal date/amount rows; sum or mean is explicit. Transaction IDs are not automatically deduplicated. Confirm reporting completeness, especially the last period; incomplete months are not automatically detected/dropped.
- Summaries: labels must already align with the selected cadence; no hidden reaggregation. Repeated summary dates require explicit sum/mean or rejection.
- Gaps: unknown by default. Confirmed zero activity is an explicit business choice. Training-only forward fill is causal, bounded to three periods, and cannot fill leading gaps or validation truth. Excluded invalid monetary targets retain unknown periods; they cannot become zero-valued validation truth. Invalid dates/values block by default; explicit exclusions are counted and cautioned.

## Models and quality policy

Candidates: last-value naive, seasonal naive, simple exponential smoothing, Holt, additive Holt-Winters, and bounded ARIMA(p,d,q). Seasonal candidates require at least two training seasons; Holt/ARIMA require 12 training observations, and all candidates require at least four. Ineligible/failed candidates stay visible. Convergence failures exclude a candidate; other captured warning categories remain visible. There is no uncontrolled parameter search or multiplicative model in this version.

Evaluation uses fixed nonoverlapping validation windows at the end of history with expanding training windows, never shuffled observations. All candidates use identical windows. Error is `actual - prediction`; pooled **MAE** or **RMSE** ranks candidates, with both metrics and fold details shown. The default primary metric is MAE. Ties resolve by candidate name. MASE, sMAPE and a separate final-test UI stage are not implemented.

A selected method must match or improve the Naive reference on the primary metric **and** pass `validation error / mean absolute level of first training window <= tolerance`. Default tolerance is **0.5**, user editable. Zero training scale passes only with effectively zero error. Baselines may be selected when explicitly allowed. This is a transparent exploratory gate, **not a universally meaningful business error threshold or proof of future reliability**. Choose a tolerance appropriate to the target's business meaning. Weak/all-failed/insufficient/ambiguous inputs yield explained no-forecast states rather than a fabricated prediction.

After selection the engine refits on all usable history. Only ARIMA currently supplies 95% model-based prediction intervals through `get_forecast`; other methods return points with a visible limitation. Negative predictions are retained. Forecasts and interval coverage depend on assumptions and are not guarantees. Full-history exploration is descriptive, not evidence available to past validation folds.

## Data, resource limits and exports

No database, accounts, automatic disk retention, cloud inference or automatic business decisions. Uploads/results are in memory; downloads are user-initiated. Logs contain run IDs, stage durations and safe error categories, not raw business values. Do not use this local prototype as a hosted multi-tenant service without reviewing isolation, access and retention.

Enforced limits: 10 MiB file bytes, 50,000 input rows, 100 columns, 20 sheets, 50 MiB expanded XLSX archive, 2,000 ZIP members, 50,000 prepared periods, six candidates, five folds, 365 future/validation steps and seasonal period up to 365. ARIMA p/q range 0–3; d range 0–2; optimizer iterations bounded to 100. These are policy caps, not guarantees of fast fits. Execution is synchronous with no hard cancellation/timeout; expensive allowed configurations can take time. Excel decompression/XML and row limits reduce risk but are not an adversarial parser-security certification.

Forecast CSV uses dated numeric predictions and optional interval columns. Comparison and validation CSV preserve candidate outcomes; JSON records effective mapping, policies, split dates, metric definitions, configurations and package versions. CSV untrusted text fields are formula-escaped; numeric signs are preserved. Metadata can contain intended business predictions when explicitly downloaded. Fingerprints identify sources but do not reconstruct them.

## Engine use and checks

```python
from forecasting_app.contracts import ForecastRequest
from forecasting_app.ingestion import read_upload
from forecasting_app.service import forecast

with open("sample_data/monthly_transactions.csv", "rb") as source:
    upload = read_upload(source.read(), "monthly_transactions.csv")
response = forecast(
    ForecastRequest(
        upload,
        "Date",
        "Sales",
        confirmed=True,
        row_kind="transactions",
        aggregation="sum",
        frequency="MS",
        horizon=12,
        validation_periods=12,
        seasonal_period=12,
    )
)
print(response.status, response.selected_model)
```

```sh
venv/bin/python -m pytest -q
venv/bin/ruff check .
venv/bin/ruff format --check .
venv/bin/python -m pip check
venv/bin/python scripts/benchmark.py
venv/bin/python -m build --wheel --no-isolation
```

50 automated tests cover readers, detection, preparation, date boundaries, chronological leakage, finite intervals, target isolation, quality/refit/all-model failure, export parity, deterministic ARIMA/smoothing winner cases and Streamlit flow/invalidation. See [VERIFICATION.md](VERIFICATION.md) for actual checks and limits of verification. No fresh separate environment was created: package work uses the supplied venv.

## Architecture and implementation context

See [DEVELOPMENT_PLAN.md](DEVELOPMENT_PLAN.md), [AGENTS.md](AGENTS.md), and the architecture PDF in this folder. Engine modules under `src/forecasting_app/` do not import Streamlit; `app.py` collects choices and displays engine responses. `sample_data/README.md` explains synthetic demos. Changes and upgrades should rerun regressions, update the lockfile and record decisions/evidence in the plan. Use Git plus the previous verified lockfile for rollback; do not retain private uploads in a commit.

Implementation APIs: [statsmodels ARIMA](https://www.statsmodels.org/stable/generated/statsmodels.tsa.arima.model.ARIMA.html), [exponential smoothing](https://www.statsmodels.org/stable/generated/statsmodels.tsa.holtwinters.ExponentialSmoothing.html), and [Streamlit AppTest](https://docs.streamlit.io/develop/api-reference/app-testing/st.testing.v1.apptest).
