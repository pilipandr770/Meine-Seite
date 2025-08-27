#!/usr/bin/env python
"""
Check and repair SQLAlchemy imports to ensure compatibility
This script runs before the application to verify and fix database connectivity
"""

import os
import sys
import importlib.util
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("sqlalchemy_check")

def check_sqlalchemy():
    """Verify SQLAlchemy installation and version"""
    try:
        import sqlalchemy
        logger.info(f"SQLAlchemy version: {sqlalchemy.__version__}")
        
        # Check if we're using the right version
        version = sqlalchemy.__version__.split('.')
        major, minor = int(version[0]), int(version[1])
        
        if major == 1 and minor == 4:
            logger.info("Using SQLAlchemy 1.4.x series - compatible with Flask-SQLAlchemy 2.5.1")
        elif major == 2 and minor >= 0:
            logger.info("Using SQLAlchemy 2.x.x series - check Flask-SQLAlchemy compatibility")
        
        # Test basic SQLAlchemy functionality
        from sqlalchemy import create_engine, text
        logger.info("Basic SQLAlchemy imports successful")
        
        # Проверка на наличие драйвера pg8000
        try:
            import pg8000
            logger.info(f"pg8000 version: {pg8000.__version__}")
            logger.info("pg8000 available as alternative PostgreSQL driver")
        except ImportError:
            logger.warning("pg8000 not installed, trying to install it...")
            try:
                import subprocess
                subprocess.check_call([sys.executable, "-m", "pip", "install", "pg8000"])
                import pg8000
                logger.info(f"pg8000 successfully installed, version: {pg8000.__version__}")
            except Exception as e2:
                logger.error(f"Failed to install pg8000: {e2}")
        
        return True
        
    except ImportError as e:
        logger.error(f"Failed to import SQLAlchemy: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error with SQLAlchemy: {e}")
        return False

def check_flask_sqlalchemy():
    """Verify Flask-SQLAlchemy installation and version"""
    try:
        import flask_sqlalchemy
        logger.info(f"Flask-SQLAlchemy version: {flask_sqlalchemy.__version__}")
        return True
    except ImportError as e:
        logger.error(f"Failed to import Flask-SQLAlchemy: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error with Flask-SQLAlchemy: {e}")
        return False

def check_psycopg2():
    """Verify psycopg2 installation and look for alternatives if needed"""
    try:
        import psycopg2
        logger.info(f"psycopg2 version: {psycopg2.__version__}")
        return True
    except ImportError as e:
        logger.warning(f"Failed to import psycopg2: {e}")
        logger.info("Using pg8000 as alternative PostgreSQL driver")
        try:
            import pg8000
            logger.info(f"pg8000 version: {pg8000.__version__}")
            return True
        except ImportError:
            logger.error("Neither psycopg2 nor pg8000 is available")
            return False
    except Exception as e:
        logger.error(f"Unexpected error with psycopg2: {e}")
        try:
            import pg8000
            logger.info(f"pg8000 version: {pg8000.__version__} will be used as fallback")
            return True
        except ImportError:
            logger.error("No PostgreSQL drivers available")
            return False

if __name__ == "__main__":
    logger.info("Checking SQLAlchemy and PostgreSQL driver compatibility...")
    
    sqlalchemy_ok = check_sqlalchemy()
    flask_sqlalchemy_ok = check_flask_sqlalchemy()
    psycopg2_ok = check_psycopg2()
    
    if sqlalchemy_ok and flask_sqlalchemy_ok:
        logger.info("SQLAlchemy environment checks passed!")
        if not psycopg2_ok:
            logger.warning("No PostgreSQL driver available, application may not function correctly")
        sys.exit(0)
    else:
        logger.error("SQLAlchemy environment checks failed!")
        sys.exit(1)
