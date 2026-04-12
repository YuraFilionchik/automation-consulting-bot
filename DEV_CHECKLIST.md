# ✅ Чеклист разработки

## Этап 1: Базовая настройка ✅

- [x] Создана структура проекта
- [x] Написан README
- [x] Созданы директории Director и Worker
- [x] Документация по архитектуре
- [x] requirements.txt
- [x] .env.example
- [x] .gitignore

## Этап 2: Код базового бота ✅

- [x] src/main.py - точка входа
- [x] src/config/settings.py - настройки
- [x] src/config/logging.py - логирование
- [x] src/models/database.py - инициализация БД
- [x] src/models/application.py - модель заявки
- [x] src/handlers/start.py - /start хендлер
- [x] src/handlers/common.py - /help, /cancel
- [x] src/handlers/application.py - прием заявок
- [x] src/handlers/consultation.py - AI консультации
- [x] src/services/ai_service.py - OpenAI интеграция
- [x] src/services/application_service.py - обработка заявок
- [x] src/keyboards/inline.py - inline клавиатуры

## Этап 3: Тестирование ⏳

- [ ] Локальный запуск бота
- [ ] Тест /start команды
- [ ] Тест потока заявок
- [ ] Тест потока консультаций
- [ ] Тест отмены действий
- [ ] Тест с реальным OpenAI API
- [ ] Тест сохранения в БД

## Этап 4: Доработка (опционально)

- [ ] Добавить модели consultation.py
- [ ] Добавить notification_service.py
- [ ] Добавить utils/validators.py
- [ ] Добавить utils/formatters.py
- [ ] Написать unit тесты
- [ ] Добавить админ панель (просмотр заявок)
- [ ] Добавить экспорт заявок в CSV/Excel

## Этап 5: Деплой ⏳

- [ ] Подготовить Linux сервер
- [ ] Настроить .env
- [ ] Установить зависимости
- [ ] Тестовый запуск
- [ ] Настроить systemd сервис
- [ ] Настроить логирование
- [ ] Настроить бэкапы БД
- [ ] Проверить работу через Telegram

## Этап 6: Мониторинг ⏳

- [ ] Проверка логов
- [ ] Мониторинг памяти
- [ ] Проверка ошибок
- [ ] Тест уведомлений админам

## Известные проблемы / TODO

1. **Хранение истории консультаций**
   - Сейчас в памяти (user_conversations dict)
   - Для продакшена: Redis или БД

2. **Уведомления админам**
   - Нужно реализовать через background task
   - Или через очередь задач

3. **Таймаут сессии**
   - Сейчас не реализован автоматически
   - Нужно добавить проверку времени последнего сообщения

4. **Валидация данных**
   - Проверка email
   - Проверка телефона
   - Валидация текста

5. **Обработка ошибок OpenAI**
   - Rate limiting
   - Timeout
   - Quota exceeded

## Команды для разработки

```bash
# Активировать окружение
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux

# Запустить бота
python -m src.main

# Проверить логи
tail -f logs/bot.log

# Запустить тесты (когда будут)
pytest
```

## Ссылки на документацию

- **aiogram 3.x**: https://docs.aiogram.dev/en/latest/
- **OpenAI API**: https://platform.openai.com/docs/api-reference
- **Telegram Bot API**: https://core.telegram.org/bots/api
