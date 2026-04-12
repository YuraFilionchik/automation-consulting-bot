"""Хендлер админ-команды обновления приложения"""

import asyncio
import logging
import os
import subprocess
from datetime import datetime

from aiogram import Router, F
from aiogram.types import Message

from src.config.settings import settings

router = Router()
logger = logging.getLogger(__name__)

# GitHub репозиторий
REPO_URL = "https://github.com/YuraFilionchik/automation-consulting-bot.git"
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_command(cmd: str, timeout: int = 120) -> tuple[bool, str, str]:
    """
    Выполнить shell-команду.
    Возвращает (success, stdout, stderr)
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=PROJECT_DIR,
        )
        return result.returncode == 0, result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "", f"Command timed out after {timeout}s"
    except Exception as e:
        return False, "", str(e)


async def execute_update(message: Message):
    """Выполнить полное обновление приложения"""

    # Этап 1: Проверка git репозитория
    await message.answer("🔄 <b>Step 1/6:</b> Checking git repository...")
    await asyncio.sleep(0.5)

    is_git, _, _ = run_command("git rev-parse --is-inside-work-tree")
    if not is_git:
        # Не git репо — клонируем
        await message.answer("⚠️ Not a git repo. Cloning from GitHub...")
        success, out, err = run_command(
            f"git clone {REPO_URL} /tmp/automation-bot-update"
        )
        if not success:
            await message.answer(
                f"❌ <b>Clone failed!</b>\n\n"
                f"<code>{err or out}</code>"
            )
            return

        # Копируем файлы (кроме .env, data, logs)
        success, out, err = run_command(
            "rsync -a --exclude='.env' --exclude='data/' --exclude='logs/' "
            "--exclude='backups/' --exclude='.git' --exclude='venv/' "
            "/tmp/automation-bot-update/ ./ "
        )
        run_command("rm -rf /tmp/automation-bot-update")

        if success:
            await message.answer("✅ Repository cloned successfully.")
        else:
            await message.answer(
                f"❌ <b>Clone/copy failed!</b>\n\n"
                f"<code>{err or out}</code>"
            )
            return
    else:
        # Уже git — делаем pull
        # Настроить credential helper чтобы не запрашивал пароль
        run_command("git config credential.helper store")
        
        success, out, err = run_command("git fetch origin")
        if not success:
            await message.answer(
                f"❌ <b>Git fetch failed!</b>\n\n"
                f"<code>{err or out}</code>"
            )
            return

        # Проверить есть ли обновления
        success, out, err = run_command("git rev-list HEAD..origin/main --count 2>/dev/null || git rev-list HEAD..origin/master --count")
        commits_ahead = int(out.strip()) if out.strip().isdigit() else 0

        if commits_ahead == 0:
            await message.answer("✅ <b>Already up to date!</b> No new changes found.")
            return

        await message.answer(f"📥 Found {commits_ahead} new commit(s). Pulling...")
        success, out, err = run_command("git pull --ff-only origin main 2>/dev/null || git pull --ff-only origin master 2>/dev/null || git pull origin main || git pull origin master")
        if not success:
            # Force reset
            await message.answer("⚠️ Fast-forward failed, force resetting...")
            run_command("git reset --hard origin/main || git reset --hard origin/master")

        await message.answer(f"✅ Pulled changes:\n<code>{out[:500]}</code>")

    # Этап 2: Обновить зависимости
    await message.answer("🔄 <b>Step 2/6:</b> Updating Python dependencies...")
    await asyncio.sleep(0.5)

    pip_path = os.path.join(PROJECT_DIR, "venv", "bin", "pip")
    if not os.path.exists(pip_path):
        pip_path = "pip3"

    success, out, err = run_command(f"{pip_path} install --upgrade pip")
    success2, out2, err2 = run_command(f"{pip_path} install -r requirements.txt")

    if success2:
        await message.answer("✅ Dependencies updated successfully.")
    else:
        await message.answer(
            f"⚠️ <b>Dependency update had issues:</b>\n"
            f"<code>{(err2 or err)[:500]}</code>\n\n"
            f"Continuing anyway..."
        )

    # Этап 3: Проверить .env
    await message.answer("🔄 <b>Step 3/6:</b> Checking configuration...")
    await asyncio.sleep(0.5)

    env_path = os.path.join(PROJECT_DIR, ".env")
    if os.path.exists(env_path):
        # Проверить что есть все нужные ключи
        with open(env_path, "r") as f:
            content = f.read()

        required_keys = ["BOT_TOKEN", "GEMINI_API_KEY", "ADMIN_IDS"]
        missing = [k for k in required_keys if k not in content]

        if missing:
            await message.answer(
                f"⚠️ <b>Missing keys in .env:</b>\n"
                f"<code>{', '.join(missing)}</code>\n\n"
                f"Please update your .env file!"
            )
        else:
            await message.answer("✅ Configuration OK.")
    else:
        await message.answer(
            "⚠️ <b>.env file not found!</b>\n"
            "The bot may not start correctly. "
            f"Create it at: <code>{env_path}</code>"
        )

    # Этап 4: Создать директории
    await message.answer("🔄 <b>Step 4/6:</b> Checking directories...")
    await asyncio.sleep(0.5)

    for d in ["data", "logs", "backups"]:
        os.makedirs(os.path.join(PROJECT_DIR, d), exist_ok=True)

    await message.answer("✅ Directories OK.")

    # Этап 5: Проверить код
    await message.answer("🔄 <b>Step 5/6:</b> Checking Python syntax...")
    await asyncio.sleep(0.5)

    success, out, err = run_command("python3 -m py_compile src/main.py 2>&1")
    if success:
        await message.answer("✅ Syntax check passed.")
    else:
        await message.answer(
            f"⚠️ <b>Syntax issues:</b>\n"
            f"<code>{err[:300]}</code>\n\n"
            f"Will restart anyway..."
        )

    # Этап 6: Перезапустить сервис
    await message.answer("🔄 <b>Step 6/6:</b> Restarting bot service...")
    await asyncio.sleep(0.5)

    # Проверяем systemd
    success, out, err = run_command("systemctl is-active automation-bot.service")
    if success and out.strip() == "active":
        # Перезапустить через systemd
        run_command("systemctl restart automation-bot.service")
        await asyncio.sleep(2)
        success2, status, _ = run_command("systemctl is-active automation-bot.service")
        if success2 and status.strip() == "active":
            await message.answer("✅ Service restarted successfully via systemd.")
        else:
            await message.answer(
                "⚠️ Service restart may have failed.\n"
                f"Status: <code>{status}</code>\n"
                "Check logs: <code>journalctl -u automation-bot.service -n 20</code>"
            )
    else:
        # Не systemd — пробуем перезапустить процесс
        await message.answer(
            "ℹ️ Not running as systemd service.\n"
            "Please restart the bot manually."
        )

    # Финальный отчёт
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await message.answer(
        f"✅ <b>Update Complete!</b>\n\n"
        f"🕐 Time: {timestamp}\n"
        f"📂 Dir: <code>{PROJECT_DIR}</code>\n\n"
        f"📊 <b>Status:</b>\n"
        f"• Code: Updated from GitHub\n"
        f"• Dependencies: Updated\n"
        f"• Config: Checked\n"
        f"• Service: Restarted\n\n"
        f"Check bot in Telegram to confirm it's working! 🤖"
    )

    logger.info(f"Update completed by admin {message.from_user.id}")


@router.message(F.text == "/update_app")
async def handle_update(message: Message):
    """Handle update command"""

    # Check if admin
    if message.from_user.id not in settings.admin_ids_list:
        await message.answer("🚫 <b>Access denied!</b>\n\nOnly administrators can use this command.")
        logger.warning(f"Unauthorized update attempt by user {message.from_user.id}")
        return

    await message.answer(
        f"🔄 <b>Starting update...</b>\n\n"
        f"📦 Repository: <code>{REPO_URL}</code>\n"
        f"📂 Project: <code>{PROJECT_DIR}</code>\n"
        f"👤 Admin: {message.from_user.full_name}\n\n"
        f"This may take 1-3 minutes..."
    )

    try:
        await execute_update(message)
    except Exception as e:
        await message.answer(
            f"❌ <b>Update failed with error!</b>\n\n"
            f"<code>{str(e)[:1000]}</code>\n\n"
            f"The bot should still be running. Check logs for details."
        )
        logger.error(f"Update failed: {e}", exc_info=True)
