import asyncio
import time
import uuid
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging
from app.core.telemetry import setup_telemetry, setup_auto_instrumentation
from app.core.metrics import PrometheusMiddleware, metrics_handler

setup_logging()

# Initialize OpenTelemetry (non-blocking)
try:
    setup_telemetry()
except Exception as e:
    import logging
    logging.getLogger("voise").warning(f"Telemetry init skipped: {e}")

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

from slowapi.errors import RateLimitExceeded
from slowapi import _rate_limit_exceeded_handler
from app.core.limiter import limiter

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

from app.api.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

# ─── Observability middleware stack (order matters) ────────────────────
app.add_middleware(PrometheusMiddleware)

# Expose /metrics at the root level (outside /api/v1)
app.add_route("/metrics", metrics_handler, methods=["GET"], include_in_schema=False)

# Wire OTEL auto-instrumentation after app is fully constructed
try:
    setup_auto_instrumentation(app)
except Exception as e:
    import logging
    logging.getLogger("voise").warning(f"Auto-instrumentation skipped: {e}")

@app.on_event("startup")
async def startup_event():
    # Verify JWT Secret key is not default in production
    from loguru import logger
    if settings.ENVIRONMENT == "prod" and settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.critical("SECURITY WARNING: Using default development SECRET_KEY in production! System startup halted.")
        raise ValueError("Cannot run in production environment with default development SECRET_KEY!")
    elif settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.warning("SECURITY WARNING: Using default development SECRET_KEY. Change this in production!")

    # Auto-create tables for development (trace_logs, eval_runs, policy_rules, etc.)
    try:
        from app.core.database import engine, Base
        from app.models.analytics import TraceLog, EvalRun, EvalTestCaseResult
        from app.models.policy_rule import PolicyRule
        from app.models.checkpoint import CallCheckpoint
        from app.models.agent_capability import AgentCapability
        from app.models.agent_identity import AgentIdentity
        from app.models.workflow import SmsMessage
        from app.models.tenant import Organization  # Ensure organizations table is created
        from app.models.user import User  # Ensure users table has the new column
        from app.models.billing import Subscription, UsageRecord, RateCard
        from app.models.phone_number import PhoneNumber
        Base.metadata.create_all(bind=engine)

        # Add missing columns for existing tables (dev migration)
        from sqlalchemy import text
        missing_cols = [
            ("audit_logs", "signature", "TEXT"),
            ("audit_logs", "previous_hash", "VARCHAR(255)"),
            ("audit_logs", "chain_head", "BOOLEAN DEFAULT TRUE"),
        ]
        for table, col, col_type in missing_cols:
            try:
                with engine.connect() as conn:
                    conn.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_type}"))
                    conn.commit()
            except Exception:
                pass
        # Drop old unique constraint on agent_identities.agent_id to allow key history
        try:
            with engine.connect() as conn:
                result = conn.execute(text(
                    "SELECT constraint_name FROM information_schema.table_constraints "
                    "WHERE table_name='agent_identities' AND constraint_type='UNIQUE'"
                ))
                for row in result:
                    conn.execute(text(f"ALTER TABLE agent_identities DROP CONSTRAINT IF EXISTS {row[0]}"))
                conn.commit()
        except Exception:
            pass

        logger.info("Database tables synchronized (trace_logs, eval_runs, policy_rules, call_checkpoints, agent_capabilities, agent_identities, etc.)")

        # ── Multi-tenant migration / seeding ─────────────────────────
        # Add organization_id column to users table if missing
        try:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS organization_id VARCHAR"))
                conn.commit()
        except Exception:
            pass

        # Seed default organization
        from app.core.database import SessionLocal
        session = SessionLocal()
        try:
            default_org = session.query(Organization).filter(Organization.name == "default").first()
            if not default_org:
                default_org = Organization(
                    id=str(uuid.uuid4()),
                    name="default",
                    domain="default.local",
                    subscription_plan="free",
                    is_active=True,
                )
                session.add(default_org)
                session.commit()
                logger.info("Default organization created for multi-tenancy")

            # Associate existing users without an org to the default org
            orphan_users = session.query(User).filter(User.organization_id.is_(None)).all()
            for u in orphan_users:
                u.organization_id = default_org.id
            if orphan_users:
                session.commit()
                logger.info(f"Associated {len(orphan_users)} existing user(s) with default organization")

            # Seed default subscription for all orgs without one
            from app.models.billing import Subscription, SubscriptionStatus
            from datetime import date, datetime, timedelta
            all_orgs = session.query(Organization).all()
            for org in all_orgs:
                existing_sub = session.query(Subscription).filter(
                    Subscription.organization_id == org.id
                ).first()
                if not existing_sub:
                    today = date.today()
                    period_start = today.replace(day=1)
                    if today.month == 12:
                        period_end = period_start.replace(year=period_start.year + 1, month=1, day=1)
                    else:
                        period_end = period_start.replace(month=period_start.month + 1, day=1)
                    sub = Subscription(
                        organization_id=org.id,
                        plan=org.subscription_plan or "free",
                        status=SubscriptionStatus.TRIALING.value,
                        billing_period_start=period_start,
                        billing_period_end=period_end,
                        trial_starts_at=datetime.utcnow(),
                        trial_ends_at=datetime.utcnow() + timedelta(days=14),
                        auto_renew="true",
                    )
                    session.add(sub)
            session.commit()

        finally:
            session.close()

        # Seed default rate cards
        try:
            session = SessionLocal()
            from app.services.metering_service import MeteringService
            MeteringService(session).seed_default_rate_cards()
            session.close()
            logger.info("Rate cards seeded")
        except Exception as rate_err:
            logger.warning(f"Rate card seeding skipped: {rate_err}")

    except Exception as e:
        logger.warning(f"Table auto-creation / org seeding skipped: {e}")

    # Start background TTL cleanup for memories
    _background_tasks = []

    async def _memory_ttl_cleanup_loop():
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                from app.core.database import SessionLocal
                from app.services.memory import get_memory_service
                db = SessionLocal()
                try:
                    service = get_memory_service(db)
                    count = await service.run_ttl_cleanup()
                    if count:
                        logger.debug(f"Background TTL cleanup removed {count} expired memory entries")
                finally:
                    db.close()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Background TTL cleanup error: {e}")

    task = asyncio.create_task(_memory_ttl_cleanup_loop())
    _background_tasks.append(task)
    logger.info("Memory TTL cleanup background task started (interval: 5 min)")

# CORS: explicit origins + local dev regex (LAN IP, alternate ports)
_cors_origins = list(settings.BACKEND_CORS_ORIGINS)
_cors_origin_regex = None
if settings.ENVIRONMENT != "prod":
    _cors_origin_regex = (
        r"https?://("
        r"localhost|127\.0\.0\.1|"
        r"192\.168\.\d{1,3}\.\d{1,3}|"
        r"10\.\d{1,3}\.\d{1,3}\.\d{1,3}|"
        r"172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3}"
        r")(:\d+)?$"
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_origin_regex=_cors_origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "Voise AI"}
    
@app.get("/")
def root():
    return {"message": "Welcome to Voise AI API"}
