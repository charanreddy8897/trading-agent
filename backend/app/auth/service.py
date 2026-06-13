"""AuthService — password hashing, TOTP, JWT token management."""
from __future__ import annotations

import base64
import io
import logging
from datetime import datetime, timedelta, timezone
from enum import Enum

import bcrypt
import pyotp
import qrcode
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.exceptions import ConfigurationError
from app.core.settings import settings
from app.models.db_models import User

logger = logging.getLogger(__name__)


class TokenType(str, Enum):
    ACCESS  = "access"
    REFRESH = "refresh"
    TEMP    = "temp"    # issued after password OK, before TOTP


class AuthService:
    """Handles all authentication logic: passwords, TOTP, and JWT tokens.

    Single responsibility per method — password logic never touches JWT logic,
    TOTP logic never touches the DB directly (caller passes User objects).
    """

    # ── User management ───────────────────────────────────────────────────────

    def create_user(self, db: Session, username: str, password: str) -> User:
        """Create the (only) user. Raises if one already exists."""
        if db.query(User).first():
            raise ConfigurationError("A user already exists. This system is single-user.")
        user = User(
            username=username,
            hashed_password=self._hash_password(password),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info("User '%s' created", username)
        return user

    def get_user(self, db: Session, username: str) -> User | None:
        return db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, db: Session, user_id: int) -> User | None:
        return db.query(User).filter(User.id == user_id).first()

    # ── Password ──────────────────────────────────────────────────────────────

    @staticmethod
    def _hash_password(plain: str) -> str:
        return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return bcrypt.checkpw(plain.encode(), hashed.encode())

    def authenticate_password(self, db: Session, username: str, password: str) -> User | None:
        """Return User if username + password are valid, else None."""
        user = self.get_user(db, username)
        if not user or not user.is_active:
            return None
        if not self.verify_password(password, user.hashed_password):
            return None
        return user

    def update_last_login(self, db: Session, user_id: int) -> None:
        """Update the user's last_login timestamp."""
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.last_login = datetime.now(timezone.utc)
            db.commit()

    # ── TOTP ──────────────────────────────────────────────────────────────────

    def generate_totp_secret(self, db: Session, user: User) -> str:
        """Generate a new TOTP secret and store it (not yet enabled)."""
        secret = pyotp.random_base32()
        user.totp_secret = secret
        db.commit()
        return secret

    def generate_backup_codes(self, db: Session, user: User) -> list[str]:
        """
        Generate 8 one-time backup codes for account recovery.

        Plain codes are returned once and never stored — only bcrypt hashes
        are persisted. If the user loses their authenticator app, they can
        use one of these codes in place of the TOTP code.
        """
        import secrets as _secrets
        plain_codes  = [_secrets.token_hex(4).upper() for _ in range(8)]  # e.g. "A3F2B1C8"
        hashed_codes = [self._hash_password(c) for c in plain_codes]
        user.backup_codes = hashed_codes
        db.commit()
        logger.info("Backup codes generated for user '%s'", user.username)
        return plain_codes

    def verify_backup_code(self, db: Session, user: User, code: str) -> bool:
        """Verify and consume a backup code (one-time use)."""
        if not user.backup_codes:
            return False
        for i, hashed in enumerate(user.backup_codes):
            if self.verify_password(code.upper(), hashed):
                # Consume the code — remove it from the list
                remaining = [h for j, h in enumerate(user.backup_codes) if j != i]
                user.backup_codes = remaining
                db.commit()
                logger.warning("Backup code used for user '%s' — %d remaining", user.username, len(remaining))
                return True
        return False

    def get_totp_uri(self, user: User) -> str:
        """Return the otpauth:// URI to encode as a QR code."""
        if not user.totp_secret:
            raise ConfigurationError("TOTP secret not generated yet")
        return pyotp.totp.TOTP(user.totp_secret).provisioning_uri(
            name=user.username,
            issuer_name=settings.totp_issuer,
        )

    def get_totp_qr_data_uri(self, user: User) -> str:
        """Generate a base64 PNG QR code for the frontend to render as <img>."""
        uri = self.get_totp_uri(user)
        img = qrcode.make(uri)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        b64 = base64.b64encode(buf.getvalue()).decode()
        return f"data:image/png;base64,{b64}"

    def verify_totp(self, user: User, code: str) -> bool:
        """Verify a 6-digit TOTP code. Allows 1 window (30s) of drift."""
        if not user.totp_secret:
            return False
        totp = pyotp.TOTP(user.totp_secret)
        return totp.verify(code, valid_window=1)

    def enable_totp(self, db: Session, user: User, code: str) -> bool:
        """Verify code against the pending secret and mark TOTP as enabled."""
        if not self.verify_totp(user, code):
            return False
        user.totp_enabled = True
        db.commit()
        logger.info("TOTP enabled for user '%s'", user.username)
        return True

    # ── JWT ───────────────────────────────────────────────────────────────────

    def create_token(self, user_id: int, token_type: TokenType) -> str:
        """Issue a signed JWT of the given type."""
        if token_type == TokenType.ACCESS:
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt_access_token_expire_minutes
            )
        elif token_type == TokenType.REFRESH:
            expire = datetime.now(timezone.utc) + timedelta(
                days=settings.jwt_refresh_token_expire_days
            )
        else:  # TEMP
            expire = datetime.now(timezone.utc) + timedelta(
                minutes=settings.jwt_temp_token_expire_minutes
            )

        payload = {
            "sub":  str(user_id),
            "type": token_type.value,
            "exp":  expire,
        }
        return jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

    def decode_token(self, token: str, expected_type: TokenType) -> dict:
        """Decode and validate a JWT. Raises JWTError on any failure."""
        payload = jwt.decode(
            token,
            settings.jwt_secret_key,
            algorithms=[settings.jwt_algorithm],
        )
        if payload.get("type") != expected_type.value:
            raise JWTError(f"Expected token type '{expected_type.value}'")
        return payload

    def record_login(self, db: Session, user: User) -> None:
        user.last_login = datetime.now(timezone.utc)
        db.commit()


auth_service = AuthService()
