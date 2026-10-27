"""Explicit prototype safety limits; not throughput guarantees."""

MAX_BYTES = 10 * 1024 * 1024
MAX_ROWS = 50_000
MAX_COLUMNS = 100
MAX_SHEETS = 20
MAX_ZIP_BYTES = 50 * 1024 * 1024
MAX_PERIODS = 50_000
FREQUENCIES = ("D", "W-MON", "W-SUN", "MS", "ME")
MODEL_NAMES = ("Naive", "Seasonal naive", "Simple smoothing", "Holt", "Holt-Winters", "ARIMA")
DETECTION_THRESHOLD = 0.70
DETECTION_MARGIN = 0.12
