import json
import os
import sys
import tkinter as tk
from tkinter import ttk, colorchooser, messagebox

try:
    import win32gui
    import win32con
except ImportError:
    print("请先安装 pywin32：pip install pywin32")
    sys.exit(1)

try:
    from pynput import keyboard
except ImportError:
    print("请先安装 pynput：pip install pynput")
    sys.exit(1)

CONFIG_FILE = "cooldown_config.json"
TRANSPARENT_COLOR = "#FF00FF"  # 透明背景色（与遮罩/文字颜色不同）

# ---------- 配置读写 ----------
def load_config():
    if not os.path.exists(CONFIG_FILE):
        default = {
            "always_on_top": True,
            "boxes": [
                {
                    "name": "技能1",
                    "start_hotkey": "4",
                    "pause_hotkey": "4",
                    "duration": "5m",          # 支持 "5m", "10m", "1h", 或纯秒数
                    "x": 100,
                    "y": 100,
                    "size": 50,
                    "font": "Arial",
                    "font_size": 14,
                    "font_color": "#FFFFFF",
                    "mask_color": "#808080",
                    "mask_alpha": 0.5
                }
            ]
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(default, f, indent=2, ensure_ascii=False)
        return default
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

def parse_duration(text):
    """将用户输入的时长字符串转换为秒。支持：'5m'、'10m'、'1h'、'90s'、纯数字（秒）"""
    text = text.strip().lower()
    if not text:
        return 0
    if text.endswith('h'):
        return int(float(text[:-1]) * 3600)
    elif text.endswith('m'):
        return int(float(text[:-1]) * 60)
    elif text.endswith('s'):
        return int(float(text[:-1]))
    else:
        return int(float(text))

def normalize_hotkey(key):
    """将用户输入的快捷键转换为 pynput 格式"""
    key = key.strip()
    if not key:
        return ""
    if key.lower().startswith('f') and key[1:].isdigit():
        return f"<{key.lower()}>"
    return key

# ---------- 冷却框窗口 ----------
class CooldownBox:
    def __init__(self, root, box_config, always_on_top=True):
        self.root = root
        self.config = box_config
        self.always_on_top = always_on_top
        self.duration = parse_duration(box_config.get("duration", "5m"))
        self.remaining = self.duration
        self.running = False
        self.penetrating = False

        self.size = int(box_config.get("size", 50))
        self.x = int(box_config.get("x", 100))
        self.y = int(box_config.get("y", 100))
        self.font_name = box_config.get("font", "Arial")
        self.font_size = int(box_config.get("font_size", 14))
        self.font_color = box_config.get("font_color", "#FFFFFF")
        self.mask_color = box_config.get("mask_color", "#808080")
        self.mask_alpha = float(box_config.get("mask_alpha", 0.5))

        # 创建无边框窗口
        self.win = tk.Toplevel(root)
        self.win.overrideredirect(True)
        self.win.geometry(f"{self.size}x{self.size}+{self.x}+{self.y}")
        self.win.attributes('-topmost', self.always_on_top)
        self.win.attributes('-transparentcolor', TRANSPARENT_COLOR)
        self.win.config(bg=TRANSPARENT_COLOR)

        self.canvas = tk.Canvas(
            self.win, width=self.size, height=self.size,
            bg=TRANSPARENT_COLOR, highlightthickness=0
        )
        self.canvas.pack(fill='both', expand=True)

        self.update_display()
        self.set_penetration(False)  # 初始不穿透，方便拖动

        # 绑定拖动事件
        self.canvas.bind("<Button-1>", self.start_move)
        self.canvas.bind("<B1-Motion>", self.on_move)

        # 右下角手柄调整大小
        self.handle = None
        self.create_resize_handle()

        # 刷新循环
        self.update_loop()

    def create_resize_handle(self):
        self.handle = self.canvas.create_rectangle(
            self.size - 10, self.size - 10, self.size, self.size,
            fill='white', outline=''
        )
        self.canvas.tag_bind(self.handle, "<Button-1>", self.start_resize)
        self.canvas.tag_bind(self.handle, "<B1-Motion>", self.on_resize)

    def start_move(self, event):
        if not self.penetrating:
            self.move_offset_x = event.x
            self.move_offset_y = event.y

    def on_move(self, event):
        if not self.penetrating and hasattr(self, 'move_offset_x'):
            x = self.win.winfo_x() + event.x - self.move_offset_x
            y = self.win.winfo_y() + event.y - self.move_offset_y
            self.win.geometry(f"+{x}+{y}")
            self.x = x
            self.y = y
            self.config['x'] = x   # 实时保存到配置
            self.config['y'] = y

    def start_resize(self, event):
        if not self.penetrating:
            self.resize_start_x = event.x_root
            self.resize_start_y = event.y_root
            self.resize_start_size = self.size

    def on_resize(self, event):
        if not self.penetrating and hasattr(self, 'resize_start_x'):
            dx = event.x_root - self.resize_start_x
            dy = event.y_root - self.resize_start_y
            new_size = max(20, min(500, self.resize_start_size + max(dx, dy)))
            if new_size != self.size:
                self.size = new_size
                self.win.geometry(f"{self.size}x{self.size}")
                self.canvas.config(width=self.size, height=self.size)
                self.update_display()
                self.create_resize_handle()
                self.config['size'] = self.size  # 实时保存到配置

    def set_penetration(self, enable):
        self.penetrating = enable
        hwnd = win32gui.GetParent(self.win.winfo_id())
        style = win32gui.GetWindowLong(hwnd, win32con.GWL_EXSTYLE)
        if enable:
            style |= win32con.WS_EX_TRANSPARENT
        else:
            style &= ~win32con.WS_EX_TRANSPARENT
        win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, style)
        win32gui.SetWindowPos(
            hwnd, 0, 0, 0, 0, 0,
            win32con.SWP_NOMOVE | win32con.SWP_NOSIZE |
            win32con.SWP_NOZORDER | win32con.SWP_FRAMECHANGED
        )

    def toggle(self):
        if self.running:
            self.pause()
        else:
            self.start()

    def start(self):
        if not self.running:
            self.running = True
            self.remaining = self.duration
            self.set_penetration(True)
            self.update_display()

    def pause(self):
        if self.running:
            self.running = False
            self.set_penetration(False)
            self.update_display()

    def update_loop(self):
        if self.running:
            if self.remaining > 0:
                self.remaining -= 1
                if self.remaining <= 0:
                    self.remaining = 0
                    self.running = False
                    self.set_penetration(False)
            self.update_display()
        self.root.after(1000, self.update_loop)

    @staticmethod
    def format_remaining(sec):
        if sec >= 60:
            return f"{int(sec // 60)}m"
        else:
            return f"{int(sec)}s"

    def update_display(self):
        self.canvas.delete("all")
        angle = 360.0 * self.remaining / self.duration if self.duration > 0 else 0

        # 透明度模拟
        stipple = ''
        alpha = self.mask_alpha
        if alpha <= 0.2:
            stipple = 'gray12'
        elif alpha <= 0.4:
            stipple = 'gray25'
        elif alpha <= 0.6:
            stipple = 'gray50'
        elif alpha <= 0.8:
            stipple = 'gray75'

        if angle > 0:
            self.canvas.create_arc(
                0, 0, self.size, self.size,
                start=90, extent=-angle,
                fill=self.mask_color, outline='',
                stipple=stipple
            )

        text = self.format_remaining(self.remaining)
        self.canvas.create_text(
            self.size / 2, self.size / 2, text=text,
            font=(self.font_name, self.font_size), fill=self.font_color
        )

        self.create_resize_handle()

# ---------- 设置窗口 ----------
class SettingsWindow:
    def __init__(self, parent_app):
        self.app = parent_app
        self.config = parent_app.config

        self.win = tk.Toplevel(parent_app.root)
        self.win.title("冷却计时器设置")
        self.win.geometry("700x500")
        self.win.attributes('-topmost', True)

        # 全局置顶选项
        self.top_var = tk.BooleanVar(value=self.config.get("always_on_top", True))
        ttk.Checkbutton(self.win, text="始终置顶冷却框", variable=self.top_var).pack(pady=5)

        # 冷却框列表框架
        list_frame = ttk.LabelFrame(self.win, text="冷却框列表")
        list_frame.pack(fill='both', expand=True, padx=10, pady=5)

        self.tree = ttk.Treeview(list_frame, columns=('name', 'start', 'pause', 'duration'),
                                 show='headings', height=6)
        self.tree.heading('name', text='名称')
        self.tree.heading('start', text='开始键')
        self.tree.heading('pause', text='暂停键')
        self.tree.heading('duration', text='冷却时间')
        self.tree.column('name', width=120)
        self.tree.column('start', width=80)
        self.tree.column('pause', width=80)
        self.tree.column('duration', width=100)
        self.tree.pack(fill='both', expand=True, padx=5, pady=5)
        self.tree.bind('<<TreeviewSelect>>', self.on_select)

        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(fill='x', padx=5, pady=5)
        ttk.Button(btn_frame, text="添加", command=self.add_box).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="删除", command=self.delete_box).pack(side='left', padx=2)

        # 编辑区
        edit_frame = ttk.LabelFrame(self.win, text="编辑选中冷却框")
        edit_frame.pack(fill='x', padx=10, pady=5)

        # 使用 grid 布局
        ttk.Label(edit_frame, text="名称:").grid(row=0, column=0, sticky='e', padx=5, pady=2)
        self.name_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.name_var, width=15).grid(row=0, column=1, padx=5, pady=2)

        ttk.Label(edit_frame, text="开始键:").grid(row=0, column=2, sticky='e', padx=5, pady=2)
        self.start_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.start_var, width=10).grid(row=0, column=3, padx=5, pady=2)

        ttk.Label(edit_frame, text="暂停键:").grid(row=0, column=4, sticky='e', padx=5, pady=2)
        self.pause_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.pause_var, width=10).grid(row=0, column=5, padx=5, pady=2)

        ttk.Label(edit_frame, text="冷却时间:").grid(row=1, column=0, sticky='e', padx=5, pady=2)
        self.duration_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.duration_var, width=15).grid(row=1, column=1, padx=5, pady=2)

        ttk.Label(edit_frame, text="字体:").grid(row=1, column=2, sticky='e', padx=5, pady=2)
        self.font_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.font_var, width=12).grid(row=1, column=3, padx=5, pady=2)

        ttk.Label(edit_frame, text="字号:").grid(row=1, column=4, sticky='e', padx=5, pady=2)
        self.font_size_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.font_size_var, width=5).grid(row=1, column=5, padx=5, pady=2)

        ttk.Label(edit_frame, text="文字颜色:").grid(row=2, column=0, sticky='e', padx=5, pady=2)
        self.font_color_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.font_color_var, width=12).grid(row=2, column=1, padx=5, pady=2)
        ttk.Button(edit_frame, text="选择", command=self.pick_font_color).grid(row=2, column=2, padx=5, pady=2)

        ttk.Label(edit_frame, text="遮罩颜色:").grid(row=2, column=3, sticky='e', padx=5, pady=2)
        self.mask_color_var = tk.StringVar()
        ttk.Entry(edit_frame, textvariable=self.mask_color_var, width=12).grid(row=2, column=4, padx=5, pady=2)
        ttk.Button(edit_frame, text="选择", command=self.pick_mask_color).grid(row=2, column=5, padx=5, pady=2)

        ttk.Label(edit_frame, text="遮罩透明度(0~1):").grid(row=3, column=0, sticky='e', padx=5, pady=2)
        self.mask_alpha_var = tk.StringVar()
        ttk.Scale(edit_frame, from_=0, to=1, orient='horizontal', length=150,
                  variable=self.mask_alpha_var, command=self.on_alpha_scale).grid(row=3, column=1, columnspan=2, padx=5, pady=2, sticky='w')

        # 按钮
        action_frame = ttk.Frame(self.win)
        action_frame.pack(fill='x', padx=10, pady=10)
        ttk.Button(action_frame, text="应用并保存", command=self.apply_changes).pack(side='left', padx=5)
        ttk.Button(action_frame, text="关闭设置", command=self.win.destroy).pack(side='left', padx=5)

        self.refresh_list()

    def refresh_list(self):
        self.tree.delete(*self.tree.get_children())
        for idx, box in enumerate(self.config.get('boxes', [])):
            self.tree.insert('', 'end', iid=str(idx), values=(
                box.get('name', ''),
                box.get('start_hotkey', ''),
                box.get('pause_hotkey', ''),
                box.get('duration', '')
            ))
        if self.config.get('boxes'):
            self.tree.selection_set('0')
            self.on_select()

    def on_select(self, event=None):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        box = self.config['boxes'][idx]
        self.name_var.set(box.get('name', ''))
        self.start_var.set(box.get('start_hotkey', ''))
        self.pause_var.set(box.get('pause_hotkey', ''))
        self.duration_var.set(box.get('duration', '5m'))
        self.font_var.set(box.get('font', 'Arial'))
        self.font_size_var.set(str(box.get('font_size', 14)))
        self.font_color_var.set(box.get('font_color', '#FFFFFF'))
        self.mask_color_var.set(box.get('mask_color', '#808080'))
        self.mask_alpha_var.set(float(box.get('mask_alpha', 0.5)))

    def add_box(self):
        new_box = {
            "name": f"技能{len(self.config['boxes'])+1}",
            "start_hotkey": "4",
            "pause_hotkey": "4",
            "duration": "5m",
            "x": 100,
            "y": 100,
            "size": 50,
            "font": "Arial",
            "font_size": 14,
            "font_color": "#FFFFFF",
            "mask_color": "#808080",
            "mask_alpha": 0.5
        }
        self.config.setdefault('boxes', []).append(new_box)
        self.refresh_list()
        self.tree.selection_set(str(len(self.config['boxes'])-1))
        self.on_select()

    def delete_box(self):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        if messagebox.askyesno("确认", "确定删除选中的冷却框吗？"):
            del self.config['boxes'][idx]
            self.refresh_list()

    def pick_font_color(self):
        color = colorchooser.askcolor(title="选择文字颜色", initialcolor=self.font_color_var.get())
        if color[1]:
            self.font_color_var.set(color[1])

    def pick_mask_color(self):
        color = colorchooser.askcolor(title="选择遮罩颜色", initialcolor=self.mask_color_var.get())
        if color[1]:
            self.mask_color_var.set(color[1])

    def on_alpha_scale(self, val):
        # 将scale值同步到变量（自动）
        pass

    def update_selected_box(self):
        selection = self.tree.selection()
        if not selection:
            return
        idx = int(selection[0])
        box = self.config['boxes'][idx]
        box['name'] = self.name_var.get()
        box['start_hotkey'] = self.start_var.get()
        box['pause_hotkey'] = self.pause_var.get()
        box['duration'] = self.duration_var.get()
        box['font'] = self.font_var.get()
        box['font_size'] = int(self.font_size_var.get())
        box['font_color'] = self.font_color_var.get()
        box['mask_color'] = self.mask_color_var.get()
        box['mask_alpha'] = float(self.mask_alpha_var.get())

    def apply_changes(self):
        # 更新当前选中的冷却框
        self.update_selected_box()
        # 更新全局置顶
        self.config['always_on_top'] = self.top_var.get()
        # 保存配置
        save_config(self.config)
        # 让主程序重建冷却框
        self.app.rebuild_boxes()
        messagebox.showinfo("成功", "设置已保存并应用！")

# ---------- 主程序 ----------
class CooldownApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.withdraw()  # 隐藏主窗口
        self.config = load_config()
        self.boxes = []
        self.hotkey_listener = None

        self.create_boxes()
        self.setup_hotkeys()
        self.open_settings()  # 启动时打开设置窗口
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_boxes(self):
        for box_config in self.config.get('boxes', []):
            box = CooldownBox(self.root, box_config, self.config.get('always_on_top', True))
            self.boxes.append(box)

    def setup_hotkeys(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
            self.hotkey_listener = None

        hotkeys = {}
        for box in self.boxes:
            start_hk = normalize_hotkey(box.config.get("start_hotkey", ""))
            pause_hk = normalize_hotkey(box.config.get("pause_hotkey", ""))

            if start_hk:
                if start_hk == pause_hk:
                    hotkeys[start_hk] = lambda b=box: self.root.after(0, b.toggle)
                else:
                    hotkeys[start_hk] = lambda b=box: self.root.after(0, b.start)
                    if pause_hk:
                        hotkeys[pause_hk] = lambda b=box: self.root.after(0, b.pause)

        # 固定退出快捷键
        hotkeys['<ctrl>+<alt>+q'] = lambda: self.root.after(0, self.on_close)

        if hotkeys:
            self.hotkey_listener = keyboard.GlobalHotKeys(hotkeys)
            self.hotkey_listener.daemon = True
            self.hotkey_listener.start()

    def rebuild_boxes(self):
        # 销毁所有冷却框
        for box in self.boxes:
            box.win.destroy()
        self.boxes.clear()
        # 重新创建
        self.create_boxes()
        self.setup_hotkeys()

    def open_settings(self):
        SettingsWindow(self)

    def on_close(self):
        if self.hotkey_listener:
            self.hotkey_listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    app = CooldownApp()
    app.root.mainloop()