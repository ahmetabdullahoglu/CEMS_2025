"""Add in_transit state to transactionstatus enum

Revision ID: 011_transaction_status_in_transit
Revises: 010_transaction_descriptions
Create Date: 2025-01-13 00:00:00.000000
"""

from alembic import op


revision = "011_transaction_status_in_transit"
down_revision = "010_transaction_descriptions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the in_transit value to transactionstatus enum."""
    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_old")
    op.execute(
        "CREATE TYPE transactionstatus AS ENUM ('pending', 'in_transit', 'completed', 'cancelled', 'failed')"
    )
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN status TYPE transactionstatus USING status::text::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_old")


def downgrade() -> None:
    """Remove the in_transit value from transactionstatus enum."""
    op.execute("UPDATE transactions SET status = 'pending' WHERE status = 'in_transit'")
    op.execute("ALTER TYPE transactionstatus RENAME TO transactionstatus_old")
    op.execute(
        "CREATE TYPE transactionstatus AS ENUM ('pending', 'completed', 'cancelled', 'failed')"
    )
    op.execute(
        "ALTER TABLE transactions ALTER COLUMN status TYPE transactionstatus USING status::text::transactionstatus"
    )
    op.execute("DROP TYPE transactionstatus_old")
