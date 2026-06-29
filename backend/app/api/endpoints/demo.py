"""
Demo call endpoint — unauthenticated, rate-limited.

Lets any visitor trigger a real outbound call to their phone number
to hear the Voise AI agent live. Uses a pre-configured demo agent
(DEMO_AGENT_ID in settings) and Redis for abuse prevention.
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session
from loguru import logger

from app.core import database
from app.core.config import settings
from app.core.deps import get_current_user_required
from app.models import agent as agent_models

router = APIRouter()

# Rate-limit keys
_IP_PREFIX = "demo:ip:"
_PHONE_PREFIX = "demo:phone:"
_IP_MAX_PER_DAY = 3
_PHONE_MAX_PER_DAY = 1
_TTL = 86400  # 24 hours


def _redis():
    import redis as redis_mod
    return redis_mod.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        password=settings.REDIS_PASSWORD or None,
        decode_responses=True,
    )


def _check_rate_limit(r, key: str, max_calls: int) -> bool:
    """Returns True if the caller is within the rate limit."""
    count = int(r.get(key) or 0)
    if count >= max_calls:
        return False
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, _TTL)
    pipe.execute()
    return True


class DemoCallRequest(BaseModel):
    phone_number: str  # E.164 format, e.g. +919840012345
    scenario: str = "payment_reminder"  # payment_reminder | lead_qualification | appointment_booking


class PilotApplyRequest(BaseModel):
    name: str
    company: str
    industry: str
    volume: str
    phone_number: str
    email: str
    use_case: str


@router.post("/call")
async def request_demo_call(
    payload: DemoCallRequest,
    request: Request,
    db: Session = Depends(database.get_db),
):
    if not settings.DEMO_AGENT_ID:
        raise HTTPException(
            status_code=503,
            detail="Demo calls are not configured yet. Please contact us directly.",
        )

    # Normalise phone
    phone = payload.phone_number.strip()
    if not phone.startswith("+"):
        phone = f"+{phone}"
    if len(phone) < 10:
        raise HTTPException(status_code=422, detail="Invalid phone number.")

    # Rate limiting
    try:
        r = _redis()
        client_ip = request.client.host if request.client else "unknown"

        if not _check_rate_limit(r, f"{_IP_PREFIX}{client_ip}", _IP_MAX_PER_DAY):
            raise HTTPException(
                status_code=429,
                detail="Too many demo calls from this network. Try again tomorrow.",
            )
        if not _check_rate_limit(r, f"{_PHONE_PREFIX}{phone}", _PHONE_MAX_PER_DAY):
            raise HTTPException(
                status_code=429,
                detail="This number has already received a demo call today. Try again tomorrow.",
            )
    except HTTPException:
        raise
    except Exception as e:
        # Redis unavailable — allow call but log the issue
        logger.warning(f"Demo rate-limit Redis unavailable: {e}. Allowing call.")

    # India telephony compliance gate (DND / consent / calling hours / DLT)
    from app.services.call_compliance_service import CallComplianceService
    compliance = CallComplianceService(db)
    allowed, c_reason = compliance.check_call_allowed(
        phone,
        from_number=settings.TWILIO_PHONE_NUMBER,
    )
    if not allowed:
        logger.warning(f"Demo call to {phone} blocked by compliance: {c_reason}")
        _human = c_reason.replace("_", " ")
        if c_reason == "outside_calling_hours":
            raise HTTPException(status_code=403, detail="Demo calls are only available 9am–9pm IST. Please try during the day.")
        raise HTTPException(status_code=403, detail=f"Call not permitted — {_human}.")

    # Look up demo agent
    agent = db.query(agent_models.Agent).filter(
        agent_models.Agent.id == settings.DEMO_AGENT_ID,
        agent_models.Agent.is_active == True,
    ).first()
    if not agent:
        raise HTTPException(
            status_code=503,
            detail="Demo agent is not available. Please contact us directly.",
        )

    # Trigger outbound call via existing Ultravox/Twilio infrastructure
    try:
        from app.orchestration.ultravox_twilio import create_ultravox_twilio_call

        from_number = settings.TWILIO_PHONE_NUMBER
        if not from_number:
            raise HTTPException(status_code=503, detail="Telephony not configured.")

        result = await create_ultravox_twilio_call(
            db=db,
            agent=agent,
            call_direction="outbound",
            caller_id=from_number,
            called_number=phone,
            twilio_call_sid=None,
            outgoing_to=phone,
        )

        logger.info(f"Demo call initiated to {phone}, scenario={payload.scenario}, call_id={result.get('callId')}")
        return {"status": "calling", "message": "Your phone will ring within 60 seconds."}

    except HTTPException:
        raise
    except Exception as exc:
        logger.error(f"Demo call failed for {phone}: {exc}")
        raise HTTPException(status_code=500, detail="Call could not be initiated. Please try again.")


@router.post("/pilot-apply")
async def apply_for_pilot(payload: PilotApplyRequest, db: Session = Depends(database.get_db)):
    """Receive a pilot-program application and persist it for the team to triage."""
    from app.models.compliance import PilotApplication

    logger.info(
        "Pilot application received | "
        f"name={payload.name!r} company={payload.company!r} "
        f"industry={payload.industry!r} volume={payload.volume!r} "
        f"email={payload.email!r} phone={payload.phone_number!r}"
    )
    application = PilotApplication(
        name=payload.name,
        company=payload.company,
        industry=payload.industry,
        volume=payload.volume,
        phone_number=payload.phone_number,
        email=payload.email,
        use_case=payload.use_case,
        status="new",
    )
    db.add(application)
    db.commit()

    return {
        "status": "received",
        "message": "We'll be in touch within 48 hours.",
    }


@router.get("/pilot-applications")
async def list_pilot_applications(
    db: Session = Depends(database.get_db),
    current_user=Depends(get_current_user_required),
):
    """List pilot applications (authenticated — for the internal team to triage)."""
    from app.models.compliance import PilotApplication

    rows = db.query(PilotApplication).order_by(PilotApplication.created_at.desc()).all()
    return {
        "applications": [
            {
                "id": r.id,
                "name": r.name,
                "company": r.company,
                "industry": r.industry,
                "volume": r.volume,
                "phone_number": r.phone_number,
                "email": r.email,
                "use_case": r.use_case,
                "status": r.status,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ],
        "total": len(rows),
    }
