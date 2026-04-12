"""Сервис уведомлений"""

import asyncio
import logging
from datetime import datetime
from typing import Optional

from aiogram import Bot

from src.config.settings import settings
from src.models.application import Application

logger = logging.getLogger(__name__)


async def notify_new_application(
    bot: Bot,
    application: Application,
    username: Optional[str] = None,
):
    """Уведомить админов о новой заявке"""

    if not settings.admin_ids_list:
        logger.warning("No admin IDs configured for notifications")
        return

    text = application.format_for_admin()
    if username:
        text += f"\n👤 Username: @{username}"

    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(
                admin_id,
                text,
                parse_mode="HTML",
            )
            logger.info(f"Admin {admin_id} notified about application #{application.id}")
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}", exc_info=True)


async def notify_admin_custom(
    bot: Bot,
    admin_id: int,
    text: str,
    parse_mode: str = "HTML",
):
    """Отправить произвольное уведомление админу"""
    try:
        await bot.send_message(admin_id, text, parse_mode=parse_mode)
    except Exception as e:
        logger.error(f"Failed to send custom notification to admin {admin_id}: {e}")


async def notify_all_admins(
    bot: Bot,
    text: str,
    parse_mode: str = "HTML",
):
    """Отправить уведомление всем админам"""
    for admin_id in settings.admin_ids_list:
        try:
            await bot.send_message(admin_id, text, parse_mode=parse_mode)
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")


def format_daily_report(applications: list, consultations: int) -> str:
    """Сформировать текст ежедневного отчёта"""

    today = datetime.now().strftime("%Y-%m-%d")

    text = f"📊 <b>Daily Report — {today}</b>\n\n"
    text += f"📨 Applications: {len(applications)}\n"

    if applications:
        new_count = sum(1 for a in applications if a.status == "new")
        text += f"   └ New: {new_count}\n"

    text += f"💬 Consultations: {consultations}\n"

    # Группировка по типу проекта
    if applications:
        types = {}
        for app in applications:
            t = app.project_type or "unknown"
            types[t] = types.get(t, 0) + 1

        if types:
            text += "\n📋 By type:\n"
            for t, count in sorted(types.items(), key=lambda x: -x[1]):
                text += f"   • {t}: {count}\n"

    return text
