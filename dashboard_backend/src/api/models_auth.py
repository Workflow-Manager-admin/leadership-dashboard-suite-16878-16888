from pydantic import BaseModel, EmailStr, Field

# PUBLIC_INTERFACE
class UserCreate(BaseModel):
    """Payload for registering a new user."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password (minimum 6 characters)")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    """Payload for user login."""
    email: EmailStr = Field(..., description="User's email address")
    password: str = Field(..., description="User's password")

# PUBLIC_INTERFACE
class UserPublic(BaseModel):
    """Public-facing data for a user."""
    user_id: str = Field(..., description="User unique identifier")
    email: EmailStr = Field(..., description="Email address")
    is_active: bool = Field(..., description="Active status")

# PUBLIC_INTERFACE
class AuthToken(BaseModel):
    """JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type (always 'bearer')")
