import sys
import os
import threading
import time
import pytesseract
from PIL import ImageGrab
import tkinter as tk
import tempfile
import shutil

# ===================== 配置项 =====================
CONFIG_FILE = "config.txt"
DETECT_INTERVAL = 0.3
HIGHLIGHT_COLOR = "red"
HIGHLIGHT_ALPHA = 0.3
# ==================================================

class ScreenHighlighter:
    def __init__(self):
        # 读取关键词
        self.keywords = self.load_keywords()
        if not self.keywords:
            self.show_error("未找到关键词，请创建 config.txt 文件，一行一个关键词")
            sys.exit()

        # 初始化Tesseract（内置到EXE中）
        self.init_tesseract()

        # 创建透明主窗口
        self.root = tk.Tk()
        self.root.title("屏幕文字高亮工具")
        self.root.attributes("-alpha", 0.0)
        self.root.attributes("-topmost", True)
        self.root.attributes("-fullscreen", True)
        self.root.attributes("-transparentcolor", "white")
        self.root.config(bg="white")

        # 创建画布用于绘制高亮框
        self.canvas = tk.Canvas(self.root, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 启动识别线程
        self.running = True
        self.detect_thread = threading.Thread(target=self.detect_loop, daemon=True)
        self.detect_thread.start()

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        print("✅ 屏幕文字高亮工具已启动")
        print(f"📋 正在监控的关键词：{self.keywords}")
        print("❌ 按 Alt+F4 关闭程序")

        self.root.mainloop()

    def load_keywords(self):
        """从同目录的config.txt读取关键词"""
        keywords = []
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and line not in keywords:
                        keywords.append(line)
        except FileNotFoundError:
            # 如果文件不存在，创建一个空的
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                f.write("# 一行一个关键词\n# 例如：\n# 开始\n# 确认\n# 提交\n")
        return keywords

    def init_tesseract(self):
        """初始化内置的Tesseract OCR引擎"""
        try:
            # 检查是否是打包后的EXE运行
            if hasattr(sys, '_MEIPASS'):
                base_path = sys._MEIPASS
            else:
                base_path = os.path.dirname(os.path.abspath(__file__))

            tess_path = os.path.join(base_path, "tesseract.exe")
            tessdata_path = os.path.join(base_path, "tessdata")

            if os.path.exists(tess_path):
                pytesseract.pytesseract.tesseract_cmd = tess_path
                os.environ['TESSDATA_PREFIX'] = tessdata_path
            else:
                # 如果没有内置，尝试使用系统安装的
                pytesseract.pytesseract.tesseract_cmd = "tesseract.exe"
        except Exception as e:
            self.show_error(f"OCR引擎初始化失败：{str(e)}\n请确保Tesseract已安装并添加到系统PATH")
            sys.exit(1)

    def detect_loop(self):
        """循环识别屏幕文字并高亮"""
        while self.running:
            try:
                # 截取整个屏幕
                screen = ImageGrab.grab()
                
                # 使用Tesseract识别文字位置
                data = pytesseract.image_to_data(
                    screen,
                    lang="chi_sim+eng",
                    output_type=pytesseract.Output.DICT
                )

                # 清空上一轮的高亮框
                self.canvas.delete("all")

                # 遍历所有识别到的文字
                n_boxes = len(data["text"])
                for i in range(n_boxes):
                    text = data["text"][i].strip()
                    if not text:
                        continue

                    # 检查是否包含关键词
                    for kw in self.keywords:
                        if kw in text:
                            x = data["left"][i]
                            y = data["top"][i]
                            w = data["width"][i]
                            h = data["height"][i]

                            # 绘制半透明高亮矩形
                            self.canvas.create_rectangle(
                                x, y, x + w, y + h,
                                fill=HIGHLIGHT_COLOR,
                                outline="",
                                alpha=HIGHLIGHT_ALPHA
                            )
            except Exception as e:
                pass  # 忽略识别过程中的错误

            time.sleep(DETECT_INTERVAL)

    def show_error(self, message):
        """显示错误消息"""
        root = tk.Tk()
        root.title("错误")
        root.geometry("400x150")
        label = tk.Label(root, text=message, wraplength=350, justify="center")
        label.pack(expand=True)
        button = tk.Button(root, text="确定", command=root.destroy)
        button.pack(pady=10)
        root.mainloop()

    def on_closing(self):
        """关闭程序时清理资源"""
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    try:
        app = ScreenHighlighter()
    except Exception as e:
        print(f"❌ 程序启动失败：{e}")
        time.sleep(5)
