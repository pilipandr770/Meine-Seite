"""
SQLAlchemy compatibility layer to handle differences between 1.4 and 2.0
This module provides functions and helpers to ensure code works with both versions
"""

import sys
import importlib.util
import logging

logger = logging.getLogger(__name__)

def get_sqlalchemy_version():
    """Get the major and minor version of SQLAlchemy"""
    try:
        import sqlalchemy
        version_str = sqlalchemy.__version__
        parts = version_str.split('.')
        return int(parts[0]), int(parts[1])
    except (ImportError, ValueError, IndexError) as e:
        logger.error(f"Error determining SQLAlchemy version: {e}")
        return None, None

def is_sqlalchemy_1():
    """Check if we're using SQLAlchemy 1.x"""
    major, _ = get_sqlalchemy_version()
    return major == 1

def is_sqlalchemy_2():
    """Check if we're using SQLAlchemy 2.x"""
    major, _ = get_sqlalchemy_version()
    return major == 2

def get_text_clause():
    """Get the appropriate text clause based on SQLAlchemy version"""
    major, _ = get_sqlalchemy_version()
    
    if major == 1:
        # In SQLAlchemy 1.4, text is imported directly
        from sqlalchemy import text
        return text
    else:
        # In SQLAlchemy 2.0+, text is typically on the db object
        from sqlalchemy import text
        return text

def execute_sql(db_session, sql, params=None, commit=False):
    """Execute SQL in a version-compatible way"""
    major, _ = get_sqlalchemy_version()
    text = get_text_clause()
    
    if params is None:
        params = {}
    
    try:
        if major == 1:
            # SQLAlchemy 1.4 style
            result = db_session.execute(text(sql), params)
            if commit:
                db_session.commit()
            return result
        else:
            # SQLAlchemy 2.0 style
            result = db_session.execute(text(sql), params)
            if commit:
                db_session.commit()
            return result
    except Exception as e:
        if commit:
            db_session.rollback()
        logger.error(f"SQL execution error: {e}")
        raise
