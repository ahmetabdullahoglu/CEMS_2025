"""
Currency Service - Async Version
Business logic for currency and exchange rate operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.currency_repo import CurrencyRepository
from app.schemas.currency import (
    CurrencyCreate,
    CurrencyUpdate,
    CurrencyResponse,
    CurrencyWithRates,
    ExchangeRateCreate,
    ExchangeRateUpdate,
    ExchangeRateResponse
)
from app.db.models.currency import Currency, ExchangeRate
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class CurrencyService:
    """Service for currency operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = CurrencyRepository(db)
    
    # ==================== Currency Operations ====================
    
    async def create_currency(
        self,
        currency_data: CurrencyCreate,
        current_user: Dict[str, Any]
    ) -> CurrencyResponse:
        """Create new currency"""
        logger.info(
            f"Creating currency {currency_data.code} by user {current_user['id']}"
        )
        
        # Validate currency code format
        if not currency_data.code.isalpha() or len(currency_data.code) != 3:
            raise ValidationError(
                "Currency code must be exactly 3 letters (ISO 4217)"
            )
        
        # Check if base currency already exists
        if currency_data.is_base_currency:
            existing_base = await self.repo.get_base_currency()
            if existing_base:
                raise ValidationError(
                    f"Base currency already exists: {existing_base.code}. "
                    "Only one base currency is allowed."
                )
        
        # Create currency
        currency_dict = currency_data.model_dump()
        currency = await self.repo.create_currency(currency_dict)
        
        logger.info(f"Currency {currency.code} created successfully")
        return CurrencyResponse.model_validate(currency)
    
    async def update_currency(
        self,
        currency_id: UUID,
        update_data: CurrencyUpdate,
        current_user: Dict[str, Any]
    ) -> CurrencyResponse:
        """Update currency"""
        logger.info(
            f"Updating currency {currency_id} by user {current_user['id']}"
        )
        
        currency = await self.repo.get_currency_by_id(currency_id)
        if not currency:
            raise ResourceNotFoundError("Currency", currency_id)
        
        # Validate base currency change
        if update_data.is_base_currency is not None:
            if update_data.is_base_currency and not currency.is_base_currency:
                existing_base = await self.repo.get_base_currency()
                if existing_base and existing_base.id != currency_id:
                    raise ValidationError(
                        f"Base currency already exists: {existing_base.code}"
                    )
        
        # Update currency
        update_dict = update_data.model_dump(exclude_unset=True)
        updated_currency = await self.repo.update_currency(currency_id, update_dict)
        
        logger.info(f"Currency {currency.code} updated successfully")
        return CurrencyResponse.model_validate(updated_currency)
    
    async def get_currency(self, currency_id: UUID) -> CurrencyResponse:
        """Get currency by ID"""
        currency = await self.repo.get_currency_by_id(currency_id)
        if not currency:
            raise ResourceNotFoundError("Currency", currency_id)
        return CurrencyResponse.model_validate(currency)
    
    async def get_currency_by_code(self, code: str) -> CurrencyResponse:
        """Get currency by code"""
        currency = await self.repo.get_currency_by_code(code)
        if not currency:
            raise ResourceNotFoundError("Currency", code)
        return CurrencyResponse.model_validate(currency)
    
    async def get_currency_with_rates(
        self,
        currency_id: UUID,
        include_historical: bool = False
    ) -> CurrencyWithRates:
        """Get currency with all exchange rates"""
        currency = await self.repo.get_currency_by_id(currency_id)
        if not currency:
            raise ResourceNotFoundError("Currency", currency_id)
        
        # Get all rates for this currency
        rates = await self.repo.get_all_rates_for_currency(
            currency_id,
            include_historical
        )
        
        currency_dict = CurrencyResponse.model_validate(currency).model_dump()
        currency_dict['current_rates'] = [
            ExchangeRateResponse.model_validate(rate) for rate in rates
        ]
        
        return CurrencyWithRates(**currency_dict)
    
    async def list_currencies(
        self,
        include_inactive: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[CurrencyResponse], int]:
        """List all currencies with pagination"""
        currencies = await self.repo.get_all_currencies(include_inactive, skip, limit)
        total = await self.repo.count_currencies(include_inactive)
        
        return (
            [CurrencyResponse.model_validate(c) for c in currencies],
            total
        )
    
    async def activate_currency(
        self,
        currency_id: UUID,
        current_user: Dict[str, Any]
    ) -> CurrencyResponse:
        """Activate currency"""
        logger.info(
            f"Activating currency {currency_id} by user {current_user['id']}"
        )
        
        currency = await self.repo.activate_currency(currency_id)
        logger.info(f"Currency {currency.code} activated")
        return CurrencyResponse.model_validate(currency)
    
    async def deactivate_currency(
        self,
        currency_id: UUID,
        current_user: Dict[str, Any]
    ) -> CurrencyResponse:
        """Deactivate currency"""
        logger.info(
            f"Deactivating currency {currency_id} by user {current_user['id']}"
        )
        
        currency = await self.repo.get_currency_by_id(currency_id)
        if not currency:
            raise ResourceNotFoundError("Currency", currency_id)
        
        if currency.is_base_currency:
            raise BusinessRuleViolationError(
                "Cannot deactivate base currency"
            )
        
        currency = await self.repo.deactivate_currency(currency_id)
        logger.info(f"Currency {currency.code} deactivated")
        return CurrencyResponse.model_validate(currency)
    
    # ==================== Exchange Rate Operations ====================
    
    async def set_exchange_rate(
        self,
        rate_data: ExchangeRateCreate,
        current_user: Dict[str, Any]
    ) -> ExchangeRateResponse:
        """Set new exchange rate"""
        logger.info(
            f"Setting exchange rate by user {current_user['id']}"
        )
        
        # Validate currencies exist and are active
        from_currency = await self.repo.get_currency_by_id(rate_data.from_currency_id)
        to_currency = await self.repo.get_currency_by_id(rate_data.to_currency_id)
        
        if not from_currency or not to_currency:
            raise ResourceNotFoundError("Currency", "specified ID")
        
        if not from_currency.is_active or not to_currency.is_active:
            raise ValidationError("Cannot set rate for inactive currency")
        
        if rate_data.from_currency_id == rate_data.to_currency_id:
            raise ValidationError("Cannot set rate for same currency")
        
        # Validate rates
        if rate_data.rate <= 0:
            raise ValidationError("Exchange rate must be greater than 0")
        
        if rate_data.buy_rate and rate_data.buy_rate <= 0:
            raise ValidationError("Buy rate must be greater than 0")
        
        if rate_data.sell_rate and rate_data.sell_rate <= 0:
            raise ValidationError("Sell rate must be greater than 0")
        
        # Get existing rate for history
        existing_rate = await self.repo.get_exchange_rate(
            rate_data.from_currency_id,
            rate_data.to_currency_id
        )
        
        # Create rate dictionary
        rate_dict = rate_data.model_dump()
        rate_dict['set_by'] = UUID(current_user['id'])
        
        # Create new rate
        new_rate = await self.repo.create_exchange_rate(rate_dict)
        
        # Create history entry
        if existing_rate:
            history_data = {
                'exchange_rate_id': new_rate.id,
                'from_currency_code': from_currency.code,
                'to_currency_code': to_currency.code,
                'old_rate': existing_rate.rate,
                'old_buy_rate': existing_rate.buy_rate,
                'old_sell_rate': existing_rate.sell_rate,
                'new_rate': new_rate.rate,
                'new_buy_rate': new_rate.buy_rate,
                'new_sell_rate': new_rate.sell_rate,
                'change_type': 'updated',
                'changed_by': UUID(current_user['id']),
                'changed_at': datetime.utcnow(),
                'reason': rate_data.notes
            }
        else:
            history_data = {
                'exchange_rate_id': new_rate.id,
                'from_currency_code': from_currency.code,
                'to_currency_code': to_currency.code,
                'old_rate': None,
                'old_buy_rate': None,
                'old_sell_rate': None,
                'new_rate': new_rate.rate,
                'new_buy_rate': new_rate.buy_rate,
                'new_sell_rate': new_rate.sell_rate,
                'change_type': 'created',
                'changed_by': UUID(current_user['id']),
                'changed_at': datetime.utcnow(),
                'reason': rate_data.notes
            }
        
        await self.repo.create_rate_history(history_data)
        
        logger.info(
            f"Exchange rate set: {from_currency.code}/{to_currency.code} = {new_rate.rate}"
        )
        return ExchangeRateResponse.model_validate(new_rate)
    
    async def get_latest_rate(
        self,
        from_currency_code: str,
        to_currency_code: str
    ) -> ExchangeRateResponse:
        """Get latest exchange rate between two currencies"""
        from_currency = await self.repo.get_currency_by_code(from_currency_code)
        to_currency = await self.repo.get_currency_by_code(to_currency_code)
        
        if not from_currency or not to_currency:
            raise ResourceNotFoundError("Currency", from_currency_code if not from_currency else to_currency_code)
        
        rate = await self.repo.get_exchange_rate(from_currency.id, to_currency.id)
        
        if not rate:
            # Try inverse rate
            inverse_rate = await self.repo.get_exchange_rate(to_currency.id, from_currency.id)
            if inverse_rate:
                # Create calculated rate from inverse
                calculated_rate = ExchangeRate(
                    id=inverse_rate.id,
                    from_currency_id=from_currency.id,
                    to_currency_id=to_currency.id,
                    rate=Decimal('1') / inverse_rate.rate,
                    buy_rate=Decimal('1') / inverse_rate.sell_rate if inverse_rate.sell_rate else None,
                    sell_rate=Decimal('1') / inverse_rate.buy_rate if inverse_rate.buy_rate else None,
                    effective_from=inverse_rate.effective_from,
                    effective_to=inverse_rate.effective_to,
                    set_by=inverse_rate.set_by,
                    notes=f"Calculated from inverse rate",
                    from_currency=from_currency,
                    to_currency=to_currency
                )
                return ExchangeRateResponse.model_validate(calculated_rate)
            
            raise ResourceNotFoundError(
                "ExchangeRate",
                f"{from_currency_code}/{to_currency_code}"
            )
        
        return ExchangeRateResponse.model_validate(rate)
    
    async def calculate_exchange(
        self,
        amount: Decimal,
        from_currency_code: str,
        to_currency_code: str,
        use_buy_rate: bool = False,
        use_sell_rate: bool = False
    ) -> Dict[str, Any]:
        """Calculate exchange amount"""
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")
        
        # Same currency
        if from_currency_code == to_currency_code:
            return {
                'from_currency': from_currency_code,
                'to_currency': to_currency_code,
                'amount': amount,
                'rate': Decimal('1'),
                'result': amount,
                'rate_type': 'same_currency'
            }
        
        # Get rate
        rate_response = await self.get_latest_rate(from_currency_code, to_currency_code)
        
        # Determine which rate to use
        rate_used = rate_response.rate
        rate_type = 'standard'
        
        if use_buy_rate and rate_response.buy_rate:
            rate_used = rate_response.buy_rate
            rate_type = 'buy'
        elif use_sell_rate and rate_response.sell_rate:
            rate_used = rate_response.sell_rate
            rate_type = 'sell'
        
        # Calculate result
        result = (amount * rate_used).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )
        
        return {
            'from_currency': from_currency_code,
            'to_currency': to_currency_code,
            'amount': amount,
            'rate': rate_used,
            'result': result,
            'rate_type': rate_type,
            'effective_from': rate_response.effective_from
        }
    
    async def get_rate_history(
        self,
        from_currency_code: str,
        to_currency_code: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[ExchangeRateResponse]:
        """Get exchange rate history"""
        from_currency = await self.repo.get_currency_by_code(from_currency_code)
        to_currency = await self.repo.get_currency_by_code(to_currency_code)
        
        if not from_currency or not to_currency:
            raise ResourceNotFoundError("Currency", from_currency_code if not from_currency else to_currency_code)
        
        rates = await self.repo.get_rate_history(
            from_currency.id,
            to_currency.id,
            start_date,
            end_date
        )
        
        return [ExchangeRateResponse.model_validate(rate) for rate in rates]
    
    async def get_all_current_rates(self) -> List[ExchangeRateResponse]:
        """Get all current exchange rates in the system"""
        # Get all active currencies
        currencies = await self.repo.get_all_currencies(include_inactive=False)
        
        all_rates = []
        for currency in currencies:
            rates = await self.repo.get_all_rates_for_currency(
                currency.id,
                include_historical=False
            )
            all_rates.extend(rates)
        
        # Remove duplicates
        seen = set()
        unique_rates = []
        for rate in all_rates:
            rate_key = (rate.from_currency_id, rate.to_currency_id)
            if rate_key not in seen:
                seen.add(rate_key)
                unique_rates.append(rate)
        
        return [ExchangeRateResponse.model_validate(rate) for rate in unique_rates]