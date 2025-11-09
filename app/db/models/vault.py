# app/db/models/vault.py
"""
Vault Management Models
======================
Models for managing main vault, vault balances, and vault transfers

Business Rules:
1. Only ONE main vault can exist (is_main=True)
2. Branch vaults are linked to branches
3. All transfers require approval for amounts > threshold
4. Balance cannot go negative
5. Complete audit trail for all operations
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    Column, String, Boolean, Numeric, DateTime, ForeignKey,
    CheckConstraint, Index, UniqueConstraint, Enum, Text
)
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import relationship
from uuid import uuid4

from app.db.base_class import BaseModel


# ==================== ENUMS ====================

class VaultType(str, PyEnum):
    """Vault types"""
    MAIN = "main"  # Central vault
    BRANCH = "branch"  # Branch vault


class VaultTransferType(str, PyEnum):
    """Types of vault transfers"""
    VAULT_TO_VAULT = "vault_to_vault"  # Between vaults
    VAULT_TO_BRANCH = "vault_to_branch"  # From vault to branch
    BRANCH_TO_VAULT = "branch_to_vault"  # From branch to vault


class VaultTransferStatus(str, PyEnum):
    """Transfer workflow statuses"""
    PENDING = "pending"  # Created, waiting approval if needed
    APPROVED = "approved"  # Approved by manager/admin
    IN_TRANSIT = "in_transit"  # Money sent, not yet received
    COMPLETED = "completed"  # Transfer completed
    CANCELLED = "cancelled"  # Transfer cancelled
    REJECTED = "rejected"  # Transfer rejected


# ==================== MODELS ====================

class Vault(BaseModel):
    """
    Vault Model
    
    Represents a vault (main central vault or branch vault)
    Business Rule: Only one main vault can exist
    """
    
    __tablename__ = "vaults"
    
    # Basic Info
    vault_code = Column(
        String(20),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique vault code (e.g., VLT-MAIN, VLT-BR001)"
    )
    
    name = Column(
        String(100),
        nullable=False,
        comment="Vault name"
    )
    
    vault_type = Column(
        Enum(VaultType, name="vault_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VaultType.BRANCH,
        index=True,
        comment="Type of vault (main or branch)"
    )
    
    # Branch Reference (nullable for main vault)
    branch_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('branches.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
        comment="Reference to branch (NULL for main vault)"
    )
    
    # Status
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Whether vault is active"
    )
    
    # Metadata
    description = Column(
        Text,
        nullable=True,
        comment="Vault description"
    )
    
    location = Column(
        String(200),
        nullable=True,
        comment="Physical location of vault"
    )
    
    # Relationships
    branch = relationship(
        "Branch",
        back_populates="vaults",
        foreign_keys=[branch_id]
    )
    
    balances = relationship(
        "VaultBalance",
        back_populates="vault",
        cascade="all, delete-orphan"
    )
    
    # Transfers from this vault
    transfers_sent = relationship(
        "VaultTransfer",
        back_populates="from_vault",
        foreign_keys="[VaultTransfer.from_vault_id]",
        cascade="all, delete-orphan"
    )
    
    # Transfers to this vault
    transfers_received = relationship(
        "VaultTransfer",
        back_populates="to_vault",
        foreign_keys="[VaultTransfer.to_vault_id]"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "(vault_type = 'main' AND branch_id IS NULL) OR "
            "(vault_type = 'branch' AND branch_id IS NOT NULL)",
            name="vault_branch_consistency_check"
        ),
        Index('idx_vault_type_active', 'vault_type', 'is_active'),
        Index('idx_vault_branch', 'branch_id', 'is_active'),
    )
    
    def __repr__(self) -> str:
        return f"<Vault(code='{self.vault_code}', type='{self.vault_type}')>"


class VaultBalance(BaseModel):
    """
    Vault Balance Model
    
    Tracks currency balances for each vault
    """
    
    __tablename__ = "vault_balances"
    
    # Foreign Keys
    vault_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('vaults.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
        comment="Reference to vault"
    )
    
    currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Reference to currency"
    )
    
    # Balance
    balance = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        default=0,
        comment="Current balance"
    )
    
    # Tracking
    last_updated = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
        index=True,
        comment="Last balance update timestamp"
    )
    
    # Relationships
    vault = relationship("Vault", back_populates="balances")
    currency = relationship("Currency", backref="vault_balances")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('vault_id', 'currency_id', name='uq_vault_currency'),
        CheckConstraint('balance >= 0', name='vault_balance_positive'),
        Index('idx_vault_balance_lookup', 'vault_id', 'currency_id'),
    )
    
    def __repr__(self) -> str:
        return f"<VaultBalance(vault_id={self.vault_id}, balance={self.balance})>"


class VaultTransfer(BaseModel):
    """
    Vault Transfer Model
    
    Manages transfers between vaults and branches
    Includes approval workflow for large amounts
    """
    
    __tablename__ = "vault_transfers"
    
    # Transfer Number
    transfer_number = Column(
        String(30),
        unique=True,
        nullable=False,
        index=True,
        comment="Unique transfer number (VTR-20250109-00001)"
    )
    
    # Source and Destination
    from_vault_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('vaults.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Source vault"
    )
    
    to_vault_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('vaults.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
        comment="Destination vault (NULL if transfer to branch)"
    )
    
    to_branch_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('branches.id', ondelete='RESTRICT'),
        nullable=True,
        index=True,
        comment="Destination branch (NULL if transfer to vault)"
    )
    
    # Transfer Details
    currency_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('currencies.id', ondelete='RESTRICT'),
        nullable=False,
        index=True,
        comment="Currency being transferred"
    )
    
    amount = Column(
        Numeric(precision=15, scale=2),
        nullable=False,
        comment="Transfer amount"
    )
    
    transfer_type = Column(
        Enum(VaultTransferType, name="vault_transfer_type_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
        comment="Type of transfer"
    )

    # Status and Workflow
    status = Column(
        Enum(VaultTransferStatus, name="vault_transfer_status_enum", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=VaultTransferStatus.PENDING,
        index=True,
        comment="Current transfer status"
    )
    
    # Users involved
    initiated_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='RESTRICT'),
        nullable=False,
        comment="User who initiated transfer"
    )
    
    approved_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who approved transfer (for large amounts)"
    )
    
    received_by = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        comment="User who received/confirmed transfer"
    )
    
    # Timestamps
    initiated_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When transfer was initiated"
    )
    
    approved_at = Column(
        DateTime,
        nullable=True,
        comment="When transfer was approved"
    )
    
    completed_at = Column(
        DateTime,
        nullable=True,
        index=True,
        comment="When transfer was completed"
    )
    
    cancelled_at = Column(
        DateTime,
        nullable=True,
        comment="When transfer was cancelled"
    )
    
    # Additional Info
    notes = Column(
        Text,
        nullable=True,
        comment="Transfer notes/reason"
    )
    
    rejection_reason = Column(
        Text,
        nullable=True,
        comment="Reason for rejection (if rejected)"
    )
    
    # Relationships
    from_vault = relationship(
        "Vault",
        back_populates="transfers_sent",
        foreign_keys=[from_vault_id]
    )
    
    to_vault = relationship(
        "Vault",
        back_populates="transfers_received",
        foreign_keys=[to_vault_id]
    )
    
    to_branch = relationship(
        "Branch",
        backref="vault_transfers_received",
        foreign_keys=[to_branch_id]
    )
    
    currency = relationship("Currency", backref="vault_transfers")
    
    initiator = relationship(
        "User",
        backref="initiated_vault_transfers",
        foreign_keys=[initiated_by]
    )

    approver = relationship(
        "User",
        backref="approved_vault_transfers",
        foreign_keys=[approved_by]
    )

    receiver = relationship(
        "User",
        backref="received_vault_transfers",
        foreign_keys=[received_by]
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint('amount > 0', name='transfer_amount_positive'),
        CheckConstraint(
            "(to_vault_id IS NOT NULL AND to_branch_id IS NULL) OR "
            "(to_vault_id IS NULL AND to_branch_id IS NOT NULL)",
            name="transfer_destination_check"
        ),
        Index('idx_transfer_status_date', 'status', 'initiated_at'),
        Index('idx_transfer_from_vault', 'from_vault_id', 'initiated_at'),
        Index('idx_transfer_to_vault', 'to_vault_id', 'initiated_at'),
        Index('idx_transfer_to_branch', 'to_branch_id', 'initiated_at'),
    )
    
    def __repr__(self) -> str:
        return f"<VaultTransfer(number='{self.transfer_number}', status='{self.status}')>"


# ==================== UTILITY CLASS ====================

class VaultTransferNumberGenerator:
    """
    Generates unique vault transfer numbers
    Format: VTR-YYYYMMDD-NNNNN
    Example: VTR-20250109-00001
    """
    
    @staticmethod
    async def generate(session, date: Optional[datetime] = None) -> str:
        """
        Generate next transfer number for the given date

        Args:
            session: Async database session
            date: Date for transfer (default: today)

        Returns:
            Unique transfer number
        """
        from sqlalchemy import select

        if date is None:
            date = datetime.utcnow()

        date_str = date.strftime("%Y%m%d")
        prefix = f"VTR-{date_str}-"

        # Get last transfer number for today
        result = await session.execute(
            select(VaultTransfer).filter(
                VaultTransfer.transfer_number.like(f"{prefix}%")
            ).order_by(VaultTransfer.transfer_number.desc()).limit(1)
        )
        last_transfer = result.scalar_one_or_none()

        if last_transfer:
            # Extract sequence number and increment
            last_seq = int(last_transfer.transfer_number.split('-')[-1])
            next_seq = last_seq + 1
        else:
            next_seq = 1

        return f"{prefix}{next_seq:05d}"
