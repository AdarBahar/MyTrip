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
    **Login with Email and Password**

    Authenticate with email address and password against the production database.

    **How to use:**
    1. Enter your registered email address
    2. Enter your password (if no password field, any non-empty string for existing users)
    3. Copy the `access_token` from the response
    4. Click the "Authorize" button in Swagger UI
    5. Enter: `Bearer <your_access_token>`
    6. Use protected endpoints with automatic authentication

    **Example:**
    - Email: `adar.bahar@gmail.com`
    - Password: `your_password` (or any string if password not implemented yet)
    - Response: `{"access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...", ...}`
    - Authorization: `Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...`

    **Note:** Only existing users in the database can login. No automatic user creation.
    """
    from app.core.jwt import create_access_token

    email = login_data.email.lower()

    # Find user by email - must exist in database
    user = db.query(User).filter(User.email == email).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password. User not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is disabled.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Password validation
    if not login_data.password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password is required.",
        )

    # Check if user has a valid password hash
    if not hasattr(user, 'password_hash') or not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not properly configured. Please contact administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password with proper error handling
    try:
        from app.core.jwt import verify_password
        if not verify_password(login_data.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
    except Exception as e:
        # Handle invalid password hash format
        print(f"Password verification error for user {user.email}: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not properly configured. Please contact administrator.",
            headers={"WWW-Authenticate": "Bearer"},
        )

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

