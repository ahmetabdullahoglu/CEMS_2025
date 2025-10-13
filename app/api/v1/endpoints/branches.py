# app/api/v1/endpoints/branches.py
"""
Branch API Endpoints - FIXED VERSION
REST API for branch management operations
"""

from typing import List, Optional
from uuid import UUID
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
    BranchStatistics
)
from app.db.models.branch import BranchBalance, RegionEnum
from app.db.models.user import User
from app.core.exceptions import (
    ResourceNotFoundError, ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


# ==================== Helper Functions ====================

def balance_to_response(balance: BranchBalance) -> dict:
    """Convert BranchBalance model to response dict"""
    return {
        "id": balance.id,
        "branch_id": balance.branch_id,
        "currency_id": balance.currency_id,
        "currency_code": balance.currency.code,
        "currency_name": balance.currency.name_en,
        "balance": balance.balance,
        "reserved_balance": balance.reserved_balance,
        "available_balance": balance.balance - balance.reserved_balance,
        "minimum_threshold": balance.minimum_threshold,
        "maximum_threshold": balance.maximum_threshold,
        "last_updated": balance.updated_at,
        "last_reconciled_at": balance.last_reconciled_at,
    }


# ==================== Branch CRUD Endpoints ====================

@router.get("", response_model=BranchListResponse)
async def list_branches(
    region: Optional[RegionEnum] = Query(None),
    is_active: bool = Query(True),
    include_balances: bool = Query(False),
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
        
        # ✅ FIX: Pass include_balances to service
        branches = await service.get_all_branches(
            region=region,
            is_active=is_active,
            include_balances=include_balances  # ← هذا السطر كان ناقص!
        )
        
        if include_balances:
            # Transform branches with balances
            balance_service = BalanceService(db)
            branch_list = []
            
            for branch in branches:
                balances = await balance_service.get_branch_balances(branch.id)
                balance_responses = [balance_to_response(b) for b in balances]
                
                branch_data = BranchWithBalances(
                    **BranchResponse.model_validate(branch).model_dump(),
                    balances=balance_responses
                )
                branch_list.append(branch_data)
            
            return BranchListResponse(total=len(branch_list), branches=branch_list)
        else:
            return BranchListResponse(
                total=len(branches),
                branches=[BranchResponse.model_validate(b) for b in branches]
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
    include_balances: bool = Query(True),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get branch by ID"""
    try:
        service = BranchService(db)
        branch = await service.get_branch_by_id(branch_id)
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Branch not found"
            )
        
        if include_balances:
            balance_service = BalanceService(db)
            balances = await balance_service.get_branch_balances(branch_id)
            balance_responses = [balance_to_response(b) for b in balances]
            
            return BranchWithBalances(
                **BranchResponse.model_validate(branch).model_dump(),
                balances=balance_responses
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
            branch_data.model_dump(),
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Branch {branch.code} created by {current_user.username}")
        return BranchResponse.model_validate(branch)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except BusinessRuleViolationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """Update branch (Admin/Manager only)"""
    try:
        service = BranchService(db)
        branch = await service.update_branch(
            branch_id,
            branch_data.model_dump(exclude_unset=True),
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        if not branch:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Branch not found")
        
        logger.info(f"Branch {branch_id} updated by {current_user.username}")
        return BranchResponse.model_validate(branch)
        
    except HTTPException:
        raise
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
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
        
        balance_responses = [balance_to_response(b) for b in balances]
        
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


@router.put("/{branch_id}/balances/{currency_id}/thresholds", response_model=BranchBalanceResponse)
async def set_balance_thresholds(
    branch_id: UUID,
    currency_id: UUID,
    thresholds: SetThresholdsRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """Set balance thresholds (Admin/Manager only)"""
    try:
        balance_service = BalanceService(db)
        balance = await balance_service.set_thresholds(
            branch_id, currency_id,
            thresholds.minimum_threshold,
            thresholds.maximum_threshold,
            current_user={"id": current_user.id, "username": current_user.username}
        )
        
        logger.info(f"Thresholds updated for branch {branch_id}, currency {currency_id}")
        return balance_to_response(balance)
        
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error setting thresholds: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set thresholds"
        )


# ==================== Statistics Endpoint ====================

@router.get("/{branch_id}/statistics", response_model=BranchStatistics)
async def get_branch_statistics(
    branch_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get branch statistics with balances summary"""
    try:
        # Get branch
        service = BranchService(db)
        branch = await service.get_branch_by_id(branch_id)
        
        if not branch:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Branch not found"
            )
        
        # Get balances
        balance_service = BalanceService(db)
        balances = await balance_service.get_branch_balances(branch_id)
        
        # Transform to summary format
        balance_summaries = []
        for balance in balances:
            balance_summaries.append({
                "currency_code": balance.currency.code,
                "currency_name": balance.currency.name_en,
                "balance": balance.balance,
                "reserved": balance.reserved_balance,
                "available": balance.balance - balance.reserved_balance,
                "minimum_threshold": balance.minimum_threshold,
                "maximum_threshold": balance.maximum_threshold,
                "is_below_minimum": balance.minimum_threshold and balance.balance < balance.minimum_threshold,
                "is_above_maximum": balance.maximum_threshold and balance.balance > balance.maximum_threshold,
                "last_updated": balance.updated_at,
                "last_reconciled": balance.last_reconciled_at,
            })
        
        # Count active alerts (simplified - you can enhance this)
        active_alerts = sum(1 for b in balance_summaries if b["is_below_minimum"] or b["is_above_maximum"])
        
        return BranchStatistics(
            branch_id=branch.id,
            branch_code=branch.code,
            branch_name=branch.name_en,
            region=branch.region.value,
            is_main_branch=branch.is_main_branch,
            total_currencies=len(balances),
            balances=balance_summaries,
            active_alerts=active_alerts
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting statistics for branch {branch_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve branch statistics"
        )