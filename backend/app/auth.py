"""
Authentication utilities: password hashing, JWT token generation/validation.
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_settings


settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TokenData(BaseModel):
    """Token payload schema."""
    sub: str  # user_id
    exp: Optional[datetime] = None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    
    Parameters
    ----------
    password : str
        Plain text password
    
    Returns
    -------
    str
        Bcrypt hash
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    
    Parameters
    ----------
    plain_password : str
        Plain text password
    hashed_password : str
        Bcrypt hash
    
    Returns
    -------
    bool
        True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    
    Parameters
    ----------
    user_id : str
        User ID to encode in token
    expires_delta : timedelta, optional
        Token expiration time
    
    Returns
    -------
    str
        JWT token
    """
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    expire = datetime.utcnow() + expires_delta
    to_encode = {
        "sub": user_id,
        "exp": expire,
    }
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )
    
    return encoded_jwt


def decode_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT token.
    
    Parameters
    ----------
    token : str
        JWT token
    
    Returns
    -------
    str or None
        User ID if valid, None if invalid
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return user_id
    except JWTError:
        return None


def validate_email(email: str) -> bool:
    """
    Validate email format.
    
    Parameters
    ----------
    email : str
        Email address
    
    Returns
    -------
    bool
        True if valid
    """
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password(password: str) -> bool:
    """
    Validate password strength (>= 8 chars).
    
    Parameters
    ----------
    password : str
        Password
    
    Returns
    -------
    bool
        True if valid
    """
    return len(password) >= 8
