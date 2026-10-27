import numpy as np
import pytest

from forecasting_app.contracts import InputError
from forecasting_app.evaluation import evaluate, metrics
from forecasting_app.models.base import predict
from forecasting_app.preprocessing import prepare


def test_metrics_hand_calculation():
    score = metrics(np.array([0, 3]), np.array([1, 1]))
    assert score["MAE"] == 1.5
    assert score["RMSE"] == pytest.approx(np.sqrt(2.5))
    assert score["Mean error"] == 0.5
    with pytest.raises(InputError):
        metrics(np.array([np.nan]), np.array([1]))


def test_baseline_long_horizon(request_factory):
    series = prepare(request_factory()).values
    prediction = predict("Seasonal naive", series, 27, 12, (1, 1, 1))
    assert prediction.points[:12].tolist() == series.iloc[-12:].tolist()
    assert prediction.points[12:24].tolist() == series.iloc[-12:].tolist()


def test_matching_folds_and_leakage(request_factory, monkeypatch):
    request = request_factory(models=("Naive", "Simple smoothing"), folds=2)
    series = prepare(request).values
    before = evaluate(series, request)
    altered = series.copy()
    altered.iloc[-6:] += 10000
    after = evaluate(altered, request)
    for original, changed in zip(before, after, strict=True):
        assert original.predictions[:6] == changed.predictions[:6]
        assert [r["prediction"] for r in original.predictions[-6:]] == [
            r["prediction"] for r in changed.predictions[-6:]
        ]
        assert original.fold_metrics[0]["train_end"] < original.fold_metrics[0]["validation_start"]
    assert (
        before[0].fold_metrics[0]["validation_start"]
        == before[1].fold_metrics[0]["validation_start"]
    )


def test_missing_truth_is_not_imputed(request_factory):
    request = request_factory(gap_policy="forward fill training")
    series = prepare(request).values
    series.iloc[-2] = np.nan
    with pytest.raises(InputError, match="Validation"):
        evaluate(series, request)


def test_failed_candidate_keeps_success(request_factory, monkeypatch):
    import forecasting_app.evaluation as module

    original = module.predict

    def fake(name, *args, **kwargs):
        if name == "Holt":
            raise RuntimeError("sensitive payload")
        return original(name, *args, **kwargs)

    monkeypatch.setattr(module, "predict", fake)
    request = request_factory()
    results = evaluate(prepare(request).values, request)
    assert results[0].status == "success"
    assert results[1].status == "failed"
    assert "sensitive" not in str(results[1])
