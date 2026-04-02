import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk, ImageDraw

# 固定路径
INPUT_DIR = r"C:\Users\Administrator\Desktop\图片裁剪\输入"
SAVE_ROOT = r"C:\Users\Administrator\Desktop\图片裁剪\输出"

os.makedirs(INPUT_DIR, exist_ok=True)
os.makedirs(SAVE_ROOT, exist_ok=True)

class ImageCutter:
    def __init__(self, root):
        self.root = root
        self.root.title("图片切片工具 - 全选+预览+5x5")
        self.root.geometry("1200x700")

        self.images = []
        self.preview_size = (150, 150)
        self.zoom_size = (800, 800)
        self.images_per_row = 5

        # --- 顶部控制区 ---
        control_frame = ttk.Frame(root)
        control_frame.pack(fill="x", pady=5, padx=5)

        # 全局全选
        self.global_select_btn = ttk.Button(control_frame, text="全 选", width=8, command=self.toggle_global_select)
        self.global_select_btn.pack(side="left", padx=5)

        # 切割预览
        ttk.Button(control_frame, text="切割预览", width=8, command=self.preview_cut).pack(side="left", padx=5)

        ttk.Label(control_frame, text="切割行数:").pack(side="left", padx=5)
        self.row_entry = ttk.Entry(control_frame, width=6)
        self.row_entry.insert(0, "5")
        self.row_entry.pack(side="left", padx=2)

        ttk.Label(control_frame, text="切割列数:").pack(side="left", padx=5)
        self.col_entry = ttk.Entry(control_frame, width=6)
        self.col_entry.insert(0, "5")
        self.col_entry.pack(side="left", padx=2)

        ttk.Button(control_frame, text="刷新图片", command=self.load_images).pack(side="left", padx=10)
        ttk.Button(control_frame, text="切割选中图片", command=self.cut_selected).pack(side="left", padx=5)

        # --- 滚动区域 ---
        self.canvas = tk.Canvas(root, bg="#f5f5f5", highlightthickness=0, bd=0)
        self.scroll = ttk.Scrollbar(root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)

        self.canvas.configure(yscrollcommand=self.scroll.set)
        self.scroll.pack(side="right", fill="y", padx=0)
        self.canvas.pack(side="left", fill="both", expand=True, padx=0, pady=0)
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.scrollable_frame.bind("<Configure>", lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<FocusIn>", lambda e: self.root.focus_set())

        self.load_images()

    # 全局全选/取消
    def toggle_global_select(self):
        if not self.images:
            return
        has_selected = any(it["var"].get() for it in self.images)
        new_state = not has_selected
        for it in self.images:
            it["var"].set(new_state)
        self.global_select_btn.config(text="取消全选" if new_state else "全 选")

    # 切割预览
    def preview_cut(self):
        selected = [it for it in self.images if it["var"].get()]
        if not selected:
            messagebox.showwarning("提示", "请先选中一张图片预览")
            return
        if len(selected) > 1:
            messagebox.showwarning("提示", "只能预览一张图片")
            return

        try:
            rows = int(self.row_entry.get())
            cols = int(self.col_entry.get())
        except:
            messagebox.showerror("错误", "行列必须是数字")
            return

        img = selected[0]["img"].copy()
        w, h = img.size
        draw = ImageDraw.Draw(img)

        for i in range(1, rows):
            y = i * h // rows
            draw.line([(0, y), (w, y)], fill="red", width=2)
        for j in range(1, cols):
            x = j * w // cols
            draw.line([(x, 0), (x, h)], fill="red", width=2)

        top = tk.Toplevel(self.root)
        top.title("切割预览（红线=切割线）")
        prev = img.copy()
        prev.thumbnail((900, 900), Image.Resampling.LANCZOS)
        tk_img = ImageTk.PhotoImage(prev)
        label = ttk.Label(top, image=tk_img)
        label.image = tk_img
        label.pack()

    def load_images(self):
        for w in self.scrollable_frame.winfo_children():
            w.destroy()
        self.images.clear()
        self.global_select_btn.config(text="全 选")

        exts = (".png", ".jpg", ".jpeg", ".bmp")
        files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(exts)]

        for i in range(0, len(files), self.images_per_row):
            row_files = files[i:i + self.images_per_row]
            row_idx = i // self.images_per_row

            row_container = ttk.Frame(self.scrollable_frame)
            row_container.grid(row=row_idx, column=0, sticky="w", pady=5)

            row_var_list = []
            row_state = tk.BooleanVar(value=False)
            btn = ttk.Button(row_container, text="本行全选", width=8)
            btn.grid(row=0, column=0, padx=5)
            btn.config(command=lambda vl=row_var_list, b=btn, rs=row_state: self.toggle_row(vl, b, rs))

            for col_idx, fname in enumerate(row_files):
                path = os.path.join(INPUT_DIR, fname)
                try:
                    img = Image.open(path).convert("RGB")
                    thumb = img.copy()
                    thumb.thumbnail(self.preview_size, Image.Resampling.LANCZOS)
                    tk_thumb = ImageTk.PhotoImage(thumb)

                    card = ttk.Frame(row_container)
                    card.grid(row=0, column=col_idx + 1, padx=8, pady=5)

                    var = tk.BooleanVar()
                    cb = ttk.Checkbutton(card, variable=var, takefocus=False)
                    cb.pack(side="left", padx=2)

                    # 图片
                    lbl = ttk.Label(card, image=tk_thumb, takefocus=False)
                    lbl.pack(side="top")
                    lbl.image = tk_thumb

                    # 文件名（无后缀，超出用...）
                    base_name = os.path.splitext(fname)[0]
                    display_name = base_name if len(base_name) <= 10 else base_name[:9] + "..."
                    name_lbl = ttk.Label(card, text=display_name, font=("微软雅黑", 9))
                    name_lbl.pack(side="bottom", pady=1)

                    lbl.bind("<Button-1>", lambda e, v=var: v.set(not v.get()))
                    lbl.bind("<Double-1>", lambda e, im=img: self.show_big(im))

                    row_var_list.append(var)
                    self.images.append({
                        "img": img,
                        "var": var,
                        "name": fname
                    })
                except:
                    continue

    def toggle_row(self, vl, btn, state):
        val = not state.get()
        state.set(val)
        for v in vl:
            v.set(val)
        btn.config(text="本行取消" if val else "本行全选")

    def show_big(self, img):
        top = tk.Toplevel(self.root)
        top.title("大图预览")
        big = img.copy()
        big.thumbnail(self.zoom_size, Image.Resampling.LANCZOS)
        tk_big = ImageTk.PhotoImage(big)
        lbl = ttk.Label(top, image=tk_big, takefocus=False)
        lbl.image = tk_big
        lbl.pack()

    def cut_selected(self):
        try:
            rows = int(self.row_entry.get())
            cols = int(self.col_entry.get())
            if rows <= 0 or cols <= 0:
                raise ValueError
        except:
            messagebox.showerror("错误", "行列必须是正整数！")
            return

        selected = [it for it in self.images if it["var"].get()]
        if not selected:
            messagebox.showwarning("提示", "请先勾选要切割的图片")
            return

        ok = 0
        for item in selected:
            try:
                img = item["img"]
                base = os.path.splitext(item["name"])[0]
                out_dir = os.path.join(SAVE_ROOT, base)
                os.makedirs(out_dir, exist_ok=True)

                w, h = img.size
                tw = w / cols
                th = h / rows

                for r in range(rows):
                    for c in range(cols):
                        box = (c * tw, r * th, (c + 1) * tw, (r + 1) * th)
                        part = img.crop(box)
                        name = f"{r+1}.{c+1}.png"
                        part.save(os.path.join(out_dir, name))
                ok += 1
            except Exception as e:
                print(e)

        messagebox.showinfo("完成", f"已切割 {ok} 张图片\n每张独立文件夹，按 1.1~5.5 命名")
        os.startfile(SAVE_ROOT)

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCutter(root)
    root.mainloop()