import pygame
import random
import math
import sys

# Инициализация Pygame
pygame.init()
pygame.mixer.init()

# Настройки экрана
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("🐠 DIVISION FISH - Математическая Аркада")

# Цвета
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
BLUE = (30, 144, 255)
DARK_BLUE = (0, 100, 200)
GREEN = (0, 255, 100)
RED = (255, 50, 50)
YELLOW = (255, 255, 0)
PURPLE = (200, 50, 255)
ORANGE = (255, 150, 0)
PINK = (255, 100, 150)
CYAN = (0, 255, 255)
COLORS = [RED, GREEN, BLUE, YELLOW, PURPLE, ORANGE, PINK, CYAN]

# Шрифты
font_large = pygame.font.Font(None, 72)
font_medium = pygame.font.Font(None, 48)
font_small = pygame.font.Font(None, 36)
font_tiny = pygame.font.Font(None, 24)

# Звуки (синтезированные)
def create_sound(frequency, duration, volume=0.5):
    sample_rate = 44100
    frames = int(duration * sample_rate)
    arr = []
    for i in range(frames):
        t = float(i) / sample_rate
        wave = math.sin(2 * math.pi * frequency * t) * volume
        arr.append(int(wave * 32767))
    return pygame.sndarray.make_sound(pygame.sndarray.array(arr))

try:
    eat_sound = create_sound(880, 0.1, 0.3)
    wrong_sound = create_sound(220, 0.3, 0.3)
    level_up_sound = create_sound(440, 0.2, 0.4)
    game_over_sound = create_sound(150, 0.8, 0.5)
except:
    eat_sound = wrong_sound = level_up_sound = game_over_sound = None

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)
        self.life = 1.0
        self.color = color
        self.size = random.randint(4, 8)
    
    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.2
        self.life -= 0.02
        self.size *= 0.98
        return self.life > 0
    
    def draw(self, screen):
        alpha = int(self.life * 255)
        color = (*self.color[:3], alpha)
        size = max(1, int(self.size))
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), size)

class Fish:
    def __init__(self):
        self.x = SCREEN_WIDTH // 2
        self.y = SCREEN_HEIGHT // 2
        self.size = 30
        self.speed = 5
        self.value = 1
        self.score = 0
        self.level = 1
        self.combo = 0
        self.max_combo = 0
        self.target_x = self.x
        self.target_y = self.y
        self.tail_wag = 0
        self.particles = []
        
    def move(self, mouse_x, mouse_y):
        self.target_x = mouse_x
        self.target_y = mouse_y
        dx = mouse_x - self.x
        dy = mouse_y - self.y
        dist = math.sqrt(dx*dx + dy*dy)
        
        if dist > 1:
            self.x += (dx / dist) * min(self.speed, dist)
            self.y += (dy / dist) * min(self.speed, dist)
        
        self.tail_wag += 0.1
        
    def grow(self, amount=1):
        self.size += amount * 1.5
        self.value += 1
        self.score += 10 * self.level * (1 + self.combo // 5)
        self.combo += 1
        if self.combo > self.max_combo:
            self.max_combo = self.combo
        if self.value % 5 == 0:
            self.level += 1
            if level_up_sound:
                level_up_sound.play()
            return True
        return False
    
    def reset_combo(self):
        self.combo = 0
    
    def draw(self, screen):
        # Тень
        pygame.draw.ellipse(screen, (0, 0, 0, 50), 
                           (self.x - self.size//1.5 + 5, self.y + self.size//2 - 5, 
                            self.size*1.2, self.size//3))
        
        # Тело рыбы
        body_color = (100, 200, 255) if self.value % 2 == 0 else (255, 150, 100)
        
        # Основное тело (эллипс)
        body_rect = pygame.Rect(self.x - self.size, self.y - self.size//2, 
                                self.size*2, self.size)
        pygame.draw.ellipse(screen, body_color, body_rect)
        
        # Глаз
        eye_x = self.x + self.size//2
        eye_y = self.y - self.size//4
        pygame.draw.circle(screen, WHITE, (int(eye_x), int(eye_y)), self.size//4)
        pygame.draw.circle(screen, BLACK, (int(eye_x + self.size//6), int(eye_y)), self.size//8)
        
        # Хвост
        tail_x = self.x - self.size
        tail_points = [
            (tail_x, self.y - self.size//2),
            (tail_x - self.size//1.5, self.y - self.size//3 + math.sin(self.tail_wag) * 5),
            (tail_x - self.size//1.5, self.y + self.size//3 + math.sin(self.tail_wag + 0.5) * 5),
            (tail_x, self.y + self.size//2)
        ]
        pygame.draw.polygon(screen, (50, 150, 200), tail_points)
        
        # Плавник
        fin_points = [
            (self.x, self.y - self.size//2),
            (self.x + self.size//4, self.y - self.size),
            (self.x + self.size//1.5, self.y - self.size//2)
        ]
        pygame.draw.polygon(screen, (80, 180, 230), fin_points)
        
        # Значение рыбы
        value_text = font_medium.render(str(self.value), True, WHITE)
        text_rect = value_text.get_rect(center=(self.x, self.y))
        screen.blit(value_text, text_rect)
        
        # Блики
        pygame.draw.ellipse(screen, (255, 255, 255, 100),
                           (self.x - self.size//3, self.y - self.size//3,
                            self.size//2, self.size//6))
    
    def add_particles(self, x, y, color, count=20):
        for _ in range(count):
            self.particles.append(Particle(x, y, color))
    
    def update_particles(self):
        self.particles = [p for p in self.particles if p.update()]
        for p in self.particles:
            p.draw(screen)

class NumberBubble:
    def __init__(self):
        self.x = random.randint(50, SCREEN_WIDTH - 50)
        self.y = random.randint(50, SCREEN_HEIGHT - 50)
        self.value = random.randint(1, 20)
        self.size = 30 + self.value * 1.5
        self.speed_x = random.uniform(-1, 1)
        self.speed_y = random.uniform(-1, 1)
        self.color = random.choice(COLORS)
        self.alive = True
        self.pulse = 0
        self.max_size = self.size
    
    def update(self):
        self.x += self.speed_x
        self.y += self.speed_y
        
        # Отскок от стен
        if self.x < self.size or self.x > SCREEN_WIDTH - self.size:
            self.speed_x *= -1
        if self.y < self.size or self.y > SCREEN_HEIGHT - self.size:
            self.speed_y *= -1
        
        # Пульсация
        self.pulse += 0.05
        self.size = self.max_size + math.sin(self.pulse) * 3
        
        # Ограничение
        self.x = max(self.size, min(SCREEN_WIDTH - self.size, self.x))
        self.y = max(self.size, min(SCREEN_HEIGHT - self.size, self.y))
    
    def draw(self, screen):
        # Свечение
        for i in range(3, 0, -1):
            alpha = 30 // i
            glow_rect = pygame.Rect(self.x - self.size*i//2, self.y - self.size*i//2, 
                                    self.size*i, self.size*i)
            pygame.draw.circle(screen, (*self.color[:3], alpha), 
                             (int(self.x), int(self.y)), int(self.size*i//2))
        
        # Основной круг
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))
        pygame.draw.circle(screen, WHITE, (int(self.x), int(self.y)), int(self.size), 2)
        
        # Значение
        text = font_small.render(str(self.value), True, WHITE)
        text_rect = text.get_rect(center=(self.x, self.y))
        screen.blit(text, text_rect)
        
        # Блик
        pygame.draw.circle(screen, (255, 255, 255, 50),
                          (int(self.x - self.size//3), int(self.y - self.size//3)),
                          int(self.size//4))
    
    def check_collision(self, fish):
        dist = math.sqrt((self.x - fish.x)**2 + (self.y - fish.y)**2)
        return dist < self.size + fish.size

class Game:
    def __init__(self):
        self.fish = Fish()
        self.bubbles = []
        self.spawn_timer = 0
        self.spawn_interval = 90
        self.running = True
        self.game_over = False
        self.paused = False
        self.start_time = pygame.time.get_ticks()
        self.score_popups = []
        self.stars = self.create_stars()
        self.bg_offset = 0
        
        # Кнопки
        self.restart_button = pygame.Rect(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 50, 160, 50)
        self.quit_button = pygame.Rect(SCREEN_WIDTH//2 - 80, SCREEN_HEIGHT//2 + 120, 160, 50)
        
        # Создаем начальные пузыри
        for _ in range(8):
            self.spawn_bubble()
    
    def create_stars(self):
        stars = []
        for _ in range(100):
            stars.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.1, 0.5)
            })
        return stars
    
    def spawn_bubble(self):
        if len(self.bubbles) < 30:
            self.bubbles.append(NumberBubble())
    
    def handle_click(self, pos):
        if self.game_over:
            if self.restart_button.collidepoint(pos):
                self.__init__()
                return True
            elif self.quit_button.collidepoint(pos):
                pygame.quit()
                sys.exit()
        return False
    
    def update(self):
        if self.game_over or self.paused:
            return
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        self.fish.move(mouse_x, mouse_y)
        
        # Обновляем пузыри
        for bubble in self.bubbles[:]:
            bubble.update()
            
            # Проверка столкновения
            if bubble.alive and bubble.check_collision(self.fish):
                if self.fish.value != 0 and bubble.value % self.fish.value == 0:
                    # Правильное деление
                    if eat_sound:
                        eat_sound.play()
                    self.fish.add_particles(bubble.x, bubble.y, bubble.color, 30)
                    level_up = self.fish.grow()
                    self.score_popups.append({
                        'text': f'+{10 * self.fish.level}',
                        'x': bubble.x,
                        'y': bubble.y - 20,
                        'life': 60,
                        'color': GREEN
                    })
                    if level_up:
                        self.score_popups.append({
                            'text': f'⭐ LEVEL {self.fish.level}!',
                            'x': SCREEN_WIDTH//2,
                            'y': SCREEN_HEIGHT//2,
                            'life': 120,
                            'color': YELLOW
                        })
                    bubble.alive = False
                    self.bubbles.remove(bubble)
                    self.spawn_bubble()
                else:
                    # Неправильное деление
                    if wrong_sound:
                        wrong_sound.play()
                    self.fish.reset_combo()
                    self.fish.add_particles(bubble.x, bubble.y, RED, 15)
                    self.score_popups.append({
                        'text': '❌',
                        'x': bubble.x,
                        'y': bubble.y - 20,
                        'life': 30,
                        'color': RED
                    })
                    # Уменьшаем рыбу
                    self.fish.size = max(15, self.fish.size - 5)
                    if self.fish.size <= 15:
                        self.game_over = True
                        if game_over_sound:
                            game_over_sound.play()
        
        # Спавн новых пузырей
        self.spawn_timer += 1
        if self.spawn_timer >= self.spawn_interval:
            self.spawn_timer = 0
            self.spawn_bubble()
            self.spawn_interval = max(30, self.spawn_interval - 0.5)
        
        # Обновляем всплывающие сообщения
        for popup in self.score_popups[:]:
            popup['life'] -= 1
            popup['y'] -= 0.5
            if popup['life'] <= 0:
                self.score_popups.remove(popup)
        
        # Обновляем частицы
        self.fish.update_particles()
        
        # Движение звезд
        for star in self.stars:
            star['y'] += star['speed']
            if star['y'] > SCREEN_HEIGHT:
                star['y'] = 0
                star['x'] = random.randint(0, SCREEN_WIDTH)
    
    def draw_background(self):
        # Градиент воды
        for i in range(SCREEN_HEIGHT):
            alpha = i / SCREEN_HEIGHT
            color = (int(10 + 20 * alpha), int(50 + 100 * alpha), int(150 + 80 * alpha))
            pygame.draw.line(screen, color, (0, i), (SCREEN_WIDTH, i))
        
        # Звезды (подводный планктон)
        for star in self.stars:
            alpha = int(100 + 155 * (star['size'] / 3))
            color = (200, 255, 200, alpha)
            pygame.draw.circle(screen, color, (int(star['x']), int(star['y'])), star['size'])
        
        # Волны
        for i in range(0, SCREEN_WIDTH, 20):
            wave_y = 50 + math.sin(i * 0.05 + self.bg_offset) * 10
            pygame.draw.circle(screen, (255, 255, 255, 20), (i, int(wave_y)), 10)
        self.bg_offset += 0.02
    
    def draw_hud(self):
        # Верхняя панель
        panel = pygame.Surface((SCREEN_WIDTH, 70))
        panel.set_alpha(180)
        panel.fill((0, 20, 40))
        screen.blit(panel, (0, 0))
        pygame.draw.line(screen, (100, 200, 255), (0, 70), (SCREEN_WIDTH, 70), 2)
        
        # Значения
        score_text = font_small.render(f'🏆 {self.fish.score}', True, YELLOW)
        screen.blit(score_text, (10, 15))
        
        level_text = font_small.render(f'⭐ Level {self.fish.level}', True, CYAN)
        screen.blit(level_text, (200, 15))
        
        value_text = font_small.render(f'🐠 Value: {self.fish.value}', True, WHITE)
        screen.blit(value_text, (400, 15))
        
        combo_text = font_small.render(f'🔥 Combo: x{self.fish.combo}', True, ORANGE)
        screen.blit(combo_text, (600, 15))
        
        bubbles_count = font_tiny.render(f'Bubbles: {len(self.bubbles)}', True, (150, 200, 255))
        screen.blit(bubbles_count, (10, 45))
        
        # Шкала размера
        bar_x, bar_y = 600, 45
        bar_width, bar_height = 180, 15
        pygame.draw.rect(screen, (50, 50, 50), (bar_x, bar_y, bar_width, bar_height))
        health = (self.fish.size - 15) / 30
        health = max(0, min(1, health))
        color = GREEN if health > 0.5 else ORANGE if health > 0.25 else RED
        pygame.draw.rect(screen, color, (bar_x, bar_y, int(bar_width * health), bar_height))
        pygame.draw.rect(screen, WHITE, (bar_x, bar_y, bar_width, bar_height), 1)
        
        size_text = font_tiny.render('Size', True, WHITE)
        screen.blit(size_text, (bar_x + 70, bar_y - 18))
    
    def draw_game_over(self):
        # Затемнение
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill(BLACK)
        screen.blit(overlay, (0, 0))
        
        # Заголовок
        title = font_large.render('💀 GAME OVER', True, RED)
        title_rect = title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 120))
        screen.blit(title, title_rect)
        
        # Статистика
        stats = [
            f'Score: {self.fish.score}',
            f'Level: {self.fish.level}',
            f'Max Combo: x{self.fish.max_combo}',
            f'Fish Value: {self.fish.value}'
        ]
        for i, stat in enumerate(stats):
            text = font_medium.render(stat, True, WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50 + i * 40))
            screen.blit(text, text_rect)
        
        # Кнопки
        pygame.draw.rect(screen, GREEN, self.restart_button)
        pygame.draw.rect(screen, RED, self.quit_button)
        
        restart_text = font_small.render('🔄 Restart', True, WHITE)
        restart_rect = restart_text.get_rect(center=self.restart_button.center)
        screen.blit(restart_text, restart_rect)
        
        quit_text = font_small.render('❌ Quit', True, WHITE)
        quit_rect = quit_text.get_rect(center=self.quit_button.center)
        screen.blit(quit_text, quit_rect)
    
    def draw(self):
        self.draw_background()
        
        # Рисуем пузыри
        for bubble in self.bubbles:
            bubble.draw(screen)
        
        # Рисуем рыбу
        self.fish.draw(screen)
        
        # Рисуем частицы
        self.fish.update_particles()
        
        # Рисуем всплывающие сообщения
        for popup in self.score_popups:
            text = font_small.render(popup['text'], True, popup['color'])
            text_rect = text.get_rect(center=(popup['x'], popup['y']))
            screen.blit(text, text_rect)
        
        # HUD
        self.draw_hud()
        
        # Инструкции
        if not self.game_over and not self.paused and len(self.bubbles) > 0:
            instruct = font_tiny.render('Ешь числа, которые делятся на твое значение!', True, (200, 200, 255))
            instruct_rect = instruct.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT - 30))
            screen.blit(instruct, instruct_rect)
        
        # Game Over
        if self.game_over:
            self.draw_game_over()
        
        pygame.display.flip()

def main():
    clock = pygame.time.Clock()
    game = Game()
    
    while game.running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if game.handle_click(event.pos):
                    pass
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    game.running = False
                elif event.key == pygame.K_SPACE:
                    game.paused = not game.paused
                elif event.key == pygame.K_r and game.game_over:
                    game.__init__()
        
        game.update()
        game.draw()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()