"""
External Exchange Rates Service
Fetches exchange rates from external APIs with fallback support
"""

import httpx
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from enum import Enum

from app.utils.logger import get_logger

logger = get_logger(__name__)


class ExternalRateSource(str, Enum):
    """Available external rate sources"""
    EXCHANGERATE_API = "exchangerate-api"
    FRANKFURTER = "frankfurter"
    AUTO = "auto"  # Try all sources with fallback


class ExternalRatesService:
    """Service to fetch exchange rates from external APIs"""

    # API endpoints
    EXCHANGERATE_API_URL = "https://api.exchangerate-api.com/v4/latest/{base}"
    FRANKFURTER_URL = "https://api.frankfurter.app/latest?from={base}"

    # Request timeout
    REQUEST_TIMEOUT = 10.0

    async def fetch_rates(
        self,
        base_currency: str = "USD",
        target_currencies: Optional[List[str]] = None,
        source: ExternalRateSource = ExternalRateSource.AUTO
    ) -> Tuple[Dict[str, Decimal], str]:
        """
        Fetch exchange rates from external API

        Args:
            base_currency: Base currency code (default: USD)
            target_currencies: List of target currency codes (None = all)
            source: Which API source to use

        Returns:
            Tuple of (rates_dict, source_used)
            rates_dict format: {"EUR": Decimal("0.92"), "GBP": Decimal("0.79"), ...}

        Raises:
            Exception if all sources fail
        """
        base_currency = base_currency.upper()

        if source == ExternalRateSource.AUTO:
            # Try all sources in order
            sources_to_try = [
                ExternalRateSource.EXCHANGERATE_API,
                ExternalRateSource.FRANKFURTER
            ]
        else:
            sources_to_try = [source]

        last_error = None

        for src in sources_to_try:
            try:
                logger.info(f"Attempting to fetch rates from {src.value} for {base_currency}")

                if src == ExternalRateSource.EXCHANGERATE_API:
                    rates = await self._fetch_from_exchangerate_api(base_currency)
                elif src == ExternalRateSource.FRANKFURTER:
                    rates = await self._fetch_from_frankfurter(base_currency)
                else:
                    continue

                # Filter to target currencies if specified
                if target_currencies:
                    target_currencies_upper = [c.upper() for c in target_currencies]
                    rates = {
                        k: v for k, v in rates.items()
                        if k in target_currencies_upper
                    }

                logger.info(f"Successfully fetched {len(rates)} rates from {src.value}")
                return rates, src.value

            except Exception as e:
                logger.warning(f"Failed to fetch from {src.value}: {e}")
                last_error = e
                continue

        # All sources failed
        error_msg = f"All external rate sources failed. Last error: {last_error}"
        logger.error(error_msg)
        raise Exception(error_msg)

    async def _fetch_from_exchangerate_api(
        self,
        base_currency: str
    ) -> Dict[str, Decimal]:
        """Fetch rates from ExchangeRate-API"""
        url = self.EXCHANGERATE_API_URL.format(base=base_currency)

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if "rates" not in data:
            raise ValueError("Invalid response format from ExchangeRate-API")

        # Convert to Decimal
        rates = {}
        for currency, rate in data["rates"].items():
            if currency != base_currency:  # Skip base currency
                rates[currency] = Decimal(str(rate))

        return rates

    async def _fetch_from_frankfurter(
        self,
        base_currency: str
    ) -> Dict[str, Decimal]:
        """Fetch rates from Frankfurter API"""
        url = self.FRANKFURTER_URL.format(base=base_currency)

        async with httpx.AsyncClient(timeout=self.REQUEST_TIMEOUT) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        if "rates" not in data:
            raise ValueError("Invalid response format from Frankfurter")

        # Convert to Decimal
        rates = {}
        for currency, rate in data["rates"].items():
            if currency != base_currency:  # Skip base currency
                rates[currency] = Decimal(str(rate))

        return rates

    async def fetch_specific_rate(
        self,
        from_currency: str,
        to_currency: str,
        source: ExternalRateSource = ExternalRateSource.AUTO
    ) -> Tuple[Optional[Decimal], str]:
        """
        Fetch a specific exchange rate

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            source: Which API source to use

        Returns:
            Tuple of (rate, source_used) or (None, "") if not found
        """
        try:
            # Try direct rate
            rates, source_used = await self.fetch_rates(
                base_currency=from_currency,
                target_currencies=[to_currency],
                source=source
            )

            if to_currency.upper() in rates:
                return rates[to_currency.upper()], source_used

            # Try inverse rate
            rates, source_used = await self.fetch_rates(
                base_currency=to_currency,
                target_currencies=[from_currency],
                source=source
            )

            if from_currency.upper() in rates:
                inverse_rate = Decimal('1') / rates[from_currency.upper()]
                return inverse_rate, source_used

            return None, ""

        except Exception as e:
            logger.error(f"Error fetching rate {from_currency}/{to_currency}: {e}")
            return None, ""

    async def fetch_cross_rate_via_usd(
        self,
        from_currency: str,
        to_currency: str,
        source: ExternalRateSource = ExternalRateSource.AUTO
    ) -> Tuple[Optional[Decimal], str]:
        """
        Calculate cross rate via USD intermediary

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            source: Which API source to use

        Returns:
            Tuple of (calculated_rate, source_used) or (None, "") if not possible
        """
        try:
            # Get from_currency -> USD rate
            from_to_usd, source_used = await self.fetch_specific_rate(
                from_currency=from_currency,
                to_currency="USD",
                source=source
            )

            if not from_to_usd:
                return None, ""

            # Get USD -> to_currency rate
            usd_to_to, _ = await self.fetch_specific_rate(
                from_currency="USD",
                to_currency=to_currency,
                source=source
            )

            if not usd_to_to:
                return None, ""

            # Calculate cross rate
            cross_rate = from_to_usd * usd_to_to

            logger.info(
                f"Calculated cross rate {from_currency}/{to_currency} = {cross_rate} "
                f"via USD ({from_to_usd} * {usd_to_to})"
            )

            return cross_rate, source_used

        except Exception as e:
            logger.error(f"Error calculating cross rate: {e}")
            return None, ""
