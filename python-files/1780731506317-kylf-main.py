import tkinter as tk

class SokobanGame:
    def __init__(self, root):
        self.root = root
        self.root.title("Игра: Передвинь ящики, чтобы найти выход")
        self.canvas = tk.Canvas(root, width=500, height=500, bg="white")
        self.canvas.pack()

        self.cell_size = 50
        self.rows = 10
        self.cols = 10

        # Изначальные позиции
        self.player_pos = [1, 1]
        self.exit_pos = [8, 8]

        # Ящики
        self.box_positions = [
            [3, 3], [4, 4], [5, 3], [2, 6], [7, 2], [6, 7]
        ]

        # Стены
        self.wall_positions = [
            [0, 0], [0, 1], [0, 2], [0, 3], [0, 4],
            [0, 5], [0, 6], [0, 7], [0, 8], [0, 9],
            [1, 0], [2, 0], [3, 0], [4, 0], [5, 0],
            [6, 0], [7, 0], [8, 0], [9, 0],
            [9, 1], [9, 2], [9, 3], [9, 4], [9, 5],
            [9, 6], [9, 7], [9, 8], [9, 9],
            [1, 9], [2, 9], [3, 9], [4, 9], [5, 9],
            [6, 9], [7, 9], [8, 9]
        ]

        # Перегородки, усложняющие путь
        self.partition_positions = [
            [2, 2], [2, 3], [2, 4], [2, 5],
            [3, 5], [4, 5], [5, 5],
            [5, 2], [5, 3], [5, 4],
            [7, 4], [7, 5], [7, 6],
            [4, 7], [5, 7], [6, 7]
        ]

        self.draw_grid()
        self.draw_objects()

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
        self.canvas.delete("objects")
        # Стены
        for pos in self.wall_positions:
            self.draw_cell(pos[0], pos[1], color="black")
        # Перегородки
        for pos in self.partition_positions:
            self.draw_cell(pos[0], pos[1], color="darkgrey")
        # Выход
        self.draw_cell(self.exit_pos[0], self.exit_pos[1], color="green", text="EXIT", font=("Arial", 10, "bold"))
        # Ящики
        for pos in self.box_positions:
            self.draw_cell(pos[0], pos[1], color="brown", text="BOX", font=("Arial", 8))
        # Игрок
        self.draw_cell(self.player_pos[0], self.player_pos[1], color="blue", text="YOU", font=("Arial", 8))

    def draw_cell(self, grid_x, grid_y, color, text="", font=None):
        x1 = grid_y * self.cell_size + 2
        y1 = grid_x * self.cell_size + 2
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

        new_x = self.player_pos[0] + dy
        new_y = self.player_pos[1] + dx

        # Проверка границ
        if not (0 <= new_x < self.rows and 0 <= new_y < self.cols):
            return

        # Проверка на стены
        if [new_x, new_y] in self.wall_positions:
            return

        # Проверка на перегородки
        if [new_x, new_y] in self.partition_positions:
            return

        # Проверка на ящик
        if [new_x, new_y] in self.box_positions:
            box_new_x = new_x + dy
            box_new_y = new_y + dx
            if not (0 <= box_new_x < self.rows and 0 <= box_new_y < self.cols):
                return
            if [box_new_x, box_new_y] in self.wall_positions:
                return
            if [box_new_x, box_new_y] in self.partition_positions:
                return
            if [box_new_x, box_new_y] in self.box_positions:
                return
            # Перемещение ящика
            index = self.box_positions.index([new_x, new_y])
            self.box_positions[index] = [box_new_x, box_new_y]
            # Перемещение игрока
            self.player_pos = [new_x, new_y]
        else:
            # Просто перемещаем игрока
            self.player_pos = [new_x, new_y]

        self.draw_objects()
        self.check_win()

    def check_win(self):
        # Условие победы: игрок на выходе и ящики на местах выхода
        if self.player_pos == self.exit_pos:
            # Проверка, есть ли ящики на выходе
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