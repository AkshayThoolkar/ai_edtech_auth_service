from sqlalchemy import Column, Integer, String, DateTime, Index, ForeignKey
from sqlalchemy.sql import func
from database.session import Base


class OTP(Base):
    __tablename__ = "otps"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    email = Column(String, nullable=False, index=True)  # Keep email for backward compatibility
    otp_code = Column(String, nullable=False)  # Store hashed OTP for security
    purpose = Column(String, nullable=False, default="verification")  # verification, login, password_reset
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Additional indexes for performance
    __table_args__ = (
        Index('idx_otp_user_id', 'user_id'),
        Index('idx_otp_email', 'email'),
        Index('idx_otp_user_purpose', 'user_id', 'purpose'),
        Index('idx_otp_expires_at', 'expires_at'),
    )
