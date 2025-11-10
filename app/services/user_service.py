"""
User Service - Core Business Logic
===================================
Comprehensive user management operations:
- User CRUD operations (create, read, update, delete)
- User authentication and password management
- Role assignment and management
- Branch assignment (primary and additional branches)
- User search and filtering
- User activation/deactivation

Features:
- Email and username uniqueness validation
- Secure password hashing
- Role-based access control integration
- Multi-branch user support
- Comprehensive error handling
- Complete audit trail

Business Rules:
1. Email must be unique (case-insensitive)
2. Username must be unique
3. Password must meet security requirements
4. Users can have multiple roles
5. Users can be assigned to multiple branches
6. Superuser flag grants all permissions
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models.user import User
from app.db.models.role import Role
from app.core.security import get_password_hash, verify_password
from app.core.exceptions import (
    ValidationError,
    ResourceNotFoundError,
    BusinessRuleViolationError,
    DatabaseOperationError,
    AuthenticationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserService:
    """Service for user management operations"""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== User CRUD Operations ====================

    async def create_user(
        self,
        user_data: Dict[str, Any],
        current_user: Optional[User] = None
    ) -> User:
        """
        Create new user with validation and role assignment

        Steps:
        1. Validate required fields (email, username, password)
        2. Check for existing email/username
        3. Hash password
        4. Create user record
        5. Assign roles if provided
        6. Commit transaction

        Args:
            user_data: Dictionary containing user data:
                - email (required): User's email address
                - username (required): Unique username
                - password (required): Plain text password (will be hashed)
                - full_name (optional): User's full name
                - phone (optional): Phone number
                - is_active (optional): Active status (default: True)
                - is_superuser (optional): Superuser flag (default: False)
                - primary_branch_id (optional): Primary branch UUID
                - role_ids (optional): List of role UUIDs to assign
            current_user: User performing the operation (for audit trail)

        Returns:
            Created User object with assigned roles

        Raises:
            ValidationError: If required fields missing or user exists
            DatabaseOperationError: If user creation fails
        """
        logger.info(f"Creating user {user_data.get('email')}")

        # Validate required fields
        email = user_data.get('email', '').strip().lower()
        username = user_data.get('username', '').strip()
        password = user_data.get('password')

        if not email or not username or not password:
            raise ValidationError("Email, username, and password are required")

        # Check if email or username already exists
        existing_user = await self._get_user_by_email_or_username(email, username)
        if existing_user:
            raise ValidationError("Email or username already exists")

        try:
            # Hash password
            hashed_password = get_password_hash(password)

            # Create user
            new_user = User(
                email=email,
                username=username,
                hashed_password=hashed_password,
                full_name=user_data.get('full_name', ''),
                phone=user_data.get('phone'),
                is_active=user_data.get('is_active', True),
                is_superuser=user_data.get('is_superuser', False),
                primary_branch_id=user_data.get('primary_branch_id')
            )

            self.db.add(new_user)
            await self.db.flush()

            # Assign roles
            role_ids = user_data.get('role_ids', [])
            if role_ids:
                await self._assign_roles(new_user, role_ids)

            await self.db.commit()
            await self.db.refresh(new_user)

            logger.info(f"User {new_user.email} created successfully")
            return new_user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise DatabaseOperationError(f"User creation failed: {str(e)}")

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by UUID

        Args:
            user_id: User's unique identifier

        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.id == user_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address (case-insensitive)

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.email == email.lower())
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_user_by_username(self, username: str) -> Optional[User]:
        """
        Get user by username

        Args:
            username: User's unique username

        Returns:
            User object if found, None otherwise
        """
        query = select(User).where(User.username == username)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def list_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        branch_id: Optional[UUID] = None
    ) -> List[User]:
        """List users with filters and search"""
        query = select(User)

        # Apply search filter
        if search:
            search_term = f"%{search.lower()}%"
            query = query.where(
                (User.full_name.ilike(search_term)) |
                (User.email.ilike(search_term)) |
                (User.username.ilike(search_term))
            )

        # Apply other filters
        if is_active is not None:
            query = query.where(User.is_active == is_active)
        if branch_id:
            query = query.where(User.primary_branch_id == branch_id)

        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_user(
        self,
        user_id: UUID,
        user_data: Dict[str, Any],
        current_user: User
    ) -> User:
        """Update user information"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            # Update allowed fields
            if 'full_name' in user_data:
                user.full_name = user_data['full_name']
            if 'phone' in user_data:
                user.phone = user_data['phone']
            if 'is_active' in user_data:
                user.is_active = user_data['is_active']
            if 'primary_branch_id' in user_data:
                user.primary_branch_id = user_data['primary_branch_id']

            # Update roles if provided
            if 'role_ids' in user_data:
                await self._assign_roles(user, user_data['role_ids'])

            await self.db.commit()
            await self.db.refresh(user)

            logger.info(f"User {user.email} updated successfully")
            return user

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            raise DatabaseOperationError(f"User update failed: {str(e)}")

    async def change_password(
        self,
        user_id: UUID,
        old_password: str,
        new_password: str
    ) -> None:
        """Change user password"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        # Verify old password
        if not verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Incorrect password")

        try:
            user.hashed_password = get_password_hash(new_password)
            await self.db.commit()
            logger.info(f"Password changed for user {user.email}")

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to change password: {str(e)}")
            raise DatabaseOperationError(f"Password change failed: {str(e)}")

    async def deactivate_user(self, user_id: UUID) -> None:
        """Deactivate user account"""
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            user.is_active = False
            await self.db.commit()
            logger.info(f"User {user.email} deactivated")

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to deactivate user: {str(e)}")
            raise DatabaseOperationError(f"User deactivation failed: {str(e)}")

    async def admin_reset_password(
        self,
        user_id: UUID,
        new_password: str,
        admin_user: User
    ) -> None:
        """
        Reset user password by admin (no current password required)

        Args:
            user_id: ID of user whose password to reset
            new_password: New password to set
            admin_user: Admin user performing the operation

        Raises:
            ResourceNotFoundError: If user not found
            DatabaseOperationError: If operation fails
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            user.hashed_password = get_password_hash(new_password)
            await self.db.commit()
            logger.info(
                f"Password reset for user {user.email} by admin {admin_user.email}"
            )

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to reset password: {str(e)}")
            raise DatabaseOperationError(f"Password reset failed: {str(e)}")

    async def delete_user(
        self,
        user_id: UUID,
        current_user: User
    ) -> None:
        """
        Permanently delete a user

        Args:
            user_id: ID of user to delete
            current_user: User performing the operation

        Raises:
            ResourceNotFoundError: If user not found
            BusinessRuleViolationError: If trying to delete self
            DatabaseOperationError: If operation fails
        """
        # Prevent self-deletion
        if user_id == current_user.id:
            raise BusinessRuleViolationError("Cannot delete your own account")

        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError(f"User {user_id} not found")

        try:
            user_email = user.email
            await self.db.delete(user)
            await self.db.commit()
            logger.info(
                f"User {user_email} permanently deleted by {current_user.email}"
            )

        except SQLAlchemyError as e:
            await self.db.rollback()
            logger.error(f"Failed to delete user: {str(e)}")
            raise DatabaseOperationError(
                f"User deletion failed. This may be due to foreign key constraints. "
                f"Consider deactivating the user instead. Error: {str(e)}"
            )

    async def bulk_create_users(
        self,
        users_data: List[Dict[str, Any]],
        current_user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        Create multiple users in bulk

        Args:
            users_data: List of user creation data
            current_user: User performing the operation

        Returns:
            Dictionary with results: total, successful, failed, errors
        """
        logger.info(f"Bulk creating {len(users_data)} users")

        results = {
            "total": len(users_data),
            "successful": 0,
            "failed": 0,
            "errors": [],
            "created_users": []
        }

        for idx, user_data in enumerate(users_data):
            try:
                # Create user
                user = await self.create_user(user_data, current_user)
                results["successful"] += 1
                results["created_users"].append({
                    "index": idx,
                    "email": user.email,
                    "id": str(user.id)
                })

            except (ValidationError, DatabaseOperationError) as e:
                results["failed"] += 1
                results["errors"].append({
                    "index": idx,
                    "email": user_data.get("email", "unknown"),
                    "error": str(e)
                })
                logger.warning(f"Failed to create user at index {idx}: {str(e)}")
                continue

        logger.info(
            f"Bulk user creation completed: "
            f"{results['successful']} successful, {results['failed']} failed"
        )

        return results

    # ==================== Role Management ====================

    async def _assign_roles(self, user: User, role_ids: List[UUID]) -> None:
        """Assign roles to user"""
        # Clear existing roles
        user.roles.clear()

        # Add new roles
        for role_id in role_ids:
            role = await self._get_role_by_id(role_id)
            if role:
                user.roles.append(role)

    async def _get_role_by_id(self, role_id: UUID) -> Optional[Role]:
        """Get role by ID"""
        query = select(Role).where(Role.id == role_id)
        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== Helper Methods ====================

    async def _get_user_by_email_or_username(
        self, email: str, username: str
    ) -> Optional[User]:
        """Check if user with email or username exists"""
        query = select(User).where(
            (User.email == email) | (User.username == username)
        )
        result = await self.db.execute(query)
        return result.scalar_one_or_none()
