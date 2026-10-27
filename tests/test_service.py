from dataclasses import replace
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from forecasting_app.contracts import UploadResult
from forecasting_app.exports import forecast_csv, metadata_json
from forecasting_app.ingestion import read_upload
from forecasting_app.service import forecast


def test_success_and_export_parity(request_factory):
    response = forecast(request_factory())
    assert response.status == "success_with_cautions", response.message
    assert response.selected_model == "Holt"
    frame = pd.read_csv(__import__("io").BytesIO(forecast_csv(response)))
    assert frame.prediction.tolist() == pytest.approx(
        [r["prediction"] for r in response.forecast_rows]
    )
    assert pd.Timestamp(frame.timestamp.iloc[0]) == pd.Timestamp("2025-01-01")
    assert len(frame) == 6
    assert '"versions"' in metadata_json(response)


def test_confirmation_and_insufficient(request_factory):
    assert forecast(request_factory(confirmed=False)).status == "needs_confirmation"
    assert (
        forecast(request_factory(values=[1, 2, 3], validation_periods=1)).status
        == "insufficient_history"
    )


def test_quality_abstention(request_factory):
    response = forecast(request_factory(max_relative_error=0, models=("Naive",)))
    assert response.status == "no_reliable_forecast"
    assert not response.forecast_rows and response.comparison


def test_zero_history_has_defined_scale(request_factory):
    response = forecast(request_factory(values=np.zeros(40), models=("Naive",)))
    assert response.forecast_rows
    assert response.diagnostics["relative_validation_error"] == 0


def test_target_isolation(request_factory):
    sales = forecast(request_factory())
    purchases = forecast(request_factory(target="purchases", target_column="Purchases"))
    assert purchases.forecast_rows[0]["prediction"] == pytest.approx(
        sales.forecast_rows[0]["prediction"] * 0.6, rel=1e-4
    )
    assert purchases.run_config["target"] == "purchases"


def test_refit_failure_never_uses_old_fit(request_factory, monkeypatch):
    import forecasting_app.service as module

    monkeypatch.setattr(
        module, "predict", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("private"))
    )
    response = forecast(request_factory())
    assert response.status == "refit_failed" and not response.forecast_rows
    assert "private" not in response.message


def test_month_end_leap_year(request_factory):
    req = request_factory(models=("Naive",), horizon=3, frequency="ME", max_relative_error=5)
    table = req.upload.table.copy()
    table["Date"] = pd.date_range("2019-02-28", periods=60, freq="ME").strftime("%Y-%m-%d")
    response = forecast(replace(req, upload=UploadResult(table, "x", "x")))
    assert [r["timestamp"][:10] for r in response.forecast_rows] == [
        "2024-02-29",
        "2024-03-31",
        "2024-04-30",
    ]


def test_sample_csv_and_xlsx(request_factory):
    root = Path(__file__).parents[1] / "sample_data"
    for name, sheet in [
        ("monthly_transactions.csv", None),
        ("business_examples.xlsx", "Transactions"),
    ]:
        upload = read_upload((root / name).read_bytes(), name, sheet)
        req = request_factory(
            upload=upload,
            row_kind="transactions",
            models=("Naive", "Holt-Winters"),
            validation_periods=12,
        )
        response = forecast(req)
        assert response.forecast_rows, response.message


@pytest.mark.parametrize(
    "settings",
    [
        {"models": ("ARIMA",)},
        {"horizon": 0},
        {"folds": 8},
        {"arima_order": (9, 1, 1)},
        {"primary_metric": "MAPE"},
    ],
)
def test_request_bounds(request_factory, settings):
    assert forecast(request_factory(**settings)).status == "invalid_input"


def test_all_candidates_fail_is_explained(request_factory, monkeypatch):
    import forecasting_app.evaluation as module

    def fail(*args, **kwargs):
        raise ValueError("private")

    monkeypatch.setattr(module, "predict", fail)
    response = forecast(request_factory())
    assert response.status == "no_eligible_model"
    assert response.comparison and not response.forecast_rows


def test_weekly_nonseasonal_workflow(request_factory):
    root = Path(__file__).parents[1] / "sample_data"
    upload = read_upload((root / "weekly_summary.csv").read_bytes(), "weekly.csv")
    response = forecast(
        request_factory(
            upload=upload,
            frequency="W-MON",
            seasonal_period=1,
            models=("Naive", "Simple smoothing", "Holt"),
            validation_periods=8,
        )
    )
    assert response.forecast_rows
    assert all(pd.Timestamp(r["timestamp"]).weekday() == 0 for r in response.forecast_rows)
