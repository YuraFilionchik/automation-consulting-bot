"""Настройки приложения"""

from pydantic import BaseModel
from pydantic_settings import BaseSettings
from typing import List, Optional


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения"""
    
    # Telegram
    BOT_TOKEN: str
    
    # AI Provider
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    
    # Администраторы
    ADMIN_IDS: str = ""  # Комма-разделенные ID
    
    # База данных
    DATABASE_PATH: str = "data/bot.db"
    
    # Логирование
    LOG_LEVEL: str = "INFO"
    
    # AI параметры
    AI_PROVIDER: str = "gemini"  # gemini или openai
    AI_MODEL: str = "gemini-2.0-flash"
    AI_TEMPERATURE: float = 0.7
    AI_MAX_TOKENS: int = 500
    
    # Сессия
    SESSION_TIMEOUT_MINUTES: int = 30
    
    @property
    def admin_ids_list(self) -> List[int]:
        """Получить список admin ID"""
        if not self.ADMIN_IDS:
            return []
        return [int(id.strip()) for id in self.ADMIN_IDS.split(",") if id.strip()]
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Глобальный экземпляр
settings = Settings()
