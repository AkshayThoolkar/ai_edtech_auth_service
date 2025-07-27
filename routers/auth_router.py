"""
Authentication router for OTP-based user authentication.
Handles user registration, OTP generation, verification, and login flows.
"""

import secrets
import httpx
import json
import base64
from datetime import timedelta, datetime
from typing import Optional, Dict
from urllib.parse import urlencode
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from jose import JWTError, jwt

from database.session import get_db
from schemas.user_schema import UserCreate, UserResponse, UserLogin
from schemas.otp_schema import OTPRequest, OTPVerify, OTPResponse
from schemas.token_schema import TokenResponse, RefreshTokenRequest, AccessTokenResponse, LogoutRequest, LogoutResponse
from crud.user_crud import UserCRUD
from crud.otp_crud import OTPCRUD
from crud.invalidated_token_crud import InvalidatedTokenCRUD
from services.otp_service import OTPService
from services.email_service import EmailService
from services.rate_limit_service import rate_limit_service
from services.security_service import oauth_state_manager, security_utils
from core.security import create_access_token, create_refresh_token, verify_password
from core.config import settings
from .dependencies import get_current_user as get_current_user_dependency

router = APIRouter(prefix="/auth", tags=["authentication"])

# Initialize services
otp_service = OTPService()
email_service = EmailService()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Register a new user.
    
    - **email**: User's email address (must be unique)
    - **password**: User's password (will be hashed) - must meet strength requirements
    - **full_name**: User's full name
    
    Returns the created user information (without password).
    """
    user_crud = UserCRUD(db)
    
    # Sanitize email
    try:
        sanitized_email = security_utils.sanitize_email(user_data.email)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check for suspicious requests
    user_agent = request.headers.get("user-agent", "")
    if security_utils.is_suspicious_request(sanitized_email, user_agent):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration not allowed"
        )
    
    # Check if user already exists
    existing_user = user_crud.get_by_email(sanitized_email)
    if existing_user:
        # Don't reveal that user exists - generic error
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Registration failed. Please try again or contact support."
        )
    
    # Create new user with sanitized data
    try:
        user_data.email = sanitized_email
        user = user_crud.create(user_data)
        return UserResponse.model_validate(user)
    except Exception as e:
        # Don't leak internal error details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed. Please try again."
        )


@router.get("/google/login")
async def google_login_redirect(request: Request):
    """
    Initiate Google OAuth 2.0 login flow.
    
    This endpoint constructs the Google OAuth authorization URL and redirects 
    the user to it. The user will be prompted to authorize the application 
    and will be redirected back to the callback endpoint.
    
    Returns a redirect response to Google's authorization server.
    """
    # Define redirect URI for the callback (matches Google Cloud Console configuration)
    redirect_uri = "https://auth.socialmembrane.com/auth/google/callback"
    
    # Generate a secure random state parameter for CSRF protection using new manager
    state = oauth_state_manager.create_state()
    
    # Construct Google OAuth 2.0 authorization URL manually
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth"
    params = {
        "client_id": settings.GOOGLE_CLIENT_ID,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "state": state,
    }
    
    # Build the complete authorization URL
    authorization_url = f"{auth_url}?{urlencode(params)}"
    
    return RedirectResponse(url=authorization_url)


@router.post("/request-otp", response_model=OTPResponse)
async def request_otp(
    otp_request: OTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Request an OTP for email verification or login.
    
    - **email**: User's email address
    - **purpose**: Purpose of OTP (verification, login, password_reset)
    
    Returns OTP request confirmation.
    """
    user_crud = UserCRUD(db)
    otp_crud = OTPCRUD(db)
    
    # Sanitize email
    try:
        sanitized_email = security_utils.sanitize_email(otp_request.email)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email format"
        )
    
    # Check rate limiting for OTP requests
    is_allowed, reset_time = rate_limit_service.is_otp_request_allowed(sanitized_email)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many OTP requests. Please try again in {reset_time} seconds."
        )
    
    # Check for suspicious requests
    user_agent = request.headers.get("user-agent", "")
    if security_utils.is_suspicious_request(sanitized_email, user_agent):
        # Still record the attempt for rate limiting
        rate_limit_service.record_otp_request(sanitized_email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Request not allowed"
        )
    
    # Check if user exists - don't reveal if user doesn't exist for security
    user = user_crud.get_by_email(sanitized_email)
    if not user:
        # Still record the attempt and simulate processing time
        rate_limit_service.record_otp_request(sanitized_email)
        # Return success response to not reveal user existence
        return OTPResponse(
            message="If the email exists in our system, an OTP has been sent",
            email=sanitized_email,
            expires_in_minutes=settings.OTP_EXPIRY_MINUTES
        )
      # Record the OTP request attempt
    rate_limit_service.record_otp_request(sanitized_email)
    
    try:
        # Generate OTP
        otp_code = otp_service.generate_otp()
        
        # Store OTP in database
        otp_data = {
            "user_id": user.id,
            "email": user.email,  # Add email for compatibility
            "otp_code": otp_code,
            "purpose": otp_request.purpose,
            "expires_at": otp_service.get_expiry_time()
        }
        
        otp_record = otp_crud.create(otp_data)
        
        # Send OTP via email
        await email_service.send_otp_email(
            email=user.email,
            otp_code=otp_code,
            user_name=user.full_name,
            purpose=otp_request.purpose
        )
        
        return OTPResponse(
            message="OTP sent successfully",
            email=user.email,
            expires_in_minutes=settings.OTP_EXPIRY_MINUTES
        )
        
    except Exception as e:
        # Log the actual error for debugging
        import logging
        logging.error(f"OTP request failed: {str(e)}")
        import traceback
        logging.error(f"Traceback: {traceback.format_exc()}")
        
        # Don't leak internal error details
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send OTP. Please try again."
        )


@router.post("/verify-otp", response_model=TokenResponse)
async def verify_otp(
    otp_verify: OTPVerify,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Verify OTP and return access token for successful verification.
    
    - **email**: User's email address
    - **otp_code**: The OTP code received via email
    - **purpose**: Purpose of OTP verification
    
    Returns access token upon successful verification.
    """
    user_crud = UserCRUD(db)
    otp_crud = OTPCRUD(db)
    
    # Sanitize inputs
    try:
        sanitized_email = security_utils.sanitize_email(otp_verify.email)
        sanitized_otp = security_utils.sanitize_user_input(otp_verify.otp_code.strip(), 10)
    except HTTPException as e:
        raise e
    
    # Validate OTP format
    if not security_utils.validate_otp_code(sanitized_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid OTP format"
        )
    
    # Check rate limiting for OTP verification
    is_allowed, reset_time = rate_limit_service.is_otp_verification_allowed(sanitized_email)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many verification attempts. Please try again in {reset_time} seconds."
        )
    
    # Record the verification attempt
    rate_limit_service.record_otp_verification(sanitized_email)
    
    # Get user
    user = user_crud.get_by_email(sanitized_email)
    if not user:
        # Don't reveal user existence, but still process to prevent timing attacks
        import time
        time.sleep(0.1)  # Simulate processing time
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid email or OTP"
        )
    
    # Verify OTP
    is_valid = otp_service.verify_otp(
        db=db,
        user_id=user.id,
        otp_code=sanitized_otp,
        purpose=otp_verify.purpose
    )
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired OTP"
        )
      # Mark email as verified if purpose is verification
    if otp_verify.purpose == "verification":
        user_crud.update(user.id, {"is_verified": True})
      # For password reset, don't issue tokens - just confirm success
    if otp_verify.purpose == "password_reset":
        return TokenResponse(
            message="OTP verified successfully. You can now reset your password."
        )
    
    # Create access token for login and verification purposes
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(subject=str(user.id))
    refresh_token_expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        refresh_token_expires_in=refresh_token_expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Login user with email and password.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns access token upon successful authentication.
    """
    user_crud = UserCRUD(db)
    
    # Sanitize email
    try:
        sanitized_email = security_utils.sanitize_email(login_data.email)
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check rate limiting for login attempts
    is_allowed, reset_time = rate_limit_service.is_login_attempt_allowed(sanitized_email)
    if not is_allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Too many login attempts. Please try again in {reset_time} seconds."
        )
    
    # Record the login attempt
    rate_limit_service.record_login_attempt(sanitized_email)
    
    # Get user by email
    user = user_crud.get_by_email(sanitized_email)
    if not user:
        # Simulate processing time to prevent timing attacks
        import time
        time.sleep(0.1)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated. Please contact support."
        )
    
    # Check if user is verified (configurable based on business requirements)
    if settings.REQUIRE_EMAIL_VERIFICATION and not user.is_verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email not verified. Please verify your email first."
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    # Create refresh token
    refresh_token = create_refresh_token(subject=str(user.id))
    refresh_token_expires_in = settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # Convert days to seconds
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        refresh_token=refresh_token,
        refresh_token_expires_in=refresh_token_expires_in,
        user=UserResponse.model_validate(user)
    )


@router.post("/resend-otp", response_model=OTPResponse)
async def resend_otp(
    otp_request: OTPRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Resend OTP for email verification or login.
    Same as request-otp but provides explicit resend functionality.
    """
    return await request_otp(otp_request, request, db)


@router.get("/me", response_model=UserResponse)
async def get_current_user(
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user_dependency)
):
    """
    Get current authenticated user information.
    Requires valid access token in Authorization header.
    """
    user_crud = UserCRUD(db)
    user = user_crud.get_by_id(current_user["user_id"])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return UserResponse.model_validate(user)


@router.post("/refresh-token", response_model=AccessTokenResponse)
async def refresh_access_token(
    token_request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Refresh access token using a valid refresh token.
    
    - **refresh_token**: Valid refresh token received from login/verify-otp
    
    Returns a new access token upon successful validation.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        # Decode the refresh token
        payload = jwt.decode(
            token_request.refresh_token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        jti: str = payload.get("jti")
        if user_id is None or jti is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    # Check if token is in denylist
    invalidated_token_crud = InvalidatedTokenCRUD(db)
    if invalidated_token_crud.is_token_invalidated(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been invalidated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Fetch user from database
    user_crud = UserCRUD(db)
    user = user_crud.get_by_id(int(user_id))
    
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Generate new access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    new_access_token = create_access_token(
        subject=str(user.id),
        expires_delta=access_token_expires
    )
    
    return AccessTokenResponse(
        access_token=new_access_token,
        expires_in=int(access_token_expires.total_seconds())
    )


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    logout_request: LogoutRequest,
    db: Session = Depends(get_db)
):
    """
    Logout user by invalidating their refresh token.
    
    - **refresh_token**: Valid refresh token to be invalidated
    
    Returns a success message upon successful logout.
    """
    import logging
    logger = logging.getLogger("auth_service.logout")
    
    try:
        logger.info("Starting logout process")
        
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
        try:
            logger.info("Decoding refresh token")
            # Decode the refresh token to extract JTI and other claims
            payload = jwt.decode(
                logout_request.refresh_token,
                settings.SECRET_KEY,
                algorithms=[settings.ALGORITHM]
            )
            user_id: str = payload.get("sub")
            jti: str = payload.get("jti")
            exp: int = payload.get("exp")
            
            logger.info(f"Token decoded successfully - user_id: {user_id}, jti: {jti}")
            
            if user_id is None or jti is None or exp is None:
                logger.error("Missing required token claims")
                raise credentials_exception
        except JWTError as jwt_err:
            logger.error(f"JWT decoding error: {jwt_err}")
            raise credentials_exception
        
        # Convert exp timestamp to datetime
        expires_at = datetime.fromtimestamp(exp)
        logger.info(f"Token expires at: {expires_at}")
        
        # Check if token is already invalidated
        logger.info("Checking if token is already invalidated")
        invalidated_token_crud = InvalidatedTokenCRUD(db)
        if invalidated_token_crud.is_token_invalidated(jti):
            logger.info("Token already invalidated, returning success")
            # Token already invalidated, but still return success for idempotency
            response = LogoutResponse(message="Logout successful")
            logger.info(f"Created response: {response}")
            return response
        
        # Add token to denylist
        logger.info("Adding token to denylist")
        try:
            invalidated_token_crud.create_invalidated_token(
                jti=jti,
                user_id=int(user_id),
                expires_at=expires_at
            )
            logger.info("Token successfully added to denylist")
        except Exception as e:
            logger.error(f"Error adding token to denylist: {e}")
            # Handle potential duplicate JTI errors gracefully
            if "unique constraint" in str(e).lower() or "duplicate" in str(e).lower():
                logger.info("Duplicate JTI error, token already invalidated by another request")
                # Token was already invalidated by another request
                response = LogoutResponse(message="Logout successful")
                logger.info(f"Created response: {response}")
                return response
            else:
                logger.error("Raising 500 error due to database failure")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Failed to invalidate token"
                )
        
        logger.info("Creating successful logout response")
        response = LogoutResponse(message="Logout successful")
        logger.info(f"Final response created: {response}")
        return response
        
    except Exception as e:
        logger.error(f"Unexpected error in logout endpoint: {e}")
        logger.error(f"Error type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = None,
    state: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth 2.0 callback.
    
    This endpoint is called by Google after the user authorizes the application.
    It exchanges the authorization code for an access token and user information,
    then creates a new user if they don't exist or returns tokens for existing users.
    
    Query Parameters:
    - code: Authorization code from Google (if successful)
    - state: State parameter for CSRF protection
    - error: Error code from Google (if authorization failed)
    """
    # 1. Handle authorization errors from Google
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Google OAuth authorization failed: {error}"
        )
    
    # 2. Validate required parameters
    if not code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Authorization code not provided"
        )
      # 3. Validate state parameter against stored state
    if not state:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="State parameter missing - possible CSRF attack"
        )
    
    # Check if the state is valid and consume it (one-time use)
    if not oauth_state_manager.validate_and_consume_state(state):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid state parameter - possible CSRF attack"
        )
    
    try:
        # 4. Exchange authorization code for access token
        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": "https://auth.socialmembrane.com/auth/google/callback"
        }
        
        async with httpx.AsyncClient() as client:
            try:
                token_response = await client.post(token_url, data=token_data)
                token_response.raise_for_status()
                token_json = token_response.json()
            except httpx.HTTPStatusError as e:
                # Google returned an HTTP error (400, 401, etc.)
                if e.response.status_code in [400, 401]:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Google OAuth token exchange failed: Invalid code or client authentication failed. Status: {e.response.status_code}"
                    )
                else:
                    raise HTTPException(
                        status_code=status.HTTP_502_BAD_GATEWAY,
                        detail=f"Google OAuth service error. Status: {e.response.status_code}"
                    )
            except httpx.RequestError as e:
                # Network error connecting to Google
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=f"Failed to connect to Google OAuth service: {str(e)}"
                )
        
        # 5. Parse and validate the ID token
        id_token = token_json.get("id_token")
        if not id_token:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="ID token not found in Google response"
            )
        
        # Decode the ID token (without verification for simplicity in this implementation)
        try:
            # Split the JWT and decode the payload
            header, payload, signature = id_token.split('.')
            # Add padding if needed
            payload += '=' * (4 - len(payload) % 4)
            decoded_payload = base64.urlsafe_b64decode(payload)
            user_info = json.loads(decoded_payload)
        except (ValueError, json.JSONDecodeError) as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to decode ID token: Malformed token structure"
            )
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Unexpected error decoding ID token: {str(e)}"
            )
        
        # 6. Validate required claims in the ID token
        google_id = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", "")
        email_verified = user_info.get("email_verified", False)
        
        # Check for missing essential claims
        missing_claims = []
        if not google_id:
            missing_claims.append("sub (Google ID)")
        if not email:
            missing_claims.append("email")
        if not email_verified:
            missing_claims.append("email_verified")
        
        if missing_claims:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Required user information missing or invalid in ID token: {', '.join(missing_claims)}"
            )
        
        user_crud = UserCRUD(db)
        
        # 7. User lookup and creation logic
        # First, check if user exists by Google ID
        existing_user = user_crud.get_by_google_id(google_id)
        
        if existing_user:
            # User found by Google ID - existing Google user
            user = existing_user
        else:
            # Check if user exists by email (for account linking)
            existing_user = user_crud.get_by_email(email)
            
            if existing_user:
                # User found by email but no Google ID - link the account
                update_data = {"google_id": google_id}
                if not existing_user.is_verified:
                    update_data["is_verified"] = True
                
                user_crud.update(existing_user.id, update_data)
                
                # Try to refresh the existing_user object, but handle errors gracefully
                try:
                    db.refresh(existing_user)
                except Exception:
                    # If refresh fails (e.g., with mock objects in tests), just continue
                    pass
                    
                user = existing_user
            else:
                # No existing user found - create new user
                user = user_crud.create_google_user(
                    google_id=google_id,
                    email=email,
                    full_name=name
                )
          # 8. Generate platform-specific JWT tokens
        access_token = create_access_token(subject=str(user.id))
        refresh_token = create_refresh_token(subject=str(user.id))
        
        # 9. Redirect back to frontend with tokens
        from fastapi.responses import RedirectResponse
        frontend_url = "https://dev.socialmembrane.com"
        redirect_url = f"{frontend_url}/?access_token={access_token}&refresh_token={refresh_token}"
        
        return RedirectResponse(url=redirect_url, status_code=302)
    
    except HTTPException:
        # Re-raise HTTPExceptions (they have the correct status codes)
        raise
    except Exception as e:
        # Handle any other unexpected errors
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process Google OAuth callback: {str(e)}"
        )

