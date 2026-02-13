# Authentication Service

A secure, production-ready authentication microservice for the AI EdTech platform. Built with FastAPI, it provides multiple authentication methods including email/password, OTP-based passwordless authentication, and Google OAuth 2.0 integration.

## What This Microservice Does

The Authentication Service is responsible for:

- **User Registration & Management** - Create and manage user accounts with secure password storage
- **Multiple Authentication Methods**:
  - Email/Password authentication with strong password requirements
  - OTP-based passwordless authentication via email
  - Google OAuth 2.0 social login
- **JWT Token Management** - Issue and manage access tokens (7-day validity) and refresh tokens
- **Email Verification** - OTP-based email verification system
- **Secure Session Management** - Token refresh and logout with token invalidation
- **Comprehensive Security** - Rate limiting, input sanitization, CSRF protection, and security headers

## How It Works

### Architecture

The service is built using:
- **FastAPI** - Modern Python web framework with automatic API documentation
- **PostgreSQL** - Relational database for user data and OTP storage
- **SQLAlchemy** - ORM for database operations
- **JWT (JSON Web Tokens)** - Stateless authentication mechanism
- **Bcrypt** - Secure password hashing
- **FastAPI-Mail** - Email delivery for OTP codes

### Authentication Flows

#### 1. Email/Password Authentication
```
User registers → Password hashed with bcrypt → Account created (unverified)
User requests OTP → 6-digit code generated → Sent via email
User verifies OTP → Email marked as verified
User logs in with password → JWT tokens issued
```

#### 2. OTP-Based Passwordless Authentication
```
User enters email → OTP generated and emailed → User verifies OTP → JWT tokens issued
```

#### 3. Google OAuth 2.0 Flow
```
User clicks "Login with Google" → Redirected to Google
Google authenticates → Returns authorization code
Service exchanges code for user info → Creates/links account → JWT tokens issued
```

#### 4. Token Management
```
Access Token: Short-lived (7 days), used for API requests
Refresh Token: Long-lived (7 days), used to obtain new access tokens
Logout: Refresh token added to denylist, cannot be reused
```

### Security Features

- **Rate Limiting**: 
  - Global: 100 requests/minute per IP
  - OTP Requests: 5 per hour per email
  - OTP Verification: 3 attempts per minute per email
  - Login Attempts: 5 per 15 minutes per email
- **Input Sanitization**: Email normalization, XSS prevention, SQL injection protection
- **Security Headers**: CSP, X-Frame-Options, X-Content-Type-Options
- **Password Requirements**: Minimum 8 characters, uppercase, lowercase, digit, special character
- **OTP Security**: SHA256 hashed storage, 10-minute expiry, one-time use
- **CSRF Protection**: OAuth state parameter validation with expiry
- **Request Logging**: Comprehensive logging for security monitoring

### Database Schema

**Users Table**:
- Basic info: id, email, full_name
- Authentication: hashed_password (nullable for OAuth users), google_id
- Status: is_active, is_verified
- Timestamps: created_at, updated_at

**OTPs Table**:
- OTP info: user_id, email, otp_code (SHA256 hashed), purpose
- Expiry: expires_at (10 minutes from creation)

**Invalidated Tokens Table**:
- Token denylist: jti (JWT ID), user_id, expires_at
- Used for secure logout functionality

## How to Use It

### Prerequisites

- Python 3.8+
- PostgreSQL database
- SMTP email server (for OTP delivery)
- Google OAuth credentials (optional, for Google login)

### Installation

1. **Clone the repository and navigate to the service directory**:
```bash
cd C:\Users\Public\Documents\Akshay\ai_edtech\code\auth_service
```

2. **Create a virtual environment**:
```bash
python -m venv venv
venv\Scripts\activate  # On Windows
# On Linux/Mac: source venv/bin/activate
```

3. **Install dependencies**:
```bash
pip install -r requirements.txt
```

4. **Set up required credentials** (see [Credentials Setup Guide](#credentials-setup-guide) below for detailed instructions)

5. **Configure environment variables**:

Create a `.env` file in the service root directory by copying the example:
```env
# Database Configuration
DATABASE_URL=postgresql://user:password@localhost:5432/auth_service_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=auth_service_db
POSTGRES_USER=user
POSTGRES_PASSWORD=password

# JWT Configuration
SECRET_KEY=your_super_secret_key_change_this_in_production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080  # 7 days
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS Configuration (JSON array of allowed origins)
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000", "https://yourdomain.com"]

# OTP Configuration
OTP_EXPIRY_MINUTES=10
OTP_MAX_ATTEMPTS=3
OTP_RATE_LIMIT_MINUTES=1
OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR=5

# Authentication Settings
REQUIRE_EMAIL_VERIFICATION=True  # Set to False for development

# Google OAuth Credentials (optional)
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Email Configuration (required for OTP delivery)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
EMAIL_FROM=your_email@gmail.com
EMAIL_STARTTLS=True
EMAIL_SSL_TLS=False

# Logging
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

**Note**: Replace all placeholder values with your actual credentials. See the [Credentials Setup Guide](#credentials-setup-guide) section below for detailed instructions on obtaining each credential.

6. **Initialize the database**:

Run database migrations:
```bash
alembic upgrade head
```

Or create tables directly:
```bash
python setup_database.py
`` Credentials Setup Guide

This section provides detailed instructions for obtaining and configuring all required credentials for the authentication service.

### 1. PostgreSQL Database Setup

**Option A: Local PostgreSQL Installation**

**Windows**:
1. Download PostgreSQL from https://www.postgresql.org/download/windows/
2. Run the installer and note the password you set for the `postgres` user
3. Open pgAdmin or use command line:
```bash
psql -U postgres
```
4. Create a new database:
```sql
CREATE DATABASE auth_service_db;
CREATE USER auth_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE auth_service_db TO auth_user;
```

**Linux (Ubuntu/Debian)**:
```bash
# Install PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE auth_service_db;
CREATE USER auth_user WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE auth_service_db TO auth_user;
\q
```

**Mac**:
```bash
# Install via Homebrew
brew install postgresql
brew services start postgresql

# Create database
createdb auth_service_db
psql auth_service_db
```

**Update your .env file**:
```env
DATABASE_URL=postgresql://auth_user:your_secure_password@localhost:5432/auth_service_db
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=auth_service_db
POSTGRES_USER=auth_user
POSTGRES_PASSWORD=your_secure_password
```

**Option B: Cloud PostgreSQL (Recommended for Production)**

**AWS RDS**:
1. Go to AWS Console → RDS → Create Database
2. Choose PostgreSQL engine
3. Select instance size and configure security groups
4. Note the endpoint, port, database name, username, and password
5. Update `DATABASE_URL` with: `postgresql://username:password@endpoint:5432/dbname`

**Heroku Postgres**:
1. Create a Heroku app: `heroku create`
2. Add Postgres: `heroku addons:create heroku-postgresql:hobby-dev`
3. Get credentials: `heroku config:get DATABASE_URL`

**Other providers**: DigitalOcean, Google Cloud SQL, Azure Database for PostgreSQL

### 2. JWT Secret Key Generation

The `SECRET_KEY` is used to sign and verify JWT tokens. It must be a strong, random string.

**Generate a secure secret key**:

**Method 1 - Python**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**Method 2 - OpenSSL**:
```bash
openssl rand -base64 32
```

**Method 3 - PowerShell (Windows)**:
```powershell
-join ((48..57) + (65..90) + (97..122) | Get-Random -Count 32 | % {[char]$_})
```

**Update your .env file**:
```env
SECRET_KEY=your_generated_secret_key_here_min_32_chars
ALGORITHM=HS256
```

**Important**: 
- Never commit your actual secret key to version control
- Use a different secret key for each environment (dev, staging, production)
- Store production keys in secure vaults (AWS Secrets Manager, Azure Key Vault, HashiCorp Vault)

### 3. Google OAuth 2.0 Credentials Setup

Google OAuth allows users to sign in with their Google accounts.

**Step-by-Step Setup**:

1. **Go to Google Cloud Console**:
   - Visit https://console.cloud.google.com/

2. **Create a New Project** (or select existing):
   - Click on project dropdown → New Project
   - Enter project name (e.g., "AI EdTech Auth Service")
   - Click "Create"

3. **Enable Google+ API**:
   - Go to "APIs & Services" → "Library"
   - Search for "Google+ API"
   - Click "Enable"

4. **Configure OAuth Consent Screen**:
   - Go to "APIs & Services" → "OAuth consent screen"
   - Choose "External" user type → Click "Create"
   - Fill in required fields:
     - App name: "AI EdTech Platform"
     - User support email: your email
     - Developer contact: your email
   - Click "Save and Continue"
   - Add scopes:
     - `openid`
     - `email`
     - `profile`
   - Click "Save and Continue"
   - Add test users (during development)
   - Click "Save and Continue"

5. **Create OAuth 2.0 Credentials**:
   - Go to "APIs & Services" → "Credentials"
   - Click "Create Credentials" → "OAuth client ID"
   - Application type: "Web application"
   - Name: "Auth Service Web Client"
   - Authorized JavaScript origins:
     - `http://localhost:8006`
     - `http://localhost:5173` (your frontend)
     - Add your production domain: `https://yourdomain.com`
   - Authorized redirect URIs:
     - `http://localhost:8006/auth/google/callback`
     - Add production callback: `https://yourdomain.com/auth/google/callback`
   - Click "Create"

6. **Copy Credentials**:
   - Copy the "Client ID" (looks like: `123456789-abcdefg.apps.googleusercontent.com`)
   - Copy the "Client Secret" (looks like: `GOCSPX-abc123xyz`)

7. **Update your .env file**:
```env
GOOGLE_CLIENT_ID=123456789-abcdefg.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-abc123xyz
```

**For Production**:
- Update authorized origins and redirect URIs to use your production domain
- Submit app for verification if you need >100 users
- Set OAuth consent screen to "In Production"

**Troubleshooting**:
- Error "redirect_uri_mismatch": Ensure callback URL in code matches Google Console exactly
- Error "access_denied": Check OAuth consent screen settings and test users

### 4. Email/SMTP Credentials Setup

Email credentials are required to send OTP codes for authentication.

#### Option A: Gmail (Recommended for Development)

**Using Gmail App Passwords** (Most Secure):

1. **Enable 2-Factor Authentication**:
   - Go to https://myaccount.google.com/security
   - Click "2-Step Verification" → Follow setup instructions

2. **Generate App Password**:
   - Go to https://myaccount.google.com/apppasswords
   - Select app: "Mail"
   - Select device: "Other" → Enter "Auth Service"
   - Click "Generate"
   - Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

3. **Update your .env file**:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@gmail.com
EMAIL_PASSWORD=abcd efgh ijkl mnop  # App password, not regular password
EMAIL_FROM=your.email@gmail.com
EMAIL_STARTTLS=True
EMAIL_SSL_TLS=False
```

**Important Notes**:
- Never use your actual Gmail password
- App passwords only work with 2FA enabled
- Gmail has sending limits: 500 emails/day for free accounts
- Remove spaces from app password in .env file: `abcdefghijklmnop`

#### Option B: SendGrid (Recommended for Production)

SendGrid is a professional email service with high deliverability.

1. **Create SendGrid Account**:
   - Go to https://signup.sendgrid.com/
   - Sign up for free tier (100 emails/day)

2. **Verify Sender Identity**:
   - Go to Settings → Sender Authentication
   - Verify a Single Sender (email address) OR
   - Authenticate Your Domain (recommended for production)

3. **Create API Key**:
   - Go to Settings → API Keys
   - Click "Create API Key"
   - Name: "Auth Service"
   - Permissions: "Restricted Access" → Check "Mail Send"
   - Click "Create & View"
   - Copy the API key (starts with `SG.`)

4. **Update your .env file**:
```env
EMAIL_HOST=smtp.sendgrid.net
EMAIL_PORT=587
EMAIL_USERNAME=apikey  # Literal string "apikey"
EMAIL_PASSWORD=SG.your_actual_api_key_here
EMAIL_FROM=verified@yourdomain.com
EMAIL_STARTTLS=True
EMAIL_SSL_TLS=False
```

#### Option C: Amazon SES

1. **Create AWS Account**: https://aws.amazon.com/
2. **Go to Amazon SES Console**
3. **Verify Email Address or Domain**
4. **Create SMTP Credentials**:
   - Go to "SMTP Settings"
   - Click "Create My SMTP Credentials"
   - Note the username and password
5. **Update .env**:
```env
EMAIL_HOST=email-smtp.us-east-1.amazonaws.com  # Adjust region
EMAIL_PORT=587
EMAIL_USERNAME=your_smtp_username
EMAIL_PASSWORD=your_smtp_password
EMAIL_FROM=verified@yourdomain.com
EMAIL_STARTTLS=True
EMAIL_SSL_TLS=False
```

#### Option D: Other SMTP Providers

**Mailgun**: https://www.mailgun.com/
**Postmark**: https://postmarkapp.com/
**Outlook/Office 365**: 
```env
EMAIL_HOST=smtp.office365.com
EMAIL_PORT=587
EMAIL_USERNAME=your.email@outlook.com
EMAIL_PASSWORD=your_password
```

**Testing Email Configuration**:
```bash
# Run the test script included in the service
python test_smtp.py
```

### 5. CORS Origins Configuration

Configure which frontend domains can access your auth service.

**Development Setup**:
```env
BACKEND_CORS_ORIGINS=["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]
```

**Production Setup**:
```env
BACKEND_CORS_ORIGINS=["https://yourdomain.com", "https://app.yourdomain.com", "https://www.yourdomain.com"]
```

**Important**:
- Must be valid JSON array format
- Include http/https protocol
- Include port if non-standard
- No trailing slashes
- Add all subdomains that need access

### Security Best Practices for Credentials

1. **Never Commit Credentials**:
   - Always add `.env` to `.gitignore`
   - Use `.env.example` with placeholder values for documentation
   - Review commits before pushing to ensure no secrets leaked

2. **Use Environment-Specific Credentials**:
   - Development: `.env.development`
   - Staging: `.env.staging`
   - Production: `.env.production`

3. **Production Credential Management**:
   - Use secret management services:
     - **AWS Secrets Manager**
     - **Azure Key Vault**
     - **HashiCorp Vault**
     - **Google Cloud Secret Manager**
   - Rotate credentials regularly (every 90 days)
   - Use principle of least privilege

4. **Credential Rotation**:
   ```bash
   # Example: Rotate JWT secret
   # 1. Generate new secret
   NEW_SECRET=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
   
   # 2. Update .env with new secret
   # 3. Restart service
   # 4. Old tokens will become invalid (users need to re-login)
   ```

5. **Monitoring and Alerts**:
   - Set up alerts for failed authentication attempts
   - Monitor for unusual API usage patterns
   - Track credential usage in logs (without logging the actual credentials)

### Verifying Your Setup

After configuring all credentials, verify the setup:

1. **Test Database Connection**:
```bash
python -c "from database.session import engine; engine.connect(); print('Database connected successfully!')"
```

2. **Test Email Configuration**:
```bash
python test_smtp.py
```

3. **Verify Google OAuth** (if configured):
```bash
python google_oauth_verification.py
```

4. **Start the Service**:
```bash
uvicorn main:app --host 0.0.0.0 --port 8006
```

5. **Check Health Endpoint**:
```bash
curl http://localhost:8006/health
# Should return: {"status": "healthy"}
```

6. **Try API Documentation**:
   - Open http://localhost:8006/docs
   - Test registration endpoint with sample data

### Troubleshooting Credentials

**Database Connection Errors**:
- Error: "could not connect to server"
  - Check PostgreSQL is running: `pg_isready`
  - Verify host/port in `.env`
  - Check firewall rules

**Email Sending Errors**:
- Error: "Authentication failed"
  - Verify EMAIL_USERNAME and EMAIL_PASSWORD
  - For Gmail: Use app password, not regular password
  - Check 2FA is enabled for Gmail

- Error: "Connection refused"
  - Verify EMAIL_HOST and EMAIL_PORT
  - Check firewall/network settings
  - Try alternative port: 465 (SSL) or 587 (TLS)

**Google OAuth Errors**:
- Error: "redirect_uri_mismatch"
  - Callback URL must match exactly in Google Console
  - Include http:// or https://
  - Check for trailing slashes

- Error: "invalid_client"
  - Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
  - Ensure OAuth consent screen is configured

**JWT Token Errors**:
- Error: "Invalid token"
  - Check SECRET_KEY is set and consistent
  - Verify ALGORITHM is "HS256"
  - Ensure token hasn't expired

##`

### Running the Service

**Start the service on port 8006**:

```bash
uvicorn main:app --host 0.0.0.0 --port 8006 --reload
```

For production deployment:
```bash
uvicorn main:app --host 0.0.0.0 --port 8006 --workers 4
```

The service will be available at:
- **API**: http://localhost:8006
- **API Documentation**: http://localhost:8006/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8006/redoc (ReDoc)

### API Endpoints

#### Public Endpoints (No Authentication Required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register a new user account |
| POST | `/auth/login` | Login with email and password |
| POST | `/auth/request-otp` | Request an OTP code via email |
| POST | `/auth/verify-otp` | Verify OTP and get access tokens |
| POST | `/auth/resend-otp` | Resend OTP code |
| GET | `/auth/google/login` | Initiate Google OAuth flow |
| GET | `/auth/google/callback` | Google OAuth callback (handled automatically) |
| POST | `/auth/refresh-token` | Get new access token using refresh token |
| POST | `/auth/logout` | Logout and invalidate refresh token |
| GET | `/health` | Health check endpoint |

#### Protected Endpoints (Requires Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/me` | Get current authenticated user information |

### API Usage Examples

#### 1. Register a New User

```bash
curl -X POST http://localhost:8006/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!",
    "full_name": "John Doe"
  }'
```

#### 2. Request OTP for Email Verification

```bash
curl -X POST http://localhost:8006/auth/request-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "purpose": "verification"
  }'
```

#### 3. Verify OTP

```bash
curl -X POST http://localhost:8006/auth/verify-otp \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "otp_code": "123456",
    "purpose": "verification"
  }'
```

Response includes:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "expires_in": 604800,
  "refresh_token_expires_in": 604800,
  "user": {
    "id": 1,
    "email": "user@example.com",
    "full_name": "John Doe",
    "is_active": true,
    "is_verified": true
  }
}
```

#### 4. Login with Email and Password

```bash
curl -X POST http://localhost:8006/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "SecurePass123!"
  }'
```

#### 5. Access Protected Endpoint

```bash
curl -X GET http://localhost:8006/auth/me \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

#### 6. Refresh Access Token

```bash
curl -X POST http://localhost:8006/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

#### 7. Logout

```bash
curl -X POST http://localhost:8006/auth/logout \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "eyJhbGciOiJIUzI1NiIs..."
  }'
```

### Client Integration

To integrate with your frontend application:

1. **Set Authorization Header**:
```javascript
const response = await fetch('http://localhost:8006/auth/me', {
  headers: {
    'Authorization': `Bearer ${accessToken}`,
    'Content-Type': 'application/json'
  }
});
```

2. **Handle Token Refresh**:
```javascript
// When access token expires, use refresh token
const refreshResponse = await fetch('http://localhost:8006/auth/refresh-token', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ refresh_token: refreshToken })
});

const { access_token } = await refreshResponse.json();
// Store new access token and retry request
```

3. **Google OAuth Integration**:
```javascript
// Redirect user to Google login
window.location.href = 'http://localhost:8006/auth/google/login';

// After successful authentication, Google redirects back with tokens
// Handle the callback on your frontend
```

### Testing

Run the test suite:
```bash
pytest tests/ -v
```

Run specific test file:
```bash
pytest tests/test_authentication_flows.py -v
```

### Database Management

**Create a new migration**:
```bash
alembic revision --autogenerate -m "Description of changes"
```

**Apply migrations**:
```bash
alembic upgrade head
```

**Rollback migration**:
```bash
alembic downgrade -1
```

### Monitoring and Logs

The service logs all requests with the following information:
- Request method, URL, client IP
- Response status code and processing time
- Failed authentication attempts
- Rate limit violations
- Slow requests (>2 seconds)

Logs are written to stdout and can be configured via the `LOG_LEVEL` environment variable.

### Production Deployment Checklist

- [ ] Change `SECRET_KEY` to a strong random value
- [ ] Set `DATABASE_URL` to production PostgreSQL instance
- [ ] Configure CORS origins to match your frontend domain
- [ ] Set up proper email SMTP credentials
- [ ] Enable `REQUIRE_EMAIL_VERIFICATION=True`
- [ ] Configure Google OAuth credentials (if using)
- [ ] Set `LOG_LEVEL=WARNING` or `ERROR` for production
- [ ] Use a process manager (systemd, supervisor) or containerization (Docker)
- [ ] Set up HTTPS with a reverse proxy (nginx, traefik)
- [ ] Configure database connection pooling
- [ ] Set up database backups
- [ ] Monitor rate limiting and adjust thresholds as needed
- [ ] Implement Redis for distributed rate limiting (optional)

### Troubleshooting

**Service won't start on port 8006**:
- Check if another service is using port 8006: `netstat -ano | findstr :8006`
- Kill the process or choose a different port

**Database connection errors**:
- Verify PostgreSQL is running: `pg_isready`
- Check DATABASE_URL in `.env` file
- Ensure database exists: `psql -U user -c "CREATE DATABASE auth_service_db;"`

**OTP emails not sending**:
- Verify EMAIL_HOST, EMAIL_USERNAME, EMAIL_PASSWORD in `.env`
- For Gmail, use App Password, not regular password
- Check SMTP server allows connections from your IP

**Google OAuth not working**:
- Verify GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET
- Check redirect URI matches in Google Cloud Console: `http://localhost:8006/auth/google/callback`
- Ensure OAuth consent screen is configured

### Support and Documentation

- **API Documentation**: Visit http://localhost:8006/docs after starting the service
- **Logs**: Check console output for detailed error messages
- **Database Schema**: See migration files in `alembic/versions/`

## Making This Service Multi-Tenant (Generic Standalone Auth Service)

This section provides guidance on converting this single-tenant authentication service into a multi-tenant system that can serve multiple applications/tenants from a single deployment.

### What is Multi-Tenancy?

Multi-tenancy allows a single instance of the auth service to serve multiple independent organizations, applications, or clients (tenants). Each tenant has:
- Isolated user data
- Custom branding and configuration
- Separate OAuth credentials
- Independent rate limiting
- Isolated token scopes

### Architecture Changes Required

#### 1. Database Schema Modifications

**Add a Tenants Table**:
```python
# models/tenant_model.py
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from database.session import Base

class Tenant(Base):
    __tablename__ = "tenants"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_key = Column(String(50), unique=True, index=True, nullable=False)  # e.g., "company-a"
    tenant_name = Column(String(255), nullable=False)  # Display name
    domain = Column(String(255), unique=True, index=True)  # e.g., "companya.com"
    is_active = Column(Boolean, default=True, nullable=False)
    
    # OAuth Configuration (per tenant)
    google_client_id = Column(String(255), nullable=True)
    google_client_secret = Column(String(255), nullable=True)
    
    # Email Configuration (per tenant)
    email_host = Column(String(255), nullable=True)
    email_port = Column(Integer, nullable=True)
    email_username = Column(String(255), nullable=True)
    email_password = Column(String(255), nullable=True)
    email_from = Column(String(255), nullable=True)
    
    # Branding
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), nullable=True)  # Hex color
    
    # Rate Limiting Configuration (per tenant)
    max_otp_requests_per_hour = Column(Integer, default=5)
    max_login_attempts = Column(Integer, default=5)
    
    # CORS Configuration
    allowed_origins = Column(Text, nullable=True)  # JSON array
    
    # API Keys for tenant management
    api_key = Column(String(255), unique=True, index=True, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
```

**Modify Users Table**:
```python
# models/user_model.py - Add tenant relationship
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)  # NEW
    email = Column(String, nullable=False)  # Remove unique=True
    # ... rest of the fields
    
    # Add composite unique constraint: email must be unique per tenant
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_google_id', 'google_id'),
        Index('idx_user_tenant', 'tenant_id'),
        UniqueConstraint('tenant_id', 'email', name='uix_tenant_email'),  # NEW
        UniqueConstraint('tenant_id', 'google_id', name='uix_tenant_google_id'),  # NEW
    )
```

**Modify OTPs Table**:
```python
# models/otp_model.py - Add tenant relationship
class OTP(Base):
    __tablename__ = "otps"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)  # NEW
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    # ... rest of the fields
```

**Modify Invalidated Tokens Table**:
```python
# models/invalidated_token_model.py - Add tenant relationship
class InvalidatedToken(Base):
    __tablename__ = "invalidated_tokens"
    
    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)  # NEW
    jti = Column(String(64), nullable=False, index=True)  # Remove unique=True
    # ... rest of the fields
    
    __table_args__ = (
        UniqueConstraint('tenant_id', 'jti', name='uix_tenant_jti'),  # NEW
        Index('idx_jti_expires', 'jti', 'expires_at'),
    )
```

#### 2. Tenant Identification Strategy

Choose one of these methods to identify tenants in API requests:

**Option A: Header-Based (Recommended)**:
```python
# middleware/tenant_middleware.py
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

class TenantMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get tenant from custom header
        tenant_key = request.headers.get("X-Tenant-Key")
        api_key = request.headers.get("X-API-Key")
        
        if not tenant_key and not api_key:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Tenant identification required"
            )
        
        # Validate tenant exists and is active
        tenant = await get_tenant_by_key_or_api_key(tenant_key, api_key)
        if not tenant or not tenant.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid or inactive tenant"
            )
        
        # Attach tenant to request state
        request.state.tenant = tenant
        
        response = await call_next(request)
        return response
```

**Option B: Subdomain-Based**:
```python
# Identify tenant by subdomain: tenant1.auth-service.com
def get_tenant_from_subdomain(request: Request) -> str:
    host = request.headers.get("host", "")
    subdomain = host.split('.')[0]
    return subdomain
```

**Option C: Path-Based**:
```python
# Include tenant in URL: /api/v1/{tenant_key}/auth/register
@router.post("/{tenant_key}/auth/register")
async def register_user(tenant_key: str, ...):
    tenant = get_tenant_by_key(tenant_key)
    ...
```

#### 3. JWT Token Modifications

Include tenant information in JWT tokens:

```python
# core/security.py
def create_access_token(
    subject: Union[str, Any], 
    tenant_id: int,
    expires_delta: timedelta = None
) -> str:
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode = {
        "exp": expire, 
        "sub": str(subject),
        "tenant_id": tenant_id,  # NEW: Include tenant context
        "iat": datetime.utcnow()  # Issued at
    }
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt
```

#### 4. CRUD Operations Updates

Update all CRUD operations to include tenant filtering:

```python
# crud/user_crud.py
class UserCRUD:
    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id  # NEW: Store tenant context
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email within tenant scope."""
        return self.db.query(User).filter(
            User.tenant_id == self.tenant_id,  # NEW: Tenant filter
            User.email == email
        ).first()
    
    def create(self, user_data: UserCreate) -> User:
        """Create a new user within tenant scope."""
        db_user = User(
            tenant_id=self.tenant_id,  # NEW: Associate with tenant
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hash_password(user_data.password)
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
```

#### 5. Configuration Management

Use tenant-specific configurations instead of global settings:

```python
# services/tenant_config_service.py
class TenantConfigService:
    """Service to get tenant-specific configuration."""
    
    def __init__(self, tenant: Tenant):
        self.tenant = tenant
    
    def get_email_config(self) -> dict:
        """Get email configuration for tenant."""
        return {
            "MAIL_HOST": self.tenant.email_host or settings.DEFAULT_EMAIL_HOST,
            "MAIL_PORT": self.tenant.email_port or settings.DEFAULT_EMAIL_PORT,
            "MAIL_USERNAME": self.tenant.email_username or settings.DEFAULT_EMAIL_USERNAME,
            "MAIL_PASSWORD": self.tenant.email_password or settings.DEFAULT_EMAIL_PASSWORD,
            "MAIL_FROM": self.tenant.email_from or settings.DEFAULT_EMAIL_FROM,
        }
    
    def get_oauth_config(self) -> dict:
        """Get OAuth configuration for tenant."""
        return {
            "google_client_id": self.tenant.google_client_id,
            "google_client_secret": self.tenant.google_client_secret,
        }
    
    def get_rate_limits(self) -> dict:
        """Get rate limit configuration for tenant."""
        return {
            "otp_requests_per_hour": self.tenant.max_otp_requests_per_hour,
            "login_attempts": self.tenant.max_login_attempts,
        }
    
    def get_cors_origins(self) -> list:
        """Get CORS origins for tenant."""
        import json
        return json.loads(self.tenant.allowed_origins or "[]")
```

#### 6. Rate Limiting Per Tenant

Modify rate limiting to be tenant-aware:

```python
# services/rate_limit_service.py
class RateLimitService:
    def check_rate_limit(
        self, 
        identifier: str,
        tenant_id: int,  # NEW
        max_attempts: int, 
        window_seconds: int
    ) -> Tuple[bool, int, int]:
        # Use tenant-scoped key
        key = f"tenant:{tenant_id}:{identifier}"  # NEW
        # ... rest of the logic
```

#### 7. API Endpoints for Tenant Management

Add admin endpoints to manage tenants:

```python
# routers/admin_router.py
from fastapi import APIRouter, Depends, HTTPException, Header
from typing import Optional

admin_router = APIRouter(prefix="/admin", tags=["admin"])

@admin_router.post("/tenants", response_model=TenantResponse)
async def create_tenant(
    tenant_data: TenantCreate,
    admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
    db: Session = Depends(get_db)
):
    """Create a new tenant (admin only)."""
    # Verify admin API key
    if admin_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    # Generate unique API key for tenant
    import secrets
    api_key = f"tenant_{secrets.token_urlsafe(32)}"
    
    tenant = Tenant(
        tenant_key=tenant_data.tenant_key,
        tenant_name=tenant_data.tenant_name,
        domain=tenant_data.domain,
        api_key=api_key,
        google_client_id=tenant_data.google_client_id,
        google_client_secret=tenant_data.google_client_secret,
        allowed_origins=json.dumps(tenant_data.allowed_origins)
    )
    
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse.model_validate(tenant)

@admin_router.get("/tenants/{tenant_id}", response_model=TenantResponse)
async def get_tenant(
    tenant_id: int,
    admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
    db: Session = Depends(get_db)
):
    """Get tenant details (admin only)."""
    if admin_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    return TenantResponse.model_validate(tenant)

@admin_router.put("/tenants/{tenant_id}", response_model=TenantResponse)
async def update_tenant(
    tenant_id: int,
    tenant_data: TenantUpdate,
    admin_api_key: str = Header(..., alias="X-Admin-API-Key"),
    db: Session = Depends(get_db)
):
    """Update tenant configuration (admin only)."""
    if admin_api_key != settings.ADMIN_API_KEY:
        raise HTTPException(status_code=403, detail="Unauthorized")
    
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    
    for key, value in tenant_data.dict(exclude_unset=True).items():
        setattr(tenant, key, value)
    
    db.commit()
    db.refresh(tenant)
    
    return TenantResponse.model_validate(tenant)
```

#### 8. Update Main Application

Modify `main.py` to include tenant middleware:

```python
# main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from middleware.tenant_middleware import TenantMiddleware  # NEW
from routers.admin_router import admin_router  # NEW

app = FastAPI(title="Multi-Tenant Auth Service")

# Add tenant middleware (before CORS)
app.add_middleware(TenantMiddleware)  # NEW

# Dynamic CORS based on tenant
@app.middleware("http")
async def dynamic_cors_middleware(request: Request, call_next):
    response = await call_next(request)
    
    # Get tenant from request state (set by TenantMiddleware)
    tenant = getattr(request.state, "tenant", None)
    if tenant and tenant.allowed_origins:
        origins = json.loads(tenant.allowed_origins)
        origin = request.headers.get("origin")
        if origin in origins:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
    
    return response

# Include routers
app.include_router(auth_router)
app.include_router(admin_router)  # NEW
```

### Implementation Steps

1. **Create Database Migration**:
```bash
# Add tenant table and relationships
alembic revision --autogenerate -m "Add multi-tenant support"
alembic upgrade head
```

2. **Update Models**: Add tenant relationships to all models

3. **Implement Tenant Middleware**: Choose identification strategy (header/subdomain/path)

4. **Update CRUD Operations**: Add tenant_id filtering to all queries

5. **Modify JWT Tokens**: Include tenant_id in token payload

6. **Update Services**: Make email, OAuth, and rate limiting tenant-aware

7. **Add Admin Endpoints**: Create tenant management API

8. **Update Tests**: Add tenant context to all test cases

9. **Update Documentation**: Document tenant-specific headers/endpoints

### Security Considerations for Multi-Tenancy

1. **Data Isolation**: 
   - Always filter queries by tenant_id
   - Use database row-level security policies (PostgreSQL RLS)
   - Consider separate databases per tenant for strict isolation

2. **API Key Management**:
   - Generate strong, unique API keys per tenant
   - Store API keys hashed (bcrypt/scrypt)
   - Support API key rotation

3. **Rate Limiting**:
   - Implement per-tenant rate limits
   - Prevent one tenant from affecting others
   - Consider using Redis for distributed rate limiting

4. **Token Validation**:
   - Always validate tenant_id in JWT matches request tenant
   - Prevent token reuse across tenants

5. **Configuration Validation**:
   - Validate tenant-specific configs (email, OAuth) before use
   - Prevent tenant A from using tenant B's credentials

### Migration Path from Single to Multi-Tenant

1. **Create Default Tenant**:
```python
# Create a default tenant for existing users
default_tenant = Tenant(
    tenant_key="default",
    tenant_name="Default Tenant",
    domain="localhost",
    api_key=generate_api_key(),
    is_active=True
)
```

2. **Associate Existing Users**:
```sql
-- Update existing users to belong to default tenant
UPDATE users SET tenant_id = (SELECT id FROM tenants WHERE tenant_key = 'default');
```

3. **Gradual Rollout**:
   - Keep single-tenant endpoints active
   - Add new multi-tenant endpoints with `/v2/` prefix
   - Migrate clients gradually
   - Deprecate old endpoints after migration

### Client Integration Example

```javascript
// Configure tenant identification
const TENANT_KEY = 'company-a';
const TENANT_API_KEY = 'tenant_xyz123...';

// Register user with tenant context
const registerResponse = await fetch('http://localhost:8006/auth/register', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Key': TENANT_KEY,        // Identify tenant
    'X-API-Key': TENANT_API_KEY        // Authenticate tenant
  },
  body: JSON.stringify({
    email: 'user@company-a.com',
    password: 'SecurePass123!',
    full_name: 'John Doe'
  })
});

// Login with tenant context
const loginResponse = await fetch('http://localhost:8006/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Tenant-Key': TENANT_KEY,
    'X-API-Key': TENANT_API_KEY
  },
  body: JSON.stringify({
    email: 'user@company-a.com',
    password: 'SecurePass123!'
  })
});
```

### Performance Optimization for Multi-Tenant

1. **Database Indexing**:
   - Add indexes on tenant_id for all tables
   - Use composite indexes: (tenant_id, email), (tenant_id, created_at)

2. **Caching**:
   - Cache tenant configurations (Redis)
   - Cache frequently accessed tenant data
   - Invalidate cache on tenant updates

3. **Connection Pooling**:
   - Configure adequate connection pool size
   - Consider per-tenant connection pools for large tenants

4. **Query Optimization**:
   - Always include tenant_id in WHERE clauses
   - Use EXPLAIN ANALYZE to optimize slow queries
   - Consider partitioning by tenant_id for very large datasets

### Monitoring Multi-Tenant Systems

1. **Per-Tenant Metrics**:
   - Track requests per tenant
   - Monitor authentication success/failure rates
   - Track token refresh rates
   - Measure response times per tenant

2. **Alerting**:
   - Alert on unusual tenant activity
   - Monitor rate limit violations per tenant
   - Track failed authentication attempts

3. **Audit Logging**:
   - Log all tenant configuration changes
   - Track admin operations
   - Record tenant creation/deletion

This multi-tenant architecture allows your auth service to scale horizontally and serve multiple independent applications from a single codebase, reducing operational overhead while maintaining strong data isolation and security.

## License

This microservice is part of the AI EdTech platform.

---

**Service Information**:
- Service Name: Authentication Service
- Default Port: 8006
- Protocol: HTTP/REST
- Authentication: JWT Bearer Token
- API Version: 1.0.0
