#!/bin/bash
# 🌱 Complete CEMS Database Seeding Script
# Run all seed scripts in correct order including Vaults

echo "🌱 CEMS Complete Database Seeding"
echo "=================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

echo -e "${BLUE}📋 Seeding Order:${NC}"
echo "   1. Users & Roles"
echo "   2. Currencies & Exchange Rates"
echo "   3. Branches & Balances"
echo "   4. Vaults & Transfers (NEW)"
echo "   5. Customers & Documents"
echo "   6. Sample Transactions"
echo ""
echo -e "${YELLOW}Starting in 3 seconds...${NC}"
sleep 3
echo ""

# 1. Basic data (users, roles)
run_seed "seed_data.py" "Basic Data (Users & Roles)"

# 2. Currencies
run_seed "seed_currencies.py" "Currencies & Exchange Rates"

# 3. Branches
run_seed "seed_branches.py" "Branches & Balances"

# 4. Vaults (NEW)
run_seed "seed_vaults.py" "Vaults & Transfers"

# 5. Customers
run_seed "seed_customers.py" "Customers & Documents"

# 6. Transactions
run_seed "seed_transactions.py" "Sample Transactions"

echo "=================================="
echo -e "${GREEN}✨ All seeding completed successfully!${NC}"
echo ""
echo "📊 Database Summary:"
echo "   ✅ Users & Roles"
echo "   ✅ Currencies (7)"
echo "   ✅ Exchange Rates"
echo "   ✅ Branches (3)"
echo "   ✅ Vaults (4) - 1 Main + 3 Branch"
echo "   ✅ Vault Balances (24)"
echo "   ✅ Vault Transfers (4)"
echo "   ✅ Customers (8)"
echo "   ✅ Transactions (15+)"
echo ""
echo "🚀 System Ready!"
echo ""
echo "📖 Test the System:"
echo "   • API Docs: http://localhost:8000/docs"
echo "   • Login: POST /api/v1/auth/login"
echo "   • Vaults: GET /api/v1/vault"
echo "   • Transfers: GET /api/v1/vault/transfers"
echo "   • Branches: GET /api/v1/branches"
echo "   • Transactions: GET /api/v1/transactions"
echo ""
echo "💡 Quick Commands:"
echo "   • Show vaults: python scripts/seed_vaults.py --show"
echo "   • Reset DB: make db-reset && bash scripts/SEED_USAGE.sh"
echo ""
