"""
Verification script to test if the search_path includes the projects_schema.
This helps diagnose SQLAlchemy relationship issues in production.
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

def verify_search_path():
    """Verify that the search_path includes all required schemas."""
    try:
        # Get schema names from environment
        base_schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
        client_schema = os.environ.get('POSTGRES_SCHEMA_CLIENTS')
        shop_schema = os.environ.get('POSTGRES_SCHEMA_SHOP')
        projects_schema = os.environ.get('POSTGRES_SCHEMA_PROJECTS', 'projects_schema')
        
        logger.info(f"Expected schemas - base: {base_schema}, client: {client_schema}, shop: {shop_schema}, projects: {projects_schema}")
        
        # Get database URI
        db_uri = get_postgres_uri()
        logger.info(f"Connecting to database: {db_uri[:50]}...")
        
        # Create engine
        engine = create_engine(db_uri)
        
        with engine.connect() as connection:
            # Check current search_path
            search_path_result = connection.execute(text("SHOW search_path")).fetchone()
            current_search_path = search_path_result[0] if search_path_result else "unknown"
            logger.info(f"Current search_path: {current_search_path}")
            
            # Check if projects_schema is in the search_path
            if projects_schema and projects_schema in current_search_path:
                logger.info(f"✅ projects_schema '{projects_schema}' is included in search_path")
            else:
                logger.warning(f"❌ projects_schema '{projects_schema}' is NOT in the search_path")
            
            # List available schemas
            schemas_result = connection.execute(
                text("SELECT schema_name FROM information_schema.schemata")
            ).fetchall()
            schema_names = [row[0] for row in schemas_result]
            logger.info(f"Available schemas in database: {schema_names}")
            
            # Verify that the required schemas exist
            required_schemas = [schema for schema in [base_schema, client_schema, shop_schema, projects_schema] if schema]
            for schema in required_schemas:
                if schema in schema_names:
                    logger.info(f"✅ Required schema '{schema}' exists in the database")
                else:
                    logger.warning(f"❌ Required schema '{schema}' DOES NOT exist in the database")
            
            # Check tables in projects_schema
            if projects_schema and projects_schema in schema_names:
                tables_result = connection.execute(
                    text(f"SELECT table_name FROM information_schema.tables WHERE table_schema = '{projects_schema}'")
                ).fetchall()
                table_names = [row[0] for row in tables_result]
                logger.info(f"Tables in {projects_schema} schema: {table_names}")
                
                # Check specifically for project and project_stage tables
                if 'project' in table_names:
                    logger.info(f"✅ project table exists in {projects_schema}")
                else:
                    logger.warning(f"❌ project table DOES NOT exist in {projects_schema}")
                
                if 'project_stage' in table_names:
                    logger.info(f"✅ project_stage table exists in {projects_schema}")
                else:
                    logger.warning(f"❌ project_stage table DOES NOT exist in {projects_schema}")
                
                # Check foreign key relationship
                if 'project' in table_names and 'project_stage' in table_names:
                    fk_query = text(f"""
                        SELECT ccu.column_name AS fk_column, 
                               tc.constraint_name AS constraint_name
                        FROM information_schema.table_constraints AS tc 
                        JOIN information_schema.constraint_column_usage AS ccu
                          ON ccu.constraint_name = tc.constraint_name
                        WHERE tc.constraint_type = 'FOREIGN KEY' 
                          AND tc.table_schema = '{projects_schema}'
                          AND tc.table_name = 'project_stage'
                    """)
                    fk_result = connection.execute(fk_query).fetchall()
                    if fk_result:
                        for row in fk_result:
                            logger.info(f"✅ Foreign key found: {row[0]} with constraint {row[1]}")
                    else:
                        logger.warning("❌ No foreign key relationship found between project_stage and project")
            
            return True
    except Exception as e:
        logger.error(f"Error verifying search_path: {str(e)}")
        return False

if __name__ == "__main__":
    if verify_search_path():
        logger.info("Search path verification completed")
    else:
        logger.error("Search path verification failed")
        sys.exit(1)
