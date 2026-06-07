"""Sector and correlated-group exposure calculator."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

from sqlalchemy.orm import Session

from app.core.settings import settings
from app.models.db_models import Position
from app.universe.sectors import CORRELATED_GROUPS


@dataclass
class ExposureReport:
    """Full exposure analysis for the current portfolio."""

    sector_pcts: dict[str, float] = field(default_factory=dict)
    correlated:  dict[str, float] = field(default_factory=dict)
    warnings:    list[str]        = field(default_factory=list)


class ExposureCalculator:
    """Computes sector and correlated-group exposure as % of total portfolio value.

    Emits a warning whenever any single sector or correlated group exceeds its
    configured limit.
    """

    def __init__(
        self,
        max_sector_pct: float = settings.max_sector_exposure_pct,
        max_correlated_pct: float = settings.max_correlated_exposure_pct,
    ) -> None:
        self.max_sector_pct     = max_sector_pct
        self.max_correlated_pct = max_correlated_pct

    @classmethod
    def from_settings(cls) -> "ExposureCalculator":
        return cls(
            max_sector_pct=settings.max_sector_exposure_pct,
            max_correlated_pct=settings.max_correlated_exposure_pct,
        )

    # ── public interface ──────────────────────────────────────────────────────

    def calc_exposure(self, db: Session) -> ExposureReport:
        """Return an ExposureReport for the current open positions."""
        positions = db.query(Position).all()
        if not positions:
            return ExposureReport()

        total = sum(float(p.market_value or 0) for p in positions)
        if total == 0:
            return ExposureReport()

        # defaultdict accumulates market value per sector
        sector_vals: defaultdict[str, float] = defaultdict(float)
        for p in positions:
            sector_vals[p.sector or "Unknown"] += float(p.market_value or 0)

        sector_pcts = {s: round((v / total) * 100, 2) for s, v in sector_vals.items()}
        warnings    = list(self._sector_warnings(sector_pcts))
        correlated  = {}

        for group in CORRELATED_GROUPS:
            group_pct = sum(sector_pcts.get(s, 0) for s in group)
            key       = "+".join(group)
            correlated[key] = round(group_pct, 2)
            if group_pct > self.max_correlated_pct:
                warnings.append(
                    f"Correlated sectors ({key}) at {group_pct:.1f}% — "
                    f"limit {self.max_correlated_pct}%"
                )

        return ExposureReport(
            sector_pcts=sector_pcts,
            correlated=correlated,
            warnings=warnings,
        )

    # ── private helpers ───────────────────────────────────────────────────────

    def _sector_warnings(self, sector_pcts: dict[str, float]):
        """Generator that yields a warning string for each over-limit sector."""
        for sector, pct in sector_pcts.items():
            if pct > self.max_sector_pct:
                yield (
                    f"{sector} exposure {pct:.1f}% exceeds {self.max_sector_pct}% limit"
                )


exposure_calculator = ExposureCalculator.from_settings()
