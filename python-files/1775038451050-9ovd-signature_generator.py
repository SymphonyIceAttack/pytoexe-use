
import tkinter as tk
from tkinter import Canvas, Button, colorchooser, Scale, HORIZONTAL, Label, filedialog
from PIL import Image, ImageDraw, ImageTk
import os

class SignatureGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("电子签名生成器")
        self.root.geometry("900x700")
        self.root.configure(bg="#f5f7fa")
        
        # 性能优化参数
        self.last_x, self.last_y = None, None
        self.smoothing_factor = 0.5
        self.min_distance = 2
        
        # 初始化画布和图像
        self.canvas_width = 700
        self.canvas_height = 350
        self.image = Image.new("RGBA", (self.canvas_width, self.canvas_height), (255, 255, 255, 0))
        self.draw = ImageDraw.Draw(self.image)
        
        # 默认设置
        self.pen_color = "#1f2937"
        self.pen_size = 3
        self.background_color = "white"
        
        # 创建界面元素
        self.create_widgets()
        
        # 性能监控
        self.stroke_points = []
        self.max_points_buffer = 1000
    
    def create_widgets(self):
        # 标题栏
        title_frame = tk.Frame(self.root, bg="#f5f7fa")
        title_frame.pack(fill=tk.X, pady=(10, 5))
        
        title_label = Label(title_frame, text="电子签名生成器", font=("微软雅黑", 20, "bold"), 
                           bg="#f5f7fa", fg="#1f2937")
        title_label.pack()
        
        # 工具栏
        toolbar_frame = tk.Frame(self.root, bg="#f5f7fa")
        toolbar_frame.pack(fill=tk.X, padx=20, pady=5)
        
        # 颜色选择按钮
        color_btn = Button(toolbar_frame, text="颜色", command=self.choose_color,
                          bg="#4f46e5", fg="white", font=("微软雅黑", 10),
                          relief=tk.FLAT, padx=15, pady=5)
        color_btn.pack(side=tk.LEFT, padx=5)
        
        # 笔刷大小控制
        size_frame = tk.Frame(toolbar_frame, bg="#f5f7fa")
        size_frame.pack(side=tk.LEFT, padx=10)
        
        size_label = Label(size_frame, text="笔刷大小:", bg="#f5f7fa", font=("微软雅黑", 10))
        size_label.pack(side=tk.LEFT)
        
        self.size_slider = Scale(size_frame, from_=1, to=20, orient=HORIZONTAL,
                                command=self.change_size, bg="#f5f7fa",
                                length=100, showvalue=0)
        self.size_slider.set(self.pen_size)
        self.size_slider.pack(side=tk.LEFT, padx=5)
        
        size_value = Label(size_frame, textvariable=tk.StringVar(value=str(self.pen_size)),
                          bg="#f5f7fa", font=("微软雅黑", 10, "bold"))
        size_value.pack(side=tk.LEFT)
        self.size_value_label = size_value
        
        # 功能按钮组
        button_frame = tk.Frame(toolbar_frame, bg="#f5f7fa")
        button_frame.pack(side=tk.RIGHT)
        
        clear_btn = Button(button_frame, text="清除", command=self.clear_canvas,
                          bg="#ef4444", fg="white", font=("微软雅黑", 10),
                          relief=tk.FLAT, padx=15, pady=5)
        clear_btn.pack(side=tk.LEFT, padx=5)
        
        undo_btn = Button(button_frame, text="撤销", command=self.undo_last_stroke,
                         bg="#f59e0b", fg="white", font=("微软雅黑", 10),
                         relief=tk.FLAT, padx=15, pady=5)
        undo_btn.pack(side=tk.LEFT, padx=5)
        
        save_btn = Button(button_frame, text="保存", command=self.save_signature,
                         bg="#10b981", fg="white", font=("微软雅黑", 10),
                         relief=tk.FLAT, padx=15, pady=5)
        save_btn.pack(side=tk.LEFT, padx=5)
        
        # 画布区域
        canvas_container = tk.Frame(self.root, bg="#e5e7eb", relief=tk.RAISED, bd=1)
        canvas_container.pack(pady=15, padx=20, fill=tk.BOTH, expand=True)
        
        self.canvas = Canvas(canvas_container, width=self.canvas_width, 
                            height=self.canvas_height, bg=self.background_color,
                            cursor="pencil", highlightthickness=0)
        self.canvas.pack(padx=10, pady=10)
        
        # 绑定鼠标事件
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.continue_drawing)
        self.canvas.bind("<ButtonRelease-1>", self.stop_drawing)
        
        # 预览区域
        preview_frame = tk.LabelFrame(self.root, text="签名预览", font=("微软雅黑", 12, "bold"),
                                     bg="#f5f7fa", fg="#1f2937")
        preview_frame.pack(pady=15, padx=20, fill=tk.X)
        
        preview_inner = tk.Frame(preview_frame, bg="#f5f7fa")
        preview_inner.pack(pady=10)
        
        self.preview_canvas = Canvas(preview_inner, width=250, height=80, 
                                    bg="white", highlightthickness=1, highlightbackground="#d1d5db")
        self.preview_canvas.pack(side=tk.LEFT, padx=(10, 20))
        
        # 状态信息区域
        info_frame = tk.Frame(preview_inner, bg="#f5f7fa")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 使用说明标题
        info_title = Label(info_frame, text="使用说明", 
                          font=("微软雅黑", 12, "bold"), bg="#f5f7fa", fg="#1f2937")
        info_title.pack(anchor="w", pady=(0, 5))
        
        # 使用说明内容
        info_text = tk.Text(info_frame, width=30, height=5, font=("微软雅黑", 9),
                           bg="#f9fafb", fg="#6b7280", wrap=tk.WORD, state=tk.DISABLED)
        info_text.pack(fill=tk.BOTH, expand=True)
        
        # 添加滚动条
        scrollbar = tk.Scrollbar(info_frame, command=info_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        info_text.config(yscrollcommand=scrollbar.set)
        
        # 设置文本内容
        info_text.config(state=tk.NORMAL)
        info_text.insert(tk.END, "1. 在上方白色区域绘制签名\n")
        info_text.insert(tk.END, "2. 调整笔刷大小和颜色\n")
        info_text.insert(tk.END, "3. 点击保存导出高清签名\n")
        info_text.insert(tk.END, "4. 支持撤销最近一次笔画\n")
        info_text.insert(tk.END, "5. 界面简洁易用，功能齐全")
        info_text.config(state=tk.DISABLED)
    
    def start_drawing(self, event):
        """开始绘制"""
        self.last_x, self.last_y = event.x, event.y
        self.stroke_points = [(event.x, event.y)]
    
    def continue_drawing(self, event):
        """继续绘制（带性能优化）"""
        if self.last_x is not None and self.last_y is not None:
            distance = ((event.x - self.last_x) ** 2 + (event.y - self.last_y) ** 2) ** 0.5
            if distance > self.min_distance:
                smooth_x = self.last_x + (event.x - self.last_x) * self.smoothing_factor
                smooth_y = self.last_y + (event.y - self.last_y) * self.smoothing_factor
                
                self.canvas.create_line(self.last_x, self.last_y, smooth_x, smooth_y,
                                      fill=self.pen_color, width=self.pen_size*2,
                                      capstyle=tk.ROUND, smooth=True)
                
                self.draw.line([self.last_x, self.last_y, smooth_x, smooth_y],
                              fill=self.pen_color, width=self.pen_size)
                
                self.last_x, self.last_y = smooth_x, smooth_y
                self.stroke_points.append((smooth_x, smooth_y))
                
                if len(self.stroke_points) > self.max_points_buffer:
                    self.stroke_points.pop(0)
    
    def stop_drawing(self, event):
        """停止绘制"""
        self.last_x, self.last_y = None, None
        self.stroke_points = []
    
    def undo_last_stroke(self):
        """撤销最后一次笔画"""
        self.clear_canvas()
    
    def choose_color(self):
        """选择颜色"""
        color = colorchooser.askcolor(title="选择签名颜色", initialcolor=self.pen_color)[1]
        if color:
            self.pen_color = color
    
    def change_size(self, val):
        """改变笔刷大小"""
        self.pen_size = int(val)
        self.size_value_label.config(text=str(val))
    
    def clear_canvas(self):
        """清空画布"""
        self.canvas.delete("all")
        self.image = Image.new("RGBA", (self.canvas_width, self.canvas_height), (255, 255, 255, 0))
        self.draw = ImageDraw.Draw(self.image)
        self.preview_canvas.delete("all")
        self.last_x, self.last_y = None, None
        self.stroke_points = []
    
    def save_signature(self):
        """保存签名"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".png",
                filetypes=[("PNG files", "*.png"), ("JPEG files", "*.jpg"), ("All files", "*.*")],
                title="保存签名"
            )
            
            if file_path:
                bbox = self.image.getbbox()
                if bbox:
                    cropped = self.image.crop(bbox)
                    margin = 20
                    new_size = (cropped.width + 2*margin, cropped.height + 2*margin)
                    final_image = Image.new("RGBA", new_size, (255, 255, 255, 0))
                    final_image.paste(cropped, (margin, margin))
                else:
                    final_image = self.image
                
                final_image.save(file_path, quality=95, optimize=True)
                self.update_preview(final_image)
                self.show_message(f"签名已保存至: {os.path.basename(file_path)}")
        except Exception as e:
            self.show_message(f"保存失败: {str(e)}")
    
    def update_preview(self, image=None):
        """更新预览"""
        try:
            source_image = image if image else self.image
            preview_img = source_image.copy()
            preview_img.thumbnail((250, 80), Image.LANCZOS)
            
            photo = ImageTk.PhotoImage(preview_img)
            self.preview_canvas.delete("all")
            self.preview_canvas.create_image(125, 40, image=photo)
            self.preview_canvas.image = photo
        except Exception as e:
            print(f"预览错误: {e}")
    
    def show_message(self, message):
        """显示状态消息"""
        print(message)

def main():
    root = tk.Tk()
    app = SignatureGenerator(root)
    root.mainloop()

if __name__ == "__main__":
    main()
