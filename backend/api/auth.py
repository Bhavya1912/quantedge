"""POST /api/v1/auth — JWT authentication."""
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel

from utils.config import settings

router = APIRouter()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=settings.JWT_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token.",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/login", response_model=TokenResponse)
async def login(req: LoginRequest):
    """
    Authenticate user. Returns JWT token.
    In production: verify against PostgreSQL user store.
    """
    # Demo: accept any non-empty credentials
    # Production: query DB, verify bcrypt hash
    if not req.email or not req.password:
        raise HTTPException(status_code=400, detail="Email and password required.")

    token = create_access_token({"sub": req.email, "email": req.email})
    return TokenResponse(
        access_token=token,
        expires_in=settings.JWT_EXPIRE_MINUTES * 60,
    )


@router.post("/register")
async def register(req: LoginRequest):
    """Register new user. In production: save to DB, trigger Razorpay subscription."""
    token = create_access_token({"sub": req.email, "email": req.email})
    return {
        "message": "Registration successful. Redirecting to payment...",
        "access_token": token,
        "razorpay_key": settings.RAZORPAY_KEY_ID,
        "amount": settings.SUBSCRIPTION_AMOUNT_PAISE,
    }
