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
pip freeze | grep pg8000

# Check SQLAlchemy and Flask-SQLAlchemy compatibility
echo "Checking SQLAlchemy compatibility..."
python check_sqlalchemy.py

# Выполнение инициализации базы данных - создание схем и таблиц
echo "Инициализация базы данных - создание схем и таблиц..."
python init_render_database_pg8000.py

# Явно создаем таблицу client_requests в схеме rozoom_clients
echo "Явное создание таблицы client_requests..."
python -c "
import os
import pg8000
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('init_tables')

database_uri = os.environ.get('DATABASE_URI')
if not database_uri:
    database_uri = os.environ.get('DATABASE_URL')

if not database_uri:
    logger.error('DATABASE_URI не найден')
    exit(1)

# Извлекаем параметры подключения из URI
if database_uri.startswith('postgresql://'):
    uri = database_uri[13:]
elif database_uri.startswith('postgres://'):
    uri = database_uri[11:]
else:
    logger.error(f'Неизвестный формат URI: {database_uri[:10]}...')
    exit(1)

user_pass, host_db = uri.split('@', 1)
user, password = user_pass.split(':', 1)

host_port, dbname = host_db.split('/', 1)
if '?' in dbname:
    dbname = dbname.split('?', 1)[0]

if ':' in host_port:
    host, port = host_port.split(':', 1)
    port = int(port)
else:
    host = host_port
    port = 5432

try:
    # Подключение к БД
    logger.info(f'Подключение к {host}:{port} database {dbname}')
    conn = pg8000.native.Connection(
        user=user,
        password=password,
        host=host,
        port=port,
        database=dbname
    )
    
    # Создаем схему rozoom_clients если не существует
    logger.info('Создание схемы rozoom_clients')
    conn.run('CREATE SCHEMA IF NOT EXISTS rozoom_clients')
    
    # Создаем таблицу client_requests
    logger.info('Создание таблицы client_requests')
    conn.run('''
    CREATE TABLE IF NOT EXISTS rozoom_clients.client_requests (
        id SERIAL PRIMARY KEY,
        project_type VARCHAR(100) NOT NULL,
        project_name VARCHAR(200),
        task_description TEXT NOT NULL,
        key_features TEXT,
        design_preferences TEXT,
        platform VARCHAR(100),
        budget VARCHAR(100),
        timeline VARCHAR(100),
        integrations TEXT,
        contact_method VARCHAR(100) NOT NULL,
        contact_info VARCHAR(200),
        status VARCHAR(30) DEFAULT 'new',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        deadline TIMESTAMP,
        priority INTEGER DEFAULT 1,
        tech_stack TEXT,
        acceptance_criteria TEXT,
        notes TEXT
    )
    ''')
    
    logger.info('Таблица создана успешно')
    conn.close()
except Exception as e:
    logger.error(f'Ошибка при создании таблицы: {e}')
    exit(1)
"
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
