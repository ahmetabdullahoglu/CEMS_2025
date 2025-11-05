# app/api/v1/endpoints/transactions.py
"""
Transaction API Endpoints
==========================
Complete transaction management endpoints:
- Income transactions (create, list, get)
- Expense transactions (create, approve, list)
- Exchange transactions (create, preview rate, list)
- Transfer transactions (initiate, receive, list)
- General operations (list all, get, cancel, stats)

Features:
- Comprehensive filtering
- Pagination support
- Permission-based access control
- Rate preview for exchanges
- Transfer workflow (initiate -> receive)
- Transaction statistics
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.db.models.user import User
from app.db.models.transaction import TransactionStatus, TransactionType
from app.services.transaction_service import TransactionService
from app.schemas.transaction import (
    # Income
    IncomeTransactionCreate,
    IncomeTransactionResponse,
    
    # Expense
    ExpenseTransactionCreate,
    ExpenseTransactionResponse,
    ExpenseApprovalRequest,
    
    # Exchange
    ExchangeTransactionCreate,
    ExchangeTransactionResponse,
    ExchangeCalculationRequest,
    ExchangeCalculationResponse,
    
    # Transfer
    TransferTransactionCreate,
    TransferTransactionResponse,
    TransferReceiptRequest,
    
    # Common
    TransactionCancelRequest,
    TransactionFilter,
    TransactionListResponse,
    TransactionSummary,
)
from app.schemas.common import SuccessResponse, PaginationParams
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== INCOME TRANSACTIONS ====================

@router.post(
    "/income",
    response_model=IncomeTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Income Transaction",
    description="Record an income transaction (service fee, commission, etc.)"
)
async def create_income_transaction(
    transaction: IncomeTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new income transaction.
    
    **Permissions Required:** transactions.create
    
    **Income Categories:**
    - service_fee: Service charges
    - commission: Commission earnings
    - other: Other income sources
    
    **Example:**
    ```json
    {
        "amount": 150.50,
        "currency_id": "uuid",
        "branch_id": "uuid",
        "customer_id": "uuid",
        "income_category": "service_fee",
        "income_source": "Money transfer service fee",
        "reference_number": "REF-2025-001"
    }
    ```
    """
    logger.info(
        f"Creating income transaction by user {current_user.id}",
        extra={"user_id": str(current_user.id), "amount": str(transaction.amount)}
    )
    
    try:
        service = TransactionService(db)
        result = await service.create_income_transaction(
            transaction=transaction,
            user_id=current_user.id
        )
        
        logger.info(
            f"Income transaction created: {result.transaction_number}",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating income transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/income",
    response_model=TransactionListResponse,
    summary="List Income Transactions",
    description="Get list of income transactions with filtering and pagination"
)
async def list_income_transactions(
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List income transactions with optional filters.
    
    **Permissions Required:** transactions.read
    
    **Filters:**
    - branch_id: Filter by specific branch
    - customer_id: Filter by customer
    - date_from: Start date (inclusive)
    - date_to: End date (inclusive)
    """
    try:
        service = TransactionService(db)
        
        # Build filter
        filters = TransactionFilter(
            transaction_type=TransactionType.INCOME,
            branch_id=branch_id,
            customer_id=customer_id,
            date_from=date_from,
            date_to=date_to
        )
        
        result = await service.list_transactions(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing income transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/income/{transaction_id}",
    response_model=IncomeTransactionResponse,
    summary="Get Income Transaction Details",
    description="Get detailed information about a specific income transaction"
)
async def get_income_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific income transaction.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        transaction = await service.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )
        
        if transaction.transaction_type != TransactionType.INCOME:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not an income transaction"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting income transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== EXPENSE TRANSACTIONS ====================

@router.post(
    "/expense",
    response_model=ExpenseTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Expense Transaction",
    description="Record an expense transaction (requires manager approval)"
)
async def create_expense_transaction(
    transaction: ExpenseTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new expense transaction (pending approval).
    
    **Permissions Required:** transactions.create
    
    **Expense Categories:**
    - rent: Office rent
    - salary: Employee salaries
    - utilities: Utilities (electricity, water, etc.)
    - maintenance: Maintenance and repairs
    - supplies: Office supplies
    - other: Other expenses
    
    **Note:** Expense transactions are created in PENDING status
    and require manager approval before funds are deducted.
    """
    logger.info(
        f"Creating expense transaction by user {current_user.id}",
        extra={"user_id": str(current_user.id), "amount": str(transaction.amount)}
    )
    
    try:
        service = TransactionService(db)
        result = await service.create_expense_transaction(
            transaction=transaction,
            user_id=current_user.id
        )
        
        logger.info(
            f"Expense transaction created: {result.transaction_number} (pending approval)",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating expense transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/expense/{transaction_id}/approve",
    response_model=ExpenseTransactionResponse,
    summary="Approve Expense Transaction",
    description="Approve a pending expense transaction (manager+ only)"
)
async def approve_expense_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    approval: ExpenseApprovalRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Approve a pending expense transaction.
    
    **Permissions Required:** transactions.approve (manager or admin)
    
    **Note:** Only transactions in PENDING status can be approved.
    Approving deducts the amount from branch balance.
    """
    # Check if user has manager or admin role
    user_roles = [role.name for role in current_user.roles]
    if "manager" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can approve expenses"
        )
    
    logger.info(
        f"Approving expense transaction {transaction_id} by user {current_user.id}",
        extra={
            "transaction_id": str(transaction_id),
            "approver_id": str(current_user.id)
        }
    )
    
    try:
        service = TransactionService(db)
        result = await service.approve_expense_transaction(
            transaction_id=transaction_id,
            approver_id=current_user.id,
            approval_notes=approval.approval_notes
        )
        
        logger.info(
            f"Expense transaction approved: {result.transaction_number}",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error approving expense transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/expense",
    response_model=TransactionListResponse,
    summary="List Expense Transactions",
    description="Get list of expense transactions with filtering"
)
async def list_expense_transactions(
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    status_filter: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List expense transactions with optional filters.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        
        filters = TransactionFilter(
            transaction_type=TransactionType.EXPENSE,
            branch_id=branch_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to
        )
        
        result = await service.list_transactions(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing expense transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== EXCHANGE TRANSACTIONS ====================

@router.post(
    "/exchange/rate-preview",
    response_model=ExchangeCalculationResponse,
    summary="Preview Exchange Rate",
    description="Calculate exchange rate and amounts before executing transaction"
)
async def preview_exchange_rate(
    calculation: ExchangeCalculationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Preview exchange rate and calculated amounts.
    
    **Use this endpoint before creating an exchange transaction
    to show the customer the exact amounts and rates.**
    
    **Example:**
    ```json
    {
        "from_currency_id": "usd-uuid",
        "to_currency_id": "try-uuid",
        "from_amount": 100.00
    }
    ```
    
    **Response:**
    ```json
    {
        "from_amount": 100.00,
        "to_amount": 3245.00,
        "exchange_rate": 32.50,
        "commission_rate": 0.015,
        "commission_amount": 5.00,
        "total_to_receive": 3240.00
    }
    ```
    """
    try:
        service = TransactionService(db)
        result = await service.calculate_exchange(calculation)
        
        return result
        
    except Exception as e:
        logger.error(f"Error calculating exchange: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/exchange",
    response_model=ExchangeTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Execute Exchange Transaction",
    description="Execute a currency exchange transaction"
)
async def create_exchange_transaction(
    transaction: ExchangeTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Execute a currency exchange transaction.
    
    **Permissions Required:** transactions.create
    
    **Process:**
    1. Validate exchange rate is current
    2. Check sufficient balance in from_currency
    3. Deduct from_currency amount (+ commission)
    4. Add to_currency amount
    5. Record transaction
    
    **Example:**
    ```json
    {
        "branch_id": "uuid",
        "customer_id": "uuid",
        "from_currency_id": "usd-uuid",
        "to_currency_id": "try-uuid",
        "from_amount": 100.00,
        "exchange_rate": 32.50,
        "commission_rate": 0.015
    }
    ```
    """
    logger.info(
        f"Creating exchange transaction by user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "from_amount": str(transaction.from_amount)
        }
    )
    
    try:
        service = TransactionService(db)
        result = await service.create_exchange_transaction(
            transaction=transaction,
            user_id=current_user.id
        )
        
        logger.info(
            f"Exchange transaction created: {result.transaction_number}",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating exchange transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/exchange",
    response_model=TransactionListResponse,
    summary="List Exchange Transactions",
    description="Get list of exchange transactions with filtering"
)
async def list_exchange_transactions(
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    from_currency_id: Optional[UUID] = Query(None, description="Filter by source currency"),
    to_currency_id: Optional[UUID] = Query(None, description="Filter by target currency"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List exchange transactions with optional filters.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        
        filters = TransactionFilter(
            transaction_type=TransactionType.EXCHANGE,
            branch_id=branch_id,
            customer_id=customer_id,
            from_currency_id=from_currency_id,
            to_currency_id=to_currency_id,
            date_from=date_from,
            date_to=date_to
        )
        
        result = await service.list_transactions(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing exchange transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/exchange/{transaction_id}",
    response_model=ExchangeTransactionResponse,
    summary="Get Exchange Transaction Details",
    description="Get detailed information about a specific exchange transaction"
)
async def get_exchange_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific exchange transaction.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        transaction = await service.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )
        
        if transaction.transaction_type != TransactionType.EXCHANGE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not an exchange transaction"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting exchange transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== TRANSFER TRANSACTIONS ====================

@router.post(
    "/transfer",
    response_model=TransferTransactionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Initiate Transfer",
    description="Initiate a fund transfer between branches"
)
async def create_transfer_transaction(
    transaction: TransferTransactionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Initiate a transfer transaction.
    
    **Permissions Required:** transactions.create
    
    **Transfer Types:**
    - branch_to_branch: Transfer between branches
    - vault_to_branch: Transfer from vault to branch
    - branch_to_vault: Transfer from branch to vault
    
    **Process:**
    1. Validate sender has sufficient balance
    2. Deduct from sender
    3. Create pending transfer (status: PENDING)
    4. Recipient must call /transfer/{id}/receive to complete
    
    **Example:**
    ```json
    {
        "from_branch_id": "uuid",
        "to_branch_id": "uuid",
        "currency_id": "uuid",
        "amount": 10000.00,
        "transfer_type": "branch_to_branch",
        "notes": "Monthly cash replenishment"
    }
    ```
    """
    logger.info(
        f"Initiating transfer by user {current_user.id}",
        extra={
            "user_id": str(current_user.id),
            "amount": str(transaction.amount)
        }
    )
    
    try:
        service = TransactionService(db)
        result = await service.create_transfer_transaction(
            transaction=transaction,
            user_id=current_user.id
        )
        
        logger.info(
            f"Transfer initiated: {result.transaction_number}",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error creating transfer transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/transfer/{transaction_id}/receive",
    response_model=TransferTransactionResponse,
    summary="Complete Transfer Receipt",
    description="Complete a transfer by receiving the funds"
)
async def receive_transfer(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    receipt: TransferReceiptRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Complete a transfer by confirming receipt.
    
    **Permissions Required:** transactions.receive
    
    **Note:** Only the recipient branch user can complete the transfer.
    This adds the amount to the recipient's balance.
    """
    logger.info(
        f"Receiving transfer {transaction_id} by user {current_user.id}",
        extra={
            "transaction_id": str(transaction_id),
            "receiver_id": str(current_user.id)
        }
    )
    
    try:
        service = TransactionService(db)
        result = await service.receive_transfer(
            transaction_id=transaction_id,
            received_by_id=current_user.id,
            receipt_notes=receipt.receipt_notes
        )
        
        logger.info(
            f"Transfer completed: {result.transaction_number}",
            extra={"transaction_id": str(result.id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error receiving transfer: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/transfer",
    response_model=TransactionListResponse,
    summary="List Transfer Transactions",
    description="Get list of transfer transactions with filtering"
)
async def list_transfer_transactions(
    from_branch_id: Optional[UUID] = Query(None, description="Filter by sender branch"),
    to_branch_id: Optional[UUID] = Query(None, description="Filter by recipient branch"),
    status_filter: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List transfer transactions with optional filters.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        
        filters = TransactionFilter(
            transaction_type=TransactionType.TRANSFER,
            from_branch_id=from_branch_id,
            to_branch_id=to_branch_id,
            status=status_filter,
            date_from=date_from,
            date_to=date_to
        )
        
        result = await service.list_transactions(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing transfer transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/transfer/{transaction_id}",
    response_model=TransferTransactionResponse,
    summary="Get Transfer Transaction Details",
    description="Get detailed information about a specific transfer transaction"
)
async def get_transfer_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of a specific transfer transaction.
    
    **Permissions Required:** transactions.read
    """
    try:
        service = TransactionService(db)
        transaction = await service.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )
        
        if transaction.transaction_type != TransactionType.TRANSFER:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Transaction is not a transfer transaction"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transfer transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== GENERAL TRANSACTION OPERATIONS ====================

@router.get(
    "",
    response_model=TransactionListResponse,
    summary="List All Transactions",
    description="Get list of all transactions with comprehensive filtering"
)
async def list_all_transactions(
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by type"),
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    customer_id: Optional[UUID] = Query(None, description="Filter by customer"),
    status_filter: Optional[TransactionStatus] = Query(None, description="Filter by status"),
    currency_id: Optional[UUID] = Query(None, description="Filter by currency"),
    amount_min: Optional[Decimal] = Query(None, description="Minimum amount"),
    amount_max: Optional[Decimal] = Query(None, description="Maximum amount"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(50, ge=1, le=100, description="Page size"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all transactions with comprehensive filtering.
    
    **Permissions Required:** transactions.read
    
    **Available Filters:**
    - transaction_type: income, expense, exchange, transfer
    - branch_id: Filter by branch
    - customer_id: Filter by customer
    - status: pending, completed, cancelled, failed
    - currency_id: Filter by currency
    - amount_min/amount_max: Amount range
    - date_from/date_to: Date range
    
    **Example:**
    ```
    GET /transactions?transaction_type=exchange&branch_id=uuid&date_from=2025-01-01
    ```
    """
    try:
        service = TransactionService(db)
        
        filters = TransactionFilter(
            transaction_type=transaction_type,
            branch_id=branch_id,
            customer_id=customer_id,
            status=status_filter,
            currency_id=currency_id,
            amount_min=amount_min,
            amount_max=amount_max,
            date_from=date_from,
            date_to=date_to
        )
        
        result = await service.list_transactions(
            filters=filters,
            skip=skip,
            limit=limit
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error listing transactions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/{transaction_id}",
    response_model=dict,  # Will return appropriate type based on transaction_type
    summary="Get Transaction Details",
    description="Get detailed information about any transaction"
)
async def get_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get details of any transaction by ID.
    
    **Permissions Required:** transactions.read
    
    Returns appropriate response schema based on transaction type.
    """
    try:
        service = TransactionService(db)
        transaction = await service.get_transaction(transaction_id)
        
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Transaction {transaction_id} not found"
            )
        
        return transaction
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.put(
    "/{transaction_id}/cancel",
    response_model=dict,
    summary="Cancel Transaction",
    description="Cancel a transaction (manager+ only)"
)
async def cancel_transaction(
    transaction_id: UUID = Path(..., description="Transaction ID"),
    cancellation: TransactionCancelRequest = ...,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel a transaction.
    
    **Permissions Required:** transactions.cancel (manager or admin)
    
    **Rules:**
    - Only pending or completed transactions can be cancelled
    - Cancelled transactions reverse their balance effects
    - Requires cancellation reason
    
    **Example:**
    ```json
    {
        "cancellation_reason": "Customer requested cancellation"
    }
    ```
    """
    # Check if user has manager or admin role
    user_roles = [role.name for role in current_user.roles]
    if "manager" not in user_roles and "admin" not in user_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only managers and admins can cancel transactions"
        )
    
    logger.info(
        f"Cancelling transaction {transaction_id} by user {current_user.id}",
        extra={
            "transaction_id": str(transaction_id),
            "cancelled_by": str(current_user.id)
        }
    )
    
    try:
        service = TransactionService(db)
        result = await service.cancel_transaction(
            transaction_id=transaction_id,
            cancelled_by_id=current_user.id,
            cancellation_reason=cancellation.cancellation_reason
        )
        
        logger.info(
            f"Transaction cancelled: {transaction_id}",
            extra={"transaction_id": str(transaction_id)}
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error cancelling transaction: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/stats/summary",
    response_model=TransactionSummary,
    summary="Get Transaction Statistics",
    description="Get transaction statistics and summary"
)
async def get_transaction_stats(
    branch_id: Optional[UUID] = Query(None, description="Filter by branch"),
    date_from: Optional[date] = Query(None, description="Start date"),
    date_to: Optional[date] = Query(None, description="End date"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get transaction statistics and summary.
    
    **Permissions Required:** transactions.read
    
    **Returns:**
    - Total transactions by type
    - Total amounts by type
    - Transaction count by status
    - Daily/weekly/monthly trends
    
    **Example Response:**
    ```json
    {
        "total_transactions": 1250,
        "total_income": 125000.00,
        "total_expenses": 45000.00,
        "total_exchanges": 250,
        "total_transfers": 50,
        "by_status": {
            "completed": 1200,
            "pending": 30,
            "cancelled": 20
        }
    }
    ```
    """
    try:
        service = TransactionService(db)
        
        filters = TransactionFilter(
            branch_id=branch_id,
            date_from=date_from,
            date_to=date_to
        )
        
        stats = await service.get_transaction_statistics(filters)
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting transaction stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
