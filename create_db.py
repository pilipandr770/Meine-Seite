"""
Скрипт для создания схемы и таблиц в PostgreSQL
Запустите этот скрипт, чтобы создать схему rozoom_schema и все необходимые таблицы
"""
import os
import psycopg2
import sys

# Добавляем текущую директорию в путь
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

def create_schema_and_tables():
    """Создание схемы и таблиц в PostgreSQL"""
    
    # Получаем URL базы данных из переменных окружения
    database_url = os.environ.get('DATABASE_URI', 'postgresql://ittoken_db_user:Xm98VVSZv7cMJkopkdWRkgvZzC7Aly42@dpg-d0visga4d50c73ekmu4g-a.frankfurt-postgres.render.com/ittoken_db')
    schema_name = 'rozoom_schema'
    
    print(f"Подключение к базе данных: {database_url}")
    print(f"Создание схемы: {schema_name}")
    
    # Создаем соединение с базой данных
    try:
        conn = psycopg2.connect(database_url)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Создаем схему, если она не существует
        print("Создание схемы...")
        cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        
        # 2. Устанавливаем путь поиска для текущей сессии
        cursor.execute(f"SET search_path TO {schema_name}")
        
        # 3. Создаем таблицы
        print("Создание таблиц...")
        
        # Создаем таблицу clients
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS client (
            id SERIAL PRIMARY KEY,
            name VARCHAR(128) NOT NULL,
            email VARCHAR(100) NOT NULL,
            phone VARCHAR(20),
            company VARCHAR(100),
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (email)
        )
        """)
        
        # Создаем таблицу tasks
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS task (
            id SERIAL PRIMARY KEY,
            client_id INTEGER REFERENCES client(id),
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status VARCHAR(50) DEFAULT 'новая',
            priority VARCHAR(50) DEFAULT 'средний',
            due_date TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        # Создаем таблицу для технических заданий (ТЗ)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS client_request (
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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        
        print("Схема и таблицы успешно созданы.")
        
        # Закрываем соединение
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Ошибка: {e}")
        return False
    
    return True

if __name__ == "__main__":
    if create_schema_and_tables():
        print("Скрипт успешно выполнен.")
    else:
        print("Скрипт завершился с ошибками.")
        sys.exit(1)
