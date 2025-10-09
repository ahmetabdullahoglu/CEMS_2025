#!/bin/bash

# ==================== CEMS Project Structure Creation Script ====================
# This script creates the complete directory structure and all necessary files
# for the CEMS (Currency Exchange Management System) project
# ================================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Print colored message
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}${message}${NC}"
}

print_message "$CYAN" "╔════════════════════════════════════════════════════════════════╗"
print_message "$CYAN" "║        CEMS Project Structure Creation Script v1.0             ║"
print_message "$CYAN" "║    Currency Exchange Management System - Complete Setup       ║"
print_message "$CYAN" "╚════════════════════════════════════════════════════════════════╝"
echo ""

# ==================== Create Directory Structure ====================
print_message "$BLUE" "🏗️  Creating directory structure..."

# Main application directories
mkdir -p app/api/v1/endpoints
mkdir -p app/core
mkdir -p app/db/models
mkdir -p app/services
mkdir -p app/repositories
mkdir -p app/schemas
mkdir -p app/middleware
mkdir -p app/utils

# Test directories
mkdir -p tests/unit
mkdir -p tests/integration
mkdir -p tests/performance

# Alembic (migrations)
mkdir -p alembic/versions

# Docker directories
mkdir -p docker/postgres
mkdir -p docker/redis
mkdir -p docker/nginx
mkdir -p docker/nginx/ssl

# Documentation
mkdir -p docs/api
mkdir -p docs/architecture
mkdir -p docs/guides

# Data directories
mkdir -p uploads
mkdir -p logs
mkdir -p temp
mkdir -p static
mkdir -p reports

# GitHub Actions
mkdir -p .github/workflows

print_message "$GREEN" "✅ Directories created"

# ==================== Create __init__.py Files ====================
print_message "$BLUE" "📝 Creating __init__.py files..."

touch app/__init__.py
touch app/api/__init__.py
touch app/api/v1/__init__.py
touch app/api/v1/endpoints/__init__.py
touch app/core/__init__.py
touch app/db/__init__.py
touch app/db/models/__init__.py
touch app/services/__init__.py
touch app/repositories/__init__.py
touch app/schemas/__init__.py
touch app/middleware/__init__.py
touch app/utils/__init__.py
touch tests/__init__.py
touch tests/unit/__init__.py
touch tests/integration/__init__.py
touch tests/performance/__init__.py

print_message "$GREEN" "✅ __init__.py files created"

# ==================== Create Root Configuration Files ====================
print_message "$BLUE" "📋 Creating root configuration files..."

# Create empty placeholders for files that need content from artifacts
touch requirements.txt
touch requirements-dev.txt
touch .env.example
touch .gitignore
touch pytest.ini
touch alembic.ini
touch Dockerfile
touch docker-compose.yml
touch docker-compose.dev.yml
touch Makefile
touch README.md
touch LICENSE
touch CHANGELOG.md
touch CONTRIBUTING.md
touch PROJECT_SETUP.md
touch COMMANDS.md
touch PHASE_1_COMPLETE.md

print_message "$GREEN" "✅ Root configuration files created"

# ==================== Create Core Application Files ====================
print_message "$BLUE" "🔧 Creating core application files..."

# Core files
touch app/main.py
touch app/core/config.py
touch app/core/constants.py
touch app/core/exceptions.py
touch app/core/security.py
touch app/api/v1/__init__.py

# Database files
touch app/db/base.py
touch app/db/base_class.py
touch app/db/__init__.py

print_message "$GREEN" "✅ Core application files created"

# ==================== Create API Endpoint Placeholders ====================
print_message "$BLUE" "🌐 Creating API endpoint files..."

cat > app/api/v1/endpoints/__init__.py << 'EOF'
"""API v1 endpoints package"""
# Endpoints will be imported here as they are implemented
EOF

# Create endpoint placeholders
touch app/api/v1/endpoints/auth.py
touch app/api/v1/endpoints/users.py
touch app/api/v1/endpoints/currencies.py
touch app/api/v1/endpoints/branches.py
touch app/api/v1/endpoints/customers.py
touch app/api/v1/endpoints/transactions.py
touch app/api/v1/endpoints/vault.py
touch app/api/v1/endpoints/reports.py
touch app/api/v1/endpoints/dashboard.py

print_message "$GREEN" "✅ API endpoint files created"

# ==================== Create Model Placeholders ====================
print_message "$BLUE" "🗄️  Creating database model files..."

touch app/db/models/__init__.py
touch app/db/models/user.py
touch app/db/models/role.py
touch app/db/models/currency.py
touch app/db/models/branch.py
touch app/db/models/customer.py
touch app/db/models/transaction.py
touch app/db/models/vault.py
touch app/db/models/document.py
touch app/db/models/audit.py

print_message "$GREEN" "✅ Model files created"

# ==================== Create Service Placeholders ====================
print_message "$BLUE" "⚙️  Creating service files..."

touch app/services/__init__.py
touch app/services/auth_service.py
touch app/services/user_service.py
touch app/services/currency_service.py
touch app/services/branch_service.py
touch app/services/balance_service.py
touch app/services/customer_service.py
touch app/services/transaction_service.py
touch app/services/vault_service.py
touch app/services/report_service.py
touch app/services/notification_service.py

print_message "$GREEN" "✅ Service files created"

# ==================== Create Repository Placeholders ====================
print_message "$BLUE" "📦 Creating repository files..."

touch app/repositories/__init__.py
touch app/repositories/user_repo.py
touch app/repositories/currency_repo.py
touch app/repositories/branch_repo.py
touch app/repositories/customer_repo.py
touch app/repositories/transaction_repo.py
touch app/repositories/vault_repo.py

print_message "$GREEN" "✅ Repository files created"

# ==================== Create Schema Placeholders ====================
print_message "$BLUE" "📐 Creating schema files..."

touch app/schemas/__init__.py
touch app/schemas/user.py
touch app/schemas/role.py
touch app/schemas/currency.py
touch app/schemas/branch.py
touch app/schemas/customer.py
touch app/schemas/transaction.py
touch app/schemas/vault.py
touch app/schemas/common.py

print_message "$GREEN" "✅ Schema files created"

# ==================== Create Utility Files ====================
print_message "$BLUE" "🔨 Creating utility files..."

touch app/utils/__init__.py
touch app/utils/logger.py
touch app/utils/validators.py
touch app/utils/generators.py
touch app/utils/security.py
touch app/utils/helpers.py

print_message "$GREEN" "✅ Utility files created"

# ==================== Create Middleware Files ====================
print_message "$BLUE" "🔌 Creating middleware files..."

touch app/middleware/__init__.py
touch app/middleware/security.py
touch app/middleware/performance.py
touch app/middleware/rbac.py

print_message "$GREEN" "✅ Middleware files created"

# ==================== Create Alembic Files ====================
print_message "$BLUE" "📊 Creating Alembic migration files..."

touch alembic/env.py
touch alembic/script.py.mako
touch alembic/README

print_message "$GREEN" "✅ Alembic files created"

# ==================== Create Docker Files ====================
print_message "$BLUE" "🐳 Creating Docker configuration files..."

touch docker/postgres/init.sql
touch docker/nginx/nginx.conf
touch docker/nginx/ssl/.gitkeep

print_message "$GREEN" "✅ Docker files created"

# ==================== Create Test Files ====================
print_message "$BLUE" "🧪 Creating test files..."

touch tests/conftest.py
touch tests/__init__.py

# Unit tests
touch tests/unit/__init__.py
touch tests/unit/test_models.py
touch tests/unit/test_services.py
touch tests/unit/test_utils.py

# Integration tests
touch tests/integration/__init__.py
touch tests/integration/test_api_auth.py
touch tests/integration/test_api_transactions.py
touch tests/integration/test_database.py

# Performance tests
touch tests/performance/__init__.py
touch tests/performance/test_load.py

print_message "$GREEN" "✅ Test files created"

# ==================== Create Documentation Files ====================
print_message "$BLUE" "📚 Creating documentation files..."

touch docs/api/endpoints.md
touch docs/architecture/overview.md
touch docs/architecture/database_schema.md
touch docs/guides/setup_guide.md
touch docs/guides/development_guide.md
touch docs/guides/deployment_guide.md

print_message "$GREEN" "✅ Documentation files created"

# ==================== Create GitHub Actions ====================
print_message "$BLUE" "🔄 Creating GitHub Actions workflow..."

touch .github/workflows/ci.yml
touch .github/workflows/deploy.yml

print_message "$GREEN" "✅ GitHub Actions files created"

# ==================== Create .gitkeep for Empty Directories ====================
print_message "$BLUE" "📌 Creating .gitkeep files..."

touch uploads/.gitkeep
touch logs/.gitkeep
touch temp/.gitkeep
touch static/.gitkeep
touch reports/.gitkeep

print_message "$GREEN" "✅ .gitkeep files created"

# ==================== Summary ====================
echo ""
print_message "$CYAN" "╔════════════════════════════════════════════════════════════════╗"
print_message "$CYAN" "║                    ✅ Structure Created!                        ║"
print_message "$CYAN" "╚════════════════════════════════════════════════════════════════╝"
echo ""

print_message "$GREEN" "📊 Project Structure Summary:"
echo ""
echo "  📁 Application Structure:"
echo "    ├── app/ (main application)"
echo "    ├── tests/ (test suite)"
echo "    ├── alembic/ (database migrations)"
echo "    ├── docker/ (Docker configuration)"
echo "    └── docs/ (documentation)"
echo ""
echo "  📄 Files Created:"
echo "    ├── Root config files: 17"
echo "    ├── Application files: 40+"
echo "    ├── Test files: 10+"
echo "    ├── Documentation: 6+"
echo "    └── Total: 70+ files"
echo ""

# Try to show tree structure
if command -v tree &> /dev/null; then
    print_message "$YELLOW" "📂 Complete Structure:"
    tree -L 3 -I '__pycache__|*.pyc|.git|venv|env' --dirsfirst
else
    print_message "$YELLOW" "💡 Tip: Install 'tree' command to see structure visualization"
    print_message "$YELLOW" "   Ubuntu/Debian: sudo apt-get install tree"
    print_message "$YELLOW" "   MacOS: brew install tree"
fi

echo ""
print_message "$CYAN" "╔════════════════════════════════════════════════════════════════╗"
print_message "$CYAN" "║                    📋 NEXT STEPS                               ║"
print_message "$CYAN" "╚════════════════════════════════════════════════════════════════╝"
echo ""
print_message "$YELLOW" "⚠️  IMPORTANT: Copy content from Claude Artifacts!"
echo ""
echo "You need to copy the content from the following artifacts to their files:"
echo ""
echo "  🔧 Configuration Files (REQUIRED):"
echo "     1. requirements.txt"
echo "     2. requirements-dev.txt"
echo "     3. .env.example"
echo "     4. .gitignore"
echo "     5. pytest.ini"
echo "     6. alembic.ini"
echo ""
echo "  🏗️  Core Application Files (REQUIRED):"
echo "     7. app/main.py"
echo "     8. app/core/config.py"
echo "     9. app/core/constants.py"
echo "     10. app/core/exceptions.py"
echo "     11. app/api/v1/__init__.py"
echo "     12. app/db/base.py"
echo "     13. app/db/base_class.py"
echo "     14. app/db/__init__.py"
echo ""
echo "  🐳 Docker Files (REQUIRED):"
echo "     15. Dockerfile"
echo "     16. docker-compose.yml"
echo "     17. docker-compose.dev.yml"
echo "     18. docker/postgres/init.sql"
echo "     19. docker/nginx/nginx.conf"
echo ""
echo "  📊 Database Migration Files (REQUIRED):"
echo "     20. alembic/env.py"
echo "     21. alembic/script.py.mako"
echo ""
echo "  🧪 Test Configuration (REQUIRED):"
echo "     22. tests/conftest.py"
echo ""
echo "  🛠️  Development Tools (REQUIRED):"
echo "     23. Makefile"
echo ""
echo "  🔄 CI/CD (REQUIRED):"
echo "     24. .github/workflows/ci.yml"
echo ""
echo "  📚 Documentation (RECOMMENDED):"
echo "     25. README.md"
echo "     26. PROJECT_SETUP.md"
echo "     27. COMMANDS.md"
echo "     28. CONTRIBUTING.md"
echo "     29. LICENSE"
echo "     30. CHANGELOG.md"
echo "     31. PHASE_1_COMPLETE.md"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""
print_message "$GREEN" "✅ After copying all files, run:"
echo ""
echo "   1️⃣  Copy .env.example to .env:"
echo "      cp .env.example .env"
echo ""
echo "   2️⃣  Generate SECRET_KEY:"
echo "      python -c \"import secrets; print(secrets.token_urlsafe(32))\""
echo ""
echo "   3️⃣  Update .env with your SECRET_KEY and database credentials"
echo ""
echo "   4️⃣  Run complete setup:"
echo "      make setup"
echo ""
echo "   5️⃣  Access the application:"
echo "      🌐 API: http://localhost:8000"
echo "      📖 Docs: http://localhost:8000/docs"
echo "      🗄️  PGAdmin: http://localhost:5050"
echo "      🔴 Redis Commander: http://localhost:8081"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""
print_message "$PURPLE" "🎯 Quick Test After Setup:"
echo ""
echo "   curl http://localhost:8000/health"
echo ""
print_message "$CYAN" "📚 Documentation:"
echo ""
echo "   • Setup Guide: PROJECT_SETUP.md"
echo "   • Commands: COMMANDS.md"
echo "   • Contributing: CONTRIBUTING.md"
echo ""
echo "────────────────────────────────────────────────────────────────"
echo ""
print_message "$GREEN" "🎉 Structure creation completed successfully!"
print_message "$YELLOW" "⚠️  Don't forget to copy content from all 32 artifacts!"
echo ""
print_message "$CYAN" "Good luck with your CEMS development! 🚀"
echo ""