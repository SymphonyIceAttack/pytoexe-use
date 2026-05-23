#!/usr/bin/env python3
"""
Пятнашки (15-puzzle) на Tkinter.

Запуск: python fifteen.py
"""

import tkinter as tk
from tkinter import messagebox
import random
import time

# Константы
SIZE = 4                # размер поля (4x4)
TILE_COUNT = SIZE * SIZE
TILE_SIZE = 100         # размер клетки в пикселях
MARGIN = 5              # отступ между плитками
WINDOW_WIDTH = TILE_SIZE * SIZE + 2 * MARGIN
WINDOW_HEIGHT = TILE_SIZE * SIZE + 120  # оставить место для кнопок/меток
FONT = ("Helvetica", 24, "bold")
BG_COLOR = "#F0F0F0"
TILE_COLOR = "#4CAF50"
EMPTY_COLOR = "#E0E0E0"
TEXT_COLOR = "white"
HIGHLIGHT_COLOR = "#81C784"

class FifteenGame(tk.Frame):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        master.title("Пятнашки")
        master.resizable(False, False)
        self.pack()

        # модель: список длины TILE_COUNT, 0 означает пустую клетку
        self.state = list(range(1, TILE_COUNT)) + [0]

        # Визуальные элементы
        self.canvas = tk.Canvas(self, width=WINDOW_WIDTH, height=WINDOW_WIDTH, bg=BG_COLOR)
        self.canvas.grid(row=0, column=0, columnspan=4, padx=10, pady=10)
        self.canvas.bind("<Button-1>", self.click)

        self.moves_var = tk.StringVar()
        self.time_var = tk.StringVar()
        self.moves_var.set("Ходов: 0")
        self.time_var.set("Время: 00:00")

        self.moves_label = tk.Label(self, textvariable=self.moves_var, font=("Helvetica", 12))
        self.moves_label.grid(row=1, column=0, sticky="w", padx=10)

        self.time_label = tk.Label(self, textvariable=self.time_var, font=("Helvetica", 12))
        self.time_label.grid(row=1, column=1, sticky="w")

        self.new_button = tk.Button(self, text="Новая игра", command=self.new_game)
        self.new_button.grid(row=1, column=2)

        self.shuffle_button = tk.Button(self, text="Перемешать", command=self.shuffle)
        self.shuffle_button.grid(row=1, column=3, padx=10)

        # Дополнительно ловим клавиши стрелок
        master.bind("<Up>", lambda e: self.move_by_key("Up"))
        master.bind("<Down>", lambda e: self.move_by_key("Down"))
        master.bind("<Left>", lambda e: self.move_by_key("Left"))
        master.bind("<Right>", lambda e: self.move_by_key("Right"))

        # Статус игры
        self.move_count = 0
        self.start_time = None
        self.running = False
        self.timer_job = None

        # Начальное перемешивание
        self.shuffle(initial=True)

    # ----------------- Модельные функции -----------------
    def index_to_rc(self, idx):
        return divmod(idx, SIZE)  # (row, col)

    def rc_to_index(self, r, c):
        return r * SIZE + c

    def find_empty(self):
        return self.state.index(0)

    def is_solved(self):
        return self.state == list(range(1, TILE_COUNT)) + [0]

    def swap(self, i, j):
        self.state[i], self.state[j] = self.state[j], self.state[i]

    # Проверка решаемости перестановки:
    # для чётного размера поля (4x4) ситуация:
    # если пустая клетка на строке с конца (начиная с 1): inversion_count + row_from_bottom -> должно быть чётным
    def is_solvable(self, arr):
        inv = 0
        flat = [x for x in arr if x != 0]
        for i in range(len(flat)):
            for j in range(i + 1, len(flat)):
                if flat[i] > flat[j]:
                    inv += 1
        empty_idx = arr.index(0)
        empty_row, _ = self.index_to_rc(empty_idx)  # row from top, 0-based
        row_from_bottom = SIZE - empty_row
        if SIZE % 2 == 1:
            return inv % 2 == 0
        else:
            # if grid width even, puzzle solvable if (inversions + row_from_bottom) is even
            return (inv + row_from_bottom) % 2 == 0

    # ----------------- UI / отрисовка -----------------
    def draw(self):
        self.canvas.delete("all")
        for i, val in enumerate(self.state):
            r, c = self.index_to_rc(i)
            x0 = c * TILE_SIZE + MARGIN
            y0 = r * TILE_SIZE + MARGIN
            x1 = x0 + TILE_SIZE - MARGIN * 2
            y1 = y0 + TILE_SIZE - MARGIN * 2
            if val == 0:
                # пустая клетка
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=EMPTY_COLOR, outline="#BDBDBD")
            else:
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=TILE_COLOR, outline="#2E7D32", width=2)
                self.canvas.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=str(val), font=FONT, fill=TEXT_COLOR)

    def highlight_tile(self, idx):
        # подсветка выбранной плитки (необязательно)
        r, c = self.index_to_rc(idx)
        x0 = c * TILE_SIZE + MARGIN
        y0 = r * TILE_SIZE + MARGIN
        x1 = x0 + TILE_SIZE - MARGIN * 2
        y1 = y0 + TILE_SIZE - MARGIN * 2
        self.canvas.create_rectangle(x0, y0, x1, y1, outline=HIGHLIGHT_COLOR, width=4)

    # ----------------- Перемешивание и старт -----------------
    def shuffle(self, initial=False):
        # Создаём случайную решаемую перестановку
        arr = list(range(TILE_COUNT))
        while True:
            random.shuffle(arr)
            if self.is_solvable(arr) and arr != list(range(1, TILE_COUNT)) + [0]:
                break
        # Привести значения к 0-значениям, где 0 — пустая
        # arr содержит числа 0..15, но нам нужно 1..15,0
        # если arr содержит 0..15 в порядке, преобразуем: 0 -> 0, k->k
        # Но лучше: создать permutation where values are 1..15 and 0 for empty
        # Преобразуем: каждая позиция i содержит число arr[i]; если arr[i]==0 -> пустая,
        # иначе число = arr[i]
        # Для простоты: возьмем arr, где значения 0..15; результат state = [x if x!=0 else 0]
        # НО чтобы сохранить числа 1..15, сделаем:
        # map: if v==0 -> 0 else v
        # Если хотим 1..15, лучше нормализуем: если arr содержит 0..15, а мы хотим 1..15,0,
        # используем permutation values mod TILE_COUNT.
        # Здесь используем простой способ: создадим perm из 1..15 и 0 в порядке arr indices.
        # Сформируем список values = []
        vals = []
        for pos in arr:
            if pos == 0:
                vals.append(0)
            else:
                vals.append(pos)
        # Но это может дать перестановку значений 1..15,0 с одной копией каждого.
        # Установим в self.state:
        self.state = vals
        # Если вдруг на последней позиции не 0 — это нормально. is_solvable гарантирует решаемость.
        self.move_count = 0
        self.moves_var.set("Ходов: 0")
        self.start_timer()
        self.draw()
        if not initial:
            # при ручном перемешивании сбросим и увеличим старт
            self.check_win()  # на случай, но маловероятно

    def new_game(self):
        # начинаем новую игру: перемешиваем
        self.shuffle()

    # ----------------- Время и счетчик -----------------
    def start_timer(self):
        # Запускаем/сбрасываем таймер
        self.start_time = time.time()
        self.running = True
        if self.timer_job:
            self.after_cancel(self.timer_job)
        self.update_timer()

    def stop_timer(self):
        self.running = False
        if self.timer_job:
            self.after_cancel(self.timer_job)
            self.timer_job = None

    def update_timer(self):
        if not self.running:
            return
        elapsed = int(time.time() - self.start_time)
        minutes = elapsed // 60
        seconds = elapsed % 60
        self.time_var.set(f"Время: {minutes:02d}:{seconds:02d}")
        self.timer_job = self.after(500, self.update_timer)

    # ----------------- Взаимодействие: клик и клавиши -----------------
    def click(self, event):
        # Определим индекс по координатам клика
        c = event.x // TILE_SIZE
        r = event.y // TILE_SIZE
        if r < 0 or r >= SIZE or c < 0 or c >= SIZE:
            return
        idx = self.rc_to_index(r, c)
        self.try_move(idx)

    def move_by_key(self, key):
        # Перемещаем пустую клетку в направлении, указанном клавишей, если возможно.
        empty = self.find_empty()
        r, c = self.index_to_rc(empty)
        if key == "Up":
            target = (r + 1, c)  # стрелка вверх — двигаем плитку вверх? удобнее: переместить плитку вниз в пустое место — но сделаем так: перемещаем пустую вниз
        elif key == "Down":
            target = (r - 1, c)
        elif key == "Left":
            target = (r, c + 1)
        elif key == "Right":
            target = (r, c - 1)
        else:
            return
        tr, tc = target
        if 0 <= tr < SIZE and 0 <= tc < SIZE:
            idx = self.rc_to_index(tr, tc)
            self.try_move(idx)

    def try_move(self, idx):
        # Перемещаем плитку в пустое место, если она соседняя (по манхэттену =1)
        empty = self.find_empty()
        er, ec = self.index_to_rc(empty)
        r, c = self.index_to_rc(idx)
        if abs(er - r) + abs(ec - c) == 1:
            self.swap(empty, idx)
            self.move_count += 1
            self.moves_var.set(f"Ходов: {self.move_count}")
            self.draw()
            if self.is_solved():
                self.on_win()

    def on_win(self):
        self.stop_timer()
        elapsed = int(time.time() - self.start_time) if self.start_time else 0
        minutes = elapsed // 60
        seconds = elapsed % 60
        messagebox.showinfo("Победа!", f"Вы решили задачу!\nХодов: {self.move_count}\nВремя: {minutes:02d}:{seconds:02d}")
        # Можно предложить автоматически начать новую игру
        # self.shuffle()

# ----------------- Запуск приложения -----------------
def main():
    root = tk.Tk()
    app = FifteenGame(root)
    root.mainloop()

if __name__ == "__main__":
    main()