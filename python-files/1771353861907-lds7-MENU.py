import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import random

class AnimatedApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Менюшка с эффектами")
        self.root.geometry("600x400")
        self.root.resizable(False, False)

        # Настройки
        self.dark_mode = tk.BooleanVar(value=True)
        self.snow_enabled = tk.BooleanVar(value=False)
        self.leaves_enabled = tk.BooleanVar(value=False)
        self.bg_image = None

        # Canvas для анимации
        self.canvas = tk.Canvas(root, width=600, height=400, bg="black")
        self.canvas.pack(fill="both", expand=True)

        # Меню
        menu = tk.Menu(root)
        root.config(menu=menu)
        settings_menu = tk.Menu(menu, tearoff=0)
        menu.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_checkbutton(label="Темная тема", variable=self.dark_mode, command=self.update_theme)
        settings_menu.add_checkbutton(label="Включить снег", variable=self.snow_enabled, command=self.toggle_snow)
        settings_menu.add_checkbutton(label="Включить листики", variable=self.leaves_enabled, command=self.toggle_leaves)
        settings_menu.add_command(label="Сменить фон", command=self.change_bg)

        # Эффекты
        self.snowflakes = []
        self.leaves = []

        # Запуск анимации
        self.animate()

    def update_theme(self):
        color = "black" if self.dark_mode.get() else "white"
        self.canvas.config(bg=color)

    def toggle_snow(self):
        if not self.snow_enabled.get():
            self.snowflakes.clear()

    def toggle_leaves(self):
        if not self.leaves_enabled.get():
            self.leaves.clear()

    def change_bg(self):
        file_path = filedialog.askopenfilename(
            title="Выберите изображение для фона",
            filetypes=[("Image files", "*.png;*.jpg;*.jpeg;*.bmp")]
        )
        if file_path:
            image = Image.open(file_path)
            image = image.resize((600, 400))
            self.bg_image = ImageTk.PhotoImage(image)
            self.canvas.create_image(0, 0, image=self.bg_image, anchor="nw")

    def animate(self):
        self.canvas.delete("effect")  # удаляем предыдущие эффекты

        # Снег
        if self.snow_enabled.get():
            if len(self.snowflakes) < 50:
                self.snowflakes.append([random.randint(0, 600), 0, random.randint(2, 5)])
            for flake in self.snowflakes:
                flake[1] += flake[2]
                self.canvas.create_text(flake[0], flake[1], text="❄", font=("Arial", flake[2]*5), fill="white", tags="effect")
            self.snowflakes = [f for f in self.snowflakes if f[1] < 400]

        # Листья
        if self.leaves_enabled.get():
            if len(self.leaves) < 20:
                self.leaves.append([random.randint(0, 600), 0, random.uniform(1, 3)])
            for leaf in self.leaves:
                leaf[1] += leaf[2]
                self.canvas.create_text(leaf[0], leaf[1], text="🍃", font=("Arial", int(20*leaf[2])), tags="effect")
            self.leaves = [l for l in self.leaves if l[1] < 400]

        self.root.after(50, self.animate)


if __name__ == "__main__":
    root = tk.Tk()
    app = AnimatedApp(root)
    root.mainloop()