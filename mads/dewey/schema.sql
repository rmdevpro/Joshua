-- Dewey Database Schema
-- Conversation storage with full-text search support

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Conversations table
CREATE TABLE IF NOT EXISTS conversations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id TEXT,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    turn_number INTEGER NOT NULL,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system', 'tool')),
    content TEXT NOT NULL,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(conversation_id, turn_number)
);

-- Startup contexts table
CREATE TABLE IF NOT EXISTS startup_contexts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT UNIQUE NOT NULL,
    content TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance

-- Index for conversation lookups by session_id
CREATE INDEX IF NOT EXISTS idx_conversations_session_id ON conversations(session_id);

-- Index for conversation sorting
CREATE INDEX IF NOT EXISTS idx_conversations_updated_at ON conversations(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at DESC);

-- Index for message lookups by conversation
CREATE INDEX IF NOT EXISTS idx_messages_conversation_id ON messages(conversation_id);

-- Index for message ordering
CREATE INDEX IF NOT EXISTS idx_messages_turn_number ON messages(conversation_id, turn_number);

-- GIN index for full-text search on message content
-- This is CRITICAL for search performance
CREATE INDEX IF NOT EXISTS idx_messages_content_fts
    ON messages USING gin(to_tsvector('english', content));

-- Index for timestamp filtering in search
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Index for active startup context lookup
CREATE INDEX IF NOT EXISTS idx_startup_contexts_active ON startup_contexts(is_active) WHERE is_active = TRUE;

-- Function to automatically update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on conversations
CREATE TRIGGER update_conversations_updated_at
    BEFORE UPDATE ON conversations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on startup_contexts
CREATE TRIGGER update_startup_contexts_updated_at
    BEFORE UPDATE ON startup_contexts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Logs table for unified logging infrastructure
CREATE TABLE IF NOT EXISTS logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    component TEXT NOT NULL,  -- e.g., 'relay', 'gates', 'fiedler', 'dewey'
    level TEXT NOT NULL CHECK (level IN ('ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')),
    message TEXT NOT NULL,
    data JSONB,  -- Structured log data (e.g., full request/response objects)
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for log queries
CREATE INDEX IF NOT EXISTS idx_logs_component ON logs(component);
CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_logs_component_created_at ON logs(component, created_at DESC);

-- GIN index for full-text search on log messages
CREATE INDEX IF NOT EXISTS idx_logs_message_fts
    ON logs USING gin(to_tsvector('english', message));

-- GIN index for JSON data queries
CREATE INDEX IF NOT EXISTS idx_logs_data ON logs USING gin(data);
