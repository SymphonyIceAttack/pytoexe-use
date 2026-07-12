import pygame
import random
import sys

# Размеры
WIDTH = 30          # ширина клетки в пикселях
HEIGHT = 30
MARGIN = 2          # отступ между клетками
SIZE = 16           # поле 16x16
MINES_COUNT = 40    # количество мин

SCREEN_WIDTH = SIZE * (WIDTH + MARGIN) + MARGIN
SCREEN_HEIGHT = SIZE * (HEIGHT + MARGIN) + MARGIN + 50  # +50 для текста

# Цвета
COLOR_BG = (192, 192, 192)
COLOR_CELL = (128, 128, 128)
COLOR_HIDDEN = (170, 170, 170)
COLOR_FLAG = (255, 0, 0)
COLOR_MINE = (0, 0, 0)
COLOR_NUM = {
    1: (0, 0, 255),
    2: (0, 128, 0),
    3: (255, 0, 0),
    4: (0, 0, 128),
    5: (128, 0, 0),
    6: (0, 128, 128),
    7: (0, 0, 0),
    8: (128, 128, 128),
}

class Minesweeper:
    def __init__(self, size, mines):
        self.size = size
        self.mines_count = mines
        self.board = [[0 for _ in range(size)] for _ in range(size)]
        self.revealed = [[False for _ in range(size)] for _ in range(size)]
        self.flags = [[False for _ in range(size)] for _ in range(size)]
        self.game_over = False
        self.win = False
        self.first_move = True
        self.generate_board()

    def generate_board(self, first_click=None):
        # Очистка
        self.board = [[0 for _ in range(self.size)] for _ in range(self.size)]
        if first_click:
            # Мины не должны быть в месте первого клика и вокруг него
            forbidden = []
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = first_click[0] + dx, first_click[1] + dy
                    if 0 <= nx < self.size and 0 <= ny < self.size:
                        forbidden.append((nx, ny))
            # Ставим мины
            mines_placed = 0
            while mines_placed < self.mines_count:
                x = random.randint(0, self.size - 1)
                y = random.randint(0, self.size - 1)
                if (x, y) not in forbidden and self.board[x][y] != -1:
                    self.board[x][y] = -1
                    mines_placed += 1
        else:
            # Обычная генерация
            positions = [(i, j) for i in range(self.size) for j in range(self.size)]
            random.shuffle(positions)
            for i in range(self.mines_count):
                x, y = positions[i]
                self.board[x][y] = -1
        # Подсчёт цифр
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == -1:
                    continue
                count = 0
                for dx in [-1, 0, 1]:
                    for dy in [-1, 0, 1]:
                        ni, nj = i + dx, j + dy
                        if 0 <= ni < self.size and 0 <= nj < self.size and self.board[ni][nj] == -1:
                            count += 1
                self.board[i][j] = count

    def reveal(self, x, y):
        if self.game_over or self.win:
            return
        if self.first_move:
            self.first_move = False
            self.generate_board((x, y))
            # Повторно подсчитаем цифры
            for i in range(self.size):
                for j in range(self.size):
                    if self.board[i][j] == -1:
                        continue
                    count = 0
                    for dx in [-1, 0, 1]:
                        for dy in [-1, 0, 1]:
                            ni, nj = i + dx, j + dy
                            if 0 <= ni < self.size and 0 <= nj < self.size and self.board[ni][nj] == -1:
                                count += 1
                    self.board[i][j] = count
        if self.flags[x][y]:
            return
        if self.board[x][y] == -1:
            self.game_over = True
            self.reveal_all_mines()
            return
        self._reveal_empty(x, y)
        self.check_win()

    def _reveal_empty(self, x, y):
        if self.revealed[x][y]:
            return
        self.revealed[x][y] = True
        if self.board[x][y] == 0:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.size and 0 <= ny < self.size and not self.revealed[nx][ny] and not self.flags[nx][ny]:
                        self._reveal_empty(nx, ny)

    def toggle_flag(self, x, y):
        if self.game_over or self.win:
            return
        if not self.revealed[x][y]:
            self.flags[x][y] = not self.flags[x][y]

    def reveal_all_mines(self):
        for i in range(self.size):
            for j in range(self.size):
                if self.board[i][j] == -1:
                    self.revealed[i][j] = True

    def check_win(self):
        opened = 0
        for i in range(self.size):
            for j in range(self.size):
                if self.revealed[i][j] and self.board[i][j] != -1:
                    opened += 1
        if opened == self.size * self.size - self.mines_count:
            self.win = True
            self.game_over = True

    def reset(self):
        self.__init__(self.size, self.mines_count)

def draw_text(screen, text, x, y, color=(0,0,0), size=30):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    screen.blit(img, (x, y))

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Сапёр")
    clock = pygame.time.Clock()
    game = Minesweeper(SIZE, MINES_COUNT)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and not game.game_over:
                x, y = event.pos
                # Определяем клетку
                col = (x - MARGIN) // (WIDTH + MARGIN)
                row = (y - MARGIN) // (HEIGHT + MARGIN)
                if 0 <= col < SIZE and 0 <= row < SIZE:
                    if event.button == 1:  # левая кнопка - открыть
                        game.reveal(col, row)
                    elif event.button == 3:  # правая - флаг
                        game.toggle_flag(col, row)
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.reset()
                    game.game_over = False
                    game.win = False
                    game.first_move = True

        # Рисование
        screen.fill(COLOR_BG)
        for i in range(SIZE):
            for j in range(SIZE):
                rect = pygame.Rect(MARGIN + i * (WIDTH + MARGIN),
                                   MARGIN + j * (HEIGHT + MARGIN),
                                   WIDTH, HEIGHT)
                if game.revealed[i][j]:
                    # Открытая клетка
                    pygame.draw.rect(screen, COLOR_CELL, rect)
                    if game.board[i][j] == -1:
                        pygame.draw.circle(screen, COLOR_MINE, rect.center, WIDTH//3)
                    elif game.board[i][j] > 0:
                        num = game.board[i][j]
                        color = COLOR_NUM.get(num, (0,0,0))
                        draw_text(screen, str(num), rect.x + WIDTH//3, rect.y + HEIGHT//4, color, WIDTH)
                else:
                    # Скрытая клетка
                    pygame.draw.rect(screen, COLOR_HIDDEN, rect)
                    pygame.draw.rect(screen, COLOR_BG, rect, 1)
                    if game.flags[i][j]:
                        # Рисуем флаг
                        pygame.draw.polygon(screen, COLOR_FLAG,
                                            [(rect.x+5, rect.y+5),
                                             (rect.x+WIDTH-10, rect.y+HEIGHT//2),
                                             (rect.x+5, rect.y+HEIGHT-5)])

        # Статус
        if game.game_over:
            if game.win:
                draw_text(screen, "ПОБЕДА! Нажми R для новой игры", 10, SCREEN_HEIGHT - 40, (0,200,0))
            else:
                draw_text(screen, "ПРОИГРЫШ! Нажми R для новой игры", 10, SCREEN_HEIGHT - 40, (200,0,0))
        else:
            draw_text(screen, f"Флагов: {sum(sum(row) for row in game.flags)} / {MINES_COUNT}", 10, SCREEN_HEIGHT - 40)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
