"""Integration tests for main API endpoints."""
import pytest


@pytest.mark.integration
@pytest.mark.api
class TestPortfolioAPI:
    """Test portfolio endpoints."""

    def test_portfolio_summary(self, client, auth_headers, sample_position):
        response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "total_value" in data
        assert "total_pnl" in data
        assert data["position_count"] >= 0

    def test_portfolio_holdings(self, client, auth_headers, sample_position):
        response = client.get("/api/v1/portfolio/holdings", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "ticker" in data[0]
            assert "shares" in data[0]

    def test_portfolio_performance(self, client, auth_headers):
        response = client.get("/api/v1/portfolio/performance?period=1M", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_sector_allocation(self, client, auth_headers, sample_position):
        response = client.get("/api/v1/portfolio/sector-allocation", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "sector_pcts" in data
        assert "warnings" in data

    def test_robinhood_sync_invalid_key(self, client, sample_position):
        response = client.post("/api/v1/portfolio/robinhood-sync",
            headers={"X-Sync-Key": "wrong-key"},
            json={"positions": [], "portfolio": {"total_value": 100000, "cash": 10000, "daily_pct": 0.5}})
        assert response.status_code == 401


@pytest.mark.integration
@pytest.mark.api
class TestScreenerAPI:
    """Test screener endpoints."""

    def test_ranked_screener_default(self, client, auth_headers):
        response = client.get("/api/v1/screener/ranked", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_ranked_screener_with_sector(self, client, auth_headers):
        response = client.get("/api/v1/screener/ranked?sector=SEMICONDUCTORS", headers=auth_headers)
        assert response.status_code == 200

    def test_ranked_screener_invalid_sector(self, client, auth_headers):
        response = client.get("/api/v1/screener/ranked?sector=INVALID", headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid sector" in response.json()["detail"]

    def test_ranked_screener_min_score(self, client, auth_headers):
        response = client.get("/api/v1/screener/ranked?min_score=50", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestAnalysisAPI:
    """Test analysis endpoints."""

    def test_get_analysis_exists(self, client, auth_headers, sample_claude_analysis):
        response = client.get("/api/v1/analysis/NVDA", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["ticker"] == "NVDA"
        assert data["conviction"] == 8
        assert data["action"] == "BUY"

    def test_get_analysis_not_found(self, client, auth_headers):
        response = client.get("/api/v1/analysis/ZZZZ", headers=auth_headers)
        assert response.status_code == 404

    def test_get_analysis_invalid_ticker(self, client, auth_headers):
        response = client.get("/api/v1/analysis/invalid@ticker", headers=auth_headers)
        assert response.status_code == 400
        assert "Invalid ticker" in response.json()["detail"]


@pytest.mark.integration
@pytest.mark.api
class TestPegAPI:
    """Test PEG endpoints."""

    def test_active_pegs(self, client, auth_headers, sample_peg_setup):
        response = client.get("/api/v1/peg/active", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        if len(data) > 0:
            assert "ticker" in data[0]
            assert "peg_date" in data[0]

    def test_peg_history_with_pagination(self, client, auth_headers, sample_peg_setup):
        response = client.get("/api/v1/peg/history?limit=10&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    def test_peg_history_limit_exceeds_max(self, client, auth_headers):
        response = client.get("/api/v1/peg/history?limit=1000", headers=auth_headers)
        assert response.status_code == 422  # validation error


@pytest.mark.integration
@pytest.mark.api
class TestMoversAPI:
    """Test movers endpoints."""

    def test_top_movers_default(self, client, auth_headers, sample_daily_prices):
        response = client.get("/api/v1/movers/top", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "gainers" in data
        assert "losers" in data

    def test_top_movers_custom_count(self, client, auth_headers):
        response = client.get("/api/v1/movers/top?count=5", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data["gainers"]) <= 5


@pytest.mark.integration
@pytest.mark.api
class TestNewsAPI:
    """Test news endpoints."""

    def test_news_feed_default(self, client, auth_headers, sample_news_item):
        response = client.get("/api/v1/news/feed", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_news_feed_with_sector(self, client, auth_headers):
        response = client.get("/api/v1/news/feed?sector=SEMICONDUCTORS", headers=auth_headers)
        assert response.status_code == 200

    def test_news_feed_invalid_sector(self, client, auth_headers):
        response = client.get("/api/v1/news/feed?sector=INVALID", headers=auth_headers)
        assert response.status_code == 400

    def test_news_feed_pagination(self, client, auth_headers):
        response = client.get("/api/v1/news/feed?limit=20&offset=0", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) <= 20


@pytest.mark.integration
@pytest.mark.api
class TestAlertsAPI:
    """Test alerts endpoints."""

    def test_active_alerts(self, client, auth_headers, sample_alert):
        response = client.get("/api/v1/alerts/active", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    def test_dismiss_alert(self, client, auth_headers, sample_alert):
        response = client.post(f"/api/v1/alerts/{sample_alert.id}/dismiss", headers=auth_headers)
        assert response.status_code == 200


@pytest.mark.integration
@pytest.mark.api
class TestSystemAPI:
    """Test system endpoints."""

    def test_health_check(self, client):
        response = client.get("/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"

    def test_pipeline_status(self, client, auth_headers):
        response = client.get("/api/v1/system/pipeline-status", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "running" in data
        assert "message" in data


@pytest.mark.integration
class TestAuthProtection:
    """Test that endpoints require authentication."""

    def test_portfolio_without_auth(self, client):
        response = client.get("/api/v1/portfolio/summary")
        assert response.status_code == 401

    def test_screener_without_auth(self, client):
        response = client.get("/api/v1/screener/ranked")
        assert response.status_code == 401

    def test_analysis_without_auth(self, client):
        response = client.get("/api/v1/analysis/NVDA")
        assert response.status_code == 401
