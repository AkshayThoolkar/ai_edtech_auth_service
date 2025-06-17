"""
Security utilities and helpers for input validation and security hardening.
"""

import re
import secrets
import string
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from fastapi import HTTPException, status


class SecurityUtils:
    """Security utility functions."""
    
    # Regex patterns for validation
    EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    OTP_PATTERN = re.compile(r'^\d{6}$')
    PASSWORD_PATTERN = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]')
    
    @staticmethod
    def validate_otp_code(otp_code: str) -> bool:
        """
        Validate OTP code format.
        
        Args:
            otp_code: OTP code to validate
            
        Returns:
            bool: True if valid format
        """
        if not otp_code:
            return False
            
        # Remove any whitespace
        otp_code = otp_code.strip()
        
        # Must be exactly 6 digits
        return bool(SecurityUtils.OTP_PATTERN.match(otp_code))
    
    @staticmethod
    def sanitize_email(email: str) -> str:
        """
        Sanitize and normalize email address.
        
        Args:
            email: Email to sanitize
            
        Returns:
            str: Sanitized email
        """
        if not email:
            return ""
            
        # Convert to lowercase and strip whitespace
        email = email.lower().strip()
        
        # Basic validation
        if not SecurityUtils.EMAIL_PATTERN.match(email):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid email format"
            )
            
        return email
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, str]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
            
        Returns:
            tuple: (is_valid, error_message)
        """
        if not password:
            return False, "Password is required"
            
        if len(password) < 8:
            return False, "Password must be at least 8 characters long"
            
        if len(password) > 128:
            return False, "Password must be no more than 128 characters long"
            
        if not re.search(r'[a-z]', password):
            return False, "Password must contain at least one lowercase letter"
            
        if not re.search(r'[A-Z]', password):
            return False, "Password must contain at least one uppercase letter"
            
        if not re.search(r'\d', password):
            return False, "Password must contain at least one digit"
            
        if not re.search(r'[@$!%*?&]', password):
            return False, "Password must contain at least one special character (@$!%*?&)"
            
        return True, ""
    
    @staticmethod
    def generate_secure_state() -> str:
        """
        Generate a secure state parameter for OAuth.
        
        Returns:
            str: Secure random state string
        """
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def sanitize_user_input(input_str: str, max_length: int = 255) -> str:
        """
        Sanitize user input to prevent various injection attacks.
        
        Args:
            input_str: Input string to sanitize
            max_length: Maximum allowed length
            
        Returns:
            str: Sanitized string
        """
        if not input_str:
            return ""
            
        # Strip whitespace
        sanitized = input_str.strip()
        
        # Check length
        if len(sanitized) > max_length:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Input too long (max {max_length} characters)"
            )
        
        # Remove null bytes and control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32 or char in '\t\n\r')
        
        return sanitized
    
    @staticmethod
    def create_safe_error_response(user_message: str, internal_error: str = None) -> HTTPException:
        """
        Create a safe error response that doesn't leak sensitive information.
        
        Args:
            user_message: Safe message for the user
            internal_error: Internal error details (logged but not returned)
            
        Returns:
            HTTPException: Safe HTTP exception
        """
        # TODO: Add logging for internal_error
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=user_message
        )
    
    @staticmethod
    def is_suspicious_request(email: str, user_agent: str = None) -> bool:
        """
        Basic suspicious request detection.
        
        Args:
            email: Email address
            user_agent: User agent string
            
        Returns:
            bool: True if request seems suspicious
        """
        # Check for obviously fake emails
        suspicious_domains = ['tempmail.org', '10minutemail.com', 'guerrillamail.com']
        email_domain = email.split('@')[-1].lower() if '@' in email else ''
        
        if email_domain in suspicious_domains:
            return True
            
        # Check for bot-like user agents
        if user_agent:
            bot_indicators = ['bot', 'crawler', 'spider', 'scraper']
            user_agent_lower = user_agent.lower()
            if any(indicator in user_agent_lower for indicator in bot_indicators):
                return True
                
        return False


class OAuthStateManager:
    """Secure OAuth state management with expiry."""
    
    def __init__(self):
        # Structure: {state: (timestamp, used)}
        self._states: Dict[str, tuple[float, bool]] = {}
        self._last_cleanup = datetime.now()
    
    def _cleanup_expired_states(self):
        """Remove expired states to prevent memory bloat."""
        current_time = datetime.now()
        
        # Cleanup every 10 minutes
        if current_time - self._last_cleanup < timedelta(minutes=10):
            return
        
        cutoff_time = current_time.timestamp() - 1800  # 30 minutes expiry
        
        expired_states = [
            state for state, (timestamp, used) in self._states.items()
            if timestamp < cutoff_time or used
        ]
        
        for state in expired_states:
            del self._states[state]
        
        self._last_cleanup = current_time
    
    def create_state(self) -> str:
        """
        Create a new OAuth state with expiry.
        
        Returns:
            str: New state parameter
        """
        self._cleanup_expired_states()
        
        state = SecurityUtils.generate_secure_state()
        self._states[state] = (datetime.now().timestamp(), False)
        
        return state
    
    def validate_and_consume_state(self, state: str) -> bool:
        """
        Validate and consume an OAuth state (one-time use).
        
        Args:
            state: State parameter to validate
            
        Returns:
            bool: True if state is valid and unused
        """
        self._cleanup_expired_states()
        
        if not state or state not in self._states:
            return False
        
        timestamp, used = self._states[state]
        
        # Check if already used
        if used:
            return False
        
        # Check if expired (30 minutes)
        if datetime.now().timestamp() - timestamp > 1800:
            del self._states[state]
            return False
        
        # Mark as used
        self._states[state] = (timestamp, True)
        return True


# Global instances
security_utils = SecurityUtils()
oauth_state_manager = OAuthStateManager()
