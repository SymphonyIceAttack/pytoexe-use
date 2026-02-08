import pygame
import time

# Инициализация
pygame.init()
screen = pygame.display.set_mode((400, 200))
pygame.display.set_caption("FPS Counter")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Arial", 64)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Очистка экрана (черный цвет)
    screen.fill((0, 0, 0))

    # Считаем FPS
    fps = str(int(clock.get_fps()))
    
    # Отрисовка текста
    fps_text = font.render(f"FPS: {fps}", True, (0, 255, 0))
    screen.blit(fps_text, (100, 70))

    pygame.display.flip()
    
    # Ограничение (например, до 60 FPS), или уберите число для максимума
    clock.tick(60) 

pygame.quit()
