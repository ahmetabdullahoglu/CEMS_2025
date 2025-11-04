# tests/unit/test_transaction_service.py
"""
Unit Tests for Transaction Service
===================================
Comprehensive tests for all transaction operations
"""

import pytest
from decimal import Decimal
from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, Mock, patch

from app.services.transaction_service import TransactionService
from app.services.balance_service import BalanceService
from app.services.currency_service import CurrencyService
from app.db.models.transaction import (
    Transaction, IncomeTransaction, ExpenseTransaction,
    ExchangeTransaction, TransferTransaction,
    TransactionType, TransactionStatus,
    IncomeCategory, ExpenseCategory, TransferType
)
from app.core.exceptions import (
    ValidationError, InsufficientBalanceError,
    BusinessRuleViolationError
)


# ==================== FIXTURES ====================

@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock(spec=AsyncSession)
    db.commit = AsyncMock()
    db.rollback = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.get = AsyncMock()
    return db


@pytest.fixture
def transaction_service(mock_db):
    """Transaction service instance"""
    return TransactionService(mock_db)


@pytest.fixture
def sample_branch_id():
    return uuid4()


@pytest.fixture
def sample_currency_id():
    return uuid4()


@pytest.fixture
def sample_user_id():
    return uuid4()


@pytest.fixture
def sample_customer_id():
    return uuid4()


# ==================== INCOME TRANSACTION TESTS ====================

class TestIncomeTransactions:
    """Test income transaction operations"""
    
    @pytest.mark.asyncio
    async def test_create_income_success(
        self, transaction_service, mock_db,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test successful income transaction creation"""
        # Setup mocks
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_branch_has_currency = AsyncMock()
        transaction_service._check_duplicate_reference = AsyncMock()
        
        # Mock transaction number generation
        transaction_service.transaction_generator.generate_number = AsyncMock(
            return_value="INC-20250109-00001"
        )
        
        # Mock balance service
        transaction_service.balance_service.update_balance = AsyncMock()
        
        # Execute
        income = await transaction_service.create_income(
            branch_id=sample_branch_id,
            amount=Decimal('1000.00'),
            currency_id=sample_currency_id,
            category=IncomeCategory.SERVICE_FEE,
            user_id=sample_user_id
        )
        
        # Assertions
        assert isinstance(income, IncomeTransaction)
        assert income.amount == Decimal('1000.00')
        assert income.transaction_type == TransactionType.INCOME
        assert income.income_category == IncomeCategory.SERVICE_FEE
        
        # Verify balance updated
        transaction_service.balance_service.update_balance.assert_called_once()
        
        # Verify commit
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_income_negative_amount(
        self, transaction_service,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test income with negative amount raises error"""
        with pytest.raises(ValidationError, match="must be positive"):
            await transaction_service.create_income(
                branch_id=sample_branch_id,
                amount=Decimal('-100.00'),
                currency_id=sample_currency_id,
                category=IncomeCategory.SERVICE_FEE,
                user_id=sample_user_id
            )
    
    @pytest.mark.asyncio
    async def test_create_income_duplicate_reference(
        self, transaction_service,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test duplicate reference number is rejected"""
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_branch_has_currency = AsyncMock()
        
        # Mock duplicate check to raise error
        transaction_service._check_duplicate_reference = AsyncMock(
            side_effect=ValidationError("Duplicate reference number")
        )
        
        with pytest.raises(ValidationError, match="Duplicate"):
            await transaction_service.create_income(
                branch_id=sample_branch_id,
                amount=Decimal('1000.00'),
                currency_id=sample_currency_id,
                category=IncomeCategory.SERVICE_FEE,
                user_id=sample_user_id,
                reference_number="REF-001"
            )
    
    @pytest.mark.asyncio
    async def test_create_income_rollback_on_error(
        self, transaction_service, mock_db,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test transaction rollback on error"""
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_branch_has_currency = AsyncMock()
        transaction_service._check_duplicate_reference = AsyncMock()
        transaction_service.transaction_generator.generate_number = AsyncMock(
            return_value="INC-20250109-00001"
        )
        
        # Make balance update fail
        transaction_service.balance_service.update_balance = AsyncMock(
            side_effect=Exception("Database error")
        )
        
        with pytest.raises(Exception):
            await transaction_service.create_income(
                branch_id=sample_branch_id,
                amount=Decimal('1000.00'),
                currency_id=sample_currency_id,
                category=IncomeCategory.SERVICE_FEE,
                user_id=sample_user_id
            )
        
        # Verify rollback called
        mock_db.rollback.assert_called()


# ==================== EXPENSE TRANSACTION TESTS ====================

class TestExpenseTransactions:
    """Test expense transaction operations"""
    
    @pytest.mark.asyncio
    async def test_create_expense_success(
        self, transaction_service, mock_db,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test successful expense transaction"""
        # Setup mocks
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_branch_has_currency = AsyncMock()
        transaction_service._check_duplicate_reference = AsyncMock()
        
        # Mock sufficient balance
        transaction_service.balance_service.get_balance = AsyncMock(
            return_value={'available_balance': 5000.00}
        )
        
        # Mock validation
        with patch('app.utils.validators.validate_transaction_limits', AsyncMock()):
            transaction_service.transaction_generator.generate_number = AsyncMock(
                return_value="EXP-20250109-00001"
            )
            transaction_service.balance_service.update_balance = AsyncMock()
            
            # Execute
            expense = await transaction_service.create_expense(
                branch_id=sample_branch_id,
                amount=Decimal('500.00'),
                currency_id=sample_currency_id,
                category=ExpenseCategory.UTILITIES,
                payee="Electric Company",
                user_id=sample_user_id
            )
            
            # Assertions
            assert isinstance(expense, ExpenseTransaction)
            assert expense.amount == Decimal('500.00')
            assert expense.expense_category == ExpenseCategory.UTILITIES
            assert expense.expense_to == "Electric Company"
    
    @pytest.mark.asyncio
    async def test_create_expense_insufficient_balance(
        self, transaction_service,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test expense with insufficient balance"""
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_branch_has_currency = AsyncMock()
        
        # Mock insufficient balance
        transaction_service.balance_service.get_balance = AsyncMock(
            return_value={'available_balance': 100.00}
        )
        
        with pytest.raises(InsufficientBalanceError):
            await transaction_service.create_expense(
                branch_id=sample_branch_id,
                amount=Decimal('500.00'),
                currency_id=sample_currency_id,
                category=ExpenseCategory.UTILITIES,
                payee="Electric Company",
                user_id=sample_user_id
            )


# ==================== EXCHANGE TRANSACTION TESTS ====================

class TestExchangeTransactions:
    """Test exchange transaction operations"""
    
    @pytest.mark.asyncio
    async def test_create_exchange_success(
        self, transaction_service, mock_db,
        sample_branch_id, sample_currency_id, sample_user_id, sample_customer_id
    ):
        """Test successful exchange transaction"""
        to_currency_id = uuid4()
        
        # Setup mocks
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._validate_customer_exists = AsyncMock()
        transaction_service._check_duplicate_reference = AsyncMock()
        
        # Mock exchange rate
        transaction_service.currency_service.get_latest_rate = AsyncMock(
            return_value={'rate': 1.5}
        )
        
        # Mock sufficient balance
        transaction_service.balance_service.get_balance = AsyncMock(
            return_value={'available_balance': 5000.00}
        )
        
        transaction_service.transaction_generator.generate_number = AsyncMock(
            return_value="EXC-20250109-00001"
        )
        transaction_service.balance_service.update_balance = AsyncMock()
        
        # Execute
        exchange = await transaction_service.create_exchange(
            branch_id=sample_branch_id,
            customer_id=sample_customer_id,
            from_currency_id=sample_currency_id,
            to_currency_id=to_currency_id,
            from_amount=Decimal('1000.00'),
            user_id=sample_user_id
        )
        
        # Assertions
        assert isinstance(exchange, ExchangeTransaction)
        assert exchange.from_amount == Decimal('1000.00')
        assert exchange.to_amount == Decimal('1500.00')  # 1000 * 1.5
        assert exchange.exchange_rate_used == Decimal('1.5')
        
        # Verify balance updated twice (from and to currencies)
        assert transaction_service.balance_service.update_balance.call_count >= 2
    
    @pytest.mark.asyncio
    async def test_create_exchange_same_currency(
        self, transaction_service,
        sample_branch_id, sample_currency_id, sample_user_id, sample_customer_id
    ):
        """Test exchange with same currencies raises error"""
        with pytest.raises(ValidationError, match="same currencies"):
            await transaction_service.create_exchange(
                branch_id=sample_branch_id,
                customer_id=sample_customer_id,
                from_currency_id=sample_currency_id,
                to_currency_id=sample_currency_id,  # Same currency!
                from_amount=Decimal('1000.00'),
                user_id=sample_user_id
            )


# ==================== TRANSFER TRANSACTION TESTS ====================

class TestTransferTransactions:
    """Test transfer transaction operations"""
    
    @pytest.mark.asyncio
    async def test_create_transfer_success(
        self, transaction_service, mock_db,
        sample_branch_id, sample_currency_id, sample_user_id
    ):
        """Test successful transfer initiation"""
        to_branch_id = uuid4()
        
        # Setup mocks
        transaction_service._validate_branch_exists = AsyncMock()
        transaction_service._validate_currency_exists = AsyncMock()
        transaction_service._check_duplicate_reference = AsyncMock()
        
        # Mock sufficient balance
        transaction_service.balance_service.get_balance = AsyncMock(
            return_value={'available_balance': 5000.00}
        )
        
        transaction_service.transaction_generator.generate_number = AsyncMock(
            return_value="TRF-20250109-00001"
        )
        transaction_service.balance_service.reserve_balance = AsyncMock()
        
        # Execute
        transfer = await transaction_service.create_transfer(
            from_branch_id=sample_branch_id,
            to_branch_id=to_branch_id,
            amount=Decimal('1000.00'),
            currency_id=sample_currency_id,
            user_id=sample_user_id
        )
        
        # Assertions
        assert isinstance(transfer, TransferTransaction)
        assert transfer.status == TransactionStatus.PENDING
        assert transfer.from_branch_id == sample_branch_id
        assert transfer.to_branch_id == to_branch_id
        
        # Verify balance reserved (not yet deducted)
        transaction_service.balance_service.reserve_balance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_transfer_success(
        self, transaction_service, mock_db, sample_user_id
    ):
        """Test completing a pending transfer"""
        transfer_id = uuid4()
        
        # Mock transfer
        mock_transfer = Mock(spec=TransferTransaction)
        mock_transfer.id = transfer_id
        mock_transfer.status = TransactionStatus.PENDING
        mock_transfer.from_branch_id = uuid4()
        mock_transfer.to_branch_id = uuid4()
        mock_transfer.currency_id = uuid4()
        mock_transfer.amount = Decimal('1000.00')
        
        mock_db.get.return_value = mock_transfer
        
        transaction_service.balance_service.update_balance = AsyncMock()
        transaction_service.balance_service.release_reserved_balance = AsyncMock()
        
        # Execute
        result = await transaction_service.complete_transfer(
            transfer_id=transfer_id,
            received_by_user_id=sample_user_id
        )
        
        # Assertions
        assert mock_transfer.status == TransactionStatus.COMPLETED
        assert mock_transfer.received_by_id == sample_user_id
        
        # Verify balances updated
        assert transaction_service.balance_service.update_balance.call_count == 2
        
        # Verify reserved balance released
        transaction_service.balance_service.release_reserved_balance.assert_called_once()


# ==================== CANCELLATION TESTS ====================

class TestTransactionCancellation:
    """Test transaction cancellation"""
    
    @pytest.mark.asyncio
    async def test_cancel_pending_income(
        self, transaction_service, mock_db, sample_user_id
    ):
        """Test cancelling pending income transaction"""
        transaction_id = uuid4()
        
        # Mock transaction
        mock_transaction = Mock(spec=IncomeTransaction)
        mock_transaction.id = transaction_id
        mock_transaction.status = TransactionStatus.PENDING
        mock_transaction.branch_id = uuid4()
        mock_transaction.currency_id = uuid4()
        mock_transaction.amount = Decimal('1000.00')
        
        mock_db.get.return_value = mock_transaction
        
        transaction_service.balance_service.update_balance = AsyncMock()
        
        # Execute
        result = await transaction_service.cancel_transaction(
            transaction_id=transaction_id,
            reason="Customer request",
            cancelled_by_user_id=sample_user_id
        )
        
        # Assertions
        assert mock_transaction.status == TransactionStatus.CANCELLED
        assert mock_transaction.cancellation_reason == "Customer request"
        
        # Verify balance reversed
        transaction_service.balance_service.update_balance.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cannot_cancel_completed_transaction(
        self, transaction_service, mock_db
    ):
        """Test cannot cancel completed transaction"""
        transaction_id = uuid4()
        
        # Mock completed transaction
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = transaction_id
        mock_transaction.status = TransactionStatus.COMPLETED
        
        mock_db.get.return_value = mock_transaction
        
        # Execute & Assert
        with pytest.raises(ValidationError, match="Only PENDING"):
            await transaction_service.cancel_transaction(
                transaction_id=transaction_id,
                reason="Cannot cancel",
                cancelled_by_user_id=uuid4()
            )


# ==================== QUERY TESTS ====================

class TestTransactionQueries:
    """Test transaction query methods"""
    
    @pytest.mark.asyncio
    async def test_get_transaction_by_id(
        self, transaction_service, mock_db
    ):
        """Test getting transaction by ID"""
        transaction_id = uuid4()
        
        mock_transaction = Mock(spec=Transaction)
        mock_transaction.id = transaction_id
        
        mock_db.get.return_value = mock_transaction
        
        # Execute
        result = await transaction_service.get_transaction(transaction_id)
        
        # Assertions
        assert result == mock_transaction
        mock_db.get.assert_called_once_with(Transaction, transaction_id)


# ==================== INTEGRATION SCENARIOS ====================

class TestIntegrationScenarios:
    """Test complete transaction scenarios"""
    
    @pytest.mark.asyncio
    async def test_full_exchange_workflow(
        self, transaction_service,
        sample_branch_id, sample_currency_id, sample_customer_id, sample_user_id
    ):
        """
        Test complete exchange workflow:
        1. Create exchange
        2. Verify balances updated
        3. Verify commission recorded
        """
        # This would be a full integration test
        # with real database transactions
        pass


# ==================== RUN TESTS ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
