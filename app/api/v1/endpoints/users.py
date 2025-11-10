"""
User Management API Endpoints
==============================
Complete user management endpoints:
- User CRUD operations (create, read, update, delete)
- User search and listing with filters
- Password management (change, reset)
- Role assignment and management
- Branch assignment (primary and additional)
- User activation/deactivation
- Bulk operations

Features:
- Email and username uniqueness validation
- Secure password handling
- Role-based access control
- Multi-branch user support
- Search by email, username, or name
- Pagination support
- Permission-based access control

Permissions:
- user:create - Create new users
- user:read - View user details
- user:update - Update user information
- user:delete - Delete users
- user:manage_roles - Assign/remove roles
- user:reset_password - Reset user passwords (admin)
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_async_db as get_db
from app.db.models.user import User
from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
    require_permission
)
from app.services.user_service import UserService
from app.schemas.user import (
    UserCreate,
    UserUpdate,
    UserResponse,
    PasswordChange,
    AdminPasswordReset
)
from app.schemas.common import BulkOperationResponse
from app.core.exceptions import (
    ResourceNotFoundError,
    ValidationError,
    AuthenticationError,
    BusinessRuleViolationError
)
from app.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter()


# ==================== User CRUD ====================

@router.post(
    "",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create New User",
    dependencies=[Depends(require_permission("user:create"))]
)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new user account

    **Required Fields:**
    - email
    - username
    - password
    - full_name

    **Permissions:** user:create
    """
    try:
        logger.info(f"Creating user {user_data.email} by {current_user.email}")

        service = UserService(db)
        user = await service.create_user(
            user_data=user_data.dict(exclude_unset=True),
            current_user=current_user
        )

        logger.info(f"User {user.email} created successfully")
        return user

    except ValidationError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user"
        )


@router.get(
    "",
    response_model=List[UserResponse],
    summary="List Users",
    dependencies=[Depends(require_permission("user:read"))]
)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None, description="Search by name, email, or username"),
    is_active: Optional[bool] = Query(None),
    branch_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all users with optional filters and search

    **Search:** Search in full_name, email, and username fields

    **Filters:**
    - is_active: Filter by active status
    - branch_id: Filter by primary branch

    **Permissions:** user:read
    """
    try:
        service = UserService(db)
        users = await service.list_users(
            skip=skip,
            limit=limit,
            search=search,
            is_active=is_active,
            branch_id=branch_id
        )

        return users

    except Exception as e:
        logger.error(f"Error listing users: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list users"
        )


@router.post(
    "/bulk",
    response_model=BulkOperationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Create Users",
    dependencies=[Depends(require_permission("user:create"))]
)
async def bulk_create_users(
    users: List[UserCreate],
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create multiple users in a single request

    **Required Fields for each user:**
    - email
    - username
    - password
    - full_name

    **Response:**
    Returns summary of successful and failed creations with error details

    **Permissions:** user:create

    **Example Request:**
    ```json
    [
      {
        "email": "user1@example.com",
        "username": "user1",
        "password": "SecurePass123!",
        "full_name": "User One",
        "phone_number": "+966501234567",
        "role_ids": []
      },
      {
        "email": "user2@example.com",
        "username": "user2",
        "password": "SecurePass456!",
        "full_name": "User Two",
        "phone_number": "+966501234568",
        "role_ids": []
      }
    ]
    ```
    """
    try:
        if not users:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Users list cannot be empty"
            )

        if len(users) > 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot create more than 100 users at once"
            )

        logger.info(f"Bulk creating {len(users)} users by {current_user.email}")

        service = UserService(db)
        users_data = [user.dict(exclude_unset=True) for user in users]
        results = await service.bulk_create_users(users_data, current_user)

        logger.info(
            f"Bulk user creation completed: "
            f"{results['successful']} successful, {results['failed']} failed"
        )

        return BulkOperationResponse(
            total=results["total"],
            successful=results["successful"],
            failed=results["failed"],
            errors=results["errors"]
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in bulk user creation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to bulk create users"
        )


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Get User by ID",
    dependencies=[Depends(require_permission("user:read"))]
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get user details by ID

    **Permissions:** user:read
    """
    try:
        service = UserService(db)
        user = await service.get_user_by_id(user_id)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User {user_id} not found"
            )

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user"
        )


@router.put(
    "/{user_id}",
    response_model=UserResponse,
    summary="Update User",
    dependencies=[Depends(require_permission("user:update"))]
)
async def update_user(
    user_id: UUID,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update user information

    **Updatable Fields:**
    - full_name
    - phone
    - is_active
    - primary_branch_id
    - role_ids

    **Permissions:** user:update
    """
    try:
        service = UserService(db)
        user = await service.update_user(
            user_id=user_id,
            user_data=user_data.dict(exclude_unset=True),
            current_user=current_user
        )

        logger.info(f"User {user.email} updated by {current_user.email}")
        return user

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update user"
        )


@router.post(
    "/{user_id}/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change Password"
)
async def change_password(
    user_id: UUID,
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Change user password

    **Note:** Users can only change their own password unless they are superuser
    """
    # Check if user is changing their own password or is superuser
    if user_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only change your own password"
        )

    try:
        service = UserService(db)
        await service.change_password(
            user_id=user_id,
            old_password=password_data.old_password,
            new_password=password_data.new_password
        )

        return {"message": "Password changed successfully"}

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error changing password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to change password"
        )


@router.post(
    "/{user_id}/deactivate",
    status_code=status.HTTP_200_OK,
    summary="Deactivate User",
    dependencies=[Depends(require_permission("user:delete"))]
)
async def deactivate_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate user account

    **Permissions:** user:delete
    """
    try:
        service = UserService(db)
        await service.deactivate_user(user_id)

        logger.info(f"User {user_id} deactivated by {current_user.email}")
        return {"message": "User deactivated successfully"}

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deactivating user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )


@router.post(
    "/{user_id}/admin-reset-password",
    status_code=status.HTTP_200_OK,
    summary="Admin Reset User Password",
    dependencies=[Depends(get_current_superuser)]
)
async def admin_reset_password(
    user_id: UUID,
    password_data: AdminPasswordReset,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
):
    """
    Reset user password by admin (no current password required)

    **Note:** This endpoint bypasses the current password requirement.
    Only superusers can access this endpoint.

    **Required Fields:**
    - new_password (must meet password strength requirements)

    **Permissions:** Superuser only
    """
    try:
        service = UserService(db)
        await service.admin_reset_password(
            user_id=user_id,
            new_password=password_data.new_password,
            admin_user=current_user
        )

        logger.info(
            f"Password reset for user {user_id} by admin {current_user.email}"
        )
        return {"message": "Password reset successfully"}

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error resetting password: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reset password"
        )


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete User",
    dependencies=[Depends(require_permission("user:delete"))]
)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Permanently delete a user

    **Warning:** This is a permanent deletion and cannot be undone.
    Consider using the deactivate endpoint instead for soft deletion.

    **Note:**
    - Cannot delete your own account
    - May fail if user has related records due to foreign key constraints
    - In such cases, deactivate the user instead

    **Permissions:** user:delete
    """
    try:
        service = UserService(db)
        await service.delete_user(
            user_id=user_id,
            current_user=current_user
        )

        logger.info(f"User {user_id} deleted by {current_user.email}")
        return {"message": "User deleted successfully"}

    except ResourceNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except BusinessRuleViolationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting user: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User"
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current authenticated user information

    **No special permissions required** - returns current user's own data
    """
    return current_user
