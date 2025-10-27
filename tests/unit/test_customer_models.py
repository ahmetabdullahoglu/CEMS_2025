"""
Test Cases for Customer Models and Schemas

Phase 5.1: Customer Management Module

Run with: pytest tests/unit/test_customer_models.py -v
"""
import pytest
from datetime import date, datetime, timedelta
from uuid import uuid4
from sqlalchemy.exc import IntegrityError

from app.db.models.customer import (
    Customer, CustomerDocument, CustomerNote,
    CustomerType, RiskLevel, DocumentType
)
from app.schemas.customer import (
    CustomerCreate, CustomerUpdate, CustomerDocumentCreate,
    CustomerNoteCreate, CustomerKYCVerification
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_branch_id():
    """Sample branch ID for testing"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user ID for testing"""
    return uuid4()


@pytest.fixture
def valid_customer_data(sample_branch_id):
    """Valid customer data for testing"""
    return {
        "first_name": "Ahmed",
        "last_name": "Ali",
        "name_ar": "أحمد علي",
        "national_id": "1234567890",
        "phone_number": "+966501234567",
        "email": "ahmed.ali@example.com",
        "date_of_birth": date(1990, 1, 15),
        "nationality": "Saudi",
        "address": "Riyadh, Al Malaz District",
        "city": "Riyadh",
        "country": "Saudi Arabia",
        "customer_type": CustomerType.INDIVIDUAL,
        "branch_id": sample_branch_id
    }


@pytest.fixture
def valid_document_data(sample_user_id):
    """Valid document data for testing"""
    return {
        "document_type": DocumentType.NATIONAL_ID,
        "document_number": "1234567890",
        "document_url": "/documents/customers/123/national_id.pdf",
        "issue_date": date(2020, 1, 1),
        "expiry_date": date(2030, 1, 1),
        "uploaded_by_id": sample_user_id
    }


# ============================================================================
# CUSTOMER MODEL TESTS
# ============================================================================

class TestCustomerModel:
    """Test Customer Model"""
    
    def test_customer_creation(self, db_session, valid_customer_data, sample_user_id):
        """Test creating a customer"""
        customer = Customer(
            **valid_customer_data,
            registered_by_id=sample_user_id
        )
        db_session.add(customer)
        db_session.commit()
        
        assert customer.id is not None
        assert customer.customer_number is not None
        assert customer.customer_number.startswith("CUS-")
        assert customer.first_name == "Ahmed"
        assert customer.last_name == "Ali"
        assert customer.full_name == "Ahmed Ali"
        assert customer.is_active is True
        assert customer.is_verified is False
        assert customer.risk_level == RiskLevel.LOW
    
    def test_customer_age_calculation(self, db_session, valid_customer_data):
        """Test customer age calculation"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Customer born in 1990, should be around 35 years old
        assert customer.age >= 34
        assert customer.age <= 36
    
    def test_customer_primary_identification(self, db_session, valid_customer_data):
        """Test primary identification property"""
        # Test with national_id
        customer1 = Customer(**valid_customer_data)
        db_session.add(customer1)
        db_session.commit()
        assert customer1.primary_identification == "1234567890"
        
        # Test with passport only
        data_passport = valid_customer_data.copy()
        data_passport["national_id"] = None
        data_passport["passport_number"] = "A12345678"
        customer2 = Customer(**data_passport)
        db_session.add(customer2)
        db_session.commit()
        assert customer2.primary_identification == "A12345678"
    
    def test_customer_unique_customer_number(self, db_session, valid_customer_data):
        """Test that customer numbers are unique"""
        customer1 = Customer(**valid_customer_data)
        db_session.add(customer1)
        db_session.commit()
        
        data2 = valid_customer_data.copy()
        data2["national_id"] = "9876543210"
        data2["phone_number"] = "+966509876543"
        customer2 = Customer(**data2)
        db_session.add(customer2)
        db_session.commit()
        
        assert customer1.customer_number != customer2.customer_number
    
    def test_customer_unique_national_id(self, db_session, valid_customer_data):
        """Test that national_id must be unique"""
        customer1 = Customer(**valid_customer_data)
        db_session.add(customer1)
        db_session.commit()
        
        # Try to create another customer with same national_id
        data2 = valid_customer_data.copy()
        data2["phone_number"] = "+966509876543"
        customer2 = Customer(**data2)
        db_session.add(customer2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_customer_must_have_identification(self, db_session, valid_customer_data):
        """Test that customer must have either national_id or passport_number"""
        data = valid_customer_data.copy()
        data["national_id"] = None
        data["passport_number"] = None
        
        customer = Customer(**data)
        db_session.add(customer)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_customer_soft_delete(self, db_session, valid_customer_data):
        """Test customer soft delete (is_active)"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Deactivate customer
        customer.is_active = False
        db_session.commit()
        
        assert customer.is_active is False
    
    def test_customer_kyc_verification(self, db_session, valid_customer_data, sample_user_id):
        """Test KYC verification process"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        assert customer.is_verified is False
        assert customer.verified_at is None
        
        # Verify customer
        customer.is_verified = True
        customer.verified_at = datetime.utcnow()
        customer.verified_by_id = sample_user_id
        customer.risk_level = RiskLevel.LOW
        db_session.commit()
        
        assert customer.is_verified is True
        assert customer.verified_at is not None
        assert customer.verified_by_id == sample_user_id


# ============================================================================
# CUSTOMER DOCUMENT MODEL TESTS
# ============================================================================

class TestCustomerDocumentModel:
    """Test CustomerDocument Model"""
    
    def test_document_creation(self, db_session, valid_customer_data, valid_document_data):
        """Test creating a customer document"""
        # Create customer first
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Create document
        document = CustomerDocument(
            customer_id=customer.id,
            **valid_document_data
        )
        db_session.add(document)
        db_session.commit()
        
        assert document.id is not None
        assert document.customer_id == customer.id
        assert document.document_type == DocumentType.NATIONAL_ID
        assert document.is_verified is False
    
    def test_document_expiry_check(self, db_session, valid_customer_data, valid_document_data):
        """Test document expiry check"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Create expired document
        expired_data = valid_document_data.copy()
        expired_data["expiry_date"] = date.today() - timedelta(days=1)
        
        document = CustomerDocument(
            customer_id=customer.id,
            **expired_data
        )
        db_session.add(document)
        db_session.commit()
        
        assert document.is_expired is True
        
        # Create valid document
        valid_data = valid_document_data.copy()
        valid_data["expiry_date"] = date.today() + timedelta(days=365)
        
        document2 = CustomerDocument(
            customer_id=customer.id,
            document_type=DocumentType.PASSPORT,
            **valid_data
        )
        db_session.add(document2)
        db_session.commit()
        
        assert document2.is_expired is False
    
    def test_document_verification(self, db_session, valid_customer_data, 
                                   valid_document_data, sample_user_id):
        """Test document verification"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        document = CustomerDocument(
            customer_id=customer.id,
            **valid_document_data
        )
        db_session.add(document)
        db_session.commit()
        
        # Verify document
        document.is_verified = True
        document.verified_at = datetime.utcnow()
        document.verified_by_id = sample_user_id
        document.verification_notes = "All information verified"
        db_session.commit()
        
        assert document.is_verified is True
        assert document.verified_at is not None
    
    def test_unique_customer_document(self, db_session, valid_customer_data, valid_document_data):
        """Test that customer can't have duplicate documents"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Create first document
        document1 = CustomerDocument(
            customer_id=customer.id,
            **valid_document_data
        )
        db_session.add(document1)
        db_session.commit()
        
        # Try to create duplicate
        document2 = CustomerDocument(
            customer_id=customer.id,
            **valid_document_data
        )
        db_session.add(document2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


# ============================================================================
# CUSTOMER NOTE MODEL TESTS
# ============================================================================

class TestCustomerNoteModel:
    """Test CustomerNote Model"""
    
    def test_note_creation(self, db_session, valid_customer_data, sample_user_id):
        """Test creating a customer note"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        note = CustomerNote(
            customer_id=customer.id,
            note_text="Customer requested higher transaction limit",
            is_alert=False,
            created_by_id=sample_user_id
        )
        db_session.add(note)
        db_session.commit()
        
        assert note.id is not None
        assert note.customer_id == customer.id
        assert note.is_alert is False
    
    def test_alert_note(self, db_session, valid_customer_data, sample_user_id):
        """Test creating an alert note"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        alert_note = CustomerNote(
            customer_id=customer.id,
            note_text="Suspicious transaction pattern detected",
            is_alert=True,
            created_by_id=sample_user_id
        )
        db_session.add(alert_note)
        db_session.commit()
        
        assert alert_note.is_alert is True
    
    def test_multiple_notes(self, db_session, valid_customer_data, sample_user_id):
        """Test multiple notes for same customer"""
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Add multiple notes
        for i in range(3):
            note = CustomerNote(
                customer_id=customer.id,
                note_text=f"Note {i+1}",
                created_by_id=sample_user_id
            )
            db_session.add(note)
        
        db_session.commit()
        
        # Check customer has 3 notes
        assert len(customer.notes) == 3


# ============================================================================
# CUSTOMER SCHEMA VALIDATION TESTS
# ============================================================================

class TestCustomerSchemas:
    """Test Customer Pydantic Schemas"""
    
    def test_valid_customer_create(self, sample_branch_id):
        """Test valid customer creation schema"""
        data = {
            "first_name": "Ahmed",
            "last_name": "Ali",
            "national_id": "1234567890",
            "phone_number": "+966501234567",
            "email": "ahmed@example.com",
            "date_of_birth": "1990-01-15",
            "nationality": "Saudi",
            "country": "Saudi Arabia",
            "branch_id": str(sample_branch_id)
        }
        
        customer = CustomerCreate(**data)
        assert customer.first_name == "Ahmed"
        assert customer.phone_number == "+966501234567"
    
    def test_invalid_national_id(self, sample_branch_id):
        """Test invalid national ID format"""
        data = {
            "first_name": "Ahmed",
            "last_name": "Ali",
            "national_id": "123",  # Too short
            "phone_number": "+966501234567",
            "date_of_birth": "1990-01-15",
            "nationality": "Saudi",
            "branch_id": str(sample_branch_id)
        }
        
        with pytest.raises(ValueError):
            CustomerCreate(**data)
    
    def test_invalid_phone_number(self, sample_branch_id):
        """Test invalid phone number"""
        data = {
            "first_name": "Ahmed",
            "last_name": "Ali",
            "national_id": "1234567890",
            "phone_number": "123",  # Too short
            "date_of_birth": "1990-01-15",
            "nationality": "Saudi",
            "branch_id": str(sample_branch_id)
        }
        
        with pytest.raises(ValueError):
            CustomerCreate(**data)
    
    def test_underage_customer(self, sample_branch_id):
        """Test that customer must be 18+"""
        data = {
            "first_name": "Young",
            "last_name": "Person",
            "national_id": "1234567890",
            "phone_number": "+966501234567",
            "date_of_birth": str(date.today() - timedelta(days=365*10)),  # 10 years old
            "nationality": "Saudi",
            "branch_id": str(sample_branch_id)
        }
        
        with pytest.raises(ValueError, match="at least 18 years old"):
            CustomerCreate(**data)
    
    def test_no_identification(self, sample_branch_id):
        """Test that at least one identification is required"""
        data = {
            "first_name": "Ahmed",
            "last_name": "Ali",
            "phone_number": "+966501234567",
            "date_of_birth": "1990-01-15",
            "nationality": "Saudi",
            "branch_id": str(sample_branch_id)
        }
        
        with pytest.raises(ValueError, match="identification"):
            CustomerCreate(**data)
    
    def test_passport_format_validation(self, sample_branch_id):
        """Test passport number validation"""
        # Valid passport
        data = {
            "first_name": "Ahmed",
            "last_name": "Ali",
            "passport_number": "A1234567",
            "phone_number": "+966501234567",
            "date_of_birth": "1990-01-15",
            "nationality": "Saudi",
            "branch_id": str(sample_branch_id)
        }
        
        customer = CustomerCreate(**data)
        assert customer.passport_number == "A1234567"
        
        # Invalid passport
        data["passport_number"] = "123"  # Too short
        with pytest.raises(ValueError):
            CustomerCreate(**data)
    
    def test_customer_update_partial(self):
        """Test partial customer update"""
        data = {
            "phone_number": "+966509876543",
            "email": "newemail@example.com"
        }
        
        update = CustomerUpdate(**data)
        assert update.phone_number == "+966509876543"
        assert update.email == "newemail@example.com"
        assert update.first_name is None  # Not provided


# ============================================================================
# CUSTOMER DOCUMENT SCHEMA TESTS
# ============================================================================

class TestCustomerDocumentSchemas:
    """Test CustomerDocument Schemas"""
    
    def test_valid_document_create(self):
        """Test valid document creation"""
        data = {
            "customer_id": str(uuid4()),
            "document_type": "national_id",
            "document_number": "1234567890",
            "document_url": "/documents/test.pdf",
            "issue_date": "2020-01-01",
            "expiry_date": "2030-01-01"
        }
        
        document = CustomerDocumentCreate(**data)
        assert document.document_type == DocumentType.NATIONAL_ID
    
    def test_expiry_before_issue(self):
        """Test that expiry date cannot be before issue date"""
        data = {
            "customer_id": str(uuid4()),
            "document_type": "national_id",
            "document_url": "/documents/test.pdf",
            "issue_date": "2030-01-01",
            "expiry_date": "2020-01-01"  # Before issue date
        }
        
        with pytest.raises(ValueError, match="after issue date"):
            CustomerDocumentCreate(**data)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

class TestCustomerIntegration:
    """Integration tests for customer with documents and notes"""
    
    def test_customer_with_documents_and_notes(self, db_session, valid_customer_data, 
                                                valid_document_data, sample_user_id):
        """Test creating customer with documents and notes"""
        # Create customer
        customer = Customer(**valid_customer_data)
        db_session.add(customer)
        db_session.commit()
        
        # Add documents
        doc1 = CustomerDocument(
            customer_id=customer.id,
            **valid_document_data
        )
        doc2_data = valid_document_data.copy()
        doc2_data["document_type"] = DocumentType.PASSPORT
        doc2_data["document_number"] = "A1234567"
        doc2 = CustomerDocument(
            customer_id=customer.id,
            **doc2_data
        )
        db_session.add_all([doc1, doc2])
        
        # Add notes
        note1 = CustomerNote(
            customer_id=customer.id,
            note_text="First contact",
            created_by_id=sample_user_id
        )
        note2 = CustomerNote(
            customer_id=customer.id,
            note_text="Verified documents",
            is_alert=False,
            created_by_id=sample_user_id
        )
        db_session.add_all([note1, note2])
        db_session.commit()
        
        # Verify relationships
        assert len(customer.documents) == 2
        assert len(customer.notes) == 2
        assert customer.documents[0].customer_id == customer.id
        assert customer.notes[0].customer_id == customer.id


# ============================================================================
# CONFTEST FIXTURES (would be in conftest.py in actual setup)
# ============================================================================

@pytest.fixture(scope="function")
def db_session():
    """
    Mock database session for testing
    In actual implementation, this would be a real database session
    """
    # This is a placeholder - in real tests, you'd use a test database
    from unittest.mock import MagicMock
    session = MagicMock()
    return session


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
