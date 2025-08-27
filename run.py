#!/usr/bin/env python
"""
Run script for the application.
Use this script to run from the project root directory.
This is the entry point for Gunicorn in production.
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

# Add app directory to path
app_dir = os.path.join(current_dir, 'app')
if app_dir not in sys.path:
    sys.path.append(app_dir)

logger.info("Initializing Flask application...")

# Create the app instance for Gunicorn to import
from app.app import create_app
app = create_app()
logger.info(f"Flask application initialized with config: {app.config['ENVIRONMENT'] if 'ENVIRONMENT' in app.config else 'default'}")

# Run the app if executed directly
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV") == "development"
    logger.info(f"Running Flask app on port {port} with debug={debug}")
    app.run(host="0.0.0.0", port=port, debug=debug)
