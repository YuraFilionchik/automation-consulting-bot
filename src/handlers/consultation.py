"""Handler for AI consultations"""

import logging

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.keyboards.inline import (
    get_start_keyboard,
    get_main_menu_inline,
    get_cancel_keyboard,
    get_confirm_application_keyboard
)
from src.services.ai_service import ai_service
from src.utils.formatters import sanitize_html

router = Router()
logger = logging.getLogger(__name__)


# Consultation states
class ConsultationState(StatesGroup):
    active = State()


# Store conversation history in memory (for simplicity)
# In production, use Redis or database
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
    """Handle message in consultation mode"""
    
    user_id = message.from_user.id
    user_message = message.text.strip()
    
    # Check if user wants to submit an application
    apply_keywords = ['want application', 'submit application', 'apply now', 'apply', 'order', 'price', 'cost']
    if any(keyword in user_message.lower() for keyword in apply_keywords):
        from src.handlers.application import start_application
        await message.answer("💡 Got it! Switching to application form...")
        await state.clear()
        await start_application(message, state)
        return
    
    # Add user message to history
    if user_id not in user_conversations:
        user_conversations[user_id] = []
    
    user_conversations[user_id].append({"role": "user", "content": user_message})
    
    # Show typing indicator
    thinking_msg = await message.answer("⏳ Thinking...")
    
    # Get AI response
    ai_response = await ai_service.get_response(
        user_message=user_message,
        conversation_history=user_conversations[user_id]
    )
    
    # Check for application request from AI
    should_switch_to_app = False
    if "APPLICATION_REQUEST" in ai_response:
        ai_response = ai_response.replace("APPLICATION_REQUEST", "").strip()
        should_switch_to_app = True

    # Add AI response to history
    user_conversations[user_id].append({"role": "assistant", "content": ai_response})
    
    # Send response
    try:
        await thinking_msg.delete()
    except Exception:
        pass

    if ai_response.strip():
        await message.answer(sanitize_html(ai_response), parse_mode="HTML")

    if should_switch_to_app:
        await message.answer(
            "Would you like to file a formal application for this project?",
            reply_markup=get_confirm_application_keyboard()
        )
    
    logger.info(f"Consultation message from user {user_id}: {len(user_message)} chars")


@router.callback_query(ConsultationState.active, F.data == "confirm_app_start")
async def process_confirm_app(callback: CallbackQuery, state: FSMContext):
    """Handle confirmation to start application from AI consultation"""

    user_id = callback.from_user.id
    history = user_conversations.get(user_id, [])

    await callback.message.edit_text("⏳ Extracting data from our conversation...", reply_markup=None)

    # Extract data using AI
    extracted_data = await ai_service.extract_application_data(history)

    from src.handlers.application import start_application
    await callback.message.delete()
    # Pass both message and the actual user who clicked the button
    await start_application(callback.message, state, initial_data=extracted_data, user=callback.from_user)
    await callback.answer()


@router.callback_query(ConsultationState.active, F.data == "continue_consultation")
async def process_continue_consultation(callback: CallbackQuery, state: FSMContext):
    """Continue consultation after declining application"""

    await callback.message.edit_text("Got it! Let's continue our conversation. What else would you like to know?")
    await callback.answer()


@router.message(F.text == "/consultation_status")
async def consultation_status(message: Message, state: FSMContext):
    """Show consultation status"""
    
    current_state = await state.get_state()
    
    if current_state == ConsultationState.active.state:
        await message.answer("💬 You are in AI consultation mode. Write your question!")
    else:
        await message.answer(
            "You are not in consultation mode. Select '💬 AI Consultation' from the main menu.",
            reply_markup=get_start_keyboard()
        )
