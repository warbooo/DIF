from __future__ import annotations

from datetime import datetime, timedelta, timezone

import jwt
from passlib.context import CryptContext

from .settings import settings

# 使用 sha256_crypt 替代 bcrypt，避免 72 字节限制
pwd_context = CryptContext(schemes=["sha256_crypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def create_access_token(*, subject: str, expires_minutes=None) -> str:
    # 默认 7 天过期，但如果传入 0 则永不过期（通过设置一个很远的未来时间）
    if expires_minutes == 0:
        # 100 年，相当于永不过期
        expire = datetime.now(timezone.utc) + timedelta(days=36500)
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=expires_minutes if expires_minutes is not None else settings.JWT_EXPIRE_MINUTES
        )
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.JWT_SECRET, algorithm="HS256")


def decode_token(token: str) -> dict:
    return jwt.decode(token, settings.JWT_SECRET, algorithms=["HS256"])
