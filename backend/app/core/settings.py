"""Application settings loaded from environment via Pydantic BaseSettings."""
from __future__ import annotations

from pathlib import Path

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Search for .env in the backend dir first, then the project root.
_HERE = Path(__file__).resolve().parent          # app/core/
_ENV_FILES = (
    str(_HERE.parent.parent / ".env"),           # backend/.env  (if it exists)
    str(_HERE.parent.parent.parent / ".env"),    # trading_agent/.env
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ENV_FILES,
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ── API keys ──────────────────────────────────────────────────────────────
    anthropic_api_key: str = Field(default="", alias="ANTHROPIC_API_KEY")
    finnhub_api_key: str = Field(default="", alias="FINNHUB_API_KEY")
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets", alias="ALPACA_BASE_URL"
    )

    # ── Robinhood MCP (deprecated direct integration) ─────────────────────────
    # DEPRECATED: Direct robin-stocks integration removed in favor of MCP
    # Use Claude Code with Robinhood MCP server instead
    # These fields kept for backward compatibility but are no longer used
    rh_username: str = Field(default="", alias="RH_USERNAME")
    rh_password: str = Field(default="", alias="RH_PASSWORD")
    rh_totp: str = Field(default="", alias="RH_TOTP")

    @computed_field  # type: ignore[misc]
    @property
    def rh_enabled(self) -> bool:
        """DEPRECATED: Always returns False. Use Robinhood MCP instead."""
        return False  # Force disabled - use MCP endpoint instead

    # ── Slack ─────────────────────────────────────────────────────────────────
    slack_bot_token: str = Field(default="", alias="SLACK_BOT_TOKEN")
    slack_channel_briefing: str = Field(default="", alias="SLACK_CHANNEL_BRIEFING")
    slack_channel_alerts: str = Field(default="", alias="SLACK_CHANNEL_ALERTS")
    slack_channel_orders: str = Field(default="", alias="SLACK_CHANNEL_ORDERS")
    slack_channel_emergency: str = Field(default="", alias="SLACK_CHANNEL_EMERGENCY")

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str = Field(
        default="postgresql://trading_user:trading_pass@localhost:5432/trading_agent",
        alias="DATABASE_URL",
    )

    # ── Trading mode ──────────────────────────────────────────────────────────
    trading_mode: str = Field(default="paper", alias="TRADING_MODE")

    # ── Robinhood MCP bridge ──────────────────────────────────────────────────
    # A static secret key that your local Claude Code session sends in the
    # X-Sync-Key header when posting to /portfolio/robinhood-sync.
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    robinhood_sync_key: str = Field(default="", alias="ROBINHOOD_SYNC_KEY")

    # ── Entry rules ───────────────────────────────────────────────────────────
    peg_gap_min_pct: float = 3.0
    peg_volume_multiple: float = 2.0
    entry_ema: int = 9
    add_ema: int = 21

    # ── Position sizing ───────────────────────────────────────────────────────
    max_position_pct: float = 10.0
    tranche_1_pct: float = 5.0
    tranche_2_pct: float = 5.0

    # ── ADR sweet-spot ────────────────────────────────────────────────────────
    adr_min: float = 3.0
    adr_max: float = 10.0

    # ── Sell / trim rules ─────────────────────────────────────────────────────
    atr_trim_threshold: float = 3.0
    late_stage_base: int = 3
    stop_loss_max_pct: float = 10.0

    # ── Risk guards ───────────────────────────────────────────────────────────
    max_daily_loss_pct: float = 3.0
    max_daily_loss_usd: float = 5000.0
    max_weekly_loss_pct: float = 7.0
    max_drawdown_pct: float = 15.0
    max_open_positions: int = 20
    max_sector_exposure_pct: float = 40.0
    max_correlated_exposure_pct: float = 60.0

    # ── Earnings ──────────────────────────────────────────────────────────────
    earnings_gap_down_wait_days: int = 3

    # ── Market hours (ET) ─────────────────────────────────────────────────────
    market_open: str = "09:30"
    market_close: str = "16:00"
    briefing_time_pt: str = "07:00"
    alert_check_interval_sec: int = 900

    # ── Data ──────────────────────────────────────────────────────────────────
    price_history_days: int = 365
    lookback_days: int = 90
    news_lookback_days: int = 7

    # ── Analysis concurrency ──────────────────────────────────────────────────
    claude_concurrency: int = 5
    claude_timeout_sec: float = 30.0
    claude_model: str = "claude-sonnet-4-5"

    # ── JWT Auth ──────────────────────────────────────────────────────────────
    # Generate with: python -c "import secrets; print(secrets.token_hex(32))"
    jwt_secret_key: str = Field(default="change-me-in-production", alias="JWT_SECRET_KEY")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 30
    jwt_refresh_token_expire_days: int = 7
    # Short-lived token issued after password check, before TOTP verification
    jwt_temp_token_expire_minutes: int = 5

    # TOTP issuer name shown in the authenticator app
    totp_issuer: str = Field(default="TradingAgent", alias="TOTP_ISSUER")


settings = Settings()
