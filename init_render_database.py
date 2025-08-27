#!/usr/bin/env python
"""
Direct PostgreSQL initialization script for Render.com
This script bypasses SQLAlchemy and directly uses psycopg2 to set up the schema
"""

import os
import sys
import logging
import psycopg2
from psycopg2 import sql

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_render_database():
    """Initialize database directly for Render.com"""
    try:
        # Get connection parameters from environment variables
        database_uri = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')
        if not database_uri:
            logger.error("No DATABASE_URI/DATABASE_URL environment variable found")
            return False

        # Always use render_schema for Render deployment
        schema = os.environ.get('POSTGRES_SCHEMA', 'render_schema')
        logger.info(f"Using schema: {schema}")
        
        # Extract connection parameters from DATABASE_URI
        if database_uri.startswith('postgresql://'):
            # Remove 'postgresql://'
            uri = database_uri[13:]
            
            # Extract username and password
            user_pass, host_db = uri.split('@', 1)
            user, password = user_pass.split(':', 1)
            
            # Extract host, port and database name
            host_port, dbname = host_db.split('/', 1)
            
            # Handle query parameters in dbname
            if '?' in dbname:
                dbname = dbname.split('?', 1)[0]
                
            # Extract host and port
            if ':' in host_port:
                host, port = host_port.split(':', 1)
                port = int(port)
            else:
                host = host_port
                port = 5432
                
            logger.info(f"Connecting to PostgreSQL at {host}:{port} database {dbname}")
            
            # Connect to the database
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )
            
            # Set autocommit to avoid transaction issues with schema creation
            conn.autocommit = True
            
            # Create a cursor
            cursor = conn.cursor()
            
            try:
                # Create schema if it doesn't exist
                logger.info(f"Creating schema {schema} if it doesn't exist...")
                cursor.execute(sql.SQL("CREATE SCHEMA IF NOT EXISTS {}").format(sql.Identifier(schema)))
                
                # Set search path to the new schema
                logger.info(f"Setting search path to {schema}...")
                cursor.execute(sql.SQL("SET search_path TO {}").format(sql.Identifier(schema)))
                
                # Check if clients table exists
                logger.info("Checking if tables exist...")
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables 
                        WHERE table_schema = %s AND table_name = 'clients'
                    )
                """, (schema,))
                
                table_exists = cursor.fetchone()[0]
                
                if not table_exists:
                    logger.info("Tables don't exist, creating them...")
                    # Read SQL script
                    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'init-render-db.sql')
                    if os.path.exists(sql_path):
                        with open(sql_path, 'r') as file:
                            sql_script = file.read()
                        
                        # Execute SQL script
                        cursor.execute(sql_script)
                        logger.info("SQL script executed successfully.")
                    else:
                        logger.error(f"SQL file not found at: {sql_path}")
                        return False
                else:
                    logger.info("Tables already exist.")
                
                logger.info("Database initialization complete!")
                return True
                
            finally:
                cursor.close()
                conn.close()
        else:
            logger.error(f"Unsupported database URI scheme: {database_uri[:10]}...")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting direct PostgreSQL initialization for Render.com...")
    success = init_render_database()
    if success:
        logger.info("Database initialization successful.")
        sys.exit(0)
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)
