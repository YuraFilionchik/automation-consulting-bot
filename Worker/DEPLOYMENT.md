# 🚀 Пошаговый деплой на Linux сервер

## Требования к серверу

- **OS**: Ubuntu 22.04 LTS
- **CPU**: 1+ ядро
- **RAM**: 512MB+ (рекомендуется 1GB)
- **Disk**: 10GB+
- **Доступ**: SSH с root или sudo

---

## Шаг 1: Подготовка сервера

```bash
# Подключение к серверу
ssh user@your-server-ip

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y python3.10 python3.10-venv python3-pip git curl

# Проверка версий
python3 --version  # Должно быть 3.10+
git --version
```

---

## Шаг 2: Создание пользователя для бота

```bash
# Создать системного пользователя
sudo useradd -m -s /bin/bash botuser

# Переключиться
sudo su - botuser
```

---

## Шаг 3: Клонирование проекта

```bash
# Клонировать репозиторий
cd ~
git clone <your-repo-url> automation-bot
cd automation-bot

# Или скопировать файлы вручную
mkdir -p automation-bot
# ... скопировать файлы ...
cd automation-bot
```

---

## Шаг 4: Настройка окружения

```bash
# Создать виртуальное окружение
python3 -m venv venv

# Активировать
source venv/bin/activate

# Установить зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Создать .env файл
cp .env.example .env
nano .env

# Заполнить переменные:
# BOT_TOKEN=your_telegram_bot_token
# OPENAI_API_KEY=your_openai_key
# ADMIN_IDS=123456789,987654321
# LOG_LEVEL=INFO
```

---

## Шаг 5: Создание директорий

```bash
# Создать необходимые директории
mkdir -p data
mkdir -p logs
mkdir -p backups

# Права доступа
chmod 755 data
chmod 755 logs
```

---

## Шаг 6: Тестовый запуск

```bash
# Активировать venv (если не активирован)
source ~/automation-bot/venv/bin/activate

# Запустить бота
cd ~/automation-bot
python -m src.main

# Должно появиться:
# [INFO] Bot started successfully
# [INFO] Bot ID: @your_bot_name
```

**Остановить**: `Ctrl+C`

---

## Шаг 7: Настройка systemd сервиса

```bash
# Выйти из-под botuser
exit

# Создать сервис (от root или через sudo)
sudo nano /etc/systemd/system/bot.service
```

**Содержимое `bot.service`:**

```ini
[Unit]
Description=Automation Consulting Telegram Bot
After=network.target

[Service]
Type=simple
User=botuser
Group=botuser
WorkingDirectory=/home/botuser/automation-bot
ExecStart=/home/botuser/automation-bot/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=append:/home/botuser/automation-bot/logs/bot.log
StandardError=append:/home/botuser/automation-bot/logs/bot-error.log

# Перезапуск каждую ночь (освобождение памяти)
RuntimeMaxSec=86400

[Install]
WantedBy=multi-user.target
```

**Активация сервиса:**

```bash
# Перезагрузить systemd
sudo systemctl daemon-reload

# Включить автозапуск
sudo systemctl enable bot.service

# Запустить бота
sudo systemctl start bot.service

# Проверить статус
sudo systemctl status bot.service

# Посмотреть логи
sudo journalctl -u bot.service -f
```

---

## Шаг 8: Настройка логирования

```bash
# Создать конфигурацию logrotate
sudo nano /etc/logrotate.d/bot
```

**Содержимое:**

```
/home/botuser/automation-bot/logs/*.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
    create 0644 botuser botuser
    sharedscripts
    postrotate
        systemctl restart bot.service
    endscript
}
```

---

## Шаг 9: Настройка бэкапов

```bash
# Создать скрипт бэкапа
sudo nano /opt/backup-bot.sh
```

**Содержимое:**

```bash
#!/bin/bash
BACKUP_DIR="/opt/bot-backups"
DB_FILE="/home/botuser/automation-bot/data/bot.db"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")

mkdir -p $BACKUP_DIR

if [ -f "$DB_FILE" ]; then
    cp $DB_FILE "$BACKUP_DIR/bot_$TIMESTAMP.db"
    echo "Backup created: bot_$TIMESTAMP.db"
    
    # Удалить старше 30 дней
    find $BACKUP_DIR -name "bot_*.db" -mtime +30 -delete
else
    echo "Database file not found!"
fi
```

**Настроить крон:**

```bash
sudo chmod +x /opt/backup-bot.sh
sudo crontab -e

# Добавить строку (бэкап каждый день в 3:00)
0 3 * * * /opt/backup-bot.sh >> /var/log/bot-backup.log 2>&1
```

---

## Шаг 10: Мониторинг

### Проверка что бот работает

```bash
# Статус сервиса
sudo systemctl status bot.service

# Логи в реальном времени
sudo journalctl -u bot.service -f

# Потребление памяти
ps aux | grep python
```

### (Опционально) Healthcheck endpoint

Можно добавить простую проверку:

```bash
# В коде бота добавить команду /ping
# Тогда проверить можно так:
# Отправить боту /ping через telegram
```

---

## Команды управления

```bash
# Статус
sudo systemctl status bot.service

# Остановить
sudo systemctl stop bot.service

# Запустить
sudo systemctl start bot.service

# Перезапустить
sudo systemctl restart bot.service

# Логи
sudo journalctl -u bot.service -n 100  # Последние 100 строк
sudo journalctl -u bot.service -f      # В реальном времени

# Перезагрузить сервис после изменений
sudo systemctl daemon-reload
sudo systemctl restart bot.service
```

---

## Troubleshooting

### Бот не запускается

```bash
# Проверить логи
sudo journalctl -u bot.service -n 50

# Проверить что порт свободен
sudo lsof -i :80 # или другой порт

# Проверить права
ls -la /home/botuser/automation-bot
```

### Бот падает периодически

```bash
# Проверить память
free -h

# Проверить логи ошибок
cat /home/botuser/automation-bot/logs/bot-error.log

# Увеличить RestartSec в bot.service если нужно
```

### Обновление кода

```bash
# Зайти под botuser
sudo su - botuser

# Обновить код
cd ~/automation-bot
git pull

# Обновить зависимости
source venv/bin/activate
pip install -r requirements.txt

# Перезапустить сервис
exit
sudo systemctl restart bot.service
```

---

## (Опционально) Настройка через Webhook

Для Telegram можно использовать polling (по умолчанию) или webhook.

**Polling** (рекомендуется для малых серверов):
- Уже работает по умолчанию
- Не требует открытых портов
- Меньше ресурсов

**Webhook** (для больших нагрузок):
- Требует HTTPS и домен
- Быстрее доставка сообщений
- Сложнее настройка

Если нужен webhook - раскомментируйте в коде и настройте nginx.
