"""
Update Role Permissions Script
Updates existing roles with the latest permissions from DEFAULT_ROLES
Run this after updating permission definitions
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.base import AsyncSessionLocal
from app.db.models.role import Role
from app.schemas.role import DEFAULT_ROLES


async def update_role_permissions(db: AsyncSession) -> None:
    """Update existing roles with new permissions"""
    print("=" * 60)
    print("Updating Role Permissions")
    print("=" * 60)
    print()

    updated_count = 0

    for role_name, role_data in DEFAULT_ROLES.items():
        # Get existing role
        result = await db.execute(
            select(Role).where(Role.name == role_name)
        )
        existing_role = result.scalar_one_or_none()

        if existing_role:
            # Compare permissions
            old_permissions = set(existing_role.permissions or [])
            new_permissions = set(role_data["permissions"])

            if old_permissions != new_permissions:
                # Update permissions
                existing_role.permissions = role_data["permissions"]
                existing_role.display_name_ar = role_data["display_name_ar"]
                existing_role.description = role_data["description"]

                added = new_permissions - old_permissions
                removed = old_permissions - new_permissions

                print(f"✓ Updated role '{role_name}':")
                if added:
                    print(f"  + Added {len(added)} permissions:")
                    for perm in sorted(added)[:5]:  # Show first 5
                        print(f"    - {perm}")
                    if len(added) > 5:
                        print(f"    ... and {len(added) - 5} more")

                if removed:
                    print(f"  - Removed {len(removed)} permissions:")
                    for perm in sorted(removed)[:5]:  # Show first 5
                        print(f"    - {perm}")
                    if len(removed) > 5:
                        print(f"    ... and {len(removed) - 5} more")

                print(f"  Total permissions: {len(new_permissions)}")
                print()
                updated_count += 1
            else:
                print(f"✓ Role '{role_name}' is already up to date")
                print()
        else:
            print(f"⚠ Role '{role_name}' not found - skipping")
            print()

    await db.commit()

    print("=" * 60)
    if updated_count > 0:
        print(f"✓ Successfully updated {updated_count} role(s)")
    else:
        print("✓ All roles are up to date")
    print("=" * 60)


async def show_role_permissions():
    """Show current permissions for all roles"""
    print("=" * 60)
    print("Current Role Permissions")
    print("=" * 60)
    print()

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Role))
        roles = result.scalars().all()

        for role in roles:
            print(f"\n{role.name.upper()} ({role.display_name_ar}):")
            print(f"Description: {role.description}")
            print(f"Permissions ({len(role.permissions or [])}):")

            # Group permissions by category
            perms_by_category = {}
            for perm in sorted(role.permissions or []):
                if ":" in perm:
                    category, action = perm.split(":", 1)
                    if category not in perms_by_category:
                        perms_by_category[category] = []
                    perms_by_category[category].append(action)

            for category in sorted(perms_by_category.keys()):
                actions = ", ".join(sorted(perms_by_category[category]))
                print(f"  {category}: {actions}")

    print("\n" + "=" * 60)


async def main():
    """Main function"""
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        await show_role_permissions()
        return

    async with AsyncSessionLocal() as db:
        try:
            await update_role_permissions(db)
        except Exception as e:
            print(f"\n❌ Error updating permissions: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print()
    if len(sys.argv) > 1 and sys.argv[1] == "--show":
        print("Showing current role permissions...")
    else:
        print("This will update existing roles with the latest permissions.")
        print("Use --show to view current permissions without updating.")
        print()
        response = input("Continue? (yes/no): ")
        if response.lower() != "yes":
            print("Operation cancelled.")
            sys.exit(0)

    print()
    asyncio.run(main())
