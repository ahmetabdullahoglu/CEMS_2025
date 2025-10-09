"""
FastAPI Dependencies
Common dependencies for API endpoints (authentication, permissions, etc.)
"""

from typing import Optional, List
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import get_db
from app.db.models.user import User
from app.core.security import decode_token
from app.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
    PermissionDeniedError,
)


# ==================== Security Scheme ====================

# HTTP Bearer token security
security = HTTPBearer(
    scheme_name="Bearer Token",
    description="JWT token obtained from /auth/login endpoint"
)


# ==================== Token Dependencies ====================

async def get_token(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """
    Extract and validate JWT token from Authorization header
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        str: JWT token
        
    Raises:
        HTTPException: If token is missing or invalid
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization token is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return credentials.credentials


# ==================== User Dependencies ====================

async def get_current_user(
    token: str = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get current authenticated user from JWT token
    
    Args:
        token: JWT access token
        db: Database session
        
    Returns:
        User: Current authenticated user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    try:
        # Decode token
        payload = decode_token(token)
        
        # Get user ID from token
        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError("Token payload is invalid")
        
        # Convert to UUID
        try:
            user_id = UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError("Invalid user ID in token")
        
        # TODO: Check if token is blacklisted (Redis)
        # if await is_token_blacklisted(token):
        #     raise InvalidTokenError("Token has been revoked")
        
        # Get user from database
        result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidTokenError("User not found")
        
        return user
        
    except TokenExpiredError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except InvalidTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get current active user (not disabled)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        User: Current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is disabled"
        )
    
    return current_user


async def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get current user and verify they are a superuser
    
    Args:
        current_user: Current active user
        
    Returns:
        User: Current superuser
        
    Raises:
        HTTPException: If user is not a superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This action requires superuser privileges"
        )
    
    return current_user


# ==================== Role-Based Dependencies ====================

def require_role(*role_names: str):
    """
    Dependency factory for role-based access control
    
    Args:
        *role_names: One or more role names (admin, manager, teller)
        
    Returns:
        Dependency function that checks if user has required role
        
    Example:
        @router.get("/admin-only", dependencies=[Depends(require_role("admin"))])
        async def admin_endpoint():
            return {"message": "Admin access granted"}
    """
    async def role_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Superuser passes all role checks
        if current_user.is_superuser:
            return current_user
        
        # Check if user has any of the required roles
        for role_name in role_names:
            if current_user.has_role(role_name):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires one of these roles: {', '.join(role_names)}"
        )
    
    return role_checker


def require_any_role(role_names: List[str]):
    """
    Alternative syntax for require_role
    
    Args:
        role_names: List of acceptable role names
        
    Returns:
        Dependency function
        
    Example:
        @router.get("/managers", dependencies=[Depends(require_any_role(["admin", "manager"]))])
    """
    return require_role(*role_names)


# ==================== Permission-Based Dependencies ====================

def require_permission(*permissions: str):
    """
    Dependency factory for permission-based access control
    
    Args:
        *permissions: One or more permission strings (e.g., "user:create")
        
    Returns:
        Dependency function that checks if user has required permissions
        
    Example:
        @router.post(
            "/users",
            dependencies=[Depends(require_permission("user:create"))]
        )
        async def create_user():
            return {"message": "User created"}
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
        
        # Check if user has all required permissions
        missing_permissions = []
        for permission in permissions:
            if not current_user.has_permission(permission):
                missing_permissions.append(permission)
        
        if missing_permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Missing required permissions: {', '.join(missing_permissions)}"
            )
        
        return current_user
    
    return permission_checker


def require_any_permission(permissions: List[str]):
    """
    Require user to have at least one of the specified permissions
    
    Args:
        permissions: List of permission strings
        
    Returns:
        Dependency function
    """
    async def permission_checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Superuser has all permissions
        if current_user.is_superuser:
            return current_user
        
        # Check if user has at least one permission
        for permission in permissions:
            if current_user.has_permission(permission):
                return current_user
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"This action requires one of these permissions: {', '.join(permissions)}"
        )
    
    return permission_checker


# ==================== Combined Dependencies ====================

def require_role_and_permission(role_name: str, permission: str):
    """
    Require both specific role AND specific permission
    
    Args:
        role_name: Required role name
        permission: Required permission string
        
    Returns:
        Dependency function
    """
    async def checker(
        current_user: User = Depends(get_current_active_user)
    ) -> User:
        # Superuser passes all checks
        if current_user.is_superuser:
            return current_user
        
        # Check role
        if not current_user.has_role(role_name):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires role: {role_name}"
            )
        
        # Check permission
        if not current_user.has_permission(permission):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This action requires permission: {permission}"
            )
        
        return current_user
    
    return checker


# ==================== Optional Authentication ====================

async def get_current_user_optional(
    token: Optional[str] = Depends(get_token),
    db: AsyncSession = Depends(get_db)
) -> Optional[User]:
    """
    Get current user if authenticated, None otherwise
    Useful for endpoints that have different behavior for authenticated users
    
    Args:
        token: Optional JWT token
        db: Database session
        
    Returns:
        User or None
    """
    if not token:
        return None
    
    try:
        return await get_current_user(token, db)
    except:
        return None