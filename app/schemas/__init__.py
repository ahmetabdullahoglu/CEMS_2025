"""
Schemas Package
Exports all Pydantic schemas
"""

from app.schemas.user import (
    UserBase,
    UserCreate,
    UserUpdate,
    UserResponse,
    UserInDB,
    UserListResponse,
    PasswordChange,
    UserBranchAssignment,
    UserRoleAssignment,
    UserStats,
)

from app.schemas.role import (
    RoleBase,
    RoleCreate,
    RoleUpdate,
    RoleResponse,
    RoleWithUsers,
    RoleListResponse,
    PermissionInfo,
    PermissionsListResponse,
    DEFAULT_ROLES,
)

# Export all schemas
__all__ = [
    # User schemas
    "UserBase",
    "UserCreate",
    "UserUpdate",
    "UserResponse",
    "UserInDB",
    "UserListResponse",
    "PasswordChange",
    # "UserBranchAssignment",
    "UserRoleAssignment",
    "UserStats",
    
    # Role schemas
    "RoleBase",
    "RoleCreate",
    "RoleUpdate",
    "RoleResponse",
    "RoleWithUsers",
    "RoleListResponse",
    "PermissionInfo",
    "PermissionsListResponse",
    "DEFAULT_ROLES",
]