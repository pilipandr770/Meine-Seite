"""
Обновление модели Client для поддержки интеграции с проектами
"""

from app.models.client import db, Client, ClientRequest
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class Project(db.Model):
    """Модель проекта, связана с клиентом и заданием"""
    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    request_id = db.Column(db.Integer, db.ForeignKey('client_request.id'))
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='new')
    start_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    client = db.relationship('Client', backref=db.backref('projects', lazy=True))
    request = db.relationship('ClientRequest', backref=db.backref('projects', lazy=True))
    stages = db.relationship('ProjectStage', backref='project', lazy=True)
    
    def __init__(self, name, client_id=None, request_id=None, description=None):
        self.name = name
        self.client_id = client_id
        self.request_id = request_id
        self.description = description
        self.start_date = datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "request_id": self.request_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "start_date": self.start_date.strftime("%Y-%m-%d %H:%M:%S") if self.start_date else None,
            "deadline": self.deadline.strftime("%Y-%m-%d %H:%M:%S") if self.deadline else None,
            "completed_date": self.completed_date.strftime("%Y-%m-%d %H:%M:%S") if self.completed_date else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
            "stages": [stage.to_dict() for stage in self.stages]
        }

class ProjectStage(db.Model):
    """Модель стадии проекта"""
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.Integer, db.ForeignKey('project.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    order_number = db.Column(db.Integer, nullable=False)
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, project_id, name, order_number, description=None):
        self.project_id = project_id
        self.name = name
        self.description = description
        self.order_number = order_number
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "name": self.name,
            "description": self.description,
            "status": self.status,
            "order_number": self.order_number,
            "start_date": self.start_date.strftime("%Y-%m-%d %H:%M:%S") if self.start_date else None,
            "end_date": self.end_date.strftime("%Y-%m-%d %H:%M:%S") if self.end_date else None,
            "created_at": self.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": self.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        }

class APIKey(db.Model):
    """Модель для хранения API ключей"""
    id = db.Column(db.Integer, primary_key=True)
    service_name = db.Column(db.String(100), nullable=False)
    api_key = db.Column(db.Text, nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, service_name, api_key, description=None):
        self.service_name = service_name
        self.api_key = api_key
        self.description = description
    
    @classmethod
    def get_key(cls, service_name):
        """Получить активный API ключ для указанного сервиса"""
        key = cls.query.filter_by(service_name=service_name, is_active=True).first()
        return key.api_key if key else None

def create_project_from_request(client_request):
    """Создает проект на основе полученного ТЗ"""
    try:
        # Ищем существующего клиента или создаем нового
        client = Client.query.filter_by(email=client_request.contact_info).first() if client_request.contact_info else None
        
        if not client and client_request.contact_info:
            # Создаем клиента
            client = Client(
                name=client_request.contact_info.split('@')[0] if '@' in client_request.contact_info else client_request.contact_info,
                email=client_request.contact_info if '@' in client_request.contact_info else f"{client_request.contact_info}@example.com",
                message=f"Автоматически создан из ТЗ {client_request.project_name}"
            )
            db.session.add(client)
            db.session.flush()  # Получаем ID без коммита
        
        # Создаем проект
        project = Project(
            name=client_request.project_name,
            client_id=client.id if client else None,
            request_id=client_request.id,
            description=client_request.task_description
        )
        db.session.add(project)
        db.session.flush()
        
        # Создаем стадии проекта
        stages = [
            {"name": "Анализ требований", "description": "Детальный разбор ТЗ, уточнение требований", "order": 1},
            {"name": "Проектирование", "description": "Разработка архитектуры и дизайна", "order": 2},
            {"name": "Разработка", "description": "Написание кода, создание функционала", "order": 3},
            {"name": "Тестирование", "description": "Проверка работоспособности, поиск ошибок", "order": 4},
            {"name": "Развертывание", "description": "Публикация проекта", "order": 5}
        ]
        
        for stage in stages:
            db.session.add(ProjectStage(
                project_id=project.id,
                name=stage["name"],
                description=stage["description"],
                order_number=stage["order"]
            ))
        
        # Обновляем статус ТЗ
        client_request.status = "in_progress"
        
        db.session.commit()
        logger.info(f"Создан проект {project.id} на основе ТЗ {client_request.id}")
        
        return project
    except Exception as e:
        db.session.rollback()
        logger.error(f"Ошибка при создании проекта: {e}")
        return None
