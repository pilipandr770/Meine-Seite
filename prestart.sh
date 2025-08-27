#!/bin/bash
# This script is executed by render.com before the application starts

# Set environment variable to indicate we're on Render
export RENDER=true

# Update pip
echo "Updating pip..."
pip install --upgrade pip

# Print Python version and environment info
echo "Python version:"
python -V
echo "Package versions:"
pip freeze | grep SQLAlchemy
pip freeze | grep flask

# Check SQLAlchemy and Flask-SQLAlchemy compatibility
echo "Checking SQLAlchemy compatibility..."
python check_sqlalchemy.py
if [ $? -ne 0 ]; then
  echo "SQLAlchemy check failed, but continuing anyway..."
fi

# Initialize the database using specialized script for Render
echo "Initializing Render-specific database schema..."
python init_render_database.py

if [ $? -eq 0 ]; then
  echo "Direct PostgreSQL database initialization successful!"
else
  echo "Direct database initialization failed, trying alternative methods..."
  
  # Try the SQL approach if psycopg2 fails
  DB_URL=$DATABASE_URI
  if [ -z "$DB_URL" ]; then
    DB_URL=$DATABASE_URL
  fi
  DB_SCHEMA=${POSTGRES_SCHEMA:-render_schema}
  
  echo "Using schema: $DB_SCHEMA"
  
  if [ -f "init-render-db.sql" ]; then
    # Extract credentials from the DB_URL
    DB_USER=$(echo $DB_URL | sed -n 's/.*:\/\/\([^:]*\):.*/\1/p')
    DB_PASS=$(echo $DB_URL | sed -n 's/.*:\/\/[^:]*:\([^@]*\).*/\1/p')
    DB_HOST=$(echo $DB_URL | sed -n 's/.*@\([^:]*\):.*/\1/p')
    DB_PORT=$(echo $DB_URL | sed -n 's/.*:\([0-9]*\)\/.*/\1/p')
    DB_NAME=$(echo $DB_URL | sed -n 's/.*\/\([^?]*\).*/\1/p')
    
    echo "Connecting to PostgreSQL database: $DB_HOST:$DB_PORT/$DB_NAME"
    
    # Use environment variables for credentials to avoid showing them in command line
    export PGPASSWORD=$DB_PASS
    psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f init-render-db.sql
    RESULT=$?
    unset PGPASSWORD
    
    if [ $RESULT -eq 0 ]; then
      echo "Render database schema setup successful!"
    else
      echo "Direct SQL initialization failed, falling back to Python scripts..."
      python init_database_new.py
      if [ $? -ne 0 ]; then
        echo "Database initialization failed! Trying original script..."
        python init_database.py
        if [ $? -ne 0 ]; then
          echo "All database initialization attempts failed!"
          exit 1
        fi
      fi
    fi
  else
    echo "Render SQL file not found, using Python scripts..."
    python init_database_new.py
    if [ $? -ne 0 ]; then
      echo "Database initialization failed! Trying original script..."
      python init_database.py
      if [ $? -ne 0 ]; then
        echo "All database initialization attempts failed!"
        exit 1
      fi
    fi
  fi
fi

# Success message
echo "Pre-start setup completed successfully!"
