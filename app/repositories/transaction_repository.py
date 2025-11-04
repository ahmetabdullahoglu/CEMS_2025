# app/repositories/transaction_repository.py
"""
Transaction Repository
======================
Data access layer for transaction operations with complex queries
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, and_, or_, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.db.models.transaction import (
    Transaction, IncomeTransaction, ExpenseTransaction,
    ExchangeTransaction, TransferTransaction,
    TransactionType, TransactionStatus
)
from app.db.models.branch import Branch
from app.db.models.currency import Currency
from app.db.models.customer import Customer
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TransactionRepository:
    """Repository for transaction data access"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== BASIC CRUD ====================
    
    async def get_by_id(
        self, transaction_id: UUID, load_relations: bool = True
    ) -> Optional[Transaction]:
        """
        Get transaction by ID with optional eager loading
        
        Args:
            transaction_id: Transaction UUID
            load_relations: Load related entities (branch, currency, user, etc.)
            
        Returns:
            Transaction or None
        """
        stmt = select(Transaction).where(Transaction.id == transaction_id)
        
        if load_relations:
            stmt = stmt.options(
                joinedload(Transaction.branch),
                joinedload(Transaction.currency),
                joinedload(Transaction.user),
                selectinload(Transaction.customer)
            )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_transaction_number(
        self, transaction_number: str
    ) -> Optional[Transaction]:
        """Get transaction by transaction number"""
        stmt = select(Transaction).where(
            Transaction.transaction_number == transaction_number
        ).options(
            joinedload(Transaction.branch),
            joinedload(Transaction.currency)
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    # ==================== FILTERED QUERIES ====================
    
    async def get_transactions(
        self,
        branch_id: Optional[UUID] = None,
        customer_id: Optional[UUID] = None,
        currency_id: Optional[UUID] = None,
        transaction_type: Optional[TransactionType] = None,
        status: Optional[TransactionStatus] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        min_amount: Optional[Decimal] = None,
        max_amount: Optional[Decimal] = None,
        reference_number: Optional[str] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "transaction_date",
        order_desc: bool = True
    ) -> Tuple[List[Transaction], int]:
        """
        Get transactions with comprehensive filtering and pagination
        
        Returns:
            Tuple of (transactions list, total count)
        """
        # Base query
        stmt = select(Transaction)
        count_stmt = select(func.count(Transaction.id))
        
        # Apply filters
        filters = []
        
        if branch_id:
            filters.append(Transaction.branch_id == branch_id)
        
        if customer_id:
            filters.append(Transaction.customer_id == customer_id)
        
        if currency_id:
            filters.append(Transaction.currency_id == currency_id)
        
        if transaction_type:
            filters.append(Transaction.transaction_type == transaction_type)
        
        if status:
            filters.append(Transaction.status == status)
        
        if date_from:
            filters.append(Transaction.transaction_date >= date_from)
        
        if date_to:
            filters.append(Transaction.transaction_date <= date_to)
        
        if min_amount is not None:
            filters.append(Transaction.amount >= min_amount)
        
        if max_amount is not None:
            filters.append(Transaction.amount <= max_amount)
        
        if reference_number:
            filters.append(
                Transaction.reference_number.ilike(f"%{reference_number}%")
            )
        
        if filters:
            stmt = stmt.where(and_(*filters))
            count_stmt = count_stmt.where(and_(*filters))
        
        # Get total count
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar()
        
        # Apply ordering
        if order_by == "transaction_date":
            order_col = Transaction.transaction_date
        elif order_by == "amount":
            order_col = Transaction.amount
        elif order_by == "created_at":
            order_col = Transaction.created_at
        else:
            order_col = Transaction.transaction_date
        
        if order_desc:
            stmt = stmt.order_by(order_col.desc())
        else:
            stmt = stmt.order_by(order_col.asc())
        
        # Apply pagination
        stmt = stmt.offset(skip).limit(limit)
        
        # Load relations
        stmt = stmt.options(
            joinedload(Transaction.branch),
            joinedload(Transaction.currency),
            joinedload(Transaction.user),
            selectinload(Transaction.customer)
        )
        
        result = await self.db.execute(stmt)
        transactions = list(result.scalars().all())
        
        return transactions, total_count
    
    # ==================== SPECIALIZED QUERIES ====================
    
    async def get_pending_transfers(
        self, branch_id: Optional[UUID] = None
    ) -> List[TransferTransaction]:
        """
        Get all pending transfers (waiting for receipt)
        
        Args:
            branch_id: Filter by destination branch (optional)
        """
        stmt = select(TransferTransaction).where(
            TransferTransaction.status == TransactionStatus.PENDING
        )
        
        if branch_id:
            stmt = stmt.where(TransferTransaction.to_branch_id == branch_id)
        
        stmt = stmt.order_by(TransferTransaction.transaction_date.desc())
        stmt = stmt.options(
            joinedload(TransferTransaction.branch),
            joinedload(TransferTransaction.currency),
            joinedload(TransferTransaction.user)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_expenses_requiring_approval(
        self, branch_id: Optional[UUID] = None
    ) -> List[ExpenseTransaction]:
        """Get expenses that need approval"""
        stmt = select(ExpenseTransaction).where(
            and_(
                ExpenseTransaction.approval_required == True,
                ExpenseTransaction.approved_by_id.is_(None),
                ExpenseTransaction.status == TransactionStatus.PENDING
            )
        )
        
        if branch_id:
            stmt = stmt.where(ExpenseTransaction.branch_id == branch_id)
        
        stmt = stmt.order_by(ExpenseTransaction.transaction_date.desc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_customer_transaction_history(
        self,
        customer_id: UUID,
        transaction_type: Optional[TransactionType] = None,
        limit: int = 50
    ) -> List[Transaction]:
        """Get recent transactions for a customer"""
        stmt = select(Transaction).where(
            Transaction.customer_id == customer_id
        )
        
        if transaction_type:
            stmt = stmt.where(Transaction.transaction_type == transaction_type)
        
        stmt = stmt.order_by(Transaction.transaction_date.desc())
        stmt = stmt.limit(limit)
        stmt = stmt.options(
            joinedload(Transaction.branch),
            joinedload(Transaction.currency)
        )
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    async def get_daily_transactions(
        self,
        branch_id: UUID,
        date: datetime
    ) -> List[Transaction]:
        """Get all transactions for a specific day"""
        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
        
        stmt = select(Transaction).where(
            and_(
                Transaction.branch_id == branch_id,
                Transaction.transaction_date >= start_of_day,
                Transaction.transaction_date <= end_of_day
            )
        )
        
        stmt = stmt.order_by(Transaction.transaction_date.asc())
        
        result = await self.db.execute(stmt)
        return list(result.scalars().all())
    
    # ==================== STATISTICS & AGGREGATION ====================
    
    async def get_transaction_summary(
        self,
        branch_id: Optional[UUID] = None,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get comprehensive transaction summary with aggregations
        """
        stmt = select(
            Transaction.transaction_type,
            Transaction.status,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount'),
            func.avg(Transaction.amount).label('avg_amount'),
            func.min(Transaction.amount).label('min_amount'),
            func.max(Transaction.amount).label('max_amount')
        )
        
        filters = []
        
        if branch_id:
            filters.append(Transaction.branch_id == branch_id)
        
        if date_from:
            filters.append(Transaction.transaction_date >= date_from)
        
        if date_to:
            filters.append(Transaction.transaction_date <= date_to)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        stmt = stmt.group_by(
            Transaction.transaction_type,
            Transaction.status
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        summary = {
            'by_type': {},
            'by_status': {},
            'overall': {
                'total_transactions': 0,
                'total_amount': Decimal('0')
            }
        }
        
        for row in rows:
            type_key = row.transaction_type.value
            status_key = row.status.value
            
            # By type
            if type_key not in summary['by_type']:
                summary['by_type'][type_key] = {
                    'count': 0,
                    'total_amount': Decimal('0')
                }
            
            summary['by_type'][type_key]['count'] += row.count
            summary['by_type'][type_key]['total_amount'] += (
                row.total_amount or Decimal('0')
            )
            
            # By status
            if status_key not in summary['by_status']:
                summary['by_status'][status_key] = {
                    'count': 0,
                    'total_amount': Decimal('0')
                }
            
            summary['by_status'][status_key]['count'] += row.count
            summary['by_status'][status_key]['total_amount'] += (
                row.total_amount or Decimal('0')
            )
            
            # Overall
            summary['overall']['total_transactions'] += row.count
            summary['overall']['total_amount'] += (
                row.total_amount or Decimal('0')
            )
        
        return summary
    
    async def get_daily_summary(
        self,
        branch_id: UUID,
        date_from: datetime,
        date_to: datetime
    ) -> List[Dict[str, Any]]:
        """
        Get daily transaction summary for a date range
        """
        stmt = select(
            func.date(Transaction.transaction_date).label('date'),
            Transaction.transaction_type,
            func.count(Transaction.id).label('count'),
            func.sum(Transaction.amount).label('total_amount')
        ).where(
            and_(
                Transaction.branch_id == branch_id,
                Transaction.transaction_date >= date_from,
                Transaction.transaction_date <= date_to,
                Transaction.status == TransactionStatus.COMPLETED
            )
        ).group_by(
            func.date(Transaction.transaction_date),
            Transaction.transaction_type
        ).order_by(
            func.date(Transaction.transaction_date).desc()
        )
        
        result = await self.db.execute(stmt)
        rows = result.all()
        
        # Group by date
        daily_data = {}
        
        for row in rows:
            date_key = row.date.isoformat()
            
            if date_key not in daily_data:
                daily_data[date_key] = {
                    'date': row.date,
                    'income': 0,
                    'expense': 0,
                    'exchange': 0,
                    'transfer': 0,
                    'total': 0
                }
            
            type_key = row.transaction_type.value
            daily_data[date_key][type_key] = int(row.count)
            daily_data[date_key]['total'] += int(row.count)
        
        return list(daily_data.values())
    
    async def get_exchange_rate_usage(
        self,
        from_currency_id: UUID,
        to_currency_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get exchange transactions with rates used
        
        Useful for rate analysis and auditing
        """
        stmt = select(ExchangeTransaction).where(
            and_(
                ExchangeTransaction.from_currency_id == from_currency_id,
                ExchangeTransaction.to_currency_id == to_currency_id,
                ExchangeTransaction.status == TransactionStatus.COMPLETED
            )
        )
        
        if date_from:
            stmt = stmt.where(ExchangeTransaction.transaction_date >= date_from)
        
        if date_to:
            stmt = stmt.where(ExchangeTransaction.transaction_date <= date_to)
        
        stmt = stmt.order_by(ExchangeTransaction.transaction_date.desc())
        
        result = await self.db.execute(stmt)
        exchanges = result.scalars().all()
        
        return [
            {
                'transaction_number': ex.transaction_number,
                'transaction_date': ex.transaction_date,
                'from_amount': float(ex.from_amount),
                'to_amount': float(ex.to_amount),
                'rate_used': float(ex.exchange_rate_used),
                'commission': float(ex.commission_amount),
                'customer_id': str(ex.customer_id) if ex.customer_id else None
            }
            for ex in exchanges
        ]
    
    # ==================== VALIDATION ====================
    
    async def check_duplicate_reference(
        self, reference_number: str
    ) -> Optional[Transaction]:
        """Check if reference number already exists"""
        stmt = select(Transaction).where(
            Transaction.reference_number == reference_number
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_last_transaction_number(
        self, transaction_type: TransactionType
    ) -> Optional[str]:
        """Get the last transaction number for a type (for number generation)"""
        stmt = select(Transaction.transaction_number).where(
            Transaction.transaction_type == transaction_type
        ).order_by(
            Transaction.created_at.desc()
        ).limit(1)
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
