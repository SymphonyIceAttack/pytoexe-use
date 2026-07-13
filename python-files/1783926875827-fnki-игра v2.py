import pygame
import sys
import random
import math

# Инициализация Pygame
pygame.init()

# Константы
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
BLOCK_SIZE = 32
FPS = 120

# Размеры мира
WORLD_WIDTH = 200
WORLD_HEIGHT = 100
SURFACE_LEVEL = 20

# Цвета
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
BROWN = (139, 69, 19)
GRAY = (128, 128, 128)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
SKY_BLUE = (135, 206, 235)
DARK_GRAY = (64, 64, 64)
ORANGE = (255, 165, 0)

# Типы блоков
BLOCK_TYPES = {
    'D': {'name': 'Дерево', 'color': GREEN},
    'Z': {'name': 'Земля', 'color': BROWN},
    'K': {'name': 'Камень', 'color': GRAY},
    'V': {'name': 'Вода', 'color': BLUE},
    'P': {'name': 'Песок', 'color': YELLOW},
    'S': {'name': 'Стекло', 'color': (200, 200, 255)},
    'R': {'name': 'Руда', 'color': ORANGE},
    'M': {'name': 'Глубинный камень', 'color': DARK_GRAY}
}

# Твёрдые блоки
SOLID_BLOCKS = {'Z', 'K', 'P', 'S', 'R', 'M'}

class Game:
    def __init__(self):
        self.fullscreen = False
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Мини-Террария - Оптимизированная версия")
        self.clock = pygame.time.Clock()
        self.small_font = pygame.font.Font(None, 24)
        
        # Игровые переменные
        self.world = {}
        self.selected_block = 'D'
        
        # Физика игрока
        self.player_width = 20
        self.player_height = 28
        self.player_x = 0
        self.player_y = 0
        self.player_vel_x = 0
        self.player_vel_y = 0
        self.gravity = 0.6
        self.jump_power = -12
        self.on_ground = False
        self.player_speed = 5
        
        # Камера
        self.camera_x = 0
        self.camera_y = 0
        
        # Кэш для оптимизации отрисовки
        self.visible_blocks_cache = []
        self.cache_valid = False
        self.last_cache_update = 0
        self.cache_update_delay = 50  # Обновляем кэш каждые 50мс
        
        # Для отслеживания состояния мыши
        self.mouse_held = False
        self.last_block_action = 0
        self.action_delay = 50  # Задержка между действиями (50мс)
        
        # Создаем мир
        self.generate_world_with_caves()
        self.spawn_player_on_solid_block()
        self.update_camera()
    
    def generate_world_with_caves(self):
        """Генерирует мир с пещерами"""
        surface_heights = []
        for x in range(WORLD_WIDTH):
            height = SURFACE_LEVEL + int(
                3 * math.sin(x * 0.05) + 
                2 * math.sin(x * 0.02 + 1) + 
                1.5 * math.sin(x * 0.1 + 2)
            )
            surface_heights.append(height)
        
        world = self.world
        world.clear()  # Очищаем мир эффективнее
        
        # Заполняем мир блоками
        for x in range(WORLD_WIDTH):
            surface_height = surface_heights[x]
            
            for y in range(WORLD_HEIGHT):
                if y < surface_height:
                    continue
                elif y == surface_height:
                    world[(x, y)] = 'D' if random.random() < 0.3 else 'Z'
                elif y < surface_height + 3:
                    world[(x, y)] = 'Z'
                elif y < surface_height + 8:
                    world[(x, y)] = 'K'
                else:
                    world[(x, y)] = 'M'
        
        self.generate_caves(surface_heights)
        self.cache_valid = False
    
    def generate_caves(self, surface_heights):
        """Генерирует пещеры"""
        world = self.world
        cave_start_depth = 20
        num_cave_systems = random.randint(20, 35)
        
        for _ in range(num_cave_systems):
            cave_x = random.randint(0, WORLD_WIDTH - 1)
            surface_height = surface_heights[cave_x]
            cave_y = surface_height + random.randint(cave_start_depth, 40)
            
            if cave_y >= WORLD_HEIGHT:
                continue
            
            cave_width = random.randint(3, 12)
            cave_height = random.randint(2, 6)
            cave_length = random.randint(5, 25)
            direction = random.choice([1, -1])
            
            for i in range(cave_length):
                current_x = cave_x + i * direction
                
                if current_x < 0 or current_x >= WORLD_WIDTH:
                    break
                
                y_offset = random.randint(-1, 1)
                current_y = cave_y + y_offset
                
                if current_y < 0 or current_y >= WORLD_HEIGHT:
                    continue
                
                for dx in range(-cave_width // 2, cave_width // 2 + 1):
                    for dy in range(-cave_height // 2, cave_height // 2 + 1):
                        check_x = current_x + dx
                        check_y = current_y + dy
                        
                        if (0 <= check_x < WORLD_WIDTH and 0 <= check_y < WORLD_HEIGHT and 
                            check_y > surface_heights[check_x]):
                            world.pop((check_x, check_y), None)
                
                if random.random() < 0.2:
                    branch_x = current_x + random.randint(-2, 2)
                    branch_y = current_y + random.randint(-3, 3)
                    
                    for dx in range(-2, 3):
                        for dy in range(-2, 3):
                            check_x = branch_x + dx
                            check_y = branch_y + dy
                            
                            if (0 <= check_x < WORLD_WIDTH and 0 <= check_y < WORLD_HEIGHT and 
                                check_y > surface_heights[check_x]):
                                world.pop((check_x, check_y), None)
        
        self.generate_ores(surface_heights)
    
    def generate_ores(self, surface_heights):
        """Генерирует руду"""
        world = self.world
        
        for _ in range(100):
            x = random.randint(0, WORLD_WIDTH - 1)
            surface_height = surface_heights[x]
            y = random.randint(surface_height + 3, surface_height + 12)
            
            if y < WORLD_HEIGHT and (x, y) in world:
                if world[(x, y)] == 'K' and random.random() < 0.3:
                    world[(x, y)] = 'R'
        
        for _ in range(80):
            x = random.randint(0, WORLD_WIDTH - 1)
            surface_height = surface_heights[x]
            y = random.randint(surface_height + 13, surface_height + 30)
            
            if y < WORLD_HEIGHT and (x, y) in world:
                if world[(x, y)] == 'M' and random.random() < 0.15:
                    world[(x, y)] = 'R'
        
        self.cache_valid = False
    
    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    
    def spawn_player_on_solid_block(self):
        """Размещает игрока на твёрдом блоке"""
        solid_blocks = [(x, y) for (x, y), block_type in self.world.items() 
                       if block_type in SOLID_BLOCKS]
        
        if solid_blocks:
            surface_blocks = [(x, y) for (x, y) in solid_blocks if y < 25]
            spawn_block = random.choice(surface_blocks if surface_blocks else solid_blocks)
            
            self.player_x = spawn_block[0] * BLOCK_SIZE + BLOCK_SIZE // 2
            self.player_y = spawn_block[1] * BLOCK_SIZE - self.player_height // 2
            
            # Проверяем, что место над блоком свободно
            for _ in range(10):
                above_pos = (spawn_block[0], spawn_block[1] - 1)
                if above_pos not in self.world:
                    break
                spawn_block = random.choice(surface_blocks if surface_blocks else solid_blocks)
                self.player_x = spawn_block[0] * BLOCK_SIZE + BLOCK_SIZE // 2
                self.player_y = spawn_block[1] * BLOCK_SIZE - self.player_height // 2
        else:
            self.player_x = SCREEN_WIDTH // 2
            self.player_y = SCREEN_HEIGHT // 2
            self.world[(self.player_x // BLOCK_SIZE, self.player_y // BLOCK_SIZE + 1)] = 'Z'
        
        self.on_ground = True
        self.player_vel_y = 0
    
    def update_camera(self):
        self.camera_x = self.player_x - self.screen.get_width() // 2
        self.camera_y = self.player_y - self.screen.get_height() // 2
    
    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    self.toggle_fullscreen()
                
                block_keys = {
                    pygame.K_1: 'D', pygame.K_2: 'Z', pygame.K_3: 'K',
                    pygame.K_4: 'V', pygame.K_5: 'P', pygame.K_6: 'S',
                    pygame.K_7: 'R', pygame.K_8: 'M'
                }
                if event.key in block_keys:
                    self.selected_block = block_keys[event.key]
                
                if event.key == pygame.K_SPACE and self.on_ground:
                    self.player_vel_y = self.jump_power
                    self.on_ground = False
                
                if event.key == pygame.K_r:
                    self.generate_world_with_caves()
                    self.spawn_player_on_solid_block()
                    self.cache_valid = False
                
                if event.key == pygame.K_n:
                    self.generate_world_with_caves()
                    self.spawn_player_on_solid_block()
                    self.update_camera()
                    self.cache_valid = False
        
        # Обработка взаимодействия с блоками
        self.handle_block_interaction()
        
        return True
    
    def handle_block_interaction(self):
        """Обработка взаимодействия с блоками через мышь"""
        current_time = pygame.time.get_ticks()
        
        # Проверяем состояние мыши
        mouse_buttons = pygame.mouse.get_pressed()
        if not any(mouse_buttons):
            self.mouse_held = False
            return
        
        # Ограничиваем частоту действий
        if current_time - self.last_block_action < self.action_delay:
            return
        
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = (mouse_x + self.camera_x) // BLOCK_SIZE
        world_y = (mouse_y + self.camera_y) // BLOCK_SIZE
        
        # Проверяем границы мира
        if world_x < 0 or world_x >= WORLD_WIDTH or world_y < 0 or world_y >= WORLD_HEIGHT:
            return
        
        block_pos = (world_x, world_y)
        player_rect = self.get_player_rect()
        block_rect = self.get_block_rect(world_x, world_y)
        
        # Проверяем, не кликает ли игрок по себе
        if block_rect.colliderect(player_rect):
            return
        
        # ЛКМ - разрушение блока
        if mouse_buttons[0]:
            if block_pos in self.world:
                del self.world[block_pos]
                self.last_block_action = current_time
                self.cache_valid = False
        
        # ПКМ - строительство блока
        elif mouse_buttons[2]:
            if block_pos not in self.world:
                self.world[block_pos] = self.selected_block
                self.last_block_action = current_time
                self.cache_valid = False
    
    def get_player_rect(self):
        return pygame.Rect(
            self.player_x - self.player_width // 2,
            self.player_y - self.player_height // 2,
            self.player_width,
            self.player_height
        )
    
    def get_block_rect(self, block_x, block_y):
        return pygame.Rect(
            block_x * BLOCK_SIZE,
            block_y * BLOCK_SIZE,
            BLOCK_SIZE,
            BLOCK_SIZE
        )
    
    def check_collision(self, rect, block_positions):
        for block_pos in block_positions:
            block_rect = self.get_block_rect(block_pos[0], block_pos[1])
            if rect.colliderect(block_rect):
                return True, block_rect
        return False, None
    
    def update(self):
        """Обновление состояния игры"""
        keys = pygame.key.get_pressed()
        
        # Горизонтальное движение
        self.player_vel_x = 0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.player_vel_x = -self.player_speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.player_vel_x = self.player_speed
        
        # Гравитация
        self.player_vel_y += self.gravity
        
        # Движение по X
        self.player_x += self.player_vel_x
        player_rect = self.get_player_rect()
        collision_blocks = list(self.world.keys())
        collision, block_rect = self.check_collision(player_rect, collision_blocks)
        
        if collision:
            if self.player_vel_x > 0:
                self.player_x = block_rect.left - self.player_width // 2
            elif self.player_vel_x < 0:
                self.player_x = block_rect.right + self.player_width // 2
            self.player_vel_x = 0
        
        # Движение по Y
        self.player_y += self.player_vel_y
        player_rect = self.get_player_rect()
        collision, block_rect = self.check_collision(player_rect, collision_blocks)
        
        if collision:
            if self.player_vel_y > 0:
                self.player_y = block_rect.top - self.player_height // 2
                self.player_vel_y = 0
                self.on_ground = True
            elif self.player_vel_y < 0:
                self.player_y = block_rect.bottom + self.player_height // 2
                self.player_vel_y = 0
        
        # Проверка на земле
        if self.player_vel_y == 0:
            test_rect = self.get_player_rect()
            test_rect.y += 1
            collision, _ = self.check_collision(test_rect, collision_blocks)
            self.on_ground = collision
        
        # Обновляем камеру
        self.update_camera()
        
        # Обновляем кэш видимых блоков, если нужно
        current_time = pygame.time.get_ticks()
        if current_time - self.last_cache_update > self.cache_update_delay:
            self.cache_valid = False
            self.last_cache_update = current_time
    
    def get_visible_blocks(self):
        """Возвращает список видимых блоков с кэшированием"""
        if self.cache_valid:
            return self.visible_blocks_cache
        
        screen_width = self.screen.get_width()
        screen_height = self.screen.get_height()
        
        start_x = max(0, int(self.camera_x // BLOCK_SIZE) - 1)
        end_x = min(WORLD_WIDTH, int((self.camera_x + screen_width) // BLOCK_SIZE) + 2)
        start_y = max(0, int(self.camera_y // BLOCK_SIZE) - 1)
        end_y = min(WORLD_HEIGHT, int((self.camera_y + screen_height) // BLOCK_SIZE) + 2)
        
        visible_blocks = []
        world = self.world
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                block_pos = (x, y)
                block_type = world.get(block_pos)
                if block_type:
                    screen_x = x * BLOCK_SIZE - self.camera_x
                    screen_y = y * BLOCK_SIZE - self.camera_y
                    visible_blocks.append((screen_x, screen_y, block_type))
        
        self.visible_blocks_cache = visible_blocks
        self.cache_valid = True
        return visible_blocks
    
    def draw(self):
        """Отрисовка игры"""
        self.screen.fill(SKY_BLUE)
        
        # Отрисовка блоков
        for screen_x, screen_y, block_type in self.get_visible_blocks():
            block_info = BLOCK_TYPES[block_type]
            block_rect = pygame.Rect(screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE)
            pygame.draw.rect(self.screen, block_info['color'], block_rect)
            pygame.draw.rect(self.screen, BLACK, block_rect, 1)
        
        # Отрисовка курсора
        mouse_x, mouse_y = pygame.mouse.get_pos()
        world_x = (mouse_x + self.camera_x) // BLOCK_SIZE
        world_y = (mouse_y + self.camera_y) // BLOCK_SIZE
        
        if 0 <= world_x < WORLD_WIDTH and 0 <= world_y < WORLD_HEIGHT:
            cursor_x = world_x * BLOCK_SIZE - self.camera_x
            cursor_y = world_y * BLOCK_SIZE - self.camera_y
            
            cursor_surf = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE), pygame.SRCALPHA)
            has_block = (world_x, world_y) in self.world
            color = (255, 0, 0, 128) if has_block else (0, 255, 0, 128)
            cursor_surf.fill(color)
            self.screen.blit(cursor_surf, (cursor_x, cursor_y))
        
        # Отрисовка игрока
        player_rect = pygame.Rect(
            self.player_x - self.camera_x - self.player_width // 2,
            self.player_y - self.camera_y - self.player_height // 2,
            self.player_width,
            self.player_height
        )
        pygame.draw.rect(self.screen, RED, player_rect)
        pygame.draw.rect(self.screen, BLACK, player_rect, 2)
        
        # UI
        self.draw_ui()
        
        pygame.display.flip()
    
    def draw_ui(self):
        """Отрисовка UI"""
        screen_height = self.screen.get_height()
        
        # Панель выбора блоков
        panel_rect = pygame.Rect(10, 10, 200, 180)
        pygame.draw.rect(self.screen, WHITE, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        
        title = self.small_font.render("Блоки:", True, BLACK)
        self.screen.blit(title, (20, 15))
        
        y_offset = 40
        for i, (key, info) in enumerate(BLOCK_TYPES.items()):
            color = (0, 200, 0) if key == self.selected_block else BLACK
            text = f"{i+1}: {info['name']}"
            text_surf = self.small_font.render(text, True, color)
            self.screen.blit(text_surf, (20, y_offset))
            y_offset += 18
        
        # Информация
        current_block = BLOCK_TYPES[self.selected_block]
        info_text = f"Блок: {current_block['name']}"
        info_surf = self.small_font.render(info_text, True, BLACK)
        self.screen.blit(info_surf, (10, screen_height - 120))
        
        hint_text = "WASD - движение | Пробел - прыжок | 1-8 - выбор блока"
        hint_surf = self.small_font.render(hint_text, True, BLACK)
        self.screen.blit(hint_surf, (10, screen_height - 95))
        
        hint_text2 = "ЛКМ - разрушить | ПКМ - построить | F11 - полноэкранный"
        hint_surf2 = self.small_font.render(hint_text2, True, BLACK)
        self.screen.blit(hint_surf2, (10, screen_height - 70))
        
        hint_text3 = "R - перегенерация | N - новый мир"
        hint_surf3 = self.small_font.render(hint_text3, True, BLACK)
        self.screen.blit(hint_surf3, (10, screen_height - 45))
        
        player_pos_text = f"Позиция: ({self.player_x//32}, {self.player_y//32})"
        player_pos_surf = self.small_font.render(player_pos_text, True, BLACK)
        self.screen.blit(player_pos_surf, (10, screen_height - 20))
        
        block_count_text = f"Блоков: {len(self.world)}"
        block_count_surf = self.small_font.render(block_count_text, True, BLACK)
        self.screen.blit(block_count_surf, (230, 10))
    
    def run(self):
        running = True
        while running:
            running = self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
