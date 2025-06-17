# Auth Service API Documentation v1.0

**Date:** June 12, 2025  
**Service:** Authentication Service for AI EdTech Platform  
**Version:** 1.0.0  

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Rate Limiting](#rate-limiting)
4. [Endpoints](#endpoints)
5. [OAuth Integration](#oauth-integration)
6. [Error Handling](#error-handling)
7. [Integration Examples](#integration-examples)

## API Overview

### Base Configuration
- **Base URL:** `http://localhost:8000` (Development) / `https://auth-api.yourdomain.com` (Production)
- **API Version:** v1.0
- **Content Type:** `application/json`
- **Authentication:** Bearer JWT Tokens
- **Rate Limiting:** 100 requests per minute per IP address

### CORS Policy
- **Allowed Origins:** Configurable via `BACKEND_CORS_ORIGINS` environment variable
- **Development:** `http://localhost:3000`, `http://localhost:3001`
- **Allowed Methods:** `GET`, `POST`, `PUT`, `DELETE`
- **Credentials:** Allowed

### Security Headers
All responses include security headers:
- `X-Content-Type-Options: nosniff`
- `X-Frame-Options: DENY`
- `X-XSS-Protection: 1; mode=block`
- `Referrer-Policy: strict-origin-when-cross-origin`
- Content Security Policy (CSP) enabled

## Authentication

### JWT Token System
The API uses a dual-token authentication system:

#### Access Token
- **Type:** JWT Bearer Token
- **Expiration:** 30 minutes (configurable)
- **Usage:** Include in `Authorization` header as `Bearer {access_token}`
- **Claims:** `sub` (user_id), `exp` (expiration)

#### Refresh Token
- **Type:** JWT with unique identifier (JTI)
- **Expiration:** 7 days (configurable)
- **Usage:** Used to obtain new access tokens
- **Claims:** `sub` (user_id), `exp` (expiration), `jti` (unique ID for invalidation)

### Token Usage
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

## Rate Limiting

### Global Rate Limits
- **General Endpoints:** 100 requests per minute per IP
- **OTP Requests:** 5 requests per email per hour
- **OTP Verification:** 3 attempts per email per 15 minutes
- **Login Attempts:** Rate limited per email address

### Rate Limit Headers
Responses include rate limiting information:
- `X-RateLimit-Limit`: Maximum requests allowed
- `X-RateLimit-Remaining`: Remaining requests in window
- `X-RateLimit-Reset`: Time when rate limit resets

## Endpoints

### Health Check Endpoints

#### GET /
Root endpoint - Service status check.

**Response:**
```json
{
  "message": "Auth Service is running"
}
```

#### GET /health
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy"
}
```

### Authentication Endpoints

#### POST /auth/register
Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Password Requirements:**
- Minimum 8 characters, maximum 128 characters
- At least one lowercase letter
- At least one uppercase letter
- At least one digit
- At least one special character (@$!%*?&)

**Response (201 Created):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-06-12T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

#### POST /auth/login
Login with email and password.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-06-12T10:30:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### POST /auth/request-otp
Request OTP for email verification or login.

**Request Body:**
```json
{
  "email": "user@example.com",
  "purpose": "verification"
}
```

**Purpose Options:**
- `verification` - Email verification
- `login` - OTP-based login
- `password_reset` - Password reset

**Response (200 OK):**
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/request-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "purpose": "verification"
  }'
```

#### POST /auth/verify-otp
Verify OTP and receive access tokens.

**Request Body:**
```json
{
  "email": "user@example.com",
  "otp_code": "123456",
  "purpose": "verification"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-06-12T10:30:00Z"
  }
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/verify-otp" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp_code": "123456",
    "purpose": "verification"
  }'
```

#### POST /auth/resend-otp
Resend OTP (same as request-otp).

**Request/Response:** Same as `/auth/request-otp`

#### GET /auth/me
Get current authenticated user information.

**Authentication:** Required (Bearer Token)

**Response (200 OK):**
```json
{
  "id": 1,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-06-12T10:30:00Z"
}
```

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

#### POST /auth/refresh-token
Refresh access token using refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/refresh-token" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

#### POST /auth/logout
Logout user by invalidating refresh token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response (200 OK):**
```json
{
  "message": "Logout successful"
}
```

**cURL Example:**
```bash
curl -X POST "http://localhost:8000/auth/logout" \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

### Google OAuth Endpoints

#### GET /auth/google/login
Initiate Google OAuth 2.0 login flow.

**Response:** Redirect to Google authorization URL

**cURL Example:**
```bash
curl -X GET "http://localhost:8000/auth/google/login"
```

**Browser Usage:**
Navigate to `http://localhost:8000/auth/google/login` to start OAuth flow.

#### GET /auth/google/callback
Handle Google OAuth callback (called by Google).

**Query Parameters:**
- `code` - Authorization code from Google
- `state` - CSRF protection parameter
- `error` - Error code (if authorization failed)

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@google.com",
    "full_name": "Google User",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-06-12T10:30:00Z"
  }
}
```

## OAuth Integration

### Google OAuth 2.0 Flow

#### Step 1: Initialize OAuth Flow
Direct user to the OAuth initiation endpoint:
```javascript
window.location.href = 'http://localhost:8000/auth/google/login';
```

#### Step 2: Google Authorization
User will be redirected to Google's authorization server and prompted to:
- Sign in to their Google account
- Grant permissions to your application
- Authorize access to profile and email

#### Step 3: Handle Callback
Google redirects back to: `http://localhost:8000/auth/google/callback`

The callback includes:
- **Success:** `code` and `state` parameters
- **Error:** `error` parameter with error code

#### Step 4: Token Exchange
The callback endpoint automatically:
- Validates the state parameter (CSRF protection)
- Exchanges authorization code for Google access token
- Retrieves user profile from Google
- Creates or links user account
- Issues platform JWT tokens

#### Frontend Integration Example
```javascript
// React example for handling OAuth
const handleGoogleLogin = () => {
  // Save current location for redirect after login
  localStorage.setItem('redirectAfterLogin', window.location.pathname);
  
  // Redirect to OAuth initiation
  window.location.href = 'http://localhost:8000/auth/google/login';
};

// Handle returning from OAuth (in your callback page component)
useEffect(() => {
  const urlParams = new URLSearchParams(window.location.search);
  const error = urlParams.get('error');
  
  if (error) {
    console.error('OAuth error:', error);
    // Handle error case
  } else {
    // OAuth was successful, tokens are in the response
    // The callback endpoint will have processed everything
    const redirectPath = localStorage.getItem('redirectAfterLogin') || '/dashboard';
    localStorage.removeItem('redirectAfterLogin');
    window.location.href = redirectPath;
  }
}, []);
```

### OAuth Security Features
- **CSRF Protection:** State parameter validation
- **Secure Token Exchange:** Server-side code exchange
- **Account Linking:** Links Google accounts to existing email accounts
- **Email Verification:** Automatic verification for Google-authenticated users

## Error Handling

### Standard HTTP Status Codes

#### 2xx Success
- `200 OK` - Request successful
- `201 Created` - Resource created successfully

#### 4xx Client Errors
- `400 Bad Request` - Invalid request data
- `401 Unauthorized` - Authentication required/failed
- `403 Forbidden` - Access denied
- `404 Not Found` - Resource not found
- `422 Unprocessable Entity` - Validation errors
- `429 Too Many Requests` - Rate limit exceeded

#### 5xx Server Errors
- `500 Internal Server Error` - Unexpected server error
- `502 Bad Gateway` - OAuth service error
- `503 Service Unavailable` - Service temporarily unavailable

### Error Response Format
```json
{
  "detail": "Error message describing what went wrong"
}
```

### Validation Error Response (422)
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "field required",
      "type": "value_error.missing"
    },
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long",
      "type": "value_error"
    }
  ]
}
```

### Rate Limiting Error (429)
```json
{
  "detail": "Too many login attempts. Please try again in 300 seconds."
}
```

## Integration Examples

### Frontend Integration (React)

#### Authentication Context
```javascript
// AuthContext.js
import React, { createContext, useContext, useState, useEffect } from 'react';

const AuthContext = createContext();

export const useAuth = () => useContext(AuthContext);

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [tokens, setTokens] = useState({
    access_token: localStorage.getItem('access_token'),
    refresh_token: localStorage.getItem('refresh_token')
  });

  const API_BASE = 'http://localhost:8000';

  // Login function
  const login = async (email, password) => {
    try {
      const response = await fetch(`${API_BASE}/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password })
      });

      if (response.ok) {
        const data = await response.json();
        setTokens({
          access_token: data.access_token,
          refresh_token: data.refresh_token
        });
        setUser(data.user);
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  // OTP verification function
  const verifyOTP = async (email, otpCode, purpose = 'verification') => {
    try {
      const response = await fetch(`${API_BASE}/auth/verify-otp`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, otp_code: otpCode, purpose })
      });

      if (response.ok) {
        const data = await response.json();
        setTokens({
          access_token: data.access_token,
          refresh_token: data.refresh_token
        });
        setUser(data.user);
        localStorage.setItem('access_token', data.access_token);
        localStorage.setItem('refresh_token', data.refresh_token);
        return { success: true };
      } else {
        const error = await response.json();
        return { success: false, error: error.detail };
      }
    } catch (error) {
      return { success: false, error: 'Network error' };
    }
  };

  // Logout function
  const logout = async () => {
    try {
      if (tokens.refresh_token) {
        await fetch(`${API_BASE}/auth/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: tokens.refresh_token })
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      setUser(null);
      setTokens({ access_token: null, refresh_token: null });
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  };

  // Token refresh function
  const refreshToken = async () => {
    try {
      const response = await fetch(`${API_BASE}/auth/refresh-token`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh_token: tokens.refresh_token })
      });

      if (response.ok) {
        const data = await response.json();
        const newTokens = {
          access_token: data.access_token,
          refresh_token: tokens.refresh_token
        };
        setTokens(newTokens);
        localStorage.setItem('access_token', data.access_token);
        return data.access_token;
      } else {
        // Refresh failed, logout user
        logout();
        return null;
      }
    } catch (error) {
      logout();
      return null;
    }
  };

  // API request with automatic token refresh
  const apiRequest = async (url, options = {}) => {
    const makeRequest = async (accessToken) => {
      return fetch(`${API_BASE}${url}`, {
        ...options,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`,
          ...options.headers
        }
      });
    };

    let response = await makeRequest(tokens.access_token);

    // If unauthorized, try to refresh token
    if (response.status === 401 && tokens.refresh_token) {
      const newAccessToken = await refreshToken();
      if (newAccessToken) {
        response = await makeRequest(newAccessToken);
      }
    }

    return response;
  };

  // Load user on app start
  useEffect(() => {
    const loadUser = async () => {
      if (tokens.access_token) {
        try {
          const response = await apiRequest('/auth/me');
          if (response.ok) {
            const userData = await response.json();
            setUser(userData);
          }
        } catch (error) {
          console.error('Failed to load user:', error);
        }
      }
      setLoading(false);
    };

    loadUser();
  }, []);

  const value = {
    user,
    loading,
    login,
    verifyOTP,
    logout,
    apiRequest
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
```

### Backend Service Integration (Python)

#### JWT Token Validation for Other Services
```python
# auth_middleware.py for other backend services
import jwt
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer
import httpx

security = HTTPBearer()

AUTH_SERVICE_URL = "http://localhost:8000"
JWT_SECRET_KEY = "your_super_secret_key_for_development_only"  # Same as auth service
JWT_ALGORITHM = "HS256"

async def verify_token(token: str = Depends(security)):
    """
    Verify JWT token from auth service.
    Can be used by other microservices to validate authentication.
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token.credentials,
            JWT_SECRET_KEY,
            algorithms=[JWT_ALGORITHM]
        )
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        return {"user_id": int(user_id)}
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expired"
        )
    except jwt.JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Usage in other services
from fastapi import FastAPI, Depends

app = FastAPI()

@app.get("/protected-resource")
async def get_protected_resource(current_user: dict = Depends(verify_token)):
    return {
        "message": "This is a protected resource",
        "user_id": current_user["user_id"]
    }
```

### Environment Configuration

#### Development Environment
```bash
# .env file for development
DATABASE_URL=postgresql://user:password@localhost:5432/auth_service_dev
SECRET_KEY=your_super_secret_key_for_development_only
GOOGLE_CLIENT_ID=your_google_client_id_here
GOOGLE_CLIENT_SECRET=your_google_client_secret_here
BACKEND_CORS_ORIGINS=["http://localhost:3000", "http://localhost:3001"]
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
```

#### Production Environment
```bash
# Production environment variables
DATABASE_URL=postgresql://username:password@prod-db:5432/auth_service_prod
SECRET_KEY=extremely_secure_random_key_here
GOOGLE_CLIENT_ID=production_google_client_id
GOOGLE_CLIENT_SECRET=production_google_client_secret
BACKEND_CORS_ORIGINS=["https://app.yourdomain.com", "https://yourdomain.com"]
LOG_LEVEL=INFO
```

---

**API Documentation Version:** 1.0  
**Last Updated:** June 12, 2025  
**Contact:** Development Team  

For questions or support, please refer to the development team or check the service logs for debugging information.
