# 🗄️ Схема базы данных (SQLite)

## Общая архитектура

- **Тип**: SQLite 3
- **Файл**: `data/bot.db`
- **Миграции**: Ручные через SQL скрипты
- **Бэкап**: Копирование файла `bot.db`

## Таблицы

### 1. users - Пользователи

```sql
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language_code VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);
CREATE INDEX idx_users_username ON users(username);
```

**Поля:**
- `telegram_id` - ID пользователя в Telegram (уникальный)
- `username` - @username из Telegram
- `language_code` - язык из Telegram API

---

### 2. applications - Заявки

```sql
CREATE TABLE IF NOT EXISTS applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    status VARCHAR(50) DEFAULT 'new',
    
    -- Данные заявки
    project_type VARCHAR(100),
    project_subtype VARCHAR(100),
    budget_range VARCHAR(50),
    timeline VARCHAR(50),
    contact_info TEXT,
    task_description TEXT,
    
    -- Метаданные
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE INDEX idx_applications_user_id ON applications(user_id);
CREATE INDEX idx_applications_status ON applications(status);
CREATE INDEX idx_applications_created ON applications(created_at);
```

**Статусы заявок:**
- `new` - Новая
- `in_progress` - В работе
- `contacted` - Связались с клиентом
- `completed` - Завершена
- `cancelled` - Отменена

---

### 3. consultations - Консультации

```sql
CREATE TABLE IF NOT EXISTS consultations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id BIGINT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    messages_count INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',
    rating INTEGER,  -- 1-5 оценка консультации
    
    FOREIGN KEY (user_id) REFERENCES users(telegram_id)
);

CREATE INDEX idx_consultations_user_id ON consultations(user_id);
CREATE INDEX idx_consultations_status ON consultations(status);
```

---

### 4. consultation_messages - Сообщения консультаций

```sql
CREATE TABLE IF NOT EXISTS consultation_messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    consultation_id INTEGER NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'user' или 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    FOREIGN KEY (consultation_id) REFERENCES consultations(id)
);

CREATE INDEX idx_messages_consultation ON consultation_messages(consultation_id);
CREATE INDEX idx_messages_created ON consultation_messages(created_at);
```

---

### 5. settings - Настройки бота

```sql
CREATE TABLE IF NOT EXISTS settings (
    key VARCHAR(100) PRIMARY KEY,
    value TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Начальные настройки
INSERT OR IGNORE INTO settings (key, value) VALUES 
    ('ai_model', 'gpt-3.5-turbo'),
    ('ai_temperature', '0.7'),
    ('max_tokens', '500'),
    ('session_timeout_minutes', '30'),
    ('admin_notifications', 'true');
```

---

## Примеры запросов

### Создать пользователя

```python
async def create_user(telegram_id, username, first_name, last_name, language_code):
    query = """
    INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name, language_code)
    VALUES (?, ?, ?, ?, ?)
    """
    await execute_query(query, (telegram_id, username, first_name, last_name, language_code))
```

### Сохранить заявку

```python
async def save_application(user_id, data):
    query = """
    INSERT INTO applications 
        (user_id, project_type, project_subtype, budget_range, timeline, 
         contact_info, task_description)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """
    return await execute_query(query, (
        user_id,
        data.get('project_type'),
        data.get('project_subtype'),
        data.get('budget_range'),
        data.get('timeline'),
        data.get('contact_info'),
        data.get('task_description')
    ))
```

### Получить все заявки

```python
async def get_all_applications(status=None, limit=50, offset=0):
    if status:
        query = """
        SELECT a.*, u.username, u.first_name 
        FROM applications a
        JOIN users u ON a.user_id = u.telegram_id
        WHERE a.status = ?
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
        """
        return await execute_query(query, (status, limit, offset))
    else:
        query = """
        SELECT a.*, u.username, u.first_name 
        FROM applications a
        JOIN users u ON a.user_id = u.telegram_id
        ORDER BY a.created_at DESC
        LIMIT ? OFFSET ?
        """
        return await execute_query(query, (limit, offset))
```

### Статистика

```python
async def get_statistics():
    queries = {
        'total_users': "SELECT COUNT(*) FROM users",
        'total_applications': "SELECT COUNT(*) FROM applications",
        'new_applications': "SELECT COUNT(*) FROM applications WHERE status = 'new'",
        'total_consultations': "SELECT COUNT(*) FROM consultations",
        'active_consultations': "SELECT COUNT(*) FROM consultations WHERE status = 'active'",
        'applications_by_type': """
            SELECT project_type, COUNT(*) as count 
            FROM applications 
            GROUP BY project_type
            ORDER BY count DESC
        """,
    }
    
    results = {}
    for key, query in queries.items():
        results[key] = await execute_query(query)
    
    return results
```

---

## Миграции

### Файл: `migrations/001_initial.sql`

```sql
-- Начальная схема (все таблицы выше)
```

### Файл: `migrations/002_add_application_notes.sql` (пример будущей миграции)

```sql
ALTER TABLE applications ADD COLUMN admin_notes TEXT;
ALTER TABLE applications ADD COLUMN priority VARCHAR(20) DEFAULT 'normal';
```

---

## Бэкап

```bash
# Скрипт для бэкапа (deploy/backup.sh)
#!/bin/bash
BACKUP_DIR="/opt/bot/backups"
DB_FILE="/opt/bot/data/bot.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

cp $DB_FILE "$BACKUP_DIR/bot_$TIMESTAMP.db"

# Хранить только последние 30 дней
find $BACKUP_DIR -name "bot_*.db" -mtime +30 -delete
```

---

## Оптимизация для SQLite

```python
# Настройки при инициализации
PRAGMA journal_mode=WAL;        # Write-Ahead Logging для конкурентности
PRAGMA synchronous=NORMAL;      # Баланс скорость/безопасность
PRAGMA cache_size=10000;        # Кэш в страницах
PRAGMA temp_store=MEMORY;       # Временные таблицы в памяти
PRAGMA foreign_keys=ON;         # Включить внешние ключи
```
