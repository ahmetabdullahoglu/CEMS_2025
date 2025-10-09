"""
Pytest Configuration and Fixtures
Shared test fixtures for CEMS
"""

import asyncio
from typing import AsyncGenerator, Generator
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.main import app
from app.db.base import Base, get_db
from app.core.config import settings

# Test database URL (use a separate test database)
TEST_DATABASE_URL = settings.DATABASE_URL.replace(
    settings.POSTGRES_DB, 
    f"{settings.POSTGRES_DB}_test"
)


# ==================== Database Fixtures ====================

@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
async def test_engine():
    """Create test database engine"""
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        poolclass=NullPool,
    )
    
    # Create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    # Drop all tables after tests
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a new database session for each test"""
    async_session = async_sessionmaker(
        test_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    
    async with async_session() as session:
        yield session
        await session.rollback()


@pytest.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create HTTP client for testing API endpoints"""
    
    async def override_get_db():
        yield db_session
    
    app.dependency_overrides[get_db] = override_get_db
    
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
    
    app.dependency_overrides.clear()


# ==================== Authentication Fixtures ====================

@pytest.fixture
async def test_user_data():
    """Sample user data for testing"""
    return {
        "username": "testuser",
        "email": "test@example.com",
        "password": "TestPass123!",
        "full_name": "Test User"
    }


@pytest.fixture
async def test_admin_data():
    """Sample admin user data"""
    return {
        "username": "admin",
        "email": "admin@example.com",
        "password": "AdminPass123!",
        "full_name": "Admin User",
        "is_superuser": True
    }


# @pytest.fixture
# async def auth_headers(client: AsyncClient, test_user_data):
#     """Get authentication headers for testing protected endpoints"""
#     # Will be implemented after authentication system is ready
#     pass


# ==================== Sample Data Fixtures ====================

@pytest.fixture
def sample_currency_data():
    """Sample currency data"""
    return {
        "code": "USD",
        "name_en": "US Dollar",
        "name_ar": "دولار أمريكي",
        "symbol": "$",
        "is_base_currency": True,
        "decimal_places": 2
    }


@pytest.fixture
def sample_branch_data():
    """Sample branch data"""
    return {
        "code": "BR001",
        "name_en": "Main Branch",
        "name_ar": "الفرع الرئيسي",
        "region": "istanbul_european",
        "address": "Test Address",
        "phone": "+90 555 123 4567",
        "email": "branch@example.com",
        "is_main_branch": True
    }


@pytest.fixture
def sample_customer_data():
    """Sample customer data"""
    return {
        "first_name": "John",
        "last_name": "Doe",
        "name_ar": "جون دو",
        "national_id": "12345678901",
        "phone_number": "+90 555 987 6543",
        "email": "john.doe@example.com",
        "date_of_birth": "1990-01-01",
        "nationality": "US",
        "customer_type": "individual",
        "risk_level": "low"
    }


# ==================== Utility Fixtures ====================

@pytest.fixture
def mock_datetime(monkeypatch):
    """Mock datetime for consistent testing"""
    from datetime import datetime
    
    class MockDatetime:
        @staticmethod
        def utcnow():
            return datetime(2025, 1, 9, 12, 0, 0)
    
    monkeypatch.setattr("datetime.datetime", MockDatetime)


@pytest.fixture(autouse=True)
async def reset_db(db_session: AsyncSession):
    """Reset database state between tests"""
    yield
    # Cleanup will happen in db_session fixture


# ==================== Pytest Hooks ====================

def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")


def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add markers based on test path
        if "integration" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        elif "unit" in str(item.fspath):
            item.add_marker(pytest.mark.unit)