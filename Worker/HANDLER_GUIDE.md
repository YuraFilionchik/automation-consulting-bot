# 📝 Руководство по созданию хендлеров

## Структура хендлера в aiogram 3.x

### Базовый пример

```python
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

router = Router()

# Группа состояний
class MyState(StatesGroup):
    state_1 = State()
    state_2 = State()

# Хендлер команды
@router.message(F.text == "/command")
async def handle_command(message: Message, state: FSMContext):
    await message.answer("Привет!")
    await state.set_state(MyState.state_1)

# Хендлер для состояния
@router.message(MyState.state_1)
async def handle_state_1(message: Message, state: FSMContext):
    # Обработка данных
    await state.update_data(user_input=message.text)
    await message.answer("Следующий вопрос...")
    await state.set_state(MyState.state_2)

# Хендлер callback (inline кнопки)
@router.callback_query(F.data == "some_action")
async def handle_callback(callback: CallbackQuery, state: FSMContext):
    await callback.message.answer("Действие выполнено")
    await callback.answer()
```

## Правила создания хендлеров

### 1. Название файлов
- `start.py` - для /start и приветствия
- `consultation.py` - для режима консультации
- `application.py` - для режима заявок
- `common.py` - для общих команд (/help, /cancel)

### 2. Регистрация роутеров
В `main.py` все роутеры регистрируются:

```python
from handlers import start, consultation, application, common

dp.include_router(start.router)
dp.include_router(consultation.router)
dp.include_router(application.router)
dp.include_router(common.router)
```

### 3. Порядок важен!
Хендлеры обрабатываются в порядке регистрации. Более специфичные хендлеры должны быть выше.

```python
# ✅ ПРАВИЛЬНО:
@router.message(F.text == "/cancel")  # Специфичный
async def handle_cancel(...):
    ...

@router.message()  # Общий (catch-all)
async def handle_all_messages(...):
    ...

# ❌ НЕПРАВИЛЬНО:
@router.message()  # Перехватит все сообщения!
async def handle_all_messages(...):
    ...

@router.message(F.text == "/cancel")  # Никогда не сработает
async def handle_cancel(...):
    ...
```

### 4. Работа с FSM

```python
# Сохранение данных
await state.update_data(
    project_type="bot",
    budget="50-100k"
)

# Получение данных
data = await state.get_data()
project_type = data.get("project_type")

# Очистка состояния
await state.clear()

# Сброс конкретного состояния
await state.set_state(None)
```

### 5. Inline клавиатуры

```python
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_project_type_keyboard():
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
```

### 6. Reply клавиатуры

```python
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text="📝 Оставить заявку"),
        KeyboardButton(text="💬 Консультация"),
    )
    builder.row(
        KeyboardButton(text="❓ Помощь"),
    )
    return builder.as_markup(resize_keyboard=True)
```

## Чеклист перед коммитом

- [ ] Хендлер зарегистрирован в `main.py`
- [ ] Есть обработка ошибок
- [ ] Пользователь понимает что происходит (ответы бота)
- [ ] Есть путь отмены (/cancel)
- [ ] Протестированы все сценарии
- [ ] Логи добавлены для отладки
