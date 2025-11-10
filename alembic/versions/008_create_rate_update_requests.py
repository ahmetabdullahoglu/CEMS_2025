"""create rate update requests table

Revision ID: 008
Revises: 007
Create Date: 2025-11-10

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '008_rate_update_requests'
down_revision = '007_vault_tables'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type if it doesn't exist using raw SQL
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE updaterequestatus AS ENUM ('pending', 'approved', 'rejected', 'expired', 'failed');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Check if table exists using raw SQL
    conn = op.get_bind()
    result = conn.execute(sa.text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables
            WHERE table_schema = 'public'
            AND table_name = 'rate_update_requests'
        )
    """))
    table_exists = result.scalar()

    if not table_exists:
        # Create table using raw SQL to avoid SQLAlchemy enum type creation issues
        op.execute("""
            CREATE TABLE rate_update_requests (
                id UUID PRIMARY KEY,
                status updaterequestatus NOT NULL,
                source VARCHAR(50) NOT NULL,
                base_currency VARCHAR(3) NOT NULL,
                fetched_rates JSON NOT NULL,
                requested_by UUID NOT NULL REFERENCES users(id),
                requested_at TIMESTAMP NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                reviewed_by UUID REFERENCES users(id),
                reviewed_at TIMESTAMP,
                review_notes TEXT,
                rates_applied_count VARCHAR,
                error_message TEXT
            )
        """)

        # Create indexes
        op.create_index('ix_rate_update_requests_status', 'rate_update_requests', ['status'])
        op.create_index('ix_rate_update_requests_requested_at', 'rate_update_requests', ['requested_at'])


def downgrade() -> None:
    op.drop_index('ix_rate_update_requests_requested_at', table_name='rate_update_requests')
    op.drop_index('ix_rate_update_requests_status', table_name='rate_update_requests')
    op.drop_table('rate_update_requests')
    op.execute('DROP TYPE IF EXISTS updaterequestatus')
