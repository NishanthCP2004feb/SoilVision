from __future__ import annotations

from typing import Optional

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import token_subject
from app.models import User

# In demo mode the bearer token is optional; in production it is required.
bearer = HTTPBearer(auto_error=not settings.demo_mode)

# Cache only the demo user's primary-key (a plain string), never the ORM
# instance, so we never hit a DetachedInstanceError across requests.
_demo_user_id: str | None = None


def _get_or_create_demo_user(db: Session) -> User:
    """Return (or create) the demo user, re-loading it from the current session."""
    global _demo_user_id

    # Fast path: we already know the PK — just fetch from the current session.
    if _demo_user_id is not None:
        user = db.get(User, _demo_user_id)
        if user is not None:
            return user

    # Look for an existing demo user row.
    from sqlalchemy import select
    user = db.scalar(select(User).where(User.email == "demo@soilwise.local"))
    if user is not None:
        _demo_user_id = user.id
        return user

    # First-ever call: create the demo user.
    from app.core.security import hash_password
    user = User(email="demo@soilwise.local", password_hash=hash_password("demo"))
    db.add(user)
    db.commit()
    db.refresh(user)
    _demo_user_id = user.id
    return user


def current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    # In demo mode, if no credentials were provided, return the demo user.
    if credentials is None:
        if settings.demo_mode:
            return _get_or_create_demo_user(db)
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")

    # Try to validate the token
    try:
        user_id = token_subject(credentials.credentials)
        user = db.get(User, user_id)
        if user is not None:
            return user
        # User no longer exists in DB
        if settings.demo_mode:
            return _get_or_create_demo_user(db)
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Account no longer exists")
    except Exception:
        # Token is invalid or expired — in demo mode, fall back to demo user
        if settings.demo_mode:
            return _get_or_create_demo_user(db)
        raise
