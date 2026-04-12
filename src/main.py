"""Точка входа приложения"""

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config.settings import settings
from src.config.logging import setup_logging
from src.models.database import init_database

from src.handlers import start, consultation, application, common, admin


async def main():
    """Главная функция"""
    
    # Настройка логирования
    logger = setup_logging()
    
    # Инициализация БД
    init_database()
    
    # Инициализация бота и диспетчера
    bot = Bot(token=settings.BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Регистрация роутеров
    from src.handlers.start import router as start_router
    from src.handlers.consultation import router as consultation_router
    from src.handlers.application import router as application_router
    from src.handlers.common import router as common_router
    from src.handlers.admin import router as admin_router
    
    dp.include_router(start_router)
    dp.include_router(consultation_router)
    dp.include_router(application_router)
    dp.include_router(common_router)
    dp.include_router(admin_router)
    
    # Запуск
    logger.info("Bot starting...")
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Bot polling error: {e}", exc_info=True)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped by user")
    except Exception as e:
        print(f"Fatal error: {e}")
