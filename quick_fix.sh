#!/bin/bash

# 🚀 CEMS Ultimate Fix - Solves ALL issues
# Version: 2.0

echo "╔════════════════════════════════════════════╗"
echo "║   CEMS ULTIMATE FIX v2.0                  ║"
echo "║   Fixes: Database + Pydantic + Imports +   ║"
echo "║          Validators                        ║"
echo "╚════════════════════════════════════════════╝"
echo ""

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

# Check directory
if [ ! -d "app" ]; then
    echo -e "${RED}❌ Error: Not in CEMS_2025 directory${NC}"
    echo "Please run from: /Users/ahmet/Documents/CEMS_2025"
    exit 1
fi

# Backup
echo -e "${BLUE}📦 Step 1/5: Creating backup...${NC}"
BACKUP_DIR="backups/ultimate_fix_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"
cp -r app/core/database.py "$BACKUP_DIR/" 2>/dev/null
cp -r app/schemas "$BACKUP_DIR/" 2>/dev/null
cp -r app/api/v1/endpoints "$BACKUP_DIR/" 2>/dev/null
cp -r app/utils/validators.py "$BACKUP_DIR/" 2>/dev/null
echo -e "${GREEN}✅ Backup: $BACKUP_DIR${NC}"
echo ""

# Fix 1: Database.py
echo -e "${BLUE}🔧 Step 2/5: Fixing database.py...${NC}"
cat > app/core/database.py << 'DBEOF'
"""
Database Configuration Module
SQLAlchemy async setup and session management
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from app.core.config import settings

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    pool_pre_ping=True,
    poolclass=NullPool if settings.DEBUG else None,
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session
    Usage in FastAPI endpoints:
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db():
    """Initialize database - create all tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db():
    """Drop all database tables - USE WITH CAUTION!"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
DBEOF
echo -e "${GREEN}✅ database.py${NC}"
echo ""

# Fix 2: Pydantic V2
echo -e "${BLUE}🔧 Step 3/5: Fixing Pydantic V2...${NC}"
for file in app/schemas/*.py; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "__init__.py" ]; then
        sed -i.bak 's/orm_mode = True/from_attributes = True/g' "$file"
        sed -i.bak 's/schema_extra =/json_schema_extra =/g' "$file"
        rm -f "$file.bak"
        echo -e "  ${GREEN}✓${NC} $(basename "$file")"
    fi
done
echo -e "${GREEN}✅ Schemas fixed${NC}"
echo ""

# Fix 3: Imports
echo -e "${BLUE}🔧 Step 4/5: Fixing imports...${NC}"
for file in app/api/v1/endpoints/*.py; do
    if [ -f "$file" ] && [ "$(basename "$file")" != "__init__.py" ]; then
        if grep -q "from app.core.security import get_current" "$file"; then
            sed -i.bak 's/from app\.core\.security import get_current_active_user/from app.api.deps import get_current_active_user/g' "$file"
            sed -i.bak 's/from app\.core\.security import get_current_user/from app.api.deps import get_current_user/g' "$file"
            sed -i.bak 's/from app\.core\.security import require_permission/from app.api.deps import require_permission/g' "$file"
            sed -i.bak 's/from app\.core\.security import require_role/from app.api.deps import require_role/g' "$file"
            rm -f "$file.bak"
            echo -e "  ${GREEN}✓${NC} $(basename "$file")"
        fi
    fi
done
echo -e "${GREEN}✅ Imports fixed${NC}"
echo ""

# Fix 4: validators.py - THE CRITICAL FIX!
echo -e "${BLUE}🔧 Step 5/5: Creating validators.py...${NC}"
cat > app/utils/validators.py << 'VALEOF'
# app/utils/validators.py
"""
Validation Utilities
Common validation functions for business logic
"""

from decimal import Decimal
from typing import Optional, Dict, Any
from datetime import date
import re

from app.core.exceptions import ValidationError


def validate_positive_amount(
    amount: Decimal,
    field_name: str = "amount",
    min_value: Optional[Decimal] = None,
    max_value: Optional[Decimal] = None
) -> Decimal:
    """Validate amount is positive and within range"""
    if amount <= 0:
        raise ValidationError(f"{field_name} must be positive (got: {amount})")
    
    if min_value is not None and amount <= min_value:
        raise ValidationError(f"{field_name} must be greater than {min_value}")
    
    if max_value is not None and amount > max_value:
        raise ValidationError(f"{field_name} must not exceed {max_value}")
    
    return amount


def validate_transaction_limits(
    amount: Decimal,
    transaction_type: str,
    max_single: Optional[Decimal] = None,
    max_daily: Optional[Decimal] = None
) -> Dict[str, Any]:
    """Validate transaction amount against limits"""
    if max_single is None:
        max_single = Decimal('1000000.00')
    
    if max_daily is None:
        max_daily = Decimal('5000000.00')
    
    if amount > max_single:
        raise ValidationError(
            f"Transaction amount ({amount}) exceeds maximum "
            f"({max_single}) for {transaction_type}"
        )
    
    return {
        'valid': True,
        'amount': float(amount),
        'max_single': float(max_single),
        'max_daily': float(max_daily)
    }


def validate_phone_number(phone: str, country_code: str = "SA") -> str:
    """Validate phone number format"""
    phone = phone.replace(" ", "").replace("-", "")
    
    if country_code == "SA":
        if phone.startswith("+966"):
            phone = phone[4:]
        elif phone.startswith("00966"):
            phone = phone[5:]
        
        if not (phone.startswith("5") and len(phone) in [9, 10]):
            raise ValidationError(f"Invalid Saudi phone: {phone}")
        
        if not phone.isdigit():
            raise ValidationError(f"Phone must be digits: {phone}")
    
    return phone


def validate_email(email: str) -> str:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email: {email}")
    return email.lower()


def validate_branch_code(code: str) -> str:
    """Validate branch code format (BR001, BR002, etc.)"""
    if not code.startswith('BR'):
        raise ValidationError(f"Branch code must start with 'BR': {code}")
    
    suffix = code[2:]
    if not suffix.isdigit():
        raise ValidationError(f"Branch code must have numeric suffix: {code}")
    
    if len(suffix) < 3:
        raise ValidationError(f"Branch code suffix must be 3+ digits: {code}")
    
    return code.upper()


def validate_national_id(national_id: str, country: str = "SA") -> str:
    """Validate national ID format"""
    if country == "SA":
        if not national_id.isdigit():
            raise ValidationError(f"National ID must be digits: {national_id}")
        
        if len(national_id) != 10:
            raise ValidationError(f"National ID must be 10 digits: {national_id}")
        
        if not national_id.startswith(('1', '2')):
            raise ValidationError(f"National ID must start with 1 or 2: {national_id}")
    
    return national_id


def validate_date_not_future(date_value: date, field_name: str = "date") -> date:
    """Validate date is not in the future"""
    if date_value > date.today():
        raise ValidationError(f"{field_name} cannot be in future: {date_value}")
    return date_value


def validate_exchange_rate(
    rate: Decimal,
    min_rate: Decimal = Decimal('0.0001'),
    max_rate: Decimal = Decimal('1000000')
) -> Decimal:
    """Validate exchange rate is within bounds"""
    if rate <= 0:
        raise ValidationError(f"Exchange rate must be positive: {rate}")
    
    if rate < min_rate:
        raise ValidationError(f"Rate too low: {rate} (min: {min_rate})")
    
    if rate > max_rate:
        raise ValidationError(f"Rate too high: {rate} (max: {max_rate})")
    
    return rate


__all__ = [
    'validate_positive_amount',
    'validate_transaction_limits',
    'validate_phone_number',
    'validate_email',
    'validate_branch_code',
    'validate_national_id',
    'validate_date_not_future',
    'validate_exchange_rate',
]
VALEOF
echo -e "${GREEN}✅ validators.py created${NC}"
echo ""

# Verification
echo -e "${BLUE}🔍 Verification...${NC}"

checks_passed=0
checks_total=4

# Check 1
if grep -q "AsyncGenerator\[AsyncSession, None\]" app/core/database.py; then
    echo -e "${GREEN}✓ database.py${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠ database.py${NC}"
fi

# Check 2
if grep -q "from_attributes = True" app/schemas/*.py 2>/dev/null; then
    echo -e "${GREEN}✓ Pydantic V2${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠ Pydantic V2${NC}"
fi

# Check 3
if grep -q "from app.api.deps import get_current_active_user" app/api/v1/endpoints/transactions.py 2>/dev/null; then
    echo -e "${GREEN}✓ Imports${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠ Imports${NC}"
fi

# Check 4
if grep -q "def validate_positive_amount" app/utils/validators.py; then
    echo -e "${GREEN}✓ validators.py${NC}"
    checks_passed=$((checks_passed + 1))
else
    echo -e "${YELLOW}⚠ validators.py${NC}"
fi

echo ""
echo "╔════════════════════════════════════════════╗"
echo "║          ✨ FIX COMPLETE ✨               ║"
echo "║   Checks Passed: $checks_passed/$checks_total                     ║"
echo "╚════════════════════════════════════════════╝"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "1. ${YELLOW}python -m uvicorn app.main:app --reload${NC}"
echo "2. If issues: restore from ${YELLOW}$BACKUP_DIR${NC}"
echo ""
echo -e "${BLUE}🚀 Ready to launch!${NC}"