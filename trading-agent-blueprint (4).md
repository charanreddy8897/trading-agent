# Trading Agent Blueprint — 1-Week Build Plan

## Your Personalized AI Trading Agent

**Goal:** Build an AI-powered trading agent that scans, analyzes, and manages your tech/semi/AI portfolio using your exact methodology (PEG setups, O'Neil bases, Weinstein stages, ADR/ATR framework) — connected to Robinhood, with daily briefings.

**Timeline:** 7 days × 8 hours = 56 hours  
**Tools:** Python, Claude Code, Claude Max (API), open-source libraries  
**Approach:** Vibe-code with Claude Code — describe what you want, iterate fast

---

## Critical Note: Robinhood Connection

Robinhood does **not** have an official public stock trading API. You have two options:

| Option | Pros | Cons |
|--------|------|------|
| **`robin_stocks`** (unofficial Python wrapper) | Reads portfolio, places orders, gets holdings | Unofficial — can break if Robinhood changes endpoints. Use at your own risk. |
| **Alpaca** (official API + paper trading) | Fully supported, paper trading mode, reliable | Separate broker account needed |

**Recommendation:** Use `robin_stocks` to **read** your Robinhood portfolio & holdings. Use Alpaca for **paper trading** new signals. Once validated, you can decide whether to execute via Robinhood or migrate to Alpaca.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    DAILY ORCHESTRATOR                        │
│              (runs every morning + evening)                  │
│         Coordinates all modules, sends you briefing          │
└────┬──────────┬──────────┬──────────┬──────────┬────────────┘
     │          │          │          │          │
┌────▼────┐ ┌──▼───┐ ┌───▼────┐ ┌───▼───┐ ┌───▼─────────┐
│  DATA   │ │SCREEN│ │ANALYSIS│ │ RISK  │ │  PORTFOLIO  │
│ PIPELINE│ │  ER  │ │ ENGINE │ │MANAGER│ │  CONNECTOR  │
│         │ │      │ │        │ │       │ │  (Robinhood)│
│-prices  │ │-PEG  │ │-Claude │ │-sizing│ │-holdings    │
│-news    │ │-ADR  │ │ LLM    │ │-stops │ │-P&L         │
│-earnings│ │-base │ │-technl │ │-sector│ │-orders      │
│-filings │ │-stage│ │-fundmtl│ │-drawdn│ │             │
└─────────┘ └──────┘ └────────┘ └───────┘ └─────────────┘
                          │
                    ┌─────▼──────┐
                    │   DAILY    │
                    │  BRIEFING  │
                    │ (email/SMS)│
                    └────────────┘
```

---

## Day-by-Day Build Plan

---

### DAY 1 (8 hrs): Project Setup + Data Pipeline

**Morning (4 hrs) — Project scaffold + Robinhood connection**

Open Claude Code in your terminal and say:

```
Create a Python trading agent project with this structure:

trading_agent/
├── config/
│   ├── settings.py          # API keys, tickers, thresholds
│   ├── universe.py          # Stock universe by sector
│   └── .env                 # Secrets (gitignored)
├── data/
│   ├── fetcher.py           # Price/volume data from yfinance
│   ├── news_fetcher.py      # News from free APIs
│   └── robinhood_reader.py  # Read RH portfolio via robin_stocks
├── screener/
│   ├── technical.py         # MA, ADR, ATR, VWAP calculations
│   ├── peg_scanner.py       # Power Earnings Gap detector
│   └── base_detector.py     # O'Neil base pattern recognition
├── analysis/
│   ├── claude_analyzer.py   # LLM analysis via Claude API
│   ├── stage_analyzer.py    # Weinstein Stage 2 detection
│   └── scoring.py           # Composite conviction scoring
├── risk/
│   ├── position_sizer.py    # Kelly/fixed-fraction sizing
│   ├── stop_manager.py      # Stop loss logic
│   └── exposure.py          # Sector concentration limits
├── portfolio/
│   ├── robinhood_sync.py    # Sync RH holdings
│   └── tracker.py           # Track positions, entries, P&L
├── alerts/
│   ├── daily_briefing.py    # Morning report generator
│   └── notifier.py          # Email/SMS delivery
├── database/
│   └── models.py            # SQLite models
├── main.py                  # Daily orchestrator
├── requirements.txt
└── README.md
```

**What to tell Claude Code:**

> "Set up the project structure. Install these packages: robin-stocks, yfinance,
> pandas, numpy, ta (technical analysis), anthropic, python-dotenv, schedule,
> sqlite3 (built-in), requests, beautifulsoup4. Create the config with my
> stock universe organized by sector."

**Stock universe to hardcode in `universe.py`:**

```python
SECTORS = {
    "AI_SOFTWARE": [
        "NVDA", "MSFT", "GOOG", "META", "AMZN", "PLTR", "AI",
        "SNOW", "CRM", "NOW", "PATH", "DDOG", "SMCI"
    ],
    "SEMICONDUCTORS": [
        "NVDA", "AMD", "INTC", "AVGO", "QCOM", "MU", "MRVL",
        "ARM", "TSM", "ASML", "LRCX", "AMAT", "ON", "ACMR",
        "TER", "KLAC"
    ],
    "MEMORY": [
        "MU", "WDC", "STX", "NXPI"
    ],
    "SPACE_DEFENSE": [
        "RKLB", "LMT", "BA", "NOC", "ASTS", "LUNR", "RDW",
        "SPIR", "RTX", "GD"
    ],
    "PHYSICAL_AI_ROBOTICS": [
        "ISRG", "TER", "TSLA", "ABBNY", "FANUY",
        "RCAT", "GH"
    ],
}

# Flatten unique tickers
ALL_TICKERS = list(set(
    ticker for sector in SECTORS.values() for ticker in sector
))
```

**Afternoon (4 hrs) — Data pipeline + Robinhood reader**

Tell Claude Code:

> "Build the data fetcher module. It should:
> 1. Use yfinance to pull daily OHLCV for all tickers in my universe (1 year history)
> 2. Store in SQLite database with table: daily_prices (ticker, date, open, high, low, close, volume, adj_close)
> 3. Build the Robinhood reader using robin_stocks that:
>    - Logs in with credentials from .env
>    - Reads current holdings, cost basis, current value, P&L
>    - Stores portfolio snapshot in SQLite
> 4. Build a news fetcher that pulls headlines from free APIs (Finnhub free tier, or NewsAPI free tier)
>    for each ticker in my universe
> 5. Add an update function that only fetches new data (incremental updates)"

**Robinhood login setup:**
```python
# In .env file:
RH_USERNAME=your_email@example.com
RH_PASSWORD=your_password
RH_TOTP=your_2fa_secret  # from Robinhood authenticator setup

# In robinhood_reader.py:
import robin_stocks.robinhood as rh

def login():
    totp = pyotp.TOTP(os.getenv("RH_TOTP")).now()
    rh.login(os.getenv("RH_USERNAME"),
             os.getenv("RH_PASSWORD"),
             mfa_code=totp)

def get_holdings():
    """Returns dict of current positions with cost basis and P&L"""
    return rh.account.build_holdings()

def get_portfolio_value():
    profile = rh.profiles.load_portfolio_profile()
    return float(profile['equity'])
```

**End of Day 1 deliverable:** Running script that fetches price data, reads your Robinhood portfolio, pulls news headlines, and stores everything in SQLite.

---

### DAY 2 (8 hrs): Technical Screener — Your Methodology

**Morning (4 hrs) — Core technical indicators**

Tell Claude Code:

> "Build the technical analysis module. For each ticker, calculate:
>
> Moving Averages:
> - 9 EMA, 21 EMA, 50 SMA, 200 SMA (daily)
> - 10-week MA, 30-week MA (Weinstein)
> - Whether price is above/below each MA
>
> ADR (Average Daily Range):
> - 14-day ADR as percentage
> - Flag stocks in my sweet spot: 3% to 10% ADR
>
> ATR (Average True Range):
> - 14-day ATR
> - ATR extension from 50-day SMA (price distance / ATR)
> - Flag when extension >= 3x ATR (sell signal per my rules)
>
> Relative Volume:
> - Current volume vs 20-day average
> - Flag when RVol > 2x (institutional activity)
>
> Store all calculations in SQLite table: technical_signals"

**Afternoon (4 hrs) — PEG Scanner + Base Detector**

Tell Claude Code:

> "Build the Power Earnings Gap (PEG) scanner based on my exact criteria:
>
> PEG Detection Rules:
> 1. Stock gapped up on earnings day (open > prior close by >= 3%)
> 2. Volume on gap day was >= 2x the 20-day average volume
> 3. The gap has NOT been filled (current price > gap day low)
> 4. Price is above the PEG candle low
>
> For each PEG detected, store:
> - PEG date, PEG low (risk level), gap percentage, volume multiple
> - Days since PEG, current distance from PEG low
> - Whether 9 EMA has caught up to price (entry zone)
>
> Also build the O'Neil Base Detector:
> 1. Identify consolidation periods (price range < 30% for 6+ weeks)
> 2. Count bases: Base 1, 2, 3, 4 (sequential consolidations in uptrend)
> 3. Flag which base number the stock is currently in
> 4. Late-stage warning when Base 3 or Base 4
>
> And Weinstein Stage Detector:
> 1. Stage 1: Price consolidating around flat 30-week MA
> 2. Stage 2: Price above rising 30-week MA (BUY zone)
> 3. Stage 3: Price oscillating around flattening 30-week MA
> 4. Stage 4: Price below declining 30-week MA (AVOID)
> Flag current stage for each ticker."

**End of Day 2 deliverable:** A screener that runs across your universe and outputs a ranked table showing PEG setups, base patterns, Weinstein stage, ADR range, and ATR extension.

---

### DAY 3 (8 hrs): Claude LLM Analysis Engine

**Morning (4 hrs) — Claude-powered stock analyzer**

Tell Claude Code:

> "Build the Claude analysis engine using the Anthropic API. It should:
>
> 1. Take a ticker symbol and gather all context:
>    - Latest technical signals from our database
>    - Recent news headlines (last 7 days)
>    - Current PEG status
>    - Base count and Weinstein stage
>    - ADR/ATR readings
>    - My current position (from Robinhood sync)
>
> 2. Send to Claude API (claude-sonnet-4-20250514) with this system prompt:
>
> SYSTEM PROMPT:
> 'You are a trading analyst specializing in growth stocks. You follow
> the William O'Neil CANSLIM methodology combined with Stan Weinstein
> stage analysis. You evaluate stocks based on:
>
> - Power Earnings Gap (PEG) setups and gap integrity
> - Base patterns (1st, 2nd, 3rd, 4th base)
> - Weinstein Stage (must be Stage 2 for buys)
> - Moving average structure (9 EMA, 21 EMA, 50 SMA, 200 SMA)
> - ADR sweet spot (3-10%)
> - ATR extension from 50 SMA (>3x = extended, consider trim)
> - Volume patterns (accumulation vs distribution)
> - Relative strength vs QQQ/SPY
>
> Your output must be JSON with these fields:
> {
>   "ticker": "SYMBOL",
>   "conviction": 1-10,
>   "action": "BUY" | "ADD" | "HOLD" | "TRIM" | "SELL" | "WATCH",
>   "entry_zone": "price range for entry",
>   "stop_loss": "price level",
>   "risk_reward": "ratio",
>   "stage": "Stage 1/2/3/4",
>   "base_number": 1-4,
>   "key_levels": {"support": X, "resistance": Y},
>   "reasoning": "2-3 sentence thesis",
>   "warnings": ["any red flags"]
> }'
>
> 3. Parse the JSON response and store in SQLite table: claude_analysis
> 4. Batch-analyze all tickers in universe (with rate limiting)"

**Afternoon (4 hrs) — Conviction scoring + sector analysis**

Tell Claude Code:

> "Build a composite scoring system that combines:
>
> Technical Score (0-40 points):
> - Price above 200 SMA: +5
> - Price above 50 SMA: +5
> - Price above 21 EMA: +5
> - Price above 9 EMA: +5
> - ADR in 3-10% range: +5
> - ATR extension < 2x: +5
> - RVol > 1.5x: +5
> - Weinstein Stage 2: +5
>
> Setup Score (0-30 points):
> - Active PEG (gap unfilled): +15
> - Base 1 or 2 (healthy): +10
> - Within 5% of 9 EMA or 21 EMA (entry zone): +5
>
> Fundamental Score (0-30 points):
> - From Claude analysis conviction (scaled to 30)
>
> Total = Technical + Setup + Fundamental (out of 100)
>
> Rank all tickers by total score.
> Also do a sector-level analysis: which sector has the most stocks
> scoring above 70? That's where leadership is."

**End of Day 3 deliverable:** Every stock in your universe gets a conviction score with Claude's analysis, ranked by sector.

---

### DAY 4 (8 hrs): Risk Management + Position Sizing

**Morning (4 hrs) — Position sizer + stop logic**

Tell Claude Code:

> "Build the risk management module using my exact rules:
>
> Position Sizing (for a portfolio read from Robinhood):
> - Max position size: 10% of portfolio
> - Entry in 2 tranches:
>   - Tranche 1: 5% at 9 EMA (guarantee participation)
>   - Tranche 2: 5% at 21 EMA or 50 SMA (deeper pullback)
> - If tranche 2 never fills, that's okay
>
> Stop Loss Rules:
> - Initial stop: below PEG candle low (if PEG setup)
> - Or: below 50 SMA (for non-PEG entries)
> - Max allowed loss per position: -10% from entry
>
> Sell Rules (from my framework):
> - ATR extension >= 3x from 50 SMA → trim 1/3 into strength
> - Base 3 or 4 + parabolic move → trim trading shares
> - Break below 10-day or 21-day on heavy volume after run → reduce
> - Break below 10-week MA on heavy volume → sell signal
> - 30-week MA flattens + price below it → exit (no longer Stage 2)
>
> Sector Exposure:
> - Max 40% in any single sector
> - Alert when correlated sectors (AI + Semi + Memory) exceed 60% combined
>
> Portfolio Circuit Breaker:
> - If portfolio drops > 5% in a single day → halt new buys
> - If portfolio drops > 10% in a week → review all positions"

**Afternoon (4 hrs) — Portfolio tracker**

Tell Claude Code:

> "Build the portfolio tracking module that:
> 1. Syncs with Robinhood holdings every morning
> 2. For each position tracks:
>    - Entry date, entry price, current price
>    - Unrealized P&L ($ and %)
>    - Which tranche filled (1st only or both)
>    - Days held
>    - Current stop loss level
>    - Sector allocation
> 3. Generates portfolio summary:
>    - Total value, daily change, weekly change
>    - Sector breakdown (pie chart data)
>    - Top winners and losers
>    - Positions near stop loss (within 3%)
>    - Positions hitting sell signals"

**End of Day 4 deliverable:** Complete risk engine that sizes positions, manages stops, and tracks your portfolio from Robinhood.

---

### DAY 5 (8 hrs): Daily Briefing + News Engine

**Morning (4 hrs) — Daily briefing generator**

Tell Claude Code:

> "Build the daily briefing system. Every morning at 7 AM PT (before market open),
> it should generate a report with these sections:
>
> === DAILY TRADING BRIEFING ===
>
> 1. MARKET OVERVIEW
>    - SPY, QQQ, SMH (semi ETF) — price, change, where vs key MAs
>    - Market stage assessment (healthy Stage 2 or pulling back?)
>
> 2. YOUR PORTFOLIO
>    - Total value (from Robinhood)
>    - Daily/weekly change
>    - Positions near stop loss (URGENT flags)
>    - Positions hitting ATR extension (trim candidates)
>
> 3. TOP SETUPS TODAY (scored > 70)
>    - Ranked by conviction score
>    - Entry zone, stop, risk/reward for each
>    - Which are PEG setups vs base breakouts
>
> 4. EARNINGS THIS WEEK (from your universe)
>    - Upcoming earnings dates
>    - Pre-earnings positioning notes
>
> 5. SECTOR NEWS
>    - Top 3-5 headlines per sector (AI, Semi, Space, Robotics)
>    - Any policy/regulatory news (chip export controls, etc.)
>
> 6. ACTION ITEMS
>    - Specific trades to consider today
>    - Stops to update
>    - Positions to review
>
> Use Claude API to synthesize the briefing into a clean, readable format.
> Send via email using smtplib (Gmail SMTP)."

**Afternoon (4 hrs) — News aggregation + sentiment**

Tell Claude Code:

> "Build the news engine:
> 1. Pull news from free sources:
>    - Finnhub API (free tier: 60 calls/min)
>    - RSS feeds: Reuters tech, Bloomberg tech, SemiWiki
>    - SEC EDGAR RSS for 8-K filings in my universe
> 2. For each ticker with news, use Claude API to:
>    - Summarize the headline in 1 sentence
>    - Score sentiment: -2 (very bearish) to +2 (very bullish)
>    - Flag if it's earnings-related, regulatory, or M&A
> 3. Store in SQLite: news_items (ticker, date, headline, summary, sentiment, source)
> 4. Feed into daily briefing"

**End of Day 5 deliverable:** A full daily briefing email that arrives before market open with your portfolio status, top setups, and sector news.

---

### DAY 6 (8 hrs): Dashboard + Alerts

**Morning (4 hrs) — Web dashboard (React artifact or Streamlit)**

Tell Claude Code:

> "Build a Streamlit dashboard with these tabs:
>
> Tab 1: PORTFOLIO
> - Current holdings table (synced from Robinhood)
> - P&L heatmap by position
> - Sector allocation donut chart
> - Positions near stops highlighted red
>
> Tab 2: SCREENER
> - All tickers ranked by conviction score
> - Color-coded: green (>70), yellow (50-70), red (<50)
> - Filterable by sector
> - Click a ticker to see Claude's full analysis
>
> Tab 3: PEG SETUPS
> - Active PEG list with gap date, gap %, volume multiple
> - Chart showing price vs PEG low
> - Entry zone markers (9 EMA, 21 EMA)
>
> Tab 4: WATCHLIST
> - Stocks approaching entry zones
> - Stocks about to report earnings
> - New Stage 2 breakouts"

**Afternoon (4 hrs) — Real-time alerts**

Tell Claude Code:

> "Build an alert system that checks every 15 minutes during market hours:
>
> BUY ALERTS:
> - Stock pulls back to 9 EMA after PEG (entry zone)
> - Stock pulls back to 21 EMA / 50 SMA during market dip
> - New PEG detected (earnings gap up with volume)
> - Stock breaks out of base on volume
>
> SELL ALERTS:
> - Position hits stop loss
> - ATR extension reaches 3x (trim signal)
> - Break below 21 EMA on heavy volume
> - Break below 10-week MA
>
> WATCH ALERTS:
> - Earnings in next 5 days for holdings
> - Unusual volume spike (>3x average)
> - Sector rotation signal (SMH breaking down)
>
> Send alerts via email and/or SMS (using Twilio free tier or email-to-SMS)"

**End of Day 6 deliverable:** A running dashboard and real-time alert system.

---

### DAY 7 (8 hrs): Integration, Testing, Automation

**Morning (4 hrs) — Wire everything together**

Tell Claude Code:

> "Create main.py as the daily orchestrator:
>
> MORNING RUN (7:00 AM PT):
> 1. Sync Robinhood portfolio
> 2. Update price data (yfinance)
> 3. Calculate all technical indicators
> 4. Run PEG scanner
> 5. Run base detector
> 6. Run Weinstein stage analysis
> 7. Run Claude analysis on top 20 tickers
> 8. Generate conviction scores
> 9. Check sell signals on existing positions
> 10. Generate and send daily briefing email
>
> INTRADAY (every 15 min, 9:30 AM - 4:00 PM ET):
> 1. Check price vs alert levels
> 2. Send alerts if triggered
>
> EVENING RUN (5:00 PM PT):
> 1. Update daily data
> 2. Log portfolio performance
> 3. Check for after-hours earnings
>
> Use Python schedule library or cron.
> Add error handling and logging throughout.
> If any module fails, log the error and continue with others."

**Afternoon (4 hrs) — Test, debug, deploy**

> "Test the full pipeline end to end:
> 1. Run morning pipeline manually, verify each step
> 2. Check that Robinhood sync works
> 3. Verify Claude analysis returns valid JSON
> 4. Send test briefing email
> 5. Set up as a systemd service or cron job on my machine
> 6. Add a simple healthcheck endpoint
> 7. Write README with setup instructions"

**End of Day 7 deliverable:** Fully working trading agent running on schedule.

---

## Key Libraries & Costs

### Python Packages (all free/open-source)

```
# requirements.txt
robin-stocks==3.0.6        # Robinhood unofficial API
yfinance==0.2.31           # Yahoo Finance data
pandas==2.1.0              # Data manipulation
numpy==1.25.0              # Numerical computing
ta==0.11.0                 # Technical analysis indicators
anthropic==0.40.0          # Claude API
python-dotenv==1.0.0       # Environment variables
schedule==1.2.0            # Task scheduling
requests==2.31.0           # HTTP requests
beautifulsoup4==4.12.0     # Web scraping
streamlit==1.36.0          # Dashboard
plotly==5.18.0             # Charts
pyotp==2.9.0               # 2FA for Robinhood
sqlite3                    # Built-in database
```

### API Keys Needed

| Service | Cost | Purpose |
|---------|------|---------|
| Anthropic (Claude) | Included in Claude Max | LLM analysis engine |
| Robinhood (robin_stocks) | Free (your account) | Portfolio sync |
| Finnhub | Free tier (60 calls/min) | News headlines |
| yfinance | Free | Price/volume data |
| Gmail SMTP | Free | Email alerts |
| Twilio (optional) | Free tier | SMS alerts |

**Total extra cost: $0 – $30/month** (mostly free with Claude Max)

---

## Your Trading Rules Encoded as Code Logic

These rules from your educational posts are built into the agent:

### Entry Rules
```
IF stock has active PEG (gap unfilled, volume 3x+)
AND Weinstein Stage 2 (price > rising 30-week MA)
AND ADR between 3% and 10%
AND price pulling back to 9 EMA
→ BUY tranche 1 (5% of portfolio)

IF price pulls back further to 21 EMA or 50 SMA
AND market (QQQ) also pulling back 3-5%
→ BUY tranche 2 (remaining 5%)
```

### Hold Rules
```
IF trend intact (above 50 SMA)
AND respecting key MAs and VWAPs
AND thesis unchanged (fundamentals still growing)
→ HOLD through -10% to -20% pullback
```

### Sell Rules
```
IF ATR extension >= 3x from 50 SMA → TRIM 1/3
IF Base 3 or 4 + going vertical → TRIM trading shares
IF breaks 10-day or 21-day on heavy volume → REDUCE
IF breaks 10-week MA on heavy volume → SELL
IF 30-week MA flattens + price below it → EXIT
```

### 3-Day Earnings Rule
```
IF stock gaps DOWN on earnings:
→ DO NOT BUY for 3 trading days
→ Wait for volatility to settle
→ Focus only on gap-UP names (PEG watchlist)
```

---

## What Claude Code Prompts to Use

Here are ready-to-paste prompts for Claude Code for each module. Copy the day's prompt and iterate:

### Day 1 Starter Prompt
```
I'm building a trading agent in Python. Create the full project structure
with these modules: data pipeline (yfinance + SQLite), Robinhood portfolio
reader (robin_stocks), news fetcher (Finnhub). Here's my stock universe:
[paste SECTORS dict]. Set up virtual env, install dependencies, and make
the data fetcher pull 1 year of daily OHLCV for all tickers. Store in SQLite.
```

### Day 3 Claude Analysis Prompt
```
Build a module that takes a ticker symbol, gathers its technical signals
and recent news from our SQLite database, then calls the Anthropic API
(claude-sonnet-4-20250514) with a trading analyst system prompt.
The system prompt should encode O'Neil CANSLIM + Weinstein stage analysis.
Return JSON with conviction score, action, entry zone, stop loss, and reasoning.
Batch-process all tickers with 1-second delay between calls.
```

### Day 5 Briefing Prompt
```
Build a daily briefing generator that:
1. Reads portfolio from Robinhood
2. Checks all positions against sell rules
3. Ranks universe by conviction score
4. Pulls top sector news
5. Formats as a clean email report
6. Sends via Gmail SMTP at 7 AM PT
Use Claude API to write the narrative sections of the briefing.
```

---

## Gradual Improvement Roadmap (Post Week 1)

Once the core is running, iterate weekly:

**Week 2-3:** Add backtesting — test your PEG strategy on historical data. Use `vectorbt` or `backtrader`.

**Week 4:** Add earnings calendar integration (pull from Yahoo Finance earnings calendar). Auto-update PEG watchlist after each earnings season.

**Week 5-6:** Add options flow data — unusual options activity often precedes big moves in semis/AI stocks.

**Week 7-8:** Build an Alpaca paper trading integration for automated execution of high-conviction signals.

**Month 3+:** Add institutional tracking (13F filings from SEC EDGAR), cross-reference with your Fintel/HedgeFollow workflow.

**Ongoing:** Fine-tune Claude's system prompt based on which calls it got right vs wrong. Track hit rate by sector.

---

## Risk Disclaimer

This is a tool to assist YOUR decision-making — not to replace it. Algorithmic trading carries real financial risk. Always:

- Paper trade first before using real money
- Start with small position sizes
- Never risk more than you can afford to lose
- The `robin_stocks` library is unofficial and unsupported
- Past performance does not guarantee future results
- This is not financial advice

---

## Quick Start (Copy-Paste into Terminal)

```bash
# Step 1: Create project
mkdir trading_agent && cd trading_agent
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Step 2: Install core dependencies
pip install robin-stocks yfinance pandas numpy ta anthropic \
    python-dotenv schedule requests beautifulsoup4 streamlit \
    plotly pyotp

# Step 3: Create .env file
cat > .env << 'EOF'
RH_USERNAME=your_email
RH_PASSWORD=your_password
RH_TOTP=your_2fa_secret
ANTHROPIC_API_KEY=your_key
FINNHUB_API_KEY=your_key
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password
EOF

# Step 4: Open Claude Code and start building
claude
```

Then paste the Day 1 prompt and start vibe-coding.

---
---

# PART 2: React Dashboard + Full-Stack Architecture + Cloud Deployment

---

## Updated Full-Stack Architecture

The original plan used Streamlit. We're replacing that with a proper React frontend + FastAPI backend — production-grade, cloud-deployable, GitHub-ready.

```
┌─────────────────────────────────────────────────────────────────────┐
│                         GITHUB REPO                                 │
│                   trading-agent-platform/                            │
├──────────────────────────┬──────────────────────────────────────────┤
│      BACKEND (Python)    │           FRONTEND (React)               │
│      /backend            │           /frontend                      │
│                          │                                          │
│  ┌──────────────────┐    │    ┌──────────────────────────────┐      │
│  │   FastAPI Server  │◄──HTTP──►│      React + Vite App       │      │
│  │   (REST API)      │    │    │                              │      │
│  │                   │    │    │  ┌────────┐ ┌──────────┐    │      │
│  │  /api/portfolio   │    │    │  │Dashboard│ │ Screener │    │      │
│  │  /api/screener    │    │    │  │  Page   │ │   Page   │    │      │
│  │  /api/analysis    │    │    │  └────────┘ └──────────┘    │      │
│  │  /api/news        │    │    │  ┌────────┐ ┌──────────┐    │      │
│  │  /api/alerts      │    │    │  │  PEG   │ │ Analysis │    │      │
│  │  /api/movers      │    │    │  │ Setups │ │  Detail  │    │      │
│  │  /api/settings    │    │    │  └────────┘ └──────────┘    │      │
│  └────────┬─────────┘    │    │  ┌────────┐ ┌──────────┐    │      │
│           │              │    │  │ Movers │ │ Sector   │    │      │
│  ┌────────▼─────────┐    │    │  │& Losers│ │ Heatmap  │    │      │
│  │  Trading Engine   │    │    │  └────────┘ └──────────┘    │      │
│  │  (existing Day1-5 │    │    └──────────────────────────────┘      │
│  │   modules)        │    │                                          │
│  └────────┬─────────┘    │                                          │
│           │              │                                          │
│  ┌────────▼─────────┐    │                                          │
│  │    SQLite /       │    │                                          │
│  │    PostgreSQL     │    │                                          │
│  └──────────────────┘    │                                          │
├──────────────────────────┴──────────────────────────────────────────┤
│                        DEPLOYMENT                                    │
│  Local → Docker Compose → Cloud (Railway / Render / AWS)            │
└─────────────────────────────────────────────────────────────────────┘
```

---

## GitHub Repository Structure

```
trading-agent-platform/
│
├── README.md
├── .gitignore
├── .env.example                    # Template (never commit real .env)
├── docker-compose.yml              # Local + cloud deployment
├── docker-compose.prod.yml         # Production overrides
│
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                     # FastAPI app entry point
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes_portfolio.py     # GET /api/portfolio/*
│   │   ├── routes_screener.py      # GET /api/screener/*
│   │   ├── routes_analysis.py      # GET /api/analysis/*
│   │   ├── routes_news.py          # GET /api/news/*
│   │   ├── routes_movers.py        # GET /api/movers/*
│   │   ├── routes_alerts.py        # GET /api/alerts/*
│   │   └── routes_settings.py      # GET/POST /api/settings/*
│   ├── config/
│   │   ├── settings.py
│   │   ├── universe.py             # Sector → ticker mapping
│   │   └── trading_rules.py        # Your rules as constants
│   ├── data/
│   │   ├── fetcher.py              # yfinance price data
│   │   ├── news_fetcher.py         # Finnhub / RSS news
│   │   └── robinhood_reader.py     # robin_stocks integration
│   ├── screener/
│   │   ├── technical.py            # MAs, ADR, ATR, RVol
│   │   ├── peg_scanner.py          # Power Earnings Gap
│   │   ├── base_detector.py        # O'Neil base counting
│   │   └── stage_analyzer.py       # Weinstein stages
│   ├── analysis/
│   │   ├── claude_analyzer.py      # Claude API analysis
│   │   └── scoring.py              # Composite conviction scoring
│   ├── risk/
│   │   ├── position_sizer.py       # 2-tranche sizing logic
│   │   ├── stop_manager.py         # Stop loss rules
│   │   └── exposure.py             # Sector concentration
│   ├── portfolio/
│   │   ├── robinhood_sync.py       # Sync RH holdings
│   │   └── tracker.py              # Position tracking + P&L
│   ├── alerts/
│   │   ├── daily_briefing.py       # Morning email report
│   │   └── notifier.py             # Email / SMS delivery
│   ├── scheduler/
│   │   └── jobs.py                 # Cron-style scheduled tasks
│   ├── database/
│   │   ├── models.py               # SQLAlchemy models
│   │   ├── connection.py           # DB session management
│   │   └── migrations/             # Alembic migrations (later)
│   └── tests/
│       ├── test_screener.py
│       ├── test_analysis.py
│       └── test_portfolio.py
│
├── frontend/
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.js
│   ├── tailwind.config.js
│   ├── index.html
│   ├── public/
│   │   └── favicon.svg
│   └── src/
│       ├── main.jsx                # App entry
│       ├── App.jsx                 # Router + layout
│       ├── index.css               # Global styles + fonts
│       ├── api/
│       │   └── client.js           # Axios/fetch wrapper for backend
│       ├── hooks/
│       │   ├── usePortfolio.js     # Portfolio data hook
│       │   ├── useScreener.js      # Screener data hook
│       │   ├── useMovers.js        # Top movers/losers hook
│       │   └── useWebSocket.js     # Real-time alerts (later)
│       ├── pages/
│       │   ├── Dashboard.jsx       # Main overview page
│       │   ├── Portfolio.jsx       # Holdings + P&L detail
│       │   ├── Screener.jsx        # Conviction-ranked universe
│       │   ├── PegSetups.jsx       # Power Earnings Gap board
│       │   ├── Analysis.jsx        # Per-ticker Claude analysis
│       │   ├── Movers.jsx          # Top movers / losers
│       │   ├── SectorView.jsx      # Sector heatmap + rotation
│       │   └── Settings.jsx        # Universe config, API keys
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Sidebar.jsx     # Navigation sidebar
│       │   │   ├── Header.jsx      # Top bar with portfolio value
│       │   │   └── Layout.jsx      # Shell wrapper
│       │   ├── charts/
│       │   │   ├── PortfolioChart.jsx      # Equity curve
│       │   │   ├── SectorDonut.jsx         # Sector allocation
│       │   │   ├── ConvictionBar.jsx       # Horizontal score bar
│       │   │   ├── MiniSparkline.jsx       # Inline sparklines
│       │   │   ├── HeatmapGrid.jsx         # Sector heatmap
│       │   │   └── PerformanceWaterfall.jsx # P&L waterfall
│       │   ├── tables/
│       │   │   ├── HoldingsTable.jsx       # Sortable holdings
│       │   │   ├── ScreenerTable.jsx       # Ranked tickers
│       │   │   └── MoversTable.jsx         # Top movers/losers
│       │   ├── cards/
│       │   │   ├── MetricCard.jsx          # KPI card (value + delta)
│       │   │   ├── TickerCard.jsx          # Individual stock card
│       │   │   ├── AlertCard.jsx           # Alert notification
│       │   │   └── PegCard.jsx             # PEG setup card
│       │   └── shared/
│       │       ├── Badge.jsx               # Status badges
│       │       ├── Tooltip.jsx             # Hover tooltips
│       │       └── LoadingSkeleton.jsx     # Loading states
│       └── utils/
│           ├── formatters.js       # Number/currency/percent formatting
│           ├── colors.js           # Color scales and palettes
│           └── constants.js        # Sector colors, thresholds
│
├── scripts/
│   ├── seed_data.py                # Seed DB with historical data
│   ├── run_backtest.py             # Backtest runner (Phase 2)
│   └── deploy.sh                   # Deployment helper
│
└── docs/
    ├── API.md                      # Backend API documentation
    ├── SETUP.md                    # Local setup instructions
    └── DEPLOYMENT.md               # Cloud deployment guide
```

---

## Backend API Design (FastAPI)

The React frontend talks to the Python backend through these REST endpoints. The backend wraps all your existing trading engine modules.

### API Endpoints

```
BASE URL: http://localhost:8000/api (local)
         https://your-app.railway.app/api (cloud)

─────────────────────────────────────────────────────────────
PORTFOLIO
─────────────────────────────────────────────────────────────
GET  /api/portfolio/summary
     → { total_value, daily_change, daily_pct, weekly_change,
         cash_available, buying_power }

GET  /api/portfolio/holdings
     → [ { ticker, shares, avg_cost, current_price, market_value,
            unrealized_pnl, unrealized_pct, sector, days_held,
            stop_loss, tranche_1_filled, tranche_2_filled,
            near_stop (bool), sell_signal (string|null) } ]

GET  /api/portfolio/performance?period=1M|3M|6M|1Y|YTD
     → [ { date, equity, daily_return, cumulative_return } ]

GET  /api/portfolio/sector-allocation
     → [ { sector, value, percentage, ticker_count } ]

─────────────────────────────────────────────────────────────
SCREENER
─────────────────────────────────────────────────────────────
GET  /api/screener/ranked?sector=all|AI_SOFTWARE|SEMICONDUCTORS|...
     → [ { ticker, sector, conviction_score, technical_score,
            setup_score, fundamental_score, action, stage,
            base_number, adr_pct, atr_extension, rvol,
            price, change_pct, above_50sma (bool),
            above_200sma (bool), peg_active (bool) } ]

GET  /api/screener/filters
     → { available_sectors, score_range, adr_range }

─────────────────────────────────────────────────────────────
ANALYSIS
─────────────────────────────────────────────────────────────
GET  /api/analysis/{ticker}
     → { ticker, conviction, action, entry_zone, stop_loss,
         risk_reward, stage, base_number, key_levels,
         reasoning, warnings, analyzed_at,
         technicals: { ema9, ema21, sma50, sma200, adr, atr,
                       atr_extension, rvol, volume_trend },
         price_history: [ {date, close} ] (90 days) }

POST /api/analysis/{ticker}/refresh
     → triggers fresh Claude analysis, returns updated result

─────────────────────────────────────────────────────────────
PEG SETUPS
─────────────────────────────────────────────────────────────
GET  /api/peg/active
     → [ { ticker, peg_date, peg_low, gap_pct, volume_multiple,
            days_since, current_price, distance_from_peg_low_pct,
            ema9_caught_up (bool), entry_zone, sector } ]

GET  /api/peg/history
     → [ { ticker, peg_date, gap_pct, outcome, max_gain_pct } ]

─────────────────────────────────────────────────────────────
MOVERS
─────────────────────────────────────────────────────────────
GET  /api/movers/top?count=10
     → { gainers: [ {ticker, price, change_pct, volume, rvol} ],
         losers:  [ {ticker, price, change_pct, volume, rvol} ] }

GET  /api/movers/unusual-volume?threshold=2.0
     → [ { ticker, volume, avg_volume, rvol, price, change_pct } ]

─────────────────────────────────────────────────────────────
NEWS
─────────────────────────────────────────────────────────────
GET  /api/news/feed?sector=all&limit=50
     → [ { ticker, headline, summary, sentiment (-2 to +2),
            source, published_at, category } ]

GET  /api/news/earnings-calendar?days=14
     → [ { ticker, earnings_date, estimate_eps, sector } ]

─────────────────────────────────────────────────────────────
ALERTS
─────────────────────────────────────────────────────────────
GET  /api/alerts/active
     → [ { id, type, ticker, message, severity, created_at } ]

POST /api/alerts/{id}/dismiss
     → { dismissed: true }

─────────────────────────────────────────────────────────────
SYSTEM
─────────────────────────────────────────────────────────────
GET  /api/health
     → { status, last_data_update, last_rh_sync, db_size }

POST /api/system/run-pipeline
     → triggers manual pipeline run

GET  /api/system/pipeline-status
     → { running (bool), last_run, next_run, steps_completed }
```

### FastAPI Main App Structure

```python
# backend/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api import (routes_portfolio, routes_screener, routes_analysis,
                 routes_news, routes_movers, routes_alerts, routes_settings)
from scheduler.jobs import start_scheduler

app = FastAPI(title="Trading Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "https://your-domain.com"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes_portfolio.router, prefix="/api/portfolio")
app.include_router(routes_screener.router,  prefix="/api/screener")
app.include_router(routes_analysis.router,  prefix="/api/analysis")
app.include_router(routes_news.router,      prefix="/api/news")
app.include_router(routes_movers.router,    prefix="/api/movers")
app.include_router(routes_alerts.router,    prefix="/api/alerts")
app.include_router(routes_settings.router,  prefix="/api/settings")

@app.on_event("startup")
async def startup():
    start_scheduler()  # kick off background jobs

@app.get("/api/health")
async def health():
    return {"status": "ok"}
```

---

## React Dashboard — Page-by-Page Design Spec

### Design Direction

**Aesthetic:** Bloomberg Terminal meets modern fintech — dark theme, data-dense, no wasted space. Monospace numbers for alignment. Color-coded signals (green = bullish, red = bearish, amber = caution, cyan = neutral/info).

**Font Pairing:**
- Display/headers: `JetBrains Mono` (sharp, technical)
- Body text: `DM Sans` (clean, readable)
- Numbers/data: `JetBrains Mono` (alignment matters for financial data)

**Color Palette:**
```css
:root {
  --bg-primary:    #0a0e17;     /* Deep navy-black */
  --bg-secondary:  #111827;     /* Card backgrounds */
  --bg-tertiary:   #1a2235;     /* Hover / active states */
  --border:        #1e293b;     /* Subtle borders */
  --text-primary:  #e2e8f0;     /* Main text */
  --text-secondary:#94a3b8;     /* Muted text */
  --accent-green:  #10b981;     /* Profit / bullish */
  --accent-red:    #ef4444;     /* Loss / bearish */
  --accent-amber:  #f59e0b;     /* Warning / caution */
  --accent-cyan:   #06b6d4;     /* Info / neutral */
  --accent-blue:   #3b82f6;     /* Primary actions */
  --accent-violet: #8b5cf6;     /* AI/Claude analysis */
}
```

---

### PAGE 1: Dashboard (Main Overview)

This is the home page — a snapshot of everything that matters before market open.

```
┌─────────────────────────────────────────────────────────────────┐
│ SIDEBAR │  HEADER: Portfolio Value  $347,250  ▲ +1.2% today    │
│         │─────────────────────────────────────────────────────── │
│ 📊 Dash │                                                       │
│ 💼 Port │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ │
│ 🔍 Scan │  │Total Val  │ │Daily P&L │ │ Open     │ │ Conviction│ │
│ ⚡ PEG  │  │$347,250   │ │+$4,127   │ │ Positions│ │ Avg Score │ │
│ 📰 News │  │▲ 12.3% YTD│ │▲ 1.20%   │ │    12    │ │   74/100  │ │
│ 🔥 Move │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ │
│ 🗺  Sect │                                                       │
│ ⚙  Set  │  ┌─────────────────────────┐ ┌───────────────────────┐│
│         │  │  EQUITY CURVE (recharts) │ │   SECTOR ALLOCATION   ││
│         │  │  Line chart: portfolio   │ │   Donut chart:         ││
│         │  │  value over 1M/3M/6M/1Y  │ │   Semi: 35%           ││
│         │  │  vs SPY benchmark        │ │   AI/SW: 28%          ││
│         │  │  Shaded area underneath  │ │   Space: 15%          ││
│         │  │                          │ │   Robotics: 12%       ││
│         │  │                          │ │   Memory: 10%         ││
│         │  └─────────────────────────┘ └───────────────────────┘│
│         │                                                       │
│         │  ┌──────────────────────┐ ┌──────────────────────────┐│
│         │  │  🔥 TOP MOVERS       │ │  🚨 ACTIVE ALERTS        ││
│         │  │                      │ │                           ││
│         │  │  RKLB   +8.4%  ██▓  │ │  ⚠ NVDA: ATR ext 3.2x   ││
│         │  │  PLTR   +5.1%  ██▒  │ │  🛑 MU: Near stop $88    ││
│         │  │  ARM    +3.7%  ██   │ │  ✅ TER: PEG entry zone   ││
│         │  │  ...                │ │  ⚠ Semi exposure: 42%     ││
│         │  │  INTC   -4.2%  ██▓  │ │                           ││
│         │  │  SPIR   -3.1%  ██   │ │                           ││
│         │  └──────────────────────┘ └──────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Components used:**
- `MetricCard` × 4 across the top (total value, daily P&L, positions, avg score)
- `PortfolioChart` — recharts `AreaChart` with gradient fill, period toggle
- `SectorDonut` — recharts `PieChart` with custom labels
- `MoversTable` — top 5 gainers, top 5 losers with inline bar width = |change%|
- `AlertCard` list — severity-colored, dismissable

---

### PAGE 2: Portfolio (Holdings Detail)

```
┌─────────────────────────────────────────────────────────────────┐
│  PORTFOLIO HOLDINGS                           Sort: P&L ▼      │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─────────────────────────── WATERFALL CHART ─────────────────┐│
│  │  P&L by position (horizontal bars, green/red)               ││
│  │  NVDA ███████████████████████  +$12,400                     ││
│  │  PLTR ██████████████           +$6,200                      ││
│  │  ARM  █████████                +$3,800                      ││
│  │  MU   ████ (red)              -$1,200                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────────── HOLDINGS TABLE ──────────────────┐│
│  │ Ticker│Shares│ Avg Cost │ Price  │ Mkt Val │  P&L   │  %   ││
│  │───────┼──────┼──────────┼────────┼─────────┼────────┼──────││
│  │ NVDA  │  45  │ $108.20  │$134.50 │$6,052   │+$1,183 │▲ 24%││
│  │ PLTR  │ 200  │  $62.30  │ $78.10 │$15,620  │+$3,160 │▲ 25%││
│  │ ARM   │  30  │ $142.00  │$168.40 │$5,052   │+$792   │▲ 19%││
│  │ MU  🛑│ 100  │  $96.50  │ $89.20 │$8,920   │-$730   │▼ -8%││
│  │ ...   │      │          │        │         │        │      ││
│  │───────┼──────┼──────────┼────────┼─────────┼────────┼──────││
│  │ Row expands on click → shows:                               ││
│  │   Entry date, stop loss, stage, base#, sector, tranches     ││
│  │   Mini price chart (90d sparkline with MA overlays)          ││
│  │   Claude analysis summary + conviction score                 ││
│  │   Action buttons: [Refresh Analysis] [Update Stop]           ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ⚠ SELL SIGNALS ACTIVE:                                        │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │ MU — Price within 3% of stop loss ($88.00). Review thesis.  ││
│  │ NVDA — ATR extension 3.2x from 50 SMA. Consider trim 1/3.  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Key features:**
- 🛑 icon on holdings near stop loss
- Expandable rows with Claude analysis inline
- P&L waterfall chart at top for visual impact
- Sell signals panel at bottom (auto-generated from risk engine)

---

### PAGE 3: Screener (Conviction-Ranked Universe)

```
┌─────────────────────────────────────────────────────────────────┐
│  CONVICTION SCREENER               Filter: [All Sectors ▼]     │
│                                    Score:  [70+ only ▼]        │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─ SCORE DISTRIBUTION ────────────────────────────────────────┐│
│  │  Histogram showing how many stocks at each score bucket      ││
│  │  [0-30: 5] [30-50: 8] [50-70: 12] [70-85: 9] [85+: 3]     ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─────────────────────── RANKED TABLE ────────────────────────┐│
│  │ # │Ticker│Score│Tech│Setup│Fund│Action│Stage│ADR% │PEG│Sect││
│  │───┼──────┼─────┼────┼─────┼────┼──────┼─────┼─────┼───┼────││
│  │ 1 │ TER  │ 92  │ 35 │  30 │ 27 │ BUY  │ S2  │5.2% │ ✅│Semi││
│  │ 2 │ RKLB │ 87  │ 32 │  30 │ 25 │ BUY  │ S2  │7.1% │ ✅│Spce││
│  │ 3 │ PLTR │ 81  │ 34 │  20 │ 27 │ ADD  │ S2  │4.8% │   │AI  ││
│  │ 4 │ ARM  │ 78  │ 30 │  25 │ 23 │WATCH │ S2  │6.3% │   │Semi││
│  │ 5 │ NVDA │ 74  │ 35 │  15 │ 24 │ HOLD │ S2  │3.9% │   │Semi││
│  │ ...                                                          ││
│  │                                                              ││
│  │ Score bar visualization:                                     ││
│  │ ████████████████████████████████████░░░░░░  74/100           ││
│  │ ├── Tech ──┤├─ Setup ─┤├─ Fund ──┤                          ││
│  │                                                              ││
│  │ Click row → navigates to /analysis/{ticker}                  ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

**Key features:**
- Stacked horizontal bar showing score breakdown (tech / setup / fundamental)
- PEG column shows ✅ for active PEG setups
- Color-coded action badges (BUY=green, SELL=red, HOLD=gray, WATCH=cyan)
- Filterable by sector, score threshold, stage, ADR range
- Click-through to detailed analysis page

---

### PAGE 4: PEG Setups (Power Earnings Gap Board)

```
┌─────────────────────────────────────────────────────────────────┐
│  ⚡ POWER EARNINGS GAP SETUPS                                  │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─── ACTIVE PEG CARDS (grid layout) ──────────────────────────┐│
│  │                                                              ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌──────────────┐ ││
│  │  │ TER         Semi│  │ RKLB       Space│  │ GH       Robo│ ││
│  │  │                 │  │                 │  │              │ ││
│  │  │ PEG: Jan 28     │  │ PEG: Feb 5      │  │ PEG: Feb 12  │ ││
│  │  │ Gap: +12.3%     │  │ Gap: +18.7%     │  │ Gap: +9.4%   │ ││
│  │  │ Vol: 4.2x avg   │  │ Vol: 6.1x avg   │  │ Vol: 3.3x avg│ ││
│  │  │                 │  │                 │  │              │ ││
│  │  │ ─── mini chart ─│  │ ─── mini chart ─│  │ ─ mini chart─│ ││
│  │  │ (price line with│  │ (shows gap day  │  │ (PEG low     │ ││
│  │  │  PEG low as     │  │  and current    │  │  marked as   │ ││
│  │  │  dashed line)   │  │  price action)  │  │  support)    │ ││
│  │  │                 │  │                 │  │              │ ││
│  │  │ PEG Low: $142.30│  │ PEG Low: $22.50 │  │ PEG Low: $78 │ ││
│  │  │ Current: $158.40│  │ Current: $28.10  │  │ Cur: $84.20  │ ││
│  │  │ 9EMA: $155.20 ✅│  │ 9EMA: $26.80    │  │ 9EMA: $82.10 │ ││
│  │  │                 │  │                 │  │              │ ││
│  │  │ [Entry Zone]    │  │ [Watching]      │  │ [Entry Zone] │ ││
│  │  │ Risk: -11.3%    │  │ Risk: -19.9%    │  │ Risk: -7.4%  │ ││
│  │  └─────────────────┘  └─────────────────┘  └──────────────┘ ││
│  │                                                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─── PEG HISTORY (past setups + outcomes) ────────────────────┐│
│  │ Ticker│ PEG Date │ Gap%  │ Max Gain │ Outcome │ Days Held   ││
│  │ TER   │ Jul 30   │ +9.2% │ +45%     │ Winner  │ 87 days     ││
│  │ TER   │ Oct 28   │ +11%  │ +53%     │ Winner  │ 64 days     ││
│  │ PLTR  │ Nov 5    │ +14%  │ +38%     │ Active  │ ongoing     ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### PAGE 5: Top Movers & Losers

```
┌─────────────────────────────────────────────────────────────────┐
│  🔥 TOP MOVERS & LOSERS          Period: [Today ▼]             │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─── TODAY'S MOVERS (your universe only) ─────────────────────┐│
│  │                                                              ││
│  │  GAINERS                      │  LOSERS                      ││
│  │  ─────────────────────        │  ─────────────────────       ││
│  │  1. RKLB   +8.4%  RVol: 3.2  │  1. INTC   -4.2%  RVol: 1.8││
│  │     ████████████████████▓     │     ████████████████▓        ││
│  │     Space · $28.10 · S2       │     Semi · $24.30 · S3       ││
│  │                               │                              ││
│  │  2. PLTR   +5.1%  RVol: 2.1  │  2. SPIR   -3.1%  RVol: 0.8││
│  │     █████████████▒            │     ██████████▒              ││
│  │     AI/SW · $78.10 · S2       │     Space · $4.20 · S1       ││
│  │                               │                              ││
│  │  3. ARM    +3.7%  RVol: 1.5  │  3. AI     -2.8%  RVol: 1.1 ││
│  │     ██████████                │     ████████▒                ││
│  │     Semi · $168.40 · S2       │     AI/SW · $22.50 · S2      ││
│  │                               │                              ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─── UNUSUAL VOLUME (RVol > 2x) ─────────────────────────────┐│
│  │ Ticker │ Volume    │ Avg Vol  │ RVol │ Price │ Chg%  │ Why? ││
│  │ RKLB   │ 45.2M     │ 14.1M   │ 3.2x │$28.10 │ +8.4% │ 📰  ││
│  │ PLTR   │ 82.3M     │ 39.2M   │ 2.1x │$78.10 │ +5.1% │ 📊  ││
│  │ ACMR   │ 3.8M      │ 1.5M   │ 2.5x │$31.20 │ +2.1% │ 🏛   ││
│  │                                                              ││
│  │ 📰 = News  📊 = Earnings  🏛 = Institutional  ⚡ = PEG       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─── SECTOR PERFORMANCE (heatmap grid) ───────────────────────┐│
│  │                                                              ││
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐         ││
│  │  │ SEMI  +2.1%  │ │ AI/SW +1.8%  │ │ SPACE +3.4%  │         ││
│  │  │  (green bg)  │ │  (green bg)  │ │ (bright grn) │         ││
│  │  └──────────────┘ └──────────────┘ └──────────────┘         ││
│  │  ┌──────────────┐ ┌──────────────┐                          ││
│  │  │ MEMORY -0.3% │ │ ROBOTICS+0.9%│                          ││
│  │  │  (red bg)    │ │  (light grn) │                          ││
│  │  └──────────────┘ └──────────────┘                          ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### PAGE 6: Sector Heatmap & Rotation

```
┌─────────────────────────────────────────────────────────────────┐
│  🗺 SECTOR ROTATION VIEW                                        │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─── TREEMAP HEATMAP ────────────────────────────────────────┐ │
│  │  (recharts Treemap — each box = 1 stock,                   │ │
│  │   size = market cap or position size,                      │ │
│  │   color = daily % change, green→red gradient)              │ │
│  │                                                             │ │
│  │  ┌──────────────────────┐┌────────────┐┌─────────────────┐ │ │
│  │  │       NVDA           ││   AVGO     ││     AMD         │ │ │
│  │  │      +1.2%           ││   +0.8%   ││    -0.3%        │ │ │
│  │  │    (large, green)    ││  (green)  ││   (light red)   │ │ │
│  │  ├──────────┬───────────┤├────────────┤├────────┬────────┤ │ │
│  │  │  ARM     │   MU      ││   PLTR     ││ RKLB   │  TER  │ │ │
│  │  │ +3.7%   │  -1.2%   ││   +5.1%    ││ +8.4% │ +2.1% │ │ │
│  │  └──────────┴───────────┘└────────────┘└────────┴────────┘ │ │
│  └─────────────────────────────────────────────────────────────┘ │
│                                                                 │
│  ┌─── SECTOR STRENGTH RANKING ─────────────────────────────────┐│
│  │  Sector         │ Avg Score │ Stage 2 % │ PEG Count │ Trend ││
│  │  Space/Defense  │    78     │    80%    │     2     │  ▲▲▲  ││
│  │  AI/Software    │    74     │    75%    │     1     │  ▲▲   ││
│  │  Semiconductors │    71     │    85%    │     3     │  ▲    ││
│  │  Robotics       │    65     │    60%    │     1     │  ──   ││
│  │  Memory         │    52     │    50%    │     0     │  ▼    ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌─── SECTOR EXPOSURE vs LIMITS ───────────────────────────────┐│
│  │  Semi+Memory+AI (correlated): 58% / 60% limit  ⚠ NEAR CAP ││
│  │  ████████████████████████████████████████████████░░░░░░░░░░ ││
│  │                                                              ││
│  │  Space/Defense: 15% / 40% limit                              ││
│  │  ████████████░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░ ││
│  └─────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────┘
```

---

### PAGE 7: Analysis Detail (Per-Ticker Deep Dive)

```
┌─────────────────────────────────────────────────────────────────┐
│  NVDA — NVIDIA Corp                    Conviction: 74/100      │
│  AI/Software · Semiconductors          Action: HOLD            │
│─────────────────────────────────────────────────────────────────│
│                                                                 │
│  ┌─── PRICE CHART (90 days) ───────────────────────────────────┐│
│  │  Candlestick or line chart with overlays:                    ││
│  │  — 9 EMA (thin cyan)                                        ││
│  │  — 21 EMA (thin yellow)                                     ││
│  │  — 50 SMA (thick blue)                                      ││
│  │  — 200 SMA (thick white)                                    ││
│  │  — PEG low (dashed green horizontal line, if active)        ││
│  │  — Stop loss (dashed red horizontal line)                   ││
│  │  — Volume bars underneath (green/red)                       ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌──── SCORES ────────┐  ┌──── KEY METRICS ───────────────────┐│
│  │                     │  │                                     ││
│  │ Technical:  35/40   │  │ Stage: 2 (confirmed)               ││
│  │ ██████████████████░ │  │ Base: #3 (late-stage caution)      ││
│  │                     │  │ ADR: 3.9% ✅ (sweet spot)           ││
│  │ Setup:     15/30    │  │ ATR Ext: 3.2x ⚠ (extended!)       ││
│  │ ████████████░░░░░░░ │  │ RVol: 1.4x                        ││
│  │                     │  │ Dist from 50 SMA: +14.2%           ││
│  │ Fundamental: 24/30  │  │ Dist from 200 SMA: +38.7%         ││
│  │ ████████████████░░░ │  │                                     ││
│  │                     │  │ Entry Zone: $125 - $128 (21 EMA)   ││
│  │ TOTAL:     74/100   │  │ Stop Loss: $118.50 (50 SMA)       ││
│  │ ██████████████████░ │  │ Risk/Reward: 1:3.2                 ││
│  └─────────────────────┘  └─────────────────────────────────────┘│
│                                                                 │
│  ┌──── CLAUDE ANALYSIS (AI) ───────────────────────────────────┐│
│  │  🤖 Analyzed: 2 hours ago         [🔄 Refresh Analysis]     ││
│  │                                                              ││
│  │  "NVDA remains a Stage 2 leader but is showing late-stage    ││
│  │   characteristics. Currently in a 3rd base pattern, which    ││
│  │   O'Neil flags as more vulnerable. ATR extension of 3.2x    ││
│  │   from the 50 SMA suggests trimming 1/3 of trading shares   ││
│  │   into strength. Core position should be held as long as     ││
│  │   price respects the 10-week MA."                            ││
│  │                                                              ││
│  │  Warnings:                                                   ││
│  │  ⚠ ATR extension above 3x — consider partial trim           ││
│  │  ⚠ Base 3 — late-stage, watch for climax top                ││
│  └─────────────────────────────────────────────────────────────┘│
│                                                                 │
│  ┌──── YOUR POSITION ─────────────────────────────────────────┐ │
│  │  Shares: 45  │  Avg Cost: $108.20  │  P&L: +$1,183 (▲24%) │ │
│  │  Tranche 1: ✅ Filled at $106     │  Tranche 2: ✅ at $110 │ │
│  │  Stop: $118.50  │  Days Held: 47  │  Sector: 9.2% of port │ │
│  └─────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

---

## Updated Day-by-Day Schedule (Week 1 — Revised)

The original plan ran backend-only for 7 days. Here's the revised schedule that includes the React dashboard:

```
DAY 1 (8h): Backend scaffold + Data pipeline + Robinhood reader
            (same as original Day 1)

DAY 2 (8h): Technical screener — PEG, bases, Weinstein, ADR/ATR
            (same as original Day 2)

DAY 3 (8h): Claude analysis engine + conviction scoring
            (same as original Day 3)

DAY 4 (8h): Risk management + FastAPI backend
            MORNING: Position sizer, stop manager, exposure limits
            AFTERNOON: Wrap ALL modules as FastAPI endpoints
              → Every module gets an API route
              → Test with curl/Postman
              → CORS enabled for React dev server

DAY 5 (8h): React frontend — Dashboard + Portfolio pages
            MORNING: Scaffold React+Vite+Tailwind project
              → Sidebar nav, layout shell, routing
              → Dashboard page (metrics, equity curve, sector donut)
              → API client (fetch wrapper)
            AFTERNOON: Portfolio page
              → Holdings table with expandable rows
              → P&L waterfall chart
              → Sell signals panel

DAY 6 (8h): React frontend — Screener + PEG + Movers pages
            MORNING: Screener page (ranked table, score bars, filters)
              → Movers page (gainers/losers, unusual volume)
            AFTERNOON: PEG setups page (card grid, mini charts)
              → Sector heatmap page
              → Analysis detail page (per-ticker deep dive)

DAY 7 (8h): Integration + GitHub + Deployment prep
            MORNING: Wire frontend↔backend end-to-end
              → Daily briefing email (keep from original plan)
              → Alert system integration
              → Full pipeline test
            AFTERNOON: GitHub + Docker + Cloud prep
              → Initialize Git repo, push to GitHub
              → Write Dockerfiles for frontend + backend
              → docker-compose for local dev
              → Write deployment docs
              → Deploy to Railway/Render (or prep for AWS)
```

---

## Frontend Tech Stack

```json
// frontend/package.json (key dependencies)
{
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0",
    "react-router-dom": "^6.22.0",
    "recharts": "^2.12.0",
    "lucide-react": "^0.383.0",
    "@tanstack/react-query": "^5.24.0",
    "axios": "^1.6.0",
    "clsx": "^2.1.0",
    "date-fns": "^3.3.0"
  },
  "devDependencies": {
    "vite": "^5.1.0",
    "tailwindcss": "^3.4.0",
    "autoprefixer": "^10.4.0",
    "postcss": "^8.4.0"
  }
}
```

**Why each library:**
- `recharts` — React charting (area charts, bar charts, pie/donut, treemap)
- `lucide-react` — Icon set (available in artifacts environment)
- `@tanstack/react-query` — Data fetching + caching + auto-refetch
- `axios` — HTTP client for backend API
- `date-fns` — Lightweight date formatting
- `clsx` — Conditional CSS class merging

---

## Claude Code Prompts for Frontend Days

### Day 5 Morning — Scaffold + Dashboard

```
Create a React + Vite + Tailwind project in /frontend with:

1. Dark theme trading dashboard layout:
   - Fixed sidebar (220px) with nav links and icons
   - Header bar showing portfolio value + daily change
   - Main content area with React Router

2. Dashboard page (/):
   - 4 metric cards: Total Value, Daily P&L, Open Positions, Avg Conviction
   - Equity curve chart (recharts AreaChart, gradient fill, period toggle)
   - Sector allocation donut chart (recharts PieChart)
   - Top 5 movers/losers mini table
   - Active alerts list

3. API client (src/api/client.js):
   - Base URL from env var (VITE_API_URL)
   - GET/POST wrapper with error handling
   - React Query hooks for each endpoint

Use this color scheme:
  bg-primary: #0a0e17, bg-card: #111827, border: #1e293b
  text: #e2e8f0, muted: #94a3b8
  green: #10b981, red: #ef4444, amber: #f59e0b, cyan: #06b6d4

Font: JetBrains Mono for numbers, DM Sans for text (Google Fonts).
All number formatting: USD currency, 2 decimal, +/- prefix with color.
```

### Day 5 Afternoon — Portfolio Page

```
Build the Portfolio page (/portfolio) with:

1. P&L waterfall chart at top:
   - Horizontal bar chart, each bar = one holding
   - Green for profit, red for loss
   - Sorted by P&L descending

2. Holdings table:
   - Columns: Ticker, Shares, Avg Cost, Price, Mkt Value, P&L ($), P&L (%), Sector
   - Sortable by any column
   - Row highlights: red border if near stop loss (within 3%)
   - Expandable rows showing:
     - Entry date, stop loss level, stage, base number
     - 90-day sparkline (recharts mini LineChart)
     - Claude analysis summary text
     - [Refresh Analysis] button

3. Sell signals panel at bottom:
   - Cards for each active sell signal
   - Color-coded by severity (red=urgent, amber=warning)

Data comes from:
  GET /api/portfolio/holdings
  GET /api/portfolio/summary
  GET /api/analysis/{ticker} (for expanded rows)
```

### Day 6 Morning — Screener + Movers

```
Build the Screener page (/screener) with:

1. Filter bar: sector dropdown, min score slider, stage filter
2. Score distribution histogram (recharts BarChart)
3. Ranked table:
   - All tickers sorted by conviction score
   - Stacked horizontal bar in each row showing Tech/Setup/Fund breakdown
   - PEG indicator (green dot if active)
   - Action badge (BUY=green, HOLD=gray, SELL=red, WATCH=cyan)
   - Click row → navigate to /analysis/{ticker}

Build the Movers page (/movers) with:
1. Two-column layout: Gainers (left), Losers (right)
2. Each card shows: ticker, change%, RVol, sector, stage
3. Horizontal bar width proportional to |change%|
4. Unusual volume table below (RVol > 2x)
5. Sector performance heatmap grid (colored boxes)

Data from:
  GET /api/screener/ranked
  GET /api/movers/top
  GET /api/movers/unusual-volume
```

### Day 6 Afternoon — PEG + Analysis + Sector

```
Build the PEG Setups page (/peg) with:
1. Card grid (3 columns) for each active PEG
2. Each card shows: ticker, PEG date, gap%, volume multiple,
   PEG low, current price, 9 EMA level, entry zone status
3. Mini chart in each card (30-day price with PEG low line)
4. History table below showing past PEGs and outcomes

Build the Analysis page (/analysis/:ticker) with:
1. Price chart (recharts LineChart, 90 days) with MA overlays:
   - 9 EMA (cyan), 21 EMA (yellow), 50 SMA (blue), 200 SMA (white)
   - PEG low (green dashed), stop loss (red dashed)
   - Volume bars underneath
2. Score breakdown panel (3 progress bars)
3. Key metrics grid (stage, base#, ADR, ATR ext, RVol)
4. Claude analysis card (reasoning text + warnings)
5. Position panel (if held: shares, cost, P&L, tranches)

Build the Sector page (/sectors) with:
1. Treemap heatmap (recharts Treemap, color=daily change)
2. Sector strength ranking table
3. Sector exposure vs limits bar chart

Data from:
  GET /api/peg/active, /api/peg/history
  GET /api/analysis/{ticker}
  GET /api/portfolio/sector-allocation
```

---

## Docker Setup for Local Development

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile (dev)
FROM node:20-alpine

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]
```

### Frontend Production Dockerfile

```dockerfile
# frontend/Dockerfile.prod
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

### docker-compose.yml (Local Development)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - ./backend:/app          # Hot reload
      - ./data:/app/data        # Persist SQLite
    restart: unless-stopped

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    environment:
      - VITE_API_URL=http://localhost:8000
    volumes:
      - ./frontend/src:/app/src # Hot reload
    depends_on:
      - backend
    restart: unless-stopped
```

### docker-compose.prod.yml (Production Override)

```yaml
version: '3.8'

services:
  backend:
    build: ./backend
    command: uvicorn main:app --host 0.0.0.0 --port 8000 --workers 2
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/trading
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile.prod
    ports:
      - "80:80"

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: pass
      POSTGRES_DB: trading
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

---

## GitHub Setup

### Step 1: Initialize Repo

```bash
cd trading-agent-platform

git init
git branch -M main

# Create .gitignore
cat > .gitignore << 'EOF'
# Environment
.env
*.env.local

# Python
__pycache__/
*.pyc
*.pyo
venv/
.venv/

# Node
node_modules/
frontend/dist/

# Database
*.sqlite
*.db
data/*.sqlite

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
EOF

# Create .env.example (safe to commit)
cat > .env.example << 'EOF'
# Robinhood (robin_stocks)
RH_USERNAME=your_email
RH_PASSWORD=your_password
RH_TOTP=your_2fa_secret

# Anthropic Claude API
ANTHROPIC_API_KEY=sk-ant-...

# News APIs
FINNHUB_API_KEY=your_key

# Email Alerts
GMAIL_USER=your_email@gmail.com
GMAIL_APP_PASSWORD=your_app_password

# Database (production only)
DATABASE_URL=sqlite:///./data/trading.db

# Frontend
VITE_API_URL=http://localhost:8000
EOF

git add .
git commit -m "Initial project structure"
```

### Step 2: Push to GitHub

```bash
# Create repo on GitHub first (via github.com or gh CLI)
gh repo create trading-agent-platform --private

git remote add origin git@github.com:YOUR_USERNAME/trading-agent-platform.git
git push -u origin main
```

### Step 3: Branch Strategy

```
main        ← production-ready code only
├── develop ← integration branch for daily work
├── feature/data-pipeline
├── feature/screener
├── feature/claude-analysis
├── feature/react-dashboard
└── feature/deployment
```

---

## Cloud Deployment Options (Post Week 1)

### Option A: Railway (Easiest — recommended to start)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Railway auto-detects Docker, deploys both services
# Set env vars in Railway dashboard
# Free tier: $5/month credit, enough for personal use
```

**Pros:** Git-push deploys, auto-SSL, built-in Postgres, $5 free credit
**Cost:** ~$10-20/month for backend + frontend + DB

### Option B: Render (Also Easy)

```yaml
# render.yaml (Infrastructure as Code)
services:
  - type: web
    name: trading-backend
    runtime: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn main:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: DATABASE_URL
        fromDatabase:
          name: trading-db
          property: connectionString

  - type: web
    name: trading-frontend
    runtime: static
    buildCommand: cd frontend && npm install && npm run build
    staticPublishPath: frontend/dist
    routes:
      - type: rewrite
        source: /*
        destination: /index.html

databases:
  - name: trading-db
    plan: free
```

**Pros:** Free tier available, easy setup, auto-deploy from GitHub
**Cost:** Free for basic, $7-19/month for always-on

### Option C: AWS (Most Control — later)

```
Architecture on AWS:
├── EC2 t3.small ($15/mo) — backend + scheduler
├── S3 + CloudFront ($2/mo) — frontend static hosting
├── RDS PostgreSQL free tier — database
├── EventBridge — cron scheduling
└── SES — email delivery (free tier: 62K emails/mo)

Total: ~$17-25/month
```

### Deployment Checklist

```
□ All secrets in environment variables (never in code)
□ CORS configured for production domain
□ Database migrated from SQLite → PostgreSQL
□ Frontend build optimized (npm run build)
□ Health check endpoint working (/api/health)
□ Scheduler running (morning + intraday + evening jobs)
□ SSL/HTTPS enabled
□ Error logging configured (Sentry free tier)
□ Daily backup of database
□ Robinhood login session management (token refresh)
```

---

## Local Development Workflow (Daily)

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn main:app --reload --port 8000

# Terminal 2: Frontend
cd frontend
npm run dev
# → Opens at http://localhost:5173

# Terminal 3: Claude Code (for building)
claude
# → Vibe code new features, paste prompts from this doc

# Terminal 4: Git
git checkout -b feature/your-feature
# ... code ...
git add . && git commit -m "Add screener page"
git push origin feature/your-feature
```

---

## Component Library Reference

Quick reference for building React components with the tools available:

### Charts (recharts)
```jsx
// Equity Curve
<AreaChart data={data}>
  <XAxis dataKey="date" />
  <YAxis />
  <Area type="monotone" dataKey="value" stroke="#3b82f6"
        fill="url(#gradient)" />
</AreaChart>

// Sector Donut
<PieChart>
  <Pie data={sectors} dataKey="value" nameKey="sector"
       innerRadius={60} outerRadius={100} />
</PieChart>

// P&L Waterfall
<BarChart data={holdings} layout="vertical">
  <Bar dataKey="pnl">
    {holdings.map(h =>
      <Cell fill={h.pnl > 0 ? '#10b981' : '#ef4444'} />
    )}
  </Bar>
</BarChart>

// Treemap Heatmap
<Treemap data={sectorData} dataKey="size"
         content={<CustomTreemapCell />} />
```

### Icons (lucide-react)
```jsx
import {
  TrendingUp, TrendingDown, BarChart3, PieChart,
  AlertTriangle, Bell, Search, Settings, Zap,
  ArrowUpRight, ArrowDownRight, Activity, Target
} from 'lucide-react'
```

### Data Fetching (React Query)
```jsx
// hooks/usePortfolio.js
import { useQuery } from '@tanstack/react-query'
import api from '../api/client'

export function usePortfolioSummary() {
  return useQuery({
    queryKey: ['portfolio', 'summary'],
    queryFn: () => api.get('/api/portfolio/summary'),
    refetchInterval: 60000, // refresh every 60s during market hours
  })
}

export function useHoldings() {
  return useQuery({
    queryKey: ['portfolio', 'holdings'],
    queryFn: () => api.get('/api/portfolio/holdings'),
    refetchInterval: 60000,
  })
}
```

---

## Full Week Summary

```
┌──────┬────────────────────────────────────────────────────┐
│ Day  │ Deliverable                                        │
├──────┼────────────────────────────────────────────────────┤
│  1   │ Data pipeline + RH reader + news + SQLite DB       │
│  2   │ PEG scanner + base detector + Weinstein stages     │
│  3   │ Claude analysis engine + conviction scoring        │
│  4   │ Risk mgmt + FastAPI backend (all endpoints live)   │
│  5   │ React: Dashboard + Portfolio pages                 │
│  6   │ React: Screener + PEG + Movers + Sector pages      │
│  7   │ Integration + GitHub + Docker + deploy prep        │
├──────┼────────────────────────────────────────────────────┤
│ Post │ Cloud deploy, backtest, options flow, auto-execute  │
└──────┴────────────────────────────────────────────────────┘
```

**After Week 1 you'll have:**
- ✅ Python backend with your full trading methodology encoded
- ✅ React dashboard with 7 pages of charts, tables, and analysis
- ✅ Robinhood portfolio synced and displayed
- ✅ Claude-powered stock analysis for every ticker
- ✅ Daily email briefing before market open
- ✅ Conviction-ranked screener with PEG detection
- ✅ Risk management with your exact sell rules
- ✅ GitHub repo, Docker setup, ready for cloud deployment

---
---

# PART 3: Requirements Gap Analysis & Enhanced Specification

---

## Gap Analysis: Our Blueprint vs. Professional Trading Agent Requirements

Below is a side-by-side comparison. Items marked ❌ are entirely missing from our blueprint. Items marked ⚠️ are partially covered but need enhancement. Items marked ✅ are already well-covered.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                    REQUIREMENTS GAP ANALYSIS                              │
├───────────────────────────────────┬──────┬────────────────────────────────┤
│ Requirement                       │Status│ Notes                          │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ FUNCTIONAL: DATA INGESTION        │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ Real-time WebSocket streaming     │ ❌   │ We only have REST polling       │
│ L1/L2 order book data             │ ❌   │ Not in our data pipeline        │
│ Historical data (multi-timeframe) │ ⚠️   │ We have daily only, need 1m-1h │
│ Dynamic indicator engine          │ ⚠️   │ We batch-calculate, not live    │
│ Sentiment analysis                │ ⚠️   │ Basic news, no composite score  │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ FUNCTIONAL: STRATEGY & EXECUTION  │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ Multi-strategy support            │ ❌   │ We have one strategy path       │
│ Order type management             │ ❌   │ No order types specified        │
│ Backtesting engine                │ ⚠️   │ Mentioned but not designed      │
│ Paper trading mode                │ ⚠️   │ Mentioned Alpaca, not built     │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ FUNCTIONAL: RISK MANAGEMENT       │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ Daily loss limits                  │ ⚠️   │ Circuit breaker exists, basic   │
│ Position sizing (% equity)        │ ✅   │ 2-tranche system built          │
│ Kill switch (flatten all)         │ ❌   │ Not in our blueprint            │
│ Sector exposure limits            │ ✅   │ 40% single, 60% correlated     │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ SYSTEM: EXCHANGE CONNECTORS       │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ Unified broker interface          │ ⚠️   │ RH only, no abstraction layer  │
│ Async order state tracking        │ ❌   │ No order lifecycle management   │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ SYSTEM: SECURITY                  │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ AES-256 credential encryption     │ ❌   │ We use .env plaintext           │
│ MFA for critical actions          │ ❌   │ No auth on dashboard            │
│ Audit logging (immutable)         │ ❌   │ No trade action logging         │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ SYSTEM: PERFORMANCE               │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ 99.9% uptime / auto-reconnect    │ ❌   │ No resilience logic             │
│ State persistence across reboots  │ ❌   │ No crash recovery               │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ UI: DASHBOARD                     │      │                                │
├───────────────────────────────────┼──────┼────────────────────────────────┤
│ Drag-and-drop widget layout       │ ❌   │ Fixed layout only               │
│ Dark/Light theme toggle           │ ⚠️   │ Dark only, no toggle            │
│ Interactive candlestick charts    │ ⚠️   │ Line charts only                │
│ Buy/sell execution markers        │ ❌   │ Not on charts                   │
│ Strategy control center           │ ❌   │ No start/stop/pause UI          │
│ Manual execution panel            │ ❌   │ No manual trade override        │
│ Risk configuration grid           │ ❌   │ No password-protected settings  │
│ Toast alerts (non-blocking)       │ ❌   │ No toast notification system    │
│ Critical modal interrupts         │ ❌   │ No modal system for emergencies │
│ Real-time PnL color-coded grids   │ ⚠️   │ Have table, not real-time       │
└───────────────────────────────────┴──────┴────────────────────────────────┘

SCORE: 4 ✅ | 8 ⚠️ | 15 ❌ = 27 requirements, 15 gaps to fill
```

---

## Enhanced Requirements Specification (Merged & Complete)

Everything below is ADDITIVE — it supplements the existing blueprint without replacing any of the current design. New modules are integrated into the existing file structure.

---

### 1. FUNCTIONAL REQUIREMENTS

---

#### 1.1 Data Ingestion & Market Analytics (ENHANCED)

**What we had:** REST-based daily OHLCV pulls via yfinance, basic news fetching.

**What we're adding:**

##### 1.1.1 Real-Time WebSocket Data Streaming — NEW

```
Module: backend/data/websocket_stream.py
```

Connect to real-time price feeds with sub-second updates during market hours.

**Implementation:**
```python
# Use Alpaca's free WebSocket stream (works without a funded account)
# OR Polygon.io WebSocket (free tier: 5 connections)
# OR Finnhub WebSocket (free tier: real-time US stocks)

import websockets
import asyncio
import json

class MarketDataStream:
    """Real-time WebSocket market data with auto-reconnect."""

    def __init__(self, provider="alpaca"):
        self.provider = provider
        self.subscribers = {}  # ticker -> [callback functions]
        self.reconnect_attempts = 0
        self.max_reconnect = 10
        self.reconnect_delay = 1  # exponential backoff

    async def connect(self):
        """Connect with auto-reconnect on failure."""
        while self.reconnect_attempts < self.max_reconnect:
            try:
                async with websockets.connect(self.ws_url) as ws:
                    await self._authenticate(ws)
                    await self._subscribe(ws, list(self.subscribers.keys()))
                    self.reconnect_attempts = 0
                    async for message in ws:
                        await self._handle_message(json.loads(message))
            except websockets.ConnectionClosed:
                self.reconnect_attempts += 1
                wait = self.reconnect_delay * (2 ** self.reconnect_attempts)
                await asyncio.sleep(min(wait, 60))

    async def _handle_message(self, data):
        """Route tick data to indicator engine and subscribers."""
        ticker = data.get("symbol")
        if ticker in self.subscribers:
            for callback in self.subscribers[ticker]:
                await callback(data)
```

**Latency target:** < 100ms from exchange tick to indicator update.
**Fallback:** If WebSocket disconnects, fall back to 15-second REST polling.

##### 1.1.2 L1/L2 Order Book Data — NEW

```
Module: backend/data/orderbook.py
```

```python
class OrderBookTracker:
    """Track bid/ask depth for your universe."""

    def track_spread(self, ticker):
        """Monitor bid-ask spread as liquidity indicator."""
        # L1: Best bid/ask (available from most free feeds)
        # L2: Full depth of book (requires Alpaca Pro or IBKR)
        pass

    def detect_large_blocks(self, ticker, threshold=10000):
        """Flag large institutional orders on the book."""
        pass
```

**Tier approach:**
- Week 1: L1 only (bid/ask from Alpaca free WebSocket)
- Post-Week 1: L2 depth if you upgrade to Alpaca Pro or IBKR

##### 1.1.3 Multi-Timeframe Historical Data — ENHANCED

```python
SUPPORTED_TIMEFRAMES = {
    "1m":  "1-minute bars",    # intraday (needs Alpaca/Polygon)
    "5m":  "5-minute bars",
    "15m": "15-minute bars",
    "1h":  "1-hour bars",
    "1d":  "Daily bars",       # primary (current)
    "1wk": "Weekly bars",      # Weinstein 30-week analysis
}
```

**Storage:** Add `timeframe` column to `daily_prices` table, rename to `price_bars`.

##### 1.1.4 Dynamic Indicator Engine (Streaming) — ENHANCED

```
Module: backend/screener/realtime_indicators.py (NEW)
```

```python
class StreamingIndicatorEngine:
    """Compute indicators incrementally as ticks arrive."""

    def on_tick(self, ticker, price, volume, timestamp):
        s = self.state.setdefault(ticker, IndicatorState())

        # Incremental EMA
        s.ema9 = price * s.k9 + s.ema9 * (1 - s.k9)
        s.ema21 = price * s.k21 + s.ema21 * (1 - s.k21)

        # Running VWAP
        s.cum_vol += volume
        s.cum_vol_price += volume * price
        s.vwap = s.cum_vol_price / s.cum_vol if s.cum_vol > 0 else price

        # Incremental RSI (Wilder smoothing)
        change = price - s.last_price
        if change > 0:
            s.avg_gain = (s.avg_gain * 13 + change) / 14
            s.avg_loss = (s.avg_loss * 13) / 14
        else:
            s.avg_gain = (s.avg_gain * 13) / 14
            s.avg_loss = (s.avg_loss * 13 + abs(change)) / 14
        rs = s.avg_gain / s.avg_loss if s.avg_loss > 0 else 100
        s.rsi = 100 - (100 / (1 + rs))
        s.last_price = price
```

**When it runs:** Market hours only (9:30 AM - 4:00 PM ET). After hours, batch calculations remain.

##### 1.1.5 Composite Sentiment Scoring — ENHANCED

```
Module: backend/analysis/sentiment_engine.py (NEW)
```

```python
class SentimentEngine:
    WEIGHTS = {
        "news_headlines": 0.30,
        "earnings_surprise": 0.25,
        "analyst_ratings": 0.20,
        "social_sentiment": 0.15,
        "insider_activity": 0.10,
    }

    def compute_composite(self, ticker) -> float:
        """Returns -1.0 (extremely bearish) to +1.0 (extremely bullish)"""
        scores = {
            "news_headlines": self._score_news(ticker),
            "earnings_surprise": self._score_earnings(ticker),
            "analyst_ratings": self._score_analysts(ticker),
            "social_sentiment": self._score_social(ticker),
            "insider_activity": self._score_insiders(ticker),
        }
        return round(sum(scores[k] * self.WEIGHTS[k] for k in self.WEIGHTS), 3)
```

---

#### 1.2 Strategy Execution & Automation (NEW SECTION)

##### 1.2.1 Multi-Strategy Support — NEW

```
Module: backend/strategies/
├── base_strategy.py        # Abstract base class
├── peg_momentum.py         # Your PEG + momentum strategy
├── mean_reversion.py       # Buy oversold Stage 2 leaders
├── earnings_play.py        # Pre/post earnings positioning
└── strategy_manager.py     # Run multiple strategies simultaneously
```

```python
class BaseStrategy(ABC):
    def __init__(self, name, allocation_pct=100):
        self.name = name
        self.allocation_pct = allocation_pct
        self.is_active = False
        self.positions = {}

    @abstractmethod
    def generate_signals(self, data) -> list: pass

    @abstractmethod
    def get_parameters(self) -> dict: pass

    def start(self): self.is_active = True
    def pause(self): self.is_active = False
    def stop(self):
        self.is_active = False
        self.positions = {}


class PEGMomentumStrategy(BaseStrategy):
    """Your methodology as a strategy."""
    def __init__(self):
        super().__init__("PEG Momentum", allocation_pct=70)
        self.params = {
            "peg_gap_min_pct": 3.0,
            "peg_volume_multiple": 2.0,
            "entry_ema": 9,
            "add_ema": 21,
            "atr_trim_threshold": 3.0,
            "adr_min": 3.0,
            "adr_max": 10.0,
            "max_position_pct": 10.0,
            "tranche_1_pct": 5.0,
            "tranche_2_pct": 5.0,
        }


class StrategyManager:
    def __init__(self):
        self.strategies = {}
        self.total_allocation = 0

    def register(self, strategy: BaseStrategy):
        if self.total_allocation + strategy.allocation_pct > 100:
            raise ValueError("Total allocation exceeds 100%")
        self.strategies[strategy.name] = strategy
        self.total_allocation += strategy.allocation_pct

    def run_all(self, market_data):
        all_signals = []
        for name, strat in self.strategies.items():
            if strat.is_active:
                all_signals.extend(strat.generate_signals(market_data))
        return self._resolve_conflicts(all_signals)
```

##### 1.2.2 Order Type Management — NEW

```
Module: backend/execution/order_manager.py
```

```python
class OrderType(Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TRAILING_STOP = "trailing_stop"
    BRACKET = "bracket"

class OrderStatus(Enum):
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIALLY_FILLED = "partial"
    FILLED = "filled"
    CANCELED = "canceled"
    REJECTED = "rejected"

class Order:
    def __init__(self, ticker, side, order_type, quantity,
                 price=None, stop_price=None, trail_pct=None):
        self.id = generate_uuid()
        self.ticker = ticker
        self.side = side
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.stop_price = stop_price
        self.trail_pct = trail_pct
        self.status = OrderStatus.PENDING
        self.created_at = datetime.utcnow()
        self.filled_at = None
        self.filled_price = None

class OrderManager:
    async def submit_order(self, order: Order) -> Order:
        order.status = OrderStatus.SUBMITTED
        result = await self.broker.place_order(order)
        self.open_orders[order.id] = order
        await self._log_action("ORDER_SUBMITTED", order)
        return order

    async def cancel_all(self):
        """KILL SWITCH: Cancel all open orders."""
        for oid in list(self.open_orders):
            await self.cancel_order(oid)
        await self._log_action("KILL_SWITCH_ACTIVATED", None)
```

##### 1.2.3 Backtesting Engine — ENHANCED

```
Module: backend/backtest/engine.py
```

```python
class BacktestResult:
    total_return: float
    annualized_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    total_trades: int
    avg_holding_days: float
    vs_benchmark: float       # alpha vs SPY
    monthly_returns: list
    equity_curve: list
    trade_log: list
```

##### 1.2.4 Paper Trading Mode — ENHANCED

```python
class PaperBroker:
    """Same interface as real broker. Swap with zero code changes."""
    def __init__(self, initial_balance=100000):
        self.balance = initial_balance
        self.positions = {}
        self.is_paper = True  # UI shows "PAPER" badge

    async def place_order(self, order):
        current_price = await self._get_live_price(order.ticker)
        fill_price = current_price * (1.0005 if order.side == "buy" else 0.9995)
        # Simulate slippage + partial fills
        pass

# Switch in config:
TRADING_MODE = "paper"  # "paper" | "live"
broker = PaperBroker() if TRADING_MODE == "paper" else RobinhoodBroker()
```

---

#### 1.3 Risk Management (ENHANCED)

##### 1.3.1 Account-Level Capital Guards — ENHANCED

```python
class CapitalGuards:
    def __init__(self, config):
        self.max_daily_loss_pct = config.get("max_daily_loss_pct", 3.0)
        self.max_daily_loss_usd = config.get("max_daily_loss_usd", 5000)
        self.max_weekly_loss_pct = config.get("max_weekly_loss_pct", 7.0)
        self.max_drawdown_pct = config.get("max_drawdown_pct", 15.0)
        self.max_open_positions = config.get("max_open_positions", 20)
        self.is_locked = False

    def check_order(self, order, portfolio) -> tuple[bool, str]:
        """Gate every order through risk checks."""
        if self.is_locked:
            return False, "Trading halted: circuit breaker active"
        if portfolio.daily_pnl_pct <= -self.max_daily_loss_pct:
            self.is_locked = True
            return False, f"Daily loss limit: {portfolio.daily_pnl_pct:.1f}%"
        if portfolio.drawdown_pct >= self.max_drawdown_pct:
            self.is_locked = True
            return False, f"Max drawdown: {portfolio.drawdown_pct:.1f}%"
        # + position size, sector exposure checks
        return True, "Passed"

    def unlock(self, password: str) -> bool:
        if verify_password(password):
            self.is_locked = False
            return True
        return False
```

##### 1.3.2 Kill Switch — NEW

```python
class KillSwitch:
    """Emergency: Cancel ALL orders + flatten ALL positions."""

    async def activate(self, reason: str):
        # 1. Cancel all pending/open orders
        await order_manager.cancel_all()
        # 2. Market sell all positions
        for pos in portfolio.get_all_positions():
            close = Order(pos.ticker, "sell", OrderType.MARKET, pos.quantity)
            await order_manager.submit_order(close)
        # 3. Lock trading
        capital_guards.is_locked = True
        # 4. Alert + audit log
        await notifier.send_emergency(f"🚨 KILL SWITCH: {reason}")
        await audit_log.record("KILL_SWITCH", reason, immutable=True)
```

---

### 2. SYSTEM & INTEGRATION REQUIREMENTS

---

#### 2.1 Unified Broker Interface — NEW

```python
class BrokerInterface(ABC):
    """Swap brokers with zero code changes."""
    @abstractmethod
    async def get_account(self) -> dict: pass
    @abstractmethod
    async def get_positions(self) -> list: pass
    @abstractmethod
    async def place_order(self, order) -> dict: pass
    @abstractmethod
    async def cancel_order(self, order_id) -> dict: pass
    @abstractmethod
    async def get_order_status(self, order_id) -> OrderStatus: pass
    @abstractmethod
    async def get_buying_power(self) -> float: pass

class RobinhoodBroker(BrokerInterface): pass
class AlpacaBroker(BrokerInterface): pass
class PaperBroker(BrokerInterface): pass
```

#### 2.2 Async Order State Tracking — NEW

```python
class OrderTracker:
    VALID_TRANSITIONS = {
        "pending":  ["submitted", "rejected"],
        "submitted": ["filled", "partial", "canceled", "rejected"],
        "partial":  ["filled", "canceled"],
        "filled":   [],
        "canceled": [],
        "rejected": [],
    }

    async def update_state(self, order_id, new_state):
        order = self.orders[order_id]
        current = order.status.value
        if new_state not in self.VALID_TRANSITIONS.get(current, []):
            raise InvalidTransition(f"{current} → {new_state}")
        order.status = OrderStatus(new_state)
        await audit_log.record("ORDER_STATE_CHANGE", {
            "order_id": order_id, "from": current, "to": new_state
        })
```

#### 2.3 Security & Data Protection — NEW

##### Credential Encryption (AES-256)
```python
from cryptography.fernet import Fernet

class CredentialVault:
    def __init__(self):
        self.key = self._load_or_generate_key()
        self.cipher = Fernet(self.key)

    def encrypt(self, plaintext: str) -> str:
        return self.cipher.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self.cipher.decrypt(ciphertext.encode()).decode()
```

##### Authentication & MFA
```python
class DashboardAuth:
    async def login(self, password, mfa_code) -> str:
        if not verify_password(password): raise HTTPException(401)
        if not pyotp.TOTP(self.mfa_secret).verify(mfa_code): raise HTTPException(401)
        return generate_session_token()

    # MFA required for:
    # - Kill switch, risk config changes, manual trades, API key edits
```

##### Immutable Audit Logging
```python
class AuditLog:
    async def record(self, action_type, details, immutable=True):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action_type,
            "details": details,
            "prev_hash": self.prev_hash,
        }
        entry["hash"] = hashlib.sha256(
            json.dumps(entry, sort_keys=True).encode()
        ).hexdigest()
        await self.db.insert("audit_log", entry)
        self.prev_hash = entry["hash"]

    async def verify_integrity(self) -> bool:
        """Verify no entries have been tampered with."""
        entries = await self.db.get_all("audit_log")
        for i in range(1, len(entries)):
            if entries[i]["prev_hash"] != entries[i-1]["hash"]:
                return False
        return True
```

#### 2.4 Performance & Reliability — NEW

##### Auto-Reconnect & Uptime
```python
class ResilienceManager:
    def __init__(self):
        self.health_status = {
            "websocket": "connected",
            "broker": "connected",
            "database": "connected",
            "scheduler": "running",
        }

    async def monitor_connections(self):
        """Check all connections every 10 seconds."""
        while True:
            await self._check_websocket()
            await self._check_broker()
            await self._check_database()
            await asyncio.sleep(10)
```

##### State Persistence Across Reboots
```python
class StateManager:
    PERSISTED_STATE = [
        "open_orders", "active_strategies", "alert_levels",
        "risk_guard_status", "last_pipeline_run",
        "websocket_subscriptions", "indicator_state",
    ]

    async def save_state(self):
        """Save to SQLite every 30 seconds + on shutdown."""
        state = {key: await self._serialize(key) for key in self.PERSISTED_STATE}
        await self.db.upsert("agent_state", {"state": json.dumps(state)})

    async def restore_state(self):
        """On startup, restore last known state."""
        row = await self.db.get("agent_state")
        if row:
            state = json.loads(row["state"])
            for key in self.PERSISTED_STATE:
                if key in state:
                    await self._restore(key, state[key])
```

**Startup sequence:**
1. Load encrypted credentials → 2. Restore state → 3. Connect broker → 4. Connect WebSocket → 5. Verify orders → 6. Resume strategies → 7. Health check → 8. Start scheduler → 9. Audit log entry

---

### 3. UI REQUIREMENTS (ENHANCED)

---

#### 3.1 Drag-and-Drop Widget Layout — NEW

```jsx
// react-grid-layout for draggable, resizable widgets
import GridLayout from "react-grid-layout";

const defaultLayout = [
  { i: "equity-curve",  x: 0, y: 0, w: 8, h: 4 },
  { i: "sector-donut",  x: 8, y: 0, w: 4, h: 4 },
  { i: "movers",        x: 0, y: 4, w: 4, h: 4 },
  { i: "alerts",        x: 4, y: 4, w: 4, h: 4 },
  { i: "screener-mini", x: 8, y: 4, w: 4, h: 4 },
];
// Layout persists to localStorage or backend
```

#### 3.2 Dark / Light Theme Toggle — ENHANCED

```jsx
const themes = {
  dark:  { bgPrimary: "#0a0e17", bgCard: "#111827", text: "#e2e8f0" },
  light: { bgPrimary: "#f8fafc", bgCard: "#ffffff", text: "#1e293b" },
};
// Toggle via sun/moon icon in header. Persists to localStorage.
```

#### 3.3 Interactive Candlestick Charts — ENHANCED

```
Library: lightweight-charts (TradingView's open-source charting)
```

Features to implement:
1. Candlestick view with volume underneath
2. MA overlays: 9 EMA (cyan), 21 EMA (yellow), 50 SMA (blue), 200 SMA (white)
3. PEG low as horizontal green dashed line
4. Stop loss as horizontal red dashed line
5. Buy markers (green arrow up) at entry points
6. Sell markers (red arrow down) at exit points
7. Anchored VWAP overlay
8. RSI subplot below main chart
9. Timeframe selector: 1D, 1W, 1M, 3M, 6M, 1Y
10. Real-time tick updates via WebSocket

#### 3.4 Strategy Control Center — NEW PAGE

```
Route: /strategies

┌─── PEG MOMENTUM ──────────────────────────────────────┐
│  Status: [● RUNNING]     Allocation: 70%               │
│  [▶ Start] [⏸ Pause] [⏹ Stop]                         │
│                                                         │
│  Parameters (editable inline):                          │
│  PEG gap minimum    [ 3.0 ] %                          │
│  Volume multiple     [ 2.0 ] x                          │
│  Entry EMA           [ 9   ] days                       │
│  ATR trim threshold  [ 3.0 ] x                          │
│  ADR range           [ 3.0 ] to [ 10.0 ] %              │
│                                                         │
│  Performance: +32.1%  │  Win: 68%  │  Sharpe: 1.8      │
└─────────────────────────────────────────────────────────┘
```

#### 3.5 Manual Execution Panel — NEW PAGE

```
Route: /trade   (🔒 Requires MFA)

Ticker: [ NVDA ]  Current: $134.50

Order type: [● Market  ○ Limit  ○ Stop  ○ Bracket]
Quantity: [ 50 ]

Risk slider:
1% ━━━━●━━━━━━━ 10%
→ 5% = $17,362 → 129 shares

[ 🟢 SUBMIT BUY ]    [ 🔴 SUBMIT SELL ]

⚠ Overrides autonomous strategy decisions.
  All manual trades logged to audit trail.
```

#### 3.6 Risk Configuration Grid — NEW PAGE

```
Route: /settings/risk   (🔒 Requires MFA to unlock)

CAPITAL GUARDS (all fields locked by default):
  Max daily loss        [ 3.0 ] %     🔒
  Max weekly loss       [ 7.0 ] %     🔒
  Max drawdown          [ 15.0 ] %    🔒
  Max open positions    [ 20 ]        🔒
  Max single position   [ 10.0 ] %    🔒
  Max sector exposure   [ 40.0 ] %    🔒

CURRENT STATUS:
  Daily P&L:  -0.8% of 3.0%  ████░░░░░░
  Drawdown:   4.2% of 15.0%  ███░░░░░░░░░

[ 🔓 Unlock to Edit ]    [ 🚨 KILL SWITCH ]
```

#### 3.7 Notifications — NEW

**Toast alerts** (non-blocking, slide in top-right):
```
✅ "Order filled: 50 shares TER @ $155.20"
⚠️ "NVDA: ATR extension 3.1x — approaching trim"
🔴 "Broker connection lost — reconnecting"
```

**Critical modals** (blocking, full overlay):
```
Triggered by: kill switch, circuit breaker, broker disconnect,
API key expired, max drawdown breach.

┌──────────────────────────────────┐
│  🚨 CRITICAL: Trading Halted     │
│  Daily loss limit: -3.2%         │
│  All new orders blocked.         │
│  [ Acknowledge ] [ Unlock ]      │
└──────────────────────────────────┘
```

**Notification center** (bell icon in header):
Last 50 notifications, unread badge, category filters.

---

### 4. UPDATED FILE STRUCTURE (all new modules)

```
backend/ additions:
├── data/
│   ├── websocket_stream.py       ← NEW
│   └── orderbook.py              ← NEW
├── screener/
│   └── realtime_indicators.py    ← NEW
├── analysis/
│   └── sentiment_engine.py       ← NEW
├── strategies/                   ← NEW DIRECTORY
│   ├── base_strategy.py
│   ├── peg_momentum.py
│   ├── mean_reversion.py
│   └── strategy_manager.py
├── execution/                    ← NEW DIRECTORY
│   ├── broker_interface.py
│   ├── robinhood_broker.py
│   ├── alpaca_broker.py
│   ├── paper_broker.py
│   ├── order_manager.py
│   └── order_tracker.py
├── risk/
│   ├── capital_guards.py         ← NEW
│   └── kill_switch.py            ← NEW
├── security/                     ← NEW DIRECTORY
│   ├── encryption.py
│   ├── auth.py
│   └── audit_log.py
├── system/                       ← NEW DIRECTORY
│   ├── resilience.py
│   └── state_manager.py
├── backtest/                     ← NEW DIRECTORY
│   ├── engine.py
│   ├── data_loader.py
│   ├── metrics.py
│   └── report.py
└── api/
    ├── routes_orders.py          ← NEW
    ├── routes_strategies.py      ← NEW
    ├── routes_backtest.py        ← NEW
    ├── routes_audit.py           ← NEW
    └── routes_risk.py            ← NEW

frontend/src/ additions:
├── pages/
│   ├── StrategyCenter.jsx        ← NEW
│   ├── ManualTrade.jsx           ← NEW
│   ├── RiskConfig.jsx            ← NEW
│   ├── Backtest.jsx              ← NEW
│   ├── AuditLog.jsx              ← NEW
│   └── Login.jsx                 ← NEW
├── components/
│   ├── charts/
│   │   └── CandlestickChart.jsx  ← NEW (lightweight-charts)
│   ├── notifications/            ← NEW DIRECTORY
│   │   ├── ToastManager.jsx
│   │   ├── CriticalModal.jsx
│   │   └── NotificationCenter.jsx
│   └── layout/
│       ├── GridLayout.jsx        ← NEW (drag-and-drop)
│       └── KillSwitchButton.jsx  ← NEW
└── context/
    ├── ThemeContext.jsx           ← NEW
    └── AuthContext.jsx            ← NEW
```

---

### 5. NEW DATABASE TABLES

```sql
CREATE TABLE orders (
    id TEXT PRIMARY KEY,
    ticker TEXT NOT NULL,
    side TEXT NOT NULL,
    order_type TEXT NOT NULL,
    quantity REAL NOT NULL,
    price REAL,
    stop_price REAL,
    trail_pct REAL,
    status TEXT NOT NULL,
    strategy TEXT,
    filled_price REAL,
    filled_quantity REAL,
    created_at TIMESTAMP,
    filled_at TIMESTAMP,
    broker_order_id TEXT
);

CREATE TABLE order_state_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT REFERENCES orders(id),
    from_state TEXT,
    to_state TEXT NOT NULL,
    timestamp TIMESTAMP NOT NULL
);

CREATE TABLE strategies (
    name TEXT PRIMARY KEY,
    status TEXT NOT NULL,
    allocation_pct REAL,
    params TEXT,
    started_at TIMESTAMP,
    total_return REAL,
    win_rate REAL,
    sharpe_ratio REAL,
    trade_count INTEGER
);

CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP NOT NULL,
    action TEXT NOT NULL,
    details TEXT NOT NULL,
    prev_hash TEXT,
    hash TEXT NOT NULL UNIQUE
);

CREATE TABLE backtest_results (
    id TEXT PRIMARY KEY,
    strategy TEXT NOT NULL,
    start_date TEXT,
    end_date TEXT,
    initial_capital REAL,
    total_return REAL,
    sharpe_ratio REAL,
    max_drawdown REAL,
    win_rate REAL,
    equity_curve TEXT,
    trade_log TEXT,
    created_at TIMESTAMP
);

CREATE TABLE notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    type TEXT NOT NULL,
    category TEXT,
    title TEXT NOT NULL,
    message TEXT NOT NULL,
    ticker TEXT,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

CREATE TABLE agent_state (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    saved_at TIMESTAMP
);

CREATE TABLE sessions (
    token TEXT PRIMARY KEY,
    created_at TIMESTAMP,
    expires_at TIMESTAMP
);
```

---

### 6. NEW DEPENDENCIES

```
# backend/requirements.txt additions
websockets==12.0
cryptography==42.0.0
vectorbt==0.26.2
aiohttp==3.9.0
apscheduler==3.10.4

# frontend/package.json additions
"lightweight-charts": "^4.1.0"
"react-grid-layout": "^1.4.4"
"react-hot-toast": "^2.4.1"
```

---

### 7. COMPLETE API ENDPOINTS (39 total, 20 new)

```
PORTFOLIO (5)
  GET  /api/portfolio/summary
  GET  /api/portfolio/holdings
  GET  /api/portfolio/performance
  GET  /api/portfolio/sector-allocation
  POST /api/portfolio/sync                    ← NEW

SCREENER (2), ANALYSIS (2), PEG (2), MOVERS (2), NEWS (2), ALERTS (2)
  (unchanged from Part 2)

ORDERS (4) — NEW
  GET  /api/orders/open
  GET  /api/orders/history
  GET  /api/orders/{id}/timeline
  POST /api/orders/manual                     🔒 MFA

STRATEGIES (5) — NEW
  GET  /api/strategies
  POST /api/strategies/{name}/start
  POST /api/strategies/{name}/pause
  POST /api/strategies/{name}/stop
  PUT  /api/strategies/{name}/params

RISK (4) — NEW
  GET  /api/risk/status
  POST /api/risk/kill-switch                  🔒 MFA
  POST /api/risk/unlock                       🔒 MFA
  PUT  /api/risk/config                       🔒 MFA

BACKTEST (2) — NEW
  POST /api/backtest/run
  GET  /api/backtest/results/{id}

AUDIT (2) — NEW
  GET  /api/audit/log
  GET  /api/audit/verify

AUTH (2) — NEW
  POST /api/auth/login
  POST /api/auth/logout

SYSTEM (3) — ENHANCED
  GET  /api/health
  POST /api/system/run-pipeline
  GET  /api/system/pipeline-status

NOTIFICATIONS (2) — NEW
  GET  /api/notifications
  POST /api/notifications/{id}/read
```

---

### 8. BUILD PRIORITY: WEEK 1 vs POST-WEEK 1

```
┌────────────────────────────────────────────┬──────┬────────┐
│ Feature                                    │ Wk 1 │Post-Wk1│
├────────────────────────────────────────────┼──────┼────────┤
│ REST data pipeline (yfinance)              │  ✅  │        │
│ WebSocket streaming                        │      │   ✅   │
│ L1/L2 order book                           │      │   ✅   │
│ Batch indicator engine                     │  ✅  │        │
│ Streaming indicator engine                 │      │   ✅   │
│ Basic news sentiment                       │  ✅  │        │
│ Composite sentiment scoring                │      │   ✅   │
│ PEG Momentum strategy                     │  ✅  │        │
│ Strategy base class + manager              │  ✅  │        │
│ Additional strategies                      │      │   ✅   │
│ Order types (market/limit/stop)            │  ✅  │        │
│ Bracket + trailing stop                    │      │   ✅   │
│ Backtesting (full metrics)                 │      │   ✅   │
│ Paper trading mode                         │  ✅  │        │
│ Position sizing + stops                    │  ✅  │        │
│ Capital guards                             │  ✅  │        │
│ Kill switch                                │  ✅  │        │
│ .env credentials (dev)                     │  ✅  │        │
│ AES-256 encryption                         │      │   ✅   │
│ Dashboard password auth                    │  ✅  │        │
│ MFA for critical actions                   │      │   ✅   │
│ Basic audit logging                        │  ✅  │        │
│ Hash-chained audit log                     │      │   ✅   │
│ Auto-reconnect (broker)                    │  ✅  │        │
│ State persistence (basic)                  │  ✅  │        │
│ Full crash recovery                        │      │   ✅   │
│ Unified broker interface                   │  ✅  │        │
│ Dashboard + Portfolio pages                │  ✅  │        │
│ Screener + PEG + Movers pages              │  ✅  │        │
│ Sector + Analysis pages                    │  ✅  │        │
│ Candlestick charts (lightweight-charts)    │      │   ✅   │
│ Buy/sell markers on charts                 │      │   ✅   │
│ Dark/Light theme toggle                    │  ✅  │        │
│ Drag-and-drop layout                       │      │   ✅   │
│ Strategy control center page               │      │   ✅   │
│ Manual execution panel                     │      │   ✅   │
│ Risk config grid                           │      │   ✅   │
│ Toast notifications                        │  ✅  │        │
│ Critical modals                            │  ✅  │        │
│ Login page                                 │  ✅  │        │
│ Docker + GitHub                            │  ✅  │        │
│ Cloud deploy (Railway/Render)              │      │   ✅   │
└────────────────────────────────────────────┴──────┴────────┘
```

---
---

# PART 4: Slack Integration (Replacing Gmail)

---

## Overview

All notifications, daily briefings, alerts, and emergency messages are delivered via Slack instead of Gmail. This gives you richer formatting (blocks, charts, interactive buttons), instant delivery, and mobile push notifications.

---

## Architecture: Two Slack Integration Layers

```
┌─────────────────────────────────────────────────────────┐
│                SLACK INTEGRATION                         │
├─────────────────────────┬───────────────────────────────┤
│  LAYER 1: Bot API       │  LAYER 2: Claude MCP          │
│  (your trading agent)   │  (Claude.ai → your Slack)     │
│                         │                                │
│  Runs in your backend   │  Runs inside Claude.ai         │
│  Sends automated msgs   │  For ad-hoc analysis you       │
│  on schedule via        │  request in chat, Claude        │
│  Slack Bot Token        │  sends directly to your Slack   │
│                         │  via the MCP connector          │
│  - Daily briefing       │                                │
│  - Alert notifications  │  - "analyze NVDA and send      │
│  - Kill switch alerts   │    to my #trading channel"     │
│  - Order fill confirms  │  - "send my PEG watchlist      │
│  - Circuit breaker      │    to Slack"                   │
└─────────────────────────┴───────────────────────────────┘
```

---

## Layer 1: Slack Bot in Your Trading Agent (Backend)

### Setup: Create a Slack App + Bot

1. Go to https://api.slack.com/apps → **Create New App**
2. Choose **From scratch** → name it "Trading Agent" → select your workspace
3. Go to **OAuth & Permissions** → add these Bot Token Scopes:
   - `chat:write` — send messages
   - `chat:write.customize` — custom bot name/icon
   - `files:write` — upload chart images
   - `channels:read` — list channels
   - `groups:read` — list private channels
4. **Install to Workspace** → copy the **Bot User OAuth Token** (`xoxb-...`)
5. Create these Slack channels:
   - `#trading-briefing` — daily morning report
   - `#trading-alerts` — real-time buy/sell/stop alerts
   - `#trading-orders` — order fills and cancellations
   - `#trading-emergency` — kill switch + circuit breaker (set to loud notifications)

### Add to .env

```bash
# Slack Bot
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_CHANNEL_BRIEFING=C0123456789    # #trading-briefing channel ID
SLACK_CHANNEL_ALERTS=C0123456790      # #trading-alerts
SLACK_CHANNEL_ORDERS=C0123456791      # #trading-orders
SLACK_CHANNEL_EMERGENCY=C0123456792   # #trading-emergency
```

### Slack Notifier Module

```
Module: backend/alerts/slack_notifier.py  (REPLACES notifier.py email logic)
```

```python
import aiohttp
import json
from datetime import datetime

class SlackNotifier:
    """Send all trading notifications to Slack channels."""

    def __init__(self):
        self.token = os.getenv("SLACK_BOT_TOKEN")
        self.channels = {
            "briefing":  os.getenv("SLACK_CHANNEL_BRIEFING"),
            "alerts":    os.getenv("SLACK_CHANNEL_ALERTS"),
            "orders":    os.getenv("SLACK_CHANNEL_ORDERS"),
            "emergency": os.getenv("SLACK_CHANNEL_EMERGENCY"),
        }
        self.base_url = "https://slack.com/api"

    async def send_message(self, channel_key: str, text: str,
                           blocks: list = None, thread_ts: str = None):
        """Send a message to a Slack channel."""
        async with aiohttp.ClientSession() as session:
            payload = {
                "channel": self.channels[channel_key],
                "text": text,  # fallback for notifications
            }
            if blocks:
                payload["blocks"] = blocks
            if thread_ts:
                payload["thread_ts"] = thread_ts

            async with session.post(
                f"{self.base_url}/chat.postMessage",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            ) as resp:
                result = await resp.json()
                if not result.get("ok"):
                    print(f"Slack error: {result.get('error')}")
                return result

    async def upload_image(self, channel_key: str, filepath: str,
                           title: str = "Chart"):
        """Upload chart screenshot or generated image."""
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field("channels", self.channels[channel_key])
            data.add_field("title", title)
            data.add_field("file", open(filepath, "rb"))

            async with session.post(
                f"{self.base_url}/files.uploadV2",
                headers={"Authorization": f"Bearer {self.token}"},
                data=data,
            ) as resp:
                return await resp.json()

    # ─── Convenience methods for each notification type ───

    async def send_daily_briefing(self, briefing: dict):
        """Morning briefing → #trading-briefing"""
        blocks = self._format_briefing_blocks(briefing)
        await self.send_message("briefing", "Daily Trading Briefing", blocks)

    async def send_buy_alert(self, ticker, reason, entry, stop, score):
        """Buy signal → #trading-alerts"""
        blocks = self._format_alert_blocks(
            emoji="🟢", color="#10b981", title=f"BUY SIGNAL: {ticker}",
            fields={
                "Reason": reason,
                "Entry Zone": f"${entry}",
                "Stop Loss": f"${stop}",
                "Conviction": f"{score}/100",
            }
        )
        await self.send_message("alerts", f"🟢 BUY: {ticker}", blocks)

    async def send_sell_alert(self, ticker, reason, current_price):
        """Sell signal → #trading-alerts"""
        blocks = self._format_alert_blocks(
            emoji="🔴", color="#ef4444", title=f"SELL SIGNAL: {ticker}",
            fields={
                "Reason": reason,
                "Current Price": f"${current_price}",
            }
        )
        await self.send_message("alerts", f"🔴 SELL: {ticker}", blocks)

    async def send_trim_alert(self, ticker, atr_ext, pct_to_trim):
        """Trim signal → #trading-alerts"""
        blocks = self._format_alert_blocks(
            emoji="🟡", color="#f59e0b",
            title=f"TRIM SIGNAL: {ticker}",
            fields={
                "ATR Extension": f"{atr_ext:.1f}x (threshold: 3.0x)",
                "Action": f"Trim {pct_to_trim}% of position",
            }
        )
        await self.send_message("alerts", f"🟡 TRIM: {ticker}", blocks)

    async def send_order_filled(self, order):
        """Order confirmation → #trading-orders"""
        side_emoji = "🟢" if order.side == "buy" else "🔴"
        blocks = self._format_alert_blocks(
            emoji=side_emoji, color="#3b82f6",
            title=f"ORDER FILLED: {order.side.upper()} {order.ticker}",
            fields={
                "Shares": str(order.filled_quantity),
                "Price": f"${order.filled_price:.2f}",
                "Total": f"${order.filled_quantity * order.filled_price:,.2f}",
                "Strategy": order.strategy or "Manual",
            }
        )
        await self.send_message("orders", f"Order filled: {order.ticker}", blocks)

    async def send_emergency(self, reason: str):
        """Kill switch / circuit breaker → #trading-emergency"""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": "🚨 EMERGENCY ALERT"}
            },
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"*{reason}*\n\nAll trading has been halted. Manual intervention required."}
            },
            {
                "type": "context",
                "elements": [{"type": "mrkdwn", "text": f"Triggered at {datetime.now().strftime('%H:%M:%S ET')}"}]
            },
        ]
        # Also use @channel to ping everyone
        await self.send_message(
            "emergency",
            f"<!channel> 🚨 {reason}",
            blocks
        )

    async def send_stop_loss_warning(self, ticker, current, stop, pct_away):
        """Near stop loss → #trading-alerts"""
        blocks = self._format_alert_blocks(
            emoji="⚠️", color="#f59e0b",
            title=f"STOP LOSS WARNING: {ticker}",
            fields={
                "Current": f"${current:.2f}",
                "Stop": f"${stop:.2f}",
                "Distance": f"{pct_away:.1f}% away",
            }
        )
        await self.send_message("alerts", f"⚠️ {ticker} near stop", blocks)

    async def send_peg_detected(self, ticker, gap_pct, volume_mult, peg_low):
        """New PEG setup found → #trading-alerts"""
        blocks = self._format_alert_blocks(
            emoji="⚡", color="#8b5cf6",
            title=f"NEW PEG DETECTED: {ticker}",
            fields={
                "Gap": f"+{gap_pct:.1f}%",
                "Volume": f"{volume_mult:.1f}x average",
                "PEG Low (risk)": f"${peg_low:.2f}",
                "Action": "Watch for 9 EMA pullback entry",
            }
        )
        await self.send_message("alerts", f"⚡ PEG: {ticker}", blocks)

    # ─── Block formatting helpers ───

    def _format_briefing_blocks(self, briefing: dict) -> list:
        """Format the full daily briefing as Slack blocks."""
        blocks = [
            {
                "type": "header",
                "text": {"type": "plain_text",
                         "text": f"📊 Daily Briefing — {datetime.now().strftime('%B %d, %Y')}"}
            },
            {"type": "divider"},
            # Market overview
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Market Overview*"},
                "fields": [
                    {"type": "mrkdwn", "text": f"*SPY:* ${briefing['spy_price']} ({briefing['spy_change']})"},
                    {"type": "mrkdwn", "text": f"*QQQ:* ${briefing['qqq_price']} ({briefing['qqq_change']})"},
                    {"type": "mrkdwn", "text": f"*SMH:* ${briefing['smh_price']} ({briefing['smh_change']})"},
                ]
            },
            {"type": "divider"},
            # Portfolio summary
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": "*Your Portfolio*"},
                "fields": [
                    {"type": "mrkdwn", "text": f"*Value:* ${briefing['portfolio_value']:,.0f}"},
                    {"type": "mrkdwn", "text": f"*Daily P&L:* {briefing['daily_pnl']}"},
                    {"type": "mrkdwn", "text": f"*Positions:* {briefing['position_count']}"},
                    {"type": "mrkdwn", "text": f"*Cash:* ${briefing['cash']:,.0f}"},
                ]
            },
            {"type": "divider"},
        ]

        # Sell signals (urgent)
        if briefing.get("sell_signals"):
            sell_text = "\n".join(
                f"• *{s['ticker']}*: {s['reason']}"
                for s in briefing["sell_signals"]
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*🚨 Active Sell Signals*\n{sell_text}"}
            })
            blocks.append({"type": "divider"})

        # Top setups
        if briefing.get("top_setups"):
            setup_text = "\n".join(
                f"• *{s['ticker']}* — Score: {s['score']}/100 — {s['action']} — Entry: ${s['entry']}"
                for s in briefing["top_setups"][:5]
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*🎯 Top Setups (Score > 70)*\n{setup_text}"}
            })
            blocks.append({"type": "divider"})

        # Earnings this week
        if briefing.get("earnings_upcoming"):
            earn_text = "\n".join(
                f"• *{e['ticker']}* — {e['date']} ({e['timing']})"
                for e in briefing["earnings_upcoming"]
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*📅 Earnings This Week*\n{earn_text}"}
            })
            blocks.append({"type": "divider"})

        # Sector news (top 5)
        if briefing.get("sector_news"):
            news_text = "\n".join(
                f"• {n['headline']} _({n['source']})_"
                for n in briefing["sector_news"][:5]
            )
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*📰 Sector News*\n{news_text}"}
            })

        # Action items
        if briefing.get("action_items"):
            action_text = "\n".join(f"→ {a}" for a in briefing["action_items"])
            blocks.append({
                "type": "section",
                "text": {"type": "mrkdwn",
                         "text": f"*✅ Action Items*\n{action_text}"}
            })

        return blocks

    def _format_alert_blocks(self, emoji, color, title, fields) -> list:
        """Generic alert block formatter."""
        field_blocks = [
            {"type": "mrkdwn", "text": f"*{k}:* {v}"}
            for k, v in fields.items()
        ]
        return [
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"{emoji} *{title}*"},
                "fields": field_blocks,
            },
            {
                "type": "context",
                "elements": [
                    {"type": "mrkdwn",
                     "text": f"{datetime.now().strftime('%H:%M:%S ET')} · Trading Agent"}
                ]
            },
        ]
```

### Dependency Change

```bash
# REMOVE from requirements.txt (no longer needed for notifications):
# smtplib is built-in but we won't use it

# KEEP (already listed):
aiohttp==3.9.0    # used for Slack API calls
```

### Updated .env.example

```bash
# ── REMOVE ──
# GMAIL_USER=your_email@gmail.com
# GMAIL_APP_PASSWORD=your_app_password

# ── ADD ──
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_CHANNEL_BRIEFING=C0123456789
SLACK_CHANNEL_ALERTS=C0123456790
SLACK_CHANNEL_ORDERS=C0123456791
SLACK_CHANNEL_EMERGENCY=C0123456792
```

---

## Layer 2: Claude MCP Connector (Ad-Hoc Analysis to Slack)

Once you connect the Slack MCP connector in Claude.ai, you can do things like:

- "Analyze NVDA and send the result to #trading-alerts"
- "Send my current PEG watchlist to #trading-briefing"
- "Post a summary of today's top movers to Slack"

Claude will use the Slack MCP tools (`slack_send_message`, etc.) to deliver
directly from your conversation — no backend code needed for these ad-hoc requests.

This is separate from the automated bot above. Think of it as:
- **Bot** = scheduled, automated (runs even when you're not in Claude)
- **MCP** = on-demand, conversational (when you ask Claude to send something)

---

## Slack Channel Strategy

```
#trading-briefing        (daily, 7 AM PT)
├── Full morning report with market overview
├── Portfolio status + sell signals
├── Top setups ranked by conviction
├── Earnings calendar
└── Sector news digest

#trading-alerts          (real-time during market hours)
├── 🟢 BUY signals (PEG entry zones, base breakouts)
├── 🔴 SELL signals (stage breakdown, stop hit)
├── 🟡 TRIM signals (ATR extension > 3x)
├── ⚠️ STOP warnings (within 3% of stop loss)
├── ⚡ NEW PEG detected
└── 📊 Unusual volume spikes (RVol > 3x)

#trading-orders          (on each fill)
├── Order submitted confirmations
├── Order filled (with price, shares, total)
├── Order canceled
└── Partial fills

#trading-emergency       (rare, loud)
├── 🚨 Kill switch activated
├── 🚨 Circuit breaker triggered (daily loss limit)
├── 🚨 Max drawdown breach
├── 🚨 Broker API disconnected
└── 🚨 API key expired
     → Uses @channel to ping everyone
     → Set this channel to "All new messages" notifications
```

---

## What the Daily Briefing Looks Like in Slack

```
┌─────────────────────────────────────────────────┐
│ 📊 Daily Briefing — May 31, 2026               │
│─────────────────────────────────────────────────│
│                                                  │
│ Market Overview                                  │
│ SPY: $547.20 (+0.8%)  QQQ: $478.30 (+1.2%)     │
│ SMH: $285.60 (+1.5%)                             │
│─────────────────────────────────────────────────│
│                                                  │
│ Your Portfolio                                   │
│ Value: $347,250    Daily P&L: +$4,127 (+1.2%)   │
│ Positions: 12      Cash: $28,400                 │
│─────────────────────────────────────────────────│
│                                                  │
│ 🚨 Active Sell Signals                           │
│ • NVDA: ATR extension 3.2x — trim 1/3           │
│ • MU: Price within 3% of stop ($88.00)           │
│─────────────────────────────────────────────────│
│                                                  │
│ 🎯 Top Setups (Score > 70)                       │
│ • TER — Score: 92 — BUY — Entry: $155            │
│ • RKLB — Score: 87 — BUY — Entry: $26            │
│ • PLTR — Score: 81 — ADD — Entry: $75             │
│─────────────────────────────────────────────────│
│                                                  │
│ 📅 Earnings This Week                            │
│ • AVGO — Jun 3 (after close)                     │
│ • MU — Jun 5 (after close)                       │
│─────────────────────────────────────────────────│
│                                                  │
│ ✅ Action Items                                   │
│ → Review NVDA trim: sell 15 shares into strength │
│ → Set alert for TER at $155 (9 EMA entry)        │
│ → Tighten MU stop to $89.50                      │
│                                                  │
│            7:00 AM PT · Trading Agent             │
└─────────────────────────────────────────────────┘
```

---

## Updated File References (Gmail → Slack)

All references to Gmail/email in the blueprint are now replaced:

| Original (Gmail)                          | Updated (Slack)                            |
|-------------------------------------------|--------------------------------------------|
| `backend/alerts/notifier.py` (smtplib)   | `backend/alerts/slack_notifier.py` (aiohttp)|
| `GMAIL_USER` in .env                      | `SLACK_BOT_TOKEN` in .env                  |
| `GMAIL_APP_PASSWORD` in .env              | `SLACK_CHANNEL_*` in .env                  |
| "Send via Gmail SMTP"                     | "Send via Slack API"                       |
| Single email destination                  | 4 purpose-specific channels                |
| Plain text / HTML email                   | Rich Slack blocks with formatting          |
| No mobile push (unless email app)         | Native Slack mobile push notifications     |

---

## Claude Code Prompt for Slack Integration (Day 5)

```
Replace the Gmail email notifier with a Slack bot notifier.

Use aiohttp to call the Slack API (chat.postMessage).
Token comes from SLACK_BOT_TOKEN env var.

Create these methods in SlackNotifier class:
- send_daily_briefing(briefing_dict) → #trading-briefing
- send_buy_alert(ticker, reason, entry, stop, score) → #trading-alerts
- send_sell_alert(ticker, reason, price) → #trading-alerts
- send_trim_alert(ticker, atr_extension, pct) → #trading-alerts
- send_order_filled(order) → #trading-orders
- send_emergency(reason) → #trading-emergency with @channel
- send_stop_loss_warning(ticker, current, stop, pct_away) → #trading-alerts
- send_peg_detected(ticker, gap_pct, vol_mult, peg_low) → #trading-alerts

Use Slack Block Kit for rich formatting. Each message should have:
- A header section with emoji + title
- Fields section with key/value pairs
- Context footer with timestamp

Channel IDs come from env vars:
SLACK_CHANNEL_BRIEFING, SLACK_CHANNEL_ALERTS,
SLACK_CHANNEL_ORDERS, SLACK_CHANNEL_EMERGENCY

Also update daily_briefing.py to call slack_notifier instead of email.
```

---

## Slack vs Gmail Comparison

```
┌─────────────────────┬──────────────┬──────────────┐
│ Feature             │ Gmail        │ Slack ✅      │
├─────────────────────┼──────────────┼──────────────┤
│ Delivery speed      │ 1-30 sec     │ < 1 sec      │
│ Mobile push         │ Depends      │ Native       │
│ Rich formatting     │ HTML only    │ Block Kit    │
│ Channel separation  │ One inbox    │ 4 channels   │
│ Interactive buttons │ No           │ Yes          │
│ Threading           │ No           │ Yes          │
│ Image upload        │ Attachment   │ Inline       │
│ @channel ping       │ No           │ Yes          │
│ Search history      │ Email search │ Slack search │
│ Setup complexity    │ App password │ Bot token    │
│ Works offline       │ Yes          │ Yes (cached) │
│ Claude MCP support  │ Yes (Gmail)  │ Yes (Slack)  │
│ Cost                │ Free         │ Free         │
└─────────────────────┴──────────────┴──────────────┘
```
-e 
---
---

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
