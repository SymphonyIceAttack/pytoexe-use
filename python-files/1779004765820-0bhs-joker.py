import pygame
import sys
import os

pygame.init()

screen_width, screen_height = 1980, 1080
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('joker')

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 20, 20)
GREEN = (0, 255, 0)

font = pygame.font.Font("KAIU.TTF", 100)
text_surface = font.render("你的电脑已经被我黑了！等死吧！", True, GREEN)
text_rect = text_surface.get_rect()
text_rect.center = (screen_width // 2, screen_height // 2 - 100)

try:
    image_path = "屏幕截图 2026-05-17 153746.png" 
    if not os.path.exists(image_path):
        raise FileNotFoundError
    my_image = pygame.image.load(image_path)
except FileNotFoundError:
    print("未找到图片文件，使用红色矩形代替演示")
    my_image = pygame.Surface((100, 100))
    my_image.fill((255, 0, 0))

image_rect = my_image.get_rect()
screen_rect = screen.get_rect()
image_rect.bottomright = screen_rect.bottomright

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    screen.fill(BLACK)
    screen.blit(text_surface, text_rect)
    screen.blit(my_image, image_rect)
    pygame.display.flip()

pygame.quit()
sys.exit()