"""FastAPI dependencies — inject the current authenticated user into any route."""
from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.orm import Session

from app.auth.service import TokenType, auth_service
from app.core.database import get_db
from app.models.db_models import User

# Tells FastAPI + Swagger to use Bearer token in Authorization header
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Validates the JWT access token and returns the authenticated User.
    Inject into any route with: `user: User = Depends(get_current_user)`
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = credentials.credentials
        payload = auth_service.decode_token(token, TokenType.ACCESS)
        user_id = int(payload["sub"])
    except (JWTError, KeyError, ValueError):
        raise credentials_exception

    user = auth_service.get_user_by_id(db, user_id)
    if not user or not user.is_active:
        raise credentials_exception

    return user
