"""
Enhanced authentication system with JWT support and backward compatibility
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.core.jwt import (
    get_user_id_from_token,
    is_fake_token,
    extract_user_id_from_fake_token,
    verify_token
)
from app.models.user import User

async def get_token_from_header(authorization: str = Header(None)) -> str:
    """Extract token from Authorization header"""
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    try:
        scheme, token = authorization.split()
        if scheme != "Bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use Bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_jwt(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token with fake token fallback"""
    
    # Handle fake tokens for backward compatibility
    if is_fake_token(token):
        user_id = extract_user_id_from_fake_token(token)
    else:
        # Handle JWT tokens
        try:
            user_id = get_user_id_from_token(token)
        except HTTPException:
            # If JWT validation fails, try fake token as fallback
            if token.startswith("fake_token_"):
                user_id = extract_user_id_from_fake_token(token)
            else:
                raise
    
    # Get user from database
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active (if field exists)
    if hasattr(user, 'is_active') and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

async def get_current_user_optional_jwt(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from token, but don't raise error if not authenticated"""
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme != "Bearer":
            return None

        # Handle both fake tokens and JWT
        if is_fake_token(token):
            user_id = extract_user_id_from_fake_token(token)
        else:
            try:
                user_id = get_user_id_from_token(token)
            except HTTPException:
                # If JWT validation fails, try fake token as fallback
                if token.startswith("fake_token_"):
                    user_id = extract_user_id_from_fake_token(token)
                else:
                    return None
        
        user = db.query(User).filter(User.id == user_id).first()
        
        # Only return user if active
        if user and (not hasattr(user, 'is_active') or user.is_active):
            return user
        return None
        
    except Exception:
        return None

def validate_token_type(token: str) -> str:
    """Validate and return token type (jwt or fake)"""
    if is_fake_token(token):
        return "fake"
    else:
        try:
            verify_token(token)
            return "jwt"
        except HTTPException:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token format",
                headers={"WWW-Authenticate": "Bearer"},
            )

def get_user_id_from_any_token(token: str) -> str:
    """Get user ID from either JWT or fake token"""
    if is_fake_token(token):
        return extract_user_id_from_fake_token(token)
    else:
        return get_user_id_from_token(token)
