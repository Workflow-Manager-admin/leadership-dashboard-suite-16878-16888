from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId

from src.api.db import get_database
from src.api.models_auth import UserCreate, UserLogin, UserPublic, AuthToken
from src.api.utils.auth_utils import (
    hash_password,
    verify_password,
    create_jwt_token,
    decode_jwt_token,
)

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

async def get_user_by_email(email: str, db: AsyncIOMotorDatabase):
    user = await db.users.find_one({"email": email})
    return user

async def get_user_by_id(user_id: str, db: AsyncIOMotorDatabase):
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    return user

# PUBLIC_INTERFACE
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncIOMotorDatabase = Depends(get_database)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate user credentials",
        headers={"WWW-Authenticate": "Bearer"}
    )
    try:
        payload = decode_jwt_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    user = await get_user_by_id(user_id, db)
    if user is None or not user.get("is_active", True):
        raise credentials_exception
    return user

# PUBLIC_INTERFACE
@router.post("/register", response_model=UserPublic, summary="Register new user")
async def register_user(payload: UserCreate, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Registers a new user, given email + password."""
    exists = await db.users.find_one({"email": payload.email})
    if exists:
        raise HTTPException(status_code=400, detail="Email already registered")
    hashed = hash_password(payload.password)
    doc = {"email": payload.email, "hashed_password": hashed, "is_active": True}
    result = await db.users.insert_one(doc)
    user_id = str(result.inserted_id)
    return UserPublic(user_id=user_id, email=payload.email, is_active=True)

# PUBLIC_INTERFACE
@router.post("/login", response_model=AuthToken, summary="Login and get JWT token")
async def login(payload: UserLogin, db: AsyncIOMotorDatabase = Depends(get_database)):
    """Authenticate and issue access token."""
    user = await db.users.find_one({"email": payload.email})
    if not user or not verify_password(payload.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access_token = create_jwt_token(data={"sub": str(user["_id"]), "email": user["email"]})
    return AuthToken(access_token=access_token, token_type="bearer")

# PUBLIC_INTERFACE
@router.post("/logout", summary="Logout (dummy; client-side)")
async def logout(request: Request):
    """Dummy endpoint for client-driven logout (JWT just deleted on client)."""
    return {"message": "Successfully logged out"}
