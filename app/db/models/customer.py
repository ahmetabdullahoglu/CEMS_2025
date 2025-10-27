"""
Customer Models for CEMS
Contains Customer, CustomerDocument, and CustomerNote models

Phase 5.1: Customer Management Module
"""
from sqlalchemy import (
    Column, String, Date, DateTime, Boolean, Enum as SQLEnum,
    ForeignKey, Text, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
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
    COMMERCIAL_REGISTRATION = "commercial_registration"  # للشركات
    TAX_CERTIFICATE = "tax_certificate"
    OTHER = "other"


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
        nullable=False, 
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
        nullable=True,  # Some customers might only have passport
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
        SQLEnum(CustomerType, name="customer_type_enum"),
        nullable=False,
        default=CustomerType.INDIVIDUAL,
        index=True
    )
    risk_level = Column(
        SQLEnum(RiskLevel, name="risk_level_enum"),
        nullable=False,
        default=RiskLevel.LOW,
        index=True,
        comment="KYC/AML risk assessment"
    )
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_verified = Column(
        Boolean, 
        default=False, 
        nullable=False,
        comment="KYC verification status"
    )
    
    # Metadata
    registered_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        nullable=False,
        index=True
    )
    verified_at = Column(DateTime, nullable=True)
    last_transaction_date = Column(DateTime, nullable=True, index=True)
    
    # Audit Fields
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime, 
        default=datetime.utcnow, 
        onupdate=datetime.utcnow,
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
    registered_by = relationship(
        "User", 
        foreign_keys=[registered_by_id],
        backref="registered_customers"
    )
    verified_by = relationship(
        "User", 
        foreign_keys=[verified_by_id],
        backref="verified_customers"
    )
    branch = relationship("Branch", backref="customers")
    documents = relationship(
        "CustomerDocument", 
        back_populates="customer",
        cascade="all, delete-orphan"
    )
    notes = relationship(
        "CustomerNote",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="desc(CustomerNote.created_at)"
    )
    # transactions = relationship(
    #     "Transaction",
    #     back_populates="customer",
    #     cascade="all, delete-orphan"
    # )
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "(national_id IS NOT NULL) OR (passport_number IS NOT NULL)",
            name="customer_must_have_identification"
        ),
        Index("idx_customer_full_name", "first_name", "last_name"),
        Index("idx_customer_branch_active", "branch_id", "is_active"),
        Index("idx_customer_risk_active", "risk_level", "is_active"),
        {"comment": "Customer information with KYC compliance"}
    )
    
    def __repr__(self):
        return f"<Customer {self.customer_number}: {self.first_name} {self.last_name}>"
    
    @property
    def full_name(self) -> str:
        """Full name of customer"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self) -> int:
        """Calculate customer age"""
        today = datetime.utcnow().date()
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
        SQLEnum(DocumentType, name="document_type_enum"),
        nullable=False,
        index=True
    )
    document_number = Column(String(100), nullable=True)
    document_url = Column(
        String(500),
        nullable=False,
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
    
    # Verification Notes
    verification_notes = Column(Text, nullable=True)
    
    # Metadata
    uploaded_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    uploaded_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )
    
    # Relationships
    customer = relationship("Customer", back_populates="documents")
    verified_by = relationship(
        "User",
        foreign_keys=[verified_by_id],
        backref="verified_documents"
    )
    uploaded_by = relationship(
        "User",
        foreign_keys=[uploaded_by_id],
        backref="uploaded_documents"
    )
    
    # Constraints
    __table_args__ = (
        Index("idx_customer_doc_type", "customer_id", "document_type"),
        Index("idx_doc_expiry", "expiry_date"),
        UniqueConstraint(
            "customer_id", "document_type", "document_number",
            name="unique_customer_document"
        ),
        {"comment": "Customer documents for KYC compliance"}
    )
    
    def __repr__(self):
        return f"<CustomerDocument {self.document_type.value} for Customer {self.customer_id}>"
    
    @property
    def is_expired(self) -> bool:
        """Check if document is expired"""
        if not self.expiry_date:
            return False
        return datetime.utcnow().date() > self.expiry_date


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
    
    # Metadata
    created_by_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
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
