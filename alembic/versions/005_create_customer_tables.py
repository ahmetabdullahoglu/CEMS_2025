"""
Create customer tables - Fixed version without branch dependency

Revision ID: 005_create_customer_tables_v2
Revises: 
Create Date: 2025-01-10 10:00:00.000000

Phase 5.1: Customer Management Module
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '005_create_customer_tables'
down_revision = '003_branch_tables'  # Will be set to your current head
branch_table_name = None
depends_on = None


def upgrade():
    """Create customer tables"""
    
    # Define enums (don't create - already exist)
    customer_type_enum = postgresql.ENUM(
        'individual', 'corporate',
        name='customer_type_enum',
        create_type=False
    )
    
    risk_level_enum = postgresql.ENUM(
        'low', 'medium', 'high',
        name='risk_level_enum',
        create_type=False
    )
    
    document_type_enum = postgresql.ENUM(
        'national_id', 'passport', 'driving_license', 'utility_bill',
        'bank_statement', 'commercial_registration', 'tax_certificate', 'other',
        name='document_type_enum',
        create_type=False
    )
    
    # Continue with table creation...

def downgrade():
    """Drop customer tables"""
    
    # Drop triggers
    op.execute("DROP TRIGGER IF EXISTS generate_customer_number_trigger ON customers;")
    op.execute("DROP TRIGGER IF EXISTS update_customer_notes_updated_at ON customer_notes;")
    op.execute("DROP TRIGGER IF EXISTS update_customer_documents_updated_at ON customer_documents;")
    op.execute("DROP TRIGGER IF EXISTS update_customers_updated_at ON customers;")
    
    # Drop functions
    op.execute("DROP FUNCTION IF EXISTS generate_customer_number();")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop tables
    op.drop_table('customer_notes')
    op.drop_table('customer_documents')
    op.drop_table('customers')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS document_type_enum;")
    op.execute("DROP TYPE IF EXISTS risk_level_enum;")
    op.execute("DROP TYPE IF EXISTS customer_type_enum;")
