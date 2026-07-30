#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
黑洞桌宠 - Black Hole Desktop Pet
一个可爱的黑洞桌面宠物，带旋转吸积盘和粒子吞噬特效
运行环境：Windows / macOS / Linux  (Python 3.8+)
"""

import tkinter as tk
import math
import random
import sys

# ==================== 配置参数 ====================
WINDOW_SIZE = 200          # 窗口大小（正方形）
BLACKHOLE_RADIUS = 30      # 黑洞本体半径
ACCRETION_INNER = 35       # 吸积盘内半径
ACCRETION_OUTER = 65       # 吸积盘外半径
PARTICLE_COUNT = 40        # 粒子数量
ROTATION_SPEED = 0.02      # 吸积盘旋转速度
GRAVITY_STRENGTH = 0.8     # 引力强度
ALWAYS_ON_TOP = True       # 是否始终置顶
TRANSPARENT_COLOR = 'magenta'  # 透明色（magenta在Windows下可做透明键）

# 颜色配置
COLORS = {
    'bg': TRANSPARENT_COLOR,
    'blackhole_center': '#000000',
    'blackhole_edge': '#1a0033',
    'accretion_hot': '#ff6600',
    'accretion_warm': '#ffaa00',
    'accretion_cool': '#ff3366',
    'particle': ['#ffffff', '#ffeecc', '#ffcc66', '#ff9933', '#ff6600'],
    'glow': '#4400aa',
}


class Particle:
    """被黑洞吸引的粒子"""
    def __init__(self, canvas, center_x, center_y):
        self.canvas = canvas
        self.cx = center_x
        self.cy = center_y
        self.reset()
        self.id = canvas.create_oval(0, 0, 0, 0, fill=self.color, outline='')

    def reset(self):
        """重置粒子到外圈随机位置"""
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(ACCRETION_OUTER + 10, WINDOW_SIZE // 2 - 5)
        self.x = self.cx + math.cos(angle) * distance
        self.y = self.cy + math.sin(angle) * distance
        self.vx = -math.sin(angle) * random.uniform(0.5, 1.5)
        self.vy = math.cos(angle) * random.uniform(0.5, 1.5)
        self.size = random.uniform(1.5, 3.5)
        self.color = random.choice(COLORS['particle'])
        self.alpha = random.uniform(0.6, 1.0)
        self.alive = True

    def update(self):
        """更新粒子位置（引力下落）"""
        if not self.alive:
            return

        # 计算到黑洞中心的方向
        dx = self.cx - self.x
        dy = self.cy - self.y
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < BLACKHOLE_RADIUS:
            # 被黑洞吞噬
            self.alive = False
            return

        # 引力加速度
        force = GRAVITY_STRENGTH * 100 / (dist * dist + 10)
        self.vx += (dx / dist) * force
        self.vy += (dy / dist) * force

        # 速度阻尼
        self.vx *= 0.995
        self.vy *= 0.995

        # 更新位置
        self.x += self.vx
        self.y += self.vy

        # 越界重置
        if (self.x < 0 or self.x > WINDOW_SIZE or
            self.y < 0 or self.y > WINDOW_SIZE):
            self.reset()

    def draw(self):
        """绘制粒子"""
        if not self.alive:
            # 隐藏已死亡粒子
            self.canvas.coords(self.id, -10, -10, -10, -10)
            return
        r = self.size
        self.canvas.coords(self.id,
                           self.x - r, self.y - r,
                           self.x + r, self.y + r)
        self.canvas.itemconfig(self.id, fill=self.color)


class BlackholePet:
    """黑洞桌宠主类"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("黑洞桌宠")

        # 窗口设置：无边框 + 透明 + 置顶
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', ALWAYS_ON_TOP)

        # 尝试设置透明（Windows）
        try:
            self.root.attributes('-transparentcolor', TRANSPARENT_COLOR)
        except tk.TclError:
            # macOS/Linux 用 alpha 通道近似
            self.root.attributes('-alpha', 0.9)

        # 窗口初始位置：屏幕右下角
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        x = screen_w - WINDOW_SIZE - 50
        y = screen_h - WINDOW_SIZE - 100
        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}+{x}+{y}")

        # 创建画布
        self.canvas = tk.Canvas(
            self.root,
            width=WINDOW_SIZE,
            height=WINDOW_SIZE,
            bg=COLORS['bg'],
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack()

        # 中心坐标
        self.cx = WINDOW_SIZE // 2
        self.cy = WINDOW_SIZE // 2

        # 动画状态
        self.rotation_angle = 0
        self.pulse_phase = 0

        # 创建粒子
        self.particles = []
        for _ in range(PARTICLE_COUNT):
            p = Particle(self.canvas, self.cx, self.cy)
            self.particles.append(p)

        # 预创建的图形元素ID
        self.glow_id = None
        self.accretion_ids = []
        self.blackhole_id = None
        self.highlight_id = None

        # 初始化图形
        self._init_shapes()

        # 鼠标拖动
        self.drag_data = {'x': 0, 'y': 0}
        self.canvas.bind('<Button-1>', self._on_press)
        self.canvas.bind('<B1-Motion>', self._on_drag)
        self.canvas.bind('<Button-3>', self._show_menu)  # 右键菜单
        self.canvas.bind('<Double-Button-1>', self._toggle_size)  # 双击切换大小

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="变大 ➕", command=self._bigger)
        self.menu.add_command(label="变小 ➖", command=self._smaller)
        self.menu.add_separator()
        self.menu.add_command(label="引力增强 💪", command=self._more_gravity)
        self.menu.add_command(label="引力减弱 🪶", command=self._less_gravity)
        self.menu.add_separator()
        self.menu.add_command(label="退出 ❌", command=self._quit)

        # 当前缩放
        self.scale = 1.0

        # 启动动画循环
        self._animate()

    def _init_shapes(self):
        """初始化所有图形元素"""
        # 外层光晕
        self.glow_id = self.canvas.create_oval(
            self.cx - ACCRETION_OUTER - 15, self.cy - ACCRETION_OUTER - 15,
            self.cx + ACCRETION_OUTER + 15, self.cy + ACCRETION_OUTER + 15,
            fill='', outline=COLORS['glow'], width=2
        )

        # 吸积盘（用多个椭圆弧模拟）
        for i in range(8):
            arc = self.canvas.create_arc(
                0, 0, 0, 0,
                start=0, extent=30,
                style='arc', outline='', width=3
            )
            self.accretion_ids.append(arc)

        # 黑洞本体
        self.blackhole_id = self.canvas.create_oval(
            self.cx - BLACKHOLE_RADIUS, self.cy - BLACKHOLE_RADIUS,
            self.cx + BLACKHOLE_RADIUS, self.cy + BLACKHOLE_RADIUS,
            fill=COLORS['blackhole_center'],
            outline=COLORS['blackhole_edge'],
            width=3
        )

        # 黑洞高光
        self.highlight_id = self.canvas.create_oval(
            self.cx - BLACKHOLE_RADIUS * 0.4, self.cy - BLACKHOLE_RADIUS * 0.6,
            self.cx + BLACKHOLE_RADIUS * 0.1, self.cy - BLACKHOLE_RADIUS * 0.2,
            fill='#330066', outline=''
        )

    def _animate(self):
        """动画主循环"""
        self.rotation_angle += ROTATION_SPEED
        self.pulse_phase += 0.05

        # 更新光晕脉动
        pulse = math.sin(self.pulse_phase) * 0.1 + 1.0
        glow_r = (ACCRETION_OUTER + 15) * pulse
        self.canvas.coords(self.glow_id,
                           self.cx - glow_r, self.cy - glow_r,
                           self.cx + glow_r, self.cy + glow_r)

        # 更新吸积盘（旋转的彩色弧线）
        for i, arc_id in enumerate(self.accretion_ids):
            angle = self.rotation_angle + (i * math.pi / 4)
            r_inner = ACCRETION_INNER + i * 3
            r_outer = ACCRETION_OUTER - i * 2

            # 计算椭圆参数（模拟倾斜的吸积盘）
            scale_y = 0.35  # 垂直压缩，模拟透视
            rx = r_outer
            ry = r_outer * scale_y

            # 位置
            x0 = self.cx - rx
            y0 = self.cy - ry
            x1 = self.cx + rx
            y1 = self.cy + ry

            self.canvas.coords(arc_id, x0, y0, x1, y1)

            # 旋转角度（转成度数）
            start_deg = (angle * 180 / math.pi) % 360
            self.canvas.itemconfig(arc_id,
                                   start=start_deg,
                                   extent=45 - i * 3,
                                   outline=self._accretion_color(i),
                                   width=4 - i * 0.3)

        # 更新黑洞高光（随旋转微调）
        hl_offset = math.sin(self.rotation_angle * 2) * 3
        self.canvas.coords(self.highlight_id,
                           self.cx - BLACKHOLE_RADIUS * 0.4 + hl_offset,
                           self.cy - BLACKHOLE_RADIUS * 0.6,
                           self.cx + BLACKHOLE_RADIUS * 0.1 + hl_offset,
                           self.cy - BLACKHOLE_RADIUS * 0.2)

        # 更新粒子
        for p in self.particles:
            p.update()
            p.draw()
            if not p.alive:
                # 粒子被吞噬后，延迟重生
                if random.random() < 0.02:
                    p.reset()

        # 把黑洞本体放到最上层
        self.canvas.tag_raise(self.blackhole_id)
        self.canvas.tag_raise(self.highlight_id)

        self.root.after(30, self._animate)

    def _accretion_color(self, index):
        """根据索引返回吸积盘颜色"""
        colors = [
            COLORS['accretion_hot'],
            COLORS['accretion_warm'],
            '#ffcc00',
            COLORS['accretion_cool'],
            '#cc33ff',
            '#6600ff',
            '#3300aa',
            '#110044',
        ]
        return colors[index % len(colors)]

    # ==================== 交互功能 ====================

    def _on_press(self, event):
        """鼠标按下，记录拖动起点"""
        self.drag_data['x'] = event.x
        self.drag_data['y'] = event.y

    def _on_drag(self, event):
        """鼠标拖动，移动窗口"""
        dx = event.x - self.drag_data['x']
        dy = event.y - self.drag_data['y']
        x = self.root.winfo_x() + dx
        y = self.root.winfo_y() + dy
        self.root.geometry(f"+{x}+{y}")

    def _show_menu(self, event):
        """显示右键菜单"""
        try:
            self.menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.menu.grab_release()

    def _toggle_size(self, event=None):
        """双击切换大小"""
        if self.scale >= 1.0:
            self._smaller()
        else:
            self._bigger()

    def _bigger(self):
        """变大"""
        self.scale = min(self.scale * 1.3, 2.5)
        self._apply_scale()

    def _smaller(self):
        """变小"""
        self.scale = max(self.scale / 1.3, 0.5)
        self._apply_scale()

    def _apply_scale(self):
        """应用缩放（调整窗口大小和所有元素）"""
        global WINDOW_SIZE, BLACKHOLE_RADIUS, ACCRETION_INNER, ACCRETION_OUTER
        base = 200
        WINDOW_SIZE = int(base * self.scale)
        BLACKHOLE_RADIUS = int(30 * self.scale)
        ACCRETION_INNER = int(35 * self.scale)
        ACCRETION_OUTER = int(65 * self.scale)

        self.root.geometry(f"{WINDOW_SIZE}x{WINDOW_SIZE}")
        self.canvas.config(width=WINDOW_SIZE, height=WINDOW_SIZE)

        self.cx = WINDOW_SIZE // 2
        self.cy = WINDOW_SIZE // 2

        # 更新粒子中心
        for p in self.particles:
            p.cx = self.cx
            p.cy = self.cy

    def _more_gravity(self):
        """增强引力"""
        global GRAVITY_STRENGTH
        GRAVITY_STRENGTH = min(GRAVITY_STRENGTH * 1.5, 5.0)

    def _less_gravity(self):
        """减弱引力"""
        global GRAVITY_STRENGTH
        GRAVITY_STRENGTH = max(GRAVITY_STRENGTH / 1.5, 0.1)

    def _quit(self):
        """退出程序"""
        self.root.destroy()
        sys.exit(0)

    def run(self):
        """运行主循环"""
        self.root.mainloop()


if __name__ == '__main__':
    pet = BlackholePet()
    pet.run()
