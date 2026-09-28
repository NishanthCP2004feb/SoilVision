from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.dependencies import current_user
from app.core.database import get_db
from app.core.security import hash_password, issue_token, verify_password
from app.models import User
from app.schemas.common import ApiResponse
from app.schemas.domain import LoginRequest, RegisterRequest, TokenData

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=ApiResponse[TokenData], status_code=status.HTTP_201_CREATED)
def register(request: RegisterRequest, db: Session = Depends(get_db)) -> ApiResponse[TokenData]:
    if db.scalar(select(User).where(User.email == request.email.lower())):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email is already registered")
    user = User(email=request.email.lower(), password_hash=hash_password(request.password))
    db.add(user); db.commit(); db.refresh(user)
    return ApiResponse(data=TokenData(access_token=issue_token(user.id)), message="Registration completed")


@router.post("/login", response_model=ApiResponse[TokenData])
def login(request: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse[TokenData]:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if user is None or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return ApiResponse(data=TokenData(access_token=issue_token(user.id)), message="Login completed")


@router.get("/me", response_model=ApiResponse[dict])
def me(user: User = Depends(current_user)) -> ApiResponse[dict]:
    return ApiResponse(data={"id": user.id, "email": user.email}, message="Current user")


@router.post("/logout", response_model=ApiResponse[dict])
def logout(user: User = Depends(current_user)) -> ApiResponse[dict]:
    return ApiResponse(data={"message": "Logged out"}, message="Logout completed")
