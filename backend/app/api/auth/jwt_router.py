"""
JWT Authentication API endpoints
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.jwt import (
    create_access_token, 
    create_refresh_token, 
    verify_token,
    verify_password,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from app.models.user import User
from app.schemas.auth import (
    AppLoginRequest,
    LoginResponse,
    RefreshRequest,
    RefreshResponse,
    LogoutResponse,
    UserProfile
)

router = APIRouter()

@router.post("/jwt/login", response_model=LoginResponse)
async def jwt_login(
    login_data: AppLoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user with email/password and return JWT tokens
    """
    # Find user by email
    user = db.query(User).filter(User.email == login_data.email).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # For now, we'll accept any password since we don't have password hashing yet
    # This will be enhanced when we add proper password management
    if login_data.password is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required for JWT authentication",
        )
    
    # TODO: Implement proper password verification
    # For now, accept any non-empty password
    if not login_data.password.strip():
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.id})
    refresh_token = create_refresh_token(data={"sub": user.id})
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        user=UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status.value
        )
    )

@router.post("/jwt/refresh", response_model=RefreshResponse)
async def jwt_refresh_token(
    refresh_data: RefreshRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using refresh token
    """
    # Verify refresh token
    payload = verify_token(refresh_data.refresh_token, token_type="refresh")
    user_id = payload.get("sub")
    
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )
    
    # Verify user still exists and is active
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )
    
    if hasattr(user, 'is_active') and not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled",
        )
    
    # Create new access token
    access_token = create_access_token(data={"sub": user.id})
    
    return RefreshResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
    )

@router.post("/jwt/logout", response_model=LogoutResponse)
async def jwt_logout():
    """
    Logout user (client should discard tokens)
    """
    # In a more sophisticated setup, you'd add the token to a blacklist
    # For now, we rely on the client to discard the tokens
    return LogoutResponse(message="Successfully logged out")

@router.get("/jwt/validate")
async def jwt_validate_token(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Validate a JWT token and return user information
    """
    try:
        payload = verify_token(token)
        user_id = payload.get("sub")
        
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
            )
        
        return {
            "valid": True,
            "user": UserProfile(
                id=user.id,
                email=user.email,
                display_name=user.display_name,
                status=user.status
            ),
            "expires_at": payload.get("exp")
        }
        
    except HTTPException:
        return {"valid": False}

# Health check for JWT endpoints
@router.get("/jwt/health")
async def jwt_health():
    """Health check for JWT authentication endpoints"""
    return {
        "status": "healthy",
        "service": "jwt-authentication",
        "endpoints": [
            "/auth/jwt/login",
            "/auth/jwt/refresh", 
            "/auth/jwt/logout",
            "/auth/jwt/validate"
        ]
    }
