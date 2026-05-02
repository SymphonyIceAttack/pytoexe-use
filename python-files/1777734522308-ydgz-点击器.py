import tkinter as tk
from tkinter import filedialog, simpledialog, ttk
from PIL import Image, ImageGrab
import cv2
import numpy as np
import pyautogui
import time
import random
import threading
import json
import os

class ImageRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图像识别与点击")
        self.image_list = []  # 存储 (图像路径, 等待时间)
        self.default_wait_time = 100  # 默认等待时间 100 毫秒
        self.screenshot_area = None
        self.rect = None
        self.start_x = None
        self.start_y = None
        self.canvas = None
        self.running = False
        self.thread = None
        self.loop_count = 1  # 默认循环次数，0 表示无限循环
        self.config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
        self.init_ui()

    def init_ui(self):
        # 左侧布局
        self.left_frame = tk.Frame(self.root)
        self.left_frame.pack(side=tk.LEFT, padx=10, pady=10)

        self.upload_button = tk.Button(self.left_frame, text="上传图像", command=self.upload_image)
        self.upload_button.pack(pady=5)

        self.screenshot_button = tk.Button(self.left_frame, text="框选截图", command=self.prepare_capture_screenshot)
        self.screenshot_button.pack(pady=5)

        self.delete_button = tk.Button(self.left_frame, text="删除图片", command=self.delete_selected_image)
        self.delete_button.pack(pady=5)

        # 循环次数设置按钮
        self.loop_button = tk.Button(self.left_frame, text="设置循环次数", command=self.set_loop_count)
        self.loop_button.pack(pady=5)

        # 显示当前循环次数
        self.loop_label = tk.Label(self.left_frame, text="循环次数: 1（0=无限）")
        self.loop_label.pack(pady=2)

        self.toggle_run_button = tk.Button(self.left_frame, text="开始运行", command=self.toggle_script)
        self.toggle_run_button.pack(pady=5)

        # 保存配置按钮
        self.save_button = tk.Button(self.left_frame, text="保存配置", command=self.save_config)
        self.save_button.pack(pady=5)

        # 加载配置按钮
        self.load_button = tk.Button(self.left_frame, text="加载配置", command=self.load_config)
        self.load_button.pack(pady=5)

        # 右侧布局
        self.right_frame = tk.Frame(self.root)
        self.right_frame.pack(side=tk.RIGHT, padx=10, pady=10)

        self.tree = ttk.Treeview(self.right_frame, columns=("图片", "等待时间"), show='headings')
        self.tree.heading("图片", text="图片")
        self.tree.heading("等待时间", text="等待时间 (毫秒)")
        self.tree.column("图片", width=200)
        self.tree.column("等待时间", width=200)
        self.tree.pack(pady=5)
        self.tree.bind('<Double-1>', self.edit_wait_time)

    def set_loop_count(self):
        count = simpledialog.askinteger(
            "设置循环次数",
            "请输入循环次数（0 = 无限循环）：",
            initialvalue=self.loop_count,
            minvalue=0
        )
        if count is not None:
            self.loop_count = count
            display = "无限循环" if count == 0 else str(count)
            self.loop_label.config(text=f"循环次数: {display}（0=无限）")

    def save_config(self):
        """保存当前图像列表和循环次数到 JSON 文件"""
        config = {
            "loop_count": self.loop_count,
            "images": [
                {"path": img_path, "wait_time": wait_time}
                for img_path, wait_time in self.image_list
            ]
        }
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("JSON 文件", "*.json")],
            initialfile="config.json"
        )
        if save_path:
            with open(save_path, "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            print(f"配置已保存到: {save_path}")

    def load_config(self):
        """从 JSON 文件加载图像列表和循环次数"""
        load_path = filedialog.askopenfilename(
            filetypes=[("JSON 文件", "*.json")]
        )
        if load_path:
            try:
                with open(load_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                self.loop_count = config.get("loop_count", 1)
                display = "无限循环" if self.loop_count == 0 else str(self.loop_count)
                self.loop_label.config(text=f"循环次数: {display}（0=无限）")
                self.image_list = [
                    (item["path"], item.get("wait_time", self.default_wait_time))
                    for item in config.get("images", [])
                ]
                self.update_image_listbox()
                print(f"配置已加载: {load_path}")
            except Exception as e:
                print(f"加载配置失败: {e}")

    def upload_image(self):
        file_path = filedialog.askopenfilename(filetypes=[("Image files", "*.jpg *.png")])
        if file_path:
            self.image_list.append((file_path, self.default_wait_time))
            self.update_image_listbox()

    def prepare_capture_screenshot(self):
        self.root.withdraw()
        time.sleep(0.5)
        self.top = tk.Toplevel(self.root)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)
        self.canvas = tk.Canvas(self.top, cursor="cross", bg='grey')
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)

    def on_button_press(self, event):
        self.start_x = event.x
        self.start_y = event.y
        if self.rect:
            self.canvas.delete(self.rect)
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_mouse_drag(self, event):
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)

    def on_button_release(self, event):
        end_x = event.x
        end_y = event.y
        bbox = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
        timestamp = f"JT{random.randint(100000, 999999)}.png"
        screenshot_path = timestamp
        screenshot = ImageGrab.grab(bbox)
        screenshot.save(screenshot_path)
        self.image_list.append((screenshot_path, self.default_wait_time))
        self.update_image_listbox()
        self.top.destroy()
        self.root.deiconify()

    def update_image_listbox(self):
        for row in self.tree.get_children():
            self.tree.delete(row)
        for img_path, wait_time in self.image_list:
            self.tree.insert("", tk.END, values=(img_path, wait_time))

    def edit_wait_time(self, event):
        selected_item = self.tree.selection()[0]
        selected_index = self.tree.index(selected_item)
        selected_image = self.image_list[selected_index]
        new_wait_time = simpledialog.askinteger("修改等待时间", "请输入新的等待时间（毫秒）：", initialvalue=selected_image[1])
        if new_wait_time is not None:
            self.image_list[selected_index] = (selected_image[0], new_wait_time)
            self.update_image_listbox()

    def delete_selected_image(self):
        selected_item = self.tree.selection()
        if selected_item:
            selected_index = self.tree.index(selected_item[0])
            del self.image_list[selected_index]
            self.update_image_listbox()

    def toggle_script(self):
        if not self.running:
            self.start_script_thread()
            self.toggle_run_button.config(text="停止运行")
        else:
            self.stop_script()
            self.toggle_run_button.config(text="开始运行")

    def start_script_thread(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_script, daemon=True)
            self.thread.start()

    def run_script(self):
        current_loop = 0
        while self.running:
            for img_path, wait_time in self.image_list:
                if not self.running:
                    break
                self.match_and_click(img_path)
                time.sleep(wait_time / 1000.0)
            current_loop += 1
            if self.loop_count != 0 and current_loop >= self.loop_count:
                break
        self.running = False
        self.root.after(0, lambda: self.toggle_run_button.config(text="开始运行"))
        print("脚本已停止")

    def stop_script(self):
        self.running = False

    def match_and_click(self, template_path):
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
        template = cv2.imread(template_path, 0)
        if template is None:
            print(f"无法读取图像: {template_path}")
            return
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
        result = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
        threshold = 0.8
        loc = np.where(result >= threshold)
        found = False
        for pt in zip(*loc[::-1]):
            click_x = pt[0] + template.shape[1] // 2
            click_y = pt[1] + template.shape[0] // 2
            pyautogui.click(click_x, click_y)
            found = True
            break
        if not found:
            print(f"未找到匹配区域: {template_path}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRecognitionApp(root)
    root.mainloop()
