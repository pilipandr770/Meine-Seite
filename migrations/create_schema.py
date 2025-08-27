"""
Скрипт для создания схемы в PostgreSQL базе данных
и миграции таблиц из SQLite в PostgreSQL
"""
import os
import sys
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import json

# Добавляем корневую директорию проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Импорт моделей для создания таблиц
from app.models.client import Client, db
from app.models.task import Task

def create_schema_if_not_exists(pg_uri, schema_name):
    """Создаем схему в PostgreSQL базе данных, если она не существует"""
    try:
        conn = psycopg2.connect(pg_uri)
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Проверяем существует ли схема
        cursor.execute(f"SELECT EXISTS(SELECT 1 FROM pg_namespace WHERE nspname = '{schema_name}');")
        schema_exists = cursor.fetchone()[0]
        
        if not schema_exists:
            print(f"Создание схемы {schema_name}...")
            cursor.execute(f"CREATE SCHEMA {schema_name};")
            print(f"Схема {schema_name} успешно создана.")
        else:
            print(f"Схема {schema_name} уже существует.")
            
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Ошибка при создании схемы: {e}")
        raise

def create_tables_in_postgres(pg_uri, schema_name):
    """Создаем таблицы в PostgreSQL"""
    from app.app import create_app
    from sqlalchemy import text
    
    # Устанавливаем переменную окружения для использования PostgreSQL
    os.environ["DATABASE_URI"] = pg_uri
    
    # Создаем приложение Flask с настроенной базой данных
    app = create_app()
    
    with app.app_context():
        # Создаем схему если она не существует
        try:
            db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}"))
            db.session.commit()
            print(f"Схема {schema_name} создана или уже существует.")
        except Exception as e:
            print(f"Ошибка при создании схемы: {e}")
            db.session.rollback()
            raise
            
        # Создаем все таблицы в PostgreSQL
        try:
            # Устанавливаем search_path для текущей сессии
            db.session.execute(text(f"SET search_path TO {schema_name}, public"))
            db.session.commit()
            
            # Создаем таблицы
            db.create_all()
            print("Таблицы успешно созданы в PostgreSQL.")
        except Exception as e:
            print(f"Ошибка при создании таблиц: {e}")
            db.session.rollback()
            raise

def migrate_data_from_sqlite_to_postgres(sqlite_uri, pg_uri, schema_name):
    """Мигрируем данные из SQLite в PostgreSQL"""
    # Подключение к SQLite
    sqlite_engine = create_engine(sqlite_uri)
    sqlite_session_maker = sessionmaker(bind=sqlite_engine)
    sqlite_session = sqlite_session_maker()
    
    # Получаем данные из SQLite
    try:
        # Загружаем клиентов из SQLite
        clients = []
        for client in sqlite_session.query(Client).all():
            client_data = {
                'id': client.id,
                'name': client.name,
                'email': client.email,
                'phone': client.phone,
                'company': client.company,
                'notes': client.notes,
                'created_at': client.created_at.isoformat() if client.created_at else None,
                'updated_at': client.updated_at.isoformat() if client.updated_at else None
            }
            clients.append(client_data)
        
        # Загружаем задачи из SQLite
        tasks = []
        for task in sqlite_session.query(Task).all():
            task_data = {
                'id': task.id,
                'client_id': task.client_id,
                'title': task.title,
                'description': task.description,
                'status': task.status,
                'priority': task.priority,
                'due_date': task.due_date.isoformat() if task.due_date else None,
                'created_at': task.created_at.isoformat() if task.created_at else None,
                'updated_at': task.updated_at.isoformat() if task.updated_at else None
            }
            tasks.append(task_data)
            
        print(f"Из SQLite загружено {len(clients)} клиентов и {len(tasks)} задач.")
    except Exception as e:
        print(f"Ошибка при загрузке данных из SQLite: {e}")
        sqlite_session.close()
        raise
    finally:
        sqlite_session.close()
    
    # Подключаемся к PostgreSQL
    try:
        # Устанавливаем переменную окружения для использования PostgreSQL
        os.environ["DATABASE_URI"] = pg_uri
        
        # Создаем приложение Flask с настроенной базой данных
        from app.app import create_app
        app = create_app()
        
        with app.app_context():
            # Устанавливаем search_path для текущей сессии
            db.session.execute(text(f"SET search_path TO {schema_name}, public;"))
            db.session.commit()
            
            # Импортируем данные в PostgreSQL
            for client_data in clients:
                # Проверяем, существует ли клиент с таким id
                existing_client = db.session.get(Client, client_data['id'])
                if not existing_client:
                    client = Client(
                        id=client_data['id'],
                        name=client_data['name'],
                        email=client_data['email'],
                        phone=client_data['phone'],
                        company=client_data['company'],
                        notes=client_data['notes']
                    )
                    db.session.add(client)
            
            # Фиксируем изменения в базе данных
            db.session.commit()
            print(f"Клиенты успешно импортированы в PostgreSQL.")
            
            for task_data in tasks:
                # Проверяем, существует ли задача с таким id
                existing_task = db.session.get(Task, task_data['id'])
                if not existing_task:
                    task = Task(
                        id=task_data['id'],
                        client_id=task_data['client_id'],
                        title=task_data['title'],
                        description=task_data['description'],
                        status=task_data['status'],
                        priority=task_data['priority']
                    )
                    # Устанавливаем даты отдельно, если они существуют
                    if task_data['due_date']:
                        from datetime import datetime
                        task.due_date = datetime.fromisoformat(task_data['due_date'])
                    db.session.add(task)
            
            # Фиксируем изменения в базе данных
            db.session.commit()
            print(f"Задачи успешно импортированы в PostgreSQL.")
    except Exception as e:
        print(f"Ошибка при импорте данных в PostgreSQL: {e}")
        db.session.rollback()
        raise

if __name__ == "__main__":
    # Получаем URI базы данных из переменных окружения
    pg_uri = os.environ.get("DATABASE_URI", "postgresql://ittoken_db_user:Xm98VVSZv7cMJkopkdWRkgvZzC7Aly42@dpg-d0visga4d50c73ekmu4g-a.frankfurt-postgres.render.com/ittoken_db")
    sqlite_uri = "sqlite:///../instance/clients.db"
    schema_name = "rozoom_schema"
    
    print(f"Подключение к PostgreSQL: {pg_uri}")
    print(f"Подключение к SQLite: {sqlite_uri}")
    
    # Создаем схему, если она не существует
    create_schema_if_not_exists(pg_uri, schema_name)
    
    # Создаем таблицы в PostgreSQL
    create_tables_in_postgres(pg_uri, schema_name)
    
    # Мигрируем данные из SQLite в PostgreSQL
    migrate_data_from_sqlite_to_postgres(sqlite_uri, pg_uri, schema_name)
    
    print("Миграция успешно завершена!")
