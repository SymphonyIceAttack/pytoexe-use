import os, sys, tempfile, subprocess, ctypes, platform, tkinter as tk

# ========== 环境 / API ==========
if platform.system() != "Windows":
    print("仅支持 Windows"); sys.exit(1)

class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
        ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]

def get_memory_info():
    s = MEMORYSTATUSEX()
    s.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(s))
    return s.ullTotalPhys/(1024**3), s.ullAvailPhys/(1024**3), s.dwMemoryLoad

def try_release_memory():
    try:
        ctypes.windll.kernel32.SetProcessWorkingSetSize(-1, -1, -1)
        return True
    except: return False

def size_fmt(b):
    for u in ('B','KB','MB','GB'):
        if b < 1024: return f"{b:.1f} {u}"
        b /= 1024
    return f"{b:.1f} TB"

# ========== 自定义组件 ==========
class ModernButton(tk.Canvas):
    """圆角扁平按钮"""
    def __init__(self, parent, text, command, width=120, height=36, radius=18,
                 bg="#ffffff", fg="#2d3436", hover_bg="#e9ecef", active_bg="#dee2e6", **kw):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                         highlightthickness=0, bd=0, **kw)
        self.command = command
        self.radius = radius
        self.colors = {"normal": bg, "hover": hover_bg, "active": active_bg}
        self.fg = fg
        self.text_str = text
        self.w, self.h = width, height
        self.state = "normal"
        self._draw(bg)
        self.bind("<Enter>", lambda e: self._hover())
        self.bind("<Leave>", lambda e: self._leave())
        self.bind("<Button-1>", lambda e: self._click())
        self.bind("<ButtonRelease-1>", lambda e: self._release())

    def _draw(self, bg_color):
        self.delete("all")
        r = self.radius
        w, h = self.w, self.h
        self._round_rect(0, 0, w, h, r, fill=bg_color, outline="")
        self.create_text(w/2, h/2, text=self.text_str, fill=self.fg,
                         font=("Segoe UI", 10, "bold"))

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r,
                  x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        self.create_polygon(points, smooth=True, **kw)

    def _hover(self):
        if self.state == "normal": self._draw(self.colors["hover"])

    def _leave(self):
        if self.state == "normal": self._draw(self.colors["normal"])

    def _click(self):
        self.state = "clicked"
        self._draw(self.colors["active"])

    def _release(self):
        self.state = "normal"
        self._draw(self.colors["normal"])
        if self.command: self.command()

    def set_active(self, is_active):
        """导航按钮高亮切换"""
        if is_active:
            self._draw("#0984e3")
            self.itemconfig("all", fill="white")
        else:
            self._draw(self.colors["normal"])
            self.itemconfig("all", fill=self.fg)

class RoundedFrame(tk.Canvas):
    """带阴影的圆角卡片，内部 frame 自动填充"""
    def __init__(self, parent, width=700, height=450, radius=20, bg="#ffffff", shadow_color="#cfd8dc", **kw):
        super().__init__(parent, width=width, height=height, bg=parent["bg"],
                         highlightthickness=0, bd=0, **kw)
        self.radius = radius
        self.bg = bg
        # 阴影
        self._round_rect(4, 4, width-4, height-4, radius, fill=shadow_color, outline="")
        # 白色卡片
        self._round_rect(0, 0, width, height, radius, fill=bg, outline="")
        # 内部框架
        self.inner = tk.Frame(self, bg=bg)
        self.create_window(0, 0, window=self.inner, anchor="nw",
                           width=width, height=height)

    def _round_rect(self, x1, y1, x2, y2, r, **kw):
        points = [x1+r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y2-r,
                  x2, y2, x2-r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y1+r, x1, y1]
        self.create_polygon(points, smooth=True, **kw)

class CircleProgress(tk.Canvas):
    def __init__(self, parent, size=150, thickness=12, bg="#ffffff", **kw):
        super().__init__(parent, width=size, height=size, bg=bg, highlightthickness=0, **kw)
        self.size = size
        self.thickness = thickness
        self.draw(0)

    def draw(self, percent):
        self.delete("all")
        d = self.thickness
        w = self.size
        self.create_arc(d, d, w-d, w-d, outline="#eceff1", width=d, style="arc", start=90, extent=360)
        angle = 360 * percent / 100
        if angle > 0:
            self.create_arc(d, d, w-d, w-d, outline="#0984e3", width=d, style="arc", start=90, extent=-angle)

# ========== 功能页面 ==========
class SystemInfoPage(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.canvas = CircleProgress(self, size=150, thickness=12, bg=bg)
        self.canvas.pack(pady=(30,10))
        self.percent_var = tk.StringVar(value="0%")
        tk.Label(self, textvariable=self.percent_var, font=("Segoe UI",24,"bold"),
                 fg="#2d3436", bg=bg).pack()
        self.info_var = tk.StringVar()
        tk.Label(self, textvariable=self.info_var, font=("Segoe UI",11),
                 fg="#636e72", bg=bg).pack(pady=10)
        ModernButton(self, text="刷新", command=self.refresh, width=100,
                     bg="#0984e3", fg="white", hover_bg="#0773c5", active_bg="#0665ad").pack(pady=20)
        self.refresh()

    def refresh(self):
        try:
            total, avail, load = get_memory_info()
            self.canvas.draw(load)
            self.percent_var.set(f"{load}% 已用")
            self.info_var.set(f"总内存 {total:.1f} GB\n可用 {avail:.1f} GB\n已用 {total-avail:.1f} GB")
        except Exception as e:
            self.info_var.set(f"错误: {e}")

class TempCleanerPage(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.temp_path = tempfile.gettempdir()
        tk.Label(self, text=f"📁 {self.temp_path}", font=("Segoe UI",9), fg="#636e72",
                 bg=bg, wraplength=500, justify="center").pack(pady=30)
        self.status_var = tk.StringVar(value="准备就绪")
        tk.Label(self, textvariable=self.status_var, font=("Segoe UI",11),
                 fg="#636e72", bg=bg).pack(pady=10)
        ModernButton(self, text="清理临时文件", command=self.clean, width=160,
                     bg="#00b894", fg="white", hover_bg="#00a381", active_bg="#009170").pack(pady=20)

    def clean(self):
        deleted, freed = 0, 0
        self.status_var.set("正在清理...")
        self.update()
        for root, dirs, files in os.walk(self.temp_path, topdown=False):
            for name in files:
                p = os.path.join(root, name)
                try:
                    freed += os.path.getsize(p); os.remove(p); deleted += 1
                except: pass
            for name in dirs:
                try: shutil.rmtree(os.path.join(root, name), ignore_errors=True)
                except: pass
        self.status_var.set(f"✅ 完成！{deleted} 个文件，释放 {size_fmt(freed)}")

class MemoryOptPage(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        self.result_var = tk.StringVar()
        tk.Label(self, textvariable=self.result_var, font=("Segoe UI",11),
                 fg="#636e72", bg=bg).pack(pady=40)
        ModernButton(self, text="执行内存优化", command=self.optimize, width=150,
                     bg="#6c5ce7", fg="white", hover_bg="#5a4bd1", active_bg="#4a3bb8").pack(pady=10)

    def optimize(self):
        if try_release_memory():
            self.result_var.set("优化已触发，请查看任务管理器")
        else:
            self.result_var.set("调用失败，可能需要管理员权限")

class NetworkToolsPage(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        btns = [("刷新 DNS 缓存", "ipconfig /flushdns"),
                ("重置 Winsock", "netsh winsock reset"),
                ("重置 IP 协议", "netsh int ip reset")]
        for text, cmd in btns:
            ModernButton(self, text=text, command=lambda c=cmd: self.run(c),
                         width=180, bg="#f0f3f7", fg="#2d3436", hover_bg="#e0e5ec").pack(pady=5)

        self.output = tk.Text(self, height=8, bg="white", fg="#2d3436", relief="flat",
                              borderwidth=1, font=("Consolas",10), padx=10, pady=10)
        self.output.pack(fill="both", expand=True, pady=(20,0))
        self.output.insert("1.0", "命令输出将显示在这里...\n")
        self.output.config(state="disabled")

    def run(self, cmd):
        self.output.config(state="normal")
        self.output.insert("end", f"\n> {cmd}\n")
        try:
            p = subprocess.run(cmd, shell=True, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, universal_newlines=True)
            if p.returncode == 0:
                self.output.insert("end", (p.stdout or "成功")+"\n", "success")
            else:
                self.output.insert("end", f"失败 (码{p.returncode}): {p.stderr}\n", "error")
        except Exception as e:
            self.output.insert("end", f"异常: {e}\n", "error")
        self.output.config(state="disabled")
        self.output.see("end")
        self.output.tag_config("success", foreground="#00b894")
        self.output.tag_config("error", foreground="#d63031")

class StartupManagerPage(tk.Frame):
    def __init__(self, parent, bg):
        super().__init__(parent, bg=bg)
        appdata = os.getenv('APPDATA') or os.path.expanduser('~')
        programdata = os.getenv('PROGRAMDATA') or 'C:\\ProgramData'
        self.user_startup = os.path.join(appdata, r'Microsoft\Windows\Start Menu\Programs\Startup')
        self.common_startup = os.path.join(programdata, r'Microsoft\Windows\Start Menu\Programs\StartUp')

        top_frm = tk.Frame(self, bg=bg)
        top_frm.pack(fill="x", pady=(0,10))

        left = tk.LabelFrame(top_frm, text="当前用户", bg=bg, font=("Segoe UI",9,"bold"))
        left.pack(side="left", fill="both", expand=True, padx=(0,5))
        self.user_list = tk.Listbox(left, bg="white", relief="flat", borderwidth=1,
                                    font=("Segoe UI",10), selectbackground="#74b9ff")
        self.user_list.pack(fill="both", expand=True, padx=8, pady=8)

        right = tk.LabelFrame(top_frm, text="所有用户", bg=bg, font=("Segoe UI",9,"bold"))
        right.pack(side="right", fill="both", expand=True, padx=(5,0))
        self.common_list = tk.Listbox(right, bg="white", relief="flat", borderwidth=1,
                                      font=("Segoe UI",10), selectbackground="#74b9ff")
        self.common_list.pack(fill="both", expand=True, padx=8, pady=8)

        btn_frm = tk.Frame(self, bg=bg)
        btn_frm.pack(fill="x", pady=10)
        ModernButton(btn_frm, text="删除选中项 (用户)", command=lambda: self.del_sel(self.user_startup, self.user_list),
                     bg="#e17055", fg="white", hover_bg="#d63031", active_bg="#c0392b").pack(side="left", padx=5)
        ModernButton(btn_frm, text="删除选中项 (公共)", command=lambda: self.del_sel(self.common_startup, self.common_list),
                     bg="#e17055", fg="white", hover_bg="#d63031", active_bg="#c0392b").pack(side="left", padx=5)
        ModernButton(btn_frm, text="刷新列表", command=self.refresh, bg="#dfe6e9", fg="#2d3436",
                     hover_bg="#b2bec3").pack(side="right", padx=5)
        self.refresh()

    def refresh(self):
        for lst, path in [(self.user_list, self.user_startup), (self.common_list, self.common_startup)]:
            lst.delete(0, "end")
            if os.path.isdir(path):
                try:
                    for name in sorted(os.listdir(path)):
                        if os.path.isfile(os.path.join(path, name)):
                            lst.insert("end", name)
                except Exception as e:
                    lst.insert("end", f"读取失败: {e}")

    def del_sel(self, base, listbox):
        sel = listbox.curselection()
        if not sel:
            tk.messagebox.showwarning("提示", "请先选中一个启动项")
            return
        fname = listbox.get(sel[0])
        fpath = os.path.join(base, fname)
        if tk.messagebox.askyesno("确认", f"删除 {fname} ?"):
            try:
                os.remove(fpath)
                listbox.delete(sel[0])
                tk.messagebox.showinfo("完成", "已删除")
            except Exception as e:
                tk.messagebox.showerror("错误", str(e))

# ========== 主程序 ==========
class ModernApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("系统优化工具箱")
        self.geometry("800x600")
        self.configure(bg="#f5f7fa")

        # 顶部标题栏
        title_bar = tk.Frame(self, bg="#ffffff", height=50)
        title_bar.pack(fill="x")
        tk.Label(title_bar, text="系统优化工具箱", font=("Segoe UI",16,"bold"),
                 fg="#2d3436", bg="#ffffff").pack(side="left", padx=20, pady=10)

        # 导航栏
        nav = tk.Frame(self, bg="#f5f7fa", height=50)
        nav.pack(fill="x", padx=30, pady=(10,0))

        self.pages = {}       # 存储 (卡片, 页面)
        self.nav_btns = {}    # 导航按钮对象

        # 页面容器
        container = tk.Frame(self, bg="#f5f7fa")
        container.pack(fill="both", expand=True, padx=30, pady=20)

        # 定义页面
        page_defs = [
            ("系统信息", SystemInfoPage),
            ("磁盘清理", TempCleanerPage),
            ("内存优化", MemoryOptPage),
            ("网络工具", NetworkToolsPage),
            ("启动项管理", StartupManagerPage),
        ]

        for name, cls in page_defs:
            card = RoundedFrame(container, width=700, height=450, bg="#ffffff")
            page = cls(card.inner, bg="#ffffff")
            # ✅ 关键修复：将页面填充到卡片内部
            page.pack(fill="both", expand=True)
            self.pages[name] = (card, page)

            btn = ModernButton(nav, text=name, command=lambda n=name: self.show_page(n),
                               width=100, bg="#dfe6e9", fg="#2d3436",
                               hover_bg="#b2bec3", active_bg="#0984e3")
            btn.pack(side="left", padx=5)
            self.nav_btns[name] = btn

        self.show_page("系统信息")

    def show_page(self, name):
        # 隐藏所有卡片
        for card, _ in self.pages.values():
            card.pack_forget()
        # 显示选中的卡片
        card, _ = self.pages[name]
        card.pack(fill="both", expand=True)

        # 高亮导航按钮
        for btn_name, btn in self.nav_btns.items():
            btn.set_active(btn_name == name)

if __name__ == "__main__":
    app = ModernApp()
    app.mainloop()