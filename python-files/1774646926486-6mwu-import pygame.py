import pygame
import random

pygame.init()

# Window
screen = pygame.display.set_mode((600, 400))
clock = pygame.time.Clock()

# Player
player = pygame.Rect(50, 150, 30, 30)

# Obstacle
wall = pygame.Rect(600, random.randint(0, 350), 20, 50)

running = True
while running:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Controls
    keys = pygame.key.get_pressed()
    if keys[pygame.K_UP]:
        player.y -= 5
    if keys[pygame.K_DOWN]:
        player.y += 5

    # Move wall
    wall.x -= 5
    if wall.x < 0:
        wall.x = 600
        wall.y = random.randint(0, 350)

    # Collision
    if player.colliderect(wall):
        print("Game Over!")
        running = False

    pygame.draw.rect(screen, (0, 255, 0), player)
    pygame.draw.rect(screen, (255, 0, 0), wall)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()