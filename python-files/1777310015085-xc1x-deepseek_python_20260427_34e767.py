import os
import sys
import glob
import webbrowser
import tkinter as tk
from tkinter import font
from ctypes import windll

# Скрытие консоли
if sys.platform == 'win32':
    try: windll.user32.ShowWindow(windll.kernel32.GetConsoleWindow(), 0)
    except: pass

def collect_shortcuts():
    user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    public_desktop = os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
    items = []
    for d in [user_desktop, public_desktop]:
        if os.path.isdir(d):
            for ext in ["*.lnk", "*.url"]:
                for path in glob.glob(os.path.join(d, ext)):
                    items.append((path, os.path.splitext(os.path.basename(path))[0]))
    
    unique = {}
    for p, n in items:
        if n not in unique: unique[n] = p
    return [(unique[n], n) for n in sorted(unique.keys())]

class PspXmbLauncher:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#1a2a4a')
        
        # Настройки PSP стиля
        self.bg_color = "#1a2a4a"
        self.accent_color = "#ffffff"
        self.select_color = "#00d2ff"
        
        self.items = collect_shortcuts()
        self.current = 0
        
        self.canvas = tk.Canvas(root, bg=self.bg_color, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.width = self.root.winfo_screenwidth()
        self.height = self.root.winfo_screenheight()
        
        # Шрифты
        self.main_font = font.Font(family='Segoe UI Light', size=24)
        self.focus_font = font.Font(family='Segoe UI Semilight', size=36, weight='bold')
        
        # Управление
        self.root.bind('<Escape>', lambda e: root.destroy())
        self.root.bind('<Right>', self.move_right)
        self.root.bind('<Left>', self.move_left)
        self.root.bind('<Return>', self.launch)
        self.root.bind('<r>', self.refresh)

        self.draw_ui()
        self.animate_bg()

    def draw_ui(self):
        self.canvas.delete("all")
        
        # Рисуем задний план (волны PSP)
        self.canvas.create_oval(-100, self.height*0.4, self.width+100, self.height*1.2, 
                                outline="#2a3a5a", width=2)
        
        # Рисуем элементы
        center_x = self.width // 2
        center_y = self.height // 2
        spacing = 350 # Расстояние между иконками
        
        for i, (path, name) in enumerate(self.items):
            # Вычисляем позицию относительно центра
            offset = (i - self.current) * spacing
            x_pos = center_x + offset
            
            if x_pos < -200 or x_pos > self.width + 200:
                continue # Оптимизация: не рисуем то, что за экраном
                
            is_active = (i == self.current)
            alpha_color = self.accent_color if is_active else "#8899aa"
            display_font = self.focus_font if is_active else self.main_font
            
            # Иконка (в стиле PSP - круг с символом)
            icon_size = 60 if is_active else 40
            self.canvas.create_oval(x_pos-icon_size, center_y-icon_size-50, 
                                    x_pos+icon_size, center_y+icon_size-50, 
                                    outline=alpha_color, width=3)
            
            # Символ внутри иконки (чередуем кнопки PS)
            symbols = ["△", "○", "✕", "□"]
            self.canvas.create_text(x_pos, center_y-50, text=symbols[i % 4], 
                                    fill=alpha_color, font=("Segoe UI", 20))

            # Текст под иконкой
            text_id = self.canvas.create_text(x_pos, center_y + 80, text=name, 
                                              fill=alpha_color, font=display_font, 
                                              anchor="n")
            
            # Если активно, добавляем "свечение"
            if is_active:
                self.canvas.create_line(x_pos - 100, center_y + 160, 
                                        x_pos + 100, center_y + 160, 
                                        fill=self.select_color, width=4)

        # Подсказки внизу
        help_txt = "✕ Enter: Запуск  |  ○ Esc: Выход  |  △ R: Обновить"
        self.canvas.create_text(center_x, self.height - 50, text=help_txt, 
                                fill="#8899aa", font=("Segoe UI", 12))

    def move_right(self, e=None):
        if self.current < len(self.items) - 1:
            self.current += 1
            self.draw_ui()

    def move_left(self, e=None):
        if self.current > 0:
            self.current -= 1
            self.draw_ui()

    def launch(self, e=None):
        if not self.items: return
        path = self.items[self.current][0]
        try:
            os.startfile(path)
            # Эффект запуска: мигнуть экраном
            self.canvas.config(bg="white")
            self.root.after(100, lambda: self.canvas.config(bg=self.bg_color))
        except: pass

    def refresh(self, e=None):
        self.items = collect_shortcuts()
        self.current = 0
        self.draw_ui()

    def animate_bg(self):
        """Плавная пульсация фона"""
        # (Логика смены оттенка синего)
        pass # Для краткости, можно добавить через self.root.after

if __name__ == "__main__":
    root = tk.Tk()
    app = PspXmbLauncher(root)
    root.mainloop()