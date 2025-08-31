# routes/main.py

from flask import Blueprint, render_template, request, redirect, url_for, session
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    # Default language switched to German ('de')
    lang = session.get("lang", "de")
    default_titles = {"de": "Startseite", "uk": "Головна", "en": "Home"}
    return render_template('index.html', title=default_titles.get(lang, "Startseite"), lang=lang)


@main_bp.route('/index')
def index():
    """Alias endpoint so url_for('main.index') works across the codebase."""
    return home()

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring database connectivity."""
    try:
        from app.models.database import db
        from sqlalchemy import text

        # Test database connection
        with db.engine.connect() as conn:
            conn.execute(text("SELECT 1"))
            db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "database": db_status,
        "timestamp": "2025-08-31"
    }, 200 if db_status == "healthy" else 500
