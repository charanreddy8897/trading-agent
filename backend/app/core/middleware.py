"""
FastAPI middleware stack:
  1. RequestLoggingMiddleware  — structured JSON request/response logs + correlation IDs
  2. SecurityHeadersMiddleware — OWASP security headers on every response
"""
from __future__ import annotations

import logging
import time
import uuid
from typing import Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging_config import sanitize
from app.core.metrics import metrics_publisher

logger = logging.getLogger(__name__)

# Headers whose values must never appear in logs
_REDACT_HEADERS = frozenset({
    "authorization", "x-sync-key", "cookie", "set-cookie",
})

# Paths excluded from request logging (too noisy)
_SKIP_LOG_PATHS = frozenset({"/health", "/api/health", "/docs", "/openapi.json"})


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Logs every request/response as a structured JSON record containing:
      - request_id (UUID4 — correlation ID, also returned in X-Request-ID header)
      - method, path, status_code, latency_ms
      - client_ip (from X-Forwarded-For or direct connection)
      - Sanitised query params (no token values)

    Metrics are also published to CloudWatch via metrics_publisher.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = str(uuid.uuid4())
        start      = time.perf_counter()

        # Attach request_id so route handlers can log it if needed
        request.state.request_id = request_id

        client_ip = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or (request.client.host if request.client else "unknown")
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            latency_ms = (time.perf_counter() - start) * 1000
            logger.error(
                "Unhandled exception",
                extra={
                    "request_id": request_id,
                    "method":     request.method,
                    "path":       request.url.path,
                    "client_ip":  client_ip,
                    "latency_ms": round(latency_ms, 2),
                    "error":      type(exc).__name__,
                },
            )
            metrics_publisher.record_request(500, latency_ms, request.url.path)
            raise

        latency_ms = (time.perf_counter() - start) * 1000
        status     = response.status_code

        if request.url.path not in _SKIP_LOG_PATHS:
            log_level = logging.WARNING if status >= 400 else logging.INFO
            logger.log(
                log_level,
                "%s %s %d",
                request.method,
                request.url.path,
                status,
                extra={
                    "request_id": request_id,
                    "method":     request.method,
                    "path":       request.url.path,
                    "status_code": status,
                    "latency_ms": round(latency_ms, 2),
                    "client_ip":  client_ip,
                    "query":      sanitize(dict(request.query_params)),
                },
            )

        metrics_publisher.record_request(status, latency_ms, request.url.path)
        response.headers["X-Request-ID"] = request_id
        return response


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds OWASP-recommended security headers to every response.
    Does not interfere with CORS (CORSMiddleware runs before this).
    """

    _HEADERS = {
        "X-Content-Type-Options":  "nosniff",
        "X-Frame-Options":         "DENY",
        "Referrer-Policy":         "strict-origin-when-cross-origin",
        "Permissions-Policy":      "geolocation=(), microphone=(), camera=()",
        # HSTS is set here but only takes effect over HTTPS (nginx handles the real HTTPS)
        "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
    }

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        for key, value in self._HEADERS.items():
            response.headers[key] = value
        return response
