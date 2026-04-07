import os
import sys
import re
import time
import math
import tempfile
import json
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageDraw

try:
    import pyperclip
except ImportError:
    print("错误：未找到 pyperclip 库\n请安装: pip install pyperclip")
    sys.exit(1)

try:
    import pystray
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

# ========== 默认配置 ==========
DEFAULT_CONFIG = {
    "replace_pattern": r'XX|xx|××|小[Xx×]|春燕|景轩|小茹|春雨',
    "replace_with": "再星",
    "target_size_kb": 400,
    "size_tolerance_kb": 50,
    "min_file_size_kb": 50
}

CONFIG_FILE = "dual_tool_config.json"


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json.load(f)
        for k, v in DEFAULT_CONFIG.items():
            if k not in config:
                config[k] = v
        if "replace_pattern" in config and config["replace_pattern"] != DEFAULT_CONFIG["replace_pattern"]:
            new_terms = ["春燕", "景轩", "小茹", "春雨"]
            missing = [term for term in new_terms if term not in config["replace_pattern"]]
            if missing:
                config["replace_pattern"] = config["replace_pattern"] + "|" + "|".join(missing)
                save_config(config)
        return config
    except Exception:
        return DEFAULT_CONFIG.copy()


def save_config(config):
    try:
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        return True
    except Exception:
        return False


def create_star_image(size, color='gold', bg_color='white'):
    img = Image.new('RGBA', (size, size), bg_color)
    draw = ImageDraw.Draw(img)
    cx = cy = size // 2
    r_outer = size * 0.45
    r_inner = size * 0.22
    points = []
    for i in range(5):
        angle = i * 72 - 90
        x_outer = cx + r_outer * math.cos(math.radians(angle))
        y_outer = cy + r_outer * math.sin(math.radians(angle))
        points.append((x_outer, y_outer))
        x_inner = cx + r_inner * math.cos(math.radians(angle + 36))
        y_inner = cy + r_inner * math.sin(math.radians(angle + 36))
        points.append((x_inner, y_inner))
    draw.polygon(points, fill=color, outline=color)
    return img


# ========== 图片压缩模块 ==========
class ImageCompressor:
    def __init__(self, config, monitor_dir):
        self.config = config
        self.monitor_dir = monitor_dir
        self.processed = {}
        self.compressed_count = 0
        self.running = True
        self.callback = None

    def set_callback(self, callback):
        self.callback = callback

    def update_dir(self, new_dir):
        self.monitor_dir = new_dir
        self.processed.clear()

    def is_image_file(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return ext in ('.jpg', '.jpeg', '.png', '.webp', '.bmp')

    def should_compress(self, filepath):
        try:
            size = os.path.getsize(filepath)
            target = self.config["target_size_kb"] * 1024
            min_size = self.config["min_file_size_kb"] * 1024
            tolerance = self.config["size_tolerance_kb"] * 1024
            if size < min_size or size <= target + tolerance:
                return False
            time.sleep(0.3)
            return size == os.path.getsize(filepath)
        except Exception:
            return False

    def compress_image(self, filepath):
        try:
            with Image.open(filepath) as img:
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                target = self.config["target_size_kb"] * 1024
                tolerance = self.config["size_tolerance_kb"] * 1024

                low, high = 20, 95
                best_quality = 85
                best_size = None
                temp_path = None
                for _ in range(12):
                    quality = (low + high) // 2
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                        temp_path = tmp.name
                    img.save(temp_path, 'JPEG', quality=quality, optimize=True)
                    size = os.path.getsize(temp_path)
                    if abs(size - target) <= tolerance:
                        best_size = size
                        best_quality = quality
                        break
                    if best_size is None or abs(size - target) < abs(best_size - target):
                        best_size = size
                        best_quality = quality
                    if size > target:
                        high = quality - 1
                    else:
                        low = quality + 1
                    if low > high:
                        break
                if best_size is not None:
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                        final_path = tmp.name
                    img.save(final_path, 'JPEG', quality=best_quality, optimize=True)
                    final_size = os.path.getsize(final_path)
                    os.remove(filepath)
                    os.rename(final_path, filepath)
                    return final_size
        except Exception:
            pass
        finally:
            if 'temp_path' in locals() and temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except:
                    pass
        return 0

    def monitor(self):
        while self.running:
            try:
                for filename in os.listdir(self.monitor_dir):
                    if not self.running:
                        break
                    filepath = os.path.join(self.monitor_dir, filename)
                    if not os.path.isfile(filepath) or not self.is_image_file(filename):
                        continue
                    try:
                        mtime = os.path.getmtime(filepath)
                    except:
                        continue
                    if filename in self.processed and self.processed[filename] == mtime:
                        continue
                    if self.should_compress(filepath):
                        if self.compress_image(filepath):
                            self.compressed_count += 1
                            if self.callback:
                                self.callback()
                    self.processed[filename] = mtime
                time.sleep(2)
            except Exception:
                time.sleep(5)

    def stop(self):
        self.running = False


# ========== 剪贴板替换模块 ==========
class ClipboardReplacer:
    def __init__(self, pattern, replace_with):
        self.pattern = pattern
        self.replace_with = replace_with
        self.compiled_re = None
        self.last_clipboard = ""
        self.replaced_count = 0
        self.running = True
        self.callback = None
        self._compile()

    def set_callback(self, callback):
        self.callback = callback

    def _compile(self):
        try:
            self.compiled_re = re.compile(self.pattern)
            return True
        except re.error:
            self.compiled_re = None
            return False

    def set_rule(self, pattern, replace_with):
        self.pattern = pattern
        self.replace_with = replace_with
        self._compile()

    def replace_text(self, text):
        if not self.compiled_re:
            return text, 0
        replaced = self.compiled_re.sub(self.replace_with, text)
        matches = len(self.compiled_re.findall(text))
        return replaced, matches

    def monitor(self):
        while self.running:
            try:
                current = pyperclip.paste()
                if (current != self.last_clipboard and
                        current.strip() and
                        self.compiled_re and
                        self.compiled_re.search(current)):
                    replaced, matches = self.replace_text(current)
                    if matches:
                        pyperclip.copy(replaced)
                        self.replaced_count += matches
                        if self.callback:
                            self.callback()
                self.last_clipboard = current
                time.sleep(0.5)
            except Exception:
                time.sleep(2)

    def stop(self):
        self.running = False


# ========== 主应用 ==========
class DualToolApp:
    def __init__(self):
        self.config = load_config()
        self.monitor_dir = os.getcwd()
        self.img_compressor = ImageCompressor(self.config, self.monitor_dir)
        self.clip_replacer = ClipboardReplacer(
            self.config["replace_pattern"],
            self.config["replace_with"]
        )
        self.tray_icon = None
        self.root = None
        self.icon_photo = None
        self.temp_icon_path = None
        self.img_compressor.set_callback(self.on_stat_update)
        self.clip_replacer.set_callback(self.on_stat_update)
        # 用于连续按两次 F12 退出的状态
        self.last_f12_time = 0
        self.f12_press_count = 0

    def on_stat_update(self):
        if self.root:
            self.root.after(0, self.update_gui)

    def update_gui(self):
        if self.root:
            self.img_count_var.set(str(self.img_compressor.compressed_count))
            self.clip_count_var.set(str(self.clip_replacer.replaced_count))
            self.dir_label.config(text=f"监控目录: {self.img_compressor.monitor_dir}")
        if HAS_TRAY and self.tray_icon:
            self.update_tray_menu()

    def save_rules(self):
        new_pattern = self.pattern_entry.get().strip()
        new_replace = self.replace_entry.get()
        if not new_pattern:
            messagebox.showerror("错误", "匹配模式不能为空！", parent=self.root)
            return
        try:
            re.compile(new_pattern)
        except re.error as e:
            messagebox.showerror("正则错误", f"无效的正则表达式：{e}", parent=self.root)
            return
        self.clip_replacer.set_rule(new_pattern, new_replace)
        self.config["replace_pattern"] = new_pattern
        self.config["replace_with"] = new_replace
        save_config(self.config)
        messagebox.showinfo("成功",
                            "已经保存好了\n\n本程序由Yang独立开发制作，版权归制作者所有。\n程序仅限个人测试、学习研究及非商业交流使用，严禁用于任何非法活动、商业盈利、侵权牟利等场景；未经授权，禁止擅自复制、分发、修改或商用。\n如有相关疑问，可通过邮箱联系：1255429936@qq.com。",
                            parent=self.root)

    def choose_dir(self):
        new_dir = filedialog.askdirectory(title="选择图片监控目录", initialdir=self.img_compressor.monitor_dir)
        if new_dir:
            self.img_compressor.update_dir(new_dir)
            self.update_gui()

    def hide_window(self):
        if self.root:
            self.root.withdraw()

    def show_window(self):
        if self.root:
            self.root.deiconify()
            self.root.lift()

    def stop_all(self, icon=None, item=None):
        self.img_compressor.stop()
        self.clip_replacer.stop()
        if self.tray_icon:
            self.tray_icon.stop()
        if self.root:
            self.root.quit()
            self.root.destroy()
        if self.temp_icon_path and os.path.exists(self.temp_icon_path):
            try:
                os.remove(self.temp_icon_path)
            except:
                pass
        sys.exit(0)

    # 连续按两次 F12 退出
    def on_f12_pressed(self, event=None):
        current_time = time.time()
        # 如果距离上次按下时间小于 0.5 秒，视为第二次按下
        if current_time - self.last_f12_time < 0.5:
            self.f12_press_count += 1
        else:
            self.f12_press_count = 1
        self.last_f12_time = current_time

        if self.f12_press_count >= 2:
            self.stop_all()

    # ========== 托盘图标 ==========
    def create_tray_icon(self):
        if not HAS_TRAY:
            return
        star_img = create_star_image(64, color='gold', bg_color='white')
        menu = (
            pystray.MenuItem(f"图片压缩: {self.img_compressor.compressed_count} 张", lambda: None),
            pystray.MenuItem(f"剪贴板替换: {self.clip_replacer.replaced_count} 次", lambda: None),
            pystray.MenuItem("---", None),
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出", self.stop_all)
        )
        self.tray_icon = pystray.Icon("star_tool", star_img, "Star", menu)

    def update_tray_menu(self):
        if not self.tray_icon:
            return
        menu = (
            pystray.MenuItem(f"图片压缩: {self.img_compressor.compressed_count} 张", lambda: None),
            pystray.MenuItem(f"剪贴板替换: {self.clip_replacer.replaced_count} 次", lambda: None),
            pystray.MenuItem("---", None),
            pystray.MenuItem("显示窗口", self.show_window),
            pystray.MenuItem("退出", self.stop_all)
        )
        self.tray_icon.menu = pystray.Menu(*menu)

    # ========== 界面美化 ==========
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        bg_color = "#f0f2f5"
        card_bg = "#ffffff"
        accent = "#2c7da0"

        style.configure("TFrame", background=bg_color)
        style.configure("TLabelframe", background=card_bg, foreground="#333")
        style.configure("TLabelframe.Label", background=card_bg, foreground="#333", font=('Segoe UI', 10, 'bold'))
        style.configure("Card.TLabelframe", background=card_bg, relief="solid", bordercolor="#e0e0e0", borderwidth=1)
        style.configure("Card.TLabelframe.Label", background=card_bg, foreground="#2c3e50", font=('Segoe UI', 10, 'bold'))
        style.configure("Count.TLabel", font=('Segoe UI', 18, 'bold'), foreground=accent, background=card_bg)
        style.configure("Desc.TLabel", font=('Segoe UI', 9), foreground="#7f8c8d", background=card_bg)
        style.configure("Accent.TButton", font=('Segoe UI', 9), background=accent, foreground="white")
        style.map("Accent.TButton", background=[('active', '#1f6390')])
        style.configure("TButton", font=('Segoe UI', 9), padding=4)

    def create_gui(self):
        self.root = tk.Tk()
        self.root.title("Star")
        self.root.geometry("450x560")  # 稍微增高一点容纳提示文字
        self.root.resizable(False, False)
        self.root.configure(bg="#f0f2f5")
        self.root.protocol("WM_DELETE_WINDOW", self.hide_window)

        star_img = create_star_image(32, color='gold', bg_color='white')
        self.temp_icon_path = tempfile.NamedTemporaryFile(suffix='.png', delete=False).name
        star_img.save(self.temp_icon_path, format='PNG')
        icon = tk.PhotoImage(file=self.temp_icon_path)
        self.root.iconphoto(True, icon)
        self.icon_photo = icon

        # 绑定 F12 事件（窗口激活时有效）
        self.root.bind('<F12>', self.on_f12_pressed)

        self.setup_styles()

        main = ttk.Frame(self.root, padding=15)
        main.pack(fill=tk.BOTH, expand=True)

        # ----- 图片压缩卡片 -----
        img_card = ttk.LabelFrame(main, text="图片自动压缩", style="Card.TLabelframe", padding=10)
        img_card.pack(fill=tk.X, pady=(0, 12))
        img_card.columnconfigure(0, weight=1)

        self.img_count_var = tk.StringVar(value="0")
        ttk.Label(img_card, textvariable=self.img_count_var, style="Count.TLabel").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(img_card, text="已压缩图片数", style="Desc.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=(0, 5))

        self.dir_label = ttk.Label(img_card, text=f"监控目录: {self.img_compressor.monitor_dir}", style="Desc.TLabel")
        self.dir_label.grid(row=2, column=0, sticky="w", padx=5, pady=(0, 5))

        btn_frame = ttk.Frame(img_card)
        btn_frame.grid(row=3, column=0, sticky="ew", pady=(0, 5))
        ttk.Button(btn_frame, text="选择图片目录", command=self.choose_dir, width=12).pack()

        # ----- 剪贴板替换卡片 -----
        clip_card = ttk.LabelFrame(main, text="剪贴板自动替换", style="Card.TLabelframe", padding=10)
        clip_card.pack(fill=tk.X, pady=(0, 12))
        clip_card.columnconfigure(0, weight=1)

        self.clip_count_var = tk.StringVar(value="0")
        ttk.Label(clip_card, textvariable=self.clip_count_var, style="Count.TLabel").grid(row=0, column=0, sticky="w", padx=5)
        ttk.Label(clip_card, text="已替换次数", style="Desc.TLabel").grid(row=1, column=0, sticky="w", padx=5, pady=(0, 8))

        ttk.Label(clip_card, text="替换词:(多词用‘|’隔开)", font=('Segoe UI', 9)).grid(row=2, column=0, sticky="w", pady=(5, 0))
        self.pattern_entry = ttk.Entry(clip_card, font=('Consolas', 10))
        self.pattern_entry.grid(row=3, column=0, sticky="ew", pady=2)
        self.pattern_entry.insert(0, self.config["replace_pattern"])

        ttk.Label(clip_card, text="替换为:", font=('Segoe UI', 9)).grid(row=4, column=0, sticky="w", pady=(5, 0))
        self.replace_entry = ttk.Entry(clip_card, font=('Segoe UI', 10))
        self.replace_entry.grid(row=5, column=0, sticky="ew", pady=2)
        self.replace_entry.insert(0, self.config["replace_with"])

        # ----- 底部按钮栏 -----
        button_bar = ttk.Frame(main)
        button_bar.pack(fill=tk.X, pady=(0, 8))
        ttk.Button(button_bar, text="保存", command=self.save_rules, style="Accent.TButton", width=12).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_bar, text="退出", command=self.stop_all, style="Accent.TButton", width=12).pack(side=tk.RIGHT, padx=(5, 0))

        # ----- 双击 F12 退出提醒 -----
        tip_label = tk.Label(
            main,
            text="提示：连续按两次 F12 即可退出程序",
            font=('Segoe UI', 8),
            fg="#aaaaaa",
            bg="#f0f2f5"
        )
        tip_label.pack(pady=(0, 0))

        self.update_gui()

    def start(self):
        self.create_gui()
        threading.Thread(target=self.img_compressor.monitor, daemon=True).start()
        threading.Thread(target=self.clip_replacer.monitor, daemon=True).start()
        if HAS_TRAY:
            self.create_tray_icon()
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        self.root.mainloop()


def main():
    app = DualToolApp()
    app.start()


if __name__ == "__main__":
    main()