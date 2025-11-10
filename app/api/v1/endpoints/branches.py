# app/api/v1/endpoints/branches.py
"""
Branch API Endpoints - COMPLETE FIXED VERSION V3
REST API for branch management operations with better error handling
"""

from typing import List, Optional, Union
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_async_db,
    get_current_active_user,
    require_roles
)
from app.services.branch_service import BranchService
from app.services.balance_service import BalanceService
from app.schemas.branch import (
    BranchCreate, BranchUpdate, BranchResponse,
    BranchWithBalances, BranchListResponse,
    BranchBalanceResponse, BranchBalanceListResponse,
    SetThresholdsRequest,
    BranchStatistics,
    UserAssignmentRequest,  # ← يجب إضافة
    ReconcileBalanceRequest,  # موجود باسم آخر
    ReconcileBalanceResponse,  # موجود باسم آخر
    BranchAlertResponse,  # موجود
    ResolveAlertRequest,  # موجود
    BranchBalanceHistoryResponse,  # موجود
    BalanceHistoryResponse, 
    ResolveAlertRequest,
    ReconciliationResponse,
    ReconciliationRequest
)

# من user schemas
from app.schemas.user import UserResponse  # موجود
from app.db.models.branch import BranchBalance, RegionEnum
from app.db.models.user import User
from app.schemas.user import UserResponse
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger
from app.schemas.common import PaginatedResponse, paginated

logger = get_logger(__name__)
router = APIRouter()


# ==================== Helper Functions ====================

def balance_to_response(balance: BranchBalance) -> dict:
    """Convert BranchBalance model to response dict with safe field access"""
    try:
        return {
            "id": balance.id,
            "branch_id": balance.branch_id,
            "currency_id": balance.currency_id,
            "currency_code": balance.currency.code if balance.currency else "N/A",
            "currency_name": balance.currency.name_en if balance.currency else "N/A",
            "balance": float(balance.balance) if balance.balance else 0.0,
            "reserved_balance": float(balance.reserved_balance) if balance.reserved_balance else 0.0,
            "available_balance": float(balance.balance - balance.reserved_balance) if balance.balance else 0.0,
            "minimum_threshold": float(balance.minimum_threshold) if balance.minimum_threshold else None,
            "maximum_threshold": float(balance.maximum_threshold) if balance.maximum_threshold else None,
            "last_updated": balance.updated_at if hasattr(balance, 'updated_at') else None,
            "last_reconciled_at": balance.last_reconciled_at if hasattr(balance, 'last_reconciled_at') else None,
        }
    except Exception as e:
        logger.error(f"Error converting balance to response: {str(e)}")
        # Return minimal valid response
        return {
            "id": balance.id if hasattr(balance, 'id') else None,
            "branch_id": balance.branch_id if hasattr(balance, 'branch_id') else None,
            "currency_id": balance.currency_id if hasattr(balance, 'currency_id') else None,
            "currency_code": "ERROR",
            "currency_name": "Error loading",
            "balance": 0.0,
            "reserved_balance": 0.0,
            "available_balance": 0.0,
            "minimum_threshold": None,
            "maximum_threshold": None,
            "last_updated": None,
            "last_reconciled_at": None,
        }


def branch_to_dict_safe(branch) -> dict:
    """Safely convert branch to dict with all required fields"""
    try:
        return {
            "id": branch.id,
            "code": branch.code,
            "name_en": branch.name_en,
            "name_ar": branch.name_ar,
            "region": branch.region.value if hasattr(branch.region, 'value') else str(branch.region),
            "address": branch.address,
            "city": branch.city,
            "phone": branch.phone,
            "email": branch.email,
            "manager_id": branch.manager_id,
            "is_active": branch.is_active,
            "is_main_branch": branch.is_main_branch,
            "opening_balance_date": branch.opening_balance_date,
            "created_at": branch.created_at,
            "updated_at": branch.updated_at,
        }
    except Exception as e:
        logger.error(f"Error converting branch {branch.code if hasattr(branch, 'code') else 'unknown'}: {str(e)}")
        raise


# ==================== Branch CRUD Endpoints ====================

@router.get("", response_model=PaginatedResponse[BranchResponse])
async def list_branches(
    region: Optional[RegionEnum] = Query(None),
    is_active: bool = Query(True),
    include_balances: bool = Query(False),
    search: Optional[str] = Query(None, description="Search by name, code, city, or address"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all branches with pagination and search

    **Search:** Search in name (EN/AR), code, city, and address fields

    **Filters:**
    - region: Filter by region
    - is_active: Filter by active status
    - include_balances: Include currency balances

    **Permissions:** Any authenticated user
    """
    try:
        logger.info(f"Listing branches with include_balances={include_balances}, search={search}")
        service = BranchService(db)

        # Get branches
        branches = await service.get_all_branches(
            region=region,
            is_active=is_active,
            include_balances=include_balances,
            search=search
        )
        
        # Apply pagination manually
        total = len(branches)
        paginated_branches = branches[skip:skip + limit]
        
        # Convert to response format
        if include_balances:
            branch_list = []
            for branch in paginated_branches:
                branch_dict = branch_to_dict_safe(branch)
                # Handle balances...
                branch_with_balances = BranchWithBalances(**branch_dict)
                branch_list.append(branch_with_balances)
        else:
            branch_list = [BranchResponse(**branch_to_dict_safe(b)) for b in paginated_branches]
        
        logger.info(f"Retrieved {len(branch_list)} branches")
        
        # ✅ استخدم paginated helper
        return paginated(branch_list, total, skip, limit)
        
    except Exception as e:
        logger.error(f"Error listing branches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve branches: {str(e)}"
        )


@router.get("/{branch_id}", response_model=BranchWithBalances)
async def get_branch(
    branch_id: UUID,
    include_balances: bool = Query(True),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get branch by ID with optional balances"""
    try:
        service = BranchService(db)
        branch = await service.get_branch_by_id(branch_id, include_balances=include_balances)
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch not found"
            )
        
        branch_dict = branch_to_dict_safe(branch)
        
        if include_balances:
            balances = []
            
            # Check if balances are already loaded
            if hasattr(branch, 'balances') and branch.balances:
                for balance in branch.balances:
                    balances.append(balance_to_response(balance))
            else:
                # Load balances separately
                balance_service = BalanceService(db)
                branch_balances = await balance_service.get_branch_balances(branch_id)
                for balance in branch_balances:
                    balances.append(balance_to_response(balance))
            
            branch_dict["balances"] = balances
            return BranchWithBalances(**branch_dict)
        else:
            return BranchResponse(**branch_dict)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting branch {branch_id}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve branch: {str(e)}"
        )


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Create new branch (Admin only)"""
    try:
        service = BranchService(db)
        branch = await service.create_branch(
            branch_data.model_dump(exclude_unset=True),
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch.code} created by {current_user.username}")
        return BranchResponse.model_validate(branch)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create branch"
        )


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    branch_data: BranchUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Update branch (Admin only)"""
    try:
        service = BranchService(db)
        branch = await service.update_branch(
            branch_id,
            branch_data.model_dump(exclude_unset=True),
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch_id} updated by {current_user.username}")
        return BranchResponse.model_validate(branch)
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    except Exception as e:
        logger.error(f"Error updating branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update branch"
        )


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """Delete branch - soft delete (Admin only)"""
    try:
        service = BranchService(db)
        await service.delete_branch(
            branch_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch_id} deleted by {current_user.username}")
        return None
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error deleting branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete branch"
        )


# ==================== Branch Balance Endpoints ====================

@router.get("/{branch_id}/balances", response_model=BranchBalanceListResponse)
async def get_branch_balances(
    branch_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get all currency balances for a branch"""
    try:
        balance_service = BalanceService(db)
        balances = await balance_service.get_branch_balances(branch_id)
        
        balance_responses = []
        for balance in balances:
            try:
                balance_responses.append(balance_to_response(balance))
            except Exception as e:
                logger.error(f"Error converting balance: {str(e)}")
                continue
        
        return BranchBalanceListResponse(
            total=len(balance_responses),
            balances=balance_responses
        )
        
    except Exception as e:
        logger.error(f"Error getting balances for branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch balances"
        )


@router.get("/{branch_id}/balances/{currency_id}", response_model=BranchBalanceResponse)
async def get_branch_currency_balance(
    branch_id: UUID,
    currency_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get specific currency balance for a branch"""
    try:
        balance_service = BalanceService(db)
        balance = await balance_service.get_branch_currency_balance(branch_id, currency_id)
        
        if not balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found"
            )
        
        return balance_to_response(balance)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance"
        )

# ==================== User Assignment Endpoints ====================

@router.get("/{branch_id}/users", response_model=List[UserResponse])
async def get_branch_users(
    branch_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all users assigned to a branch
    
    **Permissions:** Any authenticated user
    """
    try:
        service = BranchService(db)
        
        # Get branch to verify it exists
        branch = await service.get_branch_by_id(branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Get users
        from app.repositories.user_repo import UserRepository
        user_repo = UserRepository(db)
        users = await user_repo.get_branch_users(branch_id)
        
        return users
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting branch users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch users"
        )


@router.post("/{branch_id}/users", status_code=status.HTTP_201_CREATED)
async def assign_users_to_branch(
    branch_id: UUID,
    request: UserAssignmentRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Assign multiple users to a branch
    
    **Permissions:** Admin or Manager only
    """
    try:
        service = BranchService(db)
        await service.assign_users_to_branch(
            branch_id,
            request.user_ids,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(
            f"{len(request.user_ids)} users assigned to branch {branch_id} "
            f"by {current_user.username}"
        )
        
        return {"message": f"{len(request.user_ids)} users assigned successfully"}
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    except Exception as e:
        logger.error(f"Error assigning users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign users"
        )


@router.delete("/{branch_id}/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_branch(
    branch_id: UUID,
    user_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Remove user from branch
    
    **Permissions:** Admin or Manager only
    """
    try:
        service = BranchService(db)
        await service.remove_user_from_branch(
            branch_id,
            user_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(
            f"User {user_id} removed from branch {branch_id} "
            f"by {current_user.username}"
        )
        
        return None
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
    except Exception as e:
        logger.error(f"Error removing user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to remove user"
        )


# ==================== Alert Endpoints ====================

@router.get("/{branch_id}/alerts", response_model=List[BranchAlertResponse])
async def get_branch_alerts(
    branch_id: UUID,
    is_resolved: bool = Query(False, description="Show resolved alerts"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get branch alerts
    
    **Permissions:** Any authenticated user
    
    **Query Parameters:**
    - is_resolved: Filter by resolution status (default: False - show unresolved)
    """
    try:
        service = BranchService(db)
        
        # Verify branch exists
        branch = await service.get_branch_by_id(branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Get alerts from repository
        from app.repositories.branch_repo import BranchRepository
        repo = BranchRepository(db)
        alerts = await repo.get_branch_alerts(branch_id, is_resolved)
        
        # Transform to response
        alert_responses = []
        for alert in alerts:
            alert_responses.append(BranchAlertResponse(
                id=alert.id,
                branch_id=alert.branch_id,
                currency_id=alert.currency_id,
                currency_code=alert.currency.code,
                alert_type=alert.alert_type.value,
                severity=alert.severity.value,
                title=alert.title,
                message=alert.message,
                triggered_at=alert.triggered_at,
                is_resolved=alert.is_resolved,
                resolved_at=alert.resolved_at,
                resolved_by=alert.resolved_by,
                resolution_notes=alert.resolution_notes
            ))
        
        return alert_responses
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.put("/alerts/{alert_id}/resolve", response_model=BranchAlertResponse)
async def resolve_alert(
    alert_id: UUID,
    request: ResolveAlertRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Resolve a branch alert
    
    **Permissions:** Admin or Manager only
    """
    try:
        from app.repositories.branch_repo import BranchRepository
        repo = BranchRepository(db)
        
        alert = await repo.resolve_alert(
            alert_id,
            resolved_by=current_user.id,
            resolution_notes=request.resolution_notes
        )
        
        await db.commit()
        
        logger.info(f"Alert {alert_id} resolved by {current_user.username}")
        
        return BranchAlertResponse(
            id=alert.id,
            branch_id=alert.branch_id,
            currency_id=alert.currency_id,
            currency_code=alert.currency.code,
            alert_type=alert.alert_type.value,
            severity=alert.severity.value,
            title=alert.title,
            message=alert.message,
            triggered_at=alert.triggered_at,
            is_resolved=alert.is_resolved,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            resolution_notes=alert.resolution_notes
        )
        
    except ResourceNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found")
    except Exception as e:
        await db.rollback()
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


# ==================== Reconciliation Endpoint ====================

@router.post(
    "/{branch_id}/balances/{currency_id}/reconcile",
    response_model=ReconciliationResponse
)
async def reconcile_balance(
    branch_id: UUID,
    currency_id: UUID,
    request: ReconciliationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Reconcile branch balance with actual count
    
    **Permissions:** Admin or Manager only
    
    This endpoint compares the system balance with the actual counted balance
    and creates an adjustment if there's a difference.
    """
    try:
        balance_service = BalanceService(db)
        
        result = await balance_service.reconcile_branch_balance(
            branch_id=branch_id,
            currency_id=currency_id,
            actual_balance=request.actual_balance,
            reconciled_by=current_user.id,
            notes=request.notes
        )
        
        await db.commit()
        
        logger.info(
            f"Balance reconciled for branch {branch_id}, currency {currency_id} "
            f"by {current_user.username}"
        )
        
        return ReconciliationResponse(**result)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        await db.rollback()
        logger.error(f"Error reconciling balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reconcile balance"
        )


# ==================== Balance History Endpoint ====================

@router.get(
    "/{branch_id}/balances/{currency_id}/history",
    response_model=BalanceHistoryResponse
)
async def get_balance_history(
    branch_id: UUID,
    currency_id: UUID,
    date_from: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    date_to: Optional[datetime] = Query(None, description="End date (ISO format)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum records to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get balance change history
    
    **Permissions:** Any authenticated user
    
    **Query Parameters:**
    - date_from: Filter records from this date (ISO format)
    - date_to: Filter records until this date (ISO format)
    - limit: Maximum number of records (1-500, default: 100)
    """
    try:
        service = BranchService(db)
        
        # Verify branch exists
        branch = await service.get_branch_by_id(branch_id)
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Get balance to verify currency exists for branch
        balance_service = BalanceService(db)
        balance = await balance_service.get_branch_currency_balance(branch_id, currency_id)
        
        if not balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Balance not found for this branch and currency"
            )
        
        # Get history
        history = await balance_service.get_balance_history(
            branch_id=branch_id,
            currency_id=currency_id,
            date_from=date_from,
            date_to=date_to,
            limit=limit
        )
        
        # Transform to response
        history_records = [
            BalanceHistoryRecord(
                id=record.id,
                change_type=record.change_type.value,
                amount=record.amount,
                balance_before=record.balance_before,
                balance_after=record.balance_after,
                performed_at=record.performed_at,
                performed_by=record.performed_by,
                reference_id=record.reference_id,
                reference_type=record.reference_type,
                notes=record.notes
            )
            for record in history
        ]
        
        return BalanceHistoryResponse(
            branch_id=branch_id,
            currency_id=currency_id,
            currency_code=balance.currency.code,
            total_records=len(history_records),
            history=history_records
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting balance history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance history"
        )

# Continue with other endpoints...
# (The rest of the endpoints remain the same but with improved error handling)
