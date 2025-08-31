#!/usr/bin/env python
"""
Database connection test script for Render.com deployment.
This script tests the database connection and configuration.
"""

import os
import sys
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

def test_database_connection():
    """Test database connection and configuration."""
    try:
        from app.models.database import get_postgres_uri, create_db_engine
        from config import Config

        logger.info("Testing database connection...")

        # Get configuration
        config = Config()
        database_uri = config.SQLALCHEMY_DATABASE_URI
        engine_options = config.SQLALCHEMY_ENGINE_OPTIONS

        logger.info(f"Database URI: {database_uri[:50]}...")
        logger.info(f"Engine options: {engine_options}")

        # Test connection
        engine = create_db_engine(database_uri, engine_options=engine_options)

        with engine.connect() as conn:
            result = conn.execute("SELECT version()")
            version = result.fetchone()[0]
            logger.info(f"✅ Database connection successful: {version[:50]}...")

            # Test search_path
            result = conn.execute("SHOW search_path")
            search_path = result.fetchone()[0]
            logger.info(f"✅ Search path: {search_path}")

            # Test schema existence
            result = conn.execute("SELECT schema_name FROM information_schema.schemata WHERE schema_name IN ('rozoom_schema', 'rozoom_clients', 'rozoom_shop')")
            schemas = [row[0] for row in result.fetchall()]
            logger.info(f"✅ Available schemas: {schemas}")

        logger.info("✅ All database tests passed!")
        return True

    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_database_connection()
    sys.exit(0 if success else 1)
