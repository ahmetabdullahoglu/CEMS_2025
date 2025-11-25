"""
Rate Sync API Endpoints
Endpoints for synchronizing exchange rates from external sources
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.api.deps import get_db, get_current_user
from app.db.models.user import User
from app.services.rate_sync_service import RateSyncService
from app.services.external_rates_service import ExternalRateSource
from app.schemas.rate_sync import (
    InitiateRateSyncRequest,
    RateSyncResponse,
    RequestDetailsResponse,
    ApproveRatesRequest,
    ApproveRatesResponse,
    RejectRatesRequest,
    RejectRatesResponse,
    PendingRequestsResponse
)
from app.core.exceptions import ValidationError, ResourceNotFoundError
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/sync-rates", response_model=RateSyncResponse)
async def initiate_rate_sync(
    request: InitiateRateSyncRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initiate exchange rate synchronization from external source

    This endpoint:
    1. Fetches current rates from external API (with fallback)
    2. Compares with existing rates in database
    3. Creates a pending update request for review
    4. Returns request ID and comparison data

    The request will expire after 24 hours if not approved.
    """
    try:
        service = RateSyncService(db)

        # Convert ExternalSourceEnum to ExternalRateSource
        source_map = {
            "exchangerate-api": ExternalRateSource.EXCHANGERATE_API,
            "frankfurter": ExternalRateSource.FRANKFURTER,
            "auto": ExternalRateSource.AUTO
        }
        source = source_map.get(request.source.value, ExternalRateSource.AUTO)

        # Prepare specific pair if provided
        specific_pair = None
        if request.specific_pair:
            specific_pair = {
                "from": request.specific_pair.from_currency,
                "to": request.specific_pair.to_currency
            }

        result = await service.initiate_rate_sync(
            user_id=current_user.id,
            base_currency=request.base_currency,
            target_currencies=request.target_currencies,
            source=source,
            specific_pair=specific_pair
        )

        return result

    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error initiating rate sync: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync rates: {str(e)}"
        )


@router.get("/sync-requests/{request_id}", response_model=RequestDetailsResponse)
async def get_sync_request_details(
    request_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get details of a rate update request for review

    Returns:
    - Request status and metadata
    - Comparison of current vs fetched rates
    - Change percentages
    - Expiration information
    """
    try:
        service = RateSyncService(db)
        result = await service.get_request_details(UUID(request_id))
        return result

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found"
        )
    except Exception as e:
        logger.error(f"Error getting request details: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync-requests/{request_id}/approve", response_model=ApproveRatesResponse)
async def approve_and_apply_rates(
    request_id: str,
    request: ApproveRatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Approve and apply rates from a pending request

    This endpoint:
    1. Validates the request is still pending and not expired
    2. Applies the fetched rates to the database
    3. Calculates buy/sell rates with specified spread
    4. Creates exchange rate history entries
    5. Marks request as approved

    If any rates fail to apply, the response will include error details.
    """
    try:
        service = RateSyncService(db)

        result = await service.approve_and_apply_rates(
            request_id=UUID(request_id),
            user_id=current_user.id,
            notes=request.notes,
            spread_percentage=request.spread_percentage
        )

        return result

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error approving rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync-requests/{request_id}/reject", response_model=RejectRatesResponse)
async def reject_rates(
    request_id: str,
    request: RejectRatesRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Reject a pending rate update request

    The request will be marked as rejected and no rates will be applied.
    """
    try:
        service = RateSyncService(db)

        result = await service.reject_request(
            request_id=UUID(request_id),
            user_id=current_user.id,
            notes=request.notes
        )

        return result

    except ResourceNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Request {request_id} not found"
        )
    except ValidationError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error rejecting rates: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/sync-requests", response_model=PendingRequestsResponse)
async def list_pending_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all pending rate update requests

    Returns pending requests that haven't expired yet.
    Useful for seeing what requests need review.
    """
    try:
        service = RateSyncService(db)

        # Get pending requests
        requests = await service.rate_update_repo.get_pending_requests()

        # Format response
        formatted_requests = []
        for req in requests:
            formatted_requests.append({
                "request_id": str(req.id),
                "status": req.status.value,
                "source": req.source,
                "base_currency": req.base_currency,
                "rates_count": len(req.fetched_rates),
                "requested_at": req.requested_at.isoformat(),
                "expires_at": req.expires_at.isoformat(),
                "is_expired": req.is_expired
            })

        return {
            "count": len(formatted_requests),
            "requests": formatted_requests
        }

    except Exception as e:
        logger.error(f"Error listing requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/sync-requests/cleanup-expired")
async def cleanup_expired_requests(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Cleanup expired pending requests

    Marks all pending requests that have passed their expiry time as expired.
    This is useful for maintenance and can be called periodically.
    """
    try:
        service = RateSyncService(db)
        count = await service.cleanup_expired_requests()

        return {
            "message": f"Marked {count} requests as expired",
            "expired_count": count
        }

    except Exception as e:
        logger.error(f"Error cleaning up requests: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
