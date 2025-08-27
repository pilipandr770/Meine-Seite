#!/usr/bin/env python
"""
Скрипт инициализации базы данных
Создает схемы и необходимые таблицы, если они не существуют
"""

import os
import logging
import sys
import argparse

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Добавляем текущую директорию в sys.path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def init_db():
    """
    Инициализирует базу данных: создает схемы и таблицы
    """
    from app.app import create_app
    from app.models.database import db
    from sqlalchemy import text

    # Создаем приложение
    app = create_app()

    # Получаем схемы из конфига
    base_schema = app.config.get('POSTGRES_SCHEMA', 'rozoom_schema')
    client_schema = app.config.get('CLIENT_REQUESTS_SCHEMA', 'rozoom_clients')
    
    # Создаем схемы и таблицы
    with app.app_context():
        try:
            # Создаем схемы если не существуют
            db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {base_schema}"))
            logger.info(f"Схема {base_schema} создана или уже существует")
            
            if client_schema and client_schema != base_schema:
                db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {client_schema}"))
                logger.info(f"Схема {client_schema} создана или уже существует")
            
            # Коммитим создание схем
            db.session.commit()
            
            # Импортируем модели (это важно делать ПОСЛЕ создания схем)
            from app.models.client import Client, ClientRequest
            from app.models.project import Project, ProjectStage, APIKey
            
            # Создаем таблицы
            db.create_all()
            logger.info(f"Таблицы созданы в схемах {base_schema} и {client_schema}")
            
            return True
        except Exception as e:
            db.session.rollback()
            logger.error(f"Ошибка инициализации базы данных: {e}")
            return False

def main():
    """
    Основная функция для запуска скрипта
    """
    parser = argparse.ArgumentParser(description='Инициализация базы данных')
    parser.add_argument('--force', action='store_true', help='Принудительное создание схем и таблиц')
    args = parser.parse_args()
    
    if args.force:
        logger.info("Запуск принудительной инициализации базы данных")
    else:
        logger.info("Запуск инициализации базы данных")
    
    result = init_db()
    
    if result:
        logger.info("Инициализация базы данных завершена успешно")
    else:
        logger.error("Инициализация базы данных завершилась с ошибками")
        sys.exit(1)

if __name__ == "__main__":
    main()
