"""
Audit Log Model
Tracks all system activities and changes for audit trail
"""

from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import relationship
import uuid

from app.db.base_class import BaseModel


class AuditLog(BaseModel):
    """
    Audit Log Model
    Records all significant actions in the system for compliance and security
    """

    __tablename__ = "audit_logs"

    # User who performed the action
    user_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey('users.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
        comment="User who performed the action"
    )

    # Action details
    action = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Type of action performed (e.g., 'create', 'update', 'delete', 'login')"
    )

    # Entity information
    entity_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="Type of entity affected (e.g., 'transaction', 'user', 'branch')"
    )

    entity_id = Column(
        PGUUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="ID of the affected entity"
    )

    # Change tracking
    changes = Column(
        JSONB,
        nullable=True,
        comment="JSON object containing the changes made"
    )

    # Request metadata
    ip_address = Column(
        String(45),
        nullable=True,
        comment="IP address of the client (supports IPv6)"
    )

    user_agent = Column(
        String(255),
        nullable=True,
        comment="User agent string from the request"
    )

    # Additional details
    description = Column(
        Text,
        nullable=True,
        comment="Human-readable description of the action"
    )

    # Timestamp (inherited from BaseModel: created_at)
    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        comment="When the action occurred"
    )

    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="joined")

    def __repr__(self):
        return f"<AuditLog(action={self.action}, entity_type={self.entity_type}, user_id={self.user_id})>"

    def to_dict(self):
        """Convert audit log to dictionary"""
        return {
            "id": str(self.id),
            "user_id": str(self.user_id) if self.user_id else None,
            "action": self.action,
            "entity_type": self.entity_type,
            "entity_id": str(self.entity_id) if self.entity_id else None,
            "changes": self.changes,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "description": self.description,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
