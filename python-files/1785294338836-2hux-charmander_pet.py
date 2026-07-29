#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔥 小火龙桌面宠物 (Charmander Desktop Pet)
作者: AI Assistant
功能: 桌宠互动、状态管理、成长进化
"""

import tkinter as tk
from tkinter import messagebox
import random
import math
import time
import sys
import os

# ==================== 配置 ====================
WINDOW_WIDTH = 200
WINDOW_HEIGHT = 220
PET_SIZE = 120
UPDATE_INTERVAL = 50  # 毫秒
WANDER_INTERVAL = 4000  # 毫秒
STAT_DECAY_INTERVAL = 3000  # 毫秒

# ==================== 数据模型 ====================
class PetStats:
    def __init__(self):
        self.hunger = 80      # 饱食度
        self.mood = 70        # 心情值
        self.energy = 90      # 精力值
        self.love = 45        # 亲密度
        self.level = 1        # 等级
        self.exp = 0          # 经验值
        self.is_sleeping = False
        self.evolution_names = ["小火龙", "火恐龙", "喷火龙"]

    def get_name(self):
        idx = min(self.level - 1, 2)
        return self.evolution_names[idx]

    def add_exp(self, amount):
        if self.level >= 3:
            return False
        self.exp += amount
        if self.exp >= 100:
            self.exp = 0
            self.level = min(3, self.level + 1)
            return True  # 升级了
        return False

    def decay(self):
        if self.is_sleeping:
            self.energy = min(100, self.energy + 3)
            return None
        self.hunger = max(0, self.hunger - 2)
        self.mood = max(0, self.mood - 1.5)
        self.energy = max(0, self.energy - 1)

        if self.hunger < 20:
            return "hunger"
        elif self.mood < 20:
            return "mood"
        elif self.energy < 20:
            return "energy"
        return None

# ==================== 主程序 ====================
class CharmanderPet:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("小火龙桌宠")
        self.root.geometry(f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}")

        # 无边框、置顶、透明背景
        self.root.overrideredirect(True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-transparentcolor', '#000001')
        self.root.configure(bg='#000001')

        # 居中显示
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        self.root.geometry(f"+{screen_w//2 - WINDOW_WIDTH//2}+{screen_h//2 - WINDOW_HEIGHT//2}")

        # Canvas
        self.canvas = tk.Canvas(self.root, width=WINDOW_WIDTH, height=WINDOW_HEIGHT,
                               bg='#000001', highlightthickness=0)
        self.canvas.pack()

        # 数据
        self.stats = PetStats()
        self.drag_data = {"x": 0, "y": 0, "dragging": False}
        self.bubble_id = None
        self.bubble_text_id = None
        self.bubble_tail_id = None
        self.particles = []
        self.last_wander = time.time() * 1000
        self.last_decay = time.time() * 1000
        self.bubble_hide_time = 0
        self.jump_offset = 0
        self.is_jumping = False
        self.shake_angle = 0
        self.is_shaking = False
        self.flame_phase = 0

        # 绘制小火龙
        self.draw_charmander()

        # 绑定事件
        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Button-3>", self.show_menu)

        # 右键菜单
        self.menu = tk.Menu(self.root, tearoff=0, bg='#2d3436', fg='#dfe6e9',
                           activebackground='#e17055', activeforeground='#fff',
                           font=('Microsoft YaHei', 10))
        self.menu.add_command(label="🍖 喂食", command=self.feed)
        self.menu.add_command(label="🎾 玩耍", command=self.play)
        self.menu.add_command(label="👋 抚摸", command=self.pet)
        self.menu.add_command(label="💤 睡觉/起床", command=self.toggle_sleep)
        self.menu.add_separator()
        self.menu.add_command(label="📊 状态面板", command=self.show_status)
        self.menu.add_separator()
        self.menu.add_command(label="❌ 退出", command=self.on_exit)

        # 状态面板窗口
        self.status_window = None

        # 启动循环
        self.update_loop()

    # ==================== 绘制 ====================
    def draw_charmander(self):
        cx, cy = WINDOW_WIDTH // 2, WINDOW_HEIGHT // 2 + 10
        scale = 1.0
        if self.stats.level == 2:
            scale = 1.15
        elif self.stats.level == 3:
            scale = 1.3

        s = scale

        # 身体颜色
        body_color = "#ff8c42"
        belly_color = "#ffaa5c"

        # 尾巴火焰动画
        self.flame_phase += 0.15
        f1 = 1 + 0.15 * math.sin(self.flame_phase)
        f2 = 1 + 0.12 * math.sin(self.flame_phase + 1)
        f3 = 1 + 0.1 * math.sin(self.flame_phase + 2)

        # 跳跃/摇晃偏移
        jy = self.jump_offset
        sa = math.radians(self.shake_angle)

        # 睡眠效果
        brightness = 0.6 if self.stats.is_sleeping else 1.0

        # 绘制顺序：尾巴火焰 -> 身体 -> 头 -> 五官
        items = []

        # 尾巴火焰
        fx = cx + int(38 * s)
        fy = cy + int(10 * s) + jy

        # 外焰
        items.append(self.canvas.create_oval(
            fx - int(10*f1*s), fy - int(14*f1*s),
            fx + int(10*f1*s), fy + int(6*f1*s),
            fill="#ff6b35", outline="", tags="pet"
        ))
        # 中焰
        items.append(self.canvas.create_oval(
            fx - int(6*f2*s), fy - int(10*f2*s),
            fx + int(6*f2*s), fy + int(2*f2*s),
            fill="#ffd93d", outline="", tags="pet"
        ))
        # 内焰
        items.append(self.canvas.create_oval(
            fx - int(3*f3*s), fy - int(6*f3*s),
            fx + int(3*f3*s), fy - int(2*f3*s),
            fill="#ffffff", outline="", tags="pet"
        ))

        # 身体
        items.append(self.canvas.create_oval(
            cx - int(28*s), cy - int(5*s) + jy,
            cx + int(28*s), cy + int(35*s) + jy,
            fill=body_color, outline="", tags="pet"
        ))
        # 肚皮
        items.append(self.canvas.create_oval(
            cx - int(18*s), cy + int(5*s) + jy,
            cx + int(18*s), cy + int(30*s) + jy,
            fill=belly_color, outline="", tags="pet"
        ))

        # 头
        head_y = cy - int(28*s) + jy
        items.append(self.canvas.create_oval(
            cx - int(26*s), head_y - int(26*s),
            cx + int(26*s), head_y + int(26*s),
            fill=body_color, outline="", tags="pet"
        ))

        # 眼睛（白底）
        eye_y = head_y - int(5*s)
        items.append(self.canvas.create_oval(
            cx - int(16*s), eye_y - int(7*s),
            cx - int(6*s), eye_y + int(7*s),
            fill="#fff", outline="", tags="pet"
        ))
        items.append(self.canvas.create_oval(
            cx + int(6*s), eye_y - int(7*s),
            cx + int(16*s), eye_y + int(7*s),
            fill="#fff", outline="", tags="pet"
        ))

        # 眼珠
        if self.stats.is_sleeping:
            # 闭眼
            items.append(self.canvas.create_line(
                cx - int(14*s), eye_y, cx - int(8*s), eye_y + int(3*s),
                fill="#2d3436", width=2, tags="pet"
            ))
            items.append(self.canvas.create_line(
                cx + int(8*s), eye_y, cx + int(14*s), eye_y + int(3*s),
                fill="#2d3436", width=2, tags="pet"
            ))
        else:
            items.append(self.canvas.create_oval(
                cx - int(13*s), eye_y - int(3*s),
                cx - int(7*s), eye_y + int(3*s),
                fill="#2d3436", outline="", tags="pet"
            ))
            items.append(self.canvas.create_oval(
                cx + int(7*s), eye_y - int(3*s),
                cx + int(13*s), eye_y + int(3*s),
                fill="#2d3436", outline="", tags="pet"
            ))
            # 高光
            items.append(self.canvas.create_oval(
                cx - int(12*s), eye_y - int(4*s),
                cx - int(10*s), eye_y - int(2*s),
                fill="#fff", outline="", tags="pet"
            ))
            items.append(self.canvas.create_oval(
                cx + int(10*s), eye_y - int(4*s),
                cx + int(12*s), eye_y - int(2*s),
                fill="#fff", outline="", tags="pet"
            ))

        # 嘴巴
        mouth_y = head_y + int(10*s)
        if self.stats.is_sleeping:
            items.append(self.canvas.create_oval(
                cx - int(5*s), mouth_y, cx + int(5*s), mouth_y + int(4*s),
                fill="#2d3436", outline="", tags="pet"
            ))
        else:
            items.append(self.canvas.create_arc(
                cx - int(10*s), mouth_y - int(5*s),
                cx + int(10*s), mouth_y + int(8*s),
                start=0, extent=-180, style=tk.ARC,
                outline="#d63031", width=2, tags="pet"
            ))

        # 腮红
        items.append(self.canvas.create_oval(
            cx - int(22*s), head_y + int(2*s),
            cx - int(14*s), head_y + int(10*s),
            fill="#ff6b6b", outline="", tags="pet"
        ))
        items.append(self.canvas.create_oval(
            cx + int(14*s), head_y + int(2*s),
            cx + int(22*s), head_y + int(10*s),
            fill="#ff6b6b", outline="", tags="pet"
        ))

        # 手臂
        arm_y = cy + int(10*s) + jy
        items.append(self.canvas.create_oval(
            cx - int(38*s), arm_y - int(8*s),
            cx - int(24*s), arm_y + int(12*s),
            fill=body_color, outline="", tags="pet"
        ))
        items.append(self.canvas.create_oval(
            cx + int(24*s), arm_y - int(8*s),
            cx + int(38*s), arm_y + int(12*s),
            fill=body_color, outline="", tags="pet"
        ))

        # 腿
        leg_y = cy + int(32*s) + jy
        items.append(self.canvas.create_oval(
            cx - int(18*s), leg_y,
            cx - int(6*s), leg_y + int(14*s),
            fill=body_color, outline="", tags="pet"
        ))
        items.append(self.canvas.create_oval(
            cx + int(6*s), leg_y,
            cx + int(18*s), leg_y + int(14*s),
            fill=body_color, outline="", tags="pet"
        ))

        # 爪子
        claw_y = leg_y + int(12*s)
        for offset in [-12, -8, -4]:
            items.append(self.canvas.create_line(
                cx + int(offset*s), claw_y, cx + int((offset-2)*s), claw_y + int(4*s),
                fill="#d63031", width=2, tags="pet"
            ))
        for offset in [4, 8, 12]:
            items.append(self.canvas.create_line(
                cx + int(offset*s), claw_y, cx + int((offset+2)*s), claw_y + int(4*s),
                fill="#d63031", width=2, tags="pet"
            ))

        # 应用亮度
        if brightness < 1.0:
            for item in items:
                self.canvas.itemconfig(item, stipple="gray50")

        self.pet_items = items

    def clear_pet(self):
        self.canvas.delete("pet")

    def redraw(self):
        self.clear_pet()
        self.draw_charmander()

    # ==================== 气泡 ====================
    def show_bubble(self, text, duration=2000):
        self.hide_bubble()
        cx = WINDOW_WIDTH // 2
        cy = 35

        # 计算文字宽度
        text_len = len(text) * 12
        bw = max(80, text_len + 20)
        bh = 30

        bx = cx - bw // 2
        by = cy - bh // 2

        self.bubble_id = self.canvas.create_oval(
            bx, by, bx + bw, by + bh,
            fill="#fff", outline="#ddd", width=1, tags="bubble"
        )
        self.bubble_text_id = self.canvas.create_text(
            cx, cy, text=text, fill="#333", font=("Microsoft YaHei", 10, "bold"), tags="bubble"
        )
        # 小三角
        self.bubble_tail_id = self.canvas.create_polygon(
            cx - 6, by + bh - 2, cx + 6, by + bh - 2, cx, by + bh + 6,
            fill="#fff", outline="", tags="bubble"
        )

        self.bubble_hide_time = time.time() * 1000 + duration

    def hide_bubble(self):
        self.canvas.delete("bubble")
        self.bubble_id = None

    # ==================== 粒子 ====================
    def spawn_particle(self, emoji):
        cx = WINDOW_WIDTH // 2
        cy = WINDOW_HEIGHT // 2 - 20
        pid = self.canvas.create_text(cx, cy, text=emoji, font=("Segoe UI Emoji", 20), tags="particle")
        self.particles.append({"id": pid, "y": cy, "alpha": 1.0, "time": time.time()})

    def update_particles(self):
        now = time.time()
        to_remove = []
        for p in self.particles:
            elapsed = now - p["time"]
            if elapsed > 1.0:
                to_remove.append(p)
                continue
            new_y = p["y"] - elapsed * 60
            self.canvas.coords(p["id"], WINDOW_WIDTH//2, new_y)
            # 简单淡出效果通过删除重绘实现较复杂，这里用移动代替
        for p in to_remove:
            self.canvas.delete(p["id"])
            self.particles.remove(p)

    # ==================== 交互 ====================
    def on_press(self, event):
        self.drag_data["x"] = event.x_root - self.root.winfo_x()
        self.drag_data["y"] = event.y_root - self.root.winfo_y()
        self.drag_data["dragging"] = False

    def on_drag(self, event):
        self.drag_data["dragging"] = True
        x = event.x_root - self.drag_data["x"]
        y = event.y_root - self.drag_data["y"]
        self.root.geometry(f"+{x}+{y}")

    def on_release(self, event):
        if not self.drag_data["dragging"]:
            self.pet()

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def feed(self):
        if self.stats.is_sleeping:
            self.show_bubble("💤 呼噜...")
            return
        if self.stats.hunger >= 100:
            self.show_bubble("🙅 不饿啦！")
            return
        self.stats.hunger = min(100, self.stats.hunger + 20)
        self.stats.energy = min(100, self.stats.energy + 5)
        self.stats.love = min(100, self.stats.love + 5)
        leveled = self.stats.add_exp(10)
        self.show_bubble("🍖 好吃！")
        self.spawn_particle("🍖")
        if leveled:
            self.show_bubble(f"✨ 进化成{self.stats.get_name()}！", 3000)
            self.redraw()

    def play(self):
        if self.stats.is_sleeping:
            self.show_bubble("💤 呼噜...")
            return
        if self.stats.energy < 15:
            self.show_bubble("😫 太累了...")
            return
        self.stats.mood = min(100, self.stats.mood + 20)
        self.stats.energy = max(0, self.stats.energy - 15)
        self.stats.love = min(100, self.stats.love + 8)
        leveled = self.stats.add_exp(15)
        self.show_bubble("🎾 好玩！")
        self.spawn_particle("⭐")
        # 跳跃动画
        self.is_jumping = True
        self.jump_offset = -30
        self.redraw()
        self.root.after(200, lambda: self.set_jump(-15))
        self.root.after(400, lambda: self.set_jump(0))
        self.root.after(600, lambda: setattr(self, 'is_jumping', False))
        if leveled:
            self.root.after(700, lambda: self.show_bubble(f"✨ 进化成{self.stats.get_name()}！", 3000))
            self.root.after(700, self.redraw)

    def set_jump(self, val):
        self.jump_offset = val
        self.redraw()

    def pet(self):
        if self.stats.is_sleeping:
            self.show_bubble("💤 呼噜...")
            return
        self.stats.mood = min(100, self.stats.mood + 10)
        self.stats.love = min(100, self.stats.love + 12)
        leveled = self.stats.add_exp(8)
        self.show_bubble("❤️ 开心！")
        self.spawn_particle("❤️")
        # 摇晃动画
        self.is_shaking = True
        self.shake_angle = -5
        self.redraw()
        self.root.after(150, lambda: self.set_shake(5))
        self.root.after(300, lambda: self.set_shake(-5))
        self.root.after(450, lambda: self.set_shake(0))
        self.root.after(600, lambda: setattr(self, 'is_shaking', False))
        if leveled:
            self.root.after(700, lambda: self.show_bubble(f"✨ 进化成{self.stats.get_name()}！", 3000))
            self.root.after(700, self.redraw)

    def set_shake(self, val):
        self.shake_angle = val
        self.redraw()

    def toggle_sleep(self):
        if self.stats.is_sleeping:
            self.stats.is_sleeping = False
            self.show_bubble("☀️ 起床啦！")
            self.redraw()
        else:
            self.stats.is_sleeping = True
            self.show_bubble("💤 晚安...", 3000)
            self.redraw()

    def show_status(self):
        if self.status_window and self.status_window.winfo_exists():
            self.status_window.lift()
            return

        sw = tk.Toplevel(self.root)
        sw.title("状态面板")
        sw.geometry("280x320")
        sw.resizable(False, False)
        sw.configure(bg="#1a1a2e")
        sw.attributes('-topmost', True)

        # 标题
        tk.Label(sw, text=f"🔥 {self.stats.get_name()} Lv.{self.stats.level}",
                bg="#1a1a2e", fg="#e94560", font=("Microsoft YaHei", 16, "bold")).pack(pady=10)

        # 经验条
        tk.Label(sw, text=f"经验值: {int(self.stats.exp)}/100",
                bg="#1a1a2e", fg="#ccc", font=("Microsoft YaHei", 10)).pack()
        exp_canvas = tk.Canvas(sw, width=240, height=10, bg="#333", highlightthickness=0)
        exp_canvas.pack(pady=5)
        exp_canvas.create_rectangle(0, 0, 240*self.stats.exp/100, 10, fill="#feca57", outline="")

        # 状态条
        stats_data = [
            ("饱食度", self.stats.hunger, "#ff6b6b"),
            ("心情值", self.stats.mood, "#feca57"),
            ("精力值", self.stats.energy, "#48dbfb"),
            ("亲密度", self.stats.love, "#ff9ff3"),
        ]

        for name, val, color in stats_data:
            frame = tk.Frame(sw, bg="#1a1a2e")
            frame.pack(pady=8, padx=20, fill=tk.X)
            tk.Label(frame, text=f"{name}: {int(val)}%", bg="#1a1a2e", fg="#ccc",
                    font=("Microsoft YaHei", 10)).pack(anchor=tk.W)
            c = tk.Canvas(frame, width=240, height=12, bg="#333", highlightthickness=0)
            c.pack()
            c.create_rectangle(0, 0, 240*val/100, 12, fill=color, outline="")

        self.status_window = sw

    def on_exit(self):
        if messagebox.askyesno("确认", "确定要让小火龙回家吗？"):
            self.root.destroy()
            sys.exit(0)

    # ==================== 主循环 ====================
    def update_loop(self):
        now = time.time() * 1000

        # 气泡自动隐藏
        if self.bubble_hide_time > 0 and now > self.bubble_hide_time:
            self.hide_bubble()
            self.bubble_hide_time = 0

        # 自动漫游
        if now - self.last_wander > WANDER_INTERVAL:
            self.last_wander = now
            if not self.stats.is_sleeping and not self.drag_data["dragging"] and not self.is_jumping:
                self.wander()

        # 状态衰减
        if now - self.last_decay > STAT_DECAY_INTERVAL:
            self.last_decay = now
            warn = self.stats.decay()
            if warn == "hunger":
                self.show_bubble("🍖 好饿...", 2000)
            elif warn == "mood":
                self.show_bubble("😢 无聊...", 2000)
            elif warn == "energy":
                self.show_bubble("😫 好累...", 2000)
            # 自动醒来
            if self.stats.is_sleeping and self.stats.energy >= 100:
                self.stats.is_sleeping = False
                self.show_bubble("☀️ 精神满满！")
                self.redraw()

        # 粒子更新
        self.update_particles()

        # 火焰动画（持续重绘）
        if not self.is_jumping and not self.is_shaking:
            self.redraw()

        self.root.after(UPDATE_INTERVAL, self.update_loop)

    def wander(self):
        # 随机小幅度移动
        x = self.root.winfo_x()
        y = self.root.winfo_y()
        dx = random.randint(-80, 80)
        dy = random.randint(-50, 50)
        new_x = max(0, min(self.root.winfo_screenwidth() - WINDOW_WIDTH, x + dx))
        new_y = max(0, min(self.root.winfo_screenheight() - WINDOW_HEIGHT, y + dy))
        self.root.geometry(f"+{new_x}+{new_y}")

        # 随机说话
        if random.random() < 0.2:
            texts = ["🔥 咔？", "🎵 ~", "😊 ...", "👀 ？"]
            self.show_bubble(random.choice(texts), 1500)

    def run(self):
        self.show_bubble("🔥 咔！你好！", 3000)
        self.root.mainloop()

# ==================== 入口 ====================
if __name__ == "__main__":
    pet = CharmanderPet()
    pet.run()
