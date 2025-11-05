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
            # User permissions
            "user:create", "user:read", "user:update", "user:delete",
            # Branch permissions
            "branch:create", "branch:read", "branch:update", "branch:delete", "branch:assign_users",
            # Currency permissions
            "currency:create", "currency:read", "currency:update", "currency:delete", "currency:set_rates",
            # Transaction permissions
            "transaction:create", "transaction:read", "transaction:approve", "transaction:cancel",
            # Vault permissions
            "vault:read", "vault:transfer", "vault:approve_transfer",
            # Report permissions
            "report:view_branch", "report:view_all", "report:export",
            # Customer permissions
            "customer:create", "customer:read", "customer:update", "customer:delete",
        ]
    },
    "manager": {
        "name": "manager",
        "display_name_ar": "مدير الفرع",
        "description": "Branch-level management with approval capabilities",
        "permissions": [
            # User permissions (limited)
            "user:read",
            # Branch permissions
            "branch:read", "branch:update", "branch:assign_users",
            # Currency permissions (read + set rates)
            "currency:read", "currency:set_rates",
            # Transaction permissions (all)
            "transaction:create", "transaction:read", "transaction:approve", "transaction:cancel",
            # Vault permissions (limited)
            "vault:read", "vault:transfer",
            # Report permissions (branch only)
            "report:view_branch", "report:export",
            # Customer permissions (all)
            "customer:create", "customer:read", "customer:update",
        ]
    },
    "teller": {
        "name": "teller",
        "display_name_ar": "موظف الصراف",
        "description": "Front-desk operations with limited permissions",
        "permissions": [
            # Currency permissions (read only)
            "currency:read",
            # Transaction permissions (create + read)
            "transaction:create", "transaction:read",
            # Report permissions (own transactions)
            "report:view_branch",
            # Customer permissions (create + read)
            "customer:create", "customer:read",
        ]
    }
}