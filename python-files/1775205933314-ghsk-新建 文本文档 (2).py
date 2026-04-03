import tkinter as tk
import random
import sys

# ========== 专属配置 ==========
NAME = "杨惋云"
# ==============================

class RomanticSurprise:
    def __init__(self, root):
        self.root = root
        self.root.title("")
        self.root.attributes("-fullscreen", True)
        self.root.configure(bg="#121226")
        self.root.overrideredirect(True)
        self.root.protocol("WM_DELETE_WINDOW", self.close_check)
        self.root.bind("<Escape>", self.close_check)

        # 画布
        self.canvas = tk.Canvas(root, bg="#121226", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # 特效数组
        self.cherry_blossoms = []
        self.hearts = []
        self.text_content = ""
        self.text_index = 0
        self.text_id = None

        # 初始化特效
        self.init_effects()
        self.type_text()
        self.animate()

    # 浪漫文案（超长高级走心版）
    def get_love_text(self):
        return f"""致我最珍贵的 {NAME}：

我把所有的温柔与浪漫，都藏在了这个不经意的瞬间里。
世间万物，人海茫茫，唯独你，是我一眼心动的偏爱与例外。

我不想用华丽的辞藻堆砌情话，只想告诉你：
遇见你之后，星辰失色，万物温柔，
所有平凡的日子，都因为你而变得闪闪发光。

我的满心欢喜，全部给你；
我的岁岁年年，都想与你相伴。
不用质疑我的真心，
我的偏爱、我的耐心、我的温柔，
自始至终，只属于你一个人。

山野万里，你是我藏在微风里的喜欢；
星河璀璨，你是我穷尽一生的奔赴。
我爱你，不止于今时今日，
而是朝朝暮暮，岁岁年年，永不停歇。"""

    # 打字机效果
    def type_text(self):
        full_text = self.get_love_text()
        if self.text_index < len(full_text):
            self.text_content += full_text[self.text_index]
            self.text_index += 1
            if self.text_id:
                self.canvas.delete(self.text_id)
            self.text_id = self.canvas.create_text(
                self.root.winfo_screenwidth()//2, 100,
                text=self.text_content, font=("微软雅黑", 18),
                fill="#e2c9ff", justify=tk.CENTER, anchor=tk.N
            )
            self.root.after(30, self.type_text)

    # 初始化樱花+爱心特效
    def init_effects(self):
        # 樱花
        for _ in range(40):
            x = random.randint(0, self.root.winfo_screenwidth())
            y = random.randint(-800, -50)
            size = random.randint(8, 16)
            speed = random.uniform(1, 2.5)
            sway = random.uniform(-0.3, 0.3)
            self.cherry_blossoms.append([x, y, size, speed, sway])
        
        # 爱心
        for _ in range(25):
            x = random.randint(0, self.root.winfo_screenwidth())
            y = random.randint(-600, -50)
            r = random.randint(6, 14)
            dy = random.uniform(0.8, 2)
            dx = random.uniform(-0.4, 0.4)
            self.hearts.append([x, y, r, dx, dy])

    # 动态动画
    def animate(self):
        self.canvas.delete("blossom", "heart")
        w, h = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

        # 樱花飘落
        for flower in self.cherry_blossoms:
            x, y, size, speed, sway = flower
            self.canvas.create_oval(x, y, x+size, y+size, fill="#ffc2e2", outline="", tags="blossom")
            flower[0] += sway
            flower[1] += speed
            if flower[1] > h:
                flower[0] = random.randint(0, w)
                flower[1] = random.randint(-200, -50)

        # 爱心浮动
        for heart in self.hearts:
            x, y, r, dx, dy = heart
            self.canvas.create_oval(x-r, y-r, x+r, y+r, fill="#d4afff", outline="", tags="heart")
            heart[0] += dx
            heart[1] += dy
            if heart[1] > h:
                heart[0] = random.randint(50, w-50)
                heart[1] = random.randint(-300, -50)

        self.root.after(25, self.animate)

    # 关闭确认
    def close_check(self, event=None):
        top = tk.Toplevel(self.root)
        top.geometry("400x150+500+350")
        top.configure(bg="#1a1a35")
        top.resizable(0,0)
        tk.Label(top, text="真的要关掉这份专属浪漫吗？", font=("微软雅黑",14), 
                 fg="#e2c9ff", bg="#1a1a35").pack(pady=30)
        tk.Button(top, text="确定关闭", command=sys.exit, 
                  bg="#2d2b55", fg="white", width=10, height=2).pack()
        top.grab_set()

if __name__ == "__main__":
    root = tk.Tk()
    app = RomanticSurprise(root)
    root.mainloop()