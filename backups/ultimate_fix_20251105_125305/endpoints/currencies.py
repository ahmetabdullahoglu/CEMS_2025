# app/api/v1/endpoints/currencies.py
"""
Currency API Endpoints
RESTful API for currency and exchange rate operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_async_db,
    get_current_user,
    get_current_active_user,
    require_roles
)
from app.services.currency_service import CurrencyService
from app.schemas.currency import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyWithRates,
    CurrencyListResponse,
    ExchangeRateCreate,
    ExchangeRateResponse,
    ExchangeRateListResponse
)
from app.db.models.user import User
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== Currency Endpoints ====================

@router.get(
    "",
    response_model=CurrencyListResponse,
    summary="List all currencies",
    description="Get list of all currencies with optional filtering"
)
async def list_currencies(
    include_inactive: bool = Query(
        False,
        description="Include inactive currencies"
    ),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Max records to return"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all currencies
    
    **Permissions:**
    - Any authenticated user can view currencies
    
    **Parameters:**
    - **include_inactive**: Include deactivated currencies
    - **skip**: Pagination offset
    - **limit**: Page size (max 500)
    
    **Returns:**
    - List of currencies with total count
    """
    try:
        service = CurrencyService(db)
        currencies, total = await service.list_currencies(include_inactive, skip, limit)
        
        return CurrencyListResponse(
            success=True,
            data=currencies,
            total=total
        )
    except Exception as e:
        logger.error(f"Error listing currencies: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve currencies"
        )


@router.get(
    "/{currency_id}",
    response_model=CurrencyResponse,
    summary="Get currency by ID",
    description="Get detailed information about a specific currency"
)
async def get_currency(
    currency_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get currency by ID
    
    **Permissions:**
    - Any authenticated user
    
    **Parameters:**
    - **currency_id**: UUID of the currency
    
    **Returns:**
    - Currency details
    
    **Errors:**
    - 404: Currency not found
    """
    try:
        service = CurrencyService(db)
        return await service.get_currency(currency_id)
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting currency {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve currency"
        )


@router.get(
    "/code/{currency_code}",
    response_model=CurrencyResponse,
    summary="Get currency by code",
    description="Get currency information using ISO 4217 code"
)
async def get_currency_by_code(
    currency_code: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get currency by code (e.g., USD, EUR, TRY)
    
    **Permissions:**
    - Any authenticated user
    
    **Parameters:**
    - **currency_code**: ISO 4217 currency code (3 letters)
    
    **Returns:**
    - Currency details
    """
    try:
        service = CurrencyService(db)
        return await service.get_currency_by_code(currency_code.upper())
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting currency {currency_code}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve currency"
        )


@router.get(
    "/{currency_id}/with-rates",
    response_model=CurrencyWithRates,
    summary="Get currency with exchange rates",
    description="Get currency with all its exchange rates"
)
async def get_currency_with_rates(
    currency_id: UUID,
    include_historical: bool = Query(False, description="Include historical rates"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get currency with all exchange rates
    
    **Parameters:**
    - **currency_id**: UUID of the currency
    - **include_historical**: Include historical rates (default: false)
    """
    try:
        service = CurrencyService(db)
        return await service.get_currency_with_rates(currency_id, include_historical)
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error getting currency with rates {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve currency with rates"
        )


@router.post(
    "",
    response_model=CurrencyResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create new currency",
    description="Create a new currency (Admin only)"
)
async def create_currency(
    currency_data: CurrencyCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Create new currency
    
    **Permissions:**
    - Admin only
    
    **Body:**
    - Currency data (code, name, symbol, etc.)
    
    **Returns:**
    - Created currency details
    
    **Validation:**
    - Currency code must be 3 uppercase letters (ISO 4217)
    - Only one base currency allowed
    """
    try:
        service = CurrencyService(db)
        return await service.create_currency(
            currency_data,
            current_user={"id": current_user.id, "username": current_user.username}
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating currency: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create currency"
        )


@router.put(
    "/{currency_id}",
    response_model=CurrencyResponse,
    summary="Update currency",
    description="Update currency information (Admin only)"
)
async def update_currency(
    currency_id: UUID,
    update_data: CurrencyUpdate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Update currency
    
    **Permissions:**
    - Admin only
    
    **Body:**
    - Currency update data
    
    **Returns:**
    - Updated currency details
    """
    try:
        service = CurrencyService(db)
        return await service.update_currency(
            currency_id,
            update_data,
            current_user={"id": current_user.id, "username": current_user.username}
        )
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
        logger.error(f"Error updating currency {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update currency"
        )


@router.patch(
    "/{currency_id}/activate",
    response_model=CurrencyResponse,
    summary="Activate currency",
    description="Activate a currency (Admin only)"
)
async def activate_currency(
    currency_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Activate currency
    
    **Permissions:**
    - Admin only
    """
    try:
        service = CurrencyService(db)
        return await service.activate_currency(
            currency_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error activating currency {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate currency"
        )


@router.patch(
    "/{currency_id}/deactivate",
    response_model=CurrencyResponse,
    summary="Deactivate currency",
    description="Deactivate a currency (Admin only)"
)
async def deactivate_currency(
    currency_id: UUID,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin"]))
):
    """
    Deactivate currency
    
    **Permissions:**
    - Admin only
    
    **Note:**
    - Cannot deactivate base currency
    - Cannot deactivate currency with active transactions
    """
    try:
        service = CurrencyService(db)
        return await service.deactivate_currency(
            currency_id,
            current_user={"id": current_user.id, "username": current_user.username}
        )
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
        logger.error(f"Error deactivating currency {currency_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate currency"
        )


# ==================== Exchange Rate Endpoints ====================

@router.post(
    "/rates",
    response_model=ExchangeRateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Set exchange rate",
    description="Create or update exchange rate between currencies"
)
async def set_exchange_rate(
    rate_data: ExchangeRateCreate,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(require_roles(["admin", "manager"]))
):
    """
    Set new exchange rate
    
    **Permissions:**
    - Admin or Manager
    
    **Body:**
    - Exchange rate data (from/to currencies, rates, effective date)
    
    **Returns:**
    - Created exchange rate details
    
    **Notes:**
    - Previous rate is automatically archived
    - Rate must be positive
    - Both currencies must be active
    """
    try:
        service = CurrencyService(db)
        return await service.set_exchange_rate(
            rate_data,
            current_user={"id": current_user.id, "username": current_user.username}
        )
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
        logger.error(f"Error setting exchange rate: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to set exchange rate"
        )


@router.get(
    "/rates/{from_currency}/{to_currency}",
    response_model=ExchangeRateResponse,
    summary="Get current exchange rate",
    description="Get current exchange rate between two currencies"
)
async def get_exchange_rate(
    from_currency: str,
    to_currency: str,
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get current exchange rate
    
    **Parameters:**
    - **from_currency**: Source currency code (e.g., USD)
    - **to_currency**: Target currency code (e.g., EUR)
    
    **Returns:**
    - Current exchange rate details
    """
    try:
        service = CurrencyService(db)
        return await service.get_latest_rate(
            from_currency.upper(),
            to_currency.upper()
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Error getting exchange rate {from_currency}/{to_currency}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rate"
        )


@router.get(
    "/rates/history/{from_currency}/{to_currency}",
    response_model=ExchangeRateListResponse,
    summary="Get exchange rate history",
    description="Get historical exchange rates between two currencies"
)
async def get_exchange_rate_history(
    from_currency: str,
    to_currency: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    limit: int = Query(50, ge=1, le=1000, description="Max records"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get exchange rate history
    
    **Parameters:**
    - **from_currency**: Source currency code
    - **to_currency**: Target currency code
    - **start_date**: Filter from date (optional)
    - **end_date**: Filter to date (optional)
    - **limit**: Maximum number of records (default: 50, max: 1000)
    """
    try:
        service = CurrencyService(db)
        rates = await service.get_rate_history(
            from_currency.upper(),
            to_currency.upper(),
            start_date,
            end_date,
            limit
        )
        
        return ExchangeRateListResponse(
            success=True,
            data=rates,
            total=len(rates)
        )
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(
            f"Error getting exchange rate history "
            f"{from_currency}/{to_currency}: {str(e)}"
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rate history"
        )


@router.get(
    "/calculate",
    summary="Calculate currency exchange",
    description="Calculate exchange amount between currencies"
)
async def calculate_exchange(
    amount: Decimal = Query(..., description="Amount to exchange"),
    from_currency: str = Query(..., description="Source currency code"),
    to_currency: str = Query(..., description="Target currency code"),
    apply_commission: bool = Query(False, description="Apply commission"),
    db: AsyncSession = Depends(get_async_db),
    current_user: User = Depends(get_current_user)
):
    """
    Calculate currency exchange
    
    **Parameters:**
    - **amount**: Amount to exchange
    - **from_currency**: Source currency code
    - **to_currency**: Target currency code
    - **apply_commission**: Apply commission rate (default: false)
    
    **Returns:**
    - Calculation details including final amount
    """
    try:
        service = CurrencyService(db)
        result = await service.calculate_exchange(
            amount=amount,
            from_currency=from_currency.upper(),
            to_currency=to_currency.upper(),
            apply_commission=apply_commission
        )
        
        return {
            "success": True,
            "calculation": result
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
        logger.error(f"Error calculating exchange: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate exchange"
        )


# ==================== Health Check ====================

@router.get("/health/ping")
async def currency_health_check():
    """Health check endpoint for currency service"""
    return {
        "success": True,
        "service": "currency",
        "status": "healthy"
    }