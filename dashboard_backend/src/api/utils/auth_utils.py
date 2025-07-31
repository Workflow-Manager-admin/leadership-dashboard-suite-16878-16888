import os, jwt, datetime
from typing import Optional
from passlib.context import CryptContext
from dotenv import load_dotenv

# Load environment variables (for SECRET_KEY)
load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "supersecretkey")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# PUBLIC_INTERFACE
def hash_password(password: str) -> str:
    """Hash a user password for storing."""
    return pwd_context.hash(password)

# PUBLIC_INTERFACE
def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify provided password against hash."""
    return pwd_context.verify(plain_password, hashed_password)

# PUBLIC_INTERFACE
def create_jwt_token(data: dict, expires_delta: Optional[int] = None):
    """Return encoded JWT token."""
    to_encode = data.copy()
    if expires_delta is None:
        expires_delta = ACCESS_TOKEN_EXPIRE_MINUTES
    expire = datetime.datetime.utcnow() + datetime.timedelta(minutes=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

# PUBLIC_INTERFACE
def decode_jwt_token(token: str):
    """Decode a JWT, validating signature & expiration; raise if invalid/expired."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise Exception("Token has expired")
    except jwt.InvalidTokenError:
        raise Exception("Invalid token")
