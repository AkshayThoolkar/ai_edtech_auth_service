"""
Routers package for Auth Service API endpoints.
"""

from .auth_router import router as auth_router
from .dependencies import get_current_user, get_current_active_user, get_current_verified_user

__all__ = [
    "auth_router",
    "get_current_user",
    "get_current_active_user", 
    "get_current_verified_user"
]