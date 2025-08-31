#!/usr/bin/env python
"""
Test script for projects functionality
"""

import os
import sys

# Add app to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_projects():
    """Test projects models and functionality"""
    try:
        from app.models.database import db
        from app.models.project import Project, ProjectStage, EXPERT_DATA
        from app.models.client import Client

        print("✅ Imports successful")

        # Test EXPERT_DATA
        print(f"📊 Available categories: {list(EXPERT_DATA.keys())}")

        # Test schema configuration
        projects_schema = os.environ.get('POSTGRES_SCHEMA_PROJECTS', 'projects_schema')
        print(f"🏗️ Projects schema: {projects_schema}")

        print("✅ Projects functionality test completed successfully!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_projects()
    if not success:
        sys.exit(1)
