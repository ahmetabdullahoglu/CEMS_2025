# 🚀 CEMS Project Setup Guide

## ✅ Prerequisites

Before starting, ensure you have:

- **Python 3.11+** installed
- **Docker** and **Docker Compose** installed
- **Git** installed
- **PostgreSQL 15+** (if running locally without Docker)
- **Redis** (if running locally without Docker)

---

## 📦 Installation Methods

### Method 1: Quick Setup with Docker (Recommended)

This is the fastest way to get started!

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/CEMS_2025.git
cd CEMS_2025

# 2. Create .env file from example
cp .env.example .env

# 3. Generate a secure SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
# Copy the output and paste it in .env as SECRET_KEY

# 4. Run complete setup (installs deps, starts Docker, runs migrations)
make setup

# 5. Access the application
# API: http://localhost:8000
# Docs: http://localhost:8000/docs
# PGAdmin: http://localhost:5050 (admin@cems.co / admin)
# Redis Commander: http://localhost:8081
```

### Method 2: Manual Setup

```bash
# 1. Clone the repository
git clone https://github.com/your-repo/CEMS_2025.git
cd CEMS_2025

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements-dev.txt

# 4. Create .env file
cp .env.example .env

# Edit .env and set your configuration:
# - Generate SECRET_KEY: python -c "import secrets; print(secrets.token_urlsafe(32))"
# - Set database credentials
# - Configure other settings as needed

# 5. Start Docker services (PostgreSQL + Redis)
make docker-up

# Or start them separately:
# docker-compose -f docker-compose.dev.yml up -d postgres redis

# 6. Wait for database to be ready (about 10 seconds)
sleep 10

# 7. Run database migrations
make db-upgrade

# 8. Start the application
make run

# Application will be available at http://localhost:8000
```

---

## 🔧 Configuration

### Environment Variables

Edit `.env` file with your settings:

```env
# Application
DEBUG=True
SECRET_KEY=your_secret_key_here_min_32_chars

# Database
POSTGRES_SERVER=localhost  # or 'postgres' for Docker
POSTGRES_USER=cems_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=cems_db

# Redis
REDIS_HOST=localhost  # or 'redis' for Docker
REDIS_PORT=6379

# CORS
BACKEND_CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

---

## 🧪 Testing the Setup

### 1. Health Check

```bash
# Test if API is running
curl http://localhost:8000/health

# Expected response:
# {
#   "success": true,
#   "status": "healthy",
#   "version": "1.0.0",
#   "environment": "development"
# }
```

### 2. API Documentation

Visit http://localhost:8000/docs to see the interactive API documentation (Swagger UI).

### 3. Test API Endpoint

```bash
# Test ping endpoint
curl http://localhost:8000/api/v1/ping

# Expected response:
# {
#   "success": true,
#   "message": "pong"
# }
```

---

## 🛠️ Common Commands

### Development

```bash
# Start application with auto-reload
make run

# Run tests
make test

# Run specific tests
make test-unit
make test-integration

# Format code
make format

# Lint code
make lint

# Run all checks (format + lint + test)
make check
```

### Docker

```bash
# Start all services
make docker-up

# Stop all services
make docker-down

# Rebuild images
make docker-build

# View logs
make docker-logs

# Access app container shell
make docker-shell

# Access database
make db-shell

# Access Redis CLI
make redis-cli
```

### Database Migrations

```bash
# Create new migration
make migrate
# You'll be prompted to enter a message

# Apply migrations
make db-upgrade

# Rollback last migration
make db-downgrade

# View migration history
make db-history

# Reset database (DANGER!)
make db-reset
```

---

## 📁 Project Structure

```
CEMS_2025/
├── app/                          # Application code
│   ├── api/v1/endpoints/         # API endpoints
│   ├── core/                     # Core configuration
│   │   ├── config.py            # Settings
│   │   ├── constants.py         # Enums & constants
│   │   └── exceptions.py        # Custom exceptions
│   ├── db/                       # Database
│   │   ├── base.py              # SQLAlchemy setup
│   │   ├── base_class.py        # Base model
│   │   └── models/              # Database models
│   ├── services/                 # Business logic
│   ├── repositories/             # Data access layer
│   ├── schemas/                  # Pydantic schemas
│   └── main.py                  # FastAPI app
├── tests/                        # Test suite
├── alembic/                      # Database migrations
├── docker/                       # Docker configuration
├── requirements.txt              # Production dependencies
├── requirements-dev.txt          # Dev dependencies
├── .env.example                  # Environment template
├── Makefile                      # Command shortcuts
└── README.md                     # This file
```

---

## 🐛 Troubleshooting

### Issue: Port already in use

```bash
# Check what's using port 8000
lsof -i :8000
# or on Windows: netstat -ano | findstr :8000

# Kill the process or change the port in .env
PORT=8001
```

### Issue: Database connection failed

```bash
# 1. Check if PostgreSQL is running
docker-compose -f docker-compose.dev.yml ps

# 2. Check database logs
docker-compose -f docker-compose.dev.yml logs postgres

# 3. Verify credentials in .env match docker-compose.dev.yml

# 4. Try restarting database
docker-compose -f docker-compose.dev.yml restart postgres
```

### Issue: Migration errors

```bash
# 1. Check current migration status
make db-history

# 2. If needed, reset migrations (DANGER - loses data!)
make db-reset

# 3. Or downgrade and upgrade
alembic downgrade base
alembic upgrade head
```

### Issue: Import errors

```bash
# Make sure you're in virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Reinstall dependencies
pip install -r requirements-dev.txt
```

---

## 🔐 Security Checklist

Before deploying to production:

- [ ] Change all default passwords in `.env`
- [ ] Generate strong `SECRET_KEY` (min 32 characters)
- [ ] Set `DEBUG=False`
- [ ] Configure proper CORS origins
- [ ] Use HTTPS/TLS certificates
- [ ] Set up proper firewall rules
- [ ] Enable database backups
- [ ] Review and update security settings

---

## 📚 Next Steps

After successful setup:

1. **Read the documentation** in `/docs` folder
2. **Review the API** at http://localhost:8000/docs
3. **Run tests** to ensure everything works: `make test`
4. **Start implementing features** following the roadmap

---

## 🤝 Getting Help

If you encounter issues:

1. Check the [Troubleshooting](#-troubleshooting) section
2. Review Docker logs: `make docker-logs`
3. Check application logs in `logs/` directory
4. Verify your `.env` configuration
5. Ensure all prerequisites are installed

---

## ✅ Verification Checklist

- [ ] Application starts without errors
- [ ] Health endpoint responds: `curl http://localhost:8000/health`
- [ ] API docs accessible at `/docs`
- [ ] Database connection successful
- [ ] Redis connection successful
- [ ] Can create and apply migrations
- [ ] Tests pass: `make test`

---

**Ready to build CEMS!** 🎉

Next: Proceed to [Phase 2: Authentication & Authorization](./docs/phase2_authentication.md)