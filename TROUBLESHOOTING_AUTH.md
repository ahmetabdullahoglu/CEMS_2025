# 🔧 Authentication Troubleshooting Guide

## Problem: "Invalid username or password" Error

If you're getting **401 Unauthorized** when trying to login with `admin / Admin@123`, follow these steps:

---

## 🔍 Step 1: Verify Docker is Using Latest Code

### Problem
Docker might be using an old image that has the old password (`admin123` instead of `Admin@123`)

### Solution

```bash
# 1. Stop and remove all containers and volumes
make reset-all

# 2. Rebuild Docker images (IMPORTANT!)
docker compose build --no-cache

# 3. Start fresh with new images
make setup
```

**This ensures Docker uses the latest code with the correct password.**

---

## 🧪 Step 2: Run Diagnostic Scripts

### Check Database

Run the authentication debugger:

```bash
# Inside Docker container:
docker compose exec app python scripts/debug_auth.py
```

This will:
- ✅ Check if admin user exists
- ✅ Verify account is active and not locked
- ✅ Test password verification
- ✅ Automatically fix password if needed
- ✅ Show database statistics

### Test Login API

Test the login endpoint directly:

```bash
# Inside Docker container:
docker compose exec app python scripts/test_login.py
```

This will:
- ✅ Test API connectivity
- ✅ Attempt login with correct credentials
- ✅ Attempt login with wrong credentials (to verify rejection works)
- ✅ Show detailed error messages

---

## 📋 Step 3: Manual Verification

### Check User in Database

```bash
# Connect to PostgreSQL
docker compose exec postgres psql -U cems_user -d cems_db

# Check if admin user exists
SELECT username, email, is_active, is_superuser, is_locked, failed_login_attempts
FROM users
WHERE username = 'admin';

# Exit psql
\q
```

Expected output:
```
 username |     email      | is_active | is_superuser | is_locked | failed_login_attempts
----------+----------------+-----------+--------------+-----------+-----------------------
 admin    | admin@cems.co  | t         | t            | f         |                     0
```

### Check Seeding Logs

```bash
# View app logs
docker compose logs app | grep -A 10 "Creating superuser"
```

You should see:
```
Creating superuser account...
  ✓ Created superuser 'admin'
  📧 Email: admin@cems.co
  🔑 Password: Admin@123
```

---

## 🔧 Step 4: Common Issues & Fixes

### Issue 1: Old Docker Image

**Symptom**: Everything looks correct but login still fails

**Cause**: Docker is using old image with old password hash

**Fix**:
```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
sleep 5
docker compose exec app alembic upgrade head
docker compose exec app python scripts/seed_data.py
```

### Issue 2: Account Locked

**Symptom**: Account locked after multiple failed attempts

**Fix**:
```bash
# Run inside container
docker compose exec app python scripts/debug_auth.py
```

The script will automatically unlock the account.

Or manually:
```bash
docker compose exec postgres psql -U cems_user -d cems_db -c \
  "UPDATE users SET is_locked = FALSE, locked_until = NULL, failed_login_attempts = 0 WHERE username = 'admin';"
```

### Issue 3: User Doesn't Exist

**Symptom**: Debug script says "Admin user does not exist"

**Fix**:
```bash
# Re-run seeding
docker compose exec app python scripts/seed_data.py
```

### Issue 4: Password Hash Mismatch

**Symptom**: Debug script shows password verification fails

**Fix**:
```bash
# The debug script will automatically fix this
docker compose exec app python scripts/debug_auth.py
```

Or manually update:
```bash
docker compose exec app python -c "
from app.core.security import get_password_hash
print(get_password_hash('Admin@123'))
"
# Copy the output hash

docker compose exec postgres psql -U cems_user -d cems_db -c \
  "UPDATE users SET hashed_password = 'PASTE_HASH_HERE' WHERE username = 'admin';"
```

### Issue 5: Wrong Endpoint

**Symptom**: 404 Not Found

**Fix**: Make sure you're using the correct endpoint:
```
POST http://localhost:8000/api/v1/auth/login
```

Not:
- ❌ `/auth/login`
- ❌ `/api/auth/login`
- ❌ `/login`

### Issue 6: Wrong Request Format

**Symptom**: 422 Validation Error

**Fix**: Ensure your request body is correct JSON:
```json
{
  "username": "admin",
  "password": "Admin@123"
}
```

Not:
- ❌ Form data
- ❌ URL parameters
- ❌ x-www-form-urlencoded

---

## 🧪 Step 5: Test via API Docs

The easiest way to test:

1. Open: http://localhost:8000/docs
2. Find `/api/v1/auth/login` endpoint
3. Click "Try it out"
4. Enter credentials:
   ```json
   {
     "username": "admin",
     "password": "Admin@123"
   }
   ```
5. Click "Execute"

If this works, the issue is with your API client, not the server.

---

## 📊 Step 6: Check Docker Logs

```bash
# View real-time logs
make docker-logs

# Or
docker compose logs -f app

# Look for errors around authentication
docker compose logs app | grep -i "error\|auth\|login"
```

Common log messages:
- ✅ `INFO: "POST /api/v1/auth/login HTTP/1.1" 200 OK` - Success!
- ❌ `INFO: "POST /api/v1/auth/login HTTP/1.1" 401 Unauthorized` - Wrong credentials
- ❌ `INFO: "POST /api/v1/auth/login HTTP/1.1" 422 Unprocessable Entity` - Validation error

---

## ✅ Verification Checklist

After fixing, verify:

- [ ] Docker container is using latest code (`docker compose build --no-cache`)
- [ ] Database has admin user (`docker compose exec app python scripts/debug_auth.py`)
- [ ] User is active and not locked (check debug output)
- [ ] Password hash is correct (debug script verifies this)
- [ ] Login via API docs works (http://localhost:8000/docs)
- [ ] Login via curl works:
  ```bash
  curl -X POST "http://localhost:8000/api/v1/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"username":"admin","password":"Admin@123"}'
  ```

---

## 🆘 Still Not Working?

If none of the above works:

### Nuclear Option: Complete Reset

```bash
# 1. Stop everything
docker compose down -v

# 2. Remove ALL Docker images
docker image rm $(docker images 'cems*' -q) 2>/dev/null || true

# 3. Clean Python cache
make clean

# 4. Rebuild from scratch
docker compose build --no-cache

# 5. Fresh start
docker compose up -d
sleep 10

# 6. Apply migrations
docker compose exec app alembic upgrade head

# 7. Seed data
docker compose exec app python scripts/seed_data.py

# 8. Test
docker compose exec app python scripts/test_login.py
```

### Collect Debug Info

If still failing, collect this info:

```bash
# 1. Check code version in container
docker compose exec app cat scripts/seed_data.py | grep "Admin@123"

# 2. Check database state
docker compose exec app python scripts/debug_auth.py > debug_output.txt

# 3. Check API logs
docker compose logs app > app_logs.txt

# 4. Test login
docker compose exec app python scripts/test_login.py > test_output.txt
```

Then review these files for clues.

---

## 📚 Related Files

- `CREDENTIALS.md` - Default credentials documentation
- `scripts/debug_auth.py` - Authentication debugger
- `scripts/test_login.py` - Login API tester
- `scripts/seed_data.py` - User seeding script
- `app/core/security.py` - Password hashing functions
- `app/services/auth_service.py` - Authentication service

---

## 🎯 Quick Reference

**Correct Credentials:**
```
Username: admin
Password: Admin@123
Email: admin@cems.co
```

**Common Commands:**
```bash
# Rebuild and restart
docker compose down -v && docker compose build --no-cache && docker compose up -d

# Debug authentication
docker compose exec app python scripts/debug_auth.py

# Test login
docker compose exec app python scripts/test_login.py

# Re-seed users
docker compose exec app python scripts/seed_data.py

# View logs
make docker-logs
```

---

**Last Updated**: 2025-11-09
**Version**: 1.0
