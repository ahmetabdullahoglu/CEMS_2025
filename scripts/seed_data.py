"""
Seed Data Script
Creates default roles and superuser account
Run this after database migrations
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext

from app.db.base import AsyncSessionLocal
from app.db.models.user import User
from app.db.models.role import Role
from app.schemas.role import DEFAULT_ROLES
from app.core.permissions import get_role_permissions

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def create_default_roles(db: AsyncSession) -> dict:
    """
    Create default roles (admin, manager, teller)
    Updates existing roles with latest permissions
    Returns dict of role_name: role_object
    """
    print("Creating/updating default roles...")
    roles_map = {}

    for role_name, role_data in DEFAULT_ROLES.items():
        # Check if role already exists
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()

        if existing_role:
            # Update existing role with latest permissions
            existing_role.display_name_ar = role_data["display_name_ar"]
            existing_role.description = role_data["description"]
            existing_role.permissions = role_data["permissions"]
            existing_role.is_active = True

            roles_map[role_name] = existing_role
            print(f"  ✓ Updated role '{role_name}' with {len(role_data['permissions'])} permissions")
        else:
            # Create new role
            new_role = Role(
                name=role_data["name"],
                display_name_ar=role_data["display_name_ar"],
                description=role_data["description"],
                permissions=role_data["permissions"],
                is_active=True
            )
            db.add(new_role)
            await db.flush()  # Flush to get ID
            roles_map[role_name] = new_role
            print(f"  ✓ Created role '{role_name}' with {len(role_data['permissions'])} permissions")

    await db.commit()
    print(f"✓ Successfully processed {len(roles_map)} roles\n")
    return roles_map


async def create_superuser(db: AsyncSession, roles_map: dict) -> None:
    """Create default superuser account"""
    print("Creating superuser account...")
    
    # Check if superuser already exists
    result = await db.execute(
        select(User).where(User.username == "admin")
    )
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        print("  ⚠ Superuser 'admin' already exists\n")
        return
    
    # Create superuser
    admin_role = roles_map.get("admin")
    
    superuser = User(
        username="admin",
        email="admin@cems.co",
        hashed_password=pwd_context.hash("Admin@123"),  # Default password
        full_name="System Administrator",
        phone_number="+90 555 000 0000",
        is_active=True,
        is_superuser=True,
    )
    
    # Add admin role
    if admin_role:
        superuser.roles.append(admin_role)
    
    db.add(superuser)
    await db.commit()
    
    print("  ✓ Created superuser 'admin'")
    print("  📧 Email: admin@cems.co")
    print("  🔑 Password: Admin@123")
    print("  ⚠ IMPORTANT: Change this password immediately after first login!\n")


async def seed_database():
    """Main seeding function"""
    print("=" * 60)
    print("CEMS Database Seeding")
    print("=" * 60)
    print()
    
    async with AsyncSessionLocal() as db:
        try:
            # Create roles
            roles_map = await create_default_roles(db)
            
            # Create superuser
            await create_superuser(db, roles_map)
            
            print("=" * 60)
            print("✓ Database seeding completed successfully!")
            print("=" * 60)
            
        except Exception as e:
            print(f"\n❌ Error during seeding: {str(e)}")
            await db.rollback()
            raise


async def reset_database():
    """Delete all users and roles (USE WITH CAUTION!)"""
    print("=" * 60)
    print("⚠ WARNING: RESETTING DATABASE")
    print("=" * 60)
    print()
    
    response = input("Are you sure you want to delete all users and roles? (yes/no): ")
    if response.lower() != "yes":
        print("Operation cancelled.")
        return
    
    async with AsyncSessionLocal() as db:
        try:
            # Delete all users
            await db.execute("DELETE FROM user_roles")
            await db.execute("DELETE FROM user_branches")
            await db.execute("DELETE FROM users")
            await db.execute("DELETE FROM roles")
            await db.commit()
            
            print("✓ Database reset complete\n")
            print("Run seeding again to create default data.")
            
        except Exception as e:
            print(f"❌ Error during reset: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    # Check command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--reset":
        asyncio.run(reset_database())
    else:
        asyncio.run(seed_database())
        
        
async def create_default_roles(db: AsyncSession) -> dict:
    """Create default roles with updated permissions"""
    roles_map = {}
    
    for role_name, role_data in DEFAULT_ROLES.items():
        # Get permissions from permissions.py
        permissions = get_role_permissions(role_name)
        
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()
        
        if existing_role:
            # Update permissions
            existing_role.permissions = permissions
            roles_map[role_name] = existing_role
        else:
            # Create new role
            new_role = Role(
                name=role_data["name"],
                display_name_ar=role_data["display_name_ar"],
                description=role_data["description"],
                permissions=permissions,  # From permissions.py
                is_active=True
            )
            db.add(new_role)
            await db.flush()
            roles_map[role_name] = new_role
    
    await db.commit()
    return roles_map