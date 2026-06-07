# Trading Agent — Complete Prerequisites

Everything you need set up BEFORE you open Claude Code and start building. Do all of this first, then build in one go.

---

## 1. Local Machine Requirements

### Hardware (minimum)

```
CPU:    Any modern processor (M1+ Mac, or Intel/AMD with 4+ cores)
RAM:    8 GB minimum, 16 GB recommended
Disk:   5 GB free space (for data, dependencies, Docker)
OS:     macOS, Linux, or Windows (WSL2 recommended for Windows)
```

### Software — Install These First

| # | Software | Version | Install Command / Link | Why |
|---|----------|---------|----------------------|-----|
| 1 | **Python** | 3.11+ | `brew install python@3.11` (Mac) or python.org | Backend runtime |
| 2 | **Node.js** | 20+ LTS | `brew install node` or nodejs.org | React frontend |
| 3 | **Git** | Latest | `brew install git` or git-scm.com | Version control |
| 4 | **Docker Desktop** | Latest | docker.com/products/docker-desktop | Containerized deployment |
| 5 | **Claude Code** | Latest | `npm install -g @anthropic-ai/claude-code` | AI coding assistant |
| 6 | **VS Code** (optional) | Latest | code.visualstudio.com | Code editor |
| 7 | **GitHub CLI** (optional) | Latest | `brew install gh` | Repo management |

### Verify installations

```bash
python3 --version    # should show 3.11+
node --version       # should show 20+
npm --version        # should show 9+
git --version        # any recent version
docker --version     # any recent version
claude --version     # Claude Code installed
```

---

## 2. Accounts & API Keys to Create

You need 6 accounts. Create all of these before you start coding.

### 2.1 Anthropic (Claude API)

You already have Claude Max — your API key is included.

```
Where:  console.anthropic.com → API Keys → Create Key
Key:    sk-ant-api03-...
Cost:   Included in your Claude Max subscription
```

### 2.2 Robinhood (Portfolio Sync)

You already have an account. You need to set up 2FA with a TOTP app to get the secret key.

```
Step 1: Open Robinhood app → Settings → Security → Two-Factor Authentication
Step 2: Choose "Authentication App" (NOT SMS)
Step 3: When it shows the QR code, also click "Can't scan?" to reveal the SECRET KEY
Step 4: Copy that secret key — this is your RH_TOTP value
Step 5: Still scan the QR with your authenticator app so 2FA works normally

You need:
  RH_USERNAME = your Robinhood email
  RH_PASSWORD = your Robinhood password
  RH_TOTP     = the secret key from step 3 (NOT the 6-digit code)
```

**Important:** The TOTP secret is the base32 string (like `JBSWY3DPEHPK3PXP`), not the 6-digit code that changes every 30 seconds. The code uses this secret to auto-generate codes.

### 2.3 Finnhub (News & Earnings Data)

```
Where:  finnhub.io → Register → Free tier
Key:    Your API key from the dashboard
Cost:   Free (60 API calls/minute, real-time US stock prices via WebSocket)
Gives:  News headlines, earnings calendar, analyst recommendations,
        insider transactions, SEC filings, real-time WebSocket prices
```

### 2.4 Alpaca (Paper Trading + Market Data)

```
Where:  alpaca.markets → Sign Up → Paper Trading account
Keys:   Go to dashboard → Paper Trading → API Keys → Generate
You get:
  ALPACA_API_KEY    = PK...
  ALPACA_SECRET_KEY = ...
  ALPACA_BASE_URL   = https://paper-api.alpaca.markets  (paper trading)
Cost:   Free (paper trading, real-time WebSocket data for US stocks)
Gives:  Paper trading execution, WebSocket real-time prices,
        historical bars (1min to daily), order management API
```

**Why Alpaca even though you use Robinhood:** Alpaca gives you a proper API for paper trading + WebSocket streaming. Robinhood has no official API — `robin_stocks` is unofficial and only used for reading your real portfolio.

### 2.5 Slack (Notifications)

```
Step 1: Go to api.slack.com/apps → Create New App → From Scratch
Step 2: Name: "Trading Agent", Workspace: your workspace
Step 3: OAuth & Permissions → Bot Token Scopes → Add:
        - chat:write
        - chat:write.customize
        - files:write
        - channels:read
        - groups:read
Step 4: Install to Workspace → Copy Bot User OAuth Token (xoxb-...)
Step 5: Create 4 channels in your Slack workspace:
        - #trading-briefing
        - #trading-alerts
        - #trading-orders
        - #trading-emergency
Step 6: Invite the bot to each channel: /invite @Trading Agent
Step 7: Get each channel's ID:
        Right-click channel name → Copy link → ID is the last part
        (looks like C0123456789)

You need:
  SLACK_BOT_TOKEN          = xoxb-...
  SLACK_CHANNEL_BRIEFING   = C...  (#trading-briefing)
  SLACK_CHANNEL_ALERTS     = C...  (#trading-alerts)
  SLACK_CHANNEL_ORDERS     = C...  (#trading-orders)
  SLACK_CHANNEL_EMERGENCY  = C...  (#trading-emergency)
```

### 2.6 GitHub (Code Repository)

```
Where:  github.com → Create account if needed
Step 1: Create a new PRIVATE repository: trading-agent-platform
Step 2: Don't initialize with README (we'll push from local)
Step 3: Copy the repo URL: git@github.com:YOUR_USERNAME/trading-agent-platform.git

Optional: Set up SSH key for passwordless push
  ssh-keygen -t ed25519 -C "your_email"
  # Copy ~/.ssh/id_ed25519.pub → GitHub Settings → SSH Keys → Add
```

---

## 3. Complete .env File

Create this file BEFORE you start building. Fill in every value.

```bash
# ═══════════════════════════════════════════════════════
# TRADING AGENT — ENVIRONMENT VARIABLES
# ═══════════════════════════════════════════════════════

# ── Robinhood (portfolio sync via robin_stocks) ──
RH_USERNAME=your_robinhood_email@example.com
RH_PASSWORD=your_robinhood_password
RH_TOTP=YOUR_BASE32_TOTP_SECRET

# ── Anthropic Claude API ──
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# ── Finnhub (news, earnings, WebSocket prices) ──
FINNHUB_API_KEY=your_finnhub_api_key

# ── Alpaca (paper trading + market data) ──
ALPACA_API_KEY=PKyour_alpaca_key
ALPACA_SECRET_KEY=your_alpaca_secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# ── Slack (notifications) ──
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_BRIEFING=C0123456789
SLACK_CHANNEL_ALERTS=C0123456790
SLACK_CHANNEL_ORDERS=C0123456791
SLACK_CHANNEL_EMERGENCY=C0123456792

# ── Trading Mode ──
TRADING_MODE=paper

# ── Dashboard Auth (set your own password) ──
DASHBOARD_PASSWORD=your_strong_password_here

# ── Database ──
DATABASE_URL=sqlite:///./data/trading.db
```

---

## 4. Python Dependencies (All at Once)

```
# requirements.txt — copy this exactly

# Data
yfinance==0.2.31
robin-stocks==3.0.6
alpaca-trade-api==3.0.2
finnhub-python==2.4.19
websockets==12.0

# Data processing
pandas==2.1.0
numpy==1.25.0

# Technical analysis
ta==0.11.0

# AI / LLM
anthropic==0.40.0

# Web framework
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.6.0

# Async HTTP (Slack API)
aiohttp==3.9.0

# Database
sqlalchemy==2.0.25

# Scheduling
apscheduler==3.10.4

# Security
cryptography==42.0.0
pyotp==2.9.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2

# Utilities
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.0

# Backtesting (post-week-1, but install now)
vectorbt==0.26.2
```

---

## 5. Frontend Dependencies (All at Once)

```json
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "recharts": "^2.12.0",
    "lightweight-charts": "^4.1.0",
    "lucide-react": "^0.383.0",
    "@tanstack/react-query": "^5.24.0",
    "axios": "^1.6.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.3.0",
    "react-hot-toast": "^2.4.1",
    "react-grid-layout": "^1.4.4"
  },
  "devDependencies": {
    "vite": "^5.1.0",
    "@vitejs/plugin-react": "^4.2.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

---

## 6. Stock Universe to Finalize

Review this list and add/remove tickers before you start. These get hardcoded into `config/universe.py`.

```python
SECTORS = {
    "AI_SOFTWARE": [
        "NVDA", "MSFT", "GOOG", "META", "AMZN", "PLTR", "AI",
        "SNOW", "CRM", "NOW", "PATH", "DDOG", "SMCI",
    ],
    "SEMICONDUCTORS": [
        "NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU", "MRVL",
        "ARM", "TSM", "ASML", "LRCX", "AMAT", "ON", "ACMR",
        "TER", "KLAC",
    ],
    "MEMORY": [
        "MU", "WDC", "STX", "NXPI",
    ],
    "SPACE_DEFENSE": [
        "RKLB", "LMT", "BA", "NOC", "ASTS", "LUNR", "RDW",
        "SPIR", "RTX", "GD",
    ],
    "PHYSICAL_AI_ROBOTICS": [
        "ISRG", "TER", "TSLA", "ABBNY", "FANUY", "RCAT", "GH",
    ],
}
# Total unique tickers: ~45
```

**Action needed:** Go through your TradingView watchlists and add any tickers missing from this list. Remove any you don't track.

---

## 7. Trading Rules to Confirm

These get encoded as constants. Review and adjust the numbers before building.

```python
# config/trading_rules.py

# ── Entry Rules ──
PEG_GAP_MIN_PCT = 3.0           # Minimum gap % to qualify as PEG
PEG_VOLUME_MULTIPLE = 2.0       # Gap day volume must be >= 2x 20-day avg
ENTRY_EMA = 9                    # First tranche entry at 9 EMA pullback
ADD_EMA = 21                     # Second tranche at 21 EMA or 50 SMA

# ── Position Sizing ──
MAX_POSITION_PCT = 10.0          # Max 10% of portfolio per position
TRANCHE_1_PCT = 5.0              # First add: 5% of portfolio
TRANCHE_2_PCT = 5.0              # Second add: 5% of portfolio

# ── ADR Sweet Spot ──
ADR_MIN = 3.0                    # Minimum average daily range %
ADR_MAX = 10.0                   # Maximum average daily range %

# ── Sell / Trim Rules ──
ATR_TRIM_THRESHOLD = 3.0        # Trim 1/3 when ATR extension >= 3x
LATE_STAGE_BASE = 3              # Base 3+ = late stage, watch for climax
STOP_LOSS_MAX_PCT = 10.0         # Max allowed loss per position: -10%

# ── Risk Guards ──
MAX_DAILY_LOSS_PCT = 3.0         # Circuit breaker: halt if down 3%+ in a day
MAX_DAILY_LOSS_USD = 5000        # Hard dollar cap
MAX_WEEKLY_LOSS_PCT = 7.0        # Weekly loss limit
MAX_DRAWDOWN_PCT = 15.0          # Max drawdown from equity peak
MAX_OPEN_POSITIONS = 20          # Position count limit
MAX_SECTOR_EXPOSURE_PCT = 40.0   # Max in any single sector
MAX_CORRELATED_EXPOSURE_PCT = 60.0  # Max in correlated sectors combined

# ── Earnings ──
EARNINGS_GAP_DOWN_WAIT_DAYS = 3  # 3-day rule: don't buy gap-downs for 3 days

# ── Market Hours (ET) ──
MARKET_OPEN = "09:30"
MARKET_CLOSE = "16:00"
BRIEFING_TIME = "07:00"          # PT — daily briefing send time
ALERT_CHECK_INTERVAL_SEC = 900   # Check alerts every 15 minutes
```

**Action needed:** Review every number above. If your risk tolerance or position sizing is different, change it now.

---

## 8. Pre-Build Checklist

Run through this checklist. Every box must be checked before you start coding.

```
ACCOUNTS & KEYS
  □ Anthropic API key obtained and working
  □ Robinhood 2FA set to authenticator app (NOT SMS)
  □ Robinhood TOTP secret key copied (the base32 string)
  □ Finnhub account created, API key copied
  □ Alpaca paper trading account created, API key + secret copied
  □ Slack app created with bot token
  □ 4 Slack channels created (#trading-briefing, -alerts, -orders, -emergency)
  □ Slack bot invited to all 4 channels (/invite @Trading Agent)
  □ Slack channel IDs copied (right-click → copy link → last segment)
  □ GitHub repo created (private): trading-agent-platform

SOFTWARE
  □ Python 3.11+ installed and verified
  □ Node.js 20+ installed and verified
  □ Git installed and configured (git config user.name / user.email)
  □ Docker Desktop installed and running
  □ Claude Code installed (npm install -g @anthropic-ai/claude-code)

CONFIGURATION
  □ .env file created with ALL values filled in (see Section 3)
  □ Stock universe reviewed — tickers added/removed as needed
  □ Trading rules reviewed — numbers adjusted to your risk tolerance
  □ SSH key added to GitHub (for git push)

KNOWLEDGE
  □ Read the full blueprint (Parts 1-4) so you know what you're building
  □ Have your TradingView watchlist URLs handy
  □ Understand the PEG / O'Neil / Weinstein methodology (your educational posts)

OPTIONAL BUT RECOMMENDED
  □ Slack desktop app installed (for real-time notification testing)
  □ VS Code installed with Python + ESLint extensions
  □ Second monitor or tablet for referencing the blueprint while coding
```

---

## 9. Quick Verification Tests

Run these BEFORE you start building to make sure every API key works.

### Test Robinhood

```python
# test_robinhood.py
import pyotp
import robin_stocks.robinhood as rh
from dotenv import load_dotenv
import os

load_dotenv()
totp = pyotp.TOTP(os.getenv("RH_TOTP")).now()
login = rh.login(os.getenv("RH_USERNAME"), os.getenv("RH_PASSWORD"), mfa_code=totp)
print("Robinhood login:", "SUCCESS" if login else "FAILED")

holdings = rh.account.build_holdings()
print(f"Holdings: {len(holdings)} positions")
for ticker, data in list(holdings.items())[:3]:
    print(f"  {ticker}: {data['quantity']} shares @ ${data['average_buy_price']}")

rh.logout()
```

### Test Anthropic Claude

```python
# test_claude.py
from anthropic import Anthropic
from dotenv import load_dotenv
import os

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
msg = client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=100,
    messages=[{"role": "user", "content": "Say 'Claude API working' and nothing else."}]
)
print("Claude API:", msg.content[0].text)
```

### Test Finnhub

```python
# test_finnhub.py
import finnhub
from dotenv import load_dotenv
import os

load_dotenv()
client = finnhub.Client(api_key=os.getenv("FINNHUB_API_KEY"))
news = client.company_news("NVDA", _from="2026-05-25", to="2026-05-31")
print(f"Finnhub: {len(news)} news articles for NVDA")
if news:
    print(f"  Latest: {news[0]['headline'][:80]}")
```

### Test Alpaca

```python
# test_alpaca.py
from alpaca_trade_api import REST
from dotenv import load_dotenv
import os

load_dotenv()
api = REST(
    os.getenv("ALPACA_API_KEY"),
    os.getenv("ALPACA_SECRET_KEY"),
    os.getenv("ALPACA_BASE_URL")
)
account = api.get_account()
print(f"Alpaca: {account.status}")
print(f"  Buying power: ${float(account.buying_power):,.2f}")
print(f"  Portfolio: ${float(account.portfolio_value):,.2f}")
```

### Test Slack

```python
# test_slack.py
import requests
from dotenv import load_dotenv
import os

load_dotenv()
resp = requests.post(
    "https://slack.com/api/chat.postMessage",
    headers={"Authorization": f"Bearer {os.getenv('SLACK_BOT_TOKEN')}"},
    json={
        "channel": os.getenv("SLACK_CHANNEL_ALERTS"),
        "text": "✅ Trading Agent Slack integration working!",
    }
)
result = resp.json()
print(f"Slack: {'SUCCESS' if result.get('ok') else 'FAILED: ' + result.get('error', '')}")
```

### Run All Tests at Once

```bash
# Create a virtual env and install test dependencies first
python3 -m venv venv
source venv/bin/activate
pip install robin-stocks pyotp anthropic finnhub-python alpaca-trade-api requests python-dotenv

# Run each test
python test_robinhood.py
python test_claude.py
python test_finnhub.py
python test_alpaca.py
python test_slack.py
```

**Expected output — all 5 should show SUCCESS:**
```
Robinhood login: SUCCESS
Holdings: 12 positions
  NVDA: 45 shares @ $108.20
  PLTR: 200 shares @ $62.30
  ARM: 30 shares @ $142.00

Claude API: Claude API working

Finnhub: 14 news articles for NVDA
  Latest: NVIDIA Announces Next-Gen Blackwell Ultra Architecture...

Alpaca: ACTIVE
  Buying power: $100,000.00
  Portfolio: $100,000.00

Slack: SUCCESS
```

If any test fails, fix it before proceeding. Common issues:

```
Robinhood "MFA required"  → TOTP secret is wrong. Re-extract from RH app.
Robinhood "Login failed"  → Check email/password. Try logging in on web first.
Claude 401                → API key is invalid or expired. Regenerate at console.anthropic.com
Finnhub 403               → API key wrong or rate limited. Wait 1 minute, retry.
Alpaca 403                → Make sure you're using PAPER trading URL, not live.
Slack "channel_not_found" → Bot isn't invited to channel. Run /invite @Trading Agent
Slack "invalid_auth"      → Bot token is wrong. Reinstall app to workspace.
```

---

## 10. One-Shot Bootstrap Script

Once all tests pass, run this to scaffold the entire project:

```bash
#!/bin/bash
# bootstrap.sh — Run this once, then open Claude Code

set -e

echo "═══ Trading Agent Bootstrap ═══"

# 1. Create project root
mkdir -p trading-agent-platform && cd trading-agent-platform

# 2. Initialize git
git init
git branch -M main

# 3. Create .gitignore
cat > .gitignore << 'EOF'
.env
*.env.local
__pycache__/
*.pyc
venv/
.venv/
node_modules/
frontend/dist/
*.sqlite
*.db
data/*.sqlite
.vscode/
.idea/
*.swp
.DS_Store
Thumbs.db
*.log
logs/
test_*.py
EOF

# 4. Create backend structure
mkdir -p backend/{api,config,data,screener,analysis,strategies,execution,risk,security,system,backtest,portfolio,alerts,scheduler,database,tests}
touch backend/__init__.py
touch backend/{api,config,data,screener,analysis,strategies,execution,risk,security,system,backtest,portfolio,alerts,scheduler,database,tests}/__init__.py

# 5. Copy .env (you should have this ready)
cp ../.env .env 2>/dev/null || echo "⚠ Copy your .env file into this directory"

# 6. Create .env.example (safe to commit)
cat > .env.example << 'EOF'
RH_USERNAME=your_email
RH_PASSWORD=your_password
RH_TOTP=your_totp_secret
ANTHROPIC_API_KEY=sk-ant-...
FINNHUB_API_KEY=your_key
ALPACA_API_KEY=PK...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_BRIEFING=C...
SLACK_CHANNEL_ALERTS=C...
SLACK_CHANNEL_ORDERS=C...
SLACK_CHANNEL_EMERGENCY=C...
TRADING_MODE=paper
DASHBOARD_PASSWORD=your_password
DATABASE_URL=sqlite:///./data/trading.db
EOF

# 7. Python virtual env + dependencies
python3 -m venv venv
source venv/bin/activate
cat > backend/requirements.txt << 'EOF'
yfinance==0.2.31
robin-stocks==3.0.6
alpaca-trade-api==3.0.2
finnhub-python==2.4.19
websockets==12.0
pandas==2.1.0
numpy==1.25.0
ta==0.11.0
anthropic==0.40.0
fastapi==0.109.0
uvicorn==0.27.0
pydantic==2.6.0
aiohttp==3.9.0
sqlalchemy==2.0.25
apscheduler==3.10.4
cryptography==42.0.0
pyotp==2.9.0
python-jose==3.3.0
passlib==1.7.4
bcrypt==4.1.2
python-dotenv==1.0.0
requests==2.31.0
beautifulsoup4==4.12.0
EOF
pip install -r backend/requirements.txt

# 8. Frontend scaffold
npm create vite@latest frontend -- --template react
cd frontend
npm install
npm install react-router-dom recharts lightweight-charts lucide-react \
  @tanstack/react-query axios clsx date-fns react-hot-toast react-grid-layout
npm install -D tailwindcss autoprefixer postcss
npx tailwindcss init -p
cd ..

# 9. Create data directory
mkdir -p data

# 10. Docker files
cat > docker-compose.yml << 'EOF'
version: '3.8'
services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app
      - ./data:/app/data
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend
    restart: unless-stopped
EOF

cat > backend/Dockerfile << 'EOF'
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
EOF

cat > frontend/Dockerfile << 'EOF'
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host"]
EOF

# 11. Initial commit
git add .
git commit -m "Project scaffold: backend + frontend + Docker"

echo ""
echo "═══ Bootstrap complete! ═══"
echo ""
echo "Next steps:"
echo "  1. cd trading-agent-platform"
echo "  2. source venv/bin/activate"
echo "  3. claude"
echo "  4. Paste the mega-prompt from the blueprint and build everything"
echo ""
```

### Run it:

```bash
chmod +x bootstrap.sh
./bootstrap.sh
```

---

## 11. Cost Summary (Monthly)

```
┌──────────────────────────────┬────────────┐
│ Service                      │ Cost       │
├──────────────────────────────┼────────────┤
│ Claude Max (API included)    │ $100/mo    │ (you already have this)
│ Robinhood (robin_stocks)     │ Free       │
│ Finnhub (free tier)          │ Free       │
│ Alpaca (paper trading)       │ Free       │
│ Slack (free workspace)       │ Free       │
│ GitHub (private repos)       │ Free       │
│ Docker Desktop               │ Free       │
│ yfinance                     │ Free       │
├──────────────────────────────┼────────────┤
│ LOCAL TOTAL (Week 1)         │ $0 extra   │
├──────────────────────────────┼────────────┤
│ Cloud hosting (later)        │ $10-25/mo  │ Railway/Render
│ Polygon.io (later, optional) │ $30/mo     │ Faster data
├──────────────────────────────┼────────────┤
│ CLOUD TOTAL (post-Week 1)    │ $10-55/mo  │
└──────────────────────────────┴────────────┘
```

---

## 12. Time Estimate (One Go)

```
TOTAL ESTIMATED: 40-56 hours of Claude Code vibe-coding

Backend (Python + FastAPI):
  Data pipeline + RH reader + news      ~3 hrs
  Technical screener (PEG, bases, MA)    ~4 hrs
  Claude analysis + scoring              ~3 hrs
  Strategies + order management          ~3 hrs
  Risk management + kill switch          ~2 hrs
  Slack notifier + daily briefing        ~2 hrs
  FastAPI routes (all 39 endpoints)      ~4 hrs
  Security + auth + audit log            ~2 hrs
  Resilience + state persistence         ~1 hr
  Database models + migrations           ~1 hr
                                        ─────
  Backend subtotal:                     ~25 hrs

Frontend (React + Vite + Tailwind):
  Layout shell + sidebar + routing       ~2 hrs
  Dashboard page                         ~3 hrs
  Portfolio page                         ~2 hrs
  Screener page                          ~2 hrs
  PEG setups page                        ~2 hrs
  Movers page                            ~1 hr
  Sector heatmap page                    ~1 hr
  Analysis detail page                   ~2 hrs
  Settings + Login pages                 ~1 hr
  Toast + modal notification system      ~1 hr
  API client + React Query hooks         ~1 hr
                                        ─────
  Frontend subtotal:                    ~18 hrs

Integration + Deploy:
  Wire frontend ↔ backend               ~2 hrs
  Docker compose + test                  ~1 hr
  GitHub push + README                   ~1 hr
                                        ─────
  Integration subtotal:                  ~4 hrs

GRAND TOTAL:                           ~47 hrs
```

With Claude Code doing the heavy lifting, you can realistically build the core system in 5-7 focused days at 8 hours/day. Some features (drag-and-drop layout, candlestick charts, backtester) can be added iteratively after the core works.
