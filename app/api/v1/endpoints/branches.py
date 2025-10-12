# app/api/v1/endpoints/branches.py
"""
Branch API Endpoints
REST API for branch management operations
"""

from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_async_db,
    get_current_user,
    get_current_active_user,
    require_roles
)
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
from app.db.models.user import User
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== Branch CRUD Endpoints ====================

@router.get("", response_model=BranchListResponse)
async def list_branches(
    region: Optional[RegionEnum] = Query(None, description="Filter by region"),
    is_active: bool = Query(True, description="Filter by active status"),
    include_balances: bool = Query(False, description="Include balance information"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
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
        service = BranchService(db)
        branches = await service.get_all_branches(
            region=region,
            is_active=is_active
        )
        
        if include_balances:
            # Get balances for each branch
            branch_list = []
            for branch in branches:
                balance_service = BalanceService(db)
                balances = await balance_service.get_branch_balances(branch.id)
                branch_data = BranchWithBalances(
                    **BranchResponse.model_validate(branch).model_dump(),
                    balances=balances
                )
                branch_list.append(branch_data)
            
            return BranchListResponse(
                success=True,
                data=branch_list,
                total=len(branch_list)
            )
        else:
            return BranchListResponse(
                success=True,
                data=[BranchResponse.model_validate(b) for b in branches],
                total=len(branches)
            )
            
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
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get branch by ID
    
    **Permissions:** Any authenticated user
    """
    try:
        service = BranchService(db)
        branch = await service.get_branch_by_id(branch_id)
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch {branch_id} not found"
            )
        
        if include_balances:
            balance_service = BalanceService(db)
            balances = await balance_service.get_branch_balances(branch_id)
            
            return BranchWithBalances(
                **BranchResponse.model_validate(branch).model_dump(),
                balances=balances
            )
        else:
            return BranchResponse.model_validate(branch)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch"
        )


@router.post(
    "",
    response_model=BranchResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_branch(
    branch_data: BranchCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Create new branch
    
    **Permissions:** Admin or Manager only
    """
    try:
        service = BranchService(db)
        branch = await service.create_branch(
            branch_data,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch.code} created by user {current_user.username}")
        return BranchResponse.model_validate(branch)
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
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
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Update branch
    
    **Permissions:** Admin or Manager only
    """
    try:
        service = BranchService(db)
        branch = await service.update_branch(
            branch_id,
            update_data,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch.code} updated by user {current_user.username}")
        return BranchResponse.model_validate(branch)
        
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
    """
    Delete branch (soft delete)
    
    **Permissions:** Admin only
    """
    try:
        service = BranchService(db)
        await service.delete_branch(
            branch_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch_id} deleted by user {current_user.username}")
        return None
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
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
    """
    Get all currency balances for a branch
    
    **Permissions:** Any authenticated user
    """
    try:
        balance_service = BalanceService(db)
        balances = await balance_service.get_branch_balances(branch_id)
        
        return BranchBalanceListResponse(
            success=True,
            data=balances,
            total=len(balances)
        )
        
    except Exception as e:
        logger.error(f"Error getting balances for branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch balances"
        )


@router.get(
    "/{branch_id}/balances/{currency_id}",
    response_model=BranchBalanceResponse
)
async def get_branch_currency_balance(
    branch_id: UUID,
    currency_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get specific currency balance for a branch
    
    **Permissions:** Any authenticated user
    """
    try:
        balance_service = BalanceService(db)
        balance = await balance_service.get_branch_currency_balance(
            branch_id,
            currency_id
        )
        
        if not balance:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Balance not found for branch {branch_id} and currency {currency_id}"
            )
        
        return BranchBalanceResponse.model_validate(balance)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Error getting balance for branch {branch_id}, "
            f"currency {currency_id}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve balance"
        )


@router.post("/{branch_id}/balances/thresholds")
async def set_balance_thresholds(
    branch_id: UUID,
    threshold_data: SetThresholdsRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Set minimum and maximum thresholds for a currency balance
    
    **Permissions:** Admin or Manager only
    """
    try:
        balance_service = BalanceService(db)
        await balance_service.set_thresholds(
            branch_id=branch_id,
            currency_id=threshold_data.currency_id,
            minimum_threshold=threshold_data.minimum_threshold,
            maximum_threshold=threshold_data.maximum_threshold,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        return {
            "success": True,
            "message": "Thresholds updated successfully"
        }
        
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


# ==================== Branch Statistics ====================

@router.get("/{branch_id}/statistics", response_model=BranchStatistics)
async def get_branch_statistics(
    branch_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get branch statistics
    
    **Permissions:** Any authenticated user
    """
    try:
        service = BranchService(db)
        stats = await service.get_branch_statistics(branch_id)
        
        return stats
        
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting statistics for branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch statistics"
        )


# ==================== Branch Manager Assignment ====================

@router.post("/{branch_id}/assign-manager")
async def assign_manager(
    branch_id: UUID,
    manager_data: AssignManagerRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Assign or change branch manager
    
    **Permissions:** Admin only
    """
    try:
        service = BranchService(db)
        await service.assign_manager(
            branch_id=branch_id,
            manager_id=manager_data.manager_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        return {
            "success": True,
            "message": "Manager assigned successfully"
        }
        
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
        logger.error(f"Error assigning manager to branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to assign manager"
        )


# ==================== Health Check ====================

@router.get("/health/ping")
async def branch_health_check():
    """Health check endpoint for branch service"""
    return {
        "success": True,
        "service": "branch",
        "status": "healthy"
    }