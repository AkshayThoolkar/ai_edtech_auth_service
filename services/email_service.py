from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from datetime import datetime
from typing import Optional
from core.config import settings


class EmailService:
    """Service for sending emails including OTP emails."""
    
    def __init__(self):
        """Initialize email service with configuration."""
        self._config = None
    
    def _get_mail_config(self) -> ConnectionConfig:
        """Get email configuration - lazy loading."""
        if self._config is None:
            self._config = ConnectionConfig(
                MAIL_USERNAME=settings.EMAIL_USERNAME,
                MAIL_PASSWORD=settings.EMAIL_PASSWORD,
                MAIL_FROM=settings.EMAIL_FROM,
                MAIL_PORT=settings.EMAIL_PORT,
                MAIL_SERVER=settings.EMAIL_HOST,
                MAIL_STARTTLS=settings.EMAIL_STARTTLS,
                MAIL_SSL_TLS=settings.EMAIL_SSL_TLS,
                USE_CREDENTIALS=True,
                VALIDATE_CERTS=True,
            )
        return self._config
    
    async def send_otp_email(
        self,
        email: str,
        otp_code: str,
        user_name: Optional[str] = None,
        purpose: str = "verification"
    ):
        """
        Send OTP email to user.
        
        Args:
            email: Recipient email address
            otp_code: The OTP code to send
            user_name: User's name for personalization
            purpose: Purpose of the OTP (verification, login, password_reset)
        """
        # Check if email settings are configured
        if not all([settings.EMAIL_HOST, settings.EMAIL_USERNAME, settings.EMAIL_PASSWORD]):
            print(f"Email not configured. Would send OTP {otp_code} to {email}")
            return
        
        # Customize subject and content based on purpose
        if purpose == "verification":
            subject = "Verify Your Email - AI EdTech Platform"
            action_text = "verify your email address"
        elif purpose == "login":
            subject = "Your Login Code - AI EdTech Platform"
            action_text = "log into your account"
        elif purpose == "password_reset":
            subject = "Password Reset Code - AI EdTech Platform"
            action_text = "reset your password"
        else:
            subject = "Your OTP Code - AI EdTech Platform"
            action_text = "complete your request"
        
        greeting = f"Hello {user_name}," if user_name else "Hello,"
        
        body = f"""
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">AI EdTech Platform</h2>
            <p>{greeting}</p>
            <p>Your One-Time Password (OTP) to {action_text} is:</p>
            <div style="background-color: #f4f4f4; padding: 20px; text-align: center; margin: 20px 0;">
                <h1 style="color: #007bff; font-size: 32px; margin: 0; letter-spacing: 5px;">{otp_code}</h1>
            </div>
            <p>This OTP will expire in {settings.OTP_EXPIRY_MINUTES} minutes.</p>
            <p>If you did not request this OTP, please ignore this email.</p>
            <hr style="margin: 30px 0;">
            <p style="color: #666; font-size: 12px;">
                Thanks,<br>
                The AI EdTech Platform Team
            </p>
        </div>
        """
        
        message = MessageSchema(
            subject=subject,
            recipients=[email],
            body=body,
            subtype="html"
        )
        
        try:
            fm = FastMail(self._get_mail_config())
            await fm.send_message(message)
            print(f"OTP email sent to {email}")
        except Exception as e:
            print(f"Error sending OTP email to {email}: {e}")
            raise Exception(f"Failed to send email: {str(e)}")


# Legacy function for backward compatibility
async def send_otp_email(to_email: str, otp_code: str, otp_expires_at: datetime):
    """Legacy function - use EmailService class instead."""
    service = EmailService()
    await service.send_otp_email(to_email, otp_code)
