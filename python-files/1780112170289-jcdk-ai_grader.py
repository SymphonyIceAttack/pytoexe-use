import tkinter as tk
from tkinter import messagebox
import requests
import base64
import json
import time
import io
import pyautogui
from PIL import ImageGrab

# ================== 屏幕框选工具类 ==================
class ScreenSelector(tk.Toplevel):
    def __init__(self, callback):
        super().__init__()
        self.callback = callback
        self.start_x = None
        self.start_y = None
        self.rect = None
        self.area = None

        # 设置全屏、置顶、黑色半透明背景
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        self.attributes('-alpha', 0.3)
        self.config(cursor="cross")

        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.canvas.bind('<ButtonPress-1>', self.on_press)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

        self.focus_set()

    def on_press(self, event):
        self.start_x, self.start_y = event.x, event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)

    def on_drag(self, event):
        if self.rect:
            self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    def on_release(self, event):
        if self.rect:
            self.canvas.delete(self.rect)
        self.area = (min(self.start_x, event.x), min(self.start_y, event.y), max(self.start_x, event.x), max(self.start_y, event.y))
        self.destroy()
        self.callback(self.area)


# ================== 主应用程序类 ==================
class AutoGraderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("AI 自动阅卷助手 v1.0")
        self.root.geometry("450x400")
        self.root.attributes('-topmost', True) # 窗口始终置顶，方便操作
        
        self.capture_area = None
        self.setup_ui()

    def setup_ui(self):
        frame = tk.Frame(self.root, padx=15, pady=15)
        frame.pack(fill=tk.BOTH, expand=True)

        tk.Label(frame, text="智谱 API Key:", font=("微软雅黑", 9)).pack(anchor='w')
        self.api_key_entry = tk.Entry(frame, width=45, show="*")
        self.api_key_entry.pack(pady=(0, 10))

        tk.Label(frame, text="标准答案与评分规则:", font=("微软雅黑", 9)).pack(anchor='w')
        self.answer_text = tk.Text(frame, height=6, width=50, font=("微软雅黑", 9))
        self.answer_text.pack(pady=(0, 10))

        btn_frame = tk.Frame(frame)
        btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_select = tk.Button(btn_frame, text="1. 设定截屏区域", command=self.select_area, bg="#2196F3", fg="white", font=("微软雅黑", 9, "bold"))
        self.btn_select.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        
        self.btn_start = tk.Button(btn_frame, text="2. 一键阅卷并输入", command=self.start_grading, bg="#4CAF50", fg="white", font=("微软雅黑", 9, "bold"))
        self.btn_start.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(5,0))

        self.status_label = tk.Label(frame, text="状态：等待设定区域...", fg="gray", font=("微软雅黑", 9), wraplength=400, justify=tk.LEFT)
        self.status_label.pack(anchor='w', pady=(15,0))

    def select_area(self):
        self.root.withdraw() # 隐藏主窗口
        self.status_label.config(text="状态：请在屏幕上框选学生作答区域...")
        # 开启全屏选区
        ScreenSelector(self.on_area_selected)

    def on_area_selected(self, area):
        self.root.deiconify() # 恢复主窗口
        if area and (area[2] - area[0] > 10 and area[3] - area[1] > 10):
            self.capture_area = area
            self.status_label.config(text=f"状态：区域已设定 ✓\n坐标: 左上({area[0]},{area[1]}) 到 右下({area[2]},{area[3]})")
        else:
            self.status_label.config(text="状态：区域选择无效，请重新选择。")

    def start_grading(self):
        if not self.capture_area:
            messagebox.showwarning("警告", "请先点击'设定截屏区域'！")
            return
            
        api_key = self.api_key_entry.get().strip()
        criteria = self.answer_text.get("1.0", tk.END).strip()
        
        if not api_key or not criteria:
            messagebox.showwarning("警告", "请填写 API Key 和 标准答案！")
            return

        self.btn_start.config(state=tk.DISABLED)
        self.status_label.config(text="状态：正在截屏并发送给AI分析...请勿动鼠标", fg="blue")
        self.root.update()

        try:
            # 1. 截取预设区域
            img = ImageGrab.grab(bbox=self.capture_area)
            buffered = io.BytesIO()
            img.save(buffered, format="JPEG")
            img_base64 = base64.b64encode(buffered.getvalue()).decode('utf-8')
            img_url = f"data:image/jpeg;base64,{img_base64}"

            # 2. 调用智谱 GLM-4V API
            url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "glm-4v-flash", # 使用最便宜的视觉模型
                "response_format": {"type": "json_object"},
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": f"你是严格的阅卷老师。标准答案和规则：{criteria}。请看图打分，忽略涂改。只回复JSON格式：{{\"score\": 得分数字, \"reason\": \"一句话理由\"}}"},
                            {"type": "image_url", "image_url": {"url": img_url}}
                        ]
                    }
                ]
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=15)
            result = response.json()

            if "error" in result:
                raise Exception(f"API报错: {result['error']['message']}")

            content = result['choices'][0]['message']['content']
            ai_data = json.loads(content)
            score = str(ai_data.get('score', '0'))
            reason = ai_data.get('reason', '无理由')

            # 3. 准备模拟键盘输入
            self.status_label.config(text=f"状态：AI判定分数为 [{score}] 分。\n⚠️ 请立刻用鼠标点击阅卷软件的分数输入框！\n程序将在 3 秒后自动输入...", fg="red")
            self.root.update()
            
            time.sleep(3) # 给用户3秒钟时间点击目标输入框

            # 4. 模拟键盘敲击分数
            # 确保当前是英文输入法状态，否则数字可能输错
            pyautogui.typewrite(score)
            
            self.status_label.config(text=f"状态：阅卷完成 ✓\n分数：{score} 分\n理由：{reason}", fg="green")

        except json.JSONDecodeError:
            self.status_label.config(text="状态：AI返回格式错误，未获取到分数。", fg="red")
        except Exception as e:
            self.status_label.config(text=f"状态：发生错误 - {str(e)}", fg="red")
        finally:
            self.btn_start.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    app = AutoGraderApp(root)
    root.mainloop()