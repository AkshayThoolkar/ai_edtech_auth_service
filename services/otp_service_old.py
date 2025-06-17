from sqlalchemy.orm import Session
from crud import otp_crud
from schemas.otp_schema import OTPCreate
from core.security import verify_password
from datetime import datetime, timedelta, timezone
import secrets

OTP_EXPIRE_MINUTES = 15


def generate_otp_for_user(db: Session, email: str) -> tuple[str, datetime]:
    """Generate OTP for a user and store it in the database"""
    plain_otp = "".join([secrets.choice("0123456789") for _ in range(6)])
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=OTP_EXPIRE_MINUTES)
    
    otp_data = OTPCreate(
        email=email,
        otp_code=plain_otp,  # Will be hashed by otp_crud.create_or_update_otp
        expires_at=expires_at
    )
    otp_crud.create_or_update_otp(db=db, otp_in=otp_data)
    return plain_otp, expires_at


def verify_otp(db: Session, email: str, provided_otp: str) -> bool:
    """Verify OTP for a user"""
    stored_otp_obj = otp_crud.get_otp_by_email(db=db, email=email)

    if not stored_otp_obj:
        return False

    if datetime.now(timezone.utc) > stored_otp_obj.expires_at:
        # OTP expired, delete it
        otp_crud.delete_otp(db=db, email=email)
        return False

    # Verify the provided plain OTP against the stored hashed OTP
    if not verify_password(provided_otp, stored_otp_obj.otp_code):
        return False

    # OTP is valid, delete it to prevent reuse
    otp_crud.delete_otp(db=db, email=email)
    return True
