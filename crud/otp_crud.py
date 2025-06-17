from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from models.otp_model import OTP
from schemas.otp_schema import OTPCreate
from core.security import hash_password


class OTPCRUD:
    """CRUD operations for OTP model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create(self, otp_data: Dict[str, Any]) -> OTP:
        """Create a new OTP record."""
        # Delete existing OTP for the user and purpose for security
        existing_otp = self.db.query(OTP).filter(
            OTP.user_id == otp_data["user_id"],
            OTP.purpose == otp_data["purpose"]
        ).first()
        if existing_otp:
            self.db.delete(existing_otp)
            self.db.commit()
        
        # Hash the OTP before storing
        hashed_otp_code = hash_password(otp_data["otp_code"])
        
        db_otp = OTP(
            user_id=otp_data["user_id"],
            email=otp_data.get("email", ""),  # Store email for backward compatibility
            otp_code=hashed_otp_code,
            purpose=otp_data["purpose"],
            expires_at=otp_data["expires_at"]
        )
        self.db.add(db_otp)
        self.db.commit()
        self.db.refresh(db_otp)
        return db_otp
    
    def get_by_user_and_purpose(self, user_id: int, purpose: str) -> Optional[OTP]:
        """Get OTP by user ID and purpose."""
        return self.db.query(OTP).filter(
            OTP.user_id == user_id,
            OTP.purpose == purpose
        ).first()
    
    def delete_by_user_and_purpose(self, user_id: int, purpose: str) -> bool:
        """Delete OTP by user ID and purpose."""
        otp = self.get_by_user_and_purpose(user_id, purpose)
        if otp:
            self.db.delete(otp)
            self.db.commit()
            return True
        return False
    
    def delete_expired_otps(self) -> int:
        """Delete all expired OTP records."""
        from datetime import datetime
        count = self.db.query(OTP).filter(OTP.expires_at < datetime.utcnow()).count()
        self.db.query(OTP).filter(OTP.expires_at < datetime.utcnow()).delete()
        self.db.commit()
        return count


# Standalone functions for backward compatibility
def create_or_update_otp(db: Session, otp_in: OTPCreate) -> OTP:
    # This function needs to be updated to match new structure
    # For now, creating a basic implementation
    otp_data = {
        "user_id": 1,  # This should be passed in properly
        "otp_code": otp_in.otp_code,
        "purpose": "verification",  # Default purpose
        "expires_at": otp_in.expires_at
    }
    return OTPCRUD(db).create(otp_data)


def get_otp_by_email(db: Session, email: str) -> Optional[OTP]:
    # This is a legacy function that needs user_id
    return None


def delete_otp(db: Session, email: str) -> bool:
    # This is a legacy function that needs user_id
    return False
