"""add user primary_branch_id

Revision ID: 008
Revises: 007
Create Date: 2025-11-09

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008'
down_revision = '007'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add primary_branch_id column to users table
    op.add_column('users', sa.Column(
        'primary_branch_id',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment="User's primary branch for quick access"
    ))

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_users_primary_branch',
        'users',
        'branches',
        ['primary_branch_id'],
        ['id'],
        ondelete='SET NULL'
    )


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_users_primary_branch', 'users', type_='foreignkey')

    # Drop column
    op.drop_column('users', 'primary_branch_id')
