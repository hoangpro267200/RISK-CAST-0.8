-- Database initialization script
-- This script runs when the MySQL container is first created

-- Ensure UTF8MB4 character set
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

-- Create database if it doesn't exist (usually already created by MYSQL_DATABASE env var)
-- CREATE DATABASE IF NOT EXISTS riskcast_v3 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Grant privileges (if needed)
-- GRANT ALL PRIVILEGES ON riskcast_v3.* TO 'riskcast'@'%';
-- FLUSH PRIVILEGES;

-- Note: Actual schema creation is handled by Alembic migrations
-- This file can be used for any pre-migration setup if needed
