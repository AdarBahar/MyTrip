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


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    token_type: str = "bearer"
    user: UserProfile


class CurrentUser(BaseModel):
    """Current user schema for dependency injection"""
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str
    status: str
