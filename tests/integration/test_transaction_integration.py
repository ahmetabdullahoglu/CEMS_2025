# tests/integration/test_transaction_integration.py
"""
Integration Tests for Transaction Service
==========================================
Tests for concurrent scenarios, race conditions, and database integrity
"""

import pytest
import asyncio
from decimal import Decimal
from datetime import datetime, date
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from app.services.transaction_service import TransactionService
from app.services.balance_service import BalanceService
from app.db.models.transaction import (
    TransactionType, TransactionStatus,
    IncomeCategory, ExpenseCategory
)
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency, ExchangeRate
from app.db.models.user import User
from app.db.models.customer import Customer, CustomerType, RiskLevel
from app.core.exceptions import InsufficientBalanceError


# ==================== TEST DATABASE SETUP ====================

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    # Use test database
    DATABASE_URL = "postgresql+asyncpg://test_user:test_pass@localhost/cems_test"
    
    engine = create_async_engine(
        DATABASE_URL,
        echo=False,
        poolclass=NullPool  # Disable pooling for tests
    )
    
    yield engine
    
    await engine.dispose()


@pytest.fixture
async def db_session(test_engine):
    """Create database session for each test"""
    async_session = sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        # Start transaction
        await session.begin()
        
        yield session
        
        # Rollback after test
        await session.rollback()


# ==================== TEST DATA FIXTURES ====================

@pytest.fixture
async def test_branch(db_session):
    """Create test branch"""
    branch = Branch(
        code="BR-TEST-001",
        name_en="Test Branch",
        name_ar="فرع تجريبي",
        region="Istanbul_European",
        is_active=True
    )
    
    db_session.add(branch)
    await db_session.flush()
    
    return branch


@pytest.fixture
async def test_currency(db_session):
    """Create test currency"""
    currency = Currency(
        code="USD",
        name_en="US Dollar",
        name_ar="دولار أمريكي",
        symbol="$",
        is_base_currency=True,
        is_active=True
    )
    
    db_session.add(currency)
    await db_session.flush()
    
    return currency


@pytest.fixture
async def branch_balance(db_session, test_branch, test_currency):
    """Create test branch balance"""
    balance = BranchBalance(
        branch_id=test_branch.id,
        currency_id=test_currency.id,
        balance=Decimal('10000.00'),
        reserved_balance=Decimal('0.00'),
        minimum_threshold=Decimal('1000.00'),
        maximum_threshold=Decimal('50000.00')
    )
    
    db_session.add(balance)
    await db_session.flush()
    
    return balance


# ==================== CONCURRENT TRANSACTION TESTS ====================

class TestConcurrentTransactions:
    """Test concurrent transaction scenarios"""
    
    @pytest.mark.asyncio
    async def test_concurrent_expenses_sufficient_balance(
        self, db_session, test_branch, test_currency, branch_balance
    ):
        """
        Test multiple concurrent expenses with sufficient balance
        
        Scenario:
        - Initial balance: 10,000
        - 5 concurrent expenses of 1,000 each
        - Expected: All succeed, final balance: 5,000
        """
        service = TransactionService(db_session)
        user_id = uuid4()
        
        # Create 5 concurrent expenses
        async def create_expense(amount):
            return await service.create_expense(
                branch_id=test_branch.id,
                amount=amount,
                currency_id=test_currency.id,
                category=ExpenseCategory.UTILITIES,
                payee="Test Payee",
                user_id=user_id
            )
        
        # Execute concurrently
        tasks = [
            create_expense(Decimal('1000.00'))
            for _ in range(5)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all succeeded
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) == 5
        
        # Verify final balance
        await db_session.refresh(branch_balance)
        assert branch_balance.balance == Decimal('5000.00')
    
    @pytest.mark.asyncio
    async def test_concurrent_expenses_insufficient_balance(
        self, db_session, test_branch, test_currency, branch_balance
    ):
        """
        Test concurrent expenses exceeding available balance
        
        Scenario:
        - Initial balance: 10,000
        - 15 concurrent expenses of 1,000 each
        - Expected: ~10 succeed, ~5 fail with insufficient balance
        """
        service = TransactionService(db_session)
        user_id = uuid4()
        
        async def create_expense(amount):
            try:
                return await service.create_expense(
                    branch_id=test_branch.id,
                    amount=amount,
                    currency_id=test_currency.id,
                    category=ExpenseCategory.UTILITIES,
                    payee="Test Payee",
                    user_id=user_id
                )
            except InsufficientBalanceError:
                return None
        
        # Execute 15 concurrent expenses
        tasks = [
            create_expense(Decimal('1000.00'))
            for _ in range(15)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Count successful vs failed
        successful = [r for r in results if r is not None]
        failed = [r for r in results if r is None]
        
        # Should have ~10 successful (balance allows)
        assert len(successful) <= 10
        assert len(failed) >= 5
        
        # Verify balance is not negative
        await db_session.refresh(branch_balance)
        assert branch_balance.balance >= Decimal('0')
    
    @pytest.mark.asyncio
    async def test_concurrent_income_and_expense(
        self, db_session, test_branch, test_currency, branch_balance
    ):
        """
        Test mixed concurrent income and expense transactions
        
        Scenario:
        - Simultaneous income and expense operations
        - Verify balance consistency
        """
        service = TransactionService(db_session)
        user_id = uuid4()
        
        async def create_income(amount):
            return await service.create_income(
                branch_id=test_branch.id,
                amount=amount,
                currency_id=test_currency.id,
                category=IncomeCategory.SERVICE_FEE,
                user_id=user_id
            )
        
        async def create_expense(amount):
            return await service.create_expense(
                branch_id=test_branch.id,
                amount=amount,
                currency_id=test_currency.id,
                category=ExpenseCategory.UTILITIES,
                payee="Test Payee",
                user_id=user_id
            )
        
        # Mix of income and expenses
        tasks = []
        for i in range(10):
            if i % 2 == 0:
                tasks.append(create_income(Decimal('500.00')))
            else:
                tasks.append(create_expense(Decimal('300.00')))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # All should succeed
        successful = [r for r in results if not isinstance(r, Exception)]
        assert len(successful) == 10
        
        # Calculate expected balance
        # Initial: 10,000
        # Income: 5 * 500 = 2,500
        # Expense: 5 * 300 = 1,500
        # Expected: 10,000 + 2,500 - 1,500 = 11,000
        
        await db_session.refresh(branch_balance)
        assert branch_balance.balance == Decimal('11000.00')


# ==================== TRANSFER WORKFLOW TESTS ====================

class TestTransferWorkflow:
    """Test complete transfer workflows"""
    
    @pytest.mark.asyncio
    async def test_full_transfer_workflow(
        self, db_session, test_currency
    ):
        """
        Test complete branch transfer workflow:
        1. Initiate transfer
        2. Verify balance reserved
        3. Complete transfer
        4. Verify balances updated
        """
        # Create two branches
        branch_a = Branch(
            code="BR-A",
            name_en="Branch A",
            name_ar="فرع أ",
            is_active=True
        )
        branch_b = Branch(
            code="BR-B",
            name_en="Branch B",
            name_ar="فرع ب",
            is_active=True
        )
        
        db_session.add_all([branch_a, branch_b])
        await db_session.flush()
        
        # Create balances
        balance_a = BranchBalance(
            branch_id=branch_a.id,
            currency_id=test_currency.id,
            balance=Decimal('5000.00'),
            reserved_balance=Decimal('0.00')
        )
        balance_b = BranchBalance(
            branch_id=branch_b.id,
            currency_id=test_currency.id,
            balance=Decimal('3000.00'),
            reserved_balance=Decimal('0.00')
        )
        
        db_session.add_all([balance_a, balance_b])
        await db_session.flush()
        
        service = TransactionService(db_session)
        user_id = uuid4()
        
        # Step 1: Initiate transfer
        transfer = await service.create_transfer(
            from_branch_id=branch_a.id,
            to_branch_id=branch_b.id,
            amount=Decimal('1000.00'),
            currency_id=test_currency.id,
            user_id=user_id
        )
        
        assert transfer.status == TransactionStatus.PENDING
        
        # Step 2: Verify balance reserved
        await db_session.refresh(balance_a)
        assert balance_a.reserved_balance == Decimal('1000.00')
        assert balance_a.balance == Decimal('5000.00')  # Not yet deducted
        
        # Step 3: Complete transfer
        completed = await service.complete_transfer(
            transfer_id=transfer.id,
            received_by_user_id=uuid4()
        )
        
        assert completed.status == TransactionStatus.COMPLETED
        
        # Step 4: Verify final balances
        await db_session.refresh(balance_a)
        await db_session.refresh(balance_b)
        
        assert balance_a.balance == Decimal('4000.00')  # 5000 - 1000
        assert balance_a.reserved_balance == Decimal('0.00')
        assert balance_b.balance == Decimal('4000.00')  # 3000 + 1000


# ==================== EXCHANGE RATE TESTS ====================

class TestExchangeTransactions:
    """Test exchange transaction scenarios"""

    @pytest.mark.asyncio
    async def test_exchange_with_commission(
        self,
        db_session,
        test_branch,
        test_currency,
        branch_balance
    ):
        """Ensure exchange transactions fill required fields and respect constraints"""
        # Create user executing the exchange
        user = User(
            username=f"exchange_user_{uuid4().hex[:8]}",
            email=f"exchange{uuid4().hex[:6]}@test.com",
            hashed_password="hashedpassword",
            full_name="Exchange User",
            is_active=True,
            is_superuser=False,
            primary_branch_id=test_branch.id
        )

        # Create target currency and its balance record
        eur_currency = Currency(
            code="EUR",
            name_en="Euro",
            name_ar="يورو",
            symbol="€",
            is_active=True
        )

        db_session.add_all([user, eur_currency])
        await db_session.flush()

        eur_balance = BranchBalance(
            branch_id=test_branch.id,
            currency_id=eur_currency.id,
            balance=Decimal('5000.00'),
            reserved_balance=Decimal('0.00')
        )

        db_session.add(eur_balance)

        # Create customer tied to the branch
        customer = Customer(
            first_name="Integration",
            last_name="Customer",
            phone_number="+905551112233",
            email="integration.customer@test.com",
            date_of_birth=date(1990, 1, 1),
            nationality="Turkey",
            address="Integration Street",
            city="Istanbul",
            country="Turkey",
            customer_type=CustomerType.INDIVIDUAL,
            risk_level=RiskLevel.LOW,
            branch_id=test_branch.id,
            registered_by_id=user.id
        )

        # Seed exchange rate required by CurrencyService
        exchange_rate = ExchangeRate(
            from_currency_id=test_currency.id,
            to_currency_id=eur_currency.id,
            rate=Decimal('3.75'),
            set_by=user.id
        )

        db_session.add_all([customer, exchange_rate])
        await db_session.flush()

        service = TransactionService(db_session)
        from_amount = Decimal('250.00')
        description = "Integration exchange test"

        exchange = await service.create_exchange(
            branch_id=test_branch.id,
            customer_id=customer.id,
            from_currency_id=test_currency.id,
            to_currency_id=eur_currency.id,
            from_amount=from_amount,
            user_id=user.id,
            description=description
        )

        # Required fields should be populated like other transaction types
        assert exchange.currency_id == test_currency.id
        assert exchange.amount == from_amount
        assert exchange.user_id == user.id
        assert exchange.description == description
        assert exchange.status == TransactionStatus.COMPLETED

        expected_to_amount = from_amount * Decimal('3.75')
        commission_amount = from_amount * Decimal('0.01')

        assert exchange.from_amount == from_amount
        assert exchange.to_amount == expected_to_amount
        assert exchange.commission_amount == commission_amount

        # Balances should reflect deductions/additions without violating constraints
        await db_session.refresh(branch_balance)
        await db_session.refresh(eur_balance)

        assert branch_balance.balance == Decimal('10000.00') - from_amount + commission_amount
        assert eur_balance.balance == Decimal('5000.00') + expected_to_amount


# ==================== ROLLBACK TESTS ====================

class TestTransactionRollback:
    """Test transaction rollback scenarios"""
    
    @pytest.mark.asyncio
    async def test_rollback_on_balance_update_failure(
        self, db_session, test_branch, test_currency, branch_balance
    ):
        """
        Test that transaction is rolled back if balance update fails
        """
        service = TransactionService(db_session)
        
        # Mock balance service to fail
        original_update = service.balance_service.update_balance
        
        async def failing_update(*args, **kwargs):
            raise Exception("Simulated database error")
        
        service.balance_service.update_balance = failing_update
        
        initial_balance = branch_balance.balance
        
        # Try to create income (should fail and rollback)
        with pytest.raises(Exception):
            await service.create_income(
                branch_id=test_branch.id,
                amount=Decimal('1000.00'),
                currency_id=test_currency.id,
                category=IncomeCategory.SERVICE_FEE,
                user_id=uuid4()
            )
        
        # Verify balance unchanged
        await db_session.refresh(branch_balance)
        assert branch_balance.balance == initial_balance


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-s"])
