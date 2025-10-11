"""
Test cases for Branch Management Module
Tests for Branch, BranchBalance, BranchBalanceHistory, and BranchAlert models

Run with:
    pytest tests/unit/test_branch_models.py -v
    pytest tests/unit/test_branch_models.py::TestBranchModel::test_create_branch -v
"""

import pytest
import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.db.models.branch import (
    Branch, BranchBalance, BranchBalanceHistory, BranchAlert,
    RegionEnum, BalanceAlertType, AlertSeverity, BalanceChangeType
)
from app.db.models.currency import Currency
from app.db.models.user import User


# ==================== Fixtures ====================

@pytest.fixture
async def sample_currency(db_session):
    """Create a sample currency for testing"""
    currency = Currency(
        id=uuid.uuid4(),
        code="USD",
        name_en="US Dollar",
        name_ar="دولار أمريكي",
        symbol="$",
        is_base_currency=False,
        decimal_places=2,
    )
    db_session.add(currency)
    await db_session.commit()
    await db_session.refresh(currency)
    return currency


@pytest.fixture
async def sample_user(db_session):
    """Create a sample user for testing"""
    user = User(
        id=uuid.uuid4(),
        username="testuser",
        email="test@example.com",
        full_name="Test User",
        hashed_password="hashed_password",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def sample_branch(db_session, sample_user):
    """Create a sample branch for testing"""
    branch = Branch(
        id=uuid.uuid4(),
        code="BR001",
        name_en="Test Branch",
        name_ar="فرع تجريبي",
        region=RegionEnum.ISTANBUL_EUROPEAN,
        address="Test Address 123",
        city="Istanbul",
        phone="+905551234567",
        email="test@branch.com",
        manager_id=sample_user.id,
        is_main_branch=False,
        opening_balance_date=datetime.utcnow(),
    )
    db_session.add(branch)
    await db_session.commit()
    await db_session.refresh(branch)
    return branch


# ==================== Branch Model Tests ====================

@pytest.mark.asyncio
class TestBranchModel:
    """Tests for Branch model"""
    
    async def test_create_branch(self, db_session):
        """Test creating a basic branch"""
        branch = Branch(
            id=uuid.uuid4(),
            code="BR002",
            name_en="Istanbul Main",
            name_ar="اسطنبول الرئيسي",
            region=RegionEnum.ISTANBUL_EUROPEAN,
            address="Taksim Square 45",
            city="Istanbul",
            phone="+905551234568",
            email="istanbul@cems.com",
            is_main_branch=False,
        )
        
        db_session.add(branch)
        await db_session.commit()
        await db_session.refresh(branch)
        
        assert branch.id is not None
        assert branch.code == "BR002"
        assert branch.name_en == "Istanbul Main"
        assert branch.region == RegionEnum.ISTANBUL_EUROPEAN
        assert branch.is_active is True
        assert branch.created_at is not None
    
    async def test_branch_code_uniqueness(self, db_session, sample_branch):
        """Test that branch codes must be unique"""
        duplicate_branch = Branch(
            id=uuid.uuid4(),
            code=sample_branch.code,  # Same code
            name_en="Duplicate Branch",
            name_ar="فرع مكرر",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567",
        )
        
        db_session.add(duplicate_branch)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_single_main_branch_constraint(self, db_session):
        """Test that only one main branch can exist"""
        # Create first main branch
        main_branch1 = Branch(
            id=uuid.uuid4(),
            code="BR003",
            name_en="Main Branch 1",
            name_ar="الفرع الرئيسي 1",
            region=RegionEnum.ISTANBUL_EUROPEAN,
            address="Address 1",
            city="Istanbul",
            phone="+905551234569",
            is_main_branch=True,
        )
        db_session.add(main_branch1)
        await db_session.commit()
        
        # Try to create second main branch
        main_branch2 = Branch(
            id=uuid.uuid4(),
            code="BR004",
            name_en="Main Branch 2",
            name_ar="الفرع الرئيسي 2",
            region=RegionEnum.ANKARA,
            address="Address 2",
            city="Ankara",
            phone="+903121234568",
            is_main_branch=True,
        )
        db_session.add(main_branch2)
        
        # Should fail due to trigger
        with pytest.raises(Exception) as exc_info:
            await db_session.commit()
        
        assert "Only one main branch" in str(exc_info.value)
    
    async def test_branch_code_format(self, db_session):
        """Test branch code format validation"""
        invalid_branch = Branch(
            id=uuid.uuid4(),
            code="INVALID",  # Should start with BR and have numbers
            name_en="Invalid Branch",
            name_ar="فرع غير صالح",
            region=RegionEnum.ANKARA,
            address="Test Address",
            city="Ankara",
            phone="+903121234567",
        )
        
        db_session.add(invalid_branch)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_branch_relationships(self, db_session, sample_branch, sample_currency):
        """Test branch relationships with balances"""
        # Create balance for branch
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("10000.00"),
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Refresh and check relationships
        await db_session.refresh(sample_branch)
        assert len(sample_branch.balances) == 1
        assert sample_branch.balances[0].balance == Decimal("10000.00")


# ==================== BranchBalance Model Tests ====================

@pytest.mark.asyncio
class TestBranchBalanceModel:
    """Tests for BranchBalance model"""
    
    async def test_create_branch_balance(self, db_session, sample_branch, sample_currency):
        """Test creating a branch balance"""
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("50000.00"),
            reserved_balance=Decimal("5000.00"),
            minimum_threshold=Decimal("10000.00"),
            maximum_threshold=Decimal("100000.00"),
        )
        
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)
        
        assert balance.id is not None
        assert balance.balance == Decimal("50000.00")
        assert balance.reserved_balance == Decimal("5000.00")
        assert balance.available_balance == Decimal("45000.00")
    
    async def test_unique_branch_currency_constraint(self, db_session, sample_branch, sample_currency):
        """Test that branch-currency combination must be unique"""
        # Create first balance
        balance1 = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("10000.00"),
        )
        db_session.add(balance1)
        await db_session.commit()
        
        # Try to create duplicate
        balance2 = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("20000.00"),
        )
        db_session.add(balance2)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_balance_positive_constraint(self, db_session, sample_branch, sample_currency):
        """Test that balance cannot be negative"""
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("-1000.00"),  # Negative balance
        )
        
        db_session.add(balance)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_reserved_not_exceeding_balance(self, db_session, sample_branch, sample_currency):
        """Test that reserved balance cannot exceed total balance"""
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("10000.00"),
            reserved_balance=Decimal("15000.00"),  # Greater than balance
        )
        
        db_session.add(balance)
        
        with pytest.raises(IntegrityError):
            await db_session.commit()
    
    async def test_available_balance_calculation(self, db_session, sample_branch, sample_currency):
        """Test available balance property calculation"""
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("100000.00"),
            reserved_balance=Decimal("25000.00"),
        )
        
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)
        
        assert balance.available_balance == Decimal("75000.00")
    
    async def test_threshold_checks(self, db_session, sample_branch, sample_currency):
        """Test threshold checking methods"""
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("50000.00"),
            minimum_threshold=Decimal("60000.00"),  # Above current
            maximum_threshold=Decimal("40000.00"),  # Below current
        )
        
        db_session.add(balance)
        await db_session.commit()
        await db_session.refresh(balance)
        
        assert balance.is_below_minimum() is True
        assert balance.is_above_maximum() is True


# ==================== BranchBalanceHistory Tests ====================

@pytest.mark.asyncio
class TestBranchBalanceHistory:
    """Tests for BranchBalanceHistory model"""
    
    async def test_create_balance_history(self, db_session, sample_branch, sample_currency, sample_user):
        """Test creating balance history record"""
        history = BranchBalanceHistory(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            change_type=BalanceChangeType.TRANSACTION,
            amount=Decimal("5000.00"),
            balance_before=Decimal("10000.00"),
            balance_after=Decimal("15000.00"),
            reference_id=uuid.uuid4(),
            reference_type="transaction",
            performed_by=sample_user.id,
            notes="Test transaction",
        )
        
        db_session.add(history)
        await db_session.commit()
        await db_session.refresh(history)
        
        assert history.id is not None
        assert history.amount == Decimal("5000.00")
        assert history.balance_after == Decimal("15000.00")
    
    async def test_auto_log_balance_change(self, db_session, sample_branch, sample_currency):
        """Test automatic logging of balance changes via trigger"""
        # Create initial balance
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("10000.00"),
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Update balance
        balance.balance = Decimal("15000.00")
        await db_session.commit()
        
        # Check if history was auto-created
        stmt = select(BranchBalanceHistory).where(
            BranchBalanceHistory.branch_id == sample_branch.id,
            BranchBalanceHistory.currency_id == sample_currency.id
        )
        result = await db_session.execute(stmt)
        history_records = result.scalars().all()
        
        assert len(history_records) > 0
        latest_history = history_records[-1]
        assert latest_history.balance_after == Decimal("15000.00")


# ==================== BranchAlert Tests ====================

@pytest.mark.asyncio
class TestBranchAlert:
    """Tests for BranchAlert model"""
    
    async def test_create_alert(self, db_session, sample_branch, sample_currency):
        """Test creating a branch alert"""
        alert = BranchAlert(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            alert_type=BalanceAlertType.LOW_BALANCE,
            severity=AlertSeverity.WARNING,
            title="Low Balance Warning",
            message="Balance has fallen below threshold",
            triggered_at=datetime.utcnow(),
        )
        
        db_session.add(alert)
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.id is not None
        assert alert.alert_type == BalanceAlertType.LOW_BALANCE
        assert alert.severity == AlertSeverity.WARNING
        assert alert.is_resolved is False
    
    async def test_resolve_alert(self, db_session, sample_branch, sample_currency, sample_user):
        """Test resolving an alert"""
        alert = BranchAlert(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            alert_type=BalanceAlertType.LOW_BALANCE,
            severity=AlertSeverity.WARNING,
            title="Low Balance Warning",
            message="Balance has fallen below threshold",
            triggered_at=datetime.utcnow(),
        )
        
        db_session.add(alert)
        await db_session.commit()
        
        # Resolve the alert
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = sample_user.id
        alert.resolution_notes = "Balance restored"
        
        await db_session.commit()
        await db_session.refresh(alert)
        
        assert alert.is_resolved is True
        assert alert.resolved_at is not None
        assert alert.resolved_by == sample_user.id
    
    async def test_auto_alert_on_low_balance(self, db_session, sample_branch, sample_currency):
        """Test automatic alert creation on low balance"""
        # Create balance with threshold
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=sample_branch.id,
            currency_id=sample_currency.id,
            balance=Decimal("100000.00"),
            minimum_threshold=Decimal("50000.00"),
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Update balance below threshold
        balance.balance = Decimal("30000.00")
        await db_session.commit()
        
        # Check if alert was auto-created
        stmt = select(BranchAlert).where(
            BranchAlert.branch_id == sample_branch.id,
            BranchAlert.currency_id == sample_currency.id,
            BranchAlert.alert_type == BalanceAlertType.LOW_BALANCE,
            BranchAlert.is_resolved == False
        )
        result = await db_session.execute(stmt)
        alerts = result.scalars().all()
        
        assert len(alerts) > 0


# ==================== Integration Tests ====================

@pytest.mark.asyncio
class TestBranchIntegration:
    """Integration tests for branch system"""
    
    async def test_complete_branch_workflow(self, db_session, sample_user):
        """Test complete branch creation with balances and alerts"""
        # Create currency
        usd = Currency(
            id=uuid.uuid4(),
            code="USD",
            name_en="US Dollar",
            name_ar="دولار",
            symbol="$",
        )
        db_session.add(usd)
        
        # Create branch
        branch = Branch(
            id=uuid.uuid4(),
            code="BR005",
            name_en="Complete Test Branch",
            name_ar="فرع اختبار كامل",
            region=RegionEnum.ANKARA,
            address="Test St 123",
            city="Ankara",
            phone="+903121234567",
            manager_id=sample_user.id,
        )
        db_session.add(branch)
        await db_session.commit()
        
        # Create balance
        balance = BranchBalance(
            id=uuid.uuid4(),
            branch_id=branch.id,
            currency_id=usd.id,
            balance=Decimal("25000.00"),
            minimum_threshold=Decimal("50000.00"),
        )
        db_session.add(balance)
        await db_session.commit()
        
        # Verify everything was created
        await db_session.refresh(branch)
        assert len(branch.balances) == 1
        assert branch.balances[0].balance == Decimal("25000.00")
        
        # Check if low balance alert was triggered
        stmt = select(BranchAlert).where(
            BranchAlert.branch_id == branch.id,
            BranchAlert.alert_type == BalanceAlertType.LOW_BALANCE
        )
        result = await db_session.execute(stmt)
        alerts = result.scalars().all()
        assert len(alerts) > 0