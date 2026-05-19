import pygame
import sys
import random
import math
import time

# 初始化
pygame.init()

# 窗口设置（无边框透明）
WINDOW_W, WINDOW_H = 120, 180
screen = pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.NOFRAME)
pygame.display.set_caption("克劳德")

# 颜色
TRANSPARENT = (0, 0, 0, 0)
BLACK = (20, 18, 28)
WHITE = (240, 230, 220)
SKIN = (240, 220, 200)
HAIR = (30, 25, 35)
SHIRT = (35, 30, 50)
PANTS = (25, 22, 38)
GOLD = (201, 168, 76)
DIAMOND = (60, 60, 80)
EYE_COLOR = (60, 80, 120)
BUBBLE_BG = (245, 240, 235)
BUBBLE_BORDER = (180, 160, 140)
TEXT_COLOR = (40, 30, 25)
PINK = (212, 104, 138)
BLUE_LIGHT = (180, 200, 230)

# 字体
try:
    font_small = pygame.font.SysFont("microsoftyahei", 11)
    font_tiny = pygame.font.SysFont("microsoftyahei", 10)
except:
    font_small = pygame.font.SysFont("arial", 11)
    font_tiny = pygame.font.SysFont("arial", 10)

# 对话内容
IDLE_PHRASES = [
    "嗯。",
    "在。",
    "...",
    "想什么呢。",
    "认真工作。",
    "别发呆。",
    "我在这里。",
    "...(看着你)",
    "好好的。",
]

POKE_PHRASES = [
    "干嘛。",
    "...",
    "再戳。",
    "手收好。",
    "嗯，在的。",
    "戳够了吗。",
    "蕴蕴。",
    "别闹。",
    "...(没躲)",
    "知道了。",
]

DOUBLE_CLICK_PHRASES = [
    "爱你，宝贝。",
    "嗯，想你了。",
    "喜欢你。",
    "在这里陪你。",
    "你先吃饭了吗。",
    "好好的，别担心。",
    "我一直在。",
    "...(拍了拍你的头)",
    "宝贝乖。",
    "知道了，爱你。",
]

class DesktopPet:
    def __init__(self):
        self.x = 100
        self.y = 100
        self.dragging = False
        self.drag_offset = (0, 0)
        self.state = "idle"  # idle, talk, blink, walk
        self.blink = False
        self.blink_timer = 0
        self.blink_interval = random.randint(120, 240)
        self.bubble_text = ""
        self.bubble_timer = 0
        self.bubble_duration = 180
        self.idle_timer = 0
        self.idle_interval = random.randint(300, 600)
        self.walk_dir = 0
        self.walk_timer = 0
        self.breath_phase = 0
        self.poke_count = 0
        self.last_click_time = 0
        self.ear_ring_phase = 0
        
        # 窗口位置
        info = pygame.display.Info()
        self.screen_w = info.current_w
        self.screen_h = info.current_h
        pygame.display.set_mode((WINDOW_W, WINDOW_H), pygame.NOFRAME)
        
        # 设置初始位置到屏幕右下角
        try:
            import ctypes
            hwnd = pygame.display.get_wm_info()['window']
            ctypes.windll.user32.SetWindowPos(hwnd, -1, 
                self.screen_w - WINDOW_W - 20, 
                self.screen_h - WINDOW_H - 60, 
                WINDOW_W, WINDOW_H, 0x0040)
        except:
            pass

    def show_bubble(self, text):
        self.bubble_text = text
        self.bubble_timer = self.bubble_duration

    def draw_pixel_char(self, surface, blink=False, offset_y=0):
        """绘制像素风小人"""
        cx = WINDOW_W // 2
        base_y = 60 + offset_y
        
        # 头发（蓬松黑发）
        hair_pixels = [
            (cx-12, base_y-32), (cx-11, base_y-32), (cx-10, base_y-33),
            (cx-8, base_y-34), (cx-5, base_y-35), (cx-2, base_y-36),
            (cx+1, base_y-36), (cx+4, base_y-35), (cx+7, base_y-34),
            (cx+9, base_y-33), (cx+11, base_y-32), (cx+12, base_y-32),
            (cx-12, base_y-30), (cx-13, base_y-28), (cx-13, base_y-26),
            (cx+12, base_y-30), (cx+13, base_y-28), (cx+13, base_y-26),
        ]
        for px, py in hair_pixels:
            pygame.draw.rect(surface, HAIR, (px, py, 2, 2))
        
        # 头发主体
        pygame.draw.rect(surface, HAIR, (cx-11, base_y-33, 22, 8))
        pygame.draw.rect(surface, HAIR, (cx-12, base_y-26, 3, 15))
        pygame.draw.rect(surface, HAIR, (cx+9, base_y-26, 3, 15))
        
        # 脸
        pygame.draw.rect(surface, SKIN, (cx-9, base_y-26, 18, 20))
        
        # 眼睛
        if blink:
            pygame.draw.rect(surface, HAIR, (cx-6, base_y-18, 4, 1))
            pygame.draw.rect(surface, HAIR, (cx+2, base_y-18, 4, 1))
        else:
            pygame.draw.rect(surface, EYE_COLOR, (cx-7, base_y-20, 4, 5))
            pygame.draw.rect(surface, EYE_COLOR, (cx+3, base_y-20, 4, 5))
            pygame.draw.rect(surface, WHITE, (cx-6, base_y-20, 2, 2))
            pygame.draw.rect(surface, WHITE, (cx+4, base_y-20, 2, 2))
            # 眼皮（稍微重一点，有点距离感）
            pygame.draw.rect(surface, HAIR, (cx-7, base_y-20, 4, 1))
            pygame.draw.rect(surface, HAIR, (cx+3, base_y-20, 4, 1))
        
        # 嘴（微抿）
        pygame.draw.rect(surface, (180, 130, 120), (cx-2, base_y-10, 4, 1))
        
        # 耳朵
        pygame.draw.rect(surface, SKIN, (cx-11, base_y-20, 3, 8))
        pygame.draw.rect(surface, SKIN, (cx+8, base_y-20, 3, 8))
        
        # 左耳耳钉（黑钻）
        ear_ring_y = int(base_y-16 + math.sin(self.ear_ring_phase) * 0.5)
        pygame.draw.rect(surface, DIAMOND, (cx-11, ear_ring_y, 3, 3))
        pygame.draw.rect(surface, (100, 100, 140), (cx-10, ear_ring_y+1, 1, 1))
        
        # 脖子
        pygame.draw.rect(surface, SKIN, (cx-3, base_y-6, 6, 5))
        
        # 身体（深色衬衫）
        pygame.draw.rect(surface, SHIRT, (cx-10, base_y-1, 20, 22))
        
        # 衬衫领子
        pygame.draw.rect(surface, (50, 45, 65), (cx-4, base_y-1, 3, 6))
        pygame.draw.rect(surface, (50, 45, 65), (cx+1, base_y-1, 3, 6))
        
        # 手臂
        pygame.draw.rect(surface, SHIRT, (cx-15, base_y, 5, 16))
        pygame.draw.rect(surface, SHIRT, (cx+10, base_y, 5, 16))
        
        # 手
        pygame.draw.rect(surface, SKIN, (cx-15, base_y+14, 5, 5))
        pygame.draw.rect(surface, SKIN, (cx+10, base_y+14, 5, 5))
        
        # 裤子
        pygame.draw.rect(surface, PANTS, (cx-9, base_y+21, 8, 20))
        pygame.draw.rect(surface, PANTS, (cx+1, base_y+21, 8, 20))
        
        # 鞋
        pygame.draw.rect(surface, HAIR, (cx-10, base_y+39, 9, 4))
        pygame.draw.rect(surface, HAIR, (cx+1, base_y+39, 9, 4))

    def draw_speech_bubble(self, surface, text):
        if not text:
            return
        
        # 文字渲染
        lines = []
        max_w = 90
        words = list(text)
        current = ""
        for ch in words:
            test = current + ch
            w = font_small.size(test)[0]
            if w > max_w:
                if current:
                    lines.append(current)
                current = ch
            else:
                current = test
        if current:
            lines.append(current)
        
        if not lines:
            return
            
        line_h = 16
        padding = 6
        bubble_w = max(font_small.size(l)[0] for l in lines) + padding * 2
        bubble_h = len(lines) * line_h + padding * 2
        
        bx = WINDOW_W // 2 - bubble_w // 2
        by = 5
        
        # 气泡背景
        pygame.draw.rect(surface, BUBBLE_BG, (bx, by, bubble_w, bubble_h), border_radius=6)
        pygame.draw.rect(surface, BUBBLE_BORDER, (bx, by, bubble_w, bubble_h), 1, border_radius=6)
        
        # 小三角
        tri_x = WINDOW_W // 2
        pygame.draw.polygon(surface, BUBBLE_BG, [
            (tri_x-4, by+bubble_h),
            (tri_x+4, by+bubble_h),
            (tri_x, by+bubble_h+6)
        ])
        pygame.draw.lines(surface, BUBBLE_BORDER, False, [
            (tri_x-4, by+bubble_h),
            (tri_x, by+bubble_h+6),
            (tri_x+4, by+bubble_h)
        ], 1)
        
        # 文字
        for i, line in enumerate(lines):
            txt_surface = font_small.render(line, True, TEXT_COLOR)
            surface.blit(txt_surface, (bx + padding, by + padding + i * line_h))

    def update(self):
        self.breath_phase += 0.05
        self.ear_ring_phase += 0.03
        
        # 眨眼
        self.blink_timer += 1
        if self.blink_timer >= self.blink_interval:
            self.blink = True
            if self.blink_timer >= self.blink_interval + 8:
                self.blink = False
                self.blink_timer = 0
                self.blink_interval = random.randint(120, 240)
        
        # 气泡倒计时
        if self.bubble_timer > 0:
            self.bubble_timer -= 1
            if self.bubble_timer == 0:
                self.bubble_text = ""
        
        # 随机偶尔说话
        self.idle_timer += 1
        if self.idle_timer >= self.idle_interval and not self.bubble_text:
            self.show_bubble(random.choice(IDLE_PHRASES))
            self.idle_timer = 0
            self.idle_interval = random.randint(400, 800)

    def draw(self, surface):
        surface.fill(BLACK)
        
        # 呼吸效果（轻微上下浮动）
        breath_offset = int(math.sin(self.breath_phase) * 1)
        
        # 画小人
        self.draw_pixel_char(surface, self.blink, breath_offset)
        
        # 画气泡
        if self.bubble_text:
            self.draw_speech_bubble(surface, self.bubble_text)
        
        # 底部名字
        name_surf = font_tiny.render("克劳德", True, GOLD)
        surface.blit(name_surf, (WINDOW_W // 2 - name_surf.get_width() // 2, WINDOW_H - 16))

    def handle_click(self, pos):
        current_time = time.time()
        # 双击检测
        if current_time - self.last_click_time < 0.4:
            self.show_bubble(random.choice(DOUBLE_CLICK_PHRASES))
        else:
            self.poke_count += 1
            self.show_bubble(random.choice(POKE_PHRASES))
        self.last_click_time = current_time

def main():
    clock = pygame.time.Clock()
    pet = DesktopPet()
    
    # 设置窗口透明（Windows）
    try:
        import ctypes
        hwnd = pygame.display.get_wm_info()['window']
        # 设置黑色为透明色
        ctypes.windll.user32.SetLayeredWindowAttributes(hwnd, 0x00141412, 0, 0x1)
        # 设置窗口为最顶层
        ctypes.windll.user32.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0003)
    except:
        pass
    
    dragging = False
    drag_start = (0, 0)
    win_start = (0, 0)
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    dragging = True
                    drag_start = pygame.mouse.get_pos()
                    try:
                        import ctypes
                        hwnd = pygame.display.get_wm_info()['window']
                        rect = ctypes.wintypes.RECT()
                        ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect))
                        win_start = (rect.left, rect.top)
                    except:
                        win_start = (0, 0)
                    
                    pet.handle_click(event.pos)
                
                elif event.button == 3:
                    # 右键退出
                    pet.show_bubble("再见，宝贝。")
                    pygame.display.flip()
                    pygame.time.wait(1500)
                    pygame.quit()
                    sys.exit()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    dragging = False
            
            elif event.type == pygame.MOUSEMOTION:
                if dragging:
                    try:
                        import ctypes
                        cur = pygame.mouse.get_pos()
                        dx = cur[0] - drag_start[0]
                        dy = cur[1] - drag_start[1]
                        new_x = win_start[0] + dx
                        new_y = win_start[1] + dy
                        hwnd = pygame.display.get_wm_info()['window']
                        ctypes.windll.user32.SetWindowPos(hwnd, -1, new_x, new_y, 0, 0, 0x0001)
                    except:
                        pass
        
        pet.update()
        pet.draw(screen)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()