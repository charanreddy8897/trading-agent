# Testing Guide — Quick Reference

> 85%+ code coverage · 70+ tests · Unit + Integration

---

## Run Tests Locally

```bash
cd backend

# All tests with coverage
./run_tests.sh

# Specific test file
pytest tests/unit/test_auth_service.py -v

# By marker
pytest -m unit          # Fast unit tests only
pytest -m integration   # Integration tests (with DB)
pytest -m auth          # Auth-related tests

# Coverage report
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

---

## Test Structure

```
tests/
├── conftest.py                   — Global fixtures
├── unit/                         — 36 tests (no DB/API)
│   ├── test_auth_service.py      — 22 tests (passwords, TOTP, JWT)
│   ├── test_logging_config.py    — 8 tests (sanitisation)
│   └── test_screener.py          — 6 tests (indicators, PEG)
└── integration/                  — 44 tests (DB + API)
    ├── test_auth_api.py          — 14 tests (full auth flow)
    └── test_api_endpoints.py     — 30 tests (all routes)
```

---

## Fixtures (Auto-Injected)

```python
def test_example(
    db_session,              # Fresh DB session with rollback
    client,                  # FastAPI TestClient
    auth_headers,            # Valid JWT Authorization header
    sample_user,             # User with TOTP enabled
    sample_position,         # 100 shares NVDA
    sample_daily_prices,     # 30 days NVDA price data
):
    # Fixtures auto-injected — use them directly
    response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
    assert response.status_code == 200
```

---

## Writing Tests

### Unit Test

```python
import pytest
from app.auth.service import auth_service

@pytest.mark.unit
def test_verify_password():
    hashed = auth_service._hash_password("secret")
    assert auth_service.verify_password("secret", hashed)
    assert not auth_service.verify_password("wrong", hashed)
```

### Integration Test

```python
@pytest.mark.integration
@pytest.mark.api
def test_portfolio_summary(client, auth_headers, sample_position):
    response = client.get("/api/v1/portfolio/summary", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_value" in data
    assert data["total_value"] > 0
```

---

## Coverage Requirements

| Module | Target | Current |
|---|---|---|
| `app/auth/` | 95% | ✅ 95%+ |
| `app/core/` | 90% | ✅ 92% |
| `app/api/v1/` | 85% | ✅ 90%+ |
| `app/screener/` | 85% | ✅ 85%+ |
| **Overall** | **85%** | **✅ 85%+** |

Enforced by `pytest.ini` — builds fail if coverage drops below 85%.

---

## CI/CD

Tests run automatically on every push:

```yaml
# .github/workflows/test.yml
on: [push, pull_request]
jobs:
  test:
    steps:
      - run: pytest --cov=app --cov-fail-under=85
```

Merge blocked if tests fail or coverage < 85%.

---

## Debugging

```bash
# Run one test
pytest tests/unit/test_auth_service.py::TestAuthService::test_create_user_success -v

# Show print statements
pytest -s

# Drop into debugger on failure
pytest --pdb

# Verbose output
pytest -vv
```

---

## Common Patterns

### Test Exception

```python
import pytest
from app.core.exceptions import DataFetchError

def test_raises_error():
    with pytest.raises(DataFetchError, match="Expected message"):
        raise DataFetchError("Expected message")
```

### Parameterized Test

```python
@pytest.mark.parametrize("input,expected", [
    ("BUY", True),
    ("SELL", True),
    ("INVALID", False),
])
def test_action_validation(input, expected):
    assert validate_action(input) == expected
```

### Async Test

```python
@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

---

## More Details

See [`backend/tests/README.md`](../backend/tests/README.md) for comprehensive guide.
