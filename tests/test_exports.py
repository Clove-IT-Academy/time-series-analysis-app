from forecasting_app.exports import csv_bytes


def test_formula_injection_text_not_numeric():
    result = csv_bytes([{"label": "=SUM(A1)", "value": -12.5}]).decode()
    assert "'=SUM(A1)" in result
    assert ",-12.5" in result


def test_validation_export_recomputes_scores(request_factory):
    import io

    import pandas as pd
    import pytest

    from forecasting_app.evaluation import metrics
    from forecasting_app.exports import predictions_csv
    from forecasting_app.service import forecast

    response = forecast(request_factory())
    exported = pd.read_csv(io.BytesIO(predictions_csv(response)))
    for candidate in response.comparison:
        rows = exported[exported.candidate == candidate.candidate_name]
        actual = metrics(rows.actual.to_numpy(), rows.prediction.to_numpy())
        assert actual["MAE"] == pytest.approx(candidate.aggregate_metrics["MAE"])
