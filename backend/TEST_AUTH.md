# Authentication Testing Guide

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run migrations:
```bash
cd backend
alembic upgrade head
```

3. Start the server:
```bash
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

---

## API Endpoints

### 1. Register a New User

Create a new account.

**Request:**
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "MySecurePassword123"
  }'
```

**Success Response (201):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2026-11-15T10:30:00"
  }
}
```

**Error Responses:**

- Invalid email format (400):
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "not-an-email",
    "password": "MySecurePassword123"
  }'
# Returns: {"detail":"Invalid email format"}
```

- Password too short (400):
```bash
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "email": "john@example.com",
    "password": "short"
  }'
# Returns: {"detail":"Password must be at least 8 characters"}
```

- Email already registered (409):
```bash
# After first registration, try again:
curl -X POST "http://localhost:8000/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Jane Doe",
    "email": "john@example.com",
    "password": "MySecurePassword123"
  }'
# Returns: {"detail":"Email already registered"}
```

---

### 2. Login

Get access token for existing user.

**Request:**
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "MySecurePassword123"
  }'
```

**Success Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "name": "John Doe",
    "email": "john@example.com",
    "created_at": "2026-11-15T10:30:00"
  }
}
```

**Error Responses:**

- Invalid credentials (401):
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john@example.com",
    "password": "WrongPassword"
  }'
# Returns: {"detail":"Invalid email or password"}
```

- User not found (401):
```bash
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "nonexistent@example.com",
    "password": "MySecurePassword123"
  }'
# Returns: {"detail":"Invalid email or password"}
```

---

### 3. Get Current User

Get authenticated user's profile.

**Request (save token from login/register first):**
```bash
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

**Success Response (200):**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "John Doe",
  "email": "john@example.com",
  "created_at": "2026-11-15T10:30:00"
}
```

**Error Responses:**

- Missing authorization header (401):
```bash
curl -X GET "http://localhost:8000/auth/me"
# Returns: {"detail":"Missing authorization header","headers":{"WWW-Authenticate":"Bearer"}}
```

- Invalid/expired token (401):
```bash
curl -X GET "http://localhost:8000/auth/me" \
  -H "Authorization: Bearer invalid-token-here"
# Returns: {"detail":"Invalid or expired token","headers":{"WWW-Authenticate":"Bearer"}}
```

---

## Complete Test Flow

Run all tests in sequence:

```bash
#!/bin/bash

API="http://localhost:8000"

echo "=== 1. REGISTER ===" 
REGISTER_RESPONSE=$(curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test User",
    "email": "test@example.com",
    "password": "TestPassword123"
  }')

echo "$REGISTER_RESPONSE"
TOKEN=$(echo "$REGISTER_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo ""
echo "=== 2. GET ME (with token) ==="
curl -s -X GET "$API/auth/me" \
  -H "Authorization: Bearer $TOKEN" | jq .

echo ""
echo "=== 3. LOGIN (fresh) ==="
LOGIN_RESPONSE=$(curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPassword123"
  }')

echo "$LOGIN_RESPONSE" | jq .
NEW_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

echo ""
echo "=== 4. GET ME (with new token) ==="
curl -s -X GET "$API/auth/me" \
  -H "Authorization: Bearer $NEW_TOKEN" | jq .

echo ""
echo "=== 5. ERROR: Invalid credentials ==="
curl -s -X POST "$API/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "WrongPassword"
  }' | jq .

echo ""
echo "=== 6. ERROR: Email already registered ==="
curl -s -X POST "$API/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Another User",
    "email": "test@example.com",
    "password": "TestPassword123"
  }' | jq .
```

---

## Database

### View Users

```bash
# SQLite
sqlite3 birdclef.db "SELECT id, name, email, created_at FROM users;"
```

### View Recordings

```bash
sqlite3 birdclef.db "SELECT id, user_id, original_filename, status, created_at FROM recordings;"
```

### Reset Database

```bash
# Delete database and recreate
rm birdclef.db

# Run migrations
alembic upgrade head
```

---

## Swagger UI

View interactive API documentation:

```
http://localhost:8000/docs
```

All endpoints are documented and can be tested directly from the browser.

---

## Response Status Codes

| Code | Meaning | 
|------|---------|
| 200  | OK - Successful request |
| 201  | Created - Resource created (register) |
| 400  | Bad Request - Invalid input |
| 401  | Unauthorized - Missing/invalid token |
| 409  | Conflict - Email already registered |
| 422  | Unprocessable Entity - Invalid request format |
| 500  | Server Error |

