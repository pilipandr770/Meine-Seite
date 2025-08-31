"""
Простой скрипт создания пользователя-администратора
"""
import os
import sys
import logging
from flask import Flask
from werkzeug.security import generate_password_hash
import sqlite3

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Путь к базе данных SQLite
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'instance', 'clients.db')

def create_admin_user():
    """Создает пользователя-администратора напрямую в базе SQLite"""
    # Убедимся, что директория instance существует
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    try:
        # Подключаемся к базе данных SQLite
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Проверяем, существует ли таблица users
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
        if not cursor.fetchone():
            # Создаем таблицу users, если её нет
            logger.info("Creating users table...")
            cursor.execute('''
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(100) UNIQUE NOT NULL,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    first_name VARCHAR(50),
                    last_name VARCHAR(50),
                    is_admin BOOLEAN DEFAULT FALSE,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    reset_token VARCHAR(100),
                    reset_token_expiry TIMESTAMP
                )
            ''')
            logger.info("Users table created successfully.")
        
        # Проверяем, существует ли пользователь admin
        cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        admin_exists = cursor.fetchone()
        
        if not admin_exists:
            # Создаем пользователя admin
            logger.info("Creating admin user...")
            password_hash = generate_password_hash('Admin123!')
            cursor.execute('''
                INSERT INTO users (email, username, password_hash, first_name, last_name, is_admin, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('admin@example.com', 'admin', password_hash, 'Admin', 'User', True, True))
            
            conn.commit()
            logger.info("Admin user created successfully!")
        else:
            logger.info("Admin user already exists.")
        
        conn.close()
        
        return True
        
    except Exception as e:
        logger.error(f"Error creating admin user: {e}")
        return False

if __name__ == "__main__":
    create_admin_user()
