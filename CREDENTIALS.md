# 🔐 CEMS Default Credentials

## ⚠️ IMPORTANT SECURITY NOTICE

**These are DEFAULT credentials created during database seeding.**
**You MUST change these passwords immediately after first login!**

---

## 👤 Default Admin Account

After running database seeding (`make seed-all` or `python scripts/seed_data.py`):

```
Username: admin
Password: Admin@123
Email:    admin@cems.co
```

### Login Instructions

1. **Via API Docs (Recommended for Testing)**
   - Open: http://localhost:8000/docs
   - Click "Authorize" button (top right)
   - Enter credentials above
   - Click "Authorize"

2. **Via API Endpoint**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/auth/login" \
     -H "Content-Type: application/json" \
     -d '{
       "username": "admin",
       "password": "Admin@123"
     }'
   ```

3. **Via Test Script**
   ```bash
   ./quick_test_transactions.sh
   ```

---

## 🔒 Password Requirements

When changing the default password, ensure it meets these requirements:
- Minimum length: 8 characters
- Contains at least one uppercase letter
- Contains at least one lowercase letter
- Contains at least one number
- Contains at least one special character (@, #, $, etc.)

---

## 📝 Notes

### Where These Credentials Are Used

All of the following files now use the **same standardized credentials**:

1. **Database Seeding:**
   - `scripts/seed_data.py` - Creates the admin user

2. **Documentation:**
   - `Makefile` - Shows credentials after setup
   - `MAKEFILE_GUIDE.md` - Documents default login
   - `scripts/SEED_USAGE_3.sh` - Displays after seeding

3. **Testing:**
   - `tests/integration/test_currencies.py` - Integration tests
   - `tests/integration/test_api_auth.py` - Auth tests
   - `quick_test_transactions.sh` - Quick test script

4. **API Documentation:**
   - `app/api/v1/endpoints/auth.py` - Example in docs

### Admin User Details

The default admin user is created with:
- **Full Name:** System Administrator
- **Phone:** +90 555 000 0000
- **Role:** admin (superuser)
- **Permissions:** All permissions
- **Status:** Active

### How to Change Password

1. Login with default credentials
2. Navigate to user settings/profile
3. Change password to a strong, unique password
4. Store new password securely (password manager recommended)

---

## 🔐 Security Best Practices

1. **Never use default passwords in production**
2. **Change all default credentials immediately**
3. **Use a password manager** to generate and store strong passwords
4. **Enable two-factor authentication** when implemented
5. **Regularly rotate passwords** (every 90 days recommended)
6. **Use different passwords** for different environments (dev, staging, prod)
7. **Never commit credentials** to version control
8. **Use environment variables** for sensitive configuration

---

## 🚨 Security Incident Response

If you suspect the default credentials have been compromised:

1. **Immediately change the password** via the API or database
2. **Review audit logs** for unauthorized access
3. **Invalidate all existing tokens** by restarting the application
4. **Check for unauthorized changes** to users, roles, or permissions
5. **Enable additional security measures** (IP restrictions, rate limiting)

---

## 📚 Related Documentation

- `ENV_SETUP_NOTES.md` - Environment configuration
- `DATABASE_SETUP.md` - Database setup guide
- `MAKEFILE_GUIDE.md` - Makefile commands reference
- `README.md` - Project overview

---

**Last Updated:** 2025-11-09
**Version:** 1.0
**Status:** ✅ All credentials standardized and verified
