# 🎯 CEMS Command Reference Guide

Quick reference for all common commands used in CEMS development.

---

## 📦 Installation & Setup

```bash
# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Or use Make
make install           # Production
make dev-install       # Development

# Complete setup (first time)
make setup
```

---

## 🐳 Docker Commands

### Development Environment

```bash
# Start all services
make docker-up
# or
docker-compose -f docker-compose.dev.yml up -d

# Stop all services
make docker-down

# Rebuild containers
make docker-build

# View logs
make docker-logs
# or
docker-compose -f docker-compose.dev.yml logs -f app

# Access app container shell
make docker-shell
docker-compose -f docker-compose.dev.yml exec app /bin/sh

# Access database
make db-shell
docker-compose -f docker-compose.dev.yml exec postgres psql -U cems_user -d cems_db

# Access Redis CLI
make redis-cli
docker-compose -f docker-compose.dev.yml exec redis redis-cli

# View container status
docker-compose -f docker-compose.dev.yml ps

# Remove volumes (DANGER - deletes data!)
docker-compose -f docker-compose.dev.yml down -v
```

### Production Environment

```bash
# Start production services
make docker-prod-up
docker-compose up -d

# Stop production services
make docker-prod-down

# Rebuild production images
make docker-prod-build
```

---

## 🏃 Running the Application

```bash
# Development mode (with auto-reload)
make run
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode (with workers)
make run-prod
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With custom host/port
uvicorn app.main:app --host 0.0.0.0 --port 8080

# Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# ReDoc: http://localhost:8000/redoc
```

---

## 🗄️ Database & Migrations

### Alembic Migrations

```bash
# Create a new migration (auto-generate from models)
make migrate
alembic revision --autogenerate -m "description of changes"

# Apply all pending migrations
make db-upgrade
alembic upgrade head

# Rollback last migration
make db-downgrade
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# View migration history
make db-history
alembic history

# View current revision
alembic current

# Reset database (DANGER!)
make db-reset
alembic downgrade base
alembic upgrade head
```

### Database Operations

```bash
# Connect to PostgreSQL
psql -h localhost -U cems_user -d cems_db

# Inside psql:
\dt                    # List tables
\d table_name          # Describe table
\du                    # List users
\l                     # List databases
\c database_name       # Switch database
\q                     # Quit

# Backup database
pg_dump -h localhost -U cems_user cems_db > backup.sql

# Restore database
psql -h localhost -U cems_user cems_db < backup.sql

# Database reset (development only)
docker-compose -f docker-compose.dev.yml down -v
docker-compose -f docker-compose.dev.yml up -d
make db-upgrade
```

---

## 🧪 Testing

```bash
# Run all tests
make test
pytest

# Run tests with coverage
pytest --cov=app --cov-report=html --cov-report=term

# Run specific test file
pytest tests/unit/test_models.py

# Run specific test function
pytest tests/unit/test_models.py::test_user_creation

# Run unit tests only
make test-unit
pytest tests/unit/

# Run integration tests only
make test-integration
pytest tests/integration/

# Run tests with markers
pytest -m unit                    # Only unit tests
pytest -m integration             # Only integration tests
pytest -m "not slow"              # Skip slow tests

# Run tests in parallel (faster)
pytest -n auto

# Run tests with verbose output
pytest -v

# Stop on first failure
pytest -x

# Show local variables in tracebacks
pytest -l

# Update snapshots (if using snapshot testing)
pytest --snapshot-update
```

---

## 🎨 Code Quality

### Formatting

```bash
# Format code with black
black app/ tests/

# Format with line length
black app/ tests/ --line-length 88

# Check without making changes
black app/ tests/ --check

# Format imports with isort
isort app/ tests/

# Check imports
isort app/ tests/ --check-only

# Both at once
make format
```

### Linting

```bash
# Run flake8
flake8 app/ tests/

# Run with specific config
flake8 app/ --max-line-length=88 --extend-ignore=E203

# Run mypy (type checking)
mypy app/

# Run all linters
make lint

# Run all checks (format + lint + test)
make check
```

---

## 📝 Logging & Monitoring

```bash
# View application logs
tail -f logs/app.log

# View error logs only
tail -f logs/error.log

# View all logs with make
make logs

# Clear logs
rm -rf logs/*.log

# Docker logs
docker-compose -f docker-compose.dev.yml logs -f app

# Follow logs from multiple containers
docker-compose -f docker-compose.dev.yml logs -f app postgres redis
```

---

## 🧹 Cleanup

```bash
# Clean Python cache files
make clean
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Clean test cache
rm -rf .pytest_cache/ .coverage htmlcov/

# Clean Docker volumes (DANGER!)
make reset-all
docker-compose -f docker-compose.dev.yml down -v
docker volume prune

# Clean all (code + docker + uploads)
make clean
rm -rf uploads/* logs/* temp/*
```

---

## 📊 Database Queries (Quick Reference)

### PostgreSQL

```sql
-- List all tables
SELECT tablename FROM pg_tables WHERE schemaname = 'public';

-- Count rows in table
SELECT COUNT(*) FROM table_name;

-- Check database size
SELECT pg_size_pretty(pg_database_size('cems_db'));

-- Check table size
SELECT pg_size_pretty(pg_total_relation_size('table_name'));

-- Find slow queries
SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;

-- Active connections
SELECT * FROM pg_stat_activity WHERE datname = 'cems_db';

-- Kill connection
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE pid = <PID>;
```

### Redis

```bash
# Connect to Redis
redis-cli

# Inside redis-cli:
PING                   # Test connection
INFO                   # Server info
DBSIZE                 # Number of keys
KEYS *                 # List all keys (avoid in production)
GET key_name           # Get value
SET key_name value     # Set value
DEL key_name           # Delete key
FLUSHDB                # Clear current database (DANGER!)
FLUSHALL               # Clear all databases (DANGER!)
```

---

## 🚀 Deployment

```bash
# Build production image
docker build -t cems:latest .

# Tag image
docker tag cems:latest registry.example.com/cems:latest

# Push to registry
docker push registry.example.com/cems:latest

# Pull on server
docker pull registry.example.com/cems:latest

# Run production containers
docker-compose up -d

# Update running containers
docker-compose pull
docker-compose up -d

# View production logs
docker-compose logs -f --tail=100

# Backup production database
docker-compose exec postgres pg_dump -U cems_user cems_db > backup_$(date +%Y%m%d).sql
```

---

## 🔍 Debugging

```bash
# Python debugger
python -m pdb app/main.py

# IPython debugger
python -m ipdb app/main.py

# Debug with pytest
pytest --pdb                           # Drop to debugger on failure
pytest --pdb-trace                     # Drop to debugger at start

# Print SQL queries
# In .env:
# DEBUG=True

# Interactive Python shell
python
>>> from app.db.base import engine
>>> from app.db.models import User

# IPython shell (better)
ipython
```

---

## 📦 Python Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate (Linux/Mac)
source venv/bin/activate

# Activate (Windows)
venv\Scripts\activate

# Deactivate
deactivate

# Install requirements
pip install -r requirements.txt

# Freeze installed packages
pip freeze > requirements.txt

# Update all packages
pip list --outdated
pip install -U package_name
```

---

## 🔐 Security

```bash
# Generate SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate password hash
python -c "from passlib.context import CryptContext; print(CryptContext(schemes=['bcrypt']).hash('your_password'))"

# Check security headers
curl -I http://localhost:8000/health

# Scan for vulnerabilities
safety check

# Update dependencies
pip-review --auto
```

---

## 💡 Pro Tips

```bash
# Quick health check
curl http://localhost:8000/health | jq

# Test API endpoint
curl -X POST http://localhost:8000/api/v1/endpoint \
  -H "Content-Type: application/json" \
  -d '{"key": "value"}' | jq

# Watch logs in real-time
tail -f logs/app.log | grep ERROR

# Count lines of code
find app/ -name "*.py" | xargs wc -l

# Find TODO comments
grep -r "TODO" app/

# Git shortcuts
git status -sb                         # Short status
git log --oneline --graph --all       # Pretty log
git diff --stat                        # Summary of changes
```

---

## 📚 Quick Links

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **PGAdmin:** http://localhost:5050
- **Redis Commander:** http://localhost:8081

---

**Last Updated:** 2025-01-09