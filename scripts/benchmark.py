"""Record synthetic local timings/allocations; not a capacity certification."""

import json
import platform
import time
import tracemalloc
from pathlib import Path

import numpy as np
import pandas as pd

from forecasting_app.contracts import ForecastRequest
from forecasting_app.ingestion import read_upload
from forecasting_app.service import forecast


def run():
    output = {
        "machine": platform.machine(),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "cases": [],
    }
    for count, names in [
        (168, ("Naive", "Seasonal naive", "Simple smoothing", "Holt", "Holt-Winters", "ARIMA")),
        (50_000, ("Naive",)),
    ]:
        if count == 168:
            data = (Path(__file__).parents[1] / "sample_data/monthly_transactions.csv").read_bytes()
            frequency, kind, width = "MS", "transactions", 12
        else:
            frame = pd.DataFrame(
                {
                    "Date": pd.date_range("1850-01-01", periods=count, freq="D").strftime(
                        "%Y-%m-%d"
                    ),
                    "Sales": 100 + np.arange(count) % 7,
                }
            )
            data = frame.to_csv(index=False).encode()
            frequency, kind, width = "D", "summary", 30
        tracemalloc.start()
        start = time.perf_counter()
        upload = read_upload(data, "benchmark.csv")
        parsed = time.perf_counter()
        response = forecast(
            ForecastRequest(
                upload,
                "Date",
                "Sales",
                confirmed=True,
                row_kind=kind,
                frequency=frequency,
                validation_periods=width,
                horizon=12,
                models=names,
            )
        )
        end = time.perf_counter()
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        output["cases"].append(
            {
                "rows": count,
                "bytes": len(data),
                "candidates": list(names),
                "folds": 1,
                "parse_seconds": round(parsed - start, 3),
                "engine_seconds": round(end - parsed, 3),
                "peak_traced_mib": round(peak / 1024**2, 2),
                "status": response.status,
            }
        )
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    run()
