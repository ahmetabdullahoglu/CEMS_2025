"""Validate that seed helpers always provide a description."""

from types import SimpleNamespace
from uuid import uuid4

import scripts.seed_transactions as seed_transactions


def _make_branch(name: str) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), name=name)


def _make_currency(code: str) -> SimpleNamespace:
    return SimpleNamespace(id=uuid4(), code=code)


def _make_user() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4())


def _make_customer() -> SimpleNamespace:
    return SimpleNamespace(id=uuid4())


def test_generate_income_transaction_has_description():
    branches = [_make_branch("Main")] 
    currencies = {"USD": _make_currency("USD")}
    users = [_make_user()]

    data = seed_transactions.generate_income_transaction(1, branches, currencies, users)

    assert data["description"]


def test_generate_expense_transaction_has_description():
    branches = [_make_branch("Main")]
    currencies = {"USD": _make_currency("USD")}
    users = [_make_user()]

    data = seed_transactions.generate_expense_transaction(2, branches, currencies, users)

    assert data["description"]


def test_generate_exchange_transaction_has_description():
    branches = [_make_branch("Main")]
    currencies = {
        "USD": _make_currency("USD"),
        "EUR": _make_currency("EUR"),
    }
    customers = [_make_customer()]
    users = [_make_user()]

    data = seed_transactions.generate_exchange_transaction(3, branches, currencies, customers, users)

    assert data["description"]


def test_generate_transfer_transaction_has_description():
    branches = [_make_branch("A"), _make_branch("B")]
    currencies = {"USD": _make_currency("USD")}
    users = [_make_user()]

    data = seed_transactions.generate_transfer_transaction(4, branches, currencies, users)

    assert data["description"]
