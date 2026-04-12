"""Сервис обработки заявок"""

import logging
from typing import Optional

from src.models.application import Application, save_application
from src.models.database import get_db_connection
from src.config.settings import settings

logger = logging.getLogger(__name__)


async def create_application(user_id: int, data: dict) -> Application:
    """Создать новую заявку"""
    
    app_data = {
        'user_id': user_id,
        **data
    }
    
    application = await save_application(app_data)
    logger.info(f"Application #{application.id} created for user {user_id}")
    
    return application


async def notify_admin(application: Application):
    """Уведомить админов о новой заявке"""
    # Эта функция будет вызвана из хендлера
    # так как нужен доступ к bot для отправки сообщений
    logger.info(f"Admin notification needed for application #{application.id}")


def get_application_summary(data: dict) -> str:
    """Get application summary for user"""
    
    summary = "📋 <b>Application Summary:</b>\n\n"
    summary += f"Type: {data.get('project_type', 'Not specified')}\n"
    
    if data.get('project_subtype'):
        summary += f"Subtype: {data.get('project_subtype')}\n"
    
    summary += f"Budget: {data.get('budget_range', 'Not specified')}\n"
    summary += f"Timeline: {data.get('timeline', 'Not specified')}\n"
    summary += f"Contact: {data.get('contact_info', 'Not specified')}\n"
    summary += f"Task: {data.get('task_description', 'Not described')[:200]}"
    
    if len(data.get('task_description', '')) > 200:
        summary += "..."
    
    return summary
