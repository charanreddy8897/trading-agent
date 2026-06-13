"""Pydantic schemas for all auth request / response bodies."""
from __future__ import annotations

from pydantic import BaseModel


# ── Requests ──────────────────────────────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class TotpVerifyRequest(BaseModel):
    temp_token: str   # short-lived token from /auth/login
    code:       str   # 6-digit TOTP from authenticator app


class TotpSetupVerifyRequest(BaseModel):
    temp_token: str
    code:       str   # must match the newly generated secret before enabling


class RefreshRequest(BaseModel):
    refresh_token: str


# ── Responses ─────────────────────────────────────────────────────────────────

class LoginResponse(BaseModel):
    status:         str                  # "success" | "totp_required"
    temp_token:     str | None = None    # Only present when status="totp_required"
    access_token:   str | None = None    # Only present when status="success"
    refresh_token:  str | None = None    # Only present when status="success"
    token_type:     str = "bearer"


class TokenResponse(BaseModel):
    access_token:  str
    refresh_token: str
    token_type:    str = "bearer"


class TotpSetupResponse(BaseModel):
    secret:       str        # base32 secret — manual entry fallback
    otpauth_uri:  str        # scan with Google Authenticator / Authy
    qr_data_uri:  str        # data:image/png;base64,... — render as <img src="...">
    backup_codes: list[str]  # 8 one-time recovery codes — store these safely!


class UserMeResponse(BaseModel):
    id:           int
    username:     str
    totp_enabled: bool
    is_active:    bool
