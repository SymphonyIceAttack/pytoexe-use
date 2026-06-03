
import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageDraw
import random

class DigitalCamoGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("数字迷彩生成器 v1.0")

        self.add_slider("画布尺寸(px)", "size", 1024, 256, 4096)
        self.add_slider("方块尺寸(px)", "cell", 8, 2, 50)
        self.add_slider("密集程度", "density", 70, 10, 100)
        self.add_slider("不规则程度", "irregular", 80, 0, 100)
        self.add_slider("色块数量", "clusters", 60, 5, 300)

        tk.Button(root, text="生成并保存PNG", command=self.generate).pack(pady=10)

    def add_slider(self, label, attr, default, mn, mx):
        frame = tk.Frame(self.root)
        frame.pack(fill="x", padx=10, pady=4)
        tk.Label(frame, text=label, width=18, anchor="w").pack(side="left")
        scale = tk.Scale(frame, from_=mn, to=mx, orient="horizontal")
        scale.set(default)
        scale.pack(fill="x", expand=True)
        setattr(self, attr, scale)

    def generate(self):
        size = self.size.get()
        cell = self.cell.get()
        density = self.density.get()/100
        irregular = self.irregular.get()/100
        clusters = self.clusters.get()

        cols = size // cell
        rows = size // cell

        grid = [[0 for _ in range(cols)] for _ in range(rows)]

        for color_id in [1,2,3]:
            for _ in range(clusters // 3):
                x = random.randint(0, cols-1)
                y = random.randint(0, rows-1)

                growth = int((density * 250) + random.randint(0,80))

                frontier = [(x,y)]

                for _ in range(growth):
                    if not frontier:
                        break

                    cx, cy = random.choice(frontier)
                    grid[cy][cx] = color_id

                    dirs = [(1,0),(-1,0),(0,1),(0,-1)]

                    if random.random() < irregular:
                        dirs += [(1,1),(-1,-1),(1,-1),(-1,1)]

                    random.shuffle(dirs)

                    for dx,dy in dirs:
                        nx, ny = cx+dx, cy+dy
                        if 0 <= nx < cols and 0 <= ny < rows:
                            if random.random() < 0.5:
                                frontier.append((nx,ny))

        colors = {
            0:(220,220,220),
            1:(255,255,255),
            2:(140,140,140),
            3:(30,30,30)
        }

        img = Image.new("RGB",(size,size),(220,220,220))
        draw = ImageDraw.Draw(img)

        for y in range(rows):
            for x in range(cols):
                draw.rectangle(
                    [x*cell,y*cell,(x+1)*cell,(y+1)*cell],
                    fill=colors[grid[y][x]]
                )

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG","*.png")]
        )

        if path:
            img.save(path)
            messagebox.showinfo("完成", f"已保存:\n{path}")

root = tk.Tk()
app = DigitalCamoGenerator(root)
root.mainloop()
