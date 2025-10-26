"""
Authentication dependencies and utilities
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.orm import Session

from app.core.database import get_db
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
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return token
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: Session = Depends(get_db)
) -> User:
    """Get current user from JWT token with fake token fallback"""
    from app.core.jwt import (
        get_user_id_from_token,
        is_fake_token,
        extract_user_id_from_fake_token
    )

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

    return user


async def get_current_user_optional(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from token, but don't raise error if not authenticated"""
    from app.core.jwt import (
        get_user_id_from_token,
        is_fake_token,
        extract_user_id_from_fake_token
    )

    if not authorization:
        return None

    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
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
