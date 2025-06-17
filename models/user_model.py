from sqlalchemy import Column, Integer, String, Boolean, DateTime, Index
from sqlalchemy.sql import func
from database.session import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for OAuth users
    google_id = Column(String, unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    full_name = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Additional indexes for performance
    __table_args__ = (
        Index('idx_user_email', 'email'),
        Index('idx_user_google_id', 'google_id'),
        Index('idx_user_active_verified', 'is_active', 'is_verified'),
    )
