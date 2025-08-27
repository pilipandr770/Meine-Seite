#!/usr/bin/env python
import os
import sys
import logging
from sqlalchemy import create_engine, text
import time

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the current directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

def init_database():
    """Инициализирует схему базы данных для Render.com, если необходимо"""
    try:
        # Получаем DATABASE_URI из переменных окружения (проверяем обе переменные)
        database_uri = os.environ.get('DATABASE_URI') or os.environ.get('DATABASE_URL')
        if not database_uri:
            logger.error("DATABASE_URI/DATABASE_URL не заданы в переменных окружения")
            return False
            
        # Схема базы данных
        schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
        logger.info(f"Инициализация базы данных с URI: {database_uri[:20]}*** и схемой: {schema}")
        
        # Добавляем повторные попытки для Render.com, поскольку база данных может стартовать не сразу
        max_retries = 5
        retry_count = 0
        retry_delay = 3  # секунды

        while retry_count < max_retries:
            try:
                # Создаем движок SQLAlchemy
                engine = create_engine(database_uri)
                
                # Проверяем соединение и создаем схему, если необходимо
                with engine.connect() as conn:
                    # Проверяем существование схемы
                    result = conn.execute(text("SELECT schema_name FROM information_schema.schemata WHERE schema_name = :schema"), 
                                        {"schema": schema})
                    schema_exists = result.fetchone() is not None
                    
                    if not schema_exists:
                        logger.info(f"Схема {schema} не существует, создаем...")
                        # Создаем схему, если она не существует
                        conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                        conn.commit()
                    
                    # Установка поискового пути по умолчанию для этого соединения
                    conn.execute(text(f"SET search_path TO {schema}"))
                    conn.commit()
                    
                    # Создаем базовые таблицы, если необходимо
                    try:
                        # Проверяем, существует ли таблица clients
                        result = conn.execute(text(f"SELECT to_regclass('{schema}.clients')"))
                        if result.fetchone()[0] is None:
                            logger.info(f"Таблицы не существуют, создаем базовые таблицы...")
                            # Создаем базовые таблицы из SQL-файла только если их нет
                            sql_path = os.path.join(current_dir, 'init-db-new.sql')
                            if os.path.exists(sql_path):
                                with open(sql_path, 'r') as file:
                                    sql_script = file.read()
                                
                                # Выполняем скрипт
                                conn.execute(text(sql_script))
                                conn.commit()
                                logger.info("SQL-скрипт успешно выполнен.")
                            else:
                                logger.error(f"SQL файл не найден по пути: {sql_path}")
                        else:
                            logger.info("Таблицы уже существуют, пропускаем создание.")
                    except Exception as e:
                        logger.warning(f"При проверке таблиц произошла ошибка: {e}")
                        conn.rollback()
                
                logger.info(f"Соединение с базой данных успешно установлено, схема {schema} готова к использованию")
                return True
            
            except Exception as e:
                retry_count += 1
                if retry_count < max_retries:
                    logger.warning(f"Попытка {retry_count}/{max_retries} не удалась: {e}. Повторяем через {retry_delay} сек...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Увеличиваем время ожидания между попытками
                else:
                    logger.error(f"Ошибка при инициализации базы данных после {max_retries} попыток: {e}")
                    return False
                
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

# Создаем Flask приложение и выполняем миграцию через него
def init_flask_app():
    """Инициализирует Flask приложение и выполняет миграцию через него"""
    try:
        from app.app import create_app
        from app.models.client import db
        
        app = create_app()
        
        with app.app_context():
            # Создаем схему
            if app.config["SQLALCHEMY_DATABASE_URI"].startswith("postgresql"):
                try:
                    schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
                    db.session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
                    db.session.commit()
                    db.session.execute(text(f"SET search_path TO {schema}"))
                    db.session.commit()
                    logger.info(f"Схема {schema} создана или уже существует.")
                except Exception as e:
                    logger.warning(f"Ошибка при создании схемы: {e}")
                    db.session.rollback()
            
            # Создаем таблицы
            try:
                db.create_all()
                logger.info("Таблицы успешно созданы через SQLAlchemy.")
                return True
            except Exception as e:
                logger.error(f"Ошибка при создании таблиц через SQLAlchemy: {e}")
                return False
    except Exception as e:
        logger.error(f"Ошибка при инициализации Flask приложения: {e}")
        return False

if __name__ == "__main__":
    logger.info("===== Начало инициализации базы данных =====")
    
    # Сначала пробуем через чистый SQL
    success = init_database()
    if success:
        logger.info("Инициализация базы данных через SQL успешно выполнена!")
    else:
        logger.warning("Не удалось инициализировать БД через SQL, пробуем через Flask/SQLAlchemy...")
        
        # Если не получилось через SQL, пробуем через Flask/SQLAlchemy
        success = init_flask_app()
        if success:
            logger.info("Инициализация базы данных через Flask/SQLAlchemy успешно выполнена!")
        else:
            logger.error("Не удалось инициализировать базу данных.")
            sys.exit(1)
    
    logger.info("===== Инициализация базы данных завершена =====")
