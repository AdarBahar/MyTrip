"""
User schemas
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr

from app.models.user import UserStatus


class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    display_name: str
    status: UserStatus = UserStatus.ACTIVE


class UserCreate(UserBase):
    """Schema for creating a user"""
    pass


class UserUpdate(BaseModel):
    """Schema for updating a user"""
    display_name: str = None
    status: UserStatus = None


class User(UserBase):
    """User schema"""
    id: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
