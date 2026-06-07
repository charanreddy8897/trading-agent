"""Portfolio tracker — persists positions and snapshots from any data source."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date

from sqlalchemy.orm import Session

from app.models.db_models import Position, PortfolioSnapshot
from app.universe.sectors import TICKER_SECTOR

logger = logging.getLogger(__name__)


@dataclass
class PositionMetrics:
    """Computed P&L metrics for a single open position."""

    ticker: str
    shares: float
    avg_cost: float
    current_price: float
    market_value: float
    unrealized_pnl: float
    unrealized_pct: float
    sector: str
    entry_date: date | None = None
    stop_loss: float | None = None

    @classmethod
    def compute(
        cls,
        ticker: str,
        shares: float,
        avg_cost: float,
        current_price: float,
        entry_date: date | None = None,
        stop_loss: float | None = None,
    ) -> "PositionMetrics":
        market_value   = shares * current_price
        unrealized_pnl = (current_price - avg_cost) * shares
        unrealized_pct = ((current_price - avg_cost) / avg_cost * 100) if avg_cost else 0.0
        return cls(
            ticker=ticker,
            shares=shares,
            avg_cost=avg_cost,
            current_price=current_price,
            market_value=market_value,
            unrealized_pnl=unrealized_pnl,
            unrealized_pct=unrealized_pct,
            sector=TICKER_SECTOR.get(ticker, "Unknown"),
            entry_date=entry_date,
            stop_loss=stop_loss,
        )


class PortfolioTracker:
    """CRUD layer for positions and portfolio snapshots."""

    # ── public interface ──────────────────────────────────────────────────────

    def upsert_position(
        self,
        db: Session,
        ticker: str,
        shares: float,
        avg_cost: float,
        current_price: float,
        entry_date: date | None = None,
        stop_loss: float | None = None,
    ) -> Position:
        """Create or update the position record for *ticker*."""
        metrics = PositionMetrics.compute(ticker, shares, avg_cost, current_price, entry_date, stop_loss)
        pos     = db.query(Position).filter(Position.ticker == ticker).first()

        if pos:
            self._apply_metrics(pos, metrics)
        else:
            pos = Position(
                ticker=ticker,
                shares=metrics.shares,
                avg_cost=metrics.avg_cost,
                current_price=metrics.current_price,
                market_value=metrics.market_value,
                unrealized_pnl=metrics.unrealized_pnl,
                unrealized_pct=metrics.unrealized_pct,
                sector=metrics.sector,
                entry_date=metrics.entry_date or date.today(),
                stop_loss=metrics.stop_loss,
            )
            db.add(pos)

        db.commit()
        return pos

    def snapshot_portfolio(
        self,
        db: Session,
        total_value: float,
        cash: float,
        daily_change: float,
        daily_pct: float,
    ) -> None:
        """Append a portfolio-level snapshot for performance charting."""
        db.add(PortfolioSnapshot(
            total_value=total_value,
            cash=cash,
            daily_change=daily_change,
            daily_pct=daily_pct,
        ))
        db.commit()

    def get_summary(self, db: Session) -> dict:
        """Return aggregate portfolio metrics plus a list of individual positions."""
        positions = db.query(Position).all()
        total_value   = sum(float(p.market_value or 0) for p in positions)
        total_pnl     = sum(float(p.unrealized_pnl or 0) for p in positions)

        return {
            "total_value":    round(total_value,  2),
            "total_pnl":      round(total_pnl,    2),
            "position_count": len(positions),
            "positions": [self._position_to_dict(p) for p in positions],
        }

    # ── private helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _apply_metrics(pos: Position, m: PositionMetrics) -> None:
        pos.shares         = m.shares
        pos.avg_cost       = m.avg_cost
        pos.current_price  = m.current_price
        pos.market_value   = m.market_value
        pos.unrealized_pnl = m.unrealized_pnl
        pos.unrealized_pct = m.unrealized_pct
        if m.stop_loss is not None:
            pos.stop_loss  = m.stop_loss

    @staticmethod
    def _position_to_dict(p: Position) -> dict:
        return {
            "ticker":         p.ticker,
            "shares":         float(p.shares or 0),
            "avg_cost":       float(p.avg_cost or 0),
            "current_price":  float(p.current_price or 0),
            "market_value":   float(p.market_value or 0),
            "unrealized_pnl": float(p.unrealized_pnl or 0),
            "unrealized_pct": float(p.unrealized_pct or 0),
            "sector":         p.sector,
            "stop_loss":      float(p.stop_loss) if p.stop_loss else None,
        }


portfolio_tracker = PortfolioTracker()
