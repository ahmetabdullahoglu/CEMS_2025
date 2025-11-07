#!/bin/bash

# Quick Transaction Endpoints Test Script
# ========================================

BASE_URL="http://localhost:8000/api/v1"
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJjMTdmMTA2MS0yMzMyLTQwZDQtODhjZC1hNDM5MzdiN2UyMzAiLCJ1c2VybmFtZSI6ImFkbWluIiwiZW1haWwiOiJhZG1pbkBjZW1zLmNvIiwiZXhwIjoxNzYyNTA1OTgxLCJpYXQiOjE3NjI1MDUwODEsInR5cGUiOiJhY2Nlc3MifQ.pf9Z4jjQvTVBAB-05NGjC5VYWV52nO0TVLSFlSl1HbU"

# IDs from your system
BRANCH_ID="2608e84b-9cdb-443a-ab20-58e7eb6bc552"
CURRENCY_ID="b4ed7308-fe95-4459-b1ed-f14cca268321"
CUSTOMER_ID="585ce667-eea6-48b2-b23a-2f743ce5d0cc"

echo "========================================="
echo "Transaction Endpoints Quick Test"
echo "========================================="
echo ""

# Test 1: Create Income Transaction
echo "📊 Test 1: Create Income Transaction"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'POST' \
  "${BASE_URL}/transactions/income" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H 'Content-Type: application/json' \
  -d "{
    \"amount\": 150.5,
    \"branch_id\": \"${BRANCH_ID}\",
    \"currency_id\": \"${CURRENCY_ID}\",
    \"customer_id\": \"${CUSTOMER_ID}\",
    \"income_category\": \"service_fee\",
    \"income_source\": \"Test service fee\",
    \"reference_number\": \"TEST-INC-$(date +%s)\"
  }")

if echo "$RESPONSE" | jq -e '.id' > /dev/null 2>&1; then
  echo "✅ PASSED - Income transaction created"
  INCOME_ID=$(echo "$RESPONSE" | jq -r '.id')
  echo "   Transaction ID: $INCOME_ID"
else
  echo "❌ FAILED - Income transaction creation"
  echo "   Response: $(echo $RESPONSE | jq -r '.error.message // .detail // .')"
fi
echo ""

# Test 2: List Income Transactions
echo "📋 Test 2: List Income Transactions"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions/income?limit=5" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total')
  echo "✅ PASSED - Listed income transactions"
  echo "   Total: $TOTAL"
else
  echo "❌ FAILED - List income transactions"
  echo "   Response: $(echo $RESPONSE | jq -r '.error.message // .detail // .')"
fi
echo ""

# Test 3: Create Expense Transaction
echo "💸 Test 3: Create Expense Transaction"
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
  echo "✅ PASSED - Expense transaction created"
  EXPENSE_ID=$(echo "$RESPONSE" | jq -r '.id')
  echo "   Transaction ID: $EXPENSE_ID"
else
  echo "❌ FAILED - Expense transaction creation"
  echo "   Response: $(echo $RESPONSE | jq -r '.error.message // .detail // .')"
fi
echo ""

# Test 4: List All Transactions
echo "📊 Test 4: List All Transactions"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions?limit=10" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total')
  echo "✅ PASSED - Listed all transactions"
  echo "   Total: $TOTAL"
else
  echo "❌ FAILED - List all transactions"
  echo "   Response: $(echo $RESPONSE | jq -r '.error.message // .detail // .')"
fi
echo ""

# Test 5: Get Transaction Statistics
echo "📈 Test 5: Get Transaction Statistics"
echo "-------------------------------------"
RESPONSE=$(curl -s -X 'GET' \
  "${BASE_URL}/transactions/stats/summary" \
  -H "Authorization: Bearer ${TOKEN}")

if echo "$RESPONSE" | jq -e '.total_count' > /dev/null 2>&1; then
  TOTAL=$(echo "$RESPONSE" | jq -r '.total_count')
  echo "✅ PASSED - Got transaction statistics"
  echo "   Total Count: $TOTAL"
else
  echo "❌ FAILED - Get transaction statistics"
  echo "   Response: $(echo $RESPONSE | jq -r '.error.message // .detail // .')"
fi
echo ""

echo "========================================="
echo "Test Summary"
echo "========================================="
echo "✅ = Test Passed"
echo "❌ = Test Failed"
echo ""
echo "For detailed responses, run individual curl commands"
echo "========================================="
