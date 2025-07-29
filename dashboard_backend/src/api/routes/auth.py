from fastapi import APIRouter, Depends, HTTPException, status, Body
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from passlib.context import CryptContext
from pydantic import BaseModel, EmailStr, Field
from datetime import datetime, timedelta
from jose import JWTError, jwt
from typing import Optional
import pymongo.errors
from bson import ObjectId

from src.api.deps import get_db

# ---- JWT config ----
SECRET_KEY = "REPLACE_ME_WITH_SECRET"   # Update to a secure random key, and load from environment in production.
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/auth/token")

router = APIRouter()


# --- Schemas ---

class UserCreate(BaseModel):
    email: EmailStr
    full_name: Optional[str]
    password: str = Field(..., min_length=6)

class UserRead(BaseModel):
    id: Optional[str]
    email: EmailStr
    full_name: Optional[str]
    is_active: bool = True

class Token(BaseModel):
    access_token: str
    token_type: str

# --- Auth utility functions ---

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_user_by_email_mongo(db, email: str):
    return await db["users"].find_one({"email": email})

async def authenticate_user_mongo(db, email: str, password: str):
    user = await get_user_by_email_mongo(db, email)
    if user and verify_password(password, user["hashed_password"]):
        return user
    return None

def _is_valid_tataelxsi_email(email: str) -> bool:
    """Return True iff the email ends with '@tataelxsi.co.in'."""
    return email.lower().endswith("@tataelxsi.co.in")

# PUBLIC_INTERFACE
@router.post("/register", summary="Register a new user", response_model=UserRead, tags=["Authentication"])
async def register_user(user: UserCreate = Body(...), db=Depends(get_db)):
    """
    Register a new user with email and password in MongoDB. Email must be unique.
    """
    if not _is_valid_tataelxsi_email(user.email):
        raise HTTPException(
            status_code=400,
            detail="Registration restricted: only '@tataelxsi.co.in' email addresses are allowed."
        )
    users = db["users"]
    existing = await users.find_one({"email": user.email})
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pw = get_password_hash(user.password)
    user_data = {
        "email": user.email,
        "full_name": user.full_name,
        "hashed_password": hashed_pw,
        "is_active": True,
        "is_superuser": False,
        "created_at": datetime.utcnow()
    }
    try:
        insert_result = await users.insert_one(user_data)
        new_user = await users.find_one({"_id": insert_result.inserted_id})
    except pymongo.errors.DuplicateKeyError:
        raise HTTPException(status_code=400, detail="Email already registered")
    return UserRead(
        id=str(new_user["_id"]),
        email=new_user["email"],
        full_name=new_user.get("full_name"),
        is_active=new_user.get("is_active", True),
    )

# PUBLIC_INTERFACE
@router.post("/token", summary="Login and get JWT token", response_model=Token, tags=["Authentication"])
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db=Depends(get_db)):
    """
    Authenticate user and return JWT token for use in subsequent requests.
    """
    if not _is_valid_tataelxsi_email(form_data.username):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Login restricted: only '@tataelxsi.co.in' email addresses are allowed.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await authenticate_user_mongo(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": str(user["_id"])})
    return {"access_token": access_token, "token_type": "bearer"}

async def get_user_from_token(db, token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    try:
        user = await db["users"].find_one({"_id": ObjectId(user_id)})
    except Exception:
        raise credentials_exception
    if user is None:
        raise credentials_exception
    return user

# PUBLIC_INTERFACE
async def get_current_active_user(db=Depends(get_db), token: str = Depends(oauth2_scheme)):
    """
    Dependency: Get current authenticated user.
    """
    user = await get_user_from_token(db, token)
    if not user.get("is_active", True):
        raise HTTPException(status_code=400, detail="Inactive user")
    return user
