"""
Vault API Endpoints
===================
Complete vault management endpoints:
- Vault details and listing
- Vault balance management and updates
- Vault-to-vault transfers
- Vault-to-branch transfers
- Branch-to-vault transfers
- Transfer approval workflow
- Balance reconciliation
- Vault statistics and reports

Features:
- Real-time balance tracking
- Multi-currency support
- Transfer approval for large amounts
- Complete audit trail
- Reconciliation support
- Transfer status tracking

Business Rules:
- Only ONE main vault allowed
- Transfers over threshold require approval
- All transfers are atomic
- Balance cannot go negative
- Complete history maintained
"""
from typing import List, Optional
from datetime import datetime, timedelta
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_async_db, get_current_user, require_permissions
from app.db.models.user import User
from app.db.models.vault import VaultTransferStatus, VaultTransferType
from app.services.currency_service import CurrencyService
from app.services.vault_service import VaultService
from app.schemas.vault import (
    VaultCreate, VaultUpdate, VaultResponse, VaultListResponse,
    VaultBalanceResponse, VaultBalanceUpdate,
    VaultToVaultTransferCreate, VaultToBranchTransferCreate,
    BranchToVaultTransferCreate, TransferApproval,
    VaultTransferResponse, VaultTransferListResponse, TransferQuery,
    VaultReconciliationRequest, VaultReconciliationReport,
    VaultStatistics, VaultTransferSummary
)
from app.schemas.common import PaginatedResponse, paginated

router = APIRouter(tags=["vault"])


# ==================== VAULT MANAGEMENT ====================

@router.get(
    "",
    response_model=VaultResponse,
    summary="Get main vault details"
)
async def get_main_vault(
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get main vault details and balances

    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)
    vault = await vault_service.get_main_vault()

    # Load balances
    balances = await vault_service.get_vault_balance(vault.id)
    
    return VaultResponse(
        id=vault.id,
        vault_code=vault.vault_code,
        name=vault.name,
        vault_type=vault.vault_type,
        branch_id=vault.branch_id,
        is_active=vault.is_active,
        description=vault.description,
        location=vault.location,
        balances=[
            {
                'currency_code': b.currency.code,
                'currency_name': b.currency.name_en,
                'balance': b.balance,
                'last_updated': b.last_updated
            }
            for b in balances
        ],
        created_at=vault.created_at,
        updated_at=vault.updated_at
    )


@router.get(
    "/all",
    response_model=PaginatedResponse[VaultResponse],
    summary="List all vaults"
)
async def list_all_vaults(
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    is_active: Optional[bool] = Query(True, description="Filter by active status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum records to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all vaults with pagination and optional filters

    **Filters:**
    - branch_id: Filter vaults by branch
    - is_active: Show only active/inactive vaults

    **Permissions:** Any authenticated user

    **Returns:** Paginated list of vaults with metadata
    """
    vault_service = VaultService(db)

    # Get vaults list with total count
    vaults, total = await vault_service.list_vaults(
        branch_id=branch_id,
        is_active=is_active,
        skip=skip,
        limit=limit
    )

    # Convert vaults to dict format with properly formatted balances
    vaults_data = []
    for vault in vaults:
        vault_dict = {
            "id": vault.id,
            "vault_code": vault.vault_code,
            "name": vault.name,
            "vault_type": vault.vault_type.value if hasattr(vault.vault_type, 'value') else vault.vault_type,
            "branch_id": vault.branch_id,
            "is_active": vault.is_active,
            "description": vault.description,
            "location": vault.location,
            "created_at": vault.created_at,
            "updated_at": vault.updated_at,
            "balances": [
                {
                    "currency_code": balance.currency.code,
                    "currency_name": balance.currency.name,
                    "balance": balance.balance,
                    "last_updated": balance.last_updated
                }
                for balance in vault.balances
            ]
        }
        vaults_data.append(vault_dict)

    # Convert to paginated response
    return paginated(vaults_data, total, skip, limit)


@router.post(
    "",
    response_model=VaultResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new vault",
    dependencies=[Depends(require_permissions(["vault:create"]))]
)
async def create_vault(
    vault_data: VaultCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new vault (branch or main)
    
    **Permissions:** Admin only
    **Note:** Only one main vault allowed
    """
    vault_service = VaultService(db)
    vault = await vault_service.create_vault(vault_data)
    
    return VaultResponse(
        id=vault.id,
        vault_code=vault.vault_code,
        name=vault.name,
        vault_type=vault.vault_type,
        branch_id=vault.branch_id,
        is_active=vault.is_active,
        description=vault.description,
        location=vault.location,
        balances=[],
        created_at=vault.created_at,
        updated_at=vault.updated_at
    )


# ==================== BALANCE OPERATIONS ====================

@router.get(
    "/balances",
    response_model=List[VaultBalanceResponse],
    summary="Get all vault balances"
)
async def get_vault_balances(
    vault_id: Optional[UUID] = Query(None, description="Specific vault ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all currency balances for vault(s)
    
    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)

    if vault_id:
        vault = await vault_service.get_vault_by_id(vault_id)
        balances = await vault_service.get_vault_balance(vault_id)
    else:
        # Get main vault balances
        vault = await vault_service.get_main_vault()
        balances = await vault_service.get_vault_balance(vault.id)
    
    return [
        VaultBalanceResponse(
            vault_id=vault.id,
            vault_code=vault.vault_code,
            vault_name=vault.name,
            currency_id=b.currency_id,
            currency_code=b.currency.code,
            balance=b.balance,
            last_updated=b.last_updated
        )
        for b in balances
    ]


@router.get(
    "/balances/{currency_identifier}",
    response_model=VaultBalanceResponse,
    summary="Get specific currency balance by code or ID"
)
async def get_vault_balance_by_currency(
    currency_identifier: str,
    vault_id: Optional[UUID] = Query(None, description="Specific vault ID"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get balance for specific currency using either the currency UUID or currency code.

    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)
    currency_service = CurrencyService(db)

    # Resolve currency identifier from UUID or code
    try:
        currency_id = UUID(currency_identifier)
    except ValueError:
        currency = await currency_service.get_currency_by_code(currency_identifier.upper())
        currency_id = currency.id

    if vault_id:
        vault = await vault_service.get_vault_by_id(vault_id)
    else:
        vault = await vault_service.get_main_vault()

    balances = await vault_service.get_vault_balance(vault.id, currency_id)

    if not balances:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Balance not found for this currency"
        )

    balance = balances[0]

    return VaultBalanceResponse(
        vault_id=vault.id,
        vault_code=vault.vault_code,
        vault_name=vault.name,
        currency_id=balance.currency_id,
        currency_code=balance.currency.code,
        balance=balance.balance,
        last_updated=balance.last_updated
    )


@router.put(
    "/balances/adjust",
    response_model=VaultBalanceResponse,
    summary="Adjust vault balance (admin only)",
    dependencies=[Depends(require_permissions(["vault:adjust_balance"]))]
)
async def adjust_vault_balance(
    balance_data: VaultBalanceUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually adjust vault balance
    
    **Permissions:** Admin only
    **Warning:** This is for corrections only, not regular operations
    """
    vault_service = VaultService(db)

    vault = await vault_service.get_vault_by_id(balance_data.vault_id)

    # Get current balance
    current_balances = await vault_service.get_vault_balance(
        balance_data.vault_id,
        balance_data.currency_id
    )
    current_balance = current_balances[0] if current_balances else None

    if current_balance:
        difference = balance_data.new_balance - current_balance.balance
        operation = 'add' if difference > 0 else 'subtract'
        amount = abs(difference)

        updated_balance = await vault_service.update_vault_balance(
            balance_data.vault_id,
            balance_data.currency_id,
            amount,
            operation=operation
        )
    else:
        # Create new balance
        updated_balance = await vault_service.update_vault_balance(
            balance_data.vault_id,
            balance_data.currency_id,
            balance_data.new_balance,
            operation='add'
        )
    
    return VaultBalanceResponse(
        vault_id=vault.id,
        vault_code=vault.vault_code,
        vault_name=vault.name,
        currency_id=updated_balance.currency_id,
        currency_code=updated_balance.currency.code,
        balance=updated_balance.balance,
        last_updated=updated_balance.last_updated
    )


# ==================== TRANSFER OPERATIONS ====================

@router.post(
    "/transfer/vault-to-vault",
    response_model=VaultTransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Transfer between vaults",
    dependencies=[Depends(require_permissions(["vault:transfer"]))]
)
async def transfer_vault_to_vault(
    transfer_data: VaultToVaultTransferCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transfer funds between two vaults
    
    **Permissions:** Manager or Admin
    **Approval:** Required if amount >= threshold
    """
    vault_service = VaultService(db)
    transfer = await vault_service.transfer_vault_to_vault(transfer_data, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes
    )


@router.post(
    "/transfer/to-branch",
    response_model=VaultTransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Transfer from vault to branch",
    dependencies=[Depends(require_permissions(["vault:transfer"]))]
)
async def transfer_to_branch(
    transfer_data: VaultToBranchTransferCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transfer funds from vault to branch
    
    **Permissions:** Manager or Admin
    **Approval:** Required if amount >= threshold
    """
    vault_service = VaultService(db)
    transfer = await vault_service.transfer_to_branch(transfer_data, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes
    )


@router.post(
    "/transfer/from-branch",
    response_model=VaultTransferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Transfer from branch to vault",
    dependencies=[Depends(require_permissions(["vault:transfer"]))]
)
async def transfer_from_branch(
    transfer_data: BranchToVaultTransferCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Transfer funds from branch to vault
    
    **Permissions:** Manager or Admin
    """
    vault_service = VaultService(db)
    transfer = await vault_service.transfer_from_branch(transfer_data, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes
    )


# ==================== TRANSFER WORKFLOW ====================

@router.put(
    "/transfer/{transfer_id}/approve",
    response_model=VaultTransferResponse,
    summary="Approve or reject transfer",
    dependencies=[Depends(require_permissions(["vault:approve"]))]
)
async def approve_transfer(
    transfer_id: UUID,
    approval_data: TransferApproval,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve or reject a pending transfer
    
    **Permissions:** Manager or Admin only
    """
    vault_service = VaultService(db)
    transfer = await vault_service.approve_transfer(transfer_id, approval_data, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes,
        rejection_reason=transfer.rejection_reason
    )


@router.put(
    "/transfer/{transfer_id}/complete",
    response_model=VaultTransferResponse,
    summary="Mark transfer as completed",
    dependencies=[Depends(require_permissions(["vault:receive"]))]
)
async def complete_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark transfer as received/completed
    
    **Permissions:** Any user with vault:receive permission
    """
    vault_service = VaultService(db)
    transfer = await vault_service.complete_transfer(transfer_id, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes
    )


@router.delete(
    "/transfer/{transfer_id}",
    response_model=VaultTransferResponse,
    summary="Cancel transfer",
    dependencies=[Depends(require_permissions(["vault:cancel"]))]
)
async def cancel_transfer(
    transfer_id: UUID,
    reason: str = Query(..., min_length=10, description="Cancellation reason"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cancel a pending or in-transit transfer
    
    **Permissions:** Manager or Admin
    """
    vault_service = VaultService(db)
    transfer = await vault_service.cancel_transfer(transfer_id, reason, current_user)
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes,
        rejection_reason=transfer.rejection_reason
    )


# ==================== TRANSFER HISTORY ====================

@router.get(
    "/transfers",
    response_model=PaginatedResponse[VaultTransferResponse],
    summary="Get transfer history"
)
async def get_transfers(
    vault_id: Optional[UUID] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    status: Optional[VaultTransferStatus] = Query(None),
    transfer_type: Optional[VaultTransferType] = Query(None),
    date_from: Optional[datetime] = Query(None),
    date_to: Optional[datetime] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transfer history with pagination and filters

    **Filters:**
    - vault_id: Filter by vault
    - branch_id: Filter by branch
    - status: Filter by transfer status
    - transfer_type: Filter by transfer type
    - date_from/date_to: Date range filter

    **Permissions:** Any authenticated user

    **Returns:** Paginated list of vault transfers with metadata
    """
    vault_service = VaultService(db)

    transfers, total = await vault_service.get_transfer_history(
        vault_id=vault_id,
        branch_id=branch_id,
        status=status,
        date_from=date_from,
        date_to=date_to,
        skip=skip,
        limit=limit
    )

    # Convert to paginated response
    return paginated(transfers, total, skip, limit)


@router.get(
    "/transfers/{transfer_id}",
    response_model=VaultTransferResponse,
    summary="Get transfer details"
)
async def get_transfer(
    transfer_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific transfer details
    
    **Permissions:** Any authenticated user
    """
    from app.db.models.vault import VaultTransfer
    
    transfer = db.query(VaultTransfer).filter(
        VaultTransfer.id == transfer_id
    ).first()
    
    if not transfer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transfer not found"
        )
    
    return VaultTransferResponse(
        id=transfer.id,
        transfer_number=transfer.transfer_number,
        from_vault_id=transfer.from_vault_id,
        to_vault_id=transfer.to_vault_id,
        to_branch_id=transfer.to_branch_id,
        currency_id=transfer.currency_id,
        amount=transfer.amount,
        transfer_type=transfer.transfer_type,
        status=transfer.status,
        initiated_by=transfer.initiated_by,
        approved_by=transfer.approved_by,
        received_by=transfer.received_by,
        initiated_at=transfer.initiated_at,
        approved_at=transfer.approved_at,
        completed_at=transfer.completed_at,
        notes=transfer.notes,
        rejection_reason=transfer.rejection_reason
    )


# ==================== RECONCILIATION ====================

@router.post(
    "/reconciliation",
    response_model=VaultReconciliationReport,
    summary="Perform vault reconciliation",
    dependencies=[Depends(require_permissions(["vault:reconcile"]))]
)
async def reconcile_vault(
    reconciliation_data: VaultReconciliationRequest,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Perform vault balance reconciliation
    
    **Permissions:** Manager or Admin
    **Purpose:** Compare system balance with physical count
    """
    vault_service = VaultService(db)
    result = await vault_service.reconcile_vault_balance(reconciliation_data, current_user)
    
    return VaultReconciliationReport(**result)


@router.get(
    "/reconciliation/report",
    response_model=VaultReconciliationReport,
    summary="Get latest reconciliation report"
)
async def get_reconciliation_report(
    vault_id: UUID = Query(...),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest reconciliation report for vault
    
    **Permissions:** Any authenticated user
    **Note:** This would retrieve stored reconciliation records
    """
    # In production, this would fetch from a reconciliation_records table
    vault_service = VaultService(db)

    # For now, return current state as "reconciliation"
    reconciliation_data = VaultReconciliationRequest(
        vault_id=vault_id,
        notes="Current state report"
    )
    result = await vault_service.reconcile_vault_balance(reconciliation_data, current_user)

    return VaultReconciliationReport(**result)


@router.get(
    "/reconciliation",
    response_model=VaultReconciliationReport,
    summary="Get latest reconciliation report"
)
async def get_reconciliation(
    vault_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get latest reconciliation report for a vault using a query parameter.

    This mirrors the `/reconciliation/report` endpoint but allows clients to
    request via `/reconciliation?vault_id=...` to avoid path parsing issues.
    If no vault_id is provided, the main vault is used.
    """
    vault_service = VaultService(db)

    if vault_id:
        vault = await vault_service.get_vault_by_id(vault_id)
    else:
        vault = await vault_service.get_main_vault()

    reconciliation_data = VaultReconciliationRequest(
        vault_id=vault.id,
        notes="Current state report"
    )
    result = await vault_service.reconcile_vault_balance(reconciliation_data, current_user)

    return VaultReconciliationReport(**result)


# ==================== STATISTICS & ANALYTICS ====================

@router.get(
    "/statistics",
    response_model=VaultStatistics,
    summary="Get vault statistics"
)
async def get_vault_statistics(
    vault_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comprehensive vault statistics
    
    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)

    if vault_id:
        stats = await vault_service.get_vault_statistics(vault_id)
    else:
        # Get main vault stats
        main_vault = await vault_service.get_main_vault()
        stats = await vault_service.get_vault_statistics(main_vault.id)
    
    return VaultStatistics(**stats)


@router.get(
    "/statistics/transfers",
    response_model=VaultTransferSummary,
    summary="Get transfer statistics"
)
async def get_transfer_statistics(
    vault_id: Optional[UUID] = Query(None),
    period_days: int = Query(30, ge=1, le=365, description="Period in days"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get transfer summary statistics
    
    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)

    period_start = datetime.utcnow() - timedelta(days=period_days)
    period_end = datetime.utcnow()

    summary = await vault_service.get_transfer_summary(
        vault_id=vault_id,
        period_start=period_start,
        period_end=period_end
    )

    return VaultTransferSummary(**summary)


# ==================== PARAMETRIC ROUTES (MUST BE LAST) ====================
# These routes use path parameters and must come AFTER all specific routes
# to avoid catching specific paths like /balances, /transfers, /statistics

@router.get(
    "/{vault_id}",
    response_model=VaultResponse,
    summary="Get vault by ID"
)
async def get_vault(
    vault_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific vault details

    **Permissions:** Any authenticated user
    """
    vault_service = VaultService(db)
    vault = await vault_service.get_vault_by_id(vault_id)
    balances = await vault_service.get_vault_balance(vault.id)

    return VaultResponse(
        id=vault.id,
        vault_code=vault.vault_code,
        name=vault.name,
        vault_type=vault.vault_type,
        branch_id=vault.branch_id,
        is_active=vault.is_active,
        description=vault.description,
        location=vault.location,
        balances=[
            {
                'currency_code': b.currency.code,
                'currency_name': b.currency.name_en,
                'balance': b.balance,
                'last_updated': b.last_updated
            }
            for b in balances
        ],
        created_at=vault.created_at,
        updated_at=vault.updated_at
    )


@router.put(
    "/{vault_id}",
    response_model=VaultResponse,
    summary="Update vault",
    dependencies=[Depends(require_permissions(["vault:update"]))]
)
async def update_vault(
    vault_id: UUID,
    vault_data: VaultUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update vault information

    **Permissions:** Admin only
    """
    vault_service = VaultService(db)
    vault = await vault_service.update_vault(vault_id, vault_data)
    balances = await vault_service.get_vault_balance(vault.id)

    return VaultResponse(
        id=vault.id,
        vault_code=vault.vault_code,
        name=vault.name,
        vault_type=vault.vault_type,
        branch_id=vault.branch_id,
        is_active=vault.is_active,
        description=vault.description,
        location=vault.location,
        balances=[
            {
                'currency_code': b.currency.code,
                'currency_name': b.currency.name_en,
                'balance': b.balance,
                'last_updated': b.last_updated
            }
            for b in balances
        ],
        created_at=vault.created_at,
        updated_at=vault.updated_at
    )
