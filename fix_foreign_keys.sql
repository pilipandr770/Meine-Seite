-- Production database fix for foreign key constraints
-- Run this in your PostgreSQL database to fix the users foreign key issue

-- Set search path
SET search_path TO rozoom_clients,rozoom_shop,rozoom_schema;

-- Drop existing foreign key constraint if it exists
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_project_user_id'
        AND table_schema = 'projects_schema'
        AND table_name = 'project'
    ) THEN
        ALTER TABLE projects_schema.project DROP CONSTRAINT fk_project_user_id;
    END IF;
END $$;

-- Add correct foreign key constraint
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints
        WHERE constraint_name = 'fk_project_user_id_correct'
        AND table_schema = 'projects_schema'
        AND table_name = 'project'
    ) THEN
        ALTER TABLE projects_schema.project
        ADD CONSTRAINT fk_project_user_id_correct
        FOREIGN KEY (user_id) REFERENCES rozoom_schema.users(id);
    END IF;
END $$;

-- Verify the constraint was added
SELECT
    tc.constraint_name,
    tc.table_schema,
    tc.table_name,
    kcu.column_name,
    ccu.table_schema AS foreign_table_schema,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM
    information_schema.table_constraints AS tc
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE
    tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'projects_schema'
    AND tc.table_name = 'project'
    AND kcu.column_name = 'user_id';
