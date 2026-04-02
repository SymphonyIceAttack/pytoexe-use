
import ctypes
from ctypes import wintypes
import math
import time
import random

# Windows API常量
WS_OVERLAPPEDWINDOW = 0xcf0000
WS_VISIBLE = 0x10000000
CW_USEDEFAULT = 0x80000000
WM_DESTROY = 2
WM_PAINT = 15
WM_KEYDOWN = 256
WM_KEYUP = 257
VK_LEFT = 37
VK_RIGHT = 39
VK_UP = 38
VK_DOWN = 40
VK_SPACE = 32
SRCCOPY = 0xCC0020

# 颜色定义
BLACK = 0x000000
WHITE = 0xFFFFFF
RED = 0xFF0000
BLUE = 0x0000FF
GREEN = 0x00FF00

# 游戏参数
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
PLAYER_SPEED = 5
ENEMY_SPEED = 3
BULLET_SPEED = 7

# 加载Windows DLL
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32
kernel32 = ctypes.windll.kernel32

# 定义结构体
class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.c_uint),
        ("lpfnWndProc", ctypes.WINFUNCTYPE(ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM)),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", wintypes.HINSTANCE),
        ("hIcon", wintypes.HICON),
        ("hCursor", wintypes.HCURSOR),
        ("hbrBackground", wintypes.HBRUSH),
        ("lpszMenuName", wintypes.LPCWSTR),
        ("lpszClassName", wintypes.LPCWSTR)
    ]

class PAINTSTRUCT(ctypes.Structure):
    _fields_ = [
        ("hdc", wintypes.HDC),
        ("fErase", wintypes.BOOL),
        ("rcPaint", wintypes.RECT),
        ("fRestore", wintypes.BOOL),
        ("fIncUpdate", wintypes.BOOL),
        ("rgbReserved", ctypes.c_byte * 32)
    ]

class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

# 全局变量
hwnd_main = None
player_x = WINDOW_WIDTH // 2
player_y = WINDOW_HEIGHT - 100
bullets = []
enemies = []
score = 0
keys_pressed = set()
game_running = True

# 游戏对象类
class Bullet:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.active = True
    
    def update(self):
        self.y -= BULLET_SPEED
        if self.y < 0:
            self.active = False

class Enemy:
    def __init__(self):
        self.x = random.randint(50, WINDOW_WIDTH - 50)
        self.y = -50
        self.active = True
    
    def update(self):
        self.y += ENEMY_SPEED
        if self.y > WINDOW_HEIGHT:
            self.active = False

# 绘制函数
def draw_rectangle(hdc, x, y, width, height, color):
    brush = gdi32.CreateSolidBrush(color)
    old_brush = gdi32.SelectObject(hdc, brush)
    rect = wintypes.RECT(x, y, x + width, y + height)
    gdi32.Rectangle(hdc, rect.left, rect.top, rect.right, rect.bottom)
    gdi32.SelectObject(hdc, old_brush)
    gdi32.DeleteObject(brush)

def draw_circle(hdc, x, y, radius, color):
    brush = gdi32.CreateSolidBrush(color)
    old_brush = gdi32.SelectObject(hdc, brush)
    gdi32.Ellipse(hdc, x - radius, y - radius, x + radius, y + radius)
    gdi32.SelectObject(hdc, old_brush)
    gdi32.DeleteObject(brush)

def draw_player(hdc, x, y):
    # 绘制玩家飞机主体
    draw_rectangle(hdc, x - 15, y - 10, 30, 20, BLUE)
    # 绘制机翼
    draw_rectangle(hdc, x - 25, y - 5, 10, 10, BLUE)
    draw_rectangle(hdc, x + 15, y - 5, 10, 10, BLUE)
    # 绘制尾翼
    draw_rectangle(hdc, x - 5, y + 10, 10, 15, BLUE)

def draw_enemy(hdc, x, y):
    # 绘制敌机
    draw_rectangle(hdc, x - 12, y - 8, 24, 16, RED)
    draw_rectangle(hdc, x - 20, y - 3, 8, 6, RED)
    draw_rectangle(hdc, x + 12, y - 3, 8, 6, RED)

def draw_bullet(hdc, x, y):
    # 绘制子弹
    draw_circle(hdc, x, y, 3, GREEN)

def draw_score(hdc):
    # 绘制分数
    score_text = f"Score: {score}"
    gdi32.SetTextColor(hdc, WHITE)
    gdi32.SetBkMode(hdc, 1)
    rect = wintypes.RECT(10, 10, 200, 40)
    user32.DrawTextW(hdc, score_text, len(score_text), ctypes.byref(rect), 0)

def draw_game_over(hdc):
    game_over_text = "GAME OVER"
    restart_text = "Press R to Restart or ESC to Exit"
    gdi32.SetTextColor(hdc, RED)
    gdi32.SetBkMode(hdc, 1)
    
    rect1 = wintypes.RECT(WINDOW_WIDTH//2-100, WINDOW_HEIGHT//2-50, WINDOW_WIDTH//2+100, WINDOW_HEIGHT//2-10)
    rect2 = wintypes.RECT(WINDOW_WIDTH//2-150, WINDOW_HEIGHT//2, WINDOW_WIDTH//2+150, WINDOW_HEIGHT//2+40)
    
    user32.DrawTextW(hdc, game_over_text, len(game_over_text), ctypes.byref(rect1), 0x00000001)
    user32.DrawTextW(hdc, restart_text, len(restart_text), ctypes.byref(rect2), 0x00000001)

# 游戏逻辑更新
def update_game():
    global player_x, player_y, bullets, enemies, score, game_running
    
    if not game_running:
        return
    
    # 更新玩家位置
    if VK_LEFT in keys_pressed and player_x > 25:
        player_x -= PLAYER_SPEED
    if VK_RIGHT in keys_pressed and player_x < WINDOW_WIDTH - 25:
        player_x += PLAYER_SPEED
    if VK_UP in keys_pressed and player_y > 25:
        player_y -= PLAYER_SPEED
    if VK_DOWN in keys_pressed and player_y < WINDOW_HEIGHT - 25:
        player_y += PLAYER_SPEED
    
    # 更新子弹
    for bullet in bullets[:]:
        bullet.update()
        if not bullet.active:
            bullets.remove(bullet)
    
    # 更新敌人
    for enemy in enemies[:]:
        enemy.update()
        if not enemy.active:
            enemies.remove(enemy)
    
    # 生成新敌人
    if random.random() < 0.02:
        enemies.append(Enemy())
    
    # 碰撞检测 - 子弹击中敌人
    for bullet in bullets[:]:
        for enemy in enemies[:]:
            distance = math.sqrt((bullet.x - enemy.x)**2 + (bullet.y - enemy.y)**2)
            if distance < 20:
                if bullet in bullets:
                    bullets.remove(bullet)
                if enemy in enemies:
                    enemies.remove(enemy)
                score += 10
                break
    
    # 碰撞检测 - 敌人撞击玩家
    for enemy in enemies:
        distance = math.sqrt((player_x - enemy.x)**2 + (player_y - enemy.y)**2)
        if distance < 30:
            game_running = False
            break

# 窗口过程函数
def window_proc(hwnd, msg, wparam, lparam):
    global keys_pressed, game_running, player_x, player_y, bullets, enemies, score
    
    if msg == WM_DESTROY:
        user32.PostQuitMessage(0)
        return 0
    elif msg == WM_PAINT:
        ps = PAINTSTRUCT()
        hdc = user32.BeginPaint(hwnd, ctypes.byref(ps))
        
        # 填充黑色背景
        brush = gdi32.CreateSolidBrush(BLACK)
        rect = wintypes.RECT(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
        gdi32.FillRect(hdc, ctypes.byref(rect), brush)
        gdi32.DeleteObject(brush)
        
        if game_running:
            # 绘制游戏对象
            draw_player(hdc, player_x, player_y)
            
            for bullet in bullets:
                draw_bullet(hdc, bullet.x, bullet.y)
            
            for enemy in enemies:
                draw_enemy(hdc, enemy.x, enemy.y)
            
            draw_score(hdc)
        else:
            # 绘制游戏结束画面
            draw_game_over(hdc)
        
        user32.EndPaint(hwnd, ctypes.byref(ps))
        return 0
    elif msg == WM_KEYDOWN:
        keys_pressed.add(wparam)
        
        # 发射子弹
        if wparam == VK_SPACE and game_running:
            bullets.append(Bullet(player_x, player_y - 10))
        
        # 重新开始游戏
        if wparam == ord('R') and not game_running:
            reset_game()
        
        # 退出游戏
        if wparam == 27:  # ESC键
            user32.PostQuitMessage(0)
        return 0
    elif msg == WM_KEYUP:
        if wparam in keys_pressed:
            keys_pressed.remove(wparam)
        return 0
    
    return user32.DefWindowProcW(hwnd, msg, wparam, lparam)

def reset_game():
    global player_x, player_y, bullets, enemies, score, game_running
    player_x = WINDOW_WIDTH // 2
    player_y = WINDOW_HEIGHT - 100
    bullets = []
    enemies = []
    score = 0
    game_running = True

def main():
    global hwnd_main
    
    # 获取实例句柄
    hinstance = kernel32.GetModuleHandleW(None)
    
    # 注册窗口类
    wnd_class = WNDCLASS()
    wnd_class.style = 0
    wnd_class.lpfnWndProc = ctypes.WINFUNCTYPE(
        ctypes.c_long, wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM
    )(window_proc)
    wnd_class.cbClsExtra = 0
    wnd_class.cbWndExtra = 0
    wnd_class.hInstance = hinstance
    wnd_class.hIcon = None
    wnd_class.hCursor = user32.LoadCursorW(None, 32512)  # IDC_ARROW
    wnd_class.hbrBackground = gdi32.CreateSolidBrush(BLACK)
    wnd_class.lpszMenuName = None
    wnd_class.lpszClassName = "PlaneFightGame"
    
    atom = user32.RegisterClassW(ctypes.byref(wnd_class))
    if not atom:
        print("Failed to register window class")
        return
    
    # 创建窗口
    hwnd_main = user32.CreateWindowExW(
        0,
        "PlaneFightGame",
        "飞机大战游戏 - ctypes版",
        WS_OVERLAPPEDWINDOW | WS_VISIBLE,
        CW_USEDEFAULT, CW_USEDEFAULT,
        WINDOW_WIDTH, WINDOW_HEIGHT,
        None, None, hinstance, None
    )
    
    if not hwnd_main:
        print("Failed to create window")
        return
    
    # 显示窗口
    user32.ShowWindow(hwnd_main, 1)
    user32.UpdateWindow(hwnd_main)
    
    # 游戏主循环
    last_time = time.time()
    msg = wintypes.MSG()
    
    while True:
        # 处理Windows消息
        if user32.PeekMessageW(ctypes.byref(msg), None, 0, 0, 1):  # PM_REMOVE
            if msg.message == WM_QUIT:
                break
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        
        # 控制帧率并更新游戏
        current_time = time.time()
        if current_time - last_time >= 1/60:  # 60 FPS
            update_game()
            user32.InvalidateRect(hwnd_main, None, True)
            last_time = current_time

if __name__ == "__main__":
    main()
