# Script converted to Python

import pygame
import random
import math

# ===== НАСТРОЙКИ =====
WIDTH, HEIGHT = 1000, 1000
TILE_SIZE = 64
FPS = 120

# Цвета
GRASS = (107, 142, 35)
ROAD = (105, 105, 105)
WALL = (139, 90, 43)
PLAYER_COLOR = (255, 255, 0)
ZOMBIE_COLOR = (255, 0, 0)

# ===== ИНИЦИАЛИЗАЦИЯ =====
pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Project Zomboid Style - Python")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 24)

# ===== КАРТА =====
MAP_SIZE = 30
world_map = [[random.choice(['grass', 'grass', 'grass', 'road']) for _ in range(MAP_SIZE)] for _ in range(MAP_SIZE)]
# Добавляем здания
for x in range(3, 7):
    for y in range(3, 7):
        world_map[y][x] = 'wall'

# ===== ИГРОК =====
player_x, player_y = 5, 2
player_angle = 0

# ===== ЗОМБИ =====
zombies = []
for _ in range(5):
    zx = random.randint(0, MAP_SIZE-1)
    zy = random.randint(0, MAP_SIZE-1)
    if world_map[zy][zx] != 'wall':
        zombies.append([zx + 0.5, zy + 0.5, random.uniform(0, 0.5)])

# ===== ФУНКЦИИ =====
def cart_to_iso(x, y):
    """Перевод координат в изометрию"""
    iso_x = (x - y) * (TILE_SIZE // 2) + WIDTH // 2
    iso_y = (x + y) * (TILE_SIZE // 4) + 50
    return int(iso_x), int(iso_y)

def draw_isometric_tile(screen, x, y, tile_type):
    """Рисует изометрический тайл"""
    iso_x, iso_y = cart_to_iso(x, y)

    # Ромбовидный тайл
    points = [
        (iso_x, iso_y),
        (iso_x + TILE_SIZE // 2, iso_y + TILE_SIZE // 4),
        (iso_x, iso_y + TILE_SIZE // 2),
        (iso_x - TILE_SIZE // 2, iso_y + TILE_SIZE // 4)
    ]

    if tile_type == 'grass':
        color = GRASS
    elif tile_type == 'road':
        color = ROAD
    elif tile_type == 'wall':
        color = WALL

    pygame.draw.polygon(screen, color, points)
    pygame.draw.polygon(screen, (0, 0, 0), points, 1)

def draw_entity(screen, x, y, color, size=10):
    """Рисует персонажа в изометрии"""
    iso_x, iso_y = cart_to_iso(x, y)
    # Тень
    pygame.draw.ellipse(screen, (0, 0, 0, 100), 
                        (iso_x - size, iso_y - size//2, size*2, size), 0)
    # Тело
    pygame.draw.circle(screen, color, (iso_x, iso_y - size), size)
    # Голова
    pygame.draw.circle(screen, (255, 220, 180), (iso_x, iso_y - size*2), size//2)

def move_towards(zombie, target_x, target_y, speed):
    """Зомби идёт к цели"""
    dx = target_x - zombie[0]
    dy = target_y - zombie[1]
    dist = math.sqrt(dx**2 + dy**2)
    if dist > 0:
        zombie[0] += (dx / dist) * speed
        zombie[1] += (dy / dist) * speed

# ===== ИГРОВОЙ ЦИКЛ =====
running = True
while running:
    dt = clock.tick(FPS) / 1000.0

    # ===== СОБЫТИЯ =====
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # ===== УПРАВЛЕНИЕ =====
    keys = pygame.key.get_pressed()
    speed = 3 * dt

    new_x, new_y = player_x, player_y
    if keys[pygame.K_w] or keys[pygame.K_UP]:
        new_y -= speed
    if keys[pygame.K_s] or keys[pygame.K_DOWN]:
        new_y += speed
    if keys[pygame.K_a] or keys[pygame.K_LEFT]:
        new_x -= speed
    if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
        new_x += speed

    # Проверка столкновений
    if 0 <= new_x < MAP_SIZE and 0 <= new_y < MAP_SIZE:
        if world_map[int(new_y)][int(new_x)] != 'wall':
            player_x, player_y = new_x, new_y

    # ===== ЗОМБИ =====
    for z in zombies:
        move_towards(z, player_x, player_y, 1 * dt)
        # Столкновение зомби с игроком
        dist = math.sqrt((z[0] - player_x)**2 + (z[1] - player_y)**2)
        if dist < 0.5:
            # Игрок умирает
            player_x, player_y = 5, 2
            for zz in zombies:
                zz[0] = random.randint(0, MAP_SIZE-1) + 0.5
                zz[1] = random.randint(0, MAP_SIZE-1) + 0.5

    # ===== ОТРИСОВКА =====
    screen.fill((50, 50, 50))

    # Рисуем тайлы
    for y in range(MAP_SIZE):
        for x in range(MAP_SIZE):
            draw_isometric_tile(screen, x, y, world_map[y][x])

    # Рисуем зомби
    for z in zombies:
        draw_entity(screen, z[0], z[1], ZOMBIE_COLOR, 8)

    # Рисуем игрока
    draw_entity(screen, player_x, player_y, PLAYER_COLOR, 10)

    # ===== UI =====
    health_text = font.render("HP: 100%", True, (255, 255, 255))
    screen.blit(health_text, (10, 10))

    zombie_text = font.render(f"Зомби: {len(zombies)}", True, (255, 255, 255))
    screen.blit(zombie_text, (10, 35))

    controls = font.render("WASD - ходить | Изометрия 2.5D", True, (200, 200, 200))
    screen.blit(controls, (WIDTH//2 - 150, HEIGHT - 30))

    pygame.display.flip()

pygame.quit() покажи гден можно добавить еще однро здание