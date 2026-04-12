"""Общие хендлеры (/help, /cancel)"""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from src.keyboards.inline import get_start_keyboard, get_main_menu_inline

router = Router()
logger = logging.getLogger(__name__)


@router.message(F.text == "/help")
@router.callback_query(F.data == "action_help")
async def handle_help(message_or_callback: Message | CallbackQuery, state: FSMContext):
    """Handle help command"""
    
    text = (
        f"📖 <b>Help</b>\n\n"
        f"This bot helps you:\n"
        f"📝 <b>Submit Application</b> — fill out a request for bot, CRM, or automation development\n"
        f"💬 <b>AI Consultation</b> — get answers to your automation questions and identify your needs\n\n"
        f"<b>Commands:</b>\n"
        f"/start — Main menu\n"
        f"/help — This help\n"
        f"/cancel — Cancel current dialog\n\n"
        f"Choose an action in the main menu 👇"
    )
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=get_start_keyboard(), parse_mode="HTML")


@router.message(F.text == "/cancel")
@router.callback_query(F.data == "action_cancel")
async def handle_cancel(message_or_callback: Message | CallbackQuery, state: FSMContext):
    """Cancel current action"""
    
    await state.clear()
    
    text = (
        f"❌ <b>Action cancelled</b>\n\n"
        f"You can return to the main menu:"
    )
    
    if isinstance(message_or_callback, CallbackQuery):
        await message_or_callback.message.edit_text(text, reply_markup=get_main_menu_inline(), parse_mode="HTML")
        await message_or_callback.answer()
    else:
        await message_or_callback.answer(text, reply_markup=get_main_menu_inline(), parse_mode="HTML")
    
    logger.info(f"User {message_or_callback.from_user.id} cancelled action")
