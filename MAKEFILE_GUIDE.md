# 📘 Makefile Quick Reference Guide

## 🚀 Quick Start Workflows

### First Time Setup (Docker - Recommended)
```bash
make setup
```
This will:
1. Install development dependencies
2. Create .env file from template
3. Start Docker containers
4. Run all database migrations
5. Seed database with sample data

**After setup, the system is ready to use!**

### First Time Setup (Local - Without Docker)
```bash
# 1. Create .env file
make check-env

# 2. Create PostgreSQL database (requires PostgreSQL installed)
make init-db

# 3. Apply migrations
make db-upgrade

# 4. Seed data
make seed-all

# 5. Run application
make run
```

---

## 🐳 Docker Workflows

### Complete Docker Reset (Recommended)
```bash
make docker-reset
```
This exactly matches your required workflow:
- Stops containers and removes volumes (`docker compose down -v`)
- Starts containers (`docker compose up -d`)
- Waits for services to be ready
- Applies migrations (`alembic upgrade head`)
- Cleans Python cache
- Runs all seeding scripts

### Basic Docker Commands
```bash
make docker-up        # Start containers
make docker-down      # Stop containers
make docker-build     # Rebuild images
make docker-logs      # View application logs
make docker-shell     # Access container shell
```

---

## 🗄️ Database Management

### Environment Verification
```bash
make check-env
```
Verifies that:
- `.env` file exists (creates it if missing)
- `DATABASE_URL` is configured correctly
- Shows warnings if configuration is incomplete

**Automatically runs before:**
- `make run`
- `make db-upgrade`

### Local Database Initialization (Non-Docker)
```bash
make init-db
```
Creates PostgreSQL database, user, and grants privileges for **local development** (not needed for Docker).

**⚠️ Prerequisites:**
- PostgreSQL must be installed and running locally
- `postgres` superuser must be accessible

This creates:
- User: `cems_user` with password `cems_password_2025`
- Database: `cems_db` owned by `cems_user`

**For Docker users:** Skip this command - Docker Compose handles database creation automatically.

### Fresh Database
```bash
make db-fresh
```
Resets database completely and seeds all data (equivalent to `db-reset` + `seed-all`)

### Migrations
```bash
make db-upgrade       # Apply all pending migrations
make db-downgrade     # Rollback last migration
make db-reset         # Reset to base then upgrade to head
make migrate          # Create new migration (interactive)
```

---

## 🌱 Data Seeding

### Seed Everything (Recommended)
```bash
make seed-all
```
Runs `SEED_USAGE_3.sh` which executes all 6 seeding scripts in correct order:
1. Users & Roles
2. Currencies & Exchange Rates
3. Branches & Balances
4. Customers & Documents
5. Transactions
6. **Vaults & Transfers** (Phase 7)

### Individual Seeding
```bash
make seed-users         # Phase 1-2: Users and roles
make seed-currencies    # Phase 3: Currencies
make seed-branches      # Phase 4: Branches
make seed-customers     # Phase 5: Customers
make seed-transactions  # Phase 6: Transactions
make seed-vaults        # Phase 7: Vaults ⭐
```

### Vault Summary
```bash
make vault-summary
```
Displays a formatted summary of all vault balances by currency

---

## 🧪 Testing & Code Quality

### Run Tests
```bash
make test              # All tests with coverage report
make test-unit         # Unit tests only
make test-integration  # Integration tests only
```

### Code Quality
```bash
make format            # Format with black + isort
make lint              # Run flake8 + mypy
make check             # format + lint + test (full check)
```

---

## 🚀 Running the Application

### Development Mode
```bash
make run
```
Starts uvicorn with auto-reload on `http://localhost:8000`

### Production Mode
```bash
make run-prod
```
Starts uvicorn with 4 workers (no auto-reload)

### Access Points
- **API**: http://localhost:8000
- **Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🧹 Cleaning

### Clean Cache Files
```bash
make clean
```
Removes `__pycache__`, `.pyc`, `.pyo`, test caches, etc.

### Complete Reset (DANGER!)
```bash
make reset-all
```
⚠️ **WARNING**: This deletes ALL data including Docker volumes!

---

## 💡 Common Workflows

### 1. Fresh Start (New Developer)
```bash
make setup
```

### 2. Daily Development
```bash
make docker-up        # Start services
make run              # Start development server
```

### 3. After Pulling New Code
```bash
make db-upgrade       # Apply new migrations
make seed-vaults      # Seed new vault data if needed
```

### 4. Testing Your Changes
```bash
make check            # Run format + lint + tests
```

### 5. Database Issues? Complete Reset
```bash
make docker-reset     # Nuclear option - fresh everything
```

### 6. Just Need Fresh Data
```bash
make db-fresh         # Reset DB and reseed
```

---

## 📊 Vault Management Commands

### View Vault Status
```bash
make vault-summary
```
Shows:
- All vaults (Main + Branch vaults)
- Currency balances
- Total amounts
- Active status

### Seed Vault Data
```bash
make seed-vaults
```
Creates:
- 1 Main vault
- 3 Branch vaults (one per branch)
- 24 vault balances (4 vaults × 6 currencies)
- 4 sample transfers (various statuses)

---

## 🔍 Troubleshooting

### "Database connection failed"
1. Check `.env` file has correct `DATABASE_URL`
2. Ensure Docker is running: `make docker-up`
3. Wait a few seconds for PostgreSQL to be ready

### "Relation does not exist" errors
```bash
make db-upgrade       # Apply migrations first
```

### "Seeding fails"
```bash
make db-fresh         # Reset and reseed everything
```

### "Everything is broken"
```bash
make docker-reset     # Start completely fresh
```

---

## 📝 Environment Variables

Make sure your `.env` file has:

```env
# Critical for database connection
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db

# For Docker, use 'db' as host instead of 'localhost'
DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@db:5432/cems_db
```

See `ENV_SETUP_NOTES.md` for detailed configuration instructions.

---

## 🎯 Default Credentials

After running `make setup` or `make seed-all`:

```
Username: admin
Password: Admin@123
```

**⚠️ IMPORTANT:** Change this password immediately after first login!

---

## 📚 Additional Documentation

- `DATABASE_SETUP.md` - Complete database setup guide
- `VAULT_FIXES_SUMMARY.md` - All Phase 7 fixes explained
- `ENV_SETUP_NOTES.md` - Critical .env configuration
- `README.md` - Project overview

---

## ⚡ Pro Tips

1. **Always use `make docker-reset`** when switching branches with DB changes
2. **Use `make vault-summary`** to verify vault data after seeding
3. **Run `make check`** before committing code
4. **Use `make docker-logs`** to debug runtime issues
5. **Keep `.env` file private** - never commit it!

---

**Current Branch**: `claude/fix-vault-transfer-backref-011CUx1oLKncJGS1P59g9kxS`
**Status**: ✅ All Phase 7 fixes applied and tested
**Last Updated**: 2025-11-09
