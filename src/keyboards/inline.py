"""Inline клавиатуры"""

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard():
    """Main menu"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📝 Submit Application", callback_data="action_application"),
                InlineKeyboardButton(text="💬 AI Consultation", callback_data="action_consultation"),
            ],
            [
                InlineKeyboardButton(text="❓ Help", callback_data="action_help"),
            ],
        ]
    )
    return keyboard


def get_project_type_keyboard():
    """Выбор типа проекта"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🤖 Бот", callback_data="type_bot"),
                InlineKeyboardButton(text="📊 CRM", callback_data="type_crm"),
            ],
            [
                InlineKeyboardButton(text="🌐 Сайт", callback_data="type_website"),
                InlineKeyboardButton(text="🔍 Парсинг", callback_data="type_parsing"),
            ],
            [
                InlineKeyboardButton(text="📦 Другое", callback_data="type_other"),
            ],
        ]
    )
    return keyboard


def get_bot_subtype_keyboard():
    """Подтип для бота"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="📢 Рассылка", callback_data="subtype_broadcast"),
                InlineKeyboardButton(text="📝 Сбор заявок", callback_data="subtype_lead_form"),
            ],
            [
                InlineKeyboardButton(text="🔗 Интеграция", callback_data="subtype_integration"),
                InlineKeyboardButton(text="💬 Чат-бот", callback_data="subtype_chatbot"),
            ],
            [
                InlineKeyboardButton(text="📦 Другое", callback_data="subtype_other"),
            ],
        ]
    )
    return keyboard


def get_budget_keyboard():
    """Budget selection"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💵 under €500", callback_data="budget_under_500"),
                InlineKeyboardButton(text="💵💵 €500–1,500", callback_data="budget_500_1500"),
            ],
            [
                InlineKeyboardButton(text="💵💵💵 €1,500–5,000", callback_data="budget_1500_5000"),
                InlineKeyboardButton(text="💎 €5,000–15,000", callback_data="budget_5000_15000"),
            ],
            [
                InlineKeyboardButton(text="💎 €15,000+", callback_data="budget_over_15000"),
                InlineKeyboardButton(text="❓ Not decided", callback_data="budget_undefined"),
            ],
        ]
    )
    return keyboard


def get_timeline_keyboard():
    """Timeline selection"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🔥 This week", callback_data="timeline_week"),
                InlineKeyboardButton(text="📅 This month", callback_data="timeline_month"),
            ],
            [
                InlineKeyboardButton(text="🗓️ This quarter", callback_data="timeline_quarter"),
                InlineKeyboardButton(text="💭 Just planning", callback_data="timeline_planning"),
            ],
        ]
    )
    return keyboard


def get_after_application_keyboard():
    """After application submission"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="💬 AI Consultation", callback_data="action_consultation"),
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="action_main_menu"),
            ],
        ]
    )
    return keyboard


def get_cancel_keyboard():
    """Cancel keyboard"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="❌ Cancel", callback_data="action_cancel"),
            ],
        ]
    )
    return keyboard


def get_main_menu_inline():
    """Back to main menu"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🏠 Main Menu", callback_data="action_main_menu"),
            ],
        ]
    )
    return keyboard
