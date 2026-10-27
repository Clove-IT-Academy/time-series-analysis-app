"""Descriptive evidence; no causal or reliability claims."""

import numpy as np

from .contracts import SeriesData


def describe(series: SeriesData, seasonal_period: int) -> dict:
    values = series.values.dropna()
    seasonal = None
    if seasonal_period > 1 and len(values) >= 2 * seasonal_period and values.std() > 0:
        correlation = values.autocorr(seasonal_period)
        seasonal = float(correlation) if np.isfinite(correlation) else None
    positions = np.flatnonzero(series.values.notna().to_numpy())
    slope = float(np.polyfit(positions, values.to_numpy(), 1)[0]) if len(values) > 1 else 0.0
    return {
        **series.diagnostics,
        "linear_trend_per_period": slope,
        "mean": float(values.mean()),
        "standard_deviation": float(values.std()) if len(values) > 1 else 0.0,
        "seasonal_lag_correlation": seasonal,
        "seasonal_evidence_note": "Lag correlation is descriptive, not proof of seasonality.",
        "seasonal_period": seasonal_period,
    }
