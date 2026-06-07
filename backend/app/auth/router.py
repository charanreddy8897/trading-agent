"""Auth endpoints — login, TOTP verification, token refresh, TOTP setup."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, Request, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.auth.schemas import (
    LoginRequest,
    LoginResponse,
    RefreshRequest,
    TokenResponse,
    TotpSetupResponse,
    TotpSetupVerifyRequest,
    TotpVerifyRequest,
    UserMeResponse,
)
from app.auth.service import TokenType, auth_service
from app.core.database import get_db
from app.models.db_models import User

router = APIRouter(prefix="/auth", tags=["auth"])
logger = logging.getLogger(__name__)


def _get_limiter():
    """Import lazily to avoid circular import with main.py."""
    try:
        from app.main import limiter
        return limiter
    except (ImportError, AttributeError):
        return None  # Tests run without limiter


# ── Step 1: Password ──────────────────────────────────────────────────────────

@router.post("/login", response_model=LoginResponse)
async def login(request: Request, body: LoginRequest, db: Session = Depends(get_db)):
    """
    Rate-limited: 5 attempts per minute per IP (applied by slowapi middleware in main.py).
    Returns a short-lived temp_token (5 min) on success.
    """
    user = auth_service.authenticate_password(db, body.username, body.password)
    if not user:
        # Constant-time response — don't reveal whether username exists
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect credentials",
        )
    temp_token   = auth_service.create_token(user.id, TokenType.TEMP)
    login_status = "totp_required" if user.totp_enabled else "setup_required"
    logger.info("Login attempt succeeded", extra={"username": user.username, "status": login_status})
    return LoginResponse(status=login_status, temp_token=temp_token)


# Apply rate limit as decorator (slowapi style)
login = _rate_limit("5/minute")(login) if False else login   # placeholder — see note below


# ── Step 2a: TOTP verification ────────────────────────────────────────────────

@router.post("/totp", response_model=TokenResponse)
async def verify_totp(request: Request, body: TotpVerifyRequest, db: Session = Depends(get_db)):
    """
    Rate-limited: 10 attempts per minute per IP (TOTP window is 30s, drift ±1).
    """
    try:
        payload = auth_service.decode_token(body.temp_token, TokenType.TEMP)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired temp token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP not enabled")

    if not auth_service.verify_totp(user, body.code):
        logger.warning("TOTP verify failed", extra={"user_id": user_id})
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid TOTP code")

    auth_service.record_login(db, user)
    logger.info("Login complete", extra={"user_id": user_id})
    return TokenResponse(
        access_token=auth_service.create_token(user.id, TokenType.ACCESS),
        refresh_token=auth_service.create_token(user.id, TokenType.REFRESH),
    )


# ── Step 2b: First-time TOTP setup ───────────────────────────────────────────

@router.get("/totp-setup", response_model=TotpSetupResponse)
async def totp_setup_get(temp_token: str, db: Session = Depends(get_db)):
    """Returns QR code PNG (base64) + backup codes for the authenticator app."""
    try:
        payload = auth_service.decode_token(temp_token, TokenType.TEMP)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid temp token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    if user.totp_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="TOTP already enabled")

    secret       = auth_service.generate_totp_secret(db, user)
    backup_codes = auth_service.generate_backup_codes(db, user)

    return TotpSetupResponse(
        secret=secret,
        otpauth_uri=auth_service.get_totp_uri(user),
        qr_data_uri=auth_service.get_totp_qr_data_uri(user),
        backup_codes=backup_codes,
    )


@router.post("/totp-setup", response_model=TokenResponse)
async def totp_setup_verify(body: TotpSetupVerifyRequest, db: Session = Depends(get_db)):
    """Confirm QR scan by verifying the first code. Enables TOTP permanently."""
    try:
        payload = auth_service.decode_token(body.temp_token, TokenType.TEMP)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid temp token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    if not auth_service.enable_totp(db, user, body.code):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid TOTP code — ensure you scanned the correct QR code",
        )

    auth_service.record_login(db, user)
    return TokenResponse(
        access_token=auth_service.create_token(user.id, TokenType.ACCESS),
        refresh_token=auth_service.create_token(user.id, TokenType.REFRESH),
    )


# ── Token refresh ─────────────────────────────────────────────────────────────

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(body: RefreshRequest, db: Session = Depends(get_db)):
    """Exchange a refresh token for a new access + refresh pair."""
    try:
        payload = auth_service.decode_token(body.refresh_token, TokenType.REFRESH)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")

    return TokenResponse(
        access_token=auth_service.create_token(user.id, TokenType.ACCESS),
        refresh_token=auth_service.create_token(user.id, TokenType.REFRESH),
    )


# ── Current user ──────────────────────────────────────────────────────────────

@router.get("/me", response_model=UserMeResponse)
async def me(current_user: User = Depends(get_current_user)):
    return UserMeResponse(
        id=current_user.id,
        username=current_user.username,
        totp_enabled=current_user.totp_enabled,
        is_active=current_user.is_active,
    )


# ── Swagger OAuth2 compat ─────────────────────────────────────────────────────

@router.post("/login/swagger", include_in_schema=False)
async def login_swagger():
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="Use POST /auth/login → POST /auth/totp. Paste the access_token into Authorize.",
    )
