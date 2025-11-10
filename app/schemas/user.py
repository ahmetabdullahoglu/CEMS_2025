"""
User Pydantic Schemas
Request and response models for User endpoints
"""

from datetime import datetime
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
import re


# ==================== Base Schemas ====================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    full_name: str = Field(..., min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: bool = True


class UserCreate(UserBase):
    """Schema for creating a new user"""
    password: str = Field(..., min_length=8, max_length=100)
    is_superuser: bool = False
    role_ids: List[UUID] = Field(default_factory=list)
    # branch_ids: List[UUID] = Field(default_factory=list)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        Validate password strength:
        - At least 8 characters
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit
        - At least one special character
        """
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_.-]+$', v):
            raise ValueError(
                'Username can only contain letters, numbers, dots, hyphens, and underscores'
            )
        return v.lower()
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format (international format)"""
        if v is None:
            return v
        
        # Remove spaces and dashes
        cleaned = v.replace(' ', '').replace('-', '')
        
        # Check if it matches international format (+XXX...)
        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError('Invalid phone number format. Use international format (e.g., +90 555 123 4567)')
        
        return cleaned


class UserUpdate(BaseModel):
    """Schema for updating user information"""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, min_length=2, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20)
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    role_ids: Optional[List[UUID]] = None
    branch_ids: Optional[List[UUID]] = None
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Validate phone number format"""
        if v is None:
            return v
        
        cleaned = v.replace(' ', '').replace('-', '')
        if not re.match(r'^\+?[1-9]\d{1,14}$', cleaned):
            raise ValueError('Invalid phone number format')
        
        return cleaned


class PasswordChange(BaseModel):
    """Schema for password change"""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')

        return v


class AdminPasswordReset(BaseModel):
    """Schema for admin password reset (no current password required)"""
    new_password: str = Field(..., min_length=8, max_length=100)

    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')

        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')

        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')

        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')

        return v


# ==================== Response Schemas ====================

class RoleInUser(BaseModel):
    """Role information in user response"""
    id: UUID
    name: str
    display_name_ar: str
    
    class Config:
        from_attributes = True


# class BranchInUser(BaseModel):
#     """Branch information in user response"""
#     id: UUID
#     code: str
#     name_en: str
#     name_ar: str
#     is_primary: bool = False
    
#     class Config:
#         from_attributes = True


class UserResponse(UserBase):
    """User response schema (without sensitive data)"""
    id: UUID
    is_superuser: bool
    last_login: Optional[datetime] = None
    failed_login_attempts: int = 0
    is_locked: bool = False
    created_at: datetime
    updated_at: datetime
    roles: List[RoleInUser] = []
    #branches: List[BranchInUser] = []
    
    class Config:
        from_attributes = True


class UserInDB(UserResponse):
    """User schema with hashed password (for internal use only)"""
    hashed_password: str
    locked_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    """Response for list of users with pagination"""
    success: bool = True
    data: List[UserResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==================== Additional Schemas ====================

class UserBranchAssignment(BaseModel):
    """Schema for assigning user to branch"""
    user_id: UUID
    branch_id: UUID
    is_primary: bool = False


class UserRoleAssignment(BaseModel):
    """Schema for assigning role to user"""
    user_id: UUID
    role_id: UUID


class UserStats(BaseModel):
    """User statistics"""
    total_transactions: int = 0
    total_customers_registered: int = 0
    last_activity: Optional[datetime] = None