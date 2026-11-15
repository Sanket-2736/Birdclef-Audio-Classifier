#!/bin/bash

# Color codes for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API="http://localhost:8000"
EMAIL="test_$(date +%s)@example.com"  # Unique email based on timestamp

echo -e "${YELLOW}=== BirdCLEF Authentication Test Suite ===${NC}\n"

# Test 1: Register
echo -e "${YELLOW}1. Testing REGISTER${NC}"
REGISTER_RESPONSE=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test User\",
    \"email\": \"$EMAIL\",
    \"password\": \"TestPassword123\"
  }")

TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
  echo -e "${RED}✗ Registration failed${NC}"
  echo "$REGISTER_RESPONSE"
  exit 1
else
  echo -e "${GREEN}✓ Registration successful${NC}"
  echo "  Email: $EMAIL"
  echo "  Token: ${TOKEN:0:20}..."
fi

echo ""

# Test 2: Get current user
echo -e "${YELLOW}2. Testing GET /auth/me${NC}"
ME_RESPONSE=$(curl -s -X GET "$API/auth/me" \
  -H "Authorization: Bearer $TOKEN")

USER_NAME=$(echo "$ME_RESPONSE" | grep -o '"name":"[^"]*' | head -1 | cut -d'"' -f4)

if [ "$USER_NAME" = "Test User" ]; then
  echo -e "${GREEN}✓ Get user successful${NC}"
  echo "  Name: $USER_NAME"
  echo "  Response: $(echo $ME_RESPONSE | cut -c1-100)..."
else
  echo -e "${RED}✗ Get user failed${NC}"
  echo "$ME_RESPONSE"
  exit 1
fi

echo ""

# Test 3: Login with different password (should fail)
echo -e "${YELLOW}3. Testing LOGIN with wrong password (should fail)${NC}"
LOGIN_WRONG=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"WrongPassword\"
  }")

ERROR=$(echo "$LOGIN_WRONG" | grep -o '"detail":"[^"]*' | head -1 | cut -d'"' -f4)

if [ "$ERROR" = "Invalid email or password" ]; then
  echo -e "${GREEN}✓ Correct error for invalid password${NC}"
  echo "  Error: $ERROR"
else
  echo -e "${RED}✗ Expected error not received${NC}"
  echo "$LOGIN_WRONG"
  exit 1
fi

echo ""

# Test 4: Login with correct password
echo -e "${YELLOW}4. Testing LOGIN with correct password${NC}"
LOGIN_CORRECT=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d "{
    \"email\": \"$EMAIL\",
    \"password\": \"TestPassword123\"
  }")

NEW_TOKEN=$(echo "$LOGIN_CORRECT" | grep -o '"access_token":"[^"]*' | head -1 | cut -d'"' -f4)

if [ -z "$NEW_TOKEN" ]; then
  echo -e "${RED}✗ Login failed${NC}"
  echo "$LOGIN_CORRECT"
  exit 1
else
  echo -e "${GREEN}✓ Login successful${NC}"
  echo "  Token: ${NEW_TOKEN:0:20}..."
fi

echo ""

# Test 5: Duplicate email
echo -e "${YELLOW}5. Testing REGISTER with duplicate email (should fail)${NC}"
DUP_EMAIL=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Another User\",
    \"email\": \"$EMAIL\",
    \"password\": \"TestPassword123\"
  }")

ERROR=$(echo "$DUP_EMAIL" | grep -o '"detail":"[^"]*' | head -1 | cut -d'"' -f4)

if [ "$ERROR" = "Email already registered" ]; then
  echo -e "${GREEN}✓ Correct error for duplicate email${NC}"
  echo "  Error: $ERROR"
else
  echo -e "${RED}✗ Expected error not received${NC}"
  echo "$DUP_EMAIL"
  exit 1
fi

echo ""

# Test 6: Invalid email format
echo -e "${YELLOW}6. Testing REGISTER with invalid email (should fail)${NC}"
INVALID_EMAIL=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test User\",
    \"email\": \"not-an-email\",
    \"password\": \"TestPassword123\"
  }")

ERROR=$(echo "$INVALID_EMAIL" | grep -o '"detail":"[^"]*' | head -1 | cut -d'"' -f4)

if [ "$ERROR" = "Invalid email format" ]; then
  echo -e "${GREEN}✓ Correct error for invalid email${NC}"
  echo "  Error: $ERROR"
else
  echo -e "${RED}✗ Expected error not received${NC}"
  echo "$INVALID_EMAIL"
  exit 1
fi

echo ""

# Test 7: Password too short
echo -e "${YELLOW}7. Testing REGISTER with short password (should fail)${NC}"
SHORT_PASSWORD=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test User\",
    \"email\": \"test2_$(date +%s)@example.com\",
    \"password\": \"short\"
  }")

ERROR=$(echo "$SHORT_PASSWORD" | grep -o '"detail":"[^"]*' | head -1 | cut -d'"' -f4)

if [[ "$ERROR" == *"8 characters"* ]]; then
  echo -e "${GREEN}✓ Correct error for short password${NC}"
  echo "  Error: $ERROR"
else
  echo -e "${RED}✗ Expected error not received${NC}"
  echo "$SHORT_PASSWORD"
  exit 1
fi

echo ""

# Test 8: Invalid token
echo -e "${YELLOW}8. Testing GET /auth/me with invalid token (should fail)${NC}"
INVALID_TOKEN=$(curl -s -X GET "$API/auth/me" \
  -H "Authorization: Bearer invalid-token-here")

ERROR=$(echo "$INVALID_TOKEN" | grep -o '"detail":"[^"]*' | head -1 | cut -d'"' -f4)

if [[ "$ERROR" == *"Invalid or expired token"* ]]; then
  echo -e "${GREEN}✓ Correct error for invalid token${NC}"
  echo "  Error: $ERROR"
else
  echo -e "${RED}✗ Expected error not received${NC}"
  echo "$INVALID_TOKEN"
  exit 1
fi

echo ""
echo -e "${GREEN}=== ALL TESTS PASSED! ===${NC}"
