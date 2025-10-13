"""
Authentication API router
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.auth import get_current_user
from app.models.user import User, UserStatus
from app.schemas.auth import LoginRequest, LoginResponse, UserProfile

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=LoginResponse)
async def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    **Login with Email Address**

    Authenticate with email address and get a JWT access token.

    **How to use:**
    1. Enter any valid email address
    2. Copy the `access_token` from the response
    3. Click the "Authorize" button in Swagger UI
    4. Enter: `Bearer <your_access_token>`
    5. Use protected endpoints with automatic authentication

    **Example:**
    - Email: `adar.bahar@gmail.com`
    - Response: `{"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", ...}`
    - Authorization: `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

    **Note:** This automatically creates a new user account if the email doesn't exist.
    """
    from app.core.jwt import create_access_token

    email = login_data.email.lower()

    # Check if user exists
    user = db.query(User).filter(User.email == email).first()

    if not user:
        # Create new user if doesn't exist
        display_name = email.split('@')[0].replace('.', ' ').title()
        user = User(
            email=email,
            display_name=display_name,
            status=UserStatus.ACTIVE
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    # Create JWT access token
    access_token = create_access_token(data={"sub": user.id})

    return LoginResponse(
        access_token=access_token,
        user=UserProfile(
            id=user.id,
            email=user.email,
            display_name=user.display_name,
            status=user.status.value
        )
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

