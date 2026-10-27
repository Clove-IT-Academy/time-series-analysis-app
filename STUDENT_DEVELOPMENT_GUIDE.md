# Building Business Forecast Studio

## A student guide to understanding, explaining, and rebuilding the application

**Application:** Business Sales & Purchase Forecasting System  
**Code package:** `forecasting_app`  
**Guide prepared:** 27 October 2026  
**Audience:** Students who know basic Python and want to build an end-to-end forecasting application.

This guide explains the implementation in this repository: its business problem, architecture, important code paths, statistical methods, tests, and development sequence. The goal is to help you reproduce the design through understanding rather than copy files without knowing why they exist.

The actual system architecture is `Business_Sales_Purchase_Forecasting_System_Architecture.pdf`. `DEVELOPMENT_PLAN.md` records the implementation plan and decisions. This guide is a teaching companion to those documents and to the source code, not a replacement specification.

Code excerpts labeled **repository excerpt** are taken from the implementation, sometimes with surrounding code omitted. Blocks labeled **learning example** are small teaching programs or simplified reconstructions. Do not replace a production module with an abbreviated example that omits its validation.

The guide is self-contained enough to read as a PDF. Filenames are printed as code so their meaning remains clear if links are lost during conversion. Long programs stay in the repository; selected excerpts explain the decisions and operations students need to reconstruct them.

## Contents

1. What you are building
2. Prerequisites and a productive study method
3. Run the existing application and observe it
4. Architecture and repository map
5. Trace one complete request
6. Python techniques used throughout the project
7. Contracts: agreeing on data at boundaries
8. Configuration and environment
9. Ingestion: turning files into a validated table
10. Detection: suggesting columns without guessing business meaning
11. Preparation: turning records into a trustworthy series
12. Analysis: describing history without overstating it
13. Baselines and forecasting concepts
14. Statistical model adapters and the shared prediction contract
15. Chronological evaluation and metrics
16. Selection, adequacy, and abstention
17. Orchestration: assembling the workflow
18. Streamlit: keeping the interface thin and state correct
19. Exports, privacy, and reproducibility
20. Tests as executable explanations
21. Build the app yourself in seven stages
22. Guided experiments and expected observations
23. Debugging and common misconceptions
24. Independent assessment and extension projects
25. Glossary and PDF preparation notes

# 1. What you are building

Business Forecast Studio is a local web application. A user supplies business history, chooses either sales or purchases, confirms what the records mean, compares forecasting methods on later historical observations, and requests future values.

The application performs six jobs:

1. **Read:** accept a supported CSV or Excel worksheet.
2. **Interpret:** suggest date and target columns and ask the user to confirm their meaning.
3. **Prepare:** produce a regular time series using explicit business rules.
4. **Evaluate:** compare eligible methods using past-only training and later validation.
5. **Decide:** select an acceptable candidate or explain why forecasting should stop.
6. **Explain:** show forecasts, scores, assumptions, warnings, and downloadable results.

A forecast is an estimate based on historical patterns. It is not an automatic purchasing instruction, a causal explanation, or a promise of future sales.

## 1.1 A small business example

Suppose an uploaded table contains these rows:

| Date | Sales | Purchases |
| --- | ---: | ---: |
| 2025-01-05 | 100 | 60 |
| 2025-01-18 | 150 | 90 |
| 2025-02-04 | 200 | 120 |

If each row is a transaction and the user chooses monthly sales with **sum** aggregation, January sales become 250 and February sales become 200.

If the user chooses **mean**, January becomes 125. That is a different measure: average transaction amount rather than total sales.

Both calculations are mathematically valid. Only one may answer the intended business question. This is why preparation choices belong in the product, not in invisible defaults.

This two-month example explains aggregation only. It is not enough history to demonstrate meaningful model comparison.

## 1.2 Scope of the implemented application

The current version supports one uploaded dataset and one target per run. A file may contain both sales and purchases, but they are forecast separately. It runs locally in a Streamlit process and stores session data in memory by default.

Implemented model candidates are:

- Last-value naive.
- Seasonal naive.
- Simple exponential smoothing.
- Holt's additive trend method.
- Additive Holt-Winters.
- ARIMA with a bounded user-selected order.

It does not implement accounts, a database, automatic transaction-ID deduplication, deep learning, external-data predictors, automatic hyperparameter search, or production multi-tenant hosting.

**Learning checkpoint:** Explain why this project is more than a script that calls `model.fit()`.

# 2. Prerequisites and a productive study method

## 2.1 Skills to learn first

| Skill | Where you will use it |
| --- | --- |
| Functions, loops, conditionals | Every workflow stage |
| Lists, dictionaries, tuples | Settings, metadata, predictions and diagnostics |
| Classes and dataclasses | Requests, results and shared contracts |
| Exceptions and `try`/`except` | Controlled invalid-input and failure paths |
| Modules and imports | Separating engine, models and interface |
| File bytes and text encoding | CSV and Excel reading |
| pandas DataFrame and Series | Tables, date indexes, grouping and time series |
| NumPy arrays | Predictions, finite-value checks and metrics |
| Basic statistics | Means, errors, variability and correlation |
| pytest | Verifying behavior before adding complexity |

You do not need to derive every statistical estimator before starting. You must understand what information a model receives, what it returns, and how its predictions are evaluated.

## 2.2 Use three passes through the project

**Pass 1: behavior.** Use the app, trace a request and describe expected outcomes in plain language. Read Chapters 1–5 and the tests relevant to the behavior you observe.

**Pass 2: implementation.** Read Chapters 6–20 beside the named source files. For each function, write down its inputs, outputs, decisions, mutations and failure conditions.

**Pass 3: reconstruction.** Follow Chapter 21 in a separate exercise folder or branch. Implement a small piece yourself, write an example that proves it works, then compare your design with the repository.

For every study session, use this loop:

1. Predict what a function should do with a tiny example.
2. Calculate the answer by hand where possible.
3. Read or run the function.
4. Explain any difference between expectation and result.
5. Recreate the core behavior without looking at the implementation.
6. Test one successful case and one boundary/failure case.

Do not begin by memorizing `app.py`. Its widgets make more sense after you understand the engine they call.

## 2.3 Keep a learning notebook

For each module, record five answers:

- What responsibility does this module own?
- What must already be true before it runs?
- What does it guarantee on success?
- How does it communicate uncertainty or failure?
- Which test demonstrates that guarantee?

If you cannot answer these, reread the relevant function before adding another feature.

# 3. Run the existing application and observe it

The project already has a virtual environment named `venv`. Use it instead of installing packages into the system Python.

From the application directory:

```sh
venv/bin/python -m streamlit run app.py
```

Open `http://127.0.0.1:8501` in a browser. Stop the server with **Ctrl+C** in its terminal when finished.

The following commands are for reproducing dependencies if required; an already configured environment does not need reinstalling on every study session:

```sh
venv/bin/python -m pip install -r requirements.lock
venv/bin/python -m pip install --no-build-isolation --no-deps -e .
```

Here, `-m` runs a module using the selected Python interpreter. `pip install -e .` installs the local package in editable mode: imports resolve to the working source, so edits do not require reinstalling the package every time. `--no-deps` avoids resolving dependencies again after the lockfile installation.

`pyproject.toml` declares Python 3.12–3.14 compatibility constraints, but the recorded verification used Python 3.14.7 on macOS arm64. A declared version range is not proof that every platform/version combination was tested.

## 3.1 First observation exercise

Use **Monthly transactions** and keep the default monthly settings:

- Business target: sales.
- Date column: Date.
- Target column: Sales.
- Row meaning: transactions.
- Aggregation: sum.
- Frequency: MS, meaning month-start labels.
- Seasonal period: 12 samples.
- Validation periods: 12.
- Future horizon: 12.

Confirm the settings, inspect the prepared chart, then run the comparison. Record the selected method, validation score, warnings and number of forecast rows. Do not assume a particular winner before inspecting the actual response.

Next change the target to purchases. The old result and confirmation should disappear. Correct state invalidation is part of correctness, not merely an interface preference.

Use **Short history** to observe a supported no-forecast path. Use **Ambiguous fields** to inspect how numeric-looking columns can remain semantically unclear.

## 3.2 Verification commands

```sh
venv/bin/python -m pytest -q
venv/bin/ruff check .
venv/bin/ruff format --check .
venv/bin/python -m pip check
```

The historical verification record reports 50 passing tests on 16 October 2026. Treat `VERIFICATION.md` as dated evidence; the result of your own test run is the evidence for your current environment. Reading this guide does not automatically rerun those checks or start the server.

# 4. Architecture and repository map

The project is a **modular monolith**: one application with clear internal boundaries. It does not need a separate frontend server, database server or model-serving service for the teaching scope.

```text
                        USER
                          |
                          v
               app.py / Streamlit
          controls, confirmation, display
                          |
                          v
                 service.forecast()
            sequencing and outcome decisions
                          |
          +---------------+----------------+
          |               |                |
     preprocessing     analysis         evaluation
          |                                |
          |                           models/*
          |                                |
          +---------------+----------------+
                          |
                          v
                 ForecastResponse
          status + evidence + future rows
                          |
                    UI and exports
```

Before a forecast request, `app.py` also calls ingestion and detection helpers to preview the upload and collect user choices. The orchestration function remains the boundary for performing the forecast workflow.

## 4.1 Files and their responsibilities

Paths in this guide are relative to `time-series-analysis-app/`.

| File or directory | Responsibility |
| --- | --- |
| `app.py` | Streamlit controls, session lifecycle, charts and downloads |
| `src/forecasting_app/contracts.py` | Shared dataclasses and controlled exceptions |
| `src/forecasting_app/config.py` | Resource limits, frequencies and candidate names |
| `src/forecasting_app/ingestion.py` | CSV/XLSX validation, sheet listing and table reading |
| `src/forecasting_app/detection.py` | Ranked column suggestions and evidence |
| `src/forecasting_app/preprocessing.py` | Parsing, business semantics, aggregation, gaps and training-only fill |
| `src/forecasting_app/analysis.py` | Descriptive series diagnostics |
| `src/forecasting_app/models/base.py` | Shared prediction interface, eligibility and output checks |
| `src/forecasting_app/models/baselines.py` | Naive reference predictions |
| `src/forecasting_app/models/arima.py` | statsmodels ARIMA adapter |
| `src/forecasting_app/models/exponential_smoothing.py` | Smoothing adapters |
| `src/forecasting_app/evaluation.py` | Fold construction, metrics, comparison and initial selection |
| `src/forecasting_app/service.py` | Request validation, adequacy, refit and response assembly |
| `src/forecasting_app/exports.py` | Plain CSV and metadata serialization |
| `tests/` | Unit, integration and Streamlit behavior checks |
| `sample_data/` | Synthetic inputs, including a multi-sheet workbook |
| `scripts/benchmark.py` | Synthetic parsing/engine timing and allocation measurements |
| `pyproject.toml` | Package/build metadata and development-tool settings |
| `requirements.lock` | Exact recorded dependency versions |
| `.streamlit/config.toml` | Local server, theme and telemetry settings |

## 4.2 Why keep the engine independent of Streamlit?

A function that accepts a typed request and returns a result can run in a test or a Python script. It can later be called by another interface without rewriting business rules.

If the UI decided how to fill gaps while the engine decided how to aggregate transactions, you would need the browser to understand the complete preparation behavior. The same dataset could then produce different results through different entry points.

The current design puts forecasting and preparation rules in the engine. The UI gathers choices and shows the returned evidence.

**Exercise:** Identify a function you can call without opening a browser. Explain which user choices it still needs.

# 5. Trace one complete request

The following **learning example** is a complete script when saved in the project root and run with the existing venv. It uses the engine without starting Streamlit.

```python
from pathlib import Path

from forecasting_app.contracts import ForecastRequest
from forecasting_app.ingestion import read_upload
from forecasting_app.service import forecast

source = Path("sample_data/monthly_transactions.csv")
upload = read_upload(source.read_bytes(), source.name)

request = ForecastRequest(
    upload=upload,
    date_column="Date",
    target_column="Sales",
    target="sales",
    confirmed=True,
    row_kind="transactions",
    aggregation="sum",
    frequency="MS",
    horizon=12,
    validation_periods=12,
    folds=1,
    seasonal_period=12,
)

response = forecast(request)
print(response.status)
print(response.message)
print(response.selected_model)
print(response.forecast_rows[:2])
```

The example sets `confirmed=True` because the author explicitly chose and understood those synthetic fields. In a user-facing flow, do not mark arbitrary uploads confirmed without reviewing their meaning.

## 5.1 What happens at each boundary?

1. `Path.read_bytes()` loads file content. `read_upload()` checks the supported format and limits and creates an `UploadResult`.
2. `ForecastRequest` names the intended columns, business target and policies. It is a record of choices, not a fitted model.
3. `forecast()` builds run metadata and validates the request.
4. `prepare()` parses the selected columns, aggregates transactions and constructs a regular date index.
5. `describe()` adds descriptive diagnostics.
6. `evaluate()` creates chronological folds and evaluates each eligible candidate.
7. `select()` ranks completed candidates and checks their comparison with Naive.
8. The service applies the separate relative-error tolerance.
9. If accepted, the selected configuration is fitted again using all usable history.
10. The service creates exactly the requested number of future dates and predictions and returns a `ForecastResponse`.

An early failure returns a distinct outcome and message. A model is not fitted merely because the user supplied a valid CSV.

## 5.2 Trace the bundled example numerically

The monthly transaction sample has 168 rows: two transactions per month across 84 months. Monthly sum aggregation produces 84 observations.

With one 12-period validation fold:

```text
84 monthly observations
|---------- first 72 months ----------|-- last 12 months --|
             training                      validation
```

After selection, the accepted configuration is refitted on all 84 months. Only then are 12 new future months forecast.

The validation predictions and future predictions come from different fitted instances with different training ranges. You must not label the future refit's in-sample behavior as its original validation score.

# 6. Python techniques used throughout the project

## 6.1 Dataclasses

A dataclass defines named fields and generates routine initialization behavior. It makes a result clearer than a long positional tuple.

Instead of asking “is element 4 the warnings list or the forecast?”, you access `response.warnings` and `response.forecast_rows`.

## 6.2 Type annotations

`list[dict[str, float]]` describes a list of dictionaries with string keys and float values. `SeriesData | None` means a prepared series may be absent.

Annotations communicate contracts and help tools, but ordinary dataclasses do not automatically enforce every annotation at runtime. That is why `validate()` and boundary checks still exist.

## 6.3 Mutable defaults

**Repository excerpt — `contracts.py`:**

```python
warnings: list[str] = field(default_factory=list)
```

`default_factory=list` creates a new list for each object. It avoids different results accidentally sharing one mutable warnings list.

`ForecastRequest` uses `@dataclass(frozen=True)`. This prevents reassigning its fields, but it does not make the nested uploaded DataFrame deeply immutable. Respect the contract and avoid mutating a request's source table.

## 6.4 NumPy and pandas

A DataFrame holds several named columns. A Series represents one column of values with an index. For modeling, the useful representation is a numeric Series with a regular DatetimeIndex.

`series.iloc[:end]` slices by integer position. `series.loc[dates]` selects by index labels. Mixing these up can move a forecast onto the wrong observations while still producing plausible-looking numbers.

`np.isfinite()` checks both missing/non-numeric numerical representations and infinities. Finite outputs are a requirement, not proof of good forecasts.

## 6.5 Exceptions and returned statuses

Internal preparation can raise `ConfirmationRequired` or `InputError`. The service converts expected failures into response statuses and safe messages.

Candidate failures are handled inside evaluation so that one failed ARIMA fit does not discard a successful baseline. Unexpected errors are sanitized instead of exposing uploaded business values through raw library exceptions.

**Learning checkpoint:** Distinguish a raised exception, a candidate's `status`, and the overall response's `status`.

# 7. Contracts: agreeing on data at boundaries

Read `contracts.py` before reading model code.

| Object | What it carries | Why it exists |
| --- | --- | --- |
| `UploadResult` | Table, source name, fingerprint, sheet and parse warnings | Separates file reading from interpretation |
| `ColumnCandidate` | Column, role, confidence, evidence and alternatives | Makes a suggestion inspectable |
| `ForecastRequest` | User choices, data, model/evaluation settings | Makes the run explicit and repeatable |
| `SeriesData` | Target, cadence, indexed values, aggregation, gaps and diagnostics | Preserves preparation context |
| `EvaluationResult` | Candidate config, status, fold scores, aggregate scores, warnings and predictions | Preserves success and failure evidence |
| `ForecastResponse` | Overall status, message, selected model, future rows, comparison, diagnostics and run config | Gives UI and exports one consistent result |

`UploadResult` does not contain a separate `row_count` field in this implementation; code obtains the count from `len(upload.table)`. Learn the actual object, not only its conceptual architecture description.

## 7.1 Request fields worth distinguishing

- `target` is the business role: sales or purchases.
- `target_column` is the actual uploaded column used for that role.
- `frequency` determines dates and the units of a forecast step.
- `seasonal_period` is the number of samples in a repeating pattern.
- `horizon` is how many future steps to return.
- `validation_periods` is how many held-out steps to predict per historical fold.
- `folds` is how many expanding-window comparisons to run.
- `max_relative_error` is a user-chosen adequacy tolerance, not a model parameter.

Changing `horizon` does not change `validation_periods` automatically. They are separate settings in the current code. For a real use case, choose evaluation windows that represent the forecast task you care about.

## 7.2 Response outcomes

| Status used by the service | Meaning |
| --- | --- |
| `needs_confirmation` | Required semantic choices or preparation policies remain unresolved |
| `invalid_input` | Unsupported configuration, invalid values or unusable validation truth |
| `insufficient_history` | Too few periods remain before the requested validation windows |
| `no_eligible_model` | No candidate completed the evaluation successfully; can include all-fit-failure situations |
| `no_reliable_forecast` | Candidates ran, but baseline/quality requirements were not satisfied |
| `refit_failed` | Selected configuration could not safely refit on full history |
| `engine_error` | An unexpected engine failure was caught and sanitized |
| `success_with_cautions` | Future values were produced with explicit limitations |

The current successful path deliberately uses `success_with_cautions`; do not expect a separate unconditional `success` outcome from it. Status names should be read with messages and candidate evidence, especially because the current `no_eligible_model` path groups ineligibility and total fit failure.

# 8. Configuration and environment

`config.py` centralizes several limits and supported names. `service.validate()` also enforces request-specific bounds. Not every number is currently stored in one configuration class.

**Repository excerpt — `config.py`:**

```python
MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 100
FREQUENCIES = ("D", "W-MON", "W-SUN", "MS", "ME")
```

`1024 * 1024` makes this a 10 MiB byte limit. Python permits underscores in number literals for readability: `50_000` is 50000.

Other limits include 20 sheets, 50 MiB expanded XLSX content, 2,000 archive members, 50,000 prepared periods, six candidates, five folds, and 365-step bounds for horizon/validation and seasonal period. ARIMA p/q are bounded to 0–3 and d to 0–2.

These caps control possible work. They do not guarantee every allowed combination finishes quickly. A maximum iteration setting is not a wall-clock timeout.

## 8.1 Why `src/` and editable installation?

The package lives under `src/forecasting_app/`, while the UI is at the project root. Editable installation makes the package importable through its normal name. The tests also configure the `src` path in `pyproject.toml`.

`pyproject.toml` declares dependencies and version ranges. `requirements.lock` records exact installed versions. The lockfile helps reproduce the tested environment; it does not establish compatibility on untested platforms.

The built wheel contains the engine package. The application also needs root `app.py` and the sample files, so a wheel alone is not the complete Streamlit user experience.

**Exercise:** Explain the difference between “a package can be imported” and “the app can be launched with its bundled examples.”

# 9. Ingestion: turning files into a validated table

Read `ingestion.py` in this order: `_check()`, `_workbook()`, `list_sheets()`, `read_upload()`.

## 9.1 `_check()` — reject unsupported envelopes early

The function checks that bytes are nonempty and within the file limit, then accepts only `.csv` and `.xlsx` suffixes. Legacy `.xls` is intentionally unsupported. A filename is a hint, not proof that content is valid; the appropriate parser still has to read it successfully.

## 9.2 CSV reading

The reader decodes UTF-8 with optional byte-order mark using `utf-8-sig`, then uses `csv.reader(..., strict=True)`.

Important checks include:

- A header row must exist.
- Rows must have the expected number of fields.
- Column names must be nonempty and unique after trimming.
- Row/column limits are checked during iteration before building the full DataFrame.

The application does not guess every possible delimiter or encoding. A clear supported format is easier to explain and test than silently accepting different interpretations.

## 9.3 Excel reading

XLSX is a ZIP container. `_workbook()` first checks archive size/member limits and rejects named macro/external-link content. It uses read-only openpyxl loading and closes workbooks in `finally` blocks.

**Repository excerpt — workbook opening:**

```python
book = load_workbook(
    io.BytesIO(data),
    read_only=True,
    data_only=False,
    keep_links=False,
)
```

The source places this call on one line; the line wrapping here is for readability. `data_only=False` allows formula cells to be identified. `read_upload()` rejects formula headers and formula cells rather than evaluating them or trusting cached results. The user must paste values into a copy first.

`list_sheets()` lets the interface ask which sheet to use. `read_upload()` requires an explicit sheet for a multi-sheet workbook. It does not concatenate sheets with possibly different business meaning.

These safeguards reduce resource and interpretation risks; they are not a claim of complete protection against every malicious workbook.

## 9.4 Fingerprints and source identity

**Repository excerpt:**

```python
hashlib.sha256(data).hexdigest()
```

This produces a stable content fingerprint. Identical bytes produce the same digest, which is useful for identifying an input and deciding whether state is stale.

A hash is not encryption and does not store a reversible copy of the source. Keep the original data if you need to reproduce the analysis.

**Build exercise:** Implement CSV reading first. Test empty bytes, duplicate headers, unequal row widths and an oversized row count before adding Excel.

# 10. Detection: suggesting columns without guessing business meaning

`detection.py` returns suggestions; it does not determine business truth.

## 10.1 What `detect_columns()` does

For each role—date, sales, purchases—it examines every column:

1. Normalize the name to lowercase words.
2. Take up to 200 nonmissing sample values.
3. Check configured name terminology.
4. Estimate date or numeric coverage.
5. Combine name and coverage evidence into a score.
6. Sort candidates and attach alternatives.

**Repository excerpt — scoring:**

```python
score = min(1.0, (0.6 if lexical else 0.0) + 0.4 * coverage)
```

Suppose `Sales` has numeric coverage 1.0 and a matching name. Its score is 1.0. Suppose `Amount` is fully numeric but its name does not match the sales synonyms. Its score is 0.4.

Neither number is a calibrated probability. A score of 1.0 does not mean the business meaning is certain.

The present detector uses names and sampled parseability/type checks. The broader architecture discusses richer surrounding context and value evidence, but this implementation does not contain a semantic language model or an advanced contextual classifier.

## 10.2 Date evidence

The detector avoids parsing purely numeric identifiers as epoch dates. It uses datetime dtype evidence or date-like string patterns plus parsing coverage.

Detection uses permissive sampling to propose a role. Preparation later parses the selected full column under the explicit date convention. A plausible detection score does not mean every row will pass final validation.

Likewise, detection's numeric sampling removes common formatting characters, while preparation uses the user's stricter numeric convention. The two stages answer different questions: “is this a plausible field?” and “can this selected field be interpreted under these rules?”

## 10.3 `requires_confirmation()`

It flags a suggestion when the best score is below 0.70 or within 0.12 of the next candidate. This helps the UI show ambiguity.

The app still requires the overall confirmation checkbox even for high scores. The service checks `request.confirmed`; it does not silently choose columns itself.

**Exercise:** Create columns `Amount` and `Value`, both numeric. Explain why more numeric rows cannot resolve whether they mean sales, purchase cost or something else.

# 11. Preparation: turning records into a trustworthy series

`preprocessing.py` is where business semantics become modeling data. Study it carefully: a perfectly fitted model cannot repair a target that was prepared with the wrong meaning.

## 11.1 Parsing numbers

`parse_numbers()` supports three conventions:

| Convention | Example | Parsed meaning |
| --- | --- | ---: |
| plain | `1234.50` | 1234.50 |
| comma thousands | `$1,234.50` | 1234.50 |
| comma thousands | `(25.00)` | -25.00 |
| decimal comma | `1.234,50` | 1234.50 |

The formatted modes strip supported symbols and validate grouping patterns before conversion. The plain mode does not silently remove commas and currency symbols.

`errors="coerce"` converts parsing failures to missing values so the engine can count and handle them. It does not mean failed values are accepted as valid zeros.

## 11.2 Parsing dates

`parse_dates()` accepts ISO parsing or the explicitly selected day/month/year or month/day/year format. It rejects unsupported timezone-bearing values rather than silently removing timezone information. Numeric date-code dtypes are unsupported.

A string such as `03/04/2025` is ambiguous without a convention. It could mean 3 April or March 4. Both interpretations can produce valid dates, so parser success alone cannot settle the intended meaning.

## 11.3 `prepare()` in logical blocks

Read the function as a sequence rather than one long operation:

1. Validate selected columns, cadence and policies.
2. Parse dates and numbers.
3. Count invalid records and apply the reject/exclude choice.
4. Preserve known dates whose target values are invalid.
5. Sort records and bound the possible calendar span.
6. Apply transaction or summary semantics.
7. Construct a complete regular grid.
8. Mark unknown/invalid target periods and apply the chosen gap policy.
9. Return `SeriesData` with diagnostics and provenance.

The current magnitude policy rejects individual monetary values with absolute magnitude above `1e15`. This is a prototype bound, not a financial modeling law.

## 11.4 Transactions and summaries take different branches

For transactions, the selected amount is indexed by date and resampled to the chosen frequency.

**Repository excerpt:**

```python
grouped = raw.resample(request.frequency)
series = grouped.sum(min_count=1) if request.aggregation == "sum" else grouped.mean()
```

`min_count=1` matters: a bin with no valid observations should remain unknown instead of becoming zero merely because summation was requested.

For summaries, the code checks that labels align with the requested cadence. It handles repeated summary dates only under the explicitly chosen reject/sum/mean rule. It does not silently aggregate arbitrary summary labels into different calendar periods.

Two identical transaction rows are retained because they may be two genuine sales. This version does not automatically deduplicate transaction IDs. Summary duplicate policy and transaction identity are separate problems.

## 11.5 Regular frequency and anchors

| Alias | Meaning |
| --- | --- |
| D | Daily |
| W-MON | Weekly bins labeled by Monday week-end |
| W-SUN | Weekly bins labeled by Sunday week-end |
| MS | Monthly bins labeled at month start |
| ME | Monthly bins labeled at month end |

A transaction on 18 January can belong to a January bin labeled 1 January under MS. The label is the period's index convention, not a claim that the transaction happened on the first day.

For summaries, the labels must already use the chosen anchor. A month-end summary should not be silently interpreted as a month-start observation.

## 11.6 Missing periods are not all the same

Consider January = 10 and March = 30, with February absent.

| Policy | February result | Interpretation |
| --- | --- | --- |
| unresolved | Stop for confirmation | Reporting meaning is unknown |
| zero activity | 0, only if that meaning is explicitly confirmed | No business activity occurred |
| forward fill training | Keep unknown in the canonical series; fill only an appropriate training slice later | A documented modeling assumption, not observed truth |

An invalid monetary value is more serious than a wholly absent period. Suppose February has a known row with target `invalid`. Excluding that value does not prove that February activity was zero. The code keeps the period unknown even if the general absent-period policy is zero activity.

This also protects a period that contains some valid transactions and an invalid one: a partial total is not automatically accepted as complete observed truth.

## 11.7 Causal, bounded training fill

**Repository excerpt — `training_values()`:**

```python
clean = series.ffill(limit=3) if policy == "forward fill training" else series.copy()
if not np.isfinite(clean).all():
    raise InputError(
        "Training history has unresolved gaps (fill limit: 3 periods); repair source data."
    )
return clean
```

`ffill()` uses the most recent earlier value. It does not look ahead. `limit=3` permits at most three consecutive missing entries after a known value. Leading gaps remain unresolved.

Evaluation calls this function separately on each training slice. It never applies it to validation truth. The final refit may use all then-available history, but its previous validation scores retain their original fold provenance.

## 11.8 Why preparation before evaluation is not automatically leakage

The current code parses and bins records before making period-level folds. Parsing conventions and confirmed aggregation rules are deterministic choices, not statistics fitted from future values. Folds cut between the resulting periods, and learned/causal training handling occurs inside each training slice.

If you add learned outlier thresholds, scaling, interpolation, decomposition-driven feature selection or automatic period choice, do not fit those on full history and then reuse them inside earlier folds. Each new transformation needs its own information-availability analysis.

The app assumes transaction reporting periods are complete, including the last period. It warns about this; it does not automatically identify an unfinished month. This is an important limitation to understand before trusting results.

**Learning checkpoint:** Explain why “drop bad rows, fill all NaNs with zero, then fit” can create incorrect validation truth.

# 12. Analysis: describing history without overstating it

`analysis.describe()` returns preparation diagnostics plus:

- Mean.
- Sample standard deviation when enough values exist.
- Linear trend slope per period.
- Correlation with a chosen seasonal lag when sufficient data exists.

**Repository excerpt — trend calculation:**

```python
positions = np.flatnonzero(series.values.notna().to_numpy())
slope = float(np.polyfit(positions, values.to_numpy(), 1)[0]) if len(values) > 1 else 0.0
```

`np.polyfit(x, y, 1)` fits a straight line; coefficient 0 is its slope. With monthly data, the reported slope has target units per month-period. Keeping original nonmissing positions avoids pretending that a removed gap eliminated elapsed time for this slope calculation.

The seasonal diagnostic uses lag correlation. A high correlation can arise from trend as well as seasonality. The implementation labels it descriptive, not proof. It does not automatically select the seasonal period, establish causality, or perform full seasonal decomposition.

The analysis currently drops missing values for its lag-correlation calculation, which can compress gaps. Treat that number cautiously on gappy series. A useful advanced improvement is to preserve calendar-lag alignment rather than compare compressed positions.

Candidate eligibility lives in `models/base.py`; `analysis.py` does not independently decide which model wins. The broader architecture's diagnostics goals should not be mistaken for a complex stationarity or seasonality-testing system already present in this prototype.

**Exercise:** Describe a steadily increasing series that could have high lag-12 correlation even without an annual repeating pattern.

# 13. Baselines and forecasting concepts

## 13.1 Notation

Let `y_t` be the observed target at time t. Let `y_hat_(t+h)` be a forecast made for h periods ahead. Training history contains observations available before the forecast origin.

A univariate model uses one target's history. This app does not use purchases as a predictor of sales or vice versa.

## 13.2 Last-value naive

Predict the last observed training value at every future step.

Training values: `[10, 12, 15]`  
Three-step prediction: `[15, 15, 15]`

**Repository excerpt:**

```python
np.repeat(train.iloc[-1], steps)
```

This is simple, explainable and surprisingly useful as a reference. Without it, you cannot tell whether a more complex model added value.

## 13.3 Seasonal naive

Repeat the latest complete seasonal cycle in its existing order.

Training values: `[10, 20, 30, 40, 11, 21, 31, 41]`  
Season length: 4  
Six-step prediction: `[11, 21, 31, 41, 11, 21]`

**Repository excerpt:**

```python
np.resize(train.iloc[-season:].to_numpy(), steps)
```

`np.resize()` repeats the one-dimensional cycle here. It does not fit a seasonal parameter or identify the correct cycle length.

## 13.4 Simple exponential smoothing

This method maintains a smoothed level, assigning more influence to recent values.

A common level update is:

```text
new level = alpha × latest observation
          + (1 - alpha) × previous level
```

With alpha = 0.3, previous level = 100 and latest observation = 120, the new level is 106.

Simple smoothing has no explicit trend or seasonal component. In this app, statsmodels estimates the smoothing parameters; the user does not manually supply alpha.

## 13.5 Holt's method

Holt adds a trend component to the level. A simplified forecast idea is:

```text
h-step point forecast ≈ current level + h × current trend
```

A method with trend can adapt better than a flat forecast to consistently increasing sales. It can also extrapolate an inappropriate trend, which is why held-out validation and business review still matter.

## 13.6 Holt-Winters

Holt-Winters adds a repeating seasonal component. The current adapter uses additive trend and additive seasonality.

For monthly observations with a yearly pattern, seasonal period is 12. Daily observations with a weekly pattern might use 7. Frequency tells you the sampling interval; it does not prove which pattern exists.

The app requires two complete training seasons for seasonal candidates. That is a conservative eligibility rule plus library constraints, not a guarantee of reliable estimation.

## 13.7 ARIMA(p, d, q)

- **p:** autoregressive order, relating the modeled series to past values.
- **d:** differencing order, transforming levels into changes when required.
- **q:** moving-average error order, relating the modeled series to past forecast errors.

First differencing turns `[100, 110, 125]` into `[10, 15]`. With d greater than zero, p and q concern the differenced model representation; do not explain every ARIMA as a raw-level autoregression.

The MA part is not a rolling average of observations. It refers to past errors in the statistical model.

The example default `(1, 1, 1)` is a bounded starting configuration. The app does not run an automatic grid search or guarantee those settings fit every dataset.

## 13.8 Eligibility is different from suitability

A candidate can be allowed to run and still forecast poorly.

| Candidate | Current initial history guard |
| --- | --- |
| All candidates | At least four training periods |
| Holt and ARIMA | At least 12 training periods |
| Seasonal naive and Holt-Winters | Seasonal period at least 2 and at least two complete training seasons |

Other library constraints and fit failures can still occur. These are application rules, not universal statistical minimums.

**Exercise:** Explain why comparing a candidate on later validation data is necessary even after it passes every eligibility check.

# 14. Statistical model adapters and the shared prediction contract

Read `models/base.py`, then the three adapter modules.

## 14.1 `Prediction` and `predict()`

`Prediction` carries point values, optional lower/upper bounds and warnings. The shared `predict()` function:

1. Checks eligibility.
2. Calls the selected adapter.
3. Captures warnings.
4. Rejects a statsmodels convergence warning.
5. Checks point length and finite values.
6. Checks interval length, finite values and lower/upper ordering when present.

A common contract prevents evaluation from needing different code for every model family. Future dates are assembled by the service from the confirmed cadence; adapters return numerical arrays in forecast-step order.

Because arrays do not carry their own date labels here, adapter ordering and exact length are important assumptions. A stronger future interface could preserve an explicit prediction index and verify equality with the expected index.

## 14.2 ARIMA adapter

**Repository excerpt — the main operations:**

```python
fitted = ARIMA(train, order=order).fit(method_kwargs={"maxiter": 100})
forecast = fitted.get_forecast(steps=steps)
bounds = np.asarray(forecast.conf_int(alpha=0.05)) if intervals else None
```

- `ARIMA(...)` constructs a model with the training history and configuration.
- `.fit(...)` estimates its parameters with an iteration cap.
- `.get_forecast(...)` computes predictions for the requested number of steps.
- `alpha=0.05` requests model-based 95% intervals.
- Arrays are extracted into the shared `Prediction` result.

The iteration cap limits optimizer iterations; it does not enforce a maximum number of seconds.

## 14.3 Smoothing adapter

**Repository excerpt — configuration choices:**

```python
trend="add" if name in ("Holt", "Holt-Winters") else None
seasonal="add" if name == "Holt-Winters" else None
seasonal_periods=season if name == "Holt-Winters" else None
```

These expressions are keyword-value choices inside the `ExponentialSmoothing(...)` call, shown separately for explanation.

Simple smoothing gets neither explicit trend nor seasonality. Holt gets additive trend. Holt-Winters gets additive trend and seasonality. The implementation initializes estimated states and fits with bounded optimization.

The adapter returns point forecasts only. It does not manufacture smoothing intervals to make every candidate's output look identical.

## 14.4 Warnings and failures

A non-converged fit is excluded. Other warning categories are captured and shown as safe messages. Candidate exceptions are handled by evaluation, preserving other candidates' results.

Notice that the shared module imports adapters inside `predict()`, while adapters import the `Prediction` type. Delaying those imports helps avoid an immediate circular import during module initialization. If you reorganize types, understand this dependency before moving imports to the top mechanically.

**Build exercise:** Create a fake adapter that returns too few predictions. Verify that the shared boundary rejects it before scoring.

# 15. Chronological evaluation and metrics

`evaluation.py` answers: “How well did each method predict observations that followed its training history?”

## 15.1 Why not shuffle?

Randomly distributing months can give training access to observations later than the supposed forecast date. That evaluates reconstruction with future information rather than the real forecasting task.

For time-aware validation, train on earlier history and predict a later block.

## 15.2 Fold calculation in the implementation

**Repository excerpt:**

```python
width, folds = request.validation_periods, request.folds
first = len(series) - width * folds
```

Inside each fold:

```python
end = first + fold * width
train = training_values(series.iloc[:end], request.gap_policy)
actual = series.iloc[end : end + width]
```

Suppose there are 84 periods, width = 6 and folds = 3. `first` is 66.

| Fold | Training periods, numbered from 1 | Validation periods |
| --- | --- | --- |
| 1 | 1–66 | 67–72 |
| 2 | 1–72 | 73–78 |
| 3 | 1–78 | 79–84 |

The training window expands. Later folds may legitimately use earlier validation observations because those observations are now in the past relative to the later forecast origin.

Validation blocks do not overlap in this implementation. Other rolling protocols are possible, but they must be defined explicitly.

## 15.3 Matching comparisons

Every candidate uses the same fold boundaries and truth values. A candidate must complete every fold to obtain an aggregate score for selection. A partially failed candidate can retain earlier diagnostic predictions, but its partial score is not allowed to compete as if it completed the full comparison.

Before fitting, the code rejects missing/non-finite values in the entire reserved validation region. It does not improve scores by dropping difficult observations or filling missing actuals.

## 15.4 MAE, RMSE and mean error

Define each error as:

```text
error = actual - prediction
```

For actual values `[0, 3]` and predictions `[1, 1]`:

| Observation | Actual | Prediction | Error | Absolute error | Squared error |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0 | 1 | -1 | 1 | 1 |
| 2 | 3 | 1 | 2 | 2 | 4 |

Therefore:

```text
MAE        = (1 + 2) / 2        = 1.5
RMSE       = sqrt((1 + 4) / 2)  ≈ 1.5811
Mean error = (-1 + 2) / 2       = 0.5
```

MAE and RMSE use target units. Positive mean error under this convention indicates average underprediction; negative indicates average overprediction. Opposite signed errors can cancel in mean error, so it is not the only accuracy measure.

**Repository excerpt — metric return:**

```python
return {
    "MAE": float(np.mean(abs(error))),
    "RMSE": float(np.sqrt(np.mean(error**2))),
    "Mean error": float(np.mean(error)),
}
```

The function also checks nonempty matching lengths, finite errors and safe squared-error range.

## 15.5 Pooled metrics

The implementation combines all completed validation predictions and computes aggregate metrics from the pooled errors. It also preserves fold-level scores.

Pooled RMSE is not generally the arithmetic mean of fold RMSEs. Even if fold lengths match, you should pool squared errors first and then take the square root. This is an excellent hand-calculation exercise.

The app does not implement MASE, sMAPE or a mandatory separate final-test stage. Avoid describing architecture options as existing features.

## 15.6 Validation is not final proof

Choosing a model after comparing validation scores uses that data for selection. Repeatedly changing settings after seeing scores can overfit the validation process.

For a stronger independent release assessment, reserve a separate final test when enough history exists. Do not tune on that test and continue calling it untouched. The teaching app's current UI does not enforce this extra protocol.

**Learning checkpoint:** Explain why the final full-history refit should not overwrite the original validation metrics.

# 16. Selection, adequacy, and abstention

There are two decisions: which permitted candidate ranks best, and whether its evidence passes the configured adequacy rule.

## 16.1 `select()` in `evaluation.py`

The function considers completed `success` or `warning` candidates with aggregate scores. It requires a successful Naive reference, ranks by the chosen metric and then candidate name, and respects whether baseline selection is allowed.

A selected candidate must match or improve the Naive reference within the small numerical tolerance in the code. With baselines allowed and a successful Naive run, at least the reference itself may satisfy that comparison. Therefore baseline comparison alone cannot establish useful reliability.

Warning-status candidates are currently permitted to compete, while convergence warnings are already excluded by the model boundary. Read their warnings before trusting the result.

## 16.2 Relative-error adequacy in `service.py`

The service computes:

```text
scale = mean(abs(first training window))
ratio = selected primary validation error / scale
accept only when ratio <= user tolerance
```

For a first-training absolute level of 200 and selected MAE of 30, the ratio is 0.15. A tolerance of 0.20 passes it; a tolerance of 0.10 rejects it.

This ratio is not MAPE: it does not divide each error by its individual actual value. It is not MASE: its denominator is not training naive forecast error. It is a project-specific, transparent exploratory policy.

When training scale is effectively zero, the code accepts only an effectively zero score; otherwise the ratio is undefined and forecasting is declined. The numerical threshold for “effectively zero” is `1e-12`.

The default tolerance of 0.5 is not a universal business standard. Users must choose a policy meaningful for their situation; passing it is not proof of future accuracy.

## 16.3 Why abstention is a successful product behavior

The app can return no future forecast while still returning valuable evidence:

- Mapping is unclear.
- Too little training history remains.
- No candidate completes all folds.
- No permitted method matches the reference.
- The best candidate exceeds the tolerance.
- The accepted model cannot safely refit.

Producing a number regardless of these conditions would make the interface simpler but the application less trustworthy.

**Exercise:** Invent a case where a model is best among candidates but still unacceptable. State the evidence that should appear in the response.

# 17. Orchestration: assembling the workflow

Read `service.py` after understanding its dependencies. It contains three public operations: `validate()`, `preview()`, and `forecast()`.

`validate()` enforces confirmation, supported target/cadence, table bounds, integer horizons/folds, candidate names, inclusion of Naive, ARIMA order bounds, primary metric and tolerance. A dataclass alone does not perform these checks.

`preview()` validates and prepares the series, then returns descriptive diagnostics without fitting models. This lets students review the data before committing to a comparison.

`forecast()` owns the complete analytical run:

```text
Create run metadata
Validate request
Prepare the selected target
Describe the series
Check remaining training history
Evaluate candidates
Select a permitted candidate against Naive
Apply relative-error adequacy
Refit the accepted configuration on full history
Construct future dates and forecast rows
Attach warnings and return the response
```

The nested `stage()` function logs run ID, stage name and elapsed time, and optionally calls a progress callback. A callback lets the UI display progress without importing Streamlit into the engine.

## 17.1 Constructing future dates

**Repository excerpt:**

```python
dates = pd.date_range(
    series.values.index[-1],
    periods=request.horizon + 1,
    freq=request.frequency,
)[1:]
```

The first generated date is the last observed period. Slicing `[1:]` removes it, leaving exactly the requested number of new periods. Anchored calendar generation handles month ends and leap years more correctly than adding a fixed 30-day duration.

## 17.2 Error boundaries

Preparation confirmation errors become `needs_confirmation`. Expected invalid-input errors become `invalid_input`. Candidate errors stay in comparison records. Refit errors become `refit_failed`; an older fitted model is not silently reused.

Unexpected errors are sanitized. Broad catches are defensible at an application boundary that must return a controlled response; they should not become a habit of suppressing errors in every helper. Developers still need safe diagnostics and targeted tests.

Run metadata includes effective settings, a source fingerprint, sheet, run ID, software versions, metric definitions and selection rules. This supports explanation and reproduction without automatically retaining the uploaded file.

**Exercise:** Draw the earliest return point for each overall status in Chapter 7.

# 18. Streamlit: keeping the interface thin and state correct

Read `app.py` as four screens within one rerun-based script: review/map, confirm meaning, configure comparison, and display evidence/results.

Streamlit reruns the script when widget values change. Ordinary local variables are reconstructed. `st.session_state` retains selected objects for the current session.

The app stores the parsed upload, upload identity, settings identity, confirmation and latest response. It runs models only when the comparison button is pressed, rather than on every widget interaction.

## 18.1 Identity and invalidation

Upload identity combines file bytes and worksheet choice. Settings identity includes that identity, selected columns, target, preparation rules, evaluation settings, candidates, quality policy and ARIMA parameters.

**Repository excerpt:**

```python
if st.session_state.get("settings_key") != settings_key:
    st.session_state["settings_key"] = settings_key
    st.session_state["confirm"] = False
    st.session_state.pop("response", None)
```

This prevents yesterday's sales result from appearing under today's purchase settings. Removing stale output is as important as producing correct output initially.

The current UI conservatively clears results for every effective settings change, including horizon. Evaluation width is separately configured; the conservative invalidation still prevents inconsistent displays.

## 18.2 What the interface may do

It may collect values, call ingestion/detection helpers, construct a request, call `preview()` or `forecast()`, and display the response. It should not contain a second version of aggregation, model ranking or adequacy rules.

Prefer keyword arguments when reconstructing the long `ForecastRequest` in your own exercises. The current UI uses positional construction; named arguments are easier to audit when many fields are similar.

Chart lines and tables derive from the engine response. Download buttons use that same response rather than refitting another model. Reset clears session state; this is not a durable analysis-history feature.

**Exercise:** Change the target after producing a forecast. Explain which stored objects become invalid and why confirmation must reset.

# 19. Exports, privacy, and reproducibility

`exports.py` contains pure formatting helpers. They do not fit models or automatically write business data to disk.

| Function | Output |
| --- | --- |
| `csv_bytes()` | UTF-8 CSV from rows, with defensive text escaping |
| `forecast_csv()` | Future forecast rows |
| `comparison_rows()` | Candidate status, scores, warnings and errors |
| `predictions_csv()` | Dated validation actuals/predictions with candidate, fold and segment |
| `metadata_json()` | Settings, diagnostics, comparison evidence and provenance |

Prepared-observation export rows are currently assembled in `app.py` and passed to `csv_bytes()`. That is presentation/serialization, not an alternative data-preparation pipeline.

## 19.1 CSV formula injection

A spreadsheet may interpret text beginning with `=`, `+`, `-` or `@` as a formula. The export helper prefixes suspicious text with an apostrophe. It preserves actual numeric values, including negative refunds, as numbers.

The important distinction is a string containing executable-looking spreadsheet syntax versus a genuine numeric prediction. Never strip all minus signs to solve a text-safety problem.

## 19.2 Metadata is not the original dataset

A fingerprint identifies bytes but cannot reconstruct them. Versions and settings explain a run but do not guarantee bit-identical numerical results across every library/platform combination. Retain the source and use documented tolerances when comparing statistical fits.

`ForecastResponse` can contain pandas objects, so the complete object is not directly a plain JSON document. `metadata_json()` explicitly selects serializable fields and converts evaluation dataclasses. It uses `allow_nan=False` to reject invalid JSON numerical values rather than silently emitting them.

Uploads/results remain in session memory by default. Downloads are user-initiated and can intentionally contain business values. Logs should contain safe operational categories, not raw records or sensitive exception text.

# 20. Tests as executable explanations

Read tests alongside each module. A useful test explains a contract with a small input and an observable outcome.

| Test file | What to study |
| --- | --- |
| `conftest.py` | Shared request factory and deterministic synthetic input |
| `test_ingestion.py` | File limits, malformed input, sheets and formula rejection |
| `test_detection.py` | Ranked evidence, ambiguous amounts and numeric identifiers |
| `test_preprocessing.py` | Transaction semantics, duplicates, gaps, parsing and unknown truth |
| `test_evaluation.py` | Hand-computed scores, matching folds, leakage and candidate failure |
| `test_models.py` | Shared outputs, interval availability and model-dependent winners |
| `test_service.py` | Full engine flow, target isolation, quality gates and refit failure |
| `test_exports.py` | Safe text and recomputing metrics from exported predictions |
| `test_app.py` | Streamlit workflow, short history and invalidation |

## 20.1 Fixtures and approximate comparisons

`request_factory` creates a valid request so a test changes only the feature it studies. `dataclasses.replace()` makes a revised dataclass instance without rewriting every field.

`pytest.approx()` compares floating-point values within tolerance. Statistical optimizers need appropriate tolerances; exact equality of every fitted coefficient is usually a brittle test.

## 20.2 Leakage tests

The evaluation test changes the last validation block and verifies that predictions made before those values became available do not change. Scores may change because actuals changed; earlier predictions must not.

This is stronger than a test that merely checks a variable is named `train`. It examines the information dependency.

## 20.3 Failure injection

`monkeypatch` replaces a function temporarily. A test can force Holt to fail while Naive succeeds, or force the final refit to fail after successful evaluation. This verifies recovery without needing an unpredictable numerical failure.

## 20.4 Testing the interface

Streamlit `AppTest` runs the script, manipulates widgets and inspects rendered elements/session state without manually opening a browser. It verifies that the example produces output and switching targets removes it.

These tests do not establish exhaustive accessibility, hostile-upload security or performance on every platform. `VERIFICATION.md` records those limits.

# 21. Build the app yourself in seven stages

Follow the architecture's seven phases, but build the smallest useful path at each stage. Do not copy all files first and debug the entire system at once.

## Stage 1 — Define requirements and contracts

Write the supported use case and non-goals. Sketch one request from upload to forecast or abstention. Create the package environment, metadata and shared dataclasses.

**Deliverable:** Importable package and explicit request/result types.  
**Checkpoint:** Explain each field and each outcome without referring to the UI.

## Stage 2 — Read files and suggest fields

Implement CSV first, with malformed/empty/duplicate-header tests. Add XLSX sheet selection, limits and formula rejection. Implement transparent column scoring and evidence.

**Deliverable:** Validated table and ranked candidates.  
**Checkpoint:** An ambiguous `Amount` field never silently settles business meaning.

## Stage 3 — Prepare business-correct series

Implement explicit date/number parsing, transaction versus summary branches, regular calendar grids, missingness, exclusions and diagnostics. Keep raw and derived data distinct.

**Deliverable:** `SeriesData` with provenance.  
**Checkpoint:** Predict aggregate values and gap behavior by hand before running tests.

## Stage 4 — Evaluate forecasters

Start with Naive and one chronological holdout. Implement metrics before complex models. Add seasonal naive, smoothing and ARIMA through the common interface. Then add expanding folds, warning handling and quality rules.

**Deliverable:** Comparable dated historical predictions and scores.  
**Checkpoint:** Alter future actuals and prove earlier predictions remain unchanged.

## Stage 5 — Assemble the service

Implement request validation, preparation, comparison, selection, adequacy, full-history refit, future dates and typed outcomes. Add pure exports and a small engine-only example.

**Deliverable:** Complete forecast/abstention workflow without Streamlit.  
**Checkpoint:** Force candidate and refit failures and inspect the response.

## Stage 6 — Add the interface

Collect settings, display evidence, call the service, and add charts/downloads. Implement session identity and invalidation before treating the UI as finished.

**Deliverable:** Thin guided Streamlit app.  
**Checkpoint:** Every analytical result comes from the engine, and old target results cannot survive changed settings.

## Stage 7 — Verify and hand off

Run domain/integration/UI tests, check the package and documented setup, measure representative resource use, and write limitations. Include successful, ambiguous, insufficient and rejected examples.

**Deliverable:** A reproducible teaching prototype with evidence.  
**Checkpoint:** Another student can run it and explain why it sometimes declines to forecast.

At each stage, commit a small coherent increment in your own exercise repository. Write what changed, why it changed, what you checked and what remains uncertain.

# 22. Guided experiments and expected observations

Use synthetic or non-sensitive inputs. Change one variable at a time and write your prediction first.

| Experiment | Expected observation or explanation |
| --- | --- |
| Change transaction aggregation from sum to mean | The target changes from period total to average transaction amount; scores are no longer for the same business measure |
| Remove a middle period | Default unresolved policy requests confirmation; absence is not automatically zero |
| Put an invalid amount in a known period and allow exclusions | That period remains unknown, including under zero-activity policy |
| Set an extremely strict error tolerance | The service may return `no_reliable_forecast` with comparison evidence |
| Increase fold count without more history | Initial training shrinks; candidates may become ineligible or the run may report insufficient history |
| Set seasonal period to 12 with too little training history | Seasonal candidates are excluded with an explanation |
| Change sales to purchases after a run | Confirmation/output reset; another target's selected model is not reused |
| Replace a target with constant zeros and use Naive | Zero-scale handling is defined; effectively zero error can pass |
| Use month-end dates through February in a leap year | Calendar-generated dates include the correct month end |
| Disable baseline selection | Naive remains the required reference but cannot become the selected forecast |

## 22.1 Two model-comparison experiments

`test_models.py` contains fixed seed-9 cases with three six-period validation folds and ARIMA(1,0,0):

- An autoregressive process around level 100, coefficient 0.85 and innovation standard deviation 2, where ARIMA is selected under the recorded setup.
- A linear signal with slope 3 and small noise, where Holt is selected under the recorded setup.

Explain why each data-generating pattern favors a different model. Do not modify selection logic to force the expected winner. If versions change, investigate numerical/configuration differences rather than assuming the fixture establishes a universal rule.

## 22.2 Small numerical exercises with answers

1. Transactions 40, 60 and -10 in one month: sum = **90**; mean = **30**. A refund is not a missing observation.
2. N = 60, width = 6, folds = 2: first training length = **48**. Validation blocks are periods **49–54** and **55–60**.
3. Training absolute level = 100, MAE = 15, tolerance = 0.10: ratio = **0.15**, so the adequacy gate **rejects** it even if it ranks first.
4. Name evidence absent and numeric coverage = 1: current detection score = **0.4**, below the configured confidence threshold.
5. A successful full-history refit uses all observations: it does **not** retroactively change the training ranges or scores of historical evaluation folds.

# 23. Debugging and common misconceptions

| Symptom or mistaken belief | What to inspect |
| --- | --- |
| `ModuleNotFoundError: forecasting_app` | Working directory, selected interpreter and editable installation |
| Good column suggestion but parsing fails | Detection samples permissively; preparation enforces the selected convention on full data |
| Summary dates fail cadence checks | MS versus ME or the selected weekly anchor; do not silently relabel them |
| Seasonal candidate is unavailable | Earliest fold's training count and seasonal period |
| Forecast stops despite a best score | Baseline permission, baseline comparison and relative-error tolerance |
| “Forward fill should fix validation gaps” | Validation values are truth, not model inputs to invent |
| “Best model means reliable model” | Ranking is relative; adequacy and future uncertainty are separate |
| “A warning can always be ignored” | Convergence warnings exclude candidates; other warnings still require interpretation |
| “More folds always improve the experiment” | They reduce the earliest training window and increase runtime |
| “A smaller MAE always means a better business measure” | Compare the same target, units, aggregation and windows first |
| “95% intervals guarantee my future values” | Intervals depend on the model and its assumptions |
| “The hash stores my data securely” | A fingerprint identifies bytes; it is not encryption or a backup |

Debug from the narrowest boundary: inspect request settings, prepared index/values, fold ranges, candidate status, adequacy calculations, and then UI state. Use safe synthetic reproductions instead of logging entire private tables.

# 24. Independent assessment and extension projects

## 24.1 Rebuild assessment

You understand the application when you can demonstrate these without copying the final implementation:

- Read a supported file and explain one rejected-file case.
- Produce ranked column evidence and explain ambiguity.
- Convert transactions to a selected calendar series without double-counting summaries.
- Preserve the distinction between unknown reporting and observed zero.
- Implement Naive and manually verify its predictions and MAE/RMSE.
- Construct chronological folds and demonstrate absence of future-value leakage.
- Add a model through a common interface without rewriting evaluation.
- Separate ranking from adequacy and return an explained no-forecast result.
- Refit on full usable history and generate correct future dates.
- Build a UI that does not own a second set of forecasting rules.
- Invalidate changed settings and keep exports consistent with displayed results.
- Explain which safeguards are tested and which deployment claims remain unverified.

A useful final presentation is a request trace, one hand-calculated example, one successful demo, one abstention demo, and one deliberately failing test that you then repair.

## 24.2 Extensions after the core is understood

Choose one extension and specify its contract, information requirements, tests and scope impact before coding:

- Preserve calendar alignment in seasonal correlation on gappy series.
- Preserve explicit dated predictions in the shared adapter contract.
- Improve detection terminology with tested examples, while keeping manual confirmation.
- Add MASE with training-only scale and explicit zero-denominator behavior.
- Add a separate untouched final-test protocol for sufficient history.
- Detect or request explicit handling of incomplete reporting periods.
- Centralize scattered numerical limits and document their ownership.
- Add a more specific distinction between no eligible candidate and all eligible candidates failing.

Multiplicative smoothing, SARIMA, exogenous predictors, background workers and hosting are larger scope changes. They need new eligibility, evaluation, resource and privacy decisions. Do not add them merely to make a feature list longer.

# 25. Glossary and PDF preparation notes

## 25.1 Glossary

| Term | Meaning in this application |
| --- | --- |
| Target | The selected business quantity to forecast |
| Univariate series | One target indexed by time |
| Cadence/frequency | The spacing and calendar convention of observations |
| Anchor | Calendar labeling convention, such as month start or Monday week-end |
| Horizon | Number of future periods requested |
| Seasonality | A repeating pattern with a specified sample period |
| Fold | One earlier-training/later-validation comparison |
| Leakage | Use of information unavailable at the supposed forecast origin |
| Baseline | A simple reference forecasting method |
| Eligibility | Whether a method is allowed to fit these inputs |
| Convergence | Whether numerical estimation reached its required stopping behavior |
| Adequacy | Whether selected results pass the configured quality policy |
| Abstention | Returning an explanation instead of unsupported future values |
| Refit | Train the chosen configuration again on all usable history |
| Provenance | Recorded data interpretation, settings, versions and transformation history |
| Orchestrator | The service that sequences modules and assembles outcomes |
| State invalidation | Removing stored results that no longer match active inputs |

## 25.2 Repository reading route

For a focused second reading, follow:

```text
contracts.py → config.py → ingestion.py → detection.py
→ preprocessing.py → analysis.py → models/baselines.py
→ models/base.py → statistical adapters → evaluation.py
→ service.py → exports.py → app.py → tests → benchmark.py
```

Read `README.md` for operational commands, `DEVELOPMENT_PLAN.md` for requirements/decisions, and `VERIFICATION.md` for dated evidence and remaining release work. The architecture PDF governs scope; the code governs explanations of what is actually implemented.

## 25.3 Preparing this Markdown as a PDF

This document uses numbered chapters, standard tables, fenced code and plain-text diagrams so conversion does not depend on a custom renderer. Preserve monospace formatting and indentation in code. If a table is wide, wrap cells rather than shrink all text until unreadable.

A suitable instruction when providing this file to a PDF-generation interface is:

> Convert this student guide into a readable PDF. Preserve its technical explanations, chapter order, code indentation, tables and examples. Add page numbers and a table of contents. Keep code blocks legible and avoid clipping long lines. Clearly retain labels distinguishing repository excerpts, learning examples, current limitations and extension ideas. Do not invent executed test results or additional application features.

The generated PDF should remain a study guide, not a claim that every excerpt forms a standalone program. Complete runnable examples are explicitly labeled; abbreviated excerpts must be read with their source modules.
