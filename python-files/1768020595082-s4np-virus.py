import pygame
import random
import sys

pygame.init()

# Get screen size
info = pygame.display.Info()
WIDTH = info.current_w
HEIGHT = info.current_h

BOTTOM_GAP = 80  # leave bottom visible

screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.NOFRAME)
pygame.display.set_caption("SYSTEM ERROR")

clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 60, bold=True)

def random_color():
    return (random.randint(0,255), random.randint(0,255), random.randint(0,255))

running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        if event.type == pygame.QUIT:
            running = False

    # Flashing colors
    for y in range(0, HEIGHT - BOTTOM_GAP, 40):
        for x in range(0, WIDTH, 40):
            pygame.draw.rect(screen, random_color(), (x, y, 40, 40))

    # Fake warning text
    text = font.render("!! SYSTEM COMPROMISED !!", True, (255,255,255))
    screen.blit(text, (WIDTH//2 - text.get_width()//2, 50))

    sub = pygame.font.SysFont("Arial", 30).render("Press ESC to exit", True, (255,255,255))
    screen.blit(sub, (WIDTH//2 - sub.get_width()//2, 120))

    pygame.display.flip()
    clock.tick(30)

pygame.quit()
sys.exit()
