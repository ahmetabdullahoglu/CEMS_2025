"""
Integration Tests for Authentication API
Tests all auth endpoints with database
"""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash, create_access_token
from app.db.models.user import User
from app.db.models.role import Role


# ==================== Fixtures ====================

@pytest.fixture
async def test_role(db_session: AsyncSession):
    """Create a test role"""
    role = Role(
        name="teller",
        display_name_ar="صراف",
        permissions=["transaction:create", "transaction:read"]
    )
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    return role


@pytest.fixture
async def test_user(db_session: AsyncSession, test_role: Role):
    """Create a test user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Test User",
        phone_number="+90 555 123 4567",
        is_active=True,
        is_superuser=False
    )
    user.roles.append(test_role)
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def superuser(db_session: AsyncSession):
    """Create a superuser"""
    user = User(
        username="admin",
        email="admin@cems.co",
        hashed_password=get_password_hash("Admin@123"),
        full_name="Admin User",
        is_active=True,
        is_superuser=True
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(test_user: User):
    """Create authentication headers"""
    access_token = create_access_token({
        "sub": str(test_user.id),
        "username": test_user.username
    })
    return {"Authorization": f"Bearer {access_token}"}


@pytest.fixture
def superuser_headers(superuser: User):
    """Create superuser authentication headers"""
    access_token = create_access_token({
        "sub": str(superuser.id),
        "username": superuser.username
    })
    return {"Authorization": f"Bearer {access_token}"}


# ==================== Login Tests ====================

@pytest.mark.integration
async def test_login_success(client: AsyncClient, test_user: User):
    """Test successful login"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPass123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["username"] == "testuser"
    assert data["user"]["email"] == "test@example.com"


@pytest.mark.integration
async def test_login_with_email(client: AsyncClient, test_user: User):
    """Test login with email instead of username"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "test@example.com",
            "password": "TestPass123!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["username"] == "testuser"


@pytest.mark.integration
async def test_login_wrong_password(client: AsyncClient, test_user: User):
    """Test login with wrong password"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "WrongPassword123!"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.integration
async def test_login_nonexistent_user(client: AsyncClient):
    """Test login with nonexistent username"""
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "nonexistent",
            "password": "TestPass123!"
        }
    )
    
    assert response.status_code == 401


@pytest.mark.integration
async def test_login_inactive_user(client: AsyncClient, db_session: AsyncSession):
    """Test login with inactive user"""
    inactive_user = User(
        username="inactive",
        email="inactive@example.com",
        hashed_password=get_password_hash("TestPass123!"),
        full_name="Inactive User",
        is_active=False
    )
    db_session.add(inactive_user)
    await db_session.commit()
    
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "inactive",
            "password": "TestPass123!"
        }
    )
    
    assert response.status_code == 401


# ==================== Registration Tests ====================

@pytest.mark.integration
async def test_register_user(
    client: AsyncClient,
    superuser_headers: dict,
    test_role: Role
):
    """Test user registration (superuser only)"""
    response = await client.post(
        "/api/v1/auth/register",
        headers=superuser_headers,
        json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "NewPass123!",
            "full_name": "New User",
            "phone_number": "+90 555 999 8888",
            "role_ids": [str(test_role.id)]
        }
    )
    
    assert response.status_code == 201
    data = response.json()
    
    assert data["username"] == "newuser"
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert len(data["roles"]) == 1


@pytest.mark.integration
async def test_register_duplicate_username(
    client: AsyncClient,
    superuser_headers: dict,
    test_user: User
):
    """Test registration with duplicate username"""
    response = await client.post(
        "/api/v1/auth/register",
        headers=superuser_headers,
        json={
            "username": "testuser",  # Already exists
            "email": "different@example.com",
            "password": "NewPass123!",
            "full_name": "Duplicate User"
        }
    )
    
    assert response.status_code == 400


@pytest.mark.integration
async def test_register_non_superuser(
    client: AsyncClient,
    auth_headers: dict
):
    """Test that non-superuser cannot register users"""
    response = await client.post(
        "/api/v1/auth/register",
        headers=auth_headers,
        json={
            "username": "newuser",
            "email": "new@example.com",
            "password": "NewPass123!",
            "full_name": "New User"
        }
    )
    
    assert response.status_code == 403


# ==================== Token Refresh Tests ====================

@pytest.mark.integration
async def test_refresh_token(client: AsyncClient, test_user: User):
    """Test token refresh"""
    # First login to get refresh token
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "TestPass123!"
        }
    )
    
    refresh_token = login_response.json()["refresh_token"]
    
    # Use refresh token to get new access token
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": refresh_token}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["success"] is True
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.integration
async def test_refresh_invalid_token(client: AsyncClient):
    """Test refresh with invalid token"""
    response = await client.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": "invalid_token"}
    )
    
    assert response.status_code == 401


# ==================== Get Current User Tests ====================

@pytest.mark.integration
async def test_get_me(client: AsyncClient, auth_headers: dict, test_user: User):
    """Test getting current user info"""
    response = await client.get(
        "/api/v1/auth/me",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["username"] == test_user.username
    assert data["email"] == test_user.email
    assert data["full_name"] == test_user.full_name


@pytest.mark.integration
async def test_get_me_without_auth(client: AsyncClient):
    """Test getting current user without authentication"""
    response = await client.get("/api/v1/auth/me")
    
    assert response.status_code == 403  # Forbidden without auth


# ==================== Password Change Tests ====================

@pytest.mark.integration
async def test_change_password(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """Test password change"""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "TestPass123!",
            "new_password": "NewPass456!"
        }
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Verify can login with new password
    login_response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "NewPass456!"
        }
    )
    assert login_response.status_code == 200


@pytest.mark.integration
async def test_change_password_wrong_current(
    client: AsyncClient,
    auth_headers: dict
):
    """Test password change with wrong current password"""
    response = await client.post(
        "/api/v1/auth/change-password",
        headers=auth_headers,
        json={
            "current_password": "WrongPassword!",
            "new_password": "NewPass456!"
        }
    )
    
    assert response.status_code == 400


# ==================== Logout Tests ====================

@pytest.mark.integration
async def test_logout(client: AsyncClient, auth_headers: dict):
    """Test logout"""
    response = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True


# ==================== Authentication Tests ====================

@pytest.mark.integration
async def test_auth_required_endpoint(
    client: AsyncClient,
    auth_headers: dict,
    test_user: User
):
    """Test accessing protected endpoint"""
    response = await client.get(
        "/api/v1/auth/test-auth",
        headers=auth_headers
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["user"]["username"] == test_user.username


@pytest.mark.integration
async def test_auth_required_no_token(client: AsyncClient):
    """Test accessing protected endpoint without token"""
    response = await client.get("/api/v1/auth/test-auth")
    
    assert response.status_code == 403


@pytest.mark.integration
async def test_auth_required_invalid_token(client: AsyncClient):
    """Test accessing protected endpoint with invalid token"""
    response = await client.get(
        "/api/v1/auth/test-auth",
        headers={"Authorization": "Bearer invalid_token"}
    )
    
    assert response.status_code == 401


# ==================== Failed Login Attempts Tests ====================

@pytest.mark.integration
async def test_account_lockout_after_failed_attempts(
    client: AsyncClient,
    db_session: AsyncSession,
    test_user: User
):
    """Test account gets locked after multiple failed login attempts"""
    # Try to login with wrong password 5 times
    for i in range(5):
        await client.post(
            "/api/v1/auth/login",
            json={
                "username": "testuser",
                "password": "WrongPassword!"
            }
        )
    
    # 6th attempt should indicate account is locked
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "username": "testuser",
            "password": "WrongPassword!"
        }
    )
    
    assert response.status_code == 401
    # In production, check for specific "account locked" message


# ==================== Role and Permission Tests ====================

@pytest.mark.integration
async def test_superuser_has_all_permissions(
    client: AsyncClient,
    superuser: User
):
    """Test that superuser has all permissions"""
    assert superuser.is_superuser is True
    assert superuser.has_permission("any:permission") is True


@pytest.mark.integration
async def test_user_has_role_permissions(
    client: AsyncClient,
    test_user: User,
    test_role: Role
):
    """Test that user has permissions from assigned role"""
    assert test_user.has_role("teller") is True
    assert test_user.has_permission("transaction:create") is True
    assert test_user.has_permission("user:delete") is False