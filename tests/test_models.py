import numpy as np
import pytest

from forecasting_app.models.base import predict
from forecasting_app.preprocessing import prepare
from forecasting_app.service import forecast


@pytest.mark.parametrize("kind,expected", [("autoregressive", "ARIMA"), ("linear", "Holt")])
def test_documented_synthetic_model_winners(request_factory, kind, expected):
    # Fixed synthetic mechanisms, seed 9, 3 six-period folds; no fixture-aware selection.
    rng = np.random.default_rng(9)
    if kind == "autoregressive":
        values = np.zeros(240)
        for i in range(1, len(values)):
            values[i] = 0.85 * values[i - 1] + rng.normal(0, 2)
        values += 100
    else:
        values = 100 + np.arange(120) * 3 + rng.normal(0, 0.1, 120)
    response = forecast(
        request_factory(
            values=values,
            models=("Naive", "Simple smoothing", "Holt", "ARIMA"),
            arima_order=(1, 0, 0),
            validation_periods=6,
            folds=3,
            seasonal_period=1,
        )
    )
    assert response.selected_model == expected, [
        (r.candidate_name, r.aggregate_metrics) for r in response.comparison
    ]


def test_arima_intervals_are_finite_and_ordered(request_factory):
    series = prepare(
        request_factory(values=100 + np.random.default_rng(42).normal(0, 4, 60))
    ).values
    result = predict("ARIMA", series, 5, 1, (1, 0, 0), intervals=True)
    assert result.lower is not None
    assert np.all(result.lower <= result.points)
    assert np.all(result.points <= result.upper)


def test_smoothing_has_no_fabricated_intervals(request_factory):
    result = predict("Holt", prepare(request_factory()).values, 4, 12, (1, 1, 1), intervals=True)
    assert result.lower is None and result.upper is None


def test_negative_values_are_supported_additively(request_factory):
    response = forecast(request_factory(values=np.linspace(-100, -40, 60)))
    assert response.forecast_rows
    assert response.series.diagnostics["negative_values"] == 60
