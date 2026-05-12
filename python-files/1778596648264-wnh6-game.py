"""
数字锁匠 CTF题目
运行: python game.py
"""
import pygame
import os
import sys

# ============ 从图片提取flag ============
def get_flag():
    try:
        if getattr(sys, 'frozen', False):
            path = os.path.join(sys._MEIPASS, 'assets', 'bg.png')
        else:
            path = os.path.join(os.path.dirname(__file__), 'assets', 'bg.png')
        
        with open(path, 'rb') as f:
            data = f.read()
        
        marker = b'\x00\x00\x00\x00'
        start = data.rfind(marker, 0, len(data)-4) + 4
        end = data.rfind(marker, start)
        
        if start > 3 and end > start:
            return data[start:end].decode()
    except:
        pass
    return None

# ============ 游戏主体 ============
pygame.init()
screen = pygame.display.set_mode((400, 300))
pygame.display.set_caption("数字锁匠")

font_big = pygame.font.SysFont("simsun", 24)
font_small = pygame.font.SysFont("simsun", 14)
clock = pygame.time.Clock()

score = 0
show_flag = False
flag_text = ""

FAKE_FLAG = "flag{f4k3_fl4g_g0tch4}"

running = True
while running:
    screen.fill((20, 20, 50))
    
    # 标题
    title = font_big.render("数字锁匠", True, (255, 200, 50))
    screen.blit(title, (140, 30))
    
    # 分数
    score_text = font_big.render(f"分数: {score}", True, (255, 255, 255))
    screen.blit(score_text, (140, 100))
    
    # 提示
    hint = font_small.render("按 空格键 得分 按 R 重置", True, (150, 150, 150))
    screen.blit(hint, (110, 160))
    
    # 显示flag
    if show_flag:
        color = (0, 255, 0) if flag_text != FAKE_FLAG else (255, 100, 100)
        flag_display = font_big.render(flag_text, True, color)
        screen.blit(flag_display, (30, 220))
    
    # 事件处理
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                score += 10
            
            elif event.key == pygame.K_RETURN:
                # 检查分数是否刚好13140
                if score == 13140:
                    real_flag = get_flag()
                    flag_text = real_flag if real_flag else FAKE_FLAG
                else:
                    flag_text = FAKE_FLAG
                show_flag = True
            
            elif event.key == pygame.K_r:
                score = 0
                show_flag = False
                flag_text = ""
    
    pygame.display.flip()
    clock.tick(60)

pygame.quit()