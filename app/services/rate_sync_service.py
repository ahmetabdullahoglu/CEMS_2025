"""
Rate Sync Service
Manages the process of synchronizing exchange rates from external sources
"""

from typing import Dict, List, Optional, Any
from uuid import UUID
from decimal import Decimal
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.external_rates_service import ExternalRatesService, ExternalRateSource
from app.services.currency_service import CurrencyService
from app.repositories.rate_update_repo import RateUpdateRequestRepository
from app.repositories.currency_repo import CurrencyRepository
from app.db.models.rate_update_request import UpdateRequestStatus
from app.schemas.currency import ExchangeRateCreate
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)


class RateSyncService:
    """Service for synchronizing exchange rates from external sources"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.external_service = ExternalRatesService()
        self.currency_service = CurrencyService(db)
        self.rate_update_repo = RateUpdateRequestRepository(db)
        self.currency_repo = CurrencyRepository(db)

    async def initiate_rate_sync(
        self,
        user_id: UUID,
        base_currency: str = "USD",
        target_currencies: Optional[List[str]] = None,
        source: ExternalRateSource = ExternalRateSource.AUTO,
        specific_pair: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Initiate rate synchronization from external source

        Args:
            user_id: User initiating the sync
            base_currency: Base currency to fetch rates for
            target_currencies: Specific currencies to fetch (None = all active)
            source: External API source to use
            specific_pair: Specific currency pair {"from": "USD", "to": "EUR"}

        Returns:
            Dictionary with request details including ID for review/approval
        """
        logger.info(f"Initiating rate sync by user {user_id}")

        # Get all active currencies from database if not specified
        if not target_currencies and not specific_pair:
            currencies = await self.currency_repo.get_all_currencies(include_inactive=False)
            target_currencies = [c.code for c in currencies if c.code != base_currency]

        # Fetch rates from external source
        fetched_data = {}
        source_used = ""

        if specific_pair:
            # Fetch specific pair
            from_curr = specific_pair.get("from", "").upper()
            to_curr = specific_pair.get("to", "").upper()

            if not from_curr or not to_curr:
                raise ValidationError("Invalid currency pair specified")

            rate, source_used = await self._fetch_single_rate(
                from_curr, to_curr, source
            )

            if rate:
                fetched_data[f"{from_curr}/{to_curr}"] = {
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "fetched_rate": str(rate),
                    "source": source_used
                }
        else:
            # Fetch multiple rates
            fetched_data, source_used = await self._fetch_multiple_rates(
                base_currency=base_currency,
                target_currencies=target_currencies,
                source=source
            )

        if not fetched_data:
            raise ValidationError("No rates were fetched from external source")

        # Compare with current rates and prepare data
        comparison_data = await self._compare_with_current_rates(fetched_data)

        # Create pending request
        request = await self.rate_update_repo.create_request({
            "requested_by": user_id,
            "source": source_used,
            "base_currency": base_currency.upper(),
            "fetched_rates": comparison_data,
            "status": UpdateRequestStatus.PENDING
        })

        logger.info(f"Created rate update request {request.id} with {len(comparison_data)} rates")

        return {
            "request_id": str(request.id),
            "status": "pending",
            "source": source_used,
            "base_currency": base_currency,
            "rates_count": len(comparison_data),
            "expires_at": request.expires_at.isoformat(),
            "rates": comparison_data
        }

    async def _fetch_single_rate(
        self,
        from_currency: str,
        to_currency: str,
        source: ExternalRateSource
    ) -> tuple[Optional[Decimal], str]:
        """Fetch a single exchange rate with fallback to cross-rate"""
        # Try direct rate first
        rate, source_used = await self.external_service.fetch_specific_rate(
            from_currency, to_currency, source
        )

        if rate:
            return rate, source_used

        # Try cross rate via USD
        logger.info(f"Direct rate not found, trying cross rate via USD")
        rate, source_used = await self.external_service.fetch_cross_rate_via_usd(
            from_currency, to_currency, source
        )

        return rate, source_used

    async def _fetch_multiple_rates(
        self,
        base_currency: str,
        target_currencies: List[str],
        source: ExternalRateSource
    ) -> tuple[Dict[str, Any], str]:
        """Fetch multiple exchange rates"""
        fetched_data = {}

        # Fetch rates from base currency
        try:
            rates, source_used = await self.external_service.fetch_rates(
                base_currency=base_currency,
                target_currencies=target_currencies,
                source=source
            )

            for target_curr, rate in rates.items():
                pair_key = f"{base_currency}/{target_curr}"
                fetched_data[pair_key] = {
                    "from_currency": base_currency,
                    "to_currency": target_curr,
                    "fetched_rate": str(rate),
                    "source": source_used
                }

            # Also fetch inverse rates (target -> base)
            for target_curr in target_currencies:
                try:
                    inverse_rate, _ = await self.external_service.fetch_specific_rate(
                        target_curr, base_currency, source
                    )
                    if inverse_rate:
                        pair_key = f"{target_curr}/{base_currency}"
                        fetched_data[pair_key] = {
                            "from_currency": target_curr,
                            "to_currency": base_currency,
                            "fetched_rate": str(inverse_rate),
                            "source": source_used
                        }
                except Exception as e:
                    logger.warning(f"Could not fetch inverse rate for {target_curr}: {e}")

            return fetched_data, source_used

        except Exception as e:
            logger.error(f"Error fetching rates: {e}")
            raise

    async def _compare_with_current_rates(
        self,
        fetched_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare fetched rates with current database rates"""
        comparison = {}

        for pair_key, fetch_info in fetched_data.items():
            from_curr = fetch_info["from_currency"]
            to_curr = fetch_info["to_currency"]
            fetched_rate = Decimal(fetch_info["fetched_rate"])

            # Get current rate from database
            try:
                current_rate_response = await self.currency_service.get_latest_rate(
                    from_curr, to_curr, use_intermediary=False
                )
                current_rate = current_rate_response.rate

                # Calculate change
                change = fetched_rate - current_rate
                change_pct = (change / current_rate * 100) if current_rate else Decimal('0')

                comparison[pair_key] = {
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "current_rate": str(current_rate),
                    "fetched_rate": str(fetched_rate),
                    "change": str(change),
                    "change_percentage": f"{change_pct:.2f}",
                    "source": fetch_info["source"],
                    "has_current": True
                }

            except ResourceNotFoundError:
                # No current rate exists
                comparison[pair_key] = {
                    "from_currency": from_curr,
                    "to_currency": to_curr,
                    "current_rate": None,
                    "fetched_rate": str(fetched_rate),
                    "change": None,
                    "change_percentage": None,
                    "source": fetch_info["source"],
                    "has_current": False
                }

        return comparison

    async def get_request_details(
        self,
        request_id: UUID
    ) -> Dict[str, Any]:
        """Get details of a rate update request for review"""
        request = await self.rate_update_repo.get_by_id(request_id)

        if not request:
            raise ResourceNotFoundError("RateUpdateRequest", request_id)

        return {
            "request_id": str(request.id),
            "status": request.status.value,
            "source": request.source,
            "base_currency": request.base_currency,
            "requested_by": str(request.requested_by),
            "requested_at": request.requested_at.isoformat(),
            "expires_at": request.expires_at.isoformat(),
            "is_expired": request.is_expired,
            "rates_count": len(request.fetched_rates),
            "rates": request.fetched_rates,
            "reviewed_by": str(request.reviewed_by) if request.reviewed_by else None,
            "reviewed_at": request.reviewed_at.isoformat() if request.reviewed_at else None,
            "review_notes": request.review_notes,
            "rates_applied_count": request.rates_applied_count
        }

    async def approve_and_apply_rates(
        self,
        request_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None,
        spread_percentage: Decimal = Decimal("2.0")
    ) -> Dict[str, Any]:
        """
        Approve and apply rates from a pending request

        Args:
            request_id: ID of the request to approve
            user_id: User approving the request
            notes: Optional approval notes
            spread_percentage: Percentage spread for buy/sell rates (default: 2%)

        Returns:
            Dictionary with application results
        """
        request = await self.rate_update_repo.get_by_id(request_id)

        if not request:
            raise ResourceNotFoundError("RateUpdateRequest", request_id)

        if not request.is_pending:
            raise ValidationError(
                f"Request is not pending. Current status: {request.status.value}"
            )

        if request.is_expired:
            await self.rate_update_repo.update_status(
                request_id,
                UpdateRequestStatus.EXPIRED,
                reviewed_by=user_id,
                review_notes="Request expired before approval"
            )
            raise ValidationError("Request has expired")

        logger.info(f"Applying rates from request {request_id}")

        # Apply rates
        applied_count = 0
        failed_count = 0
        errors = []

        # Get user dict for currency service
        user_dict = {"id": str(user_id)}

        for pair_key, rate_data in request.fetched_rates.items():
            try:
                from_curr = rate_data["from_currency"]
                to_curr = rate_data["to_currency"]
                rate = Decimal(rate_data["fetched_rate"])

                # Calculate buy and sell rates with spread
                buy_rate = rate * (Decimal('1') - (spread_percentage / Decimal('100')))
                sell_rate = rate * (Decimal('1') + (spread_percentage / Decimal('100')))

                # Get currency IDs
                from_currency = await self.currency_repo.get_currency_by_code(from_curr)
                to_currency = await self.currency_repo.get_currency_by_code(to_curr)

                if not from_currency or not to_currency:
                    errors.append(f"{pair_key}: Currency not found")
                    failed_count += 1
                    continue

                # Create rate
                rate_create = ExchangeRateCreate(
                    from_currency_id=from_currency.id,
                    to_currency_id=to_currency.id,
                    rate=rate,
                    buy_rate=buy_rate,
                    sell_rate=sell_rate,
                    notes=f"Auto-synced from {request.source}"
                )

                await self.currency_service.set_exchange_rate(rate_create, user_dict)
                applied_count += 1

            except Exception as e:
                logger.error(f"Error applying rate {pair_key}: {e}")
                errors.append(f"{pair_key}: {str(e)}")
                failed_count += 1

        # Update request status
        status = UpdateRequestStatus.APPROVED if applied_count > 0 else UpdateRequestStatus.FAILED
        error_msg = "; ".join(errors) if errors else None

        await self.rate_update_repo.update_status(
            request_id,
            status=status,
            reviewed_by=user_id,
            review_notes=notes,
            rates_applied_count=applied_count,
            error_message=error_msg
        )

        logger.info(
            f"Applied {applied_count} rates from request {request_id}. "
            f"Failed: {failed_count}"
        )

        return {
            "request_id": str(request_id),
            "status": status.value,
            "applied_count": applied_count,
            "failed_count": failed_count,
            "errors": errors if errors else None
        }

    async def reject_request(
        self,
        request_id: UUID,
        user_id: UUID,
        notes: Optional[str] = None
    ) -> Dict[str, Any]:
        """Reject a pending rate update request"""
        request = await self.rate_update_repo.get_by_id(request_id)

        if not request:
            raise ResourceNotFoundError("RateUpdateRequest", request_id)

        if not request.is_pending:
            raise ValidationError(
                f"Request is not pending. Current status: {request.status.value}"
            )

        await self.rate_update_repo.update_status(
            request_id,
            UpdateRequestStatus.REJECTED,
            reviewed_by=user_id,
            review_notes=notes or "Rejected by user"
        )

        logger.info(f"Rejected rate update request {request_id}")

        return {
            "request_id": str(request_id),
            "status": "rejected",
            "message": "Request rejected successfully"
        }

    async def cleanup_expired_requests(self) -> int:
        """Mark expired requests as expired"""
        count = await self.rate_update_repo.expire_old_requests()
        logger.info(f"Marked {count} requests as expired")
        return count
