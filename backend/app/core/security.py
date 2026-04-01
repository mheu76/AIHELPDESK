"""
Security utilities for JWT tokens and password hashing.
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
import hashlib
import os

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# TEMPORARY: Using simple SHA256 hash due to bcrypt + Python 3.14 compatibility issue
# TODO: Revert to bcrypt once compatibility is resolved
# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.

    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database

    Returns:
        True if password matches, False otherwise
    """
    # TEMPORARY: Simple hash verification (NOT production-safe)
    return get_password_hash(plain_password) == hashed_password


def get_password_hash(password: str) -> str:
    """
    Hash a password for storage.

    Args:
        password: Plain text password

    Returns:
        Hashed password
    """
    # TEMPORARY: Simple SHA256 hash (NOT production-safe, no salt)
    # This is a workaround for bcrypt + Python 3.14 compatibility issue
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def create_access_token(
    subject: str,
    expires_delta: Optional[timedelta] = None,
    additional_claims: Optional[Dict[str, Any]] = None
) -> str:
    """
    Create a JWT access token.

    Args:
        subject: Subject of the token (usually user ID)
        expires_delta: Token expiration time (defaults to settings)
        additional_claims: Additional claims to include in token

    Returns:
        Encoded JWT token
    """
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "access"
    }

    # Add additional claims if provided
    if additional_claims:
        to_encode.update(additional_claims)

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def create_refresh_token(subject: str) -> str:
    """
    Create a JWT refresh token.

    Args:
        subject: Subject of the token (usually user ID)

    Returns:
        Encoded JWT refresh token
    """
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

    to_encode = {
        "exp": expire,
        "sub": str(subject),
        "type": "refresh"
    }

    encoded_jwt = jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token to decode

    Returns:
        Token payload if valid, None if invalid

    Raises:
        JWTError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return payload
    except JWTError as e:
        logger.warning(f"JWT decode error: {str(e)}")
        raise


def get_token_subject(token: str) -> Optional[str]:
    """
    Extract subject (user ID) from JWT token.

    Args:
        token: JWT token

    Returns:
        Subject (user ID) if valid, None if invalid
    """
    try:
        payload = decode_token(token)
        if payload:
            return payload.get("sub")
        return None
    except JWTError:
        return None
