import pygame
import random

# Инициализация Pygame
pygame.init()

# Размеры окна
WIDTH, HEIGHT = 400, 700
CELL_SIZE = 30
COLS, ROWS = WIDTH // CELL_SIZE, HEIGHT // CELL_SIZE

# Цвета в стиле "Электроника"
ELECTRONIC_COLORS = {
    'background': (255, 255, 255),
    'button_bg': (255, 0, 0),
    'button_text': (255, 255, 0),
    'grid_line': (0, 0, 0),
    'grid_fill': (0, 0, 255),
    'text': (0, 0, 0),
    'score_bg': (255, 255, 0)
}

# Создаем окно
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Тетрис в стиле Электроника")

clock = pygame.time.Clock()

# Шрифты
font = pygame.font.SysFont('Verdana', 24, bold=True)
score_font = pygame.font.SysFont('Verdana', 20, bold=True)

# Кнопки
start_button = pygame.Rect(20, 10, 120, 40)
reset_button = pygame.Rect(160, 10, 130, 40)

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
                if 0 <= y + off_y < ROWS and 0 <= x + off_x < COLS:
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
            cell_value = grid[y][x]
            color = cell_value if cell_value != 0 else ELECTRONIC_COLORS['background']
            pygame.draw.rect(screen, color, (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE))
            pygame.draw.rect(screen, ELECTRONIC_COLORS['grid_line'], (x * CELL_SIZE, y * CELL_SIZE, CELL_SIZE, CELL_SIZE), 1)

def main():
    grid = create_grid()
    current_shape = None
    current_color = None
    current_pos = [0, 0]
    fall_time = 0
    fall_speed = 500  # миллисекунды
    score = 0
    game_over = False
    running = False

    def new_shape():
        shape = random.choice(SHAPES)
        color = random.randint(1, 7)  # 1-7, соответствуют цветам
        x = COLS // 2 - len(shape[0]) // 2
        y = -len(shape)
        return shape, color, [x, y]

    current_shape, current_color, current_pos = new_shape()

    while True:
        dt = clock.tick(60)
        if running and not game_over:
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
                    score += lines * 100
                    current_shape, current_color, current_pos = new_shape()
                    if not check_valid(grid, current_shape, current_pos):
                        game_over = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if start_button.collidepoint(event.pos):
                    # Старт новой игры
                    grid = create_grid()
                    current_shape, current_color, current_pos = new_shape()
                    score = 0
                    game_over = False
                    running = True
                elif reset_button.collidepoint(event.pos):
                    # Сброс
                    grid = create_grid()
                    current_shape, current_color, current_pos = new_shape()
                    score = 0
                    game_over = False
                    running = False
            elif event.type == pygame.KEYDOWN and running and not game_over:
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

        # Отрисовка
        screen.fill(ELECTRONIC_COLORS['background'])

        # Отрисовка кнопок
        pygame.draw.rect(screen, ELECTRONIC_COLORS['button_bg'], start_button)
        start_text = font.render("Старт", True, ELECTRONIC_COLORS['button_text'])
        screen.blit(start_text, (start_button.x + 20, start_button.y + 5))
        pygame.draw.rect(screen, ELECTRONIC_COLORS['button_bg'], reset_button)
        reset_text = font.render("Сброс", True, ELECTRONIC_COLORS['button_text'])
        screen.blit(reset_text, (reset_button.x + 20, reset_button.y + 5))

        # Отрисовка сетки
        draw_grid(grid)

        # Отрисовка текущей фигуры
        if not game_over:
            for y, row in enumerate(current_shape):
                for x, cell in enumerate(row):
                    if cell:
                        px = (current_pos[0] + x) * CELL_SIZE
                        py = (current_pos[1] + y) * CELL_SIZE
                        if py >= 0:
                            pygame.draw.rect(screen, ELECTRONIC_COLORS['grid_fill'], (px, py, CELL_SIZE, CELL_SIZE))
                            pygame.draw.rect(screen, ELECTRONIC_COLORS['background'], (px, py, CELL_SIZE, CELL_SIZE), 1)

        # Отображение очков
        score_rect = pygame.Rect(10, HEIGHT - 50, 180, 40)
        pygame.draw.rect(screen, ELECTRONIC_COLORS['score_bg'], score_rect)
        score_text = score_font.render(f"Очки: {score}", True, ELECTRONIC_COLORS['background'])
        screen.blit(score_text, (score_rect.x + 10, score_rect.y + 5))

        # Сообщение о конце игры
        if game_over:
            over_text = font.render("Игра окончена!", True, (255, 0, 0))
            screen.blit(over_text, (WIDTH // 2 - over_text.get_width() // 2, HEIGHT // 2 - over_text.get_height() // 2))

        pygame.display.flip()

if __name__ == "__main__":
    main()