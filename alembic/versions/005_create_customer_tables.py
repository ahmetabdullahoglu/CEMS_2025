"""
Create customer tables - Fixed version without branch dependency

Revision ID: 005_create_customer_tables
Revises: 003_branch_tables
Create Date: 2025-01-10 10:00:00.000000

Phase 5.1: Customer Management Module
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = '005_create_customer_tables'
down_revision = '003_branch_tables'
branch_labels = None
depends_on = None


def upgrade():
    """Create customer tables"""
    
    # ==================== Create Enums ====================
    op.execute("""
        CREATE TYPE customer_type_enum AS ENUM ('individual', 'corporate')
    """)
    
    op.execute("""
        CREATE TYPE risk_level_enum AS ENUM ('low', 'medium', 'high')
    """)
    
    op.execute("""
        CREATE TYPE document_type_enum AS ENUM (
            'national_id', 'passport', 'driving_license', 'utility_bill',
            'bank_statement', 'commercial_registration', 'tax_certificate', 'other'
        )
    """)
    
    # ==================== Create customers table ====================
    op.execute("""
        CREATE TABLE customers (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_number VARCHAR(20) UNIQUE NOT NULL,
            
            -- Personal Information
            customer_type customer_type_enum NOT NULL DEFAULT 'individual',
            first_name VARCHAR(100) NOT NULL,
            last_name VARCHAR(100) NOT NULL,
            name_ar VARCHAR(200),
            date_of_birth DATE,
            nationality VARCHAR(100) NOT NULL,
            
            -- Identification
            national_id VARCHAR(20) UNIQUE,
            passport_number VARCHAR(50) UNIQUE,
            id_expiry_date DATE,
            
            -- Contact Information
            phone_number VARCHAR(20) NOT NULL,
            email VARCHAR(255),
            address TEXT,
            city VARCHAR(100),
            country VARCHAR(100) DEFAULT 'Turkey',
            
            -- Corporate Information (for corporate customers)
            company_name VARCHAR(200),
            tax_number VARCHAR(50),
            commercial_registration VARCHAR(100),
            
            -- Risk & Verification
            risk_level risk_level_enum NOT NULL DEFAULT 'low',
            is_verified BOOLEAN NOT NULL DEFAULT false,
            verification_notes TEXT,
            
            -- Branch Assignment
            branch_id UUID NOT NULL REFERENCES branches(id) ON DELETE RESTRICT,
            
            -- Registration & Verification
            registered_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            registered_at TIMESTAMP NOT NULL DEFAULT NOW(),
            verified_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            verified_at TIMESTAMP,
            
            -- Activity
            last_transaction_date TIMESTAMP,
            is_active BOOLEAN NOT NULL DEFAULT true,
            
            -- Additional Information
            additional_info JSONB,
            notes TEXT,
            
            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
            
            -- Constraints
            CONSTRAINT customer_must_have_identification 
                CHECK (national_id IS NOT NULL OR passport_number IS NOT NULL),
            CONSTRAINT customer_type_specific_fields
                CHECK (
                    (customer_type = 'individual') OR
                    (customer_type = 'corporate')
                )
        )
    """)
    
    # Create indexes (separate execute for each)
    op.execute("CREATE INDEX idx_customer_number ON customers(customer_number)")
    op.execute("CREATE INDEX idx_customer_full_name ON customers(first_name, last_name)")
    op.execute("CREATE INDEX idx_customer_branch_active ON customers(branch_id, is_active)")
    op.execute("CREATE INDEX idx_customer_risk_active ON customers(risk_level, is_active)")
    op.execute("CREATE INDEX idx_customer_national_id ON customers(national_id) WHERE national_id IS NOT NULL")
    op.execute("CREATE INDEX idx_customer_passport ON customers(passport_number) WHERE passport_number IS NOT NULL")
    op.execute("CREATE INDEX idx_customer_phone ON customers(phone_number)")
    
    # ==================== Create customer_documents table ====================
    op.execute("""
        CREATE TABLE customer_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            
            -- Document Information
            document_type document_type_enum NOT NULL,
            document_number VARCHAR(100),
            issue_date DATE,
            expiry_date DATE,
            issuing_authority VARCHAR(200),
            document_url VARCHAR(500),

            -- File Information
            file_path VARCHAR(500),
            file_name VARCHAR(255),
            file_size INTEGER,
            mime_type VARCHAR(100),
            
            -- Verification
            is_verified BOOLEAN NOT NULL DEFAULT false,
            verified_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            verified_at TIMESTAMP,
            verification_notes TEXT,
            
            -- Metadata
            uploaded_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            uploaded_at TIMESTAMP NOT NULL DEFAULT NOW(),
            notes TEXT,
            
            -- Timestamps
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create indexes for documents (separate execute for each)
    op.execute("CREATE INDEX idx_customer_documents_customer ON customer_documents(customer_id)")
    op.execute("CREATE INDEX idx_customer_documents_type ON customer_documents(document_type)")
    op.execute("CREATE INDEX idx_customer_documents_verified ON customer_documents(is_verified)")
    op.execute("CREATE INDEX idx_customer_documents_expiry ON customer_documents(expiry_date) WHERE expiry_date IS NOT NULL")
    
    # ==================== Create customer_notes table ====================
    op.execute("""
        CREATE TABLE customer_notes (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
            
            -- Note Content
            note_text TEXT NOT NULL,
            is_alert BOOLEAN NOT NULL DEFAULT false,
            
            -- Metadata
            created_by_id UUID REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    """)
    
    # Create indexes for notes (separate execute for each)
    op.execute("CREATE INDEX idx_customer_notes_customer ON customer_notes(customer_id)")
    op.execute("CREATE INDEX idx_customer_notes_alert ON customer_notes(customer_id, is_alert)")
    op.execute("CREATE INDEX idx_customer_notes_created ON customer_notes(created_at DESC)")
    
    # ==================== Create Triggers ====================
    
    # Function to update updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Function to generate customer number
    op.execute("""
        CREATE OR REPLACE FUNCTION generate_customer_number()
        RETURNS TRIGGER AS $$
        DECLARE
            new_number VARCHAR(20);
            counter INTEGER;
        BEGIN
            -- Get the next customer number for today
            SELECT COUNT(*) + 1 INTO counter
            FROM customers
            WHERE DATE(created_at) = CURRENT_DATE;
            
            -- Format: CUST-YYYYMMDD-NNNN
            new_number := 'CUST-' || 
                         TO_CHAR(CURRENT_DATE, 'YYYYMMDD') || '-' ||
                         LPAD(counter::TEXT, 4, '0');
            
            NEW.customer_number := new_number;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)
    
    # Create triggers
    op.execute("""
        CREATE TRIGGER generate_customer_number_trigger
        BEFORE INSERT ON customers
        FOR EACH ROW
        WHEN (NEW.customer_number IS NULL)
        EXECUTE FUNCTION generate_customer_number();
    """)
    
    op.execute("""
        CREATE TRIGGER update_customers_updated_at
        BEFORE UPDATE ON customers
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_customer_documents_updated_at
        BEFORE UPDATE ON customer_documents
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    op.execute("""
        CREATE TRIGGER update_customer_notes_updated_at
        BEFORE UPDATE ON customer_notes
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)
    
    print("✅ Customer tables created successfully")


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
    
    # Drop tables (in reverse order due to foreign keys)
    op.drop_table('customer_notes')
    op.drop_table('customer_documents')
    op.drop_table('customers')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS document_type_enum;")
    op.execute("DROP TYPE IF EXISTS risk_level_enum;")
    op.execute("DROP TYPE IF EXISTS customer_type_enum;")
    
    print("✅ Customer tables dropped successfully")