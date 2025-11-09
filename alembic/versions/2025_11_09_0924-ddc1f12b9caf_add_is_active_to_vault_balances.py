"""add_is_active_to_vault_balances

Revision ID: ddc1f12b9caf
Revises: 007_vault_tables
Create Date: 2025-11-09 09:24:56.605494

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ddc1f12b9caf'
down_revision: Union[str, None] = '007_vault_tables'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active column to vault_balances table"""
    op.add_column('vault_balances',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='Whether balance is active')
    )
    # Add index for is_active
    op.create_index('idx_vault_balances_active', 'vault_balances', ['is_active'])


def downgrade() -> None:
    """Remove is_active column from vault_balances table"""
    op.drop_index('idx_vault_balances_active', 'vault_balances')
    op.drop_column('vault_balances', 'is_active')