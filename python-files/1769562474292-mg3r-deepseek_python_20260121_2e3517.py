import pygame
import sys
import random
import math
from pygame.locals import *

# 初始化Pygame
pygame.init()

# 游戏窗口设置
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("原神风格塞尔达式方块世界")
clock = pygame.time.Clock()

# 颜色定义
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (76, 175, 80)
DIRT_BROWN = (121, 85, 72)
STONE_GRAY = (158, 158, 158)
WATER_BLUE = (33, 150, 243)
TREE_GREEN = (56, 142, 60)
SAND_YELLOW = (255, 235, 59)

# 游戏世界参数
BLOCK_SIZE = 40
WORLD_WIDTH = 50
WORLD_HEIGHT = 20
WORLD_DEPTH = 50

# 玩家类（原神风格角色）
class GenshinCharacter:
    def __init__(self):
        self.x = WORLD_WIDTH * BLOCK_SIZE // 2
        self.y = SCREEN_HEIGHT // 2
        self.width = 30
        self.height = 60
        self.speed = 5
        self.jump_power = 15
        self.velocity_y = 0
        self.on_ground = False
        self.direction = 1  # 1为右，-1为左
        self.animation_frame = 0
        self.animation_speed = 0.2
        self.color = (255, 77, 77)  # 原神风格红色
        self.hat_color = (255, 193, 7)  # 帽子/头发颜色
        
    def update(self, keys, world):
        # 水平移动
        if keys[K_a] or keys[K_LEFT]:
            self.x -= self.speed
            self.direction = -1
            self.animation_frame += self.animation_speed
        if keys[K_d] or keys[K_RIGHT]:
            self.x += self.speed
            self.direction = 1
            self.animation_frame += self.animation_speed
        if keys[K_w] or keys[K_UP]:
            self.y -= self.speed
        if keys[K_s] or keys[K_DOWN]:
            self.y += self.speed
            
        # 跳跃
        if (keys[K_SPACE] or keys[K_w]) and self.on_ground:
            self.velocity_y = -self.jump_power
            self.on_ground = False
            
        # 重力
        self.velocity_y += 0.8
        self.y += self.velocity_y
        
        # 边界检查
        self.x = max(0, min(self.x, WORLD_WIDTH * BLOCK_SIZE - self.width))
        
        # 地面碰撞检测（简化版）
        ground_level = SCREEN_HEIGHT - 100
        if self.y + self.height > ground_level:
            self.y = ground_level - self.height
            self.velocity_y = 0
            self.on_ground = True
            
        # 动画循环
        if self.animation_frame >= 4:
            self.animation_frame = 0
            
    def draw(self, surface, camera_x):
        # 绘制原神风格角色
        draw_x = self.x - camera_x
        draw_y = self.y
        
        # 身体
        pygame.draw.rect(surface, self.color, 
                        (draw_x, draw_y, self.width, self.height))
        
        # 头部
        head_size = 25
        pygame.draw.circle(surface, (255, 224, 178), 
                          (draw_x + self.width//2, draw_y - 5), head_size)
        
        # 头发/帽子（原神风格）
        hat_points = [
            (draw_x + self.width//2 - 15, draw_y - 10),
            (draw_x + self.width//2 + 15, draw_y - 10),
            (draw_x + self.width//2 + 20, draw_y - 30),
            (draw_x + self.width//2 - 20, draw_y - 30)
        ]
        pygame.draw.polygon(surface, self.hat_color, hat_points)
        
        # 眼睛
        eye_offset = 5 * self.direction
        pygame.draw.circle(surface, (30, 30, 30), 
                          (draw_x + self.width//2 - 5 + eye_offset, draw_y - 8), 3)
        pygame.draw.circle(surface, (30, 30, 30), 
                          (draw_x + self.width//2 + 5 + eye_offset, draw_y - 8), 3)
        
        # 腿（行走动画）
        leg_y = draw_y + self.height
        leg_offset = math.sin(self.animation_frame * math.pi) * 10
        
        pygame.draw.rect(surface, (100, 50, 50), 
                        (draw_x + 5, leg_y, 8, 15 + leg_offset))
        pygame.draw.rect(surface, (100, 50, 50), 
                        (draw_x + self.width - 13, leg_y, 8, 15 - leg_offset))

# 方块类（塞尔达风格）
class Block:
    def __init__(self, x, y, block_type):
        self.x = x
        self.y = y
        self.type = block_type
        self.colors = {
            'grass': GRASS_GREEN,
            'dirt': DIRT_BROWN,
            'stone': STONE_GRAY,
            'water': WATER_BLUE,
            'tree': TREE_GREEN,
            'sand': SAND_YELLOW
        }
        
    def draw(self, surface, camera_x):
        draw_x = self.x * BLOCK_SIZE - camera_x
        draw_y = self.y * BLOCK_SIZE
        
        if self.type == 'tree':
            # 塞尔达风格树木
            pygame.draw.rect(surface, (139, 69, 19), 
                           (draw_x + BLOCK_SIZE//4, draw_y + BLOCK_SIZE//2, 
                            BLOCK_SIZE//2, BLOCK_SIZE))
            pygame.draw.circle(surface, TREE_GREEN, 
                             (draw_x + BLOCK_SIZE//2, draw_y + BLOCK_SIZE//4), 
                             BLOCK_SIZE//1.5)
        elif self.type == 'water':
            # 动画水效果
            wave_offset = math.sin(pygame.time.get_ticks() * 0.001 + self.x) * 3
            pygame.draw.rect(surface, self.colors[self.type], 
                           (draw_x, draw_y + wave_offset, BLOCK_SIZE, BLOCK_SIZE))
            # 水波纹
            for i in range(3):
                wave_y = draw_y + wave_offset + i * 5
                pygame.draw.line(surface, (255, 255, 255, 100),
                               (draw_x, wave_y),
                               (draw_x + BLOCK_SIZE, wave_y), 1)
        else:
            # 塞尔达风格方块（带边框）
            pygame.draw.rect(surface, self.colors[self.type], 
                           (draw_x, draw_y, BLOCK_SIZE, BLOCK_SIZE))
            
            # 3D效果边框
            pygame.draw.line(surface, (255, 255, 255, 150),
                           (draw_x, draw_y),
                           (draw_x + BLOCK_SIZE, draw_y), 2)
            pygame.draw.line(surface, (255, 255, 255, 150),
                           (draw_x, draw_y),
                           (draw_x, draw_y + BLOCK_SIZE), 2)
            pygame.draw.line(surface, (100, 100, 100, 150),
                           (draw_x + BLOCK_SIZE, draw_y),
                           (draw_x + BLOCK_SIZE, draw_y + BLOCK_SIZE), 2)
            pygame.draw.line(surface, (100, 100, 100, 150),
                           (draw_x, draw_y + BLOCK_SIZE),
                           (draw_x + BLOCK_SIZE, draw_y + BLOCK_SIZE), 2)

# 生成塞尔达风格的世界
def generate_zelda_world():
    world = []
    
    # 生成地形高度图
    height_map = []
    for x in range(WORLD_WIDTH):
        height = int(10 + 5 * math.sin(x * 0.2) + 3 * math.sin(x * 0.5))
        height_map.append(height)
    
    # 创建世界方块
    for x in range(WORLD_WIDTH):
        for y in range(WORLD_HEIGHT):
            if y > height_map[x] + 1:
                block_type = 'stone'
            elif y == height_map[x]:
                # 随机生成树木和草
                if random.random() < 0.1 and x > 5 and x < WORLD_WIDTH - 5:
                    block_type = 'tree'
                else:
                    block_type = 'grass'
            elif y > height_map[x]:
                block_type = 'dirt'
            else:
                block_type = 'air'
                
            if block_type != 'air':
                world.append(Block(x, y, block_type))
    
    # 添加水域
    for x in range(15, 25):
        for y in range(12, 14):
            world.append(Block(x, y, 'water'))
    
    # 添加沙滩
    for x in range(5, 10):
        for y in range(11, 12):
            world.append(Block(x, y, 'sand'))
    
    return world

# 绘制塞尔达风格UI
def draw_zelda_ui(surface, character):
    # 顶部血条/体力条（原神风格）
    pygame.draw.rect(surface, (40, 40, 40), (20, 20, 200, 25), border_radius=5)
    pygame.draw.rect(surface, (255, 77, 77), (22, 22, 196, 21), border_radius=3)
    
    # 体力条
    pygame.draw.rect(surface, (40, 40, 40), (20, 50, 200, 15), border_radius=3)
    pygame.draw.rect(surface, (64, 196, 255), (22, 52, 180, 11), border_radius=2)
    
    # 元素图标（原神风格）
    pygame.draw.circle(surface, (255, 193, 7), (280, 35), 20)
    pygame.draw.circle(surface, (33, 150, 243), (320, 35), 20)
    pygame.draw.circle(surface, (255, 87, 34), (360, 35), 20)
    pygame.draw.circle(surface, (156, 39, 176), (400, 35), 20)
    
    # 迷你地图边框
    pygame.draw.rect(surface, (139, 69, 19), 
                    (SCREEN_WIDTH - 150, 20, 130, 130), border_radius=5)
    pygame.draw.rect(surface, (101, 67, 33), 
                    (SCREEN_WIDTH - 148, 22, 126, 126), border_radius=3)
    
    # 操作提示
    font = pygame.font.SysFont(None, 24)
    controls = [
        "WASD/方向键: 移动",
        "空格: 跳跃",
        "鼠标左键: 放置方块",
        "鼠标右键: 破坏方块",
        "ESC: 退出游戏"
    ]
    
    for i, text in enumerate(controls):
        text_surface = font.render(text, True, (240, 240, 240))
        surface.blit(text_surface, (20, 80 + i * 25))

# 绘制塞尔达风格天空和背景
def draw_zelda_background(surface, camera_x):
    # 渐变天空
    for y in range(SCREEN_HEIGHT // 2):
        color_value = 135 + y // 5
        color = (color_value, 206, 235)
        pygame.draw.line(surface, color, (0, y), (SCREEN_WIDTH, y))
    
    # 塞尔达风格云朵
    for i in range(5):
        cloud_x = (camera_x * 0.1 + i * 200) % (SCREEN_WIDTH + 400) - 200
        cloud_y = 80 + i * 30
        pygame.draw.ellipse(surface, (255, 255, 255, 200),
                          (cloud_x, cloud_y, 100, 40))
        pygame.draw.ellipse(surface, (255, 255, 255, 200),
                          (cloud_x + 30, cloud_y - 20, 120, 50))
    
    # 远处山脉（塞尔达风格）
    for i in range(3):
        mountain_x = (camera_x * 0.05 + i * 400) % (SCREEN_WIDTH + 800) - 400
        points = [
            (mountain_x, SCREEN_HEIGHT // 2 + 50),
            (mountain_x + 200, SCREEN_HEIGHT // 2 - 100),
            (mountain_x + 400, SCREEN_HEIGHT // 2 + 50)
        ]
        color = (100 + i * 20, 120 + i * 20, 140 + i * 20)
        pygame.draw.polygon(surface, color, points)

# 主游戏函数
def main():
    character = GenshinCharacter()
    world = generate_zelda_world()
    
    camera_x = 0
    inventory = {'grass': 10, 'dirt': 10, 'stone': 5}
    selected_block = 'grass'
    
    running = True
    while running:
        # 事件处理
        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_1:
                    selected_block = 'grass'
                elif event.key == K_2:
                    selected_block = 'dirt'
                elif event.key == K_3:
                    selected_block = 'stone'
                elif event.key == K_4:
                    selected_block = 'tree'
            elif event.type == MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                world_x = (mouse_x + camera_x) // BLOCK_SIZE
                world_y = mouse_y // BLOCK_SIZE
                
                if event.button == 1:  # 左键放置
                    if inventory.get(selected_block, 0) > 0:
                        world.append(Block(world_x, world_y, selected_block))
                        inventory[selected_block] -= 1
                elif event.button == 3:  # 右键破坏
                    for block in world[:]:
                        if block.x == world_x and block.y == world_y:
                            if block.type != 'water':  # 不能破坏水
                                world.remove(block)
                                inventory[block.type] = inventory.get(block.type, 0) + 1
        
        # 更新
        keys = pygame.key.get_pressed()
        character.update(keys, world)
        
        # 相机跟随（塞尔达风格平滑跟随）
        target_camera_x = character.x - SCREEN_WIDTH // 2
        camera_x += (target_camera_x - camera_x) * 0.1
        
        # 绘制
        draw_zelda_background(screen, camera_x)
        
        # 绘制世界
        for block in world:
            if (block.x * BLOCK_SIZE > camera_x - BLOCK_SIZE and 
                block.x * BLOCK_SIZE < camera_x + SCREEN_WIDTH):
                block.draw(screen, camera_x)
        
        # 绘制角色
        character.draw(screen, camera_x)
        
        # 绘制UI
        draw_zelda_ui(screen, character)
        
        # 绘制当前选中的方块
        font = pygame.font.SysFont(None, 28)
        block_text = font.render(f"选中: {selected_block} (数量: {inventory.get(selected_block, 0)})", 
                                True, (240, 240, 240))
        screen.blit(block_text, (SCREEN_WIDTH - 300, SCREEN_HEIGHT - 40))
        
        # 绘制提示
        hint_text = font.render("按1-4切换方块类型，鼠标左右键放置/破坏", True, (240, 240, 240))
        screen.blit(hint_text, (SCREEN_WIDTH // 2 - 200, SCREEN_HEIGHT - 40))
        
        pygame.display.flip()
        clock.tick(60)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()