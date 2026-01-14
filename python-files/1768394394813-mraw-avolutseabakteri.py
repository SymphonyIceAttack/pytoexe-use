import sys
import math
import random
import pygame
from typing import List, Tuple, Optional, Deque
from collections import deque

#Управление 1 2 3 4 5 6 менясть виды бактерий 
#лкм спавн еды или кристалов пкм спавн организмов n много еды в рандом месте mкристалы под мышкой сркм много еды под мышкой




WIDTH, HEIGHT = 1400, 900
PANEL_W = 520
WORLD_W = WIDTH - PANEL_W
WORLD_H = HEIGHT

BG_COLOR = (14, 16, 22)
WORLD_COLOR = (17, 19, 24)
PANEL_COLOR = (26, 28, 36)
PANEL_ACCENT = (64, 120, 255)
GRID_COLOR = (34, 36, 46)
TEXT_COLOR = (240, 244, 255)
MUTED_TEXT = (185, 190, 205)

NUTRIENT_COLOR = (130, 190, 90)
VIRUS_COLOR = (210, 70, 170)
SUN_COLOR = (255, 240, 170)
CRYSTAL_COLOR = (120, 210, 255)

random.seed()

def draw_header(surface: pygame.Surface, font: pygame.font.Font, text: str, y: int):
    lbl = font.render(text, True, TEXT_COLOR)
    surface.blit(lbl, (20, y))
    pygame.draw.line(surface, PANEL_ACCENT, (18, y+30), (PANEL_W-18, y+30), 2)

def draw_label(surface, font_small, label, value, y):
    surface.blit(font_small.render(label, True, MUTED_TEXT), (22, y))
    surface.blit(font_small.render(value, True, TEXT_COLOR), (260, y))

def draw_graph(surface: pygame.Surface, rect: pygame.Rect, data: List[float], color: Tuple[int,int,int]):
    if not data:
        return
    pygame.draw.rect(surface, (30,32,40), rect, border_radius=10)
    pygame.draw.rect(surface, (50,54,64), rect, 1, border_radius=10)
    if len(data) < 2:
        return
    m = max(1.0, max(data))
    n = len(data)
    w = rect.width
    h = rect.height
    pts = []
    for i, v in enumerate(data):
        x = rect.x + int(i*(w-2)/(n-1)) + 1
        y = rect.y + h - 2 - int((v/m)*(h-4))
        pts.append((x, y))
    if len(pts) >= 2:
        pygame.draw.lines(surface, color, False, pts, 2)

def draw_glow(surface: pygame.Surface, pos: Tuple[int,int], radius: int, color: Tuple[int,int,int], strength: int=3):
    x, y = pos
    for i in range(strength, 0, -1):
        r = int(radius * (i/strength))
        a = int(40 * (i/strength))
        s = pygame.Surface((r*2, r*2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*color, a), (r, r), r)
        surface.blit(s, (x-r, y-r), special_flags=pygame.BLEND_ADD)

def draw_bar(surface: pygame.Surface, rect: pygame.Rect, ratio: float, color: Tuple[int,int,int]):
    pygame.draw.rect(surface, (30,32,40), rect, border_radius=8)
    pygame.draw.rect(surface, (50,54,64), rect, 1, border_radius=8)
    w = max(0, min(1.0, ratio)) * (rect.width-2)
    inner = pygame.Rect(rect.x+1, rect.y+1, int(w), rect.height-2)
    pygame.draw.rect(surface, color, inner, border_radius=8)

class Button:
    def __init__(self, rect: pygame.Rect, text: str, font: pygame.font.Font, color=(50,54,64), hover=(70,76,88)):
        self.rect = rect
        self.text = text
        self.font = font
        self.color = color
        self.hover = hover

    def draw(self, surface: pygame.Surface, mouse_pos: Tuple[int,int]) -> None:
        col = self.hover if self.rect.collidepoint(mouse_pos) else self.color
        pygame.draw.rect(surface, col, self.rect, border_radius=10)
        pygame.draw.rect(surface, (90,94,106), self.rect, 2, border_radius=10)
        label = self.font.render(self.text, True, TEXT_COLOR)
        surface.blit(label, (self.rect.x + (self.rect.w - label.get_width())//2, self.rect.y + (self.rect.h - label.get_height())//2))

    def hit(self, pos: Tuple[int,int]) -> bool:
        return self.rect.collidepoint(pos)

class Particle:
    __slots__ = ("x","y","vx","vy","life","color")
    def __init__(self, x, y, color):
        ang = random.uniform(0, math.tau)
        spd = random.uniform(20, 120)
        self.x = x
        self.y = y
        self.vx = math.cos(ang)*spd
        self.vy = math.sin(ang)*spd
        self.life = random.uniform(0.3, 0.9)
        self.color = color
    def update(self, dt):
        self.life -= dt
        self.x += self.vx*dt
        self.y += self.vy*dt
        self.vx *= 0.95
        self.vy *= 0.95
    def draw(self, surface):
        if self.life <= 0: return
        a = max(0, min(255, int(255*self.life)))
        pygame.draw.circle(surface, (*self.color, a), (int(self.x), int(self.y)), 2)

class SunLight:
    """Глобальный день/ночь. Источник энергии и индикатор на панели. Без оверлея."""
    def __init__(self, period: float = 60.0, duty: float = 0.6):
        self.period = period
        self.duty = duty
        self.t = random.uniform(0, period)
        self.energy_scale = 26.0
    def step(self, dt: float):
        self.t = (self.t + dt) % self.period
    def intensity(self) -> float:
        phase = self.t / self.period
        val = 0.5*(1.0 + math.sin(2*math.pi*phase - math.pi/2))
        if val < (1.0 - self.duty):
            return 0.0
        day_min = (1.0 - self.duty)
        norm = (val - day_min) / (1.0 - day_min)
        return max(0.0, min(1.0, norm**1.3))
    def sample(self, x: float, y: float) -> float:
        return self.intensity()
    def draw_indicator(self, surface: pygame.Surface, rect: pygame.Rect, font_small: pygame.font.Font):
        k = self.intensity()
        cx = rect.x + rect.width//2
        cy = rect.y + rect.height//2
        r = min(rect.width, rect.height)//2 - 6
        pygame.draw.circle(surface, (40,42,52), (cx,cy), r+4)
        pygame.draw.circle(surface, (60,64,74), (cx,cy), r+4, 1)
        pygame.draw.circle(surface, SUN_COLOR, (cx,cy), r-6, 1)
        a2 = k * 2*math.pi
        pygame.draw.arc(surface, SUN_COLOR, (cx-r, cy-r, 2*r, 2*r), -math.pi/2, -math.pi/2 + a2, 4)
        label = "День" if k > 0.01 else "Ночь"
        surface.blit(font_small.render(f"Солнце: {label} ({k:.2f})", True, TEXT_COLOR), (rect.x, rect.y + rect.height + 8))

class Nutrient:
    __slots__ = ("x", "y", "energy", "phase")
    def __init__(self, x: float, y: float, energy: float = 25.0):
        self.x = x
        self.y = y
        self.energy = energy
        self.phase = random.random() * math.tau

class MutationCrystal:
    __slots__ = ("x","y","phase","potency")
    def __init__(self, x: float, y: float, potency: float = 150.0):
        self.x = x
        self.y = y
        self.phase = random.random() * math.tau
        self.potency = potency
    def draw(self, surface: pygame.Surface, t: float):
        phase = self.phase + t
        r = 3 + int((math.sin(phase*3.2)+1)*1.0)
        col = (CRYSTAL_COLOR[0], int(CRYSTAL_COLOR[1] + 30*math.sin(phase*2.1)), CRYSTAL_COLOR[2])
        draw_glow(surface, (int(self.x), int(self.y)), 18, (140,220,255), strength=2)
        pygame.draw.circle(surface, col, (int(self.x), int(self.y)), r)
        pygame.draw.circle(surface, (255,255,255), (int(self.x), int(self.y)), 1)

class Virus:
    __slots__ = ("x","y","angle","speed","life")
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y
        self.angle = random.uniform(0, math.tau)
        self.speed = random.uniform(80, 140)
        self.life = random.uniform(18.0, 35.0)
    def update(self, dt: float, bacteria: List["Bacterium"]):
        target = None
        best_d2 = 1e18
        for b in bacteria:
            dx = b.x - self.x
            dy = b.y - self.y
            d2 = dx*dx + dy*dy
            if d2 < best_d2:
                best_d2 = d2
                target = b
        if target is not None:
            desired = math.atan2(target.y - self.y, target.x - self.x)
            da = (desired - self.angle + math.pi) % (2*math.pi) - math.pi
            self.angle += max(-6.0*dt, min(6.0*dt, da))
        else:
            self.angle += random.uniform(-1.0, 1.0)*dt
        self.x += math.cos(self.angle) * self.speed * dt
        self.y += math.sin(self.angle) * self.speed * dt
        if self.x < 0: self.x=0; self.angle = math.pi - self.angle
        elif self.x > WORLD_W: self.x=WORLD_W; self.angle = math.pi - self.angle
        if self.y < 0: self.y=0; self.angle = -self.angle
        elif self.y > WORLD_H: self.y=WORLD_H; self.angle = -self.angle
        self.life -= dt
    def alive(self) -> bool:
        return self.life > 0
    def draw(self, surface: pygame.Surface):
        r = 4
        cx, cy = int(self.x), int(self.y)
        draw_glow(surface, (cx, cy), 12, (240,120,220), strength=2)
        pygame.draw.circle(surface, VIRUS_COLOR, (cx, cy), r)
        for i in range(6):
            a = self.angle + i * (math.tau/6)
            x1 = int(cx + math.cos(a)*r)
            y1 = int(cy + math.sin(a)*r)
            x2 = int(cx + math.cos(a)*(r+3))
            y2 = int(cy + math.sin(a)*(r+3))
            pygame.draw.line(surface, (235, 160, 220), (x1, y1), (x2, y2), 1)

KIND_LIST = ["chemo", "photo", "armored", "omnivore", "sprinter", "giant"]
KIND_NAME = {
    "chemo": "Хемо",
    "photo": "Фото",
    "armored": "Броня",
    "omnivore": "Всеядн.",
    "sprinter": "Спринт.",
    "giant": "Гигант",
}

class Bacterium:
    __slots__ = (
        "x", "y", "vx", "vy", "angle",
        "energy", "age", "gen",
        "speed", "sense", "efficiency", "size",
        "kind", "repro_mode",
        "color",
        "level", "xp", "next_xp",
    )
    def __init__(self, x: float, y: float, traits=None, gen: int = 0, kind: str = "chemo"):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.angle = random.uniform(0, math.tau)
        self.energy = 60.0
        self.age = 0
        self.gen = gen
        self.kind = kind
        self.repro_mode = 'asexual'
        self.level = 1
        self.xp = 0.0
        self.next_xp = 100.0
        if traits is None:
            if self.kind == 'photo':
                self.speed = random.uniform(28, 70)
                self.sense = random.uniform(50, 160)
                self.efficiency = random.uniform(0.55, 0.98)
                self.size = random.uniform(2.6, 5.4)
            elif self.kind == 'armored':
                self.speed = random.uniform(25, 60)
                self.sense = random.uniform(40, 130)
                self.efficiency = random.uniform(0.45, 0.9)
                self.size = random.uniform(3.8, 6.6)
            elif self.kind == 'omnivore':
                self.speed = random.uniform(35, 75)
                self.sense = random.uniform(50, 150)
                self.efficiency = random.uniform(0.5, 0.92)
                self.size = random.uniform(2.8, 5.8)
                self.repro_mode = 'sexual'
            elif self.kind == 'sprinter':
                self.speed = random.uniform(80, 120)
                self.sense = random.uniform(40, 120)
                self.efficiency = random.uniform(0.3, 0.6)
                self.size = random.uniform(2.0, 3.2)
                self.repro_mode = 'sexual'
            elif self.kind == 'giant':
                self.speed = random.uniform(20, 40)
                self.sense = random.uniform(40, 120)
                self.efficiency = random.uniform(0.55, 0.9)
                self.size = random.uniform(6.0, 8.0)
            else:
                self.speed = random.uniform(30, 80)
                self.sense = random.uniform(40, 150)
                self.efficiency = random.uniform(0.4, 0.95)
                self.size = random.uniform(2.5, 5.5)
        else:
            self.speed, self.sense, self.efficiency, self.size = traits
        base_b = (60 + int((self.sense/160)*120))
        if self.kind == "photo":
            r = int(70 + (1.0 - self.efficiency) * 80)
            g = int(160 + (self.efficiency) * 90)
            b = int(base_b * 0.6)
        elif self.kind == "armored":
            r = 60; g = 140; b = int(180 + (self.sense/150)*60)
        elif self.kind == 'omnivore':
            r = 120; g = int(150 + 80*self.efficiency); b = int(120 + 60*(self.sense/150))
        elif self.kind == 'sprinter':
            r = int(200); g = int(80 + 100*self.efficiency); b = 80
        elif self.kind == 'giant':
            r = 150; g = 120; b = int(160 + 60*(self.efficiency))
        else:
            r = int(110 + (1.0 - self.efficiency) * 145)
            g = int(85 + (self.efficiency) * 150)
            b = base_b
        self.color = (min(255, r), min(255, g), min(255, b))
    def max_energy(self):
        return 100 + self.size * 40
    def radius(self):
        return max(2, int(self.size))
    def gain_xp(self, amount: float):
        self.xp += amount
        while self.xp >= self.next_xp:
            self.xp -= self.next_xp
            self.level += 1
            self.next_xp *= 1.35
            self.speed = min(self.speed * 1.02 + 0.3, 140)
            self.sense = min(self.sense * 1.02 + 1.0, 200)
            self.efficiency = max(0.2, min(1.1, self.efficiency * 1.01 + 0.005))
            self.size = max(1.2, min(8.5, self.size * 1.01 + 0.05))
            self.energy = min(self.max_energy(), self.energy + 20)
    def update(self, dt: float, nutrients: List[Nutrient], sun: SunLight, viruses: List["Virus"], crystals: List[MutationCrystal], particles: List[Particle]):
        sense_eff = self.sense * (1.0 + min(0.6, 0.05 * self.gen) + min(0.3, 0.03 * (self.level-1)))
        learn = min(1.7, 0.5 + 0.08 * self.gen + 0.05 * (self.level-1))
        target_pos: Optional[Tuple[float, float]] = None
        if self.kind in ("chemo", "armored", "omnivore", "sprinter", "giant"):
            best_d2 = sense_eff * sense_eff
            for n in nutrients:
                dx = n.x - self.x
                dy = n.y - self.y
                d2 = dx*dx + dy*dy
                if d2 <= best_d2:
                    best_d2 = d2
                    target_pos = (n.x, n.y)
        flee_vec_x, flee_vec_y = 0.0, 0.0
        threat_rad = sense_eff * 1.0
        near_threat = 0.0
        for v in viruses:
            dx = self.x - v.x
            dy = self.y - v.y
            d2 = dx*dx + dy*dy
            if d2 <= threat_rad*threat_rad:
                d = math.sqrt(d2) + 1e-5
                w = (threat_rad - d) / threat_rad
                flee_vec_x += (dx / d) * w
                flee_vec_y += (dy / d) * w
                near_threat = max(near_threat, w)
        flee_len = math.hypot(flee_vec_x, flee_vec_y)
        if flee_len > 1e-5:
            flee_vec_x /= flee_len
            flee_vec_y /= flee_len
        seek_vec_x, seek_vec_y = 0.0, 0.0
        if target_pos is not None:
            dx = target_pos[0] - self.x
            dy = target_pos[1] - self.y
            d = math.hypot(dx, dy) + 1e-6
            seek_vec_x = dx / d
            seek_vec_y = dy / d
        else:
            seek_vec_x = math.cos(self.angle)
            seek_vec_y = math.sin(self.angle)
        avoid_w = min(2.8, learn * (1.0 + 1.7 * near_threat))
        if self.kind == "armored":
            avoid_w *= 0.6
        out_x = seek_vec_x + flee_vec_x * avoid_w
        out_y = seek_vec_y + flee_vec_y * avoid_w
        out_len = math.hypot(out_x, out_y)
        if out_len > 1e-5:
            desired_angle = math.atan2(out_y, out_x)
            turn_rate = 4.8
            da = (desired_angle - self.angle + math.pi) % (2*math.pi) - math.pi
            self.angle += max(-turn_rate*dt, min(turn_rate*dt, da))
        else:
            self.angle += random.uniform(-0.8, 0.8) * dt
        speed_now = self.speed * (0.6 + 0.4 * self.energy / self.max_energy())
        self.vx = math.cos(self.angle) * speed_now
        self.vy = math.sin(self.angle) * speed_now
        self.x += self.vx * dt
        self.y += self.vy * dt
        if self.x < 0:
            self.x = 0; self.angle = math.pi - self.angle
        elif self.x > WORLD_W:
            self.x = WORLD_W; self.angle = math.pi - self.angle
        if self.y < 0:
            self.y = 0; self.angle = -self.angle
        elif self.y > WORLD_H:
            self.y = WORLD_H; self.angle = -self.angle
        move_cost = (abs(self.vx) + abs(self.vy)) * 0.02 / max(0.2, self.efficiency)
        upkeep = 4.0 + self.size * 1.2
        if self.kind == "armored":
            upkeep *= 1.15
        if self.kind == "giant":
            upkeep *= 1.25
        self.energy -= (move_cost + upkeep) * dt
        eaten = []
        gained = 0.0
        for i, n in enumerate(nutrients):
            dx = n.x - self.x
            dy = n.y - self.y
            if dx*dx + dy*dy <= (self.radius()+3)**2:
                factor = self.efficiency
                if self.kind == "photo":
                    factor *= 0.5
                gain = n.energy * factor
                self.energy += gain
                gained += gain
                eaten.append(i)
        if gained > 0:
            self.gain_xp(gained * 0.6)
            for _ in range(8):
                particles.append(Particle(self.x, self.y, (160, 230, 120)))
        for i in reversed(eaten):
            nutrients.pop(i)
        consumed_idx = []
        for i, c in enumerate(crystals):
            dx = c.x - self.x
            dy = c.y - self.y
            if dx*dx + dy*dy <= (self.radius()+5)**2:
                bonus = c.potency
                self.energy = min(self.max_energy(), self.energy + bonus*0.35)
                self.gain_xp(bonus)
                choice = random.choice(['speed','sense','efficiency'])
                if choice == 'speed':
                    self.speed = min(150, self.speed * 1.04 + 1.0)
                elif choice == 'sense':
                    self.sense = min(210, self.sense * 1.04 + 2.0)
                else:
                    self.efficiency = min(1.1, self.efficiency * 1.03 + 0.01)
                consumed_idx.append(i)
                for _ in range(14):
                    particles.append(Particle(self.x, self.y, (140, 220, 255)))
        for i in reversed(consumed_idx):
            crystals.pop(i)
        sun_k = sun.sample(self.x, self.y)
        if sun_k > 0.0:
            add = 0.0
            if self.kind == 'photo':
                add = sun_k * sun.energy_scale * self.efficiency * dt
            elif self.kind == 'omnivore':
                add = sun_k * (sun.energy_scale * 0.45) * self.efficiency * dt
            elif self.kind == 'giant':
                add = sun_k * (sun.energy_scale * 0.25) * self.efficiency * dt
            if add > 0:
                self.energy += add
                self.gain_xp(add * 4.0)
        self.gain_xp(2.0 * dt)
        if self.energy > self.max_energy():
            self.energy = self.max_energy()
        self.age += dt
    def alive(self):
        return self.energy > 0
    def can_reproduce_asexual(self):
        return self.repro_mode == 'asexual' and self.energy > 0.8 * self.max_energy() and self.age > 8
    def reproduce_asexual(self):
        self.energy *= 0.55
        bias_eff = 1.0 + random.uniform(0.0, 0.015)
        bias_sense = 1.0 + random.uniform(0.0, 0.02)
        child_traits = (
            self.speed * random.uniform(0.97, 1.03) + random.uniform(-5, 5),
            self.sense * random.uniform(0.96, 1.04) * bias_sense + random.uniform(-4, 6),
            max(0.2, min(1.1, self.efficiency * random.uniform(0.95, 1.05) * bias_eff + random.uniform(-0.02, 0.02))),
            max(1.2, min(8.5, self.size * random.uniform(0.95, 1.05) + random.uniform(-0.3, 0.3)))
        )
        child = Bacterium(self.x + random.uniform(-6, 6), self.y + random.uniform(-6, 6), child_traits, gen=self.gen+1, kind=self.kind)
        child.energy = self.energy * 0.8
        child.repro_mode = self.repro_mode
        return child
    def draw(self, surface: pygame.Surface):
        r = self.radius()
        dirx = math.cos(self.angle)
        diry = math.sin(self.angle)
        px, py = self.x, self.y
        draw_glow(surface, (int(px+2), int(py+2)), max(8, r+6), (0,0,0), strength=2)
        body_color = self.color
        outline = (max(0, body_color[0]-40), max(0, body_color[1]-40), max(0, body_color[2]-40))
        inner = (min(255, body_color[0]+20), min(255, body_color[1]+20), min(255, body_color[2]+20))
        width = r * 1.6
        head = (int(px + dirx*(r+5)), int(py + diry*(r+5)))
        left = (int(px - diry*(width*0.5) - dirx*(r*0.6)), int(py + dirx*(width*0.5) - diry*(r*0.6)))
        right = (int(px + diry*(width*0.5) - dirx*(r*0.6)), int(py - dirx*(width*0.5) - diry*(r*0.6)))
        pygame.draw.polygon(surface, inner, (head, left, right))
        pygame.draw.circle(surface, body_color, (int(px), int(py)), r)
        pygame.draw.circle(surface, outline, (int(px), int(py)), r, 1)
        whisker_len = min(30, 8 + self.sense * (0.18 if self.kind == "photo" else 0.15))
        if self.kind == "armored":
            whisker_len *= 0.9
        ang_off = 0.6
        for sign in (-1, 1):
            a = self.angle + sign*ang_off
            wx = int(px + math.cos(a)*whisker_len)
            wy = int(py + math.sin(a)*whisker_len)
            pygame.draw.line(surface, (240, 240, 240), (int(px), int(py)), (wx, wy), 1)
        eye_x = int(px + dirx * (r*0.6))
        eye_y = int(py + diry * (r*0.6))
        if self.kind == "photo":
            pygame.draw.circle(surface, (210, 255, 170), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (40, 80, 40), (eye_x, eye_y), max(1, r//4))
        elif self.kind == "armored":
            pygame.draw.circle(surface, (180, 220, 255), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (30, 60, 90), (eye_x, eye_y), max(1, r//4))
        elif self.kind == 'sprinter':
            pygame.draw.circle(surface, (255, 180, 140), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (80, 30, 30), (eye_x, eye_y), max(1, r//4))
        elif self.kind == 'giant':
            pygame.draw.circle(surface, (220, 200, 240), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (70, 50, 90), (eye_x, eye_y), max(1, r//4))
        elif self.kind == 'omnivore':
            pygame.draw.circle(surface, (210, 240, 200), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (40, 70, 40), (eye_x, eye_y), max(1, r//4))
        else:
            pygame.draw.circle(surface, (250, 250, 250), (eye_x, eye_y), max(1, r//3))
            pygame.draw.circle(surface, (20, 20, 20), (eye_x, eye_y), max(1, r//4))
        e_ratio = max(0.0, min(1.0, self.energy / self.max_energy()))
        bar_w = max(24, r*2 + 6)
        bar_h = 4
        bx = int(px - bar_w/2)
        by = int(py + r + 6)
        pygame.draw.rect(surface, (30,30,36), (bx, by, bar_w, bar_h))
        col = (int(255*(1-e_ratio)), int(200*e_ratio), 60)
        pygame.draw.rect(surface, col, (bx+1, by+1, int((bar_w-2)*e_ratio), bar_h-2))
        prog = min(0.999, self.xp / max(1.0, self.next_xp))
        if prog > 0:
            rect = pygame.Rect(int(px - (r+7)), int(py - (r+7)), (r+7)*2, (r+7)*2)
            color = (120, 200, 255) if self.kind != 'sprinter' else (255, 180, 120)
            pygame.draw.arc(surface, color, rect, -math.pi/2, -math.pi/2 + prog*2*math.pi, 2)
        if self.level >= 2:
            small = pygame.font.SysFont("segoeui,consolas", 12)
            surface.blit(small.render(str(min(self.level,9)), True, (255,255,255)), (int(px)-4, int(py)-4))

class World:
    def __init__(self):
        self.nutrients: List[Nutrient] = []
        self.crystals: List[MutationCrystal] = []
        self.bacteria: List[Bacterium] = []
        self.viruses: List[Virus] = []
        self.particles: List[Particle] = []
        self.time = 0.0
        self.sun = SunLight(period=100.0, duty=0.55)
        self.spawn_initial()
        self.trails_enabled = True
        self.trail_surface = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        self.trail_surface.fill((0,0,0,0))
        self.resource_timer = 0.0
        self.crystal_timer = 0.0
        self.default_spawn_kind = "chemo"
        self.hist_len = 300
        self.hist_pop: Deque[int] = deque(maxlen=self.hist_len)
        self.hist_vir: Deque[int] = deque(maxlen=self.hist_len)
        self.hist_sun: Deque[float] = deque(maxlen=self.hist_len)
        self.show_full_help = False
    def reset(self):
        self.__init__()
    def spawn_initial(self):
        for _ in range(12):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="chemo"))
        for _ in range(8):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="photo"))
        for _ in range(5):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="armored"))
        for _ in range(6):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="omnivore"))
        for _ in range(6):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="sprinter"))
        for _ in range(3):
            self.bacteria.append(Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind="giant"))
        for _ in range(300):
            self.spawn_nutrient()
        for _ in range(8):
            self.add_virus((random.uniform(40, WORLD_W-40), random.uniform(40, WORLD_H-40)))
        for _ in range(12):
            self.spawn_crystal()
    def spawn_nutrient(self, pos: Optional[Tuple[float,float]] = None, energy: float = 25.0):
        if pos is None:
            x = random.uniform(10, WORLD_W-10)
            y = random.uniform(10, WORLD_H-10)
        else:
            x, y = pos
        self.nutrients.append(Nutrient(x, y, energy))
    def spawn_crystal(self, pos: Optional[Tuple[float,float]] = None, potency: float = 150.0):
        if pos is None:
            x = random.uniform(10, WORLD_W-10)
            y = random.uniform(10, WORLD_H-10)
        else:
            x, y = pos
        self.crystals.append(MutationCrystal(x, y, potency))
    def burst_nutrients(self, center=None, count=140):
        if center is None:
            cx, cy = random.uniform(80, WORLD_W-80), random.uniform(80, WORLD_H-80)
        else:
            cx, cy = center
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            r = abs(random.gauss(0, 45))
            x = max(8, min(WORLD_W-8, cx + math.cos(ang)*r))
            y = max(8, min(WORLD_H-8, cy + math.sin(ang)*r))
            self.spawn_nutrient((x,y), energy=random.uniform(18, 35))
    def burst_crystals(self, center=None, count=24):
        if center is None:
            cx, cy = random.uniform(80, WORLD_W-80), random.uniform(80, WORLD_H-80)
        else:
            cx, cy = center
        for _ in range(count):
            ang = random.uniform(0, math.tau)
            r = abs(random.gauss(0, 35))
            x = max(8, min(WORLD_W-8, cx + math.cos(ang)*r))
            y = max(8, min(WORLD_H-8, cy + math.sin(ang)*r))
            self.spawn_crystal((x,y), potency=random.uniform(120, 220))
    def add_random_bacterium(self, kind: Optional[str] = None):
        if kind is None:
            kind = random.choice(KIND_LIST)
        b = Bacterium(random.uniform(60, WORLD_W-60), random.uniform(60, WORLD_H-60), kind=kind)
        b.energy = random.uniform(50, 120)
        self.bacteria.append(b)
    def add_bacterium_at(self, pos: Tuple[float,float], kind: Optional[str] = None):
        x, y = pos
        if kind is None:
            kind = "chemo"
        b = Bacterium(x, y, kind=kind)
        b.energy = random.uniform(40, 100)
        self.bacteria.append(b)
    def add_virus(self, pos: Tuple[float,float]):
        self.viruses.append(Virus(pos[0], pos[1]))
    def step(self, dt: float):
        self.time += dt
        self.sun.step(dt)
        self.resource_timer += dt
        self.crystal_timer += dt
        spawn_rate = 30
        while self.resource_timer > 15.0 / spawn_rate:
            self.resource_timer -= 15.0 / spawn_rate
            self.spawn_nutrient()
        while self.crystal_timer > 6.0:
            self.crystal_timer -= 6.0
            if random.random() < 0.35:
                self.spawn_crystal()
        for b in self.bacteria:
            b.update(dt, self.nutrients, self.sun, self.viruses, self.crystals, self.particles)
        new_babies: List[Bacterium] = []
        for b in self.bacteria:
            if b.can_reproduce_asexual() and len(self.bacteria) + len(new_babies) < 1500:
                new_babies.append(b.reproduce_asexual())
                for _ in range(10):
                    self.particles.append(Particle(b.x, b.y, (255, 230, 160)))
        paired = set()
        for i, a in enumerate(self.bacteria):
            if a.repro_mode != 'sexual' or a.age < 6 or a.energy < 0.65*a.max_energy():
                continue
            if i in paired:
                continue
            best_j = -1
            best_d2 = (40 + a.radius()*2)**2
            for j in range(i+1, len(self.bacteria)):
                b = self.bacteria[j]
                if b.repro_mode != 'sexual' or b.kind != a.kind or j in paired:
                    continue
                if b.age < 6 or b.energy < 0.65*b.max_energy():
                    continue
                dx = a.x - b.x
                dy = a.y - b.y
                d2 = dx*dx + dy*dy
                if d2 < best_d2:
                    best_d2 = d2
                    best_j = j
            if best_j >= 0 and len(self.bacteria) + len(new_babies) < 1500:
                b = self.bacteria[best_j]
                traits = (
                    (a.speed + b.speed)/2 * random.uniform(0.97,1.03) + random.uniform(-3,3),
                    (a.sense + b.sense)/2 * random.uniform(0.97,1.03) + random.uniform(-3,3),
                    max(0.2, min(1.1, ((a.efficiency + b.efficiency)/2) * random.uniform(0.97,1.03) + random.uniform(-0.02,0.02))),
                    max(1.2, min(8.5, (a.size + b.size)/2 * random.uniform(0.97,1.03) + random.uniform(-0.2,0.2)))
                )
                child_gen = max(a.gen, b.gen) + 1
                child = Bacterium((a.x+b.x)/2 + random.uniform(-4,4), (a.y+b.y)/2 + random.uniform(-4,4), traits, gen=child_gen, kind=a.kind)
                child.repro_mode = a.repro_mode
                child.energy = min(a.energy, b.energy) * 0.6
                a.energy *= 0.6
                b.energy *= 0.6
                new_babies.append(child)
                for _ in range(14):
                    self.particles.append(Particle(child.x, child.y, (255, 220, 140)))
                paired.add(i); paired.add(best_j)
        self.bacteria = [b for b in self.bacteria if b.alive()]
        self.bacteria.extend(new_babies)
        for v in self.viruses:
            v.update(dt, self.bacteria)
        for v in self.viruses:
            for b in self.bacteria:
                dx = b.x - v.x
                dy = b.y - v.y
                if dx*dx + dy*dy <= (b.radius()+5)**2:
                    base_damage = 20.0
                    if b.kind == "armored":
                        damage = base_damage * 0.2
                        v.angle = math.atan2(v.y - b.y, v.x - b.x) + random.uniform(-0.3, 0.3)
                        v.x += math.cos(v.angle) * 2.0
                        v.y += math.sin(v.angle) * 2.0
                    else:
                        damage = base_damage
                    b.energy -= damage * dt
                    if random.random() < (0.02 if b.kind != "armored" else 0.006):
                        self.viruses.append(Virus(b.x + random.uniform(-6,6), b.y + random.uniform(-6,6)))
        died_positions = [(b.x, b.y) for b in self.bacteria if not b.alive()]
        if died_positions:
            for (x, y) in died_positions:
                for _ in range(random.randint(1, 3)):
                    self.viruses.append(Virus(x + random.uniform(-5,5), y + random.uniform(-5,5)))
        self.bacteria = [b for b in self.bacteria if b.alive()]
        self.viruses = [v for v in self.viruses if v.alive()]
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles:
            p.update(dt)
        self.hist_pop.append(len(self.bacteria))
        self.hist_vir.append(len(self.viruses))
        self.hist_sun.append(self.sun.intensity())
    def draw_world(self, surface: pygame.Surface):
        surface.fill(WORLD_COLOR)
        grid_step = 40
        for x in range(0, WORLD_W, grid_step):
            pygame.draw.line(surface, GRID_COLOR, (x,0), (x, WORLD_H))
        for y in range(0, WORLD_H, grid_step):
            pygame.draw.line(surface, GRID_COLOR, (0,y), (WORLD_W, y))
        if self.trails_enabled:
            self.trail_surface.fill((0,0,0,12), special_flags=pygame.BLEND_RGBA_SUB)
            for b in self.bacteria:
                pygame.draw.circle(self.trail_surface, (*b.color, 60), (int(b.x), int(b.y)), 1)
            surface.blit(self.trail_surface, (0,0))
        t = pygame.time.get_ticks() / 1000.0
        for n in self.nutrients:
            phase = n.phase + t
            r = 2 + int((math.sin(phase*3.0) + 1)*0.5)
            col = (NUTRIENT_COLOR[0], min(255, NUTRIENT_COLOR[1] + int(20*math.sin(phase*2.3))), NUTRIENT_COLOR[2])
            pygame.draw.circle(surface, col, (int(n.x), int(n.y)), r)
        for c in self.crystals:
            c.draw(surface, t)
        for b in self.bacteria:
            b.draw(surface)
        for v in self.viruses:
            v.draw(surface)
        for p in self.particles:
            p.draw(surface)
    def draw_panel(self, surface: pygame.Surface, font: pygame.font.Font, font_small: pygame.font.Font, sim_speed: int, paused: bool, spawn_kind: str):
        surface.fill(PANEL_COLOR)
        draw_header(surface, font, "Эволюция бактерий", 18)
        draw_label(surface, font_small, "Время", f"{self.time:6.1f}с", 58)
        draw_label(surface, font_small, "Скорость", f"x{sim_speed}", 86)
        draw_label(surface, font_small, "Пауза", "Да" if paused else "Нет", 114)
        draw_label(surface, font_small, "ПКМ спавнит", KIND_NAME.get(spawn_kind, spawn_kind), 142)
        draw_header(surface, font, "Солнце", 176)
        ind_rect = pygame.Rect(24, 208, 140, 140)
        self.sun.draw_indicator(surface, ind_rect, font_small)
        bar_rect = pygame.Rect(180, 248, PANEL_W-210, 28)
        draw_bar(surface, bar_rect, self.sun.intensity(), (255, 230, 120))
        draw_header(surface, font, "Популяции", 304)
        y = 336
        total = len(self.bacteria)
        draw_label(surface, font_small, "Всего", str(total), y); y += 28
        counts = {k:0 for k in KIND_LIST}
        for b in self.bacteria:
            counts[b.kind] = counts.get(b.kind, 0) + 1
        for k in KIND_LIST:
            label = KIND_NAME[k]
            cnt = counts.get(k, 0)
            surface.blit(font_small.render(label, True, MUTED_TEXT), (24, y))
            br = pygame.Rect(160, y, PANEL_W-190, 18)
            ratio = 0 if total == 0 else cnt/total
            color = (120,200,255) if k in ("chemo","omnivore") else (210,255,170) if k=="photo" else (180,210,255) if k=="armored" else (255,180,140) if k=="sprinter" else (220,200,240)
            draw_bar(surface, br, ratio, color)
            surface.blit(font_small.render(str(cnt), True, TEXT_COLOR), (br.x+br.width+8, y-2))
            y += 26
        surface.blit(font_small.render(f"Вирусы: {len(self.viruses)}", True, TEXT_COLOR), (24, y)); y += 26
        surface.blit(font_small.render(f"Питание: {len(self.nutrients)}", True, TEXT_COLOR), (24, y)); y += 26
        surface.blit(font_small.render(f"Кристаллы: {len(self.crystals)}", True, TEXT_COLOR), (24, y)); y += 26
        draw_header(surface, font, "Графики", y+10)
        gy = y + 42
        draw_graph(surface, pygame.Rect(24, gy, PANEL_W-48, 84), list(self.hist_pop), (120, 200, 255))
        surface.blit(font_small.render("Популяция", True, MUTED_TEXT), (28, gy-20))
        gy += 104
        draw_graph(surface, pygame.Rect(24, gy, PANEL_W-48, 84), list(self.hist_vir), (255, 140, 220))
        surface.blit(font_small.render("Вирусы", True, MUTED_TEXT), (28, gy-20))
        gy += 104
        draw_graph(surface, pygame.Rect(24, gy, PANEL_W-48, 84), list(self.hist_sun), (255, 235, 160))
        surface.blit(font_small.render("Интенсивность солнца", True, MUTED_TEXT), (28, gy-20))
        gy += 110
        draw_header(surface, font, "Управление (H — полная справка)", gy)
        y2 = gy + 34
        if not self.show_full_help:
            controls = [
                "Пробел — пауза; +/- — скорость",
                "ЛКМ — еда; СКМ — всплеск еды",
                "ПКМ — бактерия (1..6 вид); V — вирус",
                "N — всплеск еды; M — всплеск кристаллов",
                "Alt+ЛКМ — рисовать кристалы",
            ]
        else:
            controls = [
                "Пробел — пауза",
                "+/- — скорость",
                "T — следы",
                "ЛКМ — рисовать еду",
                "СКМ — всплеск еды",
                "ПКМ — бактерия (режим 1..6: хемо, фото, броня, всеядн., спринт., гигант)",
                "Shift+ПКМ — фото, Ctrl+ПКМ — броня",
                "V — вирус под курсором",
                "N — всплеск еды",
                "M — всплеск кристаллов",
                "Alt+ЛКМ — рисовать кристаллы",
                "R — сброс, Esc — выход",
            ]
        for c in controls:
            surface.blit(font_small.render(c, True, MUTED_TEXT), (24, y2))
            y2 += 26

class UI:
    def __init__(self, font: pygame.font.Font, font_small: pygame.font.Font):
        self.font = font
        self.font_small = font_small
        cx = WORLD_W//2
        cy = WORLD_H//2
        bw, bh = 320, 64
        gap = 20
        self.menu_buttons = [
            Button(pygame.Rect(cx-bw//2, cy- (bh*2 + gap), bw, bh), "Старт", font),
            Button(pygame.Rect(cx-bw//2, cy- (bh//2), bw, bh), "Настройки (скорость/вид)", font),
            Button(pygame.Rect(cx-bw//2, cy+ (bh + gap), bw, bh), "Выход", font),
        ]
        self.hud = {
            'pause': Button(pygame.Rect(16, WORLD_H-72, 90, 56), "Пауза", font_small),
            'minus': Button(pygame.Rect(116, WORLD_H-72, 60, 56), "-", font),
            'plus':  Button(pygame.Rect(182, WORLD_H-72, 60, 56), "+", font),
            'brush_food': Button(pygame.Rect(248, WORLD_H-72, 120, 56), "Еда", font_small),
            'brush_crys': Button(pygame.Rect(374, WORLD_H-72, 140, 56), "Кристаллы", font_small),
            'virus': Button(pygame.Rect(520, WORLD_H-72, 120, 56), "Вирус", font_small),
            'kind': Button(pygame.Rect(646, WORLD_H-72, 170, 56), "Вид: Хемо", font_small),
        }
        self.brush_mode = 'food'
    def draw_menu(self, surface: pygame.Surface):
        surface.fill(BG_COLOR)
        title = self.font.render("Эволюция бактерий", True, TEXT_COLOR)
        surface.blit(title, (WORLD_W//2 - title.get_width()//2, WORLD_H//2 - 220))
        mouse = pygame.mouse.get_pos()
        for b in self.menu_buttons:
            b.draw(surface, mouse)
    def draw_pause_overlay(self, surface: pygame.Surface, font: pygame.font.Font):
        overlay = pygame.Surface((WORLD_W, WORLD_H), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))
        surface.blit(overlay, (0,0))
        cx, cy = WORLD_W//2, WORLD_H//2
        bw, bh, gap = 320, 64, 20
        buttons = [
            Button(pygame.Rect(cx-bw//2, cy- (bh + gap), bw, bh), "Продолжить", font),
            Button(pygame.Rect(cx-bw//2, cy, bw, bh), "Перезапуск", font),
            Button(pygame.Rect(cx-bw//2, cy+ (bh + gap), bw, bh), "В меню", font),
        ]
        mouse = pygame.mouse.get_pos()
        for b in buttons:
            b.draw(surface, mouse)
        return buttons
    def draw_hud(self, surface: pygame.Surface, spawn_kind: str, paused: bool):
        mouse = pygame.mouse.get_pos()
        self.hud['pause'].text = "Плей" if paused else "Пауза"
        self.hud['kind'].text = f"Вид: {KIND_NAME.get(spawn_kind,'?')}"
        for btn in self.hud.values():
            btn.draw(surface, mouse)

SCENE_MENU = 0
SCENE_GAME = 1


def main():
    pygame.init()
    pygame.display.set_caption("Эволюция бактерий")
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("segoeui,consolas", 28)
    font_small = pygame.font.SysFont("segoeui,consolas", 20)

    ui = UI(font, font_small)

    scene = SCENE_MENU
    world: Optional[World] = None

    sim_speed = 1
    paused = False

    left_hold_timer = 0.0
    right_hold_timer = 0.0

    finger_down = False
    finger_pos = (0, 0)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.FINGERDOWN:
                fx = int(event.x * WIDTH)
                fy = int(event.y * HEIGHT)
                finger_down = True
                finger_pos = (fx, fy)
                pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONDOWN, {'pos': finger_pos, 'button': 1}))
            elif event.type == pygame.FINGERMOTION:
                fx = int(event.x * WIDTH)
                fy = int(event.y * HEIGHT)
                finger_pos = (fx, fy)
                pygame.mouse.set_pos(finger_pos)
            elif event.type == pygame.FINGERUP:
                fx = int(event.x * WIDTH)
                fy = int(event.y * HEIGHT)
                finger_down = False
                pygame.event.post(pygame.event.Event(pygame.MOUSEBUTTONUP, {'pos': (fx, fy), 'button': 1}))

            elif scene == SCENE_MENU:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    if ui.menu_buttons[0].hit((mx, my)):
                        world = World()
                        sim_speed = 1
                        paused = False
                        scene = SCENE_GAME
                    elif ui.menu_buttons[1].hit((mx, my)):
                        sim_speed = min(10, sim_speed + 1)
                    elif ui.menu_buttons[2].hit((mx, my)):
                        running = False
            else:
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        scene = SCENE_MENU
                        world = None
                    elif event.key == pygame.K_SPACE:
                        paused = not paused
                    elif event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                        sim_speed = min(10, sim_speed + 1)
                    elif event.key in (pygame.K_MINUS, pygame.K_UNDERSCORE):
                        sim_speed = max(1, sim_speed - 1)
                    elif event.key == pygame.K_t and world:
                        world.trails_enabled = not world.trails_enabled
                    elif event.key == pygame.K_n and world:
                        world.burst_nutrients()
                    elif event.key == pygame.K_b and world:
                        world.add_random_bacterium()
                    elif event.key == pygame.K_r and world:
                        world.reset()
                    elif event.key == pygame.K_1 and world:
                        world.default_spawn_kind = "chemo"
                    elif event.key == pygame.K_2 and world:
                        world.default_spawn_kind = "photo"
                    elif event.key == pygame.K_3 and world:
                        world.default_spawn_kind = "armored"
                    elif event.key == pygame.K_4 and world:
                        world.default_spawn_kind = "omnivore"
                    elif event.key == pygame.K_5 and world:
                        world.default_spawn_kind = "sprinter"
                    elif event.key == pygame.K_6 and world:
                        world.default_spawn_kind = "giant"
                    elif event.key == pygame.K_v and world:
                        mx, my = pygame.mouse.get_pos()
                        if mx < WORLD_W:
                            world.add_virus((mx, my))
                    elif event.key == pygame.K_m and world:
                        mx, my = pygame.mouse.get_pos()
                        if mx < WORLD_W:
                            world.burst_crystals(center=(mx, my), count=24)
                    elif event.key == pygame.K_h and world:
                        world.show_full_help = not world.show_full_help
                elif event.type == pygame.MOUSEBUTTONDOWN and world:
                    mx, my = event.pos
                    if my > WORLD_H - 90:
                        if ui.hud['pause'].hit((mx, my)):
                            paused = not paused
                        elif ui.hud['minus'].hit((mx, my)):
                            sim_speed = max(1, sim_speed - 1)
                        elif ui.hud['plus'].hit((mx, my)):
                            sim_speed = min(10, sim_speed + 1)
                        elif ui.hud['brush_food'].hit((mx, my)):
                            ui.brush_mode = 'food'
                        elif ui.hud['brush_crys'].hit((mx, my)):
                            ui.brush_mode = 'crystal'
                        elif ui.hud['virus'].hit((mx, my)):
                            wx, wy = pygame.mouse.get_pos()
                            if wx < WORLD_W:
                                world.add_virus((wx, wy))
                        elif ui.hud['kind'].hit((mx, my)):
                            cur = KIND_LIST.index(world.default_spawn_kind)
                            world.default_spawn_kind = KIND_LIST[(cur+1) % len(KIND_LIST)]
                    elif mx < WORLD_W:
                        mods = pygame.key.get_mods()
                        if event.button == 1:
                            if ui.brush_mode == 'crystal' or (mods & pygame.KMOD_ALT):
                                for _ in range(4):
                                    ang = random.uniform(0, math.tau)
                                    r = abs(random.gauss(0, 10))
                                    x = max(5, min(WORLD_W-5, mx + math.cos(ang)*r))
                                    y = max(5, min(WORLD_H-5, my + math.sin(ang)*r))
                                    world.spawn_crystal((x, y), potency=random.uniform(120,200))
                            else:
                                for _ in range(12):
                                    ang = random.uniform(0, math.tau)
                                    r = abs(random.gauss(0, 8))
                                    x = max(5, min(WORLD_W-5, mx + math.cos(ang)*r))
                                    y = max(5, min(WORLD_H-5, my + math.sin(ang)*r))
                                    world.spawn_nutrient((x, y), energy=random.uniform(18, 30))
                        elif event.button == 3:
                            kind = world.default_spawn_kind
                            if mods & pygame.KMOD_SHIFT:
                                kind = "photo"
                            elif mods & pygame.KMOD_CTRL:
                                kind = "armored"
                            world.add_bacterium_at((mx, my), kind=kind)
                        elif event.button == 2:
                            world.burst_nutrients(center=(mx, my), count=120)

        if scene == SCENE_GAME and world is not None:
            dt = min(0.033, clock.get_time() / 1000.0)
            if not paused:
                pressed = pygame.mouse.get_pressed(3)
                mx, my = pygame.mouse.get_pos()
                if mx < WORLD_W:
                    mods = pygame.key.get_mods()
                    if pressed[0]:
                        left_hold_timer += dt
                        while left_hold_timer >= 0.03:
                            left_hold_timer -= 0.03
                            if ui.brush_mode == 'crystal' or (mods & pygame.KMOD_ALT):
                                for _ in range(2):
                                    ang = random.uniform(0, math.tau)
                                    r = abs(random.gauss(0, 10))
                                    x = max(5, min(WORLD_W-5, mx + math.cos(ang)*r))
                                    y = max(5, min(WORLD_H-5, my + math.sin(ang)*r))
                                    world.spawn_crystal((x, y), potency=random.uniform(120,200))
                            else:
                                for _ in range(6):
                                    ang = random.uniform(0, math.tau)
                                    r = abs(random.gauss(0, 10))
                                    x = max(5, min(WORLD_W-5, mx + math.cos(ang)*r))
                                    y = max(5, min(WORLD_H-5, my + math.sin(ang)*r))
                                    world.spawn_nutrient((x, y), energy=random.uniform(16, 28))
                    else:
                        left_hold_timer = 0.0
                    if pressed[2]:
                        right_hold_timer += dt
                        while right_hold_timer >= 0.2:
                            right_hold_timer -= 0.2
                            kind = world.default_spawn_kind
                            mods = pygame.key.get_mods()
                            if mods & pygame.KMOD_SHIFT:
                                kind = "photo"
                            elif mods & pygame.KMOD_CTRL:
                                kind = "armored"
                            world.add_bacterium_at((mx, my), kind=kind)
                    else:
                        right_hold_timer = 0.0
                steps = max(1, sim_speed)
                sub_dt = min(0.016, dt)
                for _ in range(steps):
                    world.step(sub_dt)
            screen.fill(BG_COLOR)
            world.draw_world(screen.subsurface((0, 0, WORLD_W, WORLD_H)))
            panel_surface = screen.subsurface((WORLD_W, 0, PANEL_W, WORLD_H))
            world.draw_panel(panel_surface, font, font_small, sim_speed, paused, world.default_spawn_kind)
            ui.draw_hud(screen.subsurface((0,0,WORLD_W, WORLD_H)), world.default_spawn_kind, paused)
        else:
            ui.draw_menu(screen)
        pygame.display.flip()
        clock.tick(60)

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
