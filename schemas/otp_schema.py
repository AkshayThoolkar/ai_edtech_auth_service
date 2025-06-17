from pydantic import BaseModel, EmailStr, ConfigDict, field_validator
from datetime import datetime
from enum import Enum
import re


class OTPPurpose(str, Enum):
    verification = "verification"
    login = "login" 
    password_reset = "password_reset"


class OTPRequest(BaseModel):
    email: EmailStr
    purpose: OTPPurpose = OTPPurpose.verification


class OTPVerify(BaseModel):
    email: EmailStr
    otp_code: str
    purpose: OTPPurpose = OTPPurpose.verification
    
    @field_validator('otp_code')
    @classmethod
    def validate_otp_code(cls, v):
        if not v:
            raise ValueError('OTP code is required')
        
        # Remove whitespace
        v = v.strip()
        
        # Must be exactly 6 digits
        if not re.match(r'^\d{6}$', v):
            raise ValueError('OTP code must be exactly 6 digits')
        
        return v


class OTPResponse(BaseModel):
    message: str
    email: EmailStr
    expires_in_minutes: int


class OTPBase(BaseModel):
    email: EmailStr


class OTPCreate(OTPBase):
    otp_code: str
    expires_at: datetime


class OTPRead(OTPBase):
    model_config = ConfigDict(from_attributes=True)
    
    expires_at: datetime
