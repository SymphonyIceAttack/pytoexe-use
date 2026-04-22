#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tkinter as tk
from tkinter import messagebox, simpledialog, scrolledtext
import random
import time
import threading
import os
import sys
import win32api
import win32con
import win32file
from PIL import Image, ImageTk
import pystray
from io import BytesIO

# 初始人员名单
initial_names = [
    "鲍谷歌", "鲍文萱", "毕子昂", "蔡峻熙", "蔡欣瑜", "曹敬杨", "曹星瀚", "曹健", 
    "陈骏昕", "崔贤俊", "邓羽宸", "桂博岳", "郭奕晨", "洪高远", "黄梦怡", "靖永诚", 
    "黎孟翔", "李天诚", "刘明磊", "刘思颖", "刘以柯", "刘紫涵", "罗梦雪", "茆钰鸿", 
    "缪润慷", "潘紫萱", "强丽敏", "秦家浩", "秦卿", "盛泽宇", "宋欣雨", "孙沁萱", 
    "唐一晨", "陶乐云", "陶绮", "陶杨", "王明锐", "王泰格", "王欣悦", "汪学萍", 
    "王逸谦", "王雨涵", "王宇皓", "王雨桐", "王梓帆", "文靖涵", "吴紫昕", "夏浩岩", 
    "谢然", "许健翔", "许亦优", "许元非", "徐赵暄", "许志强", "尹吴子恒", "杨霏菲", 
    "杨添翼", "张瑞杨", "张伟杰", "张梓宸", "张子豪", "赵子琳", "朱祚弘", "宗钰晨"
]

ADMIN_PASSWORD = "20100826"
EXPECTED_KEY = "fiw379&*hiwu^fji12389jh@348f"

class RandomCallApp:
    def __init__(self, root):
        self.root = root
        self.root.title("班级随机点名系统")
        self.root.geometry("900x700")
        self.root.minsize(600, 500)
        
        # 状态变量
        self.names = initial_names.copy()
        self.picked_status = {name: False for name in self.names}
        self.person_priority = {name: 1 for name in self.names}  # 0:前 1:默认 2:后
        self.selected_count = 1
        self.is_picking = False
        self.history = []
        self.is_admin_verified = False
        self.tray = None
        self.mini_mode = False
        
        # 检查U盘
        self.check_usb_thread = threading.Thread(target=self.check_usb_loop, daemon=True)
        self.check_usb_thread.start()
        
        self.init_ui()
        
    def init_ui(self):
        # 顶部标题栏
        self.top_frame = tk.Frame(self.root, bg="#4a5568", height=30)
        self.top_frame.pack(fill=tk.X)
        
        # 左上角按钮
        self.btn_mini = tk.Button(self.top_frame, text="迷你模式", command=self.enter_mini_mode, 
                                 bg="#4a5568", fg="white", bd=0, relief=tk.FLAT)
        self.btn_mini.pack(side=tk.LEFT, padx=5, pady=5)
        
        self.btn_minimize = tk.Button(self.top_frame, text="最小化", command=self.minimize_to_tray, 
                                     bg="#4a5568", fg="white", bd=0, relief=tk.FLAT)
        self.btn_minimize.pack(side=tk.LEFT, padx=5, pady=5)
        
        # 标题
        title_label = tk.Label(self.top_frame, text="班级随机点名系统", bg="#4a5568", fg="white", font=("Microsoft YaHei", 10, "bold"))
        title_label.pack(side=tk.LEFT, expand=True)
        
        # 主内容区
        self.main_frame = tk.Frame(self.root, bg="#667eea")
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 名字显示区
        self.name_display_frame = tk.Frame(self.main_frame, bg="#667eea")
        self.name_display_frame.pack(fill=tk.X, pady=10)
        
        self.name_display = tk.Label(self.name_display_frame, text="准备开始点名", 
                                    bg="#667eea", fg="white", font=("Microsoft YaHei", 32, "bold"))
        self.name_display.pack()
        
        # 人员名单
        self.person_frame_label = tk.Label(self.main_frame, text="人员名单：", bg="#667eea", fg="white", font=("Microsoft YaHei", 10))
        self.person_frame_label.pack(anchor=tk.W)
        
        self.person_canvas = tk.Canvas(self.main_frame, bg="rgba(0,0,0,0.1)", bd=0, highlightthickness=0)
        self.person_canvas.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.person_scroll = tk.Scrollbar(self.main_frame, orient=tk.VERTICAL, command=self.person_canvas.yview)
        self.person_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        self.person_canvas.configure(yscrollcommand=self.person_scroll.set)
        
        self.person_inner = tk.Frame(self.person_canvas, bg="rgba(0,0,0,0.1)")
        self.person_canvas.create_window((0,0), window=self.person_inner, anchor=tk.NW)
        
        # 历史记录
        self.history_label = tk.Label(self.main_frame, text="抽取历史：", bg="#667eea", fg="white", font=("Microsoft YaHei", 10))
        self.history_label.pack(anchor=tk.W, pady=(10, 0))
        
        self.history_frame = tk.Frame(self.main_frame, bg="rgba(0,0,0,0.1)")
        self.history_frame.pack(fill=tk.X, pady=5)
        
        # 底部控制区
        self.control_frame = tk.Frame(self.root, bg="#4a5568", pady=10)
        self.control_frame.pack(fill=tk.X)
        
        # 人数选择
        count_frame = tk.Frame(self.control_frame, bg="#4a5568")
        count_frame.pack()
        
        tk.Label(count_frame, text="抽取人数：", bg="#4a5568", fg="white").pack(side=tk.LEFT, padx=5)
        
        self.count_buttons = []
        for i in range(1,7):
            btn = tk.Button(count_frame, text=str(i), command=lambda c=i: self.select_count(c),
                           bg="rgba(255,255,255,0.2)", fg="white", bd=0, relief=tk.FLAT, padx=15, pady=5)
            btn.pack(side=tk.LEFT, padx=2)
            self.count_buttons.append(btn)
        
        self.select_count(1)
        
        # 抽取按钮
        self.pick_btn = tk.Button(self.control_frame, text="开始抽取", command=self.start_pick,
                                 bg="rgba(255,255,255,0.3)", fg="white", bd=0, relief=tk.FLAT, 
                                 font=("Microsoft YaHei", 12, "bold"), padx=30, pady=8)
        self.pick_btn.pack(pady=10)
        
        # 更新人员网格
        self.update_person_grid()
        
        # 绑定窗口大小变化
        self.root.bind("<Configure>", self.on_resize)
        
    def on_resize(self, event):
        # 调整网格布局
        self.update_person_grid()
        # 更新滚动区域
        self.person_inner.update_idletasks()
        self.person_canvas.config(scrollregion=self.person_canvas.bbox("all"))
        
    def update_person_grid(self):
        # 清空网格
        for widget in self.person_inner.winfo_children():
            widget.destroy()
            
        # 计算列数，根据窗口大小
        window_width = self.root.winfo_width()
        col_count = max(4, min(10, window_width // 120))
        
        # 添加人员
        row = 0
        col = 0
        for name in self.names:
            is_picked = self.picked_status[name]
            bg_color = "rgba(0,0,0,0.3)" if is_picked else "rgba(255,255,255,0.2)"
            fg_color = "rgba(255,255,255,0.5)" if is_picked else "white"
            font = ("Microsoft YaHei", 10)
            
            btn = tk.Button(self.person_inner, text=name, bg=bg_color, fg=fg_color,
                          bd=0, relief=tk.FLAT, padx=8, pady=8, font=font,
                          command=lambda n=name: self.on_person_click(n))
            if is_picked:
                btn.config(font=("Microsoft YaHei", 10, "normal"))
                # 添加删除线，这里用文本的方式，因为tkinter的按钮不好加，所以用标签？不对，用标签代替按钮
                btn.destroy()
                lbl = tk.Label(self.person_inner, text=name, bg=bg_color, fg=fg_color,
                             padx=8, pady=8, font=("Microsoft YaHei", 10))
                lbl.bind("<Button-1>", lambda e, n=name: self.on_person_click(n))
                lbl.grid(row=row, column=col, padx=4, pady=4, sticky=tk.NSEW)
            else:
                btn.grid(row=row, column=col, padx=4, pady=4, sticky=tk.NSEW)
            
            col += 1
            if col >= col_count:
                col = 0
                row += 1
                
        # 添加添加按钮
        add_btn = tk.Button(self.person_inner, text="+", bg="transparent", fg="white",
                          bd=2, relief=tk.DASHED, padx=8, pady=8, font=("Microsoft YaHei", 14),
                          command=self.on_add_click)
        add_btn.grid(row=row, column=col, padx=4, pady=4, sticky=tk.NSEW)
        
        # 更新滚动
        self.person_inner.update_idletasks()
        self.person_canvas.config(scrollregion=self.person_canvas.bbox("all"))
        
    def select_count(self, count):
        self.selected_count = count
        for i, btn in enumerate(self.count_buttons):
            if i+1 == count:
                btn.config(bg="rgba(255,255,255,0.5)")
            else:
                btn.config(bg="rgba(255,255,255,0.2)")
                
    def shuffle_with_priority(self, available):
        # 按优先级分组
        high = [n for n in available if self.person_priority[n] == 0]
        normal = [n for n in available if self.person_priority[n] == 1]
        low = [n for n in available if self.person_priority[n] == 2]
        
        random.shuffle(high)
        random.shuffle(normal)
        random.shuffle(low)
        
        return high + normal + low
        
    def start_pick(self):
        if self.is_picking:
            return
            
        available = [n for n in self.names if not self.picked_status[n]]
        
        if len(available) == 0:
            messagebox.showinfo("提示", "所有人员都已抽取完毕，即将重置抽取状态！")
            for name in self.names:
                self.picked_status[name] = False
            self.update_person_grid()
            return
            
        actual_count = self.selected_count
        if len(available) < self.selected_count:
            actual_count = len(available)
            
        self.is_picking = True
        self.pick_btn.config(state=tk.DISABLED)
        for btn in self.count_buttons:
            btn.config(state=tk.DISABLED)
            
        start_time = time.time()
        
        def pick_animation():
            while time.time() - start_time < 0.8:
                random_names = random.sample(self.names, min(actual_count, len(self.names)))
                self.name_display.config(text="、".join(random_names))
                time.sleep(0.05)
                self.root.update()
                
            # 完成抽取
            shuffled = self.shuffle_with_priority(available)
            picked = shuffled[:actual_count]
            
            for name in picked:
                self.picked_status[name] = True
                
            self.name_display.config(text="、".join(picked))
            
            # 添加历史
            t = time.strftime("%H:%M:%S")
            self.history.insert(0, f"[{t}] {','.join(picked)}")
            
            # 更新历史显示
            for widget in self.history_frame.winfo_children():
                widget.destroy()
            for item in self.history[:20]:
                lbl = tk.Label(self.history_frame, text=item, bg="rgba(255,255,255,0.1)", fg="white",
                             padx=8, pady=4, font=("Microsoft YaHei", 9))
                lbl.pack(side=tk.LEFT, padx=2, pady=2)
                
            # 更新人员网格
            self.update_person_grid()
            
            self.is_picking = False
            self.pick_btn.config(state=tk.NORMAL)
            for btn in self.count_buttons:
                btn.config(state=tk.NORMAL)
                
        threading.Thread(target=pick_animation, daemon=True).start()
        
    def on_person_click(self, name):
        if not self.is_admin_verified:
            # 验证管理员
            pwd = simpledialog.askstring("管理员验证", "请输入管理员密码：", show='*')
            if pwd == ADMIN_PASSWORD:
                self.is_admin_verified = True
            else:
                # 检查U盘
                if self.check_usb_key():
                    self.is_admin_verified = True
                else:
                    messagebox.showerror("错误", "密码错误！")
                    return
                    
        # 打开优先级调整
        self.open_priority_window(name)
        
    def on_add_click(self):
        if not self.is_admin_verified:
            pwd = simpledialog.askstring("管理员验证", "请输入管理员密码：", show='*')
            if pwd == ADMIN_PASSWORD:
                self.is_admin_verified = True
            else:
                if self.check_usb_key():
                    self.is_admin_verified = True
                else:
                    messagebox.showerror("错误", "密码错误！")
                    return
                    
        # 批量添加
        self.open_batch_add_window()
        
    def open_priority_window(self, name):
        win = tk.Toplevel(self.root)
        win.title("调整抽取优先级")
        win.geometry("400x200")
        win.resizable(False, False)
        
        tk.Label(win, text=f"调整 {name} 的抽取顺序：", font=("Microsoft YaHei", 12)).pack(pady=10)
        
        priority = tk.IntVar(value=self.person_priority[name])
        
        slider = tk.Scale(win, from_=0, to=2, orient=tk.HORIZONTAL, variable=priority,
                         showvalue=0, length=300, resolution=1)
        slider.pack()
        
        label_frame = tk.Frame(win)
        label_frame.pack(fill=tk.X, padx=20)
        tk.Label(label_frame, text="较前").pack(side=tk.LEFT)
        tk.Label(label_frame, text="默认").pack(side=tk.LEFT, expand=True)
        tk.Label(label_frame, text="较后").pack(side=tk.RIGHT)
        
        def save():
            self.person_priority[name] = priority.get()
            win.destroy()
            
        def delete():
            if messagebox.askyesno("确认", f"确定要删除 {name} 吗？"):
                self.names.remove(name)
                del self.picked_status[name]
                del self.person_priority[name]
                self.update_person_grid()
                win.destroy()
                
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=10, padx=20)
        
        tk.Button(btn_frame, text="删除", command=delete, bg="red", fg="white").pack(side=tk.LEFT)
        tk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="保存", command=save, bg="#007bff", fg="white").pack(side=tk.RIGHT)
        
    def open_batch_add_window(self):
        win = tk.Toplevel(self.root)
        win.title("批量添加人员")
        win.geometry("400x300")
        
        tk.Label(win, text="请输入人员姓名，每行一个：").pack(anchor=tk.W, padx=10, pady=5)
        
        text = scrolledtext.ScrolledText(win, width=40, height=10)
        text.pack(padx=10, pady=5, fill=tk.BOTH, expand=True)
        
        def add():
            content = text.get("1.0", tk.END).strip()
            if content:
                new_names = [n.strip() for n in content.splitlines() if n.strip()]
                for name in new_names:
                    if name not in self.names:
                        self.names.append(name)
                        self.picked_status[name] = False
                        self.person_priority[name] = 1
                self.update_person_grid()
            win.destroy()
            
        btn_frame = tk.Frame(win)
        btn_frame.pack(fill=tk.X, pady=10, padx=10)
        tk.Button(btn_frame, text="取消", command=win.destroy).pack(side=tk.RIGHT, padx=5)
        tk.Button(btn_frame, text="添加", command=add, bg="#007bff", fg="white").pack(side=tk.RIGHT)
        
    def check_usb_key(self):
        # 检查所有驱动器
        drives = win32api.GetLogicalDrives()
        for i in range(26):
            if drives & (1 << i):
                drive = chr(ord('A') + i) + ':\\'
                key_path = os.path.join(drive, 'password.key')
                try:
                    if os.path.exists(key_path):
                        with open(key_path, 'r', encoding='utf-8') as f:
                            content = f.read().strip()
                            if content == EXPECTED_KEY:
                                return True
                except:
                    pass
        return False
        
    def check_usb_loop(self):
        while True:
            if not self.is_admin_verified:
                if self.check_usb_key():
                    self.is_admin_verified = True
                    self.root.after(0, lambda: messagebox.showinfo("提示", "U盘验证成功，已解锁管理员功能！"))
            time.sleep(1)
            
    def enter_mini_mode(self):
        self.mini_mode = True
        self.root.withdraw()
        
        mini_win = tk.Toplevel(self.root)
        mini_win.title("迷你点名")
        mini_win.geometry("300x200")
        mini_win.attributes('-topmost', True)
        mini_win.overrideredirect(True)
        
        def restore():
            mini_win.destroy()
            self.root.deiconify()
            self.mini_mode = False
            
        tk.Button(mini_win, text="恢复", command=restore, bg="#4a5568", fg="white").pack(anchor=tk.E, padx=5, pady=5)
        
        name_display = tk.Label(mini_win, text="准备开始点名", font=("Microsoft YaHei", 16, "bold"),
                               bg="#667eea", fg="white")
        name_display.pack(pady=10)
        
        count_frame = tk.Frame(mini_win, bg="#667eea")
        count_frame.pack()
        
        selected = tk.IntVar(value=1)
        
        for i in range(1,4):
            tk.Radiobutton(count_frame, text=str(i), variable=selected, value=i,
                          bg="#667eea", fg="white", selectcolor="#4a5568").pack(side=tk.LEFT, padx=5)
                          
        def mini_pick():
            available = [n for n in self.names if not self.picked_status[n]]
            if len(available) == 0:
                messagebox.showinfo("提示", "所有人员都已抽取完毕，即将重置！")
                for name in self.names:
                    self.picked_status[name] = False
                self.update_person_grid()
                return
                
            count = selected.get()
            actual = min(count, len(available))
            
            shuffled = self.shuffle_with_priority(available)
            picked = shuffled[:actual]
            
            for name in picked:
                self.picked_status[name] = True
                
            name_display.config(text="、".join(picked))
            
        tk.Button(mini_win, text="开始抽取", command=mini_pick,
                 bg="rgba(255,255,255,0.3)", fg="white").pack(pady=10)
                 
        mini_win.config(bg="#667eea")
        
    def set_auto_start(self, enable):
        # 设置开机自启动
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_WRITE)
        exe_path = os.path.abspath(sys.executable)
        if enable:
            # 开机自启动，并且最小化到托盘
            winreg.SetValueEx(key, "RandomCall", 0, winreg.REG_SZ, f'"{exe_path}" --minimize')
            self.auto_start_enabled = True
        else:
            try:
                winreg.DeleteValue(key, "RandomCall")
            except:
                pass
            self.auto_start_enabled = False
        winreg.CloseKey(key)
        
    def minimize_to_tray(self):
        self.root.withdraw()
        
        # 加载图标
        icon_path = os.path.join(os.path.dirname(sys.executable), 'icon.ico')
        if not os.path.exists(icon_path):
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            
        # 默认用一个简单的图标
        def on_restore(icon, item):
            icon.stop()
            self.root.deiconify()
            
        def on_toggle_auto_start(icon, item):
            self.set_auto_start(not self.auto_start_enabled)
            # 更新菜单
            icon.update_menu()
            
        def on_exit(icon, item):
            icon.stop()
            self.root.quit()
            
        # 检查当前是否已经开启自启动
        self.auto_start_enabled = False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Run", 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, "RandomCall")
            if value:
                self.auto_start_enabled = True
            winreg.CloseKey(key)
        except:
            pass
            
        image = Image.new('RGB', (64, 64), color=(102, 126, 234))
        self.tray = pystray.Icon("random_call", image, "班级随机点名", menu=pystray.Menu(
            pystray.MenuItem("打开", on_restore),
            pystray.MenuItem("开机自启动", on_toggle_auto_start, checked=lambda item: self.auto_start_enabled),
            pystray.MenuItem("退出", on_exit)
        ))
        self.tray.run_detached()

if __name__ == "__main__":
    root = tk.Tk()
    app = RandomCallApp(root)
    
    # 检查启动参数，如果是--minimize，就直接最小化到托盘
    if len(sys.argv) > 1 and sys.argv[1] == '--minimize':
        root.withdraw()
        app.minimize_to_tray()
    
    root.mainloop()

