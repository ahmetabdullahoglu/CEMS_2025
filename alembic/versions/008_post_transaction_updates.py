"""Consolidate transaction enum updates and rate request table

Revision ID: 008_post_transaction_updates
Revises: 007_vault_tables
Create Date: 2025-01-15 00:00:00.000000
"""

from typing import Tuple

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy.engine.reflection import Inspector


revision = "008_post_transaction_updates"
down_revision = "007_vault_tables"
branch_labels = None
depends_on = None

TRANSACTION_STATUS_VALUES = (
    "pending",
    "in_transit",
    "completed",
    "cancelled",
    "failed",
    "reversed",
)

INCOME_CATEGORY_VALUES = (
    "service_fee",
    "exchange_commission",
    "transfer_fee",
    "commission",
    "interest",
    "other",
)

EXPENSE_CATEGORY_VALUES = (
    "rent",
    "salary",
    "salaries",
    "utilities",
    "maintenance",
    "supplies",
    "marketing",
    "other",
)

RATE_REQUEST_STATUS_VALUES = (
    "pending",
    "approved",
    "rejected",
    "expired",
    "failed",
)


def _enum_exists(inspector: Inspector, name: str) -> bool:
    return any(enum["name"] == name for enum in inspector.get_enums())


def _recreate_enum(
    bind,
    inspector,
    enum_name: str,
    new_values: Tuple[str, ...],
    table_name: str,
    column_name: str,
    drop_default: bool = False,
    default_value: str | None = None,
) -> None:
    if drop_default:
        op.execute(
            sa.text(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} DROP DEFAULT"
            )
        )

    if _enum_exists(inspector, enum_name):
        op.execute(sa.text(f"ALTER TYPE {enum_name} RENAME TO {enum_name}_old"))

    postgresql.ENUM(*new_values, name=enum_name).create(bind, checkfirst=True)

    op.execute(
        sa.text(
            f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
            f"TYPE {enum_name} USING {column_name}::text::{enum_name}"
        )
    )

    if default_value is not None:
        op.execute(
            sa.text(
                f"ALTER TABLE {table_name} ALTER COLUMN {column_name} "
                f"SET DEFAULT '{default_value}'"
            )
        )

    op.execute(sa.text(f"DROP TYPE IF EXISTS {enum_name}_old"))


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # ---------- Rate update request table ----------
    rate_status_enum = postgresql.ENUM(
        *RATE_REQUEST_STATUS_VALUES,
        name="rateupdaterequeststatus",
        create_type=False,
    )

    if not _enum_exists(inspector, "rateupdaterequeststatus"):
        rate_status_enum.create(bind, checkfirst=False)

    op.create_table(
        "rate_update_requests",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("status", rate_status_enum, nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("fetched_rates", postgresql.JSONB(), nullable=False),
        sa.Column(
            "requested_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="RESTRICT"),
            nullable=False,
        ),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "reviewed_by",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rates_applied_count", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
    )
    op.create_index(
        "ix_rate_update_requests_status",
        "rate_update_requests",
        ["status"],
    )
    op.create_index(
        "ix_rate_update_requests_requested_at",
        "rate_update_requests",
        ["requested_at"],
    )

    # ---------- Transaction enums & description column ----------
    _recreate_enum(
        bind,
        inspector,
        "transactionstatus",
        TRANSACTION_STATUS_VALUES,
        table_name="transactions",
        column_name="status",
        drop_default=True,
        default_value="pending",
    )

    _recreate_enum(
        bind,
        inspector,
        "incomecategory",
        INCOME_CATEGORY_VALUES,
        table_name="transactions",
        column_name="income_category",
    )

    _recreate_enum(
        bind,
        inspector,
        "expensecategory",
        EXPENSE_CATEGORY_VALUES,
        table_name="transactions",
        column_name="expense_category",
    )

    op.add_column(
        "transactions",
        sa.Column(
            "description",
            sa.Text(),
            nullable=True,
            comment="Human-readable transaction summary",
        ),
    )


def downgrade() -> None:
    # Drop description column
    op.drop_column("transactions", "description")

    bind = op.get_bind()
    inspector = sa.inspect(bind)

    # Revert expense categories
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
        WHERE expense_category IN ('marketing')
        """
    )
    _recreate_enum(
        bind,
        inspector,
        "expensecategory",
        ("rent", "salary", "utilities", "maintenance", "supplies", "other"),
        table_name="transactions",
        column_name="expense_category",
    )

    # Revert income categories
    op.execute(
        """
        UPDATE transactions
        SET income_category = 'commission'
        WHERE income_category IN ('exchange_commission', 'transfer_fee')
        """
    )
    op.execute(
        """
        UPDATE transactions
        SET income_category = 'service_fee'
        WHERE income_category = 'interest'
        """
    )
    _recreate_enum(
        bind,
        inspector,
        "incomecategory",
        ("service_fee", "commission", "other"),
        table_name="transactions",
        column_name="income_category",
    )

    # Revert transaction status
    op.execute(
        """
        UPDATE transactions
        SET status = 'pending'
        WHERE status IN ('in_transit', 'reversed')
        """
    )
    _recreate_enum(
        bind,
        inspector,
        "transactionstatus",
        ("pending", "completed", "cancelled", "failed"),
        table_name="transactions",
        column_name="status",
        drop_default=True,
        default_value="pending",
    )

    # Drop rate update requests table & enum
    op.drop_index(
        "ix_rate_update_requests_requested_at",
        table_name="rate_update_requests",
    )
    op.drop_index(
        "ix_rate_update_requests_status",
        table_name="rate_update_requests",
    )
    op.drop_table("rate_update_requests")
    op.execute("DROP TYPE IF EXISTS rateupdaterequeststatus")
