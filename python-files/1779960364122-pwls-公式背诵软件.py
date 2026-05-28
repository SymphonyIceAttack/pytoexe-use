import tkinter as tk
from tkinter import ttk, messagebox
import random

# 公式题库
questions = [
    {"question": "正方形周长公式：C = ？", "answer": "4a", "hint": "a代表边长"},
    {"question": "正方形面积公式：S = ？", "answer": "a²", "hint": "a代表边长"},
    {"question": "长方形周长公式：C = ？", "answer": "2(a+b)", "hint": "a长，b宽"},
    {"question": "长方形面积公式：S = ？", "answer": "ab", "hint": "a长，b宽"},
    {"question": "平行四边形面积公式：S = ？", "answer": "ah", "hint": "a底，h高"},
    {"question": "三角形面积公式：S = ？", "answer": "ah÷2", "hint": "a底，h高"},
    {"question": "梯形面积公式：S = ？", "answer": "(a+b)h÷2", "hint": "a上底，b下底，h高"},
    {"question": "圆的周长公式：C = ？", "answer": "2πr", "hint": "r是半径"},
    {"question": "圆的面积公式：S = ？", "answer": "πr²", "hint": "r是半径"},
    {"question": "正方体表面积公式：S = ？", "answer": "6a²", "hint": "a是棱长"},
    {"question": "正方体体积公式：V = ？", "answer": "a³", "hint": "a是棱长"},
    {"question": "长方体表面积公式：S = ？", "answer": "2(ab+ah+bh)", "hint": "a长，b宽，h高"},
    {"question": "长方体体积公式：V = ？", "answer": "abh", "hint": "a长，b宽，h高"},
    {"question": "圆柱侧面积公式：S = ？", "answer": "2πrh", "hint": "r半径，h高"},
    {"question": "圆柱体积公式：V = ？", "answer": "πr²h", "hint": "r半径，h高"},
    {"question": "圆锥体积公式：V = ？", "answer": "πr²h÷3", "hint": "r半径，h高"}
]

class FormulaApp:
    def __init__(self, root):
        self.root = root
        self.root.title("六年级数学图形公式背诵软件")
        self.root.geometry("600x450")
        self.root.resizable(False, False)
        
        self.score = 0
        self.total = len(questions)
        self.current_q = None
        self.answered = False
        
        # 界面布局
        self.title_label = ttk.Label(root, text="📐 图形公式背诵软件", font=("微软雅黑", 18, "bold"))
        self.title_label.pack(pady=15)
        
        self.question_frame = ttk.LabelFrame(root, text="题目", padding=15)
        self.question_frame.pack(fill="x", padx=30, pady=10)
        
        self.question_label = ttk.Label(self.question_frame, text="点击「开始背诵」开始", font=("微软雅黑", 14), wraplength=500)
        self.question_label.pack()
        
        self.hint_label = ttk.Label(self.question_frame, text="", font=("微软雅黑", 10), foreground="gray")
        self.hint_label.pack(pady=5)
        
        self.answer_frame = ttk.Frame(root, padding=15)
        self.answer_frame.pack(fill="x", padx=30, pady=10)
        
        ttk.Label(self.answer_frame, text="你的答案：", font=("微软雅黑", 12)).grid(row=0, column=0, sticky="w")
        self.answer_entry = ttk.Entry(self.answer_frame, font=("微软雅黑", 12), width=30)
        self.answer_entry.grid(row=0, column=1, padx=10)
        
        self.button_frame = ttk.Frame(root, padding=10)
        self.button_frame.pack(pady=10)
        
        self.start_btn = ttk.Button(self.button_frame, text="开始背诵", command=self.next_question)
        self.start_btn.grid(row=0, column=0, padx=10)
        
        self.submit_btn = ttk.Button(self.button_frame, text="提交答案", command=self.check_answer, state="disabled")
        self.submit_btn.grid(row=0, column=1, padx=10)
        
        self.show_btn = ttk.Button(self.button_frame, text="查看答案", command=self.show_answer, state="disabled")
        self.show_btn.grid(row=0, column=2, padx=10)
        
        self.score_label = ttk.Label(root, text=f"当前得分：{self.score}/{self.total}", font=("微软雅黑", 12))
        self.score_label.pack(pady=10)
        
    def next_question(self):
        self.answered = False
        self.current_q = random.choice(questions)
        self.question_label.config(text=self.current_q["question"])
        self.hint_label.config(text=f"提示：{self.current_q['hint']}")
        self.answer_entry.delete(0, tk.END)
        self.submit_btn.config(state="normal")
        self.show_btn.config(state="normal")
        self.start_btn.config(text="下一题")
        
    def check_answer(self):
        if self.answered:
            return
        user_ans = self.answer_entry.get().strip()
        correct_ans = self.current_q["answer"]
        
        if user_ans == correct_ans:
            messagebox.showinfo("结果", "✅ 回答正确！")
            self.score += 1
        else:
            messagebox.showinfo("结果", f"❌ 回答错误！正确答案是：{correct_ans}")
        
        self.answered = True
        self.score_label.config(text=f"当前得分：{self.score}/{self.total}")
        self.submit_btn.config(state="disabled")
        
    def show_answer(self):
        if not self.answered:
            messagebox.showinfo("答案", f"正确答案是：{self.current_q['answer']}")
            self.answered = True
            self.submit_btn.config(state="disabled")

if __name__ == "__main__":
    root = tk.Tk()
    app = FormulaApp(root)
    root.mainloop()