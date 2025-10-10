#!/bin/bash
# Auto-fix Alembic Multiple Heads
# This script automatically fixes the multiple heads issue

set -e  # Exit on error

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        CEMS Alembic Multiple Heads Auto-Fix Script            ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Step 1: Diagnose
echo -e "${YELLOW}🔍 Step 1: Diagnosing the problem...${NC}"
echo ""

echo "Current heads:"
alembic heads || true
echo ""

echo "Current version:"
alembic current || true
echo ""

# Step 2: Identify problem migrations
echo -e "${YELLOW}🔍 Step 2: Identifying problem migrations...${NC}"
echo ""

PROBLEM_FILE="alembic/versions/*fdc482f24443*.py"

if ls $PROBLEM_FILE 1> /dev/null 2>&1; then
    echo -e "${RED}⚠️  Found problem migration: $PROBLEM_FILE${NC}"
    echo ""
    
    # Step 3: Ask for confirmation
    echo -e "${YELLOW}This migration appears to be incorrect (it drops tables in upgrade).${NC}"
    echo -e "${YELLOW}Would you like to delete it? (yes/no)${NC}"
    read -p "Enter choice: " choice
    
    if [ "$choice" = "yes" ]; then
        echo ""
        echo -e "${GREEN}🗑️  Deleting problem migration...${NC}"
        rm $PROBLEM_FILE
        echo -e "${GREEN}✅ Deleted successfully!${NC}"
        echo ""
        
        # Step 4: Verify fix
        echo -e "${GREEN}🔍 Step 3: Verifying fix...${NC}"
        echo ""
        
        echo "Current heads (should be one now):"
        alembic heads
        echo ""
        
        # Step 5: Try to upgrade
        echo -e "${GREEN}🚀 Step 4: Attempting to upgrade...${NC}"
        echo ""
        
        if alembic upgrade head; then
            echo ""
            echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║                    ✅ FIX SUCCESSFUL!                          ║${NC}"
            echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
            echo ""
            echo -e "${GREEN}✅ All migrations applied successfully!${NC}"
            echo -e "${GREEN}✅ Database is now up to date!${NC}"
            echo ""
        else
            echo ""
            echo -e "${RED}❌ Migration failed. Please check the error above.${NC}"
            exit 1
        fi
    else
        echo ""
        echo -e "${YELLOW}⚠️  Fix cancelled. No changes made.${NC}"
        echo ""
        echo "To fix manually:"
        echo "1. Delete: $PROBLEM_FILE"
        echo "2. Run: alembic upgrade head"
        exit 0
    fi
else
    echo -e "${GREEN}✅ No problem migration found!${NC}"
    echo ""
    
    # Check if there are still multiple heads
    HEAD_COUNT=$(alembic heads 2>/dev/null | wc -l)
    
    if [ $HEAD_COUNT -gt 1 ]; then
        echo -e "${YELLOW}⚠️  Still have multiple heads.${NC}"
        echo ""
        echo "Options:"
        echo "1. Create a merge migration: alembic merge -m 'merge heads' heads"
        echo "2. Manually review migrations in: alembic/versions/"
        echo ""
    else
        echo -e "${GREEN}✅ Single head found. Attempting upgrade...${NC}"
        echo ""
        
        if alembic upgrade head; then
            echo ""
            echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
            echo -e "${GREEN}║              ✅ ALL MIGRATIONS APPLIED!                        ║${NC}"
            echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
            echo ""
        else
            echo ""
            echo -e "${RED}❌ Migration failed. Please check the error above.${NC}"
            exit 1
        fi
    fi
fi

echo ""
echo -e "${BLUE}📊 Final Status:${NC}"
echo ""
echo "Current version:"
alembic current
echo ""
echo "Migration history:"
alembic history | head -10
echo ""

echo -e "${GREEN}🎉 Done!${NC}"