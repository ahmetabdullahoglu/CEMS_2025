# tests/integration/test_customer_api.py
"""
Integration Tests for Customer API
Tests the complete flow from API endpoints through service layer to database

Phase 5.2: Customer Service & API
"""
import pytest
from typing import Dict, Any
from uuid import uuid4
from datetime import date, timedelta
from httpx import AsyncClient

from app.db.models.user import User
from app.db.models.branch import Branch
from app.db.models.customer import CustomerType, RiskLevel, DocumentType


# ==================== Test Fixtures ====================

@pytest.fixture
async def test_branch(async_client: AsyncClient, admin_token: str) -> Dict[str, Any]:
    """Create a test branch"""
    response = await async_client.post(
        "/api/v1/branches",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={
            "code": "TEST001",
            "name_en": "Test Branch",
            "name_ar": "فرع تجريبي",
            "region": "Istanbul_European",
            "address": "Test Address",
            "phone": "+905551234567",
            "email": "test@branch.com"
        }
    )
    assert response.status_code == 201
    return response.json()


@pytest.fixture
def valid_customer_data(test_branch: Dict[str, Any]) -> Dict[str, Any]:
    """Valid customer data for testing"""
    return {
        "first_name": "Ahmed",
        "last_name": "Ali",
        "name_ar": "أحمد علي",
        "national_id": "12345678901",
        "phone_number": "+905551234567",
        "email": "ahmed.ali@example.com",
        "date_of_birth": "1990-01-15",
        "nationality": "Turkish",
        "address": "Istanbul, Turkey",
        "city": "Istanbul",
        "country": "Turkey",
        "customer_type": "individual",
        "branch_id": test_branch["id"]
    }


# ==================== Customer CRUD Tests ====================

@pytest.mark.asyncio
class TestCustomerCRUD:
    """Test customer CRUD operations"""
    
    async def test_create_customer_success(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test successful customer creation"""
        response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["first_name"] == "Ahmed"
        assert data["last_name"] == "Ali"
        assert data["national_id"] == "12345678901"
        assert data["customer_number"].startswith("CUS-")
        assert data["is_active"] is True
        assert data["is_verified"] is False
    
    async def test_create_customer_duplicate_national_id(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test creating customer with duplicate national ID"""
        # Create first customer
        response1 = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        assert response1.status_code == 201
        
        # Try to create duplicate
        response2 = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        assert response2.status_code == 409  # Conflict
    
    async def test_create_customer_missing_identification(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test creating customer without national_id or passport"""
        data = valid_customer_data.copy()
        data.pop("national_id")
        # No passport_number either
        
        response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=data
        )
        assert response.status_code == 422
    
    async def test_get_customer_by_id(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test retrieving customer by ID"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Get customer
        response = await async_client.get(
            f"/api/v1/customers/{customer['id']}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == customer["id"]
        assert data["customer_number"] == customer["customer_number"]
    
    async def test_get_customer_not_found(
        self,
        async_client: AsyncClient,
        user_token: str
    ):
        """Test getting non-existent customer"""
        response = await async_client.get(
            f"/api/v1/customers/{uuid4()}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404
    
    async def test_update_customer(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test updating customer information"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Update customer
        update_data = {
            "phone_number": "+905559876543",
            "email": "new.email@example.com",
            "address": "New Address"
        }
        
        response = await async_client.put(
            f"/api/v1/customers/{customer['id']}",
            headers={"Authorization": f"Bearer {user_token}"},
            json=update_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["phone_number"] == "+905559876543"
        assert data["email"] == "new.email@example.com"
        assert data["address"] == "New Address"


# ==================== Search & Filtering Tests ====================

@pytest.mark.asyncio
class TestCustomerSearch:
    """Test customer search and filtering"""
    
    async def test_search_customers_by_name(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test searching customers by name"""
        # Create customer
        await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        
        # Search
        response = await async_client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"query": "Ahmed"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert any(c["first_name"] == "Ahmed" for c in data["customers"])
    
    async def test_search_customers_by_phone(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test searching customers by phone number"""
        # Create customer
        await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        
        # Search
        response = await async_client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"query": "905551234567"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
    
    async def test_filter_customers_by_branch(
        self,
        async_client: AsyncClient,
        user_token: str,
        test_branch: Dict[str, Any],
        valid_customer_data: Dict[str, Any]
    ):
        """Test filtering customers by branch"""
        # Create customer
        await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        
        # Filter by branch
        response = await async_client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"branch_id": test_branch["id"]}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(c["branch_id"] == test_branch["id"] for c in data["customers"])
    
    async def test_filter_customers_by_verification_status(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test filtering customers by verification status"""
        # Create customer
        await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        
        # Filter unverified
        response = await async_client.get(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            params={"is_verified": False}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert all(c["is_verified"] is False for c in data["customers"])


# ==================== KYC Verification Tests ====================

@pytest.mark.asyncio
class TestCustomerKYC:
    """Test KYC verification processes"""
    
    async def test_verify_customer_kyc(
        self,
        async_client: AsyncClient,
        admin_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test KYC verification"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Add a document first
        await async_client.post(
            f"/api/v1/customers/{customer['id']}/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "document_type": "national_id",
                "document_url": "/documents/test.pdf",
                "document_number": "12345678901"
            }
        )
        
        # Verify KYC
        response = await async_client.post(
            f"/api/v1/customers/{customer['id']}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "customer_id": customer['id'],
                "is_verified": True,
                "risk_level": "low",
                "verification_notes": "All documents verified"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["risk_level"] == "low"
        assert data["verified_at"] is not None


# ==================== Document Management Tests ====================

@pytest.mark.asyncio
class TestCustomerDocuments:
    """Test customer document management"""
    
    async def test_upload_document(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test uploading customer document"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Upload document
        response = await async_client.post(
            f"/api/v1/customers/{customer['id']}/documents",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "document_type": "national_id",
                "document_url": "/documents/national_id.pdf",
                "document_number": "12345678901",
                "issue_date": "2020-01-01",
                "expiry_date": "2030-01-01"
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["document_type"] == "national_id"
        assert data["is_verified"] is False
    
    async def test_get_customer_documents(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test retrieving customer documents"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Upload document
        await async_client.post(
            f"/api/v1/customers/{customer['id']}/documents",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "document_type": "passport",
                "document_url": "/documents/passport.pdf"
            }
        )
        
        # Get documents
        response = await async_client.get(
            f"/api/v1/customers/{customer['id']}/documents",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(d["document_type"] == "passport" for d in data)
    
    async def test_verify_document(
        self,
        async_client: AsyncClient,
        admin_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test document verification"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {admin_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Upload document
        doc_response = await async_client.post(
            f"/api/v1/customers/{customer['id']}/documents",
            headers={"Authorization": f"Bearer {admin_token}"},
            json={
                "document_type": "national_id",
                "document_url": "/documents/national_id.pdf"
            }
        )
        document = doc_response.json()
        
        # Verify document
        response = await async_client.put(
            f"/api/v1/customers/documents/{document['id']}/verify",
            headers={"Authorization": f"Bearer {admin_token}"},
            params={
                "is_verified": True,
                "verification_notes": "Document verified successfully"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["is_verified"] is True
        assert data["verification_notes"] == "Document verified successfully"


# ==================== Notes Management Tests ====================

@pytest.mark.asyncio
class TestCustomerNotes:
    """Test customer notes management"""
    
    async def test_add_customer_note(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test adding note to customer"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Add note
        response = await async_client.post(
            f"/api/v1/customers/{customer['id']}/notes",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "customer_id": customer['id'],
                "note_text": "Customer requested higher transaction limit",
                "is_alert": False
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert "Customer requested higher" in data["note_text"]
        assert data["is_alert"] is False
    
    async def test_get_customer_notes(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test retrieving customer notes"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Add note
        await async_client.post(
            f"/api/v1/customers/{customer['id']}/notes",
            headers={"Authorization": f"Bearer {user_token}"},
            json={
                "customer_id": customer['id'],
                "note_text": "Test note",
                "is_alert": True
            }
        )
        
        # Get notes
        response = await async_client.get(
            f"/api/v1/customers/{customer['id']}/notes",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert any(n["note_text"] == "Test note" for n in data)


# ==================== Statistics Tests ====================

@pytest.mark.asyncio
class TestCustomerStatistics:
    """Test customer statistics"""
    
    async def test_get_customer_stats(
        self,
        async_client: AsyncClient,
        user_token: str,
        valid_customer_data: Dict[str, Any]
    ):
        """Test retrieving customer statistics"""
        # Create customer
        create_response = await async_client.post(
            "/api/v1/customers",
            headers={"Authorization": f"Bearer {user_token}"},
            json=valid_customer_data
        )
        customer = create_response.json()
        
        # Get stats
        response = await async_client.get(
            f"/api/v1/customers/{customer['id']}/stats",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "customer_id" in data
        assert "account_age_days" in data
        assert "total_transactions" in data
        assert "documents" in data
        assert data["is_verified"] is False
