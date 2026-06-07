from __future__ import annotations
from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict


# ── Robinhood MCP sync payload (posted from local Claude Code session) ────────
class RobinhoodPositionPayload(BaseModel):
    ticker:        str
    shares:        float
    avg_cost:      float
    current_price: float
    entry_date:    Optional[date]  = None
    stop_loss:     Optional[float] = None


class RobinhoodPortfolioPayload(BaseModel):
    total_value: float
    cash:        float
    daily_pct:   float = 0.0


class RobinhoodSyncPayload(BaseModel):
    positions: list[RobinhoodPositionPayload]
    portfolio: RobinhoodPortfolioPayload


class RobinhoodSyncResponse(BaseModel):
    synced_positions: int
    total_value:      float
    status:           str


# ── Portfolio ────────────────────────────────────────────────────
class PortfolioSummarySchema(BaseModel):
    total_value:    float
    total_pnl:      float
    daily_change:   float
    daily_pct:      float
    position_count: int
    cash:           Optional[float] = None


class PositionSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ticker:          str
    shares:          float
    avg_cost:        float
    current_price:   float
    market_value:    float
    unrealized_pnl:  float
    unrealized_pct:  float
    sector:          str
    entry_date:      Optional[date]   = None
    stop_loss:       Optional[float]  = None
    tranche1_filled: bool = False
    tranche2_filled: bool = False


class SectorAllocationSchema(BaseModel):
    sector_pcts: dict[str, float]
    correlated:  dict[str, float]
    warnings:    list[str]


class PerformancePoint(BaseModel):
    date:  str
    value: float


# ── Screener ─────────────────────────────────────────────────────
class ScreenerRowSchema(BaseModel):
    ticker:        str
    sector:        str
    technical:     int
    setup:         int
    fundamental:   int
    total:         int
    action:        Optional[str]   = None
    stage:         Optional[int]   = None
    base_number:   Optional[int]   = None
    adr_pct:       Optional[float] = None
    atr_extension: Optional[float] = None
    rvol:          Optional[float] = None
    peg_active:    bool = False


# ── Analysis ─────────────────────────────────────────────────────
class AnalysisSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:          int
    ticker:      str
    analyzed_at: datetime
    conviction:  Optional[int]   = None
    action:      Optional[str]   = None
    entry_zone:  Optional[str]   = None
    stop_loss:   Optional[float] = None
    risk_reward: Optional[str]   = None
    stage:       Optional[str]   = None
    base_number: Optional[int]   = None
    reasoning:   Optional[str]   = None
    warnings:    Optional[list[str]] = None
    raw_json:    Optional[dict[str, Any]] = None


# ── PEG ──────────────────────────────────────────────────────────
class PegSetupSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:              int
    ticker:          str
    peg_date:        date
    peg_low:         float
    gap_pct:         float
    volume_multiple: float
    gap_filled:      bool
    created_at:      datetime
    sector:          Optional[str]   = None
    current_price:   Optional[float] = None
    entry_zone:      Optional[str]   = None


# ── Movers ───────────────────────────────────────────────────────
class MoverSchema(BaseModel):
    ticker:      str
    price:       float
    change_pct:  float
    volume:      Optional[int]   = None
    avg_volume:  Optional[float] = None
    rvol:        Optional[float] = None
    sector:      Optional[str]   = None


class MoversResponseSchema(BaseModel):
    gainers: list[MoverSchema]
    losers:  list[MoverSchema]


# ── News ─────────────────────────────────────────────────────────
class NewsItemSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:           int
    ticker:       Optional[str]      = None
    published_at: Optional[datetime] = None
    headline:     Optional[str]      = None
    summary:      Optional[str]      = None
    sentiment:    Optional[int]      = None
    source:       Optional[str]      = None
    category:     Optional[str]      = None
    url:          Optional[str]      = None


# ── Alerts ───────────────────────────────────────────────────────
class AlertSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id:         int
    ticker:     Optional[str]      = None
    alert_type: Optional[str]      = None
    message:    Optional[str]      = None
    severity:   Optional[str]      = None
    dismissed:  bool               = False
    created_at: Optional[datetime] = None


# ── System ───────────────────────────────────────────────────────
class HealthSchema(BaseModel):
    status:           str
    db:               str
    last_data_update: Optional[str] = None


class PipelineStatusSchema(BaseModel):
    running:    bool
    last_run:   Optional[str] = None
    message:    str
