"""
Authentication Service
Handles user authentication, registration, and session management
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.core.security import (
    get_password_hash,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token_type,
    decode_token,
)
from app.core.config import settings
from app.core.exceptions import (
    InvalidCredentialsError,
    AccountLockedError,
    InvalidTokenError,
    PermissionDeniedError,
)
from app.db.models.user import User
from app.db.models.role import Role
from app.schemas.user import UserCreate


class AuthService:
    """Service class for authentication operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    
    # ==================== Authentication ====================
    
    async def authenticate_user(
        self,
        username: str,
        password: str,
        ip_address: Optional[str] = None
    ) -> tuple[User, str, str]:
        """
        Authenticate user and return user object with tokens
        
        Args:
            username: Username or email
            password: Plain text password
            ip_address: User's IP address (for logging)
            
        Returns:
            tuple: (User object, access_token, refresh_token)
            
        Raises:
            InvalidCredentialsError: If credentials are invalid
            AccountLockedError: If account is locked
        """
        # Get user by username or email
        result = await self.db.execute(
            select(User).where(
                (User.username == username) | (User.email == username)
            )
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidCredentialsError()
        
        # Check if account is locked
        if user.is_locked:
            raise AccountLockedError(
                f"Account locked until {user.locked_until.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        
        # Verify password
        if not verify_password(password, user.hashed_password):
            # Increment failed login attempts
            user.failed_login_attempts += 1
            
            # Lock account after max attempts
            if user.failed_login_attempts >= settings.MAX_LOGIN_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(
                    minutes=settings.ACCOUNT_LOCK_DURATION_MINUTES
                )
            
            await self.db.commit()
            raise InvalidCredentialsError()
        
        # Check if user is active
        if not user.is_active:
            raise InvalidCredentialsError("Account is disabled")
        
        # Successful login - reset failed attempts
        user.failed_login_attempts = 0
        user.last_login = datetime.utcnow()
        user.locked_until = None
        
        await self.db.commit()
        await self.db.refresh(user)
        
        # Create tokens
        token_data = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
        }
        
        access_token = create_access_token(token_data)
        refresh_token = create_refresh_token(token_data)
        
        return user, access_token, refresh_token
    
    
    async def register_user(
        self,
        user_data: UserCreate,
        current_user: Optional[User] = None
    ) -> User:
        """
        Register a new user
        Only superusers can create new users
        
        Args:
            user_data: User creation data
            current_user: The user performing the registration (must be superuser)
            
        Returns:
            User: Created user object
            
        Raises:
            PermissionDeniedError: If current user is not superuser
        """
        # Check permissions
        if current_user and not current_user.is_superuser:
            raise PermissionDeniedError(
                "Only superusers can create new user accounts"
            )
        
        # Check if username exists
        result = await self.db.execute(
            select(User).where(User.username == user_data.username)
        )
        if result.scalar_one_or_none():
            from app.core.exceptions import ResourceAlreadyExistsError
            raise ResourceAlreadyExistsError("User", user_data.username)
        
        # Check if email exists
        result = await self.db.execute(
            select(User).where(User.email == user_data.email)
        )
        if result.scalar_one_or_none():
            from app.core.exceptions import ResourceAlreadyExistsError
            raise ResourceAlreadyExistsError("User", user_data.email)
        
        # Create new user
        new_user = User(
            username=user_data.username.lower(),
            email=user_data.email.lower(),
            hashed_password=get_password_hash(user_data.password),
            full_name=user_data.full_name,
            phone_number=user_data.phone_number,
            is_active=user_data.is_active,
            is_superuser=user_data.is_superuser,
        )
        
        # Assign roles
        if user_data.role_ids:
            result = await self.db.execute(
                select(Role).where(Role.id.in_(user_data.role_ids))
            )
            roles = result.scalars().all()
            new_user.roles.extend(roles)
        
        self.db.add(new_user)
        await self.db.commit()
        await self.db.refresh(new_user)
        
        return new_user
    
    
    async def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token
        
        Args:
            refresh_token: Valid refresh token
            
        Returns:
            str: New access token
            
        Raises:
            InvalidTokenError: If refresh token is invalid
        """
        # Verify it's a refresh token
        payload = verify_token_type(refresh_token, "refresh")
        
        # Get user ID from token
        user_id = payload.get("sub")
        if not user_id:
            raise InvalidTokenError()
        
        # Verify user still exists and is active
        result = await self.db.execute(
            select(User).where(User.id == UUID(user_id))
        )
        user = result.scalar_one_or_none()
        
        if not user or not user.is_active:
            raise InvalidTokenError("User not found or inactive")
        
        # Create new access token
        token_data = {
            "sub": user_id,
            "username": user.username,
            "email": user.email,
        }
        
        return create_access_token(token_data)
    
    
    async def logout_user(
        self,
        token: str,
        user: User
    ) -> bool:
        """
        Logout user (invalidate token)
        
        Args:
            token: Access token to invalidate
            user: Current user
            
        Returns:
            bool: True if successful
            
        Note:
            This is a placeholder. In production, implement token blacklist
            using Redis with token expiration time.
        """
        # TODO: Add token to Redis blacklist
        # Example:
        # await redis_client.setex(
        #     f"blacklist:{token}",
        #     time=token_expiration_seconds,
        #     value="1"
        # )
        
        return True
    
    
    # ==================== Password Management ====================
    
    async def change_password(
        self,
        user: User,
        current_password: str,
        new_password: str
    ) -> bool:
        """
        Change user's password
        
        Args:
            user: Current user
            current_password: Current password for verification
            new_password: New password
            
        Returns:
            bool: True if successful
            
        Raises:
            InvalidCredentialsError: If current password is wrong
        """
        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            raise InvalidCredentialsError("Current password is incorrect")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        
        return True
    
    
    async def reset_password(
        self,
        token: str,
        new_password: str
    ) -> bool:
        """
        Reset password using reset token
        
        Args:
            token: Password reset token
            new_password: New password
            
        Returns:
            bool: True if successful
            
        Raises:
            InvalidTokenError: If token is invalid or expired
        """
        from app.core.security import verify_password_reset_token
        
        # Verify token and get email
        email = verify_password_reset_token(token)
        if not email:
            raise InvalidTokenError("Invalid or expired reset token")
        
        # Get user by email
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            raise InvalidTokenError("User not found")
        
        # Update password
        user.hashed_password = get_password_hash(new_password)
        await self.db.commit()
        
        return True
    
    
    # ==================== Permissions ====================
    
    async def check_user_permissions(
        self,
        user: User,
        required_permissions: List[str]
    ) -> bool:
        """
        Check if user has all required permissions
        
        Args:
            user: User to check
            required_permissions: List of required permission strings
            
        Returns:
            bool: True if user has all permissions
        """
        # Superuser has all permissions
        if user.is_superuser:
            return True
        
        # Check each required permission
        for permission in required_permissions:
            if not user.has_permission(permission):
                return False
        
        return True
    
    
    async def check_user_has_role(
        self,
        user: User,
        role_names: List[str]
    ) -> bool:
        """
        Check if user has any of the specified roles
        
        Args:
            user: User to check
            role_names: List of role names
            
        Returns:
            bool: True if user has at least one of the roles
        """
        # Superuser passes all role checks
        if user.is_superuser:
            return True
        
        # Check if user has any of the required roles
        for role_name in role_names:
            if user.has_role(role_name):
                return True
        
        return False
    
    
    # ==================== Account Management ====================
    
    async def unlock_account(self, user_id: UUID) -> bool:
        """
        Manually unlock a user account
        
        Args:
            user_id: User ID to unlock
            
        Returns:
            bool: True if successful
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError("User", user_id)
        
        user.failed_login_attempts = 0
        user.locked_until = None
        
        await self.db.commit()
        return True
    
    
    async def deactivate_account(self, user_id: UUID) -> bool:
        """
        Deactivate a user account
        
        Args:
            user_id: User ID to deactivate
            
        Returns:
            bool: True if successful
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            from app.core.exceptions import ResourceNotFoundError
            raise ResourceNotFoundError("User", user_id)
        
        user.is_active = False
        await self.db.commit()
        
        return True
    
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User UUID
            
        Returns:
            User: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username
        
        Args:
            username: Username
            
        Returns:
            User: User object or None
        """
        result = await self.db.execute(
            select(User).where(User.username == username)
        )
        return result.scalar_one_or_none()