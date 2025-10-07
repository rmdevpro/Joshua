-- Dewey Schema Additions for Godot Logging
-- To be run against Winni PostgreSQL database

-- Enable UUID generation if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- REQ-DEW-002: Log entry schema
-- REQ-DEW-005: Partitioning by range on created_at
-- Note: Primary key must include partition key (created_at) for partitioned tables
CREATE TABLE logs (
    id UUID DEFAULT uuid_generate_v4(),
    trace_id UUID,
    component TEXT NOT NULL,
    level TEXT NOT NULL CHECK (level IN ('ERROR', 'WARN', 'INFO', 'DEBUG', 'TRACE')),
    message TEXT NOT NULL,
    data JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id, created_at)
) PARTITION BY RANGE (created_at);

-- Create default partition for safety
CREATE TABLE logs_default PARTITION OF logs DEFAULT;

-- Indexes for efficient querying (REQ-DEW-006, REQ-DEW-007)
CREATE INDEX idx_logs_created_at ON logs(created_at DESC);
CREATE INDEX idx_logs_trace_id ON logs(trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX idx_logs_component_time ON logs(component, created_at DESC);
CREATE INDEX idx_logs_level ON logs(level);
CREATE INDEX idx_logs_message_fts ON logs USING gin(to_tsvector('english', message));
CREATE INDEX idx_logs_data ON logs USING gin(data jsonb_path_ops);

-- Partition management function
CREATE OR REPLACE FUNCTION create_daily_log_partition()
RETURNS void AS $$
DECLARE
    partition_date TEXT;
    partition_name TEXT;
BEGIN
    partition_date := to_char(NOW() + interval '1 day', 'YYYY_MM_DD');
    partition_name := 'logs_' || partition_date;

    IF NOT EXISTS(SELECT 1 FROM pg_class WHERE relname = partition_name) THEN
        EXECUTE format(
            'CREATE TABLE %I PARTITION OF logs FOR VALUES FROM (%L) TO (%L)',
            partition_name,
            (NOW() + interval '1 day')::date,
            (NOW() + interval '2 days')::date
        );
        RAISE NOTICE 'Created partition: %', partition_name;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create initial partitions
SELECT create_daily_log_partition();

-- Logger config table (optional)
CREATE TABLE IF NOT EXISTS logger_config (
    component TEXT PRIMARY KEY,
    level TEXT NOT NULL DEFAULT 'INFO',
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- To run daily partition creation, add to cron or pg_cron:
-- SELECT create_daily_log_partition();
