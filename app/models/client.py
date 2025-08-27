import os
from app.models.database import db

# Модель для збереження контактів клієнтів
class Client(db.Model):
    __tablename__ = 'clients'
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    message = db.Column(db.Text, nullable=True)

    def __init__(self, name, email, message):
        self.name = name
        self.email = email
        self.message = message

    def to_dict(self):
        return {"id": self.id, "name": self.name, "email": self.email, "message": self.message}

# Модель для збереження технічних завдань (ТЗ)
class ClientRequest(db.Model):
    base_table_name = 'client_requests'
    _extra_schema = os.getenv('POSTGRES_SCHEMA_CLIENTS')
    __tablename__ = base_table_name
    if _extra_schema:
        __table_args__ = {'schema': _extra_schema}
    id = db.Column(db.Integer, primary_key=True)
    project_type = db.Column(db.String(100), nullable=False)  # Тип проєкту (web-dev, chatbots і т.д.)
    project_name = db.Column(db.String(200), nullable=True)  # Назва проекту
    task_description = db.Column(db.Text, nullable=False)  # Опис технічного завдання
    key_features = db.Column(db.Text, nullable=True)  # Ключові функції
    design_preferences = db.Column(db.Text, nullable=True)  # Переваги дизайну
    platform = db.Column(db.String(100), nullable=True)  # Платформа
    budget = db.Column(db.String(100), nullable=True)  # Бюджет
    timeline = db.Column(db.String(100), nullable=True)  # Термін
    integrations = db.Column(db.Text, nullable=True)  # Інтеграції
    contact_method = db.Column(db.String(100), nullable=False)  # Метод зв'язку (Email, Telegram)
    contact_info = db.Column(db.String(200), nullable=True)  # Контактні дані (якщо не анонімно)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # Дата створення заявки

    def __init__(self, project_type, task_description, contact_method, contact_info):
        self.project_type = project_type
        self.task_description = task_description
        self.contact_method = contact_method
        self.contact_info = contact_info

    def to_dict(self):
        return {
            "id": self.id,
            "project_type": self.project_type,
            "project_name": self.project_name,
            "task_description": self.task_description,
            "key_features": self.key_features,
            "design_preferences": self.design_preferences,
            "platform": self.platform,
            "budget": self.budget,
            "timeline": self.timeline,
            "integrations": self.integrations,
            "contact_method": self.contact_method,
            "contact_info": self.contact_info if self.contact_method != "Анонімно" else "Немає",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
