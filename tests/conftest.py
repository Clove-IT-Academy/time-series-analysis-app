from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from forecasting_app.contracts import ForecastRequest, UploadResult


@pytest.fixture
def request_factory():
    def make(values=None, **kwargs):
        if values is None:
            values = 100 + np.arange(60) * 2.0
        table = pd.DataFrame(
            {
                "Date": pd.date_range("2020-01-01", periods=len(values), freq="MS").strftime(
                    "%Y-%m-%d"
                ),
                "Sales": values,
                "Purchases": np.asarray(values) * 0.6,
            }
        )
        request = ForecastRequest(
            UploadResult(table, "synthetic.csv", "synthetic"),
            "Date",
            "Sales",
            confirmed=True,
            row_kind="summary",
            validation_periods=6,
            models=("Naive", "Holt"),
            horizon=6,
        )
        return replace(request, **kwargs)

    return make
