import subprocess
import asyncio
import ctypes
import sys
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === НАСТРОЙКИ ===
BOT_TOKEN = "ВАШ_ТОКЕН_ОТ_BOTFATHER"
AUTHORIZED_USER_ID = 123456789            # Ваш Telegram ID

# === ПРОВЕРКА ПРАВ АДМИНИСТРАТОРА ===
def is_admin():
    """Возвращает True, если скрипт запущен от имени администратора."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

# === БЕЗОПАСНОСТЬ ===
def check_auth(update: Update) -> bool:
    return update.effective_user.id == AUTHORIZED_USER_ID

# === УНИВЕРСАЛЬНОЕ ВЫПОЛНЕНИЕ КОМАНД ===
def run_command(command: str, timeout: int = 30) -> str:
    """
    Выполняет команду:
    - если начинается с 'ps:', остальное выполняется в PowerShell
    - иначе выполняется cmd.exe /c
    Все процессы наследуют права текущего процесса (администратор или нет).
    Окна консоли не создаются.
    """
    try:
        if command.startswith("ps:"):
            ps_command = command[3:].strip()
            process = subprocess.run(
                ["powershell.exe", "-NoProfile", "-Command", ps_command],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
        else:
            process = subprocess.run(
                ["cmd.exe", "/c", command],
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
        output = process.stdout.strip() or process.stderr.strip()
        return output if output else "Команда выполнена (нет вывода)."
    except subprocess.TimeoutExpired:
        return "⚠️ Команда превысила лимит времени (30 с) и была прервана."
    except Exception as e:
        return f"❌ Ошибка выполнения: {e}"

# === АВТОПОДНЯТИЕ ПРАВ БЕЗ UAC (через планировщик) ===
TASK_NAME = "SecurityBotTask"

def create_scheduled_task_if_needed():
    """
    Если бот запущен elevated, создаёт (или обновляет) задание в Планировщике,
    которое будет запускать этот же скрипт с наивысшими правами при входе в систему.
    """
    if not is_admin():
        return False
    try:
        script_path = os.path.abspath(sys.argv[0])
        # Используем pythonw.exe, чтобы не было консольного окна
        pythonw_path = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw_path):
            pythonw_path = sys.executable  # fallback, если pythonw отсутствует

        # Команда для создания/обновления задания
        cmd = (
            f'schtasks /Create /SC ONLOGON /TN "{TASK_NAME}" /TR '
            f'"{pythonw_path} \\"{script_path}\\"" /RL HIGHEST /F'
        )
        subprocess.run(cmd, shell=True, capture_output=True, timeout=10)
        return True
    except Exception:
        return False

def run_as_scheduled_task():
    """Немедленно запускает задание планировщика (без UAC) и завершает текущий процесс."""
    try:
        subprocess.run(
            f'schtasks /Run /TN "{TASK_NAME}"',
            shell=True,
            capture_output=True,
            timeout=10
        )
    except Exception:
        pass
    sys.exit(0)

# === ОБРАБОТЧИКИ КОМАНД ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    admin_status = "✅ Права администратора" if is_admin() else "⚠️ Нет прав администратора"
    await update.message.reply_text(
        f"🛡 *Бот управления ПК*\n"
        f"Статус: {admin_status}\n\n"
        "Команды:\n"
        "/run `команда` — выполнить в cmd (по умолчанию)\n"
        "/run ps: `ps-команда` — выполнить в PowerShell\n"
        "/cmd `команда` — явно выполнить в cmd\n"
        "/firewall_on — включить брандмауэр\n"
        "/firewall_off — выключить брандмауэр\n"
        "/updates — установить обновления безопасности\n"
        "/integrity — проверить целостность системы (SFC)\n"
        "/defender_scan — быстрое сканирование Защитника\n"
        "/status — сводка состояния безопасности",
        parse_mode="Markdown"
    )

async def run_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        await update.message.reply_text("⛔ Доступ запрещён.")
        return
    if not context.args:
        await update.message.reply_text(
            "❌ Укажите команду.\nПримеры:\n`/run ipconfig`\n`/run ps: Get-Date`",
            parse_mode="Markdown"
        )
        return
    full_cmd = " ".join(context.args)
    await update.message.reply_text(f"⏳ Выполняю: `{full_cmd}`...", parse_mode="Markdown")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_command, full_cmd)
    if len(result) > 4000:
        result = result[:4000] + "\n... [обрезано]"
    await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")

async def cmd_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Явный вызов cmd (без префикса)"""
    if not check_auth(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Укажите команду. Пример: `/cmd dir`", parse_mode="Markdown")
        return
    full_cmd = " ".join(context.args)
    if full_cmd.startswith("ps:"):
        full_cmd = full_cmd[3:].strip()
    await update.message.reply_text(f"⏳ Выполняю (cmd): `{full_cmd}`...", parse_mode="Markdown")
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(None, run_command, full_cmd)
    if len(result) > 4000:
        result = result[:4000] + "\n... [обрезано]"
    await update.message.reply_text(f"```\n{result}\n```", parse_mode="Markdown")

async def firewall_on(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    cmd = "ps: Set-NetFirewallProfile -All -Enabled True"
    result = run_command(cmd)
    await update.message.reply_text(f"🔒 Брандмауэр включён:\n```\n{result}\n```", parse_mode="Markdown")

async def firewall_off(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    cmd = "ps: Set-NetFirewallProfile -All -Enabled False"
    result = run_command(cmd)
    await update.message.reply_text(f"⚠️ Брандмауэр ОТКЛЮЧЕН:\n```\n{result}\n```", parse_mode="Markdown")

async def install_updates(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    cmd = (
        "ps: if (Get-Module -ListAvailable -Name PSWindowsUpdate) { "
        "Install-WindowsUpdate -MicrosoftUpdate -AcceptAll -AutoReboot -Category 'Security Updates' "
        "} else { Write-Output 'PSWindowsUpdate не установлен. Установите: Install-Module PSWindowsUpdate' }"
    )
    result = run_command(cmd, timeout=120)
    await update.message.reply_text(f"📦 Обновления:\n```\n{result}\n```", parse_mode="Markdown")

async def system_integrity(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    await update.message.reply_text("🔍 Проверка целостности (SFC /scannow)...")
    result = run_command("sfc /scannow", timeout=600)
    await update.message.reply_text(f"📋 Результат SFC:\n```\n{result}\n```", parse_mode="Markdown")

async def defender_scan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    cmd = "ps: Start-MpScan -ScanType QuickScan"
    result = run_command(cmd, timeout=300)
    await update.message.reply_text(f"🦠 Быстрое сканирование Защитника:\n```\n{result}\n```", parse_mode="Markdown")

async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not check_auth(update):
        return
    fw = run_command("ps: Get-NetFirewallProfile | Select Name, Enabled | Format-Table -AutoSize")
    mp = run_command("ps: Get-MpComputerStatus | Select AntivirusEnabled, RealTimeProtectionEnabled | Format-List")
    status_text = f"📊 *Брандмауэр:*\n```\n{fw}\n```\n🛡 *Защитник:*\n```\n{mp}\n```"
    if len(status_text) > 4000:
        status_text = status_text[:4000] + "\n... [обрезано]"
    await update.message.reply_text(status_text, parse_mode="Markdown")

# === ЗАПУСК БОТА ===
def main():
    # Если бот уже запущен elevated, создаём задание и перезапускаемся через него
    if is_admin():
        print("✅ Обнаружены права администратора.")
        if create_scheduled_task_if_needed():
            print(f"📅 Задание '{TASK_NAME}' создано/обновлено. Перезапуск через планировщик для работы без UAC...")
            run_as_scheduled_task()
        else:
            print("⚠️ Не удалось создать задание планировщика. Продолжаю в текущем процессе (elevated).")
    else:
        # Без прав — инструкция
        print("❌ Бот не запущен от имени администратора!")
        print("   Для полноценной работы всех команд требуется запуск с elevated правами.")
        print("   Выполните следующие шаги ОДИН РАЗ:")
        print(f"   1. Запустите этот скрипт вручную от администратора (правый клик -> Запуск от имени администратора).")
        print(f"   2. Скрипт автоматически создаст задание в Планировщике '{TASK_NAME}' и перезапустится.")
        print("   3. В дальнейшем бот будет автоматически стартовать с elevated правами при входе в систему без UAC.")
        print("   Продолжаю без прав администратора (часть команд может не работать).")

    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("run", run_cmd))
    app.add_handler(CommandHandler("cmd", cmd_handler))
    app.add_handler(CommandHandler("firewall_on", firewall_on))
    app.add_handler(CommandHandler("firewall_off", firewall_off))
    app.add_handler(CommandHandler("updates", install_updates))
    app.add_handler(CommandHandler("integrity", system_integrity))
    app.add_handler(CommandHandler("defender_scan", defender_scan))
    app.add_handler(CommandHandler("status", status))

    print("🛡 Бот запущен. Ожидание команд...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()