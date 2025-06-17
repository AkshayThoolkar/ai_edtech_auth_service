"""
FastAPI dependencies for authentication and authorization.
"""

from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database.session import get_db
from crud.user_crud import UserCRUD
from core.config import settings

# Security scheme for bearer token
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> dict:
    """
    Dependency to get the current authenticated user from JWT token.
    
    Args:
        credentials: Bearer token from Authorization header
        db: Database session
        
    Returns:
        dict: User information from token payload
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode JWT token
        payload = jwt.decode(
            credentials.credentials, 
            settings.SECRET_KEY, 
            algorithms=[settings.ALGORITHM]
        )
          # Extract user information
        user_id: str = payload.get("sub")
        
        if user_id is None:
            raise credentials_exception
            
    except JWTError:
        raise credentials_exception
    
    # Verify user exists in database
    user_crud = UserCRUD(db)
    user = user_crud.get_by_id(int(user_id))
    
    if user is None:
        raise credentials_exception
    
    return {
        "user_id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "is_verified": user.is_verified,
        "is_active": user.is_active
    }


async def get_current_active_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to get current active user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        dict: Active user information
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user["is_active"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Inactive user"
        )
    return current_user


async def get_current_verified_user(
    current_user: dict = Depends(get_current_user)
) -> dict:
    """
    Dependency to get current verified user.
    
    Args:
        current_user: Current user from get_current_user dependency
        
    Returns:
        dict: Verified user information
        
    Raises:
        HTTPException: If user email is not verified
    """
    if not current_user["is_verified"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )
    return current_user


def require_roles(*required_roles: str):
    """
    Dependency factory to require specific user roles.
    
    Args:
        *required_roles: List of required roles
        
    Returns:
        Dependency function that checks user roles
    """
    async def role_checker(
        current_user: dict = Depends(get_current_active_user)
    ) -> dict:
        # Note: This assumes you have a role system in place
        # You would need to extend the User model and add role checking logic
        user_roles = current_user.get("roles", [])
        
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker
