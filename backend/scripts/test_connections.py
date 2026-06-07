"""
Test all external API connections and services.

Usage:
  python -m scripts.test_connections
"""
import asyncio
import sys
import os
from datetime import date, timedelta

sys.path.insert(0, ".")

from app.core.settings import settings
from app.core.database import SessionLocal, engine
from sqlalchemy import text


class ConnectionTester:
    """Test all external connections."""

    def __init__(self):
        self.results = []
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def _log(self, service: str, status: str, message: str):
        """Log test result."""
        if status == "PASS":
            symbol = "✓"
            self.passed += 1
        elif status == "SKIP":
            symbol = "○"
            self.skipped += 1
        else:
            symbol = "✗"
            self.failed += 1

        print(f"{symbol} {service:25} {status:6} {message}")
        self.results.append((service, status, message))

    def test_database(self):
        """Test PostgreSQL connection."""
        print("\n[1/5] Testing Database Connection...")
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                db_type = version.split()[0]
                self._log("PostgreSQL", "PASS", f"Connected: {db_type}")
        except Exception as e:
            self._log("PostgreSQL", "FAIL", str(e)[:50])

    def test_env_vars(self):
        """Check if API keys are configured."""
        print("\n[2/5] Checking API Keys...")

        # Anthropic Claude
        if settings.anthropic_api_key:
            self._log("Anthropic Claude Key", "PASS", f"Configured ({settings.anthropic_api_key[:8]}...)")
        else:
            self._log("Anthropic Claude Key", "SKIP", "Not configured in .env")

        # Finnhub
        if settings.finnhub_api_key:
            self._log("Finnhub Key", "PASS", f"Configured ({settings.finnhub_api_key[:8]}...)")
        else:
            self._log("Finnhub Key", "SKIP", "Not configured in .env")

        # Alpaca
        if settings.alpaca_api_key and settings.alpaca_secret_key:
            self._log("Alpaca Keys", "PASS", f"Configured ({settings.alpaca_api_key[:8]}...)")
        else:
            self._log("Alpaca Keys", "SKIP", "Not configured in .env")

    def test_finnhub_api(self):
        """Test Finnhub API with actual HTTP request."""
        print("\n[3/5] Testing Finnhub API...")

        if not settings.finnhub_api_key:
            self._log("Finnhub API", "SKIP", "No API key configured")
            return

        try:
            import urllib.request
            import json

            url = f"https://finnhub.io/api/v1/quote?symbol=AAPL&token={settings.finnhub_api_key}"
            with urllib.request.urlopen(url, timeout=10) as response:
                data = json.loads(response.read())

            if "c" in data and data["c"] > 0:  # 'c' is current price
                price = data["c"]
                self._log("Finnhub API", "PASS", f"AAPL quote: ${price:.2f}")
            elif "error" in data:
                self._log("Finnhub API", "FAIL", data["error"])
            else:
                self._log("Finnhub API", "FAIL", f"Unexpected response: {list(data.keys())}")
        except Exception as e:
            self._log("Finnhub API", "FAIL", str(e)[:50])

    def test_alpaca_api(self):
        """Test Alpaca API with actual HTTP request."""
        print("\n[4/5] Testing Alpaca API...")

        if not settings.alpaca_api_key or not settings.alpaca_secret_key:
            self._log("Alpaca API", "SKIP", "No API keys configured")
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
                self._log("Alpaca API", "PASS", f"Account connected, buying power: ${buying_power:,.2f}")
            else:
                self._log("Alpaca API", "FAIL", f"Unexpected response: {list(data.keys())}")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self._log("Alpaca API", "FAIL", f"HTTP {e.code}: {error_body[:40]}")
        except Exception as e:
            self._log("Alpaca API", "FAIL", str(e)[:50])

    async def test_claude_api(self):
        """Test Anthropic Claude API with actual HTTP request."""
        print("\n[5/5] Testing Anthropic Claude API...")

        if not settings.anthropic_api_key:
            self._log("Anthropic Claude API", "SKIP", "No API key configured")
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
                self._log("Anthropic Claude API", "PASS", f"Response: {response_text}")
            else:
                self._log("Anthropic Claude API", "FAIL", "Unexpected response format")
        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self._log("Anthropic Claude API", "FAIL", f"HTTP {e.code}: {error_body[:40]}")
        except Exception as e:
            self._log("Anthropic Claude API", "FAIL", str(e)[:50])

    def test_data_tables(self):
        """Check if data tables have any records."""
        print("\n[BONUS] Checking Database Tables...")
        db = SessionLocal()
        try:
            # Check daily_prices
            count = db.execute(text("SELECT COUNT(*) FROM daily_prices")).scalar()
            if count > 0:
                self._log("Data - Price History", "PASS", f"{count:,} records")
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

        except Exception as e:
            self._log("Data Tables", "FAIL", str(e)[:50])
        finally:
            db.close()

    def print_summary(self):
        """Print test summary."""
        print("\n" + "=" * 75)
        print(f"RESULTS: {self.passed} passed, {self.failed} failed, {self.skipped} skipped")
        print("=" * 75)

        if self.failed > 0:
            print("\n⚠️  FAILURES DETECTED")
            print("\nCheck your .env file and ensure API keys are valid:")
            print(f"   .env location: {os.path.abspath('.env')}")
            print("\n   Required keys:")
            print("   - ANTHROPIC_API_KEY (get from: https://console.anthropic.com/settings/keys)")
            print("   - FINNHUB_API_KEY (get from: https://finnhub.io/dashboard)")
            print("   - ALPACA_API_KEY + ALPACA_SECRET_KEY (get from: https://app.alpaca.markets/paper/dashboard)")
            print("   - DATABASE_URL (PostgreSQL connection string)")

        if self.skipped > 0 and self.failed == 0:
            print("\n💡 TIPS:")

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

            # Check if API keys missing
            missing_keys = any(
                "Not configured" in result[2]
                for result in self.results
                if "Key" in result[0]
            )
            if missing_keys:
                print("\n   🔑 Some API keys not configured.")
                print("      The system will work but with limited data sources.")
                print("      Add them to .env for full functionality.")

        if self.failed == 0 and self.passed > 0:
            print("\n✅ All critical services are working!")


async def main():
    """Run all connection tests."""
    print("\n" + "=" * 75)
    print(" " * 20 + "TRADING AGENT - CONNECTION TEST")
    print("=" * 75)

    tester = ConnectionTester()

    # Run tests
    tester.test_database()
    tester.test_env_vars()
    tester.test_finnhub_api()
    tester.test_alpaca_api()
    await tester.test_claude_api()
    tester.test_data_tables()

    # Summary
    tester.print_summary()

    # Exit code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    asyncio.run(main())
