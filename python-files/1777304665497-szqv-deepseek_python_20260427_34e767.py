#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Красивый лаунчер ярлыков рабочего стола в стиле PSP.
Поддерживает .lnk и .url, оба рабочих стола (текущий + общий).
Управление: стрелки / колесо мыши / Enter / Esc / R для обновления.
"""

import os
import sys
import glob
import webbrowser
import tkinter as tk
from tkinter import font
from ctypes import windll

# --- Скрыть консольное окно на Windows (если запущено как .py, не .pyw) ---
if sys.platform == 'win32':
    try:
        windll.user32.ShowWindow(windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass


def get_all_desktops():
    """Возвращает список путей к папкам рабочих столов (текущий + публичный)."""
    user_desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    public_desktop = os.path.join(os.environ.get("PUBLIC", "C:\\Users\\Public"), "Desktop")
    paths = []
    if os.path.isdir(user_desktop):
        paths.append(user_desktop)
    if os.path.isdir(public_desktop):
        paths.append(public_desktop)
    return paths


def collect_shortcuts():
    """Собирает все .lnk и .url с рабочих столов, возвращает список (путь, имя)."""
    items = []
    desktop_paths = get_all_desktops()
    for desktop in desktop_paths:
        # Ярлыки программ .lnk
        for lnk in glob.glob(os.path.join(desktop, "*.lnk")):
            name = os.path.splitext(os.path.basename(lnk))[0]
            items.append((lnk, name))
        # Интернет-ярлыки .url
        for url in glob.glob(os.path.join(desktop, "*.url")):
            name = os.path.splitext(os.path.basename(url))[0]
            items.append((url, name))
    # Удаляем дубликаты по имени (если ярлык есть в двух местах)
    unique = {}
    for path, name in items:
        if name not in unique:
            unique[name] = path
    # Сортируем по имени и возвращаем список пар
    result = [(unique[name], name) for name in sorted(unique.keys())]
    return result


def launch_item(path):
    """Запускает ярлык .lnk через os.startfile, а .url – через webbrowser."""
    ext = os.path.splitext(path)[1].lower()
    try:
        if ext == '.lnk':
            os.startfile(path)
        elif ext == '.url':
            # .url файл – это текстовый INI, пытаемся извлечь URL
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.lower().startswith('url='):
                        url = line[4:].strip()
                        webbrowser.open(url)
                        return
            # Если не нашли URL, всё равно пробуем через startfile
            os.startfile(path)
        else:
            os.startfile(path)
    except Exception as e:
        raise RuntimeError(f"Ошибка запуска: {e}")


class PspLauncher:
    def __init__(self, root):
        self.root = root
        self.root.attributes('-fullscreen', True)
        self.root.configure(bg='#0a0f1a')  # тёмно-синий фон
        self.root.bind('<Escape>', lambda e: root.destroy())
        self.root.bind('<Return>', self.launch)
        self.root.bind('<KP_Enter>', self.launch)
        self.root.bind('<Up>', self.move_up)
        self.root.bind('<Down>', self.move_down)
        self.root.bind('<MouseWheel>', self.on_wheel)
        self.root.bind('<Button-4>', self.on_wheel)   # Linux колесо вверх
        self.root.bind('<Button-5>', self.on_wheel)   # вниз
        self.root.bind('<r>', self.refresh)
        self.root.bind('<R>', self.refresh)

        # Шрифты (сглаженные)
        self.title_font = font.Font(family='Segoe UI', size=42, weight='bold')
        self.item_font = font.Font(family='Segoe UI', size=28)
        self.help_font = font.Font(family='Segoe UI', size=16)

        # Сбор ярлыков
        self.items = collect_shortcuts()
        self.current = 0 if self.items else -1

        # Создаём Canvas для фона с градиентом
        self.canvas = tk.Canvas(root, highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.draw_gradient()

        # Заголовок
        self.title = tk.Label(self.canvas, text="★  PSP ЛАУНЧЕР  ★",
                              font=self.title_font, fg='#ffcc44', bg='#0a0f1a')
        self.title.place(relx=0.5, y=70, anchor='n')

        # Список (будет вложен в Canvas)
        self.list_frame = tk.Frame(self.canvas, bg='#0a0f1a')
        self.canvas.create_window(50, 150, anchor='nw', window=self.list_frame, width=self.canvas.winfo_width()-100)

        # Метки для строк (динамически обновляются)
        self.labels = []
        self.refresh_list()

        # Подсказки
        help_text = "↑/↓ / мышь  ·  Enter: запуск  ·  R: обновить  ·  Esc: выход"
        self.help_label = tk.Label(self.canvas, text=help_text, font=self.help_font,
                                   fg='#88aaff', bg='#0a0f1a')
        self.help_label.place(relx=0.5, y=self.root.winfo_screenheight()-40, anchor='s')

        # Анимация изменения выбора
        self.anim_id = None
        self.root.update_idletasks()
        self.highlight_selected()

    def draw_gradient(self):
        """Рисует радиальный градиент (имитация) – просто для красоты."""
        w = self.root.winfo_screenwidth()
        h = self.root.winfo_screenheight()
        # Простой линейный градиент сверху вниз
        for i in range(h):
            r = int(10 + (i/h) * 20)
            g = int(15 + (i/h) * 30)
            b = int(26 + (i/h) * 40)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, w, i, fill=color, width=1)

    def refresh_list(self):
        """Создаёт/обновляет виджеты строк списка."""
        # Удаляем старые
        for label in self.labels:
            label.destroy()
        self.labels.clear()

        y_offset = 0
        for idx, (_, name) in enumerate(self.items):
            # Каждая строка – Frame с тенью
            frame = tk.Frame(self.list_frame, bg='#1e2a3a', relief='flat')
            frame.pack(fill='x', pady=8, padx=20)
            # Декоративный квадрат (имитация иконки)
            icon = tk.Label(frame, text="⬤", font=('Segoe UI', 22), fg='#ffaa44', bg='#1e2a3a')
            icon.pack(side='left', padx=(20, 15))
            # Текст ярлыка
            lbl = tk.Label(frame, text=name, font=self.item_font,
                           fg='#eeeeee', bg='#1e2a3a', anchor='w')
            lbl.pack(side='left', fill='x', expand=True, padx=5)
            # Привязываем клик мыши
            frame.bind('<Button-1>', lambda e, i=idx: self.set_current(i))
            lbl.bind('<Button-1>', lambda e, i=idx: self.set_current(i))
            icon.bind('<Button-1>', lambda e, i=idx: self.set_current(i))
            self.labels.append((frame, lbl, icon))

        # Обновляем подсветку
        self.highlight_selected()

    def highlight_selected(self):
        """Подсвечивает текущую выбранную строку золотым свечением."""
        for idx, (frame, lbl, icon) in enumerate(self.labels):
            if idx == self.current:
                # Эффект свечения: жёлтый фон, рамка, тень
                frame.config(bg='#3a4a6e', highlightbackground='#ffcc44',
                             highlightthickness=2, highlightcolor='#ffcc44')
                lbl.config(bg='#3a4a6e', fg='#ffffff')
                icon.config(bg='#3a4a6e', fg='#ffcc44')
                # Небольшая анимация: меняем размер шрифта плавно (имитация)
                lbl.config(font=font.Font(family='Segoe UI', size=30, weight='bold'))
            else:
                frame.config(bg='#1e2a3a', highlightthickness=0)
                lbl.config(bg='#1e2a3a', fg='#cccccc',
                           font=font.Font(family='Segoe UI', size=28))
                icon.config(bg='#1e2a3a', fg='#88aaff')
        # Прокручиваем к выбранному элементу
        if self.current >= 0:
            y_pos = self.current * (self.item_font.metrics('linespace') + 25)  # примерно
            self.canvas.yview_moveto(y_pos / max(1, len(self.items)*80))

    def set_current(self, idx):
        if 0 <= idx < len(self.items):
            self.current = idx
            self.highlight_selected()

    def move_up(self, event=None):
        if self.items and self.current > 0:
            self.current -= 1
            self.highlight_selected()

    def move_down(self, event=None):
        if self.items and self.current < len(self.items)-1:
            self.current += 1
            self.highlight_selected()

    def on_wheel(self, event):
        # event.delta для Windows, event.num для Linux
        if event.delta:
            delta = -1 if event.delta < 0 else 1
        else:
            delta = 1 if event.num == 4 else -1
        if delta < 0:
            self.move_down()
        else:
            self.move_up()

    def launch(self, event=None):
        if self.items and 0 <= self.current < len(self.items):
            path, _ = self.items[self.current]
            try:
                launch_item(path)
            except Exception as e:
                # Показать ошибку
                err = tk.Label(self.canvas, text=f"Ошибка: {e}", font=self.help_font,
                               fg='red', bg='#0a0f1a')
                err.place(relx=0.5, y=self.root.winfo_screenheight()-80, anchor='s')
                self.root.after(2000, err.destroy)

    def refresh(self, event=None):
        self.items = collect_shortcuts()
        if self.current >= len(self.items):
            self.current = len(self.items)-1
        if self.current < 0 and self.items:
            self.current = 0
        self.refresh_list()


def main():
    root = tk.Tk()
    app = PspLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()