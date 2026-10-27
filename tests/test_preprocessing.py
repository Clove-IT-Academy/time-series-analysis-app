from dataclasses import replace

import numpy as np
import pandas as pd
import pytest

from forecasting_app.contracts import ConfirmationRequired, InputError, UploadResult
from forecasting_app.preprocessing import parse_numbers, prepare, training_values


def with_table(request, dates, values):
    return replace(
        request, upload=UploadResult(pd.DataFrame({"Date": dates, "Sales": values}), "x", "x")
    )


def test_transactions_preserve_equal_rows_and_refunds(request_factory):
    request = with_table(
        request_factory(row_kind="transactions"),
        ["2024-01-01", "2024-01-01", "2024-02-01", "2024-03-01"],
        [5, 5, -4, 0],
    )
    result = prepare(request)
    assert result.values.tolist() == [10, -4, 0]
    assert result.diagnostics["negative_values"] == 1


def test_summary_duplicates_explicit(request_factory):
    request = with_table(request_factory(), ["2024-01-01", "2024-01-01", "2024-02-01"], [5, 5, 3])
    with pytest.raises(ConfirmationRequired):
        prepare(request)
    assert prepare(replace(request, duplicate_policy="sum")).values.tolist() == [10, 3]


def test_gaps_not_zero_by_default(request_factory):
    request = with_table(request_factory(), ["2024-01-01", "2024-03-01"], [1, 3])
    with pytest.raises(ConfirmationRequired):
        prepare(request)
    assert prepare(replace(request, gap_policy="zero activity")).values.tolist() == [1, 0, 3]
    assert prepare(replace(request, gap_policy="forward fill training")).values.isna().sum() == 1


def test_invalid_rows_and_anchor(request_factory):
    request = with_table(request_factory(), ["bad", "2024-02-01"], [1, 3])
    with pytest.raises(InputError):
        prepare(request)
    assert prepare(replace(request, invalid_policy="exclude")).diagnostics["excluded_rows"] == 1
    with pytest.raises(ConfirmationRequired):
        prepare(replace(request_factory(), frequency="ME"))


def test_numeric_conventions():
    assert parse_numbers(pd.Series(["$1,234.50", "(25.00)"]), "comma thousands").tolist() == [
        1234.5,
        -25,
    ]
    assert parse_numbers(pd.Series(["1.234,50"]), "decimal comma").iloc[0] == 1234.5
    assert pd.isna(parse_numbers(pd.Series(["12,34"]), "comma thousands").iloc[0])


def test_causal_fill_is_bounded():
    assert training_values(pd.Series([1, np.nan, 3]), "forward fill training").tolist() == [1, 1, 3]
    with pytest.raises(InputError):
        training_values(pd.Series([np.nan, 2]), "forward fill training")
    with pytest.raises(InputError):
        training_values(pd.Series([1, *([np.nan] * 4)]), "forward fill training")


def test_period_limit_precedes_resample(request_factory, monkeypatch):
    import forecasting_app.preprocessing as module

    monkeypatch.setattr(module, "MAX_PERIODS", 3)
    request = with_table(
        request_factory(row_kind="transactions", frequency="D"),
        ["2024-01-01", "2024-02-01"],
        [1, 2],
    )
    with pytest.raises(InputError, match="too many periods"):
        prepare(request)


def test_timezone_not_silently_removed(request_factory):
    request = with_table(request_factory(), ["2024-01-01T00:00:00Z"], [1])
    with pytest.raises(InputError, match="timezone"):
        prepare(request)


def test_invalid_exclusion_cannot_become_zero_truth(request_factory):
    request = with_table(
        request_factory(invalid_policy="exclude", gap_policy="zero activity"),
        ["2024-01-01", "2024-02-01", "2024-03-01"],
        [1, "invalid", 3],
    )
    result = prepare(request)
    assert pd.isna(result.values.iloc[1])
    assert result.diagnostics["invalid_target_period_count"] == 1
