-- JARVIS Migration 002: Row-Level Security
-- Locks down all tables so only the service role (JARVIS backend) can read/write.
-- Run once after 001_init.sql.

-- Enable RLS on every data table
ALTER TABLE IF EXISTS memories         ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects         ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tasks            ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS businesses       ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS delegations      ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS execution_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS knowledge_graph  ENABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS events           ENABLE ROW LEVEL SECURITY;

-- Drop any existing policies to avoid conflicts
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY['memories','projects','tasks','businesses',
                               'delegations','execution_history',
                               'knowledge_graph','events'])
  LOOP
    EXECUTE format('DROP POLICY IF EXISTS jarvis_backend_only ON %I', t);
  END LOOP;
END $$;

-- Single policy: only the database role that the JARVIS backend connects as
-- (set DATABASE_URL with this role) may perform any operation.
-- Public / anonymous connections are denied by default once RLS is enabled
-- and no permissive policy matches them.
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY['memories','projects','tasks','businesses',
                               'delegations','execution_history',
                               'knowledge_graph','events'])
  LOOP
    EXECUTE format(
      'CREATE POLICY jarvis_backend_only ON %I
       USING (current_user = current_setting(''app.db_user'', true)
              OR current_user = ''postgres''
              OR current_user = ''jarvis'')',
      t
    );
  END LOOP;
END $$;

-- Force RLS even for the table owner (prevents accidental superuser bypass)
DO $$
DECLARE
  t text;
BEGIN
  FOR t IN SELECT unnest(ARRAY['memories','projects','tasks','businesses',
                               'delegations','execution_history',
                               'knowledge_graph','events'])
  LOOP
    EXECUTE format('ALTER TABLE %I FORCE ROW LEVEL SECURITY', t);
  END LOOP;
END $$;

COMMENT ON SCHEMA public IS 'JARVIS RLS applied — only the service role may access data tables.';
