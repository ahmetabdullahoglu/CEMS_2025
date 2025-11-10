"""
Branch Repository - FIXED VERSION
Data access layer for branch operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.branch import (
    Branch, BranchBalance, BranchBalanceHistory, BranchAlert,
    RegionEnum, BalanceAlertType, AlertSeverity, BalanceChangeType  
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
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Branch CRUD Operations ====================
    
    async def get_all_branches(
        self,
        region: Optional[RegionEnum] = None,
        is_active: bool = True,
        include_balances: bool = False,
        search: Optional[str] = None
    ) -> List[Branch]:
        """
        Get all branches with optional filtering and search

        Args:
            region: Filter by region
            is_active: Filter by active status
            include_balances: Include balance relationships
            search: Search term for name, code, city, or address

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

        # Add search filter
        if search:
            search_term = f"%{search.lower()}%"
            filters.append(
                or_(
                    Branch.name_en.ilike(search_term),
                    Branch.name_ar.ilike(search_term),
                    Branch.code.ilike(search_term),
                    Branch.city.ilike(search_term),
                    Branch.address.ilike(search_term)
                )
            )

        if filters:
            stmt = stmt.where(and_(*filters))

        # ✅ FIX: Include currency relationship when loading balances
        if include_balances:
            stmt = stmt.options(
                selectinload(Branch.balances).selectinload(BranchBalance.currency),
                selectinload(Branch.manager)
            )  # ← الإصلاح: إغلاق القوس بشكل صحيح
        else:
            stmt = stmt.options(
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
        Update branch balance
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            new_balance: New balance amount
            reserved_balance: Optional reserved amount
            
        Returns:
            Updated balance
        """
        balance = await self.get_branch_balance(branch_id, currency_id)
        if not balance:
            raise ResourceNotFoundError(
                "BranchBalance",
                f"branch_id={branch_id}, currency_id={currency_id}"
            )
        
        try:
            balance.balance = new_balance
            if reserved_balance is not None:
                balance.reserved_balance = reserved_balance
            balance.updated_at = datetime.utcnow()
            
            await self.db.flush()
            await self.db.refresh(balance)
            
            logger.info(
                f"Balance updated for branch {branch_id}, "
                f"currency {currency_id}: {new_balance}"
            )
            return balance
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to update balance: {str(e)}")
            raise DatabaseOperationError(f"Balance update failed: {str(e)}")
    
    # ==================== Balance History Operations ====================
    
    async def create_balance_history(
        self,
        history_data: Dict[str, Any]
    ) -> BranchBalanceHistory:
        """
        Create balance history record
        
        Args:
            history_data: History record data
            
        Returns:
            Created history record
        """
        try:
            history = BranchBalanceHistory(**history_data)
            self.db.add(history)
            await self.db.flush()
            await self.db.refresh(history)
            
            logger.info(
                f"Balance history created for branch {history.branch_id}, "
                f"change type: {history.change_type}"
            )
            return history
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create balance history: {str(e)}")
            raise DatabaseOperationError(f"Balance history creation failed: {str(e)}")
    
    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[BranchBalanceHistory]:
        """
        Get balance history for branch
        
        Args:
            branch_id: Branch UUID
            currency_id: Optional currency filter
            limit: Number of records to return
            
        Returns:
            List of history records
        """
        stmt = select(BranchBalanceHistory).where(
            BranchBalanceHistory.branch_id == branch_id
        )
        
        if currency_id:
            stmt = stmt.where(BranchBalanceHistory.currency_id == currency_id)
        
        stmt = stmt.order_by(desc(BranchBalanceHistory.performed_at)).limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # ==================== Alert Operations ====================
    
    async def create_branch_alert(
        self,
        alert_data: Dict[str, Any]
    ) -> BranchAlert:
        """
        Create branch alert
        
        Args:
            alert_data: Alert data
            
        Returns:
            Created alert
        """
        try:
            alert = BranchAlert(**alert_data)
            self.db.add(alert)
            await self.db.flush()
            await self.db.refresh(alert)
            
            logger.info(
                f"Alert created for branch {alert.branch_id}: "
                f"Type: {alert.alert_type}, Severity: {alert.severity}"
            )
            return alert
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create alert: {str(e)}")
            raise DatabaseOperationError(f"Alert creation failed: {str(e)}")
    
    async def get_active_alerts(
        self,
        branch_id: UUID,
        severity: Optional[AlertSeverity] = None
    ) -> List[BranchAlert]:
        """
        Get active alerts for branch
        
        Args:
            branch_id: Branch UUID
            severity: Optional severity filter
            
        Returns:
            List of active alerts
        """
        stmt = select(BranchAlert).where(
            and_(
                BranchAlert.branch_id == branch_id,
                BranchAlert.is_resolved == False
            )
        )
        
        if severity:
            stmt = stmt.where(BranchAlert.severity == severity)
        
        stmt = stmt.order_by(desc(BranchAlert.created_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: UUID,
        resolution_notes: Optional[str] = None
    ) -> BranchAlert:
        """
        Resolve branch alert
        
        Args:
            alert_id: Alert UUID
            resolved_by: User who resolved the alert
            resolution_notes: Optional resolution notes
            
        Returns:
            Resolved alert
        """
        stmt = select(BranchAlert).where(BranchAlert.id == alert_id)
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            raise ResourceNotFoundError("BranchAlert", alert_id)
        
        try:
            alert.is_resolved = True
            alert.resolved_at = datetime.utcnow()
            alert.resolved_by = resolved_by
            alert.resolution_notes = resolution_notes
            
            await self.db.flush()
            await self.db.refresh(alert)
            
            logger.info(f"Alert {alert_id} resolved by user {resolved_by}")
            return alert
            
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to resolve alert: {str(e)}")
            raise DatabaseOperationError(f"Alert resolution failed: {str(e)}")


    async def assign_users_to_branch(
        self,
        branch_id: UUID,
        user_ids: List[UUID]
    ) -> Branch:
        """
        Assign users to branch using many-to-many relationship
        
        Args:
            branch_id: Branch UUID
            user_ids: List of user UUIDs
            
        Returns:
            Branch with updated users
        """
        from app.db.models.user import user_branches
        
        # Get branch
        branch = await self.get_branch_by_id(branch_id)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        # Clear existing assignments
        stmt_delete = user_branches.delete().where(
            user_branches.c.branch_id == branch_id
        )
        await self.db.execute(stmt_delete)
        
        # Add new assignments
        for user_id in user_ids:
            stmt_insert = user_branches.insert().values(
                branch_id=branch_id,
                user_id=user_id
            )
            await self.db.execute(stmt_insert)
        
        await self.db.flush()
        
        return branch


    async def remove_user_from_branch(
        self,
        branch_id: UUID,
        user_id: UUID
    ) -> bool:
        """
        Remove a user from branch
        
        Args:
            branch_id: Branch UUID
            user_id: User UUID
            
        Returns:
            True if successful
        """
        from app.db.models.user import user_branches
        
        stmt = user_branches.delete().where(
            and_(
                user_branches.c.branch_id == branch_id,
                user_branches.c.user_id == user_id
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        return result.rowcount > 0


    async def get_or_create_alert(
        self,
        branch_id: UUID,
        currency_id: UUID,
        alert_type: BalanceAlertType,
        severity: AlertSeverity,
        title: str,
        message: str
    ) -> BranchAlert:
        """
        Get existing unresolved alert or create new one
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            alert_type: Type of alert
            severity: Alert severity
            title: Alert title
            message: Alert message
            
        Returns:
            BranchAlert instance
        """
        # Check if alert already exists
        stmt = select(BranchAlert).where(
            and_(
                BranchAlert.branch_id == branch_id,
                BranchAlert.currency_id == currency_id,
                BranchAlert.alert_type == alert_type,
                BranchAlert.is_resolved == False
            )
        )
        
        result = await self.db.execute(stmt)
        alert = result.scalar_one_or_none()
        
        if not alert:
            # Create new alert
            alert = BranchAlert(
                id=uuid.uuid4(),
                branch_id=branch_id,
                currency_id=currency_id,
                alert_type=alert_type,
                severity=severity,
                title=title,
                message=message,
                triggered_at=datetime.utcnow()
            )
            self.db.add(alert)
            await self.db.flush()
        
        return alert


    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: UUID,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        change_type: Optional[BalanceChangeType] = None,
        limit: int = 100
    ) -> List[BranchBalanceHistory]:
        """Get balance change history"""
        stmt = select(BranchBalanceHistory).where(
            and_(
                BranchBalanceHistory.branch_id == branch_id,
                BranchBalanceHistory.currency_id == currency_id
            )
        )
        
        # Add filters
        if date_from:
            stmt = stmt.where(BranchBalanceHistory.performed_at >= date_from)
        
        if date_to:
            stmt = stmt.where(BranchBalanceHistory.performed_at <= date_to)
        
        if change_type:
            stmt = stmt.where(BranchBalanceHistory.change_type == change_type)
        
        stmt = stmt.order_by(desc(BranchBalanceHistory.performed_at))
        stmt = stmt.limit(limit)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def get_branch_alerts(
        self,
        branch_id: UUID,
        is_resolved: bool = False
    ) -> List[BranchAlert]:
        """Get branch alerts"""
        stmt = select(BranchAlert).where(
            and_(
                BranchAlert.branch_id == branch_id,
                BranchAlert.is_resolved == is_resolved
            )
        ).order_by(desc(BranchAlert.triggered_at))
        
        result = await self.db.execute(stmt)
        return result.scalars().all()


    async def resolve_alert(
        self,
        alert_id: UUID,
        resolved_by: UUID,
        resolution_notes: str
    ) -> BranchAlert:
        """Resolve an alert"""
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
        
        return alert