# Trading Agent

> AI-powered growth stock analysis using CANSLIM + Weinstein Stage methodology. Claude analyses every ticker nightly; a React dashboard surfaces recommendations in real time.

---

## Documentation

| Document | Description |
|---|---|
| [**AWS Deployment Guide**](DEPLOYMENT.md) | **Complete AWS deployment walkthrough** - CDK setup, SSM configuration, EC2 deployment, troubleshooting |
| [High-Level Design](documentation/HLD.md) | System architecture, trading strategy, infrastructure topology, cost model, security model, key flows |
| [Backend LLD](documentation/BACKEND_LLD.md) | All Python classes, DB schema, ER diagram, API reference, auth flow, async patterns, design patterns |
| [Frontend LLD](documentation/FRONTEND_LLD.md) | Component tree, pages, hooks, API client, state management, design system, data flow diagrams |
| [Infrastructure (CDK)](cdk/README.md) | AWS CDK stacks, cost breakdown, GitHub Actions CI/CD |

---

## 🚀 Production Deployment

**Live System**: https://d28apcmg03a0s.cloudfront.net  
**API Endpoint**: http://100.30.119.38  
**Region**: us-east-1  
**Account**: 657347292520

See [DEPLOYMENT.md](DEPLOYMENT.md) for complete deployment instructions.

---

## Quick Start

### Prerequisites
- Docker Desktop (for local PostgreSQL)
- Python 3.13 with `uv`
- Node.js 18+

### Local development

```bash
# 1. Clone and set up environment
git clone https://github.com/YOUR_USERNAME/trading_agent.git
cd trading_agent
cp .env.example .env          # fill in your API keys

# 2. Start PostgreSQL
docker-compose up -d db

# 3. Start backend
cd backend
uv pip install -r requirements.txt --python ../.venv/bin/python
uvicorn app.main:app --reload

# 4. Create your user (one-time)
python -m scripts.seed_user --username charan --password "your-password-min-12"

# 5. Start frontend (new terminal)
cd frontend
npm install
npm run dev
```

| Service | URL |
|---|---|
| Frontend | http://localhost:5173 |
| API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| pgAdmin | http://localhost:5050 |

### Login flow

```
POST /auth/login           → temp_token
GET  /auth/totp-setup      → scan QR with Google Authenticator (first time)
POST /auth/totp-setup      → confirm code → JWT tokens
POST /auth/totp            → every subsequent login
```

### Run tests

```bash
cd backend
./run_tests.sh             # All tests + coverage report (85%+ required)

# Or run specific test suites
pytest tests/unit -v       # Unit tests only (fast)
pytest tests/integration -v # Integration tests
pytest -m auth -v          # Auth tests only

# Coverage report opens in browser
open htmlcov/index.html
```

See [`backend/tests/README.md`](backend/tests/README.md) for comprehensive testing guide.

---

## Project Structure

```
trading_agent/
├── backend/              FastAPI + SQLAlchemy + asyncio
│   ├── app/
│   │   ├── auth/         JWT + TOTP authentication
│   │   ├── core/         Settings, database, exceptions
│   │   ├── data/         Price + news fetchers
│   │   ├── screener/     Technical, PEG, base, stage analyzers
│   │   ├── analysis/     Claude AI + universe scoring
│   │   ├── portfolio/    Alpaca + Robinhood sync
│   │   ├── risk/         Stop manager, exposure, position sizer
│   │   ├── alerts/       Slack notifier + daily briefing
│   │   ├── scheduler/    APScheduler jobs
│   │   └── api/v1/       REST endpoints
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/             React 18 + TypeScript + Vite
│   ├── src/
│   │   ├── api/          Axios client + API namespaces
│   │   ├── hooks/        TanStack Query hooks
│   │   ├── pages/        8 pages
│   │   ├── components/   Layout, charts, tables, shared
│   │   ├── types/        All TypeScript interfaces
│   │   └── utils/        Formatters + constants
│   └── vercel.json       Vercel deployment config
├── cdk/                  AWS CDK infrastructure (Python)
│   ├── stacks/
│   │   ├── network_stack.py    VPC + security groups
│   │   ├── database_stack.py   RDS PostgreSQL
│   │   ├── app_stack.py        EC2 + nginx + SSM
│   │   └── frontend_stack.py   S3 + CloudFront
│   └── README.md         Deploy guide
├── documentation/        Architecture docs (you are here)
│   ├── HLD.md
│   ├── BACKEND_LLD.md
│   └── FRONTEND_LLD.md
├── docker-compose.yml    Local dev (PostgreSQL + backend)
├── railway.toml          Railway deployment config
└── .github/workflows/    GitHub Actions CI/CD
```

---

## Environment Variables

```bash
# AI
ANTHROPIC_API_KEY=sk-ant-...

# Market data
FINNHUB_API_KEY=...

# Portfolio (paper trading)
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Notifications
SLACK_BOT_TOKEN=xoxb-...
SLACK_CHANNEL_BRIEFING=C...
SLACK_CHANNEL_ALERTS=C...
SLACK_CHANNEL_ORDERS=C...
SLACK_CHANNEL_EMERGENCY=C...

# Database
DATABASE_URL=postgresql://trading_user:trading_pass@localhost:5432/trading_agent

# Auth
JWT_SECRET_KEY=             # openssl rand -hex 32
ROBINHOOD_SYNC_KEY=         # openssl rand -hex 32

# Mode
TRADING_MODE=paper
```

---

## Tech Stack Summary

| Layer | Key technologies |
|---|---|
| Backend | FastAPI · SQLAlchemy · PostgreSQL · asyncio · Pydantic |
| AI | Claude Sonnet (`claude-sonnet-4-5`) via Anthropic SDK |
| Data | yfinance · Finnhub · Alpaca SDK · Robinhood MCP |
| Scheduling | APScheduler (morning pipeline, intraday, evening) |
| Notifications | Slack API with tenacity retries |
| Auth | JWT (python-jose) · TOTP (pyotp) · bcrypt |
| Frontend | React 18 · TypeScript · Vite · TanStack Query · Recharts · Tailwind |
| Infrastructure | AWS CDK · EC2 · RDS · S3 · CloudFront · SSM · CloudWatch |
| Deployment | Docker · Railway · Vercel · GitHub Actions |
