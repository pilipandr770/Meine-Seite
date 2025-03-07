from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# Модель для збереження контактів клієнтів
class Client(db.Model):
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
    id = db.Column(db.Integer, primary_key=True)
    project_type = db.Column(db.String(100), nullable=False)  # Тип проєкту (web-dev, chatbots і т.д.)
    task_description = db.Column(db.Text, nullable=False)  # Опис технічного завдання
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
            "task_description": self.task_description,
            "contact_method": self.contact_method,
            "contact_info": self.contact_info if self.contact_method != "Анонімно" else "Немає",
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S")
        }
