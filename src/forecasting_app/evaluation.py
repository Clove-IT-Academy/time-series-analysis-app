"""Matching chronological folds, pooled errors and separate adequacy policy."""

import numpy as np
import pandas as pd

from .contracts import EvaluationResult, ForecastRequest, InputError
from .models.base import eligibility, predict
from .preprocessing import training_values


def metrics(actual: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    if len(actual) == 0 or len(actual) != len(predicted):
        raise InputError("Scoring requires matching nonempty observations.")
    error = np.asarray(actual, dtype=float) - np.asarray(predicted, dtype=float)
    if not np.isfinite(error).all():
        raise InputError("Cannot score missing or non-finite actuals/predictions.")
    if not np.isfinite(np.square(error)).all():
        raise InputError("Errors exceed the numerical range supported for scoring.")
    return {
        "MAE": float(np.mean(abs(error))),
        "RMSE": float(np.sqrt(np.mean(error**2))),
        "Mean error": float(np.mean(error)),
    }


def evaluate(series: pd.Series, request: ForecastRequest) -> list[EvaluationResult]:
    width, folds = request.validation_periods, request.folds
    first = len(series) - width * folds
    if first < 4:
        raise InputError(
            "Too little history for these validation periods/folds; leave at least four training periods."
        )
    # Validate all truth before fitting; no candidate can silently omit difficult windows.
    if not np.isfinite(series.iloc[first:]).all():
        raise InputError(
            "Validation contains missing actuals. Repair source data or choose a different window."
        )
    results = []
    for name in request.models:
        config = {
            "seasonal_period": request.seasonal_period,
            "order": list(request.arima_order) if name == "ARIMA" else None,
        }
        result = EvaluationResult(name, config, "success")
        try:
            for fold in range(folds):
                end = first + fold * width
                train = training_values(series.iloc[:end], request.gap_policy)
                actual = series.iloc[end : end + width]
                reason = eligibility(name, train, request.seasonal_period)
                if reason:
                    result.status = "ineligible"
                    result.errors.append(reason)
                    break
                forecast = predict(name, train, width, request.seasonal_period, request.arima_order)
                result.warnings.extend(forecast.warnings or [])
                result.fold_metrics.append(
                    {
                        "fold": fold + 1,
                        "train_end": train.index[-1].isoformat(),
                        "validation_start": actual.index[0].isoformat(),
                        "validation_end": actual.index[-1].isoformat(),
                        "count": width,
                        **metrics(actual.to_numpy(), forecast.points),
                    }
                )
                for date, truth, point in zip(
                    actual.index, actual.values, forecast.points, strict=True
                ):
                    result.predictions.append(
                        {
                            "fold": fold + 1,
                            "timestamp": date.isoformat(),
                            "actual": float(truth),
                            "prediction": float(point),
                        }
                    )
            if result.status == "success":
                result.aggregate_metrics = metrics(
                    np.array([p["actual"] for p in result.predictions]),
                    np.array([p["prediction"] for p in result.predictions]),
                )
                if result.warnings:
                    result.status = "warning"
        except Exception as error:
            result.status = "failed"
            # Do not expose library exceptions, which may embed user data.
            result.errors.append(
                str(error)
                if isinstance(error, InputError)
                else "Candidate fit failed or did not converge."
            )
        results.append(result)
    return results


def select(
    results: list[EvaluationResult], request: ForecastRequest
) -> tuple[EvaluationResult | None, str]:
    valid = [r for r in results if r.status in ("success", "warning") and r.aggregate_metrics]
    if not valid:
        return None, "No eligible candidate completed every validation fold."
    naive = next((r for r in valid if r.candidate_name == "Naive"), None)
    if naive is None:
        return None, "Naive reference failed; adequacy cannot be established."
    ranked = sorted(
        valid, key=lambda r: (r.aggregate_metrics[request.primary_metric], r.candidate_name)
    )
    for candidate in ranked:
        if not request.allow_baseline and candidate.candidate_name in ("Naive", "Seasonal naive"):
            continue
        if (
            candidate.aggregate_metrics[request.primary_metric]
            <= naive.aggregate_metrics[request.primary_metric] + 1e-10
        ):
            return candidate, "Candidate matches or improves the naive reference."
    return None, "No permitted candidate matches the naive reference."
