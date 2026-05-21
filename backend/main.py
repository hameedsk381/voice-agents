from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

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

@app.on_event("startup")
async def startup_event():
    # Verify JWT Secret key is not default in production
    from loguru import logger
    if settings.ENVIRONMENT == "prod" and settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.critical("SECURITY WARNING: Using default development SECRET_KEY in production! System startup halted.")
        raise ValueError("Cannot run in production environment with default development SECRET_KEY!")
    elif settings.SECRET_KEY == "your-super-secret-key-change-in-production":
        logger.warning("SECURITY WARNING: Using default development SECRET_KEY. Change this in production!")

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
