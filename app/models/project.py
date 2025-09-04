"""
Обновление модели Client для поддержки интеграции с проектами
"""

from app.models.client import db, Client, ClientRequest
import os
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

REQUESTS_SCHEMA = os.getenv('POSTGRES_SCHEMA_CLIENTS')
BASE_SCHEMA = os.getenv('POSTGRES_SCHEMA')  # может быть None, тогда search_path
PROJECTS_SCHEMA = os.getenv('POSTGRES_SCHEMA_PROJECTS') or REQUESTS_SCHEMA or BASE_SCHEMA

# If the configured database isn't PostgreSQL, avoid using schema-qualified
# table names because SQLite doesn't support schemas the same way.
_db_url = os.getenv('DATABASE_URL') or os.getenv('DATABASE_URI') or ''
if not ('postgres' in _db_url or 'postgresql' in _db_url):
    REQUESTS_SCHEMA = None
    BASE_SCHEMA = None
    PROJECTS_SCHEMA = None

# Log schema configuration for debugging
logger.info(f"Project model using schemas: BASE_SCHEMA={BASE_SCHEMA}, REQUESTS_SCHEMA={REQUESTS_SCHEMA}, PROJECTS_SCHEMA={PROJECTS_SCHEMA}")

class Project(db.Model):
    """Модель проекта, связана с клиентом и заявкой (ClientRequest)."""
    __tablename__ = 'project'
    # Keep table args simple for SQLite/dev. Schema placement handled by PG search_path in production.
    __table_args__ = {'extend_existing': True, 'schema': PROJECTS_SCHEMA} if PROJECTS_SCHEMA else {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    client_id = db.Column(db.Integer, db.ForeignKey('clients.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('rozoom_schema.users.id'), nullable=True)
    # Use unqualified FK targets so SQLite metadata doesn't include schema names.
    request_id = db.Column(db.Integer, db.ForeignKey('client_requests.id'), nullable=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(255), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(50), default='new')
    start_date = db.Column(db.DateTime)
    deadline = db.Column(db.DateTime)
    completed_date = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Отношения
    client = db.relationship('Client', backref=db.backref('projects', lazy=True), 
                           primaryjoin="Project.client_id == Client.id",
                           foreign_keys=[client_id])
    request = db.relationship('ClientRequest', backref=db.backref('projects', lazy=True), 
                            primaryjoin="Project.request_id == ClientRequest.id",
                            foreign_keys=[request_id])
    stages = db.relationship(
        'ProjectStage', 
        backref='project', 
        lazy=True,
        primaryjoin="Project.id == ProjectStage.project_id",
        foreign_keys='ProjectStage.project_id'
    )
    
    def __init__(self, name, client_id=None, request_id=None, description=None, slug=None, user_id=None):
        from app.utils.slug import generate_slug
        
        self.name = name
        self.client_id = client_id
        self.user_id = user_id
        self.request_id = request_id
        self.description = description
        self.slug = slug or generate_slug(name)
        self.start_date = datetime.utcnow()
    
    def to_dict(self):
        return {
            "id": self.id,
            "client_id": self.client_id,
            "user_id": self.user_id,
            "request_id": self.request_id,
            "name": self.name,
            "slug": self.slug,
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
    __tablename__ = 'project_stage'
    __table_args__ = {'extend_existing': True, 'schema': PROJECTS_SCHEMA} if PROJECTS_SCHEMA else {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    # Use the same schema for both Project and ProjectStage
    project_id = db.Column(
        db.Integer, 
        db.ForeignKey(f'{PROJECTS_SCHEMA + "." if PROJECTS_SCHEMA else ""}project.id'), 
        nullable=False
    )
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(50), default='pending')
    order_number = db.Column(db.Integer, nullable=False)
    # Оценка требуемых часов для этапа (для поэтапной оплаты)
    estimated_hours = db.Column(db.Integer, default=0)
    # Фактически оплаченные/выставленные часы
    billed_hours = db.Column(db.Integer, default=0)
    # Пометка что этап полностью оплачен (billed_hours >= estimated_hours)
    is_paid = db.Column(db.Boolean, default=False)
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
            "estimated_hours": self.estimated_hours,
            "billed_hours": self.billed_hours,
            "is_paid": self.is_paid,
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
            {"name": "Создание и утверждение ТЗ", "description": "Сбор требований, анализ, составление технического задания", "order": 1},
            {"name": "Планирование и анализ требований", "description": "Детальный анализ требований, оценка сложности, планирование ресурсов", "order": 2},
            {"name": "Дизайн и прототипирование", "description": "Создание дизайна интерфейса, прототипов, UX/UI дизайн", "order": 3},
            {"name": "Фронтенд разработка", "description": "Разработка пользовательского интерфейса, клиентской части", "order": 4},
            {"name": "Бекенд разработка", "description": "Разработка серверной части, API, бизнес-логики", "order": 5},
            {"name": "Верстка", "description": "HTML/CSS верстка, адаптивный дизайн, кроссбраузерность", "order": 6},
            {"name": "Интеграция", "description": "Интеграция фронтенда и бекенда, настройка API", "order": 7},
            {"name": "Тестировка", "description": "Модульное тестирование, интеграционное тестирование, QA", "order": 8},
            {"name": "Доработка", "description": "Исправление ошибок, оптимизация производительности", "order": 9},
            {"name": "Деплой", "description": "Развертывание на сервере, настройка production среды", "order": 10},
            {"name": "Документация", "description": "Создание технической документации, инструкций пользователя", "order": 11},
            {"name": "Поддержка и сопровождение", "description": "Мониторинг, техническая поддержка, обновления", "order": 12}
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

# --- Lightweight runtime migration helpers ---
def _ensure_column_exists(table_name: str, column_name: str, ddl: str):
    """Пытаемся добавить недостающий столбец (idempotent). Работает для PostgreSQL.
    ddl пример: 'ALTER TABLE {table} ADD COLUMN IF NOT EXISTS estimated_hours INTEGER DEFAULT 0'
    """
    try:
        engine = db.get_engine()
        with engine.connect() as conn:
            conn.execute(db.text(ddl.format(table=table_name)))
    except Exception as ex:
        logger.debug(f"Skip column ensure {table_name}.{column_name}: {ex}")

try:
    # Добавляем столбец estimated_hours если его нет
    tbl = f"{PROJECTS_SCHEMA + '.' if PROJECTS_SCHEMA else ''}project_stage"
    _ensure_column_exists(tbl, 'estimated_hours', f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS estimated_hours INTEGER DEFAULT 0")
    _ensure_column_exists(tbl, 'billed_hours', f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS billed_hours INTEGER DEFAULT 0")
    _ensure_column_exists(tbl, 'is_paid', f"ALTER TABLE {tbl} ADD COLUMN IF NOT EXISTS is_paid BOOLEAN DEFAULT FALSE")
except Exception as _e:
    logger.debug(f"Runtime migration for estimated_hours failed: {_e}")
