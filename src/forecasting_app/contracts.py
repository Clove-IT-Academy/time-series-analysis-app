"""Small typed domain objects; no Streamlit or fitted objects cross the boundary."""

from dataclasses import dataclass, field
from typing import Any

import pandas as pd


@dataclass
class UploadResult:
    table: pd.DataFrame
    source_name: str
    fingerprint: str
    sheet: str | None = None
    parse_warnings: list[str] = field(default_factory=list)


@dataclass
class ColumnCandidate:
    column_name: str
    role: str
    confidence: float
    evidence: list[str]
    alternatives: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class ForecastRequest:
    upload: UploadResult
    date_column: str
    target_column: str
    target: str = "sales"
    confirmed: bool = False
    row_kind: str = "transactions"
    aggregation: str = "sum"
    frequency: str = "MS"
    date_format: str = "ISO8601"
    number_format: str = "plain"
    gap_policy: str = "unresolved"
    duplicate_policy: str = "reject"
    invalid_policy: str = "reject"
    horizon: int = 12
    validation_periods: int = 12
    folds: int = 1
    seasonal_period: int = 12
    models: tuple[str, ...] = (
        "Naive",
        "Seasonal naive",
        "Simple smoothing",
        "Holt",
        "Holt-Winters",
        "ARIMA",
    )
    arima_order: tuple[int, int, int] = (1, 1, 1)
    primary_metric: str = "MAE"
    max_relative_error: float = 0.50
    allow_baseline: bool = True


@dataclass
class SeriesData:
    target: str
    frequency: str
    values: pd.Series
    aggregation: str
    missing_periods: list[str]
    diagnostics: dict[str, Any]


@dataclass
class EvaluationResult:
    candidate_name: str
    configuration: dict[str, Any]
    status: str
    fold_metrics: list[dict[str, Any]] = field(default_factory=list)
    aggregate_metrics: dict[str, float] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    predictions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class ForecastResponse:
    status: str
    message: str
    forecast_rows: list[dict[str, Any]] = field(default_factory=list)
    selected_model: str | None = None
    comparison: list[EvaluationResult] = field(default_factory=list)
    diagnostics: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    run_config: dict[str, Any] = field(default_factory=dict)
    series: SeriesData | None = None


class InputError(ValueError):
    """A controlled, non-sensitive input error."""


class ConfirmationRequired(InputError):
    """Input semantics must be confirmed before proceeding."""
