from prometheus_client import Counter, Histogram

REQUEST_LATENCY = Histogram(
    "request_latency_seconds",
    "Request latency in seconds",
    labelnames=["method", "endpoint", "status_code"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

PREDICTION_COUNT = Counter(
    "predictions_total",
    "Total number of predictions",
    labelnames=["label"],
)

REQUEST_COUNT = Counter(
    "requests_total",
    "Total number of requests",
    labelnames=["method", "endpoint", "status_code"],
)

ERROR_COUNT = Counter(
    "prediction_errors_total",
    "Total number of prediction errors",
)
