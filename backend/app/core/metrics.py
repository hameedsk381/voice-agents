import time
import psutil
import os
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable

# ─── Counters ─────────────────────────────────────────────────────────────────

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    labelnames=["method", "path", "status"],
)

http_requests_in_flight = Gauge(
    "http_requests_in_flight",
    "Current HTTP requests in flight",
)

calls_total = Counter(
    "voice_calls_total",
    "Total voice calls handled",
    labelnames=["agent_id", "outcome"],
)

call_duration_seconds = Histogram(
    "voice_call_duration_seconds",
    "Call duration in seconds",
    labelnames=["agent_id"],
    buckets=[10, 30, 60, 120, 300, 600, 1800, 3600],
)

turn_latency_ms = Histogram(
    "voice_turn_latency_ms",
    "Per-turn processing latency by phase",
    labelnames=["phase"],
    buckets=[50, 100, 200, 500, 1000, 2000, 5000, 10000],
)

cost_total = Counter(
    "voice_cost_total_usd",
    "Total accumulated cost in USD",
    labelnames=["model"],
)

errors_total = Counter(
    "voice_errors_total",
    "Total errors by type",
    labelnames=["error_type", "source"],
)

# ─── Gauges ───────────────────────────────────────────────────────────────────

active_sessions = Gauge(
    "voice_active_sessions",
    "Currently active voice sessions",
)

memory_usage_bytes = Gauge(
    "process_memory_usage_bytes",
    "Current process memory usage in bytes",
)

active_temporal_workflows = Gauge(
    "temporal_active_workflows",
    "Active Temporal workflow executions",
)

# ─── Middleware ────────────────────────────────────────────────────────────────


class PrometheusMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        if request.url.path == "/metrics":
            return await call_next(request)

        http_requests_in_flight.inc()
        start = time.perf_counter()
        try:
            response = await call_next(request)
            status = str(response.status_code)
            return response
        except Exception as exc:
            status = "500"
            raise
        finally:
            elapsed = (time.perf_counter() - start) * 1000
            http_requests_in_flight.dec()
            http_requests_total.labels(
                method=request.method,
                path=request.url.path,
                status=status,
            ).inc()
            turn_latency_ms.labels(phase="http_total").observe(elapsed)


# ─── Metrics endpoint handler ────────────────────────────────────────────────


def metrics_handler(request: Request) -> Response:
    memory_usage_bytes.set(psutil.Process(os.getpid()).memory_info().rss)
    data = generate_latest(REGISTRY)
    return Response(content=data, media_type="text/plain; charset=utf-8")
