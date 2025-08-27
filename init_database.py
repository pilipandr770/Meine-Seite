import os
import psycopg2
import logging
from sqlalchemy import create_engine, text

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализирует схему базы данных для Render.com, если необходимо"""
    try:
        # Получаем DATABASE_URL из переменных окружения
        database_url = os.environ.get('DATABASE_URL')
        if not database_url:
            logger.error("DATABASE_URL не задан в переменных окружения")
            return False
            
        # Схема базы данных
        schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
        
        # Создаем движок SQLAlchemy
        engine = create_engine(database_url)
        
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
                
                # Создаем базовые таблицы, если необходимо
                try:
                    # Проверяем, существует ли таблица клиентов
                    result = conn.execute(text(f"SELECT to_regclass('{schema}.client')"))
                    if result.fetchone()[0] is None:
                        logger.info(f"Таблицы не существуют, создаем базовые таблицы...")
                        # Создаем базовые таблицы из SQL-файла только если их нет
                        with open('init-db-new.sql', 'r') as file:
                            sql_script = file.read()
                        
                        # Выполняем скрипт
                        conn.execute(text(sql_script))
                        conn.commit()
                except Exception as e:
                    logger.warning(f"При проверке таблиц произошла ошибка, возможно они уже существуют: {e}")
            
            logger.info(f"Соединение с базой данных успешно установлено, схема {schema} готова к использованию")
            return True
                
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        return False

if __name__ == "__main__":
    logger.info("Проверка соединения с базой данных...")
    success = init_database()
    if success:
        logger.info("Соединение с базой данных успешно установлено!")
    else:
        logger.error("Не удалось подключиться к базе данных.")
