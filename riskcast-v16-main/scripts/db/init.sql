-- =============================================================================
-- RISKCAST - Database Initialization Script
-- =============================================================================
-- This script runs when the PostgreSQL container is first created

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "btree_gin";

-- Create database if not exists (usually already created by POSTGRES_DB)
-- This is just for completeness
SELECT 'CREATE DATABASE riskcast'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'riskcast')\gexec

-- Connect to riskcast database
\c riskcast

-- Create schemas
CREATE SCHEMA IF NOT EXISTS public;
CREATE SCHEMA IF NOT EXISTS audit;

-- Set default permissions
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO riskcast;
ALTER DEFAULT PRIVILEGES IN SCHEMA audit GRANT SELECT, INSERT ON TABLES TO riskcast;

-- Log initialization
DO $$
BEGIN
    RAISE NOTICE 'RiskCast database initialized successfully';
END $$;
