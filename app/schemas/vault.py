# app/schemas/vault.py
"""
Vault Schemas
=============
Pydantic schemas for vault management

Includes schemas for:
- Vault creation, update, and responses
- Vault balance queries
- Vault transfer creation and workflow
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, validator,ConfigDict
from enum import Enum


# ==================== ENUMS ====================

class VaultTypeEnum(str, Enum):
    """Vault types"""
    MAIN = "main"
    BRANCH = "branch"


class VaultTransferTypeEnum(str, Enum):
    """Vault transfer types"""
    VAULT_TO_VAULT = "vault_to_vault"
    VAULT_TO_BRANCH = "vault_to_branch"
    BRANCH_TO_VAULT = "branch_to_vault"


class VaultTransferStatusEnum(str, Enum):
    """Vault transfer statuses"""
    PENDING = "pending"
    APPROVED = "approved"
    IN_TRANSIT = "in_transit"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


# ==================== VAULT SCHEMAS ====================

class VaultBase(BaseModel):
    """Base vault schema"""
    vault_code: str = Field(..., min_length=3, max_length=20)
    name: str = Field(..., min_length=3, max_length=100)
    vault_type: VaultTypeEnum
    description: Optional[str] = None
    location: Optional[str] = None
    
    class Config:
        use_enum_values = True


class VaultCreate(VaultBase):
    """Schema for creating a vault"""
    branch_id: Optional[UUID] = Field(None, description="Branch ID (required for branch vaults)")
    
    @validator('branch_id')
    def validate_branch_id(cls, v, values):
        """Validate that branch_id is provided for branch vaults"""
        if 'vault_type' in values:
            if values['vault_type'] == VaultTypeEnum.BRANCH and v is None:
                raise ValueError("branch_id is required for branch vaults")
            if values['vault_type'] == VaultTypeEnum.MAIN and v is not None:
                raise ValueError("branch_id must be NULL for main vault")
        return v


class VaultUpdate(BaseModel):
    """Schema for updating a vault"""
    name: Optional[str] = Field(None, min_length=3, max_length=100)
    description: Optional[str] = None
    location: Optional[str] = None
    is_active: Optional[bool] = None


class VaultBalanceInfo(BaseModel):
    """Vault balance information"""
    currency_code: str
    currency_name: str
    balance: Decimal
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)  # بدل orm_mode


class VaultResponse(BaseModel):
    """Complete vault response"""
    id: UUID
    vault_code: str
    name: str
    vault_type: VaultTypeEnum
    branch_id: Optional[UUID]
    is_active: bool
    description: Optional[str]
    location: Optional[str]
    balances: Optional[List[VaultBalanceInfo]] = []
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )


class VaultListResponse(BaseModel):
    """List of vaults"""
    total: int
    vaults: List[VaultResponse]


# ==================== VAULT BALANCE SCHEMAS ====================

class VaultBalanceQuery(BaseModel):
    """Query parameters for vault balance"""
    vault_id: UUID
    currency_id: Optional[UUID] = None


class VaultBalanceResponse(BaseModel):
    """Vault balance response"""
    vault_id: UUID
    vault_code: str
    vault_name: str
    currency_id: UUID
    currency_code: str
    balance: Decimal
    last_updated: datetime
    
    model_config = ConfigDict(from_attributes=True)  # بدل orm_mode



class VaultBalanceUpdate(BaseModel):
    """Update vault balance (admin only)"""
    vault_id: UUID
    currency_id: UUID
    new_balance: Decimal = Field(..., ge=0)
    reason: str = Field(..., min_length=10)


# ==================== VAULT TRANSFER SCHEMAS ====================

class VaultTransferBase(BaseModel):
    """Base transfer schema"""
    amount: Decimal = Field(..., gt=0, description="Transfer amount (must be positive)")
    currency_id: UUID
    notes: Optional[str] = Field(None, max_length=500)


class VaultToVaultTransferCreate(VaultTransferBase):
    """Create transfer between vaults"""
    from_vault_id: UUID
    to_vault_id: UUID
    
    @validator('to_vault_id')
    def validate_different_vaults(cls, v, values):
        """Ensure source and destination are different"""
        if 'from_vault_id' in values and v == values['from_vault_id']:
            raise ValueError("Cannot transfer to the same vault")
        return v


class VaultToBranchTransferCreate(VaultTransferBase):
    """Create transfer from vault to branch"""
    vault_id: UUID
    branch_id: UUID


class BranchToVaultTransferCreate(VaultTransferBase):
    """Create transfer from branch to vault"""
    branch_id: UUID
    vault_id: UUID


# ==================== TRANSFER APPROVAL SCHEMAS (FIXED) ====================

class TransferApproval(BaseModel):
    """Approve or reject transfer"""
    approved: bool
    notes: Optional[str] = Field(None, max_length=500)


class VaultTransferApprove(BaseModel):
    """Approve a transfer"""
    transfer_id: UUID
    approval_notes: Optional[str] = Field(None, max_length=500)


class VaultTransferReject(BaseModel):
    """Reject a transfer"""
    transfer_id: UUID
    rejection_reason: str = Field(..., min_length=10, max_length=500)


class VaultTransferComplete(BaseModel):
    """Complete a transfer (mark as received)"""
    transfer_id: UUID
    completion_notes: Optional[str] = Field(None, max_length=500)


class VaultTransferCancel(BaseModel):
    """Cancel a transfer"""
    transfer_id: UUID
    cancellation_reason: str = Field(..., min_length=10, max_length=500)


class VaultTransferResponse(BaseModel):
    """Transfer response"""
    id: UUID
    transfer_number: str
    transfer_type: VaultTransferTypeEnum
    status: VaultTransferStatusEnum
    
    from_vault_id: UUID
    from_vault_code: Optional[str] = None
    
    to_vault_id: Optional[UUID] = None
    to_vault_code: Optional[str] = None
    
    to_branch_id: Optional[UUID] = None
    to_branch_code: Optional[str] = None
    
    currency_id: UUID
    currency_code: Optional[str] = None
    amount: Decimal
    
    initiated_by: UUID
    initiated_by_name: Optional[str] = None
    initiated_at: datetime
    
    approved_by: Optional[UUID] = None
    approved_by_name: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    received_by: Optional[UUID] = None
    received_by_name: Optional[str] = None
    completed_at: Optional[datetime] = None
    
    cancelled_at: Optional[datetime] = None
    
    notes: Optional[str] = None
    rejection_reason: Optional[str] = None
    
    model_config = ConfigDict(
        from_attributes=True,
        use_enum_values=True,
    )

class VaultTransferListResponse(BaseModel):
    """List of transfers"""
    total: int
    transfers: List[VaultTransferResponse]


class TransferQuery(BaseModel):
    """Filter parameters for transfer queries"""
    vault_id: Optional[UUID] = None
    branch_id: Optional[UUID] = None
    status: Optional[VaultTransferStatusEnum] = None
    transfer_type: Optional[VaultTransferTypeEnum] = None
    currency_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    initiated_by: Optional[UUID] = None
    
    skip: int = Field(0, ge=0)
    limit: int = Field(50, ge=1, le=100)


# ==================== RECONCILIATION SCHEMAS ====================

class VaultReconciliationRequest(BaseModel):
    """Request vault reconciliation"""
    vault_id: UUID
    currency_id: Optional[UUID] = None  # If None, reconcile all currencies
    notes: Optional[str] = None


class VaultReconciliationResult(BaseModel):
    """Reconciliation result"""
    vault_id: UUID
    vault_code: str
    currency_id: UUID
    currency_code: str
    
    system_balance: Decimal
    physical_count: Optional[Decimal]
    discrepancy: Optional[Decimal]
    
    last_reconciled_at: Optional[datetime]
    reconciled_by: Optional[str]


class VaultReconciliationReport(BaseModel):
    """Complete reconciliation report"""
    vault_id: UUID
    vault_code: str
    vault_name: str
    reconciliation_date: datetime
    results: List[VaultReconciliationResult]
    total_discrepancies: int
    notes: Optional[str]


# ==================== STATISTICS SCHEMAS ====================

class VaultStatistics(BaseModel):
    """Vault statistics"""
    vault_id: UUID
    vault_code: str
    vault_name: str
    
    total_balance_usd_equivalent: Decimal
    currency_count: int
    
    pending_transfers_in: int
    pending_transfers_out: int
    
    last_transfer_date: Optional[datetime]
    last_reconciliation_date: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)  # بدل orm_mode


class VaultTransferSummary(BaseModel):
    """Transfer summary statistics"""
    period_start: datetime
    period_end: datetime
    
    total_transfers: int
    completed_transfers: int
    pending_transfers: int
    cancelled_transfers: int
    
    total_amount_transferred: Decimal
    average_transfer_amount: Decimal
    
    by_currency: List[dict] = []
    by_type: List[dict] = []
    
    
VaultTransferFilter = TransferQuery 