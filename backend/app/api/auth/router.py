"""
Authentication API router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.core.config import settings
from app.models.user import User, UserStatus
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile, AppLoginRequest, AppLoginResponse

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    authorization: str = Header(None),
    db: Session = Depends(get_db)
):
    """
    Login endpoint:
    - Production: requires Authorization: Bearer <APP_SECRET> AND valid email/password.
                  Returns a real JWT access token (and refresh token).
    - Dev/Test: email-only login for convenience (auto-creates user, returns fake token).
    """
    # Production flow: guarded by APP_SECRET header and email/password verification
    if settings.APP_ENV.lower() == "production":
        # Validate client Authorization header matches APP_SECRET
        if not authorization:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authorization header missing"
            )
        try:
            scheme, token = authorization.split()
            if scheme != "Bearer":
                raise ValueError("invalid scheme")
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authorization header format. Use 'Bearer <token>'"
            )
        if token != settings.APP_SECRET:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid client authorization"
            )

        # Require email/password auth
        from app.core.jwt import (
            create_access_token,
            create_refresh_token,
            verify_password,
            ACCESS_TOKEN_EXPIRE_MINUTES,
        )

        email = login_data.email.lower()
        user = db.query(User).filter(User.email == email).first()
        if not user or user.status != UserStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

        if not (getattr(user, "password_hash", None) and login_data.password and verify_password(login_data.password, user.password_hash)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )

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
                status=user.status.value,
            ),
        )

    # Dev/Test fallback: email-only fake-token login for local testing
    import re
    from app.core.jwt import create_fake_token_for_testing as create_fake_token

    email = login_data.email.lower()

    # Find or create user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Generate display name from email local-part
        local = email.split("@")[0]
        parts = [p for p in re.split(r"[._-]+", local) if p]
        display = " ".join([p.capitalize() for p in parts]) or email
        user = User(email=email, display_name=display, status=UserStatus.ACTIVE)
        db.add(user)
        db.commit()
        db.refresh(user)

    access_token = create_fake_token(user.id)

    return LoginResponse(
        access_token=access_token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status.value,
        ),
    )


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user)
):
    """
    **Get Current User Profile**

    Returns the profile information for the currently authenticated user.

    **Requires Authentication:** You must include a valid Bearer token in the Authorization header.

    **How to authenticate:**
    1. First login using `/auth/login` to get your token
    2. Click the "Authorize" button and enter: `Bearer <your_token>`
    3. This endpoint will then return your user profile
    """
    return UserProfile(
        id=current_user.id,
        email=current_user.email,
        display_name=current_user.display_name,
        status=current_user.status.value
    )


@router.post("/app-login", response_model=AppLoginResponse)
async def app_login(
    login_data: AppLoginRequest,
    db: Session = Depends(get_db)
):
    """
    **Simple App Login**

    Simple authentication endpoint for apps that returns authenticated/not authenticated
    without token management. Validates email and password against the user database.

    **Features:**
    - No JWT token generation or management
    - Simple boolean response (authenticated: true/false)
    - Returns user ID on successful authentication
    - Validates against hashed passwords in database
    - Checks user account status (must be ACTIVE)

    **Use Cases:**
    - Mobile apps with their own session management
    - Simple authentication checks
    - Legacy systems that don't use JWT tokens
    - Quick authentication validation

    **Request Body:**
    ```json
    {
      "email": "user@example.com",
      "password": "user_password"
    }
    ```

    **Response:**
    ```json
    {
      "authenticated": true,
      "user_id": "01K5P68329YFSCTV777EB4GM9P",
      "message": "Authentication successful"
    }
    ```

    **Error Response:**
    ```json
    {
      "authenticated": false,
      "user_id": null,
      "message": "Invalid email or password"
    }
    ```
    """
    try:
        email = login_data.email.lower()

        # Find user by email
        user = db.query(User).filter(User.email == email).first()

        if not user:
            return AppLoginResponse(
                authenticated=False,
                user_id=None,
                message="Invalid email or password"
            )

        # Check if user is active
        if user.status != UserStatus.ACTIVE:
            return AppLoginResponse(
                authenticated=False,
                user_id=None,
                message="User account is disabled"
            )

        # Check if user has a password hash
        if not hasattr(user, 'password_hash') or not user.password_hash:
            return AppLoginResponse(
                authenticated=False,
                user_id=None,
                message="User account not properly configured"
            )

        # Verify password
        from app.core.jwt import verify_password
        if not verify_password(login_data.password, user.password_hash):
            return AppLoginResponse(
                authenticated=False,
                user_id=None,
                message="Invalid email or password"
            )

        # Authentication successful
        return AppLoginResponse(
            authenticated=True,
            user_id=user.id,
            message="Authentication successful"
        )

    except Exception as e:
        # Log error for debugging but don't expose details
        print(f"App login error for email {login_data.email}: {e}")
        return AppLoginResponse(
            authenticated=False,
            user_id=None,
            message="Authentication failed"
        )


@router.post("/logout")
async def logout():
    """
    **Logout**

    Logout endpoint for completeness. Since tokens are stateless in this development system,
    this endpoint simply returns a success message.

    **Note:** In a production system, this would invalidate the token server-side.
    For this development system, simply remove the token from your client storage.
    """
    return {"message": "Successfully logged out"}

