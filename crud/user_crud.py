from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from models.user_model import User
from schemas.user_schema import UserCreate
from core.security import hash_password


class UserCRUD:
    """CRUD operations for User model."""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email."""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_by_google_id(self, google_id: str) -> Optional[User]:
        """Get user by Google ID."""
        return self.db.query(User).filter(User.google_id == google_id).first()
    
    def create(self, user_data: UserCreate) -> User:
        """Create a new user."""
        # Hash the password only if provided
        hashed_password = None
        if user_data.password:
            hashed_password = hash_password(user_data.password)
        
        db_user = User(
            email=user_data.email,
            full_name=user_data.full_name,
            hashed_password=hashed_password
            # is_verified defaults to False in the model
            # is_active defaults to True in the model
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def create_google_user(self, google_id: str, email: str, full_name: str) -> User:
        """Create a new user from Google OAuth."""
        db_user = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            is_verified=True,  # Google users are pre-verified
            is_active=True
            # No hashed_password for OAuth users
        )
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def update(self, user_id: int, update_data: Dict[str, Any]) -> Optional[User]:
        """Update user by ID."""
        user = self.get_by_id(user_id)
        if user:
            for key, value in update_data.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            self.db.commit()
            self.db.refresh(user)
        return user
    
    def delete(self, user_id: int) -> bool:
        """Delete user by ID."""
        user = self.get_by_id(user_id)
        if user:
            self.db.delete(user)
            self.db.commit()
            return True
        return False


# Standalone functions for backward compatibility
def get_user(db: Session, user_id: int) -> Optional[User]:
    return UserCRUD(db).get_by_id(user_id)


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return UserCRUD(db).get_by_email(email)


def create_user(db: Session, user: UserCreate) -> User:
    return UserCRUD(db).create(user)
