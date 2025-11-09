#!/bin/bash
# 🌱 Complete CEMS Database Seeding Script
# Runs all seed scripts in the correct order with proper error handling

set -e  # Exit on error

echo "🌱 CEMS Complete Database Seeding"
echo "===================================="
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Counters
TOTAL_STEPS=6
CURRENT_STEP=0

# Function to print step header
print_step() {
    CURRENT_STEP=$((CURRENT_STEP + 1))
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}[${CURRENT_STEP}/${TOTAL_STEPS}] $1${NC}"
    echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Function to run seed script
run_seed() {
    local script=$1
    local name=$2

    print_step "$name"

    echo -e "${YELLOW}▶ Running: ${script}${NC}"
    echo ""

    # Run the script and capture output
    if python scripts/${script}; then
        echo ""
        echo -e "${GREEN}✅ ${name} completed successfully${NC}"
        echo ""
        return 0
    else
        echo ""
        echo -e "${RED}❌ ${name} failed${NC}"
        echo -e "${RED}Error: Seeding stopped at step ${CURRENT_STEP}/${TOTAL_STEPS}${NC}"
        echo ""
        echo -e "${YELLOW}💡 Troubleshooting:${NC}"
        echo "   1. Check that migrations are applied: alembic current"
        echo "   2. Verify database connection in .env file"
        echo "   3. Check script logs above for specific errors"
        echo "   4. Review DATABASE_SETUP.md for detailed instructions"
        echo ""
        exit 1
    fi
}

# Display seeding plan
echo -e "${BLUE}📋 Seeding Plan (6 Steps):${NC}"
echo ""
echo "   ${CYAN}Phase 1-2:${NC} Foundation & Authentication"
echo "   ├─ 1️⃣  Users & Roles"
echo ""
echo "   ${CYAN}Phase 3:${NC} Currency Management"
echo "   ├─ 2️⃣  Currencies & Exchange Rates"
echo ""
echo "   ${CYAN}Phase 4:${NC} Branch Management"
echo "   ├─ 3️⃣  Branches & Balances"
echo ""
echo "   ${CYAN}Phase 5:${NC} Customer Management"
echo "   ├─ 4️⃣  Customers & Documents"
echo ""
echo "   ${CYAN}Phase 6:${NC} Transaction Management"
echo "   ├─ 5️⃣  Sample Transactions"
echo ""
echo "   ${CYAN}Phase 7:${NC} Vault Management ⭐ ${GREEN}(NEW!)${NC}"
echo "   └─ 6️⃣  Vaults & Transfers"
echo ""
echo -e "${YELLOW}⏳ Starting in 3 seconds...${NC}"
sleep 1
echo -e "${YELLOW}⏳ 2...${NC}"
sleep 1
echo -e "${YELLOW}⏳ 1...${NC}"
sleep 1
echo ""
echo -e "${GREEN}🚀 Starting seeding process...${NC}"
echo ""
sleep 1

# ==================== Execute Seeding Scripts ====================

# Step 1: Users & Roles (Foundation)
run_seed "seed_data.py" "Users & Roles (Phase 1-2)"

# Step 2: Currencies
run_seed "seed_currencies.py" "Currencies & Exchange Rates (Phase 3)"

# Step 3: Branches
run_seed "seed_branches.py" "Branches & Balances (Phase 4)"

# Step 4: Customers
run_seed "seed_customers.py" "Customers & Documents (Phase 5)"

# Step 5: Transactions
run_seed "seed_transactions.py" "Sample Transactions (Phase 6)"

# Step 6: Vaults (NEW!)
run_seed "seed_vaults.py" "Vaults & Transfers (Phase 7)"

# ==================== Success Summary ====================

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ All Seeding Completed Successfully! ✨${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📊 Database Summary:${NC}"
echo ""
echo "   ${GREEN}✅${NC} Users & Roles"
echo "      └─ 3 default roles (admin, manager, teller)"
echo "      └─ 1 admin user"
echo ""
echo "   ${GREEN}✅${NC} Currencies"
echo "      └─ 7 currencies (USD, EUR, TRY, SAR, AED, GBP, EGP)"
echo "      └─ Exchange rates matrix"
echo ""
echo "   ${GREEN}✅${NC} Branches"
echo "      └─ 3 branches (BR001, BR002, BR003)"
echo "      └─ Branch balances by currency"
echo ""
echo "   ${GREEN}✅${NC} Customers"
echo "      └─ 8 sample customers"
echo "      └─ Customer documents & notes"
echo ""
echo "   ${GREEN}✅${NC} Transactions"
echo "      └─ Income, Expense, Exchange, Transfer"
echo "      └─ 15+ sample transactions"
echo ""
echo "   ${GREEN}✅${NC} Vaults ${CYAN}(NEW!)${NC}"
echo "      └─ 1 Main vault + 3 Branch vaults"
echo "      └─ 24 vault balances"
echo "      └─ 4 sample transfers (completed, pending, in-transit)"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}🚀 System is Ready for Use!${NC}"
echo ""
echo -e "${BLUE}📖 Quick Start Guide:${NC}"
echo ""
echo -e "${YELLOW}1. API Documentation:${NC}"
echo "   http://localhost:8000/docs"
echo ""
echo -e "${YELLOW}2. Test Endpoints:${NC}"
echo "   • Login:        POST   /api/v1/auth/login"
echo "   • Vaults:       GET    /api/v1/vault"
echo "   • Transfers:    GET    /api/v1/vault/transfers"
echo "   • Branches:     GET    /api/v1/branches"
echo "   • Transactions: GET    /api/v1/transactions"
echo "   • Customers:    GET    /api/v1/customers"
echo ""
echo -e "${YELLOW}3. Default Login:${NC}"
echo "   Username: admin"
echo "   Password: admin123"
echo ""
echo -e "${YELLOW}4. Useful Commands:${NC}"
echo "   • Show vault summary:  python scripts/seed_vaults.py --show"
echo "   • Check migrations:    alembic current"
echo "   • Reset database:      docker compose down -v && docker compose up -d"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Happy Testing! 🎉${NC}"
echo ""
