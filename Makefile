.PHONY: help install dev-install clean test run docker-up docker-down migrate db-upgrade db-downgrade seed-all seed-vaults docker-reset db-fresh check-env init-db

# Default target
help:
	@echo "CEMS - Currency Exchange Management System"
	@echo ""
	@echo "📦 Installation:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make setup          - Complete initial setup (Docker + DB + Migrations)"
	@echo "  make check-env      - Verify .env file exists and is configured"
	@echo ""
	@echo "🗄️  Database:"
	@echo "  make init-db        - Create PostgreSQL database (local setup only)"
	@echo "  make db-upgrade     - Apply migrations"
	@echo "  make db-downgrade   - Rollback last migration"
	@echo "  make db-reset       - Reset database (downgrade + upgrade)"
	@echo "  make db-fresh       - Fresh database with all seeds"
	@echo "  make migrate        - Create new migration"
	@echo ""
	@echo "🌱 Seeding:"
	@echo "  make seed-all       - Run all seeding scripts (recommended)"
	@echo "  make seed-users     - Seed users and roles"
	@echo "  make seed-currencies - Seed currencies"
	@echo "  make seed-branches  - Seed branches"
	@echo "  make seed-customers - Seed customers"
	@echo "  make seed-transactions - Seed transactions"
	@echo "  make seed-vaults    - Seed vaults and transfers"
	@echo "  make vault-summary  - Show vault balances summary"
	@echo ""
	@echo "🐳 Docker:"
	@echo "  make docker-up      - Start Docker containers (development)"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-reset   - Complete Docker reset (down -v + up + migrate + seed)"
	@echo "  make docker-logs    - View application logs"
	@echo "  make docker-shell   - Access Docker container shell"
	@echo ""
	@echo "🚀 Running:"
	@echo "  make run            - Run application locally"
	@echo "  make run-prod       - Run application in production mode"
	@echo ""
	@echo "🧪 Testing & Quality:"
	@echo "  make test           - Run all tests with coverage"
	@echo "  make test-unit      - Run unit tests only"
	@echo "  make test-integration - Run integration tests only"
	@echo "  make format         - Format code with black and isort"
	@echo "  make lint           - Run linters (flake8, mypy)"
	@echo "  make check          - Run format + lint + test"
	@echo ""
	@echo "🧹 Cleaning:"
	@echo "  make clean          - Clean up cache and build files"
	@echo "  make reset-all      - ⚠️  DANGER: Delete all data and volumes"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements-dev.txt

# Cleaning
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage

# Testing
test:
	pytest tests/ -v --cov=app --cov-report=html --cov-report=term

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

# Running
run: check-env
	uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

run-prod:
	uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Docker commands
docker-up:
	docker-compose -f docker-compose.dev.yml up -d

docker-down:
	docker-compose -f docker-compose.dev.yml down

docker-build:
	docker-compose -f docker-compose.dev.yml build

docker-logs:
	docker-compose -f docker-compose.dev.yml logs -f app

docker-shell:
	docker-compose -f docker-compose.dev.yml exec app /bin/sh

# Production Docker
docker-prod-up:
	docker-compose up -d

docker-prod-down:
	docker-compose down

docker-prod-build:
	docker-compose build

# Database initialization (local setup only, not needed for Docker)
init-db:
	@echo "🔨 Creating PostgreSQL database..."
	@echo ""
	@echo "⚠️  This command is for LOCAL setup only (not Docker)"
	@echo "⚠️  Make sure PostgreSQL is installed and running"
	@echo ""
	@echo "Creating user and database with credentials from .env.example:"
	@echo "  User: cems_user"
	@echo "  Password: cems_password_2025"
	@echo "  Database: cems_db"
	@echo ""
	@-psql -U postgres -c "CREATE USER cems_user WITH PASSWORD 'cems_password_2025';" 2>/dev/null || echo "User may already exist"
	@-psql -U postgres -c "CREATE DATABASE cems_db OWNER cems_user;" 2>/dev/null || echo "Database may already exist"
	@-psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE cems_db TO cems_user;" 2>/dev/null
	@echo ""
	@echo "✅ Database initialization complete!"
	@echo "📝 Next steps:"
	@echo "   1. Verify your .env file has: DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db"
	@echo "   2. Run: make db-upgrade"
	@echo "   3. Run: make seed-all"
	@echo ""

# Database migrations
migrate:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade: check-env
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

db-history:
	alembic history

# Environment verification
check-env:
	@if [ ! -f .env ]; then \
		echo "⚠️  Error: .env file not found!"; \
		echo ""; \
		echo "Creating .env from .env.example..."; \
		cp .env.example .env; \
		echo "✅ .env file created!"; \
		echo ""; \
		echo "⚠️  IMPORTANT: Please review .env file and update settings if needed:"; \
		echo "   - DATABASE_URL should match your environment"; \
		echo "   - For Docker: use 'db' as host"; \
		echo "   - For local: use 'localhost' as host"; \
		echo ""; \
	else \
		echo "✅ .env file exists"; \
		if grep -q "^DATABASE_URL=$$" .env || ! grep -q "^DATABASE_URL=" .env; then \
			echo "⚠️  WARNING: DATABASE_URL is empty or missing in .env!"; \
			echo ""; \
			echo "Expected format:"; \
			echo "  DATABASE_URL=postgresql+asyncpg://cems_user:cems_password_2025@localhost:5432/cems_db"; \
			echo ""; \
			echo "See ENV_SETUP_NOTES.md for detailed instructions."; \
			echo ""; \
		else \
			echo "✅ DATABASE_URL is configured"; \
		fi \
	fi

# Database seeding
seed-all:
	@echo "🌱 Running all seeding scripts..."
	@chmod +x scripts/SEED_USAGE_3.sh
	@./scripts/SEED_USAGE_3.sh

seed-users:
	@echo "🌱 Seeding users and roles..."
	@python scripts/seed_data.py

seed-currencies:
	@echo "🌱 Seeding currencies..."
	@python scripts/seed_currencies.py

seed-branches:
	@echo "🌱 Seeding branches..."
	@python scripts/seed_branches.py

seed-customers:
	@echo "🌱 Seeding customers..."
	@python scripts/seed_customers.py

seed-transactions:
	@echo "🌱 Seeding transactions..."
	@python scripts/seed_transactions.py

seed-vaults:
	@echo "🌱 Seeding vaults and transfers..."
	@python scripts/seed_vaults.py

vault-summary:
	@echo "📊 Vault Balances Summary:"
	@python scripts/seed_vaults.py --show

# Fresh database setup
db-fresh: db-reset seed-all
	@echo ""
	@echo "✅ Fresh database with all data ready!"
	@echo "🚀 Start the app with: make run"

# Complete Docker reset workflow
docker-reset:
	@echo "🔄 Starting complete Docker reset..."
	@echo ""
	@echo "Step 1/6: Stopping and removing containers with volumes..."
	docker compose down -v
	@echo ""
	@echo "Step 2/6: Starting containers..."
	docker compose up -d
	@echo ""
	@echo "Step 3/6: Waiting for services to be ready..."
	sleep 5
	@echo ""
	@echo "Step 4/6: Applying database migrations..."
	docker compose exec app alembic upgrade head
	@echo ""
	@echo "Step 5/6: Cleaning Python cache..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo ""
	@echo "Step 6/6: Running seeding scripts..."
	sleep 5
	@chmod +x scripts/SEED_USAGE_3.sh
	docker compose exec app bash scripts/SEED_USAGE_3.sh
	@echo ""
	@echo "✅ Docker reset complete!"
	@echo "🚀 Application is ready at: http://localhost:8000/docs"

# Code quality
format:
	black app/ tests/
	isort app/ tests/

lint:
	flake8 app/ tests/
	mypy app/

check: format lint test

# Database tools
db-shell:
	docker-compose -f docker-compose.dev.yml exec postgres psql -U cems_user -d cems_db

redis-cli:
	docker-compose -f docker-compose.dev.yml exec redis redis-cli

# Monitoring
logs:
	tail -f logs/*.log

# Setup new environment
setup: dev-install
	@echo "🚀 Setting up CEMS development environment..."
	@echo ""
	@echo "Step 1/5: Creating .env file from template..."
	@cp -n .env.example .env || true
	@echo "⚠️  Please review .env file and update DATABASE_URL if needed"
	@echo ""
	@echo "Step 2/5: Starting Docker services..."
	@make docker-up
	@echo ""
	@echo "Step 3/5: Waiting for database to be ready..."
	@sleep 5
	@echo ""
	@echo "Step 4/5: Running migrations..."
	@make db-upgrade
	@echo ""
	@echo "Step 5/5: Seeding database with sample data..."
	@make seed-all
	@echo ""
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo "✅ Setup complete!"
	@echo ""
	@echo "📍 Quick Links:"
	@echo "   • Application:  http://localhost:8000"
	@echo "   • API Docs:     http://localhost:8000/docs"
	@echo "   • PGAdmin:      http://localhost:5050"
	@echo ""
	@echo "🔑 Default Login:"
	@echo "   • Username: admin"
	@echo "   • Password: admin123"
	@echo ""
	@echo "📚 Useful Commands:"
	@echo "   • make run          - Start development server"
	@echo "   • make test         - Run tests"
	@echo "   • make vault-summary - View vault balances"
	@echo "   • make docker-logs  - View logs"
	@echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
	@echo ""

# Complete reset (DANGER!)
reset-all: docker-down clean
	docker volume rm cems_postgres_dev_data cems_redis_dev_data || true
	rm -rf uploads/* logs/*
	@echo "⚠️  All data has been deleted!"