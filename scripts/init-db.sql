-- ============================================================
-- ERP SaaS PostgreSQL Initialization
-- Compliance Firewall: creates ai_readonly role
-- Run once on DB primary during first boot
-- ============================================================

-- ── AI Read-Only Role (Compliance Firewall Layer 1) ──────────
-- This role is used exclusively by the AI Platform.
-- It can SELECT from all tenant schemas.
-- INSERT, UPDATE, DELETE are permanently revoked.
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ai_readonly') THEN
        CREATE ROLE ai_readonly LOGIN PASSWORD 'ai_readonly_change_me';
        RAISE NOTICE 'Created role: ai_readonly';
    END IF;
END
$$;

-- Grant connect to main database
GRANT CONNECT ON DATABASE erp_saas TO ai_readonly;

-- Grant usage on public schema
GRANT USAGE ON SCHEMA public TO ai_readonly;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO ai_readonly;

-- Explicitly revoke write permissions on public schema (defense in depth)
REVOKE INSERT, UPDATE, DELETE, TRUNCATE
    ON ALL TABLES IN SCHEMA public FROM ai_readonly;

-- ── AI Results Schema ────────────────────────────────────────
-- AI Platform writes its OWN outputs here (forecasts, anomaly scores, KPI snapshots).
-- This schema is NOT part of the ERP financial ledger.
CREATE SCHEMA IF NOT EXISTS ai_results;
GRANT ALL PRIVILEGES ON SCHEMA ai_results TO ai_readonly;
ALTER DEFAULT PRIVILEGES IN SCHEMA ai_results
    GRANT ALL ON TABLES TO ai_readonly;

-- ── Function: Grant ai_readonly on new tenant schema ─────────
-- Called automatically via Django signal when a new tenant is created.
CREATE OR REPLACE FUNCTION grant_ai_readonly_on_tenant_schema(schema_name TEXT)
RETURNS VOID AS $$
BEGIN
    EXECUTE format('GRANT USAGE ON SCHEMA %I TO ai_readonly', schema_name);
    EXECUTE format('GRANT SELECT ON ALL TABLES IN SCHEMA %I TO ai_readonly', schema_name);
    EXECUTE format(
        'ALTER DEFAULT PRIVILEGES IN SCHEMA %I GRANT SELECT ON TABLES TO ai_readonly',
        schema_name
    );
    EXECUTE format(
        'REVOKE INSERT, UPDATE, DELETE, TRUNCATE ON ALL TABLES IN SCHEMA %I FROM ai_readonly',
        schema_name
    );
    RAISE NOTICE 'Granted ai_readonly SELECT on schema: %', schema_name;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- ── ZATCA Invoice Log: Immutability Policy ────────────────────
-- The ZATCAInvoiceLog table in public schema is INSERT-only.
-- Even erp_readwrite cannot UPDATE or DELETE audit log rows.
-- This is enforced after the table is created by Django migrations.
-- Run this AFTER initial migrate:
--
-- REVOKE UPDATE, DELETE ON public.zatca_zatcainvoicelog FROM erp_readwrite;
-- (Uncomment and run after first migration)

-- ── Replication user for read replica ────────────────────────
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'replicator') THEN
        CREATE ROLE replicator WITH REPLICATION LOGIN PASSWORD 'replicator_change_me';
        RAISE NOTICE 'Created role: replicator';
    END IF;
END
$$;

GRANT CONNECT ON DATABASE erp_saas TO replicator;

-- ── Performance tuning for multi-tenant workloads ────────────
ALTER SYSTEM SET max_connections = '200';
ALTER SYSTEM SET shared_buffers = '256MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET work_mem = '8MB';
ALTER SYSTEM SET maintenance_work_mem = '64MB';
ALTER SYSTEM SET wal_level = 'replica';
ALTER SYSTEM SET max_wal_senders = '3';
ALTER SYSTEM SET wal_keep_size = '64MB';
ALTER SYSTEM SET hot_standby = 'on';

SELECT pg_reload_conf();
