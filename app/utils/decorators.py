# app/utils/decorators.py
"""
Utility Decorators
==================
Reusable decorators for common patterns
"""

import asyncio
from functools import wraps
from typing import Callable, Any
from sqlalchemy.exc import OperationalError, DBAPIError

from app.utils.logger import get_logger

logger = get_logger(__name__)


def retry_on_deadlock(max_attempts: int = 3, delay: float = 0.1):
    """
    Retry async function if database deadlock detected
    
    Args:
        max_attempts: Maximum retry attempts (default: 3)
        delay: Base delay between retries in seconds (default: 0.1)
               Increases with each attempt: delay * attempt
    
    Example:
        @retry_on_deadlock(max_attempts=3, delay=0.1)
        async def create_transaction(...):
            # Database operations
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_error = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    # Execute the function
                    result = await func(*args, **kwargs)
                    
                    # Success - return result
                    if attempt > 1:
                        logger.info(
                            f"Success after {attempt} attempts: {func.__name__}"
                        )
                    return result
                    
                except (OperationalError, DBAPIError) as e:
                    last_error = e
                    error_msg = str(e).lower()
                    
                    # Check if it's a deadlock
                    is_deadlock = any([
                        "deadlock" in error_msg,
                        "lock wait timeout" in error_msg,
                        "could not obtain lock" in error_msg
                    ])
                    
                    if not is_deadlock:
                        # Not a deadlock - raise immediately
                        raise
                    
                    # It's a deadlock
                    if attempt < max_attempts:
                        # Still have attempts left - retry
                        wait_time = delay * attempt
                        logger.warning(
                            f"Deadlock detected in {func.__name__}, "
                            f"attempt {attempt}/{max_attempts}, "
                            f"retrying in {wait_time}s..."
                        )
                        await asyncio.sleep(wait_time)
                        continue
                    
                    # No more attempts - log and raise
                    logger.error(
                        f"Deadlock persists after {max_attempts} attempts "
                        f"in {func.__name__}"
                    )
                    raise
            
            # Should never reach here, but just in case
            raise last_error
        
        return wrapper
    return decorator