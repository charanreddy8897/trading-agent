"""Slack notifier — posts messages with automatic exponential back-off retries."""
from __future__ import annotations

import logging
from typing import Any

import requests
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.exceptions import NotificationError
from app.core.settings import settings

logger = logging.getLogger(__name__)

_SLACK_API = "https://slack.com/api/chat.postMessage"

_SEVERITY_EMOJI: dict[str, str] = {
    "critical": "🚨",
    "warning":  "⚠️",
    "info":     "ℹ️",
}


class SlackNotifier:
    """Sends messages to named Slack channels.

    Channel keys (alerts, briefing, orders, emergency) are resolved to real
    channel IDs from the Settings object, so callers never hard-code them.
    """

    def __init__(self, token: str, channel_map: dict[str, str]) -> None:
        self._token      = token
        self._channel_map = channel_map
        self._headers     = {
            "Authorization": f"Bearer {token}",
            "Content-Type":  "application/json",
        }

    @classmethod
    def from_settings(cls) -> "SlackNotifier":
        return cls(
            token=settings.slack_bot_token,
            channel_map={
                "alerts":    settings.slack_channel_alerts,
                "briefing":  settings.slack_channel_briefing,
                "orders":    settings.slack_channel_orders,
                "emergency": settings.slack_channel_emergency,
            },
        )

    # ── public interface ──────────────────────────────────────────────────────

    def send(self, channel_key: str, text: str, blocks: list[dict] | None = None) -> bool:
        """Send *text* to the channel identified by *channel_key*.

        Returns True on success. Logs and returns False on failure rather than
        raising, so alert failures never crash the pipeline.
        """
        channel = self._channel_map.get(channel_key)
        if not channel:
            logger.error("Unknown Slack channel key: %s", channel_key)
            return False
        try:
            self._post_with_retry(channel, text, blocks)
            return True
        except NotificationError as exc:
            logger.error("Slack delivery failed: %s", exc)
            return False

    def send_alert(self, ticker: str, message: str, severity: str = "warning") -> bool:
        emoji = _SEVERITY_EMOJI.get(severity, "📢")
        return self.send("alerts", f"{emoji} *{ticker}*: {message}")

    def send_emergency(self, message: str) -> bool:
        return self.send("emergency", f"🆘 *EMERGENCY*: {message}")

    def send_order(self, ticker: str, action: str, shares: float, price: float) -> bool:
        text = f"📋 *ORDER* | {action} {shares} {ticker} @ ${price:.2f}"
        return self.send("orders", text)

    # ── private helpers ───────────────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type(NotificationError),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )
    def _post_with_retry(
        self, channel: str, text: str, blocks: list[dict] | None
    ) -> None:
        payload: dict[str, Any] = {"channel": channel, "text": text}
        if blocks:
            payload["blocks"] = blocks
        try:
            resp   = requests.post(_SLACK_API, headers=self._headers, json=payload, timeout=10)
            result = resp.json()
            if not result.get("ok"):
                raise NotificationError(f"Slack API error: {result.get('error')}")
        except requests.RequestException as exc:
            raise NotificationError(f"Slack HTTP error: {exc}") from exc


slack_notifier = SlackNotifier.from_settings()
