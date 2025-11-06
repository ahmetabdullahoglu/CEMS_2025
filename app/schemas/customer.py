"""
Customer Schemas for CEMS
Pydantic models for request/response validation

Phase 5.1: Customer Management Module
"""
from pydantic import BaseModel, EmailStr, Field, validator, root_validator,model_validator
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID
import re

from app.db.models.customer import CustomerType, RiskLevel, DocumentType


# ============================================================================
# CUSTOMER SCHEMAS
# ============================================================================

class CustomerBase(BaseModel):
    """Base schema for Customer"""
    first_name: str = Field(..., min_length=2, max_length=100)
    last_name: str = Field(..., min_length=2, max_length=100)
    name_ar: Optional[str] = Field(None, max_length=200)
    national_id: Optional[str] = Field(None, max_length=50)
    passport_number: Optional[str] = Field(None, max_length=50)
    phone_number: str = Field(..., min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    date_of_birth: date
    nationality: str = Field(..., min_length=2, max_length=100)
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: str = Field(default="Saudi Arabia", max_length=100)
    customer_type: CustomerType = CustomerType.INDIVIDUAL
    additional_info: Optional[dict] = None
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        """Validate name contains only letters and spaces"""
        if not re.match(r'^[a-zA-Z\s\u0600-\u06FF]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v.strip()
    
    @validator('national_id')
    def validate_national_id(cls, v):
        """Validate Saudi national ID format (10 digits starting with 1 or 2)"""
        if v is None:
            return v
        
        # Remove any spaces or dashes
        v = re.sub(r'[\s-]', '', v)
        
        # Saudi ID: 10 digits starting with 1 (Saudi) or 2 (Resident)
        if not re.match(r'^[12]\d{9}$', v):
            raise ValueError(
                'Invalid national ID format. Must be 10 digits starting with 1 or 2'
            )
        return v
    
    @validator('passport_number')
    def validate_passport(cls, v):
        """Validate passport number format"""
        if v is None:
            return v
        
        # Remove spaces
        v = re.sub(r'\s', '', v)
        
        # General passport format: 6-9 alphanumeric characters
        if not re.match(r'^[A-Z0-9]{6,9}$', v.upper()):
            raise ValueError(
                'Invalid passport format. Must be 6-9 alphanumeric characters'
            )
        return v.upper()
    
    @validator('phone_number')
    def validate_phone(cls, v):
        """Validate phone number format (international format)"""
        # Remove spaces, dashes, parentheses
        v = re.sub(r'[\s\-\(\)]', '', v)
        
        # Must start with + or digits, 10-15 digits total
        if not re.match(r'^\+?\d{10,15}$', v):
            raise ValueError(
                'Invalid phone number. Must be 10-15 digits (with optional +)'
            )
        
        # Ensure it starts with +
        if not v.startswith('+'):
            v = '+' + v
        
        return v
    
    @validator('date_of_birth')
    def validate_age(cls, v):
        """Validate customer is at least 18 years old"""
        today = date.today()
        age = today.year - v.year - ((today.month, today.day) < (v.month, v.day))
        
        if age < 18:
            raise ValueError('Customer must be at least 18 years old')
        if age > 120:
            raise ValueError('Invalid date of birth')
        
        return v
    
    @model_validator(mode='after')
    def validate_identification(self):
        """Ensure at least one form of identification is provided"""
        if not self.national_id and not self.passport_number:
            raise ValueError(
                'At least one form of identification (national_id or passport_number) is required'
            )
        return self


class CustomerCreate(CustomerBase):
    """Schema for creating a new customer"""
    branch_id: UUID = Field(..., description="Primary branch ID")
    risk_level: RiskLevel = RiskLevel.LOW
    
    class Config:
        json_json_json_schema_extra = {
            "example": {
                "first_name": "Ahmed",
                "last_name": "Ali",
                "name_ar": "أحمد علي",
                "national_id": "1234567890",
                "phone_number": "+966501234567",
                "email": "ahmed.ali@example.com",
                "date_of_birth": "1990-01-15",
                "nationality": "Saudi",
                "address": "Riyadh, Al Malaz District",
                "city": "Riyadh",
                "country": "Saudi Arabia",
                "customer_type": "individual",
                "branch_id": "123e4567-e89b-12d3-a456-426614174000",
                "risk_level": "low"
            }
        }


class CustomerUpdate(BaseModel):
    """Schema for updating customer information"""
    first_name: Optional[str] = Field(None, min_length=2, max_length=100)
    last_name: Optional[str] = Field(None, min_length=2, max_length=100)
    name_ar: Optional[str] = Field(None, max_length=200)
    phone_number: Optional[str] = Field(None, min_length=10, max_length=20)
    email: Optional[EmailStr] = None
    address: Optional[str] = None
    city: Optional[str] = Field(None, max_length=100)
    country: Optional[str] = Field(None, max_length=100)
    risk_level: Optional[RiskLevel] = None
    is_active: Optional[bool] = None
    additional_info: Optional[dict] = None
    
    @validator('first_name', 'last_name')
    def validate_name(cls, v):
        if v is None:
            return v
        if not re.match(r'^[a-zA-Z\s\u0600-\u06FF]+$', v):
            raise ValueError('Name must contain only letters and spaces')
        return v.strip()
    
    @validator('phone_number')
    def validate_phone(cls, v):
        if v is None:
            return v
        v = re.sub(r'[\s\-\(\)]', '', v)
        if not re.match(r'^\+?\d{10,15}$', v):
            raise ValueError('Invalid phone number format')
        if not v.startswith('+'):
            v = '+' + v
        return v
    
    class Config:
        use_enum_values = True


class CustomerResponse(BaseModel):
    """Schema for customer response - NO VALIDATION on output"""
    # Basic Info
    id: UUID
    customer_number: str
    first_name: str
    last_name: str
    name_ar: Optional[str] = None
    
    # Identification - NO VALIDATORS HERE
    national_id: Optional[str] = None
    passport_number: Optional[str] = None
    
    # Contact
    phone_number: str
    email: Optional[EmailStr] = None
    
    # Personal Details
    date_of_birth: date
    nationality: str
    address: Optional[str] = None
    city: Optional[str] = None
    country: str
    
    # Type & Status
    customer_type: CustomerType
    risk_level: RiskLevel
    is_active: bool
    is_verified: bool
    
    # Timestamps
    registered_at: datetime
    verified_at: Optional[datetime] = None
    last_transaction_date: Optional[datetime] = None
    
    # Relationships
    branch_id: UUID
    registered_by_id: Optional[UUID] = None
    verified_by_id: Optional[UUID] = None
    
    # Metadata
    created_at: datetime
    updated_at: datetime
    additional_info: Optional[dict] = None
    
    class Config:
        from_attributes = True
        use_enum_values = True




class CustomerSearchQuery(BaseModel):
    """Schema for customer search"""
    query: Optional[str] = Field(None, description="Search by name, phone, or ID")
    customer_type: Optional[CustomerType] = None
    risk_level: Optional[RiskLevel] = None
    is_active: Optional[bool] = None
    is_verified: Optional[bool] = None
    branch_id: Optional[UUID] = None
    skip: int = Field(0, ge=0)
    limit: int = Field(100, ge=1, le=1000)


# ============================================================================
# CUSTOMER DOCUMENT SCHEMAS
# ============================================================================

class CustomerDocumentBase(BaseModel):
    """Base schema for CustomerDocument"""
    document_type: DocumentType
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    verification_notes: Optional[str] = None
    
    @validator('expiry_date')
    def validate_expiry(cls, v, values):
        """Validate expiry date is after issue date"""
        if v is None:
            return v
        
        issue_date = values.get('issue_date')
        if issue_date and v < issue_date:
            raise ValueError('Expiry date must be after issue date')
        
        return v
    
    class Config:
        use_enum_values = True


class CustomerDocumentCreate(CustomerDocumentBase):
    """Schema for uploading customer document"""
    customer_id: UUID
    document_url: str = Field(..., max_length=500)
    
    class Config:
        json_json_json_schema_extra = {
            "example": {
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "document_type": "national_id",
                "document_number": "1234567890",
                "document_url": "/documents/customers/123e4567/national_id.pdf",
                "issue_date": "2020-01-01",
                "expiry_date": "2030-01-01"
            }
        }


class CustomerDocumentUpdate(BaseModel):
    """Schema for updating document"""
    document_number: Optional[str] = Field(None, max_length=100)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    is_verified: Optional[bool] = None
    verification_notes: Optional[str] = None


class CustomerDocumentResponse(CustomerDocumentBase):
    """Schema for document response"""
    id: UUID
    customer_id: UUID
    document_url: str
    is_verified: bool
    verified_at: Optional[datetime] = None
    verified_by_id: Optional[UUID] = None
    uploaded_at: datetime
    uploaded_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
        use_enum_values = True


# ============================================================================
# CUSTOMER NOTE SCHEMAS
# ============================================================================

class CustomerNoteBase(BaseModel):
    """Base schema for CustomerNote"""
    note_text: str = Field(..., min_length=1, max_length=5000)
    is_alert: bool = False


class CustomerNoteCreate(CustomerNoteBase):
    """Schema for creating customer note"""
    customer_id: UUID
    
    class Config:
        json_json_json_schema_extra = {
            "example": {
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "note_text": "Customer requested higher transaction limit",
                "is_alert": False
            }
        }


class CustomerNoteUpdate(BaseModel):
    """Schema for updating note"""
    note_text: Optional[str] = Field(None, min_length=1, max_length=5000)
    is_alert: Optional[bool] = None


class CustomerNoteResponse(CustomerNoteBase):
    """Schema for note response"""
    id: UUID
    customer_id: UUID
    created_by_id: Optional[UUID] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# ============================================================================
# COMPREHENSIVE CUSTOMER DETAIL
# ============================================================================

class CustomerDetailResponse(CustomerResponse):
    """Comprehensive customer information with documents and notes"""
    documents: List[CustomerDocumentResponse] = []
    notes: List[CustomerNoteResponse] = []
    total_transactions: int = 0
    
    class Config:
        from_attributes = True
        use_enum_values = True


# ============================================================================
# KYC VERIFICATION
# ============================================================================

class CustomerKYCVerification(BaseModel):
    """Schema for KYC verification"""
    customer_id: UUID
    is_verified: bool
    verification_notes: Optional[str] = None
    risk_level: Optional[RiskLevel] = None
    
    class Config:
        json_json_json_schema_extra = {
            "example": {
                "customer_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_verified": True,
                "verification_notes": "All documents verified",
                "risk_level": "low"
            }
        }
