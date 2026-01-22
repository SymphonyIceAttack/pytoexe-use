import tkinter as tk
from tkinter import ttk
import psutil
import random
import os
import time
import threading

# ================= APP =================
class HackerPanel(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Painel Xny Ui")
        self.geometry("1250x720")
        self.resizable(False, False)
        self.configure(bg="#000000")

        self.style = ttk.Style(self)
        self.style.theme_use("default")
        self.style.configure(
            "Hacker.Horizontal.TProgressbar",
            troughcolor="#111111",
            background="#ffffff",
            thickness=8
        )

        self.create_ui()
        self.update_stats()

    # ================= UI =================
    def create_ui(self):
        title = tk.Label(
            self,
            text="Painel Xny Ui",
            fg="white",
            bg="black",
            font=("Consolas", 18, "bold")
        )
        title.pack(pady=12)

        main = tk.Frame(self, bg="black")
        main.pack(expand=True, fill="both", padx=20)

        # ===== LEFT =====
        left = tk.Frame(main, bg="black")
        left.pack(side="left", fill="both", expand=True, padx=10)

        self.create_system_status(left)
        self.create_ram_panel(left)
        self.create_optimization_panel(left)

        # ===== RIGHT =====
        right = tk.Frame(main, bg="black")
        right.pack(side="right", fill="both", expand=True, padx=10)

        self.create_server_panel(right)
        self.create_task_panel(right)

    # ================= PANELS =================
    def panel(self, parent, title):
        frame = tk.LabelFrame(
            parent,
            text=f" {title} ",
            fg="white",
            bg="black",
            font=("Consolas", 11, "bold"),
            bd=1,
            highlightbackground="#555555"
        )
        frame.pack(fill="both", expand=True, pady=10)
        return frame

    # ===== SYSTEM =====
    def create_system_status(self, parent):
        frame = self.panel(parent, "SYSTEM ESTATUS")
        self.cpu_bar, self.cpu_label = self.bar_row(frame, "CPU USADA")
        self.ram_bar, self.ram_label = self.bar_row(frame, "RAM USADA")

    # ===== RAM =====
    def create_ram_panel(self, parent):
        frame = self.panel(parent, "MEMORY ANALYZER")
        self.ram_total = self.text_row(frame, "TOTAL")
        self.ram_used = self.text_row(frame, "USED")
        self.ram_free = self.text_row(frame, "FREE")

    # ===== OPTIMIZATION =====
    def create_optimization_panel(self, parent):
        frame = self.panel(parent, "Optimizaçao Module")

        buttons = [
            ("Clean Temp Files", self.clean_temp),
            ("Clear DNS Cache", self.clear_dns),
            ("Restart Explorer", self.restart_explorer),
            ("Memory Clean (Safe)", self.memory_clean),
            ("Quick Optimization", self.quick_opt)
        ]

        for text, cmd in buttons:
            b = tk.Button(
                frame,
                text=text,
                font=("Consolas", 10),
                fg="white",
                bg="#111111",
                activebackground="#222222",
                activeforeground="white",
                relief="flat",
                highlightthickness=1,
                highlightbackground="#444444",
                command=lambda c=cmd, t=text: self.run_task(c, t)
            )
            b.pack(fill="x", padx=15, pady=6)

        # ===== PROGRESS BAR (NEW) =====
        self.opt_label = tk.Label(
            frame,
            text="IDLE",
            fg="#cccccc",
            bg="black",
            font=("Consolas", 9)
        )
        self.opt_label.pack(anchor="w", padx=15, pady=(10, 2))

        self.opt_bar = ttk.Progressbar(
            frame,
            style="Hacker.Horizontal.TProgressbar",
            maximum=100
        )
        self.opt_bar.pack(fill="x", padx=15, pady=(0, 8))

        self.opt_percent = tk.Label(
            frame,
            text="0%",
            fg="#888888",
            bg="black",
            font=("Consolas", 9)
        )
        self.opt_percent.pack(anchor="e", padx=15)

   
    def create_server_panel(self, parent):
        frame = self.panel(parent, "Servidores Ativos")
        self.server_list = tk.Listbox(
            frame,
            bg="black",
            fg="white",
            font=("Consolas", 10),
            highlightbackground="#444444",
            selectbackground="#222222",
            relief="flat"
        )
        self.server_list.pack(fill="both", expand=True, padx=10, pady=10)

        for _ in range(14):
            self.server_list.insert(
                "end",
                f"SERVER-{random.randint(100,999)} | ONLINE | {random.randint(12,80)}ms"
            )

  
    def create_task_panel(self, parent):
        frame = self.panel(parent, "Buscando Ms")
        self.task_label = tk.Label(
            frame, text="Monitorando servidor...",
            fg="white", bg="black",
            font=("Consolas", 10)
        )
        self.task_label.pack(anchor="w", padx=10, pady=5)

        self.task_bar = ttk.Progressbar(
            frame,
            style="Hacker.Horizontal.TProgressbar",
            maximum=100
        )
        self.task_bar.pack(fill="x", padx=10, pady=10)

    # ================= UI HELPERS =================
    def bar_row(self, parent, text):
        tk.Label(parent, text=text, fg="white", bg="black",
                 font=("Consolas", 10)).pack(anchor="w", padx=10)

        bar = ttk.Progressbar(parent, style="Hacker.Horizontal.TProgressbar", maximum=100)
        bar.pack(fill="x", padx=10, pady=4)

        value = tk.Label(parent, text="0%", fg="#cccccc", bg="black",
                         font=("Consolas", 9))
        value.pack(anchor="e", padx=10)

        return bar, value

    def text_row(self, parent, text):
        frame = tk.Frame(parent, bg="black")
        frame.pack(anchor="w", padx=10, pady=4)

        tk.Label(frame, text=text, fg="white", bg="black",
                 font=("Consolas", 10)).pack(side="left")

        label = tk.Label(frame, text="--", fg="#cccccc", bg="black",
                         font=("Consolas", 10))
        label.pack(side="right")
        return label

    # ================= OPT TASK RUNNER =================
    def run_task(self, func, name):
        threading.Thread(target=self._task_thread, args=(func, name), daemon=True).start()

    def _task_thread(self, func, name):
        self.opt_label.config(text=f"EXECUTING: {name}")
        for i in range(101):
            time.sleep(0.02)
            self.opt_bar["value"] = i
            self.opt_percent.config(text=f"{i}%")
        func()
        self.opt_label.config(text="DONE")
        time.sleep(0.5)
        self.opt_bar["value"] = 0
        self.opt_percent.config(text="0%")

    # ================= ACTIONS =================
    def clean_temp(self):
        os.system("del /s /q %temp%\\* >nul 2>&1")

    def clear_dns(self):
        os.system("ipconfig /flushdns >nul 2>&1")

    def restart_explorer(self):
        os.system("taskkill /f /im explorer.exe >nul 2>&1")
        time.sleep(1)
        os.system("start explorer.exe")

    def memory_clean(self):
        pass

    def quick_opt(self):
        self.clean_temp()
        self.clear_dns()

    # ================= UPDATE =================
    def update_stats(self):
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory()

        self.cpu_bar["value"] = cpu
        self.cpu_label.config(text=f"{cpu:.1f}%")

        self.ram_bar["value"] = ram.percent
        self.ram_label.config(text=f"{ram.percent:.1f}%")

        self.ram_total.config(text=f"{ram.total // (1024**3)} GB")
        self.ram_used.config(text=f"{ram.used // (1024**3)} GB")
        self.ram_free.config(text=f"{ram.available // (1024**3)} GB")

        self.task_bar["value"] = (self.task_bar["value"] + random.randint(2, 8)) % 100
        self.after(1000, self.update_stats)


# ================= START =================
if __name__ == "__main__":
    app = HackerPanel()
    app.mainloop()
