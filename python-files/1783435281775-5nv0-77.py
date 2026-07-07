import tkinter as tk
import random
import time

# Размеры игры
CELL_SIZE = 30
COLS = 10
ROWS = 20

# Цвета для фигур
COLORS = ["cyan", "blue", "orange", "yellow", "green", "purple", "red"]

# Определение форм фигур (матрицы 4x4)
SHAPES = [
    # I
    [[1, 1, 1, 1]],
    # J
    [[1, 0, 0],
     [1, 1, 1]],
    # L
    [[0, 0, 1],
     [1, 1, 1]],
    # O
    [[1, 1],
     [1, 1]],
    # S
    [[0, 1, 1],
     [1, 1, 0]],
    # T
    [[0, 1, 0],
     [1, 1, 1]],
    # Z
    [[1, 1, 0],
     [0, 1, 1]],
]

class Tetris:
    def __init__(self, root):
        self.root = root

        # Создаем интерфейс
        self.frame = tk.Frame(root)
        self.frame.pack()

        # Основное поле
        self.canvas = tk.Canvas(self.frame, width=COLS*CELL_SIZE, height=ROWS*CELL_SIZE, bg='black')
        self.canvas.grid(row=0, column=0, rowspan=4, padx=10, pady=10)

        # Область следующей фигуры
        self.next_canvas = tk.Canvas(self.frame, width=6*CELL_SIZE, height=6*CELL_SIZE, bg='gray')
        self.next_canvas.grid(row=0, column=1, padx=10, pady=10)
        self.next_label = tk.Label(self.frame, text="Следующая фигура")
        self.next_label.grid(row=1, column=1)

        # Кнопки
        self.btn_start = tk.Button(self.frame, text="Старт", command=self.start_game, width=10)
        self.btn_start.grid(row=2, column=1, pady=5)

        self.btn_reset = tk.Button(self.frame, text="Сброс", command=self.reset_game, width=10)
        self.btn_reset.grid(row=3, column=1, pady=5)

        # Время и очки
        self.time_label = tk.Label(self.frame, text="Время: 00:00:00")
        self.time_label.grid(row=4, column=0, sticky='w', padx=10)

        self.score_label = tk.Label(self.frame, text="Очки: 0")
        self.score_label.grid(row=4, column=1, sticky='w')

        # Изначально игра не запущена
        self.game_running = False

        # Переменные
        self.field = [[0 for _ in range(COLS)] for _ in range(ROWS)]
        self.current_shape = None
        self.current_color = None
        self.current_pos = [0, 0]
        self.next_shape = None
        self.next_color = None

        self.start_time = None
        self.timer_id = None
        self.score = 0
        self.is_game_over = False

        self.root.bind("<Key>", self.key_pressed)

        self.update_time()

    def start_game(self):
        if not self.game_running:
            self.reset_field()
            self.score = 0
            self.score_label.config(text="Очки: 0")
            self.is_game_over = False
            self.game_running = True
            self.start_time = time.time()
            self.update_time()
            self.new_shape()
            self.game_loop()

    def reset_game(self):
        self.reset_field()
        self.score = 0
        self.score_label.config(text="Очки: 0")
        self.is_game_over = False
        self.game_running = False
        self.canvas.delete("all")
        self.next_canvas.delete("all")
        self.time_label.config(text="Время: 00:00:00")
        if self.timer_id:
            self.root.after_cancel(self.timer_id)

    def reset_field(self):
        self.field = [[0 for _ in range(COLS)] for _ in range(ROWS)]

    def update_time(self):
        if self.game_running:
            elapsed = int(time.time() - self.start_time)
            h = elapsed // 3600
            m = (elapsed % 3600) // 60
            s = elapsed % 60
            self.time_label.config(text=f"Время: {h:02d}:{m:02d}:{s:02d}")
            self.timer_id = self.root.after(1000, self.update_time)
        else:
            self.time_label.config(text="Время: 00:00:00")

    def new_shape(self):
        # Генерируем следующую фигуру
        if self.next_shape is None:
            shape_idx = random.randint(0, len(SHAPES) - 1)
            self.next_shape = SHAPES[shape_idx]
            self.next_color = COLORS[shape_idx]
        # Передача следующей фигуры в текущую
        self.current_shape = self.next_shape
        self.current_color = self.next_color
        self.next_shape = None
        # Генерируем новую следующую
        shape_idx = random.randint(0, len(SHAPES) - 1)
        self.next_shape = SHAPES[shape_idx]
        self.next_color = COLORS[shape_idx]
        self.draw_next()
        self.current_pos = [0, COLS // 2 - len(self.current_shape[0]) // 2]
        if self.check_collision(self.current_shape, self.current_pos):
            self.is_game_over = True
            self.game_running = False
            self.draw_game_over()

    def check_collision(self, shape, pos):
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    x = pos[1] + j
                    y = pos[0] + i
                    if x < 0 or x >= COLS or y >= ROWS:
                        return True
                    if y >= 0 and self.field[y][x]:
                        return True
        return False

    def merge_shape(self):
        shape = self.current_shape
        pos = self.current_pos
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    y = pos[0] + i
                    x = pos[1] + j
                    if 0 <= y < ROWS and 0 <= x < COLS:
                        self.field[y][x] = self.current_color

    def clear_lines(self):
        lines_cleared = 0
        for y in range(ROWS):
            if all(self.field[y]):
                del self.field[y]
                self.field.insert(0, [0 for _ in range(COLS)])
                lines_cleared += 1
        self.score += lines_cleared * 100
        self.score_label.config(text=f"Очки: {self.score}")

    def rotate_shape(self):
        rotated = list(zip(*self.current_shape[::-1]))
        rotated = [list(row) for row in rotated]
        if not self.check_collision(rotated, self.current_pos):
            self.current_shape = rotated

    def move(self, dx):
        new_pos = [self.current_pos[0], self.current_pos[1] + dx]
        if not self.check_collision(self.current_shape, new_pos):
            self.current_pos = new_pos

    def soft_drop(self):
        new_pos = [self.current_pos[0] + 1, self.current_pos[1]]
        if not self.check_collision(self.current_shape, new_pos):
            self.current_pos = new_pos
            return True
        else:
            self.merge_shape()
            self.clear_lines()
            self.new_shape()
            return False

    def game_loop(self):
        if self.game_running:
            if not self.soft_drop():
                if self.is_game_over:
                    self.draw_game_over()
            self.draw()
            self.root.after(500, self.game_loop)

    def draw(self):
        self.canvas.delete("all")
        # Рисуем поле
        for y in range(ROWS):
            for x in range(COLS):
                color = self.field[y][x]
                if color:
                    self.draw_cell(self.canvas, x, y, color)
        # Текущая фигура
        for i, row in enumerate(self.current_shape):
            for j, cell in enumerate(row):
                if cell:
                    x = self.current_pos[1] + j
                    y = self.current_pos[0] + i
                    if y >= 0:
                        self.draw_cell(self.canvas, x, y, self.current_color)
        self.root.title(f"Тетрис - Очки: {self.score}")

    def draw_cell(self, canvas, x, y, color):
        x1 = x * CELL_SIZE
        y1 = y * CELL_SIZE
        x2 = x1 + CELL_SIZE
        y2 = y1 + CELL_SIZE
        canvas.create_rectangle(x1, y1, x2, y2, fill=color, outline='white')

    def key_pressed(self, event):
        if not self.game_running:
            return
        if self.is_game_over:
            return
        if event.keysym == 'Left':
            self.move(-1)
        elif event.keysym == 'Right':
            self.move(1)
        elif event.keysym == 'Down':
            self.soft_drop()
        elif event.keysym == 'Up':
            self.rotate_shape()
        elif event.keysym == 'space':
            while self.soft_drop():
                pass
        self.draw()

    def draw_next(self):
        self.next_canvas.delete("all")
        # Центрируем фигуру в области
        shape = self.next_shape
        offset = 0
        for i, row in enumerate(shape):
            for j, cell in enumerate(row):
                if cell:
                    x = j + 1
                    y = i + 1
                    self.draw_cell(self.next_canvas, x, y, self.next_color)

    def draw_game_over(self):
        # Создаем новое окно
        game_over_window = tk.Toplevel(self.root)
        game_over_window.title("Игра окончена")
        game_over_window.geometry("300x150")
        game_over_window.resizable(False, False)

        # Текст с результатом
        msg = f"Игра окончена!\nОчки: {self.score}"
        label = tk.Label(game_over_window, text=msg, font=('Arial', 14), justify='center')
        label.pack(pady=10)

        # Кнопка "Заново"
        restart_button = tk.Button(
            game_over_window,
            text="Заново",
            width=10,
            command=lambda: [self.reset_field(), self.score_label.config(text="Очки: 0"),
                             self.start_game(), game_over_window.destroy()]
        )
        restart_button.pack(side='left', padx=20, pady=10)

        # Кнопка "Выход" закрывает программу
        exit_button = tk.Button(
            game_over_window,
            text="Выход",
            width=10,
            command=self.root.destroy
        )
        exit_button.pack(side='right', padx=20, pady=10)

        # Запретить закрытие основного окна
        self.game_running = False

if __name__ == "__main__":
    root = tk.Tk()
    root.title("Тетрис")
    game = Tetris(root)
    root.mainloop()
