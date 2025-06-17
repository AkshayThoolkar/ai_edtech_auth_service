"""
Rate limiting service for protecting against brute force and abuse attacks.
Implements in-memory rate limiting with Redis-like interface for future scaling.
"""

import time
from typing import Dict, Tuple
from datetime import datetime, timedelta
from core.config import settings


class RateLimitService:
    """In-memory rate limiting service with automatic cleanup."""
    
    def __init__(self):
        # Structure: {key: [(timestamp, attempt_count), ...]}
        self._attempts: Dict[str, list] = {}
        self._last_cleanup = time.time()
        
    def _cleanup_expired_entries(self):
        """Remove expired entries to prevent memory bloat."""
        current_time = time.time()
        
        # Only cleanup every 5 minutes to avoid performance impact
        if current_time - self._last_cleanup < 300:
            return
            
        cutoff_time = current_time - 3600  # Keep 1 hour of history
        
        for key in list(self._attempts.keys()):
            self._attempts[key] = [
                (timestamp, count) for timestamp, count in self._attempts[key]
                if timestamp > cutoff_time
            ]
            
            # Remove empty entries
            if not self._attempts[key]:
                del self._attempts[key]
                
        self._last_cleanup = current_time
    
    def check_rate_limit(self, identifier: str, max_attempts: int, window_seconds: int) -> Tuple[bool, int, int]:
        """
        Check if an action is rate limited.
        
        Args:
            identifier: Unique identifier (email, IP, etc.)
            max_attempts: Maximum attempts allowed
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, current_attempts, seconds_until_reset)
        """
        self._cleanup_expired_entries()
        
        current_time = time.time()
        window_start = current_time - window_seconds
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
        
        # Count attempts within the window
        valid_attempts = [
            (timestamp, count) for timestamp, count in self._attempts[identifier]
            if timestamp > window_start
        ]
        
        current_attempts = sum(count for _, count in valid_attempts)
        
        # Check if rate limit exceeded
        if current_attempts >= max_attempts:
            # Find the oldest attempt to calculate reset time
            if valid_attempts:
                oldest_attempt = min(timestamp for timestamp, _ in valid_attempts)
                seconds_until_reset = int(window_seconds - (current_time - oldest_attempt))
                return False, current_attempts, max(0, seconds_until_reset)
            
        return True, current_attempts, 0
    
    def record_attempt(self, identifier: str):
        """Record an attempt for rate limiting."""
        current_time = time.time()
        
        if identifier not in self._attempts:
            self._attempts[identifier] = []
            
        self._attempts[identifier].append((current_time, 1))
    
    def is_otp_request_allowed(self, email: str) -> Tuple[bool, int]:
        """
        Check if OTP request is allowed for an email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        # Rate limit: max 5 OTP requests per hour per email
        is_allowed, current_attempts, reset_time = self.check_rate_limit(
            f"otp_request:{email}",
            settings.OTP_MAX_REQUESTS_PER_EMAIL_PER_HOUR,
            3600  # 1 hour window
        )
        
        return is_allowed, reset_time
    
    def is_otp_verification_allowed(self, email: str) -> Tuple[bool, int]:
        """
        Check if OTP verification is allowed for an email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        # Rate limit: max 3 verification attempts per minute per email
        is_allowed, current_attempts, reset_time = self.check_rate_limit(
            f"otp_verify:{email}",
            settings.OTP_MAX_ATTEMPTS,
            settings.OTP_RATE_LIMIT_MINUTES * 60
        )
        
        return is_allowed, reset_time
    
    def record_otp_request(self, email: str):
        """Record an OTP request attempt."""
        self.record_attempt(f"otp_request:{email}")
    
    def record_otp_verification(self, email: str):
        """Record an OTP verification attempt."""
        self.record_attempt(f"otp_verify:{email}")
    
    def is_login_attempt_allowed(self, email: str) -> Tuple[bool, int]:
        """
        Check if login attempt is allowed for an email.
        
        Args:
            email: User's email address
            
        Returns:
            Tuple of (is_allowed, seconds_until_reset)
        """
        # Rate limit: max 5 login attempts per 15 minutes per email
        is_allowed, current_attempts, reset_time = self.check_rate_limit(
            f"login:{email}",
            5,
            900  # 15 minutes
        )
        
        return is_allowed, reset_time
    
    def record_login_attempt(self, email: str):
        """Record a login attempt."""
        self.record_attempt(f"login:{email}")


# Global instance
rate_limit_service = RateLimitService()
