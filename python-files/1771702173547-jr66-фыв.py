import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import asyncio

class TrapModsInstaller:
    def __init__(self, root):
        self.root = root
        self.root.title("TRAP MODS INSTALLER 5.0")
        self.root.geometry("600x650")
        self.root.resizable(False, False)
        self.root.configure(bg="#000000")  # черный фон
        self.root.attributes("-alpha", 0.7)  # 70% прозрачность

        self.gta_path = ""
        self.mod_path = ""

        self.setup_ui()
        self.animate_logo()

    def setup_ui(self):
        # Логотип
        self.logo_img_orig = Image.open("logo.png")  # скачай PNG локально
        self.logo_img_orig = self.logo_img_orig.resize((300,150), Image.ANTIALIAS)
        self.logo_img = ImageTk.PhotoImage(self.logo_img_orig)
        self.logo_label = tk.Label(self.root, image=self.logo_img, bg="#000000")
        self.logo_label.place(x=150, y=10)

        # Заголовок
        self.title_label = tk.Label(self.root, text="TRAP MODS", font=("Arial",28,"bold"), fg="white", bg="#000000")
        self.title_label.place(x=200, y=170)

        # Кнопки выбора папок
        self.btn_select_gta = tk.Button(self.root, text="Выбрать папку GTA V", width=25, command=self.select_gta)
        self.btn_select_gta.place(x=210, y=220)
        self.btn_select_mod = tk.Button(self.root, text="Выбрать папку с модом", width=25, command=self.select_mod)
        self.btn_select_mod.place(x=210, y=260)

        # Чекбоксы модов
        self.check_minimap = tk.IntVar()
        self.check_bigmap = tk.IntVar()
        self.check_crosshair = tk.IntVar()
        self.check_timecycle = tk.IntVar()
        self.check_frontend = tk.IntVar()
        self.check_effects = tk.IntVar()

        tk.Checkbutton(self.root, text="Миникарта", variable=self.check_minimap, fg="white", bg="#000000").place(x=230, y=310)
        tk.Checkbutton(self.root, text="Большая карта", variable=self.check_bigmap, fg="white", bg="#000000").place(x=230, y=340)
        tk.Checkbutton(self.root, text="Прицел", variable=self.check_crosshair, fg="white", bg="#000000").place(x=230, y=370)
        tk.Checkbutton(self.root, text="Timecycle", variable=self.check_timecycle, fg="white", bg="#000000").place(x=230, y=400)
        tk.Checkbutton(self.root, text="Интерфейс", variable=self.check_frontend, fg="white", bg="#000000").place(x=230, y=430)
        tk.Checkbutton(self.root, text="Эффекты", variable=self.check_effects, fg="white", bg="#000000").place(x=230, y=460)

        # Прогресс-бар
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=400, mode="determinate")
        self.progress.place(x=100, y=540)

        # Статус
        self.label_status = tk.Label(self.root, text="", fg="white", bg="#000000", font=("Arial",10,"bold"))
        self.label_status.place(x=150, y=580)

        # Кнопка УСТАНОВИТЬ с hover анимацией
        self.btn_install = tk.Button(self.root, text="УСТАНОВИТЬ", width=25, command=lambda: asyncio.run(self.install_mods()))
        self.btn_install.place(x=210, y=500)
        self.btn_install.bind("<Enter>", lambda e: self.btn_install.config(font=("Arial",12,"bold")))
        self.btn_install.bind("<Leave>", lambda e: self.btn_install.config(font=("Arial",10)))

    def animate_logo(self):
        # Плавное появление и масштабирование логотипа
        for scale in range(50, 101, 2):
            size = int(3*scale), int(1.5*scale)
            img_resized = self.logo_img_orig.resize(size, Image.ANTIALIAS)
            self.logo_img = ImageTk.PhotoImage(img_resized)
            self.logo_label.config(image=self.logo_img)
            self.root.update()
            self.root.after(10)

    def select_gta(self):
        path = filedialog.askdirectory(title="Выберите папку GTA V")
        if path:
            self.gta_path = path

    def select_mod(self):
        path = filedialog.askdirectory(title="Выберите папку с модом")
        if path:
            self.mod_path = path

    async def install_mods(self):
        if not self.gta_path or not self.mod_path:
            messagebox.showwarning("Ошибка", "Сначала выберите папки GTA V и мода!")
            return

        self.progress["value"] = 0
        self.label_status["text"] = "Запуск установки..."
        await asyncio.sleep(0.3)

        if self.check_minimap.get(): await self.copy_file("Миникарта", 15)
        if self.check_bigmap.get(): await self.copy_file("Большая карта", 30)
        if self.check_crosshair.get(): await self.copy_file("Прицел", 45)
        if self.check_timecycle.get(): await self.copy_file("Timecycle", 60)
        if self.check_frontend.get(): await self.copy_file("Интерфейс", 80)
        if self.check_effects.get(): await self.copy_file("Эффекты", 95)

        self.progress["value"] = 100
        self.label_status["text"] = "Установка завершена!"
        messagebox.showinfo("TRAP MODS", "Установка завершена!\n\nTRAP MODS")

    async def copy_file(self, mod_name, progress_value):
        self.label_status["text"] = f"Установлен мод: {mod_name}"
        self.progress["value"] = progress_value
        await asyncio.sleep(0.3)  # имитация процесса

if __name__ == "__main__":
    root = tk.Tk()
    app = TrapModsInstaller(root)
    root.mainloop()