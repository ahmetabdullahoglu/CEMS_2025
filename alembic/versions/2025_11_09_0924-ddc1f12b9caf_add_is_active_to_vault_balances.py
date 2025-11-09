"""add_is_active_to_vault_balances

Revision ID: ddc1f12b9caf
Revises: 007_vault_tables
Create Date: 2025-11-09 09:24:56.605494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision: str = 'ddc1f12b9caf'
down_revision: Union[str, None] = '007_vault_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active column to vault_balances table if it doesn't exist"""
    # Get connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if column exists
    columns = [col['name'] for col in inspector.get_columns('vault_balances')]

    # Only add column if it doesn't exist
    if 'is_active' not in columns:
        op.add_column('vault_balances',
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                      comment='Whether balance is active')
        )
        print("✅ Added is_active column to vault_balances")
    else:
        print("ℹ️  Column is_active already exists in vault_balances, skipping...")

    # Check if index exists
    indexes = [idx['name'] for idx in inspector.get_indexes('vault_balances')]

    # Only create index if it doesn't exist
    if 'idx_vault_balances_active' not in indexes:
        op.create_index('idx_vault_balances_active', 'vault_balances', ['is_active'])
        print("✅ Created index idx_vault_balances_active")
    else:
        print("ℹ️  Index idx_vault_balances_active already exists, skipping...")


def downgrade() -> None:
    """Remove is_active column from vault_balances table"""
    # Get connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # Check if index exists before dropping
    indexes = [idx['name'] for idx in inspector.get_indexes('vault_balances')]
    if 'idx_vault_balances_active' in indexes:
        op.drop_index('idx_vault_balances_active', 'vault_balances')

    # Check if column exists before dropping
    columns = [col['name'] for col in inspector.get_columns('vault_balances')]
    if 'is_active' in columns:
        op.drop_column('vault_balances', 'is_active')