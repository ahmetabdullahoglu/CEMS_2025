"""
Branch Repository
Data access layer for branch operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError

from app.db.models.branch import (
    Branch, BranchBalance, BranchBalanceHistory, BranchAlert,
    RegionEnum, BalanceAlertType, AlertSeverity
)
from app.db.models.currency import Currency
from app.db.models.user import User
from app.core.exceptions import (
    ResourceNotFoundError,
    DatabaseOperationError,
    ValidationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BranchRepository:
    """Repository for branch data access"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== Branch CRUD Operations ====================
    
    async def get_all_branches(
        self,
        region: Optional[RegionEnum] = None,
        is_active: bool = True,
        include_balances: bool = False
    ) -> List[Branch]:
        """
        Get all branches with optional filtering
        
        Args:
            region: Filter by region
            is_active: Filter by active status
            include_balances: Include balance relationships
            
        Returns:
            List of branches
        """
        stmt = select(Branch)
        
        # Add filters
        filters = []
        if is_active is not None:
            filters.append(Branch.is_active == is_active)
        if region:
            filters.append(Branch.region == region)
        
        if filters:
            stmt = stmt.where(and_(*filters))
        
        # Include relationships if requested
        if include_balances:
            stmt = stmt.options(
                selectinload(Branch.balances),
                selectinload(Branch.manager)
            )
        
        stmt = stmt.order_by(Branch.code)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_branch_by_id(
        self,
        branch_id: UUID,
        include_balances: bool = False
    ) -> Optional[Branch]:
        """
        Get branch by ID
        
        Args:
            branch_id: Branch UUID
            include_balances: Include balance relationships
            
        Returns:
            Branch or None
        """
        stmt = select(Branch).where(Branch.id == branch_id)
        
        if include_balances:
            stmt = stmt.options(
                selectinload(Branch.balances).selectinload(BranchBalance.currency),
                selectinload(Branch.manager)
            )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_branch_by_code(self, code: str) -> Optional[Branch]:
        """Get branch by code"""
        stmt = select(Branch).where(Branch.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_main_branch(self) -> Optional[Branch]:
        """Get the main branch"""
        stmt = select(Branch).where(
            and_(
                Branch.is_main_branch == True,
                Branch.is_active == True
            )
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def create_branch(self, branch_data: Dict[str, Any]) -> Branch:
        """
        Create new branch
        
        Args:
            branch_data: Branch creation data
            
        Returns:
            Created branch
            
        Raises:
            DatabaseOperationError: If creation fails
        """
        try:
            branch = Branch(**branch_data)
            self.db.add(branch)
            await self.db.flush()
            await self.db.refresh(branch)
            
            logger.info(f"Branch {branch.code} created successfully")
            return branch
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create branch: {str(e)}")
            raise DatabaseOperationError(f"Branch creation failed: {str(e)}")
    
    async def update_branch(
        self,
        branch_id: UUID,
        update_data: Dict[str, Any]
    ) -> Branch:
        """
        Update branch
        
        Args:
            branch_id: Branch UUID
            update_data: Update data
            
        Returns:
            Updated branch
        """
        branch = await self.get_branch_by_id(branch_id)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        try:
            for key, value in update_data.items():
                setattr(branch, key, value)
            
            await self.db.flush()
            await self.db.refresh(branch)
            
            logger.info(f"Branch {branch.code} updated successfully")
            return branch
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to update branch: {str(e)}")
            raise DatabaseOperationError(f"Branch update failed: {str(e)}")
    
    async def delete_branch(self, branch_id: UUID) -> bool:
        """
        Soft delete branch (set is_active = False)
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            True if successful
        """
        branch = await self.get_branch_by_id(branch_id)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        branch.is_active = False
        await self.db.flush()
        
        logger.info(f"Branch {branch.code} deleted successfully")
        return True
    
    async def get_user_branches(self, user_id: UUID) -> List[Branch]:
        """
        Get branches assigned to a user
        
        Args:
            user_id: User UUID
            
        Returns:
            List of branches
        """
        # Import here to avoid circular imports
        from app.db.models.user import user_branches
        
        stmt = select(Branch).join(
            user_branches,
            Branch.id == user_branches.c.branch_id
        ).where(
            and_(
                user_branches.c.user_id == user_id,
                Branch.is_active == True
            )
        ).order_by(Branch.code)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # ==================== Balance Operations ====================
    
    async def get_branch_balance(
        self,
        branch_id: UUID,
        currency_id: UUID
    ) -> Optional[BranchBalance]:
        """
        Get branch balance for specific currency
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            
        Returns:
            BranchBalance or None
        """
        stmt = select(BranchBalance).where(
            and_(
                BranchBalance.branch_id == branch_id,
                BranchBalance.currency_id == currency_id,
                BranchBalance.is_active == True
            )
        ).options(selectinload(BranchBalance.currency))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_branch_balances(self, branch_id: UUID) -> List[BranchBalance]:
        """
        Get all balances for a branch
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            List of branch balances
        """
        stmt = select(BranchBalance).where(
            and_(
                BranchBalance.branch_id == branch_id,
                BranchBalance.is_active == True
            )
        ).options(selectinload(BranchBalance.currency))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_branch_balance(
        self,
        balance_data: Dict[str, Any]
    ) -> BranchBalance:
        """
        Create branch balance
        
        Args:
            balance_data: Balance creation data
            
        Returns:
            Created branch balance
        """
        try:
            balance = BranchBalance(**balance_data)
            self.db.add(balance)
            await self.db.flush()
            await self.db.refresh(balance)
            
            logger.info(
                f"Balance created for branch {balance.branch_id}, "
                f"currency {balance.currency_id}"
            )
            return balance
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create balance: {str(e)}")
            raise DatabaseOperationError(f"Balance creation failed: {str(e)}")
    
    async def update_branch_balance(
        self,
        branch_id: UUID,
        currency_id: UUID,
        new_balance: float,
        reserved_balance: Optional[float] = None
    ) -> BranchBalance:
        """
        Update branch balance (with optimistic locking)
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            new_balance: New balance amount
            reserved_balance: New reserved balance (optional)
            
                    Returns:
            Updated branch balance
        """
        balance = await self.get_branch_balance(branch_id, currency_id)
        if not balance:
            raise ResourceNotFoundError(
                "BranchBalance",
                f"branch_id={branch_id}, currency_id={currency_id}"
            )
        
        balance.balance = new_balance
        if reserved_balance is not None:
            balance.reserved_balance = reserved_balance
        balance.last_updated = datetime.utcnow()
        
        await self.db.flush()
        await self.db.refresh(balance)
        
        return balance
    
    # ==================== Balance History ====================
    
    async def create_balance_history(
        self,
        history_data: Dict[str, Any]
    ) -> BranchBalanceHistory:
        """
        Create balance history record
        
        Args:
            history_data: History data
            
        Returns:
            Created history record
        """
        history = BranchBalanceHistory(**history_data)
        self.db.add(history)
        await self.db.flush()
        
        return history
    
    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[BranchBalanceHistory]:
        """
        Get balance history with filtering
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID (optional)
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum records to return
            
        Returns:
            List of balance history records
        """
        stmt = select(BranchBalanceHistory).where(
            BranchBalanceHistory.branch_id == branch_id
        )
        
        if currency_id:
            stmt = stmt.where(BranchBalanceHistory.currency_id == currency_id)
        
        if start_date:
            stmt = stmt.where(BranchBalanceHistory.performed_at >= start_date)
        
        if end_date:
            stmt = stmt.where(BranchBalanceHistory.performed_at <= end_date)
        
        stmt = stmt.order_by(desc(BranchBalanceHistory.performed_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # ==================== Alerts ====================
    
    async def get_branch_alerts(
        self,
        branch_id: UUID,
        is_resolved: Optional[bool] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[BranchAlert]:
        """
        Get branch alerts with filtering
        
        Args:
            branch_id: Branch UUID
            is_resolved: Filter by resolution status
            severity: Filter by severity
            
        Returns:
            List of branch alerts
        """
        stmt = select(BranchAlert).where(BranchAlert.branch_id == branch_id)
        
        if is_resolved is not None:
            stmt = stmt.where(BranchAlert.is_resolved == is_resolved)
        
        if severity:
            stmt = stmt.where(BranchAlert.severity == severity)
        
        stmt = stmt.order_by(desc(BranchAlert.triggered_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def create_alert(self, alert_data: Dict[str, Any]) -> BranchAlert:
        """Create branch alert"""
        alert = BranchAlert(**alert_data)
        self.db.add(alert)
        await self.db.flush()
        
        logger.info(f"Alert created for branch {alert.branch_id}: {alert.title}")
        return alert
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: UUID,
        resolution_notes: str
    ) -> BranchAlert:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert UUID
            resolved_by: User UUID who resolved the alert
            resolution_notes: Notes about resolution
            
        Returns:
            Resolved alert
        """
        stmt = select(BranchAlert).where(BranchAlert.id == alert_id)
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise ResourceNotFoundError("BranchAlert", alert_id)
        
        alert.is_resolved = True
        alert.resolved_at = datetime.utcnow()
        alert.resolved_by = resolved_by
        alert.resolution_notes = resolution_notes
        
        await self.db.flush()
        await self.db.refresh(alert)
        
        logger.info(f"Alert {alert_id} resolved by user {resolved_by}")
        return alert
    
    # ==================== Statistics & Aggregations ====================
    
    async def get_branch_statistics(self, branch_id: UUID) -> Dict[str, Any]:
        """
        Get branch statistics
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            Dictionary with statistics
        """
        # Get total balances by currency
        stmt = select(
            Currency.code,
            func.sum(BranchBalance.balance).label('total_balance'),
            func.sum(BranchBalance.reserved_balance).label('total_reserved')
        ).join(
            BranchBalance,
            Currency.id == BranchBalance.currency_id
        ).where(
            and_(
                BranchBalance.branch_id == branch_id,
                BranchBalance.is_active == True
            )
        ).group_by(Currency.code)
        
        result = await self.db.execute(stmt)
        balances = result.all()
        
        # Get active alerts count
        alerts_stmt = select(func.count()).select_from(BranchAlert).where(
            and_(
                BranchAlert.branch_id == branch_id,
                BranchAlert.is_resolved == False
            )
        )
        alerts_result = await self.db.execute(alerts_stmt)
        active_alerts = alerts_result.scalar()
        
        return {
            'balances': [
                {
                    'currency': row.code,
                    'total': float(row.total_balance),
                    'reserved': float(row.total_reserved),
                    'available': float(row.total_balance - row.total_reserved)
                }
                for row in balances
            ],
            'active_alerts': active_alerts
        }