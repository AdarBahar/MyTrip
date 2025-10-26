# 🔐 App Login Endpoint Guide

## 📋 **Overview**

A simple authentication endpoint for apps that returns authenticated/not authenticated without token management. This endpoint validates email and password against the user database and returns a simple boolean response.

## 🚀 **Endpoint Details**

### **URL**
```
POST /auth/app-login
```

### **Request Body**
```json
{
  "email": "user@example.com",
  "password": "user_password"
}
```

### **Response Format**
```json
{
  "authenticated": true,
  "user_id": "01K5P68329YFSCTV777EB4GM9P",
  "message": "Authentication successful"
}
```

## 🎯 **Features**

- ✅ **No JWT token generation or management**
- ✅ **Simple boolean response (authenticated: true/false)**
- ✅ **Returns user ID on successful authentication**
- ✅ **Validates against hashed passwords in database**
- ✅ **Checks user account status (must be ACTIVE)**
- ✅ **Generic error messages to prevent user enumeration**
- ✅ **Graceful error handling**
- ✅ **No session management required**

## 📝 **Request Schema**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string (email) | Yes | User's email address |
| `password` | string | Yes | User's password (minimum 1 character) |

## 📤 **Response Schema**

| Field | Type | Description |
|-------|------|-------------|
| `authenticated` | boolean | Whether authentication was successful |
| `user_id` | string or null | User ID if authenticated, null otherwise |
| `message` | string | Authentication result message |

## 🔍 **Response Examples**

### **Successful Authentication**
```json
{
  "authenticated": true,
  "user_id": "01K5P68329YFSCTV777EB4GM9P",
  "message": "Authentication successful"
}
```

### **Invalid Credentials**
```json
{
  "authenticated": false,
  "user_id": null,
  "message": "Invalid email or password"
}
```

### **Disabled Account**
```json
{
  "authenticated": false,
  "user_id": null,
  "message": "User account is disabled"
}
```

### **Account Not Configured**
```json
{
  "authenticated": false,
  "user_id": null,
  "message": "User account not properly configured"
}
```

### **General Error**
```json
{
  "authenticated": false,
  "user_id": null,
  "message": "Authentication failed"
}
```

## 🛠️ **Implementation Details**

### **Authentication Flow**
1. **Email Validation**: Checks if user exists in database
2. **Account Status Check**: Ensures user status is ACTIVE
3. **Password Hash Check**: Verifies user has a password hash configured
4. **Password Verification**: Uses bcrypt to verify password against hash
5. **Response Generation**: Returns authentication result

### **Security Features**
- **Password Hashing**: Uses bcrypt for secure password storage
- **Generic Error Messages**: Prevents user enumeration attacks
- **Account Status Validation**: Blocks inactive/suspended accounts
- **Exception Handling**: Graceful error handling without exposing details

## 🎯 **Use Cases**

### **Mobile Apps**
```javascript
// React Native / Mobile App
const authenticateUser = async (email, password) => {
  try {
    const response = await fetch('https://mytrips-api.bahar.co.il/auth/app-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    const result = await response.json();
    
    if (result.authenticated) {
      // Store user_id in local storage or state
      await AsyncStorage.setItem('user_id', result.user_id);
      return { success: true, userId: result.user_id };
    } else {
      return { success: false, message: result.message };
    }
  } catch (error) {
    return { success: false, message: 'Network error' };
  }
};
```

### **Legacy Systems**
```python
# Python legacy system
import requests

def authenticate_user(email, password):
    try:
        response = requests.post(
            'https://mytrips-api.bahar.co.il/auth/app-login',
            json={'email': email, 'password': password},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            return data['authenticated'], data.get('user_id'), data['message']
        else:
            return False, None, 'Authentication failed'
    except Exception as e:
        return False, None, f'Error: {str(e)}'

# Usage
authenticated, user_id, message = authenticate_user('user@example.com', 'password')
if authenticated:
    print(f"User {user_id} authenticated successfully")
else:
    print(f"Authentication failed: {message}")
```

### **Simple Web Apps**
```javascript
// Simple JavaScript web app
async function loginUser(email, password) {
  try {
    const response = await fetch('/auth/app-login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password }),
    });
    
    const result = await response.json();
    
    if (result.authenticated) {
      // Store user info in session storage
      sessionStorage.setItem('authenticated', 'true');
      sessionStorage.setItem('user_id', result.user_id);
      window.location.href = '/dashboard';
    } else {
      document.getElementById('error').textContent = result.message;
    }
  } catch (error) {
    document.getElementById('error').textContent = 'Login failed';
  }
}
```

## 🧪 **Testing**

### **cURL Examples**
```bash
# Test valid credentials
curl -X POST "https://mytrips-api.bahar.co.il/auth/app-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "password123"}'

# Test invalid credentials
curl -X POST "https://mytrips-api.bahar.co.il/auth/app-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "wrongpassword"}'

# Test non-existent user
curl -X POST "https://mytrips-api.bahar.co.il/auth/app-login" \
  -H "Content-Type: application/json" \
  -d '{"email": "nonexistent@example.com", "password": "anypassword"}'
```

### **Expected Behavior**
- ✅ **Always returns HTTP 200** (never throws exceptions)
- ✅ **Consistent response structure** for all scenarios
- ✅ **Generic error messages** (no user enumeration)
- ✅ **Fast response times** (< 1 second)
- ✅ **Proper password verification** using bcrypt

## 🔄 **Future Enhancements**

When you're ready to add more authentication features, consider:

1. **User Registration Endpoint** (`POST /auth/app-register`)
2. **Password Reset Endpoint** (`POST /auth/app-reset-password`)
3. **Account Activation** (`POST /auth/app-activate`)
4. **Rate Limiting** (prevent brute force attacks)
5. **Account Lockout** (after failed attempts)
6. **Two-Factor Authentication** (2FA support)
7. **Session Management** (optional session tokens)

## 📚 **Related Documentation**

- **JWT Login Endpoint**: `/auth/login` (for token-based authentication)
- **User Profile Endpoint**: `/auth/me` (requires JWT token)
- **Password Hashing**: Uses bcrypt with salt rounds
- **User Model**: Includes email, password_hash, status fields
- **Database Schema**: Users table with proper indexing

## 🎉 **Ready for Production**

The app login endpoint is now deployed and ready for use:

- **Production URL**: `https://mytrips-api.bahar.co.il/auth/app-login`
- **Swagger Documentation**: `https://mytrips-api.bahar.co.il/docs`
- **Status**: ✅ Deployed and functional
- **Security**: ✅ Production-ready with proper password hashing

Start integrating this endpoint into your apps for simple, secure authentication!
