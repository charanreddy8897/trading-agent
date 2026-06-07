"""
Global pytest fixtures and configuration.

Fixtures defined here are available to all test modules.
"""
from __future__ import annotations

import os
import sys
from datetime import date, datetime
from typing import Generator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Add backend to path so tests can import app modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, get_db
from app.core.settings import Settings
from app.main import app
from app.models.db_models import (
    User,
    DailyPrice,
    TechnicalSignal,
    PegSetup,
    ClaudeAnalysis,
    Position,
    PortfolioSnapshot,
    NewsItem,
    Alert,
)


# ── Test Database ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_db_url():
    """Use in-memory SQLite for fast tests."""
    return "sqlite:///:memory:"


@pytest.fixture(scope="session")
def test_engine(test_db_url):
    """Create test engine once per session."""
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(scope="function")
def db_session(test_engine) -> Generator[Session, None, None]:
    """
    Fresh database session per test function with transaction rollback.
    Each test gets a clean slate.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ── Test Client ───────────────────────────────────────────────────────────────

@pytest.fixture(scope="function")
def client(db_session):
    """
    FastAPI TestClient with overridden database dependency.
    All API requests in tests use the in-memory test DB.
    """
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ── Test Settings ─────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_settings():
    """Mock settings for tests — no real API keys needed."""
    return Settings(
        database_url="sqlite:///:memory:",
        anthropic_api_key="test-anthropic-key",
        finnhub_api_key="test-finnhub-key",
        alpaca_api_key="test-alpaca-key",
        alpaca_secret_key="test-alpaca-secret",
        slack_bot_token="test-slack-token",
        jwt_secret_key="test-jwt-secret-32-chars-long!",
        robinhood_sync_key="test-robinhood-sync-key",
    )


# ── Test Data Fixtures ────────────────────────────────────────────────────────

@pytest.fixture
def sample_user(db_session) -> User:
    """Create a test user with TOTP enabled."""
    from app.auth.service import auth_service
    user = auth_service.create_user(db_session, "testuser", "testpassword123")
    user.totp_secret = "JBSWY3DPEHPK3PXP"  # base32 "Hello!" — valid for pyotp
    user.totp_enabled = True
    user.backup_codes = []
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def sample_daily_prices(db_session) -> list[DailyPrice]:
    """Create 30 days of price data for NVDA."""
    prices = []
    for i in range(30):
        dt = date(2026, 5, 1) + __import__("datetime").timedelta(days=i)
        price = DailyPrice(
            ticker="NVDA",
            date=dt,
            open=900.0 + i,
            high=910.0 + i,
            low=890.0 + i,
            close=905.0 + i,
            volume=50_000_000,
            adj_close=905.0 + i,
        )
        db_session.add(price)
        prices.append(price)
    db_session.commit()
    return prices


@pytest.fixture
def sample_technical_signal(db_session) -> TechnicalSignal:
    """Create a technical signal for NVDA."""
    signal = TechnicalSignal(
        ticker="NVDA",
        date=date(2026, 5, 30),
        ema9=920.0,
        ema21=915.0,
        sma50=900.0,
        sma200=850.0,
        ma10w=900.0,
        ma30w=850.0,
        adr_pct=4.5,
        atr=25.0,
        atr_extension=1.2,
        rvol=2.3,
        weinstein_stage=2,
        base_number=1,
    )
    db_session.add(signal)
    db_session.commit()
    db_session.refresh(signal)
    return signal


@pytest.fixture
def sample_peg_setup(db_session) -> PegSetup:
    """Create an active PEG setup for TSLA."""
    peg = PegSetup(
        ticker="TSLA",
        peg_date=date(2026, 5, 20),
        peg_low=250.0,
        gap_pct=5.2,
        volume_multiple=3.1,
        gap_filled=False,
    )
    db_session.add(peg)
    db_session.commit()
    db_session.refresh(peg)
    return peg


@pytest.fixture
def sample_claude_analysis(db_session) -> ClaudeAnalysis:
    """Create a Claude analysis for NVDA."""
    analysis = ClaudeAnalysis(
        ticker="NVDA",
        analyzed_at=datetime(2026, 5, 30, 10, 0, 0),
        conviction=8,
        action="BUY",
        entry_zone="900-920",
        stop_loss=850.0,
        risk_reward="1:3",
        stage="Stage 2",
        base_number=1,
        reasoning="Strong breakout with volume confirmation.",
        warnings=["Approaching 52-week high"],
        raw_json={
            "price_history": [{"date": "2026-05-30", "close": 905.0}],
            "technicals": {"ema9": 920.0, "sma50": 900.0},
        },
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


@pytest.fixture
def sample_position(db_session) -> Position:
    """Create a test position for NVDA."""
    position = Position(
        ticker="NVDA",
        shares=100,
        avg_cost=900.0,
        current_price=920.0,
        market_value=92000.0,
        unrealized_pnl=2000.0,
        unrealized_pct=2.22,
        sector="SEMICONDUCTORS",
        entry_date=date(2026, 5, 1),
        stop_loss=850.0,
        tranche1_filled=True,
        tranche2_filled=False,
    )
    db_session.add(position)
    db_session.commit()
    db_session.refresh(position)
    return position


@pytest.fixture
def sample_news_item(db_session) -> NewsItem:
    """Create a test news item for NVDA."""
    news = NewsItem(
        ticker="NVDA",
        published_at=datetime(2026, 5, 30, 9, 0, 0),
        headline="NVDA announces new AI chip",
        summary="Major breakthrough in AI processing.",
        sentiment=1,
        source="Reuters",
        category="earnings",
        url="https://example.com/news/nvda-123",
    )
    db_session.add(news)
    db_session.commit()
    db_session.refresh(news)
    return news


@pytest.fixture
def sample_alert(db_session) -> Alert:
    """Create a test alert for NVDA."""
    alert = Alert(
        ticker="NVDA",
        alert_type="NEAR_STOP",
        message="Price within 3% of stop loss",
        severity="warning",
        dismissed=False,
    )
    db_session.add(alert)
    db_session.commit()
    db_session.refresh(alert)
    return alert


# ── Auth Helpers ──────────────────────────────────────────────────────────────

@pytest.fixture
def auth_headers(sample_user):
    """Generate valid JWT headers for authenticated requests."""
    from app.auth.service import TokenType, auth_service
    access_token = auth_service.create_token(sample_user.id, TokenType.ACCESS)
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def temp_token(sample_user):
    """Generate a temp token for TOTP flow tests."""
    from app.auth.service import TokenType, auth_service
    return auth_service.create_token(sample_user.id, TokenType.TEMP)
