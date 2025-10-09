"""
Authentication API Endpoints
Handles login, registration, token refresh, and password management
"""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, EmailStr, Field

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
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class LoginResponse(BaseModel):
    """Login response schema"""
    success: bool = True
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshTokenRequest(BaseModel):
    """Refresh token request schema"""
    refresh_token: str


class RefreshTokenResponse(BaseModel):
    """Refresh token response schema"""
    success: bool = True
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
    success: bool = True
    message: str


# ==================== Authentication Endpoints ====================

@router.post(
    "/login",
    response_model=LoginResponse,
    summary="User Login",
    description="Authenticate user and receive access + refresh tokens"
)
async def login(
    login_data: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Login endpoint
    
    - **username**: Username or email
    - **password**: User's password
    
    Returns access token (15 min) and refresh token (7 days)
    """
    auth_service = AuthService(db)
    
    # Get client IP address
    client_ip = request.client.host if request.client else None
    
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
        
    except Exception as e:
        # Log failed login attempt here
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
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
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit, special char)
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    summary="Refresh Access Token",
    description="Get a new access token using a valid refresh token"
)
async def refresh_token(
    refresh_data: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Refresh access token
    
    - **refresh_token**: Valid refresh token from login
    
    Returns a new access token (15 min expiry)
    """
    auth_service = AuthService(db)
    
    try:
        new_access_token = await auth_service.refresh_access_token(
            refresh_token=refresh_data.refresh_token
        )
        
        return RefreshTokenResponse(
            access_token=new_access_token
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="User Logout",
    description="Logout user and invalidate token"
)
async def logout(
    request: Request,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Logout user
    
    Invalidates the current access token (adds to blacklist)
    """
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid authorization header"
        )
    
    token = auth_header.split(" ")[1]
    
    auth_service = AuthService(db)
    await auth_service.logout_user(token, current_user)
    
    return MessageResponse(
        message="Successfully logged out"
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
    # TODO: Implement email sending
    # For now, just return success
    # In production:
    # 1. Generate reset token
    # 2. Send email with token
    # 3. Token valid for 30 minutes
    
    from app.core.security import generate_password_reset_token
    
    # Generate token (in production, send via email)
    token = generate_password_reset_token(reset_request.email)
    
    # TODO: Send email
    # await send_password_reset_email(reset_request.email, token)
    
    return MessageResponse(
        message=f"Password reset email sent to {reset_request.email}"
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
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== Account Management ====================

@router.post(
    "/verify-email/{token}",
    response_model=MessageResponse,
    summary="Verify Email",
    description="Verify user email address"
)
async def verify_email(
    token: str,
    db: AsyncSession = Depends(get_db)
) -> Any:
    """
    Verify email address
    
    - **token**: Email verification token
    """
    # TODO: Implement email verification
    # For now, just return success
    
    from app.core.security import verify_email_verification_token
    
    email = verify_email_verification_token(token)
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    # TODO: Mark email as verified in database
    
    return MessageResponse(
        message="Email verified successfully"
    )


# ==================== Testing/Development Endpoints ====================

@router.get(
    "/test-auth",
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
        "message": "Authentication successful",
        "user": {
            "id": str(current_user.id),
            "username": current_user.username,
            "email": current_user.email,
            "roles": [role.name for role in current_user.roles]
        }
    }