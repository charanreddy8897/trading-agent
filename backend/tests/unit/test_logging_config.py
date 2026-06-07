"""Unit tests for structured logging and sanitisation."""
import pytest

from app.core.logging_config import sanitize


@pytest.mark.unit
class TestSanitize:
    """Test sensitive-data sanitisation."""

    def test_sanitize_password(self):
        data = {"username": "alice", "password": "secret"}
        result = sanitize(data)
        assert result["username"] == "alice"
        assert result["password"] == "***REDACTED***"

    def test_sanitize_api_keys(self):
        data = {
            "anthropic_api_key": "sk-ant-123",
            "finnhub_api_key": "xyz789",
            "jwt_secret_key": "supersecret",
        }
        result = sanitize(data)
        assert all(v == "***REDACTED***" for v in result.values())

    def test_sanitize_tokens(self):
        data = {
            "access_token": "eyJ...",
            "refresh_token": "eyJ...",
            "temp_token": "eyJ...",
        }
        result = sanitize(data)
        assert all(v == "***REDACTED***" for v in result.values())

    def test_sanitize_nested_dict(self):
        data = {
            "user": {"id": 1, "password": "secret"},
            "auth": {"token": "abc123"},
        }
        result = sanitize(data)
        assert result["user"]["id"] == 1
        assert result["user"]["password"] == "***REDACTED***"
        assert result["auth"]["token"] == "***REDACTED***"

    def test_sanitize_list(self):
        data = [
            {"username": "alice", "password": "pass1"},
            {"username": "bob", "password": "pass2"},
        ]
        result = sanitize(data)
        assert result[0]["password"] == "***REDACTED***"
        assert result[1]["password"] == "***REDACTED***"

    def test_sanitize_max_depth(self):
        """Nested beyond depth 5 stops recursion."""
        data = {"a": {"b": {"c": {"d": {"e": {"f": {"password": "secret"}}}}}}}
        result = sanitize(data)
        # Depth limit prevents infinite recursion
        assert result["a"]["b"]["c"]["d"]["e"]["f"]["password"] == "secret"

    def test_sanitize_case_insensitive(self):
        """Field names are case-insensitive."""
        data = {"Password": "secret", "API_KEY": "key123"}
        result = sanitize(data)
        assert result["Password"] == "***REDACTED***"
        assert result["API_KEY"] == "***REDACTED***"

    def test_sanitize_preserves_other_fields(self):
        data = {
            "user_id": 42,
            "email": "alice@example.com",
            "password": "secret",
            "metadata": {"clicks": 10},
        }
        result = sanitize(data)
        assert result["user_id"] == 42
        assert result["email"] == "alice@example.com"
        assert result["password"] == "***REDACTED***"
        assert result["metadata"]["clicks"] == 10
