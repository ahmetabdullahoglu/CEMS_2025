# alembic/versions/007_create_vault_tables.py
"""create vault management tables

Revision ID: 007_vault_tables
Revises: 006_transaction_tables
Create Date: 2025-01-09 10:00:00.000000

Creates:
- vaults table
- vault_balances table
- vault_transfers table
- Related indexes and constraints
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '007_vault_tables'
down_revision = '006_add_transactions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create vault management tables"""

    # ==================== CREATE ENUMS ====================

    # Vault Type Enum
    vault_type_enum = postgresql.ENUM(
        'main', 'branch',
        name='vault_type_enum',
        create_type=False
    )
    vault_type_enum.create(op.get_bind(), checkfirst=True)

    # Vault Transfer Type Enum
    vault_transfer_type_enum = postgresql.ENUM(
        'vault_to_vault', 'vault_to_branch', 'branch_to_vault',
        name='vault_transfer_type_enum',
        create_type=False
    )
    vault_transfer_type_enum.create(op.get_bind(), checkfirst=True)

    # Vault Transfer Status Enum
    vault_transfer_status_enum = postgresql.ENUM(
        'pending', 'approved', 'in_transit', 'completed', 'cancelled', 'rejected',
        name='vault_transfer_status_enum',
        create_type=False
    )
    vault_transfer_status_enum.create(op.get_bind(), checkfirst=True)

    # Rate Update Request Status Enum
    rate_status_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected', 'expired', 'failed',
        name='rateupdaterequeststatus',
        create_type=False
    )
    rate_status_enum.create(op.get_bind(), checkfirst=True)
    
    # ==================== CREATE VAULTS TABLE ====================
    
    op.create_table(
        'vaults',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        
        # Basic Info
        sa.Column('vault_code', sa.String(20), nullable=False, unique=True, index=True,
                  comment='Unique vault code (e.g., VLT-MAIN, VLT-BR001)'),
        sa.Column('name', sa.String(100), nullable=False,
                  comment='Vault name'),
        sa.Column('vault_type', vault_type_enum, nullable=False, server_default='branch',
                  comment='Type of vault (main or branch)'),
        
        # Branch Reference
        sa.Column('branch_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('branches.id', ondelete='RESTRICT'),
                  nullable=True, index=True,
                  comment='Reference to branch (NULL for main vault)'),
        
        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true',
                  comment='Whether vault is active'),
        
        # Metadata
        sa.Column('description', sa.Text, nullable=True,
                  comment='Vault description'),
        sa.Column('location', sa.String(200), nullable=True,
                  comment='Physical location of vault'),
        
        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        
        # Constraints
        sa.CheckConstraint(
            "(vault_type = 'main' AND branch_id IS NULL) OR (vault_type = 'branch' AND branch_id IS NOT NULL)",
            name='vault_branch_consistency_check'
        ),
        
        comment='Vaults (main and branch)'
    )
    
    # Indexes
    op.create_index('idx_vault_type_active', 'vaults', ['vault_type', 'is_active'])
    op.create_index('idx_vault_branch', 'vaults', ['branch_id', 'is_active'])
    
    # ==================== CREATE VAULT_BALANCES TABLE ====================

    op.create_table(
        'vault_balances',

        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),

        # Foreign Keys
        sa.Column('vault_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vaults.id', ondelete='CASCADE'),
                  nullable=False, index=True,
                  comment='Reference to vault'),
        sa.Column('currency_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('currencies.id', ondelete='RESTRICT'),
                  nullable=False, index=True,
                  comment='Reference to currency'),

        # Balance
        sa.Column('balance', sa.Numeric(precision=15, scale=2), nullable=False, server_default='0',
                  comment='Current balance'),

        # Tracking
        sa.Column('last_updated', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='Last balance update timestamp'),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true',
                  comment='Whether balance is active'),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.UniqueConstraint('vault_id', 'currency_id', name='uq_vault_currency'),
        sa.CheckConstraint('balance >= 0', name='vault_balance_positive'),

        comment='Vault balances by currency'
    )
    
    # Indexes
    op.create_index('idx_vault_balance_lookup', 'vault_balances', ['vault_id', 'currency_id'])
    
    # ==================== CREATE VAULT_TRANSFERS TABLE ====================
    
    op.create_table(
        'vault_transfers',
        
        # Primary Key
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('gen_random_uuid()')),
        
        # Transfer Number
        sa.Column('transfer_number', sa.String(30), nullable=False, unique=True, index=True,
                  comment='Unique transfer number (VTR-20250109-00001)'),
        
        # Source and Destination
        sa.Column('from_vault_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vaults.id', ondelete='RESTRICT'),
                  nullable=False, index=True,
                  comment='Source vault'),
        sa.Column('to_vault_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('vaults.id', ondelete='RESTRICT'),
                  nullable=True, index=True,
                  comment='Destination vault (NULL if transfer to branch)'),
        sa.Column('to_branch_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('branches.id', ondelete='RESTRICT'),
                  nullable=True, index=True,
                  comment='Destination branch (NULL if transfer to vault)'),
        
        # Transfer Details
        sa.Column('currency_id', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('currencies.id', ondelete='RESTRICT'),
                  nullable=False, index=True,
                  comment='Currency being transferred'),
        sa.Column('amount', sa.Numeric(precision=15, scale=2), nullable=False,
                  comment='Transfer amount'),
        sa.Column('transfer_type', vault_transfer_type_enum, nullable=False,
                  comment='Type of transfer'),

        # Status and Workflow
        sa.Column('status', vault_transfer_status_enum, nullable=False, server_default='pending',
                  comment='Current transfer status'),
        
        # Users
        sa.Column('initiated_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='RESTRICT'),
                  nullable=False,
                  comment='User who initiated transfer'),
        sa.Column('approved_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True,
                  comment='User who approved transfer'),
        sa.Column('received_by', postgresql.UUID(as_uuid=True),
                  sa.ForeignKey('users.id', ondelete='SET NULL'),
                  nullable=True,
                  comment='User who received/confirmed transfer'),
        
        # Timestamps
        sa.Column('initiated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP'),
                  comment='When transfer was initiated'),
        sa.Column('approved_at', sa.DateTime, nullable=True,
                  comment='When transfer was approved'),
        sa.Column('completed_at', sa.DateTime, nullable=True,
                  comment='When transfer was completed'),
        sa.Column('cancelled_at', sa.DateTime, nullable=True,
                  comment='When transfer was cancelled'),
        
        # Additional Info
        sa.Column('notes', sa.Text, nullable=True,
                  comment='Transfer notes/reason'),
        sa.Column('rejection_reason', sa.Text, nullable=True,
                  comment='Reason for rejection'),

        # Status
        sa.Column('is_active', sa.Boolean, nullable=False, server_default='true',
                  comment='Whether transfer is active'),

        # Timestamps
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),

        # Constraints
        sa.CheckConstraint('amount > 0', name='transfer_amount_positive'),
        sa.CheckConstraint(
            "(to_vault_id IS NOT NULL AND to_branch_id IS NULL) OR (to_vault_id IS NULL AND to_branch_id IS NOT NULL)",
            name='transfer_destination_check'
        ),
        
        comment='Vault transfers'
    )
    
    # Indexes
    op.create_index('idx_transfer_status_date', 'vault_transfers', ['status', 'initiated_at'])
    op.create_index('idx_transfer_from_vault', 'vault_transfers', ['from_vault_id', 'initiated_at'])
    op.create_index('idx_transfer_to_vault', 'vault_transfers', ['to_vault_id', 'initiated_at'])
    op.create_index('idx_transfer_to_branch', 'vault_transfers', ['to_branch_id', 'initiated_at'])
    op.create_index('idx_vault_transfers_active', 'vault_transfers', ['is_active'])

    # ==================== CREATE TRIGGERS AND FUNCTIONS ====================

    # Create sequence for transfer numbers
    op.execute("CREATE SEQUENCE IF NOT EXISTS vault_transfer_number_seq START 1")

    # Function to generate transfer_number using sequence
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_vault_transfer_number()
        RETURNS TRIGGER AS $$
        DECLARE
            new_number VARCHAR(30);
            seq_num BIGINT;
        BEGIN
            -- Get next sequence value (thread-safe, no race conditions)
            seq_num := nextval('vault_transfer_number_seq');

            -- Format: VTR-YYYYMMDD-NNNNN
            new_number := 'VTR-' ||
                         TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' ||
                         LPAD(seq_num::TEXT, 5, '0');

            NEW.transfer_number := new_number;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Trigger to auto-generate transfer_number
    op.execute("""
        CREATE TRIGGER trigger_generate_vault_transfer_number
        BEFORE INSERT ON vault_transfers
        FOR EACH ROW
        WHEN (NEW.transfer_number IS NULL)
        EXECUTE FUNCTION generate_vault_transfer_number();
    """)

    # ==================== CREATE TRIGGER FOR UPDATED_AT ====================
    
    # Updated_at trigger for vaults
    op.execute("""
        CREATE TRIGGER update_vaults_updated_at
        BEFORE UPDATE ON vaults
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Updated_at trigger for vault_balances
    op.execute("""
        CREATE TRIGGER update_vault_balances_updated_at
        BEFORE UPDATE ON vault_balances
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Updated_at trigger for vault_transfers
    op.execute("""
        CREATE TRIGGER update_vault_transfers_updated_at
        BEFORE UPDATE ON vault_transfers
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)

    # ==================== CREATE RATE_UPDATE_REQUESTS TABLE ====================

    op.create_table(
        'rate_update_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('status', rate_status_enum, nullable=False),
        sa.Column('source', sa.String(length=50), nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('fetched_rates', postgresql.JSONB(), nullable=False),
        sa.Column(
            'requested_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='RESTRICT'),
            nullable=False,
        ),
        sa.Column('requested_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            'reviewed_by',
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey('users.id', ondelete='SET NULL'),
            nullable=True,
        ),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('review_notes', sa.Text(), nullable=True),
        sa.Column('rates_applied_count', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
    )
    op.create_index(
        'ix_rate_update_requests_status',
        'rate_update_requests',
        ['status'],
    )
    op.create_index(
        'ix_rate_update_requests_requested_at',
        'rate_update_requests',
        ['requested_at'],
    )


def downgrade() -> None:
    """Drop vault management tables"""

    # Drop rate update requests table and indexes
    op.drop_index('ix_rate_update_requests_requested_at', table_name='rate_update_requests')
    op.drop_index('ix_rate_update_requests_status', table_name='rate_update_requests')
    op.drop_table('rate_update_requests')

    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS trigger_generate_vault_transfer_number ON vault_transfers;")
    op.execute("DROP TRIGGER IF EXISTS update_vault_transfers_updated_at ON vault_transfers;")
    op.execute("DROP TRIGGER IF EXISTS update_vault_balances_updated_at ON vault_balances;")
    op.execute("DROP TRIGGER IF EXISTS update_vaults_updated_at ON vaults;")

    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS generate_vault_transfer_number();")

    # Drop sequence
    op.execute("DROP SEQUENCE IF EXISTS vault_transfer_number_seq;")

    # Drop tables
    op.drop_table('vault_transfers')
    op.drop_table('vault_balances')
    op.drop_table('vaults')

    # Drop enums
    op.execute("DROP TYPE IF EXISTS rateupdaterequeststatus;")
    op.execute("DROP TYPE IF EXISTS vault_transfer_status_enum;")
    op.execute("DROP TYPE IF EXISTS vault_transfer_type_enum;")
    op.execute("DROP TYPE IF EXISTS vault_type_enum;")
