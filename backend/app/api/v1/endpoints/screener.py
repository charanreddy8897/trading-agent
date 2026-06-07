from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.analysis.scoring import universe_scorer
from app.core.database import get_db
from app.schemas.responses import ScreenerRowSchema
from app.universe.sectors import SECTORS

router = APIRouter()

_VALID_SECTORS = frozenset(SECTORS.keys()) | {"all"}


@router.get("/ranked", response_model=list[ScreenerRowSchema])
async def ranked_screener(
    sector:    str = Query(default="all", description="Sector key or 'all'"),
    min_score: int = Query(default=0, ge=0, le=100, description="0–100"),
    db: Session = Depends(get_db),
):
    if sector not in _VALID_SECTORS:
        raise HTTPException(status_code=400, detail=f"Invalid sector. Valid: {sorted(_VALID_SECTORS)}")

    ranking = universe_scorer.rank_universe(db)
    rows    = ranking.rows

    if sector != "all":
        rows = [r for r in rows if r.sector == sector]
    if min_score > 0:
        rows = [r for r in rows if r.total >= min_score]

    return [
        ScreenerRowSchema(
            ticker=r.ticker, sector=r.sector,
            technical=r.technical, setup=r.setup, fundamental=r.fundamental, total=r.total,
            action=r.action, stage=r.stage, base_number=r.base_number,
            adr_pct=r.adr_pct, atr_extension=r.atr_extension, rvol=r.rvol,
            peg_active=r.peg_active,
        )
        for r in rows
    ]
