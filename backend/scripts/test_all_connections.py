"""
Comprehensive Connection Test for All External Services
========================================================

Tests all external APIs and services used by the Trading Agent:
- Yahoo Finance (price data)
- Finnhub (news, company info)
- Alpaca (trading)
- Anthropic Claude (AI analysis)
- Slack (notifications)
- Robinhood (optional portfolio sync)
- Database (PostgreSQL)

Usage:
  # From backend/ directory:
  python -m scripts.test_all_connections
  python -m scripts.test_all_connections --verbose

  # From scripts/ directory:
  python test_all_connections.py
  python test_all_connections.py --verbose
"""
import asyncio
import sys
import os
from datetime import date, timedelta
from typing import Optional
from pathlib import Path

# Add backend directory to Python path (works from any directory)
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.core.settings import settings
from app.core.database import SessionLocal, engine
from sqlalchemy import text


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class ConnectionTester:
    """Test all external connections."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0
        self.warnings = 0

    def _log(self, service: str, status: str, message: str, details: Optional[str] = None):
        """Log test result with color coding."""
        if status == "PASS":
            symbol = f"{Colors.GREEN}✓{Colors.RESET}"
            self.passed += 1
        elif status == "SKIP":
            symbol = f"{Colors.GRAY}○{Colors.RESET}"
            self.skipped += 1
        elif status == "WARN":
            symbol = f"{Colors.YELLOW}⚠{Colors.RESET}"
            self.warnings += 1
        else:  # FAIL
            symbol = f"{Colors.RED}✗{Colors.RESET}"
            self.failed += 1

        print(f"{symbol} {service:30} {status:6} {message}")

        if details and self.verbose:
            for line in details.split('\n'):
                print(f"  {Colors.GRAY}{line}{Colors.RESET}")

        self.results.append((service, status, message))

    def _header(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}[{title}]{Colors.RESET}")

    # ═══════════════════════════════════════════════════════════════════════════
    # DATABASE
    # ═══════════════════════════════════════════════════════════════════════════

    def test_database(self):
        """Test PostgreSQL connection."""
        self._header("Database Connection")

        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                db_type = version.split()[0]
                version_num = version.split()[1] if len(version.split()) > 1 else "unknown"
                self._log("PostgreSQL", "PASS", f"Connected: {db_type} {version_num}")
        except Exception as e:
            self._log("PostgreSQL", "FAIL", str(e)[:50], str(e))

    def test_database_tables(self):
        """Check if database tables exist and have data."""
        db = SessionLocal()
        try:
            # Check daily_prices
            count = db.execute(text("SELECT COUNT(*) FROM daily_prices")).scalar()
            if count > 0:
                latest = db.execute(text("SELECT MAX(date) FROM daily_prices")).scalar()
                self._log("Data - Price History", "PASS", f"{count:,} records (latest: {latest})")
            else:
                self._log("Data - Price History", "SKIP", "Empty (run pipeline to populate)")

            # Check positions
            count = db.execute(text("SELECT COUNT(*) FROM positions")).scalar()
            if count > 0:
                self._log("Data - Positions", "PASS", f"{count} positions")
            else:
                self._log("Data - Positions", "SKIP", "No positions yet")

            # Check peg_setups
            count = db.execute(text("SELECT COUNT(*) FROM peg_setups")).scalar()
            if count > 0:
                self._log("Data - PEG Setups", "PASS", f"{count} setups found")
            else:
                self._log("Data - PEG Setups", "SKIP", "No PEG setups yet")

            # Check alerts
            count = db.execute(text("SELECT COUNT(*) FROM alerts WHERE is_active = true")).scalar()
            if count > 0:
                self._log("Data - Active Alerts", "PASS", f"{count} active alerts")
            else:
                self._log("Data - Active Alerts", "SKIP", "No active alerts")

            # Check news
            count = db.execute(text("SELECT COUNT(*) FROM news_items")).scalar()
            if count > 0:
                latest = db.execute(text("SELECT MAX(published_at) FROM news_items")).scalar()
                self._log("Data - News Items", "PASS", f"{count:,} articles (latest: {latest})")
            else:
                self._log("Data - News Items", "SKIP", "No news data yet")

        except Exception as e:
            self._log("Database Tables", "FAIL", str(e)[:50], str(e))
        finally:
            db.close()

    # ═══════════════════════════════════════════════════════════════════════════
    # YAHOO FINANCE
    # ═══════════════════════════════════════════════════════════════════════════

    def test_yahoo_finance(self):
        """Test Yahoo Finance API (price data)."""
        self._header("Yahoo Finance (yfinance)")

        try:
            import yfinance as yf

            # Test single ticker
            ticker = yf.Ticker("AAPL")
            info = ticker.info

            if info and 'currentPrice' in info:
                price = info.get('currentPrice', 'N/A')
                name = info.get('shortName', 'Apple Inc.')
                self._log("Yahoo Finance - Info", "PASS", f"AAPL: {name}, ${price}")
            else:
                self._log("Yahoo Finance - Info", "WARN", "Got response but missing price data")

            # Test historical data
            start_date = (date.today() - timedelta(days=7)).isoformat()
            df = yf.download("AAPL", start=start_date, progress=False)

            if not df.empty:
                latest_close = df['Close'].iloc[-1]
                rows = len(df)
                self._log("Yahoo Finance - Historical", "PASS", f"AAPL: {rows} days, latest close: ${latest_close:.2f}")
            else:
                self._log("Yahoo Finance - Historical", "FAIL", "No historical data returned")

        except ImportError:
            self._log("Yahoo Finance", "FAIL", "yfinance not installed")
        except Exception as e:
            self._log("Yahoo Finance", "FAIL", str(e)[:50], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # FINNHUB
    # ═══════════════════════════════════════════════════════════════════════════

    def test_finnhub_api_key(self):
        """Check if Finnhub API key is configured."""
        self._header("Finnhub Configuration")

        if settings.finnhub_api_key:
            self._log("Finnhub API Key", "PASS", f"Configured ({settings.finnhub_api_key[:8]}...)")
        else:
            self._log("Finnhub API Key", "SKIP", "Not configured in .env")

    def test_finnhub_quote(self):
        """Test Finnhub quote endpoint."""
        if not settings.finnhub_api_key:
            self._log("Finnhub - Quote", "SKIP", "No API key")
            return

        try:
            import urllib.request
            import json

            url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={settings.finnhub_api_key}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())

            if "c" in data and data["c"] > 0:
                price = data["c"]
                change = data.get("d", 0)
                pct = data.get("dp", 0)
                self._log("Finnhub - Quote", "PASS", f"AAPL: ${price:.2f} ({change:+.2f}, {pct:+.2f}%)")
            elif "error" in data:
                self._log("Finnhub - Quote", "FAIL", data["error"])
            else:
                self._log("Finnhub - Quote", "FAIL", f"Unexpected response: {list(data.keys())}")
        except Exception as e:
            self._log("Finnhub - Quote", "FAIL", str(e)[:50], str(e))

    def test_finnhub_news(self):
        """Test Finnhub company news endpoint."""
        if not settings.finnhub_api_key:
            self._log("Finnhub - News", "SKIP", "No API key")
            return

        try:
            import urllib.request
            import json
            from datetime import datetime

            today = date.today().isoformat()
            yesterday = (date.today() - timedelta(days=1)).isoformat()

            url = f"https://finnhub.io/api/v1/company-news?symbol=AAPL&from={yesterday}&to={today}&token={settings.finnhub_api_key}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())

            if isinstance(data, list):
                count = len(data)
                if count > 0:
                    latest = data[0]
                    headline = latest.get('headline', 'N/A')[:50]
                    self._log("Finnhub - News", "PASS", f"{count} articles (latest: {headline}...)")
                else:
                    self._log("Finnhub - News", "WARN", "No news articles returned (might be weekend)")
            else:
                self._log("Finnhub - News", "FAIL", f"Unexpected response: {type(data)}")
        except Exception as e:
            self._log("Finnhub - News", "FAIL", str(e)[:50], str(e))

    def test_finnhub_client(self):
        """Test Finnhub Python client."""
        if not settings.finnhub_api_key:
            self._log("Finnhub Client", "SKIP", "No API key")
            return

        try:
            import finnhub

            client = finnhub.Client(api_key=settings.finnhub_api_key)
            profile = client.company_profile2(symbol='AAPL')

            if profile and 'name' in profile:
                name = profile['name']
                market_cap = profile.get('marketCapitalization', 'N/A')
                self._log("Finnhub Client", "PASS", f"{name}, Market Cap: ${market_cap}B")
            else:
                self._log("Finnhub Client", "WARN", "No profile data returned")
        except ImportError:
            self._log("Finnhub Client", "FAIL", "finnhub-python not installed")
        except Exception as e:
            self._log("Finnhub Client", "FAIL", str(e)[:50], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # ALPACA
    # ═══════════════════════════════════════════════════════════════════════════

    def test_alpaca_api_key(self):
        """Check if Alpaca API keys are configured."""
        self._header("Alpaca Configuration")

        if settings.alpaca_api_key and settings.alpaca_secret_key:
            self._log("Alpaca API Keys", "PASS", f"Configured ({settings.alpaca_api_key[:8]}...)")
        else:
            self._log("Alpaca API Keys", "SKIP", "Not configured in .env")

    def test_alpaca_account(self):
        """Test Alpaca account endpoint."""
        if not settings.alpaca_api_key or not settings.alpaca_secret_key:
            self._log("Alpaca - Account", "SKIP", "No API keys")
            return

        try:
            import urllib.request
            import json

            url = f"{settings.alpaca_base_url}/v2/account"
            headers = {
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_secret_key
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())

            if "account_number" in data:
                buying_power = float(data.get("buying_power", 0))
                cash = float(data.get("cash", 0))
                equity = float(data.get("equity", 0))
                self._log("Alpaca - Account", "PASS",
                         f"Buying power: ${buying_power:,.2f}, Cash: ${cash:,.2f}, Equity: ${equity:,.2f}")
            else:
                self._log("Alpaca - Account", "FAIL", f"Unexpected response: {list(data.keys())}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self._log("Alpaca - Account", "FAIL", f"HTTP {e.code}: {error_body[:40]}", error_body)
        except Exception as e:
            self._log("Alpaca - Account", "FAIL", str(e)[:50], str(e))

    def test_alpaca_positions(self):
        """Test Alpaca positions endpoint."""
        if not settings.alpaca_api_key or not settings.alpaca_secret_key:
            self._log("Alpaca - Positions", "SKIP", "No API keys")
            return

        try:
            import urllib.request
            import json

            url = f"{settings.alpaca_base_url}/v2/positions"
            headers = {
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_secret_key
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())

            if isinstance(data, list):
                count = len(data)
                if count > 0:
                    symbols = [p['symbol'] for p in data[:3]]
                    self._log("Alpaca - Positions", "PASS", f"{count} positions: {', '.join(symbols)}...")
                else:
                    self._log("Alpaca - Positions", "SKIP", "No open positions")
            else:
                self._log("Alpaca - Positions", "FAIL", f"Unexpected response: {type(data)}")
        except Exception as e:
            self._log("Alpaca - Positions", "FAIL", str(e)[:50], str(e))

    def test_alpaca_market_data(self):
        """Test Alpaca market data endpoint."""
        if not settings.alpaca_api_key or not settings.alpaca_secret_key:
            self._log("Alpaca - Market Data", "SKIP", "No API keys")
            return

        try:
            import urllib.request
            import json

            url = f"{settings.alpaca_base_url}/v2/stocks/AAPL/quotes/latest"
            headers = {
                "APCA-API-KEY-ID": settings.alpaca_api_key,
                "APCA-API-SECRET-KEY": settings.alpaca_secret_key
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())

            if "quote" in data:
                bid = data["quote"].get("bp", 0)
                ask = data["quote"].get("ap", 0)
                self._log("Alpaca - Market Data", "PASS", f"AAPL quote: Bid ${bid:.2f}, Ask ${ask:.2f}")
            else:
                self._log("Alpaca - Market Data", "WARN", "No quote data (market might be closed)")
        except Exception as e:
            self._log("Alpaca - Market Data", "FAIL", str(e)[:50], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # ANTHROPIC CLAUDE
    # ═══════════════════════════════════════════════════════════════════════════

    async def test_claude_api_key(self):
        """Check if Anthropic API key is configured."""
        self._header("Anthropic Claude Configuration")

        if settings.anthropic_api_key:
            self._log("Anthropic API Key", "PASS", f"Configured ({settings.anthropic_api_key[:8]}...)")
        else:
            self._log("Anthropic API Key", "SKIP", "Not configured in .env")

    async def test_claude_api(self):
        """Test Anthropic Claude API."""
        if not settings.anthropic_api_key:
            self._log("Claude API", "SKIP", "No API key")
            return

        try:
            import urllib.request
            import json

            url = "https://api.anthropic.com/v1/messages"
            headers = {
                "x-api-key": settings.anthropic_api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            }
            payload = {
                "model": "claude-3-haiku-20240307",
                "max_tokens": 10,
                "messages": [{"role": "user", "content": "Say OK"}]
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers=headers
            )

            with urllib.request.urlopen(req, timeout=15) as response:
                data = json.loads(response.read())

            if "content" in data and len(data["content"]) > 0:
                response_text = data["content"][0]["text"]
                model = data.get("model", "unknown")
                self._log("Claude API", "PASS", f"Response: '{response_text}' (model: {model})")
            else:
                self._log("Claude API", "FAIL", "Unexpected response format")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self._log("Claude API", "FAIL", f"HTTP {e.code}: {error_body[:40]}", error_body)
        except Exception as e:
            self._log("Claude API", "FAIL", str(e)[:50], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # SLACK
    # ═══════════════════════════════════════════════════════════════════════════

    def test_slack_config(self):
        """Check if Slack is configured."""
        self._header("Slack Configuration")

        if settings.slack_bot_token:
            self._log("Slack Bot Token", "PASS", f"Configured ({settings.slack_bot_token[:8]}...)")
        else:
            self._log("Slack Bot Token", "SKIP", "Not configured (optional)")
            return

        # Check channels
        channels = {
            "Briefing": settings.slack_channel_briefing,
            "Alerts": settings.slack_channel_alerts,
            "Orders": settings.slack_channel_orders,
            "Emergency": settings.slack_channel_emergency,
        }

        configured = [name for name, ch in channels.items() if ch]
        if configured:
            self._log("Slack Channels", "PASS", f"Configured: {', '.join(configured)}")
        else:
            self._log("Slack Channels", "SKIP", "No channels configured")

    def test_slack_auth(self):
        """Test Slack authentication."""
        if not settings.slack_bot_token:
            self._log("Slack - Auth Test", "SKIP", "No bot token")
            return

        try:
            import urllib.request
            import json

            url = "https://slack.com/api/auth.test"
            headers = {
                "Authorization": f"Bearer {settings.slack_bot_token}"
            }

            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read())

            if data.get("ok"):
                team = data.get("team", "Unknown")
                user = data.get("user", "Unknown")
                self._log("Slack - Auth Test", "PASS", f"Connected to {team} as {user}")
            else:
                error = data.get("error", "Unknown error")
                self._log("Slack - Auth Test", "FAIL", error)
        except Exception as e:
            self._log("Slack - Auth Test", "FAIL", str(e)[:50], str(e))

    def test_slack_post_message(self):
        """Test Slack post message (dry run - doesn't actually post)."""
        if not settings.slack_bot_token or not settings.slack_channel_alerts:
            self._log("Slack - Post Message", "SKIP", "Not fully configured")
            return

        # Don't actually post, just validate we could
        self._log("Slack - Post Message", "PASS", f"Ready to post to {settings.slack_channel_alerts}")

    # ═══════════════════════════════════════════════════════════════════════════
    # ROBINHOOD (MCP)
    # ═══════════════════════════════════════════════════════════════════════════

    def test_robinhood_config(self):
        """Check if Robinhood credentials are configured."""
        self._header("Robinhood Configuration")

        if settings.rh_enabled:
            self._log("Robinhood Credentials", "PASS", f"Configured (username: {settings.rh_username})")
        else:
            missing = []
            if not settings.rh_username:
                missing.append("username")
            if not settings.rh_password:
                missing.append("password")
            if not settings.rh_totp:
                missing.append("TOTP secret")

            self._log("Robinhood Credentials", "SKIP", f"Not configured (missing: {', '.join(missing)})")

    def test_robinhood_sync_key(self):
        """Check if Robinhood sync key is configured."""
        if settings.robinhood_sync_key:
            self._log("Robinhood Sync Key", "PASS", f"Configured ({settings.robinhood_sync_key[:8]}...)")
        else:
            self._log("Robinhood Sync Key", "SKIP", "Not configured (MCP sync disabled)")

    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════

    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed + self.warnings

        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}RESULTS:{Colors.RESET} "
              f"{Colors.GREEN}{self.passed} passed{Colors.RESET}, "
              f"{Colors.RED}{self.failed} failed{Colors.RESET}, "
              f"{Colors.YELLOW}{self.warnings} warnings{Colors.RESET}, "
              f"{Colors.GRAY}{self.skipped} skipped{Colors.RESET} "
              f"(out of {total + self.skipped} tests)")
        print("=" * 80)

        if self.failed > 0:
            print(f"\n{Colors.RED}⚠️  FAILURES DETECTED{Colors.RESET}")
            print("\nCheck your .env file and ensure all API keys are valid:")
            print(f"   .env location: {os.path.abspath('.env')}")
            print("\n   Required keys:")
            print("   - ANTHROPIC_API_KEY (get from: https://console.anthropic.com/settings/keys)")
            print("   - FINNHUB_API_KEY (get from: https://finnhub.io/dashboard)")
            print("   - ALPACA_API_KEY + ALPACA_SECRET_KEY (get from: https://app.alpaca.markets/paper/dashboard)")
            print("   - DATABASE_URL (PostgreSQL connection string)")
            print("\n   Optional keys:")
            print("   - SLACK_BOT_TOKEN (Slack notifications)")
            print("   - RH_USERNAME, RH_PASSWORD, RH_TOTP (Robinhood portfolio sync)")

        if self.skipped > 0 and self.failed == 0:
            print(f"\n{Colors.BLUE}💡 TIPS:{Colors.RESET}")

            # Check if data is empty
            empty_data = any(
                "Empty" in result[2] or "No" in result[2]
                for result in self.results
                if result[0].startswith("Data -")
            )
            if empty_data:
                print("\n   📊 No data in database yet. To populate:")
                print("      curl -X POST http://localhost:8000/api/v1/system/run-pipeline")
                print("      Or wait for scheduled morning run (7 AM)")

            # Check if optional services missing
            missing_optional = any(
                "Not configured" in result[2] and "optional" in result[2].lower()
                for result in self.results
            )
            if missing_optional:
                print("\n   🔑 Some optional services not configured.")
                print("      The system will work but with limited features.")
                print("      Add them to .env for full functionality.")

        if self.failed == 0 and self.passed > 0:
            print(f"\n{Colors.GREEN}✅ All critical services are working!{Colors.RESET}")

        print("")


async def main():
    """Run all connection tests."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}TRADING AGENT - COMPREHENSIVE CONNECTION TEST{Colors.RESET}".center(80))
    print("=" * 80)

    tester = ConnectionTester(verbose=verbose)

    # Run all tests
    tester.test_database()
    tester.test_database_tables()

    tester.test_yahoo_finance()

    tester.test_finnhub_api_key()
    tester.test_finnhub_quote()
    tester.test_finnhub_news()
    tester.test_finnhub_client()

    tester.test_alpaca_api_key()
    tester.test_alpaca_account()
    tester.test_alpaca_positions()
    tester.test_alpaca_market_data()

    await tester.test_claude_api_key()
    await tester.test_claude_api()

    tester.test_slack_config()
    tester.test_slack_auth()
    tester.test_slack_post_message()

    tester.test_robinhood_config()
    tester.test_robinhood_sync_key()

    # Summary
    tester.print_summary()

    # Exit code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
