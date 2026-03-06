import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import tkinter.simpledialog as simpledialog
from PIL import Image, ImageTk
import random
import os
import sys

class MemoryTrainingGame:
    def __init__(self, root):
        self.root = root
        self.root.title("记忆训练小游戏 - Win10专用版")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        # Win10高分屏适配
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 游戏数据初始化
        self.image_config = {}
        self.current_img = ""
        self.correct_name = ""
        self.total = 0
        self.right = 0
        
        # 创建界面
        self.make_ui()

    def make_ui(self):
        # 顶部操作栏
        top = ttk.Frame(self.root, padding=10)
        top.pack(fill=tk.X)
        
        ttk.Button(top, text="添加图片", command=self.add).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="删除图片", command=self.delete).pack(side=tk.LEFT, padx=5)
        ttk.Button(top, text="重置游戏", command=self.reset).pack(side=tk.RIGHT, padx=5)
        
        # 图片展示区
        self.img_frame = ttk.Frame(self.root, padding=20)
        self.img_frame.pack(fill=tk.BOTH, expand=True)
        self.img_label = ttk.Label(self.img_frame, text="点击「添加图片」开始游戏", font=("微软雅黑", 16))
        self.img_label.pack(expand=True)
        
        # 答题区
        ans = ttk.Frame(self.root, padding=10)
        ans.pack(fill=tk.X)
        ttk.Label(ans, text="输入图片名称：", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=5)
        self.entry = ttk.Entry(ans, font=("微软雅黑", 12), width=30)
        self.entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
        ttk.Button(ans, text="提交答案", command=self.check).pack(side=tk.LEFT, padx=5)
        
        # 结果区
        res = ttk.Frame(self.root, padding=10)
        res.pack(fill=tk.X)
        ttk.Label(res, text="答题结果：", font=("微软雅黑", 12)).pack(side=tk.LEFT, padx=5)
        self.res_label = ttk.Label(res, text="", font=("微软雅黑", 12))
        self.res_label.pack(side=tk.LEFT, padx=5)
        ttk.Label(res, text="正确率：", font=("微软雅黑", 12)).pack(side=tk.RIGHT, padx=5)
        self.acc = ttk.Label(res, text="0%", font=("微软雅黑", 12), fg="green")
        self.acc.pack(side=tk.RIGHT, padx=5)

    def add(self):
        # 选择图片
        path = filedialog.askopenfilename(
            title="选择图片",
            filetypes=[("所有图片", "*.jpg *.png *.bmp *.gif"), ("所有文件", "*.*")],
            initialdir=os.path.expanduser("~\\Pictures")
        )
        if not path:
            return
        # 输入名称
        name = simpledialog.askstring("图片名称", "请输入这张图片的正确名称：")
        if not name:
            messagebox.showwarning("提示", "名称不能为空！")
            return
        self.image_config[path] = name
        messagebox.showinfo("成功", f"已添加：{name}")
        if len(self.image_config) == 1:
            self.show()

    def delete(self):
        if not self.image_config:
            messagebox.showwarning("提示", "还没有添加图片！")
            return
        win = tk.Toplevel(self.root)
        win.title("删除图片")
        win.geometry("400x300")
        ttk.Label(win, text="选择要删除的图片：", font=("微软雅黑", 12)).pack(pady=10)
        
        lb = tk.Listbox(win, font=("微软雅黑", 12), width=50, height=10)
        lb.pack(pady=10, padx=10, fill=tk.BOTH, expand=True)
        
        self.paths = list(self.image_config.keys())
        for i, p in enumerate(self.paths):
            lb.insert(tk.END, f"{i+1}. {self.image_config[p]} ({os.path.basename(p)})")
        
        def del_ok():
            sel = lb.curselection()
            if not sel:
                messagebox.showwarning("提示", "请选择要删除的图片！")
                return
            del self.image_config[self.paths[sel[0]]]
            messagebox.showinfo("成功", "删除完成！")
            win.destroy()
            if not self.image_config:
                self.img_label.config(text="点击「添加图片」开始游戏")
        
        ttk.Button(win, text="删除选中", command=del_ok).pack(pady=10)

    def show(self):
        if not self.image_config:
            return
        self.current_img = random.choice(list(self.image_config.keys()))
        self.correct_name = self.image_config[self.current_img]
        try:
            img = Image.open(self.current_img)
            img.thumbnail((600, 400), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.img_label.config(image=photo, text="")
            self.img_label.photo = photo
            self.entry.delete(0, tk.END)
            self.res_label.config(text="")
        except:
            messagebox.showerror("错误", "图片加载失败，请换一张图片试试！")

    def check(self):
        if not self.current_img:
            messagebox.showwarning("提示", "请先添加图片！")
            return
        ans = self.entry.get().strip()
        if not ans:
            messagebox.showwarning("提示", "请输入名称！")
            return
        
        self.total += 1
        if ans.lower() == self.correct_name.lower():
            self.right += 1
            self.res_label.config(text=f"正确！答案：{self.correct_name}", fg="green")
        else:
            self.res_label.config(text=f"错误！正确答案：{self.correct_name}", fg="red")
        
        acc = (self.right / self.total) * 100 if self.total > 0 else 0
        self.acc.config(text=f"{acc:.1f}%")
        self.root.after(1500, self.show)

    def reset(self):
        self.total = 0
        self.right = 0
        self.res_label.config(text="")
        self.acc.config(text="0%")
        self.entry.delete(0, tk.END)
        self.img_label.config(text="点击「添加图片」开始游戏", image="")
        self.current_img = ""
        self.correct_name = ""
        messagebox.showinfo("成功", "游戏已重置！")

if __name__ == "__main__":
    root = tk.Tk()
    app = MemoryTrainingGame(root)
    root.mainloop()