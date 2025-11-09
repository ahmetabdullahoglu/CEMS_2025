"""
Debug Authentication Issues
Check if admin user exists and test password verification
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
from passlib.context import CryptContext

from app.db.base import AsyncSessionLocal
from app.db.models.user import User
from app.core.security import verify_password, get_password_hash

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


async def debug_admin_user():
    """Debug admin user authentication"""
    print("=" * 70)
    print("🔍 Authentication Debugging Tool")
    print("=" * 70)
    print()

    async with AsyncSessionLocal() as db:
        try:
            # 1. Check if admin user exists
            print("1️⃣  Checking if admin user exists...")
            result = await db.execute(
                select(User).where(User.username == 'admin')
            )
            user = result.scalar_one_or_none()

            if not user:
                print("❌ ERROR: Admin user does not exist in database!")
                print()
                print("💡 Solution: Run seeding script:")
                print("   python scripts/seed_data.py")
                return

            print("✅ Admin user found!")
            print()

            # 2. Display user information
            print("2️⃣  User Information:")
            print(f"   Username:              {user.username}")
            print(f"   Email:                 {user.email}")
            print(f"   Full Name:             {user.full_name}")
            print(f"   Is Active:             {user.is_active}")
            print(f"   Is Superuser:          {user.is_superuser}")
            print(f"   Is Locked:             {user.is_locked}")
            print(f"   Failed Login Attempts: {user.failed_login_attempts}")
            print(f"   Last Login:            {user.last_login}")
            print(f"   Hashed Password:       {user.hashed_password[:60]}...")
            print()

            # 3. Check account status
            print("3️⃣  Account Status Check:")
            if not user.is_active:
                print("❌ ERROR: Account is DISABLED!")
                print("   Fix: Set is_active = TRUE in database")
                return
            else:
                print("✅ Account is ACTIVE")

            if user.is_locked:
                print(f"❌ ERROR: Account is LOCKED until {user.locked_until}")
                print("   Fix: Set is_locked = FALSE and locked_until = NULL")
                return
            else:
                print("✅ Account is NOT LOCKED")
            print()

            # 4. Test password verification
            print("4️⃣  Password Verification Test:")
            test_password = "Admin@123"
            print(f"   Testing password: '{test_password}'")

            # Test with verify_password function
            is_valid = verify_password(test_password, user.hashed_password)
            print(f"   Verification result: {is_valid}")

            if is_valid:
                print("✅ Password verification SUCCESSFUL!")
                print()
                print("🎯 The password is correct!")
                print()
                print("⚠️  If login still fails, check:")
                print("   1. Are you using the correct endpoint? /api/v1/auth/login")
                print("   2. Is the request body correct JSON format?")
                print("   3. Check Docker logs for errors: make docker-logs")
                print("   4. Try logging in via API docs: http://localhost:8000/docs")
            else:
                print("❌ Password verification FAILED!")
                print()
                print("🔧 Fixing password...")
                # Re-hash the password
                new_hash = get_password_hash(test_password)
                user.hashed_password = new_hash
                await db.commit()

                # Verify again
                is_valid_now = verify_password(test_password, new_hash)
                if is_valid_now:
                    print("✅ Password has been reset successfully!")
                    print(f"   New hash: {new_hash[:60]}...")
                else:
                    print("❌ Still failed! There might be a deeper issue.")
            print()

            # 5. Count total users
            print("5️⃣  Database Statistics:")
            result = await db.execute(text('SELECT COUNT(*) FROM users'))
            user_count = result.scalar()
            print(f"   Total users: {user_count}")

            result = await db.execute(text('SELECT COUNT(*) FROM roles'))
            role_count = result.scalar()
            print(f"   Total roles: {role_count}")
            print()

            # 6. Test hash creation
            print("6️⃣  Hash Creation Test:")
            test_hash_1 = pwd_context.hash(test_password)
            test_hash_2 = get_password_hash(test_password)
            print(f"   Hash 1 (pwd_context): {test_hash_1[:60]}...")
            print(f"   Hash 2 (get_password_hash): {test_hash_2[:60]}...")

            verify_1 = pwd_context.verify(test_password, test_hash_1)
            verify_2 = verify_password(test_password, test_hash_2)
            print(f"   Verify hash 1: {verify_1}")
            print(f"   Verify hash 2: {verify_2}")
            print()

            print("=" * 70)
            print("🏁 Debugging Complete")
            print("=" * 70)

        except Exception as e:
            print(f"\n❌ Error during debugging: {str(e)}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_admin_user())
