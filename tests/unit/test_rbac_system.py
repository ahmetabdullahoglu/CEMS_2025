"""
Unit Tests for RBAC System
Tests permission system, middleware, and decorators
"""

import pytest
from uuid import uuid4
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import (
    format_permission,
    parse_permission,
    get_all_permissions_list,
    get_permissions_by_category,
    validate_permission,
    get_role_permissions,
    check_permission_hierarchy,
    ROLE_PERMISSIONS,
)
from app.middleware.rbac import (
    PermissionChecker,
    BranchAccessChecker,
    permission_cache,
)
from app.db.models.user import User
from app.db.models.role import Role
from app.core.exceptions import PermissionDeniedError


# ==================== Permission System Tests ====================

@pytest.mark.unit
def test_format_permission():
    """Test permission formatting"""
    perm = format_permission("users", "create")
    assert perm == "users:create"


@pytest.mark.unit
def test_parse_permission():
    """Test permission parsing"""
    category, action = parse_permission("users:create")
    assert category == "users"
    assert action == "create"


@pytest.mark.unit
def test_parse_invalid_permission():
    """Test parsing invalid permission format"""
    with pytest.raises(ValueError):
        parse_permission("invalid_format")


@pytest.mark.unit
def test_validate_permission():
    """Test permission validation"""
    assert validate_permission("users:create") is True
    assert validate_permission("users:invalid_action") is False
    assert validate_permission("invalid_category:read") is False


@pytest.mark.unit
def test_get_all_permissions():
    """Test getting all available permissions"""
    permissions = get_all_permissions_list()
    
    assert len(permissions) > 0
    assert "users:create" in permissions
    assert "transactions:approve" in permissions
    assert "vault:transfer" in permissions


@pytest.mark.unit
def test_get_permissions_by_category():
    """Test getting permissions for category"""
    user_perms = get_permissions_by_category("users")
    
    assert "users:create" in user_perms
    assert "users:read" in user_perms
    assert "users:update" in user_perms
    assert "users:delete" in user_perms


@pytest.mark.unit
def test_get_role_permissions():
    """Test getting permissions for role"""
    admin_perms = get_role_permissions("admin")
    manager_perms = get_role_permissions("manager")
    teller_perms = get_role_permissions("teller")
    
    # Admin should have more permissions than manager
    assert len(admin_perms) > len(manager_perms)
    
    # Manager should have more than teller
    assert len(manager_perms) > len(teller_perms)
    
    # Check specific permissions
    assert "users:delete" in admin_perms
    assert "transactions:approve" in manager_perms
    assert "transactions:create" in teller_perms


@pytest.mark.unit
def test_permission_hierarchy():
    """Test permission hierarchy checking"""
    user_perms = ["users:update", "transactions:approve"]
    
    # Direct permission
    assert check_permission_hierarchy(user_perms, "users:update") is True
    
    # Hierarchical permission (update implies read)
    assert check_permission_hierarchy(user_perms, "users:read") is True
    
    # Missing permission
    assert check_permission_hierarchy(user_perms, "users:delete") is False


@pytest.mark.unit
def test_role_permission_completeness():
    """Test that role permissions are valid"""
    for role_name, permissions in ROLE_PERMISSIONS.items():
        for permission in permissions:
            assert validate_permission(permission), \
                f"Invalid permission in {role_name}: {permission}"


# ==================== Permission Checker Tests ====================

@pytest.mark.unit
async def test_superuser_has_all_permissions(db_session: AsyncSession):
    """Test that superuser has all permissions"""
    superuser = User(
        username="superuser",
        email="super@example.com",
        hashed_password="hashed",
        full_name="Super User",
        is_superuser=True
    )
    
    # Superuser should pass any permission check
    result = await PermissionChecker.check_permissions(
        user=superuser,
        required_permissions=["any:permission", "another:permission"]
    )
    assert result is True


@pytest.mark.unit
async def test_user_with_permission(db_session: AsyncSession):
    """Test user with required permission"""
    role = Role(
        name="tester",
        display_name_ar="مختبر",
        permissions=["users:read", "transactions:create"]
    )
    db_session.add(role)
    
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Should pass with required permission
    result = await PermissionChecker.check_permissions(
        user=user,
        required_permissions=["users:read"]
    )
    assert result is True


@pytest.mark.unit
async def test_user_without_permission(db_session: AsyncSession):
    """Test user without required permission"""
    role = Role(
        name="limited",
        display_name_ar="محدود",
        permissions=["users:read"]
    )
    db_session.add(role)
    
    user = User(
        username="limited",
        email="limited@example.com",
        hashed_password="hashed",
        full_name="Limited User"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Should fail without required permission
    with pytest.raises(PermissionDeniedError):
        await PermissionChecker.check_permissions(
            user=user,
            required_permissions=["users:delete"]
        )


@pytest.mark.unit
async def test_user_with_multiple_permissions(db_session: AsyncSession):
    """Test user requiring multiple permissions"""
    role = Role(
        name="multi",
        display_name_ar="متعدد",
        permissions=["users:read", "users:update", "transactions:create"]
    )
    db_session.add(role)
    
    user = User(
        username="multi",
        email="multi@example.com",
        hashed_password="hashed",
        full_name="Multi User"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Should pass with all required permissions
    result = await PermissionChecker.check_permissions(
        user=user,
        required_permissions=["users:read", "users:update"],
        require_all=True
    )
    assert result is True


@pytest.mark.unit
async def test_user_with_any_permission(db_session: AsyncSession):
    """Test user needing any one of multiple permissions"""
    role = Role(
        name="any",
        display_name_ar="أي",
        permissions=["transactions:read"]
    )
    db_session.add(role)
    
    user = User(
        username="anyuser",
        email="any@example.com",
        hashed_password="hashed",
        full_name="Any User"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Should pass with at least one permission
    result = await PermissionChecker.check_permissions(
        user=user,
        required_permissions=["transactions:read", "transactions:create"],
        require_all=False
    )
    assert result is True


# ==================== Permission Cache Tests ====================

@pytest.mark.unit
async def test_permission_cache(db_session: AsyncSession):
    """Test permission caching"""
    role = Role(
        name="cached",
        display_name_ar="مخزن",
        permissions=["users:read"]
    )
    db_session.add(role)
    
    user = User(
        username="cached",
        email="cached@example.com",
        hashed_password="hashed",
        full_name="Cached User"
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # First call - should cache
    perms1 = await PermissionChecker.get_user_permissions(user)
    
    # Second call - should use cache
    perms2 = await PermissionChecker.get_user_permissions(user)
    
    assert perms1 == perms2
    assert "users:read" in perms1


@pytest.mark.unit
async def test_cache_invalidation():
    """Test permission cache invalidation"""
    user_id = uuid4()
    
    # Set cache
    permission_cache.set(user_id, ["test:permission"])
    
    # Verify cached
    cached = permission_cache.get(user_id)
    assert cached == ["test:permission"]
    
    # Invalidate
    PermissionChecker.invalidate_user_cache(user_id)
    
    # Verify cleared
    cached_after = permission_cache.get(user_id)
    assert cached_after is None


# ==================== Branch Access Tests ====================

@pytest.mark.unit
async def test_superuser_branch_access(db_session: AsyncSession):
    """Test that superuser has access to all branches"""
    superuser = User(
        username="superuser",
        email="super@example.com",
        hashed_password="hashed",
        full_name="Super User",
        is_superuser=True
    )
    
    # Superuser should access any branch
    result = await BranchAccessChecker.check_branch_access(
        user=superuser,
        branch_id=uuid4()
    )
    assert result is True


@pytest.mark.unit
async def test_user_with_branch_access(db_session: AsyncSession):
    """Test user with branch access"""
    # TODO: This test requires Branch model to be implemented
    # For now, it's a placeholder
    pass


@pytest.mark.unit
async def test_user_without_branch_access(db_session: AsyncSession):
    """Test user without branch access"""
    # TODO: This test requires Branch model to be implemented
    # For now, it's a placeholder
    pass


# ==================== Integration Scenarios ====================

@pytest.mark.unit
async def test_admin_full_access(db_session: AsyncSession):
    """Test that admin role has comprehensive access"""
    admin_role = Role(
        name="admin",
        display_name_ar="مدير",
        permissions=get_role_permissions("admin")
    )
    db_session.add(admin_role)
    
    admin = User(
        username="admin",
        email="admin@example.com",
        hashed_password="hashed",
        full_name="Admin User"
    )
    admin.roles.append(admin_role)
    db_session.add(admin)
    await db_session.commit()
    await db_session.refresh(admin)
    
    # Admin should have all major permissions
    critical_perms = [
        "users:delete",
        "branches:delete",
        "transactions:approve",
        "vault:approve_transfer",
        "reports:view_all",
    ]
    
    result = await PermissionChecker.check_permissions(
        user=admin,
        required_permissions=critical_perms,
        require_all=True
    )
    assert result is True


@pytest.mark.unit
async def test_manager_limited_access(db_session: AsyncSession):
    """Test that manager has appropriate limited access"""
    manager_role = Role(
        name="manager",
        display_name_ar="مدير فرع",
        permissions=get_role_permissions("manager")
    )
    db_session.add(manager_role)
    
    manager = User(
        username="manager",
        email="manager@example.com",
        hashed_password="hashed",
        full_name="Manager User"
    )
    manager.roles.append(manager_role)
    db_session.add(manager)
    await db_session.commit()
    await db_session.refresh(manager)
    
    # Manager should have transaction approval
    result = await PermissionChecker.check_permissions(
        user=manager,
        required_permissions=["transactions:approve"]
    )
    assert result is True
    
    # But not user deletion
    with pytest.raises(PermissionDeniedError):
        await PermissionChecker.check_permissions(
            user=manager,
            required_permissions=["users:delete"]
        )


@pytest.mark.unit
async def test_teller_minimal_access(db_session: AsyncSession):
    """Test that teller has minimal required access"""
    teller_role = Role(
        name="teller",
        display_name_ar="صراف",
        permissions=get_role_permissions("teller")
    )
    db_session.add(teller_role)
    
    teller = User(
        username="teller",
        email="teller@example.com",
        hashed_password="hashed",
        full_name="Teller User"
    )
    teller.roles.append(teller_role)
    db_session.add(teller)
    await db_session.commit()
    await db_session.refresh(teller)
    
    # Teller should create transactions
    result = await PermissionChecker.check_permissions(
        user=teller,
        required_permissions=["transactions:create"]
    )
    assert result is True
    
    # But not approve them
    with pytest.raises(PermissionDeniedError):
        await PermissionChecker.check_permissions(
            user=teller,
            required_permissions=["transactions:approve"]
        )


@pytest.mark.unit
async def test_multiple_roles_permission_union(db_session: AsyncSession):
    """Test user with multiple roles gets union of permissions"""
    role1 = Role(
        name="role1",
        display_name_ar="دور 1",
        permissions=["users:read", "branches:read"]
    )
    role2 = Role(
        name="role2",
        display_name_ar="دور 2",
        permissions=["transactions:create", "customers:read"]
    )
    db_session.add_all([role1, role2])
    
    user = User(
        username="multirole",
        email="multi@example.com",
        hashed_password="hashed",
        full_name="Multi Role User"
    )
    user.roles.extend([role1, role2])
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # User should have permissions from both roles
    result = await PermissionChecker.check_permissions(
        user=user,
        required_permissions=[
            "users:read",
            "branches:read",
            "transactions:create",
            "customers:read"
        ],
        require_all=True
    )
    assert result is True