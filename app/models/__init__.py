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
from .user import User

# Import canonical modules so they are available when importing app.models
from . import product
from . import order
from . import coupon
from . import shop
from . import user
from . import project

__all__ = ['Client', 'User', 'db', 'product', 'order', 'coupon', 'shop', 'user', 'project']
