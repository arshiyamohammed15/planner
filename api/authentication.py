from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Set

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# Configuration
SECRET_KEY = os.environ.get("PLANNER_API_SECRET", "change-me-in-prod")
ALGORITHM = "HS256"
DEFAULT_EXPIRE_MINUTES = 60

# Auth scheme for dependency injection
http_bearer = HTTPBearer(auto_error=False)


def create_access_token(
    subject: str,
    expires_minutes: int = DEFAULT_EXPIRE_MINUTES,
    extra_claims: Optional[dict] = None,
) -> str:
    """Generate a signed JWT for the given subject."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=expires_minutes),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> dict:
    """Validate a JWT and return its payload or raise HTTP 401."""
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired"
        ) from exc
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
        ) from exc


async def auth_guard(
    credentials: HTTPAuthorizationCredentials = Depends(http_bearer),
) -> dict:
    """
    FastAPI dependency to enforce Bearer token authentication.
    Returns decoded token payload on success.
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization required"
        )
    return verify_token(credentials.credentials)


def register_auth_middleware(
    app: FastAPI, allow_paths: Optional[Iterable[str]] = None
) -> None:
    """
    Register middleware that enforces JWT auth on all routes except allowed paths.
    Supports wildcard patterns (e.g., "/tasks/*" matches "/tasks/123")
    """
    import fnmatch

    allowed: Set[str] = set(allow_paths or [])

    @app.middleware("http")
    async def auth_middleware(request: Request, call_next):
        # Let CORS preflight OPTIONS through without auth so middleware can respond.
        if request.method == "OPTIONS":
            return await call_next(request)

        # Check if path matches any allowed pattern
        path_allowed = False
        for allowed_path in allowed:
            if fnmatch.fnmatch(request.url.path, allowed_path):
                path_allowed = True
                break

        # Debug logging
        if path_allowed:
            return await call_next(request)

        authorization: str | None = request.headers.get("Authorization")
        if not authorization or not authorization.startswith("Bearer "):
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={"detail": "Authorization header missing or invalid"},
            )

        token = authorization.split(" ", 1)[1]
        verify_token(token)
        return await call_next(request)

