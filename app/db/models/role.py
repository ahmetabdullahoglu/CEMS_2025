"""
Role Database Model
Handles role-based access control (RBAC)
"""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import JSONB

from app.db.base_class import BaseModel


class Role(BaseModel):
    """
    Role model for RBAC system
    Contains permissions as flexible JSONB
    """
    
    __tablename__ = "roles"
    
    # Role Information
    name = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique role identifier (admin, manager, teller)"
    )
    
    display_name_ar = Column(
        String(100),
        nullable=False,
        comment="Arabic display name for the role"
    )
    
    description = Column(
        Text,
        nullable=True,
        comment="Detailed description of the role"
    )
    
    # Permissions stored as JSONB for flexibility
    permissions = Column(
        JSONB,
        nullable=False,
        default=list,
        comment="List of permissions granted to this role"
    )
    
    # Relationships
    users = relationship(
        "User",
        secondary="user_roles",
        primaryjoin="Role.id == user_roles.c.role_id",  # ← تحديد واضح
        secondaryjoin="User.id == user_roles.c.user_id",
        back_populates="roles",
        lazy="selectin"
    )
    
    def __repr__(self) -> str:
        return f"<Role(name='{self.name}', display_name_ar='{self.display_name_ar}')>"
    
    def has_permission(self, permission: str) -> bool:
        """Check if this role has a specific permission"""
        return permission in self.permissions
    
    def add_permission(self, permission: str) -> None:
        """Add a permission to this role"""
        if permission not in self.permissions:
            self.permissions.append(permission)
    
    def remove_permission(self, permission: str) -> None:
        """Remove a permission from this role"""
        if permission in self.permissions:
            self.permissions.remove(permission)