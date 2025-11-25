"""
Balance Service
Critical financial operations for branch balances
All operations are ATOMIC and maintain data consistency
"""

from typing import Dict, Any, Optional,List
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from app.repositories.branch_repo import BranchRepository
from app.db.models.branch import (
    BranchBalance, BranchBalanceHistory, BalanceChangeType
)
from app.core.exceptions import (
    InsufficientBalanceError,
    ValidationError,
    DatabaseOperationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BalanceService:
    """
    Service for balance operations
    
    CRITICAL: All methods must be called within a database transaction
    and should handle rollback on errors
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = BranchRepository(db)

    async def get_balance(
        self,
        branch_id: UUID,
        currency_id: UUID
    ) -> Dict[str, Any]:
        """
        Get balance information for a branch and currency

        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID

        Returns:
            Dictionary with balance information:
            - balance: Total balance
            - available_balance: Balance minus reserved
            - reserved_balance: Reserved balance
            - currency_id: Currency UUID
            - branch_id: Branch UUID

        Raises:
            ValidationError: If balance not found
        """
        balance = await self.repo.get_branch_balance(branch_id, currency_id)

        if not balance:
            raise ValidationError(
                f"Balance not found for branch {branch_id} and currency {currency_id}"
            )

        return {
            "balance": balance.balance,
            "available_balance": balance.balance - balance.reserved_balance,
            "reserved_balance": balance.reserved_balance,
            "currency_id": currency_id,
            "branch_id": branch_id,
            "last_updated": balance.last_updated
        }

    async def ensure_branch_balance(
        self, branch_id: UUID, currency_id: UUID
    ) -> BranchBalance:
        """Return an existing branch balance or create a zeroed record if missing."""

        balance = await self.repo.get_branch_balance(branch_id, currency_id)
        if balance:
            return balance

        return await self.repo.create_branch_balance({
            "branch_id": branch_id,
            "currency_id": currency_id,
            "balance": Decimal("0"),
            "reserved_balance": Decimal("0"),
            "is_active": True,
            "last_updated": datetime.utcnow()
        })

    async def update_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        amount: Decimal,
        change_type: BalanceChangeType,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None,
        performed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> BranchBalance:
        """
        Update branch balance (ATOMIC OPERATION)
        
        This is the core balance update method. All balance changes
        should go through this method to ensure consistency and audit trail.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            amount: Amount to add/subtract (positive or negative)
            change_type: Type of balance change
            reference_id: Reference to related entity (transaction, transfer, etc.)
            reference_type: Type of reference
            performed_by: User performing the operation
            notes: Additional notes
            
        Returns:
            Updated branch balance
            
        Raises:
            InsufficientBalanceError: If balance would become negative
            ValidationError: If validation fails
            DatabaseOperationError: If database operation fails
        """
        try:
            # Get current balance (with lock for update)
            balance = await self.repo.get_branch_balance(branch_id, currency_id)

            if not balance:
                # Create a zeroed balance record when none exists
                balance = await self.repo.create_branch_balance({
                    "branch_id": branch_id,
                    "currency_id": currency_id,
                    "balance": Decimal("0"),
                    "reserved_balance": Decimal("0"),
                    "is_active": True,
                    "last_updated": datetime.utcnow()
                })
            
            # Store balance before change
            balance_before = balance.balance
            
            # Calculate new balance
            new_balance = balance_before + amount
            
            # Validate new balance
            if new_balance < 0:
                raise InsufficientBalanceError(
                    f"Insufficient balance. Current: {balance_before}, "
                    f"Requested: {amount}, Result would be: {new_balance}"
                )
            
            # Validate reserved balance doesn't exceed total
            if balance.reserved_balance > new_balance:
                raise BusinessRuleViolationError(
                    f"Reserved balance ({balance.reserved_balance}) would exceed "
                    f"total balance ({new_balance})"
                )
            
            # Update balance
            balance.balance = new_balance
            balance.last_updated = datetime.utcnow()
            
            await self.db.flush()
            
            # Create history record
            await self._create_history_record(
                branch_id=branch_id,
                currency_id=currency_id,
                change_type=change_type,
                amount=amount,
                balance_before=balance_before,
                balance_after=new_balance,
                reference_id=reference_id,
                reference_type=reference_type,
                performed_by=performed_by,
                notes=notes
            )
            
            logger.info(
                f"Balance updated: Branch {branch_id}, Currency {currency_id}, "
                f"Amount {amount}, New Balance {new_balance}"
            )
            
            return balance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error updating balance: {str(e)}")
            raise DatabaseOperationError(f"Failed to update balance: {str(e)}")
    
    async def reserve_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        amount: Decimal,
        reference_id: UUID,
        reference_type: str = "transaction",
        performed_by: Optional[UUID] = None
    ) -> BranchBalance:
        """
        Reserve balance for pending transaction (ATOMIC OPERATION)
        
        This locks a portion of the balance so it's not available
        for other transactions until released or committed.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            amount: Amount to reserve
            reference_id: Transaction or transfer ID
            reference_type: Type of reference
            performed_by: User performing the operation
            
        Returns:
            Updated branch balance
            
        Raises:
            InsufficientBalanceError: If not enough available balance
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} "
                    f"and currency {currency_id}"
                )
            
            # Check available balance
            available = balance.balance - balance.reserved_balance
            if available < amount:
                raise InsufficientBalanceError(
                    f"Insufficient available balance. "
                    f"Available: {available}, Requested: {amount}"
                )
            
            # Reserve balance
            balance.reserved_balance += amount
            balance.last_updated = datetime.utcnow()
            
            await self.db.flush()
            
            logger.info(
                f"Balance reserved: Branch {branch_id}, Currency {currency_id}, "
                f"Amount {amount}, Reserved Total {balance.reserved_balance}"
            )
            
            return balance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error reserving balance: {str(e)}")
            raise DatabaseOperationError(f"Failed to reserve balance: {str(e)}")
    
    async def release_reserved_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        amount: Decimal,
        reference_id: UUID,
        performed_by: Optional[UUID] = None
    ) -> BranchBalance:
        """
        Release reserved balance (ATOMIC OPERATION)
        
        This releases previously reserved balance back to available balance.
        Used when a pending transaction is cancelled or completed.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            amount: Amount to release
            reference_id: Transaction or transfer ID
            performed_by: User performing the operation
            
        Returns:
            Updated branch balance
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} "
                    f"and currency {currency_id}"
                )
            
            # Validate release amount
            if balance.reserved_balance < amount:
                raise ValidationError(
                    f"Cannot release {amount}. "
                    f"Current reserved balance: {balance.reserved_balance}"
                )
            
            # Release balance
            balance.reserved_balance -= amount
            balance.last_updated = datetime.utcnow()
            
            await self.db.flush()
            
            logger.info(
                f"Reserved balance released: Branch {branch_id}, "
                f"Currency {currency_id}, Amount {amount}"
            )
            
            return balance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error releasing balance: {str(e)}")
            raise DatabaseOperationError(f"Failed to release balance: {str(e)}")
    
    async def commit_reserved_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        amount: Decimal,
        change_type: BalanceChangeType,
        reference_id: UUID,
        reference_type: str,
        performed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> BranchBalance:
        """
        Commit reserved balance to actual balance change (ATOMIC OPERATION)
        
        This deducts from both reserved and actual balance when a pending
        transaction is completed.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            amount: Amount to commit
            change_type: Type of change
            reference_id: Transaction or transfer ID
            reference_type: Type of reference
            performed_by: User performing the operation
            notes: Additional notes
            
        Returns:
            Updated branch balance
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} "
                    f"and currency {currency_id}"
                )
            
            balance_before = balance.balance
            
            # Validate reserved amount
            if balance.reserved_balance < amount:
                raise ValidationError(
                    f"Cannot commit {amount}. "
                    f"Current reserved balance: {balance.reserved_balance}"
                )
            
            # Commit: deduct from both reserved and actual balance
            balance.balance -= amount
            balance.reserved_balance -= amount
            balance.last_updated = datetime.utcnow()
            
            # Validate final balance
            if balance.balance < 0:
                raise InsufficientBalanceError(
                    f"Balance would become negative: {balance.balance}"
                )
            
            await self.db.flush()
            
            # Create history record
            await self._create_history_record(
                branch_id=branch_id,
                currency_id=currency_id,
                change_type=change_type,
                amount=-amount,  # Negative because it's a deduction
                balance_before=balance_before,
                balance_after=balance.balance,
                reference_id=reference_id,
                reference_type=reference_type,
                performed_by=performed_by,
                notes=notes or "Reserved balance committed"
            )
            
            logger.info(
                f"Reserved balance committed: Branch {branch_id}, "
                f"Currency {currency_id}, Amount {amount}, "
                f"New Balance {balance.balance}"
            )
            
            return balance
            
        except SQLAlchemyError as e:
            logger.error(f"Database error committing balance: {str(e)}")
            raise DatabaseOperationError(f"Failed to commit balance: {str(e)}")
    
    async def reconcile_branch_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        expected_balance: Decimal,
        performed_by: UUID,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reconcile branch balance (ATOMIC OPERATION)
        
        Compares expected balance with actual balance and creates
        an adjustment if there's a discrepancy.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            expected_balance: Expected balance amount
            performed_by: User performing reconciliation
            notes: Reconciliation notes
            
        Returns:
            Reconciliation result with details
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} "
                    f"and currency {currency_id}"
                )
            
            current_balance = balance.balance
            difference = expected_balance - current_balance
            
            result = {
                'branch_id': str(branch_id),
                'currency_id': str(currency_id),
                'current_balance': float(current_balance),
                'expected_balance': float(expected_balance),
                'difference': float(difference),
                'reconciled_at': datetime.utcnow().isoformat(),
                'performed_by': str(performed_by)
            }
            
            # If there's a discrepancy, create adjustment
            if difference != 0:
                logger.warning(
                    f"Balance discrepancy found: Branch {branch_id}, "
                    f"Currency {currency_id}, Difference {difference}"
                )
                
                # Update balance
                await self.update_balance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    amount=difference,
                    change_type=BalanceChangeType.RECONCILIATION,
                    performed_by=performed_by,
                    notes=notes or f"Reconciliation adjustment: {difference}"
                )
                
                result['adjustment_made'] = True
            else:
                result['adjustment_made'] = False
            
            # Update reconciliation timestamp
            balance.last_reconciled_at = datetime.utcnow()
            balance.last_reconciled_by = performed_by
            
            await self.db.flush()
            
            logger.info(
                f"Balance reconciled: Branch {branch_id}, "
                f"Currency {currency_id}, Adjustment {difference}"
            )
            
            return result
            
        except SQLAlchemyError as e:
            logger.error(f"Database error during reconciliation: {str(e)}")
            raise DatabaseOperationError(f"Failed to reconcile balance: {str(e)}")
    
    async def get_balance_summary(
        self,
        branch_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive balance summary for a branch
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            Balance summary with all currencies
        """
        balances = await self.repo.get_all_branch_balances(branch_id)
        
        summary = {
            'branch_id': str(branch_id),
            'total_currencies': len(balances),
            'balances': []
        }
        
        for balance in balances:
            summary['balances'].append({
                'currency_code': balance.currency.code,
                'currency_name': balance.currency.name_en,
                'balance': float(balance.balance),
                'reserved': float(balance.reserved_balance),
                'available': float(balance.available_balance),
                'minimum_threshold': float(balance.minimum_threshold) if balance.minimum_threshold else None,
                'maximum_threshold': float(balance.maximum_threshold) if balance.maximum_threshold else None,
                'is_below_minimum': balance.is_below_minimum(),
                'is_above_maximum': balance.is_above_maximum(),
                'last_updated': balance.last_updated.isoformat(),
                'last_reconciled': balance.last_reconciled_at.isoformat() if balance.last_reconciled_at else None
            })
        
        return summary
    
    async def _create_history_record(
        self,
        branch_id: UUID,
        currency_id: UUID,
        change_type: BalanceChangeType,
        amount: Decimal,
        balance_before: Decimal,
        balance_after: Decimal,
        reference_id: Optional[UUID] = None,
        reference_type: Optional[str] = None,
        performed_by: Optional[UUID] = None,
        notes: Optional[str] = None
    ) -> BranchBalanceHistory:
        """
        Internal method to create balance history record
        
        Args:
            All balance change details
            
        Returns:
            Created history record
        """
        history_data = {
            'branch_id': branch_id,
            'currency_id': currency_id,
            'change_type': change_type,
            'amount': amount,
            'balance_before': balance_before,
            'balance_after': balance_after,
            'reference_id': reference_id,
            'reference_type': reference_type,
            'performed_by': performed_by,
            'performed_at': datetime.utcnow(),
            'notes': notes
        }
        
        return await self.repo.create_balance_history(history_data)
    
    async def check_sufficient_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        required_amount: Decimal
    ) -> bool:
        """
        Check if branch has sufficient available balance
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            required_amount: Required amount
            
        Returns:
            True if sufficient balance exists
        """
        balance = await self.repo.get_branch_balance(branch_id, currency_id)
        
        if not balance:
            return False
        
        available = balance.balance - balance.reserved_balance
        return available >= required_amount
    
    # أضف هذه الدوال في app/services/balance_service.py
    # بعد دالة check_sufficient_balance

    async def get_branch_balances(
        self,
        branch_id: UUID
    ) -> list[BranchBalance]:
        """
        Get all currency balances for a branch
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            List of BranchBalance objects
        """
        try:
            balances = await self.repo.get_all_branch_balances(branch_id)
            return balances
        except Exception as e:
            logger.error(f"Error getting balances for branch {branch_id}: {str(e)}")
            raise DatabaseOperationError(f"Failed to retrieve branch balances: {str(e)}")
    
    async def get_branch_currency_balance(
        self,
        branch_id: UUID,
        currency_id: UUID
    ) -> Optional[BranchBalance]:
        """
        Get specific currency balance for a branch
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            
        Returns:
            BranchBalance object or None
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            return balance
        except Exception as e:
            logger.error(
                f"Error getting balance for branch {branch_id}, currency {currency_id}: {str(e)}"
            )
            raise DatabaseOperationError(f"Failed to retrieve balance: {str(e)}")
    
    async def set_thresholds(
        self,
        branch_id: UUID,
        currency_id: UUID,
        minimum_threshold: Optional[Decimal],
        maximum_threshold: Optional[Decimal],
        current_user: Optional[Dict[str, Any]] = None
    ) -> BranchBalance:
        """
        Set balance thresholds for alerts
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            minimum_threshold: Minimum balance threshold
            maximum_threshold: Maximum balance threshold
            current_user: User who is setting thresholds
            
        Returns:
            Updated BranchBalance object
        """
        # Validate thresholds
        if minimum_threshold is not None and minimum_threshold < 0:
            raise ValidationError("Minimum threshold cannot be negative")
        
        if maximum_threshold is not None and maximum_threshold < 0:
            raise ValidationError("Maximum threshold cannot be negative")
        
        if (minimum_threshold is not None and 
            maximum_threshold is not None and 
            minimum_threshold >= maximum_threshold):
            raise ValidationError("Minimum threshold must be less than maximum threshold")
        
        try:
            # Get existing balance
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} and currency {currency_id}"
                )
            
            # Update thresholds
            update_data = {}
            if minimum_threshold is not None:
                update_data['minimum_threshold'] = minimum_threshold
            if maximum_threshold is not None:
                update_data['maximum_threshold'] = maximum_threshold
            
            updated_balance = await self.repo.update_branch_balance(
                balance.id,
                update_data
            )
            
            logger.info(
                f"Thresholds updated for branch {branch_id}, currency {currency_id} "
                f"by user {current_user.get('username') if current_user else 'system'}"
            )
            
            return updated_balance
            
        except Exception as e:
            logger.error(f"Error setting thresholds: {str(e)}")
            raise DatabaseOperationError(f"Failed to set thresholds: {str(e)}")
    
    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> list[BranchBalanceHistory]:
        """
        Get balance change history
        
        Args:
            branch_id: Branch UUID
            currency_id: Optional currency filter
            start_date: Optional start date
            end_date: Optional end date
            limit: Maximum number of records
            
        Returns:
            List of BranchBalanceHistory records
        """
        try:
            history = await self.repo.get_balance_history(
                branch_id=branch_id,
                currency_id=currency_id,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            return history
        except Exception as e:
            logger.error(f"Error getting balance history: {str(e)}")
            raise DatabaseOperationError(f"Failed to retrieve balance history: {str(e)}")
    
    async def get_balance_summary(
        self,
        branch_id: UUID
    ) -> Dict[str, Any]:
        """
        Get comprehensive balance summary for a branch
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            Balance summary with statistics
        """
        try:
            balances = await self.repo.get_all_branch_balances(branch_id)
            
            summary = {
                'branch_id': str(branch_id),
                'total_currencies': len(balances),
                'balances': [],
                'total_balance_usd_equivalent': 0,  # Can be calculated later
                'alerts': {
                    'below_minimum': 0,
                    'above_maximum': 0
                }
            }
            
            for balance in balances:
                balance_info = {
                    'currency_code': balance.currency.code,
                    'currency_name': balance.currency.name_en,
                    'balance': float(balance.balance),
                    'reserved': float(balance.reserved_balance),
                    'available': float(balance.balance - balance.reserved_balance),
                    'minimum_threshold': float(balance.minimum_threshold) if balance.minimum_threshold else None,
                    'maximum_threshold': float(balance.maximum_threshold) if balance.maximum_threshold else None,
                    'last_updated': balance.updated_at.isoformat(),
                    'last_reconciled': balance.last_reconciled_at.isoformat() if balance.last_reconciled_at else None
                }
                
                # Check alerts
                if balance.minimum_threshold and balance.balance < balance.minimum_threshold:
                    balance_info['is_below_minimum'] = True
                    summary['alerts']['below_minimum'] += 1
                else:
                    balance_info['is_below_minimum'] = False
                
                if balance.maximum_threshold and balance.balance > balance.maximum_threshold:
                    balance_info['is_above_maximum'] = True
                    summary['alerts']['above_maximum'] += 1
                else:
                    balance_info['is_above_maximum'] = False
                
                summary['balances'].append(balance_info)
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting balance summary for branch {branch_id}: {str(e)}")
            raise DatabaseOperationError(f"Failed to retrieve balance summary: {str(e)}")
    
    async def get_branch_balance_details(
        self,
        branch_id: UUID,
        currency_id: UUID
    ) -> Dict[str, Any]:
        """
        Get detailed balance information for specific currency
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            
        Returns:
            Detailed balance information
        """
        try:
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} and currency {currency_id}"
                )
            
            return {
                'branch_id': str(branch_id),
                'currency_id': str(currency_id),
                'currency_code': balance.currency.code,
                'currency_name': balance.currency.name_en,
                'currency_symbol': balance.currency.symbol,
                'balance': float(balance.balance),
                'reserved_balance': float(balance.reserved_balance),
                'available_balance': float(balance.balance - balance.reserved_balance),
                'minimum_threshold': float(balance.minimum_threshold) if balance.minimum_threshold else None,
                'maximum_threshold': float(balance.maximum_threshold) if balance.maximum_threshold else None,
                'is_below_minimum': (
                    balance.minimum_threshold is not None and 
                    balance.balance < balance.minimum_threshold
                ),
                'is_above_maximum': (
                    balance.maximum_threshold is not None and 
                    balance.balance > balance.maximum_threshold
                ),
                'last_updated': balance.updated_at.isoformat(),
                'last_reconciled_at': balance.last_reconciled_at.isoformat() if balance.last_reconciled_at else None,
                'last_reconciled_by': str(balance.last_reconciled_by) if balance.last_reconciled_by else None
            }
            
        except Exception as e:
            logger.error(f"Error getting balance details: {str(e)}")
            raise DatabaseOperationError(f"Failed to retrieve balance details: {str(e)}")
    
    async def reconcile_branch_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        actual_balance: Decimal,
        reconciled_by: UUID,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Reconcile branch balance with actual physical count
        
        This compares the system balance with the actual counted balance
        and creates an adjustment if there's a difference.
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            actual_balance: Actual counted balance
            reconciled_by: User performing reconciliation
            notes: Additional notes
            
        Returns:
            Dict with reconciliation details:
            {
                'expected_balance': Decimal,
                'actual_balance': Decimal,
                'difference': Decimal,
                'adjustment_made': bool,
                'reconciliation_time': datetime
            }
            
        Raises:
            ValidationError: If validation fails
            DatabaseOperationError: If database operation fails
        """
        try:
            # Get current balance
            balance = await self.repo.get_branch_balance(branch_id, currency_id)
            
            if not balance:
                raise ValidationError(
                    f"Balance not found for branch {branch_id} "
                    f"and currency {currency_id}"
                )
            
            expected_balance = balance.balance
            difference = actual_balance - expected_balance
            
            reconciliation_result = {
                'expected_balance': expected_balance,
                'actual_balance': actual_balance,
                'difference': difference,
                'adjustment_made': False,
                'reconciliation_time': datetime.utcnow()
            }
            
            # If there's a difference, create adjustment
            if difference != 0:
                # Update balance
                await self.update_balance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    amount=difference,
                    change_type=BalanceChangeType.RECONCILIATION,
                    performed_by=reconciled_by,
                    notes=f"Reconciliation adjustment. {notes or ''}"
                )
                
                reconciliation_result['adjustment_made'] = True
                
                logger.warning(
                    f"Balance reconciliation adjustment: Branch {branch_id}, "
                    f"Currency {currency_id}, Difference: {difference}"
                )
            
            # Update reconciliation timestamp
            balance.last_reconciled_at = datetime.utcnow()
            balance.last_reconciled_by = reconciled_by
            
            await self.db.flush()
            
            logger.info(
                f"Balance reconciliation completed: Branch {branch_id}, "
                f"Currency {currency_id}, Expected: {expected_balance}, "
                f"Actual: {actual_balance}, Difference: {difference}"
            )
            
            return reconciliation_result
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Reconciliation failed: {str(e)}")
            raise DatabaseOperationError(f"Balance reconciliation failed: {str(e)}")


    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        change_type: Optional[BalanceChangeType] = None,
        limit: int = 100
    ) -> List[BranchBalanceHistory]:
        """
        Get balance change history with filtering
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            date_from: Start date (inclusive)
            date_to: End date (inclusive)
            change_type: Filter by change type
            limit: Maximum number of records (default: 100)
            
        Returns:
            List of balance history records
        """
        logger.info(
            f"Getting balance history: Branch {branch_id}, "
            f"Currency {currency_id}, From: {date_from}, To: {date_to}"
        )
        
        try:
            history = await self.repo.get_balance_history(
                branch_id=branch_id,
                currency_id=currency_id,
                date_from=date_from,
                date_to=date_to,
                change_type=change_type,
                limit=limit
            )
            
            return history
            
        except Exception as e:
            logger.error(f"Failed to get balance history: {str(e)}")
            raise DatabaseOperationError(f"Failed to retrieve balance history: {str(e)}")