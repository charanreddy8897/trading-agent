"""Stop-loss and sell-signal manager — monitors open positions against risk rules."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.db_models import Alert, Position, TechnicalSignal

logger = logging.getLogger(__name__)


class SignalType(str, Enum):
    STOP_HIT    = "STOP_HIT"
    NEAR_STOP   = "NEAR_STOP"
    ATR_EXTENDED = "ATR_EXTENDED"
    LATE_STAGE  = "LATE_STAGE"
    STAGE4      = "STAGE4"


class Severity(str, Enum):
    CRITICAL = "critical"
    WARNING  = "warning"
    INFO     = "info"


@dataclass
class SellSignal:
    """A single sell/trim/warning signal for an open position."""

    ticker:   str
    type:     SignalType
    severity: Severity
    message:  str

    def to_dict(self) -> dict:
        return {
            "ticker":   self.ticker,
            "type":     self.type.value,
            "severity": self.severity.value,
            "message":  self.message,
        }


class StopManager:
    """Monitors every open position against stop-loss and technical sell rules.

    Encapsulates the complete set of sell conditions:
      - Stop hit / near-stop (hard price-based)
      - ATR extension (overextended, consider trimming)
      - Late-stage base (base #3+, watch for climax)
      - Stage 4 (Weinstein — mandatory exit signal)
    """

    NEAR_STOP_BUFFER = 1.03  # within 3% of stop

    def __init__(
        self,
        atr_trim_threshold: float = settings.atr_trim_threshold,
        late_stage_base: int = settings.late_stage_base,
    ) -> None:
        self.atr_trim_threshold = atr_trim_threshold
        self.late_stage_base    = late_stage_base

    @classmethod
    def from_settings(cls) -> "StopManager":
        return cls(
            atr_trim_threshold=settings.atr_trim_threshold,
            late_stage_base=settings.late_stage_base,
        )

    # ── public interface ──────────────────────────────────────────────────────

    def check_sell_signals(self, db: Session) -> list[SellSignal]:
        """Evaluate every open position and return all triggered sell signals."""
        positions = db.query(Position).all()
        signals: list[SellSignal] = []

        for pos in positions:
            tech = (
                db.query(TechnicalSignal)
                .filter(TechnicalSignal.ticker == pos.ticker)
                .order_by(TechnicalSignal.date.desc())
                .first()
            )
            signals.extend(self._evaluate_position(pos, tech))

        return signals

    def save_alerts(self, db: Session, signals: list[SellSignal]) -> None:
        """Persist sell signals as Alert records."""
        for s in signals:
            db.add(Alert(
                ticker=s.ticker,
                alert_type=s.type.value,
                message=s.message,
                severity=s.severity.value,
            ))
        db.commit()

    # ── private helpers ───────────────────────────────────────────────────────

    def _evaluate_position(
        self, pos: Position, tech: TechnicalSignal | None
    ) -> list[SellSignal]:
        """Return all signals triggered for a single position."""
        results: list[SellSignal] = []
        ticker        = pos.ticker
        current_price = float(pos.current_price or 0)
        stop_loss     = float(pos.stop_loss or 0)

        # Price-based stop checks
        if stop_loss:
            if current_price <= stop_loss:
                results.append(SellSignal(
                    ticker=ticker,
                    type=SignalType.STOP_HIT,
                    severity=Severity.CRITICAL,
                    message=f"{ticker} hit stop loss ${stop_loss:.2f}",
                ))
            elif current_price <= stop_loss * self.NEAR_STOP_BUFFER:
                results.append(SellSignal(
                    ticker=ticker,
                    type=SignalType.NEAR_STOP,
                    severity=Severity.WARNING,
                    message=f"{ticker} within 3% of stop ${stop_loss:.2f}",
                ))

        # Technical sell conditions
        if tech:
            results.extend(self._technical_signals(ticker, tech))

        return results

    def _technical_signals(self, ticker: str, tech: TechnicalSignal) -> list[SellSignal]:
        results: list[SellSignal] = []

        if tech.atr_extension and float(tech.atr_extension) >= self.atr_trim_threshold:
            results.append(SellSignal(
                ticker=ticker,
                type=SignalType.ATR_EXTENDED,
                severity=Severity.WARNING,
                message=(
                    f"{ticker} ATR extension {float(tech.atr_extension):.1f}x "
                    f"— consider trimming 1/3"
                ),
            ))

        if tech.base_number and tech.base_number >= self.late_stage_base:
            results.append(SellSignal(
                ticker=ticker,
                type=SignalType.LATE_STAGE,
                severity=Severity.INFO,
                message=f"{ticker} is in Base #{tech.base_number} — late stage, watch for climax",
            ))

        if tech.weinstein_stage == 4:
            results.append(SellSignal(
                ticker=ticker,
                type=SignalType.STAGE4,
                severity=Severity.CRITICAL,
                message=f"{ticker} has entered Stage 4 — exit signal",
            ))

        return results


stop_manager = StopManager.from_settings()
