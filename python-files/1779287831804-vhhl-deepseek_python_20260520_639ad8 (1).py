import tkinter as tk
from tkinter import scrolledtext, messagebox
import re
import random
from collections import Counter

# 内置词库
BUILTIN_VOCAB = {
    "technology": "技术", "learn": "学习", "language": "语言", "study": "学习",
    "important": "重要的", "different": "不同的", "people": "人们", "time": "时间",
    "good": "好的", "new": "新的", "way": "方式", "make": "使/做"
}

class App:
    def __init__(self, root):
        self.root = root
        self.root.title("新概念英语·自由学")
        self.root.geometry("900x700")
        
        tk.Label(root, text="输入英文文章：", font=("Arial", 12)).pack(pady=5)
        self.text_input = scrolledtext.ScrolledText(root, height=10)
        self.text_input.pack(padx=20, fill=tk.X)
        
        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="开始分析", command=self.analyze, bg="green", fg="white").pack()
        
        tk.Label(root, text="分析结果：", font=("Arial", 12)).pack(pady=5)
        self.text_output = scrolledtext.ScrolledText(root, height=18)
        self.text_output.pack(padx=20, fill=tk.BOTH, expand=True)
    
    def analyze(self):
        article = self.text_input.get(1.0, tk.END).strip()
        if not article:
            messagebox.showwarning("提示", "请输入文章")
            return
        
        words = re.findall(r'\b[a-zA-Z]+\b', article.lower())
        word_count = len(words)
        
        result = f"【分析报告】\n单词数：{word_count}\n句子数：{len(re.findall(r'[.!?]+', article))}\n\n【重点词汇】\n"
        
        from collections import Counter
        freq = Counter(words)
        for w, c in freq.most_common(10):
            if w not in ['the','and','to','of','a','in','for','on','with','by']:
                meaning = BUILTIN_VOCAB.get(w, "未知")
                result += f"• {w} ({c}次): {meaning}\n"
        
        result += "\n【学习建议】\n• 把上面不认识的单词记下来\n• 尝试朗读文章3遍"
        
        self.text_output.delete(1.0, tk.END)
        self.text_output.insert(1.0, result)

if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()