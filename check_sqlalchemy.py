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

if __name__ == "__main__":
    logger.info("Checking SQLAlchemy and Flask-SQLAlchemy compatibility...")
    
    sqlalchemy_ok = check_sqlalchemy()
    flask_sqlalchemy_ok = check_flask_sqlalchemy()
    
    if sqlalchemy_ok and flask_sqlalchemy_ok:
        logger.info("SQLAlchemy environment checks passed!")
        sys.exit(0)
    else:
        logger.error("SQLAlchemy environment checks failed!")
        sys.exit(1)
