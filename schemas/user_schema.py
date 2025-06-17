from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from typing import Optional
from datetime import datetime
import re


class UserBase(BaseModel):
    email: EmailStr
    full_name: Optional[str] = None
    
    @field_validator('full_name')
    @classmethod
    def validate_full_name(cls, v):
        if v is not None:
            v = v.strip()
            if len(v) > 100:
                raise ValueError('Full name must be no more than 100 characters')
            if len(v) < 1:
                raise ValueError('Full name cannot be empty if provided')
            # Remove control characters
            v = ''.join(char for char in v if ord(char) >= 32 or char in '\t\n\r')
        return v


class UserCreate(UserBase):
    password: Optional[str] = None
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        # Password is optional for OTP-only registration
        if v is None:
            return v
            
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
            
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
            
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
            
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
            
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
            
        if not re.search(r'[@$!%*?&]', v):
            raise ValueError('Password must contain at least one special character (@$!%*?&)')
            
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    is_active: bool
    is_verified: bool
    created_at: datetime


# Alias for backward compatibility and clearer API responses
UserResponse = UserRead
