# Auth Service - Business Logic Documentation

## Document Version
- **Version**: 1.0
- **Last Updated**: October 3, 2025
- **Service Name**: Auth Service
- **Business Domain**: Authentication, Authorization, and Security Management

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [User Authentication Workflows](#user-authentication-workflows)
3. [Account Registration and Verification](#account-registration-and-verification)
4. [Password Management](#password-management)
5. [OTP (One-Time Password) System](#otp-one-time-password-system)
6. [Token Lifecycle Management](#token-lifecycle-management)
7. [Google OAuth Integration](#google-oauth-integration)
8. [Session Management](#session-management)
9. [Security and Access Control](#security-and-access-control)
10. [Rate Limiting and Abuse Prevention](#rate-limiting-and-abuse-prevention)
11. [Email Communications](#email-communications)
12. [Account States and Status Management](#account-states-and-status-management)
13. [Error Handling and User Feedback](#error-handling-and-user-feedback)
14. [Business Rules and Constraints](#business-rules-and-constraints)
15. [Integration with Other Microservices](#integration-with-other-microservices)
16. [Security Audit and Monitoring](#security-audit-and-monitoring)

---

## 1. Executive Summary

The Auth Service serves as the **central security gateway** for the AI-powered EdTech platform. It implements a multi-layered authentication system supporting three primary authentication methods:

1. **Email/Password Authentication**: Traditional credential-based authentication with strong password requirements
2. **OTP-Based Authentication**: Passwordless authentication using email-delivered one-time passwords
3. **Google OAuth 2.0**: Social login integration with Google accounts

### Key Business Objectives

- **Security First**: Protect user accounts and platform resources through industry-standard security practices
- **Seamless User Experience**: Multiple authentication options to accommodate different user preferences
- **Scalability**: Designed to handle authentication for all platform microservices
- **Compliance Ready**: Built with security best practices for potential regulatory compliance
- **Abuse Prevention**: Comprehensive rate limiting and suspicious activity detection

### Target Users

- **Students**: Primary users accessing learning resources
- **Educators**: Content creators and course administrators
- **System Administrators**: Platform management and monitoring
- **External Services**: Other microservices requiring user authentication

---

## 2. User Authentication Workflows

### 2.1 Email/Password Login Workflow

**Business Flow**:

1. **User Initiation**
   - User provides email and password
   - System validates input format

2. **Rate Limit Check**
   - System checks if user has exceeded login attempts (5 attempts per 15 minutes)
   - If exceeded, return 429 error with retry time
   - Purpose: Prevent brute force attacks

3. **Credential Validation**
   - Retrieve user record by email (case-insensitive lookup)
   - If user not found, return generic error (don't reveal user existence)
   - Verify password using bcrypt comparison
   - If password invalid, return generic error
   - Add artificial delay (0.1s) to prevent timing attacks

4. **Account Status Verification**
   - Check if account is active (`is_active = True`)
   - If inactive, return error directing user to contact support
   - Check if email is verified (`is_verified = True`)
   - If unverified and `REQUIRE_EMAIL_VERIFICATION = True`, reject login

5. **Token Generation**
   - Generate JWT access token (30-minute expiration)
   - Generate JWT refresh token (7-day expiration with unique JTI)
   - Return both tokens with expiration times

6. **Response**
   - Return tokens and user profile information
   - Log successful login for security monitoring

**Business Rules**:
- Generic error messages prevent account enumeration
- Rate limiting prevents brute force attacks
- Timing attack prevention through artificial delays
- Email verification can be disabled for development/testing

**Success Criteria**:
- Valid credentials provided
- Account is active and verified
- Rate limits not exceeded
- Tokens successfully generated

---

### 2.2 OTP-Based Login Workflow

**Phase 1: OTP Request**

1. **User Initiation**
   - User provides email address
   - Specifies purpose = "login"

2. **Rate Limit Check**
   - Check OTP request rate limit (5 requests per hour per email)
   - If exceeded, return 429 error with retry time

3. **User Validation**
   - Look up user by email
   - If user not found, still return success (security measure to prevent enumeration)
   - Record rate limit attempt even for non-existent users

4. **OTP Generation**
   - Generate cryptographically secure 6-digit code
   - Hash OTP using bcrypt
   - Store hashed OTP in database with 10-minute expiration
   - Delete any existing OTP for same user/purpose

5. **Email Delivery**
   - Send OTP to user's email with branded template
   - Include expiration time (10 minutes)
   - Return success response with expiration time

**Phase 2: OTP Verification**

1. **User Submission**
   - User provides email, OTP code, and purpose

2. **Input Validation**
   - Validate OTP format (exactly 6 digits)
   - Sanitize email address

3. **Rate Limit Check**
   - Check verification rate limit (3 attempts per minute)
   - If exceeded, return 429 error

4. **OTP Verification**
   - Retrieve stored OTP for user and purpose
   - If not found, return error
   - Check if OTP expired
   - If expired, delete and return error
   - Verify provided OTP against hashed OTP using bcrypt
   - If valid, delete OTP (one-time use)

5. **Token Generation**
   - Generate access and refresh tokens
   - Return tokens and user profile

**Business Rules**:
- OTP valid for 10 minutes only
- One active OTP per user per purpose
- OTP is single-use (deleted after verification)
- Rate limits prevent abuse
- Non-existent users get simulated processing time

**Advantages**:
- Passwordless authentication option
- Better for users who forget passwords
- Reduces password management burden
- More secure than SMS OTP (email is more secure)

---

### 2.3 Google OAuth Login Workflow

**Phase 1: Authorization Request**

1. **User Initiation**
   - User clicks "Login with Google" button
   - System endpoint: `GET /auth/google/login`

2. **State Generation**
   - Generate secure random state parameter (CSRF protection)
   - Store state in memory with 30-minute expiration
   - Mark state as unused

3. **Redirect to Google**
   - Construct Google OAuth URL with parameters:
     - `client_id`: Platform's Google client ID
     - `redirect_uri`: Callback URL (`http://localhost:8006/auth/google/callback`)
     - `response_type`: "code"
     - `scope`: "openid email profile"
     - `access_type`: "offline"
     - `state`: Generated state parameter
   - Redirect user to Google authorization page

4. **User Authorization**
   - User authenticates with Google
   - User authorizes platform access to profile and email
   - Google redirects back to callback URL

**Phase 2: Callback Processing**

1. **State Validation**
   - Validate state parameter matches stored value
   - Check state not already used (one-time use)
   - Check state not expired (30 minutes)
   - Mark state as consumed

2. **Authorization Code Exchange**
   - Exchange authorization code for tokens
   - POST to Google token endpoint
   - Receive access token and ID token

3. **ID Token Verification**
   - Decode ID token (JWT)
   - Extract user information:
     - `sub`: Google user ID
     - `email`: User's email
     - `name`: User's full name
     - `email_verified`: Email verification status
   - Validate email is verified by Google

4. **User Account Processing**
   - **Scenario A: Existing Google User**
     - User found by google_id
     - Use existing account
   
   - **Scenario B: Account Linking**
     - User found by email but no google_id
     - Link Google ID to existing account
     - Update `google_id` field
     - Mark as verified if not already
   
   - **Scenario C: New User**
     - No existing user found
     - Create new user account
     - Set `google_id`, `email`, `full_name`
     - Set `is_verified = True` (pre-verified by Google)
     - Set `is_active = True`
     - No password (OAuth user)

5. **Token Generation**
   - Generate platform access token
   - Generate platform refresh token
   - Redirect to frontend with tokens in URL

**Business Rules**:
- Google users are pre-verified (skip email verification)
- Account linking happens automatically by email match
- One Google ID can link to one account
- OAuth users have no password (password field is NULL)
- State parameter prevents CSRF attacks
- 30-minute state expiration window

**Security Measures**:
- CSRF protection via state parameter
- One-time state usage
- Email verification required by Google
- Secure token exchange
- Account enumeration prevention

---

## 3. Account Registration and Verification

### 3.1 Standard Registration Workflow

**Phase 1: User Registration**

1. **User Input**
   - Email address (required, must be unique)
   - Password (optional - can register with OTP only)
   - Full name (optional)

2. **Input Validation**
   - **Email Validation**:
     - Format: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
     - Converted to lowercase
     - Whitespace stripped
   
   - **Password Validation** (if provided):
     - Minimum 8 characters
     - Maximum 128 characters
     - At least one lowercase letter
     - At least one uppercase letter
     - At least one digit
     - At least one special character (@$!%*?&)
   
   - **Full Name Validation**:
     - Maximum 100 characters
     - Minimum 1 character if provided
     - Control characters removed

3. **Security Checks**
   - Check for suspicious email domains (tempmail.org, etc.)
   - Check for bot-like user agents
   - If suspicious, reject registration

4. **Uniqueness Check**
   - Check if email already exists in database
   - If exists, return generic error (don't reveal user existence)

5. **Account Creation**
   - Hash password using bcrypt (if provided)
   - Create user record with:
     - `email`: Sanitized email
     - `hashed_password`: Bcrypt hash or NULL
     - `full_name`: Sanitized name
     - `is_active`: True
     - `is_verified`: False
     - `created_at`: Current timestamp

6. **Response**
   - Return user details (without password)
   - Status: 201 Created

**Phase 2: Email Verification** (if REQUIRE_EMAIL_VERIFICATION = True)

1. **OTP Request**
   - User requests verification OTP
   - Purpose = "verification"

2. **OTP Generation and Delivery**
   - Generate 6-digit OTP
   - Hash and store with 10-minute expiration
   - Send verification email

3. **OTP Verification**
   - User submits OTP
   - System verifies OTP
   - On success: Set `is_verified = True`

4. **Account Activated**
   - User can now login
   - Generate and return tokens

**Business Rules**:
- Email uniqueness enforced
- Password optional (supports OTP-only users)
- Email verification configurable
- Generic errors prevent account enumeration
- Suspicious registrations blocked
- Password never stored in plain text

---

### 3.2 OAuth Registration Workflow

**Process**:

1. **OAuth Flow Completion**
   - User completes Google OAuth flow
   - System receives verified user information from Google

2. **Automatic Account Creation**
   - Create user with Google information
   - Set `is_verified = True` (pre-verified by Google)
   - Set `is_active = True`
   - No password required
   - Store `google_id` for future logins

3. **Immediate Access**
   - User receives tokens immediately
   - No email verification needed
   - Can access platform right away

**Business Advantages**:
- Reduced friction (no email verification needed)
- Higher conversion rate
- Delegated authentication to trusted provider
- Better user experience

---

## 4. Password Management

### 4.1 Password Policy

**Minimum Requirements**:
- Length: 8-128 characters
- Complexity:
  - At least one lowercase letter (a-z)
  - At least one uppercase letter (A-Z)
  - At least one digit (0-9)
  - At least one special character (@$!%*?&)

**Allowed Special Characters**: `@$!%*?&`

**Business Rationale**:
- Balanced security and usability
- Prevents common weak passwords
- Meets industry security standards
- Not overly restrictive

---

### 4.2 Password Storage

**Algorithm**: bcrypt with automatic salt generation

**Process**:
1. Plain password received from user
2. bcrypt generates random salt
3. Password hashed with salt
4. Hash stored in database
5. Original password never stored

**Security Features**:
- Automatic salt generation (unique per password)
- Computationally expensive (prevents brute force)
- Adaptive cost factor (can increase over time)
- Industry-standard algorithm

**Cost Factor**: Default bcrypt cost (automatically managed by passlib)

---

### 4.3 Password Reset Workflow

**Phase 1: Reset Request**

1. **User Initiation**
   - User clicks "Forgot Password"
   - Provides email address

2. **OTP Request**
   - Purpose = "password_reset"
   - System generates OTP
   - Sends to user's email

3. **Rate Limiting**
   - Same rate limits as other OTP requests
   - 5 requests per hour per email

**Phase 2: OTP Verification**

1. **User Submission**
   - User enters OTP from email
   - Purpose = "password_reset"

2. **Verification**
   - System verifies OTP
   - Does NOT issue tokens
   - Returns success message

**Phase 3: Password Update** (Not implemented in current code)

*Note: Current implementation verifies OTP but does not have a password update endpoint. This would need to be added.*

**Recommended Implementation**:
```
POST /auth/reset-password
Request: {
  "email": "user@example.com",
  "otp_code": "123456",
  "new_password": "NewSecurePass123!"
}
Process:
1. Verify OTP (if not already verified)
2. Validate new password strength
3. Hash new password
4. Update user.hashed_password
5. Delete OTP
6. Invalidate all existing tokens (security measure)
7. Return success message
```

**Business Rules**:
- Password reset requires OTP verification
- All existing tokens should be invalidated
- User must login again with new password
- Reset link/OTP expires after 10 minutes

---

## 5. OTP (One-Time Password) System

### 5.1 OTP Generation

**Algorithm**:
- Cryptographically secure random generation using `secrets` module
- Format: Exactly 6 digits (000000-999999)
- Each digit randomly chosen from 0-9

**Business Rationale**:
- 6 digits balance security and usability
- Easy to manually type
- 1 million possible combinations
- Short expiration mitigates brute force risk

---

### 5.2 OTP Storage and Security

**Storage Method**:
- OTP hashed using bcrypt before storage
- Same algorithm as password hashing
- Never stored in plain text

**Database Record**:
- `user_id`: Link to user
- `email`: User email (redundant for compatibility)
- `otp_code`: Hashed OTP
- `purpose`: verification/login/password_reset
- `expires_at`: Expiration timestamp
- `created_at`: Creation timestamp

**Security Features**:
- Hashed storage prevents database leaks
- One active OTP per user per purpose
- Automatic expiration (10 minutes)
- Single-use (deleted after verification)
- Rate limited generation and verification

---

### 5.3 OTP Purposes

**1. Verification (Email Verification)**
- **Use Case**: Verify user email after registration
- **Flow**: Register → Request OTP → Verify OTP → Account verified
- **Effect**: Sets `is_verified = True`, issues tokens

**2. Login (Passwordless Login)**
- **Use Case**: Login without password
- **Flow**: Enter email → Request OTP → Verify OTP → Receive tokens
- **Effect**: Issues access and refresh tokens

**3. Password Reset**
- **Use Case**: Reset forgotten password
- **Flow**: Request reset → Verify OTP → Update password
- **Effect**: Confirms identity before password change
- **Note**: Update endpoint not yet implemented

**Business Rules**:
- Each purpose maintains separate OTP
- User can have 3 active OTPs (one per purpose)
- Expiration and rate limits apply to all purposes

---

### 5.4 OTP Expiration and Cleanup

**Expiration**:
- **Time to Live**: 10 minutes from generation
- **Timezone**: UTC
- **Enforcement**: Checked during verification

**Cleanup Process**:
1. **Automatic Cleanup**: 
   - Expired OTPs deleted on verification attempt
   - Failed verification due to expiration triggers deletion

2. **Periodic Cleanup** (Recommended):
   - Batch delete expired OTPs
   - Suggested: Daily cron job
   - Method: `otp_service.cleanup_expired_otps(db)`

**Business Rationale**:
- 10 minutes balances security and user convenience
- Automatic cleanup prevents database bloat
- Expired OTPs pose no security risk (cannot be verified)

---

## 6. Token Lifecycle Management

### 6.1 Access Token

**Purpose**: Short-lived token for API authentication

**Specifications**:
- **Type**: JWT (JSON Web Token)
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Expiration**: 30 minutes
- **Claims**:
  - `sub`: User ID (string)
  - `exp`: Expiration timestamp (Unix time)

**Usage**:
- Included in Authorization header: `Bearer <access_token>`
- Required for all protected endpoints
- Verified by `get_current_user` dependency

**Security Features**:
- Short expiration limits damage from token theft
- Stateless (no database lookup needed)
- Signed with SECRET_KEY (prevents tampering)

**Business Rationale**:
- 30 minutes provides good balance
- Short enough to limit exposure
- Long enough for typical user session
- Refresh mechanism for longer sessions

---

### 6.2 Refresh Token

**Purpose**: Long-lived token for obtaining new access tokens

**Specifications**:
- **Type**: JWT (JSON Web Token)
- **Algorithm**: HS256
- **Expiration**: 7 days
- **Claims**:
  - `sub`: User ID (string)
  - `exp`: Expiration timestamp
  - `jti`: JWT ID (unique identifier)

**Usage**:
- Stored securely by client (e.g., httpOnly cookie)
- Used to request new access token via `/auth/refresh-token`
- Can be invalidated via `/auth/logout`

**Security Features**:
- Unique JTI allows selective invalidation
- Longer expiration for user convenience
- Invalidation tracked in database (denylist)
- Cannot be reused after logout

**Business Rationale**:
- 7 days reduces login friction
- Users stay logged in across sessions
- Balance between security and convenience
- Allows "remember me" functionality

---

### 6.3 Token Refresh Flow

**Process**:

1. **Client Request**
   - POST to `/auth/refresh-token`
   - Provide refresh token in request body

2. **Token Validation**
   - Decode JWT
   - Extract `sub` (user_id) and `jti`
   - Check token not expired

3. **Denylist Check**
   - Query `invalidated_tokens` table for JTI
   - If found, reject (token was invalidated by logout)

4. **User Validation**
   - Retrieve user by ID
   - Check user exists
   - Check user is active

5. **New Access Token**
   - Generate new access token
   - Same user ID, new expiration
   - Return new access token (NOT new refresh token)

6. **Response**
   - New access token
   - Token type: "bearer"
   - Expiration time in seconds

**Business Rules**:
- Refresh token remains valid (single refresh token per session)
- Multiple access tokens can be issued from one refresh token
- Refresh token only invalidated by logout or expiration
- User must re-login after 7 days

**Security Considerations**:
- Refresh token should be stored securely (httpOnly cookie)
- Refresh endpoint should be rate limited
- User validation ensures inactive users can't get new tokens

---

### 6.4 Token Invalidation (Logout)

**Process**:

1. **Client Request**
   - POST to `/auth/logout`
   - Provide refresh token

2. **Token Decoding**
   - Decode JWT
   - Extract `jti`, `user_id`, `exp`

3. **Denylist Check**
   - Check if JTI already in denylist
   - If already present, return success (idempotent)

4. **Denylist Addition**
   - Create `InvalidatedToken` record:
     - `jti`: Token's unique identifier
     - `user_id`: User who logged out
     - `expires_at`: Original token expiration
     - `invalidated_at`: Current timestamp
   - Handle duplicate JTI gracefully (concurrent logout attempts)

5. **Response**
   - Success message: "Logout successful"
   - Status: 200 OK

**Business Rules**:
- Only refresh tokens are invalidated (access tokens expire naturally)
- Logout is idempotent (multiple calls return success)
- Expired tokens automatically cleaned from denylist
- User must login again to get new tokens

**Denylist Cleanup**:
- Expired tokens no longer pose security risk
- Periodic cleanup recommended (daily cron job)
- Method: `invalidated_token_crud.cleanup_expired_tokens()`
- Keeps denylist table size manageable

---

## 7. Google OAuth Integration

### 7.1 OAuth Configuration

**OAuth 2.0 Provider**: Google

**Required Credentials**:
- **Client ID**: Platform's Google OAuth client ID
- **Client Secret**: Platform's Google OAuth client secret
- **Redirect URI**: `http://localhost:8006/auth/google/callback`

**OAuth Scopes**:
- `openid`: OpenID Connect
- `email`: User's email address
- `profile`: User's basic profile information

**Configuration Location**: Environment variables in `.env`

---

### 7.2 Security Measures

**CSRF Protection**:
- **State Parameter**: Secure random string (32 bytes, URL-safe)
- **Storage**: In-memory with 30-minute expiration
- **Validation**: One-time use, must match stored value
- **Cleanup**: Automatic cleanup of expired states every 10 minutes

**Token Validation**:
- ID token decoded and validated
- Required claims verified:
  - `sub`: Google user ID (required)
  - `email`: User email (required)
  - `email_verified`: Must be true
  - `name`: User's name (optional, defaults to empty)

**Error Handling**:
- Authorization errors from Google logged and returned
- Token exchange failures handled gracefully
- Malformed ID tokens rejected
- Missing required claims rejected

---

### 7.3 Account Linking Logic

**Decision Tree**:

```
1. Receive Google user info (google_id, email, name)
   
2. Check if user exists by google_id
   IF FOUND:
     → Use existing account
     → Return tokens
   
3. Check if user exists by email
   IF FOUND:
     → Link Google ID to existing account
     → Set google_id field
     → Set is_verified = True (if not already)
     → Return tokens
   
4. No existing user found
   → Create new user account
   → Set google_id, email, full_name
   → Set is_verified = True
   → Set is_active = True
   → No password (NULL)
   → Return tokens
```

**Business Rules**:
- Email is the primary linking identifier
- One Google ID per account
- One email per account
- Existing users can link Google account
- Google users automatically verified
- Account linking is transparent to user

**Benefits**:
- Users can switch between authentication methods
- Existing users can add OAuth for convenience
- No duplicate accounts for same email
- Seamless migration from password to OAuth

---

### 7.4 OAuth Error Scenarios

**1. Authorization Denied**
- **Cause**: User clicks "Cancel" on Google consent screen
- **Response**: 400 Bad Request with error detail
- **User Action**: Retry login or use different method

**2. Invalid Authorization Code**
- **Cause**: Code expired or already used
- **Response**: 400 Bad Request
- **User Action**: Restart OAuth flow

**3. State Validation Failure**
- **Cause**: CSRF attack attempt or expired state
- **Response**: 401 Unauthorized
- **User Action**: Restart OAuth flow
- **Security**: Logs suspicious activity

**4. Email Not Verified**
- **Cause**: User's Google email not verified
- **Response**: 400 Bad Request
- **User Action**: Verify email with Google first

**5. Network Errors**
- **Cause**: Cannot connect to Google services
- **Response**: 503 Service Unavailable
- **User Action**: Retry or use alternative login

---

## 8. Session Management

### 8.1 Session Concept

**Implementation**: Token-based (stateless)

The Auth Service uses **stateless JWT tokens** rather than traditional server-side sessions:

- **No Session Storage**: No session data stored on server
- **Client-Side State**: Tokens stored by client (localStorage, cookies)
- **Stateless Verification**: Each request verified independently
- **Scalability**: No session synchronization needed across servers

**Advantages**:
- Horizontal scalability (no session affinity needed)
- No session storage overhead
- Simple microservice integration
- Works across domains (CORS-enabled)

**Trade-offs**:
- Cannot immediately revoke access tokens (must wait for expiration)
- Refresh token denylist needed for logout
- Token size larger than session ID

---

### 8.2 Token Storage Recommendations

**Client-Side Storage Options**:

**1. HttpOnly Cookies (Recommended for Web)**
- **Advantages**:
  - Protected from XSS attacks
  - Automatically included in requests
  - Cannot be accessed by JavaScript
- **Usage**:
  - Store refresh token in httpOnly cookie
  - Store access token in memory or short-lived cookie
- **Security**: Best for web applications

**2. Local Storage**
- **Advantages**:
  - Simple to implement
  - Persists across browser sessions
  - Works for SPA applications
- **Disadvantages**:
  - Vulnerable to XSS attacks
  - Should only store access token, not refresh token
- **Security**: Acceptable if XSS prevention measures in place

**3. Session Storage**
- **Advantages**:
  - Cleared on browser close
  - Isolated per tab
- **Disadvantages**:
  - Vulnerable to XSS
  - Doesn't persist
- **Usage**: Temporary sessions only

**4. Memory Only**
- **Advantages**:
  - Most secure against XSS
  - Cleared on page refresh
- **Disadvantages**:
  - Poor user experience (must login frequently)
- **Usage**: High-security applications

**Current Implementation**: Client stores tokens (frontend responsibility)

---

### 8.3 Concurrent Sessions

**Policy**: Multiple concurrent sessions allowed

**Implementation**:
- Each login generates new token pair
- Multiple refresh tokens can be active simultaneously
- No limit on concurrent sessions (configurable if needed)

**Business Rationale**:
- Users often use multiple devices (phone, laptop, tablet)
- Convenience over strict security
- Users can logout from each device independently

**Security Considerations**:
- Logout only invalidates specific refresh token
- Other devices remain logged in
- Security-conscious users can implement "logout all devices" feature

**Recommended Enhancement**:
```
Implement "Logout All Devices":
1. Store refresh token JTI per user
2. Add endpoint: POST /auth/logout-all
3. Invalidate all user's refresh tokens
4. User must re-login on all devices
```

---

### 8.4 Session Timeout

**Access Token Timeout**: 30 minutes
- Automatic expiration (cannot be extended)
- Must use refresh token to get new access token

**Refresh Token Timeout**: 7 days
- After 7 days, user must re-authenticate
- Cannot be extended (security measure)

**Idle Timeout**: Not implemented (stateless tokens)
- Could be implemented with last-activity tracking
- Would require database state

**Business Impact**:
- 30-minute access token = user inactive for 30 min must refresh
- 7-day refresh token = user must login weekly
- Balance between security and convenience

**Configurable Timeouts**:
- `ACCESS_TOKEN_EXPIRE_MINUTES`: Default 30
- `REFRESH_TOKEN_EXPIRE_DAYS`: Default 7
- Can be adjusted per business requirements

---

## 9. Security and Access Control

### 9.1 Authentication vs Authorization

**Authentication** (Implemented):
- Verifies user identity (who you are)
- JWT token validation
- Password verification
- OTP verification
- OAuth provider verification

**Authorization** (Partially Implemented):
- Determines user permissions (what you can do)
- Currently implemented:
  - Active user check (`is_active`)
  - Verified user check (`is_verified`)
- Not yet implemented:
  - Role-based access control (RBAC)
  - Resource-level permissions
  - Fine-grained access control

---

### 9.2 Current Authorization Levels

**Level 1: Authenticated User**
- **Requirement**: Valid access token
- **Dependency**: `get_current_user`
- **Access**: Basic API access

**Level 2: Active User**
- **Requirement**: Valid token + `is_active = True`
- **Dependency**: `get_current_active_user`
- **Access**: Full platform access
- **Use Case**: Prevent suspended users from accessing platform

**Level 3: Verified User**
- **Requirement**: Valid token + `is_verified = True`
- **Dependency**: `get_current_verified_user`
- **Access**: Features requiring verified email
- **Use Case**: Restrict sensitive features to verified users

---

### 9.3 Role-Based Access Control (Future Enhancement)

**Recommended Implementation**:

**Roles**:
- `student`: Basic learner access
- `educator`: Content creation and course management
- `admin`: Platform administration
- `support`: Customer support access

**Database Changes Needed**:
```sql
-- Add roles table
CREATE TABLE roles (
  id SERIAL PRIMARY KEY,
  name VARCHAR(50) UNIQUE NOT NULL,
  description TEXT
);

-- Add user_roles junction table
CREATE TABLE user_roles (
  user_id INTEGER REFERENCES users(id),
  role_id INTEGER REFERENCES roles(id),
  granted_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (user_id, role_id)
);
```

**Dependency Usage**:
```python
@router.get("/admin/users")
async def list_users(
    current_user: dict = Depends(require_roles("admin"))
):
    # Only admin users can access
    ...
```

**Business Rules**:
- Users can have multiple roles
- Roles checked during request processing
- Role changes take effect immediately (stateless tokens)
- Default role: "student" on registration

---

### 9.4 Security Headers

**Implemented Headers**:

| Header | Value | Purpose |
|--------|-------|---------|
| `X-Content-Type-Options` | `nosniff` | Prevent MIME sniffing attacks |
| `X-Frame-Options` | `DENY` | Prevent clickjacking |
| `X-XSS-Protection` | `1; mode=block` | Enable browser XSS filter |
| `Referrer-Policy` | `strict-origin-when-cross-origin` | Control referrer information leakage |
| `Content-Security-Policy` | (see below) | Restrict resource loading |

**Content Security Policy**:
```
default-src 'self';
script-src 'self';
style-src 'self' 'unsafe-inline';
img-src 'self' data:;
font-src 'self';
connect-src 'self';
frame-ancestors 'none';
```

**Server Header Removal**:
- Removes `Server` header to hide server technology

**Business Impact**:
- Protects against common web vulnerabilities
- Meets security best practices
- Compliance with security standards
- Defense in depth strategy

---

## 10. Rate Limiting and Abuse Prevention

### 10.1 Rate Limiting Strategy

**Multi-Layer Approach**:

**Layer 1: Global Rate Limit**
- **Scope**: All endpoints
- **Limit**: 100 requests per minute per IP address
- **Implementation**: Middleware (applies first)
- **Purpose**: Prevent DDoS and API abuse

**Layer 2: Endpoint-Specific Rate Limits**
- **Scope**: Security-sensitive endpoints
- **Implemented For**:
  - OTP requests
  - OTP verifications
  - Login attempts
- **Purpose**: Prevent targeted attacks

---

### 10.2 Specific Rate Limits

**OTP Request Rate Limit**:
- **Limit**: 5 requests per hour per email
- **Window**: 1 hour (rolling)
- **Purpose**: Prevent OTP spam and email abuse
- **Response**: 429 with seconds until reset

**OTP Verification Rate Limit**:
- **Limit**: 3 attempts per minute per email
- **Window**: 1 minute (rolling)
- **Purpose**: Prevent brute force OTP guessing
- **Response**: 429 with seconds until reset
- **Note**: With 1M possible OTPs and 10-min expiration, brute force infeasible

**Login Rate Limit**:
- **Limit**: 5 attempts per 15 minutes per email
- **Window**: 15 minutes (rolling)
- **Purpose**: Prevent password brute force
- **Response**: 429 with seconds until reset

**Global Rate Limit**:
- **Limit**: 100 requests per minute per IP
- **Window**: 1 minute (rolling)
- **Purpose**: Prevent API abuse and DDoS
- **Response**: 429 with error message

---

### 10.3 Rate Limit Implementation

**Storage**: In-memory (dictionary-based)

**Data Structure**:
```python
{
  "identifier": [(timestamp, attempt_count), ...]
}
```

**Cleanup Strategy**:
- Automatic cleanup every 5 minutes
- Removes entries older than 1 hour
- Prevents memory bloat

**Advantages**:
- Fast (no database queries)
- Simple implementation
- Suitable for single-server deployment

**Limitations**:
- Not shared across multiple servers
- Lost on server restart
- Memory usage grows with users

**Production Recommendation**:
- Use Redis for distributed rate limiting
- Shared state across multiple servers
- Persistent across restarts
- Better performance at scale

---

### 10.4 Abuse Prevention Measures

**1. Suspicious Email Detection**
- **Detected Domains**: 
  - tempmail.org
  - 10minutemail.com
  - guerrillamail.com
- **Action**: Block registration
- **Purpose**: Prevent fake accounts

**2. Bot Detection**
- **User Agent Analysis**: 
  - Detect bot-like patterns
  - Keywords: "bot", "crawler", "spider", "scraper"
- **Action**: Block registration
- **Purpose**: Prevent automated abuse

**3. Timing Attack Prevention**
- **Implementation**: Artificial delays for non-existent users
- **Duration**: 0.1 seconds
- **Purpose**: Prevent user enumeration via response time

**4. Account Enumeration Prevention**
- **Strategy**: Generic error messages
- **Examples**:
  - "Invalid email or password" (don't say which is wrong)
  - "If the email exists, OTP has been sent" (don't confirm existence)
- **Purpose**: Prevent attackers from discovering valid accounts

**5. Input Sanitization**
- **Applied To**: All user inputs
- **Techniques**:
  - Remove control characters
  - Strip whitespace
  - Enforce length limits
  - Format validation
- **Purpose**: Prevent injection attacks (SQL, XSS, etc.)

**6. OTP Security**
- **Hashed Storage**: OTPs hashed before storage
- **Single Use**: Deleted after verification
- **Expiration**: 10-minute TTL
- **Rate Limiting**: Multiple layers
- **Purpose**: Prevent OTP-based attacks

---

## 11. Email Communications

### 11.1 Email Service Configuration

**SMTP Settings**:
- **Host**: Configurable (e.g., smtp.gmail.com)
- **Port**: Configurable (default: 587 for STARTTLS)
- **Authentication**: Username and password
- **Encryption**: STARTTLS or SSL/TLS

**Email Provider Requirements**:
- Must support SMTP
- Recommended: Gmail, SendGrid, AWS SES, Mailgun
- Must allow app-specific passwords (for Gmail)

**Fallback Behavior**:
- If email not configured, OTP printed to console
- Useful for development and testing
- Production must have email configured

---

### 11.2 Email Templates

**OTP Email Template**:

**Subject Lines** (by purpose):
- Verification: "Verify Your Email - AI EdTech Platform"
- Login: "Your Login Code - AI EdTech Platform"
- Password Reset: "Password Reset Code - AI EdTech Platform"

**Template Structure**:
```html
<div style="font-family: Arial, sans-serif; max-width: 600px;">
  <h2>AI EdTech Platform</h2>
  <p>Hello [User Name],</p>
  <p>Your One-Time Password (OTP) to [action] is:</p>
  <div style="background: #f4f4f4; padding: 20px; text-align: center;">
    <h1 style="color: #007bff; font-size: 32px; letter-spacing: 5px;">
      [OTP CODE]
    </h1>
  </div>
  <p>This OTP will expire in [X] minutes.</p>
  <p>If you did not request this OTP, please ignore this email.</p>
  <hr>
  <p style="color: #666; font-size: 12px;">
    Thanks,<br>The AI EdTech Platform Team
  </p>
</div>
```

**Template Features**:
- Branded header
- Clear OTP display (large, monospaced)
- Expiration notice
- Security warning (ignore if not requested)
- Professional footer
- Mobile-responsive design

---

### 11.3 Email Delivery Workflow

**Process**:

1. **Trigger Event**
   - OTP request received
   - User verified in database

2. **Email Preparation**
   - Select template based on purpose
   - Personalize with user's name (if available)
   - Insert OTP code
   - Set expiration time

3. **SMTP Connection**
   - Connect to SMTP server
   - Authenticate with credentials
   - Use STARTTLS for encryption

4. **Email Sending**
   - Send HTML email
   - Include proper headers
   - Set from address

5. **Error Handling**
   - Log sending errors
   - Raise exception on failure
   - Retry not implemented (recommended for production)

6. **Confirmation**
   - Log successful send
   - Return to caller

**Business Rules**:
- Emails sent asynchronously (async function)
- Failure raises exception (OTP request fails)
- No retry logic (should be added for production)
- Delivery not confirmed (no read receipts)

---

### 11.4 Email Deliverability

**Best Practices** (Recommendations):

**1. SPF Records**
- Publish SPF record for sending domain
- Prevents email spoofing
- Improves deliverability

**2. DKIM Signing**
- Sign emails with DKIM
- Verifies email authenticity
- Reduces spam classification

**3. DMARC Policy**
- Implement DMARC policy
- Provides reporting on email abuse
- Enhances security

**4. Sender Reputation**
- Use reputable email service (SendGrid, etc.)
- Monitor bounce rates
- Handle unsubscribes properly

**5. Email Content**
- Avoid spam trigger words
- Include unsubscribe link (for marketing emails)
- Use plain text + HTML multipart
- Keep HTML simple and clean

**Current Implementation**:
- Basic SMTP sending
- HTML email support
- STARTTLS encryption
- No SPF/DKIM/DMARC (infrastructure configuration)

---

## 12. Account States and Status Management

### 12.1 User Status Fields

**is_active (Boolean)**
- **Default**: True
- **Purpose**: Enable/disable account
- **Use Cases**:
  - Account suspension
  - Temporary deactivation
  - Compliance requirements
- **Effect**: Inactive users cannot login or refresh tokens

**is_verified (Boolean)**
- **Default**: False (True for OAuth users)
- **Purpose**: Track email verification
- **Use Cases**:
  - Email verification required for login
  - Feature gating (verified users only)
  - Trust level indicator
- **Effect**: Unverified users blocked from login (if `REQUIRE_EMAIL_VERIFICATION = True`)

---

### 12.2 Account Lifecycle

**State 1: Registered (Unverified)**
- **Conditions**: `is_active=True`, `is_verified=False`
- **Capabilities**:
  - Can request verification OTP
  - Can receive emails
  - Cannot login (if verification required)
- **Transitions**:
  - → Verified (via OTP verification)
  - → Suspended (admin action)

**State 2: Verified (Active)**
- **Conditions**: `is_active=True`, `is_verified=True`
- **Capabilities**:
  - Can login
  - Full platform access
  - Can link OAuth accounts
- **Transitions**:
  - → Suspended (admin action)

**State 3: Suspended**
- **Conditions**: `is_active=False`, `is_verified=*`
- **Capabilities**:
  - Cannot login
  - Cannot refresh tokens
  - Account locked
- **Transitions**:
  - → Active (admin reactivation)
  - → Deleted (admin action)

**State 4: OAuth User (Special Case)**
- **Conditions**: `is_active=True`, `is_verified=True`, `hashed_password=NULL`, `google_id!=NULL`
- **Capabilities**:
  - Can login via Google OAuth only
  - Cannot use password login
  - Can set password to enable password login
- **Transitions**:
  - → Password-enabled (set password)
  - → Suspended (admin action)

---

### 12.3 Account Suspension

**Reasons for Suspension**:
- Terms of service violation
- Suspicious activity
- User request (self-suspension)
- Payment issues (for paid features)
- Regulatory compliance

**Process**:
1. Admin sets `is_active = False`
2. All active tokens remain valid until expiration
3. User cannot refresh tokens (new tokens denied)
4. User sees "Account is deactivated" message on login
5. User directed to contact support

**Recommended Implementation**:
```
POST /auth/admin/suspend-user
Request: {
  "user_id": 123,
  "reason": "Terms of service violation",
  "notify_user": true
}
Process:
1. Verify admin authentication
2. Set user.is_active = False
3. Optionally invalidate all user's refresh tokens
4. Log suspension with reason
5. Send email notification (if requested)
```

**Reactivation**:
1. Admin sets `is_active = True`
2. User can immediately login again
3. Previous refresh tokens may still be valid
4. Send reactivation email notification

---

### 12.4 Account Deletion

**Not Currently Implemented**

**Recommended Implementation**:

**Soft Delete**:
- Add `deleted_at` timestamp field
- Set timestamp instead of removing record
- Exclude deleted users from queries
- Retain data for compliance/recovery

**Hard Delete**:
- Actually remove user record
- Cascade delete related data (OTPs, invalidated tokens)
- Consider data retention requirements
- GDPR compliance considerations

**Process**:
1. User or admin initiates deletion
2. Optionally: Grace period (e.g., 30 days) for recovery
3. Invalidate all tokens
4. Mark as deleted or remove record
5. Send confirmation email
6. Handle associated data per data retention policy

**Business Considerations**:
- GDPR "right to be forgotten"
- Data retention policies
- Audit trail requirements
- Associated content handling

---

## 13. Error Handling and User Feedback

### 13.1 Error Response Format

**Standard Error Response**:
```json
{
  "detail": "Error message here"
}
```

**Status Codes Used**:
- `400 Bad Request`: Invalid input, validation errors
- `401 Unauthorized`: Invalid/expired/missing token
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server-side errors
- `502 Bad Gateway`: External service errors (Google OAuth)
- `503 Service Unavailable`: Service temporarily unavailable

---

### 13.2 Security-Conscious Error Messages

**Principle**: Don't leak sensitive information

**Examples**:

**Bad** (reveals too much):
```json
{
  "detail": "User with email john@example.com not found"
}
```

**Good** (generic):
```json
{
  "detail": "Invalid email or password"
}
```

**Bad** (reveals user existence):
```json
{
  "detail": "Incorrect password for john@example.com"
}
```

**Good** (ambiguous):
```json
{
  "detail": "Invalid email or password"
}
```

**Implementation**:
- Same error message for "user not found" and "wrong password"
- OTP requests return success even for non-existent emails
- Registration errors generic ("Registration failed")
- Timing attacks prevented with artificial delays

---

### 13.3 Rate Limit Error Messages

**Format**:
```json
{
  "detail": "Too many [action]. Please try again in [X] seconds."
}
```

**Examples**:
```json
{
  "detail": "Too many OTP requests. Please try again in 2847 seconds."
}
```

```json
{
  "detail": "Too many login attempts. Please try again in 673 seconds."
}
```

**User-Friendly Display** (recommended frontend conversion):
- 60 seconds → "1 minute"
- 3600 seconds → "1 hour"
- 300 seconds → "5 minutes"

---

### 13.4 Validation Error Messages

**Password Validation**:
```json
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long"
    }
  ]
}
```

**Email Validation**:
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

**OTP Validation**:
```json
{
  "detail": "OTP code must be exactly 6 digits"
}
```

**Business Impact**:
- Clear error messages improve user experience
- Specific validation errors help users correct input
- Security messages remain appropriately vague

---

## 14. Business Rules and Constraints

### 14.1 Core Business Rules

**Email Uniqueness**:
- One account per email address
- Case-insensitive comparison (emails normalized to lowercase)
- Prevents duplicate accounts
- Enforced at database level (unique constraint)

**Password Optional**:
- Users can register without password (OTP-only)
- OAuth users have no password
- Password can be set later (not yet implemented)
- Flexibility for different authentication preferences

**Email Verification**:
- Configurable requirement (`REQUIRE_EMAIL_VERIFICATION`)
- Default: Required for login
- Can be disabled for development
- OAuth users pre-verified

**Account Activity**:
- Inactive accounts cannot login
- Inactive accounts cannot refresh tokens
- Admins can activate/deactivate accounts
- No automatic inactivity timeout

**Token Expiration**:
- Access tokens: 30 minutes (not renewable)
- Refresh tokens: 7 days (not renewable)
- After expiration, must re-authenticate
- Security over convenience

**Rate Limits**:
- Global: 100 req/min per IP
- OTP requests: 5/hour per email
- OTP verification: 3/min per email
- Login: 5 per 15min per email
- Non-negotiable (security requirement)

**OTP Validity**:
- 10-minute expiration
- Single-use only
- Hashed storage
- One active OTP per user per purpose

---

### 14.2 Configuration-Driven Rules

**Configurable Via Environment Variables**:

| Rule | Variable | Default | Impact |
|------|----------|---------|--------|
| Email verification required | `REQUIRE_EMAIL_VERIFICATION` | True | Login restriction |
| Access token expiration | `ACCESS_TOKEN_EXPIRE_MINUTES` | 30 | Session length |
| Refresh token expiration | `REFRESH_TOKEN_EXPIRE_DAYS` | 7 | Login frequency |
| OTP expiration | `OTP_EXPIRY_MINUTES` | 10 | OTP validity window |
| OTP max attempts | `OTP_MAX_ATTEMPTS` | 3 | Verification rate limit |
| OTP requests per hour | `OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR` | 5 | Request rate limit |
| CORS origins | `BACKEND_CORS_ORIGINS` | Dev defaults | API access control |

**Business Flexibility**:
- Adjust security/convenience balance per environment
- Stricter rules for production
- Relaxed rules for development
- Easy A/B testing of settings

---

### 14.3 Data Integrity Rules

**Database Constraints**:
- `users.email`: Unique, not null
- `users.google_id`: Unique, nullable
- `otps.user_id`: Foreign key to users.id
- `otps.expires_at`: Not null
- `invalidated_tokens.jti`: Unique, not null

**Automatic Timestamps**:
- `created_at`: Set on record creation
- `updated_at`: Updated on record modification
- Timezone-aware (UTC)

**Cleanup Requirements**:
- Expired OTPs should be deleted
- Expired invalidated tokens should be deleted
- Recommended: Daily cleanup cron job

---

## 15. Integration with Other Microservices

### 15.1 Service-to-Service Authentication

**Current Implementation**: Not explicitly defined

**Recommended Pattern**: JWT Token Validation

**Process**:
1. Frontend obtains token from auth service
2. Frontend includes token in requests to other services
3. Other services validate token:
   - Decode JWT
   - Verify signature using shared SECRET_KEY
   - Extract user_id from `sub` claim
   - Optionally query auth service for user details

**Shared Secret Approach**:
- All services share same SECRET_KEY
- Each service can validate tokens independently
- No network call to auth service needed
- Stateless and scalable

**Alternative: Token Introspection Endpoint**:
```
POST /auth/validate-token
Request: {
  "access_token": "eyJhbGc..."
}
Response: {
  "valid": true,
  "user_id": 123,
  "email": "user@example.com",
  "is_active": true,
  "is_verified": true
}
```

**Benefits**:
- Centralized validation
- Can check user status (active/verified)
- Can revoke tokens centrally
- Better audit trail

---

### 15.2 User Information Sharing

**Current Endpoints**:
- `GET /auth/me`: Get current user info (requires token)

**Recommended Enhancements**:

**1. User Lookup Endpoint** (Service-to-Service):
```
GET /auth/users/{user_id}
Headers: {
  "X-Service-Token": "service_secret_token"
}
Response: {
  "id": 123,
  "email": "user@example.com",
  "full_name": "John Doe",
  "is_active": true,
  "is_verified": true,
  "created_at": "2025-06-08T10:00:00Z"
}
```

**2. Batch User Lookup**:
```
POST /auth/users/batch
Request: {
  "user_ids": [123, 456, 789]
}
Response: {
  "users": [...]
}
```

**3. User Search** (Admin):
```
GET /auth/users?email=john@example.com
GET /auth/users?page=1&limit=50
```

---

### 15.3 Authorization Delegation

**Concept**: Other services delegate authorization to auth service

**Recommended Implementation**:

**Permission Check Endpoint**:
```
POST /auth/check-permission
Request: {
  "user_id": 123,
  "resource": "course",
  "action": "edit"
}
Response: {
  "allowed": true
}
```

**Role Check Endpoint**:
```
POST /auth/check-roles
Request: {
  "user_id": 123,
  "required_roles": ["educator", "admin"]
}
Response: {
  "has_roles": true,
  "matched_roles": ["educator"]
}
```

**Benefits**:
- Centralized authorization logic
- Consistent access control across services
- Easier to audit and modify permissions
- Single source of truth

---

### 15.4 Event Notifications

**Recommended Events** (to other services):

**User Events**:
- `user.registered`: New user created
- `user.verified`: Email verified
- `user.logged_in`: Successful login
- `user.logged_out`: User logged out
- `user.suspended`: Account suspended
- `user.reactivated`: Account reactivated

**Security Events**:
- `security.failed_login`: Failed login attempt
- `security.rate_limit_exceeded`: Rate limit hit
- `security.suspicious_activity`: Suspicious behavior detected

**Implementation Options**:
- Message queue (RabbitMQ, Kafka)
- Webhook endpoints
- Event bus (Redis Pub/Sub)
- Direct HTTP calls

**Business Value**:
- Other services can react to auth events
- Analytics tracking
- Email notifications
- Fraud detection
- User activity timeline

---

## 16. Security Audit and Monitoring

### 16.1 Logging Strategy

**Current Implementation**:

**Request Logging**:
- All requests logged with:
  - HTTP method
  - URL
  - Client IP
  - User agent
  - Response status
  - Processing time

**Log Levels**:
- `INFO`: State-changing requests (POST, PUT, DELETE)
- `DEBUG`: Read requests (GET)
- `WARNING`: 4xx/5xx responses, slow requests (>2s)

**Security Events Logged**:
- Failed login attempts
- Rate limit exceeded
- Suspicious activity detected
- Token validation failures

---

### 16.2 Recommended Audit Events

**Authentication Events**:
- Login success (user_id, IP, timestamp)
- Login failure (email, IP, reason, timestamp)
- Logout (user_id, IP, timestamp)
- Token refresh (user_id, IP, timestamp)
- OTP request (email, purpose, IP, timestamp)
- OTP verification success/failure

**Account Events**:
- Registration (email, IP, timestamp)
- Email verification (user_id, timestamp)
- Password change (user_id, IP, timestamp)
- Account suspension (user_id, admin_id, reason)
- Account reactivation (user_id, admin_id)
- OAuth account linking (user_id, provider)

**Security Events**:
- Rate limit exceeded (IP, endpoint, timestamp)
- Suspicious activity detected (details)
- Invalid token usage (token_id, IP)
- CSRF attempt (state_validation_failure)

---

### 16.3 Monitoring Metrics

**Recommended Metrics**:

**Performance**:
- Request latency (p50, p95, p99)
- Requests per second
- Error rate
- Database query time

**Security**:
- Failed login rate
- Rate limit hit rate
- Suspicious activity count
- Token validation failure rate
- OTP verification failure rate

**Business**:
- New registrations per day
- Active users (logins per day)
- OAuth vs password logins ratio
- Email verification completion rate
- Average time to verify email

**Operational**:
- Database connection pool usage
- Memory usage
- CPU usage
- Email delivery success rate

---

### 16.4 Security Alerts

**Recommended Alerts**:

**Critical**:
- Spike in failed logins (>100 in 1 min)
- Multiple rate limit violations from single IP
- Database connection failures
- Email service unavailable

**Warning**:
- Elevated error rate (>5%)
- Slow response times (>2s avg)
- High rate limit hit rate
- Suspicious activity patterns

**Info**:
- New user registrations
- OAuth account linkings
- Account suspensions

**Alert Channels**:
- Email (for critical)
- Slack/Teams (for warnings)
- Dashboard (for info)
- PagerDuty (for production critical)

---

## Business Value Summary

### Core Value Propositions

**1. Security Foundation**
- Protects user accounts and platform integrity
- Industry-standard security practices
- Multi-layered defense approach
- Compliance-ready architecture

**2. User Experience**
- Multiple authentication methods
- Passwordless option (OTP)
- Social login (Google OAuth)
- Seamless session management

**3. Scalability**
- Stateless JWT tokens
- Microservice-ready architecture
- Horizontal scalability
- No session synchronization needed

**4. Flexibility**
- Configurable security policies
- Environment-driven configuration
- Support for various authentication flows
- Extensible for future requirements

**5. Operational Excellence**
- Comprehensive logging
- Security monitoring
- Error tracking
- Performance metrics

---

## Future Enhancements Roadmap

### Phase 1: Core Improvements
- [ ] Password reset flow completion
- [ ] "Logout all devices" functionality
- [ ] Role-based access control (RBAC)
- [ ] User profile management endpoints

### Phase 2: Security Enhancements
- [ ] Two-factor authentication (2FA)
- [ ] Biometric authentication support
- [ ] IP whitelisting/blacklisting
- [ ] Advanced fraud detection

### Phase 3: Scale and Performance
- [ ] Redis-based rate limiting
- [ ] Token introspection endpoint
- [ ] Batch user operations
- [ ] Caching layer

### Phase 4: Compliance and Audit
- [ ] GDPR compliance features
- [ ] Comprehensive audit trail
- [ ] Data export functionality
- [ ] Privacy controls

### Phase 5: Advanced Features
- [ ] Magic link authentication
- [ ] Social login (Facebook, Apple, etc.)
- [ ] Enterprise SSO (SAML, LDAP)
- [ ] API key management

---

**End of Business Logic Documentation**
