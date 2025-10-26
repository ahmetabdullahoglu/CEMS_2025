# في Python console أو Jupyter
import asyncio
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.base import AsyncSessionLocal
from app.db.models.branch import Branch, BranchBalance

async def test():
    async with AsyncSessionLocal() as db:
        # Test 1: Load without relationships
        result = await db.execute(select(Branch).where(Branch.is_active == True))
        branches = result.scalars().all()
        print(f"✅ Found {len(branches)} branches")
        
        # Test 2: Load with relationships
        stmt = select(Branch).where(Branch.is_active == True).options(
            selectinload(Branch.balances).selectinload(BranchBalance.currency)
        )
        result = await db.execute(stmt)
        branches = result.scalars().all()
        
        for branch in branches:
            print(f"\n📍 Branch: {branch.code}")
            print(f"   Has balances attr: {hasattr(branch, 'balances')}")
            print(f"   Number of balances: {len(branch.balances)}")
            for balance in branch.balances:
                print(f"     - {balance.currency.code}: {balance.balance}")

asyncio.run(test())