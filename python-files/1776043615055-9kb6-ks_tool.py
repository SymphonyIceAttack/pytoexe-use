import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
from PIL import Image, ImageTk
import requests
import re
import os
import time
from urllib.parse import urlparse

# 配置请求头（模拟手机浏览器，防止被拦截）
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36',
    'Referer': 'https://www.kuaishou.com/'
}

# 创建保存图片的文件夹
SAVE_FOLDER = "快手商品图片"
if not os.path.exists(SAVE_FOLDER):
    os.makedirs(SAVE_FOLDER)

class KuaishouImageParser:
    def __init__(self, root):
        self.root = root
        self.root.title("快手商品图片解析下载器")
        self.root.geometry("800x600")
        self.root.resizable(False, False)
        
        # 初始化变量
        self.image_list = []  # 存储图片链接
        self.current_image = None  # 当前显示的图片对象
        
        # 创建界面
        self.create_widgets()

    def create_widgets(self):
        """创建GUI组件"""
        # 1. 输入区域
        input_label = ttk.Label(self.root, text="请粘贴快手分享文案：", font=("微软雅黑", 10))
        input_label.pack(pady=5)
        
        self.text_input = scrolledtext.ScrolledText(self.root, width=90, height=4)
        self.text_input.pack(pady=5)
        # 默认填入你提供的测试文案
        test_text = "фX-3csxLwrwvIb1MPф復制整段綃息，打開快掱35.99元 588#【百搭显瘦】高腰通勤牛仔短裤女夏款辣妹热裤T3"
        self.text_input.insert(tk.END, test_text)

        # 2. 按钮区域
        btn_frame = ttk.Frame(self.root)
        btn_frame.pack(pady=5)
        
        parse_btn = ttk.Button(btn_frame, text="开始解析", command=self.parse_content)
        parse_btn.grid(row=0, column=0, padx=10)
        
        clear_btn = ttk.Button(btn_frame, text="清空输入", command=lambda: self.text_input.delete(1.0, tk.END))
        clear_btn.grid(row=0, column=1, padx=10)

        # 3. 状态显示区域
        self.status_label = ttk.Label(self.root, text="状态：等待解析", font=("微软雅黑", 10))
        self.status_label.pack(pady=5)

        # 4. 图片显示区域
        img_label = ttk.Label(self.root, text="商品第一张图片：", font=("微软雅黑", 10))
        img_label.pack(pady=5)
        
        self.image_canvas = tk.Canvas(self.root, width=700, height=400, bg="white")
        self.image_canvas.pack(pady=5)

    def extract_url(self, text):
        """从文案中提取快手链接"""
        # 正则匹配快手短链接/商品链接
        pattern = r'[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z]+/[a-zA-Z0-9_-]+|kxapp://[a-zA-Z0-9_.]+'
        match = re.search(pattern, text)
        if match:
            return match.group()
        return None

    def get_real_url(self, short_url):
        """获取短链接的真实跳转地址"""
        try:
            response = requests.head(f"https://{short_url}" if "kuaishou" not in short_url else short_url, 
                                    headers=HEADERS, allow_redirects=True, timeout=10)
            return response.url
        except:
            return None

    def parse_content(self):
        """解析主函数"""
        self.status_label.config(text="状态：正在解析...")
        self.root.update()
        
        # 1. 获取输入文本
        content = self.text_input.get(1.0, tk.END).strip()
        if not content:
            messagebox.showerror("错误", "请输入快手分享文案！")
            self.status_label.config(text="状态：解析失败")
            return

        # 2. 提取链接
        url = self.extract_url(content)
        if not url:
            messagebox.showerror("错误", "未检测到有效链接！")
            self.status_label.config(text="状态：解析失败")
            return

        # 3. 获取真实商品页面
        real_url = self.get_real_url(url)
        if not real_url:
            messagebox.showerror("错误", "链接解析失败！")
            self.status_label.config(text="状态：解析失败")
            return

        # 4. 获取商品页面源码
        try:
            response = requests.get(real_url, headers=HEADERS, timeout=15)
            html = response.text
        except Exception as e:
            messagebox.showerror("错误", f"获取页面失败：{str(e)}")
            self.status_label.config(text="状态：解析失败")
            return

        # 5. 提取商品图片链接（正则匹配商品主图）
        img_pattern = r'https?://[^\s"<>]+?\.jpg|https?://[^\s"<>]+?\.png'
        img_urls = re.findall(img_pattern, html)
        # 去重+过滤无效链接
        self.image_list = list(set([img for img in img_urls if "kuaishou" in img or "kwai" in img]))

        if not self.image_list:
            messagebox.showerror("错误", "未找到商品图片！")
            self.status_label.config(text="状态：解析失败")
            return

        # 6. 下载并显示第一张图片
        self.status_label.config(text=f"状态：找到 {len(self.image_list)} 张图片，正在下载第一张...")
        self.root.update()
        
        self.download_and_show_image(self.image_list[0])

    def download_and_show_image(self, img_url):
        """下载图片并显示在窗口中"""
        try:
            # 下载图片
            img_data = requests.get(img_url, headers=HEADERS, timeout=10).content
            
            # 保存图片到本地
            img_name = f"快手商品_{int(time.time())}.jpg"
            img_path = os.path.join(SAVE_FOLDER, img_name)
            
            with open(img_path, "wb") as f:
                f.write(img_data)

            # 打开并调整图片尺寸
            image = Image.open(img_path)
            # 等比例缩放，适应画布
            canvas_w, canvas_h = 700, 400
            img_w, img_h = image.size
            scale = min(canvas_w/img_w, canvas_h/img_h)
            new_w = int(img_w * scale)
            new_h = int(img_h * scale)
            image = image.resize((new_w, new_h), Image.Resampling.LANCZOS)

            # 转换为Tkinter可用的格式
            self.current_image = ImageTk.PhotoImage(image)

            # 清空画布并显示图片
            self.image_canvas.delete(tk.ALL)
            self.image_canvas.create_image(canvas_w//2, canvas_h//2, anchor=tk.CENTER, image=self.current_image)

            self.status_label.config(text=f"状态：解析成功！图片已保存到：{SAVE_FOLDER}")
            messagebox.showinfo("成功", f"解析完成！\n共找到{len(self.image_list)}张图片\n第一张已显示并保存！")

        except Exception as e:
            messagebox.showerror("错误", f"图片加载失败：{str(e)}")
            self.status_label.config(text="状态：图片加载失败")

if __name__ == "__main__":
    root = tk.Tk()
    app = KuaishouImageParser(root)
    root.mainloop()