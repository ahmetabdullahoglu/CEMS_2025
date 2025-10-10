"""
Logging Utilities
Centralized logging configuration for CEMS
"""

import logging
import sys
from typing import Optional
from pathlib import Path

from app.core.config import settings


# ==================== Logger Configuration ====================

def setup_logging(log_level: Optional[str] = None) -> None:
    """
    Setup application-wide logging configuration
    
    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    level = log_level or settings.LOG_LEVEL
    
    # Create logs directory if it doesn't exist
    logs_dir = Path("logs")
    logs_dir.mkdir(exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(logs_dir / "cems.log")
        ]
    )
    
    # Set levels for third-party loggers
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING)
    logging.getLogger("fastapi").setLevel(logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a module
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    
    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Starting operation")
    """
    return logging.getLogger(name)


# ==================== Structured Logging ====================

class StructuredLogger:
    """
    Structured logger for JSON-formatted logs
    Useful for production environments and log aggregation
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _log(self, level: str, message: str, **kwargs):
        """Internal log method with structured data"""
        import json
        
        log_data = {
            "message": message,
            **kwargs
        }
        
        log_method = getattr(self.logger, level)
        log_method(json.dumps(log_data))
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self._log("debug", message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        self._log("info", message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self._log("warning", message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        self._log("error", message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        self._log("critical", message, **kwargs)


def get_structured_logger(name: str) -> StructuredLogger:
    """
    Get a structured logger instance
    
    Args:
        name: Logger name
    
    Returns:
        StructuredLogger instance
    """
    return StructuredLogger(name)


# ==================== Audit Logging ====================

class AuditLogger:
    """
    Specialized logger for audit trail
    Logs security-sensitive operations
    """
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        
        # Setup audit-specific file handler
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        handler = logging.FileHandler(logs_dir / "audit.log")
        handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - AUDIT - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)
    
    def log_auth_attempt(
        self,
        username: str,
        success: bool,
        ip_address: Optional[str] = None
    ):
        """Log authentication attempt"""
        status = "SUCCESS" if success else "FAILED"
        self.logger.info(
            f"Authentication {status} - User: {username}, IP: {ip_address}"
        )
    
    def log_permission_check(
        self,
        user_id: str,
        permission: str,
        granted: bool,
        resource: Optional[str] = None
    ):
        """Log permission check"""
        status = "GRANTED" if granted else "DENIED"
        self.logger.info(
            f"Permission {status} - User: {user_id}, "
            f"Permission: {permission}, Resource: {resource}"
        )
    
    def log_data_access(
        self,
        user_id: str,
        operation: str,
        resource_type: str,
        resource_id: str
    ):
        """Log data access"""
        self.logger.info(
            f"Data Access - User: {user_id}, Operation: {operation}, "
            f"Resource: {resource_type}/{resource_id}"
        )
    
    def log_data_modification(
        self,
        user_id: str,
        operation: str,
        resource_type: str,
        resource_id: str,
        changes: Optional[dict] = None
    ):
        """Log data modification"""
        import json
        changes_str = json.dumps(changes) if changes else "N/A"
        self.logger.info(
            f"Data Modification - User: {user_id}, Operation: {operation}, "
            f"Resource: {resource_type}/{resource_id}, Changes: {changes_str}"
        )


# Global audit logger instance
audit_logger = AuditLogger()


# ==================== Performance Logging ====================

class PerformanceLogger:
    """Logger for performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
        self.logger.setLevel(logging.INFO)
    
    def log_request_duration(
        self,
        endpoint: str,
        method: str,
        duration_ms: float,
        status_code: int
    ):
        """Log API request duration"""
        self.logger.info(
            f"Request - {method} {endpoint} - "
            f"Duration: {duration_ms:.2f}ms - Status: {status_code}"
        )
    
    def log_query_duration(
        self,
        query_name: str,
        duration_ms: float
    ):
        """Log database query duration"""
        if duration_ms > 1000:  # Log slow queries (>1s)
            self.logger.warning(
                f"Slow Query - {query_name} - Duration: {duration_ms:.2f}ms"
            )


# Global performance logger instance
performance_logger = PerformanceLogger()


# ==================== Initialize Logging ====================

# Setup logging when module is imported
setup_logging()


# ==================== Export ====================

__all__ = [
    "setup_logging",
    "get_logger",
    "get_structured_logger",
    "StructuredLogger",
    "AuditLogger",
    "audit_logger",
    "PerformanceLogger",
    "performance_logger",
]