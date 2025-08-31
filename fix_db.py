#!/usr/bin/env python3
"""
Database migration script to fix foreign key issues in production.
Run this script to ensure all tables are created correctly.
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.models.database import db
from sqlalchemy import text

def fix_database_structure():
    """Fix database structure issues in production"""
    app = create_app()

    with app.app_context():
        try:
            engine = db.get_engine()
            print("🔧 Fixing database structure...")

            with engine.begin() as conn:
                # Set search path to include all schemas
                conn.execute(text('SET search_path TO rozoom_clients,rozoom_shop,projects_schema,rozoom_schema'))

                # Check and create project table if needed
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'projects_schema'
                        AND table_name = 'project'
                    )
                """))
                project_exists = result.fetchone()[0]

                if not project_exists:
                    print("📝 Creating project table...")
                    conn.execute(text("""
                        CREATE TABLE projects_schema.project (
                            id SERIAL PRIMARY KEY,
                            client_id INTEGER,
                            user_id INTEGER,
                            request_id INTEGER,
                            name VARCHAR(200) NOT NULL,
                            slug VARCHAR(255) UNIQUE NOT NULL,
                            description TEXT,
                            status VARCHAR(50) DEFAULT 'new',
                            start_date TIMESTAMP,
                            deadline TIMESTAMP,
                            completed_date TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ Project table created")
                else:
                    print("✅ Project table already exists")

                # Check and create project_stage table if needed
                result = conn.execute(text("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables
                        WHERE table_schema = 'projects_schema'
                        AND table_name = 'project_stage'
                    )
                """))
                stage_exists = result.fetchone()[0]

                if not stage_exists:
                    print("📝 Creating project_stage table...")
                    conn.execute(text("""
                        CREATE TABLE projects_schema.project_stage (
                            id SERIAL PRIMARY KEY,
                            project_id INTEGER NOT NULL,
                            name VARCHAR(100) NOT NULL,
                            description TEXT,
                            status VARCHAR(50) DEFAULT 'pending',
                            order_number INTEGER NOT NULL,
                            start_date TIMESTAMP,
                            end_date TIMESTAMP,
                            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        )
                    """))
                    print("✅ ProjectStage table created")

                    # Add foreign key constraint after table creation
                    try:
                        conn.execute(text("""
                            ALTER TABLE projects_schema.project_stage
                            ADD CONSTRAINT fk_project_stage_project_id
                            FOREIGN KEY (project_id) REFERENCES projects_schema.project(id)
                        """))
                        print("✅ Foreign key constraint added")
                    except Exception as e:
                        print(f"⚠️  Could not add foreign key constraint: {e}")
                else:
                    print("✅ ProjectStage table already exists")

                print("🎉 Database structure fixed successfully!")

        except Exception as e:
            print(f"❌ Error fixing database structure: {e}")
            return False

    return True

if __name__ == "__main__":
    success = fix_database_structure()
    sys.exit(0 if success else 1)
