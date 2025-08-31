-- Database fix script for production deployment
-- Run this in your PostgreSQL database to fix foreign key issues

-- Set search path
SET search_path TO rozoom_clients,rozoom_shop,projects_schema,rozoom_schema;

-- Create project table if it doesn't exist
CREATE TABLE IF NOT EXISTS projects_schema.project (
    id SERIAL PRIMARY KEY,
    client_id INTEGER,
    user_id INTEGER,
    request_id INTEGER,
    name VARCHAR(200) NOT NULL,
    slug VARCHAR(255) UNIQUE NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'new',
    start_date TIMESTAMP,
    deadline TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create project_stage table if it doesn't exist
CREATE TABLE IF NOT EXISTS projects_schema.project_stage (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    order_number INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Add foreign key constraint if it doesn't exist
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_project_stage_project_id'
        AND table_schema = 'projects_schema'
        AND table_name = 'project_stage'
    ) THEN
        ALTER TABLE projects_schema.project_stage
        ADD CONSTRAINT fk_project_stage_project_id
        FOREIGN KEY (project_id) REFERENCES projects_schema.project(id);
    END IF;
END $$;

-- Verify tables exist
SELECT
    schemaname,
    tablename,
    tableowner
FROM pg_tables
WHERE schemaname IN ('rozoom_clients', 'rozoom_shop', 'projects_schema', 'rozoom_schema')
AND tablename IN ('project', 'project_stage', 'client_requests', 'clients', 'users')
ORDER BY schemaname, tablename;
