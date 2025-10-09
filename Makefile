.PHONY: help install dev-install clean test run docker-up docker-down migrate db-upgrade db-downgrade

# Default target
help:
	@echo "CEMS - Currency Exchange Management System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install production dependencies"
	@echo "  make dev-install    - Install development dependencies"
	@echo "  make clean          - Clean up cache and build files"
	@echo "  make test           - Run tests with coverage"
	@echo "  make run            - Run application locally"
	@echo "  make docker-up      - Start Docker containers (development)"
	@echo "  make docker-down    - Stop Docker containers"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make migrate        - Create new migration"
	@echo "  make db-upgrade     - Apply migrations"
	@echo "  make db-downgrade   - Rollback last migration"
	@echo "  make format         - Format code with black and isort"
	@echo "  make lint           - Run linters (flake8, mypy)"

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
run:
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

# Database migrations
migrate:
	@read -p "Enter migration message: " msg; \
	alembic revision --autogenerate -m "$$msg"

db-upgrade:
	alembic upgrade head

db-downgrade:
	alembic downgrade -1

db-reset:
	alembic downgrade base
	alembic upgrade head

db-history:
	alembic history

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
	@echo "Creating .env file from .env.example..."
	cp -n .env.example .env || true
	@echo "Starting Docker services..."
	make docker-up
	@echo "Waiting for database to be ready..."
	sleep 5
	@echo "Running migrations..."
	make db-upgrade
	@echo ""
	@echo "✅ Setup complete!"
	@echo "Access the application at: http://localhost:8000"
	@echo "Access the API docs at: http://localhost:8000/docs"
	@echo "Access PGAdmin at: http://localhost:5050"
	@echo ""

# Complete reset (DANGER!)
reset-all: docker-down clean
	docker volume rm cems_postgres_dev_data cems_redis_dev_data || true
	rm -rf uploads/* logs/*
	@echo "⚠️  All data has been deleted!"