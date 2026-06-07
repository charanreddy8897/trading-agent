from sqlalchemy import (
    Column, Index, Integer, String, Numeric, BigInteger, Boolean,
    Date, DateTime, Text, SmallInteger, JSON, UniqueConstraint,
)
from sqlalchemy.sql import func
from app.core.database import Base


class User(Base):
    """Single-user auth table — only one row ever exists."""
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    username        = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    totp_secret     = Column(String, nullable=True)
    totp_enabled    = Column(Boolean, default=False)
    backup_codes    = Column(JSON, nullable=True)   # list of bcrypt-hashed one-time codes
    is_active       = Column(Boolean, default=True)
    created_at      = Column(DateTime, server_default=func.now())
    last_login      = Column(DateTime, nullable=True)


class DailyPrice(Base):
    __tablename__ = "daily_prices"

    id        = Column(Integer, primary_key=True, index=True)
    ticker    = Column(String(10), nullable=False, index=True)
    date      = Column(Date, nullable=False)
    open      = Column(Numeric(12, 4))
    high      = Column(Numeric(12, 4))
    low       = Column(Numeric(12, 4))
    close     = Column(Numeric(12, 4))
    volume    = Column(BigInteger)
    adj_close = Column(Numeric(12, 4))

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_daily_prices_ticker_date"),
        Index("ix_daily_prices_ticker_date", "ticker", "date"),
    )


class TechnicalSignal(Base):
    __tablename__ = "technical_signals"

    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String(10), nullable=False, index=True)
    date            = Column(Date, nullable=False)
    ema9            = Column(Numeric(12, 4))
    ema21           = Column(Numeric(12, 4))
    sma50           = Column(Numeric(12, 4))
    sma200          = Column(Numeric(12, 4))
    ma10w           = Column(Numeric(12, 4))
    ma30w           = Column(Numeric(12, 4))
    adr_pct         = Column(Numeric(8, 4))
    atr             = Column(Numeric(12, 4))
    atr_extension   = Column(Numeric(8, 4))
    rvol            = Column(Numeric(8, 4))
    weinstein_stage = Column(SmallInteger)
    base_number     = Column(SmallInteger)

    __table_args__ = (
        UniqueConstraint("ticker", "date", name="uq_technical_signals_ticker_date"),
        Index("ix_technical_signals_ticker_date", "ticker", "date"),
    )


class PegSetup(Base):
    __tablename__ = "peg_setups"

    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String(10), nullable=False, index=True)
    peg_date        = Column(Date, nullable=False)
    peg_low         = Column(Numeric(12, 4))
    gap_pct         = Column(Numeric(8, 4))
    volume_multiple = Column(Numeric(8, 4))
    gap_filled      = Column(Boolean, default=False)
    created_at      = Column(DateTime, server_default=func.now())

    __table_args__ = (
        UniqueConstraint("ticker", "peg_date", name="uq_peg_setups_ticker_date"),
        Index("ix_peg_setups_ticker_gap_filled", "ticker", "gap_filled"),
    )


class ClaudeAnalysis(Base):
    __tablename__ = "claude_analysis"

    id          = Column(Integer, primary_key=True, index=True)
    ticker      = Column(String(10), nullable=False, index=True)
    analyzed_at = Column(DateTime, server_default=func.now())
    conviction  = Column(SmallInteger)
    action      = Column(String(10))
    entry_zone  = Column(String(50))
    stop_loss   = Column(Numeric(12, 4))
    risk_reward = Column(String(20))
    stage       = Column(String(20))
    base_number = Column(SmallInteger)
    reasoning   = Column(Text)
    warnings    = Column(JSON)
    raw_json    = Column(JSON)

    __table_args__ = (
        Index("ix_claude_analysis_ticker_analyzed_at", "ticker", "analyzed_at"),
    )


class PortfolioSnapshot(Base):
    __tablename__ = "portfolio_snapshots"

    id           = Column(Integer, primary_key=True, index=True)
    snapshot_at  = Column(DateTime, server_default=func.now())
    total_value  = Column(Numeric(14, 2))
    cash         = Column(Numeric(14, 2))
    daily_change = Column(Numeric(14, 2))
    daily_pct    = Column(Numeric(8, 4))


class Position(Base):
    __tablename__ = "positions"

    id              = Column(Integer, primary_key=True, index=True)
    ticker          = Column(String(10), nullable=False, index=True, unique=True)
    shares          = Column(Numeric(12, 4))
    avg_cost        = Column(Numeric(12, 4))
    current_price   = Column(Numeric(12, 4))
    market_value    = Column(Numeric(14, 2))
    unrealized_pnl  = Column(Numeric(14, 2))
    unrealized_pct  = Column(Numeric(8, 4))
    sector          = Column(String(50))
    entry_date      = Column(Date)
    stop_loss       = Column(Numeric(12, 4))
    tranche1_filled = Column(Boolean, default=False)
    tranche2_filled = Column(Boolean, default=False)
    updated_at      = Column(DateTime, server_default=func.now(), onupdate=func.now())


class NewsItem(Base):
    __tablename__ = "news_items"

    id           = Column(Integer, primary_key=True, index=True)
    ticker       = Column(String(10), index=True)
    published_at = Column(DateTime, index=True)
    headline     = Column(Text)
    summary      = Column(Text)
    sentiment    = Column(SmallInteger)
    source       = Column(String(100))
    category     = Column(String(50))
    url          = Column(Text, unique=True)

    __table_args__ = (
        Index("ix_news_items_ticker_published_at", "ticker", "published_at"),
    )


class Alert(Base):
    __tablename__ = "alerts"

    id         = Column(Integer, primary_key=True, index=True)
    ticker     = Column(String(10), index=True)
    alert_type = Column(String(50))
    message    = Column(Text)
    severity   = Column(String(20))
    dismissed  = Column(Boolean, default=False, index=True)
    created_at = Column(DateTime, server_default=func.now())

    __table_args__ = (
        Index("ix_alerts_dismissed_created_at", "dismissed", "created_at"),
    )
