import tkinter as tk
from tkinter import filedialog, font, scrolledtext
import os

class TextReader:
    def __init__(self, root):
        self.root = root
        self.root.title("文本阅读器 (Tk)")
        self.root.geometry("800x600")

        # 状态
        self.show_border = True
        self.bg_alpha = 1.0      # 1.0 = 不透明
        self.font_size = 20
        self.text_content = ""

        # 文本控件
        self.text_widget = scrolledtext.ScrolledText(
            root,
            wrap=tk.WORD,
            font=("微软雅黑", self.font_size),
            bg="white",
            fg="black",
            undo=True
        )
        self.text_widget.pack(fill=tk.BOTH, expand=True)
        self.text_widget.insert(tk.END, "拖拽文本文件到此处，或右键 → 打开文件")
        self.text_widget.config(state=tk.DISABLED)

        # 绑定事件
        self.text_widget.bind("<Button-3>", self.show_menu)   # 右键菜单
        self.root.bind("<Configure>", self.on_resize)         # 窗口大小变化
        self.root.drop_target_register('DROPFILES')          # Windows拖拽支持
        self.root.dnd_bind('<<Drop>>', self.on_drop)

        # 右键菜单
        self.menu = tk.Menu(root, tearoff=0)
        self.menu.add_command(label="打开文件", command=self.open_file)
        self.menu.add_separator()
        self.menu.add_command(label="退出", command=root.quit)

        # 边框
        self.border_var = tk.BooleanVar(value=True)
        self.menu.add_checkbutton(label="显示边框", variable=self.border_var, command=self.toggle_border)

        # 背景透明度子菜单
        bg_menu = tk.Menu(self.menu, tearoff=0)
        for alpha, label in [(1.0, "100%"), (0.8, "80%"), (0.6, "60%"), (0.4, "40%"), (0.2, "20%")]:
            bg_menu.add_command(label=label, command=lambda a=alpha: self.set_bg_alpha(a))
        self.menu.add_cascade(label="背景透明度", menu=bg_menu)

        # 字体大小子菜单
        size_menu = tk.Menu(self.menu, tearoff=0)
        for size in [12, 16, 20, 24, 32, 48]:
            size_menu.add_command(label=str(size), command=lambda s=size: self.set_font_size(s))
        self.menu.add_cascade(label="字体大小", menu=size_menu)

        # 窗口透明度默认不透明
        self.root.attributes('-alpha', self.bg_alpha)

    # ---------- 功能 ----------
    def open_file(self):
        filepath = filedialog.askopenfilename(filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")])
        if filepath:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, content)
            self.text_widget.config(state=tk.DISABLED)

    def toggle_border(self):
        self.show_border = self.border_var.get()
        # 通过改变窗口样式切换边框（overrideredirect 会移除标题栏，所以这里使用经典边框）
        if self.show_border:
            self.root.overrideredirect(False)
            self.root.attributes('-toolwindow', False)
        else:
            self.root.overrideredirect(True)
            # 重新设置位置和大小（因为overrideredirect会重置）
            self.root.geometry(self.root.geometry())

    def set_bg_alpha(self, alpha):
        self.bg_alpha = alpha
        self.root.attributes('-alpha', alpha)

    def set_font_size(self, size):
        self.font_size = size
        self.text_widget.config(font=("微软雅黑", size))

    def on_resize(self, event):
        # 当窗口大小变化时，更新控件大小（已经用pack fill，无需额外操作）
        pass

    def show_menu(self, event):
        self.menu.post(event.x_root, event.y_root)

    def on_drop(self, event):
        # 处理Windows拖拽
        files = self.root.tk.splitlist(event.data)
        if files:
            filepath = files[0]
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            self.text_widget.config(state=tk.NORMAL)
            self.text_widget.delete(1.0, tk.END)
            self.text_widget.insert(tk.END, content)
            self.text_widget.config(state=tk.DISABLED)

if __name__ == "__main__":
    root = tk.Tk()
    # 支持拖拽（Windows）
    try:
        root.tk.call('package', 'require', 'tkdnd')
    except:
        pass  # 如果没有tkdnd，拖拽功能不可用，不影响其他
    app = TextReader(root)
    root.mainloop()