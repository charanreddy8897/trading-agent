"""FastAPI application entry-point."""
from __future__ import annotations

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.database import init_db
from app.core.logging_config import configure_logging
from app.core.metrics import metrics_publisher
from app.core.middleware import RequestLoggingMiddleware, SecurityHeadersMiddleware
from app.scheduler.jobs import trading_scheduler

# ── Structured JSON logging (replaces basicConfig) ────────────────────────────
configure_logging(level=os.getenv("LOG_LEVEL", "INFO"))

import logging
logger = logging.getLogger(__name__)

# ── Rate limiter (shared instance, imported by auth router) ───────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["200/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Trading Agent API")
    init_db()
    trading_scheduler.start()
    metrics_publisher.start()
    yield
    logger.info("Shutting down Trading Agent API")
    trading_scheduler.stop()


app = FastAPI(
    title="Trading Agent API",
    version="1.0.0",
    docs_url="/docs",
    description="AI-powered trading analysis backend",
    lifespan=lifespan,
)

# ── Rate limiter state ────────────────────────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware (added in reverse application order) ───────────────────────────
# Order applied to requests: CORS → Security → Logging → Routes
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:3000",
        "https://d28apcmg03a0s.cloudfront.net",  # CloudFront frontend
        "http://100.30.119.38",  # EC2 direct access
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],  # explicit, not wildcard
    allow_headers=["Authorization", "Content-Type", "X-Request-ID", "X-Sync-Key"],
    allow_credentials=True,
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", include_in_schema=False)
@app.get("/api/health", include_in_schema=False)
async def health():
    return {"status": "ok"}
