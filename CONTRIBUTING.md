# 🤝 Contributing to CEMS

First off, thank you for considering contributing to CEMS! It's people like you that make CEMS such a great tool.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Process](#development-process)
- [Coding Standards](#coding-standards)
- [Testing Guidelines](#testing-guidelines)
- [Commit Guidelines](#commit-guidelines)
- [Pull Request Process](#pull-request-process)
- [Project Structure](#project-structure)

---

## 📜 Code of Conduct

### Our Pledge

We pledge to make participation in our project a harassment-free experience for everyone, regardless of age, body size, disability, ethnicity, gender identity and expression, level of experience, nationality, personal appearance, race, religion, or sexual identity and orientation.

### Our Standards

**Examples of behavior that contributes to a positive environment:**
- Using welcoming and inclusive language
- Being respectful of differing viewpoints and experiences
- Gracefully accepting constructive criticism
- Focusing on what is best for the community
- Showing empathy towards other community members

**Examples of unacceptable behavior:**
- The use of sexualized language or imagery
- Trolling, insulting/derogatory comments, and personal or political attacks
- Public or private harassment
- Publishing others' private information without explicit permission
- Other conduct which could reasonably be considered inappropriate in a professional setting

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:

- Python 3.11 or higher
- Docker and Docker Compose
- Git
- A code editor (VS Code, PyCharm, etc.)
- Basic understanding of FastAPI and SQLAlchemy

### Fork and Clone

1. Fork the repository on GitHub
2. Clone your fork locally:

```bash
git clone https://github.com/YOUR_USERNAME/CEMS_2025.git
cd CEMS_2025
```

3. Add the upstream repository:

```bash
git remote add upstream https://github.com/ORIGINAL_OWNER/CEMS_2025.git
```

### Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
make dev-install

# Copy environment file
cp .env.example .env

# Generate SECRET_KEY and update .env
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Start development services
make docker-up

# Run migrations
make db-upgrade
```

---

## 💻 Development Process

### 1. Create a Branch

Always create a new branch for your work:

```bash
# Update your local main branch
git checkout main
git pull upstream main

# Create a feature branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/bug-description
```

### Branch Naming Convention

- `feature/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation updates
- `refactor/` - Code refactoring
- `test/` - Adding or updating tests
- `chore/` - Maintenance tasks

### 2. Make Your Changes

- Write clean, maintainable code
- Follow the coding standards (see below)
- Add tests for new features
- Update documentation as needed
- Keep commits focused and atomic

### 3. Test Your Changes

```bash
# Run all tests
make test

# Run specific tests
pytest tests/unit/test_your_file.py

# Check code quality
make format
make lint
make check
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a meaningful message
git commit -m "feat: add currency exchange calculation"

# Push to your fork
git push origin feature/your-feature-name
```

---

## 📝 Coding Standards

### Python Style Guide

We follow [PEP 8](https://pep8.org/) with some modifications:

- Line length: 88 characters (Black default)
- Use type hints for all functions
- Write docstrings for all public modules, functions, classes, and methods
- Use meaningful variable and function names

### Code Formatting

We use **Black** for code formatting:

```bash
# Format all files
make format

# Check formatting without changes
black --check app/ tests/
```

### Import Sorting

We use **isort** for sorting imports:

```bash
# Sort imports
isort app/ tests/

# Check import sorting
isort --check-only app/ tests/
```

### Type Checking

We use **MyPy** for static type checking:

```bash
mypy app/
```

### Linting

We use **Flake8** for linting:

```bash
flake8 app/ tests/
```

### Example of Good Code

```python
"""
Module for currency exchange calculations.

This module provides functions to calculate exchange rates
and convert amounts between different currencies.
"""

from decimal import Decimal
from typing import Optional
from app.core.exceptions import InvalidExchangeRateError


def calculate_exchange(
    amount: Decimal,
    from_currency: str,
    to_currency: str,
    rate: Decimal,
    commission: Optional[Decimal] = None
) -> Decimal:
    """
    Calculate the exchange amount with commission.
    
    Args:
        amount: The amount to exchange
        from_currency: Source currency code (e.g., 'USD')
        to_currency: Target currency code (e.g., 'EUR')
        rate: Exchange rate from source to target
        commission: Optional commission percentage (0.01 = 1%)
    
    Returns:
        Decimal: The calculated exchange amount
    
    Raises:
        InvalidExchangeRateError: If rate is invalid
        
    Example:
        >>> calculate_exchange(Decimal("100"), "USD", "EUR", Decimal("0.85"))
        Decimal("85.00")
    """
    if rate <= 0:
        raise InvalidExchangeRateError(from_currency, to_currency)
    
    converted_amount = amount * rate
    
    if commission:
        commission_amount = converted_amount * commission
        converted_amount -= commission_amount
    
    return converted_amount.quantize(Decimal("0.01"))
```

---

## 🧪 Testing Guidelines

### Test Structure

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── test_models.py
│   ├── test_services.py
│   └── test_utils.py
├── integration/             # Integration tests (database, API)
│   ├── test_api_auth.py
│   ├── test_api_transactions.py
│   └── test_database.py
└── conftest.py             # Shared fixtures
```

### Writing Tests

#### Unit Tests

```python
"""Unit tests for currency service."""

import pytest
from decimal import Decimal
from app.services.currency_service import CurrencyService


def test_calculate_exchange_rate():
    """Test exchange rate calculation."""
    service = CurrencyService()
    result = service.calculate_exchange(
        amount=Decimal("100"),
        from_currency="USD",
        to_currency="EUR",
        rate=Decimal("0.85")
    )
    assert result == Decimal("85.00")


def test_invalid_exchange_rate_raises_error():
    """Test that invalid rate raises error."""
    service = CurrencyService()
    with pytest.raises(InvalidExchangeRateError):
        service.calculate_exchange(
            amount=Decimal("100"),
            from_currency="USD",
            to_currency="EUR",
            rate=Decimal("-1")
        )
```

#### Integration Tests

```python
"""Integration tests for currency API."""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
async def test_create_currency(client: AsyncClient, auth_headers):
    """Test creating a currency via API."""
    response = await client.post(
        "/api/v1/currencies",
        headers=auth_headers,
        json={
            "code": "USD",
            "name_en": "US Dollar",
            "symbol": "$"
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["code"] == "USD"
```

### Test Requirements

- All new features must have tests
- Aim for 80%+ code coverage
- Tests should be independent and isolated
- Use meaningful test names that describe what is being tested
- Use fixtures for common test data

### Running Tests

```bash
# All tests
make test

# Unit tests only
pytest tests/unit/

# Integration tests only
pytest tests/integration/

# Specific test file
pytest tests/unit/test_models.py

# Specific test
pytest tests/unit/test_models.py::test_user_creation

# With coverage report
pytest --cov=app --cov-report=html
```

---

## 📦 Commit Guidelines

We follow the [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: A new feature
- `fix`: A bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, missing semi-colons, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

### Examples

```bash
# Feature
git commit -m "feat(currencies): add exchange rate history tracking"

# Bug fix
git commit -m "fix(auth): resolve JWT token expiration issue"

# Documentation
git commit -m "docs(api): update authentication examples"

# Refactoring
git commit -m "refactor(transactions): improve balance update logic"

# Tests
git commit -m "test(branches): add branch creation tests"

# With body and footer
git commit -m "feat(reports): add monthly revenue report

Implement monthly revenue report generation with:
- PDF export support
- Excel export support
- Email delivery option

Closes #123"
```

---

## 🔄 Pull Request Process

### Before Submitting

1. **Update your branch** with the latest changes from upstream:

```bash
git checkout main
git pull upstream main
git checkout your-feature-branch
git rebase main
```

2. **Run all checks**:

```bash
make check  # Runs format, lint, and tests
```

3. **Update documentation** if needed

4. **Add tests** for new features

### Submitting PR

1. **Push your branch** to your fork:

```bash
git push origin your-feature-branch
```

2. **Create Pull Request** on GitHub

3. **Fill out the PR template** completely:

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests pass
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests added
```

### PR Review Process

- At least one maintainer must approve the PR
- All CI checks must pass
- Address all review comments
- Keep the PR focused on a single feature/fix
- Squash commits if requested

### After Approval

Your PR will be merged using one of these strategies:
- **Squash and merge** (default for features)
- **Rebase and merge** (for clean history)
- **Merge commit** (for important branches)

---

## 📁 Project Structure

Understanding the project structure helps you navigate and contribute effectively:

```
CEMS_2025/
├── app/
│   ├── api/v1/endpoints/      # API route handlers
│   ├── core/                  # Configuration, constants, exceptions
│   ├── db/                    # Database models and session
│   ├── services/              # Business logic
│   ├── repositories/          # Data access layer
│   ├── schemas/               # Pydantic models
│   ├── middleware/            # Custom middleware
│   └── utils/                 # Utility functions
├── tests/                     # Test suite
├── alembic/                   # Database migrations
├── docker/                    # Docker configuration
└── docs/                      # Documentation
```

### Where to Add Code

- **New API endpoint**: `app/api/v1/endpoints/`
- **Database model**: `app/db/models/`
- **Business logic**: `app/services/`
- **Data access**: `app/repositories/`
- **Request/Response schemas**: `app/schemas/`
- **Utilities**: `app/utils/`
- **Tests**: `tests/unit/` or `tests/integration/`
- **Documentation**: `docs/`

---

## 🐛 Reporting Bugs

### Before Reporting

1. Check if the bug has already been reported
2. Try to reproduce the bug on the latest version
3. Collect relevant information (logs, screenshots, etc.)

### Bug Report Template

```markdown
**Describe the bug**
A clear description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. See error

**Expected behavior**
What you expected to happen.

**Screenshots**
If applicable, add screenshots.

**Environment:**
 - OS: [e.g., Ubuntu 22.04]
 - Python version: [e.g., 3.11.5]
 - CEMS version: [e.g., 1.0.0]

**Additional context**
Any other context about the problem.
```

---

## 💡 Feature Requests

We welcome feature requests! Please:

1. Check if the feature has already been requested
2. Describe the problem it solves
3. Explain your proposed solution
4. Consider alternative solutions

---

## 📞 Questions?

- **GitHub Discussions**: For general questions
- **GitHub Issues**: For bugs and feature requests
- **Email**: dev@cems-project.com

---

## 🙏 Thank You!

Your contributions to CEMS are greatly appreciated. Every contribution, no matter how small, helps make CEMS better for everyone!

---

**Happy Coding! 🚀**