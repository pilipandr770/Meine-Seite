#!/usr/bin/env python
# create_tables.py - Скрипт для явного создания таблиц в базе данных

import os
import sys
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger('create_tables')

# Проверяем наличие переменных окружения
database_uri = os.environ.get('DATABASE_URI')
if not database_uri:
    database_uri = os.environ.get('DATABASE_URL')
if not database_uri:
    logger.error('Переменная окружения DATABASE_URI не найдена')
    sys.exit(1)

logger.info(f"Используем DATABASE_URI: {database_uri[:20]}...")

try:
    import pg8000

    # Извлекаем параметры подключения из URI
    if database_uri.startswith('postgresql://'):
        uri = database_uri[13:]
    elif database_uri.startswith('postgres://'):
        uri = database_uri[11:]
    else:
        logger.error(f'Неизвестный формат URI: {database_uri[:10]}...')
        sys.exit(1)
        
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
        
    logger.info(f'Подключение к {host}:{port}, база данных: {dbname}, пользователь: {user}')
    
    # Подключение к базе данных
    conn = pg8000.native.Connection(
        user=user,
        password=password,
        host=host,
        port=port,
        database=dbname
    )
    
    # Создание схемы rozoom_clients
    logger.info('Создание схемы rozoom_clients')
    conn.run('CREATE SCHEMA IF NOT EXISTS rozoom_clients')
    
    # Создание таблицы client_requests
    logger.info('Создание таблицы rozoom_clients.client_requests')
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
    
    # Проверка создания таблицы
    result = conn.run("SELECT EXISTS (SELECT 1 FROM pg_tables WHERE schemaname = 'rozoom_clients' AND tablename = 'client_requests')")
    
    if result[0][0]:
        logger.info('✅ Таблица rozoom_clients.client_requests успешно создана/проверена')
    else:
        logger.error('❌ Таблица rozoom_clients.client_requests не была создана')
        
    # Проверка существования таблицы через SQL
    try:
        conn.run("SELECT * FROM rozoom_clients.client_requests LIMIT 1")
        logger.info('✅ Таблица rozoom_clients.client_requests доступна для чтения')
    except Exception as e:
        logger.error(f'❌ Ошибка при чтении из таблицы: {e}')
    
    # Добавление записи для тестирования
    try:
        conn.run("""
        INSERT INTO rozoom_clients.client_requests 
        (project_type, project_name, task_description, contact_method, contact_info)
        VALUES ('test', 'Тестовый проект', 'Тестовое задание', 'Email', 'test@example.com')
        ON CONFLICT DO NOTHING
        """)
        logger.info('✅ Тестовая запись добавлена или уже существует')
    except Exception as e:
        logger.error(f'❌ Ошибка при добавлении тестовой записи: {e}')
    
    conn.close()
    logger.info('Инициализация базы данных завершена успешно')
    
except Exception as e:
    logger.error(f'Ошибка при инициализации базы данных: {e}')
    sys.exit(1)

print("Таблицы созданы успешно.")
sys.exit(0)
