"""
Security middleware for the auth service.
Adds security headers and implements basic security measures.
"""

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
import logging
from core.config import settings

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("auth_service.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; frame-ancestors 'none';"
        
        # Remove server header for security
        if "server" in response.headers:
            del response.headers["server"]
            
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log requests for security monitoring."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.time()
        
        # Extract request details
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        method = request.method
        url = str(request.url)
        
        # Log request details with proper logging levels
        if method in ["POST", "PUT", "DELETE"]:
            logger.info(f"Request: {method} {url} from {client_ip} - UA: {user_agent[:100]}")
        else:
            logger.debug(f"Request: {method} {url} from {client_ip}")
        
        response = await call_next(request)
        
        process_time = time.time() - start_time
        
        # Log response details with appropriate levels
        status_code = response.status_code
        if status_code >= 400:
            logger.warning(f"Response: {status_code} for {method} {url} - Time: {process_time:.3f}s - IP: {client_ip}")
        elif status_code >= 300:
            logger.info(f"Response: {status_code} for {method} {url} - Time: {process_time:.3f}s")
        else:
            logger.debug(f"Response: {status_code} - Time: {process_time:.3f}s")
        
        # Log slow requests
        if process_time > 2.0:  # Requests taking more than 2 seconds
            logger.warning(f"Slow request detected: {method} {url} took {process_time:.3f}s")
        
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limiting middleware - applies to ALL endpoints."""
    
    def __init__(self, app, calls_per_minute: int = 100):
        super().__init__(app)
        self.calls_per_minute = calls_per_minute
        self.requests = {}  # {ip: [timestamp1, timestamp2, ...]}
        logger.info(f"RateLimitMiddleware initialized with {calls_per_minute} calls per minute")
    
    def _cleanup_old_requests(self, ip: str):
        """Remove requests older than 1 minute."""
        current_time = time.time()
        cutoff_time = current_time - 60  # 1 minute ago
        
        if ip in self.requests:
            old_count = len(self.requests[ip])
            self.requests[ip] = [
                timestamp for timestamp in self.requests[ip]
                if timestamp > cutoff_time
            ]
            new_count = len(self.requests[ip])
            if old_count != new_count:
                logger.debug(f"Cleaned up {old_count - new_count} old requests for IP {ip}")
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        client_ip = request.client.host if request.client else "127.0.0.1"
        current_time = time.time()
        
        # Clean up old requests first
        self._cleanup_old_requests(client_ip)
        
        # Count current requests in the last minute
        current_requests = len(self.requests.get(client_ip, []))
        
        logger.debug(f"IP {client_ip}: {current_requests}/{self.calls_per_minute} requests in last minute")
        
        # Check if rate limit exceeded
        if current_requests >= self.calls_per_minute:
            logger.warning(f"Rate limit exceeded for IP {client_ip}: {current_requests} requests in last minute (limit: {self.calls_per_minute})")
            # Return 429 response directly instead of raising exception
            from fastapi.responses import JSONResponse
            return JSONResponse(
                status_code=429,
                content={
                    "detail": f"Rate limit exceeded. Maximum {self.calls_per_minute} requests per minute allowed.",
                    "error": "Too Many Requests"
                }
            )
        
        # Record this request
        if client_ip not in self.requests:
            self.requests[client_ip] = []
        
        self.requests[client_ip].append(current_time)
        
        logger.debug(f"Request recorded for IP {client_ip}. Total: {len(self.requests[client_ip])}")
        
        return await call_next(request)
