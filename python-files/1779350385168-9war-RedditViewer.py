import requests
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog
import time

def simple_translate(text):
    if not text.strip():
        return ""
    try:
        url = f"https://api.mymemory.translated.net/get?q={requests.utils.quote(text)}&langpair=en|zh-CN"
        res = requests.get(url, timeout=8)
        return res.json()["responseData"]["translatedText"]
    except:
        return text

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36"
}

class RedditViewerPro:
    def __init__(self, root):
        self.root = root
        self.root.title("Reddit合规查看器｜独立exe版")
        self.root.geometry("980x740")
        self.root.resizable(True, True)
        self.dark_mode = False

        # 快捷板块
        frame_short = ttk.Frame(root)
        frame_short.pack(pady=4)
        ttk.Button(frame_short, text="AskReddit", command=lambda:self.set_sub("AskReddit")).grid(row=0,column=0,padx=3)
        ttk.Button(frame_short, text="worldnews", command=lambda:self.set_sub("worldnews")).grid(row=0,column=1,padx=3)
        ttk.Button(frame_short, text="china", command=lambda:self.set_sub("china")).grid(row=0,column=2,padx=3)
        ttk.Button(frame_short, text="funny", command=lambda:self.set_sub("funny")).grid(row=0,column=3,padx=3)
        ttk.Button(frame_short, text="切换暗黑", command=self.toggle_dark).grid(row=0,column=4,padx=8)

        # 输入
        ttk.Label(root, text="子板块 r/：").pack()
        self.sub_entry = ttk.Entry(root, width=72)
        self.sub_entry.pack()
        self.sub_entry.insert(0, "AskReddit")

        ttk.Label(root, text="帖子ID（留空=看列表）：").pack()
        self.post_entry = ttk.Entry(root, width=72)
        self.post_entry.pack()

        frame_row = ttk.Frame(root)
        frame_row.pack(pady=3)
        ttk.Label(frame_row, text="读取条数：").grid(row=0,column=0)
        self.limit_entry = ttk.Entry(frame_row, width=8)
        self.limit_entry.grid(row=0,column=1,padx=5)
        self.limit_entry.insert(0, "6")

        # 按钮
        frame_btn = ttk.Frame(root)
        frame_btn.pack(pady=6)
        ttk.Button(frame_btn, text="🔍 获取+翻译", command=self.fetch).grid(row=0,column=0,padx=8)
        ttk.Button(frame_btn, text="💾 保存TXT", command=self.save_txt).grid(row=0,column=1,padx=8)
        ttk.Button(frame_btn, text="🗑 清空", command=self.clear).grid(row=0,column=2,padx=8)

        # 文本框
        self.text = scrolledtext.ScrolledText(
            root, wrap=tk.WORD, font=("微软雅黑", 10),
            bg="#f9f9f9", padx=8, pady=8
        )
        self.text.pack(expand=True, fill=tk.BOTH, padx=10, pady=5)

    def toggle_dark(self):
        self.dark_mode = not self.dark_mode
        if self.dark_mode:
            self.text.config(bg="#222222", fg="#eeeeee")
        else:
            self.text.config(bg="#f9f9f9", fg="#000000")

    def set_sub(self, name):
        self.sub_entry.delete(0, tk.END)
        self.sub_entry.insert(0, name)

    def fetch(self):
        self.text.delete(1.0, tk.END)
        sub = self.sub_entry.get().strip()
        pid = self.post_entry.get().strip()
        try:
            limit = int(self.limit_entry.get())
        except:
            limit = 6

        try:
            if pid:
                url = f"https://www.reddit.com/r/{sub}/comments/{pid}.json"
            else:
                url = f"https://www.reddit.com/r/{sub}.json?limit={limit}"

            resp = requests.get(url, headers=HEADERS, timeout=12)
            data = resp.json()

            if pid:
                post = data[0]["data"]["children"][0]["data"]
                title_cn = simple_translate(post["title"])
                body_cn = simple_translate(post.get("selftext", ""))
                score = post.get("score", 0)
                created = time.strftime("%Y-%m-%d", time.localtime(post["created_utc"]))
                img = post.get("url_overridden_by_dest", "")

                self.text.insert(tk.END, f"【标题】{title_cn}\n")
                self.text.insert(tk.END, f"👍点赞：{score} | 📅发布：{created}\n")
                if img:
                    self.text.insert(tk.END, f"🖼图片链接：{img}\n")
                self.text.insert(tk.END, f"\n【正文】\n{body_cn}\n\n===== 全部评论 =====\n\n")

                for c in data[1]["data"]["children"]:
                    if c["kind"] == "t1":
                        cm = simple_translate(c["data"]["body"])
                        self.text.insert(tk.END, f"- {cm}\n\n")
            else:
                for item in data["data"]["children"]:
                    p = item["data"]
                    t = simple_translate(p["title"])
                    score = p.get("score", 0)
                    link = f"https://reddit.com{p['permalink']}"
                    img = p.get("url_overridden_by_dest", "")
                    self.text.insert(tk.END, f"● {t}\n👍{score} | 🔗{link}\n")
                    if img:
                        self.text.insert(tk.END, f"🖼{img}\n")
                    self.text.insert(tk.END, "\n")
        except Exception as e:
            self.text.insert(tk.END, f"❌ 获取失败：{str(e)}")

    def save_txt(self):
        content = self.text.get(1.0, tk.END)
        path = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("TXT文件","*.txt")])
        if path:
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)

    def clear(self):
        self.text.delete(1.0, tk.END)

if __name__ == "__main__":
    root = tk.Tk()
    RedditViewerPro(root)
    root.mainloop()