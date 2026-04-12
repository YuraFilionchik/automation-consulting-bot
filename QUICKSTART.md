# 🚀 Краткое руководство по запуску

## Локальная разработка (Windows)

### 1. Установка зависимостей

```bash
# Создать виртуальное окружение
python -m venv venv

# Активировать
venv\Scripts\activate

# Установить зависимости
pip install -r requirements.txt
```

### 2. Настройка .env

```bash
# Скопировать пример
copy .env.example .env

# Открыть и заполнить:
# BOT_TOKEN - получить от @BotFather в Telegram
# OPENAI_API_KEY - получить с https://platform.openai.com
# ADMIN_IDS - ваш Telegram ID (можно узнать у @userinfobot)
```

### 3. Запуск бота

```bash
# Активировать venv
venv\Scripts\activate

# Запустить
python -m src.main
```

---

## Деплой на Linux сервер

Смотрите подробную инструкцию: `Worker/DEPLOYMENT.md`

### Кратко:

```bash
# 1. Подготовить сервер
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3.10 python3.10-venv python3-pip git

# 2. Клонировать проект
cd ~
git clone <repo-url> automation-bot
cd automation-bot

# 3. Настроить окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 4. Создать .env
cp .env.example .env
nano .env  # заполнить данные

# 5. Создать директории
mkdir -p data logs backups

# 6. Тестовый запуск
python -m src.main

# 7. Настроить systemd (см. DEPLOYMENT.md)
sudo cp deploy/bot.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable bot.service
sudo systemctl start bot.service
```

---

## Получение BOT_TOKEN

1. Открыть Telegram
2. Найти @BotFather
3. Отправить `/newbot`
4. Следовать инструкциям
5. Скопировать токен

---

## Получение OPENAI_API_KEY

1. Зайти на https://platform.openai.com
2. Создать аккаунт
3. Перейти в API Keys
4. Создать новый ключ
5. Скопировать (покажется один раз!)

---

## Получение своего Telegram ID

1. Открыть Telegram
2. Найти @userinfobot
3. Отправить любое сообщение
4. Бот вернет ваш ID

---

## Проверка работы

После запуска бота:

1. Открыть Telegram
2. Найти вашего бота
3. Отправить `/start`
4. Должно появиться главное меню с кнопками

Если ошибки - проверить логи:
- Консоль
- Файл `logs/bot.log`
