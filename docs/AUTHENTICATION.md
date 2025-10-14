# MyTrips Authentication System

This document describes the authentication system implemented in the MyTrips backend API.

## Overview

The authentication system uses JWT (JSON Web Tokens) with bcrypt password hashing for secure user authentication. Users must exist in the database with valid password hashes to authenticate.

## Features

- ✅ **JWT Token Authentication** - Secure token-based authentication
- ✅ **bcrypt Password Hashing** - Industry-standard password security
- ✅ **Database User Validation** - Only existing users can login
- ✅ **Password Verification** - Proper password validation against hashes
- ✅ **Token Expiration** - Configurable token expiration times
- ✅ **Error Handling** - Proper error responses for invalid credentials

## Authentication Flow

1. **User Login**: POST `/auth/login` with email and password
2. **Credential Validation**: System validates user exists and password is correct
3. **Token Generation**: JWT access token is generated and returned
4. **Protected Access**: Include token in Authorization header for protected endpoints

## API Endpoints

### Login
```http
POST /auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "user_password"
}
```

**Response (Success):**
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh_token": null,
  "token_type": "bearer",
  "expires_in": null,
  "user": {
    "id": "01K7EMEGZ66NEG0JV1JB30REA3",
    "email": "user@example.com",
    "display_name": "User Name",
    "status": "active"
  }
}
```

**Response (Error):**
```json
{
  "error": {
    "error_code": "AUTHENTICATION_REQUIRED",
    "message": "Invalid email or password",
    "details": null,
    "field_errors": null,
    "suggestions": [
      "Include a valid Bearer token in the Authorization header",
      "Ensure your token has not expired",
      "Contact support if you continue to have authentication issues"
    ]
  },
  "timestamp": "2025-10-14T10:07:31Z",
  "request_id": "d56e84bb-c602-47d3-8e57-13fd8fc9db4e",
  "path": "/auth/login"
}
```

### Get Current User
```http
GET /auth/me
Authorization: Bearer <access_token>
```

### Logout
```http
POST /auth/logout
Authorization: Bearer <access_token>
```

## Using Authentication

### 1. Login and Get Token
```bash
curl -X POST "https://mytrips-api.bahar.co.il/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'
```

### 2. Use Token for Protected Endpoints
```bash
curl -X GET "https://mytrips-api.bahar.co.il/trips/" \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
```

## Configuration

### Environment Variables

```bash
# JWT Configuration
APP_SECRET=your-super-secure-secret-key-change-this-in-production-min-32-chars
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

### Database Schema

The `users` table includes:
- `id` - Unique user identifier (ULID)
- `email` - User email address (unique)
- `display_name` - User's display name
- `password_hash` - bcrypt hashed password
- `status` - User status (ACTIVE, INACTIVE, SUSPENDED)
- `created_at` - Account creation timestamp
- `updated_at` - Last update timestamp

## Production Users

Default production users are created during deployment:

| Email | Password | Role |
|-------|----------|------|
| `test@example.com` | `password123` | Test User |
| `adar.bahar@gmail.com` | `admin123` | Admin |
| `admin@mytrips.com` | `admin123` | Admin |

**⚠️ Important**: Change these passwords in production!

## Security Features

### Password Hashing
- Uses bcrypt with salt for password hashing
- Passwords are never stored in plain text
- Hash verification is constant-time to prevent timing attacks

### JWT Tokens
- Tokens include user ID, expiration time, and token type
- Tokens are signed with a secret key
- Configurable expiration times
- Stateless authentication (no server-side session storage)

### Error Handling
- Generic error messages to prevent user enumeration
- Proper HTTP status codes
- Detailed logging for debugging (server-side only)

## Development

### Creating Users
```python
from app.core.jwt import get_password_hash
from app.models.user import User, UserStatus

# Hash password
password_hash = get_password_hash("user_password")

# Create user
user = User(
    email="user@example.com",
    display_name="User Name",
    password_hash=password_hash,
    status=UserStatus.ACTIVE
)
```

### Testing Authentication
```python
from app.core.jwt import create_access_token, verify_password

# Create token
token = create_access_token(data={"sub": "user_id"})

# Verify password
is_valid = verify_password("plain_password", "hashed_password")
```

## Deployment

### 1. Run Database Migrations
```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 2. Create Production Users
```bash
python scripts/create_production_users.py
```

### 3. Configure Environment
Ensure all JWT environment variables are set in `.env.production`

### 4. Test Authentication
```bash
curl -X POST "https://mytrips-api.bahar.co.il/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "password": "password123"}'
```

## Troubleshooting

### Common Issues

1. **"Invalid email or password"**
   - Check user exists in database
   - Verify password is correct
   - Check user status is ACTIVE

2. **"User account not properly configured"**
   - User exists but has no password_hash
   - Run user creation script to set passwords

3. **"Token has expired"**
   - Token has exceeded expiration time
   - Login again to get new token

4. **"Could not validate credentials"**
   - Invalid token format
   - Token signature verification failed
   - Check APP_SECRET configuration

### Debugging

```bash
# Check user in database
mysql -h host -u user -p database -e "SELECT id, email, display_name, status FROM users WHERE email = 'user@example.com';"

# Test JWT functions
python -c "
from app.core.jwt import create_access_token, verify_token
token = create_access_token(data={'sub': 'test'})
payload = verify_token(token)
print('Token test:', payload)
"

# Check backend logs
sudo journalctl -u dayplanner-backend -f
```

## Migration from Fake Tokens

The system maintains backward compatibility with fake tokens during migration:
- Fake tokens: `fake_token_<user_id>`
- JWT tokens: Standard JWT format
- Both are accepted during transition period

To fully migrate to JWT-only:
1. Update all clients to use JWT tokens
2. Remove fake token support from `app/core/auth.py`
3. Remove fake token functions from `app/core/jwt.py`
