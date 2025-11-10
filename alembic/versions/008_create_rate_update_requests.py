"""create rate update requests table

Revision ID: 008
Revises: 007
Create Date: 2025-11-10

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
    # Create enum type
    op.execute("""
        CREATE TYPE updaterequestatus AS ENUM ('pending', 'approved', 'rejected', 'expired', 'failed')
    """)

    # Create rate_update_requests table
    op.create_table(
        'rate_update_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', sa.Enum('pending', 'approved', 'rejected', 'expired', 'failed', name='updaterequestatus'), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('base_currency', sa.String(3), nullable=False),
        sa.Column('fetched_rates', postgresql.JSON, nullable=False),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('requested_at', sa.DateTime(), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('reviewed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('rates_applied_count', sa.String(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id']),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id']),
    )

    # Create indexes
    op.create_index('ix_rate_update_requests_status', 'rate_update_requests', ['status'])
    op.create_index('ix_rate_update_requests_requested_at', 'rate_update_requests', ['requested_at'])


def downgrade() -> None:
    op.drop_index('ix_rate_update_requests_requested_at')
    op.drop_index('ix_rate_update_requests_status')
    op.drop_table('rate_update_requests')
    op.execute('DROP TYPE updaterequestatus')
