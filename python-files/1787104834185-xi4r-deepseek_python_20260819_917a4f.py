# -*- coding: utf-8 -*-
"""
抖音同款 - 3D粒子玫瑰花束
在桌面绽放并缓慢旋转的粒子玫瑰
使用 Pygame + 3D 粒子系统
"""

import pygame
import math
import random
import sys
import os

# ============ 配置参数 ============
PARTICLE_COUNT = 7000          # 粒子总数
NUM_LAYERS = 35               # 花瓣层数
MAX_RADIUS = 220              # 最大半径
MAX_HEIGHT = 280              # 最大高度
ROSE_K = 4                    # 玫瑰线参数 (4瓣玫瑰)
ANIMATION_DURATION = 3.5      # 绽放动画持续时间 (秒)
ROTATION_SPEED = 0.3          # 旋转速度 (度/帧)
PARTICLE_MIN_SIZE = 2         # 粒子最小尺寸
PARTICLE_MAX_SIZE = 4         # 粒子最大尺寸
STAR_COUNT = 150              # 背景星星数量
FPS = 60                      # 帧率

# 颜色配置
COLOR_DARK_RED = (160, 20, 30)
COLOR_RED = (220, 40, 60)
COLOR_PINK = (255, 120, 160)
COLOR_LIGHT_PINK = (255, 180, 210)
COLOR_GOLD = (255, 215, 80)
COLOR_YELLOW = (255, 240, 150)
COLOR_GREEN = (50, 200, 80)
COLOR_DARK_GREEN = (20, 120, 50)


class Particle:
    """单个粒子"""
    def __init__(self, end_x, end_y, end_z, color, size):
        # 结束位置 (在玫瑰上的位置)
        self.end_x = end_x
        self.end_y = end_y
        self.end_z = end_z
        
        # 起始位置 (中心附近，用于绽放动画)
        angle = random.uniform(0, 2 * math.pi)
        dist = random.uniform(0, 30)
        self.start_x = dist * math.cos(angle)
        self.start_y = dist * math.sin(angle)
        self.start_z = random.uniform(-20, 20)
        
        # 当前插值位置
        self.x = self.start_x
        self.y = self.start_y
        self.z = self.start_z
        
        # 颜色和大小
        self.color = color
        self.size = size
        
        # 每个粒子有轻微的动画延迟，让绽放更有层次感
        self.delay = random.uniform(0, 0.3)
        
        # 小的随机浮动偏移 (让粒子在最终位置上有细微运动)
        self.float_offset_x = random.uniform(-0.5, 0.5)
        self.float_offset_y = random.uniform(-0.5, 0.5)
        self.float_offset_z = random.uniform(-0.5, 0.5)
        self.float_speed = random.uniform(0.2, 0.8)
        self.float_phase = random.uniform(0, 2 * math.pi)
    
    def update(self, progress, time):
        """更新粒子位置"""
        # 计算绽放进度 (带延迟)
        p = max(0, min(1, (progress - self.delay) / (1 - self.delay)))
        # 使用缓动函数让动画更平滑 (ease-out cubic)
        if p < 1:
            eased = 1 - (1 - p) ** 3
        else:
            eased = 1
        
        # 插值位置
        self.x = self.start_x + (self.end_x - self.start_x) * eased
        self.y = self.start_y + (self.end_y - self.start_y) * eased
        self.z = self.start_z + (self.end_z - self.start_z) * eased
        
        # 添加微小的浮动 (让粒子有呼吸感)
        float_phase = time * self.float_speed + self.float_phase
        float_scale = 0.3 * (1 - eased * 0.7)  # 绽放后浮动幅度减小
        self.x += math.sin(float_phase) * self.float_offset_x * float_scale
        self.y += math.cos(float_phase * 1.3) * self.float_offset_y * float_scale
        self.z += math.sin(float_phase * 0.7 + 1.2) * self.float_offset_z * float_scale


def generate_rose_particles():
    """生成玫瑰粒子数据"""
    particles = []
    particles_per_layer = PARTICLE_COUNT // NUM_LAYERS
    
    for layer in range(NUM_LAYERS):
        t = layer / NUM_LAYERS  # 0 ~ 1
        
        # 层参数
        height = t * MAX_HEIGHT - 60  # -60 ~ 220
        scale = 1 - t * 0.65  # 1 ~ 0.35
        phase_offset = t * 0.6  # 相位偏移，让花瓣螺旋排列
        
        # 颜色渐变: 底部深红 -> 中部红 -> 顶部粉红
        r = int(160 + 95 * t)
        g = int(30 + 150 * t * t)
        b = int(40 + 180 * t * t)
        
        # 层内粒子分布
        for i in range(particles_per_layer):
            # 角度: 在层内均匀分布 + 随机扰动
            theta = (i / particles_per_layer) * 2 * math.pi
            theta += random.uniform(-0.08, 0.08) * (1 - t * 0.5)
            
            # 玫瑰线半径: r = A * cos(k * theta + phase)
            # 加上随机扰动使花瓣更自然
            rose_r = math.cos(ROSE_K * theta + phase_offset)
            # 让花瓣形状更饱满
            rose_r = abs(rose_r) ** 0.8 * (1 if rose_r > 0 else -1)
            # 径向位置随机分布，让粒子填充花瓣内部
            r_ratio = random.uniform(0.4, 1.0) ** 0.7
            r = MAX_RADIUS * rose_r * scale * r_ratio
            
            # 计算3D坐标
            x = r * math.cos(theta)
            y = r * math.sin(theta)
            z = height + random.uniform(-8, 8)
            
            # 根据径向位置微调颜色 (边缘更亮)
            edge_factor = 0.6 + 0.4 * r_ratio
            cr = int(min(255, r * edge_factor))
            cg = int(min(255, g * edge_factor * 0.9))
            cb = int(min(255, b * edge_factor * 0.9))
            
            # 花瓣内部颜色偏深，边缘偏亮
            color = (cr, cg, cb)
            
            # 粒子大小: 根据层和径向位置变化
            size_base = PARTICLE_MIN_SIZE + (PARTICLE_MAX_SIZE - PARTICLE_MIN_SIZE) * (1 - t * 0.5)
            size = size_base * (0.7 + 0.3 * r_ratio)
            size = max(PARTICLE_MIN_SIZE, min(PARTICLE_MAX_SIZE, size))
            
            particles.append(Particle(x, y, z, color, size))
    
    # ===== 生成花蕊 (金色粒子) =====
    stamen_count = 300
    for i in range(stamen_count):
        theta = random.uniform(0, 2 * math.pi)
        r = random.uniform(0, 35) * random.uniform(0.3, 1.0)
        x = r * math.cos(theta)
        y = r * math.sin(theta)
        z = random.uniform(-15, 40)
        
        # 金色渐变
        brightness = 0.6 + 0.4 * random.random()
        color = (
            int(255 * brightness),
            int(215 * brightness),
            int(80 * brightness)
        )
        size = random.uniform(1.5, 3.5)
        particles.append(Particle(x, y, z, color, size))
    
    # ===== 生成花茎 (绿色粒子) =====
    stem_count = 400
    for i in range(stem_count):
        t = random.uniform(0, 1)
        height = -60 - t * 180  # -60 ~ -240
        r = random.uniform(0, 25) * (1 - t * 0.7)
        theta = random.uniform(0, 2 * math.pi)
        x = r * math.cos(theta) * 0.3
        y = r * math.sin(theta) * 0.3
        z = height + random.uniform(-5, 5)
        
        # 绿色渐变
        green_val = int(120 + 80 * (1 - t))
        color = (
            int(30 + 30 * (1 - t)),
            green_val,
            int(50 + 40 * (1 - t))
        )
        size = random.uniform(1.5, 3.0)
        particles.append(Particle(x, y, z, color, size))
    
    return particles


def generate_stars():
    """生成背景星星"""
    stars = []
    for _ in range(STAR_COUNT):
        x = random.uniform(-1, 1)
        y = random.uniform(-1, 1)
        # 避免星星在玫瑰区域太密集
        if abs(x) < 0.3 and abs(y) < 0.3:
            x = random.choice([-1, 1]) * random.uniform(0.4, 1)
            y = random.choice([-1, 1]) * random.uniform(0.4, 1)
        size = random.uniform(0.5, 1.8)
        brightness = random.uniform(100, 255)
        twinkle_speed = random.uniform(0.5, 2.0)
        twinkle_phase = random.uniform(0, 2 * math.pi)
        stars.append({
            'x': x, 'y': y, 
            'size': size, 
            'brightness': brightness,
            'speed': twinkle_speed,
            'phase': twinkle_phase
        })
    return stars


def project_point(x, y, z, rot_angle, screen_w, screen_h, fov=500):
    """将3D点投影到2D屏幕"""
    # 绕Y轴旋转
    cos_a = math.cos(math.radians(rot_angle))
    sin_a = math.sin(math.radians(rot_angle))
    rx = x * cos_a + z * sin_a
    rz = -x * sin_a + z * cos_a
    ry = y
    
    # 透视投影
    if rz < -fov:
        rz = -fov + 1
    scale = fov / (fov + rz)
    px = rx * scale + screen_w / 2
    py = -ry * scale + screen_h / 2
    
    return px, py, scale, rz


def main():
    """主函数"""
    # 初始化Pygame
    pygame.init()
    
    # 获取屏幕信息，创建全屏窗口
    info = pygame.display.Info()
    screen_w = info.current_w
    screen_h = info.current_h
    
    # 创建全屏窗口 (带边框，方便退出)
    screen = pygame.display.set_mode((screen_w, screen_h), pygame.FULLSCREEN)
    pygame.display.set_caption("✨ 粒子玫瑰花束 - 按 ESC 退出")
    
    # 隐藏鼠标
    pygame.mouse.set_visible(False)
    
    clock = pygame.time.Clock()
    
    # 生成粒子
    print("正在生成粒子玫瑰...")
    particles = generate_rose_particles()
    print(f"生成 {len(particles)} 个粒子")
    
    # 生成星星
    stars = generate_stars()
    
    # 动画状态
    start_time = pygame.time.get_ticks() / 1000.0
    rotation_angle = 0
    running = True
    
    # 创建用于批量绘制的surface (提高性能)
    # 使用全屏尺寸的surface作为缓存
    particle_surface = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
    
    print("按 ESC 退出程序")
    
    # 主循环
    while running:
        current_time = pygame.time.get_ticks() / 1000.0
        elapsed = current_time - start_time
        
        # ===== 事件处理 =====
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                # 按 R 键重置动画
                elif event.key == pygame.K_r:
                    start_time = current_time
                    rotation_angle = 0
        
        # ===== 计算动画进度 =====
        progress = min(1.0, elapsed / ANIMATION_DURATION)
        
        # ===== 更新粒子 =====
        for p in particles:
            p.update(progress, current_time)
        
        # ===== 更新旋转角度 =====
        # 绽放过程中旋转速度稍慢，绽放后正常
        speed_factor = 0.3 + 0.7 * progress
        rotation_angle += ROTATION_SPEED * speed_factor
        if rotation_angle > 360:
            rotation_angle -= 360
        
        # ===== 渲染 =====
        # 清空背景 (黑色)
        screen.fill((0, 0, 0))
        
        # 绘制背景星星 (带闪烁)
        for star in stars:
            twinkle = 0.5 + 0.5 * math.sin(current_time * star['speed'] + star['phase'])
            brightness = int(star['brightness'] * (0.3 + 0.7 * twinkle))
            if brightness > 20:
                sx = (star['x'] * 0.5 + 0.5) * screen_w
                sy = (star['y'] * 0.5 + 0.5) * screen_h
                size = star['size'] * (0.5 + 0.5 * twinkle)
                pygame.draw.circle(screen, (brightness, brightness, brightness), 
                                  (int(sx), int(sy)), max(1, int(size)))
        
        # ===== 绘制粒子 (按深度排序) =====
        # 计算所有粒子的投影位置和深度
        projected = []
        for p in particles:
            px, py, scale, depth = project_point(p.x, p.y, p.z, rotation_angle, screen_w, screen_h)
            if depth > -200:  # 裁剪太远的粒子
                size = max(1, int(p.size * scale * 0.8))
                if size > 0:
                    projected.append((depth, px, py, size, p.color))
        
        # 按深度排序 (远->近)
        projected.sort(key=lambda x: x[0])
        
        # 批量绘制粒子
        for depth, px, py, size, color in projected:
            # 屏幕边界裁剪
            if px < -10 or px > screen_w + 10 or py < -10 or py > screen_h + 10:
                continue
            
            # 根据深度调整透明度 (远处的粒子半透明)
            alpha = 255
            if depth < -50:
                alpha = int(255 * (1 - (depth + 50) / 200))
                alpha = max(50, min(255, alpha))
            
            if alpha < 255:
                # 创建带透明度的颜色
                color_with_alpha = (*color, alpha)
                # 绘制半透明粒子
                pygame.draw.circle(screen, color, (int(px), int(py)), size)
            else:
                pygame.draw.circle(screen, color, (int(px), int(py)), size)
        
        # ===== 绘制绽放过程中的光晕效果 =====
        if progress < 1:
            # 在绽放过程中，中心有一个柔和的光晕
            glow_radius = int(50 + 150 * (1 - progress))
            glow_alpha = int(60 * (1 - progress))
            if glow_alpha > 5:
                glow_surf = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
                center = (glow_radius, glow_radius)
                for r in range(glow_radius, 0, -5):
                    a = int(glow_alpha * (1 - r / glow_radius))
                    pygame.draw.circle(glow_surf, (255, 100, 150, a), center, r)
                screen.blit(glow_surf, (screen_w//2 - glow_radius, screen_h//2 - glow_radius))
        
        # ===== 显示提示文字 =====
        if progress < 1:
            # 绽放进度提示
            font = pygame.font.Font(None, 36)
            text = f"绽放中... {int(progress * 100)}%"
            text_surf = font.render(text, True, (255, 255, 255, 150))
            text_rect = text_surf.get_rect(center=(screen_w//2, screen_h - 60))
            screen.blit(text_surf, text_rect)
        else:
            # 显示操作提示 (淡出)
            alpha = max(0, min(255, int(255 * (1 - (elapsed - ANIMATION_DURATION) / 2))))
            if alpha > 20:
                font = pygame.font.Font(None, 24)
                text = "ESC 退出  |  R 重新绽放"
                text_surf = font.render(text, True, (200, 200, 200, alpha))
                text_rect = text_surf.get_rect(center=(screen_w//2, screen_h - 40))
                screen.blit(text_surf, text_rect)
        
        # ===== 更新屏幕 =====
        pygame.display.flip()
        clock.tick(FPS)
    
    # 退出
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()