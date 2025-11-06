"""
Customer Models for CEMS - FIXED VERSION
Contains Customer, CustomerDocument, and CustomerNote models

Phase 5.1: Customer Management Module

FIXES:
- Changed datetime.utcnow to datetime.now(timezone.utc) for timezone-aware datetimes
- This prevents "can't subtract offset-naive and offset-aware datetimes" error
"""
from sqlalchemy import (
    Column, String, Date, DateTime, Boolean, Enum as SQLEnum,
    ForeignKey, Text, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime, timezone  # ✅ Added timezone
import uuid
import enum

from app.db.base_class import Base


# Enums
class CustomerType(str, enum.Enum):
    """Customer type enumeration"""
    INDIVIDUAL = "individual"
    CORPORATE = "corporate"


class RiskLevel(str, enum.Enum):
    """Risk level for KYC/AML compliance"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class DocumentType(str, enum.Enum):
    """Document type enumeration"""
    NATIONAL_ID = "national_id"
    PASSPORT = "passport"
    DRIVING_LICENSE = "driving_license"
    UTILITY_BILL = "utility_bill"
    BANK_STATEMENT = "bank_statement"
    COMMERCIAL_REGISTRATION = "commercial_registration"
    TAX_CERTIFICATE = "tax_certificate"
    OTHER = "other"


# ✅ Helper function for timezone-aware datetime
def utcnow():
    """Return current UTC time as timezone-aware datetime"""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class Customer(Base):
    """
    Customer Model - العملاء
    
    Stores customer information with KYC compliance
    Linked to branches and supports both individual and corporate customers
    """
    __tablename__ = "customers"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Customer Identification
    customer_number = Column(
        String(20), 
        unique=True, 
        nullable=True,
        index=True,
        comment="Auto-generated: CUS-00001"
    )
    
    # Personal Information
    first_name = Column(String(100), nullable=False, index=True)
    last_name = Column(String(100), nullable=False, index=True)
    name_ar = Column(String(200), nullable=True, comment="Arabic name (optional)")
    
    # Identification Documents
    national_id = Column(
        String(50), 
        unique=True, 
        nullable=True,
        index=True,
        comment="National ID number"
    )
    passport_number = Column(
        String(50), 
        unique=True, 
        nullable=True,
        index=True,
        comment="Passport number"
    )
    
    # Contact Information
    phone_number = Column(String(20), nullable=False, index=True)
    email = Column(String(255), nullable=True, index=True)
    
    # Personal Details
    date_of_birth = Column(Date, nullable=False)
    nationality = Column(String(100), nullable=False)
    
    # Address Information
    address = Column(Text, nullable=True)
    city = Column(String(100), nullable=True)
    country = Column(String(100), nullable=False, default="Saudi Arabia")
    
    # Customer Classification
    customer_type = Column(
        SQLEnum(
            CustomerType, 
            name="customer_type_enum",
            values_callable=lambda x: [e.value for e in x]  # ✅ هذا المفتاح!
        ),
        nullable=False,
        default="individual",
        index=True
    )
    risk_level = Column(
        SQLEnum(
            RiskLevel, 
            name="risk_level_enum",
            values_callable=lambda x: [e.value for e in x]  # ✅
        ),
        nullable=False,
        default="low",
        index=True,
    )
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="KYC verification status"
    )
    
    # Metadata - ✅ FIXED: Use timezone-aware datetime
    registered_at = Column(
        DateTime, 
        default=utcnow,  # ✅ Changed from datetime.utcnow
        nullable=False,
        index=True
    )
    verified_at = Column(DateTime, nullable=True)
    last_transaction_date = Column(DateTime, nullable=True, index=True)
    
    # Audit Fields - ✅ FIXED: Use timezone-aware datetime
    created_at = Column(DateTime, default=utcnow, nullable=False)  # ✅ Changed
    updated_at = Column(
        DateTime, 
        default=utcnow,  # ✅ Changed
        onupdate=utcnow,  # ✅ Changed
        nullable=False
    )
    
    # Foreign Keys
    registered_by_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who registered this customer"
    )
    verified_by_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        comment="User who verified KYC"
    )
    branch_id = Column(
        UUID(as_uuid=True), 
        ForeignKey("branches.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        comment="Primary branch"
    )
    
    # Additional Info (flexible JSONB field)
    additional_info = Column(
        JSONB,
        nullable=True,
        comment="Additional customer information (occupation, income, etc.)"
    )
    
    # Relationships
    branch = relationship("Branch", back_populates="customers")
    registered_by = relationship("User", foreign_keys=[registered_by_id])
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    documents = relationship(
        "CustomerDocument", 
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    notes = relationship(
        "CustomerNote",
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    transactions = relationship("Transaction", back_populates="customer")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(national_id IS NOT NULL) OR (passport_number IS NOT NULL)",
            name="check_customer_identification"
        ),
        Index("idx_customer_name", "first_name", "last_name"),
        Index("idx_customer_contact", "phone_number", "email"),
        Index("idx_customer_verification", "is_verified", "risk_level"),
        UniqueConstraint("national_id", name="uq_customer_national_id"),
        UniqueConstraint("passport_number", name="uq_customer_passport"),
        {"comment": "Customer master data with KYC compliance"}
    )
    
    def __repr__(self):
        return f"<Customer {self.customer_number}: {self.full_name}>"
    
    @property
    def full_name(self) -> str:
        """Full name of customer"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate customer age - ✅ FIXED"""
        today = datetime.now(timezone.utc).date()  # ✅ Changed
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def primary_identification(self) -> str:
        """Return primary identification (national_id or passport)"""
        return self.national_id or self.passport_number or "N/A"


class CustomerDocument(Base):
    """
    Customer Document Model - وثائق العميل
    
    Stores customer documents for KYC compliance
    """
    __tablename__ = "customer_documents"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Document Information
    document_type = Column(
        SQLEnum(
            DocumentType, 
            name="document_type_enum",
            values_callable=lambda x: [e.value for e in x]  # ✅
        ),
        nullable=False,
        index=True
    )
    document_number = Column(String(100), nullable=True)
    document_url = Column(
        String(500),
        nullable=True,  # Made nullable for seed script
        comment="File path or S3 key"
    )
    
    # Document Validity
    issue_date = Column(Date, nullable=True)
    expiry_date = Column(Date, nullable=True, index=True)
    
    # Verification
    is_verified = Column(Boolean, default=False, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    verified_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    verification_notes = Column(Text, nullable=True)
    
    # Metadata - ✅ FIXED: Use timezone-aware datetime
    uploaded_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(DateTime, default=utcnow, nullable=False)  # ✅ Changed
    updated_at = Column(
        DateTime, 
        default=utcnow,  # ✅ Changed
        onupdate=utcnow,  # ✅ Changed
        nullable=False
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="documents")
    verified_by = relationship("User", foreign_keys=[verified_by_id])
    uploaded_by = relationship("User", foreign_keys=[uploaded_by_id])
    
    # Constraints
    __table_args__ = (
        Index("idx_document_customer_type", "customer_id", "document_type"),
        Index("idx_document_expiry", "expiry_date"),
        {"comment": "Customer documents for KYC/AML compliance"}
    )
    
    def __repr__(self):
        return f"<CustomerDocument {self.document_type} for {self.customer_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if document is expired - ✅ FIXED"""
        if not self.expiry_date:
            return False
        return datetime.now(timezone.utc).replace(tzinfo=None).date() > self.expiry_date  # ✅ Changed


class CustomerNote(Base):
    """
    Customer Note Model - ملاحظات العميل
    
    Internal notes by staff about customers
    """
    __tablename__ = "customer_notes"
    
    # Primary Key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign Key
    customer_id = Column(
        UUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    # Note Content
    note_text = Column(Text, nullable=False)
    is_alert = Column(
        Boolean,
        default=False,
        nullable=False,
        index=True,
        comment="Flag as important alert"
    )
    
    # Metadata - ✅ FIXED: Use timezone-aware datetime
    created_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=utcnow,  # ✅ Changed
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=utcnow,  # ✅ Changed
        onupdate=utcnow,  # ✅ Changed
        nullable=False
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="notes")
    created_by = relationship("User", backref="customer_notes")
    
    # Constraints
    __table_args__ = (
        Index("idx_customer_notes_alert", "customer_id", "is_alert"),
        {"comment": "Internal notes about customers"}
    )
    
    def __repr__(self):
        return f"<CustomerNote for Customer {self.customer_id}>"