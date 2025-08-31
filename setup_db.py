"""
Простой скрипт для создания таблиц в базе данных и администраторского аккаунта
"""
import os
import sys

# Добавляем текущую директорию в sys.path для корректного импорта
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from app import create_app
from app.models.database import db
from app.models.user import User 
from app.models.shop import Category, Product
from werkzeug.security import generate_password_hash
import logging

# Настройка логгера
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Основная функция создания таблиц и администратора"""
    try:
        # Создаем Flask приложение
        app = create_app()
        
        # Создаем контекст приложения
        with app.app_context():
            # Создаем все таблицы
            logger.info("Создание таблиц базы данных...")
            db.create_all()
            logger.info("Таблицы созданы успешно!")
            
            # Проверка наличия админа
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
                logger.info("Администратор создан успешно!")
            else:
                logger.info("Аккаунт администратора уже существует.")
            
            # Создание тестовой категории
            category = Category.query.filter_by(name='Консультации').first()
            if not category:
                logger.info("Создание тестовой категории...")
                category = Category(
                    name='Консультации',
                    slug='konsultacii',
                    description='Профессиональные консультации по различным вопросам'
                )
                db.session.add(category)
                db.session.commit()
                logger.info("Категория создана успешно!")
            else:
                logger.info("Категория 'Консультации' уже существует.")
            
            # Создание тестового продукта
            product = Product.query.filter_by(name='Часовая консультация').first()
            if not product and category:
                logger.info("Создание тестового продукта...")
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
                logger.info("Продукт создан успешно!")
            else:
                logger.info("Продукт 'Часовая консультация' уже существует или категория не найдена.")
            
            logger.info("Инициализация базы данных завершена успешно!")
    except Exception as e:
        logger.error(f"Ошибка при инициализации базы данных: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
