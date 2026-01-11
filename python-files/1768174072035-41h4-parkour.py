import pygame
import sys

pygame.init()

# --- ОКНО ---
WIDTH, HEIGHT = 800, 450
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mini Parkour")
clock = pygame.time.Clock()

# --- ЦВЕТА ---
BG = (20, 20, 30)
PLAYER_COLOR = (80, 160, 255)
PLATFORM_COLOR = (60, 200, 120)

# --- ИГРОК ---
player = pygame.Rect(50, 300, 30, 30)
vel_y = 0
speed = 5
gravity = 1
jump_power = -16
on_ground = False

# --- ПЛАТФОРМЫ ---
platforms = [
    pygame.Rect(0, 400, 800, 50),
    pygame.Rect(200, 320, 120, 20),
    pygame.Rect(380, 260, 120, 20),
    pygame.Rect(560, 200, 120, 20),
]

# --- ИГРОВОЙ ЦИКЛ ---
running = True
while running:
    clock.tick(60)
    screen.fill(BG)

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    keys = pygame.key.get_pressed()

    # --- ДВИЖЕНИЕ ---
    if keys[pygame.K_a]:
        player.x -= speed
    if keys[pygame.K_d]:
        player.x += speed
    if keys[pygame.K_SPACE] and on_ground:
        vel_y = jump_power
        on_ground = False

    # --- ГРАВИТАЦИЯ ---
    vel_y += gravity
    player.y += vel_y

    on_ground = False
    for p in platforms:
        if player.colliderect(p) and vel_y >= 0:
            player.bottom = p.top
            vel_y = 0
            on_ground = True

    # --- ЕСЛИ УПАЛ ---
    if player.y > HEIGHT:
        player.x, player.y = 50, 300
        vel_y = 0

    # --- ОТРИСОВКА ---
    pygame.draw.rect(screen, PLAYER_COLOR, player)
    for p in platforms:
        pygame.draw.rect(screen, PLATFORM_COLOR, p)

    pygame.display.flip()

pygame.quit()
sys.exit()
