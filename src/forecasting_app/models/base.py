"""Common bounded model contract and sanitized warning handling."""

import warnings
from dataclasses import dataclass

import numpy as np
import pandas as pd
from statsmodels.tools.sm_exceptions import ConvergenceWarning


@dataclass
class Prediction:
    points: np.ndarray
    lower: np.ndarray | None = None
    upper: np.ndarray | None = None
    warnings: list[str] | None = None


def eligibility(name: str, train: pd.Series, season: int) -> str | None:
    if len(train) < 4:
        return "At least four training periods are required."
    if name in ("Seasonal naive", "Holt-Winters") and (season < 2 or len(train) < 2 * season):
        return "Seasonal methods need at least two complete training seasons."
    if name in ("Holt", "ARIMA") and len(train) < 12:
        return "This candidate requires at least 12 training periods."
    return None


def predict(
    name: str, train: pd.Series, steps: int, season: int, order: tuple, intervals: bool = False
) -> Prediction:
    from .arima import arima_prediction
    from .baselines import baseline_prediction
    from .exponential_smoothing import smoothing_prediction

    reason = eligibility(name, train, season)
    if reason:
        raise ValueError(reason)
    with warnings.catch_warnings(record=True) as captured:
        warnings.simplefilter("always")
        if name in ("Naive", "Seasonal naive"):
            result = baseline_prediction(name, train, steps, season)
        elif name == "ARIMA":
            result = arima_prediction(train, steps, order, intervals)
        else:
            result = smoothing_prediction(name, train, steps, season)
    if any(issubclass(w.category, ConvergenceWarning) for w in captured):
        raise ValueError("Fit did not converge; candidate excluded.")
    result.warnings = sorted(
        {f"Model emitted {w.category.__name__}; inspect assumptions." for w in captured}
    )
    if len(result.points) != steps or not np.isfinite(result.points).all():
        raise ValueError("Candidate produced invalid predictions.")
    if result.lower is not None:
        if (
            len(result.lower) != steps
            or len(result.upper) != steps
            or not np.isfinite(result.lower).all()
            or not np.isfinite(result.upper).all()
            or (result.lower > result.upper).any()
        ):
            raise ValueError("Candidate produced invalid intervals.")
    return result
