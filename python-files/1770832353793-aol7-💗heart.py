import pygame
import math
import random

# Инициализация pygame-ce
pygame.init()
WIDTH, HEIGHT = 1400, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("👑 С Днем всех влюбленных! 👑")
clock = pygame.time.Clock()

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
PINK = (255, 192, 203)
HOT_PINK = (255, 105, 180)
DEEP_PINK = (255, 20, 147)
GOLD = (255, 215, 0)
LIGHT_GOLD = (255, 240, 150)
ROSE = (255, 40, 140)
CRIMSON = (220, 20, 60)
RUBY = (224, 17, 95)
PURPLE = (128, 0, 128)
LAVENDER = (230, 230, 250)
SILVER = (192, 192, 192)
DIAMOND = (185, 242, 255)
DARK_RED = (30, 0, 10)

class Button:
    def __init__(self, x, y, width, height, text, color, hover_color):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = hover_color
        self.current_color = color
        self.is_hovered = False
        self.font = pygame.font.SysFont('Georgia', 20, bold=True)
        
    def update(self, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        self.current_color = self.hover_color if self.is_hovered else self.color
        
    def draw(self, screen):
        # Тень кнопки
        shadow_rect = self.rect.copy()
        shadow_rect.x += 3
        shadow_rect.y += 3
        pygame.draw.rect(screen, (40, 10, 20), shadow_rect, border_radius=15)
        
        # Основная кнопка
        pygame.draw.rect(screen, self.current_color, self.rect, border_radius=15)
        pygame.draw.rect(screen, GOLD, self.rect, 2, border_radius=15)
        
        # Текст кнопки
        text = self.font.render(self.text, True, WHITE)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)
        
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(event.pos)
        return False

class GiantHeart:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.pulse = 1.0
        self.pulse_direction = 1
        self.beat_counter = 0
        
    def update(self):
        # Медленное биение сердца
        self.beat_counter += 1
        if self.beat_counter > 60:
            self.pulse_direction *= -1
            self.beat_counter = 0
        
        if self.pulse_direction > 0:
            self.pulse += 0.003
            if self.pulse > 1.08:
                self.pulse_direction = -1
        else:
            self.pulse -= 0.003
            if self.pulse < 0.92:
                self.pulse_direction = 1
        
    def draw(self, screen):
        # ОГРОМНОЕ сердце размер 700!
        size = 700 * self.pulse
        points = []
        
        for t in range(0, 628, 1):
            a = t / 100
            x = self.x + 16 * math.sin(a) ** 3 * size / 100
            y = self.y - (13 * math.cos(a) - 5 * math.cos(2*a) 
                         - 2 * math.cos(3*a) - math.cos(4*a)) * size / 100
            points.append((int(x), int(y)))
        
        if len(points) > 2:
            # Внешнее свечение
            for glow in range(8, 0, -1):
                glow_size = size + glow * 25
                glow_points = []
                for t in range(0, 628, 3):
                    a = t / 100
                    x = self.x + 16 * math.sin(a) ** 3 * glow_size / 100
                    y = self.y - (13 * math.cos(a) - 5 * math.cos(2*a) 
                                 - 2 * math.cos(3*a) - math.cos(4*a)) * glow_size / 100
                    glow_points.append((int(x), int(y)))
                if len(glow_points) > 2:
                    alpha = 35 - glow * 3
                    glow_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
                    color = (255, 100 + glow * 10, 150, alpha)
                    pygame.draw.polygon(glow_surface, color, glow_points, 3)
                    screen.blit(glow_surface, (0, 0))
            
            # Основное сердце
            pygame.draw.polygon(screen, RUBY, points)
            
            # Внутреннее сияние
            inner_points = []
            inner_size = size * 0.92
            for t in range(0, 628, 1):
                a = t / 100
                x = self.x + 16 * math.sin(a) ** 3 * inner_size / 100
                y = self.y - (13 * math.cos(a) - 5 * math.cos(2*a) 
                             - 2 * math.cos(3*a) - math.cos(4*a)) * inner_size / 100
                inner_points.append((int(x), int(y)))
            pygame.draw.polygon(screen, (255, 120, 150), inner_points)
            
            # Золотая окантовка
            pygame.draw.polygon(screen, GOLD, points, 8)
            pygame.draw.polygon(screen, LIGHT_GOLD, points, 5)
            pygame.draw.polygon(screen, WHITE, points, 3)
            
            # Бриллиантовые искры по контуру
            for i in range(0, len(points), 15):
                x, y = points[i]
                if i % 45 == 0:
                    pygame.draw.circle(screen, DIAMOND, (x, y), 5)
                    pygame.draw.circle(screen, WHITE, (x, y), 3)
                    pygame.draw.circle(screen, GOLD, (x, y), 7, 1)
                else:
                    pygame.draw.circle(screen, LIGHT_GOLD, (x, y), 2)

class Crown:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        
    def draw(self, screen):
        crown_x = self.x
        crown_y = self.y - 350
        
        # Основа короны
        pygame.draw.ellipse(screen, GOLD, (crown_x - 100, crown_y - 20, 200, 40))
        pygame.draw.ellipse(screen, LIGHT_GOLD, (crown_x - 98, crown_y - 22, 196, 40), 3)
        
        # Зубцы короны
        for i in range(5):
            x = crown_x - 80 + i * 40
            height = 60 if i == 2 else 40
            points = [
                (x - 15, crown_y - 20),
                (x, crown_y - height),
                (x + 15, crown_y - 20)
            ]
            pygame.draw.polygon(screen, GOLD, points)
            pygame.draw.polygon(screen, LIGHT_GOLD, points, 2)
            
            # Бриллианты на короне
            jewel_x = x
            jewel_y = crown_y - height + 10
            jewel_color = DIAMOND if i == 2 else (255, 80, 120)
            pygame.draw.circle(screen, jewel_color, (jewel_x, jewel_y), 8)
            pygame.draw.circle(screen, WHITE, (jewel_x, jewel_y), 4)
            pygame.draw.circle(screen, GOLD, (jewel_x, jewel_y), 10, 1)

class ShootingStar:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(100, WIDTH - 100)
        self.y = random.randint(50, 200)
        self.speed_x = random.uniform(5, 12)
        self.speed_y = random.uniform(3, 8)
        self.size = random.randint(2, 4)
        self.life = random.uniform(0.7, 1.0)
        self.trail_length = random.randint(8, 15)
        
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        self.life -= 0.005
        
        if self.x > WIDTH + 50 or self.y > HEIGHT + 50 or self.life <= 0:
            self.reset()
            
    def draw(self, screen):
        if self.life > 0:
            alpha = int(255 * self.life)
            
            for i in range(self.trail_length):
                trail_x = self.x - self.speed_x * i * 0.5
                trail_y = self.y - self.speed_y * i * 0.5
                trail_alpha = alpha - i * 25
                if trail_alpha > 0:
                    trail_size = self.size - i * 0.1
                    if trail_size > 0:
                        color = (255, 215 - i * 15, 0 + i * 20)
                        pygame.draw.circle(screen, color, 
                                         (int(trail_x), int(trail_y)), 
                                         int(trail_size))
            
            pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), self.size + 1)
            pygame.draw.circle(screen, LIGHT_GOLD, (int(self.x), int(self.y)), self.size)

class Sparkle:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.speed = random.uniform(0.5, 2)
        self.size = random.randint(1, 3)
        self.color = random.choice([GOLD, WHITE, DIAMOND, LIGHT_GOLD, (255, 200, 100), (255, 150, 200)])
        self.twinkle = random.uniform(0, math.pi * 2)
        
    def update(self):
        self.y -= self.speed * 0.1
        self.twinkle += 0.1
        if self.y < 0:
            self.y = HEIGHT
            self.x = random.randint(0, WIDTH)
            
    def draw(self, screen):
        twinkle = 0.7 + 0.3 * math.sin(self.twinkle)
        size = int(self.size * twinkle)
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

def draw_title_frame(screen):
    frame_width = 500
    frame_height = 70
    frame_x = WIDTH // 2 - frame_width // 2
    frame_y = 25
    
    shadow_rect = pygame.Rect(frame_x + 5, frame_y + 5, frame_width, frame_height)
    pygame.draw.rect(screen, (40, 10, 20), shadow_rect, border_radius=20)
    
    frame_rect = pygame.Rect(frame_x, frame_y, frame_width, frame_height)
    
    for i in range(frame_height):
        color_value = 60 + (i / frame_height) * 40
        pygame.draw.line(screen, (int(color_value), 20, 40), 
                        (frame_x, frame_y + i), 
                        (frame_x + frame_width, frame_y + i))
    
    pygame.draw.rect(screen, GOLD, frame_rect, 3, border_radius=20)
    pygame.draw.rect(screen, LIGHT_GOLD, frame_rect, 1, border_radius=20)
    
    for i in range(4):
        x = frame_x + (10 if i % 2 == 0 else frame_width - 10)
        y = frame_y + (10 if i < 2 else frame_height - 10)
        pygame.draw.circle(screen, GOLD, (x, y), 8)
        pygame.draw.circle(screen, DIAMOND, (x, y), 5)
        pygame.draw.circle(screen, WHITE, (x, y), 3)
    
    font = pygame.font.SysFont('Georgia', 32, bold=True, italic=True)
    title = "👑 С Днем всех влюбленных! 👑"
    
    shadow = font.render(title, True, (80, 20, 50))
    shadow_rect = shadow.get_rect(center=(WIDTH//2 + 3, frame_y + frame_height//2 + 3))
    screen.blit(shadow, shadow_rect)
    
    text = font.render(title, True, LIGHT_GOLD)
    text_rect = text.get_rect(center=(WIDTH//2, frame_y + frame_height//2))
    screen.blit(text, text_rect)

def draw_letter_p(screen, x, y):
    font = pygame.font.SysFont('Georgia', 120, bold=True)
    
    for i in range(5, 0, -1):
        shadow = font.render("П", True, (80 - i*10, 10, 40 - i*5))
        shadow_rect = shadow.get_rect(center=(x + i, y + i))
        screen.blit(shadow, shadow_rect)
    
    text = font.render("П", True, WHITE)
    text_rect = text.get_rect(center=(x, y))
    screen.blit(text, text_rect)
    
    text = font.render("П", True, GOLD)
    text_rect = text.get_rect(center=(x - 2, y - 2))
    screen.blit(text, text_rect)
    
    text = font.render("П", True, (255, 220, 240))
    text_rect = text.get_rect(center=(x - 4, y - 4))
    screen.blit(text, text_rect)
    
    for i in range(12):
        angle = pygame.time.get_ticks() / 500 + i * (math.pi * 2 / 12)
        dist = 50 + math.sin(pygame.time.get_ticks() / 300 + i) * 10
        bx = x + math.cos(angle) * dist
        by = y + math.sin(angle) * dist
        
        pygame.draw.circle(screen, DIAMOND, (int(bx), int(by)), 4)
        pygame.draw.circle(screen, WHITE, (int(bx), int(by)), 2)
        pygame.draw.circle(screen, GOLD, (int(bx), int(by)), 6, 1)

def draw_footer(screen):
    frame_width = 300
    frame_height = 50
    frame_x = WIDTH // 2 - frame_width // 2
    frame_y = HEIGHT - 45
    
    shadow_rect = pygame.Rect(frame_x + 3, frame_y + 3, frame_width, frame_height)
    pygame.draw.rect(screen, (40, 10, 20), shadow_rect, border_radius=15)
    
    frame_rect = pygame.Rect(frame_x, frame_y, frame_width, frame_height)
    pygame.draw.rect(screen, DARK_RED, frame_rect, border_radius=15)
    pygame.draw.rect(screen, GOLD, frame_rect, 2, border_radius=15)
    
    font = pygame.font.SysFont('Georgia', 22, italic=True)
    love = "💕 с любовью навеки 💕"
    text = font.render(love, True, ROSE)
    text_rect = text.get_rect(center=(WIDTH//2, frame_y + frame_height//2))
    
    shadow = font.render(love, True, (60, 10, 30))
    shadow_rect = shadow.get_rect(center=(WIDTH//2 + 2, frame_y + frame_height//2 + 2))
    screen.blit(shadow, shadow_rect)
    screen.blit(text, text_rect)

# Создаем объекты
heart = GiantHeart(WIDTH // 2, HEIGHT // 2 - 30)
crown = Crown(WIDTH // 2, HEIGHT // 2 - 30)
sparkles = [Sparkle() for _ in range(200)]
shooting_stars = [ShootingStar() for _ in range(10)]

# Создаем кнопку выхода
exit_button = Button(WIDTH - 120, 30, 90, 40, "Выход ✕", 
                    (180, 30, 60), (220, 50, 80))

running = True
while running:
    mouse_pos = pygame.mouse.get_pos()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
        # ИСПРАВЛЕНО: проверяем клик по кнопке
        if exit_button.is_clicked(event):
            running = False
    
    # Фон
    for i in range(HEIGHT):
        color_value = int(8 + (i / HEIGHT) * 12)
        pygame.draw.line(screen, (color_value, 0, color_value // 2), 
                        (0, i), (WIDTH, i))
    
    # Звездное поле
    for i in range(400):
        x = (i * 17 + pygame.time.get_ticks() // 50) % WIDTH
        y = (i * 11) % HEIGHT
        brightness = 20 + int(15 * math.sin(i + pygame.time.get_ticks() / 600))
        
        if i % 3 == 0:
            color = (brightness, brightness, brightness)
        elif i % 3 == 1:
            color = (brightness, brightness // 2, brightness)
        else:
            color = (brightness // 2, brightness, brightness // 2)
        
        pygame.draw.circle(screen, color, (x, y), 1)
    
    # Рисуем сердце
    heart.update()
    heart.draw(screen)
    
    # Рисуем корону
    crown.draw(screen)
    
    # Рисуем букву П
    draw_letter_p(screen, WIDTH // 2, HEIGHT // 2 - 30)
    
    # Рисуем рамку с заголовком
    draw_title_frame(screen)
    
    # Рисуем нижний текст в рамке
    draw_footer(screen)
    
    # Рисуем искорки
    for sparkle in sparkles:
        sparkle.update()
        sparkle.draw(screen)
    
    # Рисуем падающие звезды
    for star in shooting_stars:
        star.update()
        star.draw(screen)
    
    # Рисуем кнопку выхода
    exit_button.update(mouse_pos)
    exit_button.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()