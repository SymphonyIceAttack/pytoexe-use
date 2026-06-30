import pygame
import random

# رنگ‌ها
BG = (18, 18, 30)          # پس زمینه
CELL_COLOR = (30, 30, 45)  # خانه‌ها
WALL = (255, 255, 255)     # دیوار
PLAYER = (170, 0, 255)     # بازیکن
GOAL = (255, 215, 0)       # هدف
 
pygame.init()
SIZE = 400
screen = pygame.display.set_mode((SIZE, SIZE))
 
ROWS, COLS = 15, 15
CELL = (SIZE - 40) // max(ROWS, COLS)
OX = (SIZE - COLS * CELL) // 2
OY = (SIZE - ROWS * CELL) // 2 + 15
 
walls = [[set(['N','S','E','W']) for _ in range(COLS)] for _ in range(ROWS)]
vis = [[False]*COLS for _ in range(ROWS)]
 
def gen_maze():
    stack = [(0, 0)]
    vis[0][0] = True
    while stack:
        r, c = stack[-1]
        nb = []
        for dr, dc, d, opp in [(-1,0,'N','S'),(1,0,'S','N'),(0,1,'E','W'),(0,-1,'W','E')]:
            nr, nc = r+dr, c+dc
            if 0<=nr<ROWS and 0<=nc<COLS and not vis[nr][nc]:
                nb.append((nr, nc, d, opp))
        if nb:
            nr, nc, d, opp = random.choice(nb)
            walls[r][c].discard(d)
            walls[nr][nc].discard(opp)
            vis[nr][nc] = True
            stack.append((nr, nc))
        else:
            stack.pop()
 
gen_maze()
player = [0, 0]
goal = (ROWS-1, COLS-1)
moves = 0
win = False
 
def draw():
    screen.fill((240, 240, 240))
    wc = (40, 40, 60)
    for r in range(ROWS):
        for c in range(COLS):
            x = OX + c * CELL
            y = OY + r * CELL
            pygame.draw.rect(screen, (255,255,255), (x, y, CELL, CELL))
            if 'N' in walls[r][c]:
                pygame.draw.line(screen, wc, (x, y), (x+CELL, y), 2)
            if 'S' in walls[r][c]:
                pygame.draw.line(screen, wc, (x, y+CELL), (x+CELL, y+CELL), 2)
            if 'W' in walls[r][c]:
                pygame.draw.line(screen, wc, (x, y), (x, y+CELL), 2)
            if 'E' in walls[r][c]:
                pygame.draw.line(screen, wc, (x+CELL, y), (x+CELL, y+CELL), 2)
    # Goal
    gx = OX + goal[1]*CELL
    gy = OY + goal[0]*CELL
    pygame.draw.rect(screen, (50,200,50), (gx+3, gy+3, CELL-6, CELL-6))
    gf = pygame.font.Font(None, CELL-2)
    gt = gf.render('G', True, (255,255,255))
    screen.blit(gt, gt.get_rect(center=(gx+CELL//2, gy+CELL//2)))
    # Player
    px = OX + player[1]*CELL + CELL//2
    py = OY + player[0]*CELL + CELL//2
    pygame.draw.circle(screen, (52,152,219), (px, py), CELL//3)
    # Header
    font = pygame.font.Font(None, 24)
    screen.blit(font.render(f'Moves: {moves}', True, (80,80,80)), (10, 5))
    hf = pygame.font.Font(None, 16)
    screen.blit(hf.render('Tap direction to move', True, (150,150,150)), (10, 22))
    if win:
        ov = pygame.Surface((SIZE, SIZE))
        ov.fill((255,255,255))
        ov.set_alpha(180)
        screen.blit(ov, (0,0))
        bf = pygame.font.Font(None, 44)
        wt = bf.render('You Win!', True, (50,180,50))
        screen.blit(wt, wt.get_rect(center=(SIZE//2, SIZE//2-15)))
        sf = pygame.font.Font(None, 28)
        screen.blit(sf.render(f'{moves} moves - Tap for new maze', True, (80,80,80)),
                     sf.render(f'{moves} moves - Tap for new maze', True, (80,80,80)).get_rect(center=(SIZE//2, SIZE//2+20)))
    pygame.display.flip()
 
draw()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if win:
                for r in range(ROWS):
                    for c in range(COLS):
                        walls[r][c] = set(['N','S','E','W'])
                        vis[r][c] = False
                gen_maze()
                player = [0, 0]
                moves = 0
                win = False
                draw()
                continue
            tx, ty = event.pos
            px = OX + player[1]*CELL + CELL//2
            py = OY + player[0]*CELL + CELL//2
            dx = tx - px
            dy = ty - py
            moved = False
            if abs(dx) > abs(dy):
                if dx > 0 and 'E' not in walls[player[0]][player[1]]:
                  player[1] += 1; moved = True
                elif dx < 0 and 'W' not in walls[player[0]][player[1]]:
                    player[1] -= 1; moved = True
            else:
                if dy > 0 and 'S' not in walls[player[0]][player[1]]:
                    player[0] += 1; moved = True
                elif dy < 0 and 'N' not in walls[player[0]][player[1]]:
                    player[0] -= 1; moved = True
            if moved:
                moves += 1
                if player[0]==goal[0] and player[1]==goal[1]:
                    win = True
                draw()
    pygame.time.wait(50)
 
pygame.quit()  