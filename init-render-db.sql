-- Создание новой схемы специально для Render
CREATE SCHEMA IF NOT EXISTS render_schema;

-- Переключаемся на эту схему
SET search_path TO render_schema;

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS render_schema.clients (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(50),
    company VARCHAR(100),
    message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заявок от клиентов
CREATE TABLE IF NOT EXISTS render_schema.client_requests (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES render_schema.clients(id),
    project_type VARCHAR(100),
    project_name VARCHAR(200),
    task_description TEXT,
    key_features TEXT,
    design_preferences TEXT,
    platform VARCHAR(100),
    budget VARCHAR(100),
    timeline VARCHAR(100),
    integrations TEXT,
    contact_method VARCHAR(50),
    contact_info VARCHAR(100),
    status VARCHAR(50) DEFAULT 'new',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица проектов
CREATE TABLE IF NOT EXISTS render_schema.projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'new',
    client_id INTEGER REFERENCES render_schema.clients(id),
    request_id INTEGER REFERENCES render_schema.client_requests(id),
    start_date TIMESTAMP,
    deadline TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица стадий проекта
CREATE TABLE IF NOT EXISTS render_schema.project_stages (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES render_schema.projects(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    order_number INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица задач
CREATE TABLE IF NOT EXISTS render_schema.tasks (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES render_schema.projects(id),
    stage_id INTEGER REFERENCES render_schema.project_stages(id),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'todo',
    priority VARCHAR(50) DEFAULT 'medium',
    due_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица API ключей
CREATE TABLE IF NOT EXISTS render_schema.api_keys (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL UNIQUE,
    api_key VARCHAR(500) NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Добавление тестовых API ключей
INSERT INTO render_schema.api_keys (service_name, api_key, description) 
VALUES 
    ('telegram_bot_token', '7572478553:AAEJxJ9Il80zrHAjcD7ZcQnht3EP-sHYrjs', 'Token для Telegram бота'),
    ('telegram_chat_id', '7444992311', 'ID чата для уведомлений в Telegram'),
    ('openai_api_key', 'sk-your-openai-key', 'API ключ для OpenAI')
ON CONFLICT (service_name) DO NOTHING;

-- Индексы
CREATE INDEX IF NOT EXISTS idx_clients_email ON render_schema.clients (email);
CREATE INDEX IF NOT EXISTS idx_client_requests_status ON render_schema.client_requests (status);
CREATE INDEX IF NOT EXISTS idx_projects_client ON render_schema.projects (client_id);
CREATE INDEX IF NOT EXISTS idx_projects_status ON render_schema.projects (status);
CREATE INDEX IF NOT EXISTS idx_project_stages_project ON render_schema.project_stages (project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON render_schema.tasks (project_id);
CREATE INDEX IF NOT EXISTS idx_tasks_stage ON render_schema.tasks (stage_id);
