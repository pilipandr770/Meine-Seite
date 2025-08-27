#!/usr/bin/env python
"""
Run script for the application.
Use this script to run from the project root directory.
"""

import os
import sys

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

# Create the app instance for Gunicorn to import
from app.app import create_app
app = create_app()

# Run the app if executed directly
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=os.environ.get("FLASK_ENV") == "development")
