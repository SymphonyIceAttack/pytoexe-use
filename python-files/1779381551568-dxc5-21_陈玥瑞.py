Python 3.12.5 (tags/v3.12.5:ff3bc82, Aug  6 2024, 20:45:27) [MSC v.1940 64 bit (AMD64)] on win32
Type "help", "copyright", "credits" or "license()" for more information.
请使用 Python 编写一个本地单词学习程序，要求如下：
import tkinter as tk
from tkinter import messagebox, ttk, simpledialog
import json
import random
import datetime
import os
import hashlib

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
WORDS_FILE = "words.json"
QUIZ_HISTORY_FILE = os.path.join(DATA_DIR, "quiz_history.json")

LEVELS = ["熟记", "勉强", "模糊", "没印象"]
LEVEL_WEIGHTS = [1, 3, 6, 10]

DEFAULT_WORDS = [
    {"word": "apple", "meaning": "苹果"},
    {"word": "banana", "meaning": "香蕉"},
    {"word": "book", "meaning": "书"},
    {"word": "computer", "meaning": "电脑"},
    {"word": "dog", "meaning": "狗"},
    {"word": "elephant", "meaning": "大象"},
    {"word": "flower", "meaning": "花"},
    {"word": "garden", "meaning": "花园"},
    {"word": "happy", "meaning": "快乐的"},
    {"word": "important", "meaning": "重要的"},
    {"word": "job", "meaning": "工作"},
    {"word": "knowledge", "meaning": "知识"},
    {"word": "love", "meaning": "爱"},
    {"word": "music", "meaning": "音乐"},
    {"word": "notebook", "meaning": "笔记本"},
    {"word": "orange", "meaning": "橙子"},
    {"word": "people", "meaning": "人们"},
    {"word": "question", "meaning": "问题"},
    {"word": "rainbow", "meaning": "彩虹"},
    {"word": "sun", "meaning": "太阳"},
    {"word": "teacher", "meaning": "老师"},
    {"word": "university", "meaning": "大学"},
    {"word": "vegetable", "meaning": "蔬菜"},
    {"word": "water", "meaning": "水"},
    {"word": "yellow", "meaning": "黄色"},
    {"word": "zoo", "meaning": "动物园"},
    {"word": "beautiful", "meaning": "美丽的"},
    {"word": "challenge", "meaning": "挑战"},
    {"word": "different", "meaning": "不同的"},
    {"word": "excellent", "meaning": "优秀的"},
    {"word": "fantastic", "meaning": "极好的"},
    {"word": "government", "meaning": "政府"},
    {"word": "hospital", "meaning": "医院"},
    {"word": "imagine", "meaning": "想象"},
    {"word": "journey", "meaning": "旅程"},
    {"word": "kitchen", "meaning": "厨房"},
    {"word": "language", "meaning": "语言"},
    {"word": "mountain", "meaning": "山"},
    {"word": "natural", "meaning": "自然的"}
]

def init_files():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)
    
    if not os.path.exists(WORDS_FILE):
        with open(WORDS_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_WORDS, f, ensure_ascii=False, indent=2)
    
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)
    
    if not os.path.exists(QUIZ_HISTORY_FILE):
        with open(QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False)

def load_users():
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def load_words():
    try:
        with open(WORDS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return DEFAULT_WORDS

def load_quiz_history():
    try:
        with open(QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {}

def save_quiz_history(history):
    with open(QUIZ_HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class LoginWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("单词学习 - 登录")
        self.geometry("300x200")
        self.resizable(False, False)
        
        self.username_var = tk.StringVar()
        self.password_var = tk.StringVar()
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - 300) // 2
        y = (screen_height - 200) // 2
        self.geometry(f"300x200+{x}+{y}")
    
    def create_widgets(self):
        ttk.Label(self, text="用户名:").grid(row=0, column=0, padx=10, pady=10, sticky="e")
        ttk.Entry(self, textvariable=self.username_var, width=20).grid(row=0, column=1, padx=10, pady=10)
        
        ttk.Label(self, text="密码:").grid(row=1, column=0, padx=10, pady=10, sticky="e")
        ttk.Entry(self, textvariable=self.password_var, show="*", width=20).grid(row=1, column=1, padx=10, pady=10)
        
        ttk.Button(self, text="登录", command=self.login).grid(row=2, column=0, padx=10, pady=10)
        ttk.Button(self, text="注册", command=self.register).grid(row=2, column=1, padx=10, pady=10)
    
    def login(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码")
            return
        
        users = load_users()
        if username not in users:
            messagebox.showerror("错误", "用户名不存在")
            return
        
        if users[username]["password"] != hash_password(password):
            messagebox.showerror("错误", "密码错误")
            return
        
        self.parent.current_user = username
        self.parent.user_data = users[username]
        self.destroy()
        self.parent.show_main_window()
    
    def register(self):
        username = self.username_var.get().strip()
        password = self.password_var.get()
        
        if not username or not password:
            messagebox.showwarning("警告", "请输入用户名和密码")
            return
        
        if len(username) < 3:
            messagebox.showwarning("警告", "用户名至少需要3个字符")
            return
        
        if len(password) < 6:
            messagebox.showwarning("警告", "密码至少需要6个字符")
            return
        
        users = load_users()
        if username in users:
            messagebox.showerror("错误", "用户名已存在")
            return
        
        users[username] = {
            "password": hash_password(password),
            "daily_plan": 10,
            "word_progress": {},
            "last_date": ""
        }
        save_users(users)
        messagebox.showinfo("成功", "注册成功，请登录")

class BrowseFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_page = 0
        self.words_per_page = 5
        self.create_widgets()
    
    def create_widgets(self):
        self.words_listbox = tk.Listbox(self, width=60, height=15)
        self.words_listbox.pack(pady=10)
        
        self.page_label = tk.Label(self, text="第 1 页")
        self.page_label.pack(pady=5)
        
        button_frame = tk.Frame(self)
        button_frame.pack(pady=5)
        
        self.prev_btn = ttk.Button(button_frame, text="上一页", command=self.prev_page)
        self.prev_btn.pack(side="left", padx=5)
        
        self.next_btn = ttk.Button(button_frame, text="下一页", command=self.next_page)
        self.next_btn.pack(side="left", padx=5)
    
    def update_words(self):
        self.words_listbox.delete(0, tk.END)
        all_words = self.parent.get_all_words()
        total_pages = (len(all_words) + self.words_per_page - 1) // self.words_per_page
        
        start = self.current_page * self.words_per_page
        end = start + self.words_per_page
        page_words = all_words[start:end]
        
        for w in page_words:
            self.words_listbox.insert(tk.END, f"{w['word']} - {w['meaning']}")
        
        self.page_label.config(text=f"第 {self.current_page + 1} / {total_pages} 页")
        self.prev_btn.config(state=tk.DISABLED if self.current_page == 0 else tk.NORMAL)
        self.next_btn.config(state=tk.DISABLED if self.current_page >= total_pages - 1 else tk.NORMAL)
    
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.update_words()
    
    def next_page(self):
        all_words = self.parent.get_all_words()
        total_pages = (len(all_words) + self.words_per_page - 1) // self.words_per_page
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.update_words()
    
    def refresh(self):
        self.current_page = 0
        self.update_words()

class ReciteFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.current_word = None
        self.showing_answer = False
        self.show_chinese = True
        self.create_widgets()
    
    def create_widgets(self):
        self.word_label = tk.Label(self, text="", font=("Arial", 24), pady=20)
        self.word_label.pack()
        
        self.answer_label = tk.Label(self, text="", font=("Arial", 16), fg="blue", pady=10)
        self.answer_label.pack()
        
        self.show_answer_btn = ttk.Button(self, text="显示答案", command=self.show_answer)
        self.show_answer_btn.pack(pady=10)
        
        level_frame = tk.Frame(self)
        level_frame.pack(pady=10)
        
        self.level_buttons = []
        for i, level in enumerate(LEVELS):
            btn = ttk.Button(level_frame, text=level, command=lambda l=i: self.update_level(l))
            btn.pack(side="left", padx=5)
            self.level_buttons.append(btn)
        
        self.next_btn = ttk.Button(self, text="下一个单词", command=self.next_word)
        self.next_btn.pack(pady=10)
    
    def next_word(self):
        self.showing_answer = False
        self.answer_label.config(text="")
        self.show_answer_btn.config(state=tk.NORMAL)
        
        today_words = self.parent.get_today_words()
        if not today_words:
            messagebox.showinfo("提示", "今日没有需要背诵的单词")
            return
        
        weights = []
        for word in today_words:
            level = self.parent.user_data["word_progress"].get(word["word"], 3)
            weights.append(LEVEL_WEIGHTS[level])
        
        self.current_word = random.choices(today_words, weights=weights)[0]
        self.show_chinese = random.choice([True, False])
        
        if self.show_chinese:
            self.word_label.config(text=f"请回忆英文单词:\n{self.current_word['meaning']}")
        else:
            self.word_label.config(text=f"请回忆中文释义:\n{self.current_word['word']}")
    
    def show_answer(self):
        if self.current_word:
            self.showing_answer = True
            if self.show_chinese:
                self.answer_label.config(text=f"答案: {self.current_word['word']}")
            else:
                self.answer_label.config(text=f"答案: {self.current_word['meaning']}")
            self.show_answer_btn.config(state=tk.DISABLED)
    
    def update_level(self, level):
        if not self.current_word:
            return
        
        if not self.showing_answer:
            self.show_answer()
        
        word = self.current_word["word"]
        self.parent.user_data["word_progress"][word] = level
        
        users = load_users()
        users[self.parent.current_user] = self.parent.user_data
        save_users(users)
        
        messagebox.showinfo("提示", f"已记录: {word} - {LEVELS[level]}")
        self.next_word()
    
    def refresh(self):
        self.next_word()

class QuizFrame(tk.Frame):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.quiz_words = []
        self.current_index = 0
        self.correct_count = 0
        self.create_widgets()
    
    def create_widgets(self):
        self.start_btn = ttk.Button(self, text="开始测验", command=self.start_quiz)
        self.start_btn.pack(pady=20)
        
        self.word_label = tk.Label(self, text="", font=("Arial", 20), pady=20)
        self.word_label.pack()
        
        self.answer_entry = ttk.Entry(self, width=30, font=("Arial", 14))
        self.answer_entry.pack(pady=10)
        self.answer_entry.bind("<Return>", lambda e: self.check_answer())
        
        self.submit_btn = ttk.Button(self, text="提交答案", command=self.check_answer)
        self.submit_btn.pack(pady=10)
        
        self.result_label = tk.Label(self, text="", font=("Arial", 16), pady=10)
        self.result_label.pack()
        
        self.history_btn = ttk.Button(self, text="查看历史记录", command=self.show_history)
        self.history_btn.pack(pady=10)
        
        self.reset_widgets()
    
    def reset_widgets(self):
        self.word_label.config(text="")
        self.answer_entry.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
        self.result_label.config(text="")
    
    def start_quiz(self):
        today_words = self.parent.get_today_words()
        if not today_words:
            messagebox.showinfo("提示", "今日没有需要背诵的单词")
            return
        
        max_n = len(today_words)
        n = simpledialog.askinteger("输入", f"请输入测验单词数量（最多{max_n}个）:", minvalue=1, maxvalue=max_n)
        
        if not n:
            return
        
        self.quiz_words = random.sample(today_words, n)
        self.current_index = 0
        self.correct_count = 0
        
        self.start_btn.config(state=tk.DISABLED)
        self.answer_entry.config(state=tk.NORMAL)
        self.submit_btn.config(state=tk.NORMAL)
        self.result_label.config(text="")
        
        self.show_current_word()
    
    def show_current_word(self):
        if self.current_index < len(self.quiz_words):
            word = self.quiz_words[self.current_index]
            self.word_label.config(text=f"第 {self.current_index + 1} / {len(self.quiz_words)} 题\n中文释义: {word['meaning']}")
            self.answer_entry.delete(0, tk.END)
            self.answer_entry.focus()
        else:
            self.finish_quiz()
    
    def check_answer(self):
        user_answer = self.answer_entry.get().strip().lower()
        correct_word = self.quiz_words[self.current_index]["word"].lower()
        
        if user_answer == correct_word:
            self.correct_count += 1
            messagebox.showinfo("正确", "回答正确！")
        else:
            messagebox.showinfo("错误", f"回答错误！正确答案是: {self.quiz_words[self.current_index]['word']}")
        
        self.current_index += 1
        self.show_current_word()
    
    def finish_quiz(self):
        total = len(self.quiz_words)
        correct = self.correct_count
        percentage = (correct / total) * 100
        
        self.result_label.config(text=f"测验完成！\n正确: {correct} / {total} ({percentage:.1f}%)")
        
        history = load_quiz_history()
        if self.parent.current_user not in history:
            history[self.parent.current_user] = []
        
        history[self.parent.current_user].append({
            "date": datetime.date.today().isoformat(),
            "total": total,
            "correct": correct
        })
        save_quiz_history(history)
        
        self.start_btn.config(state=tk.NORMAL)
        self.answer_entry.config(state=tk.DISABLED)
        self.submit_btn.config(state=tk.DISABLED)
    
    def show_history(self):
        history = load_quiz_history()
        user_history = history.get(self.parent.current_user, [])
        
        if not user_history:
            messagebox.showinfo("提示", "暂无测验记录")
            return
        
        history_text = "测验历史记录:\n\n"
        for record in user_history:
            percentage = (record["correct"] / record["total"]) * 100
            history_text += f"{record['date']}: {record['correct']}/{record['total']} ({percentage:.1f}%)\n"
        
        messagebox.showinfo("测验历史", history_text)
    
    def refresh(self):
        self.reset_widgets()

class MainWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("单词学习程序")
        self.geometry("500x400")
        
        self.current_user = None
        self.user_data = None
        
        self.frames = {}
        self.create_menu()
        self.create_frames()
        
        self.login_window = LoginWindow(self)
        self.login_window.grab_set()
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def create_menu(self):
        menubar = tk.Menu(self)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="设置每日计划", command=self.set_daily_plan)
        file_menu.add_separator()
        file_menu.add_command(label="退出登录", command=self.logout)
        file_menu.add_command(label="退出程序", command=self.on_closing)
        menubar.add_cascade(label="文件", menu=file_menu)
        
        view_menu = tk.Menu(menubar, tearoff=0)
        view_menu.add_command(label="浏览单词", command=lambda: self.show_frame("browse"))
        view_menu.add_command(label="背诵单词", command=lambda: self.show_frame("recite"))
        view_menu.add_command(label="单词测验", command=lambda: self.show_frame("quiz"))
        menubar.add_cascade(label="视图", menu=view_menu)
        
        self.config(menu=menubar)
    
    def create_frames(self):
        self.browse_frame = BrowseFrame(self)
        self.recite_frame = ReciteFrame(self)
        self.quiz_frame = QuizFrame(self)
        
        self.frames["browse"] = self.browse_frame
        self.frames["recite"] = self.recite_frame
        self.frames["quiz"] = self.quiz_frame
        
        for frame in self.frames.values():
            frame.grid(row=0, column=0, sticky="nsew")
        
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
    
    def show_main_window(self):
        self.title(f"单词学习程序 - {self.current_user}")
        self.show_frame("browse")
    
    def show_frame(self, frame_name):
        frame = self.frames.get(frame_name)
        if frame:
            frame.tkraise()
            frame.refresh()
    
    def get_all_words(self):
        all_words = []
        today_words = self.get_today_words()
        today_word_set = {w["word"] for w in today_words}
        
        all_word_list = load_words()
        for w in all_word_list:
            if w["word"] in today_word_set:
                all_words.append({"word": w["word"], "meaning": w["meaning"], "tag": "今日"})
            elif w["word"] in self.user_data["word_progress"]:
                all_words.append({"word": w["word"], "meaning": w["meaning"], "tag": "已学"})
        
        return all_words
    
    def get_today_words(self):
        today = datetime.date.today().isoformat()
        
        if self.user_data.get("last_date") == today and "today_words" in self.user_data:
            word_list = load_words()
            word_map = {w["word"]: w for w in word_list}
            return [word_map[word] for word in self.user_data["today_words"] if word in word_map]
        
        return self.generate_today_words()
    
    def generate_today_words(self):
        word_list = load_words()
        daily_plan = self.user_data.get("daily_plan", 10)
        
        known_words = set(self.user_data["word_progress"].keys())
        unknown_words = [w for w in word_list if w["word"] not in known_words]
        need_review = [w for w in word_list if w["word"] in known_words and self.user_data["word_progress"][w["word"]] > 0]
        mastered_words = [w for w in word_list if w["word"] in known_words and self.user_data["word_progress"][w["word"]] == 0]
        
        today_words = []
        
        today_words.extend(unknown_words[:daily_plan])
        remaining = daily_plan - len(today_words)
        
        if remaining > 0 and need_review:
            weights = [LEVEL_WEIGHTS[self.user_data["word_progress"][w["word"]]] for w in need_review]
            sampled = random.choices(need_review, weights=weights, k=min(remaining, len(need_review)))
            today_words.extend(sampled)
            remaining -= len(sampled)
        
        if remaining > 0 and mastered_words:
...             sampled = random.sample(mastered_words, min(remaining, len(mastered_words)))
...             today_words.extend(sampled)
...         
...         self.user_data["today_words"] = [w["word"] for w in today_words]
...         self.user_data["last_date"] = datetime.date.today().isoformat()
...         
...         users = load_users()
...         users[self.current_user] = self.user_data
...         save_users(users)
...         
...         return today_words
...     
...     def set_daily_plan(self):
...         current_plan = self.user_data.get("daily_plan", 10)
...         new_plan = simpledialog.askinteger("设置每日计划", f"当前每日计划: {current_plan} 个单词\n请输入新的每日计划数量:", minvalue=1, maxvalue=50)
...         
...         if new_plan:
...             self.user_data["daily_plan"] = new_plan
...             users = load_users()
...             users[self.current_user] = self.user_data
...             save_users(users)
...             messagebox.showinfo("成功", f"每日计划已设置为 {new_plan} 个单词")
...     
...     def logout(self):
...         self.current_user = None
...         self.user_data = None
...         
...         self.login_window = LoginWindow(self)
...         self.login_window.grab_set()
...     
...     def on_closing(self):
...         if messagebox.askokcancel("退出", "确定要退出程序吗？"):
...             self.destroy()
... 
... if __name__ == "__main__":
...     init_files()
...     app = MainWindow()
