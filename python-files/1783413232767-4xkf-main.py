import pygame
import random

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 300, 600
CELL_SIZE = 30
COLS, ROWS = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE

# Цвета
BLACK = (0, 0, 0)
GRAY = (128, 128, 128)
COLORS = [
    (0, 255, 255),  # Циан
    (0, 0, 255),    # Синий
    (255, 165, 0),  # Оранжевый
    (255, 255, 0),  # Желтый
    (0, 255, 0),    # Зеленый
    (128, 0, 128),  # Фиолетовый
    (255, 0, 0)     # Красный
]

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Тетрис")

clock = pygame.time.Clock()

# Фигуры тетриса
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 1], [1, 1]],  # O
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1, 0], [0, 1, 1]],  # S
    [[0, 1, 1], [1, 1, 0]]   # Z
]

def create_grid():
    return [[0 for _ in range(COLS)] for _ in range(ROWS)]

def rotate(shape):
    return [list(row) for row in zip(*shape[::-1])]

def check_valid(grid, shape, offset):
    off_x, off_y = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                new_x = x + off_x
                new_y = y + off_y
                if new_x < 0 or new_x >= COLS or new_y >= ROWS:
                    return False
                if new_y >= 0 and grid[new_y][new_x]:
                    return False
    return True

def join_shapes(grid, shape, offset, color):
    off_x, off_y = offset
    for y, row in enumerate(shape):
        for x, cell in enumerate(row):
            if cell:
                grid[y + off_y][x + off_x] = color

def clear_lines(grid):
    new_grid = [row for row in grid if any(cell == 0 for cell in row)]
    lines_cleared = ROWS - len(new_grid)
    while len(new_grid) < ROWS:
        new_grid.insert(0, [0 for _ in range(COLS)])
    return new_grid, lines_cleared

def draw_grid(grid):
    for y in range(ROWS):
        for x in range(COLS):
            color = COLORS[grid[y][x]-1] if grid[y][x] else GRAY
            pygame.draw.rect(screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, BLACK, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

def main():
    grid = create_grid()
    current_shape = None
    current_color = None
    current_pos = [0, 0]
    fall_time = 0
    fall_speed = 500  # миллисекунды
    running = False

    font = pygame.font.SysFont('Arial', 25)

    # Кнопки
    start_button = pygame.Rect(10, 10, 100, 30)
    reset_button = pygame.Rect(120, 10, 100, 30)

    def new_shape():
        shape = random.choice(SHAPES)
        color = random.randint(1, len(COLORS))
        x = COLS // 2 - len(shape[0]) // 2
        y = -len(shape)
        return shape, color, [x, y]

    current_shape, current_color, current_pos = new_shape()

    while True:
        dt = clock.tick(60)
        if running:
            fall_time += dt
            if fall_time > fall_speed:
                fall_time = 0
                new_pos = [current_pos[0], current_pos[1] + 1]
                if check_valid(grid, current_shape, new_pos):
                    current_pos = new_pos
                else:
                    # Закрепляем фигуру
                    join_shapes(grid, current_shape, current_pos, current_color)
                    grid, lines = clear_lines(grid)
                    current_shape, current_color, current_pos = new_shape()
                    if not check_valid(grid, current_shape, current_pos):
                        # Игра окончена
                        running = False

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    # Начинаем новую игру
                    grid = create_grid()
                    current_shape, current_color, current_pos = new_shape()
                    running = True
                elif reset_button.collidepoint(event.pos):
                    # Сброс игры
                    grid = create_grid()
                    current_shape, current_color, current_pos = new_shape()
                    running = False
            elif event.type == pygame.KEYDOWN and running:
                if event.key == pygame.K_LEFT:
                    new_pos = [current_pos[0] - 1, current_pos[1]]
                    if check_valid(grid, current_shape, new_pos):
                        current_pos = new_pos
                elif event.key == pygame.K_RIGHT:
                    new_pos = [current_pos[0] + 1, current_pos[1]]
                    if check_valid(grid, current_shape, new_pos):
                        current_pos = new_pos
                elif event.key == pygame.K_DOWN:
                    new_pos = [current_pos[0], current_pos[1] + 1]
                    if check_valid(grid, current_shape, new_pos):
                        current_pos = new_pos
                elif event.key == pygame.K_UP:
                    rotated_shape = rotate(current_shape)
                    if check_valid(grid, rotated_shape, current_pos):
                        current_shape = rotated_shape

        # Рисование
        screen.fill(BLACK)

        # Отрисовка кнопок
        pygame.draw.rect(screen, GRAY, start_button)
        pygame.draw.rect(screen, GRAY, reset_button)
        start_text = font.render("Старт", True, BLACK)
        reset_text = font.render("Сброс", True, BLACK)
        screen.blit(start_text, (start_button.x + 10, start_button.y + 5))
        screen.blit(reset_text, (reset_button.x + 10, reset_button.y + 5))

        # Отрисовка сетки
        draw_grid(grid)

        # Отрисовка текущей фигуры
        for y, row in enumerate(current_shape):
            for x, cell in enumerate(row):
                if cell:
                    px = (current_pos[0] + x) * CELL_SIZE
                    py = (current_pos[1] + y) * CELL_SIZE
                    if py >= 0:
                        pygame.draw.rect(screen, COLORS[current_color - 1], (px, py, CELL_SIZE, CELL_SIZE))
                        pygame.draw.rect(screen, BLACK, (px, py, CELL_SIZE, CELL_SIZE), 1)

        if not running:
            # Отображение сообщения о конце игры
            msg = font.render("Игра окончена!", True, (255, 0, 0))
            screen.blit(msg, (WIDTH // 2 - msg.get_width() // 2, HEIGHT // 2 - msg.get_height() // 2))

        pygame.display.flip()

if __name__ == "__main__":
    main()