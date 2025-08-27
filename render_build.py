# Создаем базовую схему Render.build скрипт
# Запускается автоматически на Render перед запуском приложения

# Импортируем необходимые библиотеки
import os
import sys
import logging
from sqlalchemy import create_engine, text

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_schemas():
    """
    Создаем базовые схемы, необходимые для работы приложения
    """
    # Получаем URL подключения из переменных окружения
    database_url = os.environ.get('DATABASE_URL') or os.environ.get('DATABASE_URI')
    if not database_url:
        logger.error("DATABASE_URL/DATABASE_URI не определен")
        return False

    # Получаем имена схем из переменных окружения
    base_schema = os.environ.get('POSTGRES_SCHEMA', 'rozoom_schema')
    client_schema = os.environ.get('POSTGRES_SCHEMA_CLIENTS', 'rozoom_clients')

    # Нормализуем префикс URL
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    try:
        # Создаем движок для подключения к базе данных
        engine = create_engine(database_url)
        
        # Создаем схемы, если они не существуют
        with engine.connect() as conn:
            conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {base_schema}"))
            logger.info(f"Схема {base_schema} создана или уже существует")
            
            if client_schema and client_schema != base_schema:
                conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {client_schema}"))
                logger.info(f"Схема {client_schema} создана или уже существует")
            
            conn.commit()
        
        return True
    except Exception as e:
        logger.error(f"Ошибка при создании схем: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск скрипта создания схем перед деплоем...")
    if create_schemas():
        logger.info("Схемы успешно созданы")
        sys.exit(0)
    else:
        logger.error("Ошибка создания схем")
        sys.exit(1)
