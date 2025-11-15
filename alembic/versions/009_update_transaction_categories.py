"""Update transaction category enums with new values

Revision ID: 009_update_transaction_categories
Revises: 008_rate_update_requests
Create Date: 2025-01-10 00:00:00.000000
"""

from alembic import op


revision = "009_transaction_category_enums"
down_revision = "008_rate_update_requests"
branch_labels = None
depends_on = None

INCOME_NEW_VALUES = (
    "exchange_commission",
    "transfer_fee",
    "interest",
)

EXPENSE_NEW_VALUES = (
    "marketing",
    "salaries",
)


def _add_enum_value(enum_name: str, value: str) -> None:
    """Add value to PostgreSQL enum if it doesn't already exist."""
    op.execute(
        f"""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_enum e
                JOIN pg_type t ON e.enumtypid = t.oid
                WHERE t.typname = '{enum_name}' AND e.enumlabel = '{value}'
            ) THEN
                ALTER TYPE {enum_name} ADD VALUE '{value}';
            END IF;
        END;
        $$;
        """
    )


def upgrade() -> None:
    """Add the new enum values used across API, services, and scripts."""
    for value in INCOME_NEW_VALUES:
        _add_enum_value("incomecategory", value)

    for value in EXPENSE_NEW_VALUES:
        _add_enum_value("expensecategory", value)


def downgrade() -> None:
    """Rebuild enums without the newly added values.

    Existing rows using the new categories are mapped to safe legacy buckets
    before recreating the enum types.
    """

    # Map new income categories back to legacy buckets
    op.execute(
        """
        UPDATE transactions
        SET income_category = 'other'
        WHERE income_category IN ('exchange_commission', 'transfer_fee', 'interest')
        """
    )

    # Map new expense categories back to legacy buckets
    op.execute(
        """
        UPDATE transactions
        SET expense_category = 'salary'
        WHERE expense_category = 'salaries'
        """
    )
    op.execute(
        """
        UPDATE transactions
        SET expense_category = 'other'
        WHERE expense_category = 'marketing'
        """
    )

    # Recreate income enum with legacy values only
    op.execute("ALTER TYPE incomecategory RENAME TO incomecategory_new")
    op.execute(
        """
        CREATE TYPE incomecategory AS ENUM ('service_fee', 'commission', 'other')
        """
    )
    op.execute(
        """
        ALTER TABLE transactions
        ALTER COLUMN income_category
        TYPE incomecategory
        USING income_category::text::incomecategory
        """
    )
    op.execute("DROP TYPE incomecategory_new")

    # Recreate expense enum with legacy values only
    op.execute("ALTER TYPE expensecategory RENAME TO expensecategory_new")
    op.execute(
        """
        CREATE TYPE expensecategory AS ENUM (
            'rent',
            'salary',
            'utilities',
            'maintenance',
            'supplies',
            'other'
        )
        """
    )
    op.execute(
        """
        ALTER TABLE transactions
        ALTER COLUMN expense_category
        TYPE expensecategory
        USING expense_category::text::expensecategory
        """
    )
    op.execute("DROP TYPE expensecategory_new")
