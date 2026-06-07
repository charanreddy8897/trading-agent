from fastapi import APIRouter, Depends

from app.api.v1.endpoints import (
    portfolio, screener, analysis,
    news, alerts, movers, peg, system,
)
from app.schemas.responses import RobinhoodSyncResponse
from app.auth.dependencies import get_current_user
from app.auth.router import router as auth_router

api_router = APIRouter()

# ── Public — auth endpoints (no JWT required) ─────────────────────────────────
api_router.include_router(auth_router)

# Add Robinhood sync endpoint (public, protected by sync key)
api_router.add_api_route(
    "/portfolio/robinhood-sync",
    portfolio.robinhood_sync,
    methods=["POST"],
    tags=["portfolio"],
    response_model=RobinhoodSyncResponse,
)

# ── Protected — all routes below require a valid JWT access token ─────────────
_auth = {"dependencies": [Depends(get_current_user)]}

api_router.include_router(portfolio.router, prefix="/portfolio", tags=["portfolio"], **_auth)
api_router.include_router(screener.router,  prefix="/screener",  tags=["screener"],  **_auth)
api_router.include_router(analysis.router,  prefix="/analysis",  tags=["analysis"],  **_auth)
api_router.include_router(news.router,      prefix="/news",      tags=["news"],      **_auth)
api_router.include_router(alerts.router,    prefix="/alerts",    tags=["alerts"],    **_auth)
api_router.include_router(movers.router,    prefix="/movers",    tags=["movers"],    **_auth)
api_router.include_router(peg.router,       prefix="/peg",       tags=["peg"],       **_auth)
api_router.include_router(system.router,    prefix="/system",    tags=["system"],    **_auth)
