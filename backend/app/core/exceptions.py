"""Custom exception hierarchy for the trading agent."""
from __future__ import annotations


class TradingAgentError(Exception):
    """Base for all trading-agent errors."""

    def __init__(self, message: str, ticker: str | None = None, **kwargs) -> None:
        super().__init__(message)
        self.message = message
        self.ticker = ticker


class DataFetchError(TradingAgentError):
    """Raised when data cannot be fetched from an external source."""


class RateLimitError(DataFetchError):
    """Raised when an external API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int | None = None, **kwargs) -> None:
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AnalysisError(TradingAgentError):
    """Raised when AI/Claude analysis fails."""


class SyncError(TradingAgentError):
    """Raised when a portfolio sync operation fails."""


class NotificationError(TradingAgentError):
    """Raised when a Slack/notification delivery fails."""


class DatabaseError(TradingAgentError):
    """Raised for unrecoverable database operation failures."""


class ConfigurationError(TradingAgentError):
    """Raised when required configuration is missing or invalid."""
