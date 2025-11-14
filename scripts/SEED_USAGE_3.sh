#!/bin/bash
# 🌱 Complete CEMS Database Seeding Script - 10X VERSION
# Runs all seed scripts in the correct order with proper error handling
#
# ENHANCEMENTS:
# - 10x data volume (110+ customers, 470+ transactions, 40+ vault transfers)
# - Distributed data across last 6 months
# - Realistic statuses and varied data
#
# Usage:
#   ./SEED_USAGE_3.sh              # Run complete seeding

set -e  # Exit on error

echo "🌱 CEMS Complete Database Seeding - 10X VERSION"
echo "================================================"
echo ""

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
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
echo -e "${MAGENTA}🌟 Seeding Plan - 10X Data Volume${NC}"
echo ""
echo -e "${BLUE}📋 Seeding Steps (6 Phases):${NC}"
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
echo "   ${CYAN}Phase 5:${NC} Customer Management ${GREEN}(10X!)${NC}"
echo "   ├─ 4️⃣  110+ Customers & Documents"
echo ""
echo "   ${CYAN}Phase 6:${NC} Transaction Management ${GREEN}(10X!)${NC}"
echo "   ├─ 5️⃣  470+ Sample Transactions"
echo ""
echo "   ${CYAN}Phase 7:${NC} Vault Management ${GREEN}(10X!)${NC}"
echo "   └─ 6️⃣  40+ Vault Transfers"
echo ""
echo -e "${GREEN}✨ What you'll get:${NC}"
echo "      • 110+ customers (85% individual, 15% corporate)"
echo "      • 200+ documents (National IDs, Passports, etc.)"
echo "      • 470+ transactions:"
echo "        - 130 Income transactions"
echo "        - 100 Expense transactions"
echo "        - 150 Exchange transactions"
echo "        - 90 Transfer transactions"
echo "      • 40+ vault transfers (varied statuses)"
echo "      • Data distributed across last 6 months"
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

run_seed "seed_data.py" "Users & Roles (Phase 1-2)"
run_seed "seed_currencies.py" "Currencies & Exchange Rates (Phase 3)"
run_seed "seed_branches.py" "Branches & Balances (Phase 4)"
run_seed "seed_customers.py" "Customers & Documents (Phase 5) - 10X"
run_seed "seed_transactions.py" "Sample Transactions (Phase 6) - 10X"
run_seed "seed_vaults.py" "Vaults & Transfers (Phase 7) - 10X"

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
echo "      └─ 8 currencies (USD, EUR, TRY, SAR, AED, GBP, EGP, JPY)"
echo "      └─ Exchange rates matrix"
echo ""
echo "   ${GREEN}✅${NC} Branches"
echo "      └─ 4-5 branches across different regions"
echo "      └─ Multi-currency branch balances"
echo ""
echo "   ${GREEN}✅${NC} Customers ${MAGENTA}(10X!)${NC}"
echo "      └─ 110 customers (85% individual, 15% corporate)"
echo "      └─ 200+ documents (verified & pending)"
echo "      └─ 110+ notes"
echo "      └─ Risk levels: low, medium, high"
echo ""
echo "   ${GREEN}✅${NC} Transactions ${MAGENTA}(10X!)${NC}"
echo "      └─ 470 total transactions:"
echo "         • 130 Income (commissions, fees)"
echo "         • 100 Expense (rent, salaries, utilities)"
echo "         • 150 Exchange (currency conversions)"
echo "         • 90 Transfer (branch-to-branch)"
echo "      └─ Distributed across last 6 months"
echo "      └─ Varied statuses (completed, pending, in-transit)"
echo ""
echo "   ${GREEN}✅${NC} Vaults ${MAGENTA}(10X!)${NC}"
echo "      └─ 1 Main vault + Branch vaults"
echo "      └─ 40 vault transfers:"
echo "         • 28 Completed (70%)"
echo "         • 6 In-Transit (15%)"
echo "         • 4 Pending (10%)"
echo "         • 2 Cancelled (5%)"
echo "      └─ Multi-currency balances"
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
echo "   • Customers:    GET    /api/v1/customers"
echo "   • Transactions: GET    /api/v1/transactions"
echo "   • Vaults:       GET    /api/v1/vault"
echo "   • Transfers:    GET    /api/v1/vault/transfers"
echo "   • Branches:     GET    /api/v1/branches"
echo ""
echo -e "${YELLOW}3. Login Credentials:${NC}"
echo "   Username: admin"
echo "   Password: Admin@123"
echo "   ⚠️  Change password after first login!"
echo ""
echo -e "${YELLOW}4. Useful Commands:${NC}"
echo "   • Re-run seeding:      ./scripts/SEED_USAGE_3.sh"
echo "   • Show customers:      python scripts/seed_customers.py --show"
echo "   • Show transactions:   python scripts/seed_transactions.py --show"
echo "   • Show vaults:         python scripts/seed_vaults.py --show"
echo "   • Check migrations:    alembic current"
echo "   • Reset database:      docker compose down -v && docker compose up -d"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Happy Testing! 🎉${NC}"
echo ""
