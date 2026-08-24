import tkinter as tk
from tkinter import ttk
import os

class AccountHelper:
    def __init__(self, root):
        self.root = root
        self.root.title("账号助手")
        self.root.overrideredirect(True)  # 无边框，实现悬浮感
        self.root.wm_attributes('-topmost', True)  # 窗口置顶
        
        # 可爱清爽配色
        self.fab_color = "#FF9A9E"      # 粉色悬浮球
        self.card_color = "#FFFFFF"     # 白色卡片
        self.text_color = "#57606F"     # 深灰文字
        self.btn_user = "#74B9FF"       # 蓝色按钮
        self.btn_pass = "#FF6B81"       # 红色按钮
        self.hover_color = "#FF4757"
        
        self.root.configure(bg=self.fab_color)
        
        self.is_expanded = False
        self.accounts = []
        
        # 屏幕右下角定位
        self.screen_w = self.root.winfo_screenwidth()
        self.screen_h = self.root.winfo_screenheight()
        self.collapsed_size = (60, 60)
        self.expanded_size = (320, 450)
        
        self.update_pos_collapsed()
        self.root.geometry(f"{self.collapsed_size[0]}x{self.collapsed_size[1]}")
        
        self.create_widgets()
        self.load_accounts()

    def update_pos_collapsed(self):
        x = self.screen_w - self.collapsed_size[0] - 20
        y = self.screen_h - self.collapsed_size[1] - 60
        self.root.geometry(f"+{x}+{y}")

    def update_pos_expanded(self):
        x = self.screen_w - self.expanded_size[0] - 20
        y = self.screen_h - self.expanded_size[1] - 60
        self.root.geometry(f"+{x}+{y}")

    def create_widgets(self):
        # 悬浮球
        self.fab = tk.Label(self.root, text="🐾", font=("Arial", 24), 
                           bg=self.fab_color, fg="white",
                           width=4, height=2, cursor="hand2")
        self.fab.pack(fill=tk.BOTH, expand=True)
        self.fab.bind("<Button-1>", self.toggle_card)
        
        # 展开后的卡片
        self.card_frame = tk.Frame(self.root, bg=self.card_color)

        # 头部
        header = tk.Frame(self.card_frame, bg=self.card_color)
        header.pack(fill=tk.X, padx=15, pady=(15, 5))
        tk.Label(header, text="✨ 我的账号本", font=("Microsoft YaHei", 14, "bold"), 
                bg=self.card_color, fg=self.btn_pass).pack(side=tk.LEFT)
        
        close_btn = tk.Label(header, text="✕", font=("Arial", 12, "bold"), 
                            bg=self.btn_pass, fg="white", width=2, height=1, cursor="hand2")
        close_btn.pack(side=tk.RIGHT)
        close_btn.bind("<Button-1>", self.toggle_card)
        close_btn.bind("<Enter>", lambda e: close_btn.configure(bg=self.hover_color))
        close_btn.bind("<Leave>", lambda e: close_btn.configure(bg=self.btn_pass))

        # 可滚动列表
        self.list_canvas = tk.Canvas(self.card_frame, bg=self.card_color, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self.card_frame, orient="vertical", command=self.list_canvas.yview)
        self.scrollable_frame = tk.Frame(self.list_canvas, bg=self.card_color)
        
        self.scrollable_frame.bind("<Configure>", lambda e: self.list_canvas.configure(scrollregion=self.list_canvas.bbox("all")))
        self.list_canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.list_canvas.configure(yscrollcommand=scrollbar.set)
        
        self.list_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=15, pady=5)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 刷新按钮
        refresh_btn = tk.Button(self.card_frame, text="🔄 刷新列表", command=self.load_accounts,
                               bg=self.btn_pass, fg="white", relief="flat", 
                               font=("Microsoft YaHei", 10), cursor="hand2")
        refresh_btn.pack(fill=tk.X, padx=15, pady=(5, 15))

    def toggle_card(self, event=None):
        if self.is_expanded:
            self.card_frame.pack_forget()
            self.fab.pack(fill=tk.BOTH, expand=True)
            self.root.configure(bg=self.fab_color)
            self.root.geometry(f"{self.collapsed_size[0]}x{self.collapsed_size[1]}")
            self.update_pos_collapsed()
            self.is_expanded = False
        else:
            self.fab.pack_forget()
            self.card_frame.pack(fill=tk.BOTH, expand=True)
            self.root.configure(bg=self.card_color)
            self.root.geometry(f"{self.expanded_size[0]}x{self.expanded_size[1]}")
            self.update_pos_expanded()
            self.is_expanded = True
            self.render_accounts()

    def load_accounts(self):
        self.accounts = []
        # 获取 exe 或 py 文件所在目录
        base_path = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_path, "accounts.txt")
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        parts = line.split(',')
                        if len(parts) >= 3:
                            self.accounts.append({"name": parts[0], "user": parts[1], "pass": parts[2]})
        if self.is_expanded:
            self.render_accounts()

    def render_accounts(self):
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
            
        if not self.accounts:
            tk.Label(self.scrollable_frame, text="暂无账号，请编辑 accounts.txt", 
                    bg=self.card_color, fg="#A4B0BE").pack(pady=20)
            return
            
        for acc in self.accounts:
            item = tk.Frame(self.scrollable_frame, bg="#FFF9FA", relief="solid", bd=1)
            item.pack(fill=tk.X, pady=5)
            
            tk.Label(item, text=f"📌 {acc['name']}", font=("Microsoft YaHei", 11, "bold"), 
                    bg="#FFF9FA", fg=self.text_color).pack(anchor="w", padx=10, pady=(8, 2))
            tk.Label(item, text=f"账号: {acc['user']}", font=("Microsoft YaHei", 9), 
                    bg="#FFF9FA", fg="#A4B0BE").pack(anchor="w", padx=10, pady=(0, 5))
            
            btn_frame = tk.Frame(item, bg="#FFF9FA")
            btn_frame.pack(fill=tk.X, padx=10, pady=(0, 8))
            
            tk.Button(btn_frame, text="📋 账号", command=lambda u=acc['user']: self.copy(u, "账号"),
                     bg=self.btn_user, fg="white", relief="flat").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
            tk.Button(btn_frame, text="🔑 密码", command=lambda p=acc['pass']: self.copy(p, "密码"),
                     bg=self.btn_pass, fg="white", relief="flat").pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))

    def copy(self, text, label):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.show_toast(f"{label}已复制！")

    def show_toast(self, msg):
        toast = tk.Toplevel(self.root)
        toast.overrideredirect(True)
        toast.wm_attributes('-topmost', True)
        toast.geometry(f"+{self.root.winfo_x()+80}+{self.root.winfo_y()+80}")
        tk.Label(toast, text=msg, bg="#333", fg="white", padx=10, pady=5).pack()
        self.root.after(1500, toast.destroy)

if __name__ == "__main__":
    root = tk.Tk()
    app = AccountHelper(root)
    root.mainloop()