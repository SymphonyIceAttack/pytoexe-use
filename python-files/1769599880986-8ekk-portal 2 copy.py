# portal_like.py
# Оригинальная игра, вдохновлённая Portal (но это не копия).
# Требуется: pygame
# pip install pygame
#
# Управление:
# - WASD / стрелки — движение
# - ЛКМ — выстрелить оранжевый портал
# - ПКМ — выстрелить синий портал
# - R — перезарядить уровень
# - Esc — выйти
#
# Цель: добраться до "G" (goal). Порталы помогают перемещаться, сохраняется скорость и направление,
# учитывается ориентация порталов. Уровни усложняются.

import pygame
import math
import sys
from collections import deque

pygame.init()
WIDTH, HEIGHT = 1200, 720
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
CLOCK = pygame.time.Clock()
FONT = pygame.font.SysFont("Arial", 20)

TILE = 48  # размер тайла
GRAVITY = 0.8
PLAYER_RADIUS = 14
PLAYER_SPEED = 4.0
JUMP_SPEED = -12
MAX_FPS = 60

# Цвета
BG = (30, 30, 40)
WALL_COLOR = (200, 200, 200)
PLAYER_COLOR = (255, 240, 200)
PORTAL_ORANGE = (255, 140, 0)
PORTAL_BLUE = (80, 180, 255)
GOAL_COLOR = (200, 255, 180)
BUTTON_COLOR = (230, 120, 230)
DOOR_COLOR = (100, 100, 120)

# ---- Уровни (массив строк). Используй символы:
# W - стена, . - пусто, S - старт игрока, G - цель (exit)
# B - кнопка (будет открывать дверь D), D - дверь (старт закрыта)
# Можно создавать уникальные уровни по образцу.
LEVELS = [
    [
        "WWWWWWWWWWWWWWWWWWWWWWWW",
        "W.................D....W",
        "W......................W",
        "W.....W........W.......W",
        "W.....W........W.......W",
        "W.....W........W...G...W",
        "W.....W........W.......W",
        "W.....W........W.......W",
        "W......................W",
        "W.........S............W",
        "WWWWWWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWWWWWW",
        "W...W...............G..W",
        "W...W..WWWWWW........W.W",
        "W...W........W........W.W",
        "W...W........W........W.W",
        "W...W........W........W.W",
        "W...W........W........W.W",
        "W...W........W........W.W",
        "W..............B......W",
        "W.......S.............W",
        "WWWWWWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWWWWWW",
        "W......................W",
        "W..WWW......WWW........W",
        "W..W.GW....W...W.......W",
        "W..W..W....W...W.......W",
        "W..W..W....W...W.......W",
        "W..W..WWWWWW...W.......W",
        "W..W............W......W",
        "W..W..B.........W......W",
        "W.S.............W......W",
        "WWWWWWWWWWWWWWWWWWWWWWWW",
    ],
    [
        "WWWWWWWWWWWWWWWWWWWWWWWW",
        "W.............W........W",
        "W.............W...G....W",
        "W..WWW........W........W",
        "W..W.BW.......W........W",
        "W..W..W........W.......W",
        "W..W..W........W.......W",
        "W..W..WWWWWWWWWWW......W",
        "W......................W",
        "W.S...................W",
        "WWWWWWWWWWWWWWWWWWWWWWWW",
    ],
]

# Вспомогательные функции
def text(s, x, y, color=(240,240,240)):
    surf = FONT.render(s, True, color)
    SCREEN.blit(surf, (x,y))

def clamp(v, a, b):
    return max(a, min(b, v))

# Игровые сущности
class Level:
    def __init__(self, layout):
        self.layout = layout
        self.h = len(layout)
        self.w = len(layout[0])
        self.width_px = self.w * TILE
        self.height_px = self.h * TILE
        self.player_start = None
        self.goal_rect = None
        self.buttons = []  # (tilex,tiley,activated)
        self.doors = {}    # {(tilex,tiley): open_bool}
        self.parse()

    def parse(self):
        for y, row in enumerate(self.layout):
            for x, ch in enumerate(row):
                if ch == "S":
                    self.player_start = (x*TILE + TILE//2, y*TILE + TILE//2)
                elif ch == "G":
                    self.goal_rect = pygame.Rect(x*TILE, y*TILE, TILE, TILE)
                elif ch == "B":
                    self.buttons.append([x, y, False])
                elif ch == "D":
                    self.doors[(x,y)] = False

    def tile_at(self, tx, ty):
        if 0 <= ty < self.h and 0 <= tx < self.w:
            return self.layout[ty][tx]
        return "W"  # вне уровня считаем стеной

    def is_solid_at(self, tx, ty):
        ch = self.tile_at(tx,ty)
        if ch == "W": return True
        if ch == "D" and not self.doors.get((tx,ty), False): return True
        return False

    def draw(self, cam_rect):
        # отрисовка видимой части
        start_x = max(0, cam_rect.left // TILE)
        end_x = min(self.w, (cam_rect.right)//TILE + 1)
        start_y = max(0, cam_rect.top // TILE)
        end_y = min(self.h, (cam_rect.bottom)//TILE + 1)
        for y in range(start_y, end_y):
            for x in range(start_x, end_x):
                ch = self.tile_at(x,y)
                rect = pygame.Rect(x*TILE - cam_rect.left, y*TILE - cam_rect.top, TILE, TILE)
                if ch == "W":
                    pygame.draw.rect(SCREEN, WALL_COLOR, rect)
                elif ch == "G":
                    pygame.draw.rect(SCREEN, GOAL_COLOR, rect)
                elif ch == "B":
                    pygame.draw.rect(SCREEN, BUTTON_COLOR, rect)
                elif ch == "D":
                    open_state = self.doors.get((x,y), False)
                    color = (180,200,180) if open_state else DOOR_COLOR
                    pygame.draw.rect(SCREEN, color, rect)
                # else: пусто

    def update_buttons(self, player):
        # если игрок стоит на кнопке, активируем; кнопки открывают все двери in-level
        any_pressed = False
        px, py = player.pos
        for b in self.buttons:
            bx, by = b[0]*TILE + TILE//2, b[1]*TILE + TILE//2
            br = pygame.Rect(b[0]*TILE, b[1]*TILE, TILE, TILE)
            if br.collidepoint(px, py + PLAYER_RADIUS):  # немного учитываем вплотную
                b[2] = True
                any_pressed = True
            else:
                b[2] = False
        # Управление дверями: если нажата любая кнопка, открываем все двери
        for k in list(self.doors.keys()):
            self.doors[k] = any_pressed

class Player:
    def __init__(self, x,y):
        self.pos = [x, y]
        self.vel = [0.0, 0.0]
        self.on_ground = False
        self.last_teleport_time = -999
        self.teleport_cooldown = 0.12  # сек

    def rect(self):
        return pygame.Rect(self.pos[0]-PLAYER_RADIUS, self.pos[1]-PLAYER_RADIUS, PLAYER_RADIUS*2, PLAYER_RADIUS*2)

    def update(self, keys, level, dt):
        ax = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            ax = -PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            ax = PLAYER_SPEED
        # apply horizontal control (simple)
        self.vel[0] = ax

        # gravity
        self.vel[1] += GRAVITY

        # jump
        if (keys[pygame.K_w] or keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self.on_ground:
            self.vel[1] = JUMP_SPEED
            self.on_ground = False

        # integrate
        self.pos[0] += self.vel[0]
        self.collide_h(level)
        self.pos[1] += self.vel[1]
        self.on_ground = False
        self.collide_v(level)

    def collide_h(self, level):
        r = self.rect()
        # check tiles overlapping horizontally
        tiles = self._tiles_touching(r)
        for tx,ty in tiles:
            if level.is_solid_at(tx,ty):
                rect = pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)
                if r.colliderect(rect):
                    if self.vel[0] > 0:
                        self.pos[0] = rect.left - PLAYER_RADIUS
                    elif self.vel[0] < 0:
                        self.pos[0] = rect.right + PLAYER_RADIUS
                    self.vel[0] = 0
                    r = self.rect()

    def collide_v(self, level):
        r = self.rect()
        tiles = self._tiles_touching(r)
        for tx,ty in tiles:
            if level.is_solid_at(tx,ty):
                rect = pygame.Rect(tx*TILE, ty*TILE, TILE, TILE)
                if r.colliderect(rect):
                    if self.vel[1] > 0:
                        self.pos[1] = rect.top - PLAYER_RADIUS
                        self.on_ground = True
                    elif self.vel[1] < 0:
                        self.pos[1] = rect.bottom + PLAYER_RADIUS
                    self.vel[1] = 0
                    r = self.rect()

    def _tiles_touching(self, rect):
        left = max(0, int((rect.left)//TILE))
        right = int((rect.right)//TILE)
        top = max(0, int((rect.top)//TILE))
        bottom = int((rect.bottom)//TILE)
        coords = []
        for y in range(top, bottom+1):
            for x in range(left, right+1):
                coords.append((x,y))
        return coords

class Portal:
    def __init__(self):
        self.exists = False
        self.pos = (0,0)  # center in pixels
        self.normal = (0,-1)  # surface normal unit vector (which way portal faces)
        self.radius = 20
        self.color = PORTAL_ORANGE
        self.orientation = "up"  # 'up','down','left','right'

    def place(self, px, py, normal):
        self.exists = True
        self.pos = (px, py)
        self.normal = normal
        nx, ny = normal
        # determine orientation
        if abs(nx) > abs(ny):
            self.orientation = "left" if nx < 0 else "right"
        else:
            self.orientation = "up" if ny < 0 else "down"

    def draw(self, cam_rect):
        if not self.exists: return
        x = int(self.pos[0] - cam_rect.left)
        y = int(self.pos[1] - cam_rect.top)
        pygame.draw.circle(SCREEN, (0,0,0), (x,y), self.radius+6)  # outline dark
        pygame.draw.circle(SCREEN, self.color, (x,y), self.radius)
        # draw normal indicator
        nx, ny = self.normal
        pygame.draw.line(SCREEN, (0,0,0), (x,y), (x+int(nx*20), y+int(ny*20)), 3)

# Raycast для определения первой стены, куда попал выстрел
def raycast_to_wall(level, start, end):
    # шаговая проверка вдоль луча (DDA-like)
    sx, sy = start
    ex, ey = end
    dx = ex - sx
    dy = ey - sy
    dist = math.hypot(dx, dy)
    if dist == 0:
        return None
    steps = int(dist / 4) + 1
    for i in range(1, steps+1):
        t = i/steps
        x = sx + dx * t
        y = sy + dy * t
        tx = int(x // TILE)
        ty = int(y // TILE)
        if level.is_solid_at(tx,ty):
            # определим нормаль поверхности: посмотрим где ближе центр тайла
            center_x = tx*TILE + TILE/2
            center_y = ty*TILE + TILE/2
            dx_c = x - center_x
            dy_c = y - center_y
            # выбираем сторону по наибольшему абсолютному смещению
            if abs(dx_c) > abs(dy_c):
                # left or right side hit
                if dx_c > 0:
                    normal = (1,0)   # hit right half -> normal points right
                    hit_x = tx*TILE + TILE
                    hit_y = y
                else:
                    normal = (-1,0)
                    hit_x = tx*TILE
                    hit_y = y
            else:
                if dy_c > 0:
                    normal = (0,1)
                    hit_x = x
                    hit_y = ty*TILE + TILE
                else:
                    normal = (0,-1)
                    hit_x = x
                    hit_y = ty*TILE
            return (hit_x, hit_y, normal)
    return None

# Телепортация через порталы
def teleport_if_needed(player, portal_a, portal_b, t_now):
    if not portal_a.exists or not portal_b.exists:
        return
    pr = player.rect()
    # проверяем вход в оранжевый портал
    for src, dst in [(portal_a, portal_b), (portal_b, portal_a)]:
        if not src.exists or not dst.exists:
            continue
        sx, sy = src.pos
        dx = player.pos[0] - sx
        dy = player.pos[1] - sy
        # попадание по кругу
        if dx*dx + dy*dy <= (src.radius+PLAYER_RADIUS-2)**2:
            # cooldown чтобы не застрять в бесконечной телепортации
            if t_now - player.last_teleport_time < player.teleport_cooldown:
                return
            # compute local vector relative to source portal coordinate frame
            # хотим перенести положение относительно портала и повернуть по ориентации
            s_norm = src.normal
            d_norm = dst.normal
            # углы
            ang_s = math.atan2(s_norm[1], s_norm[0])
            ang_d = math.atan2(d_norm[1], d_norm[0])
            # угол для поворота вектора и скорости
            rotate = ang_d - ang_s + math.pi  # +pi потому что нормали указывают "наружу"
            # локальная позиция в полярных координатах от центра src
            relx = player.pos[0] - sx
            rely = player.pos[1] - sy
            # rotate position
            cosr = math.cos(rotate)
            sinr = math.sin(rotate)
            newx = relx * cosr - rely * sinr
            newy = relx * sinr + rely * cosr
            # новый мир. центр dst + rotated offset
            player.pos[0] = dst.pos[0] + newx
            player.pos[1] = dst.pos[1] + newy
            # rotate velocity similarly
            vx, vy = player.vel
            nvx = vx * cosr - vy * sinr
            nvy = vx * sinr + vy * cosr
            player.vel[0] = nvx
            player.vel[1] = nvy
            # небольшое смещение наружу вдоль нормали dst, чтобы не застрять внутри портала
            player.pos[0] += dst.normal[0] * (PLAYER_RADIUS + 3)
            player.pos[1] += dst.normal[1] * (PLAYER_RADIUS + 3)
            player.last_teleport_time = t_now
            return

# Камера: следует за игроком, с ограничением границ уровня
def compute_camera(level, player):
    cam_w, cam_h = WIDTH, HEIGHT
    x = int(player.pos[0] - cam_w/2)
    y = int(player.pos[1] - cam_h/2)
    x = clamp(x, 0, max(0, level.width_px - cam_w))
    y = clamp(y, 0, max(0, level.height_px - cam_h))
    return pygame.Rect(x,y,cam_w,cam_h)

# Основной игровой цикл по уровням
def run_game():
    level_idx = 0
    score = 0

    # создаём уровни-объекты
    levels = [Level(l) for l in LEVELS]

    while level_idx < len(levels):
        level = levels[level_idx]
        px, py = level.player_start if level.player_start else (TILE*2+TILE//2, TILE*2+TILE//2)
        player = Player(px, py)
        orange = Portal()
        orange.color = PORTAL_ORANGE
        blue = Portal()
        blue.color = PORTAL_BLUE
        running_level = True
        t_elapsed = 0.0

        while running_level:
            dt = CLOCK.tick(MAX_FPS) / 1000.0
            t_elapsed += dt
            for e in pygame.event.get():
                if e.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
                elif e.type == pygame.KEYDOWN:
                    if e.key == pygame.K_ESCAPE:
                        pygame.quit()
                        sys.exit()
                    if e.key == pygame.K_r:
                        running_level = False  # перезагрузить уровень (внешний цикл оставит индекс тем же)
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = pygame.mouse.get_pos()
                    cam = compute_camera(level, player)
                    # преобразовать координаты мыши в мировые
                    world_mx = mx + cam.left
                    world_my = my + cam.top
                    start = (player.pos[0], player.pos[1])
                    res = raycast_to_wall(level, start, (world_mx, world_my))
                    if res:
                        hitx, hity, normal = res
                        # корректируем позицию чтобы портал находился на поверхности тайла, внутри границ
                        # place соответствующий портал
                        if e.button == 1:  # ЛКМ -> оранжевый
                            orange.place(hitx, hity, normal)
                        elif e.button == 3:  # ПКМ -> синий
                            blue.place(hitx, hity, normal)

            keys = pygame.key.get_pressed()
            player.update(keys, level, dt)
            # кнопки и двери
            level.update_buttons(player)
            # телепортация (проверка сейчас)
            teleport_if_needed(player, orange, blue, t_elapsed)

            # проверка достижения цели
            if level.goal_rect:
                if level.goal_rect.collidepoint(player.pos[0], player.pos[1]+PLAYER_RADIUS):
                    # пройден уровень
                    level_idx += 1
                    score += 1
                    running_level = False
                    break

            # простой check fall off map
            if player.pos[1] > level.height_px + 200:
                # перезапуск уровня
                running_level = False
                break

            # камера
            cam = compute_camera(level, player)

            # отрисовка
            SCREEN.fill(BG)
            level.draw(cam)

            # draw portals
            orange.draw(cam)
            blue.draw(cam)

            # draw player
            pygame.draw.circle(SCREEN, PLAYER_COLOR, (int(player.pos[0]-cam.left), int(player.pos[1]-cam.top)), PLAYER_RADIUS)
            # draw player velocity vector
            vx, vy = player.vel
            pvx = int(player.pos[0]-cam.left + vx*4)
            pvy = int(player.pos[1]-cam.top + vy*4)
            pygame.draw.line(SCREEN, (220,120,120), (int(player.pos[0]-cam.left), int(player.pos[1]-cam.top)), (pvx,pvy), 2)

            # draw buttons
            for b in level.buttons:
                bx, by = b[0]*TILE - cam.left, b[1]*TILE - cam.top
                pygame.draw.rect(SCREEN, BUTTON_COLOR if b[2] else (120,80,120), (bx, by, TILE, TILE))

            # HUD
            text(f"Level {level_idx+1}/{len(levels)}", 10, 10)
            text("ЛКМ: оранжевый портал | ПКМ: синий портал | R: перезапуск уровня", 10, 34)
            text("Цель: достичь зелёной зоны (G). Кнопки открывают двери.", 10, 58)
            text(f"Vel: {player.vel[0]:.1f}, {player.vel[1]:.1f}", 10, 82)

            pygame.display.flip()

    # все уровни пройдены
    finish_screen(score)

def finish_screen(score):
    while True:
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif e.key == pygame.K_r:
                    run_game()
                    return
        SCREEN.fill((10,10,40))
        text("Поздравляем! Все уровни пройдены.", WIDTH//2 - 200, HEIGHT//2 - 40)
        text(f"Счёт: {score}", WIDTH//2 - 20, HEIGHT//2)
        text("Нажми R чтобы сыграть заново, Esc — выйти.", WIDTH//2 - 200, HEIGHT//2 + 40)
        pygame.display.flip()
        CLOCK.tick(30)

if __name__ == "__main__":
    run_game()
