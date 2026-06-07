"""Unit tests for AuthService — password hashing, TOTP, JWT."""
import pytest
from freezegun import freeze_time
from jose import JWTError

from app.auth.service import AuthService, TokenType, auth_service
from app.core.exceptions import ConfigurationError


@pytest.mark.unit
class TestAuthService:
    """Test AuthService methods in isolation."""

    def test_create_user_success(self, db_session):
        user = auth_service.create_user(db_session, "alice", "password123")
        assert user.username == "alice"
        assert user.hashed_password != "password123"  # hashed
        assert not user.totp_enabled
        assert user.is_active

    def test_create_user_duplicate_raises(self, db_session, sample_user):
        with pytest.raises(ConfigurationError, match="already exists"):
            auth_service.create_user(db_session, "another", "pass")

    def test_verify_password_correct(self):
        hashed = auth_service._hash_password("secret")
        assert auth_service.verify_password("secret", hashed)

    def test_verify_password_incorrect(self):
        hashed = auth_service._hash_password("secret")
        assert not auth_service.verify_password("wrong", hashed)

    def test_authenticate_password_success(self, db_session, sample_user):
        user = auth_service.authenticate_password(db_session, "testuser", "testpassword123")
        assert user is not None
        assert user.username == "testuser"

    def test_authenticate_password_wrong_password(self, db_session, sample_user):
        user = auth_service.authenticate_password(db_session, "testuser", "wrongpassword")
        assert user is None

    def test_authenticate_password_wrong_username(self, db_session):
        user = auth_service.authenticate_password(db_session, "nobody", "anypassword")
        assert user is None

    def test_authenticate_password_inactive_user(self, db_session, sample_user):
        sample_user.is_active = False
        db_session.commit()
        user = auth_service.authenticate_password(db_session, "testuser", "testpassword123")
        assert user is None

    def test_generate_totp_secret(self, db_session, sample_user):
        sample_user.totp_secret = None
        secret = auth_service.generate_totp_secret(db_session, sample_user)
        assert len(secret) == 32  # pyotp.random_base32() returns 32 chars
        assert secret == sample_user.totp_secret

    def test_get_totp_uri(self, sample_user):
        uri = auth_service.get_totp_uri(sample_user)
        assert uri.startswith("otpauth://totp/TradingAgent:testuser")
        assert "secret=JBSWY3DPEHPK3PXP" in uri

    def test_verify_totp_valid_code(self, sample_user):
        import pyotp
        totp = pyotp.TOTP(sample_user.totp_secret)
        code = totp.now()
        assert auth_service.verify_totp(sample_user, code)

    def test_verify_totp_invalid_code(self, sample_user):
        assert not auth_service.verify_totp(sample_user, "000000")

    def test_enable_totp_success(self, db_session, sample_user):
        import pyotp
        sample_user.totp_enabled = False
        totp = pyotp.TOTP(sample_user.totp_secret)
        code = totp.now()
        result = auth_service.enable_totp(db_session, sample_user, code)
        assert result is True
        assert sample_user.totp_enabled

    def test_enable_totp_invalid_code(self, db_session, sample_user):
        sample_user.totp_enabled = False
        result = auth_service.enable_totp(db_session, sample_user, "000000")
        assert result is False
        assert not sample_user.totp_enabled

    def test_generate_backup_codes(self, db_session, sample_user):
        codes = auth_service.generate_backup_codes(db_session, sample_user)
        assert len(codes) == 8
        assert all(len(c) == 8 for c in codes)  # 4 bytes hex = 8 chars uppercase
        assert len(sample_user.backup_codes) == 8

    def test_verify_backup_code_success(self, db_session, sample_user):
        codes = auth_service.generate_backup_codes(db_session, sample_user)
        first_code = codes[0]
        result = auth_service.verify_backup_code(db_session, sample_user, first_code)
        assert result is True
        assert len(sample_user.backup_codes) == 7  # consumed

    def test_verify_backup_code_invalid(self, db_session, sample_user):
        auth_service.generate_backup_codes(db_session, sample_user)
        result = auth_service.verify_backup_code(db_session, sample_user, "INVALID")
        assert result is False
        assert len(sample_user.backup_codes) == 8  # not consumed

    def test_create_token_access(self, sample_user):
        token = auth_service.create_token(sample_user.id, TokenType.ACCESS)
        assert isinstance(token, str)
        payload = auth_service.decode_token(token, TokenType.ACCESS)
        assert payload["sub"] == str(sample_user.id)
        assert payload["type"] == "access"

    def test_create_token_refresh(self, sample_user):
        token = auth_service.create_token(sample_user.id, TokenType.REFRESH)
        payload = auth_service.decode_token(token, TokenType.REFRESH)
        assert payload["type"] == "refresh"

    def test_decode_token_wrong_type(self, sample_user):
        token = auth_service.create_token(sample_user.id, TokenType.ACCESS)
        with pytest.raises(JWTError, match="Expected token type"):
            auth_service.decode_token(token, TokenType.REFRESH)

    @freeze_time("2026-01-01 12:00:00")
    def test_token_expiry_access(self, sample_user):
        """Access tokens expire in 30 minutes."""
        token = auth_service.create_token(sample_user.id, TokenType.ACCESS)
        # Move forward 31 minutes
        with freeze_time("2026-01-01 12:31:00"):
            with pytest.raises(JWTError):
                auth_service.decode_token(token, TokenType.ACCESS)

    def test_record_login(self, db_session, sample_user):
        assert sample_user.last_login is None
        auth_service.record_login(db_session, sample_user)
        assert sample_user.last_login is not None
