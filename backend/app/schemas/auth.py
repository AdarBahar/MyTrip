"""
Authentication schemas
"""
from typing import Optional
from pydantic import BaseModel, Field, EmailStr


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
    id: str
    email: str
    display_name: str
    status: str

    class Config:
        from_attributes = True
