import tkinter as tk
from tkinter import messagebox
import pyautogui
import time
import threading
from datetime import datetime


class FastPaste:
    def __init__(self, root):
        self.root = root
        self.root.title("Fast Paste")
        self.root.geometry("430x500")
        self.root.resizable(False, False)

        self.x = None
        self.y = None
        self.running = False

        tk.Label(root, text="متن موردنظر:",
                 font=("Tahoma", 11, "bold")).pack(pady=(7, 3))

        self.text_box = tk.Text(root, height=5, width=45,
                                font=("Tahoma", 10))
        self.text_box.pack()

        frame = tk.Frame(root)
        frame.pack(pady=4)

        tk.Label(frame, text="تعداد تکرار:").grid(row=0, column=0, padx=5)
        self.repeat_entry = tk.Entry(frame, width=10, justify="center")
        self.repeat_entry.insert(0, "200")
        self.repeat_entry.grid(row=0, column=1, padx=5)

        tk.Label(frame, text="مدت زمان (ثانیه):").grid(
            row=1, column=0, padx=5, pady=4)
        self.time_entry = tk.Entry(frame, width=10, justify="center")
        self.time_entry.insert(0, "5")
        self.time_entry.grid(row=1, column=1, padx=5, pady=4)

        # کلید ثبت مختصات
        tk.Button(
            root,
            text="ثبت مختصات",
            width=16,
            height=1,
            command=self.set_position
        ).pack(pady=3)

        self.position_label = tk.Label(
            root, text="مختصات ثبت نشده",
            font=("Tahoma", 10))
        self.position_label.pack(pady=3)

        buttons = tk.Frame(root)
        buttons.pack(pady=3)

        tk.Button(buttons, text="شروع", width=12, height=1,
                  command=self.start).grid(row=0, column=0, padx=5)
        tk.Button(buttons, text="توقف", width=12, height=1,
                  command=self.stop).grid(row=0, column=1, padx=5)

        self.status = tk.Label(root, text="آماده",
                               font=("Tahoma", 10, "bold"))
        self.status.pack(pady=3)

        tk.Label(root, text="لاگ زمان هر Paste:",
                 font=("Tahoma", 10, "bold")).pack(pady=(3, 2))

        log_frame = tk.Frame(root)
        log_frame.pack(padx=10, fill="both", expand=True)

        self.log_box = tk.Text(
            log_frame, height=9, width=48,
            font=("Consolas", 9), state="disabled")
        self.log_box.pack(side="left", fill="both", expand=True)

        scrollbar = tk.Scrollbar(log_frame, command=self.log_box.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_box.config(yscrollcommand=scrollbar.set)

        tk.Button(root, text="پاک کردن لاگ", width=16,
                  command=self.clear_log).pack(pady=4)

        self.root.bind("<F8>", lambda e: self.start())
        self.root.bind("<F9>", lambda e: self.stop())

    def add_log(self, text):
        def write():
            self.log_box.config(state="normal")
            self.log_box.insert(tk.END, text + "\n")
            self.log_box.see(tk.END)
            self.log_box.config(state="disabled")
        self.root.after(0, write)

    def clear_log(self):
        self.log_box.config(state="normal")
        self.log_box.delete("1.0", tk.END)
        self.log_box.config(state="disabled")

    def set_position(self):
        messagebox.showinfo(
            "ثبت مختصات",
            "OK را بزنید.\n"
            "سپس موس را روی نقطه موردنظر ببرید.\n"
            "بعد از 2 ثانیه مختصات ثبت می‌شود."
        )

        self.root.withdraw()
        time.sleep(2)
        self.x, self.y = pyautogui.position()
        self.root.deiconify()

        self.position_label.config(
            text=f"مختصات ثبت شد: X={self.x}   Y={self.y}"
        )

    def stop(self):
        self.running = False
        self.status.config(text="متوقف شد")
        self.add_log(
            f"--- توقف: {datetime.now().strftime('%H:%M:%S.%f')[:-3]} ---"
        )

    def start(self):
        if self.running:
            return

        text = self.text_box.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("خطا", "ابتدا متن را وارد کنید.")
            return

        try:
            repeat = int(self.repeat_entry.get())
            duration = float(self.time_entry.get())
        except ValueError:
            messagebox.showwarning(
                "خطا", "تعداد تکرار و مدت زمان باید عدد باشند.")
            return

        if repeat <= 0 or duration <= 0:
            messagebox.showwarning(
                "خطا", "مقادیر باید بیشتر از صفر باشند.")
            return

        if self.x is None or self.y is None:
            messagebox.showwarning(
                "خطا", "ابتدا کلید «ثبت مختصات» را بزنید.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

        self.running = True
        self.clear_log()

        threading.Thread(
            target=self.paste_loop,
            args=(repeat, duration),
            daemon=True
        ).start()

    def paste_loop(self, repeat, duration):
        interval = duration / repeat
        start_time = time.perf_counter()

        self.add_log(
            f"--- شروع: {datetime.now().strftime('%H:%M:%S.%f')[:-3]} ---")
        self.add_log(
            f"تعداد={repeat} | مدت={duration:g}s | فاصله هدف={interval*1000:.3f} ms"
        )

        for i in range(repeat):
            if not self.running:
                break

            target_time = start_time + i * interval

            while self.running:
                remaining = target_time - time.perf_counter()
                if remaining <= 0:
                    break
                if remaining > 0.002:
                    time.sleep(remaining - 0.001)

            if not self.running:
                break

            pyautogui.click(self.x, self.y)
            pyautogui.hotkey("ctrl", "v")

            timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
            self.add_log(f"{i + 1:03d} | {timestamp}")

            self.root.after(
                0,
                lambda n=i + 1: self.status.config(
                    text=f"در حال اجرا: {n} / {repeat}")
            )

        self.running = False
        self.add_log(
            f"--- پایان: {datetime.now().strftime('%H:%M:%S.%f')[:-3]} ---")
        self.root.after(0, lambda: self.status.config(text="پایان عملیات"))


root = tk.Tk()
app = FastPaste(root)
root.mainloop()
