#!/usr/bin/env python
"""
Database reset utility for RoZoom application.

This script:
1. Resets the database connection pool
2. Verifies all schema and column creation
3. Provides diagnostics for common database issues
"""

import os
import sys
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("db_reset")

# Set up path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Import Flask app context
from app import create_app
from app.models.database import db, reconnect_database
from sqlalchemy import text, inspect

def check_table_columns(engine, table_name, schema=None):
    """Check if a table exists and list its columns"""
    try:
        inspector = inspect(engine)
        full_table = f"{schema}.{table_name}" if schema else table_name
        
        if not schema:
            exists = table_name in inspector.get_table_names()
        else:
            exists = table_name in inspector.get_table_names(schema=schema)
        
        if not exists:
            logger.warning(f"Table {full_table} does not exist")
            return False, []
        
        if not schema:
            columns = inspector.get_columns(table_name)
        else:
            columns = inspector.get_columns(table_name, schema=schema)
            
        column_names = [col['name'] for col in columns]
        logger.info(f"Table {full_table} exists with columns: {', '.join(column_names)}")
        return True, column_names
    except Exception as e:
        logger.error(f"Error checking table {table_name}: {e}")
        return False, []

def ensure_order_items_columns():
    """Ensure order_items table has required columns"""
    try:
        app = create_app()
        with app.app_context():
            # Get schema from config
            shop_schema = app.config.get('SHOP_SCHEMA')
            
            # Check if order_items exists and has project_stage_id
            engine = db.get_engine(app)
            exists, columns = check_table_columns(engine, 'order_items', shop_schema)
            
            if not exists:
                logger.error("order_items table does not exist!")
                return False
                
            if 'project_stage_id' not in columns:
                logger.warning("project_stage_id column missing from order_items")
                
                # Add the missing column
                try:
                    table_name = f"{shop_schema}.order_items" if shop_schema else "order_items"
                    with engine.begin() as conn:
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS project_stage_id INTEGER"))
                        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS billed_hours INTEGER DEFAULT 0"))
                    logger.info(f"✅ Added missing columns to {table_name}")
                    return True
                except Exception as e:
                    logger.error(f"Failed to add missing columns: {e}")
                    return False
            else:
                logger.info("✅ project_stage_id column exists in order_items")
                return True
    except Exception as e:
        logger.error(f"Error ensuring order_items columns: {e}")
        return False

def check_db_health():
    """Check database health and connection"""
    app = create_app()
    with app.app_context():
        try:
            # Test connection
            result = db.session.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"Connected to PostgreSQL {version}")
            
            # Check active connections
            result = db.session.execute(text(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()"
            ))
            connections = result.scalar()
            logger.info(f"Active connections to database: {connections}")
            
            # Check for long-running transactions
            result = db.session.execute(text("""
                SELECT pid, now() - xact_start as duration, query
                FROM pg_stat_activity
                WHERE state = 'active' 
                  AND xact_start IS NOT NULL 
                  AND now() - xact_start > '30 seconds'::interval
                ORDER BY duration DESC
                LIMIT 5
            """))
            rows = result.fetchall()
            if rows:
                logger.warning(f"Found {len(rows)} long-running transactions:")
                for row in rows:
                    logger.warning(f"PID: {row[0]}, Duration: {row[1]}, Query: {row[2][:100]}...")
            else:
                logger.info("No long-running transactions found")
                
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False

def reset_db_connections():
    """Reset database connections"""
    app = create_app()
    with app.app_context():
        try:
            success = reconnect_database(app)
            if success:
                logger.info("Successfully reset database connections")
                
                # Verify with a test query
                result = db.session.execute(text("SELECT 1"))
                if result.scalar() == 1:
                    logger.info("Test query successful")
                    return True
                else:
                    logger.warning("Test query returned unexpected result")
                    return False
            else:
                logger.error("Failed to reset database connections")
                return False
        except Exception as e:
            logger.error(f"Error resetting connections: {e}")
            return False

if __name__ == "__main__":
    logger.info("Starting database reset utility")
    
    print("\n==== Database Reset Utility ====")
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("1. Checking database health")
    db_healthy = check_db_health()
    
    print("\n2. Resetting database connections")
    reset_success = reset_db_connections()
    
    print("\n3. Ensuring order_items columns")
    columns_success = ensure_order_items_columns()
    
    print("\n==== Summary ====")
    print(f"Database health check: {'✅ Passed' if db_healthy else '❌ Failed'}")
    print(f"Connection reset: {'✅ Succeeded' if reset_success else '❌ Failed'}")
    print(f"Schema check: {'✅ Passed' if columns_success else '❌ Failed'}")
    
    if not db_healthy or not reset_success or not columns_success:
        print("\n⚠️ Some checks failed. Review the logs for more information.")
        sys.exit(1)
    else:
        print("\n✅ All checks passed. Database is healthy and ready.")
        sys.exit(0)
