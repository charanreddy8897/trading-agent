"""
Structured JSON logging with sensitive-data sanitisation.

Every log record emits a JSON object with consistent fields so
CloudWatch Logs Insights can query them directly:

  fields @timestamp, level, logger, request_id, message
  | filter status_code >= 500
  | sort @timestamp desc

Sensitive keys are replaced with "***REDACTED***" recursively so
tokens, passwords, and API keys never appear in logs.
"""
from __future__ import annotations

import logging
import logging.config
from collections.abc import MutableMapping
from typing import Any

from pythonjsonlogger.json import JsonFormatter

# ── Sensitive field names (case-insensitive, normalised to lowercase_underscore)
_SENSITIVE: frozenset[str] = frozenset({
    "password", "hashed_password",
    "token", "access_token", "refresh_token", "temp_token",
    "totp_secret", "totp_code", "code",
    "secret", "jwt_secret_key", "robinhood_sync_key",
    "api_key", "anthropic_api_key", "finnhub_api_key",
    "alpaca_api_key", "alpaca_secret_key",
    "slack_bot_token",
    "authorization", "x_sync_key",
    "rh_password", "rh_totp",
    "backup_codes",
})


def sanitize(obj: Any, _depth: int = 0) -> Any:
    """Recursively redact sensitive values. Max depth 5 to avoid infinite loops."""
    if _depth > 5:
        return obj
    if isinstance(obj, MutableMapping):
        return {
            k: "***REDACTED***"
            if k.lower().replace("-", "_") in _SENSITIVE
            else sanitize(v, _depth + 1)
            for k, v in obj.items()
        }
    if isinstance(obj, (list, tuple)):
        return type(obj)(sanitize(v, _depth + 1) for v in obj)
    return obj


class SanitisedJsonFormatter(JsonFormatter):
    """JsonFormatter that strips sensitive fields before emitting."""

    def add_fields(self, log_record: dict, record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)
        # Rename level → level for consistency
        if "levelname" in log_record:
            log_record["level"] = log_record.pop("levelname")
        # Sanitise any extra kwargs passed to the log call
        for key in list(log_record.keys()):
            if key.lower().replace("-", "_") in _SENSITIVE:
                log_record[key] = "***REDACTED***"


def configure_logging(level: str = "INFO") -> None:
    """
    Call once at app startup (main.py). Replaces basicConfig.

    Emits newline-delimited JSON to stdout.
    CloudWatch agent picks this up via the log group configured in AppStack.
    """
    fmt = SanitisedJsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        rename_fields={"asctime": "timestamp", "levelname": "level", "name": "logger"},
    )

    handler = logging.StreamHandler()
    handler.setFormatter(fmt)

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Silence noisy third-party loggers
    for noisy in ("botocore", "urllib3", "s3transfer", "httpcore", "httpx"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
