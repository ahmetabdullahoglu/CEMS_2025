"""
Database Package
Exports database session, engine, base classes and utilities
"""

from app.db.base import (
    Base,
    get_db,
    AsyncSessionLocal,
    engine,
    init_db,
    drop_db
)

from app.db.base_class import (
    BaseModel,
    TimestampMixin,
    SoftDeleteMixin,
    UserTrackingMixin
)

__all__ = [
    # Database session and engine
    "Base",
    "get_db",
    "AsyncSessionLocal",
    "engine",
    "init_db",
    "drop_db",
    
    # Base classes and mixins
    "BaseModel",
    "TimestampMixin",
    "SoftDeleteMixin",
    "UserTrackingMixin",
]