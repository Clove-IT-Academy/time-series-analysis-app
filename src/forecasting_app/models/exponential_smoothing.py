import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from .base import Prediction


def smoothing_prediction(name, train, steps, season):
    fitted = ExponentialSmoothing(
        train,
        trend="add" if name in ("Holt", "Holt-Winters") else None,
        seasonal="add" if name == "Holt-Winters" else None,
        seasonal_periods=season if name == "Holt-Winters" else None,
        initialization_method="estimated",
    ).fit(optimized=True, minimize_kwargs={"options": {"maxiter": 100}})
    return Prediction(np.asarray(fitted.forecast(steps)))
