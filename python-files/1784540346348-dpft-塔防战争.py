"""
2D 俯视视角塔防游戏 (Top-down Tower Defense)  - v7.2
============================
v7.1 → v7.2 改动:
  - 新增铲子工具: 从侧边栏拖拽铲子到炮塔上松手, 即可出售该炮塔
  - 回收价值 = 基础造价 + 历次升级花费 (Tower.sell_value)

v7 → v7.1 改动:
  - 修复: 移除 wave>=20 时每敌人3%变Boss的随机规则 (避免Boss泛滥/无限刷新观感)
  - 修复: Boss/分裂敌人死亡时在遍历self.enemies时追加元素 (改为循环后统一添加)
  - Boss 仅作为里程碑出现在 20/30/40/50 波

v6 → v7 改动:
  - Boss 增强: 每30秒10%概率摧毁附近5个塔
  - Boss 起死回生: 只能复活一次, 复活后3秒无敌+无视负面效果
  - Boss 复活时召唤10个随机敌人(非Boss)

v5 → v6 改动:
  - 障碍物必须在路径侧沿 (不在路中, 不在荒地)
  - 新增地图选择画面 (开场 Pick Map, 点击或按 1-6/R)
  - 侧沿障碍物预定义在地图数据中, 不随机

运行:  python tower_defense.py
"""
import sys
import pygame
import math
import random

# ----------------------------- 配置 -----------------------------
TILE = 40
COLS = 20
ROWS = 15
SIDE_W = 200
PLAY_W = COLS * TILE
WIDTH = PLAY_W + SIDE_W
HEIGHT = ROWS * TILE

FPS = 60

# 颜色
GRASS   = (46, 139, 87)
PATH_C  = (201, 174, 130)
GRID_C  = (38, 110, 70)
WHITE   = (255, 255, 255)
BLACK   = (20, 20, 25)
RED     = (220, 60, 60)
BLUE    = (60, 130, 230)
YELLOW  = (240, 200, 50)
GRAY    = (90, 95, 105)
DARK    = (40, 44, 52)
CYAN    = (80, 220, 230)
PURPLE  = (160, 80, 200)
ORANGE  = (235, 140, 40)
BTN     = (70, 80, 95)
BTN_HI  = (95, 110, 130)
GREEN   = (140, 230, 90)
DARK_P  = (90, 30, 150)
TEAL    = (50, 210, 180)
PINK    = (230, 130, 180)

# 炮塔类型
TOWER_TYPES = {
    "arrow":  {"name": "Arrow",  "cost": 50,  "range": 110, "damage": 9,  "cooldown": 0.40, "pspeed": 360, "color": BLUE,  "splash": 0,  "slow": 0,   "desc": "Fast single-target"},
    "cannon": {"name": "Cannon", "cost": 110, "range": 105, "damage": 28, "cooldown": 1.05, "pspeed": 240, "color": GRAY,   "splash": 45, "slow": 0,   "desc": "Splash AoE"},
    "frost":  {"name": "Frost",  "cost": 80,  "range": 95,  "damage": 5,  "cooldown": 0.65, "pspeed": 320, "color": CYAN,   "splash": 0,  "slow": 0.5, "desc": "Slows enemies"},
}

# 敌人类型
ENEMY_TYPES = {
    "normal": {"hp": 45,  "speed": 74,  "reward": 8,  "radius": 12, "color": RED,    "size": 1.0, "cap": 1.16},
    "fast":   {"hp": 31,  "speed": 138, "reward": 10, "radius": 10, "color": YELLOW, "size": 0.9, "cap": 1.16},
    "tank":   {"hp": 154, "speed": 43,  "reward": 22, "radius": 16, "color": PURPLE, "size": 1.3, "cap": 1.16},
    "swarm":  {"hp": 16,  "speed": 110, "reward": 3,  "radius": 8,  "color": GREEN,  "size": 0.75,"cap": 1.10},
    "healer": {"hp": 75,  "speed": 62,  "reward": 18, "radius": 13, "color": TEAL,   "size": 1.0, "cap": 1.14},
    "split":  {"hp": 120, "speed": 70,  "reward": 12, "radius": 14, "color": PINK,   "size": 1.1, "cap": 1.13},
    "boss":   {"hp": 640, "speed": 18,  "reward": 120,"radius": 24, "color": DARK_P, "size": 1.8, "cap": 1.18},
}

MAX_WAVES = 50
START_MONEY = 250
START_LIVES = 25

OBSTACLE_KINDS = [
    ("rock",  (110, 100, 90)),
    ("rock2", (130, 120, 110)),
    ("tree",  (30,  90,  40)),
    ("bush",  (60,  130, 70)),
    ("crate", (160, 110, 60)),
]


# =============================================================================
# 预制地图池 (共 6 张)
# 每个地图:
#   name:        地图名
#   waypoints:   路径折点 (col, row)
#   obstacles:   侧沿障碍物格列表 [(col, row, kind_idx)]
#                 kind_idx: 0=rock, 1=rock2, 2=tree, 3=bush, 4=crate
# =============================================================================
MAPS = [

    # Map 1: 之字型 (Snake Pass)
    {
        "name": "Snake Pass",
        "waypoints": [
            (-1, 2), (4, 2), (4, 7),
            (9, 7), (9, 12),
            (15, 12), (15, 7),
            (COLS, 7),
        ],
        # 侧沿障碍物: 紧贴路径格的正交邻居
        "obstacles": [
            # 沿第1段 (row=2, col 0-4)
            (2, 1, 2), (3, 3, 0),
            # 沿第2段竖 (col=4, row 2-7)
            (3, 4, 1), (5, 5, 3),
            # 沿第3段横 (row=7, col 4-9)
            (5, 6, 0), (6, 8, 2), (8, 6, 1),
            # 沿第4段竖 (col=9, row 7-12)
            (8, 8, 3), (10, 10, 0),
            # 沿第5段横 (row=12, col 9-15)
            (11, 11, 2), (13, 13, 1), (14, 11, 3),
            # 沿第6段竖 (col=15, row 7-12)
            (14, 8, 0), (16, 10, 2),
            # 沿第7段横 (row=7, col 15-20)
            (16, 6, 1), (17, 8, 3), (18, 6, 0),
        ],
    },

    # Map 2: 大U型 (Grand U)
    {
        "name": "Grand U",
        "waypoints": [
            (-1, 7), (3, 7), (3, 13),
            (16, 13), (16, 1),
            (COLS, 1),
        ],
        "obstacles": [
            # 入口段 (row=7, col 0-3)
            (1, 6, 2), (2, 8, 0),
            # 左竖 (col=3, row 7-13)
            (2, 8, 1), (4, 10, 3), (2, 12, 0),
            # 底横 (row=13, col 3-16)
            (5, 12, 2), (7, 14, 1), (10, 12, 3),
            (13, 14, 0), (15, 12, 2),
            # 右竖 (col=16, row 1-13)
            (15, 2, 0), (17, 4, 3), (15, 6, 1),
            (17, 8, 2), (15, 10, 0), (17, 12, 3),
            # 出口段 (row=1, col 16-20)
            (17, 0, 2), (18, 2, 1),
        ],
    },

    # Map 3: 双折返 (Switchback)
    {
        "name": "Switchback",
        "waypoints": [
            (-1, 1), (5, 1), (5, 5),
            (10, 5), (10, 1),
            (15, 1), (15, 13),
            (COLS, 13),
        ],
        "obstacles": [
            # 第1段横 (row=1, col 0-5)
            (1, 0, 2), (3, 2, 0), (4, 0, 1),
            # 第2段竖 (col=5, row 1-5)
            (4, 2, 3), (6, 3, 0), (4, 4, 2),
            # 第3段横 (row=5, col 5-10)
            (6, 4, 1), (8, 6, 0), (9, 4, 3),
            # 第4段竖 (col=10, row 1-5) 回顶
            (9, 2, 0), (11, 3, 2), (9, 0, 1),
            # 第5段横 (row=1, col 10-15)
            (11, 0, 3), (13, 2, 0), (14, 0, 2),
            # 第6段竖 (col=15, row 1-13)
            (14, 2, 1), (16, 5, 0), (14, 7, 3),
            (16, 9, 2), (14, 11, 0), (16, 12, 1),
            # 第7段横 (row=13, col 15-20)
            (16, 14, 2), (17, 12, 0), (18, 14, 1),
        ],
    },

    # Map 4: 水平长廊 (Highway)
    {
        "name": "Highway",
        "waypoints": [
            (-1, 7), (8, 7), (8, 3),
            (14, 3), (14, 11),
            (COLS, 11),
        ],
        "obstacles": [
            # 第1段横 (row=7, col 0-8)
            (1, 6, 2), (3, 8, 0), (5, 6, 1), (7, 8, 3),
            # 第2段竖上 (col=8, row 3-7)
            (7, 4, 0), (9, 5, 2), (7, 6, 1),
            # 第3段横 (row=3, col 8-14)
            (9, 2, 3), (11, 4, 0), (12, 2, 2), (13, 4, 1),
            # 第4段竖下 (col=14, row 3-11)
            (13, 4, 0), (15, 6, 3), (13, 8, 1),
            (15, 10, 2), (13, 10, 0),
            # 第5段横 (row=11, col 14-20)
            (15, 12, 1), (16, 10, 3), (17, 12, 0), (18, 10, 2),
        ],
    },

    # Map 5: 回旋镖 (Boomerang)
    {
        "name": "Boomerang",
        "waypoints": [
            (-1, 3), (6, 3), (6, 11),
            (12, 11), (12, 5),
            (COLS, 5),
        ],
        "obstacles": [
            # 第1段横 (row=3, col 0-6)
            (1, 2, 2), (3, 4, 0), (5, 2, 1),
            # 第2段竖 (col=6, row 3-11)
            (5, 4, 3), (7, 6, 0), (5, 8, 2), (7, 10, 1),
            # 第3段横 (row=11, col 6-12)
            (7, 12, 0), (9, 10, 3), (10, 12, 1), (11, 10, 2),
            # 第4段竖上 (col=12, row 5-11)
            (11, 6, 0), (13, 8, 2), (11, 10, 1),
            # 第5段横 (row=5, col 12-20)
            (13, 4, 3), (14, 6, 0), (15, 4, 2), (16, 6, 1),
            (17, 4, 3), (18, 6, 0),
        ],
    },

    # Map 6: 迷宫型 (Labyrinth)
    {
        "name": "Labyrinth",
        "waypoints": [
            (-1, 1), (3, 1), (3, 6),
            (8, 6), (8, 1),
            (13, 1), (13, 11),
            (7, 11), (7, 13),
            (17, 13), (17, 6),
            (COLS, 6),
        ],
        "obstacles": [
            # 第1段横 (row=1, col 0-3)
            (1, 0, 2), (2, 2, 0),
            # 第2段竖 (col=3, row 1-6)
            (2, 2, 1), (4, 3, 3), (2, 5, 0),
            # 第3段横 (row=6, col 3-8)
            (4, 5, 2), (5, 7, 0), (7, 5, 1),
            # 第4段竖上 (col=8, row 1-6)
            (7, 2, 0), (9, 4, 3), (7, 5, 1),
            # 第5段横顶 (row=1, col 8-13)
            (9, 0, 2), (10, 2, 0), (12, 0, 1),
            # 第6段竖下 (col=13, row 1-11)
            (12, 2, 3), (14, 4, 0), (12, 6, 2), (14, 8, 1),
            (12, 10, 0),
            # 第7段横底 (row=11, col 7-13)
            (8, 12, 2), (9, 10, 0), (11, 12, 3), (12, 10, 1),
            # 第8段竖 (col=7, row 11-13)
            (6, 12, 0), (8, 14, 2),
            # 第9段横 (row=13, col 7-17)
            (8, 14, 1), (10, 12, 0), (12, 14, 3), (15, 12, 2),
            # 第10段竖 (col=17, row 6-13)
            (16, 7, 0), (18, 9, 1), (16, 11, 3), (18, 12, 2),
            # 第11段横 (row=6, col 17-20)
            (18, 5, 0), (19, 7, 1),
        ],
    },
]


# =============================================================================
# 工具函数
# =============================================================================
def build_path_cells(wps):
    cells = set()
    for i in range(len(wps) - 1):
        c0, r0 = wps[i]
        c1, r1 = wps[i + 1]
        if c0 == c1:
            step = 1 if r1 > r0 else -1
            for r in range(r0, r1 + step, step):
                cells.add((c0, r))
        else:
            step = 1 if c1 > c0 else -1
            for c in range(c0, c1 + step, step):
                cells.add((c, r0))
    return cells


def wps_to_pixels(wps):
    def g2p(col, row):
        if col < 0:       x = -20
        elif col >= COLS: x = COLS * TILE
        else:             x = col * TILE + TILE // 2
        return (x, row * TILE + TILE // 2)
    return [g2p(c, r) for c, r in wps]


def cell_center(col, row):
    return (col * TILE + TILE // 2, row * TILE + TILE // 2)


def make_obstacles(ob_list):
    result = []
    for col, row, kind_idx in ob_list:
        kind, color = OBSTACLE_KINDS[kind_idx % len(OBSTACLE_KINDS)]
        result.append({"col": col, "row": row, "kind": kind, "color": color})
    return result


# =============================================================================
# 实体类
# =============================================================================
class Enemy:
    def __init__(self, etype, wave, hp_scale=None, pos=None, pixel_wps=None):
        base = ENEMY_TYPES[etype]
        self.etype = etype
        self.pos = pos if pos else list(pixel_wps[0])
        self.pixel_wps = pixel_wps
        self.wp_index = 1
        self.radius = int(base["radius"] * base["size"])
        self.color = base["color"]
        self.base_speed = base["speed"]
        self.speed = self.base_speed
        self.reward = base["reward"]
        cap = base["cap"]
        if hp_scale is None:
            self.max_hp = int(base["hp"] * (cap ** (wave - 1)))
        else:
            self.max_hp = int(base["hp"] * hp_scale)
        self.hp = self.max_hp
        self.slow_timer = 0.0
        self.slow_factor = 1.0
        self.dead = False
        self.reached_end = False
        self.paid = False
        self.heal_radius = 70 if etype == "healer" else 0
        self.heal_power = 18 if etype == "healer" else 0
        self.heal_tick = 0.0
        self.boss_thick = 3 if etype == "boss" else 2

        # Boss 增强属性
        if etype == "boss":
            self.boss_destroy_timer = 0.0      # 摧塔计时器
            self.boss_destroy_cooldown = 5.0  # 每5秒尝试一次
            self.boss_has_revived = False      # 是否已复活（重点：只能一次！）
            self.boss_invincible_timer = 0.0   # 无敌时间
            self.boss_immune_debuff = False    # 无视负面效果
        else:
            self.boss_destroy_timer = 0.0
            self.boss_destroy_cooldown = 0.0
            self.boss_has_revived = True       # 非Boss视为已复活过
            self.boss_invincible_timer = 0.0
            self.boss_immune_debuff = False

    def apply_slow(self, factor, duration):
        # Boss 免疫减速（复活后3秒内）
        if self.etype == "boss" and self.boss_immune_debuff:
            return
        self.slow_timer = max(self.slow_timer, duration)
        self.slow_factor = min(self.slow_factor, factor)

    def update(self, dt, all_enemies):
        # Boss 无敌计时
        if self.etype == "boss" and self.boss_invincible_timer > 0:
            self.boss_invincible_timer -= dt
            if self.boss_invincible_timer <= 0:
                self.boss_immune_debuff = False  # 无敌结束，恢复受减速影响

        if self.slow_timer > 0:
            self.slow_timer -= dt
            eff = self.base_speed * self.slow_factor
            if self.slow_timer <= 0:
                self.slow_factor = 1.0
        else:
            eff = self.base_speed

        if self.heal_power > 0 and not self.dead:
            self.heal_tick += dt
            if self.heal_tick >= 1.0:
                self.heal_tick = 0
                for o in all_enemies:
                    if o is self or o.dead or o.reached_end:
                        continue
                    if math.hypot(o.pos[0] - self.pos[0],
                                  o.pos[1] - self.pos[1]) <= self.heal_radius:
                        o.hp = min(o.max_hp, o.hp + self.heal_power)

        if self.wp_index >= len(self.pixel_wps):
            self.reached_end = True
            return
        tx, ty = self.pixel_wps[self.wp_index]
        dx = tx - self.pos[0]
        dy = ty - self.pos[1]
        dist = math.hypot(dx, dy)
        move = eff * dt
        if dist <= move or dist == 0:
            self.pos[0], self.pos[1] = tx, ty
            self.wp_index += 1
        else:
            self.pos[0] += dx / dist * move
            self.pos[1] += dy / dist * move

    def draw(self, surf, font):
        x, y = int(self.pos[0]), int(self.pos[1])
        pygame.draw.circle(surf, self.color, (x, y), self.radius)
        pygame.draw.circle(surf, BLACK, (x, y), self.radius, self.boss_thick)
        w = self.radius * 2
        hp_ratio = max(0, self.hp / self.max_hp)
        bar_y = y - self.radius - 8
        pygame.draw.rect(surf, (40, 40, 40), (x - w // 2, bar_y, w, 4))
        pygame.draw.rect(surf, (80, 220, 80), (x - w // 2, bar_y, int(w * hp_ratio), 4))
        if self.etype == "boss":
            # 无敌状态显示金色光环
            if self.boss_invincible_timer > 0:
                pygame.draw.circle(surf, YELLOW, (x, y), self.radius + 6, 3)
            tag = font.render("BOSS", True, YELLOW)
            surf.blit(tag, (x - tag.get_width() // 2, y - self.radius - 24))
        elif self.etype == "healer":
            tag = font.render("+", True, WHITE)
            surf.blit(tag, (x - tag.get_width() // 2, y - self.radius - 18))


class Tower:
    def __init__(self, ttype, col, row):
        self.ttype = ttype
        self.col = col
        self.row = row
        self.pos = cell_center(col, row)
        self.level = 1
        self.cooldown = 0.0
        self.angle = 0
        self._apply_stats()

    def _apply_stats(self):
        s = TOWER_TYPES[self.ttype]
        mult = 1 + 0.35 * (self.level - 1)
        self.range = s["range"] + 8 * (self.level - 1)
        self.damage = s["damage"] * mult
        self.cooldown_max = s["cooldown"]
        self.pspeed = s["pspeed"]
        self.color = s["color"]
        self.splash = s["splash"]
        self.slow = s["slow"]

    @property
    def upgrade_cost(self):
        return int(TOWER_TYPES[self.ttype]["cost"] * 0.8 * self.level)

    @property
    def sell_value(self):
        """总投入价值 = 基础造价 + 历次升级花费（用于铲子回收）"""
        base = TOWER_TYPES[self.ttype]["cost"]
        total = base
        for k in range(1, self.level):
            total += int(TOWER_TYPES[self.ttype]["cost"] * 0.8 * k)
        return total

    def update(self, dt, enemies, projectiles):
        if self.cooldown > 0:
            self.cooldown -= dt
        target = None
        best_hp = -1
        for e in enemies:
            if e.dead or e.reached_end:
                continue
            d = math.hypot(e.pos[0] - self.pos[0], e.pos[1] - self.pos[1])
            if d <= self.range and e.hp > best_hp:
                best_hp = e.hp
                target = e
        if target:
            self.angle = math.atan2(target.pos[1] - self.pos[1],
                                    target.pos[0] - self.pos[0])
            if self.cooldown <= 0:
                self.cooldown = self.cooldown_max
                projectiles.append(Projectile(
                    self.pos, target, self.damage, self.pspeed,
                    self.color, self.splash, self.slow))

    def draw(self, surf, selected=False):
        x, y = self.pos
        if selected:
            pygame.draw.circle(surf, (255, 255, 255), (int(x), int(y)),
                               int(self.range), 1)
        pygame.draw.circle(surf, DARK, (int(x), int(y)), 15)
        pygame.draw.circle(surf, self.color, (int(x), int(y)), 12)
        bx = x + math.cos(self.angle) * 16
        by = y + math.sin(self.angle) * 16
        pygame.draw.line(surf, BLACK, (int(x), int(y)), (int(bx), int(by)), 5)
        for i in range(self.level):
            pygame.draw.circle(surf, YELLOW,
                               (int(x - 8 + i * 8), int(y) + 16), 2)


class Projectile:
    def __init__(self, pos, target, damage, speed, color, splash, slow):
        self.x, self.y = pos
        self.target = target
        self.tx, self.ty = target.pos
        self.damage = damage
        self.speed = speed
        self.color = color
        self.splash = splash
        self.slow = slow
        self.dead = False
        self.radius = 5 if splash == 0 else 7

    def update(self, dt, enemies):
        if self.target and not self.target.dead and not self.target.reached_end:
            self.tx, self.ty = self.target.pos
        dx = self.tx - self.x
        dy = self.ty - self.y
        dist = math.hypot(dx, dy)
        move = self.speed * dt
        if dist <= move:
            self._hit(enemies)
            self.dead = True
        else:
            self.x += dx / dist * move
            self.y += dy / dist * move

    def _hit(self, enemies):
        if self.target and not self.target.dead:
            self.target.hp -= self.damage
            if self.slow > 0:
                self.target.apply_slow(self.slow, 1.3)
            if self.target.hp <= 0:
                self.target.dead = True
        if self.splash > 0:
            for e in enemies:
                if e is self.target or e.dead:
                    continue
                if math.hypot(e.pos[0] - self.tx,
                              e.pos[1] - self.ty) <= self.splash:
                    e.hp -= self.damage * 0.6
                    if e.hp <= 0:
                        e.dead = True

    def draw(self, surf):
        pygame.draw.circle(surf, self.color, (int(self.x), int(self.y)), self.radius)
        pygame.draw.circle(surf, WHITE, (int(self.x), int(self.y)), self.radius, 1)


class GoldPopup:
    def __init__(self, x, y, amount, color=YELLOW):
        self.x, self.y = x, y
        self.amount = amount
        self.color = color
        self.life = 0.9
        self.max_life = 0.9

    def update(self, dt):
        self.y -= 28 * dt
        self.life -= dt

    def draw(self, surf, font):
        if self.life <= 0:
            return
        txt = font.render(f"+${self.amount}", True, self.color)
        surf.blit(txt, (self.x - txt.get_width() // 2, int(self.y)))


def draw_obstacle(surf, ob):
    cx, cy = cell_center(ob["col"], ob["row"])
    kind = ob["kind"]
    if kind in ("rock", "rock2"):
        seed_off = (ob["col"] * 7 + ob["row"] * 13) % 6
        pts = [(cx + math.cos(i * math.pi / 3 + 0.3 + seed_off * 0.05)
                * (TILE // 2 - 6),
                cy + math.sin(i * math.pi / 3 + 0.3 + seed_off * 0.05)
                * (TILE // 2 - 6)) for i in range(6)]
        pygame.draw.polygon(surf, ob["color"], pts)
        pygame.draw.polygon(surf, BLACK, pts, 2)
    elif kind == "tree":
        pygame.draw.rect(surf, (80, 50, 20), (cx - 3, cy + 6, 6, 12))
        pygame.draw.circle(surf, (30, 90, 40), (cx, cy - 2), 14)
        pygame.draw.circle(surf, BLACK, (cx, cy - 2), 14, 2)
    elif kind == "bush":
        pygame.draw.circle(surf, ob["color"], (cx, cy + 2), 10)
        pygame.draw.circle(surf, BLACK, (cx, cy + 2), 10, 1)
    elif kind == "crate":
        pygame.draw.rect(surf, ob["color"], (cx - 12, cy - 12, 24, 24))
        pygame.draw.rect(surf, BLACK, (cx - 12, cy - 12, 24, 24), 2)
        pygame.draw.line(surf, BLACK, (cx - 12, cy), (cx + 12, cy), 1)
        pygame.draw.line(surf, BLACK, (cx, cy - 12), (cx, cy + 12), 1)


# =============================================================================
# 波次生成
# =============================================================================
def build_wave(wave):
    queue = []
    n = 6 + wave * 3
    for i in range(n):
        r = random.random()
        if wave >= 15 and r < 0.13: queue.append("split")
        elif wave >= 10 and r < 0.28: queue.append("healer")
        elif wave >= 5  and r < 0.50: queue.append("swarm")
        elif wave >= 4  and r < 0.65: queue.append("tank")
        elif r < 0.85:                queue.append("fast")
        else:                          queue.append("normal")
    # Boss 机制: 每10关 (20/30/40/50) 刷新 1 个Boss
    if wave >= 20 and wave % 10 == 0:
        queue += ["boss"] * 1
    if wave % 5 == 0:
        queue += ["tank"] * (2 + wave // 5)
    if wave >= 30 and wave % 7 == 0:
        queue += ["swarm"] * 15
    return queue


# =============================================================================
# 地图选择画面
# =============================================================================
def run_map_picker(screen):
    """
    显示地图选择画面，返回选中的地图下标 (0-5) 或 -1=随机。
    - 滚轮上下 / 方向键: 循环切换当前高亮地图
    - Hover / 数字键: 快速定位
    - 点击地图 / Enter / 空格: 确认选择
    - R: 随机
    """
    font_big = pygame.font.Font(None, 40)
    font_sml = pygame.font.Font(None, 20)
    font_tip = pygame.font.Font(None, 22)

    PW = 280
    PH = 175
    GX = (WIDTH - 2 * PW - 20) // 2
    GY = 100
    GAP = 20

    n_maps = len(MAPS)
    rows, cols = 3, 2
    ob_colors = [c for _, c in OBSTACLE_KINDS]

    # 当前高亮的地图下标 (初始=0)
    sel_idx = 0
    # 当前鼠标悬停的下标 (用于高亮跟随鼠标)
    hover_idx = -1

    def draw_map_preview(surf, map_idx, rect, highlighted):
        x, y, w, h = rect
        # 背景色
        if highlighted:
            # 高亮: 深绿背景 + 金色粗边框
            bg = (40, 90, 65)
            border = YELLOW
            bw = 3
        elif map_idx == hover_idx:
            # Hover: 稍亮一点
            bg = (55, 65, 80)
            border = (130, 140, 160)
            bw = 2
        else:
            bg = (45, 52, 65)
            border = (90, 100, 115)
            bw = 1
        pygame.draw.rect(surf, bg, rect)
        pygame.draw.rect(surf, border, rect, bw)

        m = MAPS[map_idx]
        pcells = build_path_cells(m["waypoints"])
        obs_set = {(o[0], o[1]) for o in m["obstacles"]}
        scale_x = w / COLS
        scale_y = h / ROWS

        def blit_cell(bgx, bgy, color):
            rx = x + bgx * scale_x
            ry = y + bgy * scale_y
            rw = max(1, scale_x - 1)
            rh = max(1, scale_y - 1)
            pygame.draw.rect(surf, color, (rx, ry, rw, rh))

        for r in range(ROWS):
            for c in range(COLS):
                if (c, r) in pcells:
                    blit_cell(c, r, PATH_C)
                elif (c, r) in obs_set:
                    blit_cell(c, r, ob_colors[r % len(ob_colors)])

        # 地图名
        label = font_sml.render(f"[{map_idx + 1}] {m['name']}", True, WHITE)
        surf.blit(label, (x + 6, y + h - 18))
        # 高亮时加 ★
        if highlighted:
            star = font_sml.render("  ★ SELECTED", True, YELLOW)
            surf.blit(star, (x + 6 + label.get_width(), y + h - 18))

    def get_map_rect(idx):
        r = idx // cols
        c = idx % cols
        return (GX + c * (PW + GAP), GY + r * (PH + GAP), PW, PH)

    def get_map_idx_at(mx, my):
        for i in range(n_maps):
            rx, ry, rw, rh = get_map_rect(i)
            if rx <= mx <= rx + rw and ry <= my <= ry + rh:
                return i
        return -1

    map_rects = [get_map_rect(i) for i in range(n_maps)]
    rand_rect = (WIDTH // 2 - 80, GY + 3 * (PH + GAP) - 10, 160, 44)
    tip_y = rand_rect[1] + rand_rect[3] + 16

    # 箭头三角形的三个点 (高亮地图两侧)
    def get_arrow_left(idx):
        rx, ry, rw, rh = get_map_rect(idx)
        cx = rx - 18
        cy = ry + rh // 2
        return [(cx, cy), (cx - 10, cy - 8), (cx - 10, cy + 8)]

    def get_arrow_right(idx):
        rx, ry, rw, rh = get_map_rect(idx)
        cx = rx + rw + 18
        cy = ry + rh // 2
        return [(cx, cy), (cx + 10, cy - 8), (cx + 10, cy + 8)]

    running = True
    while running:
        dt = min(pygame.time.Clock().tick(FPS) / 1000.0, 0.05)
        mx, my = pygame.mouse.get_pos()
        hover_idx = get_map_idx_at(mx, my)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_1,): sel_idx = 0
                elif event.key in (pygame.K_2,): sel_idx = 1
                elif event.key in (pygame.K_3,): sel_idx = 2
                elif event.key in (pygame.K_4,): sel_idx = 3
                elif event.key in (pygame.K_5,): sel_idx = 4
                elif event.key in (pygame.K_6,): sel_idx = 5
                elif event.key in (pygame.K_r, pygame.K_R): return -1
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    return sel_idx
                elif event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    exit()
                # 方向键 / 滚轮等统一用下面处理

            elif event.type == pygame.MOUSEBUTTONDOWN:
                btn = event.button
                if btn == 1:  # 左键点击
                    if hover_idx >= 0:
                        return hover_idx
                    rx, ry, rw, rh = rand_rect
                    if rx <= event.pos[0] <= rx + rw and ry <= event.pos[1] <= ry + rh:
                        return -1
                elif btn in (4, 5):  # 滚轮上/下: 循环切换地图
                    delta = -1 if btn == 4 else 1
                    sel_idx = (sel_idx + delta) % n_maps
                # btn == 2 (中键按下) 和 btn == 3 (右键) 不做处理，避免误触

        # 绘制
        screen.fill((18, 22, 32))
        header = font_big.render("SELECT MAP", True, WHITE)
        screen.blit(header, (WIDTH // 2 - header.get_width() // 2, 28))

        for i in range(n_maps):
            rect = get_map_rect(i)
            draw_map_preview(screen, i, rect, highlighted=(i == sel_idx))

        # 高亮地图两侧的箭头指示
        if 0 <= sel_idx < n_maps:
            # 左侧箭头
            pts_l = get_arrow_left(sel_idx)
            pygame.draw.polygon(screen, YELLOW, pts_l)
            # 右侧箭头
            pts_r = get_arrow_right(sel_idx)
            pygame.draw.polygon(screen, YELLOW, pts_r)
            # 底部当前选中信息
            sel_name = MAPS[sel_idx]["name"]
            info = font_tip.render(
                f"Selected: [{sel_idx + 1}] {sel_name}  |  ENTER / Click to confirm",
                True, YELLOW)
            screen.blit(info, (WIDTH // 2 - info.get_width() // 2, tip_y - 28))

        # 随机按钮
        pygame.draw.rect(screen, (65, 110, 75), rand_rect, border_radius=6)
        pygame.draw.rect(screen, WHITE, rand_rect, 1, border_radius=6)
        rtxt = font_tip.render("[ R ]  RANDOM", True, WHITE)
        screen.blit(rtxt, (rand_rect[0] + 18, rand_rect[1] + 11))

        tip = font_sml.render(
            "Scroll / ↑↓ to switch  |  1-6 jump  |  R = random  |  ESC = quit",
            True, (150, 160, 175))
        screen.blit(tip, (WIDTH // 2 - tip.get_width() // 2, tip_y + 10))

        pygame.display.flip()


# =============================================================================
# 游戏主体
# =============================================================================
class Game:
    def __init__(self, map_index):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Tower Defense 2D  -  50 Waves")
        self.clock = pygame.time.Clock()
        self.font  = pygame.font.Font(None, 32)
        self.mfont = pygame.font.Font(None, 44)
        self.sfont = pygame.font.Font(None, 18)
        self.bfont = pygame.font.Font(None, 20)

        # 选中的地图
        self.map_data = MAPS[map_index] if map_index >= 0 else random.choice(MAPS)
        self.map_name = self.map_data["name"]
        wps = self.map_data["waypoints"]
        self.waypoints  = wps
        self.path_cells = build_path_cells(wps)
        self.pixel_wps  = wps_to_pixels(wps)

        self.money = START_MONEY
        self.total_earned = START_MONEY
        self.lives = START_LIVES
        self.wave = 0
        self.enemies = []
        self.towers = []
        self.projectiles = []
        self.popups = []
        self.tower_grid = {}

        self.selected_type = None
        self.selected_tower = None
        self.spawn_queue = []
        self.spawn_timer = 0
        self.spawn_interval = 0.8
        self.state = "idle"
        self.between_timer = 0
        self.paused = False

        # 铲子（拖拽出售炮塔）状态
        self.shovel_dragging = False
        self.shovel_pos = (0, 0)

        # 障碍物: 预定义在地图数据中，全部沿路径侧沿
        self.obstacles = make_obstacles(self.map_data["obstacles"])
        self.obstacle_cells = {(o["col"], o["row"]) for o in self.obstacles}

        self._build_sidebar_rects()
        self.pause_btn = pygame.Rect(PLAY_W + 20, HEIGHT - 70, SIDE_W - 40, 32)
        self.start_btn = pygame.Rect(PLAY_W + 20, HEIGHT - 34, SIDE_W - 40, 34)
        # 铲子按钮（拖动到炮塔上松手即出售并回收其价值）
        self.shovel_rect = pygame.Rect(PLAY_W + 20, 490, SIDE_W - 40, 36)

    def _build_sidebar_rects(self):
        self.type_rects = {}
        y = 260
        for key in TOWER_TYPES:
            self.type_rects[key] = pygame.Rect(PLAY_W + 20, y, SIDE_W - 40, 56)
            y += 66

    def _add_money(self, amount):
        self.money += amount
        self.total_earned += amount

    def handle_click(self, pos):
        x, y = pos
        if self.start_btn.collidepoint(pos) and self.state == "idle":
            self._start_wave()
            return
        if self.pause_btn.collidepoint(pos):
            self._toggle_pause()
            return
        if x >= PLAY_W:
            for key, rect in self.type_rects.items():
                if rect.collidepoint(pos):
                    self.selected_type = key if self.selected_type != key else None
                    self.selected_tower = None
                    return
            if self.selected_tower:
                up_rect = pygame.Rect(PLAY_W + 20, HEIGHT - 150, SIDE_W - 40, 34)
                if up_rect.collidepoint(pos):
                    self._upgrade()
            return

        col = x // TILE
        row = y // TILE
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return
        cell = (col, row)
        if cell in self.tower_grid:
            self.selected_tower = self.tower_grid[cell]
            self.selected_type = None
            return
        if (self.selected_type and cell not in self.path_cells
                and cell not in self.obstacle_cells):
            cost = TOWER_TYPES[self.selected_type]["cost"]
            if self.money >= cost:
                t = Tower(self.selected_type, col, row)
                self.towers.append(t)
                self.tower_grid[cell] = t
                self.money -= cost

    def _toggle_pause(self):
        if self.state in ("over", "win"):
            return
        self.paused = not self.paused

    def _upgrade(self):
        t = self.selected_tower
        if not t:
            return
        if self.money >= t.upgrade_cost and t.level < 4:
            self.money -= t.upgrade_cost
            t.level += 1
            t._apply_stats()

    def _drop_shovel(self, pos):
        """铲子松手：若落在某炮塔格上，则出售该炮塔并回收其总价值（含升级）"""
        x, y = pos
        if x >= PLAY_W:
            return  # 落在侧边栏，不处理
        col = x // TILE
        row = y // TILE
        if not (0 <= col < COLS and 0 <= row < ROWS):
            return
        cell = (col, row)
        t = self.tower_grid.get(cell)
        if not t:
            return
        value = t.sell_value
        del self.tower_grid[cell]
        self.towers.remove(t)
        if self.selected_tower is t:
            self.selected_tower = None
        self.money += value
        self._add_popup(t.pos[0], t.pos[1], value, GREEN)

    def _start_wave(self):
        self.wave += 1
        self.spawn_queue = build_wave(self.wave)
        self.spawn_interval = max(0.20, 0.85 - self.wave * 0.012)
        self.spawn_timer = 0
        self.state = "wave"

    def _add_popup(self, x, y, amount, color=YELLOW):
        self.popups.append(GoldPopup(x, y, amount, color))

    def update(self, dt):
        if self.paused or self.state in ("over", "win"):
            if self.paused:
                for p in self.popups:
                    p.update(dt)
                self.popups = [p for p in self.popups if p.life > 0]
            return

        if self.state == "wave":
            if self.spawn_queue:
                self.spawn_timer -= dt
                if self.spawn_timer <= 0:
                    self.enemies.append(Enemy(
                        self.spawn_queue.pop(0), self.wave,
                        pixel_wps=self.pixel_wps))
                    self.spawn_timer = self.spawn_interval

            for e in self.enemies:
                e.update(dt, self.enemies)
                if e.reached_end and not e.dead:
                    e.dead = True
                    self.lives -= 1

                # ====== Boss 增强逻辑 ======
                if e.etype == "boss" and not e.dead and not e.reached_end:
                    # 1. 每30秒10%概率摧毁附近5个塔
                    e.boss_destroy_timer += dt
                    if e.boss_destroy_timer >= e.boss_destroy_cooldown:
                        e.boss_destroy_timer = 0.0
                        if random.random() < 0.10:  # 10%概率
                            # 找附近的塔
                            nearby_towers = []
                            for t in self.towers:
                                dist = math.hypot(t.pos[0] - e.pos[0], t.pos[1] - e.pos[1])
                                if dist < 150:  # 150像素范围内
                                    nearby_towers.append((dist, t))
                            # 按距离排序，取最近的5个
                            nearby_towers.sort(key=lambda x: x[0])
                            for dist, t in nearby_towers[:5]:
                                cell = (t.col, t.row)
                                if cell in self.tower_grid:
                                    del self.tower_grid[cell]
                                self.towers.remove(t)
                                # 显示塔被摧毁的特效
                                self._add_popup(t.pos[0], t.pos[1], 0, RED)

            spawned = []  # 收集本帧新生成的敌人，循环结束后再统一加入（避免遍历中修改列表）
            for e in self.enemies:
                if e.dead and not e.paid:
                    e.paid = True
                    
                    # ====== Boss 复活逻辑 ======
                    if e.etype == "boss" and not e.boss_has_revived:
                        # Boss复活！
                        e.dead = False
                        e.paid = False
                        e.boss_has_revived = True  # 重点：标记已复活，只能一次！
                        e.hp = int(e.max_hp * 0.6)  # 复活后60%血量
                        e.boss_invincible_timer = 3.0  # 3秒无敌
                        e.boss_immune_debuff = True  # 无视负面效果
                        e.slow_timer = 0.0  # 清除减速
                        e.slow_factor = 1.0
                        
                        # 召唤10个随机敌人（非Boss）
                        spawn_types = ["normal", "fast", "tank", "swarm", "healer", "split"]
                        for _ in range(10):
                            stype = random.choice(spawn_types)
                            child = Enemy(stype, self.wave, hp_scale=0.5,
                                pos=[e.pos[0] + random.uniform(-30, 30),
                                     e.pos[1] + random.uniform(-30, 30)],
                                pixel_wps=self.pixel_wps)
                            child.wp_index = e.wp_index
                            spawned.append(child)
                        
                        # 显示复活提示
                        self._add_popup(e.pos[0], e.pos[1] - 30, 0, PINK)
                        continue  # 跳过后续死亡处理
                    
                    if not e.reached_end:
                        self._add_money(e.reward)
                        self._add_popup(e.pos[0], e.pos[1] - 8, e.reward)
                    if e.etype == "split":
                        for _ in range(2):
                            child = Enemy("swarm", 1, hp_scale=0.6,
                                pos=[e.pos[0] + random.uniform(-12, 12),
                                     e.pos[1] + random.uniform(-12, 12)],
                                pixel_wps=self.pixel_wps)
                            child.max_hp = 30
                            child.hp = 30
                            child.wp_index = e.wp_index
                            spawned.append(child)
            self.enemies.extend(spawned)
            self.enemies = [e for e in self.enemies if not e.dead]

            for t in self.towers:
                t.update(dt, self.enemies, self.projectiles)
            for p in self.projectiles:
                p.update(dt, self.enemies)
            self.projectiles = [p for p in self.projectiles if not p.dead]

            for p in self.popups:
                p.update(dt)
            self.popups = [p for p in self.popups if p.life > 0]

            if not self.spawn_queue and not self.enemies:
                bonus = 25 + self.wave * 8
                self._add_money(bonus)
                self._add_popup(PLAY_W // 2, HEIGHT // 2 - 30, bonus, CYAN)
                if self.wave >= MAX_WAVES:
                    self.state = "win"
                else:
                    self.state = "idle"
                    self.between_timer = 4.0

        elif self.state == "idle":
            if self.between_timer > 0:
                self.between_timer -= dt
                if self.between_timer <= 0:
                    self._start_wave()

        if self.lives <= 0:
            self.state = "over"

    def draw(self):
        self.screen.fill(GRASS)
        for r in range(ROWS):
            for c in range(COLS):
                rect = pygame.Rect(c * TILE, r * TILE, TILE, TILE)
                if (c, r) in self.path_cells:
                    pygame.draw.rect(self.screen, PATH_C, rect)
                else:
                    pygame.draw.rect(self.screen, GRID_C, rect, 1)
        ex, ey = self.pixel_wps[-1]
        pygame.draw.rect(self.screen, ORANGE, (PLAY_W - 6, ey - 18, 6, 36))

        for ob in self.obstacles:
            draw_obstacle(self.screen, ob)

        for t in self.towers:
            t.draw(self.screen, selected=(t is self.selected_tower))
        for e in self.enemies:
            e.draw(self.screen, self.sfont)
        for p in self.projectiles:
            p.draw(self.screen)
        for p in self.popups:
            p.draw(self.screen, self.bfont)

        self._draw_sidebar()
        if self.shovel_dragging:
            self._draw_shovel_drag()
        if self.paused:
            self._draw_pause()
        if self.state == "over":
            self._draw_overlay("GAME OVER", "Click to exit")
        elif self.state == "win":
            self._draw_overlay("VICTORY!", "Click to exit")
        pygame.display.flip()

    def _draw_sidebar(self):
        pygame.draw.rect(self.screen, DARK, (PLAY_W, 0, SIDE_W, HEIGHT))
        title = self.font.render("TOWER DEFENSE", True, WHITE)
        self.screen.blit(title, (PLAY_W + 14, 12))
        map_label = self.sfont.render(f"Map: {self.map_name}", True, CYAN)
        self.screen.blit(map_label, (PLAY_W + 14, 48))
        ver = self.sfont.render("50 Waves  -  v7.2", True, (150, 155, 165))
        self.screen.blit(ver, (PLAY_W + 14, 70))

        mtxt = self.mfont.render(f"${self.money}", True, YELLOW)
        self.screen.blit(mtxt, (PLAY_W + 20, 95))
        self.screen.blit(self.sfont.render("MONEY", True, (180, 190, 200)),
                         (PLAY_W + 20, 95 + mtxt.get_height() + 2))
        self.screen.blit(self.sfont.render(f"Total earned: ${self.total_earned}",
                         True, (140, 150, 160)),
                         (PLAY_W + 20, 95 + mtxt.get_height() + 22))

        self.screen.blit(self.bfont.render(f"Lives: {self.lives}", True, (220, 90, 90)),
                         (PLAY_W + 20, 192))
        self.screen.blit(self.bfont.render(f"Wave:  {self.wave}/{MAX_WAVES}", True, WHITE),
                         (PLAY_W + 20, 218))

        for key, rect in self.type_rects.items():
            s = TOWER_TYPES[key]
            hover = rect.collidepoint(pygame.mouse.get_pos())
            col = BTN_HI if (hover or self.selected_type == key) else BTN
            pygame.draw.rect(self.screen, col, rect)
            pygame.draw.rect(self.screen, s["color"], (rect.x + 8, rect.y + 14, 14, 14))
            self.screen.blit(self.bfont.render(s["name"], True, WHITE),
                             (rect.x + 30, rect.y + 8))
            self.screen.blit(self.sfont.render(f"${s['cost']}", True, YELLOW),
                             (rect.x + 30, rect.y + 30))
            self.screen.blit(self.sfont.render(s["desc"], True, (200, 210, 220)),
                             (rect.x + 78, rect.y + 20))

        if self.selected_tower:
            t = self.selected_tower
            s = TOWER_TYPES[t.ttype]
            py = HEIGHT - 184
            self.screen.blit(self.bfont.render(f"{s['name']} Lv{t.level}", True, WHITE),
                             (PLAY_W + 20, py))
            self.screen.blit(self.sfont.render(f"DMG {t.damage:.0f}  RNG {t.range:.0f}",
                             True, (200, 210, 220)), (PLAY_W + 20, py + 22))
            up_rect = pygame.Rect(PLAY_W + 20, HEIGHT - 150, SIDE_W - 40, 34)
            can = self.money >= t.upgrade_cost and t.level < 4
            pygame.draw.rect(self.screen, (60, 120, 60) if can else GRAY, up_rect)
            txt = "MAX LEVEL" if t.level >= 4 else f"UPGRADE  ${t.upgrade_cost}"
            self.screen.blit(self.bfont.render(txt, True, WHITE),
                             (up_rect.x + 14, up_rect.y + 8))

        # ====== 铲子按钮（拖拽到炮塔上松手出售）======
        srect = self.shovel_rect
        scol = (120, 100, 60) if self.shovel_dragging else BTN
        pygame.draw.rect(self.screen, scol, srect)
        pygame.draw.rect(self.screen, (210, 210, 210),
                         (srect.x + 12, srect.y + 5, 5, 18))
        pygame.draw.polygon(self.screen, (195, 195, 205), [
            (srect.x + 7, srect.y + 23), (srect.x + 27, srect.y + 23),
            (srect.x + 23, srect.y + 33), (srect.x + 11, srect.y + 33)])
        self.screen.blit(self.bfont.render("SHOVEL", True, WHITE),
                         (srect.x + 34, srect.y + 7))
        self.screen.blit(self.sfont.render("Drag onto a tower", True, (200, 210, 220)),
                         (srect.x + 34, srect.y + 22))

        pbtn = self.pause_btn
        pcol = (200, 150, 50) if self.paused else (80, 95, 110)
        pygame.draw.rect(self.screen, pcol, pbtn)
        self.screen.blit(self.bfont.render("PAUSE  (P)", True, WHITE),
                         (pbtn.x + 14, pbtn.y + 7))

        btn = self.start_btn
        active = self.state == "idle" and not self.paused
        pygame.draw.rect(self.screen, (60, 140, 70) if active else GRAY, btn)
        label = "START WAVE" if active else (
            "WAVE IN PROGRESS" if self.state == "wave" else "...")
        self.screen.blit(self.bfont.render(label, True, WHITE),
                         (btn.x + 18, btn.y + 9))

        if self.state == "idle" and self.between_timer > 0 and not self.paused:
            self.screen.blit(self.sfont.render(
                f"Next wave in {self.between_timer:.1f}s", True, (200, 210, 220)),
                (PLAY_W + 20, 246))

    def _draw_shovel_drag(self):
        x, y = self.shovel_pos
        if x < PLAY_W:
            col = x // TILE
            row = y // TILE
            if 0 <= col < COLS and 0 <= row < ROWS:
                t = self.tower_grid.get((col, row))
                if t:
                    pygame.draw.circle(self.screen, RED, t.pos, 22, 3)
                    val = self.bfont.render(f"Sell +${t.sell_value}", True, GREEN)
                    self.screen.blit(val, (t.pos[0] - val.get_width() // 2,
                                           t.pos[1] - 38))
        # 跟随光标的铲子图标
        pygame.draw.line(self.screen, (225, 225, 225), (x, y - 14), (x, y + 4), 5)
        pygame.draw.polygon(self.screen, (205, 205, 215), [
            (x - 9, y + 4), (x + 9, y + 4), (x + 6, y + 16), (x - 6, y + 16)])

    def _draw_pause(self):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (0, 0))
        t = self.mfont.render("PAUSED", True, WHITE)
        s = self.bfont.render("Press  P  to resume", True, (220, 220, 220))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 40))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 10))

    def _draw_overlay(self, text, sub):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        self.screen.blit(overlay, (0, 0))
        t = self.font.render(text, True, WHITE)
        s = self.bfont.render(sub, True, (220, 220, 220))
        self.screen.blit(t, (WIDTH // 2 - t.get_width() // 2, HEIGHT // 2 - 30))
        self.screen.blit(s, (WIDTH // 2 - s.get_width() // 2, HEIGHT // 2 + 10))

    def run(self):
        running = True
        while running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.state in ("over", "win"):
                        running = False
                    elif self.shovel_rect.collidepoint(event.pos):
                        self.shovel_dragging = True
                        self.shovel_pos = event.pos
                    else:
                        self.handle_click(event.pos)
                elif event.type == pygame.MOUSEMOTION:
                    if self.shovel_dragging:
                        self.shovel_pos = event.pos
                elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                    if self.shovel_dragging:
                        self._drop_shovel(event.pos)
                        self.shovel_dragging = False
                elif event.type == pygame.KEYDOWN:
                    if self.state in ("over", "win"):
                        continue
                    if event.key == pygame.K_SPACE and self.state == "idle" and not self.paused:
                        self._start_wave()
                    elif event.key == pygame.K_p:
                        self._toggle_pause()
                    elif event.key == pygame.K_ESCAPE:
                        self.selected_type = None
                        self.selected_tower = None

            self.update(dt)
            self.draw()

        pygame.quit()


# =============================================================================
# 入口
# =============================================================================
if __name__ == "__main__":
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Tower Defense 2D  -  Map Select")
    chosen = run_map_picker(screen)
    pygame.quit()

    if chosen is None:
        exit()

    Game(chosen).run()
