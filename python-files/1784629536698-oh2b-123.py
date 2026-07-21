import tkinter as tkfrom tkinter import filedialog, messagebox
from PIL import Image
import os
 
class ImageCompressor:
    def __init__(self, root):
        self.root = root
        self.root.title("图片压缩工具 - 目标大小: 100KB以内")
        self.root.geometry("500x400")
 
        # 创建界面元素
        self.create_widgets()
 
    def create_widgets(self):
        # 选择图片按钮
        self.select_btn = tk.Button(self.root, text="选择图片", command=self.select_images)
        self.select_btn.pack(pady=10)
 
        # 显示选中的图片路径
        self.file_label = tk.Label(self.root, text="未选择图片", wraplength=400)
        self.file_label.pack(pady=5)
 
        # 压缩按钮
        self.compress_btn = tk.Button(self.root, text="开始压缩", command=self.compress_images, state=tk.DISABLED)
        self.compress_btn.pack(pady=10)
 
        # 进度显示
        self.progress_label = tk.Label(self.root, text="")
        self.progress_label.pack(pady=5)
 
        # 结果显示区域
        self.result_text = tk.Text(self.root, height=10, width=60)
        self.result_text.pack(pady=10)
 
        # 清空结果按钮
        self.clear_btn = tk.Button(self.root, text="清空结果", command=self.clear_results)
        self.clear_btn.pack(pady=5)
 
        # 图片路径变量
        self.image_paths = []
 
    def select_images(self):
        file_paths = filedialog.askopenfilenames(
            title="选择要压缩的图片",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.bmp *.tiff *.webp"),
                ("All files", "*.*")
            ]
        )
         
        if file_paths:
            self.image_paths = list(file_paths)
            self.file_label.config(text=f"已选择 {len(self.image_paths)} 张图片")
            self.compress_btn.config(state=tk.NORMAL)
            self.result_text.insert(tk.END, f"已选择 {len(self.image_paths)} 张图片\n")
            for path in self.image_paths:
                self.result_text.insert(tk.END, f"- {path}\n")
 
    def compress_images(self):
        if not self.image_paths:
            messagebox.showerror("错误", "请选择至少一张图片")
            return
 
        total_images = len(self.image_paths)
        success_count = 0
         
        for i, image_path in enumerate(self.image_paths):
            try:
                # 更新进度信息
                self.progress_label.config(text=f"正在处理第 {i+1}/{total_images} 张图片...")
                self.root.update()
                 
                # 获取原始文件大小
                original_size = os.path.getsize(image_path) / 1024  # KB
                self.result_text.insert(tk.END, f"\n处理图片: {os.path.basename(image_path)}\n")
                self.result_text.insert(tk.END, f"原始大小: {original_size:.2f} KB\n")
                 
                # 打开图片
                img = Image.open(image_path)
                 
                # 如果是PNG格式，转换为RGB以避免透明度问题
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                 
                # 确定输出路径
                output_path = self.generate_output_path_batch(image_path)
                 
                # 初始压缩质量
                quality = 95
                 
                # 循环压缩直到文件大小满足要求或质量达到最小值
                while True:
                    # 保存压缩图片
                    img.save(output_path, "JPEG", optimize=True, quality=quality)
                     
                    # 检查压缩后大小
                    compressed_size = os.path.getsize(output_path) / 1024  # KB
                     
                    self.progress_label.config(text=f"正在处理: {os.path.basename(image_path)}, 当前质量: {quality}, 大小: {compressed_size:.2f}KB")
                    self.root.update()
                     
                    # 如果大小已满足要求或质量已经很低
                    if compressed_size <= 100 or quality <= 10:
                        break
                     
                    # 调整质量 - 根据当前大小按比例调整
                    if compressed_size > 150:  # 如果远大于目标，步长可以大一些
                        quality -= 15
                    elif compressed_size > 120:
                        quality -= 8
                    else:
                        quality -= 5
                     
                    # 确保质量不小于10
                    quality = max(quality, 10)
                 
                # 最终检查和调整
                final_size = os.path.getsize(output_path) / 1024
                self.result_text.insert(tk.END, f"最终质量: {quality}, 最终大小: {final_size:.2f} KB\n")
                 
                if final_size <= 100:
                    self.result_text.insert(tk.END, f"&#9989; 压缩成功! 文件已保存至: {output_path}\n")
                    success_count += 1
                else:
                    self.result_text.insert(tk.END, f"&#9888;&#65039; 无法压缩到100KB以下，最低压缩到: {final_size:.2f} KB\n")
                 
                # 确保界面更新
                self.root.update()
                 
            except Exception as e:
                self.result_text.insert(tk.END, f"&#10060; 压缩失败: {str(e)}\n")
                messagebox.showerror("错误", f"压缩过程中出现错误: {str(e)}")
         
        # 完成后显示汇总信息
        self.progress_label.config(text="完成!")
        messagebox.showinfo("完成", f"批量压缩完成!\n总共处理: {total_images} 张图片\n成功压缩: {success_count} 张图片\n无法压缩到100KB以下: {total_images - success_count} 张图片")
 
    def generate_output_path_batch(self, input_path):
        """为批量处理生成输出文件路径"""
        base_name, ext = os.path.splitext(input_path)
        counter = 1
        while True:
            output_path = f"{base_name}_compressed_{counter}.jpg"
            if not os.path.exists(output_path):
                return output_path
            counter += 1
 
    def generate_output_path(self):
        """生成输出文件路径"""
        base_name, ext = os.path.splitext(self.image_path)
        counter = 1
        while True:
            output_path = f"{base_name}_compressed_{counter}.jpg"
            if not os.path.exists(output_path):
                return output_path
            counter += 1
 
    def clear_results(self):
        self.result_text.delete(1.0, tk.END)
 
    def compress_image(self):
        # 此方法已被compress_images替代，但保留用于向后兼容性
        pass
 
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageCompressor(root)
    root.mainloop()