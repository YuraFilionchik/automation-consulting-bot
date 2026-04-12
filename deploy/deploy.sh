#!/bin/bash
set -e

echo "=================================================="
echo "  Automation Consulting Bot - Deploy Script"
echo "=================================================="

# Проверка от root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

PROJECT_DIR="/opt/automation-bot"

# 1. Обновить систему
echo ""
echo "[1/8] Updating system..."
apt update -y && apt upgrade -y

# 2. Установить Python и зависимости
echo "[2/8] Installing Python and dependencies..."
apt install -y python3 python3-venv python3-pip git curl screen

python3 --version
echo "Python installed."

# 3. Создать директорию проекта
echo "[3/8] Creating project directory..."
mkdir -p $PROJECT_DIR
cd $PROJECT_DIR

# 4. Клонировать или скопировать файлы
echo "[4/8] Setting up project files..."

# Проверяем есть ли git репозиторий
if [ -d "/tmp/project-files" ]; then
    echo "Copying from local files..."
    cp -r /tmp/project-files/* $PROJECT_DIR/
else
    echo "No local files found, please upload manually."
fi

# 5. Создать виртуальное окружение
echo "[5/8] Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip

# 6. Установить зависимости
echo "[6/8] Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
    echo "Dependencies installed."
else
    echo "ERROR: requirements.txt not found!"
    exit 1
fi

# 7. Создать директории данных
echo "[7/8] Creating data directories..."
mkdir -p data logs backups

# 8. Создать systemd сервис
echo "[8/8] Creating systemd service..."
cat > /etc/systemd/system/automation-bot.service << 'EOF'
[Unit]
Description=Automation Consulting Telegram Bot
After=network.target

[Service]
Type=simple
WorkingDirectory=/opt/automation-bot
ExecStart=/opt/automation-bot/venv/bin/python -m src.main
Restart=always
RestartSec=10
StandardOutput=append:/opt/automation-bot/logs/bot.log
StandardError=append:/opt/automation-bot/logs/bot-error.log
RuntimeMaxSec=86400

[Install]
WantedBy=multi-user.target
EOF

systemctl daemon-reload
systemctl enable automation-bot.service
systemctl restart automation-bot.service

echo ""
echo "=================================================="
echo "  ✅ Deployment complete!"
echo "=================================================="
echo ""
echo "Check status:  systemctl status automation-bot.service"
echo "View logs:     journalctl -u automation-bot.service -f"
echo "Stop:          systemctl stop automation-bot.service"
echo "Start:         systemctl start automation-bot.service"
echo ""

# Показать статус
sleep 2
systemctl status automation-bot.service --no-pager -l
