#!/bin/bash
# This script is executed by render.com before the application starts

# Update pip
pip install --upgrade pip

# Print Python and SQLAlchemy versions for debugging
python -V
pip freeze | grep SQLAlchemy

# Initialize the database
python init_database.py

# Success message
echo "Pre-start setup completed successfully!"
