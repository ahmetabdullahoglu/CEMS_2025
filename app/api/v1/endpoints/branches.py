"""
Branch API Endpoints
REST API for branch management operations
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db.base import get_db
from app.services.branch_service import BranchService
from app.services.balance_service import BalanceService
from app.schemas.branch import (
    BranchCreate, BranchUpdate, BranchResponse,
    BranchWithBalances, BranchListResponse,
    BranchBalanceResponse, BranchBalanceListResponse,
    SetThresholdsRequest, BalanceHistoryFilter,
    BranchBalanceHistoryResponse, BranchAlertResponse,
    BranchAlertListResponse, ResolveAlertRequest,
    ReconcileBalanceRequest, ReconcileBalanceResponse,
    BranchStatistics, AssignManagerRequest
)
from app.db.models.branch import RegionEnum, AlertSeverity
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/branches", tags=["branches"])


# ==================== Dependency ====================

def get_branch_service(db: Session = Depends(get_db)) -> BranchService:
    """Get branch service instance"""
    return BranchService(db)


def get_balance_service(db: Session = Depends(get_db)) -> BalanceService:
    """Get balance service instance"""
    return BalanceService(db)


# TODO: Replace with actual auth dependency
def get_current_user():
    """Mock current user - replace with actual auth"""
    return {
        'id': UUID('00000000-0000-0000-0000-000000000001'),
        'username': 'admin',
        'roles': ['admin']
    }


# ==================== Branch CRUD Endpoints ====================

@router.get("", response_model=BranchListResponse)
async def list_branches(
    region: Optional[RegionEnum] = Query(None, description="Filter by region"),
    is_active: bool = Query(True, description="Filter by active status"),
    include_balances: bool = Query(False, description="Include balance information"),
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    List all branches
    
    **Permissions:** Any authenticated user
    
    **Query Parameters:**
    - region: Filter by specific region
    - is_active: Show only active branches (default: true)
    - include_balances: Include balance information in response
    """
    try:
        branches = service.get_all_branches(region, is_active, include_balances)
        
        return {
            'total': len(branches),
            'branches': branches
        }
        
    except Exception as e:
        logger.error(f"Error listing branches: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branches"
        )


@router.get("/{branch_id}", response_model=BranchWithBalances)
async def get_branch(
    branch_id: UUID,
    include_balances: bool = Query(True, description="Include balance information"),
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get branch details by ID
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    """
    try:
        branch = service.get_branch(branch_id, include_balances)
        return branch
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch"
        )


@router.post("", response_model=BranchResponse, status_code=status.HTTP_201_CREATED)
async def create_branch(
    branch_data: BranchCreate,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Create new branch
    
    **Permissions:** Admin only
    
    **Request Body:** Branch creation data
    """
    # TODO: Check if user is admin
    
    try:
        branch = service.create_branch(
            branch_data.model_dump(),
            current_user
        )
        return branch
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create branch"
        )


@router.put("/{branch_id}", response_model=BranchResponse)
async def update_branch(
    branch_id: UUID,
    update_data: BranchUpdate,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Update branch
    
    **Permissions:** Admin or Branch Manager
    
    **Path Parameters:**
    - branch_id: Branch UUID
    
    **Request Body:** Branch update data
    """
    # TODO: Check if user is admin or branch manager
    
    try:
        branch = service.update_branch(
            branch_id,
            update_data.model_dump(exclude_unset=True),
            current_user
        )
        return branch
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update branch"
        )


@router.delete("/{branch_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_branch(
    branch_id: UUID,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Delete branch (soft delete)
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - branch_id: Branch UUID
    """
    # TODO: Check if user is admin
    
    try:
        service.delete_branch(branch_id, current_user)
        return None
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting branch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete branch"
        )


# ==================== Balance Endpoints ====================

@router.get("/{branch_id}/balances", response_model=dict)
async def get_branch_balances(
    branch_id: UUID,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get all balances for a branch
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    """
    try:
        balances = service.get_all_balances(branch_id)
        return balances
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting balances: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balances"
        )


@router.get("/{branch_id}/balances/{currency_id}", response_model=dict)
async def get_branch_balance_by_currency(
    branch_id: UUID,
    currency_id: UUID,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get branch balance for specific currency
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    - currency_id: Currency UUID
    """
    try:
        balance = service.get_branch_balance(branch_id, currency_id)
        return balance
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance"
        )


@router.put("/{branch_id}/balances/{currency_id}/thresholds", response_model=dict)
async def set_balance_thresholds(
    branch_id: UUID,
    currency_id: UUID,
    threshold_data: SetThresholdsRequest,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Set balance thresholds for alerts
    
    **Permissions:** Admin or Branch Manager
    
    **Path Parameters:**
    - branch_id: Branch UUID
    - currency_id: Currency UUID
    
    **Request Body:** Threshold values
    """
    # TODO: Check if user is admin or branch manager
    
    try:
        balance = service.set_balance_thresholds(
            branch_id,
            currency_id,
            threshold_data.minimum_threshold,
            threshold_data.maximum_threshold,
            current_user
        )
        return balance
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error setting thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set thresholds"
        )


# ==================== Balance History Endpoints ====================

@router.get("/{branch_id}/balance-history", response_model=List[dict])
async def get_balance_history(
    branch_id: UUID,
    filters: BalanceHistoryFilter = Depends(),
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get balance history for a branch
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    
    **Query Parameters:**
    - currency_id: Filter by currency
    - start_date: Filter by start date
    - end_date: Filter by end date
    - limit: Maximum records to return (default: 100)
    """
    try:
        history = service.get_balance_history(
            branch_id,
            filters.currency_id,
            filters.start_date,
            filters.end_date,
            filters.limit
        )
        return history
        
    except Exception as e:
        logger.error(f"Error getting balance history: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance history"
        )


# ==================== Reconciliation Endpoints ====================

@router.post("/{branch_id}/balances/{currency_id}/reconcile", response_model=dict)
async def reconcile_balance(
    branch_id: UUID,
    currency_id: UUID,
    reconcile_data: ReconcileBalanceRequest,
    balance_service: BalanceService = Depends(get_balance_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Reconcile branch balance
    
    **Permissions:** Admin or Branch Manager
    
    **Path Parameters:**
    - branch_id: Branch UUID
    - currency_id: Currency UUID
    
    **Request Body:** Expected balance and notes
    """
    # TODO: Check if user is admin or branch manager
    
    try:
        result = balance_service.reconcile_branch_balance(
            branch_id,
            currency_id,
            reconcile_data.expected_balance,
            current_user['id'],
            reconcile_data.notes
        )
        return result
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error reconciling balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reconcile balance"
        )


# ==================== Alert Endpoints ====================

@router.get("/{branch_id}/alerts", response_model=List[dict])
async def get_branch_alerts(
    branch_id: UUID,
    is_resolved: Optional[bool] = Query(None, description="Filter by resolution status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get branch alerts
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    
    **Query Parameters:**
    - is_resolved: Filter by resolution status
    - severity: Filter by severity level
    """
    try:
        alerts = service.get_alerts(branch_id, is_resolved, severity)
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )


@router.put("/alerts/{alert_id}/resolve", response_model=dict)
async def resolve_alert(
    alert_id: UUID,
    resolve_data: ResolveAlertRequest,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Resolve a branch alert
    
    **Permissions:** Admin or Branch Manager
    
    **Path Parameters:**
    - alert_id: Alert UUID
    
    **Request Body:** Resolution notes
    """
    # TODO: Check if user is admin or branch manager
    
    try:
        alert = service.resolve_alert(
            alert_id,
            resolve_data.resolution_notes,
            current_user
        )
        return alert
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error resolving alert: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to resolve alert"
        )


# ==================== Management Endpoints ====================

@router.post("/{branch_id}/assign-manager", response_model=BranchResponse)
async def assign_manager(
    branch_id: UUID,
    assign_data: AssignManagerRequest,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Assign manager to branch
    
    **Permissions:** Admin only
    
    **Path Parameters:**
    - branch_id: Branch UUID
    
    **Request Body:** User ID to assign as manager
    """
    # TODO: Check if user is admin
    
    try:
        branch = service.assign_manager(
            branch_id,
            assign_data.user_id,
            current_user
        )
        return branch
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error assigning manager: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign manager"
        )


# ==================== Statistics Endpoints ====================

@router.get("/{branch_id}/statistics", response_model=dict)
async def get_branch_statistics(
    branch_id: UUID,
    service: BranchService = Depends(get_branch_service),
    current_user: dict = Depends(get_current_user)
):
    """
    Get comprehensive branch statistics
    
    **Permissions:** Any authenticated user
    
    **Path Parameters:**
    - branch_id: Branch UUID
    """
    try:
        stats = service.get_branch_statistics(branch_id)
        return stats
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting statistics: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve statistics"
        )