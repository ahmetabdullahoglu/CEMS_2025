# app/services/transaction_service.py
"""
Transaction Service - Core Business Logic
==========================================
Handles all transaction operations with ACID guarantees:
- Income transactions (service fees, commissions)
- Expense transactions (rent, salaries, utilities)
- Exchange transactions (currency conversion)
- Transfer transactions (branch-to-branch, vault-to-branch)

CRITICAL: All operations are atomic with proper rollback on failures
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, Dict, Any, List
from uuid import UUID

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import selectinload, selectin_polymorphic

from app.db.models.transaction import (
    Transaction, IncomeTransaction, ExpenseTransaction,
    ExchangeTransaction, TransferTransaction,
    TransactionType, TransactionStatus,
    IncomeCategory, ExpenseCategory, TransferType,
    TransactionNumberGenerator
)
from app.db.models.branch import BranchBalance, BalanceChangeType
from app.db.models.currency import Currency, ExchangeRate
from app.services.balance_service import BalanceService
from app.services.currency_service import CurrencyService
from app.core.exceptions import (
    ValidationError, InsufficientBalanceError,
    BusinessRuleViolationError, DatabaseOperationError
)
from app.utils.logger import get_logger
from app.utils.validators import (
    validate_positive_amount, validate_transaction_limits
)
from app.utils.decorators import retry_on_deadlock


logger = get_logger(__name__)


class TransactionService:
    """
    Transaction Service handling all transaction business logic
    
    CRITICAL PRINCIPLES:
    1. All operations are atomic (commit or rollback)
    2. Balance updates must happen in same transaction
    3. No orphaned records on failures
    4. Comprehensive audit trail
    5. Proper error handling with meaningful messages
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.balance_service = BalanceService(db)
        self.currency_service = CurrencyService(db)
        self.transaction_generator = TransactionNumberGenerator()

    # ==================== INTERNAL HELPERS ====================

    def _transaction_relationship_options(self):
        """Common relationship loading options to prevent async lazy loads."""
        return (
            selectin_polymorphic(Transaction, [TransferTransaction]),
            selectinload(Transaction.branch),
            selectinload(Transaction.currency),
            selectinload(TransferTransaction.from_branch),
            selectinload(TransferTransaction.to_branch),
            selectinload(ExchangeTransaction.from_currency),
            selectinload(ExchangeTransaction.to_currency),
        )

    async def _load_transaction_with_relationships(
        self,
        transaction_id: UUID,
        model: type[Transaction] = Transaction,
    ) -> Transaction:
        """Reload a transaction with all relationships eagerly loaded."""
        stmt = (
            select(model)
            .options(*self._transaction_relationship_options())
            .where(model.id == transaction_id)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()
    
    # ==================== INCOME TRANSACTIONS ====================
    @retry_on_deadlock(max_attempts=3)
    async def create_income_transaction(
        self,
        transaction: 'IncomeTransactionCreate',
        user_id: UUID
    ) -> IncomeTransaction:
        """
        Create income transaction from schema

        Args:
            transaction: IncomeTransactionCreate schema
            user_id: User creating the transaction

        Returns:
            Created IncomeTransaction
        """
        return await self.create_income(
            branch_id=transaction.branch_id,
            amount=transaction.amount,
            currency_id=transaction.currency_id,
            category=transaction.income_category,
            user_id=user_id,
            customer_id=transaction.customer_id,
            reference_number=transaction.reference_number,
            description=transaction.description,
            notes=transaction.notes
        )

    async def create_income(
        self,
        branch_id: UUID,
        amount: Decimal,
        currency_id: UUID,
        category: IncomeCategory,
        user_id: UUID,
        customer_id: Optional[UUID] = None,
        reference_number: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> IncomeTransaction:
        """
        Create income transaction (atomic operation)
        
        Steps:
        1. Validate inputs
        2. Generate transaction number
        3. Start DB transaction
        4. Create income record
        5. Update branch balance (+amount)
        6. Create balance history
        7. Commit or rollback
        
        Args:
            branch_id: Branch receiving income
            amount: Income amount (must be positive)
            currency_id: Currency of transaction
            category: Income category (SERVICE_FEE, EXCHANGE_COMMISSION, TRANSFER_FEE, etc.)
            user_id: User executing transaction
            customer_id: Optional customer reference
            reference_number: Optional external reference
            description: Optional transaction description
            notes: Optional transaction notes
            
        Returns:
            Created IncomeTransaction
            
        Raises:
            ValidationError: Invalid inputs
            DatabaseOperationError: Transaction failed
        """
        try:
            # Step 1: Validate inputs
            validate_positive_amount(amount)
            await self._validate_branch_exists(branch_id)
            await self._validate_currency_exists(currency_id)
            await self._validate_branch_has_currency(branch_id, currency_id)
            
            if customer_id:
                await self._validate_customer_exists(customer_id)
            
            # Check for duplicate reference number
            if reference_number:
                await self._check_duplicate_reference(reference_number)
            
            # Step 2: Generate transaction number
            transaction_number = await self.transaction_generator.generate(
                self.db
            )
            
            # Step 3-7: Atomic operation
            try:
                # Create income transaction
                description_value = description or notes

                income = IncomeTransaction(
                    transaction_number=transaction_number,
                    status=TransactionStatus.PENDING,
                    amount=amount,
                    currency_id=currency_id,
                    branch_id=branch_id,
                    user_id=user_id,
                    customer_id=customer_id,
                    reference_number=reference_number,
                    description=description_value,
                    notes=notes,
                    income_category=category,
                    transaction_date=datetime.utcnow()
                )
                
                self.db.add(income)
                await self.db.flush()  # Get ID but don't commit yet
                
                # Update branch balance
                await self.balance_service.update_balance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    amount=amount,
                    change_type=BalanceChangeType.TRANSACTION,
                    reference_id=income.id,
                    reference_type="transaction",
                    notes=f"Income: {category.value}"
                )
                
                # Mark transaction as completed
                income.status = TransactionStatus.COMPLETED
                income.completed_at = datetime.utcnow()

                # Commit everything
                await self.db.commit()

                income = await self._load_transaction_with_relationships(
                    income.id, IncomeTransaction
                )

                logger.info(
                    f"Income transaction created: {transaction_number}, "
                    f"Branch: {branch_id}, Amount: {amount} {currency_id}"
                )
                
                return income
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to create income transaction: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to create income transaction: {str(e)}"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_income: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    # في app/services/transaction_service.py

    async def list_transactions(
        self,
        filters: 'TransactionFilter',
        skip: int = 0,
        limit: int = 50
    ) -> Dict[str, Any]:
        """
        List transactions with filters and pagination
        
        Args:
            filters: TransactionFilter object with filter criteria
            skip: Number of records to skip
            limit: Number of records to return
            
        Returns:
            Dict with 'transactions' list and 'total' count
        """
        try:
            logger.info(f"Listing transactions with filters: {filters.dict(exclude_none=True)}")
            
            # Build base query with eager loading to avoid async lazy-load issues
            query = select(Transaction).options(
                selectin_polymorphic(Transaction, [TransferTransaction]),
                selectinload(Transaction.branch),
                selectinload(Transaction.currency),
                selectinload(TransferTransaction.from_branch),
                selectinload(TransferTransaction.to_branch),
                selectinload(ExchangeTransaction.from_currency),
                selectinload(ExchangeTransaction.to_currency),
            )
            
            # Apply filters
            conditions = []
            
            if filters.transaction_type:
                conditions.append(Transaction.transaction_type == filters.transaction_type)
            
            if filters.branch_id:
                conditions.append(Transaction.branch_id == filters.branch_id)
            
            if filters.customer_id:
                conditions.append(Transaction.customer_id == filters.customer_id)
            
            if filters.status:
                conditions.append(Transaction.status == filters.status)
            
            if filters.currency_id:
                conditions.append(Transaction.currency_id == filters.currency_id)
            
            if filters.date_from:
                conditions.append(Transaction.transaction_date >= filters.date_from)
            
            if filters.date_to:
                conditions.append(Transaction.transaction_date <= filters.date_to)
            
            if filters.amount_min:
                conditions.append(Transaction.amount >= filters.amount_min)
            
            if filters.amount_max:
                conditions.append(Transaction.amount <= filters.amount_max)
            
            # Apply all conditions
            if conditions:
                query = query.where(and_(*conditions))
            
            # Get total count
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await self.db.execute(count_query)
            total = total_result.scalar() or 0
            
            # Apply pagination and ordering
            query = query.order_by(Transaction.transaction_date.desc())
            query = query.offset(skip).limit(limit)
            
            # Execute query
            result = await self.db.execute(query)
            transactions = result.scalars().all()
            
            logger.info(f"Found {len(transactions)} transactions (total: {total})")
            
            return {
                "transactions": transactions,
                "total": total
            }
            
        except Exception as e:
            logger.error(f"Error listing transactions: {str(e)}")
            raise
    # ==================== EXPENSE TRANSACTIONS ====================
    @retry_on_deadlock(max_attempts=3)
    async def create_expense_transaction(
        self,
        transaction: 'ExpenseTransactionCreate',
        user_id: UUID
    ) -> ExpenseTransaction:
        """
        Create expense transaction from schema

        Args:
            transaction: ExpenseTransactionCreate schema
            user_id: User creating the transaction

        Returns:
            Created ExpenseTransaction
        """
        return await self.create_expense(
            branch_id=transaction.branch_id,
            amount=transaction.amount,
            currency_id=transaction.currency_id,
            category=transaction.expense_category,
            payee=transaction.expense_to,
            user_id=user_id,
            reference_number=transaction.reference_number,
            description=transaction.description,
            notes=transaction.notes,
            requires_approval=transaction.approval_required
        )

    async def create_expense(
        self,
        branch_id: UUID,
        amount: Decimal,
        currency_id: UUID,
        category: ExpenseCategory,
        payee: str,
        user_id: UUID,
        reference_number: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None,
        requires_approval: bool = False
    ) -> ExpenseTransaction:
        """
        Create expense transaction (atomic operation)
        
        Steps:
        1. Check branch has sufficient balance
        2. Generate transaction number
        3. Start DB transaction
        4. Create expense record
        5. Update branch balance (-amount)
        6. Create balance history
        7. Handle approval workflow if required
        8. Commit or rollback
        
        Args:
            branch_id: Branch making payment
            amount: Expense amount (must be positive)
            currency_id: Currency of transaction
            category: Expense category
            payee: Payment recipient
            user_id: User executing transaction
            reference_number: Optional external reference
            description: Optional transaction description
            notes: Optional transaction notes
            requires_approval: Whether approval is needed
            
        Returns:
            Created ExpenseTransaction
            
        Raises:
            ValidationError: Invalid inputs
            InsufficientBalanceError: Not enough funds
            DatabaseOperationError: Transaction failed
        """
        try:
            # Step 1: Validate inputs
            validate_positive_amount(amount)
            await self._validate_branch_exists(branch_id)
            await self._validate_currency_exists(currency_id)
            await self._validate_branch_has_currency(branch_id, currency_id)
            
            if not payee or len(payee.strip()) < 2:
                raise ValidationError("Payee name is required and must be at least 2 characters")
            
            # Check duplicate reference
            if reference_number:
                await self._check_duplicate_reference(reference_number)
            
            # Check sufficient balance
            balance_info = await self.balance_service.get_balance(branch_id, currency_id)
            available_balance = Decimal(str(balance_info['available_balance']))
            
            if available_balance < amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Available: {available_balance}, "
                    f"Required: {amount}"
                )
            
            # Validate transaction limits
            validate_transaction_limits(amount, "expense")

            # Step 2: Generate transaction number
            transaction_number = await self.transaction_generator.generate(
                self.db
            )
            
            # Step 3-8: Atomic operation
            try:
                # Create expense transaction
                description_value = description or notes

                expense = ExpenseTransaction(
                    transaction_number=transaction_number,
                    status=TransactionStatus.PENDING if requires_approval else TransactionStatus.PENDING,
                    amount=amount,
                    currency_id=currency_id,
                    branch_id=branch_id,
                    user_id=user_id,
                    reference_number=reference_number,
                    description=description_value,
                    notes=notes,
                    expense_category=category,
                    expense_to=payee.strip(),
                    approval_required=requires_approval,
                    transaction_date=datetime.utcnow()
                )
                
                self.db.add(expense)
                await self.db.flush()
                
                # Update branch balance (deduct amount)
                await self.balance_service.update_balance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    amount=-amount,  # Negative for expense
                    change_type=BalanceChangeType.TRANSACTION,
                    reference_id=expense.id,
                    reference_type="transaction",
                    notes=f"Expense: {category.value} to {payee}"
                )
                
                # Mark as completed if no approval needed
                if not requires_approval:
                    expense.status = TransactionStatus.COMPLETED
                    expense.completed_at = datetime.utcnow()

                await self.db.commit()

                expense = await self._load_transaction_with_relationships(
                    expense.id, ExpenseTransaction
                )

                logger.info(
                    f"Expense transaction created: {transaction_number}, "
                    f"Branch: {branch_id}, Amount: {amount} {currency_id}"
                )
                
                return expense
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to create expense transaction: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to create expense transaction: {str(e)}"
                )
                
        except (ValidationError, InsufficientBalanceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_expense: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    # ==================== EXCHANGE TRANSACTIONS ====================

    async def calculate_exchange(
        self,
        calculation: 'ExchangeCalculationRequest'
    ) -> Dict[str, Any]:
        """
        Calculate exchange rate preview

        Args:
            calculation: ExchangeCalculationRequest schema

        Returns:
            ExchangeCalculationResponse dict
        """
        try:
            # Get currency details first to get codes
            from_currency = await self.db.get(Currency, calculation.from_currency_id)
            to_currency = await self.db.get(Currency, calculation.to_currency_id)

            if not from_currency:
                raise ValidationError(f"From currency not found: {calculation.from_currency_id}")
            if not to_currency:
                raise ValidationError(f"To currency not found: {calculation.to_currency_id}")

            # Get latest exchange rate using currency codes
            rate_info = await self.currency_service.get_latest_rate(
                from_currency.code,
                to_currency.code
            )

            if not rate_info:
                raise ValidationError(
                    f"No exchange rate found for {from_currency.code} -> {to_currency.code}"
                )

            exchange_rate = Decimal(str(rate_info.rate))

            # Calculate amounts
            to_amount = (calculation.from_amount * exchange_rate).quantize(Decimal("0.01"))

            # Calculate commission (default 0% unless explicitly provided)
            commission_percentage = calculation.commission_percentage if calculation.commission_percentage is not None else Decimal("0.00")
            commission_amount = (calculation.from_amount * commission_percentage / 100).quantize(Decimal("0.01"))

            # Total cost
            total_cost = calculation.from_amount + commission_amount

            # Effective rate (including commission)
            effective_rate = to_amount / calculation.from_amount if calculation.from_amount > 0 else Decimal("0")

            return {
                "from_currency_id": calculation.from_currency_id,
                "from_currency_code": from_currency.code,
                "to_currency_id": calculation.to_currency_id,
                "to_currency_code": to_currency.code,
                "from_amount": calculation.from_amount,
                "to_amount": to_amount.quantize(Decimal("0.01")),
                "exchange_rate": exchange_rate,
                "commission_percentage": commission_percentage,
                "commission_amount": commission_amount,
                "total_cost": total_cost,
                "effective_rate": effective_rate.quantize(Decimal("0.000001"))
            }

        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Error calculating exchange: {str(e)}")
            raise ValidationError(f"Failed to calculate exchange: {str(e)}")

    @retry_on_deadlock(max_attempts=3)
    async def create_exchange_transaction(
        self,
        transaction: 'ExchangeTransactionCreate',
        user_id: UUID
    ) -> ExchangeTransaction:
        """
        Create exchange transaction from schema

        Args:
            transaction: ExchangeTransactionCreate schema
            user_id: User creating the transaction

        Returns:
            Created ExchangeTransaction
        """
        return await self.create_exchange(
            branch_id=transaction.branch_id,
            customer_id=transaction.customer_id,
            from_currency_id=transaction.from_currency_id,
            to_currency_id=transaction.to_currency_id,
            from_amount=transaction.from_amount,
            commission_percentage=transaction.commission_percentage,
            user_id=user_id,
            reference_number=transaction.reference_number,
            description=transaction.description,
            notes=transaction.notes
        )

    async def create_exchange(
        self,
        branch_id: UUID,
        customer_id: Optional[UUID],
        from_currency_id: UUID,
        to_currency_id: UUID,
        from_amount: Decimal,
        commission_percentage: Optional[Decimal],
        user_id: UUID,
        reference_number: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> ExchangeTransaction:
        """
        Create currency exchange transaction (atomic operation)

        Steps:
        1. Get currency objects and their codes
        2. Get latest exchange rate
        3. Calculate to_amount and commission
        4. Check branch has from_currency balance
        5. Generate transaction number
        6. Start DB transaction
        7. Create exchange record
        8. Update branch balance (-from_amount in from_currency)
        9. Update branch balance (+to_amount in to_currency)
        10. Create commission income (if applicable)
        11. Create balance_history entries
        12. Commit or rollback
        
        Args:
            branch_id: Branch executing exchange
            customer_id: Optional customer reference
            from_currency_id: Source currency
            to_currency_id: Target currency
            from_amount: Amount to exchange
            user_id: User executing transaction
            reference_number: Optional external reference
            description: Optional transaction description
            notes: Optional transaction notes
            
        Returns:
            Created ExchangeTransaction
            
        Raises:
            ValidationError: Invalid inputs or same currencies
            InsufficientBalanceError: Not enough funds
            DatabaseOperationError: Transaction failed
        """
        try:
            # Validate inputs
            validate_positive_amount(from_amount)

            if from_currency_id == to_currency_id:
                raise ValidationError("Cannot exchange between same currencies")

            # Steps 1-12: Atomic operation
            try:
                async with self.db.begin():
                    await self._validate_branch_exists(branch_id)
                    await self._validate_currency_exists(from_currency_id)
                    await self._validate_currency_exists(to_currency_id)
                    if customer_id:
                        await self._validate_customer_exists(customer_id)

                    # Check duplicate reference
                    if reference_number:
                        await self._check_duplicate_reference(reference_number)

                    # Step 1: Get currency objects to retrieve their codes
                    from app.repositories.currency_repo import CurrencyRepository
                    currency_repo = CurrencyRepository(self.db)

                    from_currency = await currency_repo.get_currency_by_id(from_currency_id)
                    to_currency = await currency_repo.get_currency_by_id(to_currency_id)

                    if not from_currency:
                        raise ValidationError(f"Source currency {from_currency_id} not found")
                    if not to_currency:
                        raise ValidationError(f"Target currency {to_currency_id} not found")

                    # Step 2: Get latest exchange rate using currency codes
                    rate_info = await self.currency_service.get_latest_rate(
                        from_currency.code, to_currency.code
                    )

                    if not rate_info:
                        raise ValidationError(
                            f"No exchange rate found for {from_currency.code} -> {to_currency.code}"
                        )

                    # Access rate from Pydantic model object (not dictionary)
                    exchange_rate = Decimal(str(rate_info.rate))

                    # Step 3: Calculate amounts and commission using request value (can be 0)
                    to_amount = (from_amount * exchange_rate).quantize(Decimal("0.01"))

                    commission_percentage = (
                        Decimal(str(commission_percentage))
                        if commission_percentage is not None
                        else Decimal("0.00")
                    )
                    commission_amount = (from_amount * commission_percentage / 100).quantize(Decimal("0.01"))

                    total_cost = from_amount + commission_amount

                    # Step 4: Check balance using the total cost in from currency
                    from_balance_info = await self.balance_service.get_balance(
                        branch_id, from_currency_id
                    )
                    available = Decimal(str(from_balance_info['available_balance']))

                    if available < total_cost:
                        raise InsufficientBalanceError(
                            f"Insufficient {from_currency.code} balance. "
                            f"Available: {available}, Required: {total_cost}"
                        )

                    # Step 5: Generate transaction number
                    transaction_number = await self.transaction_generator.generate(
                        self.db
                    )

                    # Create exchange transaction
                    description_value = description or notes

                    exchange = ExchangeTransaction(
                        transaction_number=transaction_number,
                        status=TransactionStatus.PENDING,
                        amount=from_amount,
                        currency_id=from_currency_id,
                        branch_id=branch_id,
                        user_id=user_id,
                        customer_id=customer_id,
                        reference_number=reference_number,
                        description=description_value,
                        notes=notes,
                        from_currency_id=from_currency_id,
                        to_currency_id=to_currency_id,
                        from_amount=from_amount,
                        to_amount=to_amount,
                        exchange_rate_used=exchange_rate,
                        commission_amount=commission_amount,
                        commission_percentage=commission_percentage,
                        transaction_date=datetime.utcnow()
                    )

                    self.db.add(exchange)
                    await self.db.flush()

                    # Deduct from_currency from branch including commission (if any)
                    await self.balance_service.update_balance(
                        branch_id=branch_id,
                        currency_id=from_currency_id,
                        amount=-total_cost,
                        change_type=BalanceChangeType.TRANSACTION,
                        reference_id=exchange.id,
                        reference_type="transaction",
                        notes=(
                            f"Exchange out: {from_amount} {from_currency.code} "
                            f"to {to_currency.code} (commission {commission_amount})"
                        )
                    )

                    # Add to_currency to branch
                    await self.balance_service.update_balance(
                        branch_id=branch_id,
                        currency_id=to_currency_id,
                        amount=to_amount,
                        change_type=BalanceChangeType.TRANSACTION,
                        reference_id=exchange.id,
                        reference_type="transaction",
                        notes=f"Exchange in: {to_amount} {to_currency.code} from {from_currency.code}"
                    )

                    # Mark as completed
                    exchange.status = TransactionStatus.COMPLETED
                    exchange.completed_at = datetime.utcnow()

                # Reload exchange with required relationships to avoid lazy loads
                # outside the greenlet/async context when serializing the response.
                exchange = await self._load_transaction_with_relationships(
                    exchange.id, ExchangeTransaction
                )

                logger.info(
                    f"Exchange transaction created: {transaction_number}, "
                    f"Branch: {branch_id}, {from_amount} {from_currency.code} -> "
                    f"{to_amount} {to_currency.code}"
                )

                return exchange

            except Exception as e:
                logger.error(f"Failed to create exchange transaction: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to create exchange transaction: {str(e)}"
                )
                
        except (ValidationError, InsufficientBalanceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_exchange: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    # ==================== TRANSFER TRANSACTIONS ====================

    async def create_transfer_transaction(
        self,
        transaction: 'TransferTransactionCreate',
        user_id: UUID
    ) -> TransferTransaction:
        """
        Create transfer transaction from schema

        Args:
            transaction: TransferTransactionCreate schema
            user_id: User creating the transaction

        Returns:
            Created TransferTransaction
        """
        return await self.create_transfer(
            from_branch_id=transaction.from_branch_id,
            to_branch_id=transaction.to_branch_id,
            amount=transaction.amount,
            currency_id=transaction.currency_id,
            user_id=user_id,
            transfer_type=transaction.transfer_type,
            reference_number=transaction.reference_number,
            description=transaction.description,
            notes=transaction.notes
        )

    async def create_transfer(
        self,
        from_branch_id: UUID,
        to_branch_id: UUID,
        amount: Decimal,
        currency_id: UUID,
        user_id: UUID,
        transfer_type: TransferType = TransferType.BRANCH_TO_BRANCH,
        reference_number: Optional[str] = None,
        description: Optional[str] = None,
        notes: Optional[str] = None
    ) -> TransferTransaction:
        """
        Create branch transfer transaction (two-phase commit)
        
        Phase 1 - Initiate Transfer:
        1. Check from_branch balance
        2. Generate transaction number
        3. Start DB transaction
        4. Create transfer record (status: pending)
        5. Reserve balance in from_branch
        6. Commit
        
        Phase 2 - Complete Transfer (separate endpoint):
        Use complete_transfer() method
        
        Args:
            from_branch_id: Source branch
            to_branch_id: Destination branch
            amount: Transfer amount
            currency_id: Currency of transfer
            user_id: User initiating transfer
            transfer_type: Type of transfer
            reference_number: Optional external reference
            description: Optional transfer description
            notes: Optional transfer notes
            
        Returns:
            Created TransferTransaction (status: pending)
            
        Raises:
            ValidationError: Invalid inputs or same branches
            InsufficientBalanceError: Not enough funds
            DatabaseOperationError: Transaction failed
        """
        try:
            # Validate inputs
            validate_positive_amount(amount)
            await self._validate_branch_exists(from_branch_id)
            await self._validate_branch_exists(to_branch_id)
            await self._validate_currency_exists(currency_id)
            
            if from_branch_id == to_branch_id:
                raise ValidationError("Cannot transfer to the same branch")
            
            # Check duplicate reference
            if reference_number:
                await self._check_duplicate_reference(reference_number)
            
            # Check balance
            balance_info = await self.balance_service.get_balance(
                from_branch_id, currency_id
            )
            available = Decimal(str(balance_info['available_balance']))
            
            if available < amount:
                raise InsufficientBalanceError(
                    f"Insufficient balance for transfer. "
                    f"Available: {available}, Required: {amount}"
                )
            
            # Generate transaction number
            transaction_number = await self.transaction_generator.generate(
                self.db
            )
            
            # Atomic operation - Phase 1
            try:
                # Create transfer transaction
                description_value = description or notes

                transfer = TransferTransaction(
                    transaction_number=transaction_number,
                    status=TransactionStatus.PENDING,
                    amount=amount,
                    currency_id=currency_id,
                    branch_id=from_branch_id,
                    user_id=user_id,
                    reference_number=reference_number,
                    description=description_value,
                    notes=notes,
                    from_branch_id=from_branch_id,
                    to_branch_id=to_branch_id,
                    transfer_type=transfer_type,
                    transaction_date=datetime.utcnow()
                )
                
                self.db.add(transfer)
                await self.db.flush()
                
                # Reserve balance (don't deduct yet)
                await self.balance_service.reserve_balance(
                    branch_id=from_branch_id,
                    currency_id=currency_id,
                    amount=amount,
                    reference_id=transfer.id,
                    reference_type="transaction"
                )

                await self.db.commit()
                transfer = await self._load_transaction_with_relationships(
                    transfer.id, TransferTransaction
                )

                logger.info(
                    f"Transfer initiated: {transaction_number}, "
                    f"From: {from_branch_id} -> To: {to_branch_id}, "
                    f"Amount: {amount} {currency_id}"
                )

                return transfer
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to initiate transfer: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to initiate transfer: {str(e)}"
                )
                
        except (ValidationError, InsufficientBalanceError):
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_transfer: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    async def receive_transfer(
        self,
        transaction_id: UUID,
        received_by_id: UUID,
        receipt_notes: Optional[str] = None
    ) -> TransferTransaction:
        """
        Complete transfer by receiving funds

        Args:
            transaction_id: Transfer transaction ID
            received_by_id: User confirming receipt
            receipt_notes: Optional receipt notes

        Returns:
            Updated TransferTransaction
        """
        return await self.complete_transfer(transaction_id, received_by_id)

    async def complete_transfer(
        self,
        transfer_id: UUID,
        received_by_user_id: UUID
    ) -> TransferTransaction:
        """
        Complete transfer transaction (Phase 2)
        
        Steps:
        1. Validate transfer exists and is pending
        2. Start DB transaction
        3. Update from_branch balance (-amount)
        4. Update to_branch balance (+amount)
        5. Release reserved balance
        6. Update transfer status (completed)
        7. Commit or rollback
        
        Args:
            transfer_id: Transfer transaction ID
            received_by_user_id: User confirming receipt
            
        Returns:
            Updated TransferTransaction
            
        Raises:
            ValidationError: Invalid transfer state
            DatabaseOperationError: Transaction failed
        """
        try:
            # Get transfer
            transfer = await self.db.get(TransferTransaction, transfer_id)
            
            if not transfer:
                raise ValidationError(f"Transfer {transfer_id} not found")
            
            if transfer.status not in {
                TransactionStatus.PENDING,
                TransactionStatus.IN_TRANSIT
            }:
                raise ValidationError(
                    f"Transfer {transfer_id} cannot be completed from status: {transfer.status}"
                )
            
            # Atomic operation - Phase 2
            try:
                # Deduct from source branch
                await self.balance_service.update_balance(
                    branch_id=transfer.from_branch_id,
                    currency_id=transfer.currency_id,
                    amount=-transfer.amount,
                    change_type=BalanceChangeType.TRANSFER_OUT,
                    reference_id=transfer.id,
                    reference_type="transaction",
                    notes=f"Transfer to {transfer.to_branch_id}"
                )

                # Add to destination branch
                await self.balance_service.update_balance(
                    branch_id=transfer.to_branch_id,
                    currency_id=transfer.currency_id,
                    amount=transfer.amount,
                    change_type=BalanceChangeType.TRANSFER_IN,
                    reference_id=transfer.id,
                    reference_type="transaction",
                    notes=f"Transfer from {transfer.from_branch_id}"
                )
                
                # Release reserved balance
                await self.balance_service.release_reserved_balance(
                    branch_id=transfer.from_branch_id,
                    currency_id=transfer.currency_id,
                    amount=transfer.amount,
                    reference_id=transfer.id
                )
                
                # Update transfer status
                transfer.status = TransactionStatus.COMPLETED
                transfer.completed_at = datetime.utcnow()
                transfer.received_by_id = received_by_user_id
                transfer.received_at = datetime.utcnow()

                await self.db.commit()
                transfer = await self._load_transaction_with_relationships(
                    transfer.id, TransferTransaction
                )

                logger.info(f"Transfer completed: {transfer.transaction_number}")

                return transfer
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to complete transfer: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to complete transfer: {str(e)}"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in complete_transfer: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    # ==================== EXPENSE APPROVAL ====================

    async def approve_expense_transaction(
        self,
        transaction_id: UUID,
        approver_id: UUID,
        approval_notes: Optional[str] = None
    ) -> ExpenseTransaction:
        """
        Approve expense transaction

        Args:
            transaction_id: Expense transaction ID
            approver_id: User approving the expense
            approval_notes: Optional approval notes

        Returns:
            Approved ExpenseTransaction

        Raises:
            ValidationError: Invalid transaction or already approved
            DatabaseOperationError: Approval failed
        """
        try:
            # Get expense transaction
            expense = await self.db.get(ExpenseTransaction, transaction_id)

            if not expense:
                raise ValidationError(f"Transaction {transaction_id} not found")

            if expense.transaction_type != TransactionType.EXPENSE:
                raise ValidationError("Transaction is not an expense transaction")

            if not expense.approval_required:
                raise ValidationError("This expense does not require approval")

            if expense.approved_by_id:
                raise ValidationError("Expense already approved")

            # Approve the expense
            expense.approve(approver_id)

            # Mark the transaction as completed now that it is approved
            expense.complete(approver_id)

            # If there are approval notes, add them to the transaction notes
            if approval_notes:
                expense.notes = f"{expense.notes or ''}\nApproval notes: {approval_notes}"

            await self.db.commit()

            expense = await self._load_transaction_with_relationships(
                expense.id, ExpenseTransaction
            )

            logger.info(
                f"Expense transaction approved: {expense.transaction_number} by user {approver_id}"
            )

            return expense

        except ValidationError:
            raise
        except Exception as e:
            await self.db.rollback()
            logger.error(f"Error approving expense transaction: {str(e)}")
            raise DatabaseOperationError(f"Failed to approve expense: {str(e)}")

    # ==================== TRANSACTION CANCELLATION ====================

    async def cancel_transaction(
        self,
        transaction_id: UUID,
        reason: str,
        cancelled_by_user_id: UUID
    ) -> Transaction:
        """
        Cancel pending transaction and reverse balance changes
        
        Steps:
        1. Validate transaction exists and can be cancelled
        2. Start DB transaction
        3. Reverse balance changes
        4. Update transaction status (cancelled)
        5. Release any reserved balances
        6. Commit or rollback
        
        Args:
            transaction_id: Transaction to cancel
            reason: Cancellation reason (required)
            cancelled_by_user_id: User cancelling transaction
            
        Returns:
            Updated Transaction
            
        Raises:
            ValidationError: Cannot cancel this transaction
            DatabaseOperationError: Cancellation failed
        """
        try:
            # Get transaction
            transaction = await self.db.get(Transaction, transaction_id)
            
            if not transaction:
                raise ValidationError(f"Transaction {transaction_id} not found")
            
            if transaction.status != TransactionStatus.PENDING:
                raise ValidationError(
                    f"Cannot cancel transaction with status: {transaction.status}. "
                    f"Only PENDING transactions can be cancelled."
                )
            
            if not reason or len(reason.strip()) < 10:
                raise ValidationError(
                    "Cancellation reason must be at least 10 characters"
                )
            
            # Atomic operation
            try:
                # Reverse balance changes based on transaction type
                if isinstance(transaction, IncomeTransaction):
                    # Reverse income (deduct amount)
                    await self.balance_service.update_balance(
                        branch_id=transaction.branch_id,
                        currency_id=transaction.currency_id,
                        amount=-transaction.amount,
                        change_type=BalanceChangeType.ADJUSTMENT,
                        reference_id=transaction.id,
                        reference_type="cancellation",
                        notes=f"Cancelled income: {reason}"
                    )

                elif isinstance(transaction, ExpenseTransaction):
                    # Reverse expense (add amount back)
                    await self.balance_service.update_balance(
                        branch_id=transaction.branch_id,
                        currency_id=transaction.currency_id,
                        amount=transaction.amount,
                        change_type=BalanceChangeType.ADJUSTMENT,
                        reference_id=transaction.id,
                        reference_type="cancellation",
                        notes=f"Cancelled expense: {reason}"
                    )
                
                elif isinstance(transaction, TransferTransaction):
                    # Release reserved balance
                    await self.balance_service.release_reserved_balance(
                        branch_id=transaction.from_branch_id,
                        currency_id=transaction.currency_id,
                        amount=transaction.amount,
                        reference_id=transaction.id
                    )
                
                # Update transaction status
                transaction.status = TransactionStatus.CANCELLED
                transaction.cancelled_at = datetime.utcnow()
                transaction.cancelled_by_id = cancelled_by_user_id
                transaction.cancellation_reason = reason.strip()
                
                await self.db.commit()
                transaction = await self._load_transaction_with_relationships(
                    transaction.id, type(transaction)
                )
                
                logger.info(
                    f"Transaction cancelled: {transaction.transaction_number}, "
                    f"Reason: {reason}"
                )
                
                return transaction
                
            except Exception as e:
                await self.db.rollback()
                logger.error(f"Failed to cancel transaction: {str(e)}")
                raise DatabaseOperationError(
                    f"Failed to cancel transaction: {str(e)}"
                )
                
        except ValidationError:
            raise
        except Exception as e:
            logger.error(f"Unexpected error in cancel_transaction: {str(e)}")
            raise DatabaseOperationError(f"Transaction failed: {str(e)}")
    
    # ==================== QUERY METHODS ====================
    
    async def get_transaction(self, transaction_id: UUID) -> Optional[Transaction]:
        """Get transaction by ID with branch relationships loaded"""
        from sqlalchemy.orm import selectinload

        try:
            return await self._load_transaction_with_relationships(transaction_id)
        except Exception:
            return None
    
    async def get_transaction_by_number(
        self, transaction_number: str
    ) -> Optional[Transaction]:
        """Get transaction by transaction number"""
        stmt = (
            select(Transaction)
            .options(*self._transaction_relationship_options())
            .where(Transaction.transaction_number == transaction_number)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_branch_transactions(
        self,
        branch_id: UUID,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[Transaction]:
        """Get transactions for a branch with filters"""
        stmt = (
            select(Transaction)
            .options(*self._transaction_relationship_options())
            .where(Transaction.branch_id == branch_id)
        )
        
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        
        if status:
            stmt = stmt.where(Transaction.status == status)
        
        if date_from:
            stmt = stmt.where(Transaction.transaction_date >= date_from)
        
        if date_to:
            stmt = stmt.where(Transaction.transaction_date <= date_to)
        
        stmt = stmt.order_by(Transaction.transaction_date.desc())
        stmt = stmt.offset(skip).limit(limit)
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_transaction_statistics(
        self,
        branch_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get transaction statistics"""
        stmt = select(Transaction)

        if branch_id:
            stmt = stmt.where(Transaction.branch_id == branch_id)

        if date_from:
            stmt = stmt.where(Transaction.transaction_date >= date_from)

        if date_to:
            stmt = stmt.where(Transaction.transaction_date <= date_to)

        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())

        # Calculate statistics
        stats = {
            'total_count': len(transactions),
            'total_amount': Decimal('0'),
            'by_type': {},
            'by_status': {},
            'total_amount_by_currency': {},
            'date_range': {
                'from': None,
                'to': None
            }
        }

        # Track date range
        min_date = None
        max_date = None

        for txn in transactions:
            # Count by type
            type_key = txn.transaction_type.value
            stats['by_type'][type_key] = stats['by_type'].get(type_key, 0) + 1

            # Count by status
            status_key = txn.status.value
            stats['by_status'][status_key] = stats['by_status'].get(status_key, 0) + 1

            # Sum amounts by currency
            currency_key = str(txn.currency_id)
            if currency_key not in stats['total_amount_by_currency']:
                stats['total_amount_by_currency'][currency_key] = 0
            stats['total_amount_by_currency'][currency_key] += float(txn.amount)

            # Sum total amount (all currencies combined)
            stats['total_amount'] += txn.amount

            # Track date range
            txn_date = txn.transaction_date
            if min_date is None or txn_date < min_date:
                min_date = txn_date
            if max_date is None or txn_date > max_date:
                max_date = txn_date

        # Set date range
        if min_date and max_date:
            stats['date_range']['from'] = min_date
            stats['date_range']['to'] = max_date
        elif date_from or date_to:
            # If no transactions but date filters provided
            stats['date_range']['from'] = date_from
            stats['date_range']['to'] = date_to
        else:
            # No transactions and no filters - use current date
            now = datetime.utcnow()
            stats['date_range']['from'] = now
            stats['date_range']['to'] = now

        return stats
    
    # ==================== VALIDATION HELPERS ====================
    
    async def _validate_branch_exists(self, branch_id: UUID) -> None:
        """Validate branch exists"""
        from app.db.models.branch import Branch
        
        branch = await self.db.get(Branch, branch_id)
        if not branch:
            raise ValidationError(f"Branch {branch_id} not found")
        
        if not branch.is_active:
            raise ValidationError(f"Branch {branch_id} is not active")
    
    async def _validate_currency_exists(self, currency_id: UUID) -> None:
        """Validate currency exists"""
        currency = await self.db.get(Currency, currency_id)
        if not currency:
            raise ValidationError(f"Currency {currency_id} not found")
        
        if not currency.is_active:
            raise ValidationError(f"Currency {currency_id} is not active")
    
    async def _validate_branch_has_currency(
        self, branch_id: UUID, currency_id: UUID
    ) -> None:
        """Validate branch has a balance record for this currency"""
        balance = await self.balance_service.get_balance(branch_id, currency_id)
        if not balance:
            raise ValidationError(
                f"Branch {branch_id} does not have balance for currency {currency_id}"
            )
    
    async def _validate_customer_exists(self, customer_id: UUID) -> None:
        """Validate customer exists"""
        from app.db.models.customer import Customer
        
        customer = await self.db.get(Customer, customer_id)
        if not customer:
            raise ValidationError(f"Customer {customer_id} not found")
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer_id} is not active")
    
    async def _check_duplicate_reference(self, reference_number: str) -> None:
        """Check for duplicate reference number"""
        stmt = select(Transaction).where(
            Transaction.reference_number == reference_number
        )
        result = await self.db.execute(stmt)
        existing = result.scalar_one_or_none()
        
        if existing:
            raise ValidationError(
                f"Transaction with reference number {reference_number} already exists"
            )
