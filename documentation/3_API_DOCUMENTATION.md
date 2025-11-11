# Auth Service - Complete API Documentation

## Document Version
- **Version**: 1.0
- **Last Updated**: October 3, 2025
- **Base URL**: `http://localhost:8000`
- **API Version**: 1.0.0
- **Protocol**: HTTP/HTTPS
- **Authentication**: JWT Bearer Token

---

## Table of Contents
1. [API Overview](#api-overview)
2. [Authentication](#authentication)
3. [Common Response Formats](#common-response-formats)
4. [Error Responses](#error-responses)
5. [Rate Limiting](#rate-limiting)
6. [Endpoints Reference](#endpoints-reference)
   - [Health Check](#health-check-endpoints)
   - [Registration](#registration-endpoints)
   - [Login](#login-endpoints)
   - [OTP Management](#otp-management-endpoints)
   - [Token Management](#token-management-endpoints)
   - [User Profile](#user-profile-endpoints)
   - [OAuth](#oauth-endpoints)
7. [Security Headers](#security-headers)
8. [CORS Configuration](#cors-configuration)
9. [Example Integration Workflows](#example-integration-workflows)
10. [SDKs and Client Libraries](#sdks-and-client-libraries)
11. [Testing the API](#testing-the-api)
12. [Troubleshooting](#troubleshooting)

---

## 1. API Overview

### Base Information

**Service Name**: Auth Service  
**Base URL**: `http://localhost:8000` (Development)  
**Production URL**: `https://auth.yourdomain.com` (Configure as needed)  
**Content Type**: `application/json`  
**Character Encoding**: UTF-8

### API Characteristics

- **RESTful**: Follows REST principles
- **Stateless**: JWT-based authentication (no server-side sessions)
- **Versioned**: Currently v1.0.0
- **Rate Limited**: Global and endpoint-specific limits
- **Secure**: HTTPS in production, security headers, CSRF protection

### Supported HTTP Methods

- `GET` - Retrieve resources
- `POST` - Create resources or perform actions
- `PUT` - Update resources (future)
- `DELETE` - Delete resources (future)
- `OPTIONS` - CORS preflight requests

---

## 2. Authentication

### Authentication Methods

The API supports **three authentication methods**:

1. **JWT Bearer Token** (for authenticated endpoints)
2. **No Authentication** (for public endpoints)
3. **Service-to-Service** (future enhancement)

### Bearer Token Authentication

**Header Format**:
```http
Authorization: Bearer <access_token>
```

**Example**:
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Obtaining Tokens**:
- Login with email/password → `/auth/login`
- Verify OTP → `/auth/verify-otp`
- Google OAuth → `/auth/google/callback`
- Refresh token → `/auth/refresh-token`

### Token Expiration

| Token Type | Expiration | Renewable |
|------------|------------|-----------|
| Access Token | 30 minutes | No (use refresh token) |
| Refresh Token | 7 days | No (must re-login) |

### Handling Token Expiration

**Access Token Expired (401 response)**:
1. Use refresh token to get new access token
2. Retry original request with new access token

**Refresh Token Expired**:
1. Redirect user to login page
2. User must authenticate again

---

## 3. Common Response Formats

### Success Response Structure

**User Data Response**:
```json
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-06-08T10:30:00Z"
}
```

**Token Response**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-06-08T10:30:00Z"
  }
}
```

**OTP Response**:
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

**Simple Success Response**:
```json
{
  "message": "Logout successful"
}
```

### Field Descriptions

| Field | Type | Description |
|-------|------|-------------|
| `id` | integer | Unique user identifier |
| `email` | string | User's email address |
| `full_name` | string | User's full name (nullable) |
| `is_active` | boolean | Account active status |
| `is_verified` | boolean | Email verification status |
| `created_at` | string (ISO 8601) | Account creation timestamp (UTC) |
| `access_token` | string | JWT access token for API authentication |
| `refresh_token` | string | JWT refresh token for token renewal |
| `token_type` | string | Always "bearer" |
| `expires_in` | integer | Access token expiration time in seconds |
| `refresh_token_expires_in` | integer | Refresh token expiration time in seconds |

---

## 4. Error Responses

### Error Response Structure

**Standard Error**:
```json
{
  "detail": "Error message description"
}
```

**Validation Error**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "email"],
      "msg": "value is not a valid email address"
    }
  ]
}
```

### HTTP Status Codes

| Status Code | Meaning | Common Causes |
|-------------|---------|---------------|
| `200 OK` | Success | Request completed successfully |
| `201 Created` | Resource created | User registration successful |
| `400 Bad Request` | Invalid input | Validation error, malformed request |
| `401 Unauthorized` | Authentication failed | Invalid/expired token, wrong credentials |
| `403 Forbidden` | Permission denied | Unverified email, insufficient permissions |
| `404 Not Found` | Resource not found | Invalid endpoint |
| `429 Too Many Requests` | Rate limit exceeded | Too many requests too quickly |
| `500 Internal Server Error` | Server error | Unexpected server error |
| `502 Bad Gateway` | External service error | Google OAuth failure |
| `503 Service Unavailable` | Service temporarily down | Cannot connect to external service |

### Common Error Messages

**Authentication Errors**:
```json
{ "detail": "Invalid email or password" }
{ "detail": "Could not validate credentials" }
{ "detail": "Invalid or expired refresh token" }
{ "detail": "Token has been invalidated" }
```

**Validation Errors**:
```json
{ "detail": "Invalid email format" }
{ "detail": "Password must be at least 8 characters long" }
{ "detail": "OTP code must be exactly 6 digits" }
{ "detail": "Invalid OTP format" }
```

**Rate Limiting Errors**:
```json
{ 
  "detail": "Too many OTP requests. Please try again in 2847 seconds."
}
{ 
  "detail": "Too many login attempts. Please try again in 673 seconds."
}
{ 
  "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
  "error": "Too Many Requests"
}
```

**Account Status Errors**:
```json
{ "detail": "Account is deactivated. Please contact support." }
{ "detail": "Email not verified. Please verify your email first." }
{ "detail": "Inactive user" }
```

**Business Logic Errors**:
```json
{ "detail": "Invalid or expired OTP" }
{ "detail": "Registration failed. Please try again or contact support." }
{ "detail": "Request not allowed" }
```

---

## 5. Rate Limiting

### Global Rate Limit

**Limit**: 100 requests per minute per IP address  
**Applies To**: All endpoints  
**Response**: 429 status code with error message

**Example Response**:
```json
{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
  "error": "Too Many Requests"
}
```

### Endpoint-Specific Rate Limits

| Endpoint | Limit | Window | Identifier |
|----------|-------|--------|------------|
| `/auth/request-otp` | 5 requests | 1 hour | Email address |
| `/auth/verify-otp` | 3 attempts | 1 minute | Email address |
| `/auth/login` | 5 attempts | 15 minutes | Email address |
| `/auth/resend-otp` | 5 requests | 1 hour | Email address |

### Rate Limit Headers

*Note: Currently not implemented, but recommended for production*

**Recommended Headers**:
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1623456789
Retry-After: 60
```

### Handling Rate Limits

**Best Practices**:
1. Respect rate limits in client code
2. Implement exponential backoff for retries
3. Display user-friendly messages with retry time
4. Cache responses when appropriate
5. Use refresh tokens instead of re-authenticating

**Example Error Handling**:
```javascript
if (response.status === 429) {
  const errorData = await response.json();
  const match = errorData.detail.match(/(\d+) seconds/);
  const retryAfter = match ? parseInt(match[1]) : 60;
  
  // Display: "Too many attempts. Please try again in X minutes."
  displayError(`Please wait ${Math.ceil(retryAfter / 60)} minutes before trying again.`);
}
```

---

## 6. Endpoints Reference

### Health Check Endpoints

#### GET / - Root Endpoint

**Description**: Check if service is running

**Authentication**: None

**Request**:
```http
GET / HTTP/1.1
Host: localhost:8000
```

**Response**: 200 OK
```json
{
  "message": "Auth Service is running"
}
```

**Use Cases**:
- Service health check
- Load balancer health probe
- Deployment verification

---

#### GET /health - Health Check

**Description**: Detailed health check endpoint

**Authentication**: None

**Request**:
```http
GET /health HTTP/1.1
Host: localhost:8000
```

**Response**: 200 OK
```json
{
  "status": "healthy"
}
```

**Use Cases**:
- Kubernetes liveness probe
- Monitoring systems
- Service discovery

---

### Registration Endpoints

#### POST /auth/register - Register New User

**Description**: Create a new user account with email and password

**Authentication**: None

**Rate Limiting**: Global only (100/min)

**Request**:
```http
POST /auth/register HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | Valid email address (will be normalized to lowercase) |
| `password` | string | No | Password meeting strength requirements (see validation) |
| `full_name` | string | No | User's full name (max 100 characters) |

**Password Requirements**:
- Minimum 8 characters
- Maximum 128 characters
- At least one lowercase letter
- At least one uppercase letter
- At least one digit
- At least one special character (@$!%*?&)

**Response**: 201 Created
```json
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": false,
  "created_at": "2025-10-03T10:30:00Z"
}
```

**Error Responses**:

```json
// 400 - Invalid email format
{
  "detail": "Invalid email format"
}

// 400 - Weak password
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Password must contain at least one uppercase letter"
    }
  ]
}

// 400 - Email already exists
{
  "detail": "Registration failed. Please try again or contact support."
}

// 400 - Suspicious request (temporary email, bot)
{
  "detail": "Registration not allowed"
}

// 500 - Server error
{
  "detail": "Registration failed. Please try again."
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

**Security Notes**:
- Email normalized to lowercase
- Password never stored in plain text (bcrypt hashed)
- Generic error messages prevent account enumeration
- Suspicious emails/user agents blocked
- Input sanitization applied

**Next Steps After Registration**:
1. User receives response with `is_verified: false`
2. User requests OTP via `/auth/request-otp` (purpose: "verification")
3. User verifies OTP via `/auth/verify-otp`
4. Account becomes verified and user can login

---

### Login Endpoints

#### POST /auth/login - Login with Email and Password

**Description**: Authenticate user with email and password credentials

**Authentication**: None

**Rate Limiting**: 5 attempts per 15 minutes per email

**Request**:
```http
POST /auth/login HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `password` | string | Yes | User's password |

**Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTY0MTUwMDAsInN1YiI6IjEyMyJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2OTY5OTk4MDAsInN1YiI6IjEyMyIsImp0aSI6ImFiYzEyMyJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-10-03T10:30:00Z"
  }
}
```

**Error Responses**:

```json
// 401 - Invalid credentials
{
  "detail": "Invalid email or password"
}

// 401 - Account deactivated
{
  "detail": "Account is deactivated. Please contact support."
}

// 401 - Email not verified (if REQUIRE_EMAIL_VERIFICATION=True)
{
  "detail": "Email not verified. Please verify your email first."
}

// 429 - Rate limit exceeded
{
  "detail": "Too many login attempts. Please try again in 673 seconds."
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

**Example JavaScript (Fetch)**:
```javascript
const response = await fetch('http://localhost:8000/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePass123!'
  })
});

const data = await response.json();

if (response.ok) {
  // Store tokens securely
  localStorage.setItem('access_token', data.access_token);
  localStorage.setItem('refresh_token', data.refresh_token);
  
  // Redirect to dashboard
  window.location.href = '/dashboard';
} else {
  // Display error
  console.error('Login failed:', data.detail);
}
```

**Security Features**:
- Rate limiting prevents brute force attacks
- Generic error messages prevent account enumeration
- Timing attack prevention (0.1s delay for non-existent users)
- bcrypt password comparison (constant-time)
- Account status checks (active, verified)

**Token Storage Recommendations**:
- **Access Token**: Memory or short-lived localStorage
- **Refresh Token**: httpOnly cookie (most secure) or secure storage
- Never log tokens or include in URLs

---

### OTP Management Endpoints

#### POST /auth/request-otp - Request OTP

**Description**: Generate and send OTP to user's email

**Authentication**: None

**Rate Limiting**: 5 requests per hour per email

**Request**:
```http
POST /auth/request-otp HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "purpose": "verification"
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `purpose` | string | Yes | OTP purpose: "verification", "login", or "password_reset" |

**Response**: 200 OK
```json
{
  "message": "OTP sent successfully",
  "email": "user@example.com",
  "expires_in_minutes": 10
}
```

**Non-Existent User Response**: 200 OK (same as success)
```json
{
  "message": "If the email exists in our system, an OTP has been sent",
  "email": "nonexistent@example.com",
  "expires_in_minutes": 10
}
```

**Error Responses**:

```json
// 400 - Invalid email format
{
  "detail": "Invalid email format"
}

// 400 - Suspicious request
{
  "detail": "Request not allowed"
}

// 429 - Rate limit exceeded
{
  "detail": "Too many OTP requests. Please try again in 2847 seconds."
}

// 500 - Email sending failed
{
  "detail": "Failed to send OTP. Please try again."
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "purpose": "verification"
  }'
```

**OTP Email Example**:
```
Subject: Verify Your Email - AI EdTech Platform

Hello John,

Your One-Time Password (OTP) to verify your email address is:

╔════════╗
║ 123456 ║
╚════════╝

This OTP will expire in 10 minutes.

If you did not request this OTP, please ignore this email.

Thanks,
The AI EdTech Platform Team
```

**Business Logic**:
- OTP is 6 random digits (000000-999999)
- OTP hashed before storage (bcrypt)
- Valid for 10 minutes
- Single-use (deleted after verification)
- One active OTP per user per purpose
- Previous OTP deleted when new one generated

**Security Notes**:
- Returns success even for non-existent emails (prevents enumeration)
- Rate limiting prevents OTP spam
- Email sanitization applied
- Suspicious requests blocked

---

#### POST /auth/verify-otp - Verify OTP

**Description**: Verify OTP and optionally receive authentication tokens

**Authentication**: None

**Rate Limiting**: 3 attempts per minute per email

**Request**:
```http
POST /auth/verify-otp HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "email": "user@example.com",
  "otp_code": "123456",
  "purpose": "verification"
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `email` | string | Yes | User's email address |
| `otp_code` | string | Yes | 6-digit OTP code received via email |
| `purpose` | string | Yes | Must match OTP purpose: "verification", "login", or "password_reset" |

**Response for "verification" or "login"**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800,
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true,
    "created_at": "2025-10-03T10:30:00Z"
  }
}
```

**Response for "password_reset"**: 200 OK
```json
{
  "message": "OTP verified successfully. You can now reset your password."
}
```

**Error Responses**:

```json
// 400 - Invalid OTP format
{
  "detail": "Invalid OTP format"
}

// 400 - Invalid or expired OTP
{
  "detail": "Invalid or expired OTP"
}

// 400 - Wrong email or OTP
{
  "detail": "Invalid email or OTP"
}

// 429 - Rate limit exceeded
{
  "detail": "Too many verification attempts. Please try again in 45 seconds."
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp_code": "123456",
    "purpose": "verification"
  }'
```

**Example JavaScript**:
```javascript
const verifyOTP = async (email, otpCode, purpose) => {
  const response = await fetch('http://localhost:8000/auth/verify-otp', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      email,
      otp_code: otpCode,
      purpose
    })
  });

  const data = await response.json();

  if (response.ok) {
    if (data.access_token) {
      // Login or verification - store tokens
      localStorage.setItem('access_token', data.access_token);
      localStorage.setItem('refresh_token', data.refresh_token);
      return { success: true, user: data.user };
    } else {
      // Password reset - proceed to password update
      return { success: true, message: data.message };
    }
  } else {
    return { success: false, error: data.detail };
  }
};
```

**Business Logic**:
- OTP verified using bcrypt comparison (constant-time)
- Expired OTPs rejected and deleted
- Valid OTP deleted after verification (single-use)
- For "verification": `is_verified` set to `true`, tokens issued
- For "login": tokens issued immediately
- For "password_reset": no tokens issued (security measure)

**Security Features**:
- Rate limiting prevents brute force (3 attempts/min = max 30 attempts in OTP lifetime)
- Input sanitization and validation
- Timing attack prevention
- OTP format validation
- Generic error messages

---

#### POST /auth/resend-otp - Resend OTP

**Description**: Resend OTP (alias for request-otp with same functionality)

**Authentication**: None

**Rate Limiting**: 5 requests per hour per email (shared with request-otp)

**Request**: Same as `/auth/request-otp`

**Response**: Same as `/auth/request-otp`

**Use Case**: Provides explicit "Resend OTP" functionality in UI

---

### Token Management Endpoints

#### POST /auth/refresh-token - Refresh Access Token

**Description**: Obtain a new access token using a valid refresh token

**Authentication**: None (refresh token in body)

**Rate Limiting**: Global only

**Request**:
```http
POST /auth/refresh-token HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Valid refresh token obtained from login or OTP verification |

**Response**: 200 OK
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

**Error Responses**:

```json
// 401 - Invalid refresh token
{
  "detail": "Invalid or expired refresh token"
}

// 401 - Token invalidated (logged out)
{
  "detail": "Token has been invalidated"
}

// 401 - User not found or inactive
{
  "detail": "User not found or inactive"
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Example JavaScript (Auto-refresh)**:
```javascript
let accessToken = localStorage.getItem('access_token');
const refreshToken = localStorage.getItem('refresh_token');

const apiCall = async (url, options = {}) => {
  // Add access token to request
  options.headers = {
    ...options.headers,
    'Authorization': `Bearer ${accessToken}`
  };

  let response = await fetch(url, options);

  // If 401, try refreshing token
  if (response.status === 401) {
    const refreshResponse = await fetch('http://localhost:8000/auth/refresh-token', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });

    if (refreshResponse.ok) {
      const data = await refreshResponse.json();
      accessToken = data.access_token;
      localStorage.setItem('access_token', accessToken);

      // Retry original request with new token
      options.headers['Authorization'] = `Bearer ${accessToken}`;
      response = await fetch(url, options);
    } else {
      // Refresh failed - redirect to login
      window.location.href = '/login';
    }
  }

  return response;
};
```

**Business Logic**:
- Refresh token decoded and JTI extracted
- JTI checked against denylist (invalidated_tokens table)
- User verified to exist and be active
- New access token generated with same user_id
- Refresh token remains valid (not renewed)
- Same refresh token can be used multiple times

**Security Considerations**:
- Refresh token should be stored securely (httpOnly cookie recommended)
- Rotation not implemented (same refresh token reused)
- Logout invalidates refresh token via denylist
- User status checked on each refresh

**Token Lifecycle**:
1. Login → Receive access token (30 min) + refresh token (7 days)
2. Use access token for API calls
3. After 30 min → Access token expires
4. Use refresh token to get new access token
5. Repeat steps 2-4 for up to 7 days
6. After 7 days → Refresh token expires, must re-login

---

#### POST /auth/logout - Logout

**Description**: Invalidate refresh token to log out user

**Authentication**: None (refresh token in body)

**Rate Limiting**: Global only

**Request**:
```http
POST /auth/logout HTTP/1.1
Host: localhost:8000
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Request Body**:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `refresh_token` | string | Yes | Refresh token to invalidate |

**Response**: 200 OK
```json
{
  "message": "Logout successful"
}
```

**Error Responses**:

```json
// 401 - Invalid refresh token
{
  "detail": "Invalid or expired refresh token"
}

// 500 - Database error (rare)
{
  "detail": "Failed to invalidate token"
}
```

**Example cURL**:
```bash
curl -X POST http://localhost:8000/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
  }'
```

**Example JavaScript**:
```javascript
const logout = async () => {
  const refreshToken = localStorage.getItem('refresh_token');

  const response = await fetch('http://localhost:8000/auth/logout', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      refresh_token: refreshToken
    })
  });

  if (response.ok) {
    // Clear tokens from storage
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    
    // Redirect to login
    window.location.href = '/login';
  } else {
    console.error('Logout failed');
  }
};
```

**Business Logic**:
- Refresh token decoded to extract JTI (JWT ID)
- JTI added to invalidated_tokens table (denylist)
- Access tokens remain valid until expiration (stateless)
- User must re-login to get new tokens
- Idempotent (multiple calls return success)

**Security Notes**:
- Only invalidates the specific refresh token (device-specific logout)
- Other devices with different refresh tokens remain logged in
- Access tokens continue working until expiration (max 30 minutes)
- For immediate logout, client should clear tokens from storage

**Logout All Devices** (Future Enhancement):
```
POST /auth/logout-all
- Invalidate all refresh tokens for user
- Requires authentication
- Implementation: Store and invalidate all JTIs for user
```

---

### User Profile Endpoints

#### GET /auth/me - Get Current User

**Description**: Retrieve authenticated user's profile information

**Authentication**: Required (Bearer token)

**Rate Limiting**: Global only

**Request**:
```http
GET /auth/me HTTP/1.1
Host: localhost:8000
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response**: 200 OK
```json
{
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-10-03T10:30:00Z"
}
```

**Error Responses**:

```json
// 401 - No token provided
{
  "detail": "Not authenticated"
}

// 401 - Invalid token
{
  "detail": "Could not validate credentials"
}

// 404 - User not found (token valid but user deleted)
{
  "detail": "User not found"
}
```

**Example cURL**:
```bash
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Example JavaScript**:
```javascript
const getCurrentUser = async () => {
  const accessToken = localStorage.getItem('access_token');

  const response = await fetch('http://localhost:8000/auth/me', {
    method: 'GET',
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  });

  if (response.ok) {
    const user = await response.json();
    console.log('Current user:', user);
    return user;
  } else if (response.status === 401) {
    // Token expired or invalid - try refreshing
    console.log('Token expired, refreshing...');
    // Implement token refresh logic
  } else {
    console.error('Failed to get user');
  }
};
```

**Use Cases**:
- Display user profile in UI
- Verify authentication status
- Fetch user information after login
- Check user permissions (is_verified, is_active)

**Security**:
- Requires valid access token
- Returns only current user's data
- Cannot query other users' information

---

### OAuth Endpoints

#### GET /auth/google/login - Initiate Google OAuth

**Description**: Redirect user to Google for OAuth authorization

**Authentication**: None

**Rate Limiting**: Global only

**Request**:
```http
GET /auth/google/login HTTP/1.1
Host: localhost:8000
```

**Response**: 302 Redirect

**Location Header**:
```
https://accounts.google.com/o/oauth2/v2/auth?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost:8006/auth/google/callback&response_type=code&scope=openid+email+profile&access_type=offline&state=RANDOM_STATE_STRING
```

**Example HTML**:
```html
<a href="http://localhost:8000/auth/google/login">
  <button>Login with Google</button>
</a>
```

**Example JavaScript**:
```javascript
const loginWithGoogle = () => {
  window.location.href = 'http://localhost:8000/auth/google/login';
};
```

**Flow**:
1. User clicks "Login with Google"
2. Frontend redirects to `/auth/google/login`
3. Backend generates secure state parameter
4. Backend redirects to Google authorization URL
5. User sees Google consent screen
6. User authorizes application
7. Google redirects to `/auth/google/callback` with code

**Security**:
- State parameter prevents CSRF attacks
- State stored server-side with 30-minute expiration
- One-time use state

---

#### GET /auth/google/callback - Google OAuth Callback

**Description**: Handle OAuth callback from Google, exchange code for tokens

**Authentication**: None

**Rate Limiting**: Global only

**Request** (from Google):
```http
GET /auth/google/callback?code=AUTHORIZATION_CODE&state=STATE_PARAMETER HTTP/1.1
Host: localhost:8000
```

**Query Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `code` | string | Yes | Authorization code from Google |
| `state` | string | Yes | State parameter for CSRF protection |
| `error` | string | No | Error code if authorization failed |

**Successful Response**: 302 Redirect

**Location Header**:
```
http://localhost:5173/?access_token=ACCESS_TOKEN&refresh_token=REFRESH_TOKEN
```

**Error Responses**:

```json
// 400 - User denied authorization
{
  "detail": "Google OAuth authorization failed: access_denied"
}

// 400 - Missing authorization code
{
  "detail": "Authorization code not provided"
}

// 400 - Missing state parameter
{
  "detail": "State parameter missing - possible CSRF attack"
}

// 401 - Invalid state
{
  "detail": "Invalid state parameter - possible CSRF attack"
}

// 400 - Token exchange failed
{
  "detail": "Google OAuth token exchange failed: Invalid code or client authentication failed. Status: 400"
}

// 400 - Missing required user info
{
  "detail": "Required user information missing or invalid in ID token: email_verified"
}

// 502 - Google service error
{
  "detail": "Google OAuth service error. Status: 503"
}

// 503 - Network error
{
  "detail": "Failed to connect to Google OAuth service: Connection timeout"
}

// 500 - Server error
{
  "detail": "Failed to process Google OAuth callback: Unexpected error"
}
```

**Frontend Integration**:
```javascript
// In your frontend app (e.g., React, Vue)
// This code runs on the page that receives the OAuth redirect

const extractTokensFromURL = () => {
  const urlParams = new URLSearchParams(window.location.search);
  const accessToken = urlParams.get('access_token');
  const refreshToken = urlParams.get('refresh_token');

  if (accessToken && refreshToken) {
    // Store tokens
    localStorage.setItem('access_token', accessToken);
    localStorage.setItem('refresh_token', refreshToken);

    // Clean URL
    window.history.replaceState({}, document.title, '/');

    // Fetch user info
    fetchUserInfo();
  }
};

// Call on page load
extractTokensFromURL();
```

**Business Logic**:
1. Validate state parameter (CSRF protection)
2. Exchange authorization code for Google tokens
3. Decode ID token to extract user information
4. Check if user exists by google_id
   - If yes: Use existing account
5. Check if user exists by email
   - If yes: Link Google ID to account
6. If no existing user: Create new account
7. Set `is_verified = true` (pre-verified by Google)
8. Generate platform tokens
9. Redirect to frontend with tokens

**Account Linking**:
- Existing user with same email → Google ID linked automatically
- User can login with password OR Google
- Seamless migration from password to OAuth

**Security**:
- State validation (one-time use, 30-minute expiration)
- CSRF protection
- Email verification required by Google
- Secure token exchange
- Account enumeration prevention

---

## 7. Security Headers

All API responses include the following security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Referrer-Policy: strict-origin-when-cross-origin
Content-Security-Policy: default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';
```

**Server Header**: Removed for security (hides server technology)

---

## 8. CORS Configuration

**Allowed Origins**: Configured via `BACKEND_CORS_ORIGINS` environment variable

**Default (Development)**:
```json
[
  "http://localhost:5173",
  "http://localhost:3000",
  "http://localhost:3001"
]
```

**Allowed Methods**:
```
GET, POST, PUT, DELETE, OPTIONS
```

**Allowed Headers**: All (`*`)

**Exposed Headers**: All (`*`)

**Credentials**: Allowed (`allow_credentials: true`)

**Preflight Caching**: Default browser behavior

**Production Configuration**:
```bash
BACKEND_CORS_ORIGINS='["https://yourdomain.com", "https://app.yourdomain.com"]'
```

---

## 9. Example Integration Workflows

### Workflow 1: Email/Password Registration and Login

```javascript
// Step 1: Register user
const register = async (email, password, fullName) => {
  const response = await fetch('http://localhost:8000/auth/register', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      password,
      full_name: fullName
    })
  });
  
  if (response.ok) {
    const user = await response.json();
    console.log('User registered:', user);
    return { success: true, user };
  } else {
    const error = await response.json();
    return { success: false, error: error.detail };
  }
};

// Step 2: Request verification OTP
const requestVerificationOTP = async (email) => {
  const response = await fetch('http://localhost:8000/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      purpose: 'verification'
    })
  });
  
  return response.json();
};

// Step 3: Verify OTP
const verifyEmail = async (email, otpCode) => {
  const response = await fetch('http://localhost:8000/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      otp_code: otpCode,
      purpose: 'verification'
    })
  });
  
  if (response.ok) {
    const data = await response.json();
    // Store tokens
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return { success: true, user: data.user };
  } else {
    const error = await response.json();
    return { success: false, error: error.detail };
  }
};

// Complete registration flow
const completeRegistration = async () => {
  // 1. Register
  const regResult = await register(
    'john@example.com',
    'SecurePass123!',
    'John Doe'
  );
  
  if (!regResult.success) {
    console.error('Registration failed:', regResult.error);
    return;
  }
  
  // 2. Request OTP
  await requestVerificationOTP('john@example.com');
  console.log('OTP sent to email');
  
  // 3. User enters OTP (from email)
  const otp = prompt('Enter OTP from email:');
  
  // 4. Verify OTP
  const verifyResult = await verifyEmail('john@example.com', otp);
  
  if (verifyResult.success) {
    console.log('Registration complete! User logged in:', verifyResult.user);
    // Redirect to dashboard
    window.location.href = '/dashboard';
  } else {
    console.error('Verification failed:', verifyResult.error);
  }
};
```

---

### Workflow 2: OTP-Based Login (Passwordless)

```javascript
// Step 1: Request login OTP
const requestLoginOTP = async (email) => {
  const response = await fetch('http://localhost:8000/auth/request-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      purpose: 'login'
    })
  });
  
  return response.json();
};

// Step 2: Verify OTP and login
const loginWithOTP = async (email, otpCode) => {
  const response = await fetch('http://localhost:8000/auth/verify-otp', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      email,
      otp_code: otpCode,
      purpose: 'login'
    })
  });
  
  if (response.ok) {
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    localStorage.setItem('refresh_token', data.refresh_token);
    return { success: true, user: data.user };
  } else {
    const error = await response.json();
    return { success: false, error: error.detail };
  }
};

// Complete OTP login flow
const otpLoginFlow = async () => {
  const email = document.getElementById('email').value;
  
  // 1. Request OTP
  await requestLoginOTP(email);
  
  // 2. Show OTP input field
  document.getElementById('otp-section').style.display = 'block';
  
  // 3. User enters OTP
  document.getElementById('verify-btn').onclick = async () => {
    const otp = document.getElementById('otp-input').value;
    const result = await loginWithOTP(email, otp);
    
    if (result.success) {
      window.location.href = '/dashboard';
    } else {
      alert('Invalid OTP: ' + result.error);
    }
  };
};
```

---

### Workflow 3: Token Refresh and API Calls

```javascript
class AuthAPI {
  constructor(baseURL) {
    this.baseURL = baseURL;
    this.accessToken = localStorage.getItem('access_token');
    this.refreshToken = localStorage.getItem('refresh_token');
  }
  
  async refreshAccessToken() {
    const response = await fetch(`${this.baseURL}/auth/refresh-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: this.refreshToken
      })
    });
    
    if (response.ok) {
      const data = await response.json();
      this.accessToken = data.access_token;
      localStorage.setItem('access_token', data.access_token);
      return true;
    } else {
      // Refresh failed - logout
      this.logout();
      return false;
    }
  }
  
  async apiCall(endpoint, options = {}) {
    // Add access token
    options.headers = {
      ...options.headers,
      'Authorization': `Bearer ${this.accessToken}`
    };
    
    let response = await fetch(`${this.baseURL}${endpoint}`, options);
    
    // If 401, try refreshing token
    if (response.status === 401) {
      const refreshed = await this.refreshAccessToken();
      
      if (refreshed) {
        // Retry with new token
        options.headers['Authorization'] = `Bearer ${this.accessToken}`;
        response = await fetch(`${this.baseURL}${endpoint}`, options);
      } else {
        // Redirect to login
        window.location.href = '/login';
        throw new Error('Session expired');
      }
    }
    
    return response;
  }
  
  async getCurrentUser() {
    const response = await this.apiCall('/auth/me');
    return response.json();
  }
  
  async logout() {
    await fetch(`${this.baseURL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        refresh_token: this.refreshToken
      })
    });
    
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    window.location.href = '/login';
  }
}

// Usage
const api = new AuthAPI('http://localhost:8000');

// Make authenticated API call
const user = await api.getCurrentUser();
console.log('Current user:', user);

// Logout
await api.logout();
```

---

## 10. SDKs and Client Libraries

### JavaScript/TypeScript SDK (Conceptual)

```typescript
// auth-sdk.ts
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface RegisterData {
  email: string;
  password?: string;
  full_name?: string;
}

export interface OTPRequest {
  email: string;
  purpose: 'verification' | 'login' | 'password_reset';
}

export interface OTPVerify {
  email: string;
  otp_code: string;
  purpose: 'verification' | 'login' | 'password_reset';
}

export class AuthSDK {
  constructor(
    private baseURL: string,
    private onTokenRefresh?: (accessToken: string) => void
  ) {}
  
  async register(data: RegisterData) {
    const response = await fetch(`${this.baseURL}/auth/register`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    return this.handleResponse(response);
  }
  
  async login(credentials: LoginCredentials) {
    const response = await fetch(`${this.baseURL}/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(credentials)
    });
    
    return this.handleResponse(response);
  }
  
  async requestOTP(data: OTPRequest) {
    const response = await fetch(`${this.baseURL}/auth/request-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    return this.handleResponse(response);
  }
  
  async verifyOTP(data: OTPVerify) {
    const response = await fetch(`${this.baseURL}/auth/verify-otp`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    
    return this.handleResponse(response);
  }
  
  async refreshToken(refreshToken: string) {
    const response = await fetch(`${this.baseURL}/auth/refresh-token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    return this.handleResponse(response);
  }
  
  async logout(refreshToken: string) {
    const response = await fetch(`${this.baseURL}/auth/logout`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken })
    });
    
    return this.handleResponse(response);
  }
  
  async getCurrentUser(accessToken: string) {
    const response = await fetch(`${this.baseURL}/auth/me`, {
      headers: {
        'Authorization': `Bearer ${accessToken}`
      }
    });
    
    return this.handleResponse(response);
  }
  
  private async handleResponse(response: Response) {
    const data = await response.json();
    
    if (response.ok) {
      return { success: true, data };
    } else {
      return { success: false, error: data.detail };
    }
  }
}

// Usage
const auth = new AuthSDK('http://localhost:8000');

const result = await auth.login({
  email: 'user@example.com',
  password: 'SecurePass123!'
});

if (result.success) {
  console.log('Login successful:', result.data);
} else {
  console.error('Login failed:', result.error);
}
```

---

## 11. Testing the API

### Using cURL

**Login Test**:
```bash
# Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }' | jq

# Expected output:
# {
#   "access_token": "eyJ...",
#   "token_type": "bearer",
#   ...
# }
```

**Get Current User**:
```bash
# Replace TOKEN with your access token
curl -X GET http://localhost:8000/auth/me \
  -H "Authorization: Bearer TOKEN" | jq
```

---

### Using Postman

**1. Create Collection**: "Auth Service API"

**2. Set Environment Variables**:
```
base_url = http://localhost:8000
access_token = (empty initially)
refresh_token = (empty initially)
```

**3. Create Requests**:

**Register**:
- Method: POST
- URL: `{{base_url}}/auth/register`
- Body (JSON):
```json
{
  "email": "test@example.com",
  "password": "TestPass123!",
  "full_name": "Test User"
}
```

**Login**:
- Method: POST
- URL: `{{base_url}}/auth/login`
- Body (JSON):
```json
{
  "email": "test@example.com",
  "password": "TestPass123!"
}
```
- Tests (to save tokens):
```javascript
if (pm.response.code === 200) {
  const response = pm.response.json();
  pm.environment.set('access_token', response.access_token);
  pm.environment.set('refresh_token', response.refresh_token);
}
```

**Get Current User**:
- Method: GET
- URL: `{{base_url}}/auth/me`
- Headers: `Authorization: Bearer {{access_token}}`

---

### Using Python

```python
import requests

BASE_URL = "http://localhost:8000"

# Register
response = requests.post(
    f"{BASE_URL}/auth/register",
    json={
        "email": "python@example.com",
        "password": "PythonPass123!",
        "full_name": "Python User"
    }
)
print("Register:", response.json())

# Login
response = requests.post(
    f"{BASE_URL}/auth/login",
    json={
        "email": "python@example.com",
        "password": "PythonPass123!"
    }
)
tokens = response.json()
access_token = tokens["access_token"]
print("Login successful")

# Get current user
response = requests.get(
    f"{BASE_URL}/auth/me",
    headers={"Authorization": f"Bearer {access_token}"}
)
user = response.json()
print("Current user:", user)

# Logout
response = requests.post(
    f"{BASE_URL}/auth/logout",
    json={"refresh_token": tokens["refresh_token"]}
)
print("Logout:", response.json())
```

---

## 12. Troubleshooting

### Common Issues and Solutions

**Issue**: 401 Unauthorized on `/auth/me`  
**Cause**: Invalid or expired access token  
**Solution**: 
- Check token is included in Authorization header
- Verify token format: `Bearer <token>`
- Try refreshing token with refresh token
- If refresh fails, re-login

**Issue**: 429 Too Many Requests  
**Cause**: Rate limit exceeded  
**Solution**:
- Wait for the time specified in error message
- Implement exponential backoff
- Check for infinite retry loops
- Reduce request frequency

**Issue**: CORS error in browser  
**Cause**: Origin not in allowed CORS origins  
**Solution**:
- Add your origin to `BACKEND_CORS_ORIGINS` environment variable
- Verify frontend URL matches exactly (http vs https, port)
- Check for trailing slashes
- Restart auth service after config change

**Issue**: OTP not received  
**Cause**: Email not configured or SMTP error  
**Solution**:
- Check email configuration in `.env`
- Verify SMTP credentials
- Check email spam folder
- Look for OTP in console logs (development mode)
- Test SMTP connection separately

**Issue**: "Registration failed" generic error  
**Cause**: Email already exists OR suspicious email/user agent  
**Solution**:
- Try different email address
- Use legitimate email domain (not tempmail)
- Check for suspicious user agent
- Review server logs for details

**Issue**: Google OAuth redirect not working  
**Cause**: Redirect URI mismatch  
**Solution**:
- Verify redirect URI in Google Cloud Console matches exactly
- Check: `http://localhost:8006/auth/google/callback`
- No trailing slash
- Correct port number
- HTTP vs HTTPS

**Issue**: Token refresh not working after logout  
**Cause**: Token invalidated in denylist  
**Solution**:
- This is expected behavior
- User must re-login after logout
- Check if you're using the correct refresh token

**Issue**: Slow response times  
**Cause**: Multiple possible causes  
**Solution**:
- Check database connection
- Review rate limiting settings
- Check for network issues
- Review server logs for slow queries
- Monitor database performance

---

## Best Practices for API Integration

### 1. Token Storage

**DO**:
- Store refresh tokens in httpOnly cookies (most secure)
- Store access tokens in memory or sessionStorage for SPA
- Use secure storage mechanisms on mobile (Keychain, Keystore)

**DON'T**:
- Store tokens in localStorage if possible (XSS risk)
- Log tokens in console or logs
- Include tokens in URLs
- Store tokens in plain text files

### 2. Error Handling

**DO**:
- Handle all possible HTTP status codes
- Implement retry logic with exponential backoff
- Display user-friendly error messages
- Log errors for debugging

**DON'T**:
- Display raw API error messages to users
- Retry indefinitely
- Ignore rate limit errors

### 3. Security

**DO**:
- Always use HTTPS in production
- Validate all inputs on frontend
- Implement CSRF protection for state-changing operations
- Use Content Security Policy (CSP)

**DON'T**:
- Send passwords in GET requests
- Store passwords in localStorage
- Disable SSL certificate validation

### 4. Performance

**DO**:
- Cache user profile data
- Implement token refresh proactively (before expiration)
- Batch API requests when possible
- Use HTTP/2 for better performance

**DON'T**:
- Make unnecessary API calls
- Fetch user profile on every page load
- Ignore rate limits

---

**End of API Documentation**

---

## Quick Reference Card

### Authentication Endpoints
```
POST /auth/register      - Register new user
POST /auth/login         - Login with password
POST /auth/request-otp   - Request OTP
POST /auth/verify-otp    - Verify OTP
POST /auth/logout        - Logout
POST /auth/refresh-token - Refresh access token
GET  /auth/me            - Get current user
GET  /auth/google/login  - OAuth login
```

### Token Expiration
- Access Token: 30 minutes
- Refresh Token: 7 days
- OTP: 10 minutes

### Rate Limits
- Global: 100 req/min per IP
- OTP Request: 5/hour per email
- OTP Verify: 3/min per email
- Login: 5 per 15min per email

### Common Headers
```
Content-Type: application/json
Authorization: Bearer <token>
```

### Status Codes
- 200: Success
- 201: Created
- 400: Bad Request
- 401: Unauthorized
- 429: Rate Limited
- 500: Server Error
