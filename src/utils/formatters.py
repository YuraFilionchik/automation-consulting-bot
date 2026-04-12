"""Форматирование данных"""

from datetime import datetime
from typing import Optional


def format_currency(amount: Optional[float], currency: str = "EUR") -> str:
    """Форматировать сумму в валюте"""
    if amount is None:
        return "Not specified"
    return f"€{amount:,.0f}"


def format_date(dt: Optional[datetime], format_str: str = "%Y-%m-%d %H:%M") -> str:
    """Форматировать дату"""
    if dt is None:
        return "N/A"
    return dt.strftime(format_str)


def format_phone(phone: str) -> str:
    """Форматировать телефон для отображения"""
    digits = ''.join(c for c in phone if c.isdigit())

    if len(digits) == 11 and digits.startswith('48'):
        # Poland format
        return f"+48 {digits[2:5]} {digits[5:8]} {digits[8:11]}"

    if len(digits) == 11 and digits.startswith('7') or digits.startswith('8'):
        # Russia format
        return f"+7 ({digits[1:4]}) {digits[4:7]}-{digits[7:9]}-{digits[9:11]}"

    # Default: just return cleaned
    return phone.replace(' ', '')


def truncate(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Обрезать текст до нужной длины"""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def format_duration(seconds: int) -> str:
    """Форматировать длительность"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        return f"{minutes}m"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"


def sanitize_html(text: str) -> str:
    """Экранировать HTML-символы в пользовательском вводе"""
    replacements = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def format_application_list(applications: list, page: int = 1, per_page: int = 10) -> str:
    """Форматировать список заявок для админа"""

    total = len(applications)
    start = (page - 1) * per_page
    end = start + per_page
    page_items = applications[start:end]

    if not page_items:
        return "📭 No applications found."

    text = f"📨 <b>Applications (page {page})</b>\n"
    text += f"Total: {total}\n\n"

    for app in page_items:
        status_emoji = {
            "new": "🆕",
            "in_progress": "🔄",
            "contacted": "📞",
            "completed": "✅",
            "cancelled": "❌",
        }.get(app.status, "📋")

        text += f"{status_emoji} <b>#{app.id}</b> — {app.project_type or 'unknown'}\n"
        text += f"   💰 {app.budget_range or 'N/A'} | ⏰ {app.timeline or 'N/A'}\n"
        text += f"   🕐 {app.created_at}\n\n"

    if end < total:
        text += f"... and {total - end} more"

    return text
