import pygame
import random
import sys
import time
import math

# 初始化Pygame
pygame.init()

# 名单
NAMES = [
    "梁权耀", "赵相楊", "王锦田", "蒋政国", "王淳凯", "张奥东", "郑雨露", "张若珂", "潘家琪", "高文静",
    "杜嘉浩", "张若琦", "孙宇鸿", "文学棪", "赵明杰", "王苗清", "杨成龙", "巩浩然", "曹佳锐", "李妙可",
    "焦俊源", "翟文韬", "郑佳雯", "董志煜", "霍梦萱", "赵紫微", "白一荣", "杨子杰", "温晨霞", "马钰栗",
    "梁素硕", "石梓豪", "郝俊浩", "李钊航", "张稼蓉"
]

# 颜色定义
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GOLD = (255, 215, 0)
DARK_GRAY = (40, 40, 40)
GRAY = (100, 100, 100)
RED = (200, 50, 50)
GREEN = (50, 200, 50)

# 屏幕尺寸
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 400
FPS = 60

# 滚动参数
FONT_SIZE = 60
ITEM_WIDTH = 180  # 每个名字的宽度（包括间距）
VISIBLE_ITEMS = 7  # 可见区域显示的项数
POINTER_POS = SCREEN_WIDTH // 2  # 指针位置（屏幕中间）

class CSRollEffect:
    def __init__(self, names, screen):
        self.names = names
        self.screen = screen
        self.font = pygame.font.Font(None, FONT_SIZE)
        self.small_font = pygame.font.Font(None, 30)
        
        # 用于滚动的名称序列（复制多份以实现无限滚动）
        self.sequence = self.names * 15  # 足够长的序列
        
        # 滚动位置（像素）
        self.scroll_x = 0
        
        # 状态控制
        self.is_rolling = True
        self.result_name = None
        
        # 速度控制参数
        self.speed = 0.0
        self.max_speed = 25.0
        self.deceleration = 0.15  # 减速度
        self.stop_position = None  # 停止时的目标偏移
        
        # 动画时长控制
        self.start_time = time.time()
        self.decel_start_time = None
        self.stop_triggered = False
        
        # 渲染所有名称的surface
        self.name_surfaces = []
        self.name_widths = []
        for name in self.sequence:
            # 如果是长名字，稍微缩小字体
            if len(name) > 4:
                font_tmp = pygame.font.Font(None, FONT_SIZE-10)
                surf = font_tmp.render(name, True, WHITE)
            else:
                surf = self.font.render(name, True, WHITE)
            self.name_surfaces.append(surf)
            self.name_widths.append(surf.get_width() + 20)  # 添加间距
        
        # 预计算总的平均宽度用于布局（简单起见使用固定宽度）
        self.item_width = ITEM_WIDTH
        
        # 背景噪点效果（用于开箱氛围）
        self.noise_particles = []
        for _ in range(50):
            self.noise_particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(1, 3),
                'speed': random.uniform(0.5, 2)
            })
    
    def start_roll(self):
        """开始滚动，初始快速"""
        self.is_rolling = True
        self.speed = self.max_speed
        self.start_time = time.time()
        self.stop_triggered = False
        self.decel_start_time = None
        self.result_name = None
        # 随机初始位置
        self.scroll_x = random.randint(0, self.item_width * len(self.names))
    
    def trigger_stop(self):
        """触发停止（模拟用户点击或自动停止）"""
        if self.is_rolling and not self.stop_triggered:
            self.stop_triggered = True
            # 随机选择一个结果
            self.result_name = random.choice(self.names)
            # 计算要使结果正好对准指针所需的目标偏移
            # 找到结果在序列中的任意一个索引
            result_indices = [i for i, name in enumerate(self.sequence) if name == self.result_name]
            if result_indices:
                # 选择一个索引，使得它在停止时正好在指针位置
                target_idx = random.choice(result_indices)
                # 我们希望 target_idx 对应的名字的中心对准指针
                # 指针位置 POINTER_POS，名字中心相对于scroll_x的偏移：target_idx * item_width + item_width/2 - scroll_x
                # 设置 scroll_x 使得该中心对准 POINTER_POS
                target_center_x = target_idx * self.item_width + self.item_width // 2
                self.stop_position = target_center_x - POINTER_POS
                # 确保滚动方向自然（从右向左），如果目标位置在当前滚动位置右侧，则加上一圈的偏移
                current_pos = self.scroll_x
                if self.stop_position < current_pos - self.item_width * len(self.names) // 2:
                    self.stop_position += self.item_width * len(self.names)
                elif self.stop_position > current_pos + self.item_width * len(self.names) // 2:
                    self.stop_position -= self.item_width * len(self.names)
                
                # 开始减速
                self.decel_start_time = time.time()
    
    def update(self):
        """更新滚动状态"""
        if not self.is_rolling:
            return
        
        if self.stop_triggered and self.decel_start_time:
            # 减速阶段
            elapsed = time.time() - self.decel_start_time
            # 使用平滑的减速曲线：速度逐渐减小到0
            if elapsed < 2.0:  # 减速持续2秒
                # 速度从当前速度线性减小到0
                t = elapsed / 2.0
                # 使用缓动函数 easeOutCubic
                t = 1 - (1 - t) ** 3
                self.speed = self.max_speed * (1 - t)
                
                # 根据速度和目标位置微调，确保准确停止
                # 计算到目标位置的剩余距离
                distance_to_target = self.stop_position - self.scroll_x
                # 如果速度很小且接近目标，就停止
                if abs(distance_to_target) < 2 and self.speed < 0.5:
                    self.scroll_x = self.stop_position
                    self.is_rolling = False
                    self.speed = 0
                else:
                    # 根据剩余距离调整方向，确保最终停在目标
                    if distance_to_target > 0:
                        self.scroll_x += self.speed
                        if self.scroll_x > self.stop_position:
                            self.scroll_x = self.stop_position
                    else:
                        self.scroll_x -= self.speed
                        if self.scroll_x < self.stop_position:
                            self.scroll_x = self.stop_position
            else:
                self.scroll_x = self.stop_position
                self.is_rolling = False
                self.speed = 0
        else:
            # 快速滚动阶段，保持最大速度
            self.scroll_x += self.speed
        
        # 循环滚动位置，保持scroll_x在合理范围，防止溢出
        max_scroll = self.item_width * (len(self.sequence) - VISIBLE_ITEMS)
        if self.scroll_x > max_scroll:
            self.scroll_x -= self.item_width * len(self.names)
        elif self.scroll_x < 0:
            self.scroll_x += self.item_width * len(self.names)
    
    def draw_noise(self):
        """绘制背景噪点，增加开箱质感"""
        for p in self.noise_particles:
            p['x'] -= p['speed']
            if p['x'] < 0:
                p['x'] = SCREEN_WIDTH
                p['y'] = random.randint(0, SCREEN_HEIGHT)
            pygame.draw.circle(self.screen, (80, 80, 80), (int(p['x']), p['y']), p['size'])
    
    def draw(self):
        """绘制滚动效果"""
        # 填充背景
        self.screen.fill(DARK_GRAY)
        
        # 绘制噪点
        self.draw_noise()
        
        # 绘制半透明遮罩层（强化焦点）
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))  # 半透明黑色
        self.screen.blit(overlay, (0, 0))
        
        # 绘制滚动条区域
        start_idx = int(self.scroll_x // self.item_width)
        offset_x = self.scroll_x % self.item_width
        
        # 计算可见区域的起始和结束索引
        visible_start = start_idx
        visible_end = start_idx + VISIBLE_ITEMS + 2  # 多渲染两个以平滑边缘
        
        for i in range(visible_start, min(visible_end, len(self.sequence))):
            # 计算位置
            x = POINTER_POS - offset_x + (i - start_idx) * self.item_width - self.item_width // 2
            if x < -self.item_width or x > SCREEN_WIDTH + self.item_width:
                continue
            
            # 获取名字表面
            name_surf = self.name_surfaces[i]
            
            # 高亮当前在指针附近的名字
            name_center_x = x + name_surf.get_width() // 2
            distance_to_pointer = abs(name_center_x - POINTER_POS)
            
            # 根据距离调整亮度和大小
            if distance_to_pointer < self.item_width:
                # 靠近指针的变亮、变大
                factor = 1 - (distance_to_pointer / self.item_width) * 0.5
                scale = 1.0 + (1 - distance_to_pointer / self.item_width) * 0.3
                new_width = int(name_surf.get_width() * scale)
                new_height = int(name_surf.get_height() * scale)
                if new_width > 0 and new_height > 0:
                    scaled_surf = pygame.transform.smoothscale(name_surf, (new_width, new_height))
                    # 亮度调整
                    brightness = int(150 + 105 * factor)
                    brightness = max(0, min(255, brightness))
                    # 创建彩色副本
                    color_surf = scaled_surf.copy()
                    color_surf.fill((brightness, brightness, brightness), special_flags=pygame.BLEND_RGB_MULT)
                    self.screen.blit(color_surf, (x - (new_width - name_surf.get_width())//2, SCREEN_HEIGHT//2 - new_height//2))
            else:
                # 远处的变暗
                dark_surf = name_surf.copy()
                dark_surf.fill((100, 100, 100), special_flags=pygame.BLEND_RGB_MULT)
                self.screen.blit(dark_surf, (x, SCREEN_HEIGHT//2 - name_surf.get_height()//2))
        
        # 绘制中间的指针（金色三角形）
        pointer_points = [
            (POINTER_POS - 20, SCREEN_HEIGHT//2 - 70),
            (POINTER_POS + 20, SCREEN_HEIGHT//2 - 70),
            (POINTER_POS, SCREEN_HEIGHT//2 - 40)
        ]
        pygame.draw.polygon(self.screen, GOLD, pointer_points)
        pygame.draw.polygon(self.screen, WHITE, pointer_points, 3)
        
        # 绘制指示线
        pygame.draw.line(self.screen, GOLD, (POINTER_POS, SCREEN_HEIGHT//2 - 80), (POINTER_POS, SCREEN_HEIGHT//2 + 80), 3)
        
        # 如果停止，在底部显示结果
        if not self.is_rolling and self.result_name:
            result_text = f"点名结果: {self.result_name}"
            result_surf = self.small_font.render(result_text, True, GOLD)
            text_rect = result_surf.get_rect(center=(POINTER_POS, SCREEN_HEIGHT - 50))
            # 背景框
            bg_rect = text_rect.copy()
            bg_rect.inflate_ip(20, 10)
            pygame.draw.rect(self.screen, BLACK, bg_rect)
            pygame.draw.rect(self.screen, GOLD, bg_rect, 3)
            self.screen.blit(result_surf, text_rect)
    
    def handle_event(self, event):
        """处理事件，例如空格键开始/停止"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if self.is_rolling:
                    self.trigger_stop()
                else:
                    self.start_roll()
            elif event.key == pygame.K_r:
                self.start_roll()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # 左键
                if self.is_rolling:
                    self.trigger_stop()
                else:
                    self.start_roll()

def main():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("CS开箱风格班级点名器")
    clock = pygame.time.Clock()
    
    roll_effect = CSRollEffect(NAMES, screen)
    roll_effect.start_roll()
    
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            roll_effect.handle_event(event)
        
        roll_effect.update()
        roll_effect.draw()
        
        # 显示操作提示
        font_hint = pygame.font.Font(None, 24)
        if roll_effect.is_rolling:
            hint = "按空格或点击左键停止"
        else:
            hint = "按空格或点击左键重新开始"
        hint_surf = font_hint.render(hint, True, GRAY)
        screen.blit(hint_surf, (20, 20))
        
        pygame.display.flip()
        clock.tick(FPS)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()