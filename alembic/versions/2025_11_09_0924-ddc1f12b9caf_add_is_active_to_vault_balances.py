"""add_is_active_to_vault_tables

Revision ID: ddc1f12b9caf
Revises: 007_vault_tables
Create Date: 2025-11-09 09:24:56.605494

Adds is_active column to vault_balances and vault_transfers tables
if they don't already have it (for backward compatibility).
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
    """Add is_active column to vault tables if they don't exist"""
    # Get connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # ==================== VAULT_BALANCES ====================

    # Check if column exists in vault_balances
    vault_balances_columns = [col['name'] for col in inspector.get_columns('vault_balances')]

    # Only add column if it doesn't exist
    if 'is_active' not in vault_balances_columns:
        op.add_column('vault_balances',
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                      comment='Whether balance is active')
        )
        print("✅ Added is_active column to vault_balances")
    else:
        print("ℹ️  Column is_active already exists in vault_balances, skipping...")

    # Check if index exists
    vault_balances_indexes = [idx['name'] for idx in inspector.get_indexes('vault_balances')]

    # Only create index if it doesn't exist
    if 'idx_vault_balances_active' not in vault_balances_indexes:
        op.create_index('idx_vault_balances_active', 'vault_balances', ['is_active'])
        print("✅ Created index idx_vault_balances_active")
    else:
        print("ℹ️  Index idx_vault_balances_active already exists, skipping...")

    # ==================== VAULT_TRANSFERS ====================

    # Check if column exists in vault_transfers
    vault_transfers_columns = [col['name'] for col in inspector.get_columns('vault_transfers')]

    # Only add column if it doesn't exist
    if 'is_active' not in vault_transfers_columns:
        op.add_column('vault_transfers',
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true',
                      comment='Whether transfer is active')
        )
        print("✅ Added is_active column to vault_transfers")
    else:
        print("ℹ️  Column is_active already exists in vault_transfers, skipping...")

    # Check if index exists
    vault_transfers_indexes = [idx['name'] for idx in inspector.get_indexes('vault_transfers')]

    # Only create index if it doesn't exist
    if 'idx_vault_transfers_active' not in vault_transfers_indexes:
        op.create_index('idx_vault_transfers_active', 'vault_transfers', ['is_active'])
        print("✅ Created index idx_vault_transfers_active")
    else:
        print("ℹ️  Index idx_vault_transfers_active already exists, skipping...")


def downgrade() -> None:
    """Remove is_active column from vault tables"""
    # Get connection and inspector
    conn = op.get_bind()
    inspector = Inspector.from_engine(conn)

    # ==================== VAULT_TRANSFERS ====================

    # Check if index exists before dropping
    vault_transfers_indexes = [idx['name'] for idx in inspector.get_indexes('vault_transfers')]
    if 'idx_vault_transfers_active' in vault_transfers_indexes:
        op.drop_index('idx_vault_transfers_active', 'vault_transfers')

    # Check if column exists before dropping
    vault_transfers_columns = [col['name'] for col in inspector.get_columns('vault_transfers')]
    if 'is_active' in vault_transfers_columns:
        op.drop_column('vault_transfers', 'is_active')

    # ==================== VAULT_BALANCES ====================

    # Check if index exists before dropping
    vault_balances_indexes = [idx['name'] for idx in inspector.get_indexes('vault_balances')]
    if 'idx_vault_balances_active' in vault_balances_indexes:
        op.drop_index('idx_vault_balances_active', 'vault_balances')

    # Check if column exists before dropping
    vault_balances_columns = [col['name'] for col in inspector.get_columns('vault_balances')]
    if 'is_active' in vault_balances_columns:
        op.drop_column('vault_balances', 'is_active')