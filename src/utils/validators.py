"""Валидация данных"""

import re
from typing import Tuple, Optional


def validate_phone(text: str) -> Tuple[bool, str]:
    """
    Проверить является ли текст телефоном.
    Возвращает (is_valid, cleaned_or_message)
    """
    # Убрать всё кроме цифр, +, -, (, ), пробелов
    cleaned = re.sub(r'[^\d+\-()\s]', '', text.strip())

    # Должно быть минимум 7 цифр
    digits_only = re.sub(r'[^\d]', '', cleaned)

    if len(digits_only) < 7:
        return False, "⚠️ Please provide a valid phone number (at least 7 digits)."

    if len(digits_only) > 15:
        return False, "⚠️ Phone number seems too long. Please check and try again."

    return True, cleaned


def validate_email(text: str) -> Tuple[bool, str]:
    """
    Проверить является ли текст email.
    """
    text = text.strip()
    pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'

    if re.match(pattern, text):
        return True, text

    return False, "⚠️ That doesn't look like a valid email address. Please try again."


def validate_contact(text: str) -> Tuple[bool, str, str]:
    """
    Определить тип контакта (phone/email/other) и валидировать.
    Возвращает (is_valid, contact_type, cleaned_value)
    """
    text = text.strip()

    # Попробовать как email
    if '@' in text:
        is_valid, result = validate_email(text)
        if is_valid:
            return True, "email", result
        return False, "email", result

    # Попробовать как телефон
    if any(c.isdigit() for c in text):
        is_valid, result = validate_phone(text)
        if is_valid:
            return True, "phone", result
        return False, "phone", result

    # Просто текст — принимаем как есть
    if len(text) >= 3:
        return True, "other", text

    return False, "other", "⚠️ Contact information is too short. Please provide a phone, email, or other contact."


def validate_task_description(text: str) -> Tuple[bool, str]:
    """Проверить описание задачи"""
    text = text.strip()

    if len(text) < 10:
        return False, "⚠️ Please describe your task in more detail (at least 10 characters)."

    if len(text) > 2000:
        return True, text[:2000]  # Обрезать до 2000 символов

    return True, text


def is_likely_project_type(text: str) -> Optional[str]:
    """Определить вероятный тип проекта из текста"""
    text_lower = text.lower()

    keywords = {
        "bot": ["bot", "telegram bot", "chatbot", "бот"],
        "crm": ["crm", "bitrix", "amo", "hubspot", "pipedrive", "pipeline"],
        "website": ["website", "site", "web app", "landing page", "сайт"],
        "parsing": ["parse", "scrape", "crawl", "data collection", "парсинг", "скрапинг"],
        "integration": ["integration", "api", "connect", "sync", "автоматизация"],
    }

    for project_type, keywords_list in keywords.items():
        if any(kw in text_lower for kw in keywords_list):
            return project_type

    return None
