"""
Robinhood MCP Connection Test
==============================

Tests the Robinhood MCP sync endpoint.

DEPRECATED: Direct robin-stocks integration (removed)
NEW: MCP-based sync via Claude Code

This tests:
1. Sync key configuration
2. MCP sync endpoint availability
3. Example sync with mock data

Usage:
  python -m scripts.test_robinhood
  python -m scripts.test_robinhood --verbose
"""
import sys
from pathlib import Path
from datetime import date

# Add backend directory to path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.core.settings import settings


class Colors:
    """ANSI color codes."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    GRAY = '\033[90m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


class RobinhoodTester:
    """Test Robinhood connections."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.passed = 0
        self.failed = 0
        self.skipped = 0

    def _log(self, service: str, status: str, message: str, details: str = None):
        """Log test result."""
        if status == "PASS":
            symbol = f"{Colors.GREEN}✓{Colors.RESET}"
            self.passed += 1
        elif status == "SKIP":
            symbol = f"{Colors.GRAY}○{Colors.RESET}"
            self.skipped += 1
        else:
            symbol = f"{Colors.RED}✗{Colors.RESET}"
            self.failed += 1

        print(f"{symbol} {service:35} {status:6} {message}")

        if details and self.verbose:
            for line in details.split('\n'):
                print(f"  {Colors.GRAY}{line}{Colors.RESET}")

    def _header(self, title: str):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}[{title}]{Colors.RESET}")

    # ═══════════════════════════════════════════════════════════════════════════
    # CONFIGURATION
    # ═══════════════════════════════════════════════════════════════════════════

    def test_credentials(self):
        """Check configuration (MCP mode)."""
        self._header("Robinhood MCP Configuration")

        self._log("Direct Integration", "SKIP",
                 "Deprecated - use Robinhood MCP via Claude Code instead")

    def test_sync_key(self):
        """Check if sync key is configured."""
        if settings.robinhood_sync_key:
            self._log("Robinhood Sync Key", "PASS", f"Configured ({settings.robinhood_sync_key[:8]}...)")
        else:
            self._log("Robinhood Sync Key", "SKIP", "Not configured (MCP sync disabled)")

    # ═══════════════════════════════════════════════════════════════════════════
    # LIBRARY INSTALLATION
    # ═══════════════════════════════════════════════════════════════════════════

    def test_backend_running(self):
        """Check if backend is running."""
        self._header("Backend Status")

        try:
            import urllib.request
            import json

            url = "http://localhost:8000/health"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = json.loads(response.read())

            if data.get('status') == 'ok':
                self._log("Backend Health", "PASS", "Backend running on port 8000")
            else:
                self._log("Backend Health", "WARN", f"Unexpected response: {data}")
        except Exception as e:
            self._log("Backend Health", "FAIL", "Backend not running", str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # MCP ENDPOINT CHECK
    # ═══════════════════════════════════════════════════════════════════════════

    def test_endpoint_exists(self):
        """Test if MCP sync endpoint exists."""
        self._header("MCP Sync Endpoint")

        try:
            import urllib.request

            url = "http://localhost:8000/docs"
            with urllib.request.urlopen(url, timeout=5) as response:
                content = response.read().decode()

            if "/portfolio/robinhood-sync" in content:
                self._log("Sync Endpoint", "PASS", "Endpoint available at /api/v1/portfolio/robinhood-sync")
            else:
                self._log("Sync Endpoint", "WARN", "Endpoint not found in API docs")

        except Exception as e:
            self._log("Sync Endpoint", "FAIL", str(e)[:60], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # MCP SYNC ENDPOINT
    # ═══════════════════════════════════════════════════════════════════════════

    def test_sync_endpoint_with_mock_data(self):
        """Test the MCP sync endpoint with mock data."""
        self._header("Test Sync with Mock Data")

        if not settings.robinhood_sync_key:
            self._log("Mock Data Sync", "SKIP", "No sync key configured")
            return

        try:
            import urllib.request
            import json

            # Mock portfolio data (simulates what MCP would provide)
            mock_positions = [
                {
                    "ticker": "AAPL",
                    "shares": 10.0,
                    "avg_cost": 150.00,
                    "current_price": 175.25,
                    "entry_date": date.today().isoformat(),
                    "stop_loss": None
                }
            ]

            mock_portfolio = {
                "total_value": 2000.00,  # 10 * 175.25 + some cash
                "cash": 247.50,
                "daily_pct": 1.25
            }

            payload = {
                "positions": mock_positions,
                "portfolio": mock_portfolio
            }

            # Test the endpoint
            url = "http://localhost:8000/api/v1/portfolio/robinhood-sync"
            headers = {
                "Content-Type": "application/json",
                "X-Sync-Key": settings.robinhood_sync_key
            }

            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode(),
                headers=headers,
                method='POST'
            )

            with urllib.request.urlopen(req, timeout=10) as response:
                result = json.loads(response.read())

            if result.get('status') == 'ok':
                synced = result.get('synced_positions', 0)
                total = result.get('total_value', 0)
                self._log("Mock Data Sync", "PASS",
                         f"Synced {synced} positions, Total: ${total:,.2f}")
            else:
                self._log("Mock Data Sync", "FAIL", f"Unexpected response: {result}")

        except urllib.error.HTTPError as e:
            error_body = e.read().decode()
            self._log("Mock Data Sync", "FAIL", f"HTTP {e.code}: {error_body[:40]}", error_body)
        except Exception as e:
            self._log("Mock Data Sync", "FAIL", str(e)[:60], str(e))

    # ═══════════════════════════════════════════════════════════════════════════
    # SUMMARY
    # ═══════════════════════════════════════════════════════════════════════════

    def print_summary(self):
        """Print test summary."""
        total = self.passed + self.failed

        print("\n" + "=" * 80)
        print(f"{Colors.BOLD}RESULTS:{Colors.RESET} "
              f"{Colors.GREEN}{self.passed} passed{Colors.RESET}, "
              f"{Colors.RED}{self.failed} failed{Colors.RESET}, "
              f"{Colors.GRAY}{self.skipped} skipped{Colors.RESET} "
              f"(out of {total + self.skipped} tests)")
        print("=" * 80)

        if not settings.robinhood_sync_key:
            print(f"\n{Colors.YELLOW}ℹ️  Robinhood MCP Sync Not Configured{Colors.RESET}")
            print("\nTo enable Robinhood MCP sync, add to your .env file:")
            print("")
            print("  ROBINHOOD_SYNC_KEY=your_sync_key_here")
            print("")
            print("To generate sync key:")
            print("  python -c \"import secrets; print(secrets.token_hex(32))\"")
            print("")
            print("Then use Claude Code with Robinhood MCP to sync your portfolio.")
            print("See: scripts/robinhood_mcp_sync.py for workflow example")

        elif self.failed > 0:
            print(f"\n{Colors.RED}⚠️  ROBINHOOD MCP SYNC FAILED{Colors.RESET}")
            print("\nPossible issues:")
            print("  1. Backend not running (check: http://localhost:8000/health)")
            print("  2. Invalid ROBINHOOD_SYNC_KEY in .env")
            print("  3. MCP sync endpoint not available")
            print("")
            print("Re-run with --verbose for detailed error messages:")
            print("  python -m scripts.test_robinhood --verbose")
            print("")
            print("See MCP sync workflow:")
            print("  python -m scripts.robinhood_mcp_sync --workflow")

        elif self.passed > 0:
            print(f"\n{Colors.GREEN}✅ Robinhood connection working!{Colors.RESET}")

        print("")


def main():
    """Run all Robinhood MCP tests."""
    verbose = "--verbose" in sys.argv or "-v" in sys.argv

    print("\n" + "=" * 80)
    print(f"{Colors.BOLD}ROBINHOOD MCP CONNECTION TEST{Colors.RESET}".center(80))
    print("=" * 80)

    tester = RobinhoodTester(verbose=verbose)

    # Configuration tests
    tester.test_credentials()
    tester.test_sync_key()

    # Backend status
    tester.test_backend_running()

    # MCP endpoint tests
    tester.test_endpoint_exists()
    tester.test_sync_endpoint_with_mock_data()

    # Summary
    tester.print_summary()

    # Exit code
    sys.exit(0 if tester.failed == 0 else 1)


if __name__ == "__main__":
    main()
