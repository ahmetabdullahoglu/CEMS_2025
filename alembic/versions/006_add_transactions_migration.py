"""
Add transaction tables - With customer dependency

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
    
    # ==================== Create transactions table ====================
    op.execute("""
        CREATE TABLE transactions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            transaction_number VARCHAR(50) UNIQUE NOT NULL,
            transaction_type transactiontype NOT NULL,
            status transactionstatus NOT NULL DEFAULT 'pending',
            
            -- Core Transaction Data
            amount NUMERIC(15, 2) NOT NULL CHECK (amount > 0),
            
            -- Foreign Keys
            branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
            user_id UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
            customer_id UUID REFERENCES customers(id) ON DELETE SET NULL,
            currency_id UUID NOT NULL REFERENCES currencies(id) ON DELETE RESTRICT,
            
            -- Optional Reference
            reference_number VARCHAR(100),
            notes TEXT,
            
            -- Timestamps
            transaction_date TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMP WITH TIME ZONE,
            
            -- Cancellation Info
            cancelled_at TIMESTAMP WITH TIME ZONE,
            cancelled_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            cancellation_reason TEXT,
            
            -- Income-specific fields
            income_category incomecategory,
            income_source VARCHAR(200),
            
            -- Expense-specific fields
            expense_category expensecategory,
            expense_to VARCHAR(200),
            approval_required BOOLEAN DEFAULT false,
            approved_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            approved_at TIMESTAMP WITH TIME ZONE,
            
            -- Exchange-specific fields
            from_currency_id UUID REFERENCES currencies(id) ON DELETE RESTRICT,
            to_currency_id UUID REFERENCES currencies(id) ON DELETE RESTRICT,
            from_amount NUMERIC(15, 2),
            to_amount NUMERIC(15, 2),
            exchange_rate_used NUMERIC(12, 6),
            commission_amount NUMERIC(15, 2) DEFAULT 0.00,
            commission_percentage NUMERIC(5, 2) DEFAULT 0.00,
            
            -- Transfer-specific fields
            from_branch_id UUID REFERENCES branches(id) ON DELETE RESTRICT,
            to_branch_id UUID REFERENCES branches(id) ON DELETE RESTRICT,
            transfer_type transfertype,
            received_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            received_at TIMESTAMP WITH TIME ZONE,
            
            -- Audit
            created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
            
            -- Constraints
            CONSTRAINT check_amount_positive CHECK (amount > 0),
            CONSTRAINT check_cancelled_fields CHECK (
                (status != 'cancelled') OR 
                (cancelled_at IS NOT NULL AND cancelled_by_id IS NOT NULL)
            ),
            CONSTRAINT check_completed_fields CHECK (
                (status != 'completed') OR (completed_at IS NOT NULL)
            ),
            CONSTRAINT check_exchange_fields CHECK (
                (transaction_type != 'exchange') OR 
                (from_currency_id IS NOT NULL AND to_currency_id IS NOT NULL AND 
                 from_amount IS NOT NULL AND to_amount IS NOT NULL)
            ),
            CONSTRAINT check_transfer_fields CHECK (
                (transaction_type != 'transfer') OR 
                (from_branch_id IS NOT NULL AND to_branch_id IS NOT NULL AND transfer_type IS NOT NULL)
            )
        )
    """)
    
    # ==================== Create Indexes ====================
    op.execute("CREATE INDEX idx_transaction_number ON transactions(transaction_number)")
    op.execute("CREATE INDEX idx_transaction_type ON transactions(transaction_type)")
    op.execute("CREATE INDEX idx_transaction_status ON transactions(status)")
    op.execute("CREATE INDEX idx_transaction_branch ON transactions(branch_id)")
    op.execute("CREATE INDEX idx_transaction_user ON transactions(user_id)")
    op.execute("CREATE INDEX idx_transaction_customer ON transactions(customer_id)")
    op.execute("CREATE INDEX idx_transaction_currency ON transactions(currency_id)")
    op.execute("CREATE INDEX idx_transaction_date ON transactions(transaction_date DESC)")
    op.execute("CREATE INDEX idx_transaction_branch_date ON transactions(branch_id, transaction_date DESC)")
    op.execute("CREATE INDEX idx_transaction_customer_date ON transactions(customer_id, transaction_date DESC) WHERE customer_id IS NOT NULL")
    op.execute("CREATE INDEX idx_transaction_status_date ON transactions(status, transaction_date DESC)")
    
    # ==================== Create Functions & Triggers ====================
    
    # Function to generate transaction number
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_transaction_number()
        RETURNS TRIGGER AS $$
        DECLARE
            new_number VARCHAR(50);
            counter INTEGER;
        BEGIN
            -- Get the next transaction number for today
            SELECT COUNT(*) + 1 INTO counter
            FROM transactions
            WHERE DATE(created_at) = CURRENT_DATE;
            
            -- Format: TRX-YYYYMMDD-NNNNN
            new_number := 'TRX-' || 
                         TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' ||
                         LPAD(counter::TEXT, 5, '0');
            
            NEW.transaction_number := new_number;
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
    
    # Function to update updated_at
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
    
    # Function to prevent modification of completed transactions
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
    
    print("✅ Transaction tables created successfully")


def downgrade():
    """Drop transaction tables"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS trigger_prevent_completed_modification ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trigger_update_transaction_updated_at ON transactions")
    op.execute("DROP TRIGGER IF EXISTS trigger_generate_transaction_number ON transactions")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS prevent_completed_transaction_modification()")
    op.execute("DROP FUNCTION IF EXISTS update_transaction_updated_at()")
    op.execute("DROP FUNCTION IF EXISTS generate_transaction_number()")
    
    # Drop table
    op.drop_table('transactions')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS transfertype")
    op.execute("DROP TYPE IF EXISTS expensecategory")
    op.execute("DROP TYPE IF EXISTS incomecategory")
    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS transactiontype")
    
    print("✅ Transaction tables dropped successfully")