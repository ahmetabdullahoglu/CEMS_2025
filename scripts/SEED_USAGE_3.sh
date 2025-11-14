#!/bin/bash
# 🌱 Complete CEMS Database Seeding Script
# Runs all seed scripts in the correct order with proper error handling
#
# Usage:
#   ./SEED_USAGE_3.sh              # Default: Use new comprehensive seeding
#   ./SEED_USAGE_3.sh --legacy     # Use legacy individual seed scripts
#   ./SEED_USAGE_3.sh --small      # Use comprehensive seeding with less data

set -e  # Exit on error

# Parse arguments
MODE="comprehensive"
SMALL_MODE=""

for arg in "$@"; do
    case $arg in
        --legacy)
            MODE="legacy"
            shift
            ;;
        --small)
            SMALL_MODE="--small"
            shift
            ;;
        *)
            ;;
    esac
done

echo "🌱 CEMS Complete Database Seeding"
echo "===================================="
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
if [ "$MODE" = "comprehensive" ]; then
    TOTAL_STEPS=4
else
    TOTAL_STEPS=6
fi
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
if [ "$MODE" = "comprehensive" ]; then
    echo -e "${MAGENTA}🌟 Using NEW Comprehensive Seeding Mode${NC}"
    [ -n "$SMALL_MODE" ] && echo -e "${YELLOW}   (Small mode: reduced dataset)${NC}"
    echo ""
    echo -e "${BLUE}📋 Seeding Plan (4 Steps):${NC}"
    echo ""
    echo "   ${CYAN}Phase 1-2:${NC} Foundation & Authentication"
    echo "   ├─ 1️⃣  Users & Roles (admin, managers, tellers)"
    echo ""
    echo "   ${CYAN}Phase 3:${NC} Currency Management"
    echo "   ├─ 2️⃣  Currencies & Exchange Rates"
    echo ""
    echo "   ${CYAN}Phase 4:${NC} Branch Management"
    echo "   ├─ 3️⃣  Branches & Balances"
    echo ""
    echo "   ${CYAN}Phase 5-7:${NC} ${MAGENTA}Comprehensive Data${NC} ⭐ ${GREEN}(NEW!)${NC}"
    echo "   └─ 4️⃣  Users, Customers, Vaults, Transactions (All-in-One)"
    echo ""
    echo -e "${GREEN}✨ What you'll get:${NC}"
    if [ -n "$SMALL_MODE" ]; then
        echo "      • 10 users, 30 customers, 60 transactions"
    else
        echo "      • 30+ users (2 admins, 10 managers, 18+ tellers)"
        echo "      • 150+ customers with documents & notes"
        echo "      • 20+ vaults with multi-currency balances"
        echo "      • 50+ vault transfers"
        echo "      • 750+ transactions (Exchange, Transfer, Income, Expense)"
    fi
else
    echo -e "${YELLOW}📦 Using Legacy Seeding Mode${NC}"
    echo ""
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
    echo "   ${CYAN}Phase 7:${NC} Vault Management"
    echo "   └─ 6️⃣  Vaults & Transfers"
fi
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

# Common steps for both modes
run_seed "seed_data.py" "Users & Roles (Phase 1-2)"
run_seed "seed_currencies.py" "Currencies & Exchange Rates (Phase 3)"
run_seed "seed_branches.py" "Branches & Balances (Phase 4)"

# Mode-specific execution
if [ "$MODE" = "comprehensive" ]; then
    # New comprehensive seeding
    print_step "Comprehensive Data (Phase 5-7)"
    echo -e "${YELLOW}▶ Running: seed_comprehensive.py ${SMALL_MODE}${NC}"
    echo ""

    if python scripts/seed_comprehensive.py $SMALL_MODE; then
        echo ""
        echo -e "${GREEN}✅ Comprehensive Data completed successfully${NC}"
        echo ""
    else
        echo ""
        echo -e "${RED}❌ Comprehensive Data failed${NC}"
        echo -e "${RED}Error: Seeding stopped at step ${CURRENT_STEP}/${TOTAL_STEPS}${NC}"
        exit 1
    fi
else
    # Legacy individual seeding
    run_seed "seed_customers.py" "Customers & Documents (Phase 5)"
    run_seed "seed_transactions.py" "Sample Transactions (Phase 6)"
    run_seed "seed_vaults.py" "Vaults & Transfers (Phase 7)"
fi

# ==================== Success Summary ====================

echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ All Seeding Completed Successfully! ✨${NC}"
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${BLUE}📊 Database Summary:${NC}"
echo ""

if [ "$MODE" = "comprehensive" ]; then
    echo "   ${GREEN}✅${NC} Users & Roles"
    echo "      └─ 3 default roles (admin, manager, teller)"
    if [ -n "$SMALL_MODE" ]; then
        echo "      └─ 10+ users"
    else
        echo "      └─ 30+ users (2 admins, 10 managers, 18+ tellers)"
    fi
    echo ""
    echo "   ${GREEN}✅${NC} Currencies"
    echo "      └─ 8 currencies (USD, EUR, TRY, SAR, AED, GBP, EGP, JPY)"
    echo "      └─ Complete exchange rates matrix"
    echo ""
    echo "   ${GREEN}✅${NC} Branches"
    echo "      └─ 4-5 branches across different regions"
    echo "      └─ Multi-currency balances per branch"
    echo ""
    echo "   ${GREEN}✅${NC} Customers ${MAGENTA}(COMPREHENSIVE!)${NC}"
    if [ -n "$SMALL_MODE" ]; then
        echo "      └─ 30 customers"
    else
        echo "      └─ 150+ customers (85% individual, 15% corporate)"
    fi
    echo "      └─ 1-3 documents per customer (verified)"
    echo "      └─ 0-3 notes per customer"
    echo ""
    echo "   ${GREEN}✅${NC} Vaults ${MAGENTA}(COMPREHENSIVE!)${NC}"
    if [ -n "$SMALL_MODE" ]; then
        echo "      └─ 6-8 vaults"
        echo "      └─ 15+ vault transfers"
    else
        echo "      └─ 20+ vaults (Main, Cash, Foreign Currency, Reserve)"
        echo "      └─ 50+ vault transfers (various statuses)"
    fi
    echo "      └─ Multi-currency balances"
    echo ""
    echo "   ${GREEN}✅${NC} Transactions ${MAGENTA}(COMPREHENSIVE!)${NC}"
    if [ -n "$SMALL_MODE" ]; then
        echo "      └─ 60+ transactions"
    else
        echo "      └─ 750+ transactions"
    fi
    echo "      └─ 60% Exchange, 20% Transfer, 10% Income, 10% Expense"
    echo "      └─ Distributed across last 6 months"
    echo "      └─ Realistic statuses and amounts"
else
    echo "   ${GREEN}✅${NC} Users & Roles"
    echo "      └─ 3 default roles (admin, manager, teller)"
    echo "      └─ 1 admin user"
    echo ""
    echo "   ${GREEN}✅${NC} Currencies"
    echo "      └─ 8 currencies (USD, EUR, TRY, SAR, AED, GBP, EGP, JPY)"
    echo "      └─ Exchange rates matrix"
    echo ""
    echo "   ${GREEN}✅${NC} Branches"
    echo "      └─ 4-5 branches"
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
    echo "   ${GREEN}✅${NC} Vaults"
    echo "      └─ 1 Main vault + 3 Branch vaults"
    echo "      └─ Vault balances and transfers"
fi
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
echo -e "${YELLOW}3. Login Credentials:${NC}"
if [ "$MODE" = "comprehensive" ]; then
    echo "   ${MAGENTA}Admin:${NC}"
    echo "      Username: admin  |  Password: Admin@123"
    echo ""
    echo "   ${MAGENTA}Managers:${NC}"
    echo "      manager01 to manager10  |  Password: Password@123"
    echo ""
    echo "   ${MAGENTA}Tellers:${NC}"
    echo "      teller01 to teller18  |  Password: Password@123"
else
    echo "   Username: admin"
    echo "   Password: Admin@123"
fi
echo "   ⚠️  Change passwords after first login!"
echo ""
echo -e "${YELLOW}4. Useful Commands:${NC}"
if [ "$MODE" = "comprehensive" ]; then
    echo "   • Re-run seeding:      ./scripts/SEED_USAGE_3.sh"
    echo "   • Small dataset:       ./scripts/SEED_USAGE_3.sh --small"
    echo "   • Legacy mode:         ./scripts/SEED_USAGE_3.sh --legacy"
else
    echo "   • Show vault summary:  python scripts/seed_vaults.py --show"
fi
echo "   • Check migrations:    alembic current"
echo "   • Reset database:      docker compose down -v && docker compose up -d"
echo ""
echo -e "${CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${GREEN}Happy Testing! 🎉${NC}"
echo ""
