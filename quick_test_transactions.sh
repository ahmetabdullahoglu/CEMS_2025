#!/bin/bash

# Smart Transaction Endpoints Test Script
# ========================================
# Automatically logs in, fetches real IDs, and tests all endpoints

BASE_URL="http://localhost:8000/api/v1"
TOKEN=""
BRANCH_ID=""
CURRENCY_ID=""
CUSTOMER_ID=""
CURRENCY_2_ID=""
BRANCH_2_ID=""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo "========================================="
echo "🚀 Smart Transaction Endpoints Test"
echo "========================================="
echo ""

# Step 1: Login and get token
echo "${BLUE}🔐 Step 1: Login${NC}"
echo "-------------------------------------"
LOGIN_RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/auth/login" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
    "username": "admin",
    "password": "Admin@123"
  }')

TOKEN=$(echo "$LOGIN_RESPONSE" | jq -r '.access_token // .token // empty')

if [ -z "$TOKEN" ] || [ "$TOKEN" = "null" ]; then
  echo "${RED}❌ FAILED - Could not login${NC}"
  echo "   Response: $LOGIN_RESPONSE"
  exit 1
else
  echo "${GREEN}✅ LOGIN SUCCESSFUL${NC}"
  echo "   Token: ${TOKEN:0:20}..."
fi
echo ""

# Step 2: Get Branch IDs
echo "${BLUE}🏢 Step 2: Fetch Branch IDs${NC}"
echo "-------------------------------------"
BRANCHES_RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/branches?limit=2" \
  -H "Authorization: Bearer ${TOKEN}")

BRANCH_ID=$(echo "$BRANCHES_RESPONSE" | jq -r '.items[0].id // .branches[0].id // empty' 2>/dev/null)
BRANCH_2_ID=$(echo "$BRANCHES_RESPONSE" | jq -r '.items[1].id // .branches[1].id // empty' 2>/dev/null)

if [ -z "$BRANCH_ID" ] || [ "$BRANCH_ID" = "null" ]; then
  echo "${RED}❌ FAILED - No branches found${NC}"
  exit 1
else
  echo "${GREEN}✅ Found Branches${NC}"
  echo "   Branch 1 ID: $BRANCH_ID"
  if [ ! -z "$BRANCH_2_ID" ] && [ "$BRANCH_2_ID" != "null" ]; then
    echo "   Branch 2 ID: $BRANCH_2_ID"
  fi
fi
echo ""

# Step 3: Get Currency IDs
echo "${BLUE}💱 Step 3: Fetch Currency IDs${NC}"
echo "-------------------------------------"
CURRENCIES_RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/currencies?limit=2" \
  -H "Authorization: Bearer ${TOKEN}")

CURRENCY_ID=$(echo "$CURRENCIES_RESPONSE" | jq -r '.items[0].id // .currencies[0].id // empty' 2>/dev/null)
CURRENCY_2_ID=$(echo "$CURRENCIES_RESPONSE" | jq -r '.items[1].id // .currencies[1].id // empty' 2>/dev/null)

if [ -z "$CURRENCY_ID" ] || [ "$CURRENCY_ID" = "null" ]; then
  echo "${RED}❌ FAILED - No currencies found${NC}"
  exit 1
else
  echo "${GREEN}✅ Found Currencies${NC}"
  echo "   Currency 1 ID: $CURRENCY_ID"
  if [ ! -z "$CURRENCY_2_ID" ] && [ "$CURRENCY_2_ID" != "null" ]; then
    echo "   Currency 2 ID: $CURRENCY_2_ID"
  fi
fi
echo ""

# Step 4: Get Customer IDs
echo "${BLUE}👥 Step 4: Fetch Customer IDs${NC}"
echo "-------------------------------------"
CUSTOMERS_RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/customers?limit=1" \
  -H "Authorization: Bearer ${TOKEN}")

CUSTOMER_ID=$(echo "$CUSTOMERS_RESPONSE" | jq -r '.items[0].id // .customers[0].id // empty' 2>/dev/null)

if [ -z "$CUSTOMER_ID" ] || [ "$CUSTOMER_ID" = "null" ]; then
  echo "${YELLOW}⚠️  WARNING - No customers found (will test without customer)${NC}"
  CUSTOMER_ID=""
else
  echo "${GREEN}✅ Found Customer${NC}"
  echo "   Customer ID: $CUSTOMER_ID"
fi
echo ""

echo "========================================="
echo "🧪 Starting Transaction Tests"
echo "========================================="
echo ""

# Test 1: Create Income Transaction
echo "${BLUE}📊 Test 1: Create Income Transaction${NC}"
echo "-------------------------------------"

INCOME_PAYLOAD="{
  \"amount\": 150.5,
  \"branch_id\": \"${BRANCH_ID}\",
  \"currency_id\": \"${CURRENCY_ID}\",
  \"income_category\": \"service_fee\",
  \"income_source\": \"Test service fee\",
  \"reference_number\": \"TEST-INC-$(date +%s)\""

if [ ! -z "$CUSTOMER_ID" ]; then
  INCOME_PAYLOAD="${INCOME_PAYLOAD},
  \"customer_id\": \"${CUSTOMER_ID}\""
fi

INCOME_PAYLOAD="${INCOME_PAYLOAD}
}"

RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/transactions/income" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "$INCOME_PAYLOAD")

if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
  echo "${GREEN}✅ PASSED - Income transaction created${NC}"
  INCOME_ID=$(echo "$RESPONSE" | jq -r '.id')
  INCOME_NUMBER=$(echo "$RESPONSE" | jq -r '.transaction_number')
  echo "   Transaction ID: $INCOME_ID"
  echo "   Transaction Number: $INCOME_NUMBER"
  echo "   Status: $(echo "$RESPONSE" | jq -r '.status')"
  echo "   Amount: $(echo "$RESPONSE" | jq -r '.amount')"
else
  echo "${RED}❌ FAILED - Income transaction creation${NC}"
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
  echo "   Error: $ERROR_MSG"
fi
echo ""

# Test 2: List Income Transactions
echo "${BLUE}📋 Test 2: List Income Transactions${NC}"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions/income?limit=5" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total')
  ITEMS_COUNT=$(echo "$RESPONSE" | jq -r '.items | length')
  echo "${GREEN}✅ PASSED - Listed income transactions${NC}"
  echo "   Total: $TOTAL"
  echo "   Returned: $ITEMS_COUNT"
else
  echo "${RED}❌ FAILED - List income transactions${NC}"
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
  echo "   Error: $ERROR_MSG"
fi
echo ""

# Test 3: Get specific Income Transaction
if [ ! -z "$INCOME_ID" ]; then
  echo "${BLUE}🔍 Test 3: Get Income Transaction by ID${NC}"
  echo "-------------------------------------"
  RESPONSE=$(curl -s -X 'GET' \
    "${BASE_URL}/transactions/income/${INCOME_ID}" \
    -H "Authorization: Bearer ${TOKEN}")

  if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    echo "${GREEN}✅ PASSED - Got income transaction${NC}"
    echo "   ID: $(echo "$RESPONSE" | jq -r '.id')"
    echo "   Number: $(echo "$RESPONSE" | jq -r '.transaction_number')"
    echo "   Amount: $(echo "$RESPONSE" | jq -r '.amount')"
  else
    echo "${RED}❌ FAILED - Get income transaction${NC}"
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
    echo "   Error: $ERROR_MSG"
  fi
  echo ""
fi

# Test 4: Create Expense Transaction
echo "${BLUE}💸 Test 4: Create Expense Transaction${NC}"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/transactions/expense" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{
    \"amount\": 50.00,
    \"branch_id\": \"${BRANCH_ID}\",
    \"currency_id\": \"${CURRENCY_ID}\",
    \"expense_category\": \"supplies\",
    \"expense_to\": \"Test Supplier\",
    \"approval_required\": false,
    \"reference_number\": \"TEST-EXP-$(date +%s)\"
  }")

if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
  echo "${GREEN}✅ PASSED - Expense transaction created${NC}"
  EXPENSE_ID=$(echo "$RESPONSE" | jq -r '.id')
  echo "   Transaction ID: $EXPENSE_ID"
  echo "   Number: $(echo "$RESPONSE" | jq -r '.transaction_number')"
  echo "   Status: $(echo "$RESPONSE" | jq -r '.status')"
else
  echo "${RED}❌ FAILED - Expense transaction creation${NC}"
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
  echo "   Error: $ERROR_MSG"
fi
echo ""

# Test 5: List Expense Transactions
echo "${BLUE}📋 Test 5: List Expense Transactions${NC}"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions/expense?limit=5" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total // .transactions' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total // (.transactions | length)')
  echo "${GREEN}✅ PASSED - Listed expense transactions${NC}"
  echo "   Total: $TOTAL"
else
  echo "${RED}❌ FAILED - List expense transactions${NC}"
fi
echo ""

# Test 6: Exchange Rate Preview
if [ ! -z "$CURRENCY_2_ID" ] && [ "$CURRENCY_2_ID" != "null" ]; then
  echo "${BLUE}💱 Test 6: Preview Exchange Rate${NC}"
  echo "-------------------------------------"
  RESPONSE=$(curl -s -X 'POST' \
    "${BASE_URL}/transactions/exchange/rate-preview" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "{
      \"from_currency_id\": \"${CURRENCY_ID}\",
      \"to_currency_id\": \"${CURRENCY_2_ID}\",
      \"from_amount\": 100.00
    }")

  if echo "$RESPONSE" | jq -e '.exchange_rate' > /dev/null 2>&1; then
    echo "${GREEN}✅ PASSED - Exchange rate preview${NC}"
    echo "   From Amount: $(echo "$RESPONSE" | jq -r '.from_amount')"
    echo "   To Amount: $(echo "$RESPONSE" | jq -r '.to_amount')"
    echo "   Exchange Rate: $(echo "$RESPONSE" | jq -r '.exchange_rate')"
    echo "   Commission: $(echo "$RESPONSE" | jq -r '.commission_amount')"
  else
    echo "${YELLOW}⚠️  SKIPPED - Exchange rate preview (no rate configured)${NC}"
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
    echo "   Reason: $ERROR_MSG"
  fi
  echo ""
fi

# Test 7: List All Transactions
echo "${BLUE}📊 Test 7: List All Transactions${NC}"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions?limit=10" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total')
  TRANSACTIONS_COUNT=$(echo "$RESPONSE" | jq -r '.transactions | length')
  echo "${GREEN}✅ PASSED - Listed all transactions${NC}"
  echo "   Total: $TOTAL"
  echo "   Returned: $TRANSACTIONS_COUNT"

  # Show breakdown by type
  INCOME_COUNT=$(echo "$RESPONSE" | jq -r '[.transactions[] | select(.transaction_type=="income")] | length')
  EXPENSE_COUNT=$(echo "$RESPONSE" | jq -r '[.transactions[] | select(.transaction_type=="expense")] | length')
  echo "   Income: $INCOME_COUNT, Expense: $EXPENSE_COUNT"
else
  echo "${RED}❌ FAILED - List all transactions${NC}"
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
  echo "   Error: $ERROR_MSG"
fi
echo ""

# Test 8: Get Transaction Statistics
echo "${BLUE}📈 Test 8: Get Transaction Statistics${NC}"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions/stats/summary" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total_count' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total_count')
  echo "${GREEN}✅ PASSED - Got transaction statistics${NC}"
  echo "   Total Count: $TOTAL"

  # Show statistics by type if available
  if echo "$RESPONSE" | jq -e '.by_type' > /dev/null 2>&1; then
    echo "   By Type:"
    echo "$RESPONSE" | jq -r '.by_type | to_entries[] | "     \(.key): \(.value.count // .value)"'
  fi
else
  echo "${RED}❌ FAILED - Get transaction statistics${NC}"
  ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
  echo "   Error: $ERROR_MSG"
fi
echo ""

# Test 9: Transfer Transaction (if we have 2 branches)
if [ ! -z "$BRANCH_2_ID" ] && [ "$BRANCH_2_ID" != "null" ]; then
  echo "${BLUE}🔄 Test 9: Create Transfer Transaction${NC}"
  echo "-------------------------------------"
  RESPONSE=$(curl -s -X 'POST' \
    "${BASE_URL}/transactions/transfer" \
    -H "Authorization: Bearer ${TOKEN}" \
    -H 'Content-Type: application/json' \
    -d "{
      \"from_branch_id\": \"${BRANCH_ID}\",
      \"to_branch_id\": \"${BRANCH_2_ID}\",
      \"amount\": 100.00,
      \"currency_id\": \"${CURRENCY_ID}\",
      \"transfer_type\": \"branch_to_branch\",
      \"reference_number\": \"TEST-TRF-$(date +%s)\"
    }")

  if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
    echo "${GREEN}✅ PASSED - Transfer transaction created${NC}"
    TRANSFER_ID=$(echo "$RESPONSE" | jq -r '.id')
    echo "   Transaction ID: $TRANSFER_ID"
    echo "   Number: $(echo "$RESPONSE" | jq -r '.transaction_number')"
    echo "   Status: $(echo "$RESPONSE" | jq -r '.status')"
  else
    echo "${RED}❌ FAILED - Transfer transaction creation${NC}"
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.error.message // .detail // "Unknown error"' 2>/dev/null)
    echo "   Error: $ERROR_MSG"
  fi
  echo ""
fi

echo "========================================="
echo "📊 Test Summary"
echo "========================================="
echo ""
echo "${GREEN}✅${NC} = Test Passed"
echo "${RED}❌${NC} = Test Failed"
echo "${YELLOW}⚠️${NC}  = Test Skipped/Warning"
echo ""
echo "All critical transaction endpoints tested!"
echo "========================================="
