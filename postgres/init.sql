-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ─── MEMORY SYSTEM ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS memories (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    content     TEXT NOT NULL,
    summary     TEXT,
    embedding   VECTOR(1536),
    category    VARCHAR(50) NOT NULL DEFAULT 'episodic',
    -- categories: episodic | semantic | project | business | preference
    metadata    JSONB DEFAULT '{}',
    importance  FLOAT DEFAULT 0.5,
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memories_category    ON memories(category);
CREATE INDEX IF NOT EXISTS idx_memories_user_id     ON memories(user_id);
CREATE INDEX IF NOT EXISTS idx_memories_created_at  ON memories(created_at DESC);
-- Vector similarity index (IVFFlat for cosine similarity)
CREATE INDEX IF NOT EXISTS idx_memories_embedding
    ON memories USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ─── AGENT TASKS ────────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS agent_tasks (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    agent_type      VARCHAR(50) NOT NULL,  -- cto | sales | research | coding | operations | marketing | website | monitoring
    goal            TEXT NOT NULL,
    plan            JSONB DEFAULT '[]',    -- array of step objects
    status          VARCHAR(20) DEFAULT 'pending', -- pending | running | completed | failed | cancelled
    result_summary  TEXT,
    error_message   TEXT,
    context_refs    UUID[] DEFAULT '{}',   -- FK links to memories
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tasks_status     ON agent_tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_agent_type ON agent_tasks(agent_type);

-- ─── CHAT SESSIONS ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_sessions (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id     UUID NOT NULL DEFAULT '00000000-0000-0000-0000-000000000001',
    title       TEXT,
    mode        VARCHAR(20) DEFAULT 'text',  -- text | voice
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    last_active TIMESTAMPTZ DEFAULT NOW()
);

-- ─── CHAT MESSAGES ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS chat_messages (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id  UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role        VARCHAR(20) NOT NULL,   -- user | assistant | system | tool
    content     TEXT NOT NULL,
    tool_calls  JSONB,
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_messages_session_id ON chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON chat_messages(created_at DESC);

-- ─── CRM LEADS (DealCenter cache) ───────────────────────────────────────────
CREATE TABLE IF NOT EXISTS crm_leads (
    id              UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    external_id     VARCHAR(100),  -- DealCenter lead ID
    name            TEXT NOT NULL,
    email           VARCHAR(255),
    phone           VARCHAR(50),
    intent_score    FLOAT DEFAULT 0.5,
    status          VARCHAR(50) DEFAULT 'new',
    vehicle_interest TEXT,
    last_contacted  TIMESTAMPTZ,
    notes           TEXT,
    metadata        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- ─── KNOWLEDGE BASE ─────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS knowledge_items (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    title       TEXT NOT NULL,
    content     TEXT NOT NULL,
    embedding   VECTOR(1536),
    source_type VARCHAR(50),  -- url | file | repo | video | manual
    source_url  TEXT,
    tags        TEXT[] DEFAULT '{}',
    metadata    JSONB DEFAULT '{}',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_knowledge_embedding
    ON knowledge_items USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);

-- ─── SYSTEM HEALTH ──────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS health_logs (
    id          UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    service     VARCHAR(50) NOT NULL,
    status      VARCHAR(20) NOT NULL,  -- healthy | degraded | down
    latency_ms  INTEGER,
    message     TEXT,
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- ─── AUTO-UPDATE updated_at ──────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_memories_updated_at     BEFORE UPDATE ON memories      FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_tasks_updated_at        BEFORE UPDATE ON agent_tasks   FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_leads_updated_at        BEFORE UPDATE ON crm_leads     FOR EACH ROW EXECUTE FUNCTION update_updated_at();

-- Seed a default chat session for testing
INSERT INTO chat_sessions (id, title) VALUES
    ('11111111-1111-1111-1111-111111111111', 'JARVIS Default Session')
ON CONFLICT DO NOTHING;
