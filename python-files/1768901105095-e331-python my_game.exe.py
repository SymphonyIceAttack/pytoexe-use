import pygame
import math
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
GROUND_Y = 450
GRAVITY = 0.8
JUMP_VELOCITY = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 2
BOSS_SPEED = 1
ATTACK_DURATION = 200  # ms
ENEMY_DAMAGE = 5
BOSS_DAMAGE = 10
WORLD_WIDTH = 5000  # Very long level
FPS = 60
SHAKE_INTENSITY = 8
DASH_SPEED = 15
DASH_DURATION = 150  # ms
DASH_COOLDOWN = 500  # ms

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE_SKY = (135, 206, 235)
LIGHT_BLUE = (173, 216, 230)
GREEN_GRASS = (34, 139, 34)
DARK_GREEN = (0, 100, 0)
BROWN = (139, 69, 19)
RED = (255, 0, 0)
PLAYER_BLUE = (0, 120, 255)
ENEMY_RED = (200, 50, 50)
BOSS_PURPLE = (150, 0, 150)
YELLOW = (255, 255, 0)
GRAY = (128, 128, 128)
BROWN_DUST = (139, 69, 19)

# Game states
STATE_MENU = 'menu'
STATE_PLAYING = 'playing'
STATE_PAUSE = 'pause'
STATE_VICTORY = 'victory'
STATE_GAMEOVER = 'gameover'

# Lerp function
def lerp(a, b, t):
    return a + (b - a) * t

# Particle class
class Particle:
    def __init__(self, x, y, vx, vy, life, color, size):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color
        self.size = size

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def emit(self, x, y, count, color, vx_range, vy_range, life_range):
        for _ in range(count):
            vx = random.uniform(*vx_range)
            vy = random.uniform(*vy_range)
            life = random.uniform(*life_range)
            size = random.randint(2, 6)
            self.particles.append(Particle(x, y, vx, vy, life, color, size))
        if len(self.particles) > 500:  # Perf limit
            self.particles = self.particles[-500:]

    def update(self, dt):
        for particle in self.particles[:]:
            particle.x += particle.vx * dt / (1000 / FPS)
            particle.vy += GRAVITY * dt / (1000 / FPS)
            particle.y += particle.vy * dt / (1000 / FPS)
            particle.life -= dt / (1000 / FPS)
            if particle.life <= 0:
                self.particles.remove(particle)

    def draw(self, surface, camera_x, shake_x):
        for particle in self.particles:
            alpha_factor = particle.life / particle.max_life
            size = int(particle.size * alpha_factor)
            if size > 0:
                pygame.draw.circle(surface, particle.color, 
                                   (int(particle.x + camera_x + shake_x), int(particle.y)), size)

# Screen and clock
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Jeu de Combat 01 - Animations Fluides')
clock = pygame.time.Clock()
font = pygame.font.SysFont('Arial', 24, bold=True)
big_font = pygame.font.SysFont('Arial', 48, bold=True)

class Entity:
    def __init__(self, x, y, w, h):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.health = 100
        self.max_health = 100
        self.bar_fill = 1.0
        self.bar_fill_target = 1.0

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)

    def update_bar(self, dt):
        self.bar_fill = lerp(self.bar_fill, self.bar_fill_target, 0.15)

    def draw_health_bar(self, surface, screen_x, y_offset= -20):
        bar_w = 100
        bar_h = 10
        fill_w = int(bar_w * self.bar_fill)
        # Background
        pygame.draw.rect(surface, RED, (screen_x - 50, self.y + y_offset, bar_w, bar_h), border_radius=5)
        # Fill
        pygame.draw.rect(surface, GREEN, (screen_x - 50, self.y + y_offset, fill_w, bar_h), border_radius=5)

class Player(Entity):
    def __init__(self):
        super().__init__(100, GROUND_Y - 60, 50, 60)
        self.vy = 0
        self.on_ground = True
        self.state = 'idle'
        self.facing_right = True
        self.attack_timer = 0
        self.attack_frame = 0
        self.hurt_timer = 0
        self.has_key = False
        self.health = 100
        self.max_health = 100
        self.score = 0
        self.bob_time = 0
        self.dash_timer = 0
        self.dash_cooldown = 0
        self.dash_dir = 0
        self.combo_count = 0
        self.combo_timer = 0

    def update(self, keys, camera_x, dt, particles, shake_timer, enemies, boss, key_item, door):
        if self.state in ['ko', 'victory']:
            return camera_x

        # Combo timer
        if self.combo_timer > 0:
            self.combo_timer -= dt / (1000 / FPS)
        if self.combo_timer <= 0:
            self.combo_count = 0

        # Dash
        if self.dash_cooldown > 0:
            self.dash_cooldown -= dt / (1000 / FPS)
        if keys[pygame.K_LSHIFT] and self.dash_cooldown <= 0 and self.dash_timer <= 0:
            self.dash_timer = DASH_DURATION / (1000 / FPS)
            self.dash_dir = 1 if self.facing_right else -1
            self.dash_cooldown = DASH_COOLDOWN / (1000 / FPS)
            particles.emit(self.x + 25, self.y + 40, 20, LIGHT_BLUE, (-5 * self.dash_dir, 5 * self.dash_dir), (-3, 3), (10, 20))

        dx = 0
        if self.dash_timer > 0:
            dx = DASH_SPEED * self.dash_dir
            self.dash_timer -= dt / (1000 / FPS)
            self.state = 'dash'
        else:
            if keys[pygame.K_LEFT]:
                dx = -PLAYER_SPEED
                self.facing_right = False
                self.state = 'run'
                if self.on_ground:
                    particles.emit(self.x + 5, self.y + 60, 2, BROWN_DUST, (-1, 1), (0, 2), (15, 25))
            if keys[pygame.K_RIGHT]:
                dx = PLAYER_SPEED
                self.facing_right = True
                self.state = 'run'
                if self.on_ground:
                    particles.emit(self.x + 45, self.y + 60, 2, BROWN_DUST, (-1, 1), (0, 2), (15, 25))
            if dx == 0 and self.state not in ['attack', 'hurt', 'action', 'ko', 'victory', 'dash']:
                self.state = 'idle'

        camera_x -= dx * dt / (1000 / FPS)

        # Jump
        if keys[pygame.K_SPACE] and self.on_ground:
            self.vy = JUMP_VELOCITY
            self.on_ground = False

        # Gravity
        self.vy += GRAVITY * dt / (1000 / FPS)
        self.y += self.vy * dt / (1000 / FPS)
        if self.y >= GROUND_Y - 60:
            self.y = GROUND_Y - 60
            self.vy = 0
            self.on_ground = True

        # Attack with combo multiplier
        if keys[pygame.K_x] and self.attack_timer == 0:
            self.state = 'attack'
            self.attack_timer = pygame.time.get_ticks()
            self.combo_count = min(self.combo_count + 1, 3)
            self.combo_timer = 40  # Reset timer for next combo

        if self.state == 'attack':
            current_time = pygame.time.get_ticks()
            elapsed = current_time - self.attack_timer
            if elapsed < 100:
                self.attack_frame = 1
            elif elapsed < 200:
                self.attack_frame = 2
                # Emit sparks
                spark_x = self.x + (70 if self.facing_right else -20)
                dir_vx = (8, 15) if self.facing_right else (-15, -8)
                particles.emit(spark_x, self.y + 25, 12, YELLOW, dir_vx, (-6, 3), (20, 40))
                # Damage with combo
                damage = 20 * (1 + 0.5 * (self.combo_count - 1))
                attack_rect = pygame.Rect(
                    self.x + (45 if self.facing_right else -25),
                    self.y + 15,
                    30,
                    20
                )
                for enemy in enemies:
                    if attack_rect.colliderect(enemy.get_rect()) and enemy.health > 0:
                        enemy.health -= damage
                        enemy.hurt_timer = 20
                        enemy.bar_fill_target = max(0, enemy.health / enemy.max_health)
                        if enemy.health <= 0:
                            particles.emit(enemy.x + 25, enemy.y + 30, 25, GRAY, (-10, 10), (-15, -5), (30, 50))
                            self.score += 50
                if boss and attack_rect.colliderect(boss.get_rect()) and boss.health > 0:
                    boss.health -= damage
                    boss.hurt_timer = 30
                    boss.bar_fill_target = max(0, boss.health / boss.max_health)
                    if boss.health <= 0:
                        particles.emit(boss.x + 50, boss.y + 50, 50, GRAY, (-15, 15), (-20, -5), (40, 60))
                        self.score += 500
                        shake_timer[0] = 30
            else:
                self.attack_timer = 0
                self.state = 'idle'

        # Hurt
        if self.hurt_timer > 0:
            self.state = 'hurt'
            self.hurt_timer -= dt / (1000 / FPS)
            particles.emit(self.x + 25, self.y + 30, 10, RED, (-8, 8), (-10, -2), (20, 35))
        elif self.state == 'hurt':
            self.state = 'idle'

        # Key pickup
        if not self.has_key and self.get_rect().colliderect(key_item.get_rect()):
            self.has_key = True
            self.state = 'action'
            key_item.collected = True
            particles.emit(key_item.x + 15, key_item.y + 15, 15, YELLOW, (-5, 5), (-8, -2), (25, 40))

        # Door
        if self.has_key and self.get_rect().colliderect(door.get_rect()):
            self.state = 'victory'
            particles.emit(door.x + 25, door.y + 25, 50, GREEN, (-10, 10), (-15, -5), (40, 60))

        if self.health <= 0:
            self.state = 'ko'
            particles.emit(self.x + 25, self.y + 30, 30, RED, (-12, 12), (-18, -5), (35, 55))

        self.update_bar(dt)

        # Clamp camera
        target_camera = -self.x + SCREEN_WIDTH / 3
        camera_x = lerp(camera_x, target_camera, 0.12 * dt / (1000 / FPS))
        camera_x = max(min(camera_x, 0), -WORLD_WIDTH + SCREEN_WIDTH)

        return camera_x

    def draw(self, surface, camera_x, shake_x, show_hitbox):
        screen_x = self.x + camera_x + shake_x
        bob = math.sin(self.bob_time * 0.015) * 2 if self.on_ground else 0

        # Afterimage for attack
        if self.state == 'attack' and self.attack_frame == 2:
            afterimage = pygame.Surface((self.w, self.h), pygame.SRCALPHA)
            afterimage.fill((255, 255, 0, 100))  # Semi-transparent yellow
            surface.blit(afterimage, (screen_x, self.y + bob))

        # Body
        body_y = self.y + bob
        pygame.draw.ellipse(surface, PLAYER_BLUE, (screen_x + 5, body_y + 10, 40, 35))

        # Head
        pygame.draw.circle(surface, (220, 220, 255), (int(screen_x + 25), int(body_y)), 18)

        # Eyes
        eye_offset = 3 if self.state == 'hurt' else 0
        pygame.draw.circle(surface, BLACK, (int(screen_x + 18 + eye_offset), int(body_y - 2)), 3)
        pygame.draw.circle(surface, BLACK, (int(screen_x + 32 - eye_offset), int(body_y - 2)), 3)

        # Arms
        pygame.draw.line(surface, PLAYER_BLUE, (screen_x + 8, body_y + 18), (screen_x, body_y + 32), 5)
        pygame.draw.line(surface, PLAYER_BLUE, (screen_x + 42, body_y + 18), (screen_x + 50, body_y + 32), 5)

        # Sword on attack
        if self.state == 'attack' and self.attack_frame == 2:
            sword_start = (screen_x + 42, body_y + 22) if self.facing_right else (screen_x + 8, body_y + 22)
            sword_end_x = screen_x + 70 if self.facing_right else screen_x - 20
            sword_end = (sword_end_x, body_y + 22 + (random.random() - 0.5) * 4)
            pygame.draw.line(surface, YELLOW, sword_start, sword_end, 4)
            pygame.draw.line(surface, (255, 200, 0), sword_start, sword_end, 2)

        # Legs run cycle
        leg_time = pygame.time.get_ticks() * 0.02
        leg1_offset = math.sin(leg_time) * 8 if self.state == 'run' else 0
        leg2_offset = math.sin(leg_time + math.pi) * 8 if self.state == 'run' else 0
        pygame.draw.line(surface, (0, 60, 150), (screen_x + 12, body_y + 45), (screen_x + 8, body_y + 60 + leg1_offset), 6)
        pygame.draw.line(surface, (0, 60, 150), (screen_x + 38, body_y + 45), (screen_x + 42, body_y + 60 + leg2_offset), 6)

        self.draw_health_bar(surface, screen_x + 25)

        # Debug hitbox
        if show_hitbox:
            pygame.draw.rect(surface, YELLOW, (screen_x, body_y, 50, 60), 2)

# (Le reste du code pour Enemy, Boss, KeyItem, Door, background, loop, etc. reste identique à ta version précédente. Ajoute juste les nouvelles variables comme self.dash_timer dans l'update du player, et adapte les appels.)

# Exemple pour ajouter le debug hitbox dans le loop :
show_hitbox = False
# Dans playing:
if keys[pygame.K_h]:
    show_hitbox = not show_hitbox
# Lors du draw du player: player.draw(screen, camera_x, shake_x, show_hitbox)

# Fade for menus (example for victory/gameover)
fade_alpha = 0
# In loop for victory/gameover:
fade_alpha = min(fade_alpha + dt / (1000 / FPS) * 255 / 1, 255)  # Fade in over 1s
overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
overlay.fill(BLACK)
overlay.set_alpha(fade_alpha)
screen.blit(overlay, (0, 0))