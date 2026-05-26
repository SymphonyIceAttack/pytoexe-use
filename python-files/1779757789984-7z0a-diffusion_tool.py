import tkinter as tk
from tkinter import ttk, Canvas, Frame

# 主界面：扩散模型模拟器
class DiffusionSimulator:
    def __init__(self, root):
        self.root = root
        self.root.title("扩散模型 Diffusion Model - AI学习工具")
        self.root.geometry("900x550")
        self.root.resizable(False, False)

        # 状态：步数0-10，0清晰，10纯噪声
        self.step = 0
        self.max_step = 10

        # 创建界面
        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # 标题
        title = tk.Label(self.root, text="扩散模型原理可视化", font=("微软雅黑", 20, "bold"))
        title.pack(pady=10)

        # 说明
        desc = tk.Label(self.root, text="前向扩散：不断加噪 → 纯噪声\n反向生成：不断去噪 → 还原清晰图", font=("微软雅黑", 12))
        desc.pack()

        # 主画布区域
        self.canvas = Canvas(self.root, width=500, height=300, bg="white", bd=2, relief="solid")
        self.canvas.pack(pady=20)

        # 进度条
        self.progress_label = tk.Label(self.root, text=f"当前扩散步数：{self.step}/{self.max_step}", font=("微软雅黑", 14))
        self.progress_label.pack()

        # 按钮区
        btn_frame = Frame(self.root)
        btn_frame.pack(pady=15)

        self.noise_btn = ttk.Button(btn_frame, text="➡ 加噪（扩散）", command=self.add_noise)
        self.noise_btn.grid(row=0, column=0, padx=15)

        self.denoise_btn = ttk.Button(btn_frame, text="⬅ 去噪（生成）", command=self.remove_noise)
        self.denoise_btn.grid(row=0, column=1, padx=15)

        self.reset_btn = ttk.Button(btn_frame, text="🔄 重置", command=self.reset)
        self.reset_btn.grid(row=0, column=2, padx=15)

        # 概念解释区
        concept_frame = Frame(self.root)
        concept_frame.pack(pady=5)

        ttk.Label(concept_frame, text="📘 扩散模型核心概念", font=("微软雅黑", 13, "bold")).grid(row=0, column=0, columnspan=2)
        ttk.Label(concept_frame, text="• 前向过程：给图片逐步加噪").grid(row=1, column=0, sticky="w", pady=3)
        ttk.Label(concept_frame, text="• 反向过程：模型学习如何去掉噪点").grid(row=2, column=0, sticky="w", pady=3)
        ttk.Label(concept_frame, text="• AI画图：就是从纯噪声反向还原出图片").grid(row=3, column=0, sticky="w", pady=3)

    # 绘制当前状态
    def update_display(self):
        self.canvas.delete("all")
        w, h = 500, 300

        # 画一个简单的“图片”：人脸/图案
        if self.step == 0:
            # 清晰原图
            self.canvas.create_oval(150, 50, 350, 250, fill="#FFE4B5", outline="black", width=3)
            self.canvas.create_oval(200, 100, 240, 140, fill="black")  # 左眼
            self.canvas.create_oval(260, 100, 300, 140, fill="black")  # 右眼
            self.canvas.create_rectangle(220, 180, 280, 210, fill="#8B4513")  # 嘴
            self.canvas.create_text(250, 270, text="清晰原图", font=("微软雅黑", 14))

        else:
            # 噪声覆盖程度 = step/10
            cover_rate = self.step / self.max_step
            noise_area = int(w * cover_rate)

            # 底层：残留原图
            self.canvas.create_oval(150, 50, 350, 250, fill="#FFE4B5", outline="gray", width=1)
            self.canvas.create_oval(200, 100, 240, 140, fill="gray")
            self.canvas.create_oval(260, 100, 300, 140, fill="gray")
            self.canvas.create_rectangle(220, 180, 280, 210, fill="gray")

            # 上层：噪声方块
            for _ in range(120):
                import random
                x = random.randint(0, w)
                y = random.randint(0, h)
                size = random.randint(2, 8)
                self.canvas.create_rectangle(x, y, x+size, y+size, fill="black", outline="")

            # 文字提示
            if self.step < 4:
                tip = "轻微噪声"
            elif self.step < 7:
                tip = "中度噪声"
            elif self.step < 10:
                tip = "重度噪声"
            else:
                tip = "纯噪声"
            self.canvas.create_text(250, 270, text=tip, font=("微软雅黑", 14))

        self.progress_label.config(text=f"当前扩散步数：{self.step}/{self.max_step}")

    # 加噪（前向扩散）
    def add_noise(self):
        if self.step < self.max_step:
            self.step += 1
            self.update_display()

    # 去噪（反向生成）
    def remove_noise(self):
        if self.step > 0:
            self.step -= 1
            self.update_display()

    # 重置
    def reset(self):
        self.step = 0
        self.update_display()

if __name__ == "__main__":
    root = tk.Tk()
    app = DiffusionSimulator(root)
    root.mainloop()