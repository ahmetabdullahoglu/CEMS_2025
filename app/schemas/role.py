"""
Role Pydantic Schemas
Request and response models for Role endpoints
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field


# ==================== Base Schemas ====================

class RoleBase(BaseModel):
    """Base role schema with common fields"""
    name: str = Field(..., min_length=2, max_length=50)
    display_name_ar: str = Field(..., min_length=2, max_length=100)
    description: Optional[str] = None
    permissions: List[str] = Field(default_factory=list)


class RoleCreate(RoleBase):
    """Schema for creating a new role"""
    is_active: bool = True


class RoleUpdate(BaseModel):
    """Schema for updating role information"""
    display_name_ar: Optional[str] = Field(None, min_length=2, max_length=100)
    description: Optional[str] = None
    permissions: Optional[List[str]] = None
    is_active: Optional[bool] = None


# ==================== Response Schemas ====================

class RoleResponse(RoleBase):
    """Role response schema"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class RoleWithUsers(RoleResponse):
    """Role response with user count"""
    user_count: int = 0


class RoleListResponse(BaseModel):
    """Response for list of roles"""
    success: bool = True
    data: List[RoleResponse]
    total: int


# ==================== Permission Schemas ====================

class PermissionInfo(BaseModel):
    """Information about a permission"""
    name: str
    display_name: str
    description: str
    category: str


class PermissionsListResponse(BaseModel):
    """List of all available permissions"""
    success: bool = True
    data: List[PermissionInfo]
    categories: List[str]


# ==================== Default Roles Data ====================

# These will be used for seeding the database
DEFAULT_ROLES = {
    "admin": {
        "name": "admin",
        "display_name_ar": "مدير النظام",
        "description": "Full system access with all permissions",
        "permissions": [
            # User Management
            "users:create", "users:read", "users:update", "users:delete",
            "users:assign_roles", "users:manage_permissions",

            # Branch Management
            "branches:create", "branches:read", "branches:update", "branches:delete",
            "branches:assign_users", "branches:view_all", "branches:manage_balances",

            # Currency Management
            "currencies:create", "currencies:read", "currencies:update", "currencies:delete",
            "currencies:set_rates", "currencies:view_rates", "currencies:manage_rates",

            # Transaction Management
            "transactions:create", "transactions:read", "transactions:update",
            "transactions:delete", "transactions:approve", "transactions:cancel",
            "transactions:view_all",

            # Vault Management
            "vault:create", "vault:read", "vault:update", "vault:transfer",
            "vault:approve", "vault:receive", "vault:cancel",
            "vault:view_balances", "vault:adjust_balance", "vault:reconcile",

            # Reports
            "reports:view_branch", "reports:view_all", "reports:export",
            "reports:generate", "reports:schedule",

            # Customer Management
            "customers:create", "customers:read", "customers:update", "customers:delete",
            "customers:verify", "customers:view_all",

            # Document Management
            "documents:upload", "documents:read", "documents:update", "documents:delete",
            "documents:verify", "documents:download",

            # System Management
            "system:view_logs", "system:manage_settings", "system:backup",
            "system:restore", "system:maintenance",
        ]
    },
    "manager": {
        "name": "manager",
        "display_name_ar": "مدير الفرع",
        "description": "Branch-level management with approval capabilities",
        "permissions": [
            # User Management (limited)
            "users:read",

            # Branch Management
            "branches:read", "branches:update", "branches:assign_users",
            "branches:view_own", "branches:manage_balances",

            # Currency Management
            "currencies:read", "currencies:set_rates", "currencies:view_rates",

            # Transaction Management
            "transactions:create", "transactions:read", "transactions:update",
            "transactions:approve", "transactions:cancel", "transactions:view_branch",

            # Vault Management
            "vault:read", "vault:transfer", "vault:approve", "vault:receive",
            "vault:cancel", "vault:view_balances", "vault:adjust_balance", "vault:reconcile",

            # Reports
            "reports:view_branch", "reports:export", "reports:generate",

            # Customer Management
            "customers:create", "customers:read", "customers:update",
            "customers:verify", "customers:view_branch",

            # Document Management
            "documents:upload", "documents:read", "documents:update",
            "documents:verify", "documents:download",
        ]
    },
    "teller": {
        "name": "teller",
        "display_name_ar": "موظف الصراف",
        "description": "Front-desk operations with limited permissions",
        "permissions": [
            # Currency Management (read only)
            "currencies:read", "currencies:view_rates",

            # Transaction Management
            "transactions:create", "transactions:read", "transactions:view_own",

            # Reports
            "reports:view_branch",

            # Customer Management
            "customers:create", "customers:read", "customers:view_branch",

            # Document Management
            "documents:upload", "documents:read",
        ]
    }
}