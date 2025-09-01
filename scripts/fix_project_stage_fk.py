"""
Fix for Project-ProjectStage relationship in the database.
This script runs SQL commands to ensure the foreign key relationship is correctly established.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add the parent directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables
load_dotenv()

def get_postgres_uri():
    """Get the PostgreSQL URI from environment variables."""
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI')
    if not database_url:
        host = os.environ.get('DATABASE_HOST', 'localhost')
        port = os.environ.get('DATABASE_PORT', '5432')
        database = os.environ.get('DATABASE_NAME', 'rozoom')
        username = os.environ.get('DATABASE_USERNAME', 'postgres')
        password = os.environ.get('DATABASE_PASSWORD', 'postgres')
        database_url = f'postgresql://{username}:{password}@{host}:{port}/{database}'

    # Normalize the prefix
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url

def fix_project_stage_foreign_key():
    """Fix the foreign key relationship between ProjectStage and Project tables."""
    try:
        # Get schema names from environment
        schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
        projects_schema = os.environ.get('POSTGRES_SCHEMA_PROJECTS', 'projects_schema')
        
        # Get database URI
        db_uri = get_postgres_uri()
        logger.info(f"Connecting to database: {db_uri[:50]}...")
        
        # Create engine
        engine = create_engine(db_uri)
        
        with engine.connect() as connection:
            # Set search path to include both schemas
            search_path = f"{projects_schema},{schema}"
            connection.execute(text(f"SET search_path TO {search_path}"))
            logger.info(f"Set search_path to: {search_path}")
            
            # Check if the foreign key constraint exists
            check_fk_sql = text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = :schema
                AND table_name = 'project_stage'
                AND constraint_type = 'FOREIGN KEY'
                AND constraint_name LIKE '%project_id%'
            """)
            
            results = connection.execute(check_fk_sql, {'schema': projects_schema}).fetchall()
            
            if results:
                # Drop the existing constraint
                for row in results:
                    constraint_name = row[0]
                    logger.info(f"Dropping existing constraint: {constraint_name}")
                    connection.execute(
                        text(f"ALTER TABLE {projects_schema}.project_stage DROP CONSTRAINT IF EXISTS {constraint_name}")
                    )
            
            # Add the correct foreign key constraint
            logger.info("Adding new foreign key constraint...")
            connection.execute(
                text(f"""
                    ALTER TABLE {projects_schema}.project_stage 
                    ADD CONSTRAINT project_stage_project_id_fkey 
                    FOREIGN KEY (project_id) 
                    REFERENCES {projects_schema}.project(id)
                """)
            )
            
            # In SQLAlchemy >= 1.4, connection.commit() is no longer available
            # The transaction is committed automatically when the context manager exits
            logger.info("Foreign key constraint updated successfully")
            
            # Verify the constraint
            verify_sql = text("""
                SELECT constraint_name
                FROM information_schema.table_constraints
                WHERE table_schema = :schema
                AND table_name = 'project_stage'
                AND constraint_type = 'FOREIGN KEY'
            """)
            
            verify_results = connection.execute(verify_sql, {'schema': projects_schema}).fetchall()
            logger.info(f"Verified constraints: {[row[0] for row in verify_results]}")
            
            return True
    except Exception as e:
        logger.error(f"Error fixing foreign key: {str(e)}")
        return False

if __name__ == "__main__":
    if fix_project_stage_foreign_key():
        logger.info("Database migration completed successfully")
    else:
        logger.error("Database migration failed")
        sys.exit(1)
