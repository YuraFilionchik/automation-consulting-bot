"""Хендлер для AI консультаций"""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.keyboards.inline import get_start_keyboard, get_main_menu_inline, get_cancel_keyboard
from src.services.ai_service import ai_service

router = Router()
logger = logging.getLogger(__name__)


# Состояния для консультации
class ConsultationState(StatesGroup):
    active = State()


# Хранение истории диалога в памяти (для простоты)
# В продакшене лучше использовать Redis или БД
user_conversations = {}


@router.callback_query(F.data == "action_consultation")
async def start_consultation(callback: CallbackQuery, state: FSMContext):
    """Start consultation"""
    
    await state.set_state(ConsultationState.active)
    
    # Initialize conversation for user
    user_id = callback.from_user.id
    user_conversations[user_id] = []
    
    text = (
        f"💬 <b>AI Consultant Session</b>\n\n"
        f"Great! I'm your AI automation consultant.\n\n"
        f"Describe your question or task, and I'll try to help with recommendations!\n\n"
        f"You can write something like:\n"
        f"• I want a bot for my business\n"
        f"• Need to automate reports\n"
        f"• Interested in CRM integration\n\n"
        f"Write your question below 👇"
    )
    
    await callback.message.edit_text(text, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
    await callback.answer()
    logger.info(f"User {user_id} started consultation")


@router.message(ConsultationState.active)
async def handle_consultation_message(message: Message, state: FSMContext):
    """Обработка сообщения в режиме консультации"""
    
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Проверить хочет ли пользователь оставить заявку
    if any(keyword in user_message.lower() for keyword in ['хочу заявку', 'оставить заявку', 'оформить заявку']):
        from src.handlers.application import start_application
        await message.answer("💡 Понял! Переключаю на оформление заявки...")
        await state.clear()
        # Создать фейковый callback для вызова функции
        class FakeCallback:
            def __init__(self, user):
                self.message = message
                self.from_user = user
        await start_application(FakeCallback(message.from_user), state)
        return
    
    # Добавить сообщение пользователя в историю
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    # Показать индикатор набора текста
    await message.answer("⏳ Думаю...")
    
    # Получить ответ от AI
    ai_response = await ai_service.get_response(
        user_message=user_message,
        conversation_history=user_conversations[user_id]
    )
    
    # Добавить ответ AI в историю
    user_conversations[user_id].append({"role": "assistant", "content": ai_response})
    
    # Отправить ответ
    await message.delete()  # Удалить "Думаю..."
    await message.answer(ai_response, parse_mode="HTML")
    
    logger.info(f"Consultation message from user {user_id}: {len(user_message)} chars")


@router.message(F.text == "/consultation_status")
async def consultation_status(message: Message, state: FSMContext):
    """Показать статус консультации"""
    
    current_state = await state.get_state()
    
    if current_state == ConsultationState.active.state:
        await message.answer("💬 Вы находитесь в режиме консультации с AI. Напишите ваш вопрос!")
    else:
        await message.answer(
            "Вы не в режиме консультации. Выберите '💬 Консультация с AI' в главном меню.",
            reply_markup=get_start_keyboard()
        )
