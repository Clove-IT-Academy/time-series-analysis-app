"""Deterministic, explicit business-data preparation without learned imputation."""

import re

import numpy as np
import pandas as pd

from .config import FREQUENCIES, MAX_PERIODS
from .contracts import ConfirmationRequired, ForecastRequest, InputError, SeriesData


def parse_numbers(values: pd.Series, convention: str) -> pd.Series:
    if convention not in ("plain", "comma thousands", "decimal comma"):
        raise InputError("Choose a supported numeric convention.")
    text = values.astype("string").str.strip()
    if convention == "plain":
        return pd.to_numeric(text, errors="coerce").astype(float)
    text = text.str.replace(r"[$€£₹\s]", "", regex=True)
    text = text.str.replace(r"^\((.*)\)$", r"-\1", regex=True)
    if convention == "comma thousands":
        pattern = r"^[+-]?(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?$"
        valid = text.str.match(pattern, na=False)
        text = text.where(valid).str.replace(",", "", regex=False)
    else:
        pattern = r"^[+-]?(?:\d{1,3}(?:\.\d{3})+|\d+)(?:,\d+)?$"
        valid = text.str.match(pattern, na=False)
        text = (
            text.where(valid).str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
        )
    return pd.to_numeric(text, errors="coerce").astype(float)


def parse_dates(values: pd.Series, date_format: str) -> pd.Series:
    if date_format not in ("ISO8601", "%d/%m/%Y", "%m/%d/%Y"):
        raise InputError("Choose ISO dates, day/month/year or month/day/year.")
    # Reject timezone-bearing data rather than dropping timezone semantics.
    for value in values.dropna():
        if getattr(value, "tzinfo", None) is not None or re.search(
            r"(?:Z|[+-]\d{2}:?\d{2})$", str(value)
        ):
            raise InputError(
                "Use consistently timezone-naive business dates; timezone offsets are unsupported."
            )
    if pd.api.types.is_numeric_dtype(values):
        raise InputError("Numeric date codes are unsupported; supply actual dates.")
    return pd.to_datetime(values, format=date_format, errors="coerce")


def suggest_frequency(values: pd.Series) -> str | None:
    try:
        dates = (
            pd.DatetimeIndex(pd.to_datetime(values, format="mixed", errors="coerce").dropna())
            .unique()
            .sort_values()
        )
        if len(dates) < 3:
            return None
        if dates.is_month_start.all():
            return "MS"
        if dates.is_month_end.all():
            return "ME"
        inferred = pd.infer_freq(dates)
        return inferred if inferred in FREQUENCIES else None
    except (ValueError, TypeError):
        return None


def prepare(request: ForecastRequest) -> SeriesData:
    table = request.upload.table
    if request.date_column not in table or request.target_column not in table:
        raise InputError("Selected columns are not present in the active table.")
    if request.date_column == request.target_column:
        raise InputError("Date and target must be different columns.")
    if request.frequency not in FREQUENCIES:
        raise InputError("Unsupported frequency. Choose daily, anchored weekly or monthly.")
    if request.row_kind not in ("transactions", "summary"):
        raise ConfirmationRequired("Confirm whether rows are transactions or periodic summaries.")
    if request.gap_policy not in ("unresolved", "zero activity", "forward fill training"):
        raise InputError("Unsupported missing-period policy.")
    if request.invalid_policy not in ("reject", "exclude") or request.duplicate_policy not in (
        "reject",
        "sum",
        "mean",
    ):
        raise InputError("Unsupported invalid-row or summary-duplicate policy.")
    if request.aggregation not in ("sum", "mean"):
        raise InputError("Choose sum or mean aggregation explicitly.")
    dates = parse_dates(table[request.date_column], request.date_format)
    numbers = parse_numbers(table[request.target_column], request.number_format)
    if (numbers.dropna().abs() > 1e15).any():
        raise InputError(
            "Monetary values must have absolute magnitude at most 1e15 in this prototype."
        )
    invalid = dates.isna() | ~np.isfinite(numbers)
    excluded = int(invalid.sum())
    if excluded and request.invalid_policy == "reject":
        raise InputError(
            f"{excluded} rows have invalid dates or numeric targets. Correct them or explicitly exclude them."
        )
    # Retain known dates of invalid targets as unknown periods, even when rows are
    # explicitly excluded. Exclusion must not turn incomplete reporting into zero truth.
    bad_target_dates = dates[dates.notna() & ~np.isfinite(numbers)]
    work = pd.DataFrame(
        {"date": dates[dates.notna()], "value": numbers[dates.notna()]}
    ).sort_values("date")
    if work.empty:
        raise InputError("No usable rows remain after parsing.")
    # Bound the calendar span before resampling/date_range can allocate empty bins.
    first_date, last_date = work.date.min(), work.date.max()
    days = (last_date.date() - first_date.date()).days
    estimated = (
        days + 1
        if request.frequency == "D"
        else days // 7 + 2
        if request.frequency.startswith("W-")
        else (last_date.year - first_date.year) * 12 + last_date.month - first_date.month + 1
    )
    if estimated > MAX_PERIODS:
        raise InputError("Date range creates too many periods; choose a coarser frequency.")
    if request.row_kind == "summary":
        if not work.date.eq(work.date.dt.normalize()).all():
            raise InputError("Periodic summaries must use date-only period labels.")
        duplicate_count = int(work.date.duplicated().sum())
        if duplicate_count and request.duplicate_policy == "reject":
            raise ConfirmationRequired(
                "Repeated summary dates require an explicit sum/mean duplicate policy."
            )
        raw = work.groupby("date").value.agg(
            request.duplicate_policy if duplicate_count else "first"
        )
        # Summary dates must already be aligned: no hidden reaggregation into bins.
        aligned = pd.date_range(raw.index.min(), raw.index.max(), freq=request.frequency)
        if not raw.index.isin(aligned).all():
            raise ConfirmationRequired(
                "Summary dates do not match this cadence/anchor. Choose the correct frequency."
            )
        series = raw
    else:
        duplicate_count = 0
        raw = work.set_index("date").value
        # Calendar binning is deterministic; folds split only between complete output periods.
        grouped = raw.resample(request.frequency)
        series = grouped.sum(min_count=1) if request.aggregation == "sum" else grouped.mean()
    start, end = series.index.min(), series.index.max()
    approx_periods = (end - start).days + 1
    if request.frequency == "D" and approx_periods > MAX_PERIODS:
        raise InputError("Date range creates too many periods; choose a coarser frequency.")
    if (end.year - start.year) * 12 + end.month - start.month > MAX_PERIODS:
        raise InputError("Date range exceeds the period limit.")
    grid = pd.date_range(start, end, freq=request.frequency)
    if len(grid) > MAX_PERIODS:
        raise InputError("Prepared series exceeds 50,000 periods.")
    if np.isinf(series).any():
        raise InputError("Aggregation produced non-finite values; review amounts and aggregation.")
    series = series.reindex(grid).astype(float).rename(request.target)
    invalid_target_periods = []
    if len(bad_target_dates):
        marked = (
            pd.Series(1, index=pd.DatetimeIndex(bad_target_dates)).resample(request.frequency).sum()
        )
        invalid_target_periods = marked.index[marked.gt(0)].intersection(series.index).tolist()
        series.loc[invalid_target_periods] = np.nan
    gaps = series.index[series.isna()].strftime("%Y-%m-%d").tolist()
    if gaps and request.gap_policy == "zero activity":
        series = series.fillna(0.0)
        # Known invalid targets are not evidence of zero activity.
        series.loc[invalid_target_periods] = np.nan
    elif gaps and request.gap_policy == "unresolved":
        raise ConfirmationRequired(
            f"{len(gaps)} missing periods: confirm zero activity or a training-only fill policy."
        )
    return SeriesData(
        request.target,
        request.frequency,
        series,
        request.aggregation,
        gaps,
        {
            "input_rows": len(table),
            "usable_rows": int((~invalid).sum()),
            "invalid_target_period_count": len(invalid_target_periods),
            "excluded_rows": excluded,
            "periods": len(series),
            "missing_period_count": len(gaps),
            "summary_duplicates_aggregated": duplicate_count,
            "row_kind": request.row_kind,
            "start": start.isoformat(),
            "end": end.isoformat(),
            "frequency": request.frequency,
            "gap_policy": request.gap_policy,
            "zero_values": int(series.eq(0).sum()),
            "negative_values": int(series.lt(0).sum()),
            "transactions_retained": request.row_kind == "transactions",
        },
    )


def training_values(series: pd.Series, policy: str) -> pd.Series:
    """Causal bounded fill only within the history supplied by the caller."""
    clean = series.ffill(limit=3) if policy == "forward fill training" else series.copy()
    if not np.isfinite(clean).all():
        raise InputError(
            "Training history has unresolved gaps (fill limit: 3 periods); repair source data."
        )
    return clean
