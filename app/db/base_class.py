"""
Base Model Classes and Mixins
Common fields and functionality for all database models
"""

import uuid
from datetime import datetime
from typing import Any
from sqlalchemy import Column, DateTime, Boolean, String, UUID as PGUUID
from sqlalchemy.ext.declarative import declared_attr
from app.db.base import Base


class TimestampMixin:
    """Mixin for automatic timestamp tracking"""
    
    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True
    )
    
    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False
    )


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    deleted_at = Column(DateTime, nullable=True)


class UserTrackingMixin:
    """Mixin to track which user created/updated records"""
    
    @declared_attr
    def created_by(cls):
        return Column(
            PGUUID(as_uuid=True),
            # ForeignKey('users.id'),  # Uncomment when User model exists
            nullable=True
        )
    
    @declared_attr
    def updated_by(cls):
        return Column(
            PGUUID(as_uuid=True),
            # ForeignKey('users.id'),  # Uncomment when User model exists
            nullable=True
        )


class BaseModel(Base, TimestampMixin):
    """
    Base model class with common fields
    All models should inherit from this
    """
    
    __abstract__ = True
    
    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        unique=True,
        nullable=False
    )
    
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    
    def dict(self) -> dict[str, Any]:
        """Convert model to dictionary"""
        return {
            column.name: getattr(self, column.name)
            for column in self.__table__.columns
        }
    
    def __repr__(self) -> str:
        """String representation of the model"""
        return f"<{self.__class__.__name__}(id={self.id})>"