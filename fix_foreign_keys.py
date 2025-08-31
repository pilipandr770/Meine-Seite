#!/usr/bin/env python3
"""
Database migration script to fix foreign key constraints in production.
Run this script to fix the users foreign key issue.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text, MetaData, Table, Column, Integer, String, DateTime, Text, Boolean, ForeignKey
from sqlalchemy.exc import SQLAlchemyError

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import get_postgres_uri, db
from app.models.user import User
from app.models.project import Project, ProjectStage
from app.models.client import Client, ClientRequest

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fix_foreign_keys():
    """Fix foreign key constraints for production deployment."""

    try:
        # Get database URI
        database_url = get_postgres_uri()
        logger.info(f"Connecting to database: {database_url.replace(database_url.split('@')[0].split(':')[1], '***')}")

        # Create engine
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Start a transaction
            with conn.begin():
                # Set search path
                conn.execute(text("SET search_path TO rozoom_clients,rozoom_shop,rozoom_schema"))

                # Check if users table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'rozoom_schema'
                        AND table_name = 'users'
                    )
                """))
                users_exists = result.fetchone()[0]

                if not users_exists:
                    logger.error("Users table does not exist in rozoom_schema. Creating it...")
                    # Create users table if it doesn't exist
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS rozoom_schema.users (
                            id SERIAL PRIMARY KEY,
                            email VARCHAR(100) UNIQUE NOT NULL,
                            username VARCHAR(50) UNIQUE NOT NULL,
                            password_hash VARCHAR(255) NOT NULL,
                            first_name VARCHAR(50),
                            last_name VARCHAR(50),
                            is_admin BOOLEAN DEFAULT FALSE,
                            is_active BOOLEAN DEFAULT TRUE,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            last_login TIMESTAMP,
                            reset_token VARCHAR(100),
                            reset_token_expiry TIMESTAMP
                        )
                    """))
                    logger.info("Users table created successfully")

                # Check if projects table exists
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'projects_schema'
                        AND table_name = 'project'
                    )
                """))
                projects_exists = result.fetchone()[0]

                if not projects_exists:
                    logger.info("Projects table does not exist. Creating it...")
                    # Create projects table
                    conn.execute(text("""
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
                        )
                    """))
                    logger.info("Projects table created successfully")

                # Drop existing incorrect foreign key constraint if it exists
                result = conn.execute(text("""
                    SELECT constraint_name FROM information_schema.table_constraints
                    WHERE constraint_type = 'FOREIGN KEY'
                    AND table_schema = 'projects_schema'
                    AND table_name = 'project'
                    AND constraint_name LIKE '%user_id%'
                """))
                existing_constraints = result.fetchall()

                for constraint in existing_constraints:
                    constraint_name = constraint[0]
                    logger.info(f"Dropping existing constraint: {constraint_name}")
                    conn.execute(text(f"ALTER TABLE projects_schema.project DROP CONSTRAINT IF EXISTS {constraint_name}"))

                # Add correct foreign key constraint
                logger.info("Adding correct foreign key constraint for user_id")
                conn.execute(text("""
                    ALTER TABLE projects_schema.project
                    ADD CONSTRAINT fk_project_user_id_correct
                    FOREIGN KEY (user_id) REFERENCES rozoom_schema.users(id)
                """))

                # Verify the constraint was added
                result = conn.execute(text("""
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
                        AND kcu.column_name = 'user_id'
                """))

                constraint_info = result.fetchone()
                if constraint_info:
                    logger.info(f"✅ Foreign key constraint verified: {constraint_info[0]}")
                    logger.info(f"   References: {constraint_info[4]}.{constraint_info[5]}.{constraint_info[6]}")
                else:
                    logger.error("❌ Foreign key constraint was not created properly")

                logger.info("✅ Database foreign key fix completed successfully!")

    except SQLAlchemyError as e:
        logger.error(f"Database error during migration: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during migration: {e}")
        return False

    return True

if __name__ == "__main__":
    logger.info("Starting database foreign key fix...")
    success = fix_foreign_keys()
    if success:
        logger.info("✅ Migration completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Migration failed!")
        sys.exit(1)
