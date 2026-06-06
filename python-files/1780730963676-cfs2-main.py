import tkinter as tk

class SokobanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Игра: Передвинь ящики, чтобы найти выход")
        self.canvas = tk.Canvas(root, width=500, height=500, bg="white")
        self.canvas.pack()

        # Размер клетки
        self.cell_size = 50

        # Создаем игровую сетку (10x10)
        self.rows = 10
        self.cols = 10

        # Изначальные позиции объектов
        self.player_pos = [1, 1]
        self.exit_pos = [8, 8]
        self.box_positions = [[3, 3], [4, 4], [5, 3]]

        # Создаем объекты
        self.draw_grid()
        self.draw_objects()

        # Назначаем обработчики клавиш
        self.root.bind("<Key>", self.move_player)

    def draw_grid(self):
        for i in range(self.rows):
            for j in range(self.cols):
                x1 = j * self.cell_size
                y1 = i * self.cell_size
                x2 = x1 + self.cell_size
                y2 = y1 + self.cell_size
                self.canvas.create_rectangle(x1, y1, x2, y2, fill="lightgrey", outline="black")

    def draw_objects(self):
        # Очистить все объекты
        self.canvas.delete("objects")

        # Нарисовать выход
        x, y = self.exit_pos
        self.draw_cell(x, y, color="green", text="EXIT", font=("Arial", 10, "bold"))

        # Нарисовать ящики
        for pos in self.box_positions:
            x, y = pos
            self.draw_cell(x, y, color="brown", text="BOX", font=("Arial", 8))

        # Нарисовать игрока
        x, y = self.player_pos
        self.draw_cell(x, y, color="blue", text="YOU", font=("Arial", 8))

    def draw_cell(self, grid_x, grid_y, color, text="", font=None):
        x1 = grid_x * self.cell_size + 2
        y1 = grid_y * self.cell_size + 2
        x2 = x1 + self.cell_size - 4
        y2 = y1 + self.cell_size - 4
        self.canvas.create_rectangle(x1, y1, x2, y2, fill=color, tags="objects")
        if text:
            self.canvas.create_text(
                (x1 + x2) / 2,
                (y1 + y2) / 2,
                text=text,
                fill="white",
                font=font,
                tags="objects",
            )

    def move_player(self, event):
        direction = event.keysym
        dx, dy = 0, 0
        if direction == "Up":
            dy = -1
        elif direction == "Down":
            dy = 1
        elif direction == "Left":
            dx = -1
        elif direction == "Right":
            dx = 1
        else:
            return

        new_x = self.player_pos[0] + dx
        new_y = self.player_pos[1] + dy

        # Проверка границ
        if not (0 <= new_x < self.cols and 0 <= new_y < self.rows):
            return

        # Проверка на ящик
        if [new_x, new_y] in self.box_positions:
            # Попытка сдвинуть ящик
            box_new_x = new_x + dx
            box_new_y = new_y + dy
            # Проверка границ и свободных клеток
            if not (0 <= box_new_x < self.cols and 0 <= box_new_y < self.rows):
                return
            if [box_new_x, box_new_y] in self.box_positions:
                return
            # Перемещаем ящик
            index = self.box_positions.index([new_x, new_y])
            self.box_positions[index] = [box_new_x, box_new_y]
            # Перемещаем игрок
            self.player_pos = [new_x, new_y]
        else:
            # Просто перемещение игрока
            self.player_pos = [new_x, new_y]

        self.draw_objects()
        self.check_win()

    def check_win(self):
        if self.player_pos == self.exit_pos:
            # Проверка, есть ли ящики на месте выхода
            if self.exit_pos in self.box_positions:
                self.show_message("Ящики мешают выйти!")
            else:
                self.show_message("Поздравляем! Вы нашли выход!")

    def show_message(self, message):
        popup = tk.Toplevel()
        popup.title("Сообщение")
        label = tk.Label(popup, text=message, font=("Arial", 14))
        label.pack(padx=20, pady=20)
        btn = tk.Button(popup, text="ОК", command=popup.destroy)
        btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    game = SokobanGame(root)
    root.mainloop()