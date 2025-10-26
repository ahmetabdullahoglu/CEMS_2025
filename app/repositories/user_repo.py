"""
User Repository
Data access layer for user operations
"""

from typing import List, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import select, and_, or_, update, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from app.db.models.user import User, user_branches, user_roles
from app.db.models.branch import Branch
from app.db.models.role import Role
from app.core.exceptions import (
    ResourceNotFoundError,
    DatabaseOperationError,
    ValidationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)


class UserRepository:
    """Repository for user data access"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Basic User Operations ====================
    
    async def get_user_by_id(
        self,
        user_id: UUID,
        include_roles: bool = False,
        include_branches: bool = False
    ) -> Optional[User]:
        """
        Get user by ID
        
        Args:
            user_id: User UUID
            include_roles: Include role relationships
            include_branches: Include branch relationships
            
        Returns:
            User object or None
        """
        stmt = select(User).where(User.id == user_id)
        
        if include_roles:
            stmt = stmt.options(selectinload(User.roles))
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        stmt = select(User).where(User.username == username)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        stmt = select(User).where(User.email == email)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_all_users(
        self,
        is_active: Optional[bool] = None,
        include_roles: bool = False
    ) -> List[User]:
        """
        Get all users with optional filtering
        
        Args:
            is_active: Filter by active status
            include_roles: Include role relationships
            
        Returns:
            List of User objects
        """
        stmt = select(User)
        
        if is_active is not None:
            stmt = stmt.where(User.is_active == is_active)
        
        if include_roles:
            stmt = stmt.options(selectinload(User.roles))
        
        stmt = stmt.order_by(User.username)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    # ==================== Branch-User Relationships ====================
    
    async def get_branch_users(self, branch_id: UUID) -> List[User]:
        """
        Get all users assigned to a specific branch
        
        Args:
            branch_id: Branch UUID
            
        Returns:
            List of User objects assigned to the branch
        """
        stmt = select(User).join(
            user_branches,
            User.id == user_branches.c.user_id
        ).where(
            and_(
                user_branches.c.branch_id == branch_id,
                User.is_active == True
            )
        ).options(
            selectinload(User.roles)
        ).order_by(User.username)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_branches(self, user_id: UUID) -> List[Branch]:
        """
        Get all branches assigned to a user
        
        Args:
            user_id: User UUID
            
        Returns:
            List of Branch objects
        """
        stmt = select(Branch).join(
            user_branches,
            Branch.id == user_branches.c.branch_id
        ).where(
            and_(
                user_branches.c.user_id == user_id,
                Branch.is_active == True
            )
        ).order_by(Branch.code)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def get_user_primary_branch(self, user_id: UUID) -> Optional[Branch]:
        """
        Get user's primary branch
        
        Args:
            user_id: User UUID
            
        Returns:
            Primary Branch object or None
        """
        stmt = select(Branch).join(
            user_branches,
            Branch.id == user_branches.c.branch_id
        ).where(
            and_(
                user_branches.c.user_id == user_id,
                user_branches.c.is_primary == True,
                Branch.is_active == True
            )
        )
        
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
    
    async def assign_user_to_branch(
        self,
        user_id: UUID,
        branch_id: UUID,
        is_primary: bool = False,
        assigned_by: Optional[UUID] = None
    ) -> bool:
        """
        Assign a user to a branch
        
        Args:
            user_id: User UUID
            branch_id: Branch UUID
            is_primary: Whether this is the primary branch
            assigned_by: UUID of user making the assignment
            
        Returns:
            True if successful
        """
        # If this is primary, unset other primary branches for this user
        if is_primary:
            stmt = update(user_branches).where(
                user_branches.c.user_id == user_id
            ).values(is_primary=False)
            await self.db.execute(stmt)
        
        # Insert new assignment
        stmt = user_branches.insert().values(
            user_id=user_id,
            branch_id=branch_id,
            is_primary=is_primary,
            assigned_by=assigned_by
        )
        
        try:
            await self.db.execute(stmt)
            await self.db.flush()
            logger.info(f"User {user_id} assigned to branch {branch_id}")
            return True
        except IntegrityError as e:
            logger.error(f"Failed to assign user to branch: {str(e)}")
            # Assignment might already exist, which is okay
            return False
    
    async def remove_user_from_branch(
        self,
        user_id: UUID,
        branch_id: UUID
    ) -> bool:
        """
        Remove user from branch
        
        Args:
            user_id: User UUID
            branch_id: Branch UUID
            
        Returns:
            True if successful
        """
        stmt = delete(user_branches).where(
            and_(
                user_branches.c.user_id == user_id,
                user_branches.c.branch_id == branch_id
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        logger.info(f"User {user_id} removed from branch {branch_id}")
        return result.rowcount > 0
    
    # ==================== Role Management ====================
    
    async def get_user_roles(self, user_id: UUID) -> List[Role]:
        """Get all roles for a user"""
        user = await self.get_user_by_id(user_id, include_roles=True)
        return user.roles if user else []
    
    async def assign_role_to_user(
        self,
        user_id: UUID,
        role_id: UUID,
        assigned_by: Optional[UUID] = None
    ) -> bool:
        """
        Assign a role to user
        
        Args:
            user_id: User UUID
            role_id: Role UUID
            assigned_by: UUID of user making the assignment
            
        Returns:
            True if successful
        """
        stmt = user_roles.insert().values(
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by
        )
        
        try:
            await self.db.execute(stmt)
            await self.db.flush()
            logger.info(f"Role {role_id} assigned to user {user_id}")
            return True
        except IntegrityError as e:
            logger.error(f"Failed to assign role to user: {str(e)}")
            return False
    
    async def remove_role_from_user(
        self,
        user_id: UUID,
        role_id: UUID
    ) -> bool:
        """Remove role from user"""
        stmt = delete(user_roles).where(
            and_(
                user_roles.c.user_id == user_id,
                user_roles.c.role_id == role_id
            )
        )
        
        result = await self.db.execute(stmt)
        await self.db.flush()
        
        logger.info(f"Role {role_id} removed from user {user_id}")
        return result.rowcount > 0
    
    # ==================== User CRUD ====================
    
    async def create_user(self, user_data: Dict[str, Any]) -> User:
        """
        Create new user
        
        Args:
            user_data: User creation data
            
        Returns:
            Created User object
        """
        try:
            user = User(**user_data)
            self.db.add(user)
            await self.db.flush()
            await self.db.refresh(user)
            
            logger.info(f"User {user.username} created successfully")
            return user
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to create user: {str(e)}")
            raise DatabaseOperationError(f"User creation failed: {str(e)}")
    
    async def update_user(
        self,
        user_id: UUID,
        update_data: Dict[str, Any]
    ) -> User:
        """
        Update user
        
        Args:
            user_id: User UUID
            update_data: Update data
            
        Returns:
            Updated User object
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)
        
        try:
            for key, value in update_data.items():
                setattr(user, key, value)
            
            await self.db.flush()
            await self.db.refresh(user)
            
            logger.info(f"User {user.username} updated successfully")
            return user
        except IntegrityError as e:
            await self.db.rollback()
            logger.error(f"Failed to update user: {str(e)}")
            raise DatabaseOperationError(f"User update failed: {str(e)}")
    
    async def delete_user(self, user_id: UUID) -> bool:
        """
        Soft delete user (set is_active = False)
        
        Args:
            user_id: User UUID
            
        Returns:
            True if successful
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            raise ResourceNotFoundError("User", user_id)
        
        user.is_active = False
        await self.db.flush()
        
        logger.info(f"User {user.username} deactivated successfully")
        return True
    
    # ==================== Statistics & Queries ====================
    
    async def count_active_users(self) -> int:
        """Count active users"""
        stmt = select(User).where(User.is_active == True)
        result = await self.db.execute(stmt)
        return len(result.scalars().all())
    
    async def get_users_by_role(self, role_name: str) -> List[User]:
        """Get all users with a specific role"""
        stmt = select(User).join(
            user_roles,
            User.id == user_roles.c.user_id
        ).join(
            Role,
            Role.id == user_roles.c.role_id
        ).where(
            and_(
                Role.name == role_name,
                User.is_active == True
            )
        ).options(
            selectinload(User.roles)
        ).order_by(User.username)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()
    
    async def search_users(
        self,
        query: str,
        limit: int = 20
    ) -> List[User]:
        """
        Search users by username, email, or full name
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            List of matching User objects
        """
        search_pattern = f"%{query}%"
        
        stmt = select(User).where(
            and_(
                User.is_active == True,
                or_(
                    User.username.ilike(search_pattern),
                    User.email.ilike(search_pattern),
                    User.full_name.ilike(search_pattern)
                )
            )
        ).limit(limit).order_by(User.username)
        
        result = await self.db.execute(stmt)
        return result.scalars().all()