from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=8, max_length=256)
    email: Optional[str] = None


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=256)


class AuthResponse(BaseModel):
    token: str


class MeResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None


class TokenRefreshResponse(BaseModel):
    token: str

