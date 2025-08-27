-- Создание схемы для изоляции данных
CREATE SCHEMA IF NOT EXISTS rozoom_schema;

-- Устанавливаем путь поиска по умолчанию
SET search_path TO rozoom_schema;

-- Таблица клиентов
CREATE TABLE IF NOT EXISTS client (
    id SERIAL PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    company VARCHAR(100),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица заданий/ТЗ
CREATE TABLE IF NOT EXISTS client_request (
    id SERIAL PRIMARY KEY,
    project_type VARCHAR(100) NOT NULL,
    project_name VARCHAR(200),
    task_description TEXT NOT NULL,
    key_features TEXT,
    design_preferences TEXT,
    platform VARCHAR(100),
    budget VARCHAR(100),
    timeline VARCHAR(100),
    integrations TEXT,
    contact_method VARCHAR(100) NOT NULL,
    contact_info VARCHAR(200),
    status VARCHAR(50) DEFAULT 'new',
    assigned_to VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица проектов
CREATE TABLE IF NOT EXISTS project (
    id SERIAL PRIMARY KEY,
    client_id INTEGER REFERENCES client(id),
    request_id INTEGER REFERENCES client_request(id),
    name VARCHAR(200) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'new',
    start_date TIMESTAMP,
    deadline TIMESTAMP,
    completed_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для отслеживания стадий проекта
CREATE TABLE IF NOT EXISTS project_stage (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES project(id),
    name VARCHAR(100) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'pending',
    order_number INTEGER NOT NULL,
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица для хранения ключей API и внешних сервисов
CREATE TABLE IF NOT EXISTS api_keys (
    id SERIAL PRIMARY KEY,
    service_name VARCHAR(100) NOT NULL,
    api_key TEXT NOT NULL,
    description TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Вставка тестовых данных (опционально)
INSERT INTO api_keys (service_name, api_key, description) 
VALUES ('telegram_bot', '7572478553:AAEJxJ9Il80zrHAjcD7ZcQnht3EP-sHYrjs', 'Основной Telegram бот для уведомлений');
