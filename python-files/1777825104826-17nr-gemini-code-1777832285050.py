import tkinter as tk
from tkinter import messagebox
import os
import subprocess

class PortableLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("Console Launcher")
        
        # Делаем окно полноэкранным
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#121212") # Темный фон в стиле интерфейсов PS/Xbox

        # Заголовок
        self.header = tk.Label(
            root, text="ГЛАВНОЕ МЕНЮ", font=("Segoe UI", 32, "bold"),
            bg="#121212", fg="#ffffff", pady=40
        )
        self.header.pack()

        # Контейнер для ярлыков (фрейм с прокруткой)
        self.canvas = tk.Canvas(root, bg="#121212", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.grid_frame = tk.Frame(self.canvas, bg="#121212")

        self.grid_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((root.winfo_screenwidth()//2, 0), window=self.grid_frame, anchor="n")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True, padx=50)
        
        # Загружаем ярлыки
        self.load_shortcuts()

        # Кнопка выхода (Esc)
        self.root.bind("<Escape>", lambda e: self.root.destroy())

    def load_shortcuts(self):
        """Сканирует рабочий стол и создает 'плитки'"""
        desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
        public_desktop = os.path.join(os.environ['PUBLIC'], 'Desktop')
        
        paths = [desktop, public_desktop]
        
        col = 0
        row = 0
        max_cols = 5 # Количество иконок в ряд

        for path in paths:
            if not os.path.exists(path): continue
            
            for item in os.listdir(path):
                if item.lower() == 'desktop.ini': continue
                
                full_path = os.path.join(path, item)
                name = os.path.splitext(item)[0]
                if len(name) > 15: name = name[:12] + "..."

                # Создаем "плитку" приложения
                btn = tk.Button(
                    self.grid_frame, 
                    text=f"🎮\n{name}", 
                    font=("Segoe UI", 12, "bold"),
                    fg="white", 
                    bg="#1e1e1e",
                    activebackground="#107c10", # Цвет при нажатии (Xbox Green)
                    activeforeground="white",
                    width=15, 
                    height=6,
                    relief="flat",
                    cursor="hand2",
                    command=lambda p=full_path: self.launch(p)
                )
                btn.grid(row=row, column=col, padx=15, pady=15)
                
                # Эффект наведения
                btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#333333"))
                btn.bind("<Leave>", lambda e, b=btn: b.configure(bg="#1e1e1e"))

                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1

    def launch(self, path):
        try:
            os.startfile(path)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось запустить:\n{path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = PortableLauncher(root)
    root.mainloop()