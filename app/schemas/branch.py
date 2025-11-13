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
    usd_value: Optional[float] = None  # Total USD equivalent value (calculated on demand)

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


# ==================== User Assignment Schemas ====================

class UserAssignmentRequest(BaseModel):
    """
    Request schema for assigning users to branch
    
    Used in: POST /branches/{branch_id}/users
    """
    user_ids: List[UUID] = Field(
        ...,
        description="List of user UUIDs to assign to the branch",
        min_length=1
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "user_ids": [
                    "123e4567-e89b-12d3-a456-426614174000",
                    "223e4567-e89b-12d3-a456-426614174001",
                    "323e4567-e89b-12d3-a456-426614174002"
                ]
            }
        }
    )


class UserBranchAssignment(BaseModel):
    """
    Schema representing a user-branch assignment
    
    Used for detailed assignment information
    """
    user_id: UUID
    branch_id: UUID
    is_primary: bool = False
    assigned_at: datetime
    assigned_by: Optional[UUID] = None
    
    model_config = ConfigDict(from_attributes=True)


class BranchUsersResponse(BaseModel):
    """
    Response schema for branch users list
    
    Used in: GET /branches/{branch_id}/users
    """
    branch_id: UUID
    branch_code: str
    branch_name: str
    total_users: int
    users: List['UserResponse']  # From app.schemas.user
    
    model_config = ConfigDict(from_attributes=True)

class UserResponse(BaseModel):
    """User response for branch assignments"""
    id: UUID
    username: str
    email: str
    full_name: str
    is_active: bool
    
    class Config:
        from_attributes = True

# ==================== Reconciliation Schemas ====================

class ReconciliationRequest(BaseModel):
    """
    Request schema for balance reconciliation
    
    Used in: POST /branches/{branch_id}/balances/{currency_id}/reconcile
    """
    actual_balance: Decimal = Field(
        ...,
        ge=0,
        description="Actual counted balance"
    )
    notes: Optional[str] = Field(
        None,
        max_length=500,
        description="Additional notes about the reconciliation"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "actual_balance": 52500.50,
                "notes": "Physical count performed at end of business day. Discrepancy found due to unrecorded commission."
            }
        }
    )


class ReconciliationResponse(BaseModel):
    """
    Response schema for balance reconciliation
    
    Returns detailed reconciliation results
    """
    branch_id: UUID
    currency_id: UUID
    currency_code: str
    expected_balance: Decimal
    actual_balance: Decimal
    difference: Decimal
    difference_percentage: Optional[float] = None
    adjustment_made: bool
    reconciliation_time: datetime
    reconciled_by: UUID
    notes: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "branch_id": "123e4567-e89b-12d3-a456-426614174000",
                "currency_id": "223e4567-e89b-12d3-a456-426614174001",
                "currency_code": "USD",
                "expected_balance": 50000.00,
                "actual_balance": 52500.50,
                "difference": 2500.50,
                "difference_percentage": 5.0,
                "adjustment_made": True,
                "reconciliation_time": "2025-10-26T18:00:00Z",
                "reconciled_by": "323e4567-e89b-12d3-a456-426614174002",
                "notes": "Physical count reconciliation"
            }
        }
    )


class ReconciliationHistory(BaseModel):
    """
    Historical reconciliation record
    
    Used for viewing past reconciliations
    """
    id: UUID
    branch_id: UUID
    currency_id: UUID
    currency_code: str
    expected_balance: Decimal
    actual_balance: Decimal
    difference: Decimal
    reconciled_at: datetime
    reconciled_by: UUID
    reconciled_by_name: str
    notes: Optional[str] = None
    
    model_config = ConfigDict(from_attributes=True)


class ReconciliationHistoryResponse(BaseModel):
    """
    Response for reconciliation history list
    """
    branch_id: UUID
    currency_id: UUID
    total_records: int
    reconciliations: List[ReconciliationHistory]
    
    model_config = ConfigDict(from_attributes=True)

# ==================== Alert Schemas ====================

class BranchAlertResponse(BaseModel):
    """Branch alert response"""
    id: UUID
    branch_id: UUID
    currency_id: UUID
    currency_code: str
    alert_type: str
    severity: str
    title: str
    message: str
    triggered_at: datetime
    is_resolved: bool
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[UUID] = None
    resolution_notes: Optional[str] = None
    
    class Config:
        from_attributes = True

class AlertResolutionRequest(BaseModel):
    """
    Request schema for resolving an alert
    
    Used in: PUT /branches/alerts/{alert_id}/resolve
    """
    resolution_notes: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Detailed notes about how the alert was resolved"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "resolution_notes": "Balance has been topped up with 50,000 TRY from main vault. Alert threshold has been reviewed and updated."
            }
        }
    )


class AlertStatistics(BaseModel):
    """
    Statistics about branch alerts
    
    Used for dashboard and monitoring
    """
    branch_id: UUID
    total_active_alerts: int
    critical_count: int
    warning_count: int
    info_count: int
    low_balance_count: int
    high_balance_count: int
    oldest_unresolved: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Balance History Schemas ====================

class BalanceHistoryRecord(BaseModel):
    """
    Single balance history record
    
    Simplified version for list responses
    """
    id: UUID
    change_type: str  # BalanceChangeType as string
    amount: Decimal
    balance_before: Decimal
    balance_after: Decimal
    performed_at: datetime
    performed_by: Optional[UUID] = None
    reference_id: Optional[UUID] = None
    reference_type: Optional[str] = None
    notes: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "change_type": "transaction",
                "amount": 5000.00,
                "balance_before": 10000.00,
                "balance_after": 15000.00,
                "performed_at": "2025-10-26T10:30:00Z",
                "performed_by": "223e4567-e89b-12d3-a456-426614174001",
                "reference_id": "323e4567-e89b-12d3-a456-426614174002",
                "reference_type": "income_transaction",
                "notes": "Daily income deposit"
            }
        }
    )


class BalanceHistoryResponse(BaseModel):
    """
    Complete balance history response with metadata
    
    Used in: GET /branches/{branch_id}/balances/{currency_id}/history
    """
    branch_id: UUID
    currency_id: UUID
    currency_code: str
    currency_name: str
    current_balance: Decimal
    total_records: int
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    history: List[BalanceHistoryRecord]
    
    model_config = ConfigDict(
        from_attributes=True,
        json_schema_extra={
            "example": {
                "branch_id": "123e4567-e89b-12d3-a456-426614174000",
                "currency_id": "223e4567-e89b-12d3-a456-426614174001",
                "currency_code": "USD",
                "currency_name": "US Dollar",
                "current_balance": 50000.00,
                "total_records": 3,
                "date_from": "2025-10-01T00:00:00Z",
                "date_to": "2025-10-26T23:59:59Z",
                "history": []
            }
        }
    )


class BalanceHistoryFilter(BaseModel):
    """
    Filter parameters for balance history queries
    
    Used as query parameters
    """
    date_from: Optional[datetime] = Field(
        None,
        description="Start date for history (ISO format)"
    )
    date_to: Optional[datetime] = Field(
        None,
        description="End date for history (ISO format)"
    )
    change_type: Optional[str] = Field(
        None,
        description="Filter by change type (transaction, adjustment, etc.)"
    )
    limit: int = Field(
        100,
        ge=1,
        le=500,
        description="Maximum number of records to return"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "date_from": "2025-10-01T00:00:00Z",
                "date_to": "2025-10-26T23:59:59Z",
                "change_type": "transaction",
                "limit": 100
            }
        }
    )
    
# ==================== Statistsics Schemas ====================

class CurrencyBalanceSummary(BaseModel):
    """Summary of balance for a single currency"""
    currency_code: str
    currency_name: str
    balance: Decimal
    reserved: Decimal
    available: Decimal
    minimum_threshold: Optional[Decimal] = None
    maximum_threshold: Optional[Decimal] = None
    is_below_minimum: bool = False
    is_above_maximum: bool = False
    last_updated: datetime
    last_reconciled: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class BranchStatistics(BaseModel):
    """
    Complete branch statistics
    
    Used in: GET /branches/{branch_id}/statistics
    """
    branch_id: UUID
    branch_code: str
    branch_name: str
    region: str
    is_main_branch: bool
    total_currencies: int
    balances: List[CurrencyBalanceSummary]
    active_alerts: int
    critical_alerts: int
    total_users: int
    last_transaction: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)