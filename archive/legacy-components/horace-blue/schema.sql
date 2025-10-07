-- schema.sql

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Table: horace_collections
-- Stores named groups of files.
CREATE TABLE horace_collections (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

CREATE INDEX idx_horace_collections_name ON horace_collections(name);

-- Table: horace_files
-- The central catalog of all files managed by Horace.
CREATE TABLE horace_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_path TEXT NOT NULL,
    owner TEXT NOT NULL,
    purpose TEXT,
    tags TEXT[] DEFAULT '{}',
    size BIGINT NOT NULL,
    mime_type TEXT,
    checksum TEXT NOT NULL,  -- SHA256
    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'archived', 'deleted')),
    current_version INTEGER DEFAULT 1,
    collection_id UUID REFERENCES horace_collections(id) ON DELETE SET NULL,
    correlation_id TEXT,  -- Link to Fiedler run or conversation
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    deleted_at TIMESTAMPTZ,  -- Soft delete timestamp
    metadata JSONB DEFAULT '{}'  -- Extensible metadata
);

-- Indexes for common query patterns
CREATE INDEX idx_horace_files_owner ON horace_files(owner);
CREATE INDEX idx_horace_files_tags ON horace_files USING GIN(tags);
CREATE INDEX idx_horace_files_checksum ON horace_files(checksum);
CREATE INDEX idx_horace_files_status ON horace_files(status);
CREATE INDEX idx_horace_files_collection ON horace_files(collection_id);
CREATE INDEX idx_horace_files_created_at ON horace_files(created_at DESC);

-- Composite index for common search patterns (DeepSeek-R1 recommendation)
CREATE INDEX idx_horace_files_search ON horace_files (owner, status, created_at, mime_type);

-- Table: horace_versions
-- Tracks the history of each file.
CREATE TABLE horace_versions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    file_id UUID NOT NULL REFERENCES horace_files(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    size BIGINT NOT NULL,
    checksum TEXT NOT NULL,
    version_path TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(file_id, version)
);

CREATE INDEX idx_horace_versions_file ON horace_versions(file_id, version DESC);

-- Trigger to update the 'updated_at' timestamp on horace_files
CREATE OR REPLACE FUNCTION update_modified_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_horace_files_modtime
BEFORE UPDATE ON horace_files
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();

CREATE TRIGGER update_horace_collections_modtime
BEFORE UPDATE ON horace_collections
FOR EACH ROW
EXECUTE PROCEDURE update_modified_column();
