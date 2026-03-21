import pygame
import sys
import random

pygame.init()

W, H = 1200, 700
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("和平精英")
clock = pygame.time.Clock()

WHITE  = (255,255,255)
BLACK  = (0,0,0)
RED    = (220,30,30)
GREEN  = (20,160,40)
BLUE   = (40,100,255)
SKIN   = (255,220,196)
HAIR   = (70,40,15)
PANTS  = (50,70,110)
YELLOW = (255,200,0)
ORANGE = (255,140,0)
CYAN   = (0,200,255)
GRAY   = (50,50,60)
DARK   = (18,18,22)
LGREEN = (0,200,0)

state = "splash"
load_progress = 0
selected_mode = "训练场"

player = {
    "x": 200, "y": H-100,
    "hp": 200, "max_hp": 200,
    "speed": 6,
    "vy": 0, "jump_pow": -17, "gravity": 0.8,
    "on_ground": True,
    "crouch": False, "prone": False,
}

mecha = None

def spawn_mecha():
    global mecha
    mecha = {
        "x": 600, "y": H-140,
        "hp": 2000, "max_hp": 2000,
        "weapon": "加特林",
        "overload": False, "over_time": 0,
        "dash_cd": 0, "shoot_cd": 0
    }

def txt(t, x, y, c=WHITE, s=28):
    f = pygame.font.Font(None, s)
    screen.blit(f.render(t, True, c), (x, y))

def draw_girl():
    x, y = player["x"], player["y"]
    if player["prone"]:
        pygame.draw.rect(screen, WHITE, (x-18, y-12, 42, 12))
        pygame.draw.circle(screen, SKIN, (x+10, y-6), 8)
        return
    ch = 35 if player["crouch"] else 70
    pygame.draw.rect(screen, WHITE, (x-18, y-ch, 36, 40))
    pygame.draw.rect(screen, PANTS, (x-16, y-ch+40, 32, 30))
    pygame.draw.circle(screen, SKIN, (x, y-ch+10), 14)
    pygame.draw.rect(screen, HAIR, (x-14, y-ch-6, 28, 8))
    pygame.draw.circle(screen, BLACK, (x-6, y-ch+8), 2)
    pygame.draw.circle(screen, BLACK, (x+6, y-ch+8), 2)

def draw_mecha():
    if not mecha: return
    x, y = mecha["x"], mecha["y"]
    color = (200,100,0) if mecha["overload"] else (100,100,180)
    pygame.draw.rect(screen, color, (x-40, y-100, 80, 100))
    pygame.draw.rect(screen, GRAY, (x-50, y-40, 100, 20))

def btn(t, x, y, w, h, c, fc):
    mx, my = pygame.mouse.get_pos()
    mb = pygame.mouse.get_pressed()
    col = c if x < mx < x+w and y < my < y+h else fc
    pygame.draw.rect(screen, col, (x, y, w, h))
    txt(t, x+10, y+8, WHITE, 26)
    return x < mx < x+w and y < my < y+h and mb[0]

# ==================== 主循环 ====================
while True:
    screen.fill(BLACK)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    if state == "splash":
        txt("和平精英", 450, 250, YELLOW, 80)
        txt("GAME FOR PEACE", 450, 340, WHITE, 32)
        pygame.display.update()
        pygame.time.delay(1500)
        state = "loading"

    elif state == "loading":
        txt("正在加载...", 460, 300, WHITE, 30)
        pygame.draw.rect(screen, DARK, (350, 380, 500, 30))
        pygame.draw.rect(screen, LGREEN, (350, 380, load_progress, 30))
        load_progress += 3
        if load_progress >= 500:
            state = "login"
        pygame.display.update()

    elif state == "login":
        txt("和平精英", 470, 150, YELLOW, 70)
        txt("请登录", 540, 280, WHITE, 36)
        
        if btn("  微信登录", 420, 350, 340, 60, (0,180,0), (0,120,0)):
            state = "hall"
        if btn("  QQ登录", 420, 430, 340, 60, (0,120,255), (0,80,200)):
            state = "hall"

    elif state == "hall":
        txt("和平精英", 500, 60, YELLOW, 64)
        if btn("开始游戏", 480, 220, 220, 60, BLUE, (20,40,90)):
            spawn_mecha()
            state = "game"
        txt(f"模式: {selected_mode}", 480, 300)
        if btn("训练场", 380, 400, 140, 50, BLUE, DARK):
            selected_mode = "训练场"
        if btn("经典", 540, 400, 140, 50, BLUE, DARK):
            selected_mode = "经典模式"
        if btn("地铁逃生", 700, 400, 140, 50, BLUE, DARK):
            selected_mode = "地铁逃生"

    elif state == "game":
        screen.fill((30,140,60) if selected_mode=="经典模式" else (40,40,50))
        txt(f"{selected_mode}", 20, 20)
        draw_girl()
        if selected_mode == "训练场":
            draw_mecha()

        keys = pygame.key.get_pressed()
        move = False
        if keys[pygame.K_a]:
            player["x"] -= player["speed"]
        if keys[pygame.K_d]:
            player["x"] += player["speed"]
        if keys[pygame.K_z]:
            player["crouch"] = True
        else:
            player["crouch"] = False
        if keys[pygame.K_c]:
            player["prone"] = True
        else:
            player["prone"] = False
        if keys[pygame.K_SPACE] and player["on_ground"]:
            player["vy"] = player["jump_pow"]
            player["on_ground"] = False

        player["vy"] += player["gravity"]
        player["y"] += player["vy"]
        if player["y"] >= H-100:
            player["y"] = H-100
            player["vy"] = 0
            player["on_ground"] = True

        if mecha:
            if btn("加特林", 800,200,140,50, BLUE,DARK):
                mecha["weapon"] = "加特林"
            if btn("激光", 800,260,140,50, RED,DARK):
                mecha["weapon"] = "激光"
            if btn("榴弹", 800,320,140,50, ORANGE,DARK):
                mecha["weapon"] = "榴弹"
            if btn("大刀", 800,380,140,50, GRAY,DARK):
                mecha["weapon"] = "大刀"
            if btn("过载", 800,440,140,50, ORANGE,DARK):
                mecha["overload"] = True
                mecha["over_time"] = 300
            if btn("冲刺", 800,500,140,50, CYAN,DARK):
                if mecha["dash_cd"] <= 0:
                    mecha["x"] += 180
                    mecha["dash_cd"] = 120
            mecha["dash_cd"] -= 1

    pygame.display.update()
    clock.tick(60)
