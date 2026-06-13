import random
import pygame
from pygame.version import PygameVersion
# размер окна
WNDW = 1000
WNDH = 700
FPS = 60
# цвета
black = (23,0,40)
White = (255,255,255)
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
Yellow  = (255,255,0)
orange = (255,165,0)
gray = (128,128,128)
brown = (128,0,0)

pygame.init()
pygame.mixer.init()
wnd = pygame.display.set_mode((WNDW,WNDH))
pygame.display.set_caption('space game')
cl = pygame.time.Clock()

ship_size = 150
ship_speed = 15
rock_size = 150
rock_speed = 20
bullet_speed = 25
max_xp = 10
hp = max_xp
score = 0
gui_font = pygame.font.SysFont('', 30, False, False)

ship_box = pygame.Rect(0, 0, ship_size, ship_size)
ship_box.bottom = WNDH
ship_box.centerx = WNDW // 2

rock_box = pygame.Rect(0, 0, rock_size, rock_size)
rock_box.bottom = -rock_size
rock_box.centerx = random.randint(rock_size//2, WNDW - rock_size//2)

rock_box2 = pygame.Rect(0, 0, rock_size, rock_size)
rock_box2.bottom = -rock_size*4
rock_box2.centerx = random.randint(rock_size//2, WNDW - rock_size//2)

rock_box3 = pygame.Rect(0, 0, rock_size, rock_size)
rock_box3.bottom = -rock_size*6
rock_box3.centerx = random.randint(rock_size//2, WNDW - rock_size//2)

bullet_list = []

ship_img_o = pygame.image.load('img/ship1.png')
rock_img_o = pygame.image.load('img/asteroid1.png')
rock_img2_o = pygame.image.load('img/asteroid2.png')
rock_img3_o = pygame.image.load('img/asteroid3.png')

ship_img = pygame.transform.scale(ship_img_o, (ship_size, ship_size))
rock_img = pygame.transform.scale(rock_img_o, (rock_size, rock_size))
rock_img2 = pygame.transform.scale(rock_img2_o, (rock_size, rock_size))
rock_img3 = pygame.transform.scale(rock_img3_o, (rock_size, rock_size))

run = True

while run:

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bullet_box = pygame.Rect(0, 0, 4, 12)
                bullet_box.centerx = ship_box.centerx
                bullet_box.bottom = ship_box.top
                bullet_list.append(bullet_box)

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        ship_box.x -= ship_speed
    if keys[pygame.K_RIGHT]:
        ship_box.x += ship_speed
    if keys[pygame.K_ESCAPE]:
        run = False

    for bullet_box in bullet_list:
        bullet_box.centery -= bullet_speed
        if bullet_box.bottom < 0:
            bullet_list.remove(bullet_box)
        else:
            if bullet_box.colliderect(rock_box):
                bullet_list.remove(bullet_box)
                rock_box.bottom = -rock_size
                rock_box.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)
                score += 1
            elif bullet_box.colliderect(rock_box2):
                bullet_list.remove(bullet_box)
                rock_box2.bottom = -rock_size
                rock_box2.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)
                score += 1
            elif bullet_box.colliderect(rock_box3):
                bullet_list.remove(bullet_box)
                rock_box3.bottom = -rock_size
                rock_box3.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)
                score += 1


    rock_box.y += rock_speed
    if rock_box.top > WNDH:
        rock_box.bottom = -rock_size
        rock_box.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)

    rock_box2.y += rock_speed
    if rock_box2.top > WNDH:
        rock_box2.bottom = -rock_size
        rock_box2.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)

    rock_box3.y += rock_speed
    if rock_box3.top > WNDH:
        rock_box3.bottom = -rock_size
        rock_box3.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)

    if ship_box.colliderect(rock_box):
        hp -= 1
        rock_box.bottom = -rock_size
        rock_box.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)
    if ship_box.colliderect(rock_box2):
        hp -= 1
        rock_box2.bottom = -rock_size
        rock_box2.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)
    if ship_box.colliderect(rock_box3):
        hp -= 1
        rock_box3.bottom = -rock_size
        rock_box3.centerx = random.randint(rock_size // 2, WNDW - rock_size // 2)

    if hp <= 0:
        run = False

    wnd.fill(black)
    #pygame.draw.rect(wnd, WHITE, rock_box)
    wnd.blit(rock_img, rock_box)
    #pygame.draw.rect(wnd, WHITE, rock_box2)
    wnd.blit(rock_img2, rock_box2)
    #pygame.draw.rect(wnd, WHITE, rock_box3)
    wnd.blit(rock_img3, rock_box3)
    #pygame.draw.rect(wnd, YELLOW, ship_box)
    wnd.blit(ship_img, ship_box)

    for bullet_box in bullet_list:
        pygame.draw.rect(wnd, red, bullet_box)

    txt = gui_font.render(f'HP: {hp}', True, red)
    wnd.blit(txt, (0, 0))

    txt = gui_font.render(f'Очки: {score}', True, red)
    wnd.blit(txt, (0, 20))

    pygame.display.update()
    cl.tick(FPS)
pygame.quit()
