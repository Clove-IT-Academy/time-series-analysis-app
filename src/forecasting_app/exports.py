"""Pure user-initiated exports from the same engine response."""

import json
from dataclasses import asdict

import pandas as pd

from .contracts import ForecastResponse


def csv_bytes(rows: list[dict]) -> bytes:
    frame = pd.DataFrame(rows)
    # Only untrusted text is escaped; genuine signed numerical values remain numbers.
    for column in frame:
        frame[column] = frame[column].map(
            lambda v: (
                "'" + v
                if isinstance(v, str) and v.lstrip().startswith(("=", "+", "-", "@", "\t", "\r"))
                else v
            )
        )
    return frame.to_csv(index=False).encode("utf-8")


def forecast_csv(response: ForecastResponse) -> bytes:
    return csv_bytes(response.forecast_rows)


def comparison_rows(response: ForecastResponse) -> list[dict]:
    return [
        {
            "candidate": r.candidate_name,
            "status": r.status,
            **r.aggregate_metrics,
            "warnings": "; ".join(r.warnings),
            "errors": "; ".join(r.errors),
        }
        for r in response.comparison
    ]


def predictions_csv(response: ForecastResponse) -> bytes:
    return csv_bytes(
        [
            {
                **row,
                "candidate": r.candidate_name,
                "segment": "validation",
                "target": response.run_config["target"],
            }
            for r in response.comparison
            for row in r.predictions
        ]
    )


def metadata_json(response: ForecastResponse) -> str:
    return json.dumps(
        {
            "status": response.status,
            "message": response.message,
            "selected_model": response.selected_model,
            "run_config": response.run_config,
            "diagnostics": response.diagnostics,
            "warnings": response.warnings,
            "comparison": [asdict(r) for r in response.comparison],
        },
        indent=2,
        allow_nan=False,
    )
