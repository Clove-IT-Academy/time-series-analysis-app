import numpy as np
from statsmodels.tsa.arima.model import ARIMA

from .base import Prediction


def arima_prediction(train, steps, order, intervals):
    fitted = ARIMA(train, order=order).fit(method_kwargs={"maxiter": 100})
    forecast = fitted.get_forecast(steps=steps)
    bounds = np.asarray(forecast.conf_int(alpha=0.05)) if intervals else None
    return Prediction(
        np.asarray(forecast.predicted_mean),
        bounds[:, 0] if bounds is not None else None,
        bounds[:, 1] if bounds is not None else None,
    )
