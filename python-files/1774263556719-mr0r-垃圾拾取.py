import pygame
import random
import math
import os
import sys

pygame.init()

# 屏幕设置
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Eco Code Warrior")
clock = pygame.time.Clock()

# 颜色定义
BACKGROUND = (10, 20, 30)  # 背景色
PLAYER_COLOR = (0, 255, 150)  # 玩家颜色
TRASH_COLOR = (255, 200, 50)  # 垃圾颜色
ENEMY_COLORS = {  # 敌人颜色
    'malware': (255, 50, 50),  # 恶意软件
    'trojan': (180, 50, 220),  # 木马病毒
    'ransomware': (50, 180, 255)  # 勒索软件
}
UI_COLOR = (180, 230, 255)  # UI颜色
GRID_COLOR = (30, 40, 60)  # 网格颜色
TEXT_COLOR = (40, 60, 80)  # 文本颜色

# 创建内置字体
def create_builtin_font(size=24, bold=False):
    """创建内置像素字体以避免系统字体问题"""
    # 使用指定字体文件
    try:
        # 尝试加载字体
        font = pygame.font.Font('Microsoft JhengHei.ttf', size)
    except:
        # 如果失败，回退到默认字体
        font = pygame.font.Font(None, size)
    
    font.set_bold(bold)
    return font

# 错误代码列表
ERROR_TEXTS = [
    "SyntaxErr", "NullPtr", "404", "NaN",
    "TypeErr", "SegFault", "500", "EOF"
]

# 环保知识
ENV_FACTS = [
    "Recycle 1 ton plastic = save 685 gallons oil",
    "E-waste accounts for 5% of global pollution",
    "Code optimization reduces server energy consumption",
    "1 old phone can pollute 60,000 liters of water",
    "50 million tons of e-waste discarded globally each year"
]

# 玩家类
class Player:
    def __init__(self, x, y):
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.radius = 20  # 半径
        self.dash_cooldown = 0  # 冲刺冷却时间
    
    def draw(self, screen):
        """绘制玩家角色"""
        # 绘制身体
        pygame.draw.circle(screen, PLAYER_COLOR, (self.x, self.y), self.radius)
        pygame.draw.circle(screen, BACKGROUND, (self.x, self.y), self.radius - 5)
        
        # 绘制眼睛
        pygame.draw.rect(screen, PLAYER_COLOR, (self.x - 8, self.y - 6, 6, 12))
        pygame.draw.rect(screen, PLAYER_COLOR, (self.x + 2, self.y - 6, 6, 12))
        
        # 绘制标识符
        font = create_builtin_font(16, bold=True)
        text = font.render("{}", True, PLAYER_COLOR)
        screen.blit(text, (self.x - 10, self.y - 10))
    
    def update(self, keys):
        """更新玩家位置"""
        dx, dy = 0, 0  # 移动增量
        
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -5  # 向左移动
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = 5  # 向右移动
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -5  # 向上移动
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = 5  # 向下移动
            
        # 冲刺能力
        if keys[pygame.K_SPACE] and self.dash_cooldown <= 0:
            dx *= 3  # x方向加速
            dy *= 3  # y方向加速
            self.dash_cooldown = 30  # 设置冷却时间
        
        # 更新冷却时间
        if self.dash_cooldown > 0:
            self.dash_cooldown -= 1
            
        # 更新位置
        self.x = max(self.radius, min(SCREEN_WIDTH - self.radius, self.x + dx))  # 限制x在屏幕内
        self.y = max(self.radius, min(SCREEN_HEIGHT - self.radius, self.y + dy))  # 限制y在屏幕内

# 垃圾类
class Trash:
    def __init__(self, x, y):
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.size = 15  # 尺寸
        self.type = random.choice(['error', 'warning', 'bug'])  # 类型
        self.value = 10 if self.type == 'warning' else 20  # 分值
        self.text = random.choice(ERROR_TEXTS)  # 显示文本
    
    def draw(self, screen):
        """绘制垃圾"""
        # 绘制主体
        pygame.draw.rect(screen, TRASH_COLOR, (self.x - self.size, self.y - self.size, 
                                             self.size * 2, self.size * 2))
        pygame.draw.rect(screen, BACKGROUND, (self.x - self.size + 4, self.y - self.size + 4, 
                                           self.size * 2 - 8, self.size * 2 - 8))
        
        # 绘制文本
        font = create_builtin_font(12)
        text = font.render(self.text, True, TRASH_COLOR)
        # 计算文本位置
        text_x = self.x - text.get_width() // 2  # 中心水平对齐
        text_y = self.y - text.get_height() // 2  # 中心垂直对齐
        screen.blit(text, (text_x, text_y))

# 敌人类
class Enemy:
    def __init__(self, x, y, enemy_type):
        self.x = x  # x坐标
        self.y = y  # y坐标
        self.size = 25  # 尺寸
        self.type = enemy_type  # 敌人类别
        self.color = ENEMY_COLORS[enemy_type]  # 颜色
        self.speed = random.uniform(1.0, 2.5)  # 移动速度
    
    def draw(self, screen):
        """绘制敌人"""
        # 绘制主体
        pygame.draw.circle(screen, self.color, (self.x, self.y), self.size)
        pygame.draw.circle(screen, BACKGROUND, (self.x, self.y), self.size - 5)
        
        # 绘制标识符
        font = create_builtin_font(20, bold=True)
        text = font.render("X", True, self.color)
        screen.blit(text, (self.x - text.get_width() // 2 - 3, self.y - text.get_height() // 2 - 8))
        
        # 绘制类型文本
        font = create_builtin_font(14)
        text = font.render(self.type.upper(), True, (200, 200, 200))
        screen.blit(text, (self.x - text.get_width() // 2, self.y + self.size + 5))

# 主游戏函数
def main():
    """运行主游戏循环"""
    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)  # 创建玩家在屏幕中央
    trash_list = []  # 垃圾列表
    enemies_list = []  # 敌人列表
    frame_count = 0  # 帧计数器
    game_over = False  # 游戏结束标志
    score = 0  # 分数
    health = 3  # 生命值
    level = 1  # 关卡级别
    current_fact = ""  # 当前环保知识
    fact_timer = 0  # 知识显示计时器
    
    running = True
    while running:
        # 处理事件
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # 关闭窗口事件
                running = False
            elif event.type == pygame.KEYDOWN:  # 按键事件
                if event.key == pygame.K_q:  # 退出游戏
                    running = False
                if game_over and event.key == pygame.K_r:  # 游戏结束且按R键
                    # 重置游戏
                    player = Player(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
                    trash_list = []
                    enemies_list = []
                    frame_count = 0
                    game_over = False
                    score = 0
                    health = 3
                    level = 1
                    current_fact = ""
                    fact_timer = 0
        
        if not game_over:  # 游戏运行中
            # 获取按键状态
            keys = pygame.key.get_pressed()
            
            # 更新玩家位置
            player.update(keys)
            
            # 生成垃圾
            frame_count += 1
            if frame_count % 45 == 0 and len(trash_list) < 15:  # 每45帧生成一个垃圾
                trash_list.append(Trash(
                    random.randint(20, SCREEN_WIDTH - 20),  # 随机x坐标
                    random.randint(20, SCREEN_HEIGHT - 20)   # 随机y坐标
                ))
            
            # 生成敌人
            if frame_count % 120 == 0 and len(enemies_list) < 5:  # 每120帧生成一个敌人
                # 从边缘生成敌人
                side = random.choice(['top', 'right', 'bottom', 'left'])  # 随机选择屏幕边缘
                if side == 'top':  # 顶部边缘
                    x = random.randint(0, SCREEN_WIDTH)
                    y = -30
                elif side == 'right':  # 右侧边缘
                    x = SCREEN_WIDTH + 30
                    y = random.randint(0, SCREEN_HEIGHT)
                elif side == 'bottom':  # 底部边缘
                    x = random.randint(0, SCREEN_WIDTH)
                    y = SCREEN_HEIGHT + 30
                else:  # 左侧边缘
                    x = -30
                    y = random.randint(0, SCREEN_HEIGHT)
                    
                enemies_list.append(Enemy(
                    x, y, 
                    random.choice(['malware', 'trojan', 'ransomware'])  # 随机敌人类别
                ))
            
            # 更新敌人位置
            for enemy in enemies_list:
                # 计算敌人到玩家的向量
                dx = player.x - enemy.x
                dy = player.y - enemy.y
                dist = max(0.1, math.sqrt(dx ** 2 + dy ** 2))  # 计算距离
                
                # 移动敌人(向玩家移动)
                enemy.x += (dx / dist) * enemy.speed
                enemy.y += (dy / dist) * enemy.speed
                
                # 检测碰撞
                enemy_dist = math.sqrt((player.x - enemy.x) ** 2 + (player.y - enemy.y) ** 2)
                if enemy_dist < (player.radius + enemy.size):  # 如果碰撞
                    health -= 0.03  # 减少生命值
                    if health <= 0:  # 生命值为0
                        game_over = True  # 游戏结束
            
            # 检测垃圾收集
            for trash in trash_list[:]:
                trash_dist = math.sqrt((player.x - trash.x) ** 2 + (player.y - trash.y) ** 2)
                if trash_dist < (player.radius + trash.size):  # 如果碰撞
                    trash_list.remove(trash)  # 移除垃圾
                    score += trash.value  # 增加分数
                    
                    # 触发环保知识
                    if trash.type == 'bug' and random.random() < 0.3 and fact_timer <= 0:
                        current_fact = random.choice(ENV_FACTS)  # 随机选择环保知识
                        fact_timer = 180  # 设置显示计时器
            
            # 更新知识计时器
            if fact_timer > 0:
                fact_timer -= 1
            
            # 关卡升级
            if score >= level * 100 and level < 5:  # 分数达到升级条件
                level += 1  # 提升关卡
                health = min(5, health + 0.5)  # 升级时恢复部分生命值
        
        # 绘制背景
        screen.fill(BACKGROUND)
        
        # 绘制网格背景
        for x in range(0, SCREEN_WIDTH, 20):  # 垂直网格线
            pygame.draw.line(screen, GRID_COLOR, (x, 0), (x, SCREEN_HEIGHT), 1)
        for y in range(0, SCREEN_HEIGHT, 20):  # 水平网格线
            pygame.draw.line(screen, GRID_COLOR, (0, y), (SCREEN_WIDTH, y), 1)
        
        # 绘制垃圾
        for trash in trash_list:
            trash.draw(screen)
        
        # 绘制敌人
        for enemy in enemies_list:
            enemy.draw(screen)
        
        # 绘制玩家
        player.draw(screen)
        
        # 绘制UI
        # 生命条
        for i in range(int(health)):
            pygame.draw.rect(screen, (200, 50, 50), (35 + i * 35, SCREEN_HEIGHT - 45, 25, 25))
            font = create_builtin_font(18)
            # 使用实心方块代替心形符号
            text = font.render("■", True, (255, 100, 100))
            screen.blit(text, (35 + i * 35, SCREEN_HEIGHT - 45))
        
        # 分数显示
        font = create_builtin_font(18)
        text = font.render(f"Score: {score}", True, UI_COLOR)
        text_x = SCREEN_WIDTH - 150  # 右侧位置
        text_y = SCREEN_HEIGHT - 45  # 底部位置
        screen.blit(text, (text_x, text_y))
        
        # 关卡显示
        font = create_builtin_font(18)
        text = font.render(f"Level: {level}", True, (100, 255, 100))
        text_x = SCREEN_WIDTH // 2 - text.get_width() // 2  # 居中
        text_y = SCREEN_HEIGHT - 45  # 底部位置
        screen.blit(text, (text_x, text_y))
        
        # 环保知识显示
        if fact_timer > 0:
            pygame.draw.rect(screen, (0, 0, 0, 180), (SCREEN_WIDTH // 2 - 300, 10, 600, 40))  # 半透明背景
            font = create_builtin_font(16)
            text = font.render(f"Eco Fact: {current_fact}", True, (100, 255, 200))
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, 30))
        
        # 控制说明
        if not game_over:
            font = create_builtin_font(14)
            text = font.render("Arrow Keys: Move | Space: Dash", True, (150, 150, 150))
            screen.blit(text, (10, 10))
        
        # 游戏结束画面
        if game_over:
            # 半透明覆盖层
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0, 0, 0, 180))  # 半透明黑色
            screen.blit(s, (0, 0))
            
            # 游戏结束文本
            font = create_builtin_font(40, bold=True)
            text = font.render("Game Over", True, (255, 50, 50))
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 + 30))
            
            # 最终分数
            font = create_builtin_font(30)
            text = font.render(f"Final Score: {score}", True, UI_COLOR)
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 30))
            
            # 重新开始提示
            font = create_builtin_font(24)
            text = font.render("Press [R] to Restart", True, (200, 200, 100))
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 100))
            
            text = font.render("Press [Q] to Quit", True, (200, 200, 100))
            screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, SCREEN_HEIGHT // 2 - 140))
        
        pygame.display.flip()  # 更新屏幕显示
        clock.tick(60)  # 限制帧率为60FPS
    
    pygame.quit()  # 退出pygame
    sys.exit()  # 退出程序

if __name__ == "__main__":
    main()  # 运行游戏
