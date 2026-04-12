"""Хендлер для /start и главного меню"""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.keyboards.inline import get_start_keyboard

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/start")
async def handle_start(message: Message, state: FSMContext):
    """Handle /start command"""
    
    # Clear state if any
    await state.clear()
    
    text = (
        f"👋 <b>Welcome!</b>\n\n"
        f"I'm your AI consultant for business automation.\n\n"
        f"I can help you in two ways:\n"
        f"📝 <b>Submit Application</b> — fill out a project request\n"
        f"💬 <b>AI Consultation</b> — get answers to your automation questions\n\n"
        f"Choose an option below 👇"
    )
    
    await message.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    logger.info(f"User {message.from_user.id} started bot")


@router.callback_query(F.data == "action_main_menu")
async def handle_main_menu(callback: CallbackQuery, state: FSMContext):
    """Return to main menu"""
    
    await state.clear()
    
    text = (
        f"🏠 <b>Main Menu</b>\n\n"
        f"Choose an action:"
    )
    
    await callback.message.edit_text(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
    await callback.answer()
