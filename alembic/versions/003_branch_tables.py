"""Add branch tables

Revision ID: 003_branch_tables
Revises: 002_currencies
Create Date: 2025-10-10 16:30:00
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '003_branch_tables'
down_revision = '002_currencies'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE regionenum AS ENUM ('Istanbul_European', 'Istanbul_Asian', 'Ankara', 'Izmir', 'Bursa', 'Antalya', 'Adana', 'Gaziantep', 'Konya', 'Other')")
    op.execute("CREATE TYPE balancealerttype AS ENUM ('low_balance', 'high_balance', 'suspicious_activity', 'reconciliation_needed', 'threshold_warning')")
    op.execute("CREATE TYPE alertseverity AS ENUM ('info', 'warning', 'critical')")
    op.execute("CREATE TYPE balancechangetype AS ENUM ('transaction', 'adjustment', 'transfer_in', 'transfer_out', 'reconciliation', 'initial_balance')")
    
    # Create branches table
    op.execute("""
        CREATE TABLE branches (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            code VARCHAR(10) UNIQUE NOT NULL,
            name_en VARCHAR(200) NOT NULL,
            name_ar VARCHAR(200) NOT NULL,
            region regionenum NOT NULL,
            address VARCHAR(500) NOT NULL,
            city VARCHAR(100) NOT NULL,
            phone VARCHAR(20) NOT NULL,
            email VARCHAR(100),
            manager_id UUID REFERENCES users(id) ON DELETE SET NULL,
            is_main_branch BOOLEAN NOT NULL DEFAULT false,
            opening_balance_date TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            created_by UUID,
            updated_by UUID,
            CONSTRAINT branch_code_format_check CHECK (code ~ '^BR[0-9]{3,6}$'),
            CONSTRAINT branch_phone_length_check CHECK (LENGTH(phone) >= 10)
        )
    """)
    
    op.execute("CREATE INDEX idx_branch_code ON branches(code)")
    op.execute("CREATE INDEX idx_branch_region_active ON branches(region, is_active)")
    op.execute("CREATE INDEX idx_branch_main ON branches(is_main_branch, is_active)")
    
    # Create branch_balances table
    op.execute("""
        CREATE TABLE branch_balances (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
            currency_id UUID NOT NULL REFERENCES currencies(id) ON DELETE RESTRICT,
            balance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            reserved_balance NUMERIC(15, 2) NOT NULL DEFAULT 0,
            minimum_threshold NUMERIC(15, 2),
            maximum_threshold NUMERIC(15, 2),
            last_updated TIMESTAMP NOT NULL DEFAULT now(),
            last_reconciled_at TIMESTAMP,
            last_reconciled_by UUID REFERENCES users(id) ON DELETE SET NULL,
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            UNIQUE(branch_id, currency_id),
            CONSTRAINT branch_balance_positive_check CHECK (balance >= 0),
            CONSTRAINT reserved_balance_positive_check CHECK (reserved_balance >= 0),
            CONSTRAINT reserved_not_exceeding_balance CHECK (reserved_balance <= balance)
        )
    """)
    
    op.execute("CREATE INDEX idx_branch_balance_lookup ON branch_balances(branch_id, currency_id)")
    
    # Create branch_balance_history table
    op.execute("""
        CREATE TABLE branch_balance_history (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
            currency_id UUID NOT NULL REFERENCES currencies(id) ON DELETE RESTRICT,
            change_type balancechangetype NOT NULL,
            amount NUMERIC(15, 2) NOT NULL,
            balance_before NUMERIC(15, 2) NOT NULL,
            balance_after NUMERIC(15, 2) NOT NULL,
            reference_id UUID,
            reference_type VARCHAR(50),
            performed_by UUID REFERENCES users(id) ON DELETE SET NULL,
            performed_at TIMESTAMP NOT NULL DEFAULT now(),
            notes VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now(),
            CONSTRAINT history_balance_before_positive CHECK (balance_before >= 0),
            CONSTRAINT history_balance_after_positive CHECK (balance_after >= 0)
        )
    """)
    
    op.execute("CREATE INDEX idx_balance_history_lookup ON branch_balance_history(branch_id, currency_id, performed_at)")
    
    # Create branch_alerts table
    op.execute("""
        CREATE TABLE branch_alerts (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE CASCADE,
            currency_id UUID REFERENCES currencies(id) ON DELETE RESTRICT,
            alert_type balancealerttype NOT NULL,
            severity alertseverity NOT NULL DEFAULT 'info',
            title VARCHAR(200) NOT NULL,
            message VARCHAR(1000) NOT NULL,
            alert_data TEXT,
            is_resolved BOOLEAN NOT NULL DEFAULT false,
            triggered_at TIMESTAMP NOT NULL DEFAULT now(),
            resolved_at TIMESTAMP,
            resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
            resolution_notes VARCHAR(500),
            is_active BOOLEAN NOT NULL DEFAULT true,
            created_at TIMESTAMP NOT NULL DEFAULT now(),
            updated_at TIMESTAMP NOT NULL DEFAULT now()
        )
    """)
    
    op.execute("CREATE INDEX idx_branch_alerts_active ON branch_alerts(branch_id, is_resolved, severity)")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS branch_alerts CASCADE")
    op.execute("DROP TABLE IF EXISTS branch_balance_history CASCADE")
    op.execute("DROP TABLE IF EXISTS branch_balances CASCADE")
    op.execute("DROP TABLE IF EXISTS branches CASCADE")
    op.execute("DROP TYPE IF EXISTS balancechangetype")
    op.execute("DROP TYPE IF EXISTS alertseverity")
    op.execute("DROP TYPE IF EXISTS balancealerttype")
    op.execute("DROP TYPE IF EXISTS regionenum")
