-- ============================================
-- 1. CREATE SCHEMA
-- ============================================
CREATE SCHEMA IF NOT EXISTS ncaa_pool;

-- ============================================
-- 2. CREATE ROLES (nologin roles for permission inheritance)
-- ============================================

-- Read-only role
CREATE ROLE ncaa_pool_read NOLOGIN;

-- Read-write role (inherits from read role)
CREATE ROLE ncaa_pool_readwrite NOLOGIN;
GRANT ncaa_pool_read TO ncaa_pool_readwrite;
GRANT ncaa_pool_readwrite TO admin;
GRANT ncaa_pool_read TO casey;
GRANT ncaa_pool_read TO cudde;
GRANT ncaa_pool_read TO pat;

-- ============================================
-- 3. GRANT SCHEMA PERMISSIONS
-- ============================================

-- Read role: usage on schema
GRANT USAGE ON SCHEMA ncaa_pool TO ncaa_pool_read;

-- ReadWrite role: usage + create on schema
GRANT USAGE, CREATE ON SCHEMA ncaa_pool TO ncaa_pool_readwrite;

-- ============================================
-- 4. GRANT PERMISSIONS ON EXISTING OBJECTS
-- ============================================

-- Read role: select on all existing tables/views
GRANT SELECT ON ALL TABLES IN SCHEMA ncaa_pool TO ncaa_pool_read;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA ncaa_pool TO ncaa_pool_read;

-- ReadWrite role: full DML on all existing tables
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ncaa_pool TO ncaa_pool_readwrite;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA ncaa_pool TO ncaa_pool_readwrite;

-- ============================================
-- 5. SET DEFAULT PRIVILEGES FOR FUTURE OBJECTS
-- ============================================

-- Future privileges for read role
ALTER DEFAULT PRIVILEGES IN SCHEMA ncaa_pool
    GRANT SELECT ON TABLES TO ncaa_pool_read;

ALTER DEFAULT PRIVILEGES IN SCHEMA ncaa_pool
    GRANT SELECT ON SEQUENCES TO ncaa_pool_read;

-- Future privileges for readwrite role
ALTER DEFAULT PRIVILEGES IN SCHEMA ncaa_pool
    GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO ncaa_pool_readwrite;

ALTER DEFAULT PRIVILEGES IN SCHEMA ncaa_pool
    GRANT USAGE, SELECT ON SEQUENCES TO ncaa_pool_readwrite;

-- ============================================
-- 6. CREATE SERVICE USER WITH LOGIN
-- ============================================

-- Create login user
CREATE ROLE ncaa_pool_app LOGIN PASSWORD '****';

-- Grant readwrite role to service user (role hierarchy)
GRANT ncaa_pool_readwrite TO ncaa_pool_app;

-- Set default search path for convenience
ALTER ROLE ncaa_pool_app SET search_path TO ncaa_pool, public;
