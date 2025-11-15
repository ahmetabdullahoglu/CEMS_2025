"""
Transaction Models
==================
Complete transaction management system supporting:
- Income transactions (service fees, commissions)
- Expense transactions (rent, salaries, utilities)
- Exchange transactions (currency conversion with rates)
- Transfer transactions (between branches and vaults)

Features:
- Single Table Inheritance for all transaction types
- State machine for status transitions
- Automatic transaction number generation
- Immutable completed transactions
- Full audit trail
- Comprehensive validation
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import uuid4

from sqlalchemy import (
    Column, String, DateTime, Numeric, Boolean, Text,
    ForeignKey, CheckConstraint, Index, event, Enum as SQLEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship, validates, Session
from sqlalchemy.ext.hybrid import hybrid_property

from app.db.base import Base
from app.core.constants import (
    TransactionType,
    TransactionStatus,
    IncomeCategory,
    ExpenseCategory,
)


# ==================== Enumerations ====================


class TransferType(str, Enum):
    """Transfer transaction types"""
    BRANCH_TO_BRANCH = "branch_to_branch"
    VAULT_TO_BRANCH = "vault_to_branch"
    BRANCH_TO_VAULT = "branch_to_vault"


# ==================== Base Transaction Model ====================

class Transaction(Base):
    """
    Base Transaction Model (Single Table Inheritance)
    
    All transaction types inherit from this base model.
    Polymorphic identity determines the specific transaction type.
    """
    
    __tablename__ = "transactions"
    
    # ========== Primary Fields ==========
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    transaction_number = Column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique transaction number: TRX-20250109-00001"
    )
    transaction_type = Column(
        SQLEnum(TransactionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Discriminator for Single Table Inheritance"
    )
    
    # ========== Status & State Management ==========
    status = Column(
        SQLEnum(TransactionStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=TransactionStatus.PENDING,
        index=True
    )
    
    # ========== Core Transaction Data ==========
    amount = Column(
        Numeric(15, 2),
        nullable=False,
        comment="Transaction amount (always positive)"
    )
    
    # ========== Relationships ==========
    branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="User who executed the transaction"
    )
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    currency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=False,
        index=True
    )
    
    # ========== Optional Reference ==========
    reference_number = Column(
        String(100),
        nullable=True,
        comment="External reference number"
    )
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable transaction summary"
    )
    notes = Column(Text, nullable=True)

    # ========== Commission (primarily for Exchange transactions) ==========
    commission_amount = Column(
        Numeric(15, 2),
        nullable=True,
        default=Decimal("0.00"),
        comment="Commission charged (mainly for exchange transactions)"
    )

    # ========== Timestamps ==========
    transaction_date = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        index=True
    )
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # ========== Cancellation Info ==========
    cancelled_at = Column(DateTime(timezone=True), nullable=True)
    cancelled_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    cancellation_reason = Column(Text, nullable=True)
    
    # ========== Audit Trail ==========
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )
    
    # ========== Polymorphic Configuration ==========
    __mapper_args__ = {
        "polymorphic_identity": "transaction",
        "polymorphic_on": transaction_type,
        "with_polymorphic": "*"
    }
    
    # ========== SQLAlchemy Relationships ==========
    branch = relationship("Branch", foreign_keys=[branch_id], back_populates="transactions")
    user = relationship("User", foreign_keys=[user_id], back_populates="transactions")
    customer = relationship("Customer", foreign_keys=[customer_id])
    currency = relationship("Currency", foreign_keys=[currency_id])
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id], overlaps="cancelled_transactions")
    
    # ========== Constraints ==========
    __table_args__ = (
        CheckConstraint("amount > 0", name="check_amount_positive"),
        CheckConstraint(
            "(status != 'cancelled') OR (cancelled_at IS NOT NULL AND cancelled_by_id IS NOT NULL)",
            name="check_cancellation_data"
        ),
        CheckConstraint(
            "(status != 'completed') OR (completed_at IS NOT NULL)",
            name="check_completion_data"
        ),
        Index("idx_transaction_date_status", "transaction_date", "status"),
        Index("idx_branch_currency_date", "branch_id", "currency_id", "transaction_date"),
    )
    
    # ========== Properties ==========
    @hybrid_property
    def is_completed(self) -> bool:
        """Check if transaction is completed"""
        return self.status == TransactionStatus.COMPLETED
    
    @hybrid_property
    def is_cancellable(self) -> bool:
        """Check if transaction can be cancelled"""
        return self.status == TransactionStatus.PENDING
    
    @hybrid_property
    def is_mutable(self) -> bool:
        """Check if transaction can be modified"""
        return self.status == TransactionStatus.PENDING

    # ========== Compatibility Properties (for report service) ==========
    @property
    def source_amount(self):
        """Compatibility property: returns from_amount for exchange, amount for others"""
        if self.transaction_type == TransactionType.EXCHANGE:
            return getattr(self, 'from_amount', None) or self.amount
        return self.amount

    @property
    def target_amount(self):
        """Compatibility property: returns to_amount for exchange transactions"""
        if self.transaction_type == TransactionType.EXCHANGE:
            return getattr(self, 'to_amount', None)
        return None

    @property
    def source_currency(self):
        """Compatibility property: returns from_currency for exchange, currency for others"""
        if self.transaction_type == TransactionType.EXCHANGE:
            return getattr(self, 'from_currency', None) or self.currency
        return self.currency

    @property
    def target_currency(self):
        """Compatibility property: returns to_currency for exchange transactions"""
        if self.transaction_type == TransactionType.EXCHANGE:
            return getattr(self, 'to_currency', None)
        return None

    @property
    def source_currency_code(self):
        """Compatibility property: returns currency code"""
        curr = self.source_currency
        return curr.code if curr else None

    @property
    def exchange_rate(self):
        """Compatibility property: returns exchange_rate_used for exchange transactions"""
        if self.transaction_type == TransactionType.EXCHANGE:
            return getattr(self, 'exchange_rate_used', None)
        return None

    @property
    def commission(self):
        """Alias for commission_amount for backward compatibility"""
        return self.commission_amount or Decimal("0.00")

    # ========== Validation ==========
    @validates("status")
    def validate_status_transition(self, key, new_status):
        """Validate status transitions according to state machine"""
        if not self.status:  # New transaction
            return new_status
        
        # Define valid transitions
        valid_transitions = {
            TransactionStatus.PENDING: [
                TransactionStatus.IN_TRANSIT,
                TransactionStatus.COMPLETED,
                TransactionStatus.CANCELLED,
                TransactionStatus.FAILED
            ],
            TransactionStatus.IN_TRANSIT: [
                TransactionStatus.COMPLETED,
                TransactionStatus.FAILED
            ],
            TransactionStatus.COMPLETED: [],  # Immutable
            TransactionStatus.CANCELLED: [],  # Immutable
            TransactionStatus.FAILED: [TransactionStatus.PENDING]  # Can retry
        }
        
        current_status = TransactionStatus(self.status)
        new_status_enum = TransactionStatus(new_status)
        
        if new_status_enum not in valid_transitions.get(current_status, []):
            raise ValueError(
                f"Invalid status transition: {current_status.value} -> {new_status_enum.value}"
            )
        
        return new_status
    
    # ========== Business Methods ==========
    def complete(self, user_id: UUID) -> None:
        """Mark transaction as completed"""
        if not self.is_cancellable:
            raise ValueError("Only pending transactions can be completed")
        
        self.status = TransactionStatus.COMPLETED
        self.completed_at = datetime.utcnow()
    
    def cancel(self, user_id: UUID, reason: str) -> None:
        """Cancel transaction"""
        if not self.is_cancellable:
            raise ValueError("Only pending transactions can be cancelled")
        
        self.status = TransactionStatus.CANCELLED
        self.cancelled_at = datetime.utcnow()
        self.cancelled_by_id = user_id
        self.cancellation_reason = reason
    
    def fail(self, reason: str) -> None:
        """Mark transaction as failed"""
        if self.status != TransactionStatus.PENDING:
            raise ValueError("Only pending transactions can be marked as failed")
        
        self.status = TransactionStatus.FAILED
        self.notes = f"{self.notes or ''}\nFAILED: {reason}"
    
    def __repr__(self):
        return (
            f"<Transaction(number='{self.transaction_number}', "
            f"type='{self.transaction_type.value}', "
            f"status='{self.status.value}', "
            f"amount={self.amount})>"
        )


# ==================== Income Transaction ====================

class IncomeTransaction(Transaction):
    """
    Income Transaction
    
    Represents money received by the branch (service fees, commissions, etc.)
    """
    
    __tablename__ = None  # Use parent table
    
    # ========== Income Specific Fields ==========
    income_category = Column(
        SQLEnum(IncomeCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Category of income"
    )
    income_source = Column(
        String(200),
        nullable=True,
        comment="Description of income source"
    )
    
    # ========== Polymorphic Configuration ==========
    __mapper_args__ = {
        "polymorphic_identity": "income"  # Must match enum value exactly
    }
    
    def __repr__(self):
        return (
            f"<IncomeTransaction(number='{self.transaction_number}', "
            f"category='{self.income_category.value if self.income_category else None}', "
            f"amount={self.amount})>"
        )


# ==================== Expense Transaction ====================

class ExpenseTransaction(Transaction):
    """
    Expense Transaction
    
    Represents money paid out by the branch (rent, salaries, utilities, etc.)
    May require approval based on amount or category.
    """
    
    __tablename__ = None  # Use parent table
    
    # ========== Expense Specific Fields ==========
    expense_category = Column(
        SQLEnum(ExpenseCategory, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Category of expense"
    )
    expense_to = Column(
        String(200),
        nullable=True,
        comment="Payee name"
    )
    
    # ========== Approval Workflow ==========
    approval_required = Column(
        Boolean,
        nullable=False,
        default=False,
        comment="Whether this expense requires approval"
    )
    approved_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    approved_at = Column(DateTime(timezone=True), nullable=True)
    
    # ========== Polymorphic Configuration ==========
    __mapper_args__ = {
        "polymorphic_identity": "expense"  # Must match enum value exactly
    }
    
    # ========== Relationships ==========
    approved_by = relationship("User", foreign_keys=[approved_by_id], overlaps="approved_expenses")
    
    # ========== Properties ==========
    @hybrid_property
    def is_approved(self) -> bool:
        """Check if expense is approved"""
        return not self.approval_required or (
            self.approved_by_id is not None and self.approved_at is not None
        )
    
    # ========== Business Methods ==========
    def approve(self, approver_id: UUID) -> None:
        """Approve expense transaction"""
        if not self.approval_required:
            raise ValueError("This expense does not require approval")
        
        if self.approved_by_id:
            raise ValueError("Expense already approved")
        
        self.approved_by_id = approver_id
        self.approved_at = datetime.utcnow()
    
    def __repr__(self):
        return (
            f"<ExpenseTransaction(number='{self.transaction_number}', "
            f"category='{self.expense_category.value if self.expense_category else None}', "
            f"to='{self.expense_to}', amount={self.amount})>"
        )


# ==================== Exchange Transaction ====================

class ExchangeTransaction(Transaction):
    """
    Exchange Transaction
    
    Currency conversion with exchange rates and commission.
    Records the actual rate used at transaction time (snapshot).
    """
    
    __tablename__ = None  # Use parent table
    
    # ========== Exchange Specific Fields ==========
    from_currency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Source currency"
    )
    to_currency_id = Column(
        UUID(as_uuid=True),
        ForeignKey("currencies.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Target currency"
    )
    
    from_amount = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Amount in source currency"
    )
    to_amount = Column(
        Numeric(15, 2),
        nullable=True,
        comment="Amount in target currency"
    )
    
    # ========== Rate Snapshot ==========
    exchange_rate_used = Column(
        Numeric(12, 6),
        nullable=True,
        comment="Actual exchange rate used (snapshot at transaction time)"
    )

    # ========== Commission Percentage (for Exchange) ==========
    commission_percentage = Column(
        Numeric(5, 2),
        nullable=True,
        default=Decimal("0.00"),
        comment="Commission percentage applied"
    )

    # ========== Polymorphic Configuration ==========
    __mapper_args__ = {
        "polymorphic_identity": "exchange"  # Must match enum value exactly
    }
    
    # ========== Relationships ==========
    from_currency = relationship("Currency", foreign_keys=[from_currency_id], overlaps="exchange_from")
    to_currency = relationship("Currency", foreign_keys=[to_currency_id], overlaps="exchange_to")
    
    # ========== Properties ==========
    @hybrid_property
    def effective_rate(self) -> Decimal:
        """Calculate effective rate including commission"""
        if not self.from_amount or self.from_amount == 0:
            return Decimal("0")
        return self.to_amount / self.from_amount
    
    @hybrid_property
    def total_cost(self) -> Decimal:
        """Total cost including commission"""
        return self.from_amount + (self.commission_amount or Decimal("0.00"))
    
    # ========== Business Methods ==========
    def calculate_commission(self, rate: Decimal) -> Decimal:
        """Calculate commission based on percentage"""
        if not self.commission_percentage:
            return Decimal("0.00")
        
        return (self.from_amount * self.commission_percentage / 100).quantize(
            Decimal("0.01")
        )
    
    def __repr__(self):
        return (
            f"<ExchangeTransaction(number='{self.transaction_number}', "
            f"from={self.from_amount}, to={self.to_amount}, "
            f"rate={self.exchange_rate_used})>"
        )


# ==================== Transfer Transaction ====================

class TransferTransaction(Transaction):
    """
    Transfer Transaction
    
    Money transfer between branches or between branch and vault.
    Requires sender and receiver confirmation.
    """
    
    __tablename__ = None  # Use parent table
    
    # ========== Transfer Specific Fields ==========
    from_branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Source branch"
    )
    to_branch_id = Column(
        UUID(as_uuid=True),
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=True,
        comment="Destination branch"
    )
    
    transfer_type = Column(
        SQLEnum(TransferType, values_callable=lambda x: [e.value for e in x]),
        nullable=True,
        comment="Type of transfer operation"
    )
    
    # ========== Receiver Info ==========
    received_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who received the transfer"
    )
    received_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the transfer was received"
    )
    
    # ========== Polymorphic Configuration ==========
    __mapper_args__ = {
        "polymorphic_identity": "transfer"  # Must match enum value exactly
    }
    
    # ========== Relationships ==========
    from_branch = relationship("Branch", foreign_keys=[from_branch_id])
    to_branch = relationship("Branch", foreign_keys=[to_branch_id])
    received_by = relationship("User", foreign_keys=[received_by_id], overlaps="received_transfers")
    
    # ========== Properties ==========
    @hybrid_property
    def is_received(self) -> bool:
        """Check if transfer has been received"""
        return self.received_by_id is not None and self.received_at is not None
    
    @hybrid_property
    def is_pending_receipt(self) -> bool:
        """Check if transfer is waiting to be received"""
        return (
            self.status == TransactionStatus.COMPLETED and
            not self.is_received
        )
    
    # ========== Business Methods ==========
    def mark_as_received(self, receiver_id: UUID) -> None:
        """Mark transfer as received"""
        if not self.is_completed:
            raise ValueError("Transfer must be completed before it can be received")
        
        if self.is_received:
            raise ValueError("Transfer already received")
        
        self.received_by_id = receiver_id
        self.received_at = datetime.utcnow()
    
    def __repr__(self):
        return (
            f"<TransferTransaction(number='{self.transaction_number}', "
            f"type='{self.transfer_type.value if self.transfer_type else None}', "
            f"amount={self.amount})>"
        )


# ==================== Transaction Number Generator ====================

class TransactionNumberGenerator:
    """
    Transaction Number Generator

    Generates unique transaction numbers in format: TRX-YYYYMMDD-NNNNN
    Thread-safe and database-backed.
    """

    @staticmethod
    async def generate(session: 'AsyncSession', transaction_date: datetime = None) -> str:
        """
        Generate unique transaction number (async)

        Args:
            session: Async database session
            transaction_date: Transaction date (default: now)

        Returns:
            Unique transaction number (e.g., TRX-20250109-00001)
        """
        from sqlalchemy import select

        if transaction_date is None:
            transaction_date = datetime.utcnow()

        date_str = transaction_date.strftime("%Y%m%d")
        prefix = f"TRX-{date_str}-"

        # Get the last transaction number for today using async query
        stmt = (
            select(Transaction)
            .where(Transaction.transaction_number.like(f"{prefix}%"))
            .order_by(Transaction.transaction_number.desc())
            .limit(1)
        )
        result = await session.execute(stmt)
        last_transaction = result.scalar_one_or_none()

        if last_transaction:
            # Extract sequence number and increment
            last_number = int(last_transaction.transaction_number.split("-")[-1])
            next_number = last_number + 1
        else:
            next_number = 1

        return f"{prefix}{next_number:05d}"


# ==================== Events & Triggers ====================

@event.listens_for(Transaction, "before_insert")
def generate_transaction_number(mapper, connection, target):
    """Generate transaction number before insert if not provided"""
    if not target.transaction_number:
        # Note: This requires the session to be available
        # In practice, this should be handled by the service layer
        pass


@event.listens_for(Transaction, "before_update")
def prevent_completed_modification(mapper, connection, target):
    """Prevent modification of completed transactions"""
    if target.status == TransactionStatus.COMPLETED:
        # Get the original object state
        state = target._sa_instance_state
        if state.has_identity and not state.pending:
            # Check if any fields besides allowed ones are being modified
            allowed_fields = {"updated_at", "notes"}
            history = state.get_history("status", True)
            
            # If status is already completed and we're trying to modify other fields
            if history.unchanged and history.unchanged[0] == TransactionStatus.COMPLETED:
                for attr in state.attrs:
                    if attr.key not in allowed_fields and attr.history.has_changes():
                        raise ValueError(
                            f"Cannot modify completed transaction: {target.transaction_number}"
                        )


# ==================== Indexes for Performance ====================

# Additional indexes are created via __table_args__ in each model
# Key indexes:
# - transaction_number (unique, for lookups)
# - transaction_date + status (for queries)
# - branch_id + currency_id + transaction_date (for balance calculations)
# - customer_id (for customer history)
# - user_id (for user activity tracking)