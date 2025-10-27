#!/bin/bash
# 🌱 Quick Seed Script for CEMS
# Run all seed scripts in correct order

echo "🌱 CEMS Database Seeding"
echo "========================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to run script
run_seed() {
    local script=$1
    local name=$2
    
    echo -e "${YELLOW}▶ Running ${name}...${NC}"
    python scripts/${script}
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ ${name} completed${NC}"
        echo ""
    else
        echo -e "${RED}❌ ${name} failed${NC}"
        exit 1
    fi
}

# 1. Basic data (users, roles)
run_seed "seed_data.py" "Basic Data (Users & Roles)"

# 2. Currencies
run_seed "seed_currencies.py" "Currencies & Exchange Rates"

# 3. Branches
run_seed "seed_branches.py" "Branches & Balances"

# 4. Customers
run_seed "seed_customers.py" "Customers & Documents"

echo "========================"
echo -e "${GREEN}✨ All seeding completed successfully!${NC}"
echo ""
echo "📊 Summary:"
echo "   ✅ Users & Roles"
echo "   ✅ Currencies (7)"
echo "   ✅ Exchange Rates"
echo "   ✅ Branches (3)"
echo "   ✅ Customers (8)"
echo ""
echo "🚀 Ready to test: http://localhost:8000/docs"
