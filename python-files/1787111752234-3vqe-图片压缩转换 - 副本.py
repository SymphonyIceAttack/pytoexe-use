import os
from PIL import Image
import tkinter as tk
from tkinter import filedialog, ttk, messagebox


def get_all_images(root_dir):
    img_exts = {".png", ".webp", ".bmp", ".tiff", ".tif", ".jpeg", ".jpg"}
    file_list = []
    for dirpath, _, filenames in os.walk(root_dir):
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext in img_exts:
                file_list.append(os.path.join(dirpath, fn))
    return file_list


def compress_image_auto_resize(image: Image.Image, save_path: str, max_size_bytes: int, min_side: int):
    original_w, original_h = image.size
    current_img = image.copy()

    quality = 95
    step = 5
    while quality >= 10:
        current_img.save(save_path, format="JPEG", quality=quality, optimize=True)
        fsize = os.path.getsize(save_path)
        if fsize <= max_size_bytes:
            return True, fsize, quality, (current_img.width, current_img.height), "仅调整画质"
        quality -= step

    scale = 0.9
    while scale >= 0.2:
        new_w = int(original_w * scale)
        new_h = int(original_h * scale)
        if new_w < min_side or new_h < min_side:
            break
        current_img = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
        current_img.save(save_path, format="JPEG", quality=10, optimize=True)
        fsize = os.path.getsize(save_path)
        if fsize <= max_size_bytes:
            return True, fsize, 10, (new_w, new_h), "已缩小分辨率"
        scale -= 0.1

    final_w = max(int(original_w * scale), min_side)
    final_h = max(int(original_h * scale), min_side)
    current_img = image.resize((final_w, final_h), Image.Resampling.LANCZOS)
    current_img.save(save_path, format="JPEG", quality=10, optimize=True)
    final_size = os.path.getsize(save_path)
    return False, final_size, 10, (final_w, final_h), "已缩到最小边长，仍超限"


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("图片批量转JPG压缩工具")
        self.geometry("720x520")
        self.resizable(True, True)

        # 窗口居中
        self.update_idletasks()
        win_width = self.winfo_width()
        win_height = self.winfo_height()
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        self.geometry(f"720x520+{x}+{y}")

        self.folder_path = tk.StringVar()
        self.max_mb = tk.StringVar(value="1.0")
        self.min_side = tk.StringVar(value="800")

        frame_top = ttk.Frame(self, padding=10)
        frame_top.pack(fill=tk.X)

        ttk.Label(frame_top, text="目标文件夹:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_top, textvariable=self.folder_path, width=55).grid(row=0, column=1, padx=5)
        ttk.Button(frame_top, text="选择文件夹", command=self.select_folder).grid(row=0, column=2)

        frame_param = ttk.Frame(self, padding=10)
        frame_param.pack(fill=tk.X)
        ttk.Label(frame_param, text="最大文件(MB):").grid(row=0, column=0, sticky="w")
        ttk.Entry(frame_param, textvariable=self.max_mb, width=8).grid(row=0, column=1, padx=5)
        ttk.Label(frame_param, text="最小边长(px):").grid(row=0, column=2, sticky="w", padx=(15, 0))
        ttk.Entry(frame_param, textvariable=self.min_side, width=8).grid(row=0, column=3, padx=5)

        frame_btn = ttk.Frame(self, padding=10)
        frame_btn.pack()
        self.run_btn = ttk.Button(frame_btn, text="开始处理（⚠️原地覆盖，请先备份图片）", command=self.start_work)
        self.run_btn.pack()

        ttk.Label(self, text="运行日志：").pack(anchor="w", padx=10)
        self.log_text = tk.Text(self, wrap=tk.WORD)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0,10))

    def log(self, msg):
        self.log_text.insert(tk.END, msg + "\n")
        self.log_text.see(tk.END)
        self.update_idletasks()

    def select_folder(self):
        path = filedialog.askdirectory(title="选择图片根目录（递归所有子文件夹）")
        if path:
            self.folder_path.set(path)

    def start_work(self):
        src_folder = self.folder_path.get().strip()
        if not src_folder or not os.path.isdir(src_folder):
            messagebox.showwarning("提示", "请先选择有效文件夹")
            return
        try:
            max_size_bytes = int(float(self.max_mb.get()) * 1024 * 1024)
            min_side_val = int(self.min_side.get())
        except ValueError:
            messagebox.showerror("参数错误", "最大文件、最小边长请输入数字")
            return

        if not messagebox.askyesno("确认", "⚠️会原地覆盖/删除原图！确认已备份图片再继续？"):
            return

        self.run_btn.config(state=tk.DISABLED)
        self.log_text.delete(1.0, tk.END)
        self.log(f"开始处理，文件夹：{src_folder}")
        self.log(f"最大文件：{self.max_mb.get()}MB，最小边长：{min_side_val}px")

        img_paths = get_all_images(src_folder)
        total = len(img_paths)
        skip_cnt = 0
        process_cnt = 0

        for idx, img_path in enumerate(img_paths, 1):
            try:
                ext = os.path.splitext(img_path)[1].lower()
                file_size = os.path.getsize(img_path)

                if ext == ".jpg" and file_size <= max_size_bytes:
                    self.log(f"[{idx}/{total}] ⏭跳过：{img_path} 已是JPG且大小符合")
                    skip_cnt += 1
                    continue

                self.log(f"[{idx}/{total}] 处理：{img_path}")
                with Image.open(img_path) as im:
                    if im.mode in ("RGBA", "P"):
                        im = im.convert("RGB")

                    dir_name = os.path.dirname(img_path)
                    base_name = os.path.splitext(os.path.basename(img_path))[0]
                    new_jpg_path = os.path.join(dir_name, f"{base_name}.jpg")

                    ok, fsize, q, out_size, mode_info = compress_image_auto_resize(
                        im, new_jpg_path, max_size_bytes=max_size_bytes, min_side=min_side_val
                    )
                    if ext != ".jpg":
                        if os.path.exists(img_path):
                            os.remove(img_path)
                    process_cnt += 1
                    status = "✅达标" if ok else "⚠️已到下限仍超大小"
                    self.log(f"    → {status} {mode_info} |输出尺寸{out_size[0]}×{out_size[1]} | {fsize/1024:.2f}KB quality={q}")
            except Exception as e:
                self.log(f"❌失败 {img_path} : {str(e)}")

        self.log(f"\n=====处理完成=====")
        self.log(f"总计:{total} |跳过:{skip_cnt} |实际处理:{process_cnt}")
        self.run_btn.config(state=tk.NORMAL)
        messagebox.showinfo("完成", f"处理结束\n总计:{total} |跳过:{skip_cnt} |实际处理:{process_cnt}")


if __name__ == "__main__":
    app = App()
    app.mainloop()
