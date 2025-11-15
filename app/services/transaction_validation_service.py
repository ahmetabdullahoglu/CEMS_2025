# app/services/transaction_validation_service.py
"""
Transaction Validation Service
===============================
Comprehensive validation for all transaction operations:
- Balance sufficiency checks
- Exchange rate validation
- Transaction limits
- Duplicate detection
- Business rule enforcement
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.transaction import Transaction, TransactionType, TransactionStatus
from app.db.models.branch import Branch, BranchBalance
from app.db.models.currency import Currency, ExchangeRate
from app.db.models.customer import Customer
from app.core.exceptions import (
    ValidationError, InsufficientBalanceError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionValidationService:
    """Service for transaction validation"""
    
    # Configuration constants (can be moved to config)
    MAX_TRANSACTION_AMOUNT = Decimal('1000000.00')  # Maximum single transaction
    MAX_DAILY_TRANSACTION_AMOUNT = Decimal('5000000.00')  # Maximum per day
    MAX_CUSTOMER_DAILY_EXCHANGES = 10  # Maximum exchanges per customer per day
    EXCHANGE_RATE_STALENESS_HOURS = 24  # Max age for exchange rate
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== BALANCE VALIDATION ====================
    
    async def validate_sufficient_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        required_amount: Decimal,
        include_reserved: bool = True
    ) -> Dict[str, Any]:
        """
        Validate branch has sufficient balance
        
        Args:
            branch_id: Branch ID
            currency_id: Currency ID
            required_amount: Amount needed
            include_reserved: Consider reserved balance
            
        Returns:
            Dict with balance info and validation result
            
        Raises:
            InsufficientBalanceError: Not enough funds
        """
        # Get branch balance
        stmt = select(BranchBalance).where(
            and_(
                BranchBalance.branch_id == branch_id,
                BranchBalance.currency_id == currency_id
            )
        )
        
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()
        
        if not balance:
            raise ValidationError(
                f"No balance record found for branch {branch_id} "
                f"and currency {currency_id}"
            )
        
        # Calculate available balance
        available = balance.balance
        if include_reserved:
            available = balance.balance - balance.reserved_balance
        
        # Validate sufficiency
        if available < required_amount:
            raise InsufficientBalanceError(
                f"Insufficient balance. Available: {available}, "
                f"Required: {required_amount}, "
                f"Currency: {currency_id}"
            )
        
        return {
            'sufficient': True,
            'available_balance': float(available),
            'required_amount': float(required_amount),
            'remaining_after': float(available - required_amount)
        }
    
    async def check_balance_threshold(
        self,
        branch_id: UUID,
        currency_id: UUID,
        amount_change: Decimal
    ) -> Dict[str, Any]:
        """
        Check if transaction will trigger balance threshold alerts
        
        Returns:
            Dict with threshold warnings
        """
        stmt = select(BranchBalance).where(
            and_(
                BranchBalance.branch_id == branch_id,
                BranchBalance.currency_id == currency_id
            )
        )
        
        result = await self.db.execute(stmt)
        balance = result.scalar_one_or_none()
        
        if not balance:
            return {'warnings': []}
        
        new_balance = balance.balance + amount_change
        warnings = []
        
        # Check minimum threshold
        if balance.minimum_threshold and new_balance < balance.minimum_threshold:
            warnings.append({
                'type': 'below_minimum',
                'threshold': float(balance.minimum_threshold),
                'new_balance': float(new_balance),
                'severity': 'warning'
            })
        
        # Check maximum threshold
        if balance.maximum_threshold and new_balance > balance.maximum_threshold:
            warnings.append({
                'type': 'above_maximum',
                'threshold': float(balance.maximum_threshold),
                'new_balance': float(new_balance),
                'severity': 'warning'
            })
        
        return {
            'will_trigger_alerts': len(warnings) > 0,
            'warnings': warnings
        }
    
    # ==================== EXCHANGE RATE VALIDATION ====================
    
    async def validate_exchange_rate(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        max_age_hours: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Validate exchange rate exists and is not stale
        
        Args:
            from_currency_id: Source currency
            to_currency_id: Target currency
            max_age_hours: Maximum rate age in hours (default: 24)
            
        Returns:
            Dict with rate info and validation result
            
        Raises:
            ValidationError: No rate found or rate is stale
        """
        max_age = max_age_hours or self.EXCHANGE_RATE_STALENESS_HOURS
        
        # Get latest rate
        stmt = select(ExchangeRate).where(
            and_(
                ExchangeRate.from_currency_id == from_currency_id,
                ExchangeRate.to_currency_id == to_currency_id,
                ExchangeRate.is_active == True
            )
        ).order_by(ExchangeRate.effective_from.desc()).limit(1)
        
        result = await self.db.execute(stmt)
        rate = result.scalar_one_or_none()
        
        if not rate:
            raise ValidationError(
                f"No exchange rate found for {from_currency_id} -> {to_currency_id}"
            )
        
        # Check staleness
        age = datetime.utcnow() - rate.effective_from
        age_hours = age.total_seconds() / 3600

        if age_hours > max_age:
            raise ValidationError(
                f"Exchange rate is stale (age: {age_hours:.1f} hours, "
                f"max: {max_age} hours). Please update rate."
            )

        return {
            'rate': float(rate.rate),
            'effective_date': rate.effective_from.isoformat(),
            'age_hours': age_hours,
            'is_fresh': age_hours <= max_age
        }
    
    async def calculate_exchange_amount(
        self,
        from_amount: Decimal,
        from_currency_id: UUID,
        to_currency_id: UUID,
        include_commission: bool = True,
        commission_rate: Optional[Decimal] = None
    ) -> Dict[str, Any]:
        """
        Calculate exchange amounts with validation
        
        Args:
            from_amount: Amount to exchange
            from_currency_id: Source currency
            to_currency_id: Target currency
            include_commission: Include commission calculation
            commission_rate: Commission rate (default: 1%)
            
        Returns:
            Dict with calculated amounts
        """
        # Validate rate
        rate_info = await self.validate_exchange_rate(
            from_currency_id, to_currency_id
        )
        
        rate = Decimal(str(rate_info['rate']))
        
        # Calculate to_amount
        to_amount = from_amount * rate
        
        # Calculate commission
        commission = Decimal('0')
        if include_commission:
            comm_rate = commission_rate or Decimal('0.01')  # 1% default
            commission = from_amount * comm_rate
        
        # Net amounts
        net_from_amount = from_amount + commission
        net_to_amount = to_amount
        
        return {
            'from_amount': float(from_amount),
            'to_amount': float(to_amount),
            'exchange_rate': float(rate),
            'commission_amount': float(commission),
            'commission_rate': float(commission_rate or Decimal('0.01')),
            'net_from_amount': float(net_from_amount),
            'net_to_amount': float(net_to_amount),
            'rate_age_hours': rate_info['age_hours']
        }
    
    # ==================== TRANSACTION LIMITS ====================
    
    async def validate_transaction_limits(
        self,
        branch_id: UUID,
        amount: Decimal,
        transaction_type: TransactionType
    ) -> Dict[str, Any]:
        """
        Validate transaction doesn't exceed limits
        
        Checks:
        - Single transaction maximum
        - Daily transaction maximum per branch
        
        Args:
            branch_id: Branch ID
            amount: Transaction amount
            transaction_type: Type of transaction
            
        Returns:
            Dict with limit validation info
            
        Raises:
            BusinessRuleViolationError: Limit exceeded
        """
        # Check single transaction limit
        if amount > self.MAX_TRANSACTION_AMOUNT:
            raise BusinessRuleViolationError(
                f"Transaction amount {amount} exceeds maximum allowed "
                f"{self.MAX_TRANSACTION_AMOUNT}"
            )
        
        # Get today's total for this branch
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        today_end = datetime.utcnow().replace(
            hour=23, minute=59, second=59, microsecond=999999
        )
        
        stmt = select(func.sum(Transaction.amount)).where(
            and_(
                Transaction.branch_id == branch_id,
                Transaction.transaction_type == transaction_type,
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.transaction_date >= today_start,
                Transaction.transaction_date <= today_end
            )
        )
        
        result = await self.db.execute(stmt)
        daily_total = result.scalar() or Decimal('0')
        
        # Check daily limit
        new_daily_total = daily_total + amount
        
        if new_daily_total > self.MAX_DAILY_TRANSACTION_AMOUNT:
            raise BusinessRuleViolationError(
                f"Daily transaction limit exceeded. "
                f"Today's total: {daily_total}, "
                f"This transaction: {amount}, "
                f"Maximum: {self.MAX_DAILY_TRANSACTION_AMOUNT}"
            )
        
        return {
            'within_limits': True,
            'single_transaction_limit': float(self.MAX_TRANSACTION_AMOUNT),
            'daily_limit': float(self.MAX_DAILY_TRANSACTION_AMOUNT),
            'today_total': float(daily_total),
            'remaining_today': float(
                self.MAX_DAILY_TRANSACTION_AMOUNT - new_daily_total
            )
        }
    
    async def validate_customer_exchange_limit(
        self,
        customer_id: UUID
    ) -> Dict[str, Any]:
        """
        Validate customer hasn't exceeded daily exchange limit
        
        Args:
            customer_id: Customer ID
            
        Returns:
            Dict with customer limit info
            
        Raises:
            BusinessRuleViolationError: Customer exceeded daily limit
        """
        today_start = datetime.utcnow().replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        
        stmt = select(func.count(Transaction.id)).where(
            and_(
                Transaction.customer_id == customer_id,
                Transaction.transaction_type == TransactionType.EXCHANGE,
                Transaction.status == TransactionStatus.COMPLETED,
                Transaction.transaction_date >= today_start
            )
        )
        
        result = await self.db.execute(stmt)
        today_count = result.scalar() or 0
        
        if today_count >= self.MAX_CUSTOMER_DAILY_EXCHANGES:
            raise BusinessRuleViolationError(
                f"Customer has reached daily exchange limit "
                f"({self.MAX_CUSTOMER_DAILY_EXCHANGES} exchanges)"
            )
        
        return {
            'within_limit': True,
            'today_count': today_count,
            'daily_limit': self.MAX_CUSTOMER_DAILY_EXCHANGES,
            'remaining': self.MAX_CUSTOMER_DAILY_EXCHANGES - today_count
        }
    
    # ==================== DUPLICATE DETECTION ====================
    
    async def check_duplicate_transaction(
        self,
        reference_number: Optional[str] = None,
        branch_id: Optional[UUID] = None,
        amount: Optional[Decimal] = None,
        currency_id: Optional[UUID] = None,
        time_window_minutes: int = 5
    ) -> Optional[Transaction]:
        """
        Check for potential duplicate transactions
        
        Checks for:
        1. Exact reference number match
        2. Same branch, amount, currency within time window
        
        Args:
            reference_number: External reference
            branch_id: Branch ID
            amount: Transaction amount
            currency_id: Currency ID
            time_window_minutes: Time window for duplicate detection
            
        Returns:
            Existing transaction if duplicate found, None otherwise
        """
        # Check reference number
        if reference_number:
            stmt = select(Transaction).where(
                Transaction.reference_number == reference_number
            )
            result = await self.db.execute(stmt)
            existing = result.scalar_one_or_none()
            
            if existing:
                logger.warning(
                    f"Duplicate reference number detected: {reference_number}"
                )
                return existing
        
        # Check similar transaction in time window
        if all([branch_id, amount, currency_id]):
            time_threshold = datetime.utcnow() - timedelta(
                minutes=time_window_minutes
            )
            
            stmt = select(Transaction).where(
                and_(
                    Transaction.branch_id == branch_id,
                    Transaction.amount == amount,
                    Transaction.currency_id == currency_id,
                    Transaction.transaction_date >= time_threshold,
                    Transaction.status != TransactionStatus.CANCELLED
                )
            )
            
            result = await self.db.execute(stmt)
            similar = result.scalar_one_or_none()
            
            if similar:
                logger.warning(
                    f"Similar transaction detected within {time_window_minutes} "
                    f"minutes: {similar.transaction_number}"
                )
                return similar
        
        return None
    
    # ==================== ENTITY VALIDATION ====================
    
    async def validate_branch(self, branch_id: UUID) -> Branch:
        """Validate branch exists and is active"""
        branch = await self.db.get(Branch, branch_id)
        
        if not branch:
            raise ValidationError(f"Branch {branch_id} not found")
        
        if not branch.is_active:
            raise ValidationError(f"Branch {branch_id} is not active")
        
        return branch
    
    async def validate_currency(self, currency_id: UUID) -> Currency:
        """Validate currency exists and is active"""
        currency = await self.db.get(Currency, currency_id)
        
        if not currency:
            raise ValidationError(f"Currency {currency_id} not found")
        
        if not currency.is_active:
            raise ValidationError(f"Currency {currency_id} is not active")
        
        return currency
    
    async def validate_customer(self, customer_id: UUID) -> Customer:
        """Validate customer exists and is active"""
        customer = await self.db.get(Customer, customer_id)
        
        if not customer:
            raise ValidationError(f"Customer {customer_id} not found")
        
        if not customer.is_active:
            raise ValidationError(f"Customer {customer_id} is not active")
        
        # Check KYC verification
        if not customer.kyc_verified:
            raise ValidationError(
                f"Customer {customer_id} KYC not verified. "
                f"Cannot process transactions."
            )
        
        return customer
    
    # ==================== BUSINESS RULES ====================
    
    async def validate_transaction_cancellation(
        self,
        transaction: Transaction
    ) -> Dict[str, bool]:
        """
        Validate if transaction can be cancelled
        
        Rules:
        - Only PENDING transactions can be cancelled
        - Completed transactions are immutable
        - Already cancelled transactions cannot be re-cancelled
        
        Args:
            transaction: Transaction to cancel
            
        Returns:
            Dict with cancellation validation
            
        Raises:
            BusinessRuleViolationError: Cannot cancel
        """
        if transaction.status == TransactionStatus.COMPLETED:
            raise BusinessRuleViolationError(
                f"Cannot cancel completed transaction {transaction.transaction_number}"
            )
        
        if transaction.status == TransactionStatus.CANCELLED:
            raise BusinessRuleViolationError(
                f"Transaction {transaction.transaction_number} is already cancelled"
            )
        
        if transaction.status != TransactionStatus.PENDING:
            raise BusinessRuleViolationError(
                f"Cannot cancel transaction with status: {transaction.status}"
            )
        
        return {
            'can_cancel': True,
            'reason': 'Transaction is in PENDING status'
        }
    
    async def validate_transfer_receipt(
        self,
        transfer: Transaction
    ) -> Dict[str, bool]:
        """
        Validate transfer can be received/completed
        
        Args:
            transfer: Transfer transaction
            
        Returns:
            Dict with receipt validation
            
        Raises:
            BusinessRuleViolationError: Cannot receive
        """
        if not isinstance(transfer, Transaction) or \
           transfer.transaction_type != TransactionType.TRANSFER:
            raise ValidationError("Not a transfer transaction")
        
        if transfer.status not in {
            TransactionStatus.PENDING,
            TransactionStatus.IN_TRANSIT
        }:
            raise BusinessRuleViolationError(
                f"Transfer {transfer.transaction_number} is not ready for receipt "
                f"(status: {transfer.status})"
            )

        return {
            'can_receive': True,
            'reason': 'Transfer is ready for receipt'
        }
