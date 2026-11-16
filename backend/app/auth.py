
"""
Authentication utilities: password hashing, JWT token generation/validation.
"""

from datetime import datetime, timedelta
from typing import Optional
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

from .config import get_settings


print("[DEBUG] Initializing authentication utilities...")

settings = get_settings()

print("[DEBUG] Application settings loaded successfully.")
print(f"[DEBUG] JWT Algorithm: {settings.ALGORITHM}")
print(f"[DEBUG] Access Token Expiry: {settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes")


# Password hashing context
print("[DEBUG] Initializing bcrypt password hashing context...")

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

print("[SUCCESS] Password hashing context initialized.")


class TokenData(BaseModel):
    """Token payload schema."""

    sub: str  # user_id
    exp: Optional[datetime] = None


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.
    """

    print("\n[DEBUG] hash_password() called")
    print(f"[DEBUG] Password received | Type: {type(password).__name__}")
    print(f"[DEBUG] Password length: {len(password) if password else 0}")

    print("[DEBUG] Starting bcrypt password hashing...")

    hashed_password = pwd_context.hash(password)

    print("[SUCCESS] Password hashed successfully.")
    print(f"[DEBUG] Generated hash length: {len(hashed_password)}")
    print(f"[DEBUG] Hash algorithm: {pwd_context.schemes()[0]}")

    return hashed_password


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against its hash.
    """

    print("\n[DEBUG] verify_password() called")

    print(f"[DEBUG] Plain password type: {type(plain_password).__name__}")
    print(f"[DEBUG] Hashed password type: {type(hashed_password).__name__}")

    print("[DEBUG] Starting password verification...")

    is_valid = pwd_context.verify(plain_password, hashed_password)

    if is_valid:
        print("[SUCCESS] Password verification successful.")
    else:
        print("[WARNING] Password verification failed. Password does not match.")

    return is_valid


def create_access_token(
    user_id: str,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a JWT access token.
    """

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] create_access_token() called")
    print(f"[DEBUG] User ID: {user_id}")
    print("[DEBUG] ==========================================")

    if expires_delta is None:

        print("[DEBUG] No custom expiration provided.")

        expires_delta = timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        print(
            f"[DEBUG] Using configured expiration: "
            f"{settings.ACCESS_TOKEN_EXPIRE_MINUTES} minutes"
        )

    else:

        print(f"[DEBUG] Custom expiration provided: {expires_delta}")

    expire = datetime.utcnow() + expires_delta

    print(f"[DEBUG] Token creation time: {datetime.utcnow()}")
    print(f"[DEBUG] Token expiration time: {expire}")

    to_encode = {
        "sub": user_id,
        "exp": expire,
    }

    print("[DEBUG] JWT payload constructed.")
    print(f"[DEBUG] Payload fields: {list(to_encode.keys())}")
    print(f"[DEBUG] JWT Algorithm: {settings.ALGORITHM}")

    print("[DEBUG] Encoding JWT token...")

    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )

    print("[SUCCESS] JWT access token generated successfully.")
    print(f"[DEBUG] Generated token length: {len(encoded_jwt)}")
    print("[DEBUG] Token value hidden for security.")

    print("[DEBUG] ==========================================\n")

    return encoded_jwt


def decode_token(token: str) -> Optional[str]:
    """
    Decode and validate a JWT token.
    """

    print("\n[DEBUG] ==========================================")
    print("[DEBUG] decode_token() called")
    print(f"[DEBUG] Token type: {type(token).__name__}")
    print(f"[DEBUG] Token length: {len(token) if token else 0}")
    print("[DEBUG] Token value hidden for security.")
    print("[DEBUG] ==========================================")

    try:

        print("[DEBUG] Starting JWT decoding and validation...")
        print(f"[DEBUG] Expected JWT Algorithm: {settings.ALGORITHM}")

        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM],
        )

        print("[SUCCESS] JWT decoded and validated successfully.")

        print(f"[DEBUG] Payload fields: {list(payload.keys())}")

        user_id: str = payload.get("sub")

        if user_id is None:

            print("[WARNING] JWT payload does not contain a subject (sub).")
            print("[DEBUG] Returning None.")

            return None

        print(f"[SUCCESS] User ID extracted from JWT: {user_id}")

        if "exp" in payload:
            print("[DEBUG] Token expiration claim exists.")

        print("[SUCCESS] JWT validation completed successfully.")
        print("[DEBUG] ==========================================\n")

        return user_id

    except JWTError as e:

        print("[ERROR] JWT validation failed.")
        print(f"[ERROR] Exception type: {type(e).__name__}")
        print(f"[ERROR] Exception message: {str(e)}")
        print("[DEBUG] Returning None for invalid token.")
        print("[DEBUG] ==========================================\n")

        return None


def validate_email(email: str) -> bool:
    """
    Validate email format.
    """

    import re

    print("\n[DEBUG] validate_email() called")
    print(f"[DEBUG] Email type: {type(email).__name__}")
    print(f"[DEBUG] Email length: {len(email) if email else 0}")

    pattern = r'^[a-zA-Z0-9.\_%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'

    print("[DEBUG] Applying email validation regex...")

    is_valid = re.match(pattern, email) is not None

    if is_valid:

        print("[SUCCESS] Email format validation passed.")

    else:

        print("[WARNING] Email format validation failed.")

    return is_valid


def validate_password(password: str) -> bool:
    """
    Validate password strength (>= 8 chars).
    """

    print("\n[DEBUG] validate_password() called")
    print(f"[DEBUG] Password type: {type(password).__name__}")

    password_length = len(password)

    print(f"[DEBUG] Password length: {password_length}")
    print("[DEBUG] Minimum required length: 8 characters")

    is_valid = password_length >= 8

    if is_valid:

        print("[SUCCESS] Password length validation passed.")

    else:

        print("[WARNING] Password length validation failed.")
        print(f"[WARNING] Current length: {password_length}")
        print(f"[WARNING] Required length: 8")

    return is_valid


print("[SUCCESS] Authentication utilities loaded successfully.")
