import tkinter as tk
import random
import math

# ===================== 【全可调核心参数】一键修改 =====================
POPUP_COUNT = 50          # 弹窗数量
POPUP_DELAY = 180        # 弹窗逐个生成间隔
WINDOW_ALPHA = 1       # 弹窗最终透明度
FADE_SPEED = 20           # 淡入速度（越小越快）
ROUND_RADIUS = 18         # 圆角大小

# 主弹窗尺寸
MAIN_W = 350
MAIN_H = 180

# 小巧弹窗尺寸（已缩小）
POPUP_W = 200
POPUP_H = 60

# 点击提示框尺寸
TIP_W = 300
TIP_H = 65

# 爱心大小可调（数字越大爱心越大）
HEART_SCALE = 25
# ====================================================================

# ===================== 【EMO伤感文案】孤独/遗憾/温柔 =====================
messages = [
    "遗憾常有", "无人懂我", "深夜难眠", "心事重重",
    "爱意消散", "独自撑伞", "旧人难遇", "满心疲惫",
    "人海孤独", "万事皆空", "风也沉默", "雾里看花",
    "无人等候", "半生遗憾", "清醒孤独", "渐行渐远"
]

# ===================== 【EMO暗色系】低饱和冷色调 =====================
bg_colors = [
    "#8A92A5", "#7D8491", "#9A8C9F", "#6B7280",
    "#887C8C", "#717786", "#908999", "#787F8E"
]

# EMO提示框颜色
TIP_COLOR = "#6B7280"
TRANSPARENT_COLOR = "#000001"

class PerfectPopupApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.attributes("-transparentcolor", TRANSPARENT_COLOR)
        self.windows = []
        self.is_animating = False
        self.arrived_count = 0
        self.create_main_popup()

    # ===================== 全局无锯齿圆角函数 =====================
    def create_rounded_win(self, width, height, bg_color, init_alpha=0):
        win = tk.Toplevel(self.root)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        win.attributes("-alpha", init_alpha)
        win.attributes("-transparentcolor", TRANSPARENT_COLOR)
        
        canvas = tk.Canvas(win, width=width, height=height, bg=TRANSPARENT_COLOR, highlightthickness=0)
        canvas.pack()
        
        # 无锯齿圆角绘制
        r = ROUND_RADIUS
        canvas.create_rectangle(r, 0, width-r, height, fill=bg_color, outline=bg_color)
        canvas.create_rectangle(0, r, width, height-r, fill=bg_color, outline=bg_color)
        canvas.create_arc(0, 0, 2*r, 2*r, start=90, extent=90, fill=bg_color, outline=bg_color)
        canvas.create_arc(width-2*r, 0, width, 2*r, start=0, extent=90, fill=bg_color, outline=bg_color)
        canvas.create_arc(0, height-2*r, 2*r, height, start=180, extent=90, fill=bg_color, outline=bg_color)
        canvas.create_arc(width-2*r, height-2*r, width, height, start=270, extent=90, fill=bg_color, outline=bg_color)
        
        return win, canvas

    # ===================== 主弹窗（EMO风格） =====================
    def create_main_popup(self):
        win, canvas = self.create_rounded_win(MAIN_W, MAIN_H, "#908999", WINDOW_ALPHA)
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"+{(sw-MAIN_W)//2}+{(sh-MAIN_H)//2}")

        tk.Label(canvas, text="人海里 独自前行", bg="#908999", font=("楷体", 22, "bold"), fg="#F5F5F5"
                ).place(x=0,y=30,width=MAIN_W,height=50)
        tk.Button(canvas, text="离开", bg="#717786", fg="white", font=("楷体",14),
                 command=lambda: self.close_win(win)).place(x=60,y=110,width=100,height=40)
        tk.Button(canvas, text="停留", bg="#8A92A5", fg="white", font=("楷体",14),
                 command=lambda: self.start_slow_popups(win)).place(x=190,y=110,width=100,height=40)
        self.windows.append(win)

    # ===================== 弹窗缓慢逐个生成 =====================
    def start_slow_popups(self, main_win):
        self.close_win(main_win)
        self.sw, self.sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        self.current_popup_num = 0
        self.generate_one_popup()

    def generate_one_popup(self):
        if self.current_popup_num >= POPUP_COUNT:
            self.root.after(300, self.create_tip_win)
            return
        # 生成弹窗 + 淡入动画
        self.create_small_popup()
        self.current_popup_num += 1
        self.root.after(POPUP_DELAY, self.generate_one_popup)

    # ===================== 弹窗淡入缓慢显现（透明→清晰） =====================
    def create_small_popup(self):
        color = random.choice(bg_colors)
        # 初始完全透明
        win, canvas = self.create_rounded_win(POPUP_W, POPUP_H, color, init_alpha=0.0)
        x = random.randint(0, self.sw - POPUP_W)
        y = random.randint(0, self.sh - POPUP_H)
        win.geometry(f"+{x}+{y}")

        tk.Label(canvas, text=random.choice(messages), bg=color, font=("楷体", 18, "bold"), fg="#F5F5F5"
                ).place(x=0,y=0,width=POPUP_W,height=POPUP_H)
        self.windows.append(win)

        # 启动淡入动画：从透明慢慢显现
        self.fade_in(win)

    def fade_in(self, win, current_alpha=0.0):
        """弹窗淡入效果：透明→清晰"""
        if not win.winfo_exists():
            return
        if current_alpha >= WINDOW_ALPHA:
            return
        # 逐步增加透明度
        win.attributes("-alpha", current_alpha)
        next_alpha = current_alpha + 0.05
        win.after(FADE_SPEED, self.fade_in, win, next_alpha)

    # ===================== 点击提示框（强制置顶） =====================
    def create_tip_win(self):
        win, canvas = self.create_rounded_win(TIP_W, TIP_H, TIP_COLOR, WINDOW_ALPHA)
        win.attributes("-topmost", True)
        win.lift()
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        win.geometry(f"+{(sw-TIP_W)//2}+{sh//2+100}")

        tk.Label(canvas, text="♥ 点击收起遗憾", bg=TIP_COLOR, font=("楷体", 19, "bold"), fg="#F5F5F5"
                ).place(x=0,y=0,width=TIP_W,height=TIP_H)
        win.bind("<Button-1>", lambda e: self.start_heart(win))

    # ===================== 爱心汇聚动画（大小可调） =====================
    def start_heart(self, tip_win):
        self.close_win(tip_win)
        self.is_animating = True
        sw, sh = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        cx, cy = sw//2, sh//2
        points = self.gen_heart(len(self.windows))

        for i, win in enumerate(self.windows):
            tx = cx + int(points[i][0] * HEART_SCALE) - (POPUP_W//2)
            ty = cy + int(points[i][1] * HEART_SCALE) - (POPUP_H//2)
            self.animate_move(win, tx, ty, i*25)

    def gen_heart(self, num):
        pts = []
        for i in range(num):
            t = 2*math.pi*i/num
            x = 16*math.sin(t)**3
            y = -(13*math.cos(t)-5*math.cos(2*t)-2*math.cos(3*t)-math.cos(4*t))
            pts.append((x,y))
        return pts

    def animate_move(self, win, tx, ty, delay):
        if not win.winfo_exists(): return
        sx, sy = win.winfo_x(), win.winfo_y()
        step = 0
        def move():
            nonlocal step
            if step > 30:
                self.arrived_count +=1
                if self.arrived_count == len(self.windows):
                    self.root.after(2000, self.fade_all)
                return
            p = 1-(1-step/30)**2
            cx = int(sx + (tx-sx)*p)
            cy = int(sy + (ty-sy)*p)
            win.geometry(f"+{cx}+{cy}")
            step +=1
            win.after(20, move)
        win.after(delay, move)

    def fade_all(self):
        for win in self.windows:
            self.fade_out(win)

    def fade_out(self, win, alpha=WINDOW_ALPHA):
        if not win.winfo_exists(): return
        if alpha <=0:
            win.destroy()
            return
        win.attributes("-alpha", alpha)
        win.after(40, lambda: self.fade_out(win, alpha-0.05))

    # ===================== 工具函数 =====================
    def close_win(self, win):
        if win.winfo_exists(): win.destroy()
        if win in self.windows: self.windows.remove(win)

    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = PerfectPopupApp()
    app.run()