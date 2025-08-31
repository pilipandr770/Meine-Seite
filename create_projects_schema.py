#!/usr/bin/env python
"""
Script to create the projects schema in PostgreSQL
Run this after deploying to Render.com
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_projects_schema():
    """Create projects schema and tables"""
    try:
        # Import database utilities
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from app.models.database import get_postgres_uri, db
        from app.models.project import Project, ProjectStage
        from sqlalchemy import create_engine, text

        # Get database URI
        database_uri = get_postgres_uri()
        if not database_uri:
            logger.error("No database URI found")
            return False

        # Create engine
        engine = create_engine(database_uri)

        # Set schema name
        projects_schema = os.environ.get('POSTGRES_SCHEMA_PROJECTS', 'projects_schema')

        with engine.begin() as conn:
            # Create schema
            logger.info(f"Creating schema: {projects_schema}")
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {projects_schema}"))

            # Set search path to include the new schema
            conn.execute(text(f"SET search_path TO {projects_schema}, public"))

            # Create tables
            logger.info("Creating tables...")
            Project.__table__.create(bind=engine, checkfirst=True)
            ProjectStage.__table__.create(bind=engine, checkfirst=True)

            logger.info("Projects schema and tables created successfully!")
            return True

    except Exception as e:
        logger.error(f"Error creating projects schema: {e}")
        return False

if __name__ == "__main__":
    success = create_projects_schema()
    if success:
        logger.info("✅ Projects schema setup completed successfully!")
    else:
        logger.error("❌ Failed to create projects schema")
        sys.exit(1)
