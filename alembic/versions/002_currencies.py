"""create currencies and exchange rates tables

Revision ID: 002_currencies
Revises: 001_users_roles
Create Date: 2025-01-10 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision: str = '002_currencies'
down_revision: Union[str, None] = '001_users_roles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create currency-related tables"""
    
    # Create currencies table
    op.create_table(
        'currencies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('code', sa.String(3), nullable=False, unique=True, index=True),
        sa.Column('name_en', sa.String(100), nullable=False),
        sa.Column('name_ar', sa.String(100), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=True),
        sa.Column('is_base_currency', sa.Boolean(), nullable=False, server_default='false', index=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('decimal_places', sa.Integer(), nullable=False, server_default='2'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint('LENGTH(code) = 3', name='currency_code_length_check'),
        sa.CheckConstraint('decimal_places >= 0', name='currency_decimal_places_positive'),
    )
    
    # Create exchange_rates table
    op.create_table(
        'exchange_rates',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('from_currency_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('to_currency_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('currencies.id', ondelete='RESTRICT'), nullable=False, index=True),
        sa.Column('rate', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('buy_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('sell_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('effective_from', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('effective_to', sa.DateTime(), nullable=True, index=True),
        sa.Column('set_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('notes', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.UniqueConstraint('from_currency_id', 'to_currency_id', 'effective_from', name='unique_currency_pair_time'),
        sa.CheckConstraint('rate > 0', name='exchange_rate_positive'),
        sa.CheckConstraint('buy_rate IS NULL OR buy_rate > 0', name='buy_rate_positive'),
        sa.CheckConstraint('sell_rate IS NULL OR sell_rate > 0', name='sell_rate_positive'),
        sa.CheckConstraint('from_currency_id != to_currency_id', name='different_currencies'),
        sa.CheckConstraint('effective_to IS NULL OR effective_to > effective_from', name='valid_effective_period'),
    )
    
    # Create exchange_rate_history table
    op.create_table(
        'exchange_rate_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('exchange_rate_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('exchange_rates.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('from_currency_code', sa.String(3), nullable=False),
        sa.Column('to_currency_code', sa.String(3), nullable=False),
        sa.Column('old_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('old_buy_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('old_sell_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('new_rate', sa.Numeric(precision=15, scale=6), nullable=False),
        sa.Column('new_buy_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('new_sell_rate', sa.Numeric(precision=15, scale=6), nullable=True),
        sa.Column('change_type', sa.String(20), nullable=False),
        sa.Column('changed_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('changed_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('reason', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        
        # Constraints
        sa.CheckConstraint("change_type IN ('created', 'updated', 'deactivated')", name='valid_change_type'),
    )
    
    # Create indexes for better performance
    op.create_index('idx_exchange_rates_from_currency', 'exchange_rates', ['from_currency_id'])
    op.create_index('idx_exchange_rates_to_currency', 'exchange_rates', ['to_currency_id'])
    op.create_index('idx_exchange_rates_effective_period', 'exchange_rates', ['effective_from', 'effective_to'])
    op.create_index('idx_exchange_rate_history_changed_at', 'exchange_rate_history', ['changed_at'])
    
    # Create trigger for updated_at on currencies
    op.execute("""
        CREATE TRIGGER update_currencies_updated_at BEFORE UPDATE ON currencies
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create trigger for updated_at on exchange_rates
    op.execute("""
        CREATE TRIGGER update_exchange_rates_updated_at BEFORE UPDATE ON exchange_rates
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """)
    
    # Create function to track exchange rate changes
    op.execute("""
        CREATE OR REPLACE FUNCTION track_exchange_rate_changes()
        RETURNS TRIGGER AS $$
        DECLARE
            from_code TEXT;
            to_code TEXT;
        BEGIN
            -- Get currency codes
            SELECT code INTO from_code FROM currencies WHERE id = NEW.from_currency_id;
            SELECT code INTO to_code FROM currencies WHERE id = NEW.to_currency_id;
            
            IF TG_OP = 'INSERT' THEN
                -- Log creation
                INSERT INTO exchange_rate_history (
                    id, exchange_rate_id, from_currency_code, to_currency_code,
                    new_rate, new_buy_rate, new_sell_rate,
                    change_type, changed_by, changed_at
                ) VALUES (
                    gen_random_uuid(), NEW.id, from_code, to_code,
                    NEW.rate, NEW.buy_rate, NEW.sell_rate,
                    'created', NEW.set_by, NOW()
                );
            ELSIF TG_OP = 'UPDATE' THEN
                -- Log update if rates changed
                IF NEW.rate != OLD.rate OR 
                   NEW.buy_rate IS DISTINCT FROM OLD.buy_rate OR 
                   NEW.sell_rate IS DISTINCT FROM OLD.sell_rate THEN
                    INSERT INTO exchange_rate_history (
                        id, exchange_rate_id, from_currency_code, to_currency_code,
                        old_rate, old_buy_rate, old_sell_rate,
                        new_rate, new_buy_rate, new_sell_rate,
                        change_type, changed_by, changed_at
                    ) VALUES (
                        gen_random_uuid(), NEW.id, from_code, to_code,
                        OLD.rate, OLD.buy_rate, OLD.sell_rate,
                        NEW.rate, NEW.buy_rate, NEW.sell_rate,
                        'updated', NEW.set_by, NOW()
                    );
                END IF;
            END IF;
            
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to track exchange rate changes
    op.execute("""
        CREATE TRIGGER track_exchange_rate_changes_trigger
        AFTER INSERT OR UPDATE ON exchange_rates
        FOR EACH ROW EXECUTE FUNCTION track_exchange_rate_changes();
    """)
    
    # Create function to prevent multiple base currencies
    op.execute("""
        CREATE OR REPLACE FUNCTION check_single_base_currency()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.is_base_currency = TRUE THEN
                -- Check if another base currency exists
                IF EXISTS (
                    SELECT 1 FROM currencies 
                    WHERE is_base_currency = TRUE 
                    AND id != NEW.id
                    AND is_active = TRUE
                ) THEN
                    RAISE EXCEPTION 'Only one base currency can be active at a time';
                END IF;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create trigger to enforce single base currency
    op.execute("""
        CREATE TRIGGER check_single_base_currency_trigger
        BEFORE INSERT OR UPDATE ON currencies
        FOR EACH ROW EXECUTE FUNCTION check_single_base_currency();
    """)


def downgrade() -> None:
    """Drop all currency-related tables and triggers"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS check_single_base_currency_trigger ON currencies;")
    op.execute("DROP TRIGGER IF EXISTS track_exchange_rate_changes_trigger ON exchange_rates;")
    op.execute("DROP TRIGGER IF EXISTS update_exchange_rates_updated_at ON exchange_rates;")
    op.execute("DROP TRIGGER IF EXISTS update_currencies_updated_at ON currencies;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS check_single_base_currency();")
    op.execute("DROP FUNCTION IF EXISTS track_exchange_rate_changes();")
    
    # Drop indexes
    op.drop_index('idx_exchange_rate_history_changed_at', 'exchange_rate_history')
    op.drop_index('idx_exchange_rates_effective_period', 'exchange_rates')
    op.drop_index('idx_exchange_rates_to_currency', 'exchange_rates')
    op.drop_index('idx_exchange_rates_from_currency', 'exchange_rates')
    
    # Drop tables
    op.drop_table('exchange_rate_history')
    op.drop_table('exchange_rates')
    op.drop_table('currencies')