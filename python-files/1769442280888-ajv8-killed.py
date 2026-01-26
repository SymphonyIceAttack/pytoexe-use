import math
import random
import sys
from dataclasses import dataclass
from typing import List, Tuple
import pygame

WIDTH, HEIGHT = 960, 540
FPS = 60

BG_COLOR = (14, 16, 20)
GRID_COLOR = (22, 26, 34)
TEXT_COLOR = (230, 235, 245)

PLAYER_COLOR = (245, 245, 245)
PLAYER_HIT_COLOR = (255, 210, 80)
CRYSTAL_COLOR = (80, 240, 140)
ENEMY_COLOR = (250, 70, 70)
SHIELD_COLOR = (80, 160, 255)

BASE_SIZE = 14
CRYSTAL_SIZE = 12
ENEMY_SIZE = 16
SHIELD_SIZE = 12

MAX_PARTICLES = 220
PLAYER_SPEED = 4.0
PLAYER_ACCEL = 0.18
PLAYER_FRICTION = 0.86

ENEMY_BASE_SPEED = 1.6
ENEMY_SPEED_GROWTH = 0.06
ENEMY_SPAWN_BASE = 3
ENEMY_SPAWN_GROWTH = 1

CRYSTALS_TO_LEVEL = 6
SHIELD_DURATION = 4.0
SHIELD_SPAWN_CHANCE = 0.18
HIT_INVULN_TIME = 0.7

Vec = pygame.math.Vector2

@dataclass
class Particle:
    pos: Vec
    vel: Vec
    size: int
    color: Tuple[int,int,int]
    life: float

@dataclass
class Entity:
    rect: pygame.Rect
    vel: Vec
    color: Tuple[int,int,int]

def clamp(value, lo, hi):
    return max(lo, min(hi, value))

def rand_rect_inside(size, margin=24):
    x = random.randint(margin, WIDTH-size-margin)
    y = random.randint(margin, HEIGHT-size-margin)
    return pygame.Rect(x,y,size,size)

def rect_center(rect):
    return Vec(rect.centerx, rect.centery)

def spawn_particles(particles, pos, base_color, count, speed, size_range, life_range):
    for _ in range(count):
        if len(particles)>=MAX_PARTICLES: break
        angle=random.random()*math.tau
        mag=random.uniform(speed*0.35,speed)
        vel=Vec(math.cos(angle), math.sin(angle))*mag
        size=random.randint(size_range[0],size_range[1])
        life=random.uniform(life_range[0],life_range[1])
        c=tuple(clamp(ch+random.randint(-15,15),0,255) for ch in base_color)
        particles.append(Particle(pos.copy(), vel, size, c, life))

def draw_rect_alpha(surface, color, rect, alpha):
    temp=pygame.Surface((rect.width, rect.height), pygame.SRCALPHA)
    temp.fill((*color, alpha))
    surface.blit(temp, rect.topleft)

class SquareDash:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Square Dash")
        self.screen=pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock=pygame.time.Clock()
        self.font=pygame.font.SysFont("consolas", 18)
        self.font_big=pygame.font.SysFont("consolas", 36, bold=True)
        self.reset()

    def reset(self):
        self.running=True
        self.paused=False
        self.game_over=False
        self.level=1
        self.score=0
        self.time_survived=0.0
        self.crystals_collected_level=0
        self.particles=[]
        self.player=Entity(pygame.Rect(WIDTH//2,HEIGHT//2,BASE_SIZE,BASE_SIZE),Vec(0,0),PLAYER_COLOR)
        self.crystal=Entity(rand_rect_inside(CRYSTAL_SIZE),Vec(0,0),CRYSTAL_COLOR)
        self.shield_pickup=None
        self.enemies=[]
        self._spawn_enemies_for_level()
        self.shield_time_left=0.0
        self.hit_invuln_left=0.0

    def _spawn_enemies_for_level(self):
        target=int(ENEMY_SPAWN_BASE+(self.level-1)*ENEMY_SPAWN_GROWTH)
        self.enemies.clear()
        for _ in range(target):
            rect=rand_rect_inside(ENEMY_SIZE)
            while rect.colliderect(self.player.rect.inflate(120,120)):
                rect=rand_rect_inside(ENEMY_SIZE)
            self.enemies.append(Entity(rect,Vec(0,0),ENEMY_COLOR))

    def _enemy_speed(self):
        return ENEMY_BASE_SPEED+(self.level-1)*ENEMY_SPEED_GROWTH

    def run(self):
        while self.running:
            dt=self.clock.tick(FPS)/1000.0
            self._handle_events()
            if not self.paused and not self.game_over:
                self._update(dt)
            self._render()
        pygame.quit()
        sys.exit(0)

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type==pygame.QUIT:self.running=False
            elif event.type==pygame.KEYDOWN:
                if event.key==pygame.K_ESCAPE:self.running=False
                elif event.key==pygame.K_p and not self.game_over:self.paused=not self.paused
                elif event.key==pygame.K_r and self.game_over:self.reset()

    def _read_input(self):
        keys=pygame.key.get_pressed()
        x=y=0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: x-=1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: x+=1
        if keys[pygame.K_UP] or keys[pygame.K_w]: y-=1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]: y+=1
        v=Vec(x,y)
        return v.normalize() if v.length_squared()>0 else v

    def _update(self, dt):
        self.time_survived+=dt
        self.shield_time_left=max(0.0,self.shield_time_left-dt)
        self.hit_invuln_left=max(0.0,self.hit_invuln_left-dt)
        direction=self._read_input()
        self.player.vel+=direction*(PLAYER_SPEED/max(0.001,dt))*(PLAYER_ACCEL*dt)
        self.player.vel*=PLAYER_FRICTION
        self.player.vel.x=clamp(self.player.vel.x,-PLAYER_SPEED,PLAYER_SPEED)
        self.player.vel.y=clamp(self.player.vel.y,-PLAYER_SPEED,PLAYER_SPEED)
        self._move_rect(self.player.rect,self.player.vel)
        ppos=rect_center(self.player.rect)
        espeed=self._enemy_speed()
        for e in self.enemies:
            epos=rect_center(e.rect)
            to_player=ppos-epos
            if to_player.length_squared()>0: to_player=to_player.normalize()
            e.vel=e.vel.lerp(to_player*espeed,0.06)
            self._move_rect(e.rect,e.vel)
        if self.player.rect.colliderect(self.crystal.rect): self._collect_crystal()
        if self.shield_pickup and self.player.rect.colliderect(self.shield_pickup.rect): self._collect_shield()
        if self.hit_invuln_left<=0.0:
            for e in self.enemies:
                if self.player.rect.colliderect(e.rect):
                    self._player_hit()
                    break
        self._update_particles(dt)

    def _move_rect(self, rect, vel):
        rect.x+=int(round(vel.x))
        rect.y+=int(round(vel.y))
        if rect.left<0: rect.left=0; vel.x*=-0.65
        if rect.right>WIDTH: rect.right=WIDTH; vel.x*=-0.65
        if rect.top<0: rect.top=0; vel.y*=-0.65
        if rect.bottom>HEIGHT: rect.bottom=HEIGHT; vel.y*=-0.65

    def _collect_crystal(self):
        self.score+=10+self.level
        self.crystals_collected_level+=1
        spawn_particles(self.particles, rect_center(self.crystal.rect), CRYSTAL_COLOR,26,120.0,(3,7),(0.25,0.55))
        self.crystal.rect=rand_rect_inside(CRYSTAL_SIZE)
        if self.shield_pickup is None and random.random()<SHIELD_SPAWN_CHANCE:
            shield_rect=rand_rect_inside(SHIELD_SIZE)
            tries=0
            while (shield_rect.colliderect(self.player.rect.inflate(80,80)) or shield_rect.colliderect(self.crystal.rect.inflate(40,40))) and tries<30:
                shield_rect=rand_rect_inside(SHIELD_SIZE); tries+=1
            self.shield_pickup=Entity(shield_rect,Vec(0,0),SHIELD_COLOR)
        if self.crystals_collected_level>=CRYSTALS_TO_LEVEL:
            self.level+=1
            self.crystals_collected_level=0
            self.score+=50
            spawn_particles(self.particles, rect_center(self.player.rect), (255,255,255),42,170.0,(3,8),(0.3,0.75))
            self._spawn_enemies_for_level()

    def _collect_shield(self):
        self.shield_time_left=SHIELD_DURATION
        self.shield_pickup=None
        spawn_particles(self.particles, rect_center(self.player.rect), SHIELD_COLOR,34,150.0,(3,7),(0.35,0.7))

    def _player_hit(self):
        if self.shield_time_left>0.0:
            self.shield_time_left=max(0.0,self.shield_time_left-1.2)
            self.hit_invuln_left=HIT_INVULN_TIME
            spawn_particles(self.particles, rect_center(self.player.rect), SHIELD_COLOR,26,190.0,(3,7),(0.2,0.55))
            return
        spawn_particles(self.particles, rect_center(self.player.rect), ENEMY_COLOR,70,240.0,(3,9),(0.35,0.95))
        self.game_over=True

    def _update_particles(self, dt):
        alive=[]
        for p in self.particles:
            p.life-=dt
            if p.life<=0: continue
            p.pos+=p.vel*dt
            p.vel*=0.92
            if p.pos.x<0 or p.pos.x>WIDTH: p.vel.x*=-0.7
            if p.pos.y<0 or p.pos.y>HEIGHT: p.vel.y*=-0.7
            alive.append(p)
        self.particles=alive

    def _render(self):
        self.screen.fill(BG_COLOR)
        self._draw_grid()
        pygame.draw.rect(self.screen, self.crystal.color, self.crystal.rect)
        if self.shield_pickup: pygame.draw.rect(self.screen, self.shield_pickup.color, self.shield_pickup.rect)
        for e in self.enemies: pygame.draw.rect(self.screen,e.color,e.rect)
        player_color=PLAYER_HIT_COLOR if self.hit_invuln_left>0.0 else self.player.color
        pygame.draw.rect(self.screen, player_color, self.player.rect)
        if self.shield_time_left>0:
            aura_size=int(BASE_SIZE+10+6*math.sin(pygame.time.get_ticks()/120.0))
            aura=self.player.rect.copy(); aura.width=aura.height=aura_size; aura.center=self.player.rect.center
            draw_rect_alpha(self.screen, SHIELD_COLOR, aura, 70)
        for p in self.particles: pygame.draw.rect(self.screen,p.color,pygame.Rect(int(p.pos.x),int(p.pos.y),p.size,p.size))
        self._draw_ui()
        if self.paused: self._draw_center_message("PAUZA","Stiskni P pro pokračování")
        if self.game_over: self._draw_center_message("KONEC HRY","Stiskni R pro restart")
        pygame.display.flip()

    def _draw_grid(self):
        step=24
        for x in range(0,WIDTH,step): pygame.draw.line(self.screen, GRID_COLOR, (x,0),(x,HEIGHT),1)
        for y in range(0,HEIGHT,step): pygame.draw.line(self.screen, GRID_COLOR, (0,y),(WIDTH,y),1)

    def _draw_ui(self):
        shield_txt=f"ŠTÍT: {self.shield_time_left:0.1f}s" if self.shield_time_left>0 else "ŠTÍT: -"
        lines=[f"Skóre: {self.score}",f"Level: {self.level}",f"Čas: {self.time_survived:0.1f}s",shield_txt,"P: pauza | R: restart (po smrti) | ESC: konec"]
        y=10
        for i,line in enumerate(lines):
            surf=self.font.render(line,True,TEXT_COLOR)
            self.screen.blit(surf,(10,y))
            y+=20 if i<3 else 18
        bar_x, bar_y = 10, HEIGHT-24; bar_w, bar_h = 220,12
        pygame.draw.rect(self.screen,(30,36,48),(bar_x,bar_y,bar_w,bar_h))
        fill_w=int(bar_w*self.crystals_collected_level/CRYSTALS_TO_LEVEL)
        pygame.draw.rect(self.screen,CRYSTAL_COLOR,(bar_x,bar_y,fill_w,bar_h))
        label=self.font.render("Postup:",True,TEXT_COLOR)
        self.screen.blit(label,(bar_x,bar_y-18))

    def _draw_center_message(self, title, subtitle):
        overlay=pygame.Surface((WIDTH,HEIGHT), pygame.SRCALPHA)
        overlay.fill((0,0,0,140))
        self.screen.blit(overlay,(0,0))
        title_s=self.font_big.render(title,True,TEXT_COLOR)
        sub_s=self.font.render(subtitle,True,TEXT_COLOR)
        self.screen.blit(title_s,title_s.get_rect(center=(WIDTH//2,HEIGHT//2-20)))
        self.screen.blit(sub_s,sub_s.get_rect(center=(WIDTH//2,HEIGHT//2+20)))

def main():
    game=SquareDash()
    game.run()

if __name__=="__main__":
    main()
