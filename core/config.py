from pydantic_settings import BaseSettings
from typing import Optional, List
import os
import json


class Settings(BaseSettings):
    # Security - NO DEFAULT VALUES FOR PRODUCTION SECRETS
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/auth_service_dev"
    SECRET_KEY: str = "your_super_secret_key_for_development_only"  # MUST be overridden in production
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 10080  # 7 days (7 × 24 × 60 minutes) - Industry standard for educational platforms
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
      # CORS Configuration - Environment-driven for security
    # Set BACKEND_CORS_ORIGINS as JSON string: '["https://yourdomain.com", "https://app.yourdomain.com"]'
    BACKEND_CORS_ORIGINS: str = '["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]'  # Development only
    
    # Logging Configuration
    LOG_LEVEL: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
      # OTP Security Configuration
    OTP_EXPIRY_MINUTES: int = 10
    OTP_MAX_ATTEMPTS: int = 3
    OTP_RATE_LIMIT_MINUTES: int = 1
    OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR: int = 5

    # Authentication Configuration
    REQUIRE_EMAIL_VERIFICATION: bool = True  # Set to False for development/testing to skip email verification

    # Google OAuth Credentials - REQUIRED for production
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Database connection details
    POSTGRES_HOST: Optional[str] = None
    POSTGRES_PORT: Optional[int] = None
    POSTGRES_DB: Optional[str] = None
    POSTGRES_USER: Optional[str] = None
    POSTGRES_PASSWORD: Optional[str] = None
      # Email settings - REQUIRED for production
    EMAIL_HOST: Optional[str] = None
    EMAIL_PORT: Optional[int] = None
    EMAIL_USERNAME: Optional[str] = None
    EMAIL_PASSWORD: Optional[str] = None
    EMAIL_FROM: Optional[str] = None
    EMAIL_STARTTLS: Optional[bool] = True
    EMAIL_SSL_TLS: Optional[bool] = False

    @property
    def cors_origins(self) -> List[str]:
        """Parse CORS origins from JSON string."""
        try:
            return json.loads(self.BACKEND_CORS_ORIGINS)
        except json.JSONDecodeError:
            # Fallback to development origins if JSON parsing fails
            return ["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]

    class Config:
        env_file = ".env"
        env_file_encoding = 'utf-8'


settings = Settings()
