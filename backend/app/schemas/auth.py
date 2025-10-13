"""
Authentication schemas
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict


class UserProfile(BaseModel):
    """User profile schema"""
    id: str
    email: str
    display_name: str
    status: str


class LoginRequest(BaseModel):
    """Login request schema"""
    email: EmailStr
    password: str = Field(..., min_length=1, description="User password")


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: Optional[str] = Field(None, description="JWT refresh token")
    token_type: str = "bearer"
    expires_in: Optional[int] = Field(None, description="Token expiry time in seconds")
    user: UserProfile


class CurrentUser(BaseModel):
    """Current user schema for dependency injection"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    status: str


class RefreshRequest(BaseModel):
    """Token refresh request schema"""
    refresh_token: str = Field(..., description="JWT refresh token")


class RefreshResponse(BaseModel):
    """Token refresh response schema"""
    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry time in seconds")


class LogoutResponse(BaseModel):
    """Logout response schema"""
    message: str = Field(default="Successfully logged out", description="Logout success message")


class TokenValidationResponse(BaseModel):
    """Token validation response schema"""
    valid: bool = Field(..., description="Whether the token is valid")
    user_id: Optional[str] = Field(None, description="User ID if token is valid")
    expires_at: Optional[str] = Field(None, description="Token expiration time")
