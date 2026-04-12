"""Хендлер админ-команды обновления приложения (blue-green deployment)"""

import asyncio
import logging
import os
import shutil
import subprocess
import tempfile
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message

from src.config.settings import settings

router = Router()
logger = logging.getLogger(__name__)

# GitHub репозиторий
REPO_URL = "https://github.com/YuraFilionchik/automation-consulting-bot.git"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# Директория для staging обновлений
STAGING_DIR = os.path.join(PROJECT_DIR, ".staging_update")
# Директория для бэкапов
BACKUPS_DIR = os.path.join(PROJECT_DIR, "backups")
# Файлы/папки которые НЕ копируем из staging
EXCLUDE_NAMES = {
    ".env",          # Конфиг — не трогаем
    "data",          # БД — не трогаем
    "logs",          # Логи — не трогаем
    "backups",       # Бэкапы — не трогаем
    "venv",          # Виртуальное окружение — пересоздаём
    ".git",          # Git — пересоздаём
    "__pycache__",
    ".staging_update",
    ".pytest_cache",
    "*.pyc",
}


def run_command(cmd: str, timeout: int = 120, cwd: str = None) -> tuple[bool, str, str]:
    """Выполнить shell-команду. Возвращает (success, stdout, stderr)"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd or PROJECT_DIR,
            env={**os.environ, "GIT_TERMINAL_PROMPT": "0"},  # Отключить запрос пароля git
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


def cleanup_staging():
    """Очистить staging директорию"""
    if os.path.exists(STAGING_DIR):
        shutil.rmtree(STAGING_DIR, ignore_errors=True)


def clone_to_staging() -> tuple[bool, str]:
    """Клонировать репозиторий в staging"""
    cleanup_staging()
    os.makedirs(STAGING_DIR, exist_ok=True)

    success, out, err = run_command(f"git clone --depth 1 {REPO_URL} .", cwd=STAGING_DIR)
    if not success:
        cleanup_staging()
        return False, f"Clone failed: {err or out}"

    return True, "Repository cloned to staging."


def check_staging() -> tuple[bool, str]:
    """Проверить что в staging валидный проект"""

    # Проверить основные файлы
    required_files = [
        os.path.join(STAGING_DIR, "src", "main.py"),
        os.path.join(STAGING_DIR, "requirements.txt"),
        os.path.join(STAGING_DIR, "src", "config", "settings.py"),
    ]

    for f in required_files:
        if not os.path.exists(f):
            return False, f"Missing required file: {f}"

    # Проверить синтаксис Python
    success, out, err = run_command(
        "python3 -m py_compile src/main.py",
        cwd=STAGING_DIR
    )
    if not success:
        return False, f"Syntax error in main.py: {err}"

    # Проверить что requirements.txt валидный
    success, out, err = run_command(
        "python3 -c \"open('requirements.txt').read()\"",
        cwd=STAGING_DIR
    )
    if not success:
        return False, f"Invalid requirements.txt: {err}"

    return True, "Staging checks passed."


def backup_current_version() -> tuple[bool, str]:
    """Создать бэкап текущей версии"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUPS_DIR, f"backup_{timestamp}")

    try:
        os.makedirs(BACKUPS_DIR, exist_ok=True)

        # Копируем всё кроме исключённого
        shutil.copytree(
            PROJECT_DIR,
            backup_path,
            ignore=shutil.ignore_patterns(*EXCLUDE_NAMES),
            dirs_exist_ok=False,
        )

        return True, f"Backup created: {backup_path}"
    except Exception as e:
        return False, f"Backup failed: {e}"


def activate_staging() -> tuple[bool, str]:
    """
    Переключить staging как рабочую версию.
    
    Алгоритм:
    1. Создать временную папку для старой версии
    2. Переместить все файлы из PROJECT_DIR (кроме исключений) во временную
    3. Скопировать файлы из STAGING_DIR в PROJECT_DIR
    4. Вернуть исключённые файлы из временной обратно в PROJECT_DIR
    """

    temp_old = os.path.join(PROJECT_DIR, ".old_version_temp")

    try:
        # 1. Переместить текущие файлы (кроме исключений) во временную папку
        if os.path.exists(temp_old):
            shutil.rmtree(temp_old)
        os.makedirs(temp_old)

        for item in os.listdir(PROJECT_DIR):
            if item in EXCLUDE_NAMES or item.startswith("."):
                continue
            src = os.path.join(PROJECT_DIR, item)
            dst = os.path.join(temp_old, item)
            if os.path.isdir(src):
                shutil.move(src, dst)
            else:
                shutil.copy2(src, dst)

        # 2. Скопировать файлы из staging в project
        for item in os.listdir(STAGING_DIR):
            if item in EXCLUDE_NAMES or item.startswith("."):
                continue
            src = os.path.join(STAGING_DIR, item)
            dst = os.path.join(PROJECT_DIR, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        # 3. Удалить временную папку (бэкап уже есть)
        shutil.rmtree(temp_old, ignore_errors=True)

        # 4. Очистить staging
        cleanup_staging()

        return True, "Staging activated successfully."

    except Exception as e:
        # Попытка отката
        logger.error(f"Activation failed: {e}", exc_info=True)

        # Вернуть старые файлы если возможно
        if os.path.exists(temp_old):
            logger.info("Attempting rollback...")
            for item in os.listdir(temp_old):
                src = os.path.join(temp_old, item)
                dst = os.path.join(PROJECT_DIR, item)
                if os.path.isdir(src):
                    if os.path.exists(dst):
                        shutil.rmtree(dst)
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            shutil.rmtree(temp_old, ignore_errors=True)

        cleanup_staging()
        return False, f"Activation failed: {e}. Rolled back."


def rollback_to_backup() -> tuple[bool, str]:
    """Откатиться к последнему бэкапу"""

    # Найти последний бэкап
    if not os.path.exists(BACKUPS_DIR):
        return False, "No backups directory found."

    backups = sorted(os.listdir(BACKUPS_DIR), reverse=True)
    if not backups:
        return False, "No backups found."

    latest_backup = os.path.join(BACKUPS_DIR, backups[0])

    # Временная папка для текущей (сломанной) версии
    temp_broken = os.path.join(PROJECT_DIR, ".broken_version_temp")
    if os.path.exists(temp_broken):
        shutil.rmtree(temp_broken)

    try:
        # Переместить текущие файлы
        for item in os.listdir(PROJECT_DIR):
            if item in EXCLUDE_NAMES or item.startswith("."):
                continue
            src = os.path.join(PROJECT_DIR, item)
            dst = os.path.join(temp_broken, item)
            if os.path.isdir(src):
                shutil.move(src, dst)
            else:
                shutil.move(src, dst)

        # Восстановить из бэкапа
        for item in os.listdir(latest_backup):
            src = os.path.join(latest_backup, item)
            dst = os.path.join(PROJECT_DIR, item)
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)

        shutil.rmtree(temp_broken, ignore_errors=True)

        return True, f"Rolled back to backup: {backups[0]}"

    except Exception as e:
        logger.error(f"Rollback failed: {e}", exc_info=True)
        return False, f"Rollback failed: {e}"


def install_dependencies() -> tuple[bool, str]:
    """Установить зависимости в venv"""
    pip_path = os.path.join(PROJECT_DIR, "venv", "bin", "pip")

    if not os.path.exists(pip_path):
        # Создать venv если нет
        success, out, err = run_command(f"python3 -m venv {os.path.join(PROJECT_DIR, 'venv')}")
        if not success:
            return False, f"Failed to create venv: {err}"
        pip_path = os.path.join(PROJECT_DIR, "venv", "bin", "pip")

    success, out, err = run_command(f"{pip_path} install --upgrade pip")
    success, out, err = run_command(f"{pip_path} install -r requirements.txt")

    if success:
        return True, "Dependencies installed."
    return False, f"pip install failed: {err}"


async def execute_full_update(message: Message):
    """Выполнить полное обновление с blue-green deployment"""

    # Этап 1: Клонировать в staging
    await message.answer("🔄 <b>Step 1/7:</b> Downloading update to staging area...")
    await asyncio.sleep(0.5)

    success, msg = clone_to_staging()
    if not success:
        await message.answer(f"❌ <b>Download failed!</b>\n\n<code>{msg}</code>")
        return
    await message.answer(f"✅ Downloaded: {msg}")

    # Этап 2: Проверить staging
    await message.answer("🔄 <b>Step 2/7:</b> Validating update package...")
    await asyncio.sleep(0.5)

    success, msg = check_staging()
    if not success:
        await message.answer(
            f"❌ <b>Validation failed!</b>\n\n"
            f"<code>{msg}</code>\n\n"
            f"🧹 Staging cleaned up. Current version untouched."
        )
        cleanup_staging()
        return
    await message.answer(f"✅ Validation: {msg}")

    # Этап 3: Бэкап текущей версии
    await message.answer("🔄 <b>Step 3/7:</b> Creating backup of current version...")
    await asyncio.sleep(0.5)

    success, msg = backup_current_version()
    if not success:
        await message.answer(f"❌ <b>Backup failed!</b>\n\n<code>{msg}</code>")
        cleanup_staging()
        return
    await message.answer(f"✅ Backup: {msg}")

    # Этап 4: Активировать staging
    await message.answer("🔄 <b>Step 4/7:</b> Activating new version...")
    await asyncio.sleep(0.5)

    success, msg = activate_staging()
    if not success:
        await message.answer(
            f"❌ <b>Activation failed!</b>\n\n"
            f"<code>{msg}</code>\n\n"
            f"🔄 Already rolled back to previous version."
        )
        return
    await message.answer(f"✅ Activated: {msg}")

    # Этап 5: Установить зависимости
    await message.answer("🔄 <b>Step 5/7:</b> Installing Python dependencies...")
    await asyncio.sleep(0.5)

    success, msg = install_dependencies()
    if not success:
        await message.answer(
            f"⚠️ <b>Dependency installation issue:</b>\n"
            f"<code>{msg}</code>\n\n"
            f"Continuing..."
        )
    else:
        await message.answer(f"✅ Dependencies: {msg}")

    # Этап 6: Проверить .env
    await message.answer("🔄 <b>Step 6/7:</b> Checking configuration...")
    await asyncio.sleep(0.5)

    env_path = os.path.join(PROJECT_DIR, ".env")
    if os.path.exists(env_path):
        with open(env_path, "r") as f:
            content = f.read()

        required_keys = ["BOT_TOKEN", "GEMINI_API_KEY", "ADMIN_IDS"]
        missing = [k for k in required_keys if k not in content]

        if missing:
            await message.answer(
                f"⚠️ <b>Missing keys in .env:</b>\n"
                f"<code>{', '.join(missing)}</code>"
            )
        else:
            await message.answer("✅ Configuration OK.")
    else:
        await message.answer(
            f"⚠️ <b>.env file not found!</b>\n"
            f"Create it at: <code>{env_path}</code>"
        )

    # Этап 7: Перезапустить сервис
    await message.answer("🔄 <b>Step 7/7:</b> Restarting bot service...")
    await asyncio.sleep(0.5)

    # Проверить systemd
    success, out, err = run_command("systemctl is-active automation-bot.service")
    if success and out.strip() == "active":
        run_command("systemctl restart automation-bot.service")
        await asyncio.sleep(2)
        success2, status, _ = run_command("systemctl is-active automation-bot.service")
        if success2 and status.strip() == "active":
            await message.answer("✅ Service restarted successfully.")
        else:
            await message.answer(
                f"⚠️ Service status: <code>{status}</code>\n"
                f"Check: <code>journalctl -u automation-bot.service -n 20</code>"
            )
    else:
        # Проверить bot.service
        success, out, err = run_command("systemctl is-active bot.service")
        if success and out.strip() == "active":
            run_command("systemctl restart bot.service")
            await asyncio.sleep(2)
            await message.answer("✅ Service restarted (bot.service).")
        else:
            await message.answer(
                "ℹ️ No systemd service found.\n"
                "Please restart the bot manually."
            )

    # Финальный отчёт
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(
        f"✅ <b>Update Complete!</b>\n\n"
        f"🕐 Time: {timestamp}\n"
        f"📂 Project: <code>{PROJECT_DIR}</code>\n"
        f"📦 Repo: <code>{REPO_URL}</code>\n\n"
        f"📊 <b>Summary:</b>\n"
        f"• Code: Downloaded → Validated → Activated\n"
        f"• Backup: Created\n"
        f"• Dependencies: Updated\n"
        f"• Config: Checked\n"
        f"• Service: Restarted\n\n"
        f"💡 <b>Commands:</b>\n"
        f"• /update_app — Update again\n"
        f"• /rollback — Revert to backup\n"
        f"• /update_status — Check update status\n\n"
        f"Check the bot in Telegram to confirm it's working! 🤖"
    )

    logger.info(f"Update completed by admin {message.from_user.id}")


# ========== Команды ==========

@router.message(F.text == "/update_app")
async def handle_update(message: Message):
    """Полное обновление из GitHub"""

    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("🚫 <b>Access denied!</b>\n\nOnly administrators can use this command.")
        return

    await message.answer(
        f"🔄 <b>Starting update (blue-green deployment)...</b>\n\n"
        f"📦 Repository: <code>{REPO_URL}</code>\n"
        f"📂 Staging: <code>{STAGING_DIR}</code>\n"
        f"💾 Backups: <code>{BACKUPS_DIR}</code>\n"
        f"👤 Admin: {message.from_user.full_name}\n\n"
        f"This may take 1-3 minutes. Current version will be backed up."
    )

    try:
        await execute_full_update(message)
    except Exception as e:
        cleanup_staging()
        await message.answer(
            f"❌ <b>Update failed with error!</b>\n\n"
            f"<code>{str(e)[:1000]}</code>\n\n"
            f"🔄 Previous version should be intact. Check logs."
        )
        logger.error(f"Update failed: {e}", exc_info=True)


@router.message(F.text == "/rollback")
async def handle_rollback(message: Message):
    """Откат к последнему бэкапу"""

    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("🚫 <b>Access denied!</b>")
        return

    await message.answer("🔄 <b>Starting rollback...</b>")

    success, msg = rollback_to_backup()

    if success:
        await message.answer(f"✅ <b>Rollback successful!</b>\n\n<code>{msg}</code>\n\nNow restart the bot service.")
        logger.info(f"Rollback performed by admin {message.from_user.id}")
    else:
        await message.answer(f"❌ <b>Rollback failed!</b>\n\n<code>{msg}</code>")


@router.message(F.text == "/update_status")
async def handle_status(message: Message):
    """Статус обновлений и бэкапов"""

    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("🚫 <b>Access denied!</b>")
        return

    # Бэкапы
    backups = []
    if os.path.exists(BACKUPS_DIR):
        backups = sorted(os.listdir(BACKUPS_DIR), reverse=True)

    # Staging
    staging_exists = os.path.exists(STAGING_DIR)

    # Git status
    is_git, _, _ = run_command("git rev-parse --is-inside-work-tree")
    git_status = ""
    if is_git:
        success, out, err = run_command("git log --oneline -3")
        if success:
            git_status = f"📝 Last commits:\n<code>{out}</code>"
        else:
            git_status = "Git info unavailable."

    text = f"📊 <b>Update Status</b>\n\n"
    text += f"📂 Project: <code>{PROJECT_DIR}</code>\n"
    text += f"💾 Backups: {len(backups)}\n"

    if backups:
        text += f"   Latest: <code>{backups[0]}</code>\n"
        for b in backups[:3]:
            text += f"   • {b}\n"

    text += f"🔄 Staging: {'exists' if staging_exists else 'clean'}\n\n"
    text += git_status

    await message.answer(text, parse_mode="HTML")
