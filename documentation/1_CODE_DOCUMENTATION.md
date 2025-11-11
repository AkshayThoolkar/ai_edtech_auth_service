# Auth Service - Complete Code Documentation

## Document Version
- **Version**: 1.0
- **Last Updated**: October 3, 2025
- **Service Name**: Auth Service
- **Service Port**: 8006
- **Framework**: FastAPI 
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Authentication**: JWT (JSON Web Tokens) with bcrypt password hashing

---

## Table of Contents
1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Core Components](#core-components)
4. [Database Models](#database-models)
5. [API Schemas](#api-schemas)
6. [CRUD Operations](#crud-operations)
7. [Services Layer](#services-layer)
8. [Middleware](#middleware)
9. [Dependencies](#dependencies)
10. [Database Migrations](#database-migrations)
11. [Configuration](#configuration)
12. [Testing Infrastructure](#testing-infrastructure)
13. [Dependencies and Libraries](#dependencies-and-libraries)

---

## 1. Overview

The **Auth Service** is a critical security microservice within the AI-powered EdTech platform responsible for:
- User authentication and authorization
- JWT token generation, validation, and refresh
- OTP (One-Time Password) generation and verification
- Google OAuth 2.0 integration
- Session management and logout functionality
- Security hardening with rate limiting and input validation
- Email-based verification workflows

The service uses **PostgreSQL** as its primary database and implements industry-standard security practices including bcrypt password hashing, JWT token management, CSRF protection, and comprehensive rate limiting.

---

## 2. Directory Structure

```
auth_service/
├── main.py                          # FastAPI application entry point
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment variables template
├── alembic.ini                      # Alembic migration configuration
│
├── core/                            # Core utilities and configuration
│   ├── __init__.py
│   ├── config.py                    # Application settings and environment variables
│   └── security.py                  # JWT token generation and password hashing
│
├── models/                          # SQLAlchemy database models
│   ├── __init__.py
│   ├── user_model.py                # User database model
│   ├── otp_model.py                 # OTP database model
│   └── invalidated_token_model.py   # Token denylist model
│
├── schemas/                         # Pydantic schemas for request/response
│   ├── __init__.py
│   ├── user_schema.py               # User-related schemas
│   ├── token_schema.py              # Token-related schemas
│   └── otp_schema.py                # OTP-related schemas
│
├── crud/                            # Database CRUD operations
│   ├── __init__.py
│   ├── user_crud.py                 # User CRUD operations
│   ├── otp_crud.py                  # OTP CRUD operations
│   └── invalidated_token_crud.py    # Token invalidation CRUD
│
├── routers/                         # API route handlers
│   ├── __init__.py
│   ├── auth_router.py               # Authentication endpoints
│   └── dependencies.py              # FastAPI dependencies
│
├── services/                        # Business logic services
│   ├── __init__.py
│   ├── otp_service.py               # OTP generation and verification
│   ├── email_service.py             # Email sending functionality
│   ├── rate_limit_service.py        # Rate limiting implementation
│   └── security_service.py          # Security utilities and OAuth state management
│
├── middleware/                      # FastAPI middleware
│   ├── __init__.py
│   └── security_middleware.py       # Security headers, logging, rate limiting
│
├── database/                        # Database configuration
│   ├── __init__.py
│   └── session.py                   # Database session management
│
├── alembic/                         # Database migration files
│   ├── env.py
│   ├── script.py.mako
│   └── versions/                    # Migration versions
│       ├── 987e257921db_create_user_and_otp_tables.py
│       ├── c2b7d882b174_add_hashed_password_column.py
│       ├── f5070496e546_fix_otp_table_schema_add_user_id_and_.py
│       ├── 1f85d57b8e52_fix_otp_id_autoincrement.py
│       └── 6f684eed73e5_add_invalidated_tokens_table_for_logout_.py
│
└── tests/                           # Test suite
    ├── __init__.py
    ├── conftest.py                  # Pytest configuration and fixtures
    ├── test_google_auth_fixed.py    # Google OAuth tests
    ├── test_logout.py               # Logout functionality tests
    ├── test_logout_fixed.py
    └── test_logout_simple.py
```

---

## 3. Core Components

### 3.1 main.py - Application Entry Point

**Location**: `auth_service/main.py`

**Purpose**: FastAPI application initialization and configuration

**Key Components**:

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from routers.auth_router import router as auth_router
from middleware.security_middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    RateLimitMiddleware
)

app = FastAPI(
    title="Auth Service",
    description="Authentication service for the EdTech platform",
    version="1.0.0"
)
```

**Middleware Stack** (order matters - first added executes last):
1. **SecurityHeadersMiddleware**: Adds security headers (X-Frame-Options, CSP, etc.)
2. **RequestLoggingMiddleware**: Logs all requests with timestamps and client info
3. **RateLimitMiddleware**: Global rate limiting (100 requests/minute per IP)
4. **CORSMiddleware**: Cross-Origin Resource Sharing configuration

**Health Check Endpoints**:
- `GET /` - Root endpoint returning service status
- `GET /health` - Health check endpoint

---

### 3.2 core/config.py - Configuration Management

**Location**: `auth_service/core/config.py`

**Purpose**: Centralized configuration using Pydantic Settings

**Class**: `Settings(BaseSettings)`

**Environment Variables**:

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `DATABASE_URL` | str | `postgresql://user:password@localhost:5432/auth_service_dev` | PostgreSQL connection string |
| `SECRET_KEY` | str | Dev default | JWT signing secret key (MUST override in production) |
| `ALGORITHM` | str | `HS256` | JWT signing algorithm |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | 30 | Access token expiration time |
| `REFRESH_TOKEN_EXPIRE_DAYS` | int | 7 | Refresh token expiration time |
| `BACKEND_CORS_ORIGINS` | str | JSON array | Allowed CORS origins |
| `LOG_LEVEL` | str | `INFO` | Logging level |
| `OTP_EXPIRY_MINUTES` | int | 10 | OTP expiration time |
| `OTP_MAX_ATTEMPTS` | int | 3 | Maximum OTP verification attempts |
| `OTP_RATE_LIMIT_MINUTES` | int | 1 | OTP rate limit window |
| `OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR` | int | 5 | Maximum OTP requests per hour |
| `REQUIRE_EMAIL_VERIFICATION` | bool | True | Enforce email verification |
| `GOOGLE_CLIENT_ID` | str | None | Google OAuth client ID |
| `GOOGLE_CLIENT_SECRET` | str | None | Google OAuth client secret |
| `EMAIL_HOST` | str | None | SMTP server hostname |
| `EMAIL_PORT` | int | None | SMTP server port |
| `EMAIL_USERNAME` | str | None | SMTP username |
| `EMAIL_PASSWORD` | str | None | SMTP password |
| `EMAIL_FROM` | str | None | Email sender address |
| `EMAIL_STARTTLS` | bool | True | Use STARTTLS |
| `EMAIL_SSL_TLS` | bool | False | Use SSL/TLS |

**Properties**:
- `cors_origins`: Parses JSON string from `BACKEND_CORS_ORIGINS` into list

**Global Instance**: `settings = Settings()`

---

### 3.3 core/security.py - Security Functions

**Location**: `auth_service/core/security.py`

**Purpose**: JWT token generation and password hashing utilities

**Functions**:

#### 3.3.1 `create_access_token(subject, expires_delta=None) -> str`
- **Purpose**: Generate JWT access token
- **Parameters**:
  - `subject`: User identifier (usually user ID)
  - `expires_delta`: Optional custom expiration timedelta
- **Returns**: Encoded JWT token string
- **Token Claims**:
  - `exp`: Expiration timestamp
  - `sub`: Subject (user ID)

#### 3.3.2 `create_refresh_token(subject, expires_delta=None) -> str`
- **Purpose**: Generate JWT refresh token with JTI
- **Parameters**:
  - `subject`: User identifier
  - `expires_delta`: Optional custom expiration timedelta
- **Returns**: Encoded JWT token string
- **Token Claims**:
  - `exp`: Expiration timestamp
  - `sub`: Subject (user ID)
  - `jti`: JWT ID (unique identifier for token invalidation)

#### 3.3.3 `verify_password(plain_password: str, hashed_password: str) -> bool`
- **Purpose**: Verify password against hashed version
- **Algorithm**: bcrypt via passlib
- **Returns**: True if password matches, False otherwise

#### 3.3.4 `hash_password(password: str) -> str`
- **Purpose**: Hash password using bcrypt
- **Algorithm**: bcrypt via passlib
- **Returns**: Hashed password string

**Password Context Configuration**:
```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

---

## 4. Database Models

### 4.1 User Model

**Location**: `auth_service/models/user_model.py`

**Table Name**: `users`

**Class**: `User(Base)`

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key, Index | Auto-incrementing user ID |
| `email` | String | Unique, Index, Not Null | User email address |
| `hashed_password` | String | Nullable | Bcrypt hashed password (null for OAuth users) |
| `google_id` | String | Unique, Index, Nullable | Google OAuth user ID |
| `is_active` | Boolean | Not Null, Default=True | Account active status |
| `is_verified` | Boolean | Not Null, Default=False | Email verification status |
| `full_name` | String | Nullable | User's full name |
| `created_at` | DateTime(TZ) | Not Null, Server Default=now() | Creation timestamp |
| `updated_at` | DateTime(TZ) | Not Null, Server Default=now(), On Update | Last update timestamp |

**Indexes**:
- `idx_user_email`: Index on `email` (unique)
- `idx_user_google_id`: Index on `google_id` (unique)
- `idx_user_active_verified`: Composite index on `is_active` and `is_verified`

**Relationships**: None (standalone model)

---

### 4.2 OTP Model

**Location**: `auth_service/models/otp_model.py`

**Table Name**: `otps`

**Class**: `OTP(Base)`

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key, Index, Auto-increment | Auto-incrementing OTP ID |
| `user_id` | Integer | Foreign Key (users.id), Not Null, Index | Reference to user |
| `email` | String | Not Null, Index | User email (for backward compatibility) |
| `otp_code` | String | Not Null | Hashed OTP code |
| `purpose` | String | Not Null, Default='verification' | OTP purpose (verification/login/password_reset) |
| `expires_at` | DateTime(TZ) | Not Null | OTP expiration timestamp |
| `created_at` | DateTime(TZ) | Not Null, Server Default=now() | Creation timestamp |

**Indexes**:
- `idx_otp_user_id`: Index on `user_id`
- `idx_otp_email`: Index on `email`
- `idx_otp_user_purpose`: Composite index on `user_id` and `purpose`
- `idx_otp_expires_at`: Index on `expires_at` (for cleanup queries)

**Relationships**:
- Foreign Key to `users.id`

**Security Note**: OTP codes are hashed using bcrypt before storage

---

### 4.3 InvalidatedToken Model

**Location**: `auth_service/models/invalidated_token_model.py`

**Table Name**: `invalidated_tokens`

**Class**: `InvalidatedToken(Base)`

**Purpose**: Token denylist for logout functionality

**Columns**:

| Column | Type | Constraints | Description |
|--------|------|-------------|-------------|
| `id` | Integer | Primary Key, Index | Auto-incrementing ID |
| `jti` | String(64) | Unique, Not Null, Index | JWT ID from refresh token |
| `user_id` | Integer | Not Null, Index | User who invalidated the token |
| `expires_at` | DateTime | Not Null | Original token expiration time |
| `invalidated_at` | DateTime | Not Null, Default=utcnow() | When token was invalidated |

**Indexes**:
- `idx_jti_expires`: Composite index on `jti` and `expires_at`
- Primary index on `id`
- Unique index on `jti`
- Index on `user_id`

**Cleanup Strategy**: Expired tokens can be periodically removed from the table

---

## 5. API Schemas

### 5.1 User Schemas

**Location**: `auth_service/schemas/user_schema.py`

#### 5.1.1 `UserBase(BaseModel)`
**Fields**:
- `email: EmailStr` - Email address (validated)
- `full_name: Optional[str]` - User's full name

**Validators**:
- `validate_full_name`: 
  - Strips whitespace
  - Max 100 characters
  - Min 1 character if provided
  - Removes control characters

#### 5.1.2 `UserCreate(UserBase)`
**Additional Fields**:
- `password: Optional[str]` - Password (optional for OTP-only registration)

**Password Validation Rules**:
- Minimum 8 characters
- Maximum 128 characters
- At least one lowercase letter
- At least one uppercase letter
- At least one digit
- At least one special character (@$!%*?&)

#### 5.1.3 `UserLogin(BaseModel)`
**Fields**:
- `email: EmailStr` - Email address
- `password: str` - Password

#### 5.1.4 `UserRead(UserBase)` / `UserResponse`
**Fields**:
- All `UserBase` fields
- `id: int` - User ID
- `is_active: bool` - Active status
- `is_verified: bool` - Verification status
- `created_at: datetime` - Creation timestamp

**Configuration**: `model_config = ConfigDict(from_attributes=True)`

---

### 5.2 Token Schemas

**Location**: `auth_service/schemas/token_schema.py`

#### 5.2.1 `TokenData(BaseModel)`
**Fields**:
- `user_id: Optional[int]` - User ID from token

#### 5.2.2 `Token(BaseModel)`
**Fields**:
- `access_token: str` - JWT access token
- `refresh_token: str` - JWT refresh token
- `token_type: str` - Token type (always "bearer")

#### 5.2.3 `TokenResponse(BaseModel)`
**Fields**:
- `access_token: Optional[str]` - JWT access token
- `token_type: str = "bearer"` - Token type
- `expires_in: Optional[int]` - Access token expiration in seconds
- `refresh_token: Optional[str]` - JWT refresh token
- `refresh_token_expires_in: Optional[int]` - Refresh token expiration in seconds
- `user: Optional[UserResponse]` - User information
- `message: Optional[str]` - Optional message

#### 5.2.4 `RefreshTokenRequest(BaseModel)`
**Fields**:
- `refresh_token: str` - Refresh token to exchange

#### 5.2.5 `AccessTokenResponse(BaseModel)`
**Fields**:
- `access_token: str` - New access token
- `token_type: str = "bearer"` - Token type
- `expires_in: int` - Expiration in seconds

#### 5.2.6 `LogoutRequest(BaseModel)`
**Fields**:
- `refresh_token: str` - Refresh token to invalidate

#### 5.2.7 `LogoutResponse(BaseModel)`
**Fields**:
- `message: str` - Logout status message

---

### 5.3 OTP Schemas

**Location**: `auth_service/schemas/otp_schema.py`

#### 5.3.1 `OTPPurpose(str, Enum)`
**Values**:
- `verification` - Email verification
- `login` - OTP-based login
- `password_reset` - Password reset flow

#### 5.3.2 `OTPRequest(BaseModel)`
**Fields**:
- `email: EmailStr` - User email
- `purpose: OTPPurpose = OTPPurpose.verification` - OTP purpose

#### 5.3.3 `OTPVerify(BaseModel)`
**Fields**:
- `email: EmailStr` - User email
- `otp_code: str` - 6-digit OTP code
- `purpose: OTPPurpose = OTPPurpose.verification` - OTP purpose

**Validators**:
- `validate_otp_code`:
  - Required field
  - Strips whitespace
  - Must be exactly 6 digits
  - Regex: `^\d{6}$`

#### 5.3.4 `OTPResponse(BaseModel)`
**Fields**:
- `message: str` - Response message
- `email: EmailStr` - User email
- `expires_in_minutes: int` - OTP expiration time

---

## 6. CRUD Operations

### 6.1 User CRUD

**Location**: `auth_service/crud/user_crud.py`

**Class**: `UserCRUD`

#### 6.1.1 `__init__(self, db: Session)`
- Initialize with database session

#### 6.1.2 `get_by_id(self, user_id: int) -> Optional[User]`
- **Purpose**: Retrieve user by ID
- **Returns**: User object or None

#### 6.1.3 `get_by_email(self, email: str) -> Optional[User]`
- **Purpose**: Retrieve user by email
- **Returns**: User object or None

#### 6.1.4 `get_by_google_id(self, google_id: str) -> Optional[User]`
- **Purpose**: Retrieve user by Google OAuth ID
- **Returns**: User object or None

#### 6.1.5 `create(self, user_data: UserCreate) -> User`
- **Purpose**: Create new user with email/password
- **Process**:
  1. Hash password if provided
  2. Create User model instance
  3. Set defaults: `is_verified=False`, `is_active=True`
  4. Add to database
  5. Commit and refresh
- **Returns**: Created User object

#### 6.1.6 `create_google_user(self, google_id: str, email: str, full_name: str) -> User`
- **Purpose**: Create new user from Google OAuth
- **Process**:
  1. Create User with google_id
  2. Set `is_verified=True` (pre-verified by Google)
  3. Set `is_active=True`
  4. No password (OAuth user)
- **Returns**: Created User object

#### 6.1.7 `update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]`
- **Purpose**: Update user fields
- **Process**:
  1. Retrieve user by ID
  2. Update provided fields
  3. Commit and refresh
- **Returns**: Updated User object or None

#### 6.1.8 `delete(self, user_id: int) -> bool`
- **Purpose**: Delete user by ID
- **Returns**: True if deleted, False if not found

**Legacy Functions**:
- `get_user(db, user_id)` - Wrapper for backward compatibility
- `get_user_by_email(db, email)` - Wrapper for backward compatibility
- `create_user(db, user)` - Wrapper for backward compatibility

---

### 6.2 OTP CRUD

**Location**: `auth_service/crud/otp_crud.py`

**Class**: `OTPCRUD`

#### 6.2.1 `__init__(self, db: Session)`
- Initialize with database session

#### 6.2.2 `create(self, otp_data: Dict[str, Any]) -> OTP`
- **Purpose**: Create or replace OTP record
- **Process**:
  1. Delete existing OTP for user_id and purpose (one OTP per user per purpose)
  2. Hash OTP code using bcrypt
  3. Create OTP model instance
  4. Add to database and commit
- **Returns**: Created OTP object
- **Security**: OTP is hashed before storage

#### 6.2.3 `get_by_user_and_purpose(self, user_id: int, purpose: str) -> Optional[OTP]`
- **Purpose**: Retrieve OTP by user ID and purpose
- **Returns**: OTP object or None

#### 6.2.4 `delete_by_user_and_purpose(self, user_id: int, purpose: str) -> bool`
- **Purpose**: Delete OTP record
- **Returns**: True if deleted, False if not found

#### 6.2.5 `delete_expired_otps(self) -> int`
- **Purpose**: Clean up expired OTP records
- **Process**: Delete all OTPs where `expires_at < current_time`
- **Returns**: Count of deleted records

---

### 6.3 Invalidated Token CRUD

**Location**: `auth_service/crud/invalidated_token_crud.py`

**Class**: `InvalidatedTokenCRUD`

#### 6.3.1 `__init__(self, db: Session)`
- Initialize with database session

#### 6.3.2 `create_invalidated_token(self, jti: str, user_id: int, expires_at: datetime) -> InvalidatedToken`
- **Purpose**: Add token to denylist
- **Parameters**:
  - `jti`: JWT ID from refresh token
  - `user_id`: User who invalidated the token
  - `expires_at`: Original token expiration time
- **Returns**: Created InvalidatedToken object
- **Note**: Does not call `db.refresh()` to avoid transaction issues in tests

#### 6.3.3 `is_token_invalidated(self, jti: str) -> bool`
- **Purpose**: Check if token JTI is in denylist
- **Process**: Query for non-expired invalidated tokens with matching JTI
- **Returns**: True if token is invalidated, False otherwise

#### 6.3.4 `get_by_jti(self, jti: str) -> Optional[InvalidatedToken]`
- **Purpose**: Retrieve invalidated token by JTI
- **Returns**: InvalidatedToken object or None

#### 6.3.5 `cleanup_expired_tokens(self) -> int`
- **Purpose**: Remove expired tokens from denylist
- **Process**: Delete tokens where `expires_at <= current_time`
- **Returns**: Count of deleted tokens
- **Usage**: Should be called periodically (e.g., daily cron job)

---

## 7. Services Layer

### 7.1 OTP Service

**Location**: `auth_service/services/otp_service.py`

**Class**: `OTPService`

#### 7.1.1 `generate_otp(self) -> str`
- **Purpose**: Generate secure 6-digit OTP
- **Algorithm**: Uses `secrets.choice()` for cryptographic randomness
- **Returns**: 6-digit numeric string

#### 7.1.2 `get_expiry_time(self) -> datetime`
- **Purpose**: Calculate OTP expiration time
- **Calculation**: `current_time + OTP_EXPIRY_MINUTES`
- **Returns**: Timezone-aware datetime

#### 7.1.3 `verify_otp(self, db: Session, user_id: int, otp_code: str, purpose: str) -> bool`
- **Purpose**: Verify OTP for user
- **Process**:
  1. Retrieve stored OTP by user_id and purpose
  2. Check if OTP exists
  3. Check if OTP is expired (delete if expired)
  4. Verify provided OTP against stored hashed OTP using bcrypt
  5. Delete OTP after successful verification (one-time use)
- **Returns**: True if valid, False otherwise
- **Security**: Uses constant-time bcrypt comparison to prevent timing attacks

#### 7.1.4 `cleanup_expired_otps(self, db: Session) -> int`
- **Purpose**: Clean up expired OTP records
- **Returns**: Count of deleted records

---

### 7.2 Email Service

**Location**: `auth_service/services/email_service.py`

**Class**: `EmailService`

#### 7.2.1 `__init__(self)`
- Initialize email service with lazy configuration loading

#### 7.2.2 `_get_mail_config(self) -> ConnectionConfig`
- **Purpose**: Get email configuration (lazy loading)
- **Configuration**:
  - `MAIL_USERNAME`: SMTP username
  - `MAIL_PASSWORD`: SMTP password
  - `MAIL_FROM`: Sender email
  - `MAIL_PORT`: SMTP port
  - `MAIL_SERVER`: SMTP server hostname
  - `MAIL_STARTTLS`: Enable STARTTLS
  - `MAIL_SSL_TLS`: Enable SSL/TLS
  - `USE_CREDENTIALS`: True
  - `VALIDATE_CERTS`: True

#### 7.2.3 `send_otp_email(self, email: str, otp_code: str, user_name: Optional[str] = None, purpose: str = "verification") -> None`
- **Purpose**: Send OTP email to user
- **Parameters**:
  - `email`: Recipient email address
  - `otp_code`: 6-digit OTP code
  - `user_name`: User's name for personalization
  - `purpose`: OTP purpose (verification/login/password_reset)
- **Email Subjects** (based on purpose):
  - `verification`: "Verify Your Email - AI EdTech Platform"
  - `login`: "Your Login Code - AI EdTech Platform"
  - `password_reset`: "Password Reset Code - AI EdTech Platform"
- **Email Format**: HTML with styled OTP display
- **Fallback**: If email not configured, prints to console
- **Error Handling**: Raises exception on failure

---

### 7.3 Rate Limit Service

**Location**: `auth_service/services/rate_limit_service.py`

**Class**: `RateLimitService`

**Purpose**: In-memory rate limiting with automatic cleanup

#### 7.3.1 `__init__(self)`
- Initialize rate limit service
- **Data Structure**: `{key: [(timestamp, attempt_count), ...]}`

#### 7.3.2 `_cleanup_expired_entries(self)`
- **Purpose**: Remove expired entries to prevent memory bloat
- **Trigger**: Every 5 minutes
- **Retention**: Keeps 1 hour of history

#### 7.3.3 `check_rate_limit(self, identifier: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int, int]`
- **Purpose**: Check if action is rate limited
- **Parameters**:
  - `identifier`: Unique identifier (email, IP, etc.)
  - `max_attempts`: Maximum attempts allowed
  - `window_seconds`: Time window in seconds
- **Returns**: `(is_allowed, current_attempts, seconds_until_reset)`

#### 7.3.4 `record_attempt(self, identifier: str)`
- **Purpose**: Record an attempt for rate limiting

#### 7.3.5 `is_otp_request_allowed(self, email: str) -> Tuple[bool, int]`
- **Rate Limit**: 5 OTP requests per hour per email
- **Returns**: `(is_allowed, seconds_until_reset)`

#### 7.3.6 `is_otp_verification_allowed(self, email: str) -> Tuple[bool, int]`
- **Rate Limit**: 3 verification attempts per minute per email
- **Returns**: `(is_allowed, seconds_until_reset)`

#### 7.3.7 `record_otp_request(self, email: str)`
- Record OTP request attempt

#### 7.3.8 `record_otp_verification(self, email: str)`
- Record OTP verification attempt

#### 7.3.9 `is_login_attempt_allowed(self, email: str) -> Tuple[bool, int]`
- **Rate Limit**: 5 login attempts per 15 minutes per email
- **Returns**: `(is_allowed, seconds_until_reset)`

#### 7.3.10 `record_login_attempt(self, email: str)`
- Record login attempt

**Global Instance**: `rate_limit_service = RateLimitService()`

---

### 7.4 Security Service

**Location**: `auth_service/services/security_service.py`

**Class**: `SecurityUtils`

#### 7.4.1 `validate_otp_code(otp_code: str) -> bool` (static)
- **Purpose**: Validate OTP code format
- **Validation**: Exactly 6 digits
- **Regex**: `^\d{6}$`

#### 7.4.2 `sanitize_email(email: str) -> str` (static)
- **Purpose**: Sanitize and normalize email
- **Process**:
  1. Convert to lowercase
  2. Strip whitespace
  3. Validate format with regex
- **Regex**: `^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$`
- **Raises**: HTTPException if invalid

#### 7.4.3 `validate_password_strength(password: str) -> tuple[bool, str]` (static)
- **Purpose**: Validate password strength
- **Rules**:
  - Required field
  - 8-128 characters
  - At least one lowercase letter
  - At least one uppercase letter
  - At least one digit
  - At least one special character (@$!%*?&)
- **Returns**: `(is_valid, error_message)`

#### 7.4.4 `generate_secure_state() -> str` (static)
- **Purpose**: Generate secure OAuth state parameter
- **Algorithm**: `secrets.token_urlsafe(32)`
- **Returns**: 32-character URL-safe random string

#### 7.4.5 `sanitize_user_input(input_str: str, max_length: int = 255) -> str` (static)
- **Purpose**: Sanitize user input to prevent injection attacks
- **Process**:
  1. Strip whitespace
  2. Check length (max_length)
  3. Remove null bytes and control characters
- **Returns**: Sanitized string

#### 7.4.6 `create_safe_error_response(user_message: str, internal_error: str = None) -> HTTPException` (static)
- **Purpose**: Create safe error response without leaking sensitive info
- **Returns**: HTTPException with user-safe message

#### 7.4.7 `is_suspicious_request(email: str, user_agent: str = None) -> bool` (static)
- **Purpose**: Basic suspicious request detection
- **Checks**:
  - Temporary email domains (tempmail.org, etc.)
  - Bot-like user agents
- **Returns**: True if suspicious

**Class**: `OAuthStateManager`

**Purpose**: Secure OAuth state management with expiry

#### OAuth State Manager Methods:

#### 7.4.8 `__init__(self)`
- **Data Structure**: `{state: (timestamp, used)}`

#### 7.4.9 `_cleanup_expired_states(self)`
- **Purpose**: Remove expired states
- **Trigger**: Every 10 minutes
- **Expiry**: 30 minutes

#### 7.4.10 `create_state(self) -> str`
- **Purpose**: Create new OAuth state with expiry
- **Returns**: Secure random state string

#### 7.4.11 `validate_and_consume_state(self, state: str) -> bool`
- **Purpose**: Validate and consume OAuth state (one-time use)
- **Checks**:
  1. State exists
  2. Not already used
  3. Not expired (30 minutes)
  4. Marks as used
- **Returns**: True if valid

**Global Instances**:
- `security_utils = SecurityUtils()`
- `oauth_state_manager = OAuthStateManager()`

---

## 8. Middleware

### 8.1 Security Headers Middleware

**Location**: `auth_service/middleware/security_middleware.py`

**Class**: `SecurityHeadersMiddleware(BaseHTTPMiddleware)`

**Purpose**: Add security headers to all responses

**Headers Added**:
- `X-Content-Type-Options: nosniff` - Prevent MIME type sniffing
- `X-Frame-Options: DENY` - Prevent clickjacking
- `X-XSS-Protection: 1; mode=block` - Enable XSS filter
- `Referrer-Policy: strict-origin-when-cross-origin` - Control referrer information
- `Content-Security-Policy` - Restrict resource loading
- Removes `server` header for security

---

### 8.2 Request Logging Middleware

**Location**: `auth_service/middleware/security_middleware.py`

**Class**: `RequestLoggingMiddleware(BaseHTTPMiddleware)`

**Purpose**: Log requests for security monitoring

**Logging Levels**:
- `INFO`: POST, PUT, DELETE requests
- `DEBUG`: GET, HEAD requests
- `WARNING`: 4xx and 5xx responses, slow requests (>2s)

**Logged Information**:
- HTTP method
- URL
- Client IP
- User agent (truncated to 100 chars)
- Response status code
- Processing time
- Slow request detection (>2 seconds)

---

### 8.3 Rate Limit Middleware

**Location**: `auth_service/middleware/security_middleware.py`

**Class**: `RateLimitMiddleware(BaseHTTPMiddleware)`

**Purpose**: Global rate limiting for all endpoints

**Configuration**:
- Default: 100 requests per minute per IP
- Configurable via constructor parameter

**Implementation**:
- In-memory storage: `{ip: [timestamp1, timestamp2, ...]}`
- Automatic cleanup of requests older than 1 minute
- Returns 429 (Too Many Requests) when limit exceeded

**Response Format** (when rate limited):
```json
{
  "detail": "Rate limit exceeded. Maximum 100 requests per minute allowed.",
  "error": "Too Many Requests"
}
```

---

## 9. Dependencies

### 9.1 Authentication Dependencies

**Location**: `auth_service/routers/dependencies.py`

#### 9.1.1 `get_current_user(credentials, db) -> dict`
- **Purpose**: Extract and validate JWT token from Authorization header
- **Security Scheme**: HTTPBearer
- **Process**:
  1. Decode JWT token
  2. Extract user_id from `sub` claim
  3. Verify user exists in database
  4. Return user information dict
- **Returns**: 
```python
{
    "user_id": int,
    "email": str,
    "full_name": str,
    "is_verified": bool,
    "is_active": bool
}
```
- **Raises**: 401 Unauthorized if token invalid or user not found

#### 9.1.2 `get_current_active_user(current_user) -> dict`
- **Purpose**: Ensure user is active
- **Depends**: `get_current_user`
- **Raises**: 400 Bad Request if user inactive

#### 9.1.3 `get_current_verified_user(current_user) -> dict`
- **Purpose**: Ensure user email is verified
- **Depends**: `get_current_user`
- **Raises**: 403 Forbidden if email not verified

#### 9.1.4 `require_roles(*required_roles: str)`
- **Purpose**: Dependency factory for role-based access control
- **Note**: Placeholder implementation - requires User model extension with roles
- **Raises**: 403 Forbidden if user lacks required roles

---

## 10. Database Migrations

### 10.1 Alembic Configuration

**Configuration File**: `alembic.ini`

**Environment File**: `alembic/env.py`

**Database URL**: Loaded from environment variables via `core.config.settings`

### 10.2 Migration History

#### Migration 1: `987e257921db_create_user_and_otp_tables.py`
- **Date**: June 8, 2025
- **Changes**:
  - Created `users` table with indexes
  - Created `otps` table with indexes
  - Initial schema setup

#### Migration 2: `c2b7d882b174_add_hashed_password_column.py`
- **Changes**: Added `hashed_password` column to users table

#### Migration 3: `f5070496e546_fix_otp_table_schema_add_user_id_and_.py`
- **Changes**: 
  - Added `user_id` foreign key to otps table
  - Added `purpose` field to support multiple OTP types
  - Updated indexes

#### Migration 4: `1f85d57b8e52_fix_otp_id_autoincrement.py`
- **Changes**: Fixed OTP ID column to use auto-increment

#### Migration 5: `6f684eed73e5_add_invalidated_tokens_table_for_logout_.py`
- **Date**: June 10, 2025
- **Changes**:
  - Created `invalidated_tokens` table
  - Added indexes for efficient token lookup
  - Enabled logout/token invalidation functionality

### 10.3 Running Migrations

```powershell
# Generate new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history

# Check current version
alembic current
```

---

## 11. Configuration

### 11.1 Environment Variables

**Template File**: `.env.example`

**Required Variables** (Production):
- `DATABASE_URL` - PostgreSQL connection string
- `SECRET_KEY` - Strong random secret for JWT signing
- `GOOGLE_CLIENT_ID` - Google OAuth client ID
- `GOOGLE_CLIENT_SECRET` - Google OAuth client secret
- `EMAIL_HOST` - SMTP server
- `EMAIL_USERNAME` - SMTP username
- `EMAIL_PASSWORD` - SMTP password
- `EMAIL_FROM` - Sender email address

**Optional Variables**:
- `ALGORITHM` - JWT algorithm (default: HS256)
- `ACCESS_TOKEN_EXPIRE_MINUTES` - Token expiration (default: 30)
- `REFRESH_TOKEN_EXPIRE_DAYS` - Refresh token expiration (default: 7)
- `BACKEND_CORS_ORIGINS` - JSON array of allowed origins
- `LOG_LEVEL` - Logging level (default: INFO)
- `OTP_EXPIRY_MINUTES` - OTP expiration (default: 10)
- `REQUIRE_EMAIL_VERIFICATION` - Enforce email verification (default: True)

### 11.2 CORS Configuration

**Method**: Environment-driven via `BACKEND_CORS_ORIGINS`

**Format**: JSON array string

**Example**:
```bash
BACKEND_CORS_ORIGINS='["https://yourdomain.com", "https://app.yourdomain.com"]'
```

**Development Default**:
```json
["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]
```

---

## 12. Testing Infrastructure

### 12.1 Test Configuration

**Location**: `auth_service/tests/conftest.py`

**Framework**: pytest with FastAPI TestClient

#### 12.1.1 Fixtures

**`test_client`** (session scope):
- Creates FastAPI TestClient
- `follow_redirects=False` for testing redirects
- Yields client for test use

**`test_db`**:
- Creates in-memory SQLite database
- Creates all tables from Base.metadata
- Enables SQL logging for debugging
- Yields database session
- Cleans up after test

**`test_client_with_db`**:
- File-based SQLite database (avoids threading issues)
- Overrides `get_db` dependency
- Creates temporary database file
- Cleans up after tests
- Properly disposes engine

**`mock_google_client_id`**:
- Provides test Google client ID

**`mock_settings`**:
- Mocks settings module with test values
- Includes all necessary configuration

### 12.2 Test Files

**Location**: `auth_service/tests/`

**Test Files**:
- `test_google_auth_fixed.py` - Google OAuth flow tests
- `test_logout.py` - Logout functionality tests
- `test_logout_fixed.py` - Fixed logout tests
- `test_logout_simple.py` - Simple logout tests

### 12.3 Running Tests

```powershell
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_logout.py

# Run with coverage
pytest --cov=. --cov-report=html
```

---

## 13. Dependencies and Libraries

### 13.1 Core Dependencies

**From `requirements.txt`**:

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | Latest | Web framework |
| `uvicorn[standard]` | Latest | ASGI server |
| `sqlalchemy` | Latest | ORM for database |
| `psycopg2-binary` | Latest | PostgreSQL adapter |
| `alembic` | Latest | Database migrations |
| `python-jose[cryptography]` | Latest | JWT token handling |
| `pydantic[email]` | Latest | Data validation and email validation |
| `pydantic-settings` | Latest | Settings management |
| `passlib[bcrypt]` | Latest | Password hashing |
| `python-dotenv` | Latest | Environment variable loading |
| `fastapi-mail` | Latest | Email sending |
| `authlib` | Latest | OAuth support |
| `pytest` | Latest | Testing framework |
| `pytest-asyncio` | Latest | Async test support |
| `httpx` | Latest | HTTP client for tests and OAuth |

### 13.2 Import Dependencies

**Standard Library**:
- `datetime`, `timedelta` - Time handling
- `typing` - Type hints
- `secrets` - Cryptographic random generation
- `uuid` - Unique identifier generation
- `json` - JSON parsing
- `base64` - Base64 encoding/decoding
- `logging` - Logging functionality
- `time` - Time utilities
- `re` - Regular expressions
- `os`, `sys` - System utilities

**Third-Party**:
- `fastapi` - Core framework
- `sqlalchemy` - Database ORM
- `jose.jwt` - JWT operations
- `passlib.context` - Password hashing context
- `pydantic` - Data validation
- `httpx` - HTTP client

---

## Security Implementation Summary

### Authentication Mechanisms
1. **Email/Password**: Bcrypt hashed passwords, JWT tokens
2. **OTP-based**: 6-digit codes, hashed storage, rate limited
3. **Google OAuth 2.0**: PKCE flow, state validation, account linking

### Token Management
- **Access Tokens**: 30-minute expiration, JWT with user ID
- **Refresh Tokens**: 7-day expiration, JWT with JTI for invalidation
- **Token Invalidation**: Denylist table for logout functionality

### Security Features
- **Rate Limiting**: Global (100/min per IP) + endpoint-specific
- **Input Validation**: Email, password, OTP format validation
- **Input Sanitization**: XSS prevention, SQL injection prevention
- **CSRF Protection**: OAuth state parameter validation
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options
- **Password Hashing**: Bcrypt with automatic salt generation
- **OTP Security**: Hashed storage, one-time use, expiration
- **Request Logging**: Security monitoring and audit trail

---

## Data Flow Diagrams

### Registration Flow
1. Client → POST /auth/register (email, password, name)
2. Validate input and sanitize
3. Hash password with bcrypt
4. Create user record (is_verified=False)
5. Return user details (without password)

### OTP Verification Flow
1. Client → POST /auth/request-otp (email, purpose)
2. Check rate limits
3. Generate 6-digit OTP
4. Hash OTP and store in database
5. Send OTP via email
6. Client → POST /auth/verify-otp (email, otp_code, purpose)
7. Verify OTP against hashed value
8. Mark email as verified
9. Delete OTP (one-time use)
10. Generate access and refresh tokens
11. Return tokens and user details

### Login Flow
1. Client → POST /auth/login (email, password)
2. Check rate limits
3. Retrieve user by email
4. Verify password against hashed password
5. Check user is active and verified
6. Generate access and refresh tokens
7. Return tokens and user details

### Token Refresh Flow
1. Client → POST /auth/refresh-token (refresh_token)
2. Decode and validate refresh token
3. Check token not in denylist
4. Verify user exists and is active
5. Generate new access token
6. Return new access token

### Logout Flow
1. Client → POST /auth/logout (refresh_token)
2. Decode refresh token to extract JTI
3. Add JTI to invalidated_tokens table
4. Return success message

### Google OAuth Flow
1. Client → GET /auth/google/login
2. Generate secure state parameter
3. Redirect to Google authorization URL
4. User authorizes on Google
5. Google → GET /auth/google/callback (code, state)
6. Validate state parameter
7. Exchange code for access token
8. Decode ID token to get user info
9. Find or create user account
10. Link Google ID to existing email if found
11. Generate platform tokens
12. Redirect to frontend with tokens

---

## File Purpose Summary

| File/Directory | Purpose |
|----------------|---------|
| `main.py` | FastAPI app initialization, middleware, routes |
| `core/config.py` | Environment variables and settings |
| `core/security.py` | JWT and password hashing functions |
| `models/*.py` | SQLAlchemy database models |
| `schemas/*.py` | Pydantic request/response schemas |
| `crud/*.py` | Database CRUD operations |
| `routers/auth_router.py` | Authentication API endpoints |
| `routers/dependencies.py` | FastAPI dependencies for auth |
| `services/otp_service.py` | OTP generation and verification logic |
| `services/email_service.py` | Email sending functionality |
| `services/rate_limit_service.py` | Rate limiting implementation |
| `services/security_service.py` | Security utilities and OAuth state |
| `middleware/security_middleware.py` | Security headers, logging, rate limiting |
| `database/session.py` | Database connection and session |
| `alembic/` | Database migration files |
| `tests/` | Test suite and fixtures |

---

**End of Code Documentation**
