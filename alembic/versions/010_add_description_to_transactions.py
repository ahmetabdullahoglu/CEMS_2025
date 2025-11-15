"""
Add description column to transactions

Revision ID: 010_transaction_descriptions
Revises: 009_transaction_category_enums
Create Date: 2025-01-11 00:00:00.000000
"""

from alembic import op
import sqlalchemy as sa


revision = "010_transaction_descriptions"
down_revision = "009_transaction_category_enums"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add the nullable description column used by APIs and scripts."""
    op.add_column(
        "transactions",
        sa.Column("description", sa.Text(), nullable=True, comment="Human-readable transaction summary"),
    )


def downgrade() -> None:
    """Remove the description column if it exists."""
    op.drop_column("transactions", "description")
