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
        to_currency_code: str,
        use_intermediary: bool = True
    ) -> ExchangeRateResponse:
        """
        Get latest exchange rate between two currencies

        Args:
            from_currency_code: Source currency code
            to_currency_code: Target currency code
            use_intermediary: If True, try to find rate via USD if direct rate not found

        Returns:
            ExchangeRateResponse with the exchange rate
        """
        logger.info(f"Getting latest rate for {from_currency_code}/{to_currency_code}, use_intermediary={use_intermediary}")
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
                    created_at=inverse_rate.created_at,
                    updated_at=inverse_rate.updated_at,
                    from_currency=from_currency,
                    to_currency=to_currency
                )
                return ExchangeRateResponse.model_validate(calculated_rate)

            # Try intermediary currency (USD) if enabled
            if use_intermediary and from_currency_code != "USD" and to_currency_code != "USD":
                try:
                    cross_rate = await self._get_cross_rate_via_usd(
                        from_currency_code,
                        to_currency_code,
                        from_currency,
                        to_currency
                    )
                    if cross_rate:
                        return cross_rate
                except Exception as e:
                    logger.error(f"Failed to calculate cross rate via USD: {e}", exc_info=True)

            raise ResourceNotFoundError(
                "ExchangeRate",
                f"{from_currency_code}/{to_currency_code}"
            )

        logger.info(f"Found direct rate for {from_currency_code}/{to_currency_code}: {rate.rate}")
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

    # ==================== Advanced Exchange Operations ====================

    async def _get_cross_rate_via_usd(
        self,
        from_currency_code: str,
        to_currency_code: str,
        from_currency: Currency,
        to_currency: Currency
    ) -> Optional[ExchangeRateResponse]:
        """
        Calculate cross rate via USD intermediary
        Example: AED -> USD -> EGP

        Args:
            from_currency_code: Source currency code
            to_currency_code: Target currency code
            from_currency: Source currency object
            to_currency: Target currency object

        Returns:
            ExchangeRateResponse with calculated cross rate, or None if not possible
        """
        logger.info(
            f"Attempting to calculate cross rate {from_currency_code}/{to_currency_code} via USD"
        )

        # Get USD currency
        usd_currency = await self.repo.get_currency_by_code("USD")
        if not usd_currency:
            logger.warning("USD currency not found in system")
            return None

        # Get from_currency -> USD rate
        from_to_usd = await self.repo.get_exchange_rate(from_currency.id, usd_currency.id)
        if not from_to_usd:
            # Try inverse
            usd_to_from = await self.repo.get_exchange_rate(usd_currency.id, from_currency.id)
            if usd_to_from:
                from_to_usd_rate = Decimal('1') / usd_to_from.rate
                from_to_usd_buy = Decimal('1') / usd_to_from.sell_rate if usd_to_from.sell_rate else None
                from_to_usd_sell = Decimal('1') / usd_to_from.buy_rate if usd_to_from.buy_rate else None
            else:
                logger.debug(f"No rate found for {from_currency_code} -> USD")
                return None
        else:
            from_to_usd_rate = from_to_usd.rate
            from_to_usd_buy = from_to_usd.buy_rate
            from_to_usd_sell = from_to_usd.sell_rate

        # Get USD -> to_currency rate
        usd_to_to = await self.repo.get_exchange_rate(usd_currency.id, to_currency.id)
        if not usd_to_to:
            # Try inverse
            to_to_usd = await self.repo.get_exchange_rate(to_currency.id, usd_currency.id)
            if to_to_usd:
                usd_to_to_rate = Decimal('1') / to_to_usd.rate
                usd_to_to_buy = Decimal('1') / to_to_usd.sell_rate if to_to_usd.sell_rate else None
                usd_to_to_sell = Decimal('1') / to_to_usd.buy_rate if to_to_usd.buy_rate else None
            else:
                logger.debug(f"No rate found for USD -> {to_currency_code}")
                return None
        else:
            usd_to_to_rate = usd_to_to.rate
            usd_to_to_buy = usd_to_to.buy_rate
            usd_to_to_sell = usd_to_to.sell_rate

        # Calculate cross rate: from -> USD -> to
        cross_rate = from_to_usd_rate * usd_to_to_rate
        cross_buy_rate = None
        cross_sell_rate = None

        if from_to_usd_buy and usd_to_to_buy:
            cross_buy_rate = from_to_usd_buy * usd_to_to_buy
        if from_to_usd_sell and usd_to_to_sell:
            cross_sell_rate = from_to_usd_sell * usd_to_to_sell

        logger.info(
            f"Calculated cross rate {from_currency_code}/{to_currency_code} = {cross_rate} "
            f"(via USD: {from_to_usd_rate} * {usd_to_to_rate})"
        )

        # Create calculated rate object
        current_time = datetime.utcnow()
        calculated_rate = ExchangeRate(
            id=UUID('00000000-0000-0000-0000-000000000000'),  # Dummy ID for calculated rate
            from_currency_id=from_currency.id,
            to_currency_id=to_currency.id,
            rate=cross_rate,
            buy_rate=cross_buy_rate,
            sell_rate=cross_sell_rate,
            effective_from=current_time,
            effective_to=None,
            set_by=UUID('00000000-0000-0000-0000-000000000000'),  # System
            notes=f"Calculated via USD: {from_currency_code}->USD ({from_to_usd_rate}) * USD->{to_currency_code} ({usd_to_to_rate})",
            created_at=current_time,
            updated_at=current_time,
            from_currency=from_currency,
            to_currency=to_currency
        )

        logger.info(f"Validating calculated rate for {from_currency_code}/{to_currency_code}")
        try:
            validated_rate = ExchangeRateResponse.model_validate(calculated_rate)
            logger.info(f"Successfully validated cross rate for {from_currency_code}/{to_currency_code}")
            return validated_rate
        except Exception as e:
            logger.error(f"Failed to validate cross rate: {e}", exc_info=True)
            raise

    async def convert_amount(
        self,
        amount: Decimal,
        from_currency_code: str,
        to_currency_code: str,
        use_buy_rate: bool = False,
        use_sell_rate: bool = False,
        use_intermediary: bool = True
    ) -> Dict[str, Any]:
        """
        Convert amount from one currency to another
        Supports cross-currency conversion via USD intermediary

        Args:
            amount: Amount to convert
            from_currency_code: Source currency code
            to_currency_code: Target currency code
            use_buy_rate: Use buy rate if available
            use_sell_rate: Use sell rate if available
            use_intermediary: Allow conversion via USD if direct rate not found

        Returns:
            Dictionary with conversion details
        """
        if amount <= 0:
            raise ValidationError("Amount must be greater than 0")

        # Same currency
        if from_currency_code.upper() == to_currency_code.upper():
            return {
                'from_currency': from_currency_code,
                'to_currency': to_currency_code,
                'from_amount': amount,
                'rate': Decimal('1'),
                'to_amount': amount,
                'rate_type': 'same_currency',
                'via_intermediary': False
            }

        # Get rate (with intermediary support)
        rate_response = await self.get_latest_rate(
            from_currency_code.upper(),
            to_currency_code.upper(),
            use_intermediary=use_intermediary
        )

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
        to_amount = (amount * rate_used).quantize(
            Decimal('0.01'),
            rounding=ROUND_HALF_UP
        )

        # Check if this was calculated via intermediary
        via_intermediary = 'via USD' in (rate_response.notes or '')

        return {
            'from_currency': from_currency_code,
            'to_currency': to_currency_code,
            'from_amount': amount,
            'rate': rate_used,
            'to_amount': to_amount,
            'rate_type': rate_type,
            'via_intermediary': via_intermediary,
            'effective_from': rate_response.effective_from,
            'notes': rate_response.notes
        }

    async def aggregate_balances(
        self,
        balances: List[Dict[str, Any]],
        target_currency_code: str = "USD",
        use_buy_rate: bool = False,
        use_sell_rate: bool = False
    ) -> Dict[str, Any]:
        """
        Aggregate balances from multiple currencies into a single target currency

        Args:
            balances: List of dictionaries with 'currency_code' and 'amount' keys
            target_currency_code: Currency to convert all balances to (default: USD)
            use_buy_rate: Use buy rates for conversion
            use_sell_rate: Use sell rates for conversion

        Returns:
            Dictionary with aggregated balance and conversion details

        Example:
            balances = [
                {'currency_code': 'TRY', 'amount': Decimal('100000.00')},
                {'currency_code': 'EUR', 'amount': Decimal('5000.00')},
                {'currency_code': 'EGP', 'amount': Decimal('50000.00')}
            ]
            result = await service.aggregate_balances(balances, 'USD')
        """
        if not balances:
            return {
                'target_currency': target_currency_code,
                'total_amount': Decimal('0'),
                'breakdown': []
            }

        # Validate target currency exists
        target_currency = await self.repo.get_currency_by_code(target_currency_code.upper())
        if not target_currency:
            raise ResourceNotFoundError("Currency", target_currency_code)

        total = Decimal('0')
        breakdown = []

        for balance_item in balances:
            currency_code = balance_item.get('currency_code', '').upper()
            amount = balance_item.get('amount', Decimal('0'))

            if not currency_code or amount <= 0:
                continue

            try:
                # Convert to target currency
                conversion = await self.convert_amount(
                    amount=amount,
                    from_currency_code=currency_code,
                    to_currency_code=target_currency_code,
                    use_buy_rate=use_buy_rate,
                    use_sell_rate=use_sell_rate,
                    use_intermediary=True
                )

                total += conversion['to_amount']

                breakdown.append({
                    'currency': currency_code,
                    'original_amount': amount,
                    'converted_amount': conversion['to_amount'],
                    'rate_used': conversion['rate'],
                    'rate_type': conversion['rate_type'],
                    'via_intermediary': conversion.get('via_intermediary', False)
                })

            except Exception as e:
                logger.warning(
                    f"Could not convert {currency_code} to {target_currency_code}: {e}"
                )
                # Add to breakdown but don't include in total
                breakdown.append({
                    'currency': currency_code,
                    'original_amount': amount,
                    'converted_amount': None,
                    'error': str(e)
                })

        return {
            'target_currency': target_currency_code,
            'total_amount': total,
            'breakdown': breakdown,
            'rate_type': 'buy' if use_buy_rate else ('sell' if use_sell_rate else 'standard')
        }