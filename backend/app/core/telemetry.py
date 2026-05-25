import os
import time
import json
import uuid
from datetime import datetime
from typing import Optional, Dict, Any, Callable, TYPE_CHECKING
from contextlib import contextmanager, asynccontextmanager

if TYPE_CHECKING:
    from fastapi import FastAPI
from loguru import logger

from opentelemetry import trace, propagate
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource, SERVICE_NAME, SERVICE_VERSION, DEPLOYMENT_ENVIRONMENT
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.trace import SpanKind, Status, StatusCode

from app.core.config import settings


def setup_telemetry() -> TracerProvider:
    resource = Resource.create({
        SERVICE_NAME: settings.PROJECT_NAME or "voise-ai",
        SERVICE_VERSION: os.getenv("APP_VERSION", "0.1.0"),
        DEPLOYMENT_ENVIRONMENT: settings.ENVIRONMENT or "dev",
    })

    provider = TracerProvider(resource=resource)

    # Always export to console in dev for debugging
    if settings.ENVIRONMENT != "prod":
        provider.add_span_processor(BatchSpanProcessor(ConsoleSpanExporter()))

    # OTLP endpoint (e.g., self-hosted collector, Grafana Tempo, SigNoz, etc.)
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    otlp_headers = os.getenv("OTEL_EXPORTER_OTLP_HEADERS")
    if otlp_endpoint:
        exporter = OTLPSpanExporter(
            endpoint=f"{otlp_endpoint.rstrip('/')}/v1/traces",
            headers=otlp_headers,
        )
        provider.add_span_processor(BatchSpanProcessor(exporter))

    trace.set_tracer_provider(provider)
    return provider


def setup_auto_instrumentation(app: "FastAPI"):
    """Wire OpenTelemetry ASGI middleware and library instrumentations.

    Must be called *after* FastAPI app creation. Receives the app instance
    to avoid circular imports.
    """
    otlp_endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT")
    if not otlp_endpoint:
        logger.info("OTEL_EXPORTER_OTLP_ENDPOINT not set — skipping auto-instrumentation")
        return

    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        FastAPIInstrumentor.instrument_app(app)

        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from app.core.database import engine
        SQLAlchemyInstrumentor().instrument(engine=engine.sync_engine)

        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()

        logger.info("OpenTelemetry auto-instrumentation enabled (fastapi, sqlalchemy, httpx)")
    except Exception as e:
        logger.warning(f"Auto-instrumentation skipped: {e}")


def get_tracer(name: str = "voise-ai") -> trace.Tracer:
    return trace.get_tracer(name)


# ─── Convenience helpers ─────────────────────────────────────────────


@asynccontextmanager
async def async_trace_span(
    tracer: trace.Tracer,
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            span.set_attributes(attributes)
        start = time.perf_counter()
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            span.set_attribute("duration_ms", round(elapsed_ms, 2))


@contextmanager
def sync_trace_span(
    tracer: trace.Tracer,
    name: str,
    attributes: Optional[Dict[str, Any]] = None,
    kind: SpanKind = SpanKind.INTERNAL,
):
    with tracer.start_as_current_span(name, kind=kind) as span:
        if attributes:
            span.set_attributes(attributes)
        start = time.perf_counter()
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(Status(StatusCode.ERROR, str(e)))
            raise
        finally:
            elapsed_ms = (time.perf_counter() - start) * 1000
            span.set_attribute("duration_ms", round(elapsed_ms, 2))


# ─── Persistent trace storage (DB fallback when no OTLP collector) ──


from app.core.database import SessionLocal
from app.models.analytics import TraceLog


def persist_span(
    session_id: str,
    span_name: str,
    span_type: str,
    duration_ms: float,
    attributes: Optional[Dict[str, Any]] = None,
    status_code: str = "OK",
    status_message: str = "",
    parent_span_id: Optional[str] = None,
    agent_id: Optional[str] = None,
    organization_id: Optional[str] = None,
):
    try:
        with SessionLocal() as db:
            log = TraceLog(
                id=str(uuid.uuid4()),
                session_id=session_id,
                parent_span_id=parent_span_id,
                span_name=span_name,
                span_type=span_type,
                duration_ms=round(duration_ms, 2),
                attributes=attributes or {},
                status_code=status_code,
                status_message=status_message,
                agent_id=agent_id,
                organization_id=organization_id,
            )
            db.add(log)
            db.commit()
    except Exception as e:
        logger.error(f"Failed to persist trace span: {e}")
