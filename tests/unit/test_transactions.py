"""
Transaction Models Unit Tests
==============================
Comprehensive tests for all transaction types and business logic.

Test Coverage:
- Transaction number generation
- Status state machine
- Income transactions
- Expense transactions (with approval)
- Exchange transactions (with rates)
- Transfer transactions (with receipt)
- Validation and constraints
- Immutability of completed transactions
"""

import pytest
from datetime import datetime, timedelta
from decimal import Decimal
from uuid import uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

# Import models (adjust path as needed)
from app.db.models.transaction import (
    Transaction,
    IncomeTransaction,
    ExpenseTransaction,
    ExchangeTransaction,
    TransferTransaction,
    TransactionType,
    TransactionStatus,
    IncomeCategory,
    ExpenseCategory,
    TransferType,
    TransactionNumberGenerator
)


# ==================== Fixtures ====================

@pytest.fixture
def sample_branch_id():
    """Sample branch UUID"""
    return uuid4()


@pytest.fixture
def sample_user_id():
    """Sample user UUID"""
    return uuid4()


@pytest.fixture
def sample_customer_id():
    """Sample customer UUID"""
    return uuid4()


@pytest.fixture
def sample_currency_id():
    """Sample currency UUID"""
    return uuid4()


@pytest.fixture
def sample_usd_id():
    """USD currency ID"""
    return uuid4()


@pytest.fixture
def sample_sar_id():
    """SAR currency ID"""
    return uuid4()


# ==================== Base Transaction Tests ====================

class TestBaseTransaction:
    """Test base transaction functionality"""
    
    def test_create_base_transaction(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test creating a base transaction"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("100.50"),
            status=TransactionStatus.PENDING,
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(transaction)
        db_session.commit()
        
        assert transaction.id is not None
        assert transaction.transaction_number == "TRX-20250109-00001"
        assert transaction.amount == Decimal("100.50")
        assert transaction.status == TransactionStatus.PENDING
    
    def test_transaction_number_uniqueness(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test that transaction numbers must be unique"""
        transaction1 = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("100.00"),
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction1)
        db_session.commit()
        
        # Try to create another with same number
        transaction2 = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",  # Same number
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("200.00"),
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction2)
        
        with pytest.raises(IntegrityError):
            db_session.commit()
    
    def test_amount_must_be_positive(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test that amount must be positive"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("-100.00"),  # Negative amount
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==================== Status State Machine Tests ====================

class TestStatusStateMachine:
    """Test transaction status transitions"""
    
    def test_pending_to_completed(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test valid transition: pending -> completed"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("100.00"),
            status=TransactionStatus.PENDING,
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Complete the transaction
        transaction.complete(sample_user_id)
        db_session.commit()
        
        assert transaction.status == TransactionStatus.COMPLETED
        assert transaction.completed_at is not None
    
    def test_pending_to_cancelled(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test valid transition: pending -> cancelled"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("100.00"),
            status=TransactionStatus.PENDING,
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction)
        db_session.commit()
        
        # Cancel the transaction
        transaction.cancel(sample_user_id, "Customer request")
        db_session.commit()
        
        assert transaction.status == TransactionStatus.CANCELLED
        assert transaction.cancelled_at is not None
        assert transaction.cancelled_by_id == sample_user_id
        assert transaction.cancellation_reason == "Customer request"

    def test_transfer_in_transit_transition(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Transfers can move from pending -> in_transit -> completed"""
        transfer = TransferTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00099",
            transaction_type=TransactionType.TRANSFER,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("2500.00"),
            status=TransactionStatus.PENDING,
            from_branch_id=sample_branch_id,
            to_branch_id=uuid4(),
            transfer_type=TransferType.BRANCH_TO_BRANCH,
            transaction_date=datetime.utcnow()
        )

        db_session.add(transfer)
        db_session.commit()

        transfer.status = TransactionStatus.IN_TRANSIT
        db_session.commit()
        assert transfer.status == TransactionStatus.IN_TRANSIT

        transfer.status = TransactionStatus.COMPLETED
        transfer.completed_at = datetime.utcnow()
        db_session.commit()
        assert transfer.status == TransactionStatus.COMPLETED

    def test_completed_immutable(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test that completed transactions cannot be modified"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("100.00"),
            status=TransactionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            transaction_date=datetime.utcnow()
        )
        db_session.add(transaction)
        db_session.commit()

        # Try to cancel completed transaction
        with pytest.raises(ValueError, match="Only pending transactions can be cancelled"):
            transaction.cancel(sample_user_id, "Trying to cancel completed")

    def test_completed_status_sets_completed_at_before_commit(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Transactions saved as completed automatically populate completed_at"""
        transaction = Transaction(
            id=uuid4(),
            transaction_number=f"TRX-AUTO-{uuid4().hex[:6].upper()}",
            transaction_type=TransactionType.INCOME,
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("250.00"),
            status=TransactionStatus.COMPLETED,
            transaction_date=datetime.utcnow()
        )

        db_session.add(transaction)
        db_session.commit()

        assert transaction.completed_at is not None


# ==================== Income Transaction Tests ====================

class TestIncomeTransaction:
    """Test income transaction specific functionality"""
    
    def test_create_income_transaction(
        self, db_session, sample_branch_id, sample_user_id, 
        sample_customer_id, sample_currency_id
    ):
        """Test creating income transaction"""
        income = IncomeTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            customer_id=sample_customer_id,
            currency_id=sample_currency_id,
            amount=Decimal("150.00"),
            income_category=IncomeCategory.SERVICE_FEE,
            income_source="Money transfer service",
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(income)
        db_session.commit()
        
        assert income.transaction_type == TransactionType.INCOME
        assert income.income_category == IncomeCategory.SERVICE_FEE
        assert income.income_source == "Money transfer service"
        assert income.amount == Decimal("150.00")
    
    def test_income_categories(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test different income categories"""
        categories = [
            IncomeCategory.SERVICE_FEE,
            IncomeCategory.EXCHANGE_COMMISSION,
            IncomeCategory.TRANSFER_FEE,
            IncomeCategory.INTEREST,
            IncomeCategory.COMMISSION,
            IncomeCategory.OTHER,
        ]
        
        for i, category in enumerate(categories):
            income = IncomeTransaction(
                id=uuid4(),
                transaction_number=f"TRX-20250109-{i+1:05d}",
                branch_id=sample_branch_id,
                user_id=sample_user_id,
                currency_id=sample_currency_id,
                amount=Decimal("100.00"),
                income_category=category,
                transaction_date=datetime.utcnow()
            )
            db_session.add(income)
        
        db_session.commit()
        
        # Verify all created
        incomes = db_session.query(IncomeTransaction).all()
        assert len(incomes) == len(categories)


# ==================== Expense Transaction Tests ====================

class TestExpenseTransaction:
    """Test expense transaction specific functionality"""
    
    def test_create_expense_transaction(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test creating expense transaction"""
        expense = ExpenseTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("5000.00"),
            expense_category=ExpenseCategory.RENT,
            expense_to="Property Owner LLC",
            approval_required=False,
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(expense)
        db_session.commit()
        
        assert expense.transaction_type == TransactionType.EXPENSE
        assert expense.expense_category == ExpenseCategory.RENT
        assert expense.expense_to == "Property Owner LLC"
        assert not expense.approval_required

    def test_expense_categories(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test creating expenses across the supported categories"""
        categories = [
            ExpenseCategory.RENT,
            ExpenseCategory.SALARIES,
            ExpenseCategory.MARKETING,
            ExpenseCategory.UTILITIES,
            ExpenseCategory.MAINTENANCE,
            ExpenseCategory.SUPPLIES,
            ExpenseCategory.OTHER,
        ]

        for idx, category in enumerate(categories):
            expense = ExpenseTransaction(
                id=uuid4(),
                transaction_number=f"TRX-EXP-{idx+1:05d}",
                branch_id=sample_branch_id,
                user_id=sample_user_id,
                currency_id=sample_currency_id,
                amount=Decimal("250.00"),
                expense_category=category,
                expense_to=f"Vendor {idx}",
                transaction_date=datetime.utcnow(),
            )
            db_session.add(expense)

        db_session.commit()

        expenses = db_session.query(ExpenseTransaction).all()
        assert len(expenses) >= len(categories)

    def test_expense_approval_workflow(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test expense approval workflow"""
        approver_id = uuid4()
        
        expense = ExpenseTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("10000.00"),
            expense_category=ExpenseCategory.SALARY,
            expense_to="Employee Name",
            approval_required=True,
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(expense)
        db_session.commit()
        
        # Initially not approved
        assert not expense.is_approved
        
        # Approve expense
        expense.approve(approver_id)
        db_session.commit()
        
        assert expense.is_approved
        assert expense.approved_by_id == approver_id
        assert expense.approved_at is not None
    
    def test_cannot_approve_twice(
        self, db_session, sample_branch_id, sample_user_id, sample_currency_id
    ):
        """Test that expense cannot be approved twice"""
        approver_id = uuid4()
        
        expense = ExpenseTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("10000.00"),
            expense_category=ExpenseCategory.SALARY,
            expense_to="Employee Name",
            approval_required=True,
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(expense)
        expense.approve(approver_id)
        db_session.commit()
        
        # Try to approve again
        with pytest.raises(ValueError, match="Expense already approved"):
            expense.approve(uuid4())


# ==================== Exchange Transaction Tests ====================

class TestExchangeTransaction:
    """Test exchange transaction specific functionality"""
    
    def test_create_exchange_transaction(
        self, db_session, sample_branch_id, sample_user_id,
        sample_customer_id, sample_currency_id, sample_usd_id, sample_sar_id
    ):
        """Test creating exchange transaction"""
        exchange = ExchangeTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            customer_id=sample_customer_id,
            currency_id=sample_currency_id,
            amount=Decimal("1000.00"),
            from_currency_id=sample_usd_id,
            to_currency_id=sample_sar_id,
            from_amount=Decimal("1000.00"),
            to_amount=Decimal("3750.00"),
            exchange_rate_used=Decimal("3.75"),
            commission_percentage=Decimal("1.5"),
            commission_amount=Decimal("15.00"),
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(exchange)
        db_session.commit()
        
        assert exchange.transaction_type == TransactionType.EXCHANGE
        assert exchange.from_amount == Decimal("1000.00")
        assert exchange.to_amount == Decimal("3750.00")
        assert exchange.exchange_rate_used == Decimal("3.75")
        assert exchange.commission_amount == Decimal("15.00")
    
    def test_exchange_effective_rate(
        self, db_session, sample_branch_id, sample_user_id,
        sample_currency_id, sample_usd_id, sample_sar_id
    ):
        """Test effective rate calculation"""
        exchange = ExchangeTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("1000.00"),
            from_currency_id=sample_usd_id,
            to_currency_id=sample_sar_id,
            from_amount=Decimal("1000.00"),
            to_amount=Decimal("3750.00"),
            exchange_rate_used=Decimal("3.75"),
            commission_percentage=Decimal("0.00"),
            commission_amount=Decimal("0.00"),
            transaction_date=datetime.utcnow()
        )
        
        assert exchange.effective_rate == Decimal("3.75")
        assert exchange.total_cost == Decimal("1000.00")
    
    def test_cannot_exchange_same_currency(
        self, db_session, sample_branch_id, sample_user_id,
        sample_currency_id, sample_usd_id
    ):
        """Test that cannot exchange same currency"""
        exchange = ExchangeTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("1000.00"),
            from_currency_id=sample_usd_id,
            to_currency_id=sample_usd_id,  # Same currency
            from_amount=Decimal("1000.00"),
            to_amount=Decimal("1000.00"),
            exchange_rate_used=Decimal("1.00"),
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(exchange)
        
        with pytest.raises(IntegrityError):
            db_session.commit()


# ==================== Transfer Transaction Tests ====================

class TestTransferTransaction:
    """Test transfer transaction specific functionality"""
    
    def test_create_transfer_transaction(
        self, db_session, sample_user_id, sample_currency_id
    ):
        """Test creating transfer transaction"""
        from_branch_id = uuid4()
        to_branch_id = uuid4()
        
        transfer = TransferTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=from_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("10000.00"),
            from_branch_id=from_branch_id,
            to_branch_id=to_branch_id,
            transfer_type=TransferType.BRANCH_TO_BRANCH,
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        assert transfer.transaction_type == TransactionType.TRANSFER
        assert transfer.transfer_type == TransferType.BRANCH_TO_BRANCH
        assert transfer.from_branch_id == from_branch_id
        assert transfer.to_branch_id == to_branch_id
    
    def test_transfer_receipt(
        self, db_session, sample_user_id, sample_currency_id
    ):
        """Test transfer receipt workflow"""
        from_branch_id = uuid4()
        to_branch_id = uuid4()
        receiver_id = uuid4()
        
        transfer = TransferTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=from_branch_id,
            user_id=sample_user_id,
            currency_id=sample_currency_id,
            amount=Decimal("10000.00"),
            from_branch_id=from_branch_id,
            to_branch_id=to_branch_id,
            transfer_type=TransferType.BRANCH_TO_BRANCH,
            status=TransactionStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(transfer)
        db_session.commit()
        
        # Initially not received
        assert not transfer.is_received
        assert transfer.is_pending_receipt
        
        # Mark as received
        transfer.mark_as_received(receiver_id)
        db_session.commit()
        
        assert transfer.is_received
        assert not transfer.is_pending_receipt
        assert transfer.received_by_id == receiver_id
        assert transfer.received_at is not None
    
    def test_cannot_transfer_to_same_branch(
        self, db_session, sample_user_id, sample_currency_id
    ):
        """Test that cannot transfer to same branch"""
        branch_id = uuid4()

        with pytest.raises(ValueError, match="Source and destination branches must be different"):
            TransferTransaction(
                id=uuid4(),
                transaction_number="TRX-20250109-00001",
                branch_id=branch_id,
                user_id=sample_user_id,
                currency_id=sample_currency_id,
                amount=Decimal("10000.00"),
                from_branch_id=branch_id,
                to_branch_id=branch_id,  # Same branch
                transfer_type=TransferType.BRANCH_TO_BRANCH,
                transaction_date=datetime.utcnow()
            )


# ==================== Transaction Number Generator Tests ====================

class TestTransactionNumberGenerator:
    """Test transaction number generation"""
    
    def test_generate_sequential_numbers(self, db_session):
        """Test sequential number generation"""
        today = datetime.utcnow()
        
        # Generate first number
        number1 = TransactionNumberGenerator.generate(db_session, today)
        assert number1.startswith(f"TRX-{today.strftime('%Y%m%d')}-")
        assert number1.endswith("00001")
        
        # Generate second number (mock by creating transaction)
        # In real scenario, would create actual transaction
        # Here we test the format
        assert len(number1) == 19  # TRX-YYYYMMDD-NNNNN


# ==================== Integration Tests ====================

class TestTransactionIntegration:
    """Integration tests for transaction system"""
    
    def test_complete_transaction_lifecycle(
        self, db_session, sample_branch_id, sample_user_id,
        sample_customer_id, sample_currency_id
    ):
        """Test complete lifecycle of a transaction"""
        # Create pending transaction
        income = IncomeTransaction(
            id=uuid4(),
            transaction_number="TRX-20250109-00001",
            branch_id=sample_branch_id,
            user_id=sample_user_id,
            customer_id=sample_customer_id,
            currency_id=sample_currency_id,
            amount=Decimal("500.00"),
            income_category=IncomeCategory.COMMISSION,
            income_source="Currency exchange commission",
            transaction_date=datetime.utcnow()
        )
        
        db_session.add(income)
        db_session.commit()
        
        # Verify pending status
        assert income.status == TransactionStatus.PENDING
        assert income.is_cancellable
        assert income.is_mutable
        
        # Complete transaction
        income.complete(sample_user_id)
        db_session.commit()
        
        # Verify completed status
        assert income.status == TransactionStatus.COMPLETED
        assert income.is_completed
        assert not income.is_cancellable
        assert not income.is_mutable
        assert income.completed_at is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
