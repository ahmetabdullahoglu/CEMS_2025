"""
Rate Update Request Model
Stores pending exchange rate update requests for approval
"""

from sqlalchemy import Column, String, DateTime, Text, Enum as SQLEnum, JSON, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta, timezone
import uuid
import enum

from app.db.base_class import Base


class UpdateRequestStatus(str, enum.Enum):
    """Status of rate update request"""
    PENDING = "pending"  # Waiting for approval
    APPROVED = "approved"  # Approved and applied
    REJECTED = "rejected"  # Rejected by user
    EXPIRED = "expired"  # Expired (not approved in time)
    FAILED = "failed"  # Failed to apply


def _utc_now_naive() -> datetime:
    """Return current UTC time without tzinfo for DB compatibility."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class RateUpdateRequest(Base):
    """
    Stores pending exchange rate update requests

    Workflow:
    1. User initiates rate sync
    2. System fetches rates from external API
    3. Creates pending request with fetched data
    4. User reviews and compares with current rates
    5. User approves/rejects request
    6. If approved: rates are updated in database
    7. Requests expire after 24 hours if not acted upon
    """

    __tablename__ = "rate_update_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Request metadata
    status = Column(
        SQLEnum(
            UpdateRequestStatus,
            name='rateupdaterequeststatus',
            values_callable=lambda enum_cls: [member.value for member in enum_cls]
        ),
        default=UpdateRequestStatus.PENDING,
        nullable=False,
        index=True
    )
    source = Column(String(50), nullable=False)  # e.g., "exchangerate-api"
    base_currency = Column(String(3), nullable=False)  # Base currency used for fetching

    # Fetched data (JSON format)
    # Format: {"EUR": {"rate": "0.92", "old_rate": "0.91", "change_pct": "1.09"}, ...}
    fetched_rates = Column(JSON, nullable=False)

    # Request details
    requested_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    requested_at = Column(DateTime, default=_utc_now_naive, nullable=False)

    # Expiry (24 hours from creation)
    expires_at = Column(DateTime, nullable=False)

    # Approval/Rejection
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text, nullable=True)

    # Applied rates count (after approval)
    rates_applied_count = Column(Integer, default=0, nullable=True)

    # Error message if failed
    error_message = Column(Text, nullable=True)

    # Relationships
    requester = relationship("User", foreign_keys=[requested_by], backref="rate_update_requests")
    reviewer = relationship("User", foreign_keys=[reviewed_by], backref="reviewed_rate_updates")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Set expiry to 24 hours from now if not provided
        if not self.expires_at:
            self.expires_at = _utc_now_naive() + timedelta(hours=24)

    @property
    def is_expired(self) -> bool:
        """Check if request has expired"""
        return _utc_now_naive() > self.expires_at

    @property
    def is_pending(self) -> bool:
        """Check if request is still pending"""
        return self.status == UpdateRequestStatus.PENDING and not self.is_expired

    def __repr__(self):
        return f"<RateUpdateRequest {self.id} - {self.status.value} - {self.source}>"
