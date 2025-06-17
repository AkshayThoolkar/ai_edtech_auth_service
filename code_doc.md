# Auth Service Code Documentation v1.0

## Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Project Structure](#project-structure)
3. [Core Modules](#core-modules)
4. [Database Schema](#database-schema)
5. [Business Logic](#business-logic)
6. [Security Implementation](#security-implementation)
7. [Testing Strategy](#testing-strategy)
8. [Developer Onboarding](#developer-onboarding)
9. [Configuration Management](#configuration-management)
10. [API Layer](#api-layer)
11. [Deployment Considerations](#deployment-considerations)

---

## Architecture Overview

### System Architecture
The Auth Service follows a **layered architecture** pattern with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  FastAPI    │  │   Routers   │  │    Middleware       │ │
│  │  Main App   │  │ (auth_router)│  │ (Security/Logging)  │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                    │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Services  │  │   Schemas   │  │    Dependencies     │ │
│  │ (OTP/Email/ │  │ (Pydantic   │  │   (Authentication)  │ │
│  │ Security)   │  │ Validation) │  │                     │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                     Data Access Layer                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │    CRUD     │  │   Models    │  │     Database        │ │
│  │ Operations  │  │ (SQLAlchemy)│  │    Session          │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                        Database                             │
│                   PostgreSQL/SQLite                        │
└─────────────────────────────────────────────────────────────┘
```

### Request Flow
1. **HTTP Request** → FastAPI application
2. **Middleware Processing** → Security headers, logging, rate limiting
3. **Router Handling** → Route-specific logic in `auth_router.py`
4. **Service Layer** → Business logic processing
5. **Data Layer** → CRUD operations and database interactions
6. **Response Generation** → Pydantic schema validation and JSON response

### Key Design Patterns
- **Dependency Injection**: FastAPI's dependency system for database sessions and authentication
- **Repository Pattern**: CRUD classes abstract database operations
- **Service Layer Pattern**: Business logic separated from data access
- **Factory Pattern**: Used in configuration and service initialization
- **Observer Pattern**: Middleware for cross-cutting concerns

---

## Project Structure

```
auth_service/
├── main.py                          # FastAPI application entry point
├── requirements.txt                 # Python dependencies
├── alembic.ini                     # Database migration configuration
├── .env.example                    # Environment variables template
│
├── core/                           # Core application logic
│   ├── __init__.py
│   ├── config.py                   # Application configuration management
│   └── security.py                 # Authentication and security utilities
│
├── models/                         # SQLAlchemy database models
│   ├── __init__.py
│   ├── user_model.py               # User entity model
│   ├── otp_model.py                # One-Time Password model
│   └── invalidated_token_model.py  # Token blacklist model
│
├── schemas/                        # Pydantic data validation schemas
│   ├── __init__.py
│   ├── user_schema.py              # User request/response schemas
│   ├── otp_schema.py               # OTP request/response schemas
│   └── token_schema.py             # JWT token schemas
│
├── routers/                        # FastAPI route handlers
│   ├── __init__.py
│   ├── auth_router.py              # Authentication endpoints
│   └── dependencies.py             # Route dependencies
│
├── services/                       # Business logic layer
│   ├── __init__.py
│   ├── otp_service.py              # OTP generation and verification
│   ├── email_service.py            # Email/OTP delivery services
│   ├── rate_limit_service.py       # Rate limiting logic
│   └── security_service.py         # Security utilities and OAuth
│
├── crud/                           # Database operations (Repository pattern)
│   ├── __init__.py
│   ├── user_crud.py                # User database operations
│   ├── otp_crud.py                 # OTP database operations
│   └── invalidated_token_crud.py   # Token management operations
│
├── middleware/                     # Custom middleware
│   ├── __init__.py
│   └── security_middleware.py      # Security headers, logging, rate limiting
│
├── database/                       # Database configuration
│   ├── __init__.py
│   └── session.py                  # SQLAlchemy session management
│
├── alembic/                        # Database migrations
│   ├── env.py                      # Alembic environment configuration
│   ├── script.py.mako             # Migration template
│   └── versions/                   # Migration version files
│       ├── 987e257921db_create_user_and_otp_tables.py
│       ├── c2b7d882b174_add_hashed_password_column.py
│       ├── f5070496e546_fix_otp_table_schema_add_user_id_and_.py
│       ├── 6f684eed73e5_add_invalidated_tokens_table_for_logout_.py
│       └── 1f85d57b8e52_fix_otp_id_autoincrement.py
│
└── tests/                          # Test suite
    ├── __init__.py
    ├── conftest.py                 # Pytest configuration and fixtures
    ├── test_google_auth_fixed.py   # Google OAuth tests
    ├── test_logout_fixed.py        # Logout functionality tests
    └── test_logout_simple.py       # Simple logout tests
```

---

## Core Modules

### core/ - Application Core

#### core/config.py
**Purpose**: Centralized configuration management using Pydantic Settings

**Key Features**:
- Environment-based configuration
- Type validation and parsing
- CORS origins management
- Security settings (JWT, OTP, rate limiting)
- Database connection configuration
- Email service settings

**Critical Settings**:
```python
class Settings(BaseSettings):
    # Security - NO DEFAULT VALUES FOR PRODUCTION
    DATABASE_URL: str
    SECRET_KEY: str  # Must be overridden in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # OTP Security
    OTP_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_LIMIT_MINUTES: int = 1
```

#### core/security.py
**Purpose**: Security utilities for authentication and authorization

**Key Functions**:
- `create_access_token()`: JWT access token generation
- `create_refresh_token()`: JWT refresh token with unique JTI
- `verify_password()`: Bcrypt password verification
- `hash_password()`: Bcrypt password hashing

**Security Features**:
- Uses `jose` library for JWT operations
- Bcrypt hashing with `passlib`
- Unique JTI (JWT ID) for refresh tokens to enable revocation

### models/ - Database Models

#### models/user_model.py
**Purpose**: User entity definition with SQLAlchemy ORM

**Schema**:
```python
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    google_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Indexes**:
- Primary index on `id`
- Unique indexes on `email` and `google_id`
- Composite index on `is_active` and `is_verified` for efficient queries

#### models/otp_model.py
**Purpose**: One-Time Password storage for verification flows

**Schema**:
```python
class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    email = Column(String, nullable=False, index=True)
    otp_code = Column(String, nullable=False)  # Hashed for security
    purpose = Column(String, nullable=False, default="verification")
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

**Security Features**:
- OTP codes are hashed before storage
- Automatic expiration with `expires_at`
- Purpose-based OTP types (verification, login, password_reset)

#### models/invalidated_token_model.py
**Purpose**: Token blacklist for logout functionality

**Schema**:
```python
class InvalidatedToken(Base):
    __tablename__ = "invalidated_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    expires_at = Column(DateTime, nullable=False)
    invalidated_at = Column(DateTime, default=datetime.utcnow)
```

**Purpose**: Enables secure logout by tracking invalidated refresh tokens

### schemas/ - Data Validation

#### schemas/user_schema.py
**Purpose**: Pydantic models for user data validation

**Key Schemas**:
- `UserBase`: Common user fields
- `UserCreate`: User registration with password validation
- `UserLogin`: Login credentials
- `UserRead/UserResponse`: API response model

**Password Validation Rules**:
```python
@field_validator('password')
@classmethod
def validate_password(cls, v):
    # Minimum 8 characters
    # At least one lowercase, uppercase, digit, special character
    # Maximum 128 characters
    # Comprehensive regex validation
```

#### schemas/otp_schema.py
**Purpose**: OTP request and response validation

#### schemas/token_schema.py
**Purpose**: JWT token request and response schemas

### routers/ - API Endpoints

#### routers/auth_router.py
**Purpose**: Authentication API endpoints implementation

**Key Endpoints**:
- `POST /auth/register`: User registration
- `POST /auth/generate-otp`: OTP generation for login
- `POST /auth/verify-otp`: OTP verification and login
- `POST /auth/refresh`: Token refresh
- `POST /auth/logout`: Secure logout
- `GET /auth/google`: Google OAuth initiation
- `GET /auth/google/callback`: Google OAuth callback

**Security Features**:
- Input sanitization and validation
- Rate limiting per endpoint
- Comprehensive error handling
- Request logging and monitoring

#### routers/dependencies.py
**Purpose**: Reusable dependency functions for authentication

---

## Database Schema

### Entity Relationship Diagram
```
┌─────────────────────────────────────────────────────────────┐
│                        Users Table                          │
├─────────────────────────────────────────────────────────────┤
│ id (PK) │ email (UNIQUE) │ hashed_password │ google_id      │
│ is_active │ is_verified │ full_name │ created_at │ updated_at │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 1:N
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                         OTPs Table                          │
├─────────────────────────────────────────────────────────────┤
│ id (PK) │ user_id (FK) │ email │ otp_code │ purpose        │
│ expires_at │ created_at                                     │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                 Invalidated Tokens Table                    │
├─────────────────────────────────────────────────────────────┤
│ id (PK) │ jti (UNIQUE) │ user_id │ expires_at │ invalidated_at │
└─────────────────────────────────────────────────────────────┘
```

### Database Migration History
1. **987e257921db**: Initial user and OTP tables creation
2. **c2b7d882b174**: Added hashed_password column for password authentication
3. **f5070496e546**: Enhanced OTP table schema with user_id and purpose fields
4. **6f684eed73e5**: Added invalidated_tokens table for secure logout
5. **1f85d57b8e52**: Fixed OTP ID autoincrement functionality

### Performance Optimizations
- **Indexes**: Strategic indexing on frequently queried columns
- **Composite Indexes**: Multi-column indexes for complex queries
- **Foreign Key Constraints**: Maintain referential integrity
- **Timezone-aware DateTime**: Consistent timestamp handling

---

## Business Logic

### Authentication Flow

#### 1. User Registration Flow
```
User Registration Request
         │
         ▼
Input Validation (Pydantic)
         │
         ▼
Email Uniqueness Check
         │
         ▼
Password Hashing (Bcrypt)
         │
         ▼
User Creation in Database
         │
         ▼
Response with User Data
```

#### 2. OTP-Based Login Flow
```
OTP Generation Request
         │
         ▼
User Existence Verification
         │
         ▼
Rate Limit Check
         │
         ▼
6-Digit OTP Generation
         │
         ▼
OTP Hashing and Storage
         │
         ▼
Email Delivery (Future)
         │
         ▼
OTP Verification Request
         │
         ▼
OTP Validation and Cleanup
         │
         ▼
JWT Token Generation
         │
         ▼
Authentication Success
```

#### 3. Google OAuth Flow
```
OAuth Initiation
         │
         ▼
State Parameter Generation
         │
         ▼
Google Authorization URL
         │
         ▼
Google Callback Processing
         │
         ▼
User Info Retrieval
         │
         ▼
User Creation/Update
         │
         ▼
JWT Token Generation
```

### Service Layer Architecture

#### OTPService
**Responsibilities**:
- Secure 6-digit OTP generation using `secrets`
- OTP expiration time calculation
- OTP verification with automatic cleanup
- Expired OTP cleanup operations

**Security Features**:
- Cryptographically secure random generation
- Hashed storage (never store plain OTPs)
- Automatic expiration and cleanup
- Single-use verification

#### EmailService (Future Enhancement)
**Planned Responsibilities**:
- SMTP configuration and connection management
- OTP email template rendering
- Delivery status tracking
- Retry mechanisms for failed deliveries

#### SecurityService
**Responsibilities**:
- OAuth state management
- Request sanitization and validation
- Suspicious activity detection
- Security utility functions

### Error Handling Strategy
- **Comprehensive Exception Handling**: Catch and handle specific exceptions
- **User-Friendly Error Messages**: Never expose internal system details
- **Security-First Approach**: Generic error messages to prevent information disclosure
- **Structured Error Responses**: Consistent error response format
- **Logging**: Comprehensive error logging for debugging and monitoring

---

## Security Implementation

### Authentication Mechanisms

#### 1. JWT (JSON Web Tokens)
**Implementation**:
- **Access Tokens**: Short-lived (30 minutes default)
- **Refresh Tokens**: Long-lived (7 days default) with unique JTI
- **Algorithm**: HS256 (HMAC with SHA-256)
- **Library**: `python-jose[cryptography]`

**Security Features**:
```python
def create_refresh_token(subject, expires_delta=None):
    # Unique JWT ID for token revocation
    jti = uuid.uuid4().hex
    to_encode = {"exp": expire, "sub": str(subject), "jti": jti}
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
```

#### 2. Password Security
**Hashing**: Bcrypt with `passlib`
**Validation Rules**:
- Minimum 8 characters
- At least one lowercase letter
- At least one uppercase letter
- At least one digit
- At least one special character (@$!%*?&)
- Maximum 128 characters

#### 3. OAuth 2.0 (Google)
**Implementation**:
- Authorization Code flow
- State parameter for CSRF protection
- Secure credential handling
- User profile information retrieval

### Security Middleware

#### SecurityHeadersMiddleware
**Headers Applied**:
```python
response.headers["X-Content-Type-Options"] = "nosniff"
response.headers["X-Frame-Options"] = "DENY"
response.headers["X-XSS-Protection"] = "1; mode=block"
response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
response.headers["Content-Security-Policy"] = "default-src 'self'; ..."
```

#### RateLimitMiddleware
**Features**:
- Global rate limiting (100 requests/minute per IP)
- Memory-based rate limit tracking
- Automatic cleanup of expired entries
- Customizable limits per endpoint

#### RequestLoggingMiddleware
**Logging Features**:
- Request details (method, URL, IP, User-Agent)
- Response time tracking
- Status code monitoring
- Slow request detection (>2 seconds)
- Security event logging

### Input Validation and Sanitization
- **Pydantic Validation**: Type checking and format validation
- **Email Sanitization**: Normalize and validate email addresses
- **SQL Injection Prevention**: SQLAlchemy ORM with parameterized queries
- **XSS Prevention**: Input sanitization and output encoding

### Token Management
#### Logout Implementation
1. **Refresh Token Invalidation**: Add JTI to blacklist
2. **Database Storage**: Store invalidated tokens with expiration
3. **Verification**: Check token blacklist on refresh attempts
4. **Cleanup**: Automatic removal of expired blacklist entries

---

## Testing Strategy

### Test Structure
```
tests/
├── conftest.py                 # Pytest configuration and fixtures
├── test_google_auth_fixed.py   # Google OAuth integration tests
├── test_logout_fixed.py        # Comprehensive logout tests
└── test_logout_simple.py       # Basic logout functionality tests
```

### Testing Framework
- **Primary**: `pytest` with `pytest-asyncio`
- **HTTP Client**: `httpx` and FastAPI's `TestClient`
- **Database**: In-memory SQLite for isolated testing
- **Mocking**: `unittest.mock` for external dependencies

### Test Configuration (conftest.py)
```python
@pytest.fixture(scope="session")
def test_client():
    """Create a test client for FastAPI application."""
    with TestClient(app, follow_redirects=False) as client:
        yield client

@pytest.fixture
def test_db():
    """Create isolated test database session."""
    engine = create_engine("sqlite:///:memory:", 
                          connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    # ... session management
```

### Test Coverage Areas

#### 1. Authentication Tests
- User registration with various input scenarios
- Password validation edge cases
- Login flow with valid/invalid credentials
- JWT token generation and validation

#### 2. OTP Tests
- OTP generation and storage
- OTP verification with correct/incorrect codes
- OTP expiration handling
- Rate limiting enforcement

#### 3. OAuth Tests (test_google_auth_fixed.py)
- Google OAuth initiation
- Callback processing
- User creation from OAuth data
- Error handling for OAuth failures

#### 4. Logout Tests
- **test_logout_fixed.py**: Comprehensive logout scenarios
- **test_logout_simple.py**: Basic logout functionality
- Token invalidation verification
- Refresh token blacklisting

### Mock Strategies
- **External APIs**: Mock Google OAuth endpoints
- **Email Service**: Mock SMTP operations
- **Time-dependent Operations**: Mock datetime for consistent testing
- **Database Operations**: Use test database with rollback

### Continuous Integration Considerations
- **Environment Isolation**: Test-specific environment variables
- **Database Setup**: Automated test database creation
- **Cleanup**: Proper teardown of test resources
- **Parallel Execution**: Thread-safe test design

---

## Developer Onboarding

### Prerequisites
- **Python**: 3.8+ (recommended 3.9+)
- **PostgreSQL**: 12+ for production
- **Git**: Version control
- **IDE**: VS Code with Python extension recommended

### Local Development Setup

#### 1. Environment Setup
```powershell
# Clone the repository
git clone <repository-url>
cd auth_service

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -r requirements.txt
```

#### 2. Environment Configuration
```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# Key variables to set:
# - DATABASE_URL
# - SECRET_KEY
# - GOOGLE_CLIENT_ID (optional)
# - GOOGLE_CLIENT_SECRET (optional)
```

#### 3. Database Setup
```powershell
# Run database migrations
alembic upgrade head

# Or create initial database (development)
python setup_database.py
```

#### 4. Run the Application
```powershell
# Development server
python main.py

# Or with uvicorn directly
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### Development Workflow

#### 1. Code Style and Conventions
- **PEP 8**: Python style guidelines
- **Type Hints**: Use type annotations for better code documentation
- **Docstrings**: Document all functions and classes
- **Import Organization**: Standard library, third-party, local imports

#### 2. Database Migrations
```powershell
# Create new migration
alembic revision --autogenerate -m "Description of changes"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1
```

#### 3. Testing
```powershell
# Run all tests
pytest

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/test_logout_fixed.py

# Run with verbose output
pytest -v
```

#### 4. Adding New Features

##### Adding New Endpoints
1. **Define Schema**: Create Pydantic models in `schemas/`
2. **Database Model**: Add SQLAlchemy model if needed
3. **CRUD Operations**: Implement database operations in `crud/`
4. **Business Logic**: Add service layer logic in `services/`
5. **Router**: Create endpoint in appropriate router
6. **Tests**: Write comprehensive tests
7. **Documentation**: Update API documentation

##### Example: Adding User Profile Update
```python
# 1. Schema (schemas/user_schema.py)
class UserUpdate(BaseModel):
    full_name: Optional[str] = None

# 2. CRUD (crud/user_crud.py)
def update_user(self, user_id: int, data: dict) -> User:
    # Implementation

# 3. Router (routers/auth_router.py)
@router.put("/profile", response_model=UserResponse)
async def update_profile(
    update_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Implementation
```

### Common Development Tasks

#### 1. Adding Environment Variables
```python
# 1. Add to core/config.py
class Settings(BaseSettings):
    NEW_SETTING: str = "default_value"

# 2. Update .env.example
NEW_SETTING=production_value
```

#### 2. Database Schema Changes
```powershell
# 1. Modify model in models/
# 2. Generate migration
alembic revision --autogenerate -m "Add new column"
# 3. Review generated migration
# 4. Apply migration
alembic upgrade head
```

#### 3. Adding New Dependencies
```powershell
# 1. Install package
pip install new-package

# 2. Update requirements.txt
pip freeze | findstr new-package >> requirements.txt
```

### Debugging and Troubleshooting

#### Common Issues

1. **Database Connection Errors**
   - Check DATABASE_URL in .env
   - Verify PostgreSQL is running
   - Check network connectivity

2. **Import Errors**
   - Verify virtual environment activation
   - Check PYTHONPATH configuration
   - Ensure all dependencies installed

3. **JWT Token Issues**
   - Verify SECRET_KEY configuration
   - Check token expiration settings
   - Validate JWT algorithm settings

4. **Migration Errors**
   - Check database schema manually
   - Review migration files for conflicts
   - Consider manual migration fixes

#### Debugging Tools
- **Logging**: Use built-in logging configuration
- **Database Inspection**: SQLAlchemy inspector for schema verification
- **API Testing**: Use `/docs` endpoint for Swagger UI
- **Token Debugging**: JWT.io for token inspection

#### Performance Monitoring
- **Request Logging**: Monitor response times in logs
- **Database Queries**: Enable SQLAlchemy query logging
- **Memory Usage**: Monitor application memory consumption
- **Rate Limiting**: Check rate limit hit rates

---

## Configuration Management

### Environment-Based Configuration
The application uses **Pydantic Settings** for robust configuration management:

```python
class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/auth_service_dev"
    
    # Security
    SECRET_KEY: str  # MUST be overridden in production
    ALGORITHM: str = "HS256"
    
    # CORS - JSON string format
    BACKEND_CORS_ORIGINS: str = '["http://localhost:3000"]'
    
    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        return json.loads(self.BACKEND_CORS_ORIGINS)
```

### Configuration Categories

#### 1. Security Configuration
- **SECRET_KEY**: JWT signing key (critical for production)
- **ALGORITHM**: JWT algorithm (HS256)
- **Token Expiration**: Access and refresh token lifetimes
- **OTP Settings**: Expiration, attempts, rate limits

#### 2. Database Configuration
- **DATABASE_URL**: Primary database connection
- **Connection Pooling**: SQLAlchemy engine configuration
- **Migration Settings**: Alembic configuration

#### 3. CORS Configuration
- **Environment-Driven**: JSON string format for origins
- **Development**: localhost origins
- **Production**: Specific domain origins

#### 4. Logging Configuration
- **LOG_LEVEL**: Configurable logging verbosity
- **Structured Logging**: JSON format for production
- **Security Logging**: Authentication events

### Production Considerations
- **Secret Management**: Use environment variables or secret managers
- **Database**: PostgreSQL with connection pooling
- **HTTPS**: SSL/TLS termination at load balancer
- **Monitoring**: Application performance monitoring

---

## API Layer

### FastAPI Application Structure
```python
app = FastAPI(
    title="Auth Service",
    description="Authentication service for the EdTech platform",
    version="1.0.0"
)

# Middleware stack (order matters)
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, calls_per_minute=100)
app.add_middleware(CORSMiddleware, ...)

# Router inclusion
app.include_router(auth_router)
```

### Endpoint Documentation
Comprehensive API documentation available at `/docs` (Swagger UI) and `/redoc`.

### Response Standards
- **Consistent Format**: Pydantic schema validation
- **HTTP Status Codes**: Proper status code usage
- **Error Responses**: Structured error messages
- **Security**: No sensitive data exposure

---

## Deployment Considerations

### Production Checklist
- [ ] Environment variables configured
- [ ] SECRET_KEY set to secure random value
- [ ] Database connection pooling configured
- [ ] HTTPS enabled
- [ ] Rate limiting tuned for production load
- [ ] Logging configured for monitoring
- [ ] Database migrations applied
- [ ] Health check endpoints verified

### Scaling Considerations
- **Horizontal Scaling**: Stateless application design
- **Database**: Connection pooling and read replicas
- **Caching**: Redis for session management
- **Load Balancing**: Multiple application instances
- **Rate Limiting**: Distributed rate limiting with Redis

### Monitoring and Observability
- **Health Checks**: `/health` endpoint
- **Metrics**: Application performance metrics
- **Logging**: Structured logging for analysis
- **Alerting**: Critical error notifications
- **Tracing**: Request tracing for debugging

---

## Code Quality and Maintenance

### Code Quality Standards
- **Type Hints**: Comprehensive type annotations
- **Documentation**: Docstrings for all public functions
- **Error Handling**: Comprehensive exception handling
- **Security**: Input validation and sanitization
- **Performance**: Efficient database queries and caching

### Maintenance Tasks
- **Security Updates**: Regular dependency updates
- **Database Cleanup**: Expired token and OTP cleanup
- **Log Rotation**: Log file management
- **Performance Monitoring**: Query optimization
- **Backup Strategy**: Database backup procedures

---

## Conclusion

This documentation provides a comprehensive overview of the Auth Service codebase. The service is designed with security, scalability, and maintainability as primary concerns. The modular architecture ensures that components can be developed, tested, and deployed independently while maintaining clear separation of concerns.

For additional information or clarification on any aspect of the system, please refer to the inline code documentation or contact the development team.

**Version**: 1.0  
**Last Updated**: June 12, 2025  
**Maintained By**: EdTech Development Team
