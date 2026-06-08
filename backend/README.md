# Trading Agent Backend

Production-ready trading system with PEG pattern detection, technical analysis, and portfolio management.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [First-Time Setup](#first-time-setup)
3. [Authentication Flow](#authentication-flow)
4. [Daily Login](#daily-login)
5. [Testing Connections](#testing-connections)
6. [Using the API](#using-the-api)
7. [Troubleshooting](#troubleshooting)

---

## Quick Start

```bash
# 1. Start the backend
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 2. Test connections
python -m scripts.test_connections

# 3. Access API docs
open http://localhost:8000/docs
```

---

## First-Time Setup

### Prerequisites

1. **Database**: PostgreSQL running and accessible
2. **Python**: 3.11+ with virtual environment
3. **API Keys**: Configured in `.env` file

### Step 1: Install Dependencies

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2: Configure Environment

Create `.env` file in the `backend/` directory:

```bash
# Database
DATABASE_URL=postgresql://trading_user:your_password@localhost:5432/trading_agent

# API Keys
ANTHROPIC_API_KEY=sk-ant-...
FINNHUB_API_KEY=...
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...

# JWT Secret (generate with: openssl rand -hex 32)
JWT_SECRET_KEY=your_secret_key_here

# Optional: Slack notifications
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_ALERTS=...
```

### Step 3: Run Database Migrations

```bash
# Add backup_codes column to users table
python -m scripts.migrate_db
```

### Step 4: Create Your User Account

```bash
python -m scripts.seed_user --username YOUR_USERNAME --password "YOUR_STRONG_PASSWORD"
```

**Requirements**:
- Username: 3-50 characters
- Password: At least 8 characters

**Output**:
```
✓ User 'YOUR_USERNAME' created successfully
✓ Next step: Login and set up TOTP (Two-Factor Authentication)
```

### Step 5: Start the Backend

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000

# Or run in background:
nohup uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/trading-agent.log 2>&1 &
```

**You should see**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

---

## Authentication Flow

The system uses **2FA (Two-Factor Authentication)** with TOTP (Time-based One-Time Password) for security.

### First-Time Login: Enable 2FA

#### Step 1: Login with Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD"
  }'
```

**Response**:
```json
{
  "status": "setup_required",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Save the `temp_token`** - it expires in 5 minutes.

#### Step 2: Get TOTP Secret & QR Code

```bash
curl "http://localhost:8000/api/v1/auth/totp-setup?temp_token=YOUR_TEMP_TOKEN"
```

**Response**:
```json
{
  "secret": "GNZRPROVCZLMCCTEHNPOCWMXJRXSHYF6",
  "otpauth_uri": "otpauth://totp/TradingAgent:yourname?secret=...",
  "qr_data_uri": "data:image/png;base64,...",
  "backup_codes": [
    "0C5AD181", "C10CB734", "5977EFEB", "7E34A60A",
    "7718019E", "FE885211", "A7EA5E97", "6D70BF92"
  ]
}
```

#### Step 3: Add to Authenticator App

**Option A: Scan QR Code**
1. Save the `qr_data_uri` as an HTML file and open in browser
2. Scan with **Google Authenticator** or **Authy** app

**Option B: Manual Entry** (Recommended)
1. Open Google Authenticator or Authy on your phone
2. Tap **"Add Account"** → **"Enter a setup key"**
3. Fill in:
   - **Account name**: `TradingAgent` (or any name you want)
   - **Key**: `GNZRPROVCZLMCCTEHNPOCWMXJRXSHYF6` (from response)
   - **Type**: Time-based
4. Tap **"Add"**

**⚠️ CRITICAL: Save Your Backup Codes**

Copy the 8 backup codes to a safe place (password manager, encrypted note). These are **one-time emergency codes** if you lose your phone!

```
0C5AD181  C10CB734  5977EFEB  7E34A60A
7718019E  FE885211  A7EA5E97  6D70BF92
```

#### Step 4: Verify TOTP Setup

Get the 6-digit code from your authenticator app and run:

```bash
curl -X POST http://localhost:8000/api/v1/auth/totp-setup \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "YOUR_TEMP_TOKEN",
    "code": "123456"
  }'
```

**Replace `123456` with your actual 6-digit code!**

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**Save both tokens**:
- `access_token`: Valid for 15 minutes (use for API calls)
- `refresh_token`: Valid for 7 days (use to get new access tokens)

**✅ 2FA Setup Complete!** From now on, every login requires password + TOTP code.

---

## Daily Login

After initial setup, the login process is simpler:

### Step 1: Login with Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "YOUR_USERNAME",
    "password": "YOUR_PASSWORD"
  }'
```

**Response**:
```json
{
  "status": "totp_required",
  "temp_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Step 2: Verify TOTP Code

Get the current 6-digit code from your authenticator app (refreshes every 30 seconds):

```bash
curl -X POST http://localhost:8000/api/v1/auth/totp \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "YOUR_TEMP_TOKEN",
    "code": "654321"
  }'
```

**Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

**✅ You're logged in!** Use the `access_token` for all API calls.

### Step 3: Refresh Access Token (When Expired)

Access tokens expire after 15 minutes. Use your refresh token to get a new pair:

```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

**Response**: New `access_token` and `refresh_token`

---

## Testing Connections

Use the connection test script to verify all external services are working:

```bash
python -m scripts.test_connections
```

**What it tests**:
1. ✓ PostgreSQL database connection
2. ✓ API keys configured (Anthropic, Finnhub, Alpaca)
3. ✓ Finnhub API (live market data)
4. ✓ Alpaca API (trading account)
5. ✓ Anthropic Claude API (AI analysis)
6. ✓ Database tables populated

**Example Output**:

```
===========================================================================
                    TRADING AGENT - CONNECTION TEST
===========================================================================

[1/5] Testing Database Connection...
✓ PostgreSQL                PASS   Connected: PostgreSQL

[2/5] Checking API Keys...
✓ Anthropic Claude Key      PASS   Configured (sk-ant-a...)
✓ Finnhub Key               PASS   Configured (d8ebp4hr...)
✓ Alpaca Keys               PASS   Configured (PKUDQD6B...)

[3/5] Testing Finnhub API...
✓ Finnhub API               PASS   AAPL quote: $311.23

[4/5] Testing Alpaca API...
✓ Alpaca API                PASS   Account connected, buying power: $400,000.00

[5/5] Testing Anthropic Claude API...
✓ Anthropic Claude API      PASS   Response: OK

[BONUS] Checking Database Tables...
✓ Data - Price History      PASS   12,550 records
○ Data - Positions          SKIP   No positions yet
✓ Data - PEG Setups         PASS   131 setups found
○ Data - Active Alerts      SKIP   No active alerts

===========================================================================
RESULTS: 8 passed, 0 failed, 2 skipped
===========================================================================

✅ All critical services are working!
```

**If tests fail**, check:
1. `.env` file has correct API keys
2. Database is running and accessible
3. Network connection is active

---

## Using the API

### Access Swagger UI (Interactive Docs)

1. Open: http://localhost:8000/docs
2. Click **"Authorize"** button (🔓 icon, top right)
3. In the **HTTPBearer** field, paste your `access_token`:
   ```
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```
4. Click **"Authorize"** → **"Close"**
5. Now all endpoints are unlocked!

### Example API Calls

**Get Your User Info**:
```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Get Top Ranked Stocks**:
```bash
curl http://localhost:8000/api/v1/screener/ranked \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Get PEG Setups**:
```bash
curl http://localhost:8000/api/v1/screener/peg-setups \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Get Portfolio Summary**:
```bash
curl http://localhost:8000/api/v1/portfolio/summary \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Run Data Pipeline (Fetch Latest Prices)**:
```bash
curl -X POST http://localhost:8000/api/v1/system/run-pipeline \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

---

## Troubleshooting

### 🔴 "Invalid or expired token"

**Cause**: Access token expired (15 min lifetime)

**Fix**: Use refresh token to get a new access token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "YOUR_REFRESH_TOKEN"}'
```

---

### 🔴 "Invalid temp token"

**Cause**: Temp token expired (5 min lifetime) or already used

**Fix**: Login again to get a fresh temp token:
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"YOUR_USERNAME","password":"YOUR_PASSWORD"}'
```

---

### 🔴 "Invalid TOTP code"

**Causes**:
1. Code expired (codes refresh every 30 seconds)
2. Phone time not synced with server

**Fix**:
1. Wait for a fresh code in your authenticator app
2. Enter the code within 30 seconds
3. Check your phone's time is synced (Settings → Date & Time → Auto)

**Emergency**: Use a backup code instead of TOTP code (one-time use)

---

### 🔴 Lost Your Phone (Can't Generate TOTP Codes)

**Option 1: Use Backup Codes**

Use one of your 8 backup codes instead of the TOTP code:
```bash
curl -X POST http://localhost:8000/api/v1/auth/totp \
  -H "Content-Type: application/json" \
  -d '{
    "temp_token": "YOUR_TEMP_TOKEN",
    "code": "0C5AD181"
  }'
```

**⚠️ Each backup code works only once!** You'll have 7 left after using one.

**Option 2: Reset TOTP (Admin Access Required)**

If you have database access:
```bash
python -m scripts.reset_password --username YOUR_USERNAME --password "NEW_PASSWORD"
```

This resets password + disables TOTP, so you can set up 2FA again.

---

### 🔴 Database Connection Errors

**Error**: `connection refused` or `could not connect to server`

**Check**:
1. PostgreSQL is running:
   ```bash
   pg_isready -h localhost -p 5432
   ```
2. Database exists:
   ```bash
   psql -U trading_user -d trading_agent -c "SELECT 1"
   ```
3. `.env` has correct `DATABASE_URL`

---

### 🔴 API Key Errors

**Error**: `401 Unauthorized` or `403 Forbidden` from external APIs

**Check**:
1. Run connection test:
   ```bash
   python -m scripts.test_connections
   ```
2. Verify API keys in `.env` are valid
3. Check API usage limits:
   - Finnhub: https://finnhub.io/dashboard
   - Alpaca: https://app.alpaca.markets/paper/dashboard
   - Anthropic: https://console.anthropic.com/settings/keys

---

### 🔴 Port 8000 Already in Use

**Error**: `OSError: [Errno 48] Address already in use`

**Fix**:
```bash
# Kill existing process
kill $(lsof -ti:8000)

# Then restart
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

---

## Useful Scripts

### Reset User Password

```bash
python -m scripts.reset_password \
  --username YOUR_USERNAME \
  --password "NEW_PASSWORD"
```

**Effect**:
- Resets password
- Disables TOTP (you'll need to set up 2FA again)

---

### Run Database Migration

```bash
python -m scripts.migrate_db
```

**Effect**: Adds `backup_codes` column to `users` table if missing

---

### Check Logs

```bash
# Real-time logs
tail -f /tmp/trading-agent.log

# Last 100 lines
tail -100 /tmp/trading-agent.log

# Search for errors
grep ERROR /tmp/trading-agent.log
```

---

## Security Notes

1. **Never commit `.env` file** - Contains sensitive API keys
2. **Never share your tokens** - Treat like passwords
3. **Use strong passwords** - Minimum 12 characters, mix of types
4. **Save backup codes securely** - Password manager or encrypted storage
5. **Refresh tokens after 7 days** - They expire and must be renewed by logging in again

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                         CLIENT                               │
│  (Browser, curl, Python script, Mobile app)                 │
└────────────────┬────────────────────────────────────────────┘
                 │
                 │ HTTPS
                 ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  Authentication Layer (JWT + TOTP)                   │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  API Endpoints (Screener, Portfolio, Alerts, System) │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Business Logic (Scanners, Analyzers, Risk Manager)  │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │  Data Layer (Database, External APIs)                │  │
│  └──────────────────────────────────────────────────────┘  │
└───┬──────────────────┬────────────────────┬─────────────────┘
    │                  │                    │
    │                  │                    │
    ▼                  ▼                    ▼
┌─────────┐   ┌────────────────┐   ┌───────────────┐
│PostgreSQL│  │ External APIs  │   │ Scheduler     │
│ Database │  │ • Finnhub      │   │ (APScheduler) │
│          │  │ • Alpaca       │   │               │
│          │  │ • Anthropic    │   │ • Morning Run │
│          │  │                │   │ • Intraday    │
└──────────┘  └────────────────┘   └───────────────┘
```

---

## Support

**Issues?** Check:
1. This README's [Troubleshooting](#troubleshooting) section
2. Backend logs: `tail -f /tmp/trading-agent.log`
3. Connection test: `python -m scripts.test_connections`
4. API health: `curl http://localhost:8000/health`

**Still stuck?** File an issue with:
- Error message (full traceback)
- Steps to reproduce
- Output from connection test
- Last 50 lines of logs

---

## Quick Reference Card

### Start Backend
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Login
```bash
# Step 1: Password
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"USER","password":"PASS"}'

# Step 2: TOTP
curl -X POST http://localhost:8000/api/v1/auth/totp \
  -H "Content-Type: application/json" \
  -d '{"temp_token":"TOKEN","code":"123456"}'
```

### Test Connections
```bash
python -m scripts.test_connections
```

### Access API
```bash
# In Swagger UI: http://localhost:8000/docs
# Authorize → Paste access_token → Try endpoints

# Or via curl:
curl http://localhost:8000/api/v1/screener/ranked \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Check Status
```bash
# Health
curl http://localhost:8000/health

# Logs
tail -f /tmp/trading-agent.log

# Database
python -m scripts.test_connections
```

---

**Version**: 1.0  
**Last Updated**: 2026-06-05  
**Python**: 3.11+  
**Database**: PostgreSQL 14+
