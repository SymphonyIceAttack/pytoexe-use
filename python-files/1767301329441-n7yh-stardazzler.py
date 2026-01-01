import pygame
import math
import random
import sys

# ========== INITIALIZATION ==========
pygame.init()
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🌟 STAR DAZZLER - The Cosmic Journey")

# Colors
COLORS = {
    'bg': (5, 10, 25),
    'player': (0, 200, 255),
    'trail': (50, 100, 180),
    'enemy_red': (255, 80, 100),
    'enemy_blue': (100, 180, 255),
    'enemy_green': (80, 255, 150),
    'enemy_boss': (200, 100, 255),
    'bullet': (0, 255, 255),
    'planet': (100, 180, 255),
    'planet_ring': (150, 200, 255),

    'ui_gold': (255, 215, 0),
    'ui_green': (0, 255, 150),
    'ui_red': (255, 80, 80),
    'text': (240, 240, 255)
}

FPS = 60
clock = pygame.time.Clock()

# ========== PARTICLE SYSTEM ==========
class ParticleSystem:
    @staticmethod
    def create_explosion(x, y, color, count=15):
        particles = []
        for _ in range(count):
            particles.append({
                'x': x, 'y': y,
                'vx': random.uniform(-3, 3),
                'vy': random.uniform(-3, 3),
                'color': color,
                'size': random.uniform(2, 5),
                'life': random.uniform(20, 35)
            })
        return particles

    @staticmethod
    def update_particles(particles):
        to_remove = []
        for p in particles:
            p['x'] += p['vx']
            p['y'] += p['vy']
            p['life'] -= 1

            if p['life'] <= 0:
                to_remove.append(p)

        for p in to_remove:
            particles.remove(p)

    @staticmethod
    def draw_particles(surface, particles):
        for p in particles:
            color = p['color']
            alpha = int((p['life'] / 35) * 255)
            if len(color) == 4:
                color = (color[0], color[1], color[2], alpha)
            else:
                color = (*color, alpha)

            temp_surface = pygame.Surface((int(p['size']*2), int(p['size']*2)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surface, color, (int(p['size']), int(p['size'])), int(p['size']))
            surface.blit(temp_surface, (int(p['x'] - p['size']), int(p['y'] - p['size'])))

# ========== PLAYER ==========
class Player:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT - 100  # ثابت في أسفل الشاشة
        self.radius = 25
        self.speed = 5
        self.angle = 0


        self.health = 100
        self.max_health = 100
        self.score = 0
        self.level = 1
        self.upgrades = {'damage': 0, 'speed': 0}

        self.shoot_cooldown = 0
        self.shoot_delay = 15
        self.particles = []
        self.bullets_per_shot = 3  # إضافة: عدد الرصاصات في كل مرة
        self.bullet_spread = 0.15  # إضافة: انتشار الرصاصات

    def update(self, keys, mouse_pos):
        # حركة أفقية فقط
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.x -= self.speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.x += self.speed

        # الحدود
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x))

        # التصويب
        self.angle = math.atan2(mouse_pos[1] - self.y, mouse_pos[0] - self.x)

        # تحديث الجسيمات
        ParticleSystem.update_particles(self.particles)

        # تبريد الطلقة
        if self.shoot_cooldown > 0:

            self.shoot_cooldown -= 1

    def shoot(self):
        bullets = []
        if self.shoot_cooldown <= 0:
            self.shoot_cooldown = max(8, self.shoot_delay - self.upgrades['speed'])

            # إطلاق عدة رصاصات مع انتشار
            if self.bullets_per_shot % 2 == 1:  # عدد فردي (رصاصة مركزية + انتشار)
                # الرصاصة المركزية
                bullets.append({
                    'x': self.x + math.cos(self.angle) * (self.radius + 10),
                    'y': self.y + math.sin(self.angle) * (self.radius + 10),
                    'angle': self.angle,
                    'speed': 12 + self.upgrades['damage'],
                    'damage': 10 + self.upgrades['damage'] * 2
                })

                # الرصاصات الجانبية
                for i in range(1, (self.bullets_per_shot // 2) + 1):
                    spread = self.bullet_spread * i
                    # رصاصة يسار
                    bullets.append({
                        'x': self.x + math.cos(self.angle - spread) * (self.radius + 10),
                        'y': self.y + math.sin(self.angle - spread) * (self.radius + 10),
                        'angle': self.angle - spread,
                        'speed': 12 + self.upgrades['damage'],
                        'damage': 8 + self.upgrades['damage'] * 2  # ضرر أقل 

 
                    })
                    # رصاصة يمين
                    bullets.append({
                        'x': self.x + math.cos(self.angle + spread) * (self.radius + 10),
                        'y': self.y + math.sin(self.angle + spread) * (self.radius + 10),
                        'angle': self.angle + spread,
                        'speed': 12 + self.upgrades['damage'],
                        'damage': 8 + self.upgrades['damage'] * 2
                    })
            else:  # عدد زوجي (رصاصات متناظرة)
                half_count = self.bullets_per_shot // 2
                for i in range(half_count):
                    spread = self.bullet_spread * (i + 0.5)
                    # رصاصة يسار
                    bullets.append({
                        'x': self.x + math.cos(self.angle - spread) * (self.radius + 10),
                        'y': self.y + math.sin(self.angle - spread) * (self.radius + 10),
                        'angle': self.angle - spread,
                        'speed': 12 + self.upgrades['damage'],
                        'damage': 8 + self.upgrades['damage'] * 2
                    })
                    # رصاصة يمين
                    bullets.append({
                        'x': self.x + math.cos(self.angle + spread) * (self.radius + 10),
                        'y': self.y + math.sin(self.angle + spread) * (self.radius + 10),

                        'angle': self.angle + spread,
                        'speed': 12 + self.upgrades['damage'],
                        'damage': 8 + self.upgrades['damage'] * 2
                    })
        return bullets

    def take_damage(self, amount):
        self.health = max(0, self.health - amount)
        self.particles.extend(ParticleSystem.create_explosion(
            self.x, self.y, (255, 50, 50)))

    def level_up(self):
        self.level += 1
        self.max_health += 10
        self.health = min(self.max_health, self.health + 15)
        self.score += 100

        # ترقية عدد الرصاصات كل 3 مستويات
        if self.level % 3 == 0 and self.bullets_per_shot < 7:
            self.bullets_per_shot += 1
            self.bullet_spread = max(0.05, self.bullet_spread - 0.01)

    def draw(self, surface):
        # جسيمات المحرك
        ParticleSystem.draw_particles(surface, self.particles)

        # جسم السفينة (مثلث)
        points = [
            (self.x + math.cos(self.angle) * self.radius * 1.2,
             self.y + math.sin(self.angle) * self.radius * 1.2),
            (self.x + math.cos(self.angle + 2.4) * self.radius,
             self.y + math.sin(self.angle + 2.4) * self.radius),

            (self.x + math.cos(self.angle - 2.4) * self.radius,
             self.y + math.sin(self.angle - 2.4) * self.radius)
        ]
        pygame.draw.polygon(surface, COLORS['player'], points)

        # محركات خلفية
        for offset in [1.8, -1.8]:
            engine_x = self.x - math.cos(self.angle) * self.radius * 0.7
            engine_y = self.y - math.sin(self.angle) * self.radius * 0.7
            engine_x += math.cos(self.angle + offset) * self.radius * 0.4
            engine_y += math.sin(self.angle + offset) * self.radius * 0.4
            pygame.draw.circle(surface, (255, 150, 50), 
                             (int(engine_x), int(engine_y)), 5)

# ========== ENEMIES ==========
class Enemy:
    TYPES = ['scout', 'fighter', 'cruiser', 'boss']

    def __init__(self, x, y, enemy_type='scout', level=1):
        self.x = x
        self.y = y
        self.type = enemy_type

        if enemy_type == 'scout':
            self.radius = 18
            self.speed = 1.2 + level * 0.1
            self.health = 25 + level * 2
            self.color = COLORS['enemy_red']
            self.points = 50
        elif enemy_type == 'fighter':
            self.radius = 22
            self.speed = 1.0 + level * 0.08

            self.health = 40 + level * 3
            self.color = COLORS['enemy_blue']
            self.points = 80
        elif enemy_type == 'cruiser':
            self.radius = 28
            self.speed = 0.5 + level * 0.02
            self.health = 80 + level * 5
            self.color = COLORS['enemy_green']
            self.points = 150
        else:  # boss
            self.radius = 35
            self.speed = 0.5 + level * 0.02
            self.health = 150 + level * 7
            self.color = COLORS['enemy_boss']
            self.points = 300

        self.angle = math.pi / 2  # دائماً للأسفل

    def update(self, trail_speed=0):
        # يتحرك للأسفل + سرعة المسار
        self.y += self.speed + trail_speed

        # اهتزاز بسيط
        self.x += math.sin(pygame.time.get_ticks() * 0.002 + self.y * 0.02) * 0.3

    def take_damage(self, amount):
        self.health -= amount
        return ParticleSystem.create_explosion(self.x, self.y, self.color)

    def draw(self, surface):
        if self.type == 'boss':

            pygame.draw.circle(surface, self.color, 
                             (int(self.x), int(self.y)), self.radius)
            pygame.draw.circle(surface, (255, 255, 200), 
                             (int(self.x), int(self.y)), self.radius // 2)
        else:
            pygame.draw.circle(surface, self.color, 
                             (int(self.x), int(self.y)), self.radius)

            if self.type == 'fighter':
                pygame.draw.circle(surface, (255, 255, 200), 
                                 (int(self.x), int(self.y)), self.radius // 3)

# ========== BULLET ==========
class Bullet:
    def __init__(self, x, y, angle, speed, damage):
        self.x = x
        self.y = y
        self.angle = angle
        self.speed = speed
        self.damage = damage

    def update(self):
        self.x += math.cos(self.angle) * self.speed
        self.y += math.sin(self.angle) * self.speed
        return (self.x < -50 or self.x > SCREEN_WIDTH + 50 or 
                self.y < -50 or self.y > SCREEN_HEIGHT + 50)

    def draw(self, surface):
        pygame.draw.circle(surface, COLORS['bullet'], 
                         (int(self.x), int(self.y)), 6)
        pygame.draw.circle(surface, (255, 255, 255), 
                         (int(self.x), int(self.y)), 3)


# ========== ENEMY FORMATIONS ==========
class EnemyFormation:
    FORMATIONS = [
        {'name': 'triangle', 'count': 3, 'types': ['scout'] * 3},
        {'name': 'square', 'count': 4, 'types': ['scout'] * 3 + ['fighter']},
        {'name': 'pentagon', 'count': 5, 'types': ['scout'] * 2 + ['fighter'] * 2 + ['cruiser']},
        {'name': 'hexagon', 'count': 6, 'types': ['fighter'] * 3 + ['cruiser'] * 2 + ['boss']},
        {'name': 'final', 'count': 7, 'types': ['cruiser'] * 3 + ['boss'] * 4}
    ]

    def __init__(self, formation_index):
        self.formation = self.FORMATIONS[formation_index % 5]
        self.enemies = []
        self.create_formation(formation_index)

    def create_formation(self, level):
        center_x = SCREEN_WIDTH // 2
        start_y = -100

        if self.formation['name'] == 'triangle':
            positions = [
                (center_x, start_y),
                (center_x - 60, start_y + 80),
                (center_x + 60, start_y + 80)
            ]
        elif self.formation['name'] == 'square':
            positions = [
                (center_x - 50, start_y),
                (center_x + 50, start_y),

                (center_x - 50, start_y + 60),
                (center_x + 50, start_y + 60)
            ]
        elif self.formation['name'] == 'pentagon':
            positions = []
            for i in range(5):
                angle = (2 * math.pi * i / 5) - math.pi/2
                positions.append((
                    center_x + math.cos(angle) * 70,
                    start_y + math.sin(angle) * 70 + 70
                ))
        elif self.formation['name'] == 'hexagon':
            positions = []
            for i in range(6):
                angle = (2 * math.pi * i / 6)
                positions.append((
                    center_x + math.cos(angle) * 90,
                    start_y + math.sin(angle) * 90 + 90
                ))
        else:  # final
            positions = [(center_x, start_y + 100)]  # الزعيم
            for i in range(6):
                angle = (2 * math.pi * i / 6)
                positions.append((
                    center_x + math.cos(angle) * 110,
                    start_y + math.sin(angle) * 110 + 100
                ))

        # إنشاء الأعداء
        for i, (x, y) in enumerate(positions):
            if i < len(self.formation['types']):
                enemy_type = self.formation['types'][i]

                enemy = Enemy(x, y, enemy_type, level + 1)
                self.enemies.append(enemy)

    def update(self, trail_speed=0):
        for enemy in self.enemies[:]:
            enemy.update(trail_speed)
            if enemy.y > SCREEN_HEIGHT + 100:  # إذا خرج من الأسفل
                self.enemies.remove(enemy)

    def draw(self, surface):
        for enemy in self.enemies:
            enemy.draw(surface)

    def is_defeated(self):
        return len(self.enemies) == 0

# ========== SPACE TRAIL ==========
class SpaceTrail:
    def __init__(self):
        self.current_formation = 0
        self.total_formations = 5
        self.formations = []
        self.progress = 0
        self.planet_reached = False
        self.trail_speed = 1.0  # سرعة تحرك المسار للأسفل

        # إنشاء المجموعات
        for i in range(self.total_formations):
            self.formations.append(EnemyFormation(i))

        # كوكب النهاية - يبدأ بعيداً جداً في الأعلى
        self.planet = {

            'x': SCREEN_WIDTH // 2,
            'y': -5000,  # بعيد جداً في الأعلى
            'radius': 100,
            'start_y': -5000,
            'target_y': SCREEN_HEIGHT // 2  # يصل إلى منتصف الشاشة
        }

    def update(self):
        # تحديث المجموعة الحالية
        if self.current_formation < self.total_formations:
            self.formations[self.current_formation].update(self.trail_speed)

            # الانتقال للمجموعة التالية
            if self.formations[self.current_formation].is_defeated():
                self.current_formation += 1
                # زيادة صعوبة بعد كل مجموعة
                self.trail_speed += 0.2

        # حساب التقدم: المسافة التي قطعها الكوكب
        total_distance = abs(self.planet['target_y'] - self.planet['start_y'])
        current_distance = abs(self.planet['y'] - self.planet['start_y'])
        self.progress = min(100, (current_distance / total_distance) * 100)

        # تحريك الكوكب للأسفل
        self.planet['y'] += self.trail_speed

        # الوصول للكوكب - عندما يكون قريباً من اللاعب
        planet_center_y = self.planet['y'] + self.planet['radius']
        player_y = SCREEN_HEIGHT - 100  # موقع اللاعب


        # إذا اقترب الكوكب من اللاعب (مع هامش 200 بكسل)
        if planet_center_y > player_y - 200 and not self.planet_reached:
            self.planet_reached = True

    def draw(self, surface):
        # رسم المسار
        trail_width = 80

        # مسار متحرك للأسفل
        for i in range(20):
            alpha = 50 - i * 2
            y_pos = i * 40

            temp_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.line(temp_surface, (*COLORS['trail'], alpha),
                           (SCREEN_WIDTH//2 - trail_width//2, y_pos),
                           (SCREEN_WIDTH//2 + trail_width//2, y_pos), 3)
            surface.blit(temp_surface, (0, 0))

        # رسم المجموعات
        if self.current_formation < self.total_formations:
            self.formations[self.current_formation].draw(surface)

        # رسم الكوكب (فقط عندما يكون مرئياً)
        planet_y = self.planet['y']

        # إذا كان الكوكب في نطاق الرؤية
        if planet_y < SCREEN_HEIGHT + 300 and planet_y > -300:
            # إنشاء سطح شفاف للحلقات
            rings_surface = pygame.Surface((SCREEN_WIDTH, 

SCREEN_HEIGHT), pygame.SRCALPHA)

            # حلقات الكوكب
            pygame.draw.circle(rings_surface, (*COLORS['planet_ring'], 150),
                             (self.planet['x'], int(planet_y)), 140, 8)
            pygame.draw.circle(rings_surface, (*COLORS['planet_ring'], 100),
                             (self.planet['x'], int(planet_y)), 170, 6)
            pygame.draw.circle(rings_surface, (*COLORS['planet_ring'], 80),
                             (self.planet['x'], int(planet_y)), 200, 4)

            surface.blit(rings_surface, (0, 0))

            # الكوكب
            pygame.draw.circle(surface, COLORS['planet'], 
                             (self.planet['x'], int(planet_y)), 
                             self.planet['radius'])

            # تفاصيل الكوكب
            for i in range(3):
                angle = pygame.time.get_ticks() * 0.0005 + i * 2.1
                cloud_x = self.planet['x'] + math.cos(angle) * (self.planet['radius'] * 0.6)
                cloud_y = planet_y + math.sin(angle) * (self.planet['radius'] * 0.3)
                pygame.draw.circle(surface, (150, 200, 255),
                                 (int(cloud_x), int(cloud_y)), 
                                 self.planet['radius'] // 4)

# ========== UI MANAGER ==========

class UIManager:
    def __init__(self):
        self.font_large = pygame.font.SysFont('arial', 48, bold=True)
        self.font_medium = pygame.font.SysFont('arial', 32)
        self.font_small = pygame.font.SysFont('arial', 24)

        self.menu_buttons = [
            {'text': '🚀 Start Journey', 'y': 300, 'action': 'start'},
            {'text': '⚙  Settings', 'y': 370, 'action': 'settings'},
            {'text': '✖  Exit', 'y': 440, 'action': 'exit'}
        ]
        self.selected = 0

    def draw_menu(self, surface):
        surface.fill(COLORS['bg'])

        # النجوم 
        for _ in range(15):  
            x = random.randint(0, SCREEN_WIDTH)
            y = random.randint(0, SCREEN_HEIGHT)
            size =  2
            pygame.draw.circle(surface, (200, 200, 200), (x, y), size)

        # العنوان
        title = self.font_large.render("STAR DAZZLER", True, COLORS['ui_gold'])
        subtitle = self.font_medium.render("The Cosmic Journey to Uranus", True, COLORS['text'])
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))
        surface.blit(subtitle, (SCREEN_WIDTH//2 - subtitle.get_width()//2, 210))


        # الأزرار
        for i, btn in enumerate(self.menu_buttons):
            color = COLORS['player'] if i == self.selected else (60, 80, 120)
            rect = pygame.Rect(SCREEN_WIDTH//2 - 150, btn['y'], 300, 50)

            pygame.draw.rect(surface, color, rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['ui_gold'], rect, 3, border_radius=10)

            text = self.font_medium.render(btn['text'], True, COLORS['text'])
            surface.blit(text, (rect.centerx - text.get_width()//2, 
                              rect.centery - text.get_height()//2))

    def draw_game_ui(self, surface, player, trail):
        # شريط الصحة
        pygame.draw.rect(surface, (40, 40, 60), (20, 20, 200, 25))
        health_width = int((player.health / player.max_health) * 200)
        health_color = COLORS['ui_green'] if player.health > 50 else COLORS['ui_gold'] if player.health > 20 else COLORS['ui_red']
        pygame.draw.rect(surface, health_color, (20, 20, health_width, 25))

        health_text = self.font_small.render(f"Health: {int(player.health)}", True, COLORS['text'])
        surface.blit(health_text, (230, 20))

        # المعلومات - إضافة: عرض عدد الرصاصات
        info_y = 60

        texts = [
            f"Score: {player.score}",
            f"Formation: {min(trail.current_formation + 1, trail.total_formations)}/{trail.total_formations}",
            f"Progress: {int(trail.progress)}%",
            f"Speed: {trail.trail_speed:.1f}",
            f"Bullets: {player.bullets_per_shot}" 
        ]

        for i, text in enumerate(texts):
            text_surf = self.font_small.render(text, True, COLORS['text'])
            surface.blit(text_surf, (20, info_y + i * 30))

        # شريط التقدم
        progress_bg = pygame.Rect(SCREEN_WIDTH - 220, 20, 200, 20)
        pygame.draw.rect(surface, (40, 40, 60), progress_bg)
        progress_fill = pygame.Rect(SCREEN_WIDTH - 220, 20, int(200 * (trail.progress / 100)), 20)
        pygame.draw.rect(surface, COLORS['ui_gold'], progress_fill)

        progress_text = self.font_small.render("Journey to Uranus", True, COLORS['text'])
        surface.blit(progress_text, (SCREEN_WIDTH - 220, 45))

    def draw_game_over(self, surface, player, trail):
        # رسم خلفية شفافة
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 0, 0))
        surface.blit(overlay, (0, 0))


        title = self.font_large.render("Journey Ended", True, COLORS['ui_red'])
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))

        stats = [
            f"Final Score: {player.score}",
            f"Formations Completed: {trail.current_formation}/{trail.total_formations}",
            f"Progress: {int(trail.progress)}%",
            f"Player Level: {player.level}",
            f"Max Bullets: {player.bullets_per_shot}"  
        ]

        for i, stat in enumerate(stats):
            text = self.font_medium.render(stat, True, COLORS['text'])
            surface.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 250 + i * 45))

        # الأزرار
        buttons = [
            {'text': '🔄 Try Again', 'y': 520, 'action': 'retry'},
            {'text': '📋 Main Menu', 'y': 590, 'action': 'menu'}
        ]

        for btn in buttons:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 180, btn['y'], 360, 50)
            pygame.draw.rect(surface, COLORS['player'], rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['ui_gold'], rect, 3, 

border_radius=10)

            text = self.font_medium.render(btn['text'], True, COLORS['text'])
            surface.blit(text, (rect.centerx - text.get_width()//2,
                              rect.centery - text.get_height()//2))

    def draw_victory(self, surface, player):
        # رسم خلفية شفافة
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(200)
        overlay.fill((0, 20, 10))
        surface.blit(overlay, (0, 0))

        title = self.font_large.render("Reached Uranus!", True, COLORS['ui_green'])
        surface.blit(title, (SCREEN_WIDTH//2 - title.get_width()//2, 150))

        message = self.font_medium.render("Congratulations! You completed the cosmic journey", True, COLORS['text'])
        surface.blit(message, (SCREEN_WIDTH//2 - message.get_width()//2, 220))

        stats = [
            f"Final Score: {player.score}",
            f"Final Level: {player.level}",
            f"Performance: {'★★★★★' if player.health > 50 else '★★★★☆'}",
            f"Max Bullets: {player.bullets_per_shot}"  
        ]


        for i, stat in enumerate(stats):
            text = self.font_medium.render(stat, True, COLORS['text'])
            surface.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, 300 + i * 50))

        # الأزرار
        buttons = [
            {'text': '🚀 New Journey', 'y': 520, 'action': 'retry'},
            {'text': '📋 Main Menu', 'y': 590, 'action': 'menu'}
        ]

        for btn in buttons:
            rect = pygame.Rect(SCREEN_WIDTH//2 - 180, btn['y'], 360, 50)
            pygame.draw.rect(surface, COLORS['ui_green'], rect, border_radius=10)
            pygame.draw.rect(surface, COLORS['ui_gold'], rect, 3, border_radius=10)

            text = self.font_medium.render(btn['text'], True, (0, 0, 0))
            surface.blit(text, (rect.centerx - text.get_width()//2,
                              rect.centery - text.get_height()//2))

# ========== MAIN GAME ==========
class Game:
    def __init__(self):
        self.player = Player()
        self.bullets = []
        self.particles = []
        self.trail = SpaceTrail()
        self.ui = UIManager()

        self.game_state = 'menu'
        self.mouse_pressed = False

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            if event.type == pygame.KEYDOWN:
                if self.game_state == 'menu':
                    if event.key in [pygame.K_UP, pygame.K_w]:
                        self.ui.selected = (self.ui.selected - 1) % 3
                    elif event.key in [pygame.K_DOWN, pygame.K_s]:
                        self.ui.selected = (self.ui.selected + 1) % 3
                    elif event.key == pygame.K_RETURN:
                        action = self.ui.menu_buttons[self.ui.selected]['action']
                        if action == 'start':
                            self.start_game()
                        elif action == 'exit':
                            pygame.quit()
                            sys.exit()

                elif self.game_state in ['game_over', 'victory']:
                    if event.key == pygame.K_RETURN:
                        self.start_game()
                    elif event.key == pygame.K_ESCAPE:
                        self.game_state = 'menu'

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.mouse_pressed = True

                if self.game_state == 'playing':
                    bullets_data = self.player.shoot()  # تغيير: إرجاع قائمة
                    for bullet_data in bullets_data:
                        self.bullets.append(Bullet(**bullet_data))

                elif self.game_state in ['game_over', 'victory']:
                    pos = pygame.mouse.get_pos()
                    buttons = [
                        pygame.Rect(SCREEN_WIDTH//2 - 180, 520, 360, 50),
                        pygame.Rect(SCREEN_WIDTH//2 - 180, 590, 360, 50)
                    ]

                    if buttons[0].collidepoint(pos):
                        self.start_game()
                    elif buttons[1].collidepoint(pos):
                        self.game_state = 'menu'

            if event.type == pygame.MOUSEBUTTONUP:
                self.mouse_pressed = False

    def start_game(self):
        self.player = Player()
        self.bullets.clear()
        self.particles.clear()
        self.trail = SpaceTrail()
        self.game_state = 'playing'

    def update(self):
        if self.game_state != 'playing':
            return

        keys = pygame.key.get_pressed()

        mouse_pos = pygame.mouse.get_pos()

        # اللاعب يبقى ثابتاً في مكانه
        self.player.update(keys, mouse_pos)
        self.trail.update()  # المسار والأعداء يتحركون

        if self.mouse_pressed:
            bullets_data = self.player.shoot()  # تغيير: إرجاع قائمة
            for bullet_data in bullets_data:
                self.bullets.append(Bullet(**bullet_data))

        # تحديث الرصاصات والتحقق من التصادمات مع الأعداء
        for bullet in self.bullets[:]:
            if bullet.update():
                self.bullets.remove(bullet)
                continue

            # التصادم مع الأعداء
            if self.trail.current_formation < self.trail.total_formations:
                formation = self.trail.formations[self.trail.current_formation]
                for enemy in formation.enemies[:]:
                    dx = bullet.x - enemy.x
                    dy = bullet.y - enemy.y
                    distance = math.sqrt(dx*dx + dy*dy)

                    if distance < 6 + enemy.radius:
                        self.particles.extend(enemy.take_damage(bullet.damage))
                        self.player.score += 10

                        if enemy.health <= 0:

                            formation.enemies.remove(enemy)
                            self.player.score += enemy.points
                            if self.player.score % 300 == 0:
                                self.player.level_up()

                        if bullet in self.bullets:
                            self.bullets.remove(bullet)
                        break

        # التحقق من التصادم بين اللاعب والأعداء
        if self.trail.current_formation < self.trail.total_formations:
            formation = self.trail.formations[self.trail.current_formation]
            for enemy in formation.enemies:
                dx = enemy.x - self.player.x
                dy = enemy.y - self.player.y
                distance = math.sqrt(dx*dx + dy*dy)

                # موت فوري إذا لمس العدو اللاعب
                if distance < enemy.radius + self.player.radius:
                    self.player.health = 0
                    formation.enemies.remove(enemy)
                    break

        # تحديث الجسيمات
        ParticleSystem.update_particles(self.particles)

        # التحقق من شروط نهاية اللعبة
        if self.player.health <= 0:
            self.game_state = 'game_over'
        elif self.trail.planet_reached:
            self.game_state = 'victory'


    def draw(self):
        screen.fill(COLORS['bg'])

        if self.game_state == 'menu':
            self.ui.draw_menu(screen)

        elif self.game_state == 'playing':
            self.trail.draw(screen)

            for bullet in self.bullets:
                bullet.draw(screen)

            ParticleSystem.draw_particles(screen, self.particles)
            self.player.draw(screen)
            self.ui.draw_game_ui(screen, self.player, self.trail)

        elif self.game_state == 'game_over':
            self.trail.draw(screen)
            self.player.draw(screen)
            self.ui.draw_game_over(screen, self.player, self.trail)

        elif self.game_state == 'victory':
            self.trail.draw(screen)
            self.player.draw(screen)
            self.ui.draw_victory(screen, self.player)

        pygame.display.flip()

# ========== RUN GAME ==========
if __name__ == "__main__":
    game = Game()


    while True:
        game.handle_events()
        game.update()
        game.draw()
        clock.tick(FPS)