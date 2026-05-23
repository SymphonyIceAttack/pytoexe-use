import pygame
import random
import os

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Константы
WINDOW_SIZE = 500
GRID_SIZE = 4
CELL_SIZE = WINDOW_SIZE // GRID_SIZE
FPS = 60

# Цвета
BACKGROUND = (30, 30, 40)
EMPTY_CELL = (50, 50, 65)
CELL_COLORS = [
    (255, 107, 107),  # Красный
    (78, 205, 196),  # Бирюзовый
    (255, 230, 109),  # Жёлтый
    (26, 83, 92),  # Тёмный бирюзовый
    (247, 255, 247),  # Белый
    (255, 159, 28),  # Оранжевый
    (138, 43, 226),  # Фиолетовый
    (0, 200, 83),  # Зелёный
    (255, 64, 129),  # Розовый
    (63, 81, 181),  # Индиго
    (0, 188, 212),  # Голубой
    (255, 87, 34),  # Оранжевый-красный
    (156, 39, 176),  # Пурпурный
    (76, 175, 80),  # Светло-зелёный
    (255, 193, 7),  # Янтарный
]

# Создание окна
screen = pygame.display.set_mode((WINDOW_SIZE, WINDOW_SIZE + 80))
pygame.display.set_caption("🧩 Пятнашки")
clock = pygame.time.Clock()

# Шрифты
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)


# Звуки (генерируем программно, если нет файлов)
def create_beep_sound(frequency, duration, volume=0.3):
    sample_rate = 44100
    samples = int(sample_rate * duration)
    sound_data = bytearray()

    for i in range(samples):
        t = i / sample_rate
        # Генерация волны с затуханием
        value = int(volume * 127 * (1 - t / duration) *
                    (1 if int(t * frequency * 2) % 2 == 0 else -1))
        sound_data.append(128 + value)
        sound_data.append(128 + value)

    return pygame.mixer.Sound(buffer=bytes(sound_data))


# Создаём звуки
try:
    move_sound = create_beep_sound(800, 0.1)
    win_sound = create_beep_sound(523, 0.2)  # До
    win_sound2 = create_beep_sound(659, 0.2)  # Ми
    win_sound3 = create_beep_sound(784, 0.3)  # Соль
    error_sound = create_beep_sound(200, 0.15)
except:
    move_sound = None
    win_sound = None


class PuzzleGame:
    def __init__(self):
        self.grid = []
        self.empty_pos = (3, 3)
        self.moves = 0
        self.won = False
        self.particles = []
        self.init_grid()

    def init_grid(self):
        # Создаём решённую сетку
        numbers = list(range(1, GRID_SIZE * GRID_SIZE)) + [0]
        self.grid = [numbers[i:i + GRID_SIZE] for i in range(0, len(numbers), GRID_SIZE)]
        self.empty_pos = (GRID_SIZE - 1, GRID_SIZE - 1)
        self.moves = 0
        self.won = False

        # Перемешиваем (делаем случайные валидные ходы)
        self.shuffle(150)

    def shuffle(self, moves_count):
        for _ in range(moves_count):
            neighbors = self.get_neighbors(self.empty_pos)
            if neighbors:
                row, col = random.choice(neighbors)
                self.grid[self.empty_pos[0]][self.empty_pos[1]] = self.grid[row][col]
                self.grid[row][col] = 0
                self.empty_pos = (row, col)
        self.moves = 0

    def get_neighbors(self, pos):
        row, col = pos
        neighbors = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_row, new_col = row + dr, col + dc
            if 0 <= new_row < GRID_SIZE and 0 <= new_col < GRID_SIZE:
                neighbors.append((new_row, new_col))
        return neighbors

    def can_move(self, row, col):
        er, ec = self.empty_pos
        return abs(row - er) + abs(col - ec) == 1

    def move(self, row, col):
        if self.can_move(row, col) and not self.won:
            self.grid[self.empty_pos[0]][self.empty_pos[1]] = self.grid[row][col]
            self.grid[row][col] = 0
            self.empty_pos = (row, col)
            self.moves += 1

            # Звук хода
            if move_sound:
                move_sound.play()

            # Частицы
            self.add_particles(
                col * CELL_SIZE + CELL_SIZE // 2,
                row * CELL_SIZE + CELL_SIZE // 2,
                CELL_COLORS[self.grid[self.empty_pos[0]][self.empty_pos[1]] - 1]
                if self.grid[self.empty_pos[0]][self.empty_pos[1]] > 0
                else (255, 255, 255)
            )

            self.check_win()
            return True
        else:
            if error_sound:
                error_sound.play()
            return False

    def check_win(self):
        expected = 1
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                if row == GRID_SIZE - 1 and col == GRID_SIZE - 1:
                    if self.grid[row][col] != 0:
                        return False
                else:
                    if self.grid[row][col] != expected:
                        return False
                    expected += 1
        self.won = True
        # Победная мелодия
        if win_sound:
            win_sound.play()
            pygame.time.wait(200)
            win_sound2.play()
            pygame.time.wait(200)
            win_sound3.play()
        return True

    def add_particles(self, x, y, color):
        for _ in range(10):
            self.particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-3, 3),
                'life': 30,
                'color': color,
                'size': random.randint(3, 6)
            })

    def update_particles(self):
        for p in self.particles[:]:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1
            p['size'] = max(1, p['size'] - 0.2)
            if p['life'] <= 0:
                self.particles.remove(p)

    def draw_rounded_rect(self, surface, color, rect, radius):
        pygame.draw.rect(surface, color, rect, border_radius=radius)

    def draw(self):
        # Фон
        screen.fill(BACKGROUND)

        # Заголовок
        title = font_medium.render("🧩 Пятнашки", True, (255, 255, 255))
        screen.blit(title, (WINDOW_SIZE // 2 - title.get_width() // 2, 10))

        # Счётчик ходов
        moves_text = font_small.render(f"Ходов: {self.moves}", True, (200, 200, 200))
        screen.blit(moves_text, (20, 50))

        # Кнопка "Новая игра"
        restart_rect = pygame.Rect(WINDOW_SIZE - 150, 45, 130, 35)
        pygame.draw.rect(screen, (78, 205, 196), restart_rect, border_radius=8)
        restart_text = font_small.render("Новая игра", True, (30, 30, 40))
        screen.blit(restart_text, (restart_rect.centerx - restart_text.get_width() // 2,
                                   restart_rect.centery - restart_text.get_height() // 2))

        # Игровое поле
        board_offset_y = 80

        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                x = col * CELL_SIZE + 5
                y = row * CELL_SIZE + board_offset_y + 5
                rect = pygame.Rect(x, y, CELL_SIZE - 10, CELL_SIZE - 10)

                if self.grid[row][col] == 0:
                    # Пустая ячейка
                    self.draw_rounded_rect(screen, EMPTY_CELL, rect, 12)
                else:
                    # Ячейка с числом
                    num = self.grid[row][col]
                    color_idx = (num - 1) % len(CELL_COLORS)
                    color = CELL_COLORS[color_idx]

                    # Градиентный эффект (светлее сверху)
                    self.draw_rounded_rect(screen, color, rect, 12)

                    # Обводка
                    pygame.draw.rect(screen,
                                     (min(255, c + 30) for c in color),
                                     rect, width=2, border_radius=12)

                    # Тень (эффект 3D)
                    shadow_rect = rect.copy()
                    shadow_rect.y += 3
                    pygame.draw.rect(screen,
                                     (max(0, c - 40) for c in color),
                                     shadow_rect, border_radius=12)

                    # Число
                    text = font_large.render(str(num), True, (255, 255, 255))
                    text_shadow = font_large.render(str(num), True, (0, 0, 0, 100))

                    text_x = x + (CELL_SIZE - 10) // 2 - text.get_width() // 2
                    text_y = y + (CELL_SIZE - 10) // 2 - text.get_height() // 2

                    screen.blit(text_shadow, (text_x + 2, text_y + 2))
                    screen.blit(text, (text_x, text_y))

        # Частицы
        for p in self.particles:
            alpha = int(255 * (p['life'] / 30))
            color = (*p['color'][:3], alpha)
            pygame.draw.circle(screen, p['color'], (int(p['x']), int(p['y'])), int(p['size']))

        # Экран победы
        if self.won:
            overlay = pygame.Surface((WINDOW_SIZE, WINDOW_SIZE + 80))
            overlay.fill((0, 0, 0))
            overlay.set_alpha(180)
            screen.blit(overlay, (0, 0))

            win_text = font_large.render("🎉 Победа!", True, (255, 215, 0))
            win_rect = win_text.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 20))
            screen.blit(win_text, win_rect)

            moves_win = font_medium.render(f"За {self.moves} ходов", True, (255, 255, 255))
            moves_rect = moves_win.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 80))
            screen.blit(moves_win, moves_rect)

            hint = font_small.render("Нажмите R для новой игры", True, (200, 200, 200))
            hint_rect = hint.get_rect(center=(WINDOW_SIZE // 2, WINDOW_SIZE // 2 + 130))
            screen.blit(hint, hint_rect)


def main():
    game = PuzzleGame()
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    game.init_grid()
                elif event.key == pygame.K_ESCAPE:
                    running = True

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    x, y = event.pos

                    # Проверка кнопки "Новая игра"
                    restart_rect = pygame.Rect(WINDOW_SIZE - 150, 45, 130, 35)
                    if restart_rect.collidepoint(x, y):
                        game.init_grid()
                        continue

                    # Проверка клика по ячейке
                    board_offset_y = 80
                    if y > board_offset_y:
                        col = x // CELL_SIZE
                        row = (y - board_offset_y) // CELL_SIZE
                        if 0 <= row < GRID_SIZE and 0 <= col < GRID_SIZE:
                            game.move(row, col)

            elif event.type == pygame.MOUSEMOTION:
                # Эффект наведения можно добавить здесь
                pass

        game.update_particles()
        game.draw()
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()