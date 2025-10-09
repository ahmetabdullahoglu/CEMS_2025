"""
Security Utilities
Password hashing and JWT token management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings
from app.core.exceptions import InvalidTokenError, TokenExpiredError


# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Password Hashing ====================

def get_password_hash(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        str: Hashed password
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hash
    
    Args:
        plain_password: Plain text password
        hashed_password: Hashed password from database
        
    Returns:
        bool: True if password matches
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==================== JWT Token Management ====================

def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT access token
    
    Args:
        data: Data to encode in token (usually user_id, username)
        expires_delta: Custom expiration time (optional)
        
    Returns:
        str: Encoded JWT token
        
    Example:
        >>> token = create_access_token({"sub": user_id, "username": "john"})
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "access"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def create_refresh_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None
) -> str:
    """
    Create JWT refresh token (longer expiration)
    
    Args:
        data: Data to encode in token
        expires_delta: Custom expiration time (optional)
        
    Returns:
        str: Encoded JWT refresh token
    """
    to_encode = data.copy()
    
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )
    
    to_encode.update({
        "exp": expire,
        "iat": datetime.utcnow(),
        "type": "refresh"
    })
    
    encoded_jwt = jwt.encode(
        to_encode,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )
    
    return encoded_jwt


def decode_token(token: str) -> Dict[str, Any]:
    """
    Decode and verify JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        InvalidTokenError: If token is invalid
        TokenExpiredError: If token has expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        raise TokenExpiredError()
        
    except JWTError:
        raise InvalidTokenError()


def verify_token_type(token: str, expected_type: str) -> Dict[str, Any]:
    """
    Verify token and check its type (access or refresh)
    
    Args:
        token: JWT token string
        expected_type: Expected token type ("access" or "refresh")
        
    Returns:
        dict: Decoded token payload
        
    Raises:
        InvalidTokenError: If token type doesn't match
    """
    payload = decode_token(token)
    
    token_type = payload.get("type")
    if token_type != expected_type:
        raise InvalidTokenError(
            f"Invalid token type. Expected '{expected_type}', got '{token_type}'"
        )
    
    return payload


def get_token_expire_time(token: str) -> Optional[datetime]:
    """
    Get token expiration time
    
    Args:
        token: JWT token string
        
    Returns:
        datetime: Token expiration time or None if invalid
    """
    try:
        payload = decode_token(token)
        exp_timestamp = payload.get("exp")
        
        if exp_timestamp:
            return datetime.fromtimestamp(exp_timestamp)
        
        return None
        
    except (InvalidTokenError, TokenExpiredError):
        return None


def is_token_expired(token: str) -> bool:
    """
    Check if token is expired
    
    Args:
        token: JWT token string
        
    Returns:
        bool: True if token is expired
    """
    expire_time = get_token_expire_time(token)
    
    if expire_time is None:
        return True
    
    return datetime.utcnow() > expire_time


# ==================== Utility Functions ====================

def generate_password_reset_token(email: str) -> str:
    """
    Generate a token for password reset
    
    Args:
        email: User's email address
        
    Returns:
        str: Password reset token (valid for 30 minutes)
    """
    delta = timedelta(minutes=30)
    return create_access_token(
        data={"sub": email, "purpose": "password_reset"},
        expires_delta=delta
    )


def verify_password_reset_token(token: str) -> Optional[str]:
    """
    Verify password reset token and extract email
    
    Args:
        token: Password reset token
        
    Returns:
        str: User's email if token is valid, None otherwise
    """
    try:
        payload = decode_token(token)
        
        # Check token purpose
        if payload.get("purpose") != "password_reset":
            return None
        
        return payload.get("sub")
        
    except (InvalidTokenError, TokenExpiredError):
        return None


def generate_email_verification_token(email: str) -> str:
    """
    Generate a token for email verification
    
    Args:
        email: User's email address
        
    Returns:
        str: Email verification token (valid for 24 hours)
    """
    delta = timedelta(hours=24)
    return create_access_token(
        data={"sub": email, "purpose": "email_verification"},
        expires_delta=delta
    )


def verify_email_verification_token(token: str) -> Optional[str]:
    """
    Verify email verification token and extract email
    
    Args:
        token: Email verification token
        
    Returns:
        str: User's email if token is valid, None otherwise
    """
    try:
        payload = decode_token(token)
        
        # Check token purpose
        if payload.get("purpose") != "email_verification":
            return None
        
        return payload.get("sub")
        
    except (InvalidTokenError, TokenExpiredError):
        return None