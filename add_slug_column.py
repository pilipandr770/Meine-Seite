#!/usr/bin/env python3
"""
Script to add slug column to projects_schema.project table
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Simple app creation without routes
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import Config

def create_simple_app():
    """Create a simple Flask app for database operations"""
    app = Flask(__name__)
    app.config.from_object(Config)
    return app

def add_slug_column():
    """Add slug column to project table"""
    app = create_simple_app()
    db = SQLAlchemy(app)

    with app.app_context():
        try:
            # Check if column already exists
            from sqlalchemy import text
            result = db.session.execute(text("""
                SELECT column_name
                FROM information_schema.columns
                WHERE table_schema = 'projects_schema'
                AND table_name = 'project'
                AND column_name = 'slug'
            """))

            if result.fetchone():
                print("✅ Slug column already exists in projects_schema.project table")
                return

            # Add slug column
            print("📝 Adding slug column to projects_schema.project table...")
            db.session.execute(text("""
                ALTER TABLE projects_schema.project
                ADD COLUMN slug VARCHAR(255) UNIQUE NOT NULL DEFAULT 'temp-slug'
            """))

            # Generate slugs for existing projects
            print("🔄 Generating slugs for existing projects...")
            projects = db.session.execute(text("""
                SELECT id, name FROM projects_schema.project
            """)).fetchall()

            # Import slug generator
            from app.utils.slug import generate_slug

            for project in projects:
                base_slug = generate_slug(project.name)
                slug = base_slug
                counter = 1

                # Check for uniqueness
                while True:
                    existing = db.session.execute(text("""
                        SELECT id FROM projects_schema.project
                        WHERE slug = :slug AND id != :project_id
                    """), {'slug': slug, 'project_id': project.id}).fetchone()

                    if not existing:
                        break
                    slug = f"{base_slug}-{counter}"
                    counter += 1

                # Update the project with the generated slug
                db.session.execute(text("""
                    UPDATE projects_schema.project
                    SET slug = :slug
                    WHERE id = :project_id
                """), {'slug': slug, 'project_id': project.id})

                print(f"✅ Updated project '{project.name}' with slug '{slug}'")

            # Remove default constraint
            db.session.execute(text("""
                ALTER TABLE projects_schema.project
                ALTER COLUMN slug DROP DEFAULT
            """))

            db.session.commit()
            print("✅ Successfully added slug column and generated slugs for all projects!")

        except Exception as e:
            db.session.rollback()
            print(f"❌ Error: {e}")
            raise

if __name__ == "__main__":
    add_slug_column()
