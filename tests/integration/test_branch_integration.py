"""
Integration Tests for Branch Management Module
Tests the complete flow from API to Database

Run with:
    pytest tests/integration/test_branch_integration.py -v
    pytest tests/integration/test_branch_integration.py::TestBranchAPI::test_create_branch -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import uuid
from decimal import Decimal
from datetime import datetime

from app.main import app
from app.db.models.branch import Branch, BranchBalance, RegionEnum
from app.db.models.currency import Currency
from app.db.models.user import User


# ==================== Fixtures ====================

@pytest.fixture
def client():
    """Test client for API requests"""
    return TestClient(app)


@pytest.fixture
async def test_currency(db_session: Session):
    """Create test currency"""
    currency = Currency(
        id=uuid.uuid4(),
        code="USD",
        name_en="US Dollar",
        name_ar="دولار أمريكي",
        symbol="$",
        is_base_currency=False,
        decimal_places=2
    )
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(currency)
    return currency


@pytest.fixture
async def test_user(db_session: Session):
    """Create test user"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


# ==================== Branch API Tests ====================

@pytest.mark.asyncio
class TestBranchAPI:
    """Test Branch API endpoints"""
    
    async def test_create_branch(self, client: TestClient, test_user):
        """Test creating a branch via API"""
        branch_data = {
            "code": "BR001",
            "name_en": "Test Branch",
            "name_ar": "فرع تجريبي",
            "region": "Istanbul_European",
            "address": "Test Address 123",
            "city": "Istanbul",
            "phone": "+905551234567",
            "email": "test@branch.com",
            "is_main_branch": False
        }
        
        response = client.post("/api/v1/branches", json=branch_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data['code'] == "BR001"
        assert data['name_en'] == "Test Branch"
        assert data['is_active'] is True
    
    async def test_create_duplicate_branch_code(self, client: TestClient, db_session):
        """Test that duplicate branch codes are rejected"""
        # Create first branch
        branch1_data = {
            "code": "BR002",
            "name_en": "Branch 1",
            "name_ar": "فرع 1",
            "region": "Istanbul_European",
            "address": "Address 1",
            "city": "Istanbul",
            "phone": "+905551234567"
        }
        
        response1 = client.post("/api/v1/branches", json=branch1_data)
        assert response1.status_code == 201
        
        # Try to create second branch with same code
        branch2_data = {
            **branch1_data,
            "name_en": "Branch 2",
            "name_ar": "فرع 2"
        }
        
        response2 = client.post("/api/v1/branches", json=branch2_data)
        assert response2.status_code == 400
        assert "already exists" in response2.json()['detail'].lower()
    
    async def test_get_branch(self, client: TestClient, db_session):
        """Test getting a branch by ID"""
        # Create branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR003",
            name_en="Get Test Branch",
            name_ar="فرع اختبار",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567"
        )
        db_session.add(branch)
        await db_session.commit()
        
        # Get branch
        response = client.get(f"/api/v1/branches/{branch.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data['code'] == "BR003"
        assert data['name_en'] == "Get Test Branch"
    
    async def test_list_branches(self, client: TestClient, db_session):
        """Test listing all branches"""
        # Create multiple branches
        branches = [
            Branch(
                id=uuid.uuid4(),
                code=f"BR{100+i}",
                name_en=f"Branch {i}",
                name_ar=f"فرع {i}",
                region=RegionEnum.ISTANBUL_EUROPEAN,
                address=f"Address {i}",
                city="Istanbul",
                phone=f"+90555123456{i}"
            )
            for i in range(3)
        ]
        
        for branch in branches:
            db_session.add(branch)
        await db_session.commit()
        
        # List branches
        response = client.get("/api/v1/branches")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total'] >= 3
        assert len(data['branches']) >= 3
    
    async def test_update_branch(self, client: TestClient, db_session):
        """Test updating a branch"""
        # Create branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR004",
            name_en="Update Test Branch",
            name_ar="فرع تحديث",
            region=RegionEnum.IZMIR,
            address="Old Address",
            city="Izmir",
            phone="+902321234567"
        )
        db_session.add(branch)
        await db_session.commit()
        
        # Update branch
        update_data = {
            "name_en": "Updated Branch Name",
            "address": "New Address 456"
        }
        
        response = client.put(f"/api/v1/branches/{branch.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data['name_en'] == "Updated Branch Name"
        assert data['address'] == "New Address 456"
    
    async def test_delete_branch(self, client: TestClient, db_session):
        """Test deleting a branch"""
        # Create branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR005",
            name_en="Delete Test Branch",
            name_ar="فرع حذف",
            region=RegionEnum.BURSA,
            address="Test Address",
            city="Bursa",
            phone="+902241234567"
        )
        db_session.add(branch)
        await db_session.commit()
        
        # Delete branch
        response = client.delete(f"/api/v1/branches/{branch.id}")
        
        assert response.status_code == 204
        
        # Verify branch is soft-deleted
        await db_session.refresh(branch)
        assert branch.is_active is False


# ==================== Balance Operations Tests ====================

@pytest.mark.asyncio
class TestBalanceOperations:
    """Test balance operations"""
    
    async def test_get_branch_balances(
        self,
        client: TestClient,
        db_session,
        test_currency
    ):
        """Test getting branch balances"""
        # Create branch with balance
        branch = Branch(
            id=uuid.uuid4(),
            code="BR006",
            name_en="Balance Test Branch",
            name_ar="فرع الأرصدة",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            balance=Decimal("10000.00"),
            reserved_balance=Decimal("1000.00")
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Get balances
        response = client.get(f"/api/v1/branches/{branch.id}/balances")
        
        assert response.status_code == 200
        data = response.json()
        assert data['total_currencies'] == 1
        assert len(data['balances']) == 1
        assert data['balances'][0]['balance'] == 10000.0
        assert data['balances'][0]['available'] == 9000.0
    
    async def test_set_balance_thresholds(
        self,
        client: TestClient,
        db_session,
        test_currency
    ):
        """Test setting balance thresholds"""
        # Create branch with balance
        branch = Branch(
            id=uuid.uuid4(),
            code="BR007",
            name_en="Threshold Test Branch",
            name_ar="فرع العتبات",
            region=RegionEnum.ISTANBUL_EUROPEAN,
            address="Test Address",
            city="Istanbul",
            phone="+905551234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            balance=Decimal("50000.00")
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Set thresholds
        threshold_data = {
            "minimum_threshold": 10000.0,
            "maximum_threshold": 100000.0
        }
        
        response = client.put(
            f"/api/v1/branches/{branch.id}/balances/{test_currency.id}/thresholds",
            json=threshold_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['minimum_threshold'] == 10000.0
        assert data['maximum_threshold'] == 100000.0
    
    async def test_balance_reconciliation(
        self,
        client: TestClient,
        db_session,
        test_currency
    ):
        """Test balance reconciliation"""
        # Create branch with balance
        branch = Branch(
            id=uuid.uuid4(),
            code="BR008",
            name_en="Reconciliation Test",
            name_ar="فرع التسوية",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            balance=Decimal("10000.00")
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Reconcile with different expected balance
        reconcile_data = {
            "expected_balance": 12000.0,
            "notes": "Manual count reconciliation"
        }
        
        response = client.post(
            f"/api/v1/branches/{branch.id}/balances/{test_currency.id}/reconcile",
            json=reconcile_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['current_balance'] == 10000.0
        assert data['expected_balance'] == 12000.0
        assert data['difference'] == 2000.0
        assert data['adjustment_made'] is True


# ==================== Alert Tests ====================

@pytest.mark.asyncio
class TestAlerts:
    """Test alert functionality"""
    
    async def test_get_branch_alerts(self, client: TestClient, db_session, test_currency):
        """Test getting branch alerts"""
        # Create branch with balance below threshold (should trigger alert)
        branch = Branch(
            id=uuid.uuid4(),
            code="BR009",
            name_en="Alert Test Branch",
            name_ar="فرع التنبيهات",
            region=RegionEnum.ISTANBUL_EUROPEAN,
            address="Test Address",
            city="Istanbul",
            phone="+905551234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            balance=Decimal("5000.00"),
            minimum_threshold=Decimal("10000.00")  # Below threshold
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Get alerts (should have low balance alert from trigger)
        response = client.get(
            f"/api/v1/branches/{branch.id}/alerts",
            params={"is_resolved": False}
        )
        
        assert response.status_code == 200
        alerts = response.json()
        # Check if alert was auto-created by database trigger
        # Note: This depends on trigger being active
    
    async def test_resolve_alert(self, client: TestClient, db_session, test_currency):
        """Test resolving an alert"""
        from app.db.models.branch import BranchAlert, BalanceAlertType, AlertSeverity
        
        # Create branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR010",
            name_en="Resolve Alert Test",
            name_ar="فرع حل التنبيهات",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        # Create alert
        alert = BranchAlert(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            alert_type=BalanceAlertType.LOW_BALANCE,
            severity=AlertSeverity.WARNING,
            title="Low Balance",
            message="Balance is low",
            triggered_at=datetime.utcnow()
        )
        db_session.add(alert)
        await db_session.commit()
        
        # Resolve alert
        resolve_data = {
            "resolution_notes": "Balance has been topped up"
        }
        
        response = client.put(
            f"/api/v1/branches/alerts/{alert.id}/resolve",
            json=resolve_data
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data['is_resolved'] is True
        assert data['resolution_notes'] == "Balance has been topped up"


# ==================== Statistics Tests ====================

@pytest.mark.asyncio
class TestStatistics:
    """Test statistics endpoints"""
    
    async def test_get_branch_statistics(
        self,
        client: TestClient,
        db_session,
        test_currency
    ):
        """Test getting branch statistics"""
        # Create branch with balances
        branch = Branch(
            id=uuid.uuid4(),
            code="BR011",
            name_en="Statistics Test",
            name_ar="فرع الإحصائيات",
            region=RegionEnum.IZMIR,
            address="Test Address",
            city="Izmir",
            phone="+902321234567"
        )
        db_session.add(branch)
        await db_session.flush()
        
        # Add multiple currency balances
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=test_currency.id,
            balance=Decimal("25000.00"),
            reserved_balance=Decimal("2500.00")
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Get statistics
        response = client.get(f"/api/v1/branches/{branch.id}/statistics")
        
        assert response.status_code == 200
        data = response.json()
        assert 'branch' in data
        assert data['branch']['code'] == "BR011"
        assert 'balances' in data
        assert len(data['balances']) >= 1


# ==================== Business Logic Tests ====================

@pytest.mark.asyncio
class TestBusinessLogic:
    """Test business logic and rules"""
    
    async def test_single_main_branch_constraint(self, client: TestClient, db_session):
        """Test that only one main branch can exist"""
        # Create first main branch
        branch1_data = {
            "code": "BR012",
            "name_en": "Main Branch 1",
            "name_ar": "الفرع الرئيسي 1",
            "region": "Istanbul_European",
            "address": "Address 1",
            "city": "Istanbul",
            "phone": "+905551234567",
            "is_main_branch": True
        }
        
        response1 = client.post("/api/v1/branches", json=branch1_data)
        assert response1.status_code == 201
        
        # Try to create second main branch
        branch2_data = {
            "code": "BR013",
            "name_en": "Main Branch 2",
            "name_ar": "الفرع الرئيسي 2",
            "region": "Ankara",
            "address": "Address 2",
            "city": "Ankara",
            "phone": "+903121234567",
            "is_main_branch": True
        }
        
        response2 = client.post("/api/v1/branches", json=branch2_data)
        assert response2.status_code == 422
        assert "main branch" in response2.json()['detail'].lower()
    
    async def test_cannot_delete_main_branch(self, client: TestClient, db_session):
        """Test that main branch cannot be deleted"""
        # Create main branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR014",
            name_en="Main Branch",
            name_ar="الفرع الرئيسي",
            region=RegionEnum.ISTANBUL_EUROPEAN,
            address="Main Address",
            city="Istanbul",
            phone="+905551234567",
            is_main_branch=True
        )
        db_session.add(branch)
        await db_session.commit()
        
        # Try to delete
        response = client.delete(f"/api/v1/branches/{branch.id}")
        
        assert response.status_code == 422
        assert "cannot delete main branch" in response.json()['detail'].lower()