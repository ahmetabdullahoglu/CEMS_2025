"""
Unit Tests for User and Role Models
Tests model creation, relationships, and business logic
"""

import pytest
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.db.models.user import User, user_roles, user_branches
from app.db.models.role import Role

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# ==================== Role Model Tests ====================

@pytest.mark.unit
async def test_create_role(db_session: AsyncSession):
    """Test creating a role"""
    role = Role(
        name="test_role",
        display_name_ar="دور اختبار",
        description="Test role for unit testing",
        permissions=["test:read", "test:write"],
        is_active=True
    )
    
    db_session.add(role)
    await db_session.commit()
    await db_session.refresh(role)
    
    assert role.id is not None
    assert role.name == "test_role"
    assert role.display_name_ar == "دور اختبار"
    assert len(role.permissions) == 2
    assert "test:read" in role.permissions


@pytest.mark.unit
async def test_role_has_permission(db_session: AsyncSession):
    """Test role permission checking"""
    role = Role(
        name="manager",
        display_name_ar="مدير",
        permissions=["user:read", "user:create", "branch:read"]
    )
    
    assert role.has_permission("user:read") is True
    assert role.has_permission("user:delete") is False


@pytest.mark.unit
async def test_role_add_remove_permission(db_session: AsyncSession):
    """Test adding and removing permissions"""
    role = Role(
        name="teller",
        display_name_ar="صراف",
        permissions=["transaction:create"]
    )
    
    # Add permission
    role.add_permission("transaction:read")
    assert "transaction:read" in role.permissions
    
    # Try to add duplicate (should not add)
    initial_count = len(role.permissions)
    role.add_permission("transaction:read")
    assert len(role.permissions) == initial_count
    
    # Remove permission
    role.remove_permission("transaction:create")
    assert "transaction:create" not in role.permissions


# ==================== User Model Tests ====================

@pytest.mark.unit
async def test_create_user(db_session: AsyncSession):
    """Test creating a user"""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=pwd_context.hash("TestPass123!"),
        full_name="Test User",
        phone_number="+90 555 123 4567",
        is_active=True,
        is_superuser=False
    )
    
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.id is not None
    assert user.username == "testuser"
    assert user.email == "test@example.com"
    assert user.full_name == "Test User"
    assert user.is_active is True
    assert user.is_superuser is False


@pytest.mark.unit
async def test_user_unique_constraints(db_session: AsyncSession):
    """Test that username and email must be unique"""
    user1 = User(
        username="duplicate",
        email="unique1@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="User One"
    )
    db_session.add(user1)
    await db_session.commit()
    
    # Try to create user with same username
    user2 = User(
        username="duplicate",
        email="unique2@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="User Two"
    )
    db_session.add(user2)
    
    with pytest.raises(Exception):  # Will raise IntegrityError
        await db_session.commit()


@pytest.mark.unit
async def test_user_is_locked_property(db_session: AsyncSession):
    """Test user account lock functionality"""
    user = User(
        username="locktest",
        email="lock@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Lock Test",
        locked_until=None
    )
    
    # Not locked
    assert user.is_locked is False
    
    # Lock for 30 minutes
    user.locked_until = datetime.utcnow() + timedelta(minutes=30)
    assert user.is_locked is True
    
    # Lock expired
    user.locked_until = datetime.utcnow() - timedelta(minutes=1)
    assert user.is_locked is False


@pytest.mark.unit
async def test_user_password_hashing(db_session: AsyncSession):
    """Test that passwords are properly hashed"""
    password = "SecurePass123!"
    hashed = pwd_context.hash(password)
    
    user = User(
        username="hashtest",
        email="hash@example.com",
        hashed_password=hashed,
        full_name="Hash Test"
    )
    
    # Password should not be stored in plain text
    assert user.hashed_password != password
    
    # Verify password
    assert pwd_context.verify(password, user.hashed_password)


# ==================== User-Role Relationship Tests ====================

@pytest.mark.unit
async def test_user_role_assignment(db_session: AsyncSession):
    """Test assigning roles to users"""
    # Create role
    admin_role = Role(
        name="admin",
        display_name_ar="مدير",
        permissions=["all"]
    )
    db_session.add(admin_role)
    
    # Create user
    user = User(
        username="roletest",
        email="role@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Role Test"
    )
    db_session.add(user)
    
    # Assign role to user
    user.roles.append(admin_role)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    # Verify relationship
    assert len(user.roles) == 1
    assert user.roles[0].name == "admin"


@pytest.mark.unit
async def test_user_has_role(db_session: AsyncSession):
    """Test checking if user has a specific role"""
    role = Role(
        name="manager",
        display_name_ar="مدير",
        permissions=[]
    )
    db_session.add(role)
    
    user = User(
        username="rolecheck",
        email="rolecheck@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Role Check"
    )
    user.roles.append(role)
    db_session.add(user)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.has_role("manager") is True
    assert user.has_role("admin") is False


@pytest.mark.unit
async def test_user_has_permission(db_session: AsyncSession):
    """Test checking if user has a specific permission"""
    role = Role(
        name="teller",
        display_name_ar="صراف",
        permissions=["transaction:create", "transaction:read"]
    )
    db_session.add(role)
    
    user = User(
        username="permtest",
        email="perm@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Permission Test"
    )
    user.roles.append(role)
    db_session.add(user)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    assert user.has_permission("transaction:create") is True
    assert user.has_permission("transaction:delete") is False


@pytest.mark.unit
async def test_superuser_has_all_permissions(db_session: AsyncSession):
    """Test that superuser has all permissions"""
    user = User(
        username="superuser",
        email="super@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Super User",
        is_superuser=True
    )
    db_session.add(user)
    await db_session.commit()
    
    # Superuser should have all permissions
    assert user.has_permission("any:permission") is True
    assert user.has_permission("anything:else") is True


# ==================== Multiple Roles Tests ====================

@pytest.mark.unit
async def test_user_multiple_roles(db_session: AsyncSession):
    """Test user with multiple roles"""
    role1 = Role(
        name="manager",
        display_name_ar="مدير",
        permissions=["branch:read", "branch:update"]
    )
    role2 = Role(
        name="teller",
        display_name_ar="صراف",
        permissions=["transaction:create"]
    )
    db_session.add_all([role1, role2])
    
    user = User(
        username="multirole",
        email="multi@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Multi Role"
    )
    user.roles.extend([role1, role2])
    db_session.add(user)
    
    await db_session.commit()
    await db_session.refresh(user)
    
    # User should have permissions from both roles
    assert len(user.roles) == 2
    assert user.has_permission("branch:read") is True
    assert user.has_permission("transaction:create") is True


# ==================== Query Tests ====================

@pytest.mark.unit
async def test_query_users_by_role(db_session: AsyncSession):
    """Test querying users by role"""
    admin_role = Role(name="admin", display_name_ar="مدير", permissions=[])
    db_session.add(admin_role)
    
    user1 = User(
        username="admin1",
        email="admin1@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Admin One"
    )
    user1.roles.append(admin_role)
    
    user2 = User(
        username="admin2",
        email="admin2@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Admin Two"
    )
    user2.roles.append(admin_role)
    
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # Query users with admin role
    result = await db_session.execute(
        select(User).join(User.roles).where(Role.name == "admin")
    )
    admin_users = result.scalars().all()
    
    assert len(admin_users) >= 2


@pytest.mark.unit
async def test_query_active_users(db_session: AsyncSession):
    """Test querying active users"""
    user1 = User(
        username="active1",
        email="active1@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Active One",
        is_active=True
    )
    user2 = User(
        username="inactive1",
        email="inactive1@example.com",
        hashed_password=pwd_context.hash("Pass123!"),
        full_name="Inactive One",
        is_active=False
    )
    db_session.add_all([user1, user2])
    await db_session.commit()
    
    # Query only active users
    result = await db_session.execute(
        select(User).where(User.is_active == True)
    )
    active_users = result.scalars().all()
    
    # Should not include inactive user
    assert all(u.is_active for u in active_users)