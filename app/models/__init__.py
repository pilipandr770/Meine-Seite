"""
Инициализация пакета models для приложения.
Предоставляет классы и функции для работы с базой данных.
"""
try:
    # Попытка импорта из нового модуля database
    from app.models.database import db, init_db
except ImportError:
    # Запасной вариант - берем экземпляр db из модуля client
    from .client import db

from .client import Client
__all__ = ['Client', 'db']
