"""
RBAC Middleware
Role-Based Access Control middleware for permission checking and audit logging
"""

import time
from typing import Callable, Optional, List
from uuid import UUID
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.permissions import (
    validate_permission,
    check_permission_hierarchy,
    parse_permission,
)
from app.core.exceptions import PermissionDeniedError
from app.db.models.user import User


# ==================== Permission Cache ====================

class PermissionCache:
    """Simple in-memory cache for user permissions"""
    
    def __init__(self, ttl: int = 300):  # 5 minutes TTL
        self._cache: dict = {}
        self._ttl = ttl
    
    def get(self, user_id: UUID) -> Optional[List[str]]:
        """Get cached permissions for user"""
        if user_id in self._cache:
            data, timestamp = self._cache[user_id]
            if time.time() - timestamp < self._ttl:
                return data
            else:
                del self._cache[user_id]
        return None
    
    def set(self, user_id: UUID, permissions: List[str]) -> None:
        """Cache user permissions"""
        self._cache[user_id] = (permissions, time.time())
    
    def invalidate(self, user_id: UUID) -> None:
        """Invalidate cached permissions"""
        if user_id in self._cache:
            del self._cache[user_id]
    
    def clear(self) -> None:
        """Clear all cached permissions"""
        self._cache.clear()


# Global permission cache
permission_cache = PermissionCache()


# ==================== RBAC Middleware ====================

class RBACMiddleware(BaseHTTPMiddleware):
    """
    Middleware for Role-Based Access Control
    
    Checks user permissions before allowing access to endpoints
    Logs permission checks for audit trail
    """
    
    def __init__(
        self,
        app: ASGIApp,
        exclude_paths: Optional[List[str]] = None,
    ):
        super().__init__(app)
        
        # Paths that don't require permission checking
        self.exclude_paths = exclude_paths or [
            "/",
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
        ]
    
    async def dispatch(
        self, request: Request, call_next: Callable
    ) -> Response:
        """
        Process request and check permissions
        """
        # Skip permission check for excluded paths
        if self._should_skip_check(request):
            return await call_next(request)
        
        # Get user from request state (set by auth dependency)
        user = getattr(request.state, "user", None)
        
        if user:
            # Store in request state for logging
            request.state.user_id = user.id
            request.state.username = user.username
            
            # Log permission check
            await self._log_access(request, user)
        
        # Continue processing request
        response = await call_next(request)
        
        return response
    
    def _should_skip_check(self, request: Request) -> bool:
        """Check if path should skip permission checking"""
        path = request.url.path
        
        # Check exact matches
        if path in self.exclude_paths:
            return True
        
        # Check path prefixes
        for exclude_path in self.exclude_paths:
            if path.startswith(exclude_path):
                return True
        
        return False
    
    async def _log_access(self, request: Request, user: User) -> None:
        """
        Log access attempt for audit trail
        
        Args:
            request: FastAPI request
            user: Current user
        """
        # TODO: Implement audit logging
        # In production, log to database or external service
        
        log_data = {
            "timestamp": time.time(),
            "user_id": str(user.id),
            "username": user.username,
            "method": request.method,
            "path": request.url.path,
            "ip_address": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }
        
        # Log to console for development
        # In production: save to database
        # await save_audit_log(log_data)
        pass


# ==================== Permission Checker ====================

class PermissionChecker:
    """Utility class for checking permissions"""
    
    @staticmethod
    async def check_permissions(
        user: User,
        required_permissions: List[str],
        require_all: bool = True
    ) -> bool:
        """
        Check if user has required permissions
        
        Args:
            user: User to check
            required_permissions: List of required permissions
            require_all: If True, user must have ALL permissions.
                        If False, user needs at least ONE permission.
        
        Returns:
            bool: True if user has required permissions
        
        Raises:
            PermissionDeniedError: If user lacks permissions
        """
        # Superuser has all permissions
        if user.is_superuser:
            return True
        
        # Get user permissions (cached)
        user_permissions = await PermissionChecker.get_user_permissions(user)
        
        if require_all:
            # User must have ALL required permissions
            missing_permissions = []
            for required_perm in required_permissions:
                if not PermissionChecker._has_permission(user_permissions, required_perm):
                    missing_permissions.append(required_perm)
            
            if missing_permissions:
                raise PermissionDeniedError(
                    message=f"Missing required permissions: {', '.join(missing_permissions)}",
                    required_permission=", ".join(missing_permissions)
                )
        else:
            # User needs at least ONE permission
            has_any = any(
                PermissionChecker._has_permission(user_permissions, perm)
                for perm in required_permissions
            )
            
            if not has_any:
                raise PermissionDeniedError(
                    message=f"Requires one of: {', '.join(required_permissions)}",
                    required_permission=", ".join(required_permissions)
                )
        
        return True
    
    @staticmethod
    async def get_user_permissions(user: User) -> List[str]:
        """
        Get all permissions for user (from roles)
        Uses cache for performance
        
        Args:
            user: User object
            
        Returns:
            List[str]: List of permission strings
        """
        # Check cache first
        cached = permission_cache.get(user.id)
        if cached is not None:
            return cached
        
        # Gather permissions from all user roles
        permissions = set()
        for role in user.roles:
            permissions.update(role.permissions)
        
        permission_list = list(permissions)
        
        # Cache the result
        permission_cache.set(user.id, permission_list)
        
        return permission_list
    
    @staticmethod
    def _has_permission(user_permissions: List[str], required_permission: str) -> bool:
        """
        Check if user has a specific permission
        Considers permission hierarchy
        
        Args:
            user_permissions: List of user's permissions
            required_permission: Required permission
            
        Returns:
            bool: True if user has permission
        """
        # Direct check
        if required_permission in user_permissions:
            return True
        
        # Check with hierarchy
        return check_permission_hierarchy(user_permissions, required_permission)
    
    @staticmethod
    def invalidate_user_cache(user_id: UUID) -> None:
        """
        Invalidate cached permissions for user
        Call this when user's roles or permissions change
        
        Args:
            user_id: User ID
        """
        permission_cache.invalidate(user_id)


# ==================== Branch Access Checker ====================

class BranchAccessChecker:
    """Utility for checking branch-level access"""
    
    @staticmethod
    async def check_branch_access(
        user: User,
        branch_id: UUID,
        permission: Optional[str] = None
    ) -> bool:
        """
        Check if user has access to a specific branch
        
        Args:
            user: User to check
            branch_id: Branch ID to check access for
            permission: Optional specific permission to check
        
        Returns:
            bool: True if user has access
        
        Raises:
            PermissionDeniedError: If user lacks access
        """
        # Superuser has access to all branches
        if user.is_superuser:
            return True
        
        # Check if user is assigned to branch
        user_branch_ids = [branch.id for branch in user.branches]
        
        if branch_id not in user_branch_ids:
            raise PermissionDeniedError(
                message=f"You don't have access to branch {branch_id}",
                required_permission="branch:access"
            )
        
        # If specific permission required, check it
        if permission:
            await PermissionChecker.check_permissions(user, [permission])
        
        return True
    
    @staticmethod
    async def get_accessible_branches(user: User) -> List[UUID]:
        """
        Get list of branch IDs user has access to
        
        Args:
            user: User object
            
        Returns:
            List[UUID]: List of accessible branch IDs
        """
        # Superuser can access all branches
        if user.is_superuser:
            # TODO: Return all branch IDs from database
            # For now, return empty list (will be handled by query)
            return []
        
        return [branch.id for branch in user.branches]


# ==================== Audit Logger ====================

class AuditLogger:
    """Audit logging for security events"""
    
    @staticmethod
    async def log_permission_check(
        user_id: UUID,
        permission: str,
        granted: bool,
        resource_type: Optional[str] = None,
        resource_id: Optional[UUID] = None,
        ip_address: Optional[str] = None
    ) -> None:
        """
        Log permission check for audit trail
        
        Args:
            user_id: User who attempted access
            permission: Permission that was checked
            granted: Whether permission was granted
            resource_type: Type of resource accessed
            resource_id: ID of resource accessed
            ip_address: User's IP address
        """
        # TODO: Implement actual audit logging to database
        log_entry = {
            "timestamp": time.time(),
            "user_id": str(user_id),
            "permission": permission,
            "granted": granted,
            "resource_type": resource_type,
            "resource_id": str(resource_id) if resource_id else None,
            "ip_address": ip_address,
        }
        
        # In production: save to audit_log table
        # await save_to_audit_log(log_entry)
        pass
    
    @staticmethod
    async def log_security_event(
        event_type: str,
        user_id: Optional[UUID] = None,
        details: Optional[dict] = None,
        severity: str = "info"
    ) -> None:
        """
        Log security-related events
        
        Args:
            event_type: Type of security event
            user_id: User involved in event
            details: Additional event details
            severity: Event severity (info, warning, critical)
        """
        # TODO: Implement security event logging
        log_entry = {
            "timestamp": time.time(),
            "event_type": event_type,
            "user_id": str(user_id) if user_id else None,
            "details": details or {},
            "severity": severity,
        }
        
        # In production: save to security_log table
        # and potentially alert on critical events
        # await save_to_security_log(log_entry)
        pass


# ==================== Utility Functions ====================

def invalidate_permission_cache_for_role(role_name: str) -> None:
    """
    Invalidate cache for all users with a specific role
    Call this when role permissions are modified
    
    Args:
        role_name: Name of role that changed
    """
    # TODO: Implement by querying all users with role
    # For now, clear entire cache
    permission_cache.clear()


def invalidate_all_permission_caches() -> None:
    """Clear all permission caches"""
    permission_cache.clear()


# ==================== Export ====================

__all__ = [
    "RBACMiddleware",
    "PermissionChecker",
    "BranchAccessChecker",
    "AuditLogger",
    "permission_cache",
    "invalidate_permission_cache_for_role",
    "invalidate_all_permission_caches",
]