"""
Authentication dependencies and utilities
"""
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
    """Get current user from fake token"""
    if not token or not token.startswith("fake_token_"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract user ID from fake token
    try:
        user_id = token.replace("fake_token_", "")
        user = db.query(User).filter(User.id == user_id).first()
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return user
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token format",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user_optional(
    authorization: str = Header(None),
    db: Session = Depends(get_db)
) -> User | None:
    """Get current user from token, but don't raise error if not authenticated"""
    if not authorization:
        return None
    
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer" or not token.startswith("fake_token_"):
            return None
        
        user_id = token.replace("fake_token_", "")
        user = db.query(User).filter(User.id == user_id).first()
        return user
    except Exception:
        return None
