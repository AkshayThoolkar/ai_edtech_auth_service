"""
Model for storing invalidated refresh tokens (denylist).
"""

from sqlalchemy import Column, Integer, String, DateTime, Index
from datetime import datetime
from database.session import Base


class InvalidatedToken(Base):
    __tablename__ = "invalidated_tokens"

    id = Column(Integer, primary_key=True, index=True)
    jti = Column(String(64), unique=True, nullable=False, index=True)  # JWT ID
    user_id = Column(Integer, nullable=False, index=True)  # For easier cleanup/querying
    expires_at = Column(DateTime, nullable=False)  # When the original token expires
    invalidated_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Add compound index for efficient queries
    __table_args__ = (
        Index('idx_jti_expires', 'jti', 'expires_at'),
    )
