"""
SOC-LLM Audit Platform - FastAPI Application Entry Point
"""
import traceback
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.config import get_settings
from app.api.v1 import router as api_v1_router
from app.api.websocket import router as ws_router
from app.infrastructure.database import init_db
from app.core.audit_module.realtime_risk_monitor import risk_monitor

logger = structlog.get_logger()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting SOC-LLM Audit Platform", version=settings.APP_VERSION)
    await init_db()
    await risk_monitor.start()
    yield
    await risk_monitor.stop()
    logger.info("Shutting down SOC-LLM Audit Platform")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Módulo de Auditoría Ético-Normativa para Pipeline SOC con LLM",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan,
)

# Security Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

if not settings.DEBUG:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*.soc-llm.local", "localhost"],
    )

# API Routes
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
app.include_router(ws_router, prefix="/ws")


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    tb = traceback.format_exception(type(exc), exc, exc.__traceback__)
    logger.error("Unhandled exception", path=str(request.url), error=str(exc), traceback="".join(tb))
    return JSONResponse(status_code=500, content={"detail": str(exc), "traceback": "".join(tb[-3:])})


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "environment": settings.ENVIRONMENT,
    }
