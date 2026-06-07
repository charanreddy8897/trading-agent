"""Position sizing — tranched Kelly-style entries with hard stop-loss cap."""
from __future__ import annotations

from dataclasses import dataclass

from app.core.settings import settings


@dataclass
class TranchePlan:
    """Complete position-size plan for a two-tranche entry."""

    tranche1_shares: float
    tranche1_value:  float
    tranche2_shares: float
    tranche2_value:  float
    max_position:    float
    risk_pct:        float
    within_max_risk: bool


class PositionSizer:
    """Computes tranche sizes and stop prices for a given portfolio value.

    Encapsulates the O'Neil two-tranche entry model:
      Tranche 1 — initial position at breakout / PEG reclaim
      Tranche 2 — add on confirmation (price holds above entry)
    """

    def __init__(
        self,
        portfolio_value: float,
        max_position_pct: float = settings.max_position_pct,
        tranche_1_pct: float = settings.tranche_1_pct,
        tranche_2_pct: float = settings.tranche_2_pct,
        stop_loss_max_pct: float = settings.stop_loss_max_pct,
    ) -> None:
        self.portfolio_value   = portfolio_value
        self.max_position_pct  = max_position_pct
        self.tranche_1_pct     = tranche_1_pct
        self.tranche_2_pct     = tranche_2_pct
        self.stop_loss_max_pct = stop_loss_max_pct

    # ── public interface ──────────────────────────────────────────────────────

    def size_tranches(self, entry_price: float, stop_price: float) -> TranchePlan:
        """Return a TranchePlan for the given entry/stop prices."""
        t1_value = self.portfolio_value * (self.tranche_1_pct  / 100)
        t2_value = self.portfolio_value * (self.tranche_2_pct  / 100)
        max_val  = self.portfolio_value * (self.max_position_pct / 100)

        t1_shares = t1_value / entry_price
        t2_shares = t2_value / entry_price
        risk_pct  = ((entry_price - stop_price) / entry_price) * 100

        return TranchePlan(
            tranche1_shares=round(t1_shares, 2),
            tranche1_value=round(t1_value,   2),
            tranche2_shares=round(t2_shares, 2),
            tranche2_value=round(t2_value,   2),
            max_position=round(max_val,       2),
            risk_pct=round(risk_pct,          2),
            within_max_risk=risk_pct <= self.stop_loss_max_pct,
        )

    # ── static helpers (no instance state needed) ─────────────────────────────

    @staticmethod
    def calc_stop_from_peg(peg_low: float, buffer: float = 0.01) -> float:
        """Stop = peg_low × (1 − buffer); default 1% below the PEG low."""
        return round(peg_low * (1 - buffer), 4)

    @staticmethod
    def calc_stop_from_sma50(sma50: float, buffer: float = 0.02) -> float:
        """Stop = SMA50 × (1 − buffer); default 2% below the 50-day MA."""
        return round(sma50 * (1 - buffer), 4)

    # ── class method factory ──────────────────────────────────────────────────

    @classmethod
    def for_portfolio(cls, portfolio_value: float) -> "PositionSizer":
        """Create a sizer bound to *portfolio_value* using settings defaults."""
        return cls(portfolio_value=portfolio_value)
