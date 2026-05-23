import tkinter as tk
from tkinter import messagebox
import random
import math
import sys
import os

# Попытка импортировать pygame для звуков
try:
    import pygame
    pygame.mixer.init()
    SOUND_ENABLED = True
except ImportError:
    SOUND_ENABLED = False
    print("Pygame не установлен. Звуки отключены. Установите: pip install pygame")

# Константы
SIZE = 4  # Размер поля 4x4
TILE_SIZE = 100
BUTTON_SIZE = TILE_SIZE - 10
MARGIN = 5
WIDTH = SIZE * TILE_SIZE + 40
HEIGHT = SIZE * TILE_SIZE + 120

# Цвета (красочная палитра)
COLORS = {
    'bg': '#2C3E50',          # темно-синий фон
    'frame': '#34495E',       # рамка
    'tile': {
        0: '#ECF0F1',         # пустая клетка
        1: '#E74C3C',         # красный
        2: '#E67E22',         # оранжевый
        3: '#F1C40F',         # желтый
        4: '#2ECC71',         # зеленый
        5: '#1ABC9C',         # бирюзовый
        6: '#3498DB',         # синий
        7: '#9B59B6',         # фиолетовый
        8: '#34495E',         # темно-синий
        9: '#16A085',         # темно-бирюзовый
        10: '#27AE60',        # темно-зеленый
        11: '#2980B9',        # темно-синий
        12: '#8E44AD',        # темно-фиолетовый
        13: '#2C3E50',        # серо-синий
        14: '#D35400',        # темно-оранжевый
        15: '#C0392B'         # темно-красный
    },
    'text': '#FFFFFF',
    'win_bg': '#27AE60',
    'info': '#ECF0F1'
}

class FifteenPuzzle:
    def __init__(self, root):
        self.root = root
        self.root.title("Пятнашки - Puzzle 15")
        self.root.geometry(f"{WIDTH}x{HEIGHT}")
        self.root.configure(bg=COLORS['bg'])
        self.root.resizable(False, False)
        
        # Звуки
        self.move_sound = None
        self.win_sound = None
        if SOUND_ENABLED:
            try:
                # Создаем простые звуки (биперы) через pygame.mixer.Sound
                # Если файлов нет - используем встроенные beep через winsound (Windows) или print
                pass
            except:
                pass
        
        self.board = []
        self.empty_row = SIZE - 1
        self.empty_col = SIZE - 1
        self.moves = 0
        
        # Фрейм для информации
        info_frame = tk.Frame(root, bg=COLORS['bg'])
        info_frame.pack(pady=10)
        
        self.moves_label = tk.Label(info_frame, text="Ходов: 0", font=("Arial", 16, "bold"),
                                    fg=COLORS['info'], bg=COLORS['bg'])
        self.moves_label.pack(side=tk.LEFT, padx=20)
        
        self.reset_btn = tk.Button(info_frame, text="Новая игра", font=("Arial", 12, "bold"),
                                   bg=COLORS['frame'], fg=COLORS['text'],
                                   command=self.reset_game, cursor="hand2")
        self.reset_btn.pack(side=tk.LEFT, padx=20)
        
        self.shuffle_btn = tk.Button(info_frame, text="Перемешать", font=("Arial", 12, "bold"),
                                     bg=COLORS['frame'], fg=COLORS['text'],
                                     command=self.shuffle_board, cursor="hand2")
        self.shuffle_btn.pack(side=tk.LEFT, padx=20)
        
        # Фрейм для игрового поля
        self.game_frame = tk.Frame(root, bg=COLORS['frame'], bd=5, relief=tk.RAISED)
        self.game_frame.pack(pady=10)
        
        # Кнопки-плитки
        self.buttons = [[None for _ in range(SIZE)] for _ in range(SIZE)]
        
        self.create_board()
        self.reset_game()
    
    def play_sound(self, sound_type="move"):
        """Воспроизведение звука (простой beep через системный динамик)"""
        if not SOUND_ENABLED:
            return
        try:
            if sound_type == "move":
                # Короткий писк
                import winsound
                winsound.Beep(800, 50)
            elif sound_type == "win":
                import winsound
                winsound.Beep(1000, 200)
                winsound.Beep(1200, 200)
        except:
            # Если не Windows или нет winsound - просто пропускаем
            pass
    
    def create_board(self):
        """Создание игрового поля (кнопки)"""
        for i in range(SIZE):
            for j in range(SIZE):
                btn = tk.Button(self.game_frame, width=6, height=3,
                                font=("Arial", 24, "bold"),
                                relief=tk.RAISED, bd=3,
                                command=lambda r=i, c=j: self.move_tile(r, c))
                btn.grid(row=i, column=j, padx=MARGIN, pady=MARGIN)
                self.buttons[i][j] = btn
    
    def update_board(self):
        """Обновление отображения плиток"""
        for i in range(SIZE):
            for j in range(SIZE):
                value = self.board[i][j]
                if value == 0:  # пустая клетка
                    self.buttons[i][j].config(text="", state=tk.DISABLED,
                                              bg=COLORS['tile'][0],
                                              activebackground=COLORS['tile'][0])
                else:
                    self.buttons[i][j].config(text=str(value), state=tk.NORMAL,
                                              bg=COLORS['tile'][value % len(COLORS['tile'])],
                                              activebackground=COLORS['tile'][value % len(COLORS['tile'])],
                                              fg=COLORS['text'])
        
        self.moves_label.config(text=f"Ходов: {self.moves}")
    
    def is_solved(self):
        """Проверка, собрана ли головоломка"""
        correct = 1
        for i in range(SIZE):
            for j in range(SIZE):
                if i == SIZE-1 and j == SIZE-1:
                    if self.board[i][j] != 0:
                        return False
                else:
                    if self.board[i][j] != correct:
                        return False
                    correct += 1
        return True
    
    def move_tile(self, row, col):
        """Перемещение плитки, если возможно"""
        if (abs(row - self.empty_row) + abs(col - self.empty_col)) == 1:
            # Можно переместить
            self.board[self.empty_row][self.empty_col], self.board[row][col] = \
                self.board[row][col], self.board[self.empty_row][self.empty_col]
            self.empty_row, self.empty_col = row, col
            self.moves += 1
            self.update_board()
            self.play_sound("move")
            
            # Проверка победы
            if self.is_solved():
                self.play_sound("win")
                messagebox.showinfo("Поздравляем!", 
                                    f"Вы собрали головоломку за {self.moves} ходов!\nНажмите OK для новой игры.")
                self.reset_game()
    
    def reset_game(self):
        """Сброс игры (собранное состояние)"""
        self.board = [[i * SIZE + j + 1 for j in range(SIZE)] for i in range(SIZE)]
        self.board[SIZE-1][SIZE-1] = 0
        self.empty_row = SIZE - 1
        self.empty_col = SIZE - 1
        self.moves = 0
        self.update_board()
    
    def shuffle_board(self, steps=200):
        """Перемешивание поля случайными ходами"""
        for _ in range(steps):
            neighbors = []
            if self.empty_row > 0:
                neighbors.append((self.empty_row-1, self.empty_col))
            if self.empty_row < SIZE-1:
                neighbors.append((self.empty_row+1, self.empty_col))
            if self.empty_col > 0:
                neighbors.append((self.empty_row, self.empty_col-1))
            if self.empty_col < SIZE-1:
                neighbors.append((self.empty_row, self.empty_col+1))
            
            if neighbors:
                r, c = random.choice(neighbors)
                # Аналог move_tile без увеличения счетчика ходов и звуков
                self.board[self.empty_row][self.empty_col], self.board[r][c] = \
                    self.board[r][c], self.board[self.empty_row][self.empty_col]
                self.empty_row, self.empty_col = r, c
        
        self.moves = 0
        self.update_board()

def main():
    root = tk.Tk()
    game = FifteenPuzzle(root)
    
    # Центрирование окна
    root.update_idletasks()
    x = (root.winfo_screenwidth() // 2) - (WIDTH // 2)
    y = (root.winfo_screenheight() // 2) - (HEIGHT // 2)
    root.geometry(f"{WIDTH}x{HEIGHT}+{x}+{y}")
    
    root.mainloop()

if __name__ == "__main__":
    main()