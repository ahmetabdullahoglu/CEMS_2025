"""
Currency API Endpoints
RESTful API for currency and exchange rate operations
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api import deps
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
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/currencies", tags=["Currencies"])


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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
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
        currencies, total = service.list_currencies(include_inactive, skip, limit)
        
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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
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
        return service.get_currency(currency_id)
    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=e.message
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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Get currency by code (e.g., USD, EUR, TRY)
    
    **Parameters:**
    - **currency_code**: ISO 4217 currency code (3 letters)
    
    **Returns:**
    - Currency details
    """
    try:
        service = CurrencyService(db)
        return service.get_currency_by_code(currency_code.upper())
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/{currency_id}/with-rates",
    response_model=CurrencyWithRates,
    summary="Get currency with exchange rates",
    description="Get currency with all current exchange rates"
)
async def get_currency_with_rates(
    currency_id: UUID,
    include_historical: bool = Query(False, description="Include historical rates"),
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Get currency with all exchange rates
    
    **Parameters:**
    - **currency_id**: UUID of the currency
    - **include_historical**: Include inactive/historical rates
    
    **Returns:**
    - Currency with list of exchange rates
    """
    try:
        service = CurrencyService(db)
        return service.get_currency_with_rates(currency_id, include_historical)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.require_role(["admin"]))
):
    """
    Create new currency
    
    **Permissions:**
    - Admin only
    
    **Body:**
    - Currency creation data (code, names, symbol, etc.)
    
    **Returns:**
    - Created currency details
    
    **Errors:**
    - 400: Validation error (duplicate code, invalid base currency, etc.)
    """
    try:
        service = CurrencyService(db)
        return service.create_currency(currency_data, current_user)
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=e.message
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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.require_role(["admin"]))
):
    """
    Update currency
    
    **Permissions:**
    - Admin only
    
    **Parameters:**
    - **currency_id**: UUID of currency to update
    
    **Body:**
    - Fields to update (partial update supported)
    
    **Returns:**
    - Updated currency details
    """
    try:
        service = CurrencyService(db)
        return service.update_currency(currency_id, update_data, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.patch(
    "/{currency_id}/activate",
    response_model=CurrencyResponse,
    summary="Activate currency",
    description="Activate a currency (Admin only)"
)
async def activate_currency(
    currency_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.require_role(["admin"]))
):
    """
    Activate currency
    
    **Permissions:**
    - Admin only
    """
    try:
        service = CurrencyService(db)
        return service.activate_currency(currency_id, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.patch(
    "/{currency_id}/deactivate",
    response_model=CurrencyResponse,
    summary="Deactivate currency",
    description="Deactivate a currency (Admin only)"
)
async def deactivate_currency(
    currency_id: UUID,
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.require_role(["admin"]))
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
        return service.deactivate_currency(currency_id, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
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
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.require_role(["admin", "manager"]))
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
    - Previous rate for same currency pair will be automatically deactivated
    - History entry is created for audit trail
    """
    try:
        service = CurrencyService(db)
        return service.set_exchange_rate(rate_data, current_user)
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/rates/{from_code}/{to_code}",
    response_model=ExchangeRateResponse,
    summary="Get current exchange rate",
    description="Get current exchange rate between two currencies"
)
async def get_exchange_rate(
    from_code: str,
    to_code: str,
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Get current exchange rate
    
    **Parameters:**
    - **from_code**: Source currency code (e.g., USD)
    - **to_code**: Target currency code (e.g., EUR)
    
    **Returns:**
    - Current exchange rate details
    
    **Notes:**
    - If direct rate not found, inverse rate will be calculated
    """
    try:
        service = CurrencyService(db)
        return service.get_latest_rate(from_code.upper(), to_code.upper())
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/rates/history/{from_code}/{to_code}",
    response_model=ExchangeRateListResponse,
    summary="Get exchange rate history",
    description="Get historical exchange rates between two currencies"
)
async def get_rate_history(
    from_code: str,
    to_code: str,
    start_date: Optional[datetime] = Query(None, description="Start date"),
    end_date: Optional[datetime] = Query(None, description="End date"),
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Get exchange rate history
    
    **Parameters:**
    - **from_code**: Source currency code
    - **to_code**: Target currency code
    - **start_date**: Filter from this date (optional)
    - **end_date**: Filter until this date (optional)
    
    **Returns:**
    - List of historical exchange rates
    """
    try:
        service = CurrencyService(db)
        rates = service.get_rate_history(
            from_code.upper(),
            to_code.upper(),
            start_date,
            end_date
        )
        
        return ExchangeRateListResponse(
            success=True,
            data=rates,
            total=len(rates)
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get(
    "/rates/all",
    response_model=ExchangeRateListResponse,
    summary="Get all current rates",
    description="Get all current exchange rates in the system"
)
async def get_all_rates(
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Get all current exchange rates
    
    **Returns:**
    - List of all active exchange rates
    """
    try:
        service = CurrencyService(db)
        rates = service.get_all_current_rates()
        
        return ExchangeRateListResponse(
            success=True,
            data=rates,
            total=len(rates)
        )
    except Exception as e:
        logger.error(f"Error getting all rates: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve exchange rates"
        )


@router.get(
    "/calculate",
    summary="Calculate exchange amount",
    description="Calculate converted amount based on current exchange rate"
)
async def calculate_exchange(
    amount: Decimal = Query(..., gt=0, description="Amount to convert"),
    from_currency: str = Query(..., min_length=3, max_length=3, description="Source currency code"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Target currency code"),
    use_buy_rate: bool = Query(False, description="Use buy rate if available"),
    use_sell_rate: bool = Query(False, description="Use sell rate if available"),
    db: Session = Depends(deps.get_db),
    current_user: dict = Depends(deps.get_current_user)
):
    """
    Calculate exchange amount
    
    **Parameters:**
    - **amount**: Amount to convert (must be > 0)
    - **from_currency**: Source currency code
    - **to_currency**: Target currency code
    - **use_buy_rate**: Use buy rate instead of standard rate
    - **use_sell_rate**: Use sell rate instead of standard rate
    
    **Returns:**
    - Calculation details including:
      - Original amount and currency
      - Exchange rate used
      - Converted amount
      - Rate type (standard/buy/sell)
      - Rate effective date
    
    **Example:**
    ```
    GET /currencies/calculate?amount=100&from_currency=USD&to_currency=EUR
    
    Response:
    {
      "from_currency": "USD",
      "to_currency": "EUR",
      "amount": 100.00,
      "rate": 0.85,
      "result": 85.00,
      "rate_type": "standard",
      "effective_from": "2025-10-10T10:00:00"
    }
    ```
    """
    try:
        service = CurrencyService(db)
        return service.calculate_exchange(
            amount,
            from_currency.upper(),
            to_currency.upper(),
            use_buy_rate,
            use_sell_rate
        )
    except NotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )