"""Инициализация и работа с базой данных"""

import sqlite3
import logging
from pathlib import Path
from contextlib import contextmanager

from src.config.settings import settings

logger = logging.getLogger(__name__)


def init_database():
    """Инициализация базы данных"""
    
    # Создать директорию для данных
    db_path = Path(settings.DATABASE_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Оптимизация SQLite
    cursor.executescript("""
        PRAGMA journal_mode=WAL;
        PRAGMA synchronous=NORMAL;
        PRAGMA cache_size=10000;
        PRAGMA temp_store=MEMORY;
        PRAGMA foreign_keys=ON;
    """)
    
    # Создать таблицы
    cursor.executescript("""
        -- Пользователи
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id BIGINT UNIQUE NOT NULL,
            username VARCHAR(255),
            first_name VARCHAR(255),
            last_name VARCHAR(255),
            language_code VARCHAR(10) DEFAULT 'ru',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        
        -- Заявки
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            status VARCHAR(50) DEFAULT 'new',
            project_type VARCHAR(100),
            project_subtype VARCHAR(100),
            budget_range VARCHAR(50),
            timeline VARCHAR(50),
            contact_info TEXT,
            task_description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            completed_at TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id);
        CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
        
        -- Консультации
        CREATE TABLE IF NOT EXISTS consultations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id BIGINT NOT NULL,
            started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            ended_at TIMESTAMP,
            messages_count INTEGER DEFAULT 0,
            status VARCHAR(50) DEFAULT 'active',
            rating INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(telegram_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_consultations_user_id ON consultations(user_id);
        
        -- Сообщения консультаций
        CREATE TABLE IF NOT EXISTS consultation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consultation_id INTEGER NOT NULL,
            role VARCHAR(20) NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (consultation_id) REFERENCES consultations(id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_messages_consultation ON consultation_messages(consultation_id);
        
        -- Настройки
        CREATE TABLE IF NOT EXISTS settings (
            key VARCHAR(100) PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    
    # Вставить настройки по умолчанию
    cursor.executescript("""
        INSERT OR IGNORE INTO settings (key, value) VALUES 
            ('ai_model', 'gpt-3.5-turbo'),
            ('ai_temperature', '0.7'),
            ('max_tokens', '500'),
            ('session_timeout_minutes', '30'),
            ('admin_notifications', 'true');
    """)
    
    conn.commit()
    conn.close()
    
    logger.info(f"Database initialized at {db_path}")


@contextmanager
def get_db_connection():
    """Контекстный менеджер для подключения к БД"""
    conn = sqlite3.connect(settings.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database error: {e}")
        raise
    finally:
        conn.close()
