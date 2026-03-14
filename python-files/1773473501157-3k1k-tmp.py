import subprocess
import sys
import os

# ====================== 自动安装依赖库 ======================
def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
    except Exception as e:
        print(f"安装 {package} 失败：{e}")

required_packages = {
    "PIL": "Pillow",
    "numpy": "numpy"
}

for imp_name, pkg_name in required_packages.items():
    try:
        __import__(imp_name)
    except ImportError:
        print(f"正在自动安装依赖：{pkg_name} ...")
        install_package(pkg_name)

# ====================== 主程序 ======================
import tkinter as tk
from tkinter import filedialog, messagebox, Toplevel
from PIL import Image, ImageTk
import numpy as np
from datetime import datetime, timedelta

class PreviewWindow(Toplevel):
    def __init__(self, parent, gcode, canvas_size=800):
        super().__init__(parent)
        self.title("xingchen laser")
        self.gcode = gcode
        self.canvas_size = canvas_size
        self.geometry(f"{canvas_size + 50}x{canvas_size + 100}")
        
        self.is_playing = False
        self.skip_flag = False
        self._setup_ui()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self, bg="white", width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack(pady=10)
        
        btn_frame = tk.Frame(self)
        btn_frame.pack(pady=5)
        
        self.btn_play = tk.Button(btn_frame, text="播放动画", command=self.start_anim, width=15)
        self.btn_play.grid(row=0, column=0, padx=5)
        
        self.btn_skip = tk.Button(btn_frame, text="直接显示", command=self.skip_draw, width=15, state=tk.DISABLED)
        self.btn_skip.grid(row=0, column=1, padx=5)
        
        tk.Button(btn_frame, text="关闭", command=self.destroy, width=15).grid(row=0, column=2, padx=5)

        self.status_lbl = tk.Label(self, text=f"共 {len(self.gcode)} 条指令")
        self.status_lbl.pack(pady=5)

    def start_anim(self):
        if self.is_playing:
            return
        self.canvas.delete("all")
        self.is_playing = True
        self.skip_flag = False
        self.btn_play.config(state=tk.DISABLED)
        self.btn_skip.config(state=tk.NORMAL)
        
        self.current_x, self.current_y = 0, 0
        self.pen_down = False
        self.index = 0
        self.total = len(self.gcode)
        self._anim_loop()

    def _anim_loop(self):
        if not self.is_playing:
            return

        if self.skip_flag:
            for i in range(self.index, self.total):
                self._exec_cmd(self.gcode[i], fast=True)
            self._end_anim("已跳过")
            return

        if self.index < self.total:
            self._exec_cmd(self.gcode[self.index], fast=False)
            self.index += 1
            
            if self.index % 200 == 0:
                self.status_lbl.config(text=f"预览中: {self.index} / {self.total}")
            
            self.after(1, self._anim_loop)
        else:
            self._end_anim("播放完成")

    def _exec_cmd(self, cmd, fast=False):
        if cmd.startswith("move"):
            try:
                coords = cmd.split("(")[1].split(")")[0].split(",")
                new_x = int(float(coords[0].strip()))
                new_y = int(float(coords[1].strip()))
                
                if self.pen_down:
                    self.canvas.create_line(self.current_x, self.current_y, new_x, new_y, fill="red", width=1)
                
                self.current_x, self.current_y = new_x, new_y
            except Exception as e:
                pass
        elif cmd == "laser.open":
            self.pen_down = True
        elif cmd == "laser.close":
            self.pen_down = False

    def skip_draw(self):
        self.skip_flag = True

    def _end_anim(self, msg):
        self.is_playing = False
        self.btn_play.config(state=tk.NORMAL)
        self.btn_skip.config(state=tk.DISABLED)
        self.status_lbl.config(text=msg)

class LaserPathConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Xingchen laser")
        self.root.geometry("850x850")

        self.final_code = []
        self.canvas_size = 800
        self.cmd_per_second = 150
        
        self._setup_ui()

    def _setup_ui(self):
        self.canvas = tk.Canvas(self.root, bg="white", width=self.canvas_size, height=self.canvas_size)
        self.canvas.pack(pady=10)

        frame_ctrl = tk.Frame(self.root)
        frame_ctrl.pack(pady=5)

        tk.Button(frame_ctrl, text="加载图片", command=self.load_img).grid(row=0, column=0, padx=5)
        
        tk.Label(frame_ctrl, text="转换灵敏度:").grid(row=0, column=1, padx=5)
        self.scale_thresh = tk.Scale(frame_ctrl, from_=0, to=255, orient=tk.HORIZONTAL, length=100, command=self.update_view)
        self.scale_thresh.set(128)
        self.scale_thresh.grid(row=0, column=2, padx=5)

        tk.Label(frame_ctrl, text="轮廓线粗细:").grid(row=0, column=3, padx=5)
        self.scale_thick = tk.Scale(frame_ctrl, from_=1, to=10, orient=tk.HORIZONTAL, length=80, command=self.update_view)
        self.scale_thick.set(1)
        self.scale_thick.grid(row=0, column=4, padx=5)

        frame_opt = tk.Frame(self.root)
        frame_opt.pack(pady=5)
        self.var_inv = tk.BooleanVar()
        self.var_hollow = tk.BooleanVar()
        tk.Checkbutton(frame_opt, text="反色", variable=self.var_inv, command=self.update_view).pack(side=tk.LEFT, padx=10)
        tk.Checkbutton(frame_opt, text="轮廓模式", variable=self.var_hollow, command=self.update_view).pack(side=tk.LEFT, padx=10)

        frame_action = tk.Frame(self.root)
        frame_action.pack(pady=15)

        tk.Button(frame_action, text="生成", command=self.generate_code, bg="#e3f2fd", width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_action, text="预览", command=self.open_preview_window, bg="#fff3e0", width=16).pack(side=tk.LEFT, padx=5)
        tk.Button(frame_action, text="保存为txt", command=self.save_file, bg="#c8e6c9", width=16).pack(side=tk.LEFT, padx=5)

        self.lbl_time = tk.Label(self.root, text="预计耗时: --:--  | 预计完成: --:--:--", fg="green", font=("微软雅黑", 10))
        self.lbl_time.pack(pady=2)

        self.lbl_info = tk.Label(self.root, text="", fg="blue", font=("微软雅黑", 10))
        self.lbl_info.pack(pady=5)

        self.img_origin = None

    def load_img(self):
        path = filedialog.askopenfilename(filetypes=[("Images", "*.png;*.jpg;*.jpeg;*.bmp")])
        if not path: return
        self.img_origin = Image.open(path).convert("L").resize((self.canvas_size, self.canvas_size), Image.Resampling.LANCZOS)
        self.update_view()

    def _dilate_fast(self, img):
        h, w = img.shape
        out = np.zeros_like(img)
        for y in range(h):
            for x in range(w):
                if img[y, x] == 255:
                    out[y, x] = 255
                    if y > 0: out[y-1, x] = 255
                    if y < h-1: out[y+1, x] = 255
                    if x > 0: out[y, x-1] = 255
                    if x < w-1: out[y, x+1] = 255
        return out

    def _get_hollow_edge(self, bin_arr):
        h, w = bin_arr.shape
        edge_arr = np.ones_like(bin_arr) * 255
        for y in range(1, h-1):
            for x in range(1, w-1):
                if bin_arr[y, x] == 0:
                    up = bin_arr[y-1, x]
                    down = bin_arr[y+1, x]
                    left = bin_arr[y, x-1]
                    right = bin_arr[y, x+1]
                    if up == 255 or down == 255 or left == 255 or right == 255:
                        edge_arr[y, x] = 0
        return edge_arr

    def update_view(self, *args):
        if not self.img_origin: return
        arr = np.array(self.img_origin)
        thresh = self.scale_thresh.get()
        thickness = self.scale_thick.get()
        
        if self.var_inv.get():
            bin_arr = (arr > thresh) * 255
        else:
            bin_arr = (arr < thresh) * 255

        display_arr = bin_arr
        if self.var_hollow.get():
            hollow_edge = self._get_hollow_edge(bin_arr)
            if thickness > 1:
                inv_edge = 255 - hollow_edge
                for _ in range(thickness - 1):
                    inv_edge = self._dilate_fast(inv_edge)
                hollow_edge = 255 - inv_edge
            display_arr = hollow_edge

        self.img_display = ImageTk.PhotoImage(Image.fromarray(display_arr.astype(np.uint8)))
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_display)

    def _trace_contour(self, edge_arr):
        h, w = edge_arr.shape
        visited = np.zeros_like(edge_arr, dtype=bool)
        contours = []
        directions = [(-1,0), (-1,1), (0,1), (1,1), (1,0), (1,-1), (0,-1), (-1,-1)]

        for y in range(h):
            for x in range(w):
                if edge_arr[y, x] == 0 and not visited[y, x]:
                    contour = []
                    current_x, current_y = x, y
                    while True:
                        if visited[current_y, current_x]: break
                        if edge_arr[current_y, current_x] != 0: break
                        visited[current_y, current_x] = True
                        contour.append((current_x, current_y))
                        found_next = False
                        for dx, dy in directions:
                            nx = current_x + dx
                            ny = current_y + dy
                            if 0 <= nx < w and 0 <= ny < h:
                                if edge_arr[ny, nx] == 0 and not visited[ny, nx]:
                                    current_x, current_y = nx, ny
                                    found_next = True
                                    break
                        if not found_next: break
                    if len(contour) > 10:
                        contours.append(contour)
        return contours

    def generate_code(self):
        if not self.img_origin:
            messagebox.showwarning("提示", "请先加载图片")
            return

        arr = np.array(self.img_origin)
        thresh = self.scale_thresh.get()
        thickness = self.scale_thick.get()
        is_hollow = self.var_hollow.get()
        
        if self.var_inv.get():
            bin_arr = (arr > thresh) * 255
        else:
            bin_arr = (arr < thresh) * 255

        self.final_code = []

        if is_hollow:
            hollow_edge = self._get_hollow_edge(bin_arr)
            if thickness > 1:
                inv_edge = 255 - hollow_edge
                for _ in range(thickness - 1):
                    inv_edge = self._dilate_fast(inv_edge)
                hollow_edge = 255 - inv_edge
            contours = self._trace_contour(hollow_edge)
            for contour in contours:
                if len(contour) < 2: continue
                start_x, start_y = contour[0]
                self.final_code.append(f"move({start_x}, {start_y})")
                self.final_code.append("laser.open")
                for (px, py) in contour[1:]:
                    self.final_code.append(f"move({px}, {py})")
                self.final_code.append("laser.close")
        else:
            h, w = bin_arr.shape
            for y in range(h):
                x = 0
                while x < w:
                    if bin_arr[y, x] == 0:
                        sx = x
                        while x < w and bin_arr[y, x] == 0: x += 1
                        ex = x - 1
                        self.final_code.append(f"move({sx}, {y})")
                        self.final_code.append("laser.open")
                        self.final_code.append(f"move({ex}, {y})")
                        self.final_code.append("laser.close")
                    else: x += 1

        total_lines = len(self.final_code)
        est_seconds = total_lines / self.cmd_per_second
        finish_dt = datetime.now() + timedelta(seconds=est_seconds)
        est_str = f"{int(est_seconds//60):02d}:{int(est_seconds%60):02d}"
        finish_str = finish_dt.strftime("%H:%M:%S")
        
        self.lbl_time.config(text=f"预计耗时: {est_str}  | 预计完成: {finish_str}")
        self.lbl_info.config(text=f"生成成功, 指令数: {len(self.final_code)}")
        messagebox.showinfo("生成完成", f"路径代码生成完毕，总指令数: {len(self.final_code)} ")

    def open_preview_window(self):
        if not self.final_code:
            r = messagebox.askyesno("提示", "当前无指令，是否从.txt文件加载预览")
            if r:
                path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
                if path:
                    with open(path, "r", encoding="utf-8") as f:
                        code = [line.strip() for line in f if line.strip()]
                    PreviewWindow(self.root, code)
            return
        PreviewWindow(self.root, self.final_code)

    def save_file(self):
        if not self.final_code:
            messagebox.showwarning("提示", "请先生成路径")
            return
        
        save_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            title="保存激光路径文件"
        )
        if not save_path: return

        with open(save_path, "w", encoding="utf-8") as f:
            f.write("\n".join(self.final_code))
        
        messagebox.showinfo("保存成功", f"文件已保存至：\n{save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = LaserPathConverter(root)
    root.mainloop()