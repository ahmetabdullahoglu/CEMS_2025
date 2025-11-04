"""
Add transaction tables - Without customer dependency

Revision ID: 006_add_transactions
Revises: 005_create_customer_tables
Create Date: 2025-01-09 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '006_add_transactions'
down_revision = '005_create_customer_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create transaction tables"""
    
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing_enums = [e['name'] for e in inspector.get_enums()]
    
    # ==================== Create Enums ====================
    if 'transactiontype' not in existing_enums:
        op.execute("CREATE TYPE transactiontype AS ENUM ('income', 'expense', 'exchange', 'transfer')")
    
    if 'transactionstatus' not in existing_enums:
        op.execute("CREATE TYPE transactionstatus AS ENUM ('pending', 'completed', 'cancelled', 'failed')")
    
    if 'incomecategory' not in existing_enums:
        op.execute("CREATE TYPE incomecategory AS ENUM ('service_fee', 'commission', 'other')")
    
    if 'expensecategory' not in existing_enums:
        op.execute("CREATE TYPE expensecategory AS ENUM ('rent', 'salary', 'utilities', 'maintenance', 'supplies', 'other')")
    
    if 'transfertype' not in existing_enums:
        op.execute("CREATE TYPE transfertype AS ENUM ('branch_to_branch', 'vault_to_branch', 'branch_to_vault')")
    
    # ==================== Create Table ====================
    op.create_table(
        'transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('transaction_number', sa.String(50), nullable=False, unique=True),
        sa.Column('transaction_type', postgresql.ENUM('income', 'expense', 'exchange', 'transfer', 
                  name='transactiontype', create_type=False), nullable=False),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'cancelled', 'failed',
                  name='transactionstatus', create_type=False), nullable=False, 
                 server_default='pending'),
        sa.Column('amount', sa.Numeric(15, 2), nullable=False),
        
        # Foreign Keys
        sa.Column('branch_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('customer_id', postgresql.UUID(as_uuid=True), nullable=True),  # NO FK for now
        sa.Column('currency_id', postgresql.UUID(as_uuid=True), nullable=False),
        
        sa.Column('reference_number', sa.String(100), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('transaction_date', sa.DateTime(timezone=True), nullable=False,
                 server_default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('cancelled_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('cancellation_reason', sa.Text, nullable=True),
        
        # Income fields
        sa.Column('income_category', postgresql.ENUM('service_fee', 'commission', 'other',
                  name='incomecategory', create_type=False), nullable=True),
        sa.Column('income_source', sa.String(200), nullable=True),
        
        # Expense fields
        sa.Column('expense_category', postgresql.ENUM('rent', 'salary', 'utilities', 'maintenance', 'supplies', 'other',
                  name='expensecategory', create_type=False), nullable=True),
        sa.Column('expense_to', sa.String(200), nullable=True),
        sa.Column('approval_required', sa.Boolean, nullable=True, server_default='false'),
        sa.Column('approved_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        
        # Exchange fields
        sa.Column('from_currency_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_currency_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('from_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('to_amount', sa.Numeric(15, 2), nullable=True),
        sa.Column('exchange_rate_used', sa.Numeric(12, 6), nullable=True),
        sa.Column('commission_amount', sa.Numeric(15, 2), nullable=True, server_default='0.00'),
        sa.Column('commission_percentage', sa.Numeric(5, 2), nullable=True, server_default='0.00'),
        
        # Transfer fields
        sa.Column('from_branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('to_branch_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('transfer_type', postgresql.ENUM('branch_to_branch', 'vault_to_branch', 'branch_to_vault',
                  name='transfertype', create_type=False), nullable=True),
        sa.Column('received_by_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=True),
        
        # Audit
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        
        # ========== Foreign Keys (WITHOUT customer FK) ==========
        sa.ForeignKeyConstraint(['branch_id'], ['branches.id'], name='fk_transaction_branch', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_transaction_user', ondelete='RESTRICT'),
        # REMOVED: customer FK - will add later when customers table exists
        sa.ForeignKeyConstraint(['currency_id'], ['currencies.id'], name='fk_transaction_currency', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['cancelled_by_id'], ['users.id'], name='fk_transaction_cancelled_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['approved_by_id'], ['users.id'], name='fk_transaction_approved_by', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['from_currency_id'], ['currencies.id'], name='fk_transaction_from_currency', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_currency_id'], ['currencies.id'], name='fk_transaction_to_currency', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['from_branch_id'], ['branches.id'], name='fk_transaction_from_branch', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['to_branch_id'], ['branches.id'], name='fk_transaction_to_branch', ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['received_by_id'], ['users.id'], name='fk_transaction_received_by', ondelete='SET NULL'),
        
        # ========== Constraints ==========
        sa.CheckConstraint('amount > 0', name='check_amount_positive'),
        sa.CheckConstraint("(status != 'cancelled') OR (cancelled_at IS NOT NULL AND cancelled_by_id IS NOT NULL)", name='check_cancellation_data'),
        sa.CheckConstraint("(status != 'completed') OR (completed_at IS NOT NULL)", name='check_completion_data'),
        sa.CheckConstraint("(transaction_type != 'expense') OR (approval_required = false) OR (approved_by_id IS NOT NULL AND approved_at IS NOT NULL)", name='check_expense_approval'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (from_amount > 0)", name='check_exchange_from_amount'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (to_amount > 0)", name='check_exchange_to_amount'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (exchange_rate_used > 0)", name='check_exchange_rate_positive'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (commission_amount >= 0)", name='check_commission_non_negative'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (commission_percentage >= 0 AND commission_percentage <= 100)", name='check_commission_percentage_range'),
        sa.CheckConstraint("(transaction_type != 'exchange') OR (from_currency_id != to_currency_id)", name='check_different_currencies'),
        sa.CheckConstraint("(transaction_type != 'transfer') OR (from_branch_id != to_branch_id)", name='check_different_branches'),
        sa.CheckConstraint("(transaction_type != 'transfer') OR (transfer_type != 'branch_to_branch') OR (from_branch_id IS NOT NULL AND to_branch_id IS NOT NULL)", name='check_branch_transfer_branches'),
    )
    
    # ==================== Indexes ====================
    op.create_index('idx_transaction_number', 'transactions', ['transaction_number'], unique=True)
    op.create_index('idx_transaction_type', 'transactions', ['transaction_type'])
    op.create_index('idx_transaction_status', 'transactions', ['status'])
    op.create_index('idx_transaction_date_status', 'transactions', ['transaction_date', 'status'])
    op.create_index('idx_branch_currency_date', 'transactions', ['branch_id', 'currency_id', 'transaction_date'])
    op.create_index('idx_transaction_branch', 'transactions', ['branch_id'])
    op.create_index('idx_transaction_user', 'transactions', ['user_id'])
    op.create_index('idx_transaction_customer', 'transactions', ['customer_id'])
    op.create_index('idx_transaction_currency', 'transactions', ['currency_id'])
    
    # ==================== Triggers ====================
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_transaction_number()
        RETURNS TRIGGER AS $$
        DECLARE
            date_str TEXT;
            prefix TEXT;
            last_number INTEGER;
            next_number INTEGER;
        BEGIN
            date_str := TO_CHAR(NEW.transaction_date, 'YYYYMMDD');
            prefix := 'TRX-' || date_str || '-';
            
            SELECT COALESCE(
                MAX(CAST(SUBSTRING(transaction_number FROM LENGTH(prefix) + 1) AS INTEGER)), 0
            ) INTO last_number
            FROM transactions
            WHERE transaction_number LIKE prefix || '%';
            
            next_number := last_number + 1;
            NEW.transaction_number := prefix || LPAD(next_number::TEXT, 5, '0');
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_generate_transaction_number
        BEFORE INSERT ON transactions
        FOR EACH ROW
        WHEN (NEW.transaction_number IS NULL)
        EXECUTE FUNCTION generate_transaction_number();
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION update_transaction_updated_at()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_update_transaction_updated_at
        BEFORE UPDATE ON transactions
        FOR EACH ROW
        EXECUTE FUNCTION update_transaction_updated_at();
    """)
    
    op.execute("""
        CREATE OR REPLACE FUNCTION prevent_completed_transaction_modification()
        RETURNS TRIGGER AS $$
        BEGIN
            IF OLD.status = 'completed' AND NEW.status = 'completed' THEN
                IF (OLD.amount != NEW.amount OR
                    OLD.transaction_type != NEW.transaction_type OR
                    OLD.branch_id != NEW.branch_id OR
                    OLD.currency_id != NEW.currency_id OR
                    OLD.transaction_date != NEW.transaction_date) THEN
                    RAISE EXCEPTION 'Cannot modify completed transaction %', OLD.transaction_number;
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    op.execute("""
        CREATE TRIGGER trigger_prevent_completed_modification
        BEFORE UPDATE ON transactions
        FOR EACH ROW
        EXECUTE FUNCTION prevent_completed_transaction_modification();
    """)
    
    print("✅ Transaction tables created successfully (without customer FK)")


def downgrade():
    """Drop transaction tables"""
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_completed_modification ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_transaction_updated_at ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trigger_generate_transaction_number ON transactions")
    op.execute("DROP FUNCTION IF EXISTS prevent_completed_transaction_modification()")
    op.execute("DROP FUNCTION IF EXISTS update_transaction_updated_at()")
    op.execute("DROP FUNCTION IF EXISTS generate_transaction_number()")
    op.drop_table('transactions')
    op.execute("DROP TYPE IF EXISTS transfertype")
    op.execute("DROP TYPE IF EXISTS expensecategory")
    op.execute("DROP TYPE IF EXISTS incomecategory")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    print("✅ Transaction tables dropped")