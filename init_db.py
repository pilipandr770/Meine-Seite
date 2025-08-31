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
    try:
        from app import create_app
        from app.models.database import db
        from sqlalchemy import text
        from app.models.user import User
        from app.models.shop import Category, Product
        from werkzeug.security import generate_password_hash
    except ImportError as e:
        logger.error(f"Ошибка импорта: {e}")
        return False

    # Создаем приложение
    app = create_app()

    # Получаем схемы из конфига
    base_schema = app.config.get('POSTGRES_SCHEMA', 'rozoom_schema')
    client_schema = app.config.get('POSTGRES_SCHEMA_CLIENTS', 'rozoom_clients')
    
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
            
            # Создаем таблицы
            db.create_all()
            logger.info(f"Таблицы созданы в схемах {base_schema} и {client_schema}")
            
            # Проверка, существует ли уже администратор
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                logger.info("Создание аккаунта администратора...")
                admin = User(
                    username='admin',
                    email='admin@example.com',
                    password_hash=generate_password_hash('Admin123!'),
                    is_admin=True,
                    is_active=True
                )
                db.session.add(admin)
                db.session.commit()
                logger.info("Аккаунт администратора создан!")
            else:
                logger.info("Аккаунт администратора уже существует")
                
            # Создание тестовой категории
            category = Category.query.filter_by(name='Консультации').first()
            if not category:
                logger.info("Создание категории 'Консультации'...")
                category = Category(
                    name='Консультации',
                    slug='konsultacii',
                    description='Профессиональные консультации по различным вопросам'
                )
                db.session.add(category)
                db.session.commit()
                logger.info("Категория создана!")
            else:
                logger.info("Категория 'Консультации' уже существует")
            
            # Создание тестового продукта
            product = Product.query.filter_by(name='Часовая консультация').first()
            if not product and category:
                logger.info("Создание продукта 'Часовая консультация'...")
                product = Product(
                    name='Часовая консультация',
                    slug='chasovaya-konsultaciya',
                    description='Индивидуальная часовая консультация по вашему запросу',
                    short_description='Индивидуальная консультация - 60 минут',
                    price=99.99,
                    stock=10,
                    is_active=True,
                    is_featured=True,
                    category_id=category.id,
                    duration=60,
                    is_virtual=True
                )
                db.session.add(product)
                db.session.commit()
                logger.info("Продукт создан!")
            else:
                logger.info("Продукт 'Часовая консультация' уже существует или категория не найдена")
            
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
