import os
import re
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

def clean_name(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("图片压缩工具")
        self.geometry("900x600")
        self.resizable(False, False)
        
        self.img_path = None
        self.target = tk.IntVar(value=400)
        self.new_name = tk.StringVar()
        self.fmt = tk.StringVar(value="JPG")
        self.save_dir = tk.StringVar()
        
        self.create_ui()

    def create_ui(self):
        f = ttk.Frame(self)
        f.pack(pady=20, padx=20, fill="both", expand=True)
        
        ttk.Label(f, text="图片压缩工具", font=("Arial", 16)).pack(pady=10)
        
        self.img_label = ttk.Label(f, text="预览区", width=40, height=15, relief="solid")
        self.img_label.pack(pady=10)
        
        ttk.Button(f, text="选择图片", command=self.load_img).pack()
        
        ttk.Label(f, text="目标大小(KB)").pack()
        ttk.Entry(f, textvariable=self.target).pack()
        
        ttk.Label(f, text="输出文件名").pack()
        ttk.Entry(f, textvariable=self.new_name).pack()
        
        ttk.Label(f, text="保存位置").pack()
        ttk.Entry(f, textvariable=self.save_dir).pack()
        ttk.Button(f, text="选择文件夹", command=self.select_dir).pack()
        
        self.btn = ttk.Button(f, text="开始压缩", command=self.start)
        self.btn.pack(pady=15)
        
        self.pb = ttk.Progressbar(f, length=500)
        self.pb.pack()

    def load_img(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.png *.bmp")])
        if not p:
            return
        self.img_path = p
        im = Image.open(p)
        im.thumbnail((300, 300))
        self.photo = ImageTk.PhotoImage(im)
        self.img_label.config(image=self.photo)

    def select_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.save_dir.set(d)

    def start(self):
        self.btn.config(state="disabled")
        threading.Thread(target=self.run).start()

    def run(self):
        try:
            if not self.img_path or not self.save_dir.get():
                messagebox.showwarning("提示", "请选择图片和保存位置")
                return
            
            name = clean_name(self.new_name.get())
            ext = self.fmt.get().lower()
            out = os.path.join(self.save_dir.get(), name + "." + ext)
            
            img = Image.open(self.img_path).convert("RGB")
            q = 90
            while True:
                img.save(out, quality=q)
                s = os.path.getsize(out) / 1024
                if s <= self.target.get() or q <= 10:
                    break
                q -= 5
            messagebox.showinfo("完成", "压缩成功！")
        except:
            messagebox.showerror("错误", "压缩失败")
        finally:
            self.btn.config(state="normal")

if __name__ == "__main__":
    App().mainloop()