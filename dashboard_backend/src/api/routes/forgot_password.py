from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
import os
import smtplib
from email.message import EmailMessage
from jose import jwt
from src.api.deps import get_db

RESET_TOKEN_SECRET = os.getenv("RESET_TOKEN_SECRET", "CHANGEME_RESET_TOKEN_SECRET")
RESET_TOKEN_ALGORITHM = "HS256"
RESET_TOKEN_EXPIRY_MINUTES = int(os.getenv("RESET_TOKEN_EXPIRY_MINUTES", "30"))

# SMTP configuration via environment
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
SMTP_PORT = int(os.getenv("SMTP_PORT", "25"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASS = os.getenv("SMTP_PASS")
SMTP_FROM = os.getenv("SMTP_FROM", "no-reply@dashboard.local")

router = APIRouter()

class ForgotPasswordRequest(BaseModel):
    email: EmailStr = Field(..., description="Registered @tataelxsi.co.in email")

class ForgotPasswordResponse(BaseModel):
    sent: bool = Field(..., description="Whether an email was sent if the user exists.")
    message: str

def _is_valid_tataelxsi_email(email: str) -> bool:
    """Return True iff the email ends with '@tataelxsi.co.in'."""
    return email.lower().endswith("@tataelxsi.co.in")

def create_reset_token(email: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=RESET_TOKEN_EXPIRY_MINUTES)
    payload = {"sub": email, "exp": expire}
    return jwt.encode(payload, RESET_TOKEN_SECRET, algorithm=RESET_TOKEN_ALGORITHM)

def send_reset_email(to_email: str, reset_url: str) -> None:
    subject = "Dashboard Password Reset Request"
    body = f"""
    A password reset was requested for your dashboard account.

    Please use the following link to reset your password. This link is valid for {RESET_TOKEN_EXPIRY_MINUTES} minutes:

    {reset_url}

    If you did not request this, please ignore this email.

    -- SLT Dashboard Team
    """
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = SMTP_FROM
    msg["To"] = to_email
    msg.set_content(body)
    try:
        if SMTP_USER and SMTP_PASS:
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.starttls()
                server.login(SMTP_USER, SMTP_PASS)
                server.send_message(msg)
        else:
            # fallback to non-auth SMTP (local dev/test)
            with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
                server.send_message(msg)
    except Exception as e:
        raise RuntimeError(f"Failed to send reset email: {e}")

# PUBLIC_INTERFACE
@router.post(
    "/forgot-password",
    summary="Request password reset for valid @tataelxsi.co.in accounts",
    tags=["Authentication"],
    response_model=ForgotPasswordResponse
)
async def forgot_password(
    request: Request,
    data: ForgotPasswordRequest = Body(...), 
    db=Depends(get_db)
):
    """
    Initiates password reset:
      - Accepts a valid @tataelxsi.co.in email.
      - If user exists, generates a secure token and emails reset link.
      - If user does NOT exist, behaves identically (never discloses user registration status).
    Returns: { "sent": true, "message": "If the email exists, a reset link will be sent." }
    """
    email = data.email.strip().lower()
    if not _is_valid_tataelxsi_email(email):
        raise HTTPException(status_code=400, detail="Only @tataelxsi.co.in emails are allowed.")

    user = await db["users"].find_one({"email": email})
    # Always behave the same regardless of user existence
    host = os.getenv("SITE_URL") or request.base_url._url.rstrip("/")
    # You should define SITE_URL env to the deployed base URL, for e.g. "https://dashboard.tataelxsi.co.in"
    if user:
        token = create_reset_token(email)
        reset_url = f"{host}/reset-password?token={token}"
        try:
            send_reset_email(email, reset_url)
        except Exception:
            # Still don't leak info, pretend success for the client
            # Optionally, log error internally
            pass
    # Don't allow username enumeration
    return ForgotPasswordResponse(
        sent=True,
        message="If the email is registered, a reset link has been sent."
    )
