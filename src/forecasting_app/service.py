"""Single UI-independent orchestration boundary."""

import importlib.metadata
import logging
import time
import uuid
from dataclasses import fields
from typing import Callable

import numpy as np
import pandas as pd

from .analysis import describe
from .config import FREQUENCIES, MAX_COLUMNS, MAX_ROWS, MODEL_NAMES
from .contracts import ConfirmationRequired, ForecastRequest, ForecastResponse, InputError
from .evaluation import evaluate, select
from .models.base import predict
from .preprocessing import prepare, training_values

logger = logging.getLogger(__name__)


def validate(request: ForecastRequest):
    if not request.confirmed:
        raise ConfirmationRequired(
            "Confirm the date, target, row meaning, aggregation and cadence before forecasting."
        )
    if request.target not in ("sales", "purchases"):
        raise InputError("Choose sales or purchases for this run.")
    if (
        request.upload.table.empty
        or len(request.upload.table) > MAX_ROWS
        or len(request.upload.table.columns) > MAX_COLUMNS
    ):
        raise InputError("Table must contain 1–50,000 rows and at most 100 columns.")
    if request.upload.table.columns.duplicated().any():
        raise InputError("Column names must be unique.")
    for value, low, high, label in (
        (request.horizon, 1, 365, "Horizon"),
        (request.validation_periods, 1, 365, "Validation window"),
        (request.folds, 1, 5, "Folds"),
        (request.seasonal_period, 1, 365, "Seasonal period"),
    ):
        if type(value) is not int or not low <= value <= high:
            raise InputError(f"{label} must be an integer between {low} and {high}.")
    if (
        not request.models
        or len(request.models) > 6
        or len(set(request.models)) != len(request.models)
    ):
        raise InputError("Select 1–6 distinct candidate configurations.")
    if set(request.models) - set(MODEL_NAMES) or "Naive" not in request.models:
        raise InputError("Candidates must be supported methods and include the Naive reference.")
    if (
        len(request.arima_order) != 3
        or any(type(v) is not int for v in request.arima_order)
        or not (
            0 <= request.arima_order[0] <= 3
            and 0 <= request.arima_order[1] <= 2
            and 0 <= request.arima_order[2] <= 3
        )
    ):
        raise InputError("ARIMA orders must satisfy p/q: 0–3 and d: 0–2.")
    if (
        request.primary_metric not in ("MAE", "RMSE")
        or not np.isfinite(request.max_relative_error)
        or not 0 <= request.max_relative_error <= 5
    ):
        raise InputError("Choose MAE/RMSE and a relative error tolerance between 0 and 5.")
    if request.frequency not in FREQUENCIES:
        raise InputError("Unsupported cadence.")


def forecast(
    request: ForecastRequest, progress: Callable[[str], None] | None = None
) -> ForecastResponse:
    started = time.perf_counter()
    run_id = uuid.uuid4().hex[:12]
    config = {f.name: getattr(request, f.name) for f in fields(request) if f.name != "upload"}
    config.update(
        {
            "source_fingerprint": request.upload.fingerprint,
            "sheet": request.upload.sheet,
            "run_id": run_id,
            "schema_version": 1,
            "versions": {
                name: importlib.metadata.version(name)
                for name in ("pandas", "numpy", "statsmodels", "streamlit", "openpyxl")
            },
            "interval_coverage": 0.95,
            "error_definition": "actual minus prediction",
            "quality_rule": "Not worse than naive AND primary error / first-training mean absolute level <= tolerance",
            "tie_policy": "primary error then candidate name",
            "fold_aggregation": "pooled point errors",
        }
    )
    response = ForecastResponse("invalid_input", "Run not completed.", run_config=config)

    def stage(name):
        logger.info(
            "run=%s stage=%s elapsed_seconds=%.3f", run_id, name, time.perf_counter() - started
        )
        if progress:
            progress(name)

    try:
        stage("Validate choices")
        validate(request)
        stage("Prepare series")
        series = prepare(request)
        response.series = series
        response.diagnostics = describe(series, request.seasonal_period)
        if len(series.values) - request.validation_periods * request.folds < 4:
            response.status = "insufficient_history"
            response.message = "Leave at least four training periods before validation. Reduce window/folds or add history."
            return response
        stage("Evaluate candidates")
        response.comparison = evaluate(series.values, request)
        selected, explanation = select(response.comparison, request)
        if selected is None:
            any_fit = any(c.status in ("success", "warning") for c in response.comparison)
            response.status = "no_reliable_forecast" if any_fit else "no_eligible_model"
            response.message = explanation
            return response
        first = len(series.values) - request.validation_periods * request.folds
        train = training_values(series.values.iloc[:first], request.gap_policy)
        scale = float(train.abs().mean())
        score = selected.aggregate_metrics[request.primary_metric]
        ratio = score / scale if scale > 1e-12 else (0.0 if score <= 1e-12 else None)
        response.diagnostics.update(
            {"training_absolute_level": scale, "relative_validation_error": ratio}
        )
        if ratio is None or ratio > request.max_relative_error:
            response.status = "no_reliable_forecast"
            response.message = "Validation error exceeds the chosen training-scale tolerance. Review history and assumptions; no future forecast returned."
            return response
        stage("Refit and forecast")
        try:
            history = training_values(series.values, request.gap_policy)
            prediction = predict(
                selected.candidate_name,
                history,
                request.horizon,
                request.seasonal_period,
                request.arima_order,
                intervals=True,
            )
        except Exception:
            response.status = "refit_failed"
            response.message = "Selected candidate could not refit safely on full history. No old-fit forecast substituted."
            return response
        dates = pd.date_range(
            series.values.index[-1], periods=request.horizon + 1, freq=request.frequency
        )[1:]
        for i, date in enumerate(dates):
            row = {
                "timestamp": date.isoformat(),
                "target": request.target,
                "prediction": float(prediction.points[i]),
            }
            if prediction.lower is not None:
                row.update(
                    {"lower_95": float(prediction.lower[i]), "upper_95": float(prediction.upper[i])}
                )
            response.forecast_rows.append(row)
        response.selected_model = selected.candidate_name
        response.warnings = [
            "Forecasts are estimates, not guarantees. Validation may not reflect future conditions."
        ]
        response.warnings.extend(sorted(set(selected.warnings + (prediction.warnings or []))))
        if prediction.lower is None:
            response.warnings.append(
                "Prediction intervals are not implemented for this selected method."
            )
        if request.row_kind == "transactions":
            response.warnings.append(
                "Transaction reporting periods are assumed complete, including the last period. Confirm this before using the forecast."
            )
        if request.folds == 1:
            response.warnings.append("One holdout window provides limited evidence of stability.")
        if series.missing_periods:
            response.warnings.append(f"Missing-period policy applied: {request.gap_policy}.")
        if series.diagnostics["excluded_rows"]:
            response.warnings.append(
                "Invalid source rows were excluded by explicit policy; inspect counts."
            )
        if series.diagnostics["negative_values"] or any(
            r["prediction"] < 0 for r in response.forecast_rows
        ):
            response.warnings.append(
                "Negative adjustments or predictions are retained; review their business meaning."
            )
        response.status = "success_with_cautions"
        response.message = f"{selected.candidate_name} selected. {explanation} Passed your configured error tolerance."
        stage("Complete")
        return response
    except ConfirmationRequired as error:
        response.status, response.message = "needs_confirmation", str(error)
    except InputError as error:
        response.status, response.message = "invalid_input", str(error)
    except Exception:
        # No raw exception text: parser/library exceptions can contain business values.
        logger.error("run=%s category=unexpected_engine_failure", run_id)
        response.status, response.message = (
            "engine_error",
            "Analysis could not complete. Check the data policies and reduce configuration complexity.",
        )
    return response


def preview(request: ForecastRequest):
    """Engine-owned preparation/diagnostics without fitting; same gates as forecast."""
    validate(request)
    series = prepare(request)
    return series, describe(series, request.seasonal_period)
