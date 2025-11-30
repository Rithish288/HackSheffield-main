-- ReplyChallenge Database Schema
-- Run this SQL in your Supabase SQL Editor

-- Create the requests table
CREATE TABLE IF NOT EXISTS requests (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  
  -- Conversation tracking
  session_id TEXT NOT NULL,
  
  -- User information
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  username TEXT DEFAULT 'WebUser',
  
  -- Chat content
  prompt TEXT NOT NULL,
  response TEXT NOT NULL,
  
  -- API tracking
  tokens_used INTEGER,
  metadata JSONB,
  
  -- Timestamps
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::TEXT, NOW()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::TEXT, NOW()) NOT NULL
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_requests_session_id ON requests(session_id);
CREATE INDEX IF NOT EXISTS idx_requests_created_at ON requests(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_requests_user_id ON requests(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_username ON requests(username);

-- Enable Row Level Security (optional, but recommended)
ALTER TABLE requests ENABLE ROW LEVEL SECURITY;

-- Create policy to allow anonymous users to read/write
CREATE POLICY "Allow all operations" ON requests
  FOR ALL
  USING (TRUE)
  WITH CHECK (TRUE);

-- Done! Your table is ready to use.

-- Facts table (structured extracted memories / user facts)
CREATE TABLE IF NOT EXISTS facts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES auth.users ON DELETE SET NULL,
  username TEXT,
  request_id UUID REFERENCES requests(id) ON DELETE SET NULL,
  fact_type TEXT NOT NULL,
  value TEXT NOT NULL,
  normalized_value TEXT,
  confidence NUMERIC,
  metadata JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::TEXT, NOW()) NOT NULL,
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT TIMEZONE('utc'::TEXT, NOW()) NOT NULL,
  active BOOLEAN DEFAULT TRUE
);

CREATE INDEX IF NOT EXISTS idx_facts_user_id ON facts(user_id);
CREATE INDEX IF NOT EXISTS idx_facts_username ON facts(username);
CREATE INDEX IF NOT EXISTS idx_facts_fact_type ON facts(fact_type);
