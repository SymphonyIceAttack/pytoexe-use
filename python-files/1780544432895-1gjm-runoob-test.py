#!/usr/bin/python
# Write Python 3 code in this online editor and run it.
print("Hello, World!");
import sys
import os
import cv2
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog, messagebox

# 如果有训练好的YOLOv8模型，可以解开此注释
# from ultralytics import YOLO

class WatermarkRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 水印自动识别与清除工具 (x86)")
        self.root.geometry("900x700")

        # 状态变量
        self.image_path = None
        self.original_img = None
        self.display_img = None
        self.mask = None
        
        # AI模型载入标记
        self.model = None 
        # self.model = YOLO("yolov8n-seg.pt") # 替换为你训练好的水印分割模型

        # 界面布局
        self.init_ui()

    def init_ui(self):
        # 顶部工具栏
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        btn_open = tk.Button(btn_frame, text="导入图片", command=self.load_image, bg="#4CAF50", fg="white")
        btn_open.pack(side=tk.LEFT, padx=5)

        btn_auto_detect = tk.Button(btn_frame, text="AI 自动识别水印", command=self.ai_detect, bg="#2196F3", fg="white")
        btn_auto_detect.pack(side=tk.LEFT, padx=5)

        btn_remove = tk.Button(btn_frame, text="清除水印", command=self.remove_watermark, bg="#F44336", fg="white")
        btn_remove.pack(side=tk.LEFT, padx=5)

        btn_save = tk.Button(btn_frame, text="保存图片", command=self.save_image, bg="#FF9800", fg="white")
        btn_save.pack(side=tk.LEFT, padx=5)

        # 画笔大小调节
        tk.Label(btn_frame, text="手动微调画笔大小:").pack(side=tk.LEFT, padx=10)
        self.brush_size_slider = tk.Scale(btn_frame, from_=5, to=50, orient=tk.HORIZONTAL)
        self.brush_size_slider.set(15)
        self.brush_size_slider.pack(side=tk.LEFT)

        # 图像显示区域
        self.canvas = tk.Canvas(self.root, bg="gray")
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # 鼠标画笔绑定（用于手动微调AI没识别干净的地方）
        self.canvas.bind("<B1-Motion>", self.paint)

    def load_image(self):
        self.image_path = filedialog.askopenfilename(filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")])
        if not self.image_path:
            return

        self.original_img = cv2.imread(self.image_path)
        self.mask = np.zeros(self.original_img.shape[:2], dtype=np.uint8)
        self.show_image()

    def show_image(self):
        if self.original_img is None:
            return

        # 调整尺寸以适应视口
        h, w = self.original_img.shape[:2]
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        if canvas_w < 10: canvas_w = 800
        if canvas_h < 10: canvas_h = 500

        scale = min(canvas_w/w, canvas_h/h)
        new_w, new_h = int(w * scale), int(h * scale)
        
        # 缩放图像用于显示
        resized = cv2.resize(self.original_img, (new_w, new_h))
        # 转换为RGBA方便与红色的Mask混合显示
        self.display_img = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
        
        self.update_canvas()

    def update_canvas(self):
        if self.display_img is None:
            return
        
        # 混合Mask（半透明红色表示待消除区域）
        h, w = self.original_img.shape[:2]
        resized_mask = cv2.resize(self.mask, (self.display_img.shape[1], self.display_img.shape[0]))
        
        overlay = self.display_img.copy()
        overlay[resized_mask > 0] = [255, 0, 0] # 红色标记
        
        # 混合原图和红色标记
        blended = cv2.addWeighted(self.display_img, 0.7, overlay, 0.3, 0)

        img_pil = Image.fromarray(blended)
        self.img_tk = ImageTk.PhotoImage(image=img_pil)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.img_tk)

    def paint(self, event):
        """鼠标手动涂抹，用于AI识别不准时的补充"""
        if self.original_img is None:
            return
        
        # 计算比例
        canvas_w = self.img_tk.width()
        canvas_h = self.img_tk.height()
        img_h, img_w = self.original_img.shape[:2]

        # 将Canvas坐标映射回原图坐标
        rx = int(event.x * (img_w / canvas_w))
        ry = int(event.y * (img_h / canvas_h))

        brush_r = self.brush_size_slider.get()
        cv2.circle(self.mask, (rx, ry), brush_r, 255, -1)
        self.update_canvas()

    def ai_detect(self):
        """AI 自动识别水印算法接口"""
        if self.original_img is None:
            messagebox.showwarning("警告", "请先导入图片！")
            return

        # ----------------- AI识别算法部分 -----------------
        # 方法一：如果你训练了 YOLOv8-segmentation 模型：
        # if self.model:
        #     results = self.model(self.original_img)
        #     if results[0].masks is not None:
        #         # 获取分割掩膜并转为二值图
        #         self.mask = (results[0].masks.data[0].cpu().numpy() * 255).astype(np.uint8)
        #         self.mask = cv2.resize(self.mask, (self.original_img.shape[1], self.original_img.shape[0]))
        
        # 方法二：传统图像AI（亮度和边缘检测，针对特定纯色水印）
        gray = cv2.cvtColor(self.original_img, cv2.COLOR_BGR2GRAY)
        # 假设水印一般偏亮，用高通滤波或自适应阈值提取高亮文字
        thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        # 这里仅做一个演示性质的半自动提取接口（通过强度过滤）
        _, self.mask = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY) 
        
        # 膨胀一下掩膜，确保边缘也被覆盖
        kernel = np.ones((5, 5), np.uint8)
        self.mask = cv2.dilate(self.mask, kernel, iterations=1)
        
        self.update_canvas()
        messagebox.showinfo("提示", "AI识别完成，红色区域为识别到的水印。你可以用鼠标补充画笔微调。")

    def remove_watermark(self):
        """清除水印算法"""
        if self.original_img is None or self.mask is None:
            return
        
        # 使用 OpenCV Telea 算法进行图像修复（快速修复）
        # 如果需要更高画质，可以接入 LaMa 或其他 GAN 修复模型接口
        messagebox.showinfo("处理中", "正在清除水印，请稍候...")
        result = cv2.inpaint(self.original_img, self.mask, inpaintRadius=7, flags=cv2.INPAINT_TELEA)
        
        # 更新原图为去水印后的图，并清空Mask
        self.original_img = result
        self.mask = np.zeros(self.original_img.shape[:2], dtype=np.uint8)
        self.show_image()
        messagebox.showinfo("成功", "水印清除完毕！")

    def save_image(self):
        if self.original_img is None:
            return
        save_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG info", "*.png"), ("JPEG info", "*.jpg")])
        if save_path:
            cv2.imwrite(save_path, self.original_img)
            messagebox.showinfo("保存成功", f"照片已成功保存至:\n{save_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = WatermarkRemoverApp(root)
    root.mainloop()