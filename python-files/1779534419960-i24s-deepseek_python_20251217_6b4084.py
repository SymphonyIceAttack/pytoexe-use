import pygame
import sys
import random
import math
from collections import deque

# Инициализация PyGame и микшера
pygame.init()
pygame.mixer.init()

# Размеры окна - УВЕЛИЧЕНО
SCREEN_WIDTH = 1400
SCREEN_HEIGHT = 1000

# Константы игры
BOARD_SIZE = 7
CELL_SIZE = 100  # Увеличенный размер клетки
BOARD_WIDTH = CELL_SIZE * BOARD_SIZE
BOARD_HEIGHT = CELL_SIZE * BOARD_SIZE
BOARD_OFFSET_X = (SCREEN_WIDTH - BOARD_WIDTH) // 2
BOARD_OFFSET_Y = 180

# Цвета шариков
COLORS = [
    (255, 50, 50),    # Красный
    (50, 200, 50),    # Зеленый
    (50, 100, 255),   # Синий
    (255, 200, 50),   # Желтый
    (200, 50, 200),   # Фиолетовый
    (50, 200, 200),   # Голубой
    (255, 150, 50),   # Оранжевый
]

# Другие цвета
BG_COLOR = (15, 20, 35)
GRID_COLOR = (70, 80, 120)
CELL_COLOR = (35, 40, 75)
SELECTED_COLOR = (120, 130, 180)
PATH_COLOR = (100, 200, 255)
TEXT_COLOR = (240, 240, 240)
SCORE_COLOR = (255, 215, 0)
NEXT_BALLS_COLOR = (45, 50, 90)
HIGHLIGHT_COLOR = (255, 255, 100)
AVAILABLE_MOVE_COLOR = (100, 255, 100, 100)

# Настройки игры
NEXT_BALLS_COUNT = 3
MIN_LINE_LENGTH = 3
INITIAL_BALLS = 5

# Создание окна
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Игра Линии 7x7")
clock = pygame.time.Clock()

# Загрузка шрифтов
try:
    title_font = pygame.font.Font(None, 80)
    score_font = pygame.font.Font(None, 56)
    info_font = pygame.font.Font(None, 40)
    ball_font = pygame.font.Font(None, 32)
except:
    title_font = pygame.font.SysFont('Arial', 80, bold=True)
    score_font = pygame.font.SysFont('Arial', 56)
    info_font = pygame.font.SysFont('Arial', 40)
    ball_font = pygame.font.SysFont('Arial', 32)

# Создание звуков
def create_sounds():
    sounds = {}
    
    try:
        # Звук выбора шарика
        sounds['select'] = pygame.mixer.Sound(buffer=bytes([150 + i % 50 for i in range(2000)]))
        sounds['select'].set_volume(0.3)
        
        # Звук движения шарика
        sounds['move'] = pygame.mixer.Sound(buffer=bytes([100 + (i * 2) % 100 for i in range(3000)]))
        sounds['move'].set_volume(0.2)
        
        # Звук удаления линии
        sounds['remove'] = pygame.mixer.Sound(buffer=bytes([(i // 2) % 256 for i in range(4000)]))
        sounds['remove'].set_volume(0.4)
        
        # Звук появления новых шариков
        sounds['appear'] = pygame.mixer.Sound(buffer=bytes([50 + i % 150 for i in range(2500)]))
        sounds['appear'].set_volume(0.3)
        
        # Звук кнопки
        sounds['button'] = pygame.mixer.Sound(buffer=bytes([120 + i % 60 for i in range(1500)]))
        sounds['button'].set_volume(0.2)
        
        # Звук ошибки
        sounds['error'] = pygame.mixer.Sound(buffer=bytes([(255 - i // 20) % 256 for i in range(1000)]))
        sounds['error'].set_volume(0.3)
        
        # Звук бонусных очков
        sounds['bonus'] = pygame.mixer.Sound(buffer=bytes([i % 256 for i in range(3000)]))
        sounds['bonus'].set_volume(0.4)
        
    except Exception as e:
        print(f"Ошибка создания звуков: {e}")
        class DummySound:
            def play(self): pass
            def set_volume(self, v): pass
        for key in ['select', 'move', 'remove', 'appear', 'button', 'error', 'bonus']:
            sounds[key] = DummySound()
    
    return sounds

sounds = create_sounds()

class Ball:
    def __init__(self, color_idx, x, y, cell_x, cell_y):
        self.color_idx = color_idx
        self.color = COLORS[color_idx]
        self.x = x
        self.y = y
        self.cell_x = cell_x
        self.cell_y = cell_y
        self.target_x = x
        self.target_y = y
        self.radius = CELL_SIZE // 2 - 12
        self.moving = False
        self.appearing = False
        self.removing = False
        self.animation_progress = 0
        self.scale = 1.0
        self.pulse = 0
        self.glow = 0
        
    def update(self, dt):
        if self.moving:
            self.animation_progress += dt * 4
            if self.animation_progress >= 1:
                self.animation_progress = 1
                self.x = self.target_x
                self.y = self.target_y
                self.moving = False
            else:
                # Плавное движение с easing
                t = self.animation_progress
                ease_t = t * t * (3 - 2 * t)  # Smoothstep
                self.x = self.x * (1 - ease_t) + self.target_x * ease_t
                self.y = self.y * (1 - ease_t) + self.target_y * ease_t
                
        elif self.appearing:
            self.animation_progress += dt * 5
            if self.animation_progress >= 1:
                self.animation_progress = 1
                self.appearing = False
            self.scale = self.animation_progress
            
        elif self.removing:
            self.animation_progress += dt * 7
            if self.animation_progress >= 1:
                self.animation_progress = 1
            self.scale = 1 - self.animation_progress
            
        # Пульсация для выделенных шариков
        if not (self.moving or self.appearing or self.removing):
            self.pulse = (math.sin(pygame.time.get_ticks() * 0.002) + 1) * 0.1
            
        # Свечение для новых шариков
        if self.appearing:
            self.glow = (math.sin(pygame.time.get_ticks() * 0.01) + 1) * 0.5
            
    def draw(self, screen):
        if self.scale <= 0:
            return
            
        x = int(self.x)
        y = int(self.y)
        radius = int(self.radius * self.scale)
        
        if radius <= 0:
            return
            
        # Свечение для новых шариков
        if self.glow > 0:
            glow_radius = int(radius * (1 + self.glow * 0.3))
            glow_surface = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surface, (*self.color, int(100 * self.glow)), 
                             (glow_radius, glow_radius), glow_radius)
            screen.blit(glow_surface, (x - glow_radius, y - glow_radius))
        
        # Тень
        shadow_offset = 5
        pygame.draw.circle(screen, (0, 0, 0, 150), 
                          (x + shadow_offset, y + shadow_offset), 
                          radius)
        
        # Основной шар
        pygame.draw.circle(screen, self.color, (x, y), radius)
        
        # Градиент для объема
        for i in range(3):
            grad_radius = radius - i * 3
            if grad_radius > 0:
                color_mult = 1.0 - i * 0.15
                grad_color = (
                    min(255, int(self.color[0] * color_mult)),
                    min(255, int(self.color[1] * color_mult)),
                    min(255, int(self.color[2] * color_mult))
                )
                pygame.draw.circle(screen, grad_color, (x, y), grad_radius)
        
        # Блик
        highlight_radius = radius * 0.5
        highlight_offset = radius * 0.3
        pygame.draw.circle(screen, (255, 255, 255, 220), 
                          (x - int(highlight_offset), y - int(highlight_offset)), 
                          int(highlight_radius))
        
        # Контур
        pygame.draw.circle(screen, (255, 255, 255), (x, y), radius, 4)
        
        # Пульсация если выделен
        if self.pulse > 0:
            pulse_radius = int(radius * (1 + self.pulse))
            pygame.draw.circle(screen, (*self.color, 120), (x, y), pulse_radius, 6)

class LinesGame:
    def __init__(self):
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_ball = None
        self.score = 0
        self.game_over = False
        self.win = False
        self.next_balls = []
        self.path = []
        self.balls_to_remove = []
        self.waiting_for_move = True
        self.animating = False
        self.move_completed = False
        self.new_balls_to_add = []
        self.combo = 0
        
        self.init_game()
        
    def init_game(self):
        # Очищаем поле
        self.board = [[None for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        self.selected_ball = None
        self.score = 0
        self.game_over = False
        self.win = False
        self.path = []
        self.balls_to_remove = []
        self.waiting_for_move = True
        self.animating = False
        self.move_completed = False
        self.new_balls_to_add = []
        self.combo = 0
        
        # Генерируем начальные шарики
        placed_balls = 0
        while placed_balls < INITIAL_BALLS:
            if self.add_random_ball(animate=False):
                placed_balls += 1
        
        # Генерируем следующие шарики
        self.generate_next_balls()
        
    def add_random_ball(self, animate=True, specific_color=None):
        empty_cells = []
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                if self.board[y][x] is None:
                    empty_cells.append((x, y))
        
        if not empty_cells:
            return False
            
        x, y = random.choice(empty_cells)
        
        if specific_color is not None:
            color_idx = specific_color
        else:
            color_idx = random.randint(0, len(COLORS) - 1)
        
        ball_x = BOARD_OFFSET_X + x * CELL_SIZE + CELL_SIZE // 2
        ball_y = BOARD_OFFSET_Y + y * CELL_SIZE + CELL_SIZE // 2
        
        ball = Ball(color_idx, ball_x, ball_y, x, y)
        
        if animate:
            ball.appearing = True
            ball.scale = 0
            ball.animation_progress = 0
            sounds['appear'].play()
        else:
            ball.scale = 1
            ball.appearing = False
            
        self.board[y][x] = ball
        
        # Проверяем линии только если это не начальная расстановка
        if animate:
            # Сохраняем шарик для последующей проверки
            self.new_balls_to_add.append((x, y, ball))
        
        return True
        
    def generate_next_balls(self):
        self.next_balls = []
        for _ in range(NEXT_BALLS_COUNT):
            color_idx = random.randint(0, len(COLORS) - 1)
            self.next_balls.append(color_idx)
    
    def get_cell_from_pos(self, pos):
        x, y = pos
        if (BOARD_OFFSET_X <= x < BOARD_OFFSET_X + BOARD_WIDTH and
            BOARD_OFFSET_Y <= y < BOARD_OFFSET_Y + BOARD_HEIGHT):
            cell_x = (x - BOARD_OFFSET_X) // CELL_SIZE
            cell_y = (y - BOARD_OFFSET_Y) // CELL_SIZE
            return int(cell_x), int(cell_y)
        return None, None
    
    def select_ball(self, cell_x, cell_y):
        if not (0 <= cell_x < BOARD_SIZE and 0 <= cell_y < BOARD_SIZE):
            return
            
        ball = self.board[cell_y][cell_x]
        if ball and not ball.removing and not ball.moving and not ball.appearing:
            if self.selected_ball == (cell_x, cell_y):
                self.selected_ball = None
                sounds['button'].play()
            else:
                self.selected_ball = (cell_x, cell_y)
                sounds['select'].play()
    
    def move_ball(self, from_x, from_y, to_x, to_y):
        if not (0 <= to_x < BOARD_SIZE and 0 <= to_y < BOARD_SIZE):
            sounds['error'].play()
            return False
            
        if self.board[to_y][to_x] is not None:
            sounds['error'].play()
            return False
            
        # Поиск пути
        path = self.find_path(from_x, from_y, to_x, to_y)
        if not path:
            sounds['error'].play()
            return False
            
        ball = self.board[from_y][from_x]
        if ball.removing or ball.moving or ball.appearing:
            return False
            
        self.board[from_y][from_x] = None
        self.board[to_y][to_x] = ball
        
        ball.cell_x = to_x
        ball.cell_y = to_y
        ball.target_x = BOARD_OFFSET_X + to_x * CELL_SIZE + CELL_SIZE // 2
        ball.target_y = BOARD_OFFSET_Y + to_y * CELL_SIZE + CELL_SIZE // 2
        ball.moving = True
        ball.animation_progress = 0
        
        self.selected_ball = None
        self.path = path
        self.waiting_for_move = False
        self.animating = True
        self.move_completed = True
        self.combo = 0  # Сброс комбо при новом ходе
        sounds['move'].play()
        
        return True
    
    def find_path(self, start_x, start_y, end_x, end_y):
        queue = deque()
        queue.append((start_x, start_y, []))
        visited = [[False for _ in range(BOARD_SIZE)] for _ in range(BOARD_SIZE)]
        visited[start_y][start_x] = True
        
        directions = [(0, -1), (1, 0), (0, 1), (-1, 0)]
        
        while queue:
            x, y, path = queue.popleft()
            
            if x == end_x and y == end_y:
                return path + [(x, y)]
            
            for dx, dy in directions:
                new_x, new_y = x + dx, y + dy
                
                if (0 <= new_x < BOARD_SIZE and 0 <= new_y < BOARD_SIZE and
                    not visited[new_y][new_x] and 
                    self.board[new_y][new_x] is None):
                    
                    visited[new_y][new_x] = True
                    queue.append((new_x, new_y, path + [(x, y)]))
        
        return None
    
    def check_lines_from_pos(self, x, y):
        """Проверяем линии от определенной позиции"""
        ball = self.board[y][x]
        if not ball:
            return []
        
        lines_found = []
        color_idx = ball.color_idx
        
        # Проверяем все направления
        directions = [
            [(0, 1), (0, -1)],   # Вертикаль
            [(1, 0), (-1, 0)],   # Горизонталь
            [(1, 1), (-1, -1)],  # Диагональ \
            [(1, -1), (-1, 1)]   # Диагональ /
        ]
        
        for dir_pair in directions:
            line = [(x, y)]
            
            # Проверяем в обе стороны
            for dx, dy in dir_pair:
                nx, ny = x + dx, y + dy
                while (0 <= nx < BOARD_SIZE and 0 <= ny < BOARD_SIZE and
                       self.board[ny][nx] and self.board[ny][nx].color_idx == color_idx):
                    line.append((nx, ny))
                    nx += dx
                    ny += dy
            
            if len(line) >= MIN_LINE_LENGTH:
                lines_found.extend(line)
        
        return list(set(lines_found))
    
    def check_all_lines(self):
        """Проверяем все линии на поле"""
        all_lines = []
        checked = set()
        
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                ball = self.board[y][x]
                if ball and (x, y) not in checked:
                    lines = self.check_lines_from_pos(x, y)
                    if lines:
                        all_lines.extend(lines)
                        for pos in lines:
                            checked.add(pos)
        
        return list(set(all_lines))
    
    def process_lines(self, lines_to_remove):
        """Обрабатываем найденные линии"""
        if not lines_to_remove:
            return False
            
        for x, y in lines_to_remove:
            ball = self.board[y][x]
            if ball and (cell_x, cell_y, ball) not in self.balls_to_remove:
                ball.removing = True
                ball.animation_progress = 0
                self.balls_to_remove.append((x, y, ball))
        
        # Начисляем очки с учетом комбо
        points = len(lines_to_remove) * 10
        if len(lines_to_remove) >= 5:
            points *= 2
            sounds['bonus'].play()
        
        self.combo += 1
        combo_multiplier = 1 + (self.combo - 1) * 0.5
        points = int(points * combo_multiplier)
        
        self.score += points
        sounds['remove'].play()
        
        return True
    
    def update(self, dt):
        # Обновляем все шарики
        self.animating = False
        
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                ball = self.board[y][x]
                if ball:
                    ball.update(dt)
                    if ball.moving or ball.appearing or ball.removing:
                        self.animating = True
        
        # Удаляем шарики после завершения анимации удаления
        new_balls_to_remove = []
        for x, y, ball in self.balls_to_remove:
            if ball.removing and ball.animation_progress < 1:
                new_balls_to_remove.append((x, y, ball))
            else:
                self.board[y][x] = None
        self.balls_to_remove = new_balls_to_remove
        
        # Если нет активных анимаций
        if not self.animating:
            # Если ход был завершен
            if self.move_completed:
                # Проверяем линии от перемещенного шарика
                lines_found = self.check_all_lines()
                if lines_found:
                    self.process_lines(lines_found)
                    self.animating = True
                else:
                    # Нет линий, добавляем новые шарики
                    self.add_new_balls()
                    self.move_completed = False
            
            # Если были добавлены новые шарики
            elif self.new_balls_to_add:
                # Проверяем линии от новых шариков
                lines_found = []
                for x, y, ball in self.new_balls_to_add:
                    if not ball.appearing:  # Шарик уже появился
                        lines = self.check_lines_from_pos(x, y)
                        if lines:
                            lines_found.extend(lines)
                
                if lines_found:
                    self.process_lines(list(set(lines_found)))
                    self.animating = True
                else:
                    # Разрешаем следующий ход
                    self.waiting_for_move = True
                
                self.new_balls_to_add = []
        
        # Проверка конца игры
        if not self.game_over and not self.animating:
            empty_cells = sum(1 for row in self.board for cell in row if cell is None)
            if empty_cells < NEXT_BALLS_COUNT:
                # Проверяем есть ли возможные ходы
                has_moves = False
                for y in range(BOARD_SIZE):
                    for x in range(BOARD_SIZE):
                        if self.board[y][x]:
                            # Ищем пустые клетки, куда можно пойти
                            for ty in range(BOARD_SIZE):
                                for tx in range(BOARD_SIZE):
                                    if self.board[ty][tx] is None:
                                        if self.find_path(x, y, tx, ty):
                                            has_moves = True
                                            break
                                if has_moves:
                                    break
                        if has_moves:
                            break
                    if has_moves:
                        break
                
                if not has_moves:
                    self.game_over = True
                    self.win = (self.score > 100)  # Условная победа
    
    def add_new_balls(self):
        """Добавляет новые шарики после хода"""
        if not self.next_balls:
            self.generate_next_balls()
        
        balls_added = 0
        while self.next_balls and balls_added < NEXT_BALLS_COUNT:
            color_idx = self.next_balls[balls_added]
            if not self.add_random_ball(animate=True, specific_color=color_idx):
                # Нет свободных клеток
                self.game_over = True
                break
            balls_added += 1
        
        if balls_added > 0:
            self.next_balls = self.next_balls[balls_added:]
    
    def draw(self, screen):
        # Фон с градиентом
        for y in range(SCREEN_HEIGHT):
            color_value = int(15 + y / SCREEN_HEIGHT * 10)
            pygame.draw.line(screen, (color_value, color_value + 5, color_value + 20), 
                           (0, y), (SCREEN_WIDTH, y))
        
        # Декоративные элементы фона
        for i in range(20):
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size = random.randint(2, 5)
            color = random.choice(COLORS)
            pygame.draw.circle(screen, (*color, 30), (x, y), size)
        
        # Рамка игрового поля
        border_rect = pygame.Rect(
            BOARD_OFFSET_X - 20, BOARD_OFFSET_Y - 20,
            BOARD_WIDTH + 40, BOARD_HEIGHT + 40
        )
        pygame.draw.rect(screen, (60, 70, 110), border_rect, border_radius=20)
        pygame.draw.rect(screen, (90, 100, 150), border_rect, 5, border_radius=20)
        
        # Фон игрового поля
        pygame.draw.rect(screen, CELL_COLOR, 
                        (BOARD_OFFSET_X - 10, BOARD_OFFSET_Y - 10, 
                         BOARD_WIDTH + 20, BOARD_HEIGHT + 20), 
                        border_radius=15)
        
        # Сетка
        for i in range(BOARD_SIZE + 1):
            # Вертикальные линии
            pygame.draw.line(screen, GRID_COLOR,
                           (BOARD_OFFSET_X + i * CELL_SIZE, BOARD_OFFSET_Y),
                           (BOARD_OFFSET_X + i * CELL_SIZE, BOARD_OFFSET_Y + BOARD_HEIGHT),
                           4)
            # Горизонтальные линии
            pygame.draw.line(screen, GRID_COLOR,
                           (BOARD_OFFSET_X, BOARD_OFFSET_Y + i * CELL_SIZE),
                           (BOARD_OFFSET_X + BOARD_WIDTH, BOARD_OFFSET_Y + i * CELL_SIZE),
                           4)
        
        # Подсветка доступных ходов
        if self.selected_ball and self.waiting_for_move:
            sel_x, sel_y = self.selected_ball
            for y in range(BOARD_SIZE):
                for x in range(BOARD_SIZE):
                    if self.board[y][x] is None:
                        if self.find_path(sel_x, sel_y, x, y):
                            # Полупрозрачный зеленый квадрат
                            move_surface = pygame.Surface((CELL_SIZE - 20, CELL_SIZE - 20), pygame.SRCALPHA)
                            move_surface.fill((100, 255, 100, 80))
                            screen.blit(move_surface, 
                                      (BOARD_OFFSET_X + x * CELL_SIZE + 10,
                                       BOARD_OFFSET_Y + y * CELL_SIZE + 10))
        
        # Подсветка выбранной клетки
        if self.selected_ball:
            sel_x, sel_y = self.selected_ball
            rect = pygame.Rect(
                BOARD_OFFSET_X + sel_x * CELL_SIZE + 5,
                BOARD_OFFSET_Y + sel_y * CELL_SIZE + 5,
                CELL_SIZE - 10,
                CELL_SIZE - 10
            )
            pygame.draw.rect(screen, SELECTED_COLOR, rect, 6, border_radius=10)
            
            # Анимация выбора
            pulse_size = (math.sin(pygame.time.get_ticks() * 0.003) + 1) * 0.1
            pulse_rect = pygame.Rect(
                BOARD_OFFSET_X + sel_x * CELL_SIZE + 5 - int(CELL_SIZE * pulse_size),
                BOARD_OFFSET_Y + sel_y * CELL_SIZE + 5 - int(CELL_SIZE * pulse_size),
                CELL_SIZE - 10 + int(CELL_SIZE * pulse_size * 2),
                CELL_SIZE - 10 + int(CELL_SIZE * pulse_size * 2)
            )
            pygame.draw.rect(screen, (*SELECTED_COLOR, 100), pulse_rect, 3, border_radius=10)
        
        # Путь перемещения
        if self.path and len(self.path) > 1:
            points = []
            for x, y in self.path:
                center_x = BOARD_OFFSET_X + x * CELL_SIZE + CELL_SIZE // 2
                center_y = BOARD_OFFSET_Y + y * CELL_SIZE + CELL_SIZE // 2
                points.append((center_x, center_y))
            
            # Рисуем путь с градиентом
            for i in range(len(points) - 1):
                start_pos = points[i]
                end_pos = points[i + 1]
                color_value = int(100 + i * 30)
                path_color = (color_value, min(255, color_value + 100), 255)
                pygame.draw.line(screen, path_color, start_pos, end_pos, 8)
            
            # Точки на пути
            for i, point in enumerate(points):
                radius = 10 if i == 0 or i == len(points) - 1 else 8
                color = (255, 255, 0) if i == len(points) - 1 else (100, 200, 255)
                pygame.draw.circle(screen, color, point, radius)
                pygame.draw.circle(screen, (255, 255, 255), point, radius, 2)
        
        # Рисуем шарики
        for y in range(BOARD_SIZE):
            for x in range(BOARD_SIZE):
                ball = self.board[y][x]
                if ball:
                    ball.draw(screen)
        
        # Интерфейс
        self.draw_ui(screen)
        
        # Сообщение о конце игры
        if self.game_over:
            self.draw_game_over(screen)
    
    def draw_ui(self, screen):
        # Заголовок
        title = title_font.render("ИГРА ЛИНИИ 7x7", True, TEXT_COLOR)
        screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 40))
        
        # Счет
        score_bg = pygame.Rect(SCREEN_WIDTH // 2 - 200, 120, 400, 70)
        pygame.draw.rect(screen, (40, 45, 80), score_bg, border_radius=15)
        pygame.draw.rect(screen, (70, 80, 130), score_bg, 4, border_radius=15)
        
        score_text = score_font.render(f"СЧЁТ: {self.score}", True, SCORE_COLOR)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 135))
        
        # Комбо
        if self.combo > 1:
            combo_text = info_font.render(f"КОМБО x{self.combo}!", True, (255, 100, 100))
            screen.blit(combo_text, (SCREEN_WIDTH // 2 - combo_text.get_width() // 2, 185))
        
        # Статус игры
        status_y = BOARD_OFFSET_Y + BOARD_HEIGHT + 40
        if self.game_over:
            status = "ИГРА ЗАВЕРШЕНА"
            color = (255, 100, 100)
        elif not self.waiting_for_move or self.animating:
            status = "ПРОИСХОДИТ АНИМАЦИЯ..."
            color = (255, 200, 100)
        else:
            status = "ВАШ ХОД! ВЫБЕРИТЕ ШАРИК"
            color = (100, 255, 100)
        
        status_text = info_font.render(status, True, color)
        screen.blit(status_text, (SCREEN_WIDTH // 2 - status_text.get_width() // 2, status_y))
        
        # Следующие шарики
        next_y = status_y + 60
        next_title = info_font.render("СЛЕДУЮЩИЕ ШАРИКИ:", True, TEXT_COLOR)
        screen.blit(next_title, (SCREEN_WIDTH // 2 - next_title.get_width() // 2, next_y))
        
        # Фон для следующих шариков
        next_bg_width = NEXT_BALLS_COUNT * 80 + 60
        next_bg_x = SCREEN_WIDTH // 2 - next_bg_width // 2
        next_bg_rect = pygame.Rect(next_bg_x, next_y + 40, next_bg_width, 100)
        pygame.draw.rect(screen, NEXT_BALLS_COLOR, next_bg_rect, border_radius=15)
        pygame.draw.rect(screen, (70, 80, 130), next_bg_rect, 4, border_radius=15)
        
        # Рисуем следующие шарики
        for i, color_idx in enumerate(self.next_balls):
            color = COLORS[color_idx]
            ball_x = SCREEN_WIDTH // 2 - (NEXT_BALLS_COUNT * 80) // 2 + i * 80 + 40
            ball_y = next_y + 90
            
            # Свечение
            glow_surface = pygame.Surface((70, 70), pygame.SRCALPHA)
            glow = (math.sin(pygame.time.get_ticks() * 0.005 + i) + 1) * 0.3
            pygame.draw.circle(glow_surface, (*color, int(100 * glow)), (35, 35), 35)
            screen.blit(glow_surface, (ball_x - 35, ball_y - 35))
            
            # Шарик
            pygame.draw.circle(screen, color, (ball_x, ball_y), 30)
            
            # Объем
            pygame.draw.circle(screen, 
                             (min(255, color[0] + 50),
                              min(255, color[1] + 50),
                              min(255, color[2] + 50)),
                             (ball_x, ball_y), 20)
            
            # Контур
            pygame.draw.circle(screen, (255, 255, 255), (ball_x, ball_y), 30, 4)
            
            # Блик
            pygame.draw.circle(screen, (255, 255, 255, 200), 
                             (ball_x - 10, ball_y - 10), 12)
            
            # Номер
            num_text = ball_font.render(str(i + 1), True, (255, 255, 255))
            screen.blit(num_text, (ball_x - num_text.get_width() // 2, 
                                 ball_y - num_text.get_height() // 2))
        
        # Инструкция
        instr_y = next_y + 170
        instructions = [
            "1. КЛИКНИТЕ НА ШАРИК, ЧТОБЫ ВЫБРАТЬ ЕГО",
            "2. КЛИКНИТЕ НА ПОДСВЕЧЕННУЮ КЛЕТКУ, ЧТОБЫ ПЕРЕМЕСТИТЬ",
            "3. СОБЕРИТЕ 3+ ШАРИКОВ В ЛИНИЮ (ГОРИЗОНТАЛЬНО, ВЕРТИКАЛЬНО ИЛИ ПО ДИАГОНАЛИ)",
            "4. ЛИНИЯ ИСЧЕЗНЕТ И ВЫ ПОЛУЧИТЕ ОЧКИ!",
            "5. ПОСЛЕ КАЖДОГО ХОДА ПОЯВЛЯЮТСЯ 3 НОВЫХ ШАРИКА"
        ]
        
        for i, text in enumerate(instructions):
            instr_bg = pygame.Rect(SCREEN_WIDTH // 2 - 550, instr_y + i * 42 - 5, 1100, 40)
            pygame.draw.rect(screen, (30, 35, 65, 200), instr_bg, border_radius=8)
            
            instr_text = info_font.render(text, True, (200, 220, 255))
            screen.blit(instr_text, (SCREEN_WIDTH // 2 - instr_text.get_width() // 2, 
                                    instr_y + i * 42))
    
    def draw_game_over(self, screen):
        # Полупрозрачный фон
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 220))
        screen.blit(overlay, (0, 0))
        
        # Рамка сообщения
        message_rect = pygame.Rect(SCREEN_WIDTH // 2 - 300, SCREEN_HEIGHT // 2 - 150, 600, 300)
        pygame.draw.rect(screen, (40, 45, 80), message_rect, border_radius=20)
        pygame.draw.rect(screen, (70, 80, 130), message_rect, 6, border_radius=20)
        
        # Сообщение
        if self.win:
            message = "ПОБЕДА!"
            color = (100, 255, 100)
            sub_message = "Отличный результат!"
        else:
            message = "ИГРА ОКОНЧЕНА"
            color = (255, 100, 100)
            sub_message = "Попробуйте еще раз!"
        
        msg_text = title_font.render(message, True, color)
        screen.blit(msg_text, (SCREEN_WIDTH // 2 - msg_text.get_width() // 2, 
                              SCREEN_HEIGHT // 2 - 100))
        
        score_text = score_font.render(f"ИТОГОВЫЙ СЧЁТ: {self.score}", True, SCORE_COLOR)
        screen.blit(score_text, (SCREEN_WIDTH // 2 - score_text.get_width() // 2, 
                                SCREEN_HEIGHT // 2 - 20))
        
        sub_text = info_font.render(sub_message, True, (200, 200, 255))
        screen.blit(sub_text, (SCREEN_WIDTH // 2 - sub_text.get_width() // 2, 
                              SCREEN_HEIGHT // 2 + 30))
        
        restart_text = info_font.render("НАЖМИТЕ R ДЛЯ НОВОЙ ИГРЫ ИЛИ ESC ДЛЯ ВЫХОДА", 
                                      True, TEXT_COLOR)
        screen.blit(restart_text, (SCREEN_WIDTH // 2 - restart_text.get_width() // 2, 
                                  SCREEN_HEIGHT // 2 + 100))

class Button:
    def __init__(self, x, y, width, height, text, action=None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.action = action
        self.hovered = False
        self.color = (60, 70, 120)
        self.hover_color = (80, 90, 140)
        self.clicked = False
    
    def draw(self, screen):
        color = self.hover_color if self.hovered else self.color
        
        # Тень
        shadow_rect = self.rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        pygame.draw.rect(screen, (0, 0, 0, 100), shadow_rect, border_radius=10)
        
        # Кнопка
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (100, 110, 180), self.rect, 3, border_radius=10)
        
        # Эффект нажатия
        if self.clicked:
            pygame.draw.rect(screen, (255, 255, 255, 50), self.rect, border_radius=10)
        
        text = info_font.render(self.text, True, TEXT_COLOR)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)
    
    def check_hover(self, pos):
        self.hovered = self.rect.collidepoint(pos)
        return self.hovered
    
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered and self.action:
                self.clicked = True
                sounds['button'].play()
                return self.action()
        elif event.type == pygame.MOUSEBUTTONUP:
            self.clicked = False
        return None

def main():
    game = LinesGame()
    
    # Создание кнопки новой игры
    button_width = 220
    button_height = 60
    restart_button = Button(SCREEN_WIDTH - button_width - 40, 40, 
                           button_width, button_height, 
                           "НОВАЯ ИГРА", lambda: game.init_game())
    
    running = True
    last_time = pygame.time.get_ticks()
    
    while running:
        current_time = pygame.time.get_ticks()
        dt = (current_time - last_time) / 1000.0
        last_time = current_time
        
        mouse_pos = pygame.mouse.get_pos()
        
        # Обработка событий
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Клавиши
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_r:
                    game.init_game()
                    sounds['button'].play()
            
            # Кнопка мыши
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                # Проверяем клик по игровому полю
                cell_x, cell_y = game.get_cell_from_pos(mouse_pos)
                
                if cell_x is not None and cell_y is not None:
                    if not game.game_over and game.waiting_for_move and not game.animating:
                        if game.selected_ball:
                            # Пытаемся переместить выбранный шарик
                            if game.move_ball(game.selected_ball[0], game.selected_ball[1], 
                                           cell_x, cell_y):
                                print(f"Шарик перемещен с ({game.selected_ball[0]},{game.selected_ball[1]}) на ({cell_x},{cell_y})")
                        else:
                            # Выбираем шарик
                            game.select_ball(cell_x, cell_y)
                            if game.selected_ball:
                                print(f"Шарик выбран: ({cell_x},{cell_y})")
                
                # Проверяем кнопку
                restart_button.handle_event(event)
        
        # Обновление игры
        game.update(dt)
        
        # Проверка наведения на кнопку
        restart_button.check_hover(mouse_pos)
        
        # Отрисовка
        game.draw(screen)
        restart_button.draw(screen)
        
        # Подсказка в углу
        hint_text = info_font.render("ESC - выход, R - новая игра", True, (180, 180, 220))
        screen.blit(hint_text, (20, SCREEN_HEIGHT - 50))
        
        # Отладочная информация
        debug_y = SCREEN_HEIGHT - 100
        debug_texts = [
            f"Состояние: {'ход' if game.waiting_for_move else 'анимация' if game.animating else 'обработка'}",
            f"Следующих шариков: {len(game.next_balls)}",
            f"Шариков на удаление: {len(game.balls_to_remove)}",
            f"Комбо: {game.combo}",
            f"Свободных клеток: {sum(1 for row in game.board for cell in row if cell is None)}"
        ]
        
        for i, text in enumerate(debug_texts):
            debug_text = ball_font.render(text, True, (150, 200, 150))
            screen.blit(debug_text, (20, debug_y + i * 20))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()