"""
Authentication API Endpoints
Handles login, registration, token refresh, and password management
"""

from typing import Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Request, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field, validator

from app.db.base import get_db
from app.services.auth_service import AuthService
from app.schemas.user import UserCreate, UserResponse, PasswordChange
from app.api.deps import (
    get_current_user,
    get_current_active_user,
    get_current_superuser,
)
from app.db.models.user import User


router = APIRouter()


# ==================== Request/Response Schemas ====================

class LoginRequest(BaseModel):
    """Login request schema"""
    username: str = Field(..., min_length=3, max_length=50, description="Username or email")
    password: str = Field(..., min_length=8, max_length=100, description="Password")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "admin",
                "password": "Admin@123"
            }
        }


class LoginResponse(BaseModel):
    """Login response schema"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str = Field(..., description="Refresh token from login")


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    access_token: str
    token_type: str = "bearer"


class PasswordResetRequest(BaseModel):
    """Password reset request schema"""
    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Password reset confirmation schema"""
    token: str
    new_password: str = Field(..., min_length=8)


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str


# ==================== Authentication Endpoints ====================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate user and receive access + refresh tokens",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"}
    }
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login endpoint
    
    **Request Body:**
    - `username`: Username or email
    - `password`: User's password
    
    **Returns:**
    - Access token (valid for 15 minutes)
    - Refresh token (valid for 7 days)
    - User information
    
    **Example:**
    ```json
    {
        "username": "admin",
        "password": "Admin@123"
    }
    ```
    """
    auth_service = AuthService(db)
    
    # Get client IP address for logging
    client_ip = request.client.host if request.client else "unknown"
    
    try:
        user, access_token, refresh_token = await auth_service.authenticate_user(
            username=login_data.username,
            password=login_data.password,
            ip_address=client_ip
        )
        
        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse.model_validate(user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/register",
    response_model=UserResponse,
    summary="Register New User",
    description="Create a new user account (superuser only)",
    status_code=status.HTTP_201_CREATED
)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_superuser)
) -> Any:
    """
    Register a new user (Superuser only)
    
    - **username**: Unique username
    - **email**: Unique email address
    - **password**: Strong password (min 8 chars)
    - **full_name**: User's full name
    - **role_ids**: List of role UUIDs to assign
    """
    auth_service = AuthService(db)
    
    try:
        new_user = await auth_service.register_user(
            user_data=user_data,
            current_user=current_user
        )
        
        return UserResponse.model_validate(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh Access Token",
    description="Get a new access token using refresh token"
)
async def refresh_token(
    token_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token
    
    - **refresh_token**: Valid refresh token from login
    
    Returns a new access token
    """
    auth_service = AuthService(db)
    
    try:
        new_access_token = await auth_service.refresh_access_token(
            refresh_token=token_data.refresh_token
        )
        
        return RefreshTokenResponse(
            access_token=new_access_token
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User Logout",
    description="Logout current user (invalidate token)"
)
async def logout(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout user
    
    Note: In production, this should add token to blacklist in Redis
    """
    return MessageResponse(
        message="Logged out successfully"
    )


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get Current User",
    description="Get currently authenticated user's information"
)
async def get_me(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Get current user information
    
    Returns detailed information about the authenticated user
    including roles and permissions
    """
    return UserResponse.model_validate(current_user)


# ==================== Password Management ====================

@router.post(
    "/change-password",
    response_model=MessageResponse,
    summary="Change Password",
    description="Change current user's password"
)
async def change_password(
    password_data: PasswordChange,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Change password
    
    - **current_password**: Current password for verification
    - **new_password**: New strong password
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.change_password(
            user=current_user,
            current_password=password_data.current_password,
            new_password=password_data.new_password
        )
        
        return MessageResponse(
            message="Password changed successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/request-password-reset",
    response_model=MessageResponse,
    summary="Request Password Reset",
    description="Request a password reset token via email"
)
async def request_password_reset(
    reset_request: PasswordResetRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Request password reset
    
    - **email**: User's email address
    
    Sends a password reset email with a token (valid for 30 minutes)
    """
    from app.core.security import generate_password_reset_token
    
    # Generate token (in production, send via email)
    token = generate_password_reset_token(reset_request.email)
    
    # TODO: Send email with token
    # await send_password_reset_email(reset_request.email, token)
    
    return MessageResponse(
        message=f"Password reset instructions sent to {reset_request.email}"
    )


@router.post(
    "/reset-password",
    response_model=MessageResponse,
    summary="Reset Password",
    description="Reset password using token from email"
)
async def reset_password(
    reset_data: PasswordResetConfirm,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Reset password
    
    - **token**: Password reset token from email
    - **new_password**: New strong password
    """
    auth_service = AuthService(db)
    
    try:
        await auth_service.reset_password(
            token=reset_data.token,
            new_password=reset_data.new_password
        )
        
        return MessageResponse(
            message="Password reset successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Testing Endpoints ====================

@router.get(
    "/test",
    summary="Test Authentication",
    description="Test endpoint to verify authentication is working"
)
async def test_auth(
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Test authentication
    
    Returns user info if authentication is successful
    """
    return {
        "success": True,
        "message": "Authentication working!",
        "user": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "is_superuser": current_user.is_superuser,
            "roles": [role.name for role in current_user.roles]
        }
    }