-- ============================================================================
-- Supabase Authentication Setup for AI Video Agent
-- ============================================================================
-- This script creates user-specific tables with Row Level Security (RLS)
-- to ensure users can only access their own data
-- ============================================================================

-- Enable UUID extension if not already enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================================
-- 1. USER FILES TABLE
-- Stores metadata for user-uploaded files
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL UNIQUE,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL, -- e.g., 'video', 'audio', 'pdf'
    file_size BIGINT NOT NULL,
    storage_path TEXT, -- Supabase Storage path
    language TEXT DEFAULT 'english',
    status TEXT DEFAULT 'processing', -- 'processing', 'completed', 'failed'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Indexes for faster queries
    CONSTRAINT user_files_file_type_check CHECK (file_type IN ('video', 'audio', 'pdf'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_files_user_id ON user_files(user_id);
CREATE INDEX IF NOT EXISTS idx_user_files_job_id ON user_files(job_id);
CREATE INDEX IF NOT EXISTS idx_user_files_created_at ON user_files(created_at DESC);

-- Enable RLS
ALTER TABLE user_files ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_files
-- Users can only see their own files
CREATE POLICY "Users can view their own files"
    ON user_files FOR SELECT
    USING (auth.uid() = user_id);

-- Users can only insert their own files
CREATE POLICY "Users can insert their own files"
    ON user_files FOR INSERT
    WITH CHECK (auth.uid() = user_id);

-- Users can only update their own files
CREATE POLICY "Users can update their own files"
    ON user_files FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- Users can only delete their own files
CREATE POLICY "Users can delete their own files"
    ON user_files FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 2. USER ANALYSIS RESULTS TABLE
-- Stores analysis results for processed files
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL REFERENCES user_files(job_id) ON DELETE CASCADE,
    title TEXT,
    transcript TEXT,
    summary TEXT,
    action_items TEXT,
    key_decisions TEXT,
    open_questions TEXT,
    source_type TEXT, -- 'video', 'audio', 'pdf'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Ensure one result per job
    UNIQUE(job_id)
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_analysis_results_user_id ON user_analysis_results(user_id);
CREATE INDEX IF NOT EXISTS idx_user_analysis_results_job_id ON user_analysis_results(job_id);

-- Enable RLS
ALTER TABLE user_analysis_results ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_analysis_results
CREATE POLICY "Users can view their own analysis results"
    ON user_analysis_results FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own analysis results"
    ON user_analysis_results FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own analysis results"
    ON user_analysis_results FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own analysis results"
    ON user_analysis_results FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 3. USER CHAT HISTORY TABLE
-- Stores chat messages for RAG interactions
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    job_id TEXT NOT NULL REFERENCES user_files(job_id) ON DELETE CASCADE,
    role TEXT NOT NULL, -- 'user' or 'assistant'
    message TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT user_chat_history_role_check CHECK (role IN ('user', 'assistant'))
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_chat_history_user_id ON user_chat_history(user_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_history_job_id ON user_chat_history(job_id);
CREATE INDEX IF NOT EXISTS idx_user_chat_history_created_at ON user_chat_history(created_at);

-- Enable RLS
ALTER TABLE user_chat_history ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_chat_history
CREATE POLICY "Users can view their own chat history"
    ON user_chat_history FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own chat messages"
    ON user_chat_history FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can delete their own chat history"
    ON user_chat_history FOR DELETE
    USING (auth.uid() = user_id);

-- ============================================================================
-- 4. USER SESSIONS TABLE
-- Tracks user sessions and activity
-- ============================================================================
CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    session_end TIMESTAMP WITH TIME ZONE,
    last_activity TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ip_address INET,
    user_agent TEXT,
    
    -- Indexes
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_user_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_user_sessions_last_activity ON user_sessions(last_activity DESC);

-- Enable RLS
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for user_sessions
CREATE POLICY "Users can view their own sessions"
    ON user_sessions FOR SELECT
    USING (auth.uid() = user_id);

CREATE POLICY "Users can insert their own sessions"
    ON user_sessions FOR INSERT
    WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update their own sessions"
    ON user_sessions FOR UPDATE
    USING (auth.uid() = user_id)
    WITH CHECK (auth.uid() = user_id);

-- ============================================================================
-- 5. FUNCTIONS FOR AUTOMATIC TIMESTAMP UPDATES
-- ============================================================================

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Triggers for updated_at columns
CREATE TRIGGER update_user_files_updated_at
    BEFORE UPDATE ON user_files
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_analysis_results_updated_at
    BEFORE UPDATE ON user_analysis_results
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 6. STORAGE BUCKET SETUP
-- ============================================================================
-- Note: Run this in Supabase Dashboard > Storage or via Supabase CLI
-- This creates a private bucket for user files

-- Create storage bucket for user files (if not exists)
INSERT INTO storage.buckets (id, name, public)
VALUES ('user-media', 'user-media', false)
ON CONFLICT (id) DO NOTHING;

-- Storage RLS policies
-- Users can only upload to their own folder
CREATE POLICY "Users can upload to their own folder"
    ON storage.objects FOR INSERT
    WITH CHECK (
        bucket_id = 'user-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can only view their own files
CREATE POLICY "Users can view their own files"
    ON storage.objects FOR SELECT
    USING (
        bucket_id = 'user-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can only update their own files
CREATE POLICY "Users can update their own files"
    ON storage.objects FOR UPDATE
    USING (
        bucket_id = 'user-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- Users can only delete their own files
CREATE POLICY "Users can delete their own files"
    ON storage.objects FOR DELETE
    USING (
        bucket_id = 'user-media' AND
        (storage.foldername(name))[1] = auth.uid()::text
    );

-- ============================================================================
-- 7. HELPER VIEWS (Optional)
-- ============================================================================

-- View for user file statistics
CREATE OR REPLACE VIEW user_file_stats AS
SELECT 
    user_id,
    COUNT(*) as total_files,
    SUM(file_size) as total_size_bytes,
    COUNT(CASE WHEN file_type = 'video' THEN 1 END) as video_count,
    COUNT(CASE WHEN file_type = 'audio' THEN 1 END) as audio_count,
    COUNT(CASE WHEN file_type = 'pdf' THEN 1 END) as pdf_count,
    COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
    COUNT(CASE WHEN status = 'processing' THEN 1 END) as processing_count,
    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count
FROM user_files
GROUP BY user_id;

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Run these to verify the setup:

-- Check if tables exist
-- SELECT table_name FROM information_schema.tables 
-- WHERE table_schema = 'public' AND table_name LIKE 'user_%';

-- Check RLS is enabled
-- SELECT tablename, rowsecurity FROM pg_tables 
-- WHERE schemaname = 'public' AND tablename LIKE 'user_%';

-- Check policies
-- SELECT tablename, policyname, permissive, roles, cmd, qual 
-- FROM pg_policies WHERE tablename LIKE 'user_%';

-- ============================================================================
-- NOTES
-- ============================================================================
-- 1. All tables use auth.uid() to reference the authenticated user
-- 2. RLS ensures users can only access their own data
-- 3. Cascade deletes ensure data cleanup when users are deleted
-- 4. Indexes optimize common query patterns
-- 5. Storage bucket uses folder-based isolation (user_id/filename)
-- ============================================================================
