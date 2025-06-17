from pydantic import BaseModel
from typing import Optional
from .user_schema import UserResponse


class TokenData(BaseModel):
    user_id: Optional[int] = None


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class TokenResponse(BaseModel):
    access_token: Optional[str] = None
    token_type: str = "bearer"
    expires_in: Optional[int] = None  # access_token expiration in seconds
    refresh_token: Optional[str] = None
    refresh_token_expires_in: Optional[int] = None  # refresh_token expiration in seconds
    user: Optional[UserResponse] = None
    message: Optional[str] = None  # For non-token responses like password reset confirmation


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AccessTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str


class LogoutResponse(BaseModel):
    message: str
