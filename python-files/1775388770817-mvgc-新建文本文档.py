import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
import json
import subprocess
import os
import time
import winsound
from datetime import datetime, timedelta, timezone
from threading import Timer

# ===================== 配置路径 =====================
HOME = os.path.expanduser("~")
APP_DIR = os.path.join(HOME, ".system_helper_launcher")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
ALERT_SOUND = None

os.makedirs(APP_DIR, exist_ok=True)

# ===================== 主程序 =====================
class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("多功能桌面启动器")
        self.geometry("1000x700")
        self.configure(bg="#f0f2f5")
        self.apps = []
        self.load_config()

        # 拖拽移动相关变量
        self.drag_data = {"x": 0, "y": 0, "item": None, "index": -1}

        self.build_ui()
        self.refresh_desktop()
        self.start_top_clock()
        self.start_fatigue_reminder()

    # ===================== 配置 =====================
    def load_config(self):
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    self.apps = json.load(f)
        except:
            self.apps = []

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.apps, f, ensure_ascii=False, indent=4)

    def clear_config(self):
        if not messagebox.askyesno("警告", "确定清空所有图标？不可恢复！"):
            return
        self.apps.clear()
        if os.path.exists(CONFIG_FILE):
            os.remove(CONFIG_FILE)
        self.refresh_desktop()
        messagebox.showinfo("完成", "已清空配置")

    # ===================== 顶部UI（工具抽屉按钮） =====================
    def build_ui(self):
        top = tk.Frame(self, bg="#2C3E50", height=80)
        top.pack(fill=tk.X)
        top.pack_propagate(False)

        tk.Label(top, text="📱 多功能启动器", fg="white", bg="#2C3E50",
                 font=("微软雅黑", 20, "bold")).pack(side=tk.LEFT, padx=20)

        # 工具抽屉按钮（仿你给的图标样式）
        tool_btn = tk.Button(
            top, text="🔧 工具", bg="#3498DB", fg="white",
            font=("微软雅黑", 12, "bold"), relief=tk.FLAT,
            command=self.show_tool_drawer, width=8
        )
        tool_btn.pack(side=tk.RIGHT, padx=15)

        # 清空配置按钮
        tk.Button(
            top, text="清空配置", bg="#E74C3C", fg="white",
            font=("微软雅黑", 10), relief=tk.FLAT,
            command=self.clear_config, width=10
        ).pack(side=tk.RIGHT, padx=5)

        self.top_time_label = tk.Label(top, fg="white", bg="#2C3E50", font=("Consolas", 15))
        self.top_time_label.pack(side=tk.RIGHT, padx=15)

        self.desktop = tk.Frame(self, bg="#f0f2f5")
        self.desktop.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)

    # ===================== 工具抽屉（所有添加功能整合） =====================
    def show_tool_drawer(self):
        drawer = tk.Toplevel(self)
        drawer.title("工具抽屉")
        drawer.geometry("400x500")
        drawer.resizable(False, False)
        drawer.configure(bg="#f0f2f5")

        tk.Label(drawer, text="添加图标/工具", font=("微软雅黑", 16, "bold"), bg="#f0f2f5").pack(pady=15)

        # 按钮样式
        btn_style = {"font": ("微软雅黑", 12), "width": 20, "bg": "#3498DB", "fg": "white", "relief": tk.FLAT}

        tk.Button(drawer, text="+ 添加BAT文件", command=self.add_bat, **btn_style).pack(pady=8)
        tk.Button(drawer, text="+ 生成EXE启动BAT", command=self.make_bat_for_exe, **btn_style).pack(pady=8)
        tk.Button(drawer, text="+ 添加UTC时钟", command=self.add_utc_clock, **btn_style).pack(pady=8)
        tk.Button(drawer, text="+ 添加秒表", command=lambda: self.add_tool("stopwatch"), **btn_style).pack(pady=8)
        tk.Button(drawer, text="+ 添加倒计时", command=lambda: self.add_tool("countdown"), **btn_style).pack(pady=8)
        tk.Button(drawer, text="⚙️ 设置提示音", command=self.set_alert_sound, **btn_style).pack(pady=8)

    # ===================== 顶部时钟 =====================
    def start_top_clock(self):
        self.top_time_label.config(text=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        self.after(1000, self.start_top_clock)

    # ===================== 提示音设置 =====================
    def set_alert_sound(self):
        global ALERT_SOUND
        path = filedialog.askopenfilename(filetypes=[("音频文件", "*.wav")])
        if path:
            ALERT_SOUND = path
            messagebox.showinfo("成功", "已设置自定义提示音")

    def play_alert(self):
        try:
            if ALERT_SOUND and os.path.exists(ALERT_SOUND):
                winsound.PlaySound(ALERT_SOUND, winsound.SND_FILENAME | winsound.SND_ASYNC)
            else:
                winsound.Beep(1200, 400)
                winsound.Beep(1600, 400)
        except:
            pass

    # ===================== 疲劳提醒 =====================
    def start_fatigue_reminder(self):
        def remind():
            self.play_alert()
            messagebox.showwarning("休息提醒", "已使用1小时，建议休息眼睛～")
            self.start_fatigue_reminder()
        try:
            self.fatigue_timer.cancel()
        except:
            pass
        self.fatigue_timer = Timer(3600, remind)
        self.fatigue_timer.daemon = True
        self.fatigue_timer.start()

    # ===================== 添加工具（修复：用sub_type区分） =====================
    def add_tool(self, sub_type):
        if sub_type == "stopwatch":
            self.apps.append({
                "type": "tool",
                "sub_type": "stopwatch",
                "name": "秒表"
            })
        elif sub_type == "countdown":
            self.apps.append({
                "type": "tool",
                "sub_type": "countdown",
                "name": "倒计时"
            })
        self.save_config()
        self.refresh_desktop()

    def add_utc_clock(self):
        offset_str = simpledialog.askstring("添加UTC时钟", "输入时区偏移（示例：+8、-5、0）:")
        if not offset_str:
            return
        try:
            offset = int(offset_str)
            if not (-12 <= offset <= 14):
                messagebox.showerror("错误", "请输入 -12 ~ +14")
                return
            self.apps.append({
                "type": "tool",
                "sub_type": "utc",
                "name": f"UTC{offset:+}",
                "offset": offset
            })
            self.save_config()
            self.refresh_desktop()
        except:
            messagebox.showerror("格式错误", "请输入数字，如 +8、-5")

    # ===================== 一键生成 EXE 启动 BAT =====================
    def make_bat_for_exe(self):
        exe_path = filedialog.askopenfilename(title="选择 EXE", filetypes=[("EXE", "*.exe")])
        if not exe_path:
            return
        name = os.path.splitext(os.path.basename(exe_path))[0]
        bat_path = os.path.join(APP_DIR, f"启动_{name}.bat")
        content = f'@echo off\nchcp 65001\necho 启动 {name}...\npushd "{os.path.dirname(exe_path)}"\nstart "" "{exe_path}"\npopd\nexit'
        with open(bat_path, "w", encoding="utf-8") as f:
            f.write(content)
        self.apps.append({"type": "bat", "name": f"启动{name}", "path": bat_path})
        self.save_config()
        self.refresh_desktop()
        messagebox.showinfo("成功", f"已生成启动脚本")

    def add_bat(self):
        path = filedialog.askopenfilename(title="选择 BAT", filetypes=[("BAT", "*.bat")])
        if not path:
            return
        name = os.path.basename(path).replace(".bat", "")
        self.apps.append({"type": "bat", "name": name, "path": path})
        self.save_config()
        self.refresh_desktop()

    # ===================== 图标菜单（…） =====================
    def show_menu(self, event, index):
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="重命名", command=lambda: self.rename_item(index))
        menu.add_command(label="删除", command=lambda: self.delete_item(index))
        menu.post(event.x_root, event.y_root)

    def rename_item(self, index):
        new = simpledialog.askstring("重命名", "新名称：")
        if new:
            self.apps[index]["name"] = new
            self.save_config()
            self.refresh_desktop()

    def delete_item(self, index):
        if messagebox.askyesno("删除", "确定删除？"):
            del self.apps[index]
            self.save_config()
            self.refresh_desktop()

    # ===================== 拖拽移动图标 =====================
    def on_drag_start(self, event, index, card):
        self.drag_data["x"] = event.x
        self.drag_data["y"] = event.y
        self.drag_data["item"] = card
        self.drag_data["index"] = index
        # 提升拖拽窗口层级
        card.lift()

    def on_drag_motion(self, event):
        if not self.drag_data["item"]:
            return
        dx = event.x - self.drag_data["x"]
        dy = event.y - self.drag_data["y"]
        x = self.drag_data["item"].winfo_x() + dx
        y = self.drag_data["item"].winfo_y() + dy
        self.drag_data["item"].place(x=x, y=y)

    def on_drag_end(self, event):
        if not self.drag_data["item"]:
            return
        # 获取当前位置，计算新的网格位置
        x = self.drag_data["item"].winfo_rootx() - self.desktop.winfo_rootx()
        y = self.drag_data["item"].winfo_rooty() - self.desktop.winfo_rooty()
        max_col = 5
        col = int(x / (self.desktop.winfo_width() / max_col))
        row = int(y / 100)
        col = max(0, min(col, max_col - 1))
        new_idx = row * max_col + col
        new_idx = max(0, min(new_idx, len(self.apps) - 1))

        # 交换位置
        old_idx = self.drag_data["index"]
        if new_idx != old_idx:
            self.apps.insert(new_idx, self.apps.pop(old_idx))
            self.save_config()

        # 重置拖拽数据，刷新界面
        self.drag_data = {"x": 0, "y": 0, "item": None, "index": -1}
        self.refresh_desktop()

    # ===================== 桌面卡片（修复：按sub_type渲染+拖拽） =====================
    def refresh_desktop(self):
        for w in self.desktop.winfo_children():
            w.destroy()

        row, col, max_col = 0, 0, 5
        for idx, item in enumerate(self.apps):
            card = tk.Frame(self.desktop, bg="white", bd=1, relief=tk.RIDGE, padx=8, pady=8)
            card.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")

            # 绑定拖拽事件
            card.bind("<Button-1>", lambda e, i=idx, c=card: self.on_drag_start(e, i, c))
            card.bind("<B1-Motion>", self.on_drag_motion)
            card.bind("<ButtonRelease-1>", self.on_drag_end)

            # … 菜单按钮
            menu_btn = tk.Label(card, text="⋮", font=("Arial", 12), bg="white", cursor="hand2")
            menu_btn.place(relx=0.9, rely=0.05, anchor="ne")
            menu_btn.bind("<Button-1>", lambda e, i=idx: self.show_menu(e, i))

            # 内容（按sub_type判断，不依赖name）
            if item["type"] == "bat":
                tk.Label(card, text="📄", font=("Arial", 30), bg="white").pack(pady=2)
                tk.Label(card, text=item["name"], font=("微软雅黑", 11), bg="white", wraplength=100).pack(pady=2)
                card.bind("<Button-1>", lambda e, i=item: self.run_bat(i), add="+")

            elif item["type"] == "tool":
                sub_type = item.get("sub_type", "")
                if sub_type == "utc":
                    self.create_utc_clock(card, item)
                elif sub_type == "stopwatch":
                    self.create_stopwatch(card)
                elif sub_type == "countdown":
                    self.create_countdown(card)

            col += 1
            if col >= max_col:
                col = 0
                row += 1

        for c in range(max_col):
            self.desktop.columnconfigure(c, weight=1)

    # ===================== UTC时钟 =====================
    def create_utc_clock(self, parent, item):
        offset = item["offset"]
        title = item["name"]
        tk.Label(parent, text=title, font=("微软雅黑", 11, "bold"), bg="white").pack(pady=(2,4))
        time_label = tk.Label(parent, text="00:00:00", font=("Consolas", 14), bg="white")
        time_label.pack(pady=(0,4))

        def update():
            utc_now = datetime.now(timezone.utc)
            t = utc_now + timedelta(hours=offset)
            time_label.config(text=t.strftime("%m-%d %H:%M:%S"))
            parent.after(1000, update)
        update()

    # ===================== 秒表（毫秒级） =====================
    def create_stopwatch(self, parent):
        tk.Label(parent, text="秒表", font=("微软雅黑", 11, "bold"), bg="white").pack(pady=(2,4))
        display = tk.Label(parent, text="00:00:00.000", font=("Consolas", 13), bg="white")
        display.pack(pady=(0,4))

        running = False
        start_t = 0
        elapsed = 0.0

        def tick():
            if running:
                dt = time.time() - start_t + elapsed
                h = int(dt//3600)
                m = int((dt%3600)//60)
                s = int(dt%60)
                ms = int((dt*1000)%1000)
                display.config(text=f"{h:02d}:{m:02d}:{s:02d}.{ms:03d}")
                parent.after(10, tick)

        def start():
            nonlocal running, start_t
            if not running:
                running = True
                start_t = time.time()
                tick()

        def stop():
            nonlocal running, elapsed
            running = False
            elapsed += time.time() - start_t

        def reset():
            nonlocal elapsed
            elapsed = 0.0
            display.config(text="00:00:00.000")

        bar = tk.Frame(parent, bg="white")
        bar.pack(fill=tk.X)
        tk.Button(bar, text="▶", width=2, command=start).pack(side=tk.LEFT, expand=True)
        tk.Button(bar, text="■", width=2, command=stop).pack(side=tk.LEFT, expand=True)
        tk.Button(bar, text="⟲", width=2, command=reset).pack(side=tk.LEFT, expand=True)

    # ===================== 倒计时（带声音） =====================
    def create_countdown(self, parent):
        tk.Label(parent, text="倒计时", font=("微软雅黑", 11, "bold"), bg="white").pack(pady=(2,4))
        display = tk.Label(parent, text="00:00:00", font=("Consolas", 14), bg="white")
        display.pack(pady=(0,4))

        total = 0
        timer = None

        def step():
            nonlocal total, timer
            if total <= 0:
                display.config(text="00:00:00")
                self.play_alert()
                messagebox.showinfo("完成", "时间到！")
                timer = None
                return
            h = total//3600
            m = (total%3600)//60
            s = total%60
            display.config(text=f"{h:02d}:{m:02d}:{s:02d}")
            total -= 1
            timer = parent.after(1000, step)

        def start():
            nonlocal total
            try:
                h = simpledialog.askinteger("时", "小时", minvalue=0, maxvalue=23) or 0
                m = simpledialog.askinteger("分", "分钟", minvalue=0, maxvalue=59) or 0
                s = simpledialog.askinteger("秒", "秒", minvalue=0, maxvalue=59) or 0
                total = h*3600 + m*60 + s
                if total>0:
                    step()
            except:
                pass

        def stop():
            nonlocal timer
            if timer:
                parent.after_cancel(timer)
                timer = None

        bar = tk.Frame(parent, bg="white")
        bar.pack(fill=tk.X)
        tk.Button(bar, text="▶", width=2, command=start).pack(side=tk.LEFT, expand=True)
        tk.Button(bar, text="■", width=2, command=stop).pack(side=tk.LEFT, expand=True)

    # ===================== 运行BAT =====================
    def run_bat(self, item):
        path = item.get("path")
        if not os.path.isfile(path):
            messagebox.showerror("错误", "文件不存在")
            return
        try:
            subprocess.Popen(
                path, cwd=os.path.dirname(path),
                shell=True, creationflags=subprocess.CREATE_NEW_CONSOLE
            )
        except Exception as e:
            messagebox.showerror("失败", str(e))

if __name__ == "__main__":
    app = Launcher()
    app.mainloop()