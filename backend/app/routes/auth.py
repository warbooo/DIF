from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..core.security import create_access_token, hash_password, verify_password, decode_token
from ..db.session import get_db
from ..db.models import User
from ..deps import get_current_user
from ..schemas.auth import AuthResponse, LoginRequest, MeResponse, RegisterRequest, TokenRefreshResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)) -> AuthResponse:
    username = req.username.strip()
    existing = db.query(User).filter(User.username == username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")

    user = User(
        username=username,
        email=req.email,
        hashed_password=hash_password(req.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # 创建永不过期的 token（100 年）
    token = create_access_token(subject=str(user.id), expires_minutes=0)
    return AuthResponse(token=token)


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    username = req.username.strip()
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    # 创建永不过期的 token（100 年）
    token = create_access_token(subject=str(user.id), expires_minutes=0)
    return AuthResponse(token=token)


@router.get("/me", response_model=MeResponse)
def me(current_user: User = Depends(get_current_user)) -> MeResponse:
    return MeResponse(id=current_user.id, username=current_user.username, email=current_user.email)


@router.post("/refresh", response_model=TokenRefreshResponse)
def refresh_token(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> TokenRefreshResponse:
    """刷新 token（在 token 即将过期时调用）"""
    # 创建永不过期的 token
    new_token = create_access_token(subject=str(current_user.id), expires_minutes=0)
    return TokenRefreshResponse(token=new_token)

