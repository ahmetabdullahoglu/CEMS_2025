"""
User Database Model
Handles user authentication and management
"""

from datetime import datetime
from typing import List
from sqlalchemy import Column, String, Boolean, DateTime, Integer, Table, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid

from app.db.base_class import BaseModel


# Association table for User-Branch many-to-many relationship
user_branches = Table(
    'user_branches',
    BaseModel.metadata,
    Column('id', PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('user_id', PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('branch_id', PGUUID(as_uuid=True), ForeignKey('branches.id', ondelete='CASCADE'), nullable=False),
    Column('is_primary', Boolean, default=False, nullable=False),
    Column('assigned_at', DateTime, default=datetime.utcnow, nullable=False),
    #Column('assigned_by', PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True),
    Column('assigned_by', PGUUID(as_uuid=True), nullable=True)  # بدون FK

)


# Association table for User-Role many-to-many relationship
user_roles = Table(
    'user_roles',
    BaseModel.metadata,
    Column('id', PGUUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
    Column('user_id', PGUUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
    Column('role_id', PGUUID(as_uuid=True), ForeignKey('roles.id', ondelete='CASCADE'), nullable=False),
    Column('assigned_at', DateTime, default=datetime.utcnow, nullable=False),
    Column('assigned_by', PGUUID(as_uuid=True), ForeignKey('users.id'), nullable=True),
)


class User(BaseModel):
    """
    User model for authentication and authorization
    Supports multiple branches and roles
    """
    
    __tablename__ = "users"
    
    # Basic Information
    username = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique username for login"
    )
    
    email = Column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
        comment="User email address"
    )
    
    hashed_password = Column(
        String(255),
        nullable=False,
        comment="Bcrypt hashed password"
    )
    
    full_name = Column(
        String(100),
        nullable=False,
        comment="User's full name"
    )
    
    phone_number = Column(
        String(20),
        nullable=True,
        comment="User's phone number (optional)"
    )
    
    # Status Fields
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether the account is active"
    )
    
    is_superuser = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether user has superuser privileges"
    )
    
    # Security Fields
    last_login = Column(
        DateTime,
        nullable=True,
        comment="Timestamp of last successful login"
    )
    
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Count of consecutive failed login attempts"
    )
    
    locked_until = Column(
        DateTime,
        nullable=True,
        comment="Account lock expiration timestamp"
    )
    
    # Relationships
    # branches = relationship(
    #     "Branch",
    #     secondary=user_branches,
    #     back_populates="users",
    #     lazy="selectin"
    # )
    
    roles = relationship(
        "Role",
        secondary=user_roles,
        primaryjoin="User.id == user_roles.c.user_id",  # ← تحديد واضح
        secondaryjoin="Role.id == user_roles.c.role_id",
        back_populates="users",
        lazy="selectin"
    )
    
    # Back references (will be populated by related models)
    # transactions = relationship("Transaction", back_populates="user")
    # created_customers = relationship("Customer", back_populates="created_by_user")
    
    def __repr__(self) -> str:
        return f"<User(username='{self.username}', email='{self.email}')>"
    
    @property
    def is_locked(self) -> bool:
        """Check if account is currently locked"""
        if self.locked_until is None:
            return False
        return datetime.utcnow() < self.locked_until
    
    def has_role(self, role_name: str) -> bool:
        """Check if user has a specific role"""
        return any(role.name == role_name for role in self.roles)
    
    def has_permission(self, permission: str) -> bool:
        """Check if user has a specific permission through any of their roles"""
        if self.is_superuser:
            return True
        
        for role in self.roles:
            if permission in role.permissions:
                return True
        
        return False
    
    # def get_primary_branch(self):
    #     """Get user's primary branch"""
    #     # This will need to be implemented with a query to user_branches table
    #     # For now, return first branch if any
    #     return self.branches[0] if self.branches else None