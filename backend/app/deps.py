from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from .core.security import decode_token
from .db.session import get_db
from .db.models import User
from typing import Optional

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    # 调试日志：打印接收到的认证信息
    print(f"[DEBUG] get_current_user - credentials: {credentials}")
    if credentials:
        print(f"[DEBUG] get_current_user - credentials.credentials: {credentials.credentials[:20]}...")
    
    if credentials is None or not credentials.credentials:
        print(f"[DEBUG] get_current_user - 认证失败：credentials={credentials}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid token",
        )

    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
        print(f"[DEBUG] get_current_user - 解码成功：user_id={user_id}")
    except Exception as e:
        print(f"[DEBUG] get_current_user - 解码失败：{e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        print(f"[DEBUG] get_current_user - 用户不存在：user_id={user_id}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    print(f"[DEBUG] get_current_user - 验证成功：user={user.username}")
    return user


def get_current_user_from_token(request: Request, db: Session) -> Optional[User]:
    """从请求中获取当前用户（不抛出异常）"""
    from fastapi import Request
    
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None
    
    try:
        token = auth_header.replace('Bearer ', '')
        payload = decode_token(token)
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """可选认证，如果没有token则返回None"""
    if credentials is None or not credentials.credentials:
        return None
    
    try:
        payload = decode_token(credentials.credentials)
        user_id = int(payload["sub"])
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None

