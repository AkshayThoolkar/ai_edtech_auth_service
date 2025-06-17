"""
CRUD operations for InvalidatedToken model.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from models.invalidated_token_model import InvalidatedToken


class InvalidatedTokenCRUD:
    """CRUD operations for InvalidatedToken model."""
    
    def __init__(self, db: Session):
        self.db = db

    def create_invalidated_token(
        self, 
        jti: str, 
        user_id: int, 
        expires_at: datetime
    ) -> InvalidatedToken:
        """Create a new invalidated token entry."""
        invalidated_token = InvalidatedToken(
            jti=jti,
            user_id=user_id,
            expires_at=expires_at
        )
        self.db.add(invalidated_token)
        self.db.commit()
        # Remove the refresh call that causes transaction issues in tests
        # self.db.refresh(invalidated_token)
        return invalidated_token

    def is_token_invalidated(self, jti: str) -> bool:
        """Check if a token JTI is in the denylist."""
        invalidated_token = self.db.query(InvalidatedToken).filter(
            InvalidatedToken.jti == jti,
            InvalidatedToken.expires_at > datetime.utcnow()  # Only check non-expired denylisted tokens
        ).first()
        return invalidated_token is not None

    def get_by_jti(self, jti: str) -> Optional[InvalidatedToken]:
        """Get an invalidated token by its JTI."""
        return self.db.query(InvalidatedToken).filter(
            InvalidatedToken.jti == jti
        ).first()

    def cleanup_expired_tokens(self) -> int:
        """Remove expired tokens from the denylist. Returns count of deleted tokens."""
        deleted_count = self.db.query(InvalidatedToken).filter(
            InvalidatedToken.expires_at <= datetime.utcnow()
        ).delete()
        self.db.commit()
        return deleted_count
