from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.db_models import NewsItem
from app.schemas.responses import NewsItemSchema
from app.universe.sectors import SECTORS

router = APIRouter()

_VALID_SECTORS = frozenset(SECTORS.keys()) | {"all"}


@router.get("/feed", response_model=list[NewsItemSchema])
async def news_feed(
    sector: str = Query(default="all", description="Sector key or 'all'"),
    limit:  int = Query(default=50,  ge=1, le=200, description="Max 200 results"),
    offset: int = Query(default=0,   ge=0, description="Pagination offset"),
    db: Session = Depends(get_db),
):
    if sector not in _VALID_SECTORS:
        raise HTTPException(status_code=400, detail=f"Invalid sector. Valid: {sorted(_VALID_SECTORS)}")

    query = db.query(NewsItem).order_by(NewsItem.published_at.desc())
    if sector != "all":
        query = query.filter(NewsItem.ticker.in_(SECTORS[sector]))

    return [NewsItemSchema.model_validate(n) for n in query.offset(offset).limit(limit).all()]
