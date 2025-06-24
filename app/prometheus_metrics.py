#!/bin/python3
from prometheus_client import Counter, Histogram, make_asgi_app


# Prometheus Metrics
REQUEST_COUNT = Counter(
    "request_count", "Total number of requests", ["method", "endpoint"])
REQUEST_LATENCY = Histogram(
    "request_latency_seconds", "Request latency in seconds", ["method", "endpoint"])


# Mounting the Prometheus metrics endpoint.
def mount_prometheus_endpoint(app):
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
