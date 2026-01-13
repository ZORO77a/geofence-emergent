from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import os
import string
import hashlib
import secrets
from hmac import compare_digest
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv(Path(__file__).parent / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY or SECRET_KEY == "your-secret-key-change-in-production":
    raise ValueError("SECRET_KEY environment variable must be set to a strong random value!")

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def hash_otp(otp: str) -> str:
    """Hash OTP before storing in database using PBKDF2"""
    return hashlib.pbkdf2_hmac('sha256', otp.encode(), b'otp_salt', 100000).hex()

def verify_otp(plain_otp: str, hashed_otp: str) -> bool:
    """Verify OTP against hashed version using constant-time comparison"""
    return compare_digest(hash_otp(plain_otp), hashed_otp)

def create_access_token(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None

def generate_otp(length: int = 6) -> str:
    """Generate cryptographically secure OTP using secrets module"""
    return ''.join(str(secrets.randbelow(10)) for _ in range(length))

def generate_reset_token(length: int = 32) -> str:
    """Generate cryptographically secure password reset token"""
    return secrets.token_urlsafe(length)

def create_reset_token(data: dict, expires_delta: timedelta = None):
    """Create password reset token with 1 hour expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=1)
    to_encode.update({"exp": expire, "type": "reset"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_reset_token(token: str):
    """Verify reset token and return email if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "reset":
            return None
        return payload.get("email")
    except JWTError:
        return None

def generate_csrf_token() -> str:
    """Generate cryptographically secure CSRF token"""
    return secrets.token_urlsafe(32)

def create_csrf_token(data: dict):
    """Create signed CSRF token"""
    to_encode = data.copy()
    to_encode.update({"type": "csrf", "exp": datetime.utcnow() + timedelta(hours=1)})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verify_csrf_token(token: str):
    """Verify CSRF token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "csrf":
            return None
        return payload
    except JWTError:
        return None

def create_refresh_token(data: dict, expires_delta: timedelta = None):
    """Create refresh token with 7-day expiration"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def verify_refresh_token(token: str):
    """Verify refresh token and return username if valid"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            return None
        return payload.get("sub")
    except JWTError:
        return None

