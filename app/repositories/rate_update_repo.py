"""
Rate Update Request Repository
"""

from typing import List, Optional
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models.rate_update_request import RateUpdateRequest, UpdateRequestStatus


class RateUpdateRequestRepository:
    """Repository for rate update requests"""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_request(self, data: dict) -> RateUpdateRequest:
        """Create a new rate update request"""
        request = RateUpdateRequest(**data)
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_by_id(self, request_id: UUID) -> Optional[RateUpdateRequest]:
        """Get request by ID with relationships"""
        result = await self.db.execute(
            select(RateUpdateRequest)
            .options(
                selectinload(RateUpdateRequest.requester),
                selectinload(RateUpdateRequest.reviewer)
            )
            .where(RateUpdateRequest.id == request_id)
        )
        return result.scalar_one_or_none()

    async def get_pending_requests(
        self,
        limit: int = 100
    ) -> List[RateUpdateRequest]:
        """Get all pending requests"""
        result = await self.db.execute(
            select(RateUpdateRequest)
            .where(
                and_(
                    RateUpdateRequest.status == UpdateRequestStatus.PENDING,
                    RateUpdateRequest.expires_at > datetime.utcnow()
                )
            )
            .order_by(RateUpdateRequest.requested_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        request_id: UUID,
        status: UpdateRequestStatus,
        reviewed_by: Optional[UUID] = None,
        review_notes: Optional[str] = None,
        rates_applied_count: Optional[int] = None,
        error_message: Optional[str] = None
    ) -> RateUpdateRequest:
        """Update request status"""
        request = await self.get_by_id(request_id)
        if not request:
            raise ValueError(f"Request {request_id} not found")

        request.status = status
        request.reviewed_at = datetime.utcnow()

        if reviewed_by:
            request.reviewed_by = reviewed_by
        if review_notes:
            request.review_notes = review_notes
        if rates_applied_count is not None:
            request.rates_applied_count = rates_applied_count
        if error_message:
            request.error_message = error_message

        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def expire_old_requests(self) -> int:
        """Mark expired pending requests as expired"""
        result = await self.db.execute(
            select(RateUpdateRequest).where(
                and_(
                    RateUpdateRequest.status == UpdateRequestStatus.PENDING,
                    RateUpdateRequest.expires_at <= datetime.utcnow()
                )
            )
        )
        expired_requests = result.scalars().all()

        count = 0
        for request in expired_requests:
            request.status = UpdateRequestStatus.EXPIRED
            count += 1

        if count > 0:
            await self.db.commit()

        return count

    async def get_recent_requests(
        self,
        user_id: Optional[UUID] = None,
        limit: int = 50
    ) -> List[RateUpdateRequest]:
        """Get recent requests, optionally filtered by user"""
        query = select(RateUpdateRequest).order_by(
            RateUpdateRequest.requested_at.desc()
        ).limit(limit)

        if user_id:
            query = query.where(RateUpdateRequest.requested_by == user_id)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def delete_request(self, request_id: UUID) -> bool:
        """Delete a request"""
        request = await self.get_by_id(request_id)
        if not request:
            return False

        await self.db.delete(request)
        await self.db.commit()
        return True
