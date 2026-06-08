# Trading Agent — Test Suite

> Comprehensive unit and integration tests with 85%+ code coverage.

---

## Quick Start

```bash
# Run all tests with coverage
cd backend
./run_tests.sh

# Run specific test file
../.venv/bin/pytest tests/unit/test_auth_service.py -v

# Run tests by marker
../.venv/bin/pytest -m unit          # Unit tests only (fast)
../.venv/bin/pytest -m integration   # Integration tests (requires DB)
../.venv/bin/pytest -m auth          # Auth-related tests only

# Run with coverage report
../.venv/bin/pytest --cov=app --cov-report=html
# Open htmlcov/index.html in browser

# Run tests in parallel (faster)
../.venv/bin/pytest -n auto
```

---

## Directory Structure

```
tests/
├── conftest.py               — Global fixtures (DB, client, sample data)
├── pytest.ini                — Pytest configuration
├── unit/                     — Fast tests, no external dependencies
│   ├── test_auth_service.py  — Password hashing, TOTP, JWT
│   ├── test_logging_config.py — Log sanitisation
│   └── test_screener.py      — Technical indicators, PEG detection
├── integration/              — Tests with DB + API
│   ├── test_auth_api.py      — Full auth flow via HTTP
│   └── test_api_endpoints.py — All protected API routes
└── fixtures/                 — Shared test data factories
```

---

## Test Fixtures

All fixtures are defined in `conftest.py` and available to all test modules.

### Database Fixtures

| Fixture | Scope | Description |
|---|---|---|
| `test_engine` | session | SQLite in-memory engine (shared) |
| `db_session` | function | Fresh DB session per test with rollback |

### Sample Data Fixtures

| Fixture | Returns | Description |
|---|---|---|
| `sample_user` | `User` | Test user with TOTP enabled |
| `sample_daily_prices` | `list[DailyPrice]` | 30 days of NVDA price data |
| `sample_technical_signal` | `TechnicalSignal` | Computed indicators for NVDA |
| `sample_peg_setup` | `PegSetup` | Active PEG for TSLA |
| `sample_claude_analysis` | `ClaudeAnalysis` | Claude recommendation for NVDA |
| `sample_position` | `Position` | 100 shares NVDA position |
| `sample_news_item` | `NewsItem` | Single news headline |
| `sample_alert` | `Alert` | NEAR_STOP alert |

### API Testing Fixtures

| Fixture | Returns | Description |
|---|---|---|
| `client` | `TestClient` | FastAPI test client with overridden DB |
| `auth_headers` | `dict` | Valid JWT `Authorization` header |
| `temp_token` | `str` | Temp token for TOTP flow testing |

---

## Writing Tests

### Unit Test Example

```python
import pytest
from app.auth.service import auth_service

@pytest.mark.unit
def test_verify_password_correct():
    hashed = auth_service._hash_password("secret")
    assert auth_service.verify_password("secret", hashed)
```

### Integration Test Example

```python
import pytest

@pytest.mark.integration
@pytest.mark.api
def test_portfolio_summary(client, auth_headers, sample_position):
    response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_value" in data
```

### Using Fixtures

```python
def test_with_fixtures(db_session, sample_user, sample_position):
    # db_session, sample_user, sample_position are automatically injected
    positions = db_session.query(Position).all()
    assert len(positions) >= 1
```

---

## Coverage Requirements

- **Minimum:** 85% (enforced by pytest.ini)
- **Target:** 90%+

### Check Coverage

```bash
# Terminal report
../.venv/bin/pytest --cov=app --cov-report=term-missing

# HTML report (detailed per-line coverage)
../.venv/bin/pytest --cov=app --cov-report=html
open htmlcov/index.html
```

### Coverage by Module (Expected)

| Module | Target | Notes |
|---|---|---|
| `app/auth/` | 95%+ | Critical security code |
| `app/core/` | 90%+ | Database, settings, logging |
| `app/api/v1/` | 85%+ | All endpoints tested |
| `app/screener/` | 85%+ | Technical indicators, PEG scanner |
| `app/analysis/` | 70%+ | Claude calls mocked in tests |
| `app/data/` | 70%+ | External API calls mocked |

---

## Test Markers

Mark tests with decorators to run subsets:

```python
@pytest.mark.unit          # Fast, no DB
@pytest.mark.integration   # Requires DB
@pytest.mark.api           # API endpoint tests
@pytest.mark.auth          # Auth-related
@pytest.mark.slow          # Long-running tests
```

Run specific markers:
```bash
pytest -m unit             # Only unit tests
pytest -m "not slow"       # Skip slow tests
pytest -m "integration and api"  # Integration API tests only
```

---

## Mocking External APIs

External API calls (Claude, Finnhub, Alpaca) should be mocked in tests.

### Example: Mock Claude API

```python
def test_claude_analysis(mocker, db_session):
    mock_response = {"conviction": 8, "action": "BUY", ...}
    mocker.patch("app.analysis.claude_analyzer.ClaudeAnalyzer._call_api", return_value=mock_response)

    result = claude_analyzer.analyze_ticker_async(db_session, "NVDA")
    assert result["conviction"] == 8
```

### Example: Mock Slack Notifier

```python
def test_slack_notification(mocker):
    mock_post = mocker.patch("app.alerts.notifier.SlackNotifier._post_with_retry", return_value=True)

    result = slack_notifier.send("briefing", "Test message")
    assert result is True
    mock_post.assert_called_once()
```

---

## Continuous Integration

Tests run automatically on every push via GitHub Actions:

```yaml
# .github/workflows/test.yml
name: Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.13'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest --cov=app --cov-fail-under=85
```

---

## Debugging Failed Tests

### Run One Test

```bash
pytest tests/unit/test_auth_service.py::TestAuthService::test_create_user_success -v
```

### Show Print Statements

```bash
pytest -s  # or --capture=no
```

### Drop into PDB on Failure

```bash
pytest --pdb
```

### Verbose Output

```bash
pytest -vv
```

---

## Test Data Factories (Future)

For generating large volumes of test data, use Faker:

```python
from faker import Faker
fake = Faker()

def create_fake_position(db_session):
    return Position(
        ticker=fake.random_element(["NVDA", "TSLA", "AAPL"]),
        shares=fake.random_int(min=10, max=1000),
        avg_cost=fake.pyfloat(min_value=10, max_value=1000),
        ...
    )
```

---

## Performance Testing (Future)

Use `pytest-benchmark` for performance regression detection:

```bash
pip install pytest-benchmark

# In test:
def test_screener_performance(benchmark, db_session):
    result = benchmark(universe_scorer.rank_universe, db_session)
    assert len(result.rows) > 0
```

---

## Test Database Management

### In-Memory SQLite (Default)

Fast, isolated, no cleanup needed. Perfect for CI.

### PostgreSQL Test DB (Optional)

For testing Postgres-specific features:

```python
# conftest.py
@pytest.fixture(scope="session")
def test_db_url():
    return "postgresql://test_user:test_pass@localhost:5432/test_trading_agent"
```

Run tests:
```bash
# Create test DB first
psql -U postgres -c "CREATE DATABASE test_trading_agent;"
pytest
```

---

## Common Test Patterns

### Test Exception Handling

```python
import pytest
from app.core.exceptions import DataFetchError

def test_raises_exception():
    with pytest.raises(DataFetchError, match="Expected error message"):
        raise DataFetchError("Expected error message")
```

### Test Async Functions

```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

### Parameterized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("BUY", True),
    ("SELL", True),
    ("INVALID", False),
])
def test_action_validation(input, expected):
    assert validate_action(input) == expected
```

---

## Troubleshooting

### Import Errors

If tests can't import `app` modules:
```bash
# Make sure you're in the backend/ directory
cd backend
pytest
```

### Fixture Not Found

Make sure the fixture is defined in `conftest.py` or imported at the top of your test file.

### Database Locked (SQLite)

SQLite doesn't handle concurrent writes. Ensure `scope="function"` on `db_session` fixture.

### Tests Pass Locally, Fail in CI

Check:
- Environment variables (use `test_settings` fixture)
- File paths (use `Path(__file__).parent`)
- Time zones (use `freezegun` for time-dependent tests)
