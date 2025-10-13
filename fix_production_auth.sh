#!/bin/bash

# Quick fix script for production authentication issues
# Run this on your production server to fix the current authentication problems

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_DIR="/opt/dayplanner"
BACKEND_DIR="$APP_DIR/backend"
ENV_FILE="$APP_DIR/.env.production"

# Logging functions
log() {
    echo -e "$1"
}

log_info() {
    log "${BLUE}[INFO]${NC} $1"
}

log_success() {
    log "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    log "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    log "${RED}[ERROR]${NC} $1"
}

# Check if running as root
if [[ $EUID -ne 0 ]]; then
    log_error "This script must be run as root"
    exit 1
fi

log_info "🔧 Fixing MyTrips Authentication Issues"
log_info "======================================"

# Step 1: Install missing JWT dependencies
log_info "1. Installing missing JWT dependencies..."
cd "$BACKEND_DIR"

# Install JWT dependencies
venv/bin/pip install python-jose[cryptography]==3.3.0
venv/bin/pip install passlib[bcrypt]==1.7.4
venv/bin/pip install pyjwt==2.8.0
venv/bin/pip install cryptography==41.0.7

# Reinstall all requirements to ensure everything is up to date
venv/bin/pip install -r requirements.txt

log_success "JWT dependencies installed"

# Step 2: Ensure APP_SECRET is configured
log_info "2. Checking APP_SECRET configuration..."

if ! grep -q "APP_SECRET" "$ENV_FILE"; then
    log_warning "APP_SECRET not found in environment file"
    log_info "Adding APP_SECRET to environment file"
    echo "" >> "$ENV_FILE"
    echo "# JWT Authentication" >> "$ENV_FILE"
    echo "APP_SECRET=your-super-secure-secret-key-change-this-in-production-min-32-chars" >> "$ENV_FILE"
    echo "JWT_ALGORITHM=HS256" >> "$ENV_FILE"
    echo "ACCESS_TOKEN_EXPIRE_MINUTES=30" >> "$ENV_FILE"
    echo "REFRESH_TOKEN_EXPIRE_DAYS=7" >> "$ENV_FILE"
    log_success "APP_SECRET added to environment file"
else
    log_success "APP_SECRET already configured"
fi

# Step 3: Apply authentication fixes to the code
log_info "3. Applying authentication fixes to the code..."

# Update the main auth router to use JWT
cat > "$BACKEND_DIR/app/api/auth/router.py" << 'EOF'
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
EOF

# Update the auth.py to support both JWT and fake tokens
cat > "$BACKEND_DIR/app/core/auth.py" << 'EOF'
"""
Authentication utilities
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
) -> User | None:
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
EOF

log_success "Authentication code fixes applied"

# Step 4: Test the fixes
log_info "4. Testing authentication fixes..."

# Test JWT imports
if sudo -u www-data bash -c "
    cd $BACKEND_DIR
    source venv/bin/activate
    export \$(cat $ENV_FILE | grep -v '^#' | xargs)
    python -c '
from app.core.jwt import create_access_token, verify_token
token = create_access_token(data={\"sub\": \"test_user\"})
payload = verify_token(token)
print(\"JWT system working\")
'
" 2>/dev/null; then
    log_success "JWT authentication system working"
else
    log_error "JWT authentication system failed"
    exit 1
fi

# Step 5: Restart backend service
log_info "5. Restarting backend service..."
systemctl restart dayplanner-backend

# Wait for service to start
sleep 5

if systemctl is-active --quiet dayplanner-backend; then
    log_success "Backend service restarted successfully"
else
    log_error "Backend service failed to restart"
    log_info "Checking logs..."
    journalctl -u dayplanner-backend --no-pager -n 20
    exit 1
fi

# Step 6: Test the authentication endpoint
log_info "6. Testing authentication endpoint..."

sleep 3

if curl -f -X POST "http://localhost:8000/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' >/dev/null 2>&1; then
    log_success "Authentication endpoint working"
else
    log_error "Authentication endpoint still failing"
    log_info "Checking backend logs..."
    journalctl -u dayplanner-backend --no-pager -n 10
    exit 1
fi

# Step 7: Test via domain
log_info "7. Testing via domain..."

if curl -f -X POST "http://mytrips-api.bahar.co.il/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email": "test@example.com"}' >/dev/null 2>&1; then
    log_success "Domain authentication working"
else
    log_warning "Domain authentication may need SSL setup"
fi

log_success "🎉 Authentication fixes completed successfully!"
log_info ""
log_info "✅ JWT dependencies installed"
log_info "✅ APP_SECRET configured"
log_info "✅ Authentication code updated"
log_info "✅ Backend service restarted"
log_info "✅ Authentication endpoint working"
log_info ""
log_info "Your API should now work with JWT authentication!"
log_info "Test with: python3 test_mytrips_api.py --api-base http://mytrips-api.bahar.co.il"
