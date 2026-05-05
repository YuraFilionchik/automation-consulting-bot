"""Handler for applications"""

import logging
from typing import Optional

from aiogram import Bot, Router, F
from aiogram.types import Message, CallbackQuery, User
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.keyboards.inline import (
    get_project_type_keyboard,
    get_bot_subtype_keyboard,
    get_budget_keyboard,
    get_timeline_keyboard,
    get_after_application_keyboard,
    get_cancel_keyboard,
)
from src.models.application import Application
from src.services.application_service import create_application, get_application_summary
from src.services.notification_service import notify_new_application
from src.config.settings import settings
from src.utils.validators import validate_contact, validate_task_description, is_likely_project_type

router = Router()
logger = logging.getLogger(__name__)


# Application states
class ApplicationState(StatesGroup):
    project_type = State()
    project_subtype = State()
    budget_range = State()
    timeline = State()
    contact_info = State()
    task_description = State()


@router.callback_query(F.data == "action_application")
async def start_application_callback(callback: CallbackQuery, state: FSMContext):
    """Start application flow from callback"""
    await start_application(callback.message, state, callback=callback)


async def start_application(message: Message, state: FSMContext, callback: CallbackQuery = None, initial_data: dict = None, user: User = None):
    """Start application flow (logic)"""
    
    # Store user info in state if provided
    if user:
        await state.update_data(user_id=user.id, username=user.username)
    elif message.from_user and not message.from_user.is_bot:
        await state.update_data(user_id=message.from_user.id, username=message.from_user.username)

    if initial_data:
        # Pre-fill data from AI extraction
        # Filter out None values
        filtered_data = {k: v for k, v in initial_data.items() if v is not None}
        await state.update_data(**filtered_data)

        # Start the smart flow
        await continue_application_flow(message, state)
        return

    await state.set_state(ApplicationState.project_type)
    
    text = (
        f"📝 <b>Application Form</b>\n\n"
        f"Great! I'll help you submit an application. What type of project are you interested in?\n\n"
        f"Choose from the options or write your own:"
    )
    
    if callback:
        await callback.message.edit_text(text, reply_markup=get_project_type_keyboard(), parse_mode="HTML")
        await callback.answer()
        user_id = callback.from_user.id
    else:
        await message.answer(text, reply_markup=get_project_type_keyboard(), parse_mode="HTML")
        user_id = message.from_user.id if message.from_user else "unknown"

    logger.info(f"User {user_id} started application")


async def continue_application_flow(message: Message, state: FSMContext, bot: Bot = None):
    """Smartly continue application flow by skipping already filled fields"""

    data = await state.get_data()

    # 1. Project Type
    if not data.get('project_type'):
        await state.set_state(ApplicationState.project_type)
        await _send_or_edit(message, "What type of project are you interested in?\n\nChoose from the options or write your own:", get_project_type_keyboard())
        return

    # 2. Project Subtype (only if project_type is bot)
    if data.get('project_type') == 'bot' and not data.get('project_subtype'):
        await state.set_state(ApplicationState.project_subtype)
        await _send_or_edit(message, "What functionality do you need from the bot?", get_bot_subtype_keyboard())
        return

    # 3. Budget
    if not data.get('budget_range'):
        await state.set_state(ApplicationState.budget_range)
        await _send_or_edit(message, "What's your planned budget?", get_budget_keyboard())
        return

    # 4. Timeline
    if not data.get('timeline'):
        await state.set_state(ApplicationState.timeline)
        await _send_or_edit(message, "When are you planning to start?", get_timeline_keyboard())
        return

    # 5. Contact Info
    contact_info = data.get('contact_info')
    if contact_info:
        # Re-validate if it came from AI
        is_valid, contact_type, result = validate_contact(contact_info)
        if not is_valid:
            contact_info = None # Trigger asking again
        else:
            await state.update_data(contact_info=result)

    if not contact_info:
        await state.set_state(ApplicationState.contact_info)
        await _send_or_edit(message, "How can we reach you?\n\nPlease provide your phone or email:", get_cancel_keyboard())
        return

    # 6. Task Description
    task_desc = data.get('task_description')
    if task_desc:
        is_valid, result = validate_task_description(task_desc)
        if not is_valid:
            task_desc = None
        else:
            await state.update_data(task_description=result)

    if not task_desc:
        await state.set_state(ApplicationState.task_description)
        await _send_or_edit(message, "Tell us more about your task.\n\nWhat exactly do you need done? Describe in your own words (at least 10 characters):", get_cancel_keyboard())
        return

    # All data present!
    if not bot:
        bot = message.bot

    await finalize_application(message, state, bot)


async def _send_or_edit(message: Message, text: str, reply_markup=None):
    """Helper to edit bot message or send a new one if it's a user message"""
    if message.from_user and message.from_user.is_bot:
        try:
            await message.edit_text(text, reply_markup=reply_markup, parse_mode="HTML")
            return
        except Exception:
            pass
    await message.answer(text, reply_markup=reply_markup, parse_mode="HTML")


@router.callback_query(ApplicationState.project_type, F.data.startswith("type_"))
async def set_project_type_callback(callback: CallbackQuery, state: FSMContext):
    """Set project type from button"""
    
    project_type = callback.data.replace("type_", "")
    await process_project_type(project_type, callback.message, state, callback)


@router.message(ApplicationState.project_type, F.text)
async def set_project_type_message(message: Message, state: FSMContext):
    """Set project type from text"""

    project_type = is_likely_project_type(message.text)

    if project_type:
        await process_project_type(project_type, message, state)
    else:
        await message.answer(
            "I couldn't quite determine the project type. Please choose from the buttons below or describe more clearly:",
            reply_markup=get_project_type_keyboard()
        )


async def process_project_type(project_type: str, message: Message, state: FSMContext, callback: CallbackQuery = None):
    """Common logic for project type processing"""
    await state.update_data(project_type=project_type)
    if callback:
        await callback.answer()
    
    await continue_application_flow(message, state)


@router.callback_query(ApplicationState.project_subtype, F.data.startswith("subtype_"))
async def set_project_subtype(callback: CallbackQuery, state: FSMContext):
    """Set project subtype"""
    
    subtype = callback.data.replace("subtype_", "")
    await state.update_data(project_subtype=subtype)
    await callback.answer()
    await continue_application_flow(callback.message, state)


@router.message(ApplicationState.project_subtype)
async def set_project_subtype_text(message: Message):
    """Handle text input for project subtype"""
    await message.answer(
        "Please select the bot functionality using the buttons below:",
        reply_markup=get_bot_subtype_keyboard()
    )


@router.callback_query(ApplicationState.budget_range, F.data.startswith("budget_"))
async def set_budget(callback: CallbackQuery, state: FSMContext):
    """Set budget range"""
    
    budget = callback.data.replace("budget_", "")
    budget_map = {
        "under_500": "under €500",
        "500_1500": "€500–1,500",
        "1500_5000": "€1,500–5,000",
        "5000_15000": "€5,000–15,000",
        "over_15000": "€15,000+",
        "undefined": "Not decided yet",
    }
    
    await state.update_data(budget_range=budget_map.get(budget, budget))
    await callback.answer()
    await continue_application_flow(callback.message, state)


@router.message(ApplicationState.budget_range)
async def set_budget_text(message: Message):
    """Handle text input for budget"""
    await message.answer(
        "Please select your budget range using the buttons below:",
        reply_markup=get_budget_keyboard()
    )


@router.callback_query(ApplicationState.timeline, F.data.startswith("timeline_"))
async def set_timeline(callback: CallbackQuery, state: FSMContext):
    """Set timeline"""
    
    timeline = callback.data.replace("timeline_", "")
    timeline_map = {
        "week": "This week",
        "month": "This month",
        "quarter": "This quarter",
        "planning": "Just planning",
    }
    
    await state.update_data(timeline=timeline_map.get(timeline, timeline))
    await callback.answer()
    await continue_application_flow(callback.message, state)


@router.message(ApplicationState.timeline)
async def set_timeline_text(message: Message):
    """Handle text input for timeline"""
    await message.answer(
        "Please select your timeline using the buttons below:",
        reply_markup=get_timeline_keyboard()
    )


@router.message(ApplicationState.contact_info)
async def set_contact_info(message: Message, state: FSMContext):
    """Set contact information"""
    
    is_valid, contact_type, result = validate_contact(message.text)

    if not is_valid:
        await message.answer(result, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        return

    await state.update_data(contact_info=result)
    await continue_application_flow(message, state)


@router.message(ApplicationState.task_description)
async def set_task_description(message: Message, state: FSMContext, bot: Bot):
    """Set task description and save application"""
    
    is_valid, result = validate_task_description(message.text)

    if not is_valid:
        await message.answer(result, reply_markup=get_cancel_keyboard(), parse_mode="HTML")
        return

    await state.update_data(task_description=result)
    await finalize_application(message, state, bot)


async def finalize_application(message: Message, state: FSMContext, bot: Bot):
    """Finalize and save application"""
    
    # Get data
    data = await state.get_data()
    user_id = data.get('user_id')
    username = data.get('username', 'unknown')
    
    # Fallback to current user if not in data
    if not user_id and message.from_user and not message.from_user.is_bot:
        user_id = message.from_user.id
        username = message.from_user.username

    if not user_id:
        logger.error("Cannot finalize application: user_id is missing")
        if message:
            await message.answer("An error occurred. Please try starting the application again.")
        await state.clear()
        return

    # Save application
    application = await create_application(user_id, data)
    
    # Show summary
    summary = get_application_summary(data)
    if message:
        await message.answer(summary, parse_mode="HTML")
    
    # Show confirmation
    confirmation = (
        f"✅ <b>Application #{application.id} submitted!</b>\n\n"
        f"Our manager will contact you shortly!\n\n"
        f"Would you like to get an AI consultation?"
    )
    
    if message:
        await message.answer(confirmation, reply_markup=get_after_application_keyboard(), parse_mode="HTML")
    
    # Notify admins
    await notify_new_application(bot, application, username)
    
    await state.clear()
    logger.info(f"Application #{application.id} completed by user {user_id}")
