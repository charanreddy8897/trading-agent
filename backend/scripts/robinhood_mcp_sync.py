"""
Robinhood MCP Sync - Example Script
====================================

This script demonstrates how to sync Robinhood portfolio data from Claude Code
to your Trading Agent backend using the Robinhood MCP server.

PREREQUISITES:
1. Claude Code with Robinhood MCP server configured
2. ROBINHOOD_SYNC_KEY configured in backend .env
3. Backend server running on http://localhost:8000

USAGE IN CLAUDE CODE:
1. Use Robinhood MCP tools to fetch your portfolio:
   - robinhood_get_portfolio()
   - robinhood_get_positions()

2. Run this script to sync the data:
   python -m scripts.robinhood_mcp_sync

OR USE THIS AS A TEMPLATE FOR CLAUDE CODE INTEGRATION:
   Copy the sync_to_backend() function and use it in your Claude Code workflows.

NOTE: This script is a template/example. The actual data fetching happens
in Claude Code via MCP tools, not in Python code.
"""
import sys
from pathlib import Path
from datetime import date
from typing import List, Dict, Any

# Add backend directory to path
script_dir = Path(__file__).resolve().parent
backend_dir = script_dir.parent
sys.path.insert(0, str(backend_dir))

from app.core.settings import settings


def sync_to_backend(positions: List[Dict[str, Any]], portfolio: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sync Robinhood portfolio data to the Trading Agent backend.

    Args:
        positions: List of position dicts with keys:
            - ticker (str): Stock symbol
            - shares (float): Number of shares
            - avg_cost (float): Average cost per share
            - current_price (float): Current market price
            - entry_date (str): ISO date string (optional)
            - stop_loss (float | None): Stop loss price (optional)

        portfolio: Portfolio summary dict with keys:
            - total_value (float): Total portfolio value
            - cash (float): Available cash
            - daily_pct (float): Daily percent change

    Returns:
        Response dict from the backend API

    Raises:
        Exception: If sync fails (invalid key, network error, etc.)
    """
    import urllib.request
    import json

    if not settings.robinhood_sync_key:
        raise ValueError(
            "ROBINHOOD_SYNC_KEY not configured in .env file. "
            "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
        )

    # Prepare payload
    payload = {
        "positions": positions,
        "portfolio": portfolio
    }

    # API endpoint
    url = "http://localhost:8000/api/v1/portfolio/robinhood-sync"
    headers = {
        "Content-Type": "application/json",
        "X-Sync-Key": settings.robinhood_sync_key
    }

    # Make request
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers,
        method='POST'
    )

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            result = json.loads(response.read())
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        raise Exception(f"HTTP {e.code}: {error_body}")


def example_sync():
    """
    Example sync with mock data.

    In a real Claude Code workflow, you would:
    1. Use robinhood_get_positions() MCP tool to get real data
    2. Use robinhood_get_portfolio() MCP tool to get portfolio summary
    3. Pass that data to sync_to_backend()
    """
    print("=" * 80)
    print("ROBINHOOD MCP SYNC - EXAMPLE")
    print("=" * 80)
    print("")
    print("This is an example with mock data.")
    print("In Claude Code, use Robinhood MCP tools to get real data.")
    print("")

    # Mock data (in Claude Code, this comes from MCP tools)
    example_positions = [
        {
            "ticker": "AAPL",
            "shares": 10.0,
            "avg_cost": 150.50,
            "current_price": 175.25,
            "entry_date": "2026-01-15",
            "stop_loss": None
        },
        {
            "ticker": "MSFT",
            "shares": 5.0,
            "avg_cost": 320.00,
            "current_price": 380.50,
            "entry_date": "2026-02-01",
            "stop_loss": 300.00
        }
    ]

    example_portfolio = {
        "total_value": 3655.00,  # (10 * 175.25) + (5 * 380.50) + cash
        "cash": 250.00,
        "daily_pct": 1.25
    }

    print("Example positions:")
    for pos in example_positions:
        pnl = (pos['current_price'] - pos['avg_cost']) * pos['shares']
        print(f"  {pos['ticker']}: {pos['shares']} shares @ ${pos['avg_cost']:.2f} "
              f"→ ${pos['current_price']:.2f} (P&L: ${pnl:+,.2f})")
    print("")
    print(f"Portfolio value: ${example_portfolio['total_value']:,.2f}")
    print(f"Cash: ${example_portfolio['cash']:,.2f}")
    print(f"Daily change: {example_portfolio['daily_pct']:+.2f}%")
    print("")

    # Sync to backend
    try:
        print("Syncing to backend...")
        result = sync_to_backend(example_positions, example_portfolio)

        print("✅ Sync successful!")
        print(f"   Synced {result['synced_positions']} positions")
        print(f"   Total value: ${result['total_value']:,.2f}")
        print(f"   Status: {result['status']}")
        print("")
        print("View in backend:")
        print("  http://localhost:8000/api/v1/portfolio/summary")
        print("  http://localhost:8000/api/v1/portfolio/holdings")

    except Exception as e:
        print(f"❌ Sync failed: {e}")
        print("")
        print("Troubleshooting:")
        print("  1. Is backend running? (http://localhost:8000/health)")
        print("  2. Is ROBINHOOD_SYNC_KEY set in .env?")
        print("  3. Check backend logs for errors")


def print_mcp_workflow():
    """Print the MCP workflow for Claude Code."""
    print("")
    print("=" * 80)
    print("HOW TO USE IN CLAUDE CODE")
    print("=" * 80)
    print("")
    print("1. Authenticate Robinhood MCP:")
    print("   Use Claude Code's Robinhood MCP server")
    print("   (MCP handles authentication via OAuth)")
    print("")
    print("2. Fetch your Robinhood portfolio:")
    print("   Use MCP tools:")
    print("   - robinhood_get_account() → account info")
    print("   - robinhood_get_positions() → list of positions")
    print("   - robinhood_get_portfolio() → portfolio summary")
    print("")
    print("3. Transform data to Trading Agent format:")
    print("   positions = [")
    print("       {")
    print("           'ticker': pos['symbol'],")
    print("           'shares': pos['quantity'],")
    print("           'avg_cost': pos['average_buy_price'],")
    print("           'current_price': pos['current_price'],")
    print("           'entry_date': pos['created_at'][:10],")
    print("           'stop_loss': None")
    print("       }")
    print("       for pos in robinhood_positions")
    print("   ]")
    print("")
    print("   portfolio = {")
    print("       'total_value': robinhood_portfolio['equity'],")
    print("       'cash': robinhood_portfolio['cash'],")
    print("       'daily_pct': robinhood_portfolio['equity_previous_close_pct']")
    print("   }")
    print("")
    print("4. Sync to backend:")
    print("   from scripts.robinhood_mcp_sync import sync_to_backend")
    print("   result = sync_to_backend(positions, portfolio)")
    print("")
    print("5. Verify sync:")
    print("   curl http://localhost:8000/api/v1/portfolio/summary")
    print("")


def main():
    """Run example sync and print workflow."""
    import argparse

    parser = argparse.ArgumentParser(description="Robinhood MCP sync example")
    parser.add_argument(
        "--workflow",
        action="store_true",
        help="Show MCP workflow for Claude Code (don't sync)"
    )
    args = parser.parse_args()

    if args.workflow:
        print_mcp_workflow()
    else:
        # Run example sync
        example_sync()
        print("")
        print("To see the MCP workflow for Claude Code:")
        print("  python -m scripts.robinhood_mcp_sync --workflow")


if __name__ == "__main__":
    main()
