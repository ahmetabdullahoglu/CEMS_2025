"""
Branch Database Models
Handles branch management, balances, and alerts
Phase 4, Component 4.1
"""

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Boolean, DateTime, ForeignKey, 
    CheckConstraint, UniqueConstraint, Numeric, Enum, Index, text
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
import uuid

from app.db.base_class import BaseModel, UserTrackingMixin


# ==================== Enums ====================

class RegionEnum(str, PyEnum):
    """Regions for branch locations in Turkey"""
    ISTANBUL_EUROPEAN = "Istanbul_European"
    ISTANBUL_ASIAN = "Istanbul_Asian"
    ANKARA = "Ankara"
    IZMIR = "Izmir"
    BURSA = "Bursa"
    ANTALYA = "Antalya"
    ADANA = "Adana"
    GAZIANTEP = "Gaziantep"
    KONYA = "Konya"
    OTHER = "Other"


class BalanceAlertType(str, PyEnum):
    """Types of balance alerts"""
    LOW_BALANCE = "low_balance"
    HIGH_BALANCE = "high_balance"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RECONCILIATION_NEEDED = "reconciliation_needed"
    THRESHOLD_WARNING = "threshold_warning"


class AlertSeverity(str, PyEnum):
    """Severity levels for alerts"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class BalanceChangeType(str, PyEnum):
    """Types of balance changes"""
    TRANSACTION = "transaction"
    ADJUSTMENT = "adjustment"
    TRANSFER_IN = "transfer_in"
    TRANSFER_OUT = "transfer_out"
    RECONCILIATION = "reconciliation"
    INITIAL_BALANCE = "initial_balance"


# ==================== Models ====================

class Branch(BaseModel, UserTrackingMixin):
    """
    Branch model
    Represents physical branch locations
    """
    
    __tablename__ = "branches"
    
    # Basic Information
    code = Column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique branch code (BR001, BR002, etc.)"
    )
    
    name_en = Column(
        String(200),
        nullable=False,
        comment="Branch name in English"
    )
    
    name_ar = Column(
        String(200),
        nullable=False,
        comment="Branch name in Arabic"
    )
    
    # Location Details
    region = Column(
        Enum(
            RegionEnum,
            values_callable=lambda obj: [e.value for e in obj],  # استخدم القيمة وليس الاسم
            name="regionenum",
            create_type=False  # الـ type موجود في قاعدة البيانات
        ),
        nullable=False,
        index=True,
        comment="Geographic region of the branch"
    )
    
    address = Column(
        String(500),
        nullable=False,
        comment="Full address of the branch"
    )
    
    city = Column(
        String(100),
        nullable=False,
        index=True,
        comment="City where branch is located"
    )
    
    # Contact Information
    phone = Column(
        String(20),
        nullable=False,
        comment="Branch phone number"
    )
    
    email = Column(
        String(100),
        nullable=True,
        comment="Branch email address"
    )
    
    # Management
    manager_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="Branch manager (User)"
    )
    
    # Branch Type
    is_main_branch = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether this is the main branch (only one allowed)"
    )
    
    # Operational Dates
    opening_balance_date = Column(
        DateTime,
        nullable=True,
        comment="Date when branch started operations"
    )
    
    # Relationships
    manager = relationship(
        "User",
        foreign_keys=[manager_id],
        backref="managed_branches"
    )
    
    balances = relationship(
        "BranchBalance",
        back_populates="branch",
        cascade="all, delete-orphan"
    )
    
    balance_history = relationship(
        "BranchBalanceHistory",
        back_populates="branch",
        cascade="all, delete-orphan"
    )
    
    alerts = relationship(
        "BranchAlert",
        back_populates="branch",
        cascade="all, delete-orphan"
    )
    
    transactions = relationship(
        "Transaction",
        back_populates="branch",
        foreign_keys="[Transaction.branch_id]"
    )
    customers = relationship(
        "Customer",
        back_populates="branch"
    )
    vaults = relationship(
        "Vault",
        back_populates="branch",
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint("code ~ '^BR[0-9]{3,6}$'", name="branch_code_format_check"),
        CheckConstraint("LENGTH(phone) >= 10", name="branch_phone_length_check"),
        Index('idx_branch_region_active', 'region', 'is_active'),
        Index('idx_branch_main', 'is_main_branch', 'is_active'),
    )

    @property
    def name(self) -> str:
        """Backward compatibility property - returns English name by default"""
        return self.name_en

    def __repr__(self) -> str:
        return f"<Branch(code='{self.code}', name='{self.name_en}')>"


class BranchBalance(BaseModel):
    """
    Branch Balance model
    Tracks currency balances for each branch
    """
    
    __tablename__ = "branch_balances"
    
    # Foreign Keys
    branch_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('branches.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to branch"
    )
    
    currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Reference to currency"
    )
    
    # Balance Information
    balance = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=0,
        comment="Current balance for this currency"
    )
    
    reserved_balance = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=0,
        comment="Balance reserved for pending transactions"
    )
    
    # Note: available_balance is computed (balance - reserved_balance)
    # We'll use a hybrid_property or computed column for this
    
    # Thresholds for Alerts
    minimum_threshold = Column(
        Numeric(precision=15, scale=2),
        nullable=True,
        comment="Minimum balance threshold (triggers low balance alert)"
    )
    
    maximum_threshold = Column(
        Numeric(precision=15, scale=2),
        nullable=True,
        comment="Maximum balance threshold (triggers high balance alert)"
    )
    
    # Audit Information
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        comment="Last time balance was updated"
    )
    
    last_reconciled_at = Column(
        DateTime,
        nullable=True,
        comment="Last time balance was reconciled"
    )
    
    last_reconciled_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who performed last reconciliation"
    )
    
    # Relationships
    branch = relationship("Branch", back_populates="balances")
    currency = relationship("Currency", backref="branch_balances")
    reconciled_by_user = relationship("User", foreign_keys=[last_reconciled_by])
    
    # # Add this relationship
    # transactions = relationship(
    #     "Transaction",
    #     back_populates="branch",
    #     foreign_keys="Transaction.branch_id",
    #     cascade="all, delete-orphan"
    # )
    # Table constraints
    __table_args__ = (
        UniqueConstraint('branch_id', 'currency_id', name='uq_branch_currency'),
        CheckConstraint('balance >= 0', name='branch_balance_positive_check'),
        CheckConstraint('reserved_balance >= 0', name='reserved_balance_positive_check'),
        CheckConstraint('reserved_balance <= balance', name='reserved_not_exceeding_balance'),
        CheckConstraint(
            'minimum_threshold IS NULL OR minimum_threshold >= 0',
            name='min_threshold_positive_check'
        ),
        CheckConstraint(
            'maximum_threshold IS NULL OR maximum_threshold > 0',
            name='max_threshold_positive_check'
        ),
        Index('idx_branch_balance_lookup', 'branch_id', 'currency_id'),
        Index('idx_branch_balance_thresholds', 'branch_id', 'balance', 'minimum_threshold'),
    )
    
    @property
    def available_balance(self) -> Decimal:
        """Calculate available balance (balance - reserved)"""
        return self.balance - self.reserved_balance
    
    def is_below_minimum(self) -> bool:
        """Check if balance is below minimum threshold"""
        if self.minimum_threshold is None:
            return False
        return self.balance < self.minimum_threshold
    
    def is_above_maximum(self) -> bool:
        """Check if balance is above maximum threshold"""
        if self.maximum_threshold is None:
            return False
        return self.balance > self.maximum_threshold
    
    def __repr__(self) -> str:
        return f"<BranchBalance(branch_id={self.branch_id}, currency_id={self.currency_id}, balance={self.balance})>"


class BranchBalanceHistory(BaseModel):
    """
    Branch Balance History model
    Tracks all balance changes for audit trail
    """
    
    __tablename__ = "branch_balance_history"
    
    # Foreign Keys
    branch_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('branches.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to branch"
    )
    
    currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Reference to currency"
    )
    
    # Change Information
    change_type = Column(
        Enum(BalanceChangeType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of balance change"
    )
    
    amount = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        comment="Amount changed (positive or negative)"
    )
    
    balance_before = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        comment="Balance before the change"
    )
    
    balance_after = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        comment="Balance after the change"
    )
    
    # Reference Information
    reference_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Reference to related transaction or transfer"
    )
    
    reference_type = Column(
        String(50),
        nullable=True,
        comment="Type of reference (transaction, transfer, etc.)"
    )
    
    # Audit
    performed_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who performed the change"
    )
    
    performed_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the change occurred"
    )
    
    notes = Column(
        String(500),
        nullable=True,
        comment="Additional notes about the change"
    )
    
    # Relationships
    branch = relationship("Branch", back_populates="balance_history")
    currency = relationship("Currency", backref="branch_balance_history")
    user = relationship("User", foreign_keys=[performed_by])
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('balance_before >= 0', name='history_balance_before_positive'),
        CheckConstraint('balance_after >= 0', name='history_balance_after_positive'),
        Index('idx_balance_history_lookup', 'branch_id', 'currency_id', 'performed_at'),
        Index('idx_balance_history_reference', 'reference_id', 'reference_type'),
    )
    
    def __repr__(self) -> str:
        return f"<BranchBalanceHistory(branch_id={self.branch_id}, amount={self.amount}, type={self.change_type})>"


class BranchAlert(BaseModel):
    """
    Branch Alert model
    Manages alerts for branches (low balance, suspicious activity, etc.)
    """
    
    __tablename__ = "branch_alerts"
    
    # Foreign Keys
    branch_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('branches.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to branch"
    )
    
    currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
        comment="Reference to currency (if alert is currency-specific)"
    )
    
    # Alert Information
    alert_type = Column(
        Enum(BalanceAlertType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of alert"
    )

    severity = Column(
        Enum(AlertSeverity, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=AlertSeverity.INFO,
        index=True,
        comment="Alert severity level"
    )
    
    title = Column(
        String(200),
        nullable=False,
        comment="Alert title"
    )
    
    message = Column(
        String(1000),
        nullable=False,
        comment="Detailed alert message"
    )
    
    # Alert Data (JSON for flexible storage)
    alert_data = Column(
        String,  # Will store JSON string
        nullable=True,
        comment="Additional alert data as JSON"
    )
    
    # Alert Status
    is_resolved = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Whether alert has been resolved"
    )
    
    # Timestamps
    triggered_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the alert was triggered"
    )
    
    resolved_at = Column(
        DateTime,
        nullable=True,
        comment="When the alert was resolved"
    )
    
    resolved_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who resolved the alert"
    )
    
    resolution_notes = Column(
        String(500),
        nullable=True,
        comment="Notes about how the alert was resolved"
    )
    
    # Relationships
    branch = relationship("Branch", back_populates="alerts")
    currency = relationship("Currency", backref="branch_alerts")
    resolver = relationship("User", foreign_keys=[resolved_by])
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "(is_resolved = FALSE AND resolved_at IS NULL) OR "
            "(is_resolved = TRUE AND resolved_at IS NOT NULL)",
            name='alert_resolved_consistency_check'
        ),
        Index('idx_branch_alerts_active', 'branch_id', 'is_resolved', 'severity'),
        Index('idx_branch_alerts_time', 'triggered_at', 'is_resolved'),
    )
    
    def __repr__(self) -> str:
        status = "RESOLVED" if self.is_resolved else "ACTIVE"
        return f"<BranchAlert({status}, type={self.alert_type}, severity={self.severity})>"