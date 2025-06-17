"""
OTP service for generation, storage, and verification of One-Time Passwords.
"""

from sqlalchemy.orm import Session
from crud.otp_crud import OTPCRUD
from core.security import verify_password
from core.config import settings
from datetime import datetime, timedelta, timezone
import secrets


class OTPService:
    """Service for OTP generation, storage, and verification."""
    
    def generate_otp(self) -> str:
        """Generate a secure 6-digit OTP."""
        return "".join([secrets.choice("0123456789") for _ in range(6)])
    
    def get_expiry_time(self) -> datetime:
        """Get OTP expiry time."""
        return datetime.now(timezone.utc) + timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
    
    def verify_otp(self, db: Session, user_id: int, otp_code: str, purpose: str) -> bool:
        """
        Verify OTP for a user.
        
        Args:
            db: Database session
            user_id: User ID
            otp_code: Plain OTP code to verify
            purpose: Purpose of the OTP
            
        Returns:
            bool: True if OTP is valid, False otherwise
        """
        otp_crud = OTPCRUD(db)
        
        # Get stored OTP
        stored_otp = otp_crud.get_by_user_and_purpose(user_id, purpose)
        if not stored_otp:
            return False
        
        # Check if OTP is expired
        if datetime.now(timezone.utc) > stored_otp.expires_at:
            # OTP expired, delete it
            otp_crud.delete_by_user_and_purpose(user_id, purpose)
            return False
        
        # Verify the provided plain OTP against the stored hashed OTP
        if not verify_password(otp_code, stored_otp.otp_code):
            return False
        
        # OTP is valid, delete it to prevent reuse
        otp_crud.delete_by_user_and_purpose(user_id, purpose)
        return True
    
    def cleanup_expired_otps(self, db: Session) -> int:
        """Clean up expired OTP records."""
        otp_crud = OTPCRUD(db)
        return otp_crud.delete_expired_otps()


# Legacy functions for backward compatibility
def generate_otp_for_user(db: Session, email: str) -> tuple[str, datetime]:
    """Legacy function - use OTPService class instead."""
    service = OTPService()
    otp_code = service.generate_otp()
    expires_at = service.get_expiry_time()
    return otp_code, expires_at


def verify_otp(db: Session, email: str, provided_otp: str) -> bool:
    """Legacy function - use OTPService class instead."""
    # This function is deprecated as it doesn't support user_id and purpose
    return False
