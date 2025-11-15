"""Tests ensuring transaction enums stay consistent across layers."""

from app.core.constants import IncomeCategory as CoreIncomeCategory
from app.core.constants import ExpenseCategory as CoreExpenseCategory
from app.db.models.transaction import (
    IncomeCategory as ModelIncomeCategory,
    ExpenseCategory as ModelExpenseCategory,
)
from decimal import Decimal
from uuid import uuid4

from app.schemas.transaction import (
    IncomeCategoryEnum,
    ExpenseCategoryEnum,
    IncomeTransactionCreate,
    ExpenseTransactionCreate,
)
import scripts.seed_transactions as seed_transactions


def test_income_category_alignment():
    """All income categories should match across constants, models, schemas, and scripts."""
    core_values = {category.value for category in CoreIncomeCategory}
    model_values = {category.value for category in ModelIncomeCategory}
    schema_values = {category.value for category in IncomeCategoryEnum}

    assert core_values == model_values == schema_values

    script_values = {category.value for _, category in seed_transactions.INCOME_SOURCES}
    assert script_values.issubset(core_values)


def test_expense_category_alignment():
    """All expense categories should match across constants, models, schemas, and scripts."""
    core_values = {category.value for category in CoreExpenseCategory}
    model_values = {category.value for category in ModelExpenseCategory}
    schema_values = {category.value for category in ExpenseCategoryEnum}

    assert core_values == model_values == schema_values

    script_values = {category.value for _, category, _ in seed_transactions.EXPENSE_DATA}
    assert script_values.issubset(core_values)


def test_income_schema_accepts_new_categories():
    """IncomeTransactionCreate should validate the new enums."""
    payload = IncomeTransactionCreate(
        amount=Decimal("125.00"),
        currency_id=uuid4(),
        branch_id=uuid4(),
        income_category=IncomeCategoryEnum.EXCHANGE_COMMISSION,
    )

    assert payload.income_category is IncomeCategoryEnum.EXCHANGE_COMMISSION


def test_expense_schema_accepts_new_categories():
    """ExpenseTransactionCreate should validate the new enums."""
    payload = ExpenseTransactionCreate(
        amount=Decimal("450.00"),
        currency_id=uuid4(),
        branch_id=uuid4(),
        expense_category=ExpenseCategoryEnum.MARKETING,
        expense_to="Test Vendor",
    )

    assert payload.expense_category is ExpenseCategoryEnum.MARKETING
