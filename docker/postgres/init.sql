-- CEMS PostgreSQL Initialization Script
-- This script runs automatically when PostgreSQL container is first created

-- Create database if not exists (handled by Docker env vars)
-- CREATE DATABASE cems_db;

-- Connect to the database
\c cems_db;

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";  -- For text search optimization

-- Create custom types for better performance
-- (These will be created automatically by SQLAlchemy, but we can prepare the DB)

-- Set timezone to UTC
SET timezone = 'UTC';

-- Create audit trigger function for tracking changes
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Informational comments
COMMENT ON DATABASE cems_db IS 'Currency Exchange Management System Database';

-- Grant privileges (if needed for additional users)
-- GRANT ALL PRIVILEGES ON DATABASE cems_db TO cems_user;

-- Create schemas for organization (optional)
-- CREATE SCHEMA IF NOT EXISTS auth;
-- CREATE SCHEMA IF NOT EXISTS transactions;
-- CREATE SCHEMA IF NOT EXISTS reports;

-- Performance optimizations
ALTER DATABASE cems_db SET random_page_cost = 1.1;  -- SSD optimization
ALTER DATABASE cems_db SET effective_cache_size = '4GB';

-- Connection pooling settings (optional)
-- ALTER SYSTEM SET max_connections = 200;
-- ALTER SYSTEM SET shared_buffers = '256MB';

-- Success message
SELECT 'CEMS Database initialized successfully!' AS status;