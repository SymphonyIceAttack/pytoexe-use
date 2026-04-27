#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Безоконный лаунчер (tkinter) – показывает ярлыки с рабочего стола.
Управление: стрелки / колесо мыши / Enter / Esc.
Скрывает консоль на Windows (файл должен иметь расширение .pyw).
"""

import os
import sys
import glob
import tkinter as tk
from tkinter import font

# --- Скрыть консольное окно на Windows (если файл .py, а не .pyw) ---
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass


def get_desktop_path():
    """Путь к рабочему столу"""
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    if os.path.isdir(desktop):
        return desktop
    alt = os.environ.get("USERPROFILE", "")
    if alt:
        alt_desktop = os.path.join(alt, "Desktop")
        if os.path.isdir(alt_desktop):
            return alt_desktop
    raise RuntimeError("Не найден рабочий стол")


def collect_shortcuts(desktop_path):
    """Список (путь к lnk, название)"""
    items = []
    for lnk in glob.glob(os.path.join(desktop_path, "*.lnk")):
        name = os.path.splitext(os.path.basename(lnk))[0]
        items.append((lnk, name))
    items.sort(key=lambda x: x[1].lower())
    return items


class LauncherApp:
    def __init__(self, root, shortcuts):
        self.root = root
        self.shortcuts = shortcuts
        self.current_index = 0 if shortcuts else -1
        self.scroll_offset = 0

        # Настройки окна – полный экран, без рамки
        root.attributes('-fullscreen', True)
        root.configure(bg='black')
        root.bind('<Escape>', lambda e: root.quit())
        root.bind('<Return>', self.launch_selected)
        root.bind('<KP_Enter>', self.launch_selected)
        root.bind('<Up>', self.move_up)
        root.bind('<Down>', self.move_down)
        root.bind('<MouseWheel>', self.on_mousewheel)   # Windows
        root.bind('<Button-4>', self.on_mousewheel)    # Linux / колесо вверх
        root.bind('<Button-5>', self.on_mousewheel)    # колесо вниз
        root.bind('<r>', self.refresh)
        root.bind('<R>', self.refresh)

        # Шрифты
        self.item_font = font.Font(family='Segoe UI', size=28)
        self.title_font = font.Font(family='Segoe UI', size=36, weight='bold')
        self.help_font = font.Font(family='Segoe UI', size=16)

        # Фрейм для списка (чтобы управлять прокруткой)
        self.list_frame = tk.Frame(root, bg='black')
        self.list_frame.pack(fill=tk.BOTH, expand=True, padx=50, pady=(80, 60))

        self.canvas = tk.Canvas(self.list_frame, bg='black', highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.list_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Внутренний фрейм, куда будем складывать строки
        self.inner = tk.Frame(self.canvas, bg='black')
        self.canvas_window = self.canvas.create_window((0, 0), window=self.inner, anchor='nw', width=self.canvas.winfo_width())

        self.inner.bind('<Configure>', self._on_inner_configure)
        self.canvas.bind('<Configure>', self._on_canvas_configure)

        # Заголовок и подсказки (в корневом окне, вне прокрутки)
        self.title_label = tk.Label(root, text="★ ЛАУНЧЕР ЯРЛЫКОВ ★",
                                    font=self.title_font, fg='#64b5f6', bg='black')
        self.title_label.place(relx=0.5, y=30, anchor='n')

        self.help_label = tk.Label(root,
                                   text="↑/↓ / Колёсико – навигация    •    Enter – запуск    •    R – обновить    •    Esc – выход",
                                   font=self.help_font, fg='#aaaaaa', bg='black')
        self.help_label.place(relx=0.5, y=root.winfo_screenheight() - 40, anchor='s')

        self.update_list()

    def _on_inner_configure(self, event=None):
        """Обновить область прокрутки при изменении содержимого"""
        self.canvas.configure(scrollregion=self.canvas.bbox('all'))

    def _on_canvas_configure(self, event):
        """Растянуть внутренний фрейм по ширине canvas"""
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def update_list(self):
        """Перерисовать список ярлыков (с учётом скролла)"""
        # Удаляем старые виджеты
        for widget in self.inner.winfo_children():
            widget.destroy()

        if not self.shortcuts:
            lbl = tk.Label(self.inner, text="Нет ярлыков (*.lnk) на рабочем столе",
                           font=self.item_font, fg='#ff8888', bg='black')
            lbl.pack(pady=20)
            return

        # Отображаем все элементы, но только видимые? В Canvas всё равно всё рисуется, но мы просто создаём все строки.
        # Для красоты можно и не делать виртуальную прокрутку – tkinter сам справится.
        for idx, (_, name) in enumerate(self.shortcuts):
            frame = tk.Frame(self.inner, bg='#2a2a2a' if idx == self.current_index else 'black')
            frame.pack(fill=tk.X, pady=5)
            # Подсветка выбранного
            label = tk.Label(frame, text=name, font=self.item_font,
                             fg='white', bg='#2a2a2a' if idx == self.current_index else 'black',
                             anchor='w')
            label.pack(fill=tk.X, padx=20, pady=5)
            if idx == self.current_index:
                # Добавляем рамку
                frame.config(highlightbackground='gold', highlightthickness=2, highlightcolor='gold')
            # Клик по строке – выбор
            label.bind('<Button-1>', lambda e, i=idx: self.set_current(i))
            frame.bind('<Button-1>', lambda e, i=idx: self.set_current(i))

        # Прокрутка к текущему элементу
        self.canvas.yview_moveto(0)  # сначала сброс
        if self.current_index >= 0:
            # Примерный расчёт позиции (грубо)
            item_height = 50  # примерная высота одной строки
            target_y = self.current_index * item_height
            self.canvas.yview_moveto(target_y / (len(self.shortcuts) * item_height))

    def set_current(self, idx):
        if 0 <= idx < len(self.shortcuts):
            self.current_index = idx
            self.update_list()

    def move_up(self, event=None):
        if self.shortcuts and self.current_index > 0:
            self.current_index -= 1
            self.update_list()

    def move_down(self, event=None):
        if self.shortcuts and self.current_index < len(self.shortcuts) - 1:
            self.current_index += 1
            self.update_list()

    def on_mousewheel(self, event):
        # event.delta для Windows, event.num для Linux
        if event.delta:
            delta = -1 if event.delta < 0 else 1
        else:
            delta = 1 if event.num == 4 else -1
        if delta < 0:
            self.move_down()
        else:
            self.move_up()

    def launch_selected(self, event=None):
        if self.shortcuts and 0 <= self.current_index < len(self.shortcuts):
            lnk_path = self.shortcuts[self.current_index][0]
            try:
                os.startfile(lnk_path)
            except Exception as e:
                # Показать ошибку на пару секунд
                err_label = tk.Label(self.root, text=f"Ошибка: {e}", font=self.help_font,
                                     fg='red', bg='black')
                err_label.place(relx=0.5, y=self.root.winfo_screenheight() - 80, anchor='s')
                self.root.after(2000, err_label.destroy)

    def refresh(self, event=None):
        try:
            desktop = get_desktop_path()
            new_shorts = collect_shortcuts(desktop)
            self.shortcuts = new_shorts
            if self.current_index >= len(self.shortcuts):
                self.current_index = len(self.shortcuts) - 1
            if self.current_index < 0 and self.shortcuts:
                self.current_index = 0
            self.update_list()
        except Exception as e:
            print("Ошибка обновления:", e)


def main():
    desktop_path = get_desktop_path()
    shortcuts = collect_shortcuts(desktop_path)

    root = tk.Tk()
    app = LauncherApp(root, shortcuts)
    root.mainloop()


if __name__ == "__main__":
    main()