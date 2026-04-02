import pygame
import math
import random
import sys

# Инициализация
pygame.init()
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Horror - Escape the Dungeon")
clock = pygame.time.Clock()

# Цвета
BLACK = (0,0,0)
WHITE = (255,255,255)
RED = (200,0,0)
GREEN = (0,200,0)
BLUE = (0,0,200)
DARK_GREY = (40,40,40)

# Карта лабиринта (1 - стена, 0 - проход, 2 - ключ, 3 - враг, 4 - выход)
MAP = [
    [1,1,1,1,1,1,1,1,1,1],
    [1,0,0,0,1,0,0,0,0,1],
    [1,0,1,0,1,0,1,0,0,1],
    [1,0,1,0,0,0,1,0,2,1],
    [1,0,1,1,1,0,1,0,0,1],
    [1,0,0,0,3,0,0,0,0,1],
    [1,1,1,0,1,1,1,0,1,1],
    [1,0,0,0,0,0,0,0,0,1],
    [1,0,0,0,1,0,4,0,0,1],
    [1,1,1,1,1,1,1,1,1,1],
]
MAP_SIZE = len(MAP)
TILE_SIZE = 1.0  # условный размер тайла

# Параметры игрока
pos_x, pos_y = 1.5, 1.5
angle = 0
fov = math.pi / 3
move_speed = 2.0
rot_speed = 2.5
health = 100
has_key = False
game_over = False
win = False

# Параметры врага (патрулирует или идет к игроку)
enemy_x, enemy_y = 5.5, 4.5
enemy_alive = True

# Звук (писк через pygame.mixer)
pygame.mixer.init()
def beep(frequency, duration):
    sample_rate = 44100
    n_samples = int(sample_rate * duration)
    buf = pygame.sndarray.make_sound(bytearray(n_samples * 2))
    # Упрощенно: используем pygame.mixer.Sound сгенерированный
    # Но для простоты - встроенный звук
    pass

# Функция для проверки столкновения со стенами
def is_wall(x, y):
    ix = int(x)
    iy = int(y)
    if ix < 0 or iy < 0 or ix >= MAP_SIZE or iy >= MAP_SIZE:
        return True
    return MAP[iy][ix] == 1

# Функция рендеринга 3D (рейкастинг)
def render():
    global health, game_over, win, has_key, enemy_alive, enemy_x, enemy_y
    screen.fill(BLACK)
    # Рейкастинг для каждого столбца экрана
    for col in range(WIDTH):
        # Угол луча
        ray_angle = angle - fov/2 + (col / WIDTH) * fov
        # Начальные координаты
        ray_x = pos_x
        ray_y = pos_y
        # Направление
        dir_x = math.cos(ray_angle)
        dir_y = math.sin(ray_angle)
        # Длина шага
        step_x = 1 if dir_x > 0 else -1
        step_y = 1 if dir_y > 0 else -1
        # Расстояние до следующей вертикальной/горизонтальной границы
        next_x = (int(ray_x) + (1 if dir_x > 0 else 0)) if dir_x != 0 else float('inf')
        next_y = (int(ray_y) + (1 if dir_y > 0 else 0)) if dir_y != 0 else float('inf')
        delta_x = 1/abs(dir_x) if dir_x != 0 else float('inf')
        delta_y = 1/abs(dir_y) if dir_y != 0 else float('inf')
        # DDA
        hit = False
        side = 0
        while not hit:
            if next_x < next_y:
                ray_x = next_x
                next_x += delta_x
                side = 0
            else:
                ray_y = next_y
                next_y += delta_y
                side = 1
            if is_wall(ray_x - (dir_x * 0.001), ray_y - (dir_y * 0.001)):
                hit = True
        # Расстояние
        if side == 0:
            dist = abs(ray_x - pos_x) / abs(dir_x) if dir_x != 0 else float('inf')
        else:
            dist = abs(ray_y - pos_y) / abs(dir_y) if dir_y != 0 else float('inf')
        # Коррекция fish-eye
        dist *= math.cos(angle - ray_angle)
        # Высота стены
        wall_height = HEIGHT / (dist + 0.0001)
        # Цвет стены (чем дальше - тем темнее)
        shade = 1.0 - min(1.0, dist / 8)
        if side == 0:
            color = (int(100 * shade), int(100 * shade), int(100 * shade))
        else:
            color = (int(70 * shade), int(70 * shade), int(70 * shade))
        # Рисуем столбец
        y_start = max(0, HEIGHT//2 - wall_height//2)
        y_end = min(HEIGHT, HEIGHT//2 + wall_height//2)
        pygame.draw.rect(screen, color, (col, y_start, 1, y_end - y_start))
    
    # Интерфейс
    font = pygame.font.SysFont("Arial", 24)
    health_text = font.render(f"HP: {health}", True, RED)
    screen.blit(health_text, (10, 10))
    key_text = font.render(f"Key: {'Yes' if has_key else 'No'}", True, WHITE)
    screen.blit(key_text, (10, 40))
    if game_over:
        over = font.render("GAME OVER - Press R to restart", True, RED)
        screen.blit(over, (WIDTH//2-150, HEIGHT//2))
    elif win:
        win_text = font.render("YOU ESCAPED! Press R to play again", True, GREEN)
        screen.blit(win_text, (WIDTH//2-150, HEIGHT//2))
    
    # Враг (спрайт) - рисуем красный квадрат в 3D пространстве (не реализовано, упрощенно)
    # Для простоты - если враг виден и жив, накладываем эффект
    if enemy_alive and not game_over and not win:
        # Вычисляем угол до врага
        dx = enemy_x - pos_x
        dy = enemy_y - pos_y
        enemy_dist = math.sqrt(dx*dx + dy*dy)
        if enemy_dist < 2:
            health -= 0.5
            if health <= 0:
                game_over = True
    pygame.display.flip()

# Движение врага
def update_enemy():
    global enemy_x, enemy_y, health, game_over
    if not enemy_alive or game_over:
        return
    dx = pos_x - enemy_x
    dy = pos_y - enemy_y
    dist = math.sqrt(dx*dx + dy*dy)
    if dist < 0.5:
        health -= 15
        if health <= 0:
            game_over = True
        # Отбросить врага назад
        enemy_x -= dx * 0.5
        enemy_y -= dy * 0.5
    elif dist < 5:
        # Движение к игроку
        step = 0.03
        new_x = enemy_x + dx/dist * step
        new_y = enemy_y + dy/dist * step
        if not is_wall(new_x, new_y):
            enemy_x, enemy_y = new_x, new_y

# Проверка сбора ключа и выхода
def check_interaction():
    global has_key, win, game_over
    ix, iy = int(pos_x), int(pos_y)
    if 0 <= ix < MAP_SIZE and 0 <= iy < MAP_SIZE:
        if MAP[iy][ix] == 2:
            has_key = True
            MAP[iy][ix] = 0  # убрать ключ
            # звук
        if MAP[iy][ix] == 4 and has_key:
            win = True
        if MAP[iy][ix] == 3 and enemy_alive:
            # враг уже существует, но на карте клетка 3 - стартовая позиция
            pass

# Главный цикл
def main():
    global pos_x, pos_y, angle, health, game_over, win, has_key, enemy_alive, enemy_x, enemy_y
    running = True
    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r and (game_over or win):
                    # Рестарт
                    pos_x, pos_y = 1.5, 1.5
                    angle = 0
                    health = 100
                    game_over = False
                    win = False
                    has_key = False
                    enemy_alive = True
                    enemy_x, enemy_y = 5.5, 4.5
                    # Восстановить карту
                    for i in range(MAP_SIZE):
                        for j in range(MAP_SIZE):
                            if MAP[i][j] == 2 or MAP[i][j] == 4:
                                MAP[i][j] = 0
                    MAP[3][8] = 2
                    MAP[8][6] = 4
                    MAP[5][4] = 3
        if not game_over and not win:
            keys = pygame.key.get_pressed()
            # Движение вперед-назад
            if keys[pygame.K_w]:
                new_x = pos_x + math.cos(angle) * move_speed * 0.016
                new_y = pos_y + math.sin(angle) * move_speed * 0.016
                if not is_wall(new_x, new_y):
                    pos_x, pos_y = new_x, new_y
            if keys[pygame.K_s]:
                new_x = pos_x - math.cos(angle) * move_speed * 0.016
                new_y = pos_y - math.sin(angle) * move_speed * 0.016
                if not is_wall(new_x, new_y):
                    pos_x, pos_y = new_x, new_y
            # Поворот
            if keys[pygame.K_a]:
                angle -= rot_speed * 0.016
            if keys[pygame.K_d]:
                angle += rot_speed * 0.016
            # Обновление врага
            update_enemy()
            check_interaction()
        render()
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()