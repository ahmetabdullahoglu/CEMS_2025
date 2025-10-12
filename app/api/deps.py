# app/api/deps.py
"""
FastAPI Dependencies
Common dependencies for API endpoints (authentication, permissions, roles, etc.)
Merged from two versions with naming priority to the second version.
"""

from typing import AsyncGenerator, Optional, List
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db.models.user import User
from app.core.security import decode_token
from app.core.exceptions import (
    InvalidTokenError,
    TokenExpiredError,
)

# ==================== Database ====================

async def get_async_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Async DB session wrapper (from first version).
    Use this if you prefer `get_async_db` as a dependency.
    """
    async for session in get_db():
        yield session

# ==================== Security Schemes ====================

# Strict HTTP Bearer (priority to second version behavior)
security = HTTPBearer(
    scheme_name="Bearer",
    description="JWT token from /auth/login endpoint",
    auto_error=True,  # strict: raise 401 if missing
)

# Optional HTTP Bearer for endpoints that allow anonymous access
security_optional = HTTPBearer(
    scheme_name="BearerOptional",
    description="Optional JWT token (no 401 if missing)",
    auto_error=False,  # do not raise when Authorization header is absent
)

# ==================== Token Extraction ====================

async def get_token_from_header(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    """
    Extract JWT token from Authorization header (strict).
    Expected: Authorization: Bearer <token>
    """
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return credentials.credentials


async def get_token_from_header_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_optional),
) -> Optional[str]:
    """
    Extract JWT token from Authorization header (optional).
    Returns None if header is missing/invalid instead of raising.
    """
    if not credentials or not credentials.credentials:
        return None
    return credentials.credentials

# ==================== User Authentication ====================

async def get_current_user(
    token: str = Depends(get_token_from_header),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Main authentication dependency (second version naming retained).
    """
    try:
        payload = decode_token(token)

        user_id_str: str = payload.get("sub")
        if not user_id_str:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: malformed user ID",
                headers={"WWW-Authenticate": "Bearer"},
            )

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        return user

    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """Ensure user is active (second version naming retained)."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled",
        )
    return current_user

async def get_current_superuser(
    current_user: User = Depends(get_current_active_user),
) -> User:
    """Ensure user is superuser (second version naming retained)."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Superuser privileges required",
        )
    return current_user

# Optional auth (works with/without token)
async def get_current_user_optional(
    token: Optional[str] = Depends(get_token_from_header_optional),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """
    Return current user if authenticated; otherwise None.
    (Fixed to truly be optional using security_optional.)
    """
    if not token:
        return None
    try:
        return await get_current_user(token, db)  # reuse strict logic
    except HTTPException:
        return None

# ==================== Permission Checks ====================

def require_permissions(required_permissions: List[str]):
    """
    Require ALL specified permissions (second version naming retained).
    """
    async def check_permissions(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        for permission in required_permissions:
            if not current_user.has_permission(permission):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Permission denied: {permission} required",
                )
        return current_user
    return check_permissions

def require_permission(permission: str):
    """
    Require a SINGLE permission (from first version).
    """
    async def checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permission: {permission}",
            )
        return current_user
    return checker

def require_any_permission(permissions: List[str]):
    """
    Require at least ONE of the specified permissions (from first version).
    """
    async def checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        for permission in permissions:
            if current_user.has_permission(permission):
                return current_user
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires one of these permissions: {', '.join(permissions)}",
        )
    return checker

# ==================== Role Checks ====================

def require_any_role(required_roles: List[str]):
    """
    Require at least ONE of the specified roles (second version naming retained).
    """
    async def check_roles(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = [role.name for role in getattr(current_user, "roles", [])]
        if not any(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: one of {required_roles} role required",
            )
        return current_user
    return check_roles

def require_all_roles(required_roles: List[str]):
    """
    Require ALL specified roles (second version naming retained).
    """
    async def check_roles(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        user_roles = [role.name for role in getattr(current_user, "roles", [])]
        if not all(role in user_roles for role in required_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied: all of {required_roles} roles required",
            )
        return current_user
    return check_roles

def require_role(role_name: str):
    """
    Require a SINGLE role (from first version).
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_role(role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {role_name}",
            )
        return current_user
    return role_checker

def require_role_and_permission(role_name: str, permission: str):
    """
    Require BOTH a specific role AND a specific permission (from first version).
    """
    async def checker(
        current_user: User = Depends(get_current_active_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        if not current_user.has_role(role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required role: {role_name}",
            )
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required permission: {permission}",
            )
        return current_user
    return checker


def require_roles(role_names: List[str]):
    """
    Backwards-compatible alias.
    Old behavior: require at least ONE of the specified roles.
    """
    return require_any_role(role_names)

# ==================== Utility ====================

async def verify_admin_or_owner(
    item_owner_id: UUID,
    current_user: User = Depends(get_current_active_user),
) -> User:
    """
    Allow if superuser or owner (from first version).
    """
    if current_user.is_superuser or current_user.id == item_owner_id:
        return current_user
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Not authorized to access this resource",
    )

# ==================== Export All ====================
__all__ = [
    # DB
    "get_async_db",
    # Tokens
    "get_token_from_header",
    "get_token_from_header_optional",
    # Auth
    "get_current_user",
    "get_current_active_user",
    "get_current_superuser",
    "get_current_user_optional",
    # Permissions
    "require_permission",
    "require_permissions",
    "require_any_permission",
    # Roles
    "require_role",
    "require_any_role",
    "require_all_roles",
    "require_role_and_permission",
    "require_roles",  # <-- أضف هذا
    # Utils
    "verify_admin_or_owner",
]
