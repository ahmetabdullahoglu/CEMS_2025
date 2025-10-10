"""
Currency Pydantic Schemas
Request and response models for Currency endpoints
"""

from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Annotated
from uuid import UUID
from pydantic import BaseModel, Field, field_validator, condecimal


# ==================== Type Aliases ====================
# Pydantic v2 compatible decimal types
ExchangeRateDecimal = Annotated[Decimal, condecimal(gt=0, max_digits=20, decimal_places=6)]
MoneyDecimal = Annotated[Decimal, condecimal(ge=0, max_digits=20, decimal_places=6)]


# ==================== Currency Schemas ====================

class CurrencyBase(BaseModel):
    """Base currency schema"""
    code: str = Field(..., min_length=3, max_length=3, description="ISO 4217 currency code")
    name_en: str = Field(..., min_length=2, max_length=100, description="English name")
    name_ar: str = Field(..., min_length=2, max_length=100, description="Arabic name")
    symbol: Optional[str] = Field(None, max_length=10, description="Currency symbol")
    is_base_currency: bool = Field(default=False, description="Is this the base currency?")
    decimal_places: int = Field(default=2, ge=0, le=8, description="Number of decimal places")
    
    @field_validator('code')
    @classmethod
    def validate_code_uppercase(cls, v: str) -> str:
        """Ensure currency code is uppercase"""
        return v.upper()
    
    @field_validator('code')
    @classmethod
    def validate_code_format(cls, v: str) -> str:
        """Validate currency code format (3 letters)"""
        if not v.isalpha():
            raise ValueError('Currency code must contain only letters')
        return v


class CurrencyCreate(CurrencyBase):
    """Schema for creating a new currency"""
    is_active: bool = True


class CurrencyUpdate(BaseModel):
    """Schema for updating currency"""
    name_en: Optional[str] = Field(None, min_length=2, max_length=100)
    name_ar: Optional[str] = Field(None, min_length=2, max_length=100)
    symbol: Optional[str] = Field(None, max_length=10)
    is_base_currency: Optional[bool] = None
    decimal_places: Optional[int] = Field(None, ge=0, le=8)
    is_active: Optional[bool] = None


class CurrencyResponse(CurrencyBase):
    """Currency response schema"""
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CurrencyWithRates(CurrencyResponse):
    """Currency response with current exchange rates"""
    current_rates: List['ExchangeRateResponse'] = []
    
    class Config:
        from_attributes = True


class CurrencyListResponse(BaseModel):
    """Response for list of currencies"""
    success: bool = True
    data: List[CurrencyResponse]
    total: int


# ==================== Exchange Rate Schemas ====================

class ExchangeRateBase(BaseModel):
    """Base exchange rate schema"""
    from_currency_id: UUID
    to_currency_id: UUID
    rate: ExchangeRateDecimal = Field(..., description="Exchange rate")
    buy_rate: Optional[ExchangeRateDecimal] = Field(None, description="Buy rate")
    sell_rate: Optional[ExchangeRateDecimal] = Field(None, description="Sell rate")
    effective_from: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = Field(None, max_length=500)
    
    @field_validator('from_currency_id', 'to_currency_id')
    @classmethod
    def validate_currency_ids(cls, v: UUID) -> UUID:
        """Validate currency IDs are not empty"""
        if not v:
            raise ValueError('Currency ID cannot be empty')
        return v


class ExchangeRateCreate(ExchangeRateBase):
    """Schema for creating a new exchange rate"""
    pass


class ExchangeRateUpdate(BaseModel):
    """Schema for updating exchange rate"""
    rate: Optional[ExchangeRateDecimal] = None
    buy_rate: Optional[ExchangeRateDecimal] = None
    sell_rate: Optional[ExchangeRateDecimal] = None
    effective_from: Optional[datetime] = None
    effective_to: Optional[datetime] = None
    notes: Optional[str] = Field(None, max_length=500)


class ExchangeRateResponse(ExchangeRateBase):
    """Exchange rate response schema"""
    id: UUID
    effective_to: Optional[datetime]
    set_by: UUID
    is_current: bool
    created_at: datetime
    updated_at: datetime
    
    # Include currency information
    from_currency: CurrencyResponse
    to_currency: CurrencyResponse
    
    class Config:
        from_attributes = True


class ExchangeRateWithDetails(ExchangeRateResponse):
    """Exchange rate with setter details"""
    setter_username: Optional[str] = None
    
    class Config:
        from_attributes = True


class ExchangeRateListResponse(BaseModel):
    """Response for list of exchange rates"""
    success: bool = True
    data: List[ExchangeRateResponse]
    total: int


# ==================== Exchange Rate History Schemas ====================

class ExchangeRateHistoryResponse(BaseModel):
    """Exchange rate history response"""
    id: UUID
    exchange_rate_id: UUID
    from_currency_code: str
    to_currency_code: str
    old_rate: Optional[ExchangeRateDecimal]
    old_buy_rate: Optional[ExchangeRateDecimal]
    old_sell_rate: Optional[ExchangeRateDecimal]
    new_rate: ExchangeRateDecimal
    new_buy_rate: Optional[ExchangeRateDecimal]
    new_sell_rate: Optional[ExchangeRateDecimal]
    change_type: str
    changed_by: UUID
    changed_at: datetime
    reason: Optional[str]
    rate_change_percentage: Decimal
    
    class Config:
        from_attributes = True


class ExchangeRateHistoryListResponse(BaseModel):
    """Response for exchange rate history list"""
    success: bool = True
    data: List[ExchangeRateHistoryResponse]
    total: int


# ==================== Utility Schemas ====================

class CurrencyPairRequest(BaseModel):
    """Request for currency pair operations"""
    from_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    to_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    
    @field_validator('from_currency', 'to_currency')
    @classmethod
    def validate_code_uppercase(cls, v: str) -> str:
        """Ensure currency codes are uppercase"""
        return v.upper()


class ExchangeCalculationRequest(CurrencyPairRequest):
    """Request for exchange calculation"""
    amount: MoneyDecimal = Field(..., description="Amount to exchange")
    use_buy_rate: bool = Field(default=False, description="Use buy rate if available")
    use_sell_rate: bool = Field(default=False, description="Use sell rate if available")


class ExchangeCalculationResponse(BaseModel):
    """Response for exchange calculation"""
    success: bool = True
    from_currency: str
    to_currency: str
    from_amount: Decimal
    to_amount: Decimal
    rate_used: Decimal
    commission: Optional[Decimal] = None
    total_amount: Decimal
    calculation_time: datetime = Field(default_factory=datetime.utcnow)


class CurrentRateRequest(CurrencyPairRequest):
    """Request to get current exchange rate"""
    pass


class CurrentRateResponse(BaseModel):
    """Response with current exchange rate"""
    success: bool = True
    from_currency: str
    to_currency: str
    rate: Decimal
    buy_rate: Optional[Decimal]
    sell_rate: Optional[Decimal]
    effective_from: datetime
    inverse_rate: Decimal


class RateHistoryRequest(CurrencyPairRequest):
    """Request for rate history"""
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(default=100, ge=1, le=1000)


class SetRateRequest(BaseModel):
    """Request to set exchange rate"""
    from_currency: str = Field(..., min_length=3, max_length=3)
    to_currency: str = Field(..., min_length=3, max_length=3)
    rate: ExchangeRateDecimal = Field(..., description="Exchange rate")
    buy_rate: Optional[ExchangeRateDecimal] = Field(None, description="Buy rate")
    sell_rate: Optional[ExchangeRateDecimal] = Field(None, description="Sell rate")
    notes: Optional[str] = Field(None, max_length=500)
    effective_from: datetime = Field(default_factory=datetime.utcnow)


class CurrencyStatsResponse(BaseModel):
    """Currency statistics response"""
    success: bool = True
    currency_code: str
    total_transactions: int = 0
    total_volume: Decimal = Decimal('0')
    average_rate: Optional[Decimal] = None
    highest_rate: Optional[Decimal] = None
    lowest_rate: Optional[Decimal] = None
    last_updated: Optional[datetime] = None


# ==================== Common Response ====================

class MessageResponse(BaseModel):
    """Generic message response"""
    success: bool = True
    message: str


# Update forward references
CurrencyWithRates.model_rebuild()