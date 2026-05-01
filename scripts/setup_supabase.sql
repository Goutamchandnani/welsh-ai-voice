-- scripts/setup_supabase.sql
-- Run this in the Supabase SQL Editor

-- 1. Create the api_keys table
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    key_hash TEXT UNIQUE NOT NULL,       -- We store the hash, not the raw key, for security
    prefix TEXT NOT NULL,                -- e.g., 'lc_live_' or 'lc_test_'
    user_email TEXT NOT NULL,            -- Who owns this key
    status TEXT NOT NULL DEFAULT 'active', -- 'active' or 'revoked'
    tier TEXT NOT NULL DEFAULT 'free',   -- 'free' or 'pro'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for fast lookups when verifying keys
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
CREATE INDEX idx_api_keys_status ON api_keys(status);


-- 2. Create the usage_logs table
CREATE TABLE usage_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    api_key_id UUID REFERENCES api_keys(id), -- Links to the api_keys table
    endpoint TEXT NOT NULL,                  -- e.g., '/v1/voice'
    audio_duration_seconds FLOAT,            -- How much audio they processed (if applicable)
    latency_seconds FLOAT,                   -- How long the request took
    status_code INTEGER NOT NULL,            -- e.g., 200 or 500
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- Index for fast usage querying
CREATE INDEX idx_usage_logs_api_key_id ON usage_logs(api_key_id);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);

-- 3. Set up Row Level Security (RLS)
-- We enable RLS here for security. By not adding any policies, we block all access
-- from the public 'anon' key. Our FastAPI backend uses the 'service_role' key,
-- which automatically bypasses RLS and has full access.
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
