"""
Transaction Pydantic Schemas
=============================
Request and response schemas for all transaction types:
- Income transactions
- Expense transactions
- Exchange transactions
- Transfer transactions

Features:
- Input validation
- Type safety
- Comprehensive examples
- Status-specific responses
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict

from app.core.constants import (
    TransactionType,
    TransactionStatus,
    IncomeCategory,
    ExpenseCategory,
)
from app.db.models.transaction import TransferType


# ==================== Enumerations (Mirror from Models/Core) ====================

TransactionTypeEnum = TransactionType
TransactionStatusEnum = TransactionStatus
IncomeCategoryEnum = IncomeCategory
ExpenseCategoryEnum = ExpenseCategory
TransferTypeEnum = TransferType


# ==================== Base Transaction Schemas ====================

class TransactionBase(BaseModel):
    """Base transaction schema with common fields"""
    
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Transaction amount (must be positive)"
    )
    currency_id: UUID = Field(..., description="Currency ID")
    branch_id: UUID = Field(..., description="Branch ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID (optional)")
    reference_number: Optional[str] = Field(
        None,
        max_length=100,
        description="External reference number"
    )
    description: Optional[str] = Field(
        None,
        description="Human-readable transaction summary"
    )
    notes: Optional[str] = Field(None, description="Transaction notes")
    transaction_date: Optional[datetime] = Field(
        None,
        description="Transaction date (defaults to now)"
    )
    
    @field_validator("amount")
    @classmethod
    def validate_amount(cls, v):
        """Validate amount precision"""
        if v <= 0:
            raise ValueError("Amount must be positive")
        # Ensure 2 decimal places
        return Decimal(str(v)).quantize(Decimal("0.01"))


# ==================== Income Transaction Schemas ====================

class IncomeTransactionCreate(TransactionBase):
    """Schema for creating income transaction"""
    
    income_category: IncomeCategoryEnum = Field(
        ...,
        description="Income category"
    )
    income_source: Optional[str] = Field(
        None,
        max_length=200,
        description="Description of income source"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 150.50,
                "currency_id": "123e4567-e89b-12d3-a456-426614174000",
                "branch_id": "223e4567-e89b-12d3-a456-426614174001",
                "customer_id": "323e4567-e89b-12d3-a456-426614174002",
                "income_category": "service_fee",
                "income_source": "Money transfer service fee",
                "reference_number": "REF-2025-001",
                "notes": "Standard service fee for international transfer"
            }
        }
    )


class IncomeTransactionResponse(TransactionBase):
    """Schema for income transaction response"""

    id: UUID
    transaction_number: str
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum
    income_category: IncomeCategoryEnum
    income_source: Optional[str] = None
    user_id: UUID
    branch_name: Optional[str] = Field(None, description="Branch name")
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_id: Optional[UUID] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ==================== Expense Transaction Schemas ====================

class ExpenseTransactionCreate(TransactionBase):
    """Schema for creating expense transaction"""
    
    expense_category: ExpenseCategoryEnum = Field(
        ...,
        description="Expense category"
    )
    expense_to: str = Field(
        ...,
        max_length=200,
        description="Payee name"
    )
    approval_required: bool = Field(
        False,
        description="Whether approval is required"
    )
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "amount": 5000.00,
                "currency_id": "123e4567-e89b-12d3-a456-426614174000",
                "branch_id": "223e4567-e89b-12d3-a456-426614174001",
                "expense_category": "rent",
                "expense_to": "Property Owner LLC",
                "approval_required": True,
                "reference_number": "RENT-JAN-2025",
                "notes": "January 2025 monthly rent payment"
            }
        }
    )


class ExpenseTransactionResponse(TransactionBase):
    """Schema for expense transaction response"""

    id: UUID
    transaction_number: str
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum
    expense_category: ExpenseCategoryEnum
    expense_to: str
    approval_required: bool
    approved_by_id: Optional[UUID] = None
    approved_at: Optional[datetime] = None
    user_id: UUID
    branch_name: Optional[str] = Field(None, description="Branch name")
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_id: Optional[UUID] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    # Computed field
    is_approved: bool = Field(default=False, description="Approval status")

    model_config = ConfigDict(from_attributes=True)


class ExpenseApprovalRequest(BaseModel):
    """Schema for approving expense"""

    approval_notes: Optional[str] = Field(None, description="Approval notes")

    # Backwards compatibility alias
    @property
    def notes(self) -> Optional[str]:
        return self.approval_notes


# ==================== Exchange Transaction Schemas ====================

class ExchangeTransactionCreate(BaseModel):
    """Schema for creating exchange transaction"""
    
    branch_id: UUID = Field(..., description="Branch ID")
    customer_id: Optional[UUID] = Field(None, description="Customer ID")
    
    from_currency_id: UUID = Field(..., description="Source currency ID")
    to_currency_id: UUID = Field(..., description="Target currency ID")
    from_amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Amount in source currency"
    )
    
    # Optional: can be calculated
    exchange_rate: Optional[Decimal] = Field(
        None,
        gt=0,
        description="Exchange rate (if not provided, uses current rate)"
    )
    commission_percentage: Optional[Decimal] = Field(
        None,
        ge=0,
        le=100,
        description="Commission percentage (if not provided, uses default)"
    )
    
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(
        None,
        description="Human-readable transaction summary",
    )
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None
    
    @model_validator(mode='after')
    def validate_currencies(self):
        """Ensure different currencies"""
        if self.from_currency_id == self.to_currency_id:
            raise ValueError("Source and target currencies must be different")
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "branch_id": "223e4567-e89b-12d3-a456-426614174001",
                "customer_id": "323e4567-e89b-12d3-a456-426614174002",
                "from_currency_id": "423e4567-e89b-12d3-a456-426614174003",
                "to_currency_id": "523e4567-e89b-12d3-a456-426614174004",
                "from_amount": 1000.00,
                "exchange_rate": 3.75,
                "commission_percentage": 1.5,
                "reference_number": "EXC-2025-001",
                "description": "USD to SAR exchange for customer",
                "notes": "Walk-in transaction"
            }
        }
    )


class ExchangeTransactionResponse(BaseModel):
    """Schema for exchange transaction response"""

    id: UUID
    transaction_number: str
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum

    branch_id: UUID
    branch_name: Optional[str] = Field(None, description="Branch name")
    customer_id: Optional[UUID]
    user_id: UUID

    from_currency_id: UUID
    to_currency_id: UUID
    from_amount: Decimal
    to_amount: Decimal

    exchange_rate_used: Decimal
    commission_amount: Decimal
    commission_percentage: Decimal

    # Computed fields
    effective_rate: Decimal = Field(description="Effective rate with commission")
    total_cost: Decimal = Field(description="Total cost including commission")

    reference_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_id: Optional[UUID] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExchangeCalculationRequest(BaseModel):
    """Schema for exchange rate calculation"""
    
    from_currency_id: UUID
    to_currency_id: UUID
    from_amount: Decimal = Field(..., gt=0)
    commission_percentage: Optional[Decimal] = Field(None, ge=0, le=100)


class ExchangeCalculationResponse(BaseModel):
    """Schema for exchange calculation result"""
    
    from_currency_id: UUID
    from_currency_code: str
    to_currency_id: UUID
    to_currency_code: str
    from_amount: Decimal
    to_amount: Decimal
    exchange_rate: Decimal
    commission_percentage: Decimal
    commission_amount: Decimal
    total_cost: Decimal
    effective_rate: Decimal


# ==================== Transfer Transaction Schemas ====================

class TransferTransactionCreate(BaseModel):
    """Schema for creating transfer transaction"""
    
    from_branch_id: UUID = Field(..., description="Source branch ID")
    to_branch_id: UUID = Field(..., description="Destination branch ID")
    amount: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        description="Transfer amount"
    )
    currency_id: UUID = Field(..., description="Currency ID")
    transfer_type: TransferTypeEnum = Field(
        ...,
        description="Transfer type"
    )
    
    reference_number: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = Field(
        None,
        description="Human-readable transaction summary",
    )
    notes: Optional[str] = None
    transaction_date: Optional[datetime] = None
    
    @model_validator(mode='after')
    def validate_branches(self):
        """Ensure different branches"""
        if self.from_branch_id == self.to_branch_id:
            raise ValueError("Source and destination branches must be different")
        return self
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "from_branch_id": "223e4567-e89b-12d3-a456-426614174001",
                "to_branch_id": "623e4567-e89b-12d3-a456-426614174005",
                "amount": 10000.00,
                "currency_id": "423e4567-e89b-12d3-a456-426614174003",
                "transfer_type": "branch_to_branch",
                "reference_number": "TRF-2025-001",
                "description": "Monthly cash allocation transfer",
                "notes": "Courier drop"
            }
        }
    )


class TransferTransactionResponse(BaseModel):
    """Schema for transfer transaction response"""

    id: UUID
    transaction_number: str
    transaction_type: TransactionTypeEnum
    status: TransactionStatusEnum

    from_branch_id: UUID
    from_branch_name: Optional[str] = Field(None, description="Source branch name")
    to_branch_id: UUID
    to_branch_name: Optional[str] = Field(None, description="Destination branch name")
    amount: Decimal
    currency_id: UUID
    transfer_type: TransferTypeEnum

    user_id: UUID  # Who initiated
    received_by_id: Optional[UUID] = None  # Who received
    received_at: Optional[datetime] = None

    # Computed fields
    is_received: bool = Field(default=False, description="Reception status")
    is_pending_receipt: bool = Field(
        default=False,
        description="Waiting for receipt confirmation"
    )

    reference_number: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    transaction_date: datetime
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    cancelled_by_id: Optional[UUID] = None
    cancellation_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransferReceiptRequest(BaseModel):
    """Schema for confirming transfer receipt"""

    receipt_notes: Optional[str] = Field(None, description="Receipt notes")

    # Backwards compatibility alias
    @property
    def notes(self) -> Optional[str]:
        return self.receipt_notes


# ==================== Common Transaction Operations ====================

class TransactionCancelRequest(BaseModel):
    """Schema for cancelling transaction"""

    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Cancellation reason (required)"
    )

    # Backwards compatibility alias
    @property
    def cancellation_reason(self) -> str:
        return self.reason


class TransactionStatusUpdate(BaseModel):
    """Schema for updating transaction status"""
    
    status: TransactionStatusEnum
    reason: Optional[str] = Field(None, description="Reason for status change")


# ==================== List & Filter Schemas ====================

class TransactionFilter(BaseModel):
    """Schema for filtering transactions"""

    branch_id: Optional[UUID] = None
    customer_id: Optional[UUID] = None
    currency_id: Optional[UUID] = None
    from_currency_id: Optional[UUID] = None
    to_currency_id: Optional[UUID] = None
    from_branch_id: Optional[UUID] = None
    to_branch_id: Optional[UUID] = None
    transaction_type: Optional[TransactionTypeEnum] = None
    status: Optional[TransactionStatusEnum] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    amount_min: Optional[Decimal] = Field(None, ge=0)
    amount_max: Optional[Decimal] = Field(None, ge=0)
    
    # Pagination
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "branch_id": "223e4567-e89b-12d3-a456-426614174001",
                "transaction_type": "exchange",
                "status": "completed",
                "date_from": "2025-01-01T00:00:00Z",
                "date_to": "2025-01-31T23:59:59Z",
                "amount_min": 100.00,
                "amount_max": 10000.00,
                "skip": 0,
                "limit": 50
            }
        }
    )


class TransactionListResponse(BaseModel):
    """Schema for transaction list response"""
    
    total: int
    transactions: List[
        IncomeTransactionResponse |
        ExpenseTransactionResponse |
        ExchangeTransactionResponse |
        TransferTransactionResponse
    ]
    
    model_config = ConfigDict(from_attributes=True)


# ==================== Statistics & Summary ====================

class TransactionSummary(BaseModel):
    """Summary statistics for transactions"""
    
    total_count: int
    total_amount: Decimal
    by_status: dict[str, int]
    by_type: dict[str, int]
    date_range: dict[str, datetime]


class DailyTransactionSummary(BaseModel):
    """Daily transaction summary"""
    
    date: datetime
    total_transactions: int
    total_income: Decimal
    total_expense: Decimal
    total_exchange: Decimal
    total_transfer: Decimal
    net_amount: Decimal


# ==================== Response Wrappers ====================

class TransactionSuccessResponse(BaseModel):
    """Success response wrapper"""
    
    success: bool = True
    message: str
    data: (
        IncomeTransactionResponse |
        ExpenseTransactionResponse |
        ExchangeTransactionResponse |
        TransferTransactionResponse
    )


class TransactionErrorResponse(BaseModel):
    """Error response wrapper"""
    
    success: bool = False
    error: str
    details: Optional[dict] = None