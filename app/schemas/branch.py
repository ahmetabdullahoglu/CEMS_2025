# app/schemas/branch.py
"""
Branch Management Schemas - FIXED VERSION
Pydantic models for branch-related operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, validator, ConfigDict

from app.db.models.branch import (
    RegionEnum, BalanceChangeType, BalanceAlertType, AlertSeverity
)


# ==================== Branch Schemas ====================

class BranchBase(BaseModel):
    """Base branch schema with common fields"""
    code: str = Field(..., min_length=5, max_length=10, description="Branch code (e.g., BR001)")
    name_en: str = Field(..., min_length=2, max_length=200, description="English name")
    name_ar: str = Field(..., min_length=2, max_length=200, description="Arabic name")
    region: RegionEnum = Field(..., description="Geographic region")
    address: str = Field(..., min_length=10, max_length=500, description="Full address")
    city: str = Field(..., min_length=2, max_length=100, description="City")
    phone: str = Field(..., min_length=10, max_length=20, description="Phone number")
    email: Optional[str] = Field(None, max_length=100, description="Email address")
    
    @validator('code')
    def validate_code_format(cls, v):
        """Validate branch code format (BR followed by digits)"""
        if not v.startswith('BR') or not v[2:].isdigit():
            raise ValueError("Branch code must start with 'BR' followed by digits (e.g., BR001)")
        return v
    
    @validator('email')
    def validate_email(cls, v):
        """Basic email validation"""
        if v and '@' not in v:
            raise ValueError("Invalid email format")
        return v
    
    model_config = ConfigDict(from_attributes=True)


class BranchCreate(BranchBase):
    """Schema for creating a branch"""
    manager_id: Optional[UUID] = Field(None, description="Manager user ID")
    is_main_branch: bool = Field(False, description="Whether this is the main branch")
    opening_balance_date: Optional[datetime] = Field(None, description="Opening date")


class BranchUpdate(BaseModel):
    """Schema for updating a branch"""
    name_en: Optional[str] = Field(None, min_length=2, max_length=200)
    name_ar: Optional[str] = Field(None, min_length=2, max_length=200)
    region: Optional[RegionEnum] = None
    address: Optional[str] = Field(None, min_length=10, max_length=500)
    city: Optional[str] = Field(None, min_length=2, max_length=100)
    phone: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    manager_id: Optional[UUID] = None
    is_main_branch: Optional[bool] = None
    is_active: Optional[bool] = None
    
    model_config = ConfigDict(from_attributes=True)


class BranchResponse(BranchBase):
    """Schema for branch response - FIXED: opening_balance_date is truly optional"""
    id: UUID
    manager_id: Optional[UUID]
    is_main_branch: bool
    is_active: bool
    opening_balance_date: Optional[datetime] = None  # ✅ FIX: Default to None
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Branch Balance Schemas ====================

class BranchBalanceBase(BaseModel):
    """Base branch balance schema"""
    balance: Decimal = Field(..., ge=0, description="Current balance")
    reserved_balance: Decimal = Field(0, ge=0, description="Reserved balance")
    minimum_threshold: Optional[Decimal] = Field(None, ge=0, description="Minimum threshold")
    maximum_threshold: Optional[Decimal] = Field(None, gt=0, description="Maximum threshold")
    
    @validator('reserved_balance')
    def validate_reserved(cls, v, values):
        """Validate reserved balance doesn't exceed total"""
        if 'balance' in values and v > values['balance']:
            raise ValueError("Reserved balance cannot exceed total balance")
        return v
    
    @validator('maximum_threshold')
    def validate_thresholds(cls, v, values):
        """Validate threshold logic"""
        if v and 'minimum_threshold' in values and values['minimum_threshold']:
            if values['minimum_threshold'] >= v:
                raise ValueError("Minimum threshold must be less than maximum threshold")
        return v
    
    model_config = ConfigDict(from_attributes=True)


class BranchBalanceResponse(BranchBalanceBase):
    """Schema for branch balance response"""
    id: UUID
    branch_id: UUID
    currency_id: UUID
    currency_code: str
    currency_name: str
    available_balance: Decimal
    last_updated: datetime
    last_reconciled_at: Optional[datetime] = None  # ✅ FIX: Default to None
    
    model_config = ConfigDict(from_attributes=True)


class BranchWithBalances(BranchResponse):
    """Schema for branch with balances"""
    balances: List[BranchBalanceResponse] = []
    
    model_config = ConfigDict(from_attributes=True)


class SetThresholdsRequest(BaseModel):
    """Schema for setting balance thresholds"""
    minimum_threshold: Optional[Decimal] = Field(None, ge=0)
    maximum_threshold: Optional[Decimal] = Field(None, gt=0)
    
    @validator('maximum_threshold')
    def validate_thresholds(cls, v, values):
        """Validate threshold logic"""
        if v and 'minimum_threshold' in values and values['minimum_threshold']:
            if values['minimum_threshold'] >= v:
                raise ValueError("Minimum threshold must be less than maximum threshold")
        return v


# ==================== Branch Balance History Schemas ====================

class BranchBalanceHistoryResponse(BaseModel):
    """Schema for balance history response"""
    id: UUID
    branch_id: UUID
    currency_id: UUID
    change_type: BalanceChangeType
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    performed_at: datetime
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class BalanceHistoryFilter(BaseModel):
    """Schema for filtering balance history"""
    currency_id: Optional[UUID] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(100, ge=1, le=1000)


# ==================== Branch Alert Schemas ====================

class BranchAlertResponse(BaseModel):
    """Schema for branch alert response"""
    id: UUID
    branch_id: UUID
    currency_id: Optional[UUID] = None
    currency_code: Optional[str] = None
    alert_type: BalanceAlertType
    severity: AlertSeverity
    title: str
    message: str
    is_resolved: bool
    triggered_at: datetime
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ResolveAlertRequest(BaseModel):
    """Schema for resolving an alert"""
    resolution_notes: str = Field(..., min_length=10, max_length=500)


# ==================== Balance Operations Schemas ====================

class ReconcileBalanceRequest(BaseModel):
    """Schema for balance reconciliation"""
    expected_balance: Decimal = Field(..., ge=0)
    notes: Optional[str] = Field(None, max_length=500)


class ReconcileBalanceResponse(BaseModel):
    """Schema for reconciliation response"""
    branch_id: UUID
    currency_id: UUID
    current_balance: Decimal
    expected_balance: Decimal
    difference: Decimal
    adjustment_made: bool
    reconciled_at: datetime
    performed_by: UUID


# ==================== Statistics Schemas ====================

class BranchBalanceSummary(BaseModel):
    """Schema for balance summary"""
    currency_code: str
    currency_name: str
    balance: Decimal
    reserved: Decimal
    available: Decimal
    minimum_threshold: Optional[Decimal] = None
    maximum_threshold: Optional[Decimal] = None
    is_below_minimum: bool
    is_above_maximum: bool
    last_updated: datetime
    last_reconciled: Optional[datetime] = None


class BranchStatistics(BaseModel):
    """Schema for branch statistics"""
    branch_id: UUID
    branch_code: str
    branch_name: str
    region: str
    is_main_branch: bool
    total_currencies: int
    balances: List[BranchBalanceSummary]
    active_alerts: int


# ==================== List Response Schemas ====================

class BranchListResponse(BaseModel):
    """Schema for list of branches - supports both types"""
    total: int
    branches: List[BranchResponse | BranchWithBalances]  # ✅ FIX: Support both types
    
    model_config = ConfigDict(from_attributes=True)


class BranchBalanceListResponse(BaseModel):
    """Schema for list of balances"""
    total: int
    balances: List[BranchBalanceResponse | dict]  # ✅ FIX: Support dict too
    
    model_config = ConfigDict(from_attributes=True)


class BranchAlertListResponse(BaseModel):
    """Schema for list of alerts"""
    total: int
    alerts: List[BranchAlertResponse]


# ==================== Assignment Schemas ====================

class AssignManagerRequest(BaseModel):
    """Schema for assigning manager"""
    user_id: UUID = Field(..., description="User ID to assign as manager")


class AssignUsersRequest(BaseModel):
    """Schema for assigning users to branch"""
    user_ids: List[UUID] = Field(..., min_length=1, description="List of user IDs")
    is_primary: bool = Field(False, description="Whether this is primary branch for users")
