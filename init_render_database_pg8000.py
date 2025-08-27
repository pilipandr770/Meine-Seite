#!/usr/bin/env python
"""
Alternative PostgreSQL initialization script for Render.com using pg8000 instead of psycopg2
This script avoids the Python 3.13 compatibility issues with psycopg2-binary
"""

import os
import sys
import logging
import time

# Configure logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_render_database():
    """Initialize database directly for Render.com using pg8000"""
    try:
        # Import pg8000 - pure Python PostgreSQL driver
        try:
            import pg8000.native
            logger.info("Successfully imported pg8000")
        except ImportError:
            logger.error("Failed to import pg8000. Installing it...")
            import subprocess
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pg8000"])
            import pg8000.native
            logger.info("Successfully installed and imported pg8000")

        # Get connection parameters from environment variables
        database_uri = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')
        if not database_uri:
            logger.error("No DATABASE_URI/DATABASE_URL environment variable found")
            return False

        # Always use render_schema for Render deployment
        schema = os.environ.get('POSTGRES_SCHEMA', 'render_schema')
        logger.info(f"Using schema: {schema}")
        
        # Extract connection parameters from DATABASE_URI
        if database_uri.startswith('postgresql://') or database_uri.startswith('postgres://'):
            # Remove prefix
            if database_uri.startswith('postgresql://'):
                uri = database_uri[13:]
            else:  # postgres://
                uri = database_uri[11:]
            
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
            
            # Try connecting with retries
            conn = None
            for attempt in range(3):
                try:
                    logger.info(f"Connection attempt {attempt+1}/3...")
                    conn = pg8000.native.Connection(
                        user=user,
                        password=password,
                        host=host,
                        port=port,
                        database=dbname
                    )
                    logger.info("Successfully connected to PostgreSQL")
                    break
                except Exception as e:
                    logger.error(f"Connection attempt {attempt+1} failed: {e}")
                    if attempt < 2:  # If not the last attempt
                        time.sleep(2)  # Wait before retry
                    else:
                        logger.error("All connection attempts failed")
                        return False
            
            try:
                # Create schema if it doesn't exist
                logger.info(f"Creating schema {schema} if it doesn't exist...")
                conn.run(f"CREATE SCHEMA IF NOT EXISTS {schema}")
                
                # Set search path to the new schema
                logger.info(f"Setting search path to {schema}...")
                conn.run(f"SET search_path TO {schema}")
                
                # Check if clients table exists and rozoom_clients schema/table
                logger.info("Checking if tables exist...")
                exists_result = conn.run(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = $1 AND table_name = 'clients')",
                    (schema,)
                )
                table_exists = exists_result[0][0]
                
                # Check if rozoom_clients.client_requests exists
                client_schema = 'rozoom_clients'
                client_requests_result = conn.run(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_schema = $1 AND table_name = 'client_requests')",
                    (client_schema,)
                )
                client_requests_exists = client_requests_result[0][0]
                
                # Create rozoom_clients schema if needed
                if not client_requests_exists:
                    logger.info(f"Creating schema {client_schema} if it doesn't exist...")
                    conn.run(f"CREATE SCHEMA IF NOT EXISTS {client_schema}")
                    
                    logger.info(f"Creating client_requests table in {client_schema} schema...")
                    conn.run(f"""
                        CREATE TABLE IF NOT EXISTS {client_schema}.client_requests (
                            id SERIAL PRIMARY KEY,
                            project_type VARCHAR(100) NOT NULL,
                            project_name VARCHAR(200),
                            task_description TEXT NOT NULL,
                            key_features TEXT,
                            design_preferences TEXT,
                            platform VARCHAR(100),
                            budget VARCHAR(100),
                            timeline VARCHAR(100),
                            integrations TEXT,
                            contact_method VARCHAR(100) NOT NULL,
                            contact_info VARCHAR(200),
                            status VARCHAR(30) DEFAULT 'new',
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            deadline TIMESTAMP,
                            priority INTEGER DEFAULT 1,
                            tech_stack TEXT,
                            acceptance_criteria TEXT,
                            notes TEXT
                        )
                    """)
                    logger.info(f"Successfully created {client_schema}.client_requests table")
                
                if not table_exists:
                    logger.info("Tables don't exist, creating them...")
                    # Read SQL script
                    sql_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'init-render-db.sql')
                    if os.path.exists(sql_path):
                        with open(sql_path, 'r') as file:
                            sql_script = file.read()
                        
                        # Execute SQL script - pg8000 doesn't support executing multiple statements at once
                        # Split script into individual statements
                        statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
                        for statement in statements:
                            conn.run(statement)
                        logger.info("SQL script executed successfully.")
                    else:
                        # Create basic tables directly
                        logger.warning(f"SQL file not found at: {sql_path}, creating basic tables directly")
                        
                        # Create clients table
                        conn.run(f"""
                            CREATE TABLE IF NOT EXISTS {schema}.clients (
                                id SERIAL PRIMARY KEY,
                                name VARCHAR(100) NOT NULL,
                                email VARCHAR(100) UNIQUE,
                                phone VARCHAR(20),
                                status VARCHAR(20),
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        # Create tasks table
                        conn.run(f"""
                            CREATE TABLE IF NOT EXISTS {schema}.tasks (
                                id SERIAL PRIMARY KEY,
                                client_id INTEGER REFERENCES {schema}.clients(id),
                                title VARCHAR(200) NOT NULL,
                                description TEXT,
                                status VARCHAR(20),
                                due_date DATE,
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                            )
                        """)
                        
                        # Create rozoom_clients schema and client_requests table
                        client_schema = 'rozoom_clients'
                        logger.info(f"Creating schema {client_schema} if it doesn't exist...")
                        conn.run(f"CREATE SCHEMA IF NOT EXISTS {client_schema}")
                        
                        logger.info(f"Creating client_requests table in {client_schema} schema...")
                        conn.run(f"""
                            CREATE TABLE IF NOT EXISTS {client_schema}.client_requests (
                                id SERIAL PRIMARY KEY,
                                project_type VARCHAR(100) NOT NULL,
                                project_name VARCHAR(200),
                                task_description TEXT NOT NULL,
                                key_features TEXT,
                                design_preferences TEXT,
                                platform VARCHAR(100),
                                budget VARCHAR(100),
                                timeline VARCHAR(100),
                                integrations TEXT,
                                contact_method VARCHAR(100) NOT NULL,
                                contact_info VARCHAR(200),
                                status VARCHAR(30) DEFAULT 'new',
                                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                                deadline TIMESTAMP,
                                priority INTEGER DEFAULT 1,
                                tech_stack TEXT,
                                acceptance_criteria TEXT,
                                notes TEXT
                            )
                        """)
                        logger.info("Basic tables created successfully")
                else:
                    logger.info("Tables already exist.")
                
                logger.info("Database initialization complete!")
                return True
                
            finally:
                if conn:
                    conn.close()
                    logger.info("Database connection closed.")
        else:
            logger.error(f"Unsupported database URI scheme: {database_uri[:10]}...")
            return False
            
    except Exception as e:
        logger.error(f"Error initializing database: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting PostgreSQL initialization using pg8000 for Render.com...")
    success = init_render_database()
    if success:
        logger.info("Database initialization successful.")
        sys.exit(0)
    else:
        logger.error("Database initialization failed.")
        sys.exit(1)
