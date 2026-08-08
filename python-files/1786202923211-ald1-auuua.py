import hashlib
import sys
import threading
import tkinter as tk
from tkinter import font, messagebox

if sys.platform == "win32":
    import ctypes
    import winsound


class UltimatePrank(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("System Critical Lockdown")
        self.attributes("-fullscreen", True)
        self.attributes("-topmost", True)

        # Полное скрытие курсора мыши
        self.configure(cursor="none")

        # Отключение закрытия окна через Alt+F4 или крестик
        self.protocol("WM_DELETE_WINDOW", lambda: None)

        # Карта заблокированных клавиш для вывода предупреждений
        self.blocked_keys = {
            "Escape": "Esc",
            "Shift_L": "Shift",
            "Shift_R": "Shift",
            "Control_L": "Ctrl",
            "Control_R": "Ctrl",
            "Alt_L": "Alt",
            "Alt_R": "Alt",
            "Tab": "Tab",
            "Win_L": "Win",
            "Win_R": "Win",
        }

        # Привязка заблокированных клавиш
        for key in self.blocked_keys:
            self.bind(f"<KeyPress-{key}>", self.key_pressed_warning)

        # Перехват Ctrl + Shift + Esc
        self.bind("<Control-Shift-Escape>", self.fake_task_manager_block)

        # Скрытие панели задач
        self.hide_taskbar()

        # Установка громкости на максимум при старте
        self.set_max_volume()

        # Правильный пароль
        self.correct_password = "810624"
        self.correct_hash = hashlib.sha256(
            self.correct_password.encode("utf-8")
        ).hexdigest()

        self.attempts_left = 3

        # 6 часов в секундах (6 * 60 * 60 = 21600)
        self.seconds_left = 21600

        self.countdown_job = None
        self.blink_job = None
        self.typing_job = None
        self.blink_state = False

        self.global_timer_tick()
        self.setup_boot_screen()

    def key_pressed_warning(self, event):
        """Обработка нажатия заблокированных клавиш с показом сообщения."""
        key_name = self.blocked_keys.get(event.keysym, event.keysym)
        messagebox.showwarning(
            "Доступ запрещён",
            f"Клавиша {key_name} недоступна!"
        )
        return "break"

    def fake_task_manager_block(self, event=None):
        """Имитация блокировки Диспетчера задач."""
        messagebox.showwarning(
            "Предупреждение системы",
            "Диспетчер задач заблокирован администратором!"
        )
        return "break"

    def set_max_volume(self):
        """Принудительно устанавливает громкость Windows на 100%."""
        if sys.platform == "win32":
            try:
                # 0xFFFFFFFF выставляет максимальный уровень звука для всех каналов
                ctypes.windll.winmm.waveOutSetVolume(0, 0xFFFFFFFF)
            except Exception:
                pass

    def play_sound_async(self, sound_type):
        """Запуск генерации страшных звуков с постоянным сбросом громкости на максимум."""
        threading.Thread(target=self._generate_scary_audio, args=(sound_type,), daemon=True).start()

    def _generate_scary_audio(self, sound_type):
        """Генерация звуков через winsound с зафиксированной максимальной громкостью."""
        if sys.platform != "win32":
            return

        self.set_max_volume()

        try:
            if sound_type == "boot":
                # Низкочастотный гул
                for _ in range(2):
                    self.set_max_volume()
                    winsound.Beep(150, 150)
                    winsound.Beep(120, 200)
            elif sound_type == "scare":
                # Резкий сигнал
                for freq in [800, 200, 900, 180]:
                    self.set_max_volume()
                    winsound.Beep(freq, 100)
            elif sound_type == "lock":
                # Пульсирующая сирена
                for _ in range(2):
                    self.set_max_volume()
                    winsound.Beep(400, 120)
                    winsound.Beep(800, 120)
            elif sound_type == "wrong_code_scream":
                # ОЧЕНЬ ГРОМКИЙ РЕЗКИЙ ВИЗГ/СИРЕНА при ошибке
                for _ in range(6):
                    self.set_max_volume()
                    winsound.Beep(2500, 80)
                    winsound.Beep(3500, 80)
                    winsound.Beep(1500, 100)
                    winsound.Beep(4000, 120)
        except Exception:
            pass

    def hide_taskbar(self):
        """Скрывает панель задач Windows."""
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 0)
            except Exception:
                pass

    def show_taskbar(self):
        """Возвращает панель задач обратно."""
        if sys.platform == "win32":
            try:
                hwnd = ctypes.windll.user32.FindWindowW("Shell_TrayWnd", None)
                if hwnd:
                    ctypes.windll.user32.ShowWindow(hwnd, 5)
            except Exception:
                pass

    def global_timer_tick(self):
        if self.seconds_left > 0:
            self.seconds_left -= 1

        if hasattr(self, "lbl_timer") and self.lbl_timer.winfo_exists():
            hours, remainder = divmod(self.seconds_left, 3600)
            mins, secs = divmod(remainder, 60)

            if hours > 0:
                self.lbl_timer.config(
                    text=f"До авто-удаления данных: {hours:02d}:{mins:02d}:{secs:02d}"
                )
            else:
                self.lbl_timer.config(
                    text=f"До авто-удаления данных: {mins:02d}:{secs:02d}"
                )

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
        self.configure(bg="black", cursor="none")

        frame_boot = tk.Frame(self, bg="black", cursor="none")
        frame_boot.pack(fill="both", expand=True)

        console_font = font.Font(family="Consolas", size=13)

        self.full_boot_log = (
            "Booting Windows . . .\n"
            "Boot error: 0x03527737\n"
            "Boot error: 0x0266712\n"
            "Boot error: 0x02897593\n"
            "Boot error: 0x01447812\n"
            "Boot error: 0x0150974\n"
            "Boot error: 0x03873700\n"
            "Boot error: 0x0700882\n"
            "Boot error: 0x03803618\n"
            "Memory section at address 0x0424* is locked!\n"
            "Service WRTCryptor started.\n"
            "System fucked!!!\n\n"
            "* Windows hacked!"
        )

        self.lbl_console = tk.Label(
            frame_boot,
            text="",
            fg="white",
            bg="black",
            font=console_font,
            justify="left",
            anchor="nw",
            cursor="none"
        )
        self.lbl_console.place(x=20, y=20)

        center_frame = tk.Frame(frame_boot, bg="black", cursor="none")
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        try:
            self.eye_img = tk.PhotoImage(file="eye.png")
            tk.Label(center_frame, image=self.eye_img, bg="black", cursor="none").pack(pady=(0, 20))
        except Exception:
            tk.Label(
                center_frame,
                text="[ 👁 ]",
                fg="white",
                bg="black",
                font=("Arial", 60),
                cursor="none"
            ).pack(pady=(0, 20))

        tk.Label(
            center_frame,
            text="ВАС ЗАМЕТИЛИ",
            fg="white",
            bg="black",
            font=("Arial", 36, "bold"),
            cursor="none"
        ).pack()

        self.play_sound_async("boot")

        # Быстрый вывод текста
        self.type_writer_effect(0)

    def type_writer_effect(self, index):
        """Максимально быстрый вывод лога (1 мс)."""
        if index <= len(self.full_boot_log):
            self.lbl_console.config(text=self.full_boot_log[:index])
            self.typing_job = self.after(1, self.type_writer_effect, index + 1)
        else:
            self.after(1000, self.setup_scare_screen)

    def setup_scare_screen(self):
        self.clear_screen()
        self.configure(bg="black", cursor="none")

        frame_scare = tk.Frame(self, bg="black", cursor="none")
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

        ascii_font = font.Font(family="Consolas", size=11, weight="bold")

        tk.Label(
            frame_scare,
            text=reaper_art,
            fg="red",
            bg="black",
            font=ascii_font,
            justify="left",
            cursor="none"
        ).place(relx=0.5, rely=0.5, anchor="center")

        self.play_sound_async("scare")
        self.after(1500, self.setup_lock_screen)

    def setup_lock_screen(self):
        self.clear_screen()
        self.configure(bg="#4a0000", cursor="none")

        center_frame = tk.Frame(
            self,
            bg="#0d0d0d",
            highlightbackground="red",
            highlightthickness=4,
            padx=45,
            pady=35,
            cursor="none"
        )
        center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.lbl_title = tk.Label(
            center_frame,
            text="⚠️ ВАШ КОМПЬЮТЕР ЗАБЛОКИРОВАН ⚠️",
            fg="red",
            bg="#0d0d0d",
            font=("Arial", 22, "bold"),
            cursor="none"
        )
        self.lbl_title.pack(pady=(0, 15))

        warning_text = (
            "Ах ты проказник! 😈\n"
            "Не пугайся, всё под контролем.\n\n"
            "Позвони мне, чтобы получить код разблокировки! 📞😎"
        )

        tk.Label(
            center_frame,
            text=warning_text,
            fg="#dddddd",
            bg="#0d0d0d",
            font=("Arial", 13),
            justify="center",
            cursor="none"
        ).pack(pady=10)

        hours, remainder = divmod(self.seconds_left, 3600)
        mins, secs = divmod(remainder, 60)

        self.lbl_timer = tk.Label(
            center_frame,
            text=f"До авто-удаления данных: {hours:02d}:{mins:02d}:{secs:02d}",
            fg="#ffcc00",
            bg="#0d0d0d",
            font=("Consolas", 14, "bold"),
            cursor="none"
        )
        self.lbl_timer.pack(pady=5)

        self.lbl_attempts = tk.Label(
            center_frame,
            text=f"Осталось попыток ввода: {self.attempts_left}",
            fg="#ff4444",
            bg="#0d0d0d",
            font=("Arial", 11),
            cursor="none"
        )
        self.lbl_attempts.pack(pady=(0, 10))

        self.play_sound_async("lock")
        self.start_blinking()

        def only_digits(value):
            return value.isdigit() or value == ""

        validate_cmd = self.register(only_digits)

        # Квадратная каретка (курсор ввода)
        self.entry_code = tk.Entry(
            center_frame,
            font=("Consolas", 24),
            justify="center",
            width=12,
            bg="#1a1a1a",
            fg="#00ff00",
            insertbackground="#00ff00",
            insertwidth=10,
            validate="key",
            validatecommand=(validate_cmd, "%P"),
            cursor="none"
        )

        self.entry_code.pack(pady=10)
        self.entry_code.focus_set()

        self.bind("<Return>", self.check_code)

        tk.Button(
            center_frame,
            text="РАЗБЛОКИРОВАТЬ",
            font=("Arial", 12, "bold"),
            bg="red",
            fg="white",
            activebackground="#990000",
            activeforeground="white",
            command=self.check_code,
            cursor="none",
            padx=10,
            pady=5
        ).pack(pady=15)

    def start_blinking(self):
        if hasattr(self, "lbl_title") and self.lbl_title.winfo_exists():
            self.blink_state = not self.blink_state
            color = "yellow" if self.blink_state else "red"
            self.lbl_title.config(fg=color)
            self.blink_job = self.after(800, self.start_blinking)

    def check_code(self, event=None):
        input_code = self.entry_code.get().strip()
        input_hash = hashlib.sha256(input_code.encode("utf-8")).hexdigest()

        if input_hash == self.correct_hash or input_code == self.correct_password:
            self.configure(cursor="arrow")
            messagebox.showinfo("System", "Код принят. Доступ восстановлен!")
            self.safe_destroy()
        else:
            self.attempts_left -= 1
            self.play_sound_async("wrong_code_scream")

            if self.attempts_left > 0:
                messagebox.showerror(
                    "ОШИБКА",
                    f"НЕВЕРНЫЙ КОД!\nОсталось попыток: {self.attempts_left}"
                )
                self.lbl_attempts.config(
                    text=f"Осталось попыток ввода: {self.attempts_left}"
                )
                self.entry_code.delete(0, tk.END)
            else:
                messagebox.showwarning(
                    "ВНИМАНИЕ",
                    "Превышено число попыток! Перезапуск интерфейса..."
                )
                self.attempts_left = 3
                self.setup_boot_screen()

    def safe_destroy(self):
        if self.countdown_job:
            self.after_cancel(self.countdown_job)

        if self.blink_job:
            self.after_cancel(self.blink_job)

        if self.typing_job:
            self.after_cancel(self.typing_job)

        self.configure(cursor="arrow")
        self.show_taskbar()
        self.destroy()


if __name__ == "__main__":
    app = UltimatePrank()
    app.mainloop()
