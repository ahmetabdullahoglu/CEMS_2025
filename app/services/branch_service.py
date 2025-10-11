"""
Branch Service
Business logic for branch administrative operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession


from app.repositories.branch_repo import BranchRepository
from app.services.balance_service import BalanceService
from app.db.models.branch import (
    Branch, BranchAlert, RegionEnum,
    BalanceAlertType, AlertSeverity
)
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
    DatabaseOperationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class BranchService:
    """Service for branch operations"""
    
    async def __init__(self, db: Session):
        self.db = db
        self.repo = BranchRepository(db)
        self.balance_service = BalanceService(db)
    
    # ==================== Branch CRUD Operations ====================
    
    async def create_branch(
        self,
        branch_data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Branch:
        """
        Create new branch
        
        Args:
            branch_data: Branch creation data
            current_user: Current authenticated user
            
        Returns:
            Created branch
            
        Raises:
            ValidationError: If validation fails
            BusinessRuleViolationError: If business rules violated
        """
        logger.info(
            f"Creating branch {branch_data.get('code')} "
            f"by user {current_user['id']}"
        )
        
        # Validate branch code format
        code = branch_data.get('code', '')
        if not code.startswith('BR') or not code[2:].isdigit():
            raise ValidationError(
                "Branch code must start with 'BR' followed by digits (e.g., BR001)"
            )
        
        # Check if code already exists
        existing = await self.repo.get_branch_by_code(code)
        if existing:
            raise ValidationError(f"Branch code {code} already exists")
        
        # Check main branch constraint
        if branch_data.get('is_main_branch', False):
            main_branch = await self.repo.get_main_branch()
            if main_branch:
                raise BusinessRuleViolationError(
                    f"Main branch already exists: {main_branch.code}. "
                    "Only one main branch is allowed."
                )
        
        try:
            # Add audit fields
            branch_data['created_by'] = current_user['id']
            branch_data['updated_by'] = current_user['id']
            
            # Create branch
            branch = await self.repo.create_branch(branch_data)
            await self.db.commit()
            
            logger.info(f"Branch {branch.code} created successfully")
            return branch
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to create branch: {str(e)}")
            raise DatabaseOperationError(f"Branch creation failed: {str(e)}")
    
    async def update_branch(
        self,
        branch_id: UUID,
        update_data: Dict[str, Any],
        current_user: Dict[str, Any]
    ) -> Branch:
        """
        Update branch
        
        Args:
            branch_id: Branch UUID
            update_data: Update data
            current_user: Current authenticated user
            
        Returns:
            Updated branch
        """
        logger.info(
            f"Updating branch {branch_id} by user {current_user['id']}"
        )
        
        branch = await self.repo.get_branch_by_id(branch_id)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        # Check main branch constraint if being updated
        if update_data.get('is_main_branch', False) and not branch.is_main_branch:
            main_branch = await self.repo.get_main_branch()
            if main_branch and main_branch.id != branch_id:
                raise BusinessRuleViolationError(
                    f"Main branch already exists: {main_branch.code}"
                )
        
        try:
            # Add audit field
            update_data['updated_by'] = current_user['id']
            
            # Update branch
            updated_branch = await self.repo.update_branch(branch_id, update_data)
            await self.db.commit()
            
            logger.info(f"Branch {branch.code} updated successfully")
            return updated_branch
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to update branch: {str(e)}")
            raise DatabaseOperationError(f"Branch update failed: {str(e)}")
    
    async def delete_branch(
        self,
        branch_id: UUID,
        current_user: Dict[str, Any]
    ) -> bool:
        """
        Soft delete branch
        
        Args:
            branch_id: Branch UUID
            current_user: Current authenticated user
            
        Returns:
            True if successful
            
        Raises:
            BusinessRuleViolationError: If branch cannot be deleted
        """
        logger.info(
            f"Deleting branch {branch_id} by user {current_user['id']}"
        )
        
        branch = await self.repo.get_branch_by_id(branch_id, include_balances=True)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        # Check if main branch
        if branch.is_main_branch:
            raise BusinessRuleViolationError(
                "Cannot delete main branch"
            )
        
        # Check if branch has balances (optional: you may want to allow this)
        if branch.balances:
            total_balance = sum(b.balance for b in branch.balances)
            if total_balance > 0:
                raise BusinessRuleViolationError(
                    f"Cannot delete branch with non-zero balances. "
                    f"Total balance: {total_balance}"
                )
        
        try:
            await self.repo.delete_branch(branch_id)
            await self.db.commit()
            
            logger.info(f"Branch {branch.code} deleted successfully")
            return True
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to delete branch: {str(e)}")
            raise DatabaseOperationError(f"Branch deletion failed: {str(e)}")
    
    async def get_branch(
        self,
        branch_id: UUID,
        include_balances: bool = False
    ) -> Branch:
        """Get branch by ID"""
        branch = await self.repo.get_branch_by_id(branch_id, include_balances)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        return branch
    
    async def get_branch_by_code(self, code: str) -> Branch:
        """Get branch by code"""
        branch = await self.repo.get_branch_by_code(code)
        if not branch:
            raise ResourceNotFoundError("Branch", code)
        return branch
    
    async def get_all_branches(
        self,
        region: Optional[RegionEnum] = None,
        is_active: bool = True,
        include_balances: bool = False
    ) -> List[Branch]:
        """Get all branches with filtering"""
        return await self.repo.get_all_branches(region, is_active, include_balances)
    
    async def get_user_branches(self, user_id: UUID) -> List[Branch]:
        """Get branches assigned to a user"""
        return await self.repo.get_user_branches(user_id)
    
    # ==================== Branch-User Assignment ====================
    
    async def assign_manager(
        self,
        branch_id: UUID,
        user_id: UUID,
        current_user: Dict[str, Any]
    ) -> Branch:
        """
        Assign manager to branch
        
        Args:
            branch_id: Branch UUID
            user_id: User UUID to assign as manager
            current_user: Current authenticated user
            
        Returns:
            Updated branch
        """
        logger.info(
            f"Assigning user {user_id} as manager of branch {branch_id} "
            f"by user {current_user['id']}"
        )
        
        branch = await self.repo.get_branch_by_id(branch_id)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        try:
            update_data = {
                'manager_id': user_id,
                'updated_by': current_user['id']
            }
            
            updated_branch = await self.repo.update_branch(branch_id, update_data)
            await self.db.commit()
            
            logger.info(f"Manager assigned successfully to branch {branch.code}")
            return updated_branch
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to assign manager: {str(e)}")
            raise DatabaseOperationError(f"Manager assignment failed: {str(e)}")
    
    # ==================== Balance Management ====================
    
    async def get_branch_balance(
        self,
        branch_id: UUID,
        currency_id: UUID
    ) -> Dict[str, Any]:
        """
        Get branch balance for specific currency
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            
        Returns:
            Balance information
        """
        balance = await self.repo.get_branch_balance(branch_id, currency_id)
        if not balance:
            raise ResourceNotFoundError(
                "BranchBalance",
                f"branch_id={branch_id}, currency_id={currency_id}"
            )
        
        return {
            'branch_id': str(branch_id),
            'currency_code': balance.currency.code,
            'currency_name': balance.currency.name_en,
            'balance': float(balance.balance),
            'reserved_balance': float(balance.reserved_balance),
            'available_balance': float(balance.available_balance),
            'minimum_threshold': float(balance.minimum_threshold) if balance.minimum_threshold else None,
            'maximum_threshold': float(balance.maximum_threshold) if balance.maximum_threshold else None,
            'last_updated': balance.last_updated.isoformat(),
            'last_reconciled_at': balance.last_reconciled_at.isoformat() if balance.last_reconciled_at else None
        }
    
    async def get_all_balances(self, branch_id: UUID) -> Dict[str, Any]:
        """Get all balances for a branch"""
        return self.balance_service.get_balance_summary(branch_id)
    
    async def set_balance_thresholds(
        self,
        branch_id: UUID,
        currency_id: UUID,
        minimum_threshold: Optional[float],
        maximum_threshold: Optional[float],
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Set balance thresholds for alerts
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID
            minimum_threshold: Minimum balance threshold
            maximum_threshold: Maximum balance threshold
            current_user: Current authenticated user
            
        Returns:
            Updated balance information
        """
        logger.info(
            f"Setting thresholds for branch {branch_id}, currency {currency_id} "
            f"by user {current_user['id']}"
        )
        
        balance = self.repo.get_branch_balance(branch_id, currency_id)
        if not balance:
            raise ResourceNotFoundError(
                "BranchBalance",
                f"branch_id={branch_id}, currency_id={currency_id}"
            )
        
        # Validate thresholds
        if minimum_threshold and minimum_threshold < 0:
            raise ValidationError("Minimum threshold cannot be negative")
        
        if maximum_threshold and maximum_threshold < 0:
            raise ValidationError("Maximum threshold cannot be negative")
        
        if (minimum_threshold and maximum_threshold and 
            minimum_threshold >= maximum_threshold):
            raise ValidationError(
                "Minimum threshold must be less than maximum threshold"
            )
        
        try:
            balance.minimum_threshold = minimum_threshold
            balance.maximum_threshold = maximum_threshold
            await self.db.flush()
            await self.db.commit()
            
            logger.info(f"Thresholds set successfully")
            return await self.get_branch_balance(branch_id, currency_id)
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to set thresholds: {str(e)}")
            raise DatabaseOperationError(f"Threshold update failed: {str(e)}")
    
    # ==================== Alert Management ====================
    
    async def check_balance_alerts(self, branch_id: UUID) -> List[Dict[str, Any]]:
        """
        Check for balance alerts
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            List of active alerts
        """
        alerts = await self.repo.get_branch_alerts(
            branch_id,
            is_resolved=False
        )
        
        return [
            {
                'id': str(alert.id),
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'triggered_at': alert.triggered_at.isoformat(),
                'currency_code': alert.currency.code if alert.currency else None
            }
            for alert in alerts
        ]
    
    async def get_alerts(
        self,
        branch_id: UUID,
        is_resolved: Optional[bool] = None,
        severity: Optional[AlertSeverity] = None
    ) -> List[Dict[str, Any]]:
        """
        Get branch alerts with filtering
        
        Args:
            branch_id: Branch UUID
            is_resolved: Filter by resolution status
            severity: Filter by severity
            
        Returns:
            List of alerts
        """
        alerts = await self.repo.get_branch_alerts(branch_id, is_resolved, severity)
        
        return [
            {
                'id': str(alert.id),
                'branch_id': str(alert.branch_id),
                'currency_id': str(alert.currency_id) if alert.currency_id else None,
                'alert_type': alert.alert_type.value,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'is_resolved': alert.is_resolved,
                'triggered_at': alert.triggered_at.isoformat(),
                'resolved_at': alert.resolved_at.isoformat() if alert.resolved_at else None,
                'resolved_by': str(alert.resolved_by) if alert.resolved_by else None,
                'resolution_notes': alert.resolution_notes
            }
            for alert in alerts
        ]
    
    async def resolve_alert(
        self,
        alert_id: UUID,
        resolution_notes: str,
        current_user: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Resolve an alert
        
        Args:
            alert_id: Alert UUID
            resolution_notes: Notes about resolution
            current_user: Current authenticated user
            
        Returns:
            Resolved alert information
        """
        logger.info(
            f"Resolving alert {alert_id} by user {current_user['id']}"
        )
        
        try:
            alert = await self.repo.resolve_alert(
                alert_id,
                current_user['id'],
                resolution_notes
            )
            await self.db.commit()
            
            logger.info(f"Alert {alert_id} resolved successfully")
            
            return {
                'id': str(alert.id),
                'is_resolved': True,
                'resolved_at': alert.resolved_at.isoformat(),
                'resolved_by': str(alert.resolved_by),
                'resolution_notes': alert.resolution_notes
            }
            
        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to resolve alert: {str(e)}")
            raise DatabaseOperationError(f"Alert resolution failed: {str(e)}")
    
    # ==================== Statistics & Reports ====================
    
    async def get_branch_statistics(self, branch_id: UUID) -> Dict[str, Any]:
        """
        Get comprehensive branch statistics
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            Branch statistics
        """
        branch = await self.repo.get_branch_by_id(branch_id, include_balances=True)
        if not branch:
            raise ResourceNotFoundError("Branch", branch_id)
        
        stats = await self.repo.get_branch_statistics(branch_id)
        
        # Add branch details
        stats['branch'] = {
            'code': branch.code,
            'name_en': branch.name_en,
            'name_ar': branch.name_ar,
            'region': branch.region.value,
            'is_main_branch': branch.is_main_branch,
            'is_active': branch.is_active
        }
        
        return stats
    
    async def get_balance_history(
        self,
        branch_id: UUID,
        currency_id: Optional[UUID] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get balance history with filtering
        
        Args:
            branch_id: Branch UUID
            currency_id: Currency UUID (optional)
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum records
            
        Returns:
            List of balance history records
        """
        history = await self.repo.get_balance_history(
            branch_id,
            currency_id,
            start_date,
            end_date,
            limit
        )
        
        return [
            {
                'id': str(record.id),
                'change_type': record.change_type.value,
                'amount': float(record.amount),
                'balance_before': float(record.balance_before),
                'balance_after': float(record.balance_after),
                'reference_id': str(record.reference_id) if record.reference_id else None,
                'reference_type': record.reference_type,
                'performed_at': record.performed_at.isoformat(),
                'notes': record.notes
            }
            for record in history
        ]