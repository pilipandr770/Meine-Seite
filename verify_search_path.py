#!/usr/bin/env python3
"""
Script to verify that the search_path includes projects_schema and ProjectStage can be created.
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

# Add the app directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.models.database import get_postgres_uri

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def verify_search_path():
    """Verify that search_path includes projects_schema and tables can be created."""

    try:
        # Get database URI
        database_url = get_postgres_uri()
        logger.info(f"Connecting to database: {database_url.replace(database_url.split('@')[0].split(':')[1], '***')}")

        # Create engine
        engine = create_engine(database_url)

        with engine.connect() as conn:
            # Check current search_path
            result = conn.execute(text("SHOW search_path"))
            current_search_path = result.fetchone()[0]
            logger.info(f"Current search_path: {current_search_path}")

            # Set search_path to include projects_schema
            conn.execute(text("SET search_path TO rozoom_clients,rozoom_shop,projects_schema,rozoom_schema"))
            logger.info("Set search_path to include projects_schema")

            # Verify we can access the project table
            try:
                result = conn.execute(text("SELECT COUNT(*) FROM projects_schema.project"))
                project_count = result.fetchone()[0]
                logger.info(f"✅ Can access projects_schema.project table: {project_count} records")
            except Exception as e:
                logger.error(f"❌ Cannot access projects_schema.project table: {e}")
                return False

            # Try to create ProjectStage table
            try:
                conn.execute(text("""
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
                    )
                """))
                logger.info("✅ ProjectStage table created successfully")
            except Exception as e:
                logger.error(f"❌ Failed to create ProjectStage table: {e}")
                return False

            # Try to add foreign key constraint
            try:
                # Drop existing constraint if it exists
                conn.execute(text("""
                    ALTER TABLE projects_schema.project_stage
                    DROP CONSTRAINT IF EXISTS fk_project_stage_project_id_correct
                """))

                # Add the constraint
                conn.execute(text("""
                    ALTER TABLE projects_schema.project_stage
                    ADD CONSTRAINT fk_project_stage_project_id_correct
                    FOREIGN KEY (project_id) REFERENCES projects_schema.project(id)
                """))
                logger.info("✅ Foreign key constraint added successfully")
            except Exception as e:
                logger.error(f"❌ Failed to add foreign key constraint: {e}")
                return False

            logger.info("✅ All verifications passed!")

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return False

    return True

if __name__ == "__main__":
    logger.info("Verifying search_path and ProjectStage creation...")
    success = verify_search_path()
    if success:
        logger.info("✅ Verification completed successfully!")
        sys.exit(0)
    else:
        logger.error("❌ Verification failed!")
        sys.exit(1)
