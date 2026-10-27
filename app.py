"""Streamlit thin client: explicit controls in, engine evidence out."""

import hashlib
import logging
from pathlib import Path

import pandas as pd
import streamlit as st

from forecasting_app.config import FREQUENCIES, MODEL_NAMES
from forecasting_app.contracts import ForecastRequest, InputError
from forecasting_app.detection import detect_columns, requires_confirmation
from forecasting_app.exports import (
    comparison_rows,
    csv_bytes,
    forecast_csv,
    metadata_json,
    predictions_csv,
)
from forecasting_app.ingestion import list_sheets, read_upload
from forecasting_app.preprocessing import suggest_frequency
from forecasting_app.service import forecast, preview

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s %(message)s")

st.set_page_config(page_title="Business Forecast Studio", page_icon="📈", layout="wide")
st.title("Business Forecast Studio")
st.caption("Explore the past. Compare methods. Forecast with context.")
st.info(
    "Local teaching prototype · One sales or purchase target per run · Uploads stay in session memory"
)

with st.sidebar:
    st.header("Your workspace")
    source = st.radio("Data source", ["Synthetic example", "Upload a file"])
    st.caption("CSV and XLSX · up to 10 MiB · 50,000 rows · 100 columns")
    if st.button("Reset session"):
        st.session_state.clear()
        st.rerun()
    st.divider()
    st.markdown(
        "**How it works**\n\n1. Review your records\n2. Confirm their meaning\n3. Compare past-only forecasts\n4. Review evidence and export"
    )
    st.caption("No automatic business decisions. A model may decline to forecast.")

try:
    if source == "Synthetic example":
        example = st.selectbox(
            "Example",
            ["Monthly transactions", "Weekly summaries", "Ambiguous fields", "Short history"],
        )
        name = {
            "Monthly transactions": "monthly_transactions.csv",
            "Weekly summaries": "weekly_summary.csv",
            "Ambiguous fields": "ambiguous.csv",
            "Short history": "short.csv",
        }[example]
        data = (Path(__file__).parent / "sample_data" / name).read_bytes()
    else:
        uploaded = st.file_uploader("Upload business history", type=["csv", "xlsx"])
        if uploaded is None:
            st.session_state.pop("response", None)
            st.stop()
        name, data = uploaded.name, uploaded.getvalue()
    sheets = list_sheets(data, name)
    sheet = st.selectbox("Worksheet", sheets) if sheets else None
    identity = hashlib.sha256(data + str(sheet).encode()).hexdigest()
    if st.session_state.get("upload_key") != identity:
        st.session_state["upload"] = read_upload(data, name, sheet)
        st.session_state["upload_key"] = identity
        st.session_state.pop("response", None)
    upload = st.session_state["upload"]
except InputError as error:
    st.error(str(error))
    st.session_state.pop("response", None)
    st.stop()

st.subheader("1 · Review and map")
st.caption(
    f"{len(upload.table):,} records · {len(upload.table.columns)} columns · Preview shows the first 15 rows"
)
st.dataframe(upload.table.head(15), width="stretch", hide_index=True)
candidates = detect_columns(upload.table)
left, middle, right = st.columns(3)
with left:
    target = st.selectbox("Business target", ["sales", "purchases"])
with middle:
    date_col = st.selectbox("Date column", [c.column_name for c in candidates["date"]])
with right:
    value_col = st.selectbox(
        "Target column", [c.column_name for c in candidates[target]], key=f"target_column_{target}"
    )
with st.expander("Why these columns? See detection evidence"):
    st.caption(
        "Scores combine terminology and sample parseability. They are heuristic scores, not probabilities."
    )
    st.dataframe(
        [
            {
                "role": role,
                "column": c.column_name,
                "score": c.confidence,
                "evidence": "; ".join(c.evidence),
            }
            for role in ("date", target)
            for c in candidates[role]
        ],
        hide_index=True,
        width="stretch",
    )
if requires_confirmation(candidates["date"]) or requires_confirmation(candidates[target]):
    st.warning(
        "Detection is ambiguous. Review alternatives and explicitly confirm the intended fields below."
    )

st.subheader("2 · Confirm business meaning")
a, b, c = st.columns(3)
with a:
    row_kind = st.selectbox("What does one row represent?", ["transactions", "summary"])
    aggregation = st.selectbox(
        "Transaction aggregation",
        ["sum", "mean"],
        disabled=row_kind == "summary",
        help="Sum totals flows; mean averages transaction amounts. Summaries are not reaggregated.",
    )
    dup = st.selectbox(
        "Repeated summary dates", ["reject", "sum", "mean"], disabled=row_kind != "summary"
    )
with b:
    suggested = suggest_frequency(upload.table[date_col])
    frequency = st.selectbox(
        "Frequency / calendar anchor",
        FREQUENCIES,
        index=list(FREQUENCIES).index(suggested) if suggested else 3,
    )
    st.caption(
        f"Suggested cadence: {suggested or 'uncertain — choose explicitly'}. W-MON/W-SUN label week-end; MS/ME label month-start/end."
    )
    gap = st.selectbox(
        "Absent periods mean…",
        ["unresolved", "zero activity", "forward fill training"],
        help="Unknown periods are not zero by default. Forward fill uses at most 3 prior training periods; validation gaps always block scoring.",
    )
with c:
    date_format = st.selectbox("Date convention", ["ISO8601", "%d/%m/%Y", "%m/%d/%Y"])
    number_format = st.selectbox(
        "Numeric convention", ["plain", "comma thousands", "decimal comma"]
    )
    invalid = st.selectbox(
        "Invalid date / target rows",
        ["reject", "exclude"],
        help="Exclusions are counted in diagnostics. Valid zeros/refunds are retained.",
    )

st.subheader("3 · Set comparison and quality rules")
a, b, c = st.columns(3)
with a:
    horizon = st.number_input("Future periods", 1, 365, 12)
    validation = st.number_input("Periods per validation fold", 1, 365, 12)
    folds = st.number_input(
        "Chronological folds",
        1,
        5,
        1,
        help="Expanding training windows; nonoverlapping validation windows at the end of history.",
    )
with b:
    season = st.number_input(
        "Samples per seasonal cycle",
        1,
        365,
        12,
        help="Monthly yearly pattern = 12; weekly yearly ≈ 52. Cadence alone does not establish a seasonal pattern.",
    )
    metric = st.selectbox("Primary ranking metric", ["MAE", "RMSE"])
    tolerance = st.number_input(
        "Maximum error / training absolute level",
        0.0,
        5.0,
        0.5,
        0.05,
        help="An exploratory adequacy rule: pooled validation error divided by mean absolute level of the first training window. Not a universal business tolerance.",
    )
with c:
    models = st.multiselect("Candidates", MODEL_NAMES, default=list(MODEL_NAMES))
    allow_baseline = st.checkbox("Allow a baseline as the selected method", value=True)
    st.caption(
        "The Naive reference is required. Selection must match or beat it and pass your error tolerance."
    )
with st.expander("ARIMA configuration and interpretation"):
    pcol, dcol, qcol = st.columns(3)
    p = pcol.number_input("p · past values", 0, 3, 1)
    d = dcol.number_input("d · differences", 0, 2, 1)
    q = qcol.number_input("q · past forecast errors", 0, 3, 1)
    st.caption(
        "MA refers to past forecast errors, not rolling averages. Settings are examples, not guaranteed optima. Smoothing candidates are additive. Only ARIMA currently supplies 95% model-based intervals."
    )

# Reset confirmation whenever any effective input changes, including source/sheet/target.
settings = (
    identity,
    date_col,
    value_col,
    target,
    row_kind,
    aggregation,
    frequency,
    gap,
    dup,
    date_format,
    number_format,
    invalid,
    horizon,
    validation,
    folds,
    season,
    metric,
    tolerance,
    tuple(models),
    allow_baseline,
    p,
    d,
    q,
)
settings_key = hashlib.sha256(repr(settings).encode()).hexdigest()
if st.session_state.get("settings_key") != settings_key:
    st.session_state["settings_key"] = settings_key
    st.session_state["confirm"] = False
    st.session_state.pop("response", None)
confirmed = st.checkbox(
    "I confirm the fields, row meaning, aggregation, frequency and data policies.", key="confirm"
)
request = ForecastRequest(
    upload,
    date_col,
    value_col,
    target,
    confirmed,
    row_kind,
    aggregation,
    frequency,
    date_format,
    number_format,
    gap,
    dup,
    invalid,
    int(horizon),
    int(validation),
    int(folds),
    int(season),
    tuple(models),
    (int(p), int(d), int(q)),
    metric,
    float(tolerance),
    allow_baseline,
)
if confirmed:
    try:
        prepared, diagnostics = preview(request)
        with st.expander("Prepared series and diagnostics · review before running", expanded=True):
            st.line_chart(prepared.values, color="#137C73")
            st.json(diagnostics)
            st.caption(
                "Full-history exploration is descriptive; evaluation fits each candidate on its earlier training history only."
            )
    except InputError as error:
        st.warning(str(error))

if st.button("Compare and forecast", type="primary", disabled=not confirmed):
    with st.status("Running analysis…", expanded=True) as status:
        response = forecast(request, progress=lambda stage: st.write(stage))
        st.session_state["response"] = response
        status.update(
            label="Analysis complete",
            state="complete" if response.forecast_rows else "error",
            expanded=False,
        )

response = st.session_state.get("response")
if response is not None:
    st.subheader("4 · Evidence and forecast")
    st.caption(f"Outcome: {response.status.replace('_', ' ')}")
    (st.success if response.forecast_rows else st.warning)(response.message)
    if response.comparison:
        st.dataframe(comparison_rows(response), hide_index=True, width="stretch")
        with st.expander("Fold scores, configuration and candidate diagnostics"):
            for result in response.comparison:
                st.markdown(f"**{result.candidate_name} · {result.status}**")
                st.json(result.configuration)
                if result.fold_metrics:
                    st.dataframe(result.fold_metrics, hide_index=True)
                for message in result.errors + result.warnings:
                    st.write(message)
        st.download_button(
            "Download validation predictions",
            predictions_csv(response),
            "validation_predictions.csv",
            "text/csv",
        )
        st.download_button(
            "Download comparison",
            csv_bytes(comparison_rows(response)),
            "comparison.csv",
            "text/csv",
        )
    if response.forecast_rows:
        frame = pd.DataFrame(response.forecast_rows).set_index("timestamp")
        frame.index = pd.to_datetime(frame.index)
        chart = pd.DataFrame({"History": response.series.values, "Forecast": frame.prediction})
        st.line_chart(chart, color=["#8495A5", "#137C73"])
        st.caption(
            "Forecast begins after the last historical period. Bounds, if present below, are ARIMA's 95% model-based prediction intervals, not guarantees."
        )
        st.dataframe(frame, width="stretch")
        for warning in response.warnings:
            st.caption(f"• {warning}")
        st.download_button(
            "Download future forecast",
            forecast_csv(response),
            "forecast.csv",
            "text/csv",
            type="primary",
        )
        st.download_button(
            "Download prepared observations",
            csv_bytes(
                [
                    {
                        "timestamp": date.isoformat(),
                        "value": None if pd.isna(value) else float(value),
                    }
                    for date, value in response.series.values.items()
                ]
            ),
            "prepared_observations.csv",
            "text/csv",
        )
    with st.expander("Run provenance and data diagnostics"):
        st.json(response.diagnostics)
        st.json(response.run_config)
    st.download_button(
        "Download run metadata", metadata_json(response), "run_metadata.json", "application/json"
    )
