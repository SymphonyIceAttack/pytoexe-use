import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import ctypes
import sys
from difflib import SequenceMatcher

# --- 1. 隐藏黑框框 (自动) ---
def hide_console():
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
hide_console()

# --- 2. 核心智能算法区 ---

# 常用日美名称别名库 (帮你解决 Rockman 这种问题)
ALIAS_DB = {
    'rockman': 'megaman',
    'mega man': 'rockman',
    'bio hazard': 'resident evil',
    'pocket monsters': 'pokemon',
    'koukaku kidoutai': 'ghost in the shell',
    'samurai spirits': 'samurai shodown',
    'bare knuckle': 'streets of rage',
    'jet set radio': 'jet grind radio'
}

def roman_to_int(name):
    """把文件名里的罗马数字 I, II, III 换成 1, 2, 3，方便匹配"""
    # 简单处理常见的 1-5 即可，太复杂的反而容易误伤
    name = re.sub(r'\bI\b', '1', name)
    name = re.sub(r'\bII\b', '2', name)
    name = re.sub(r'\bIII\b', '3', name)
    name = re.sub(r'\bIV\b', '4', name)
    name = re.sub(r'\bV\b', '5', name)
    return name

def clean_text(text):
    """超级清洗：去符号、去括号、转小写、处理别名"""
    text = text.lower()
    # 去掉方括号 [] 和 圆括号 () 的内容
    text = re.sub(r'\[.*?\]', '', text) 
    text = re.sub(r'\(.*?\)', '', text)
    # 把 Snake_s 变成 snakes (去掉符号连接)
    text = text.replace("'", "").replace("_", " ").replace("-", " ")
    # 处理罗马数字
    text = roman_to_int(text)
    # 替换常用别名
    for k, v in ALIAS_DB.items():
        if k in text:
            text = text.replace(k, v)
    # 只保留字母和数字
    text = re.sub(r'[^a-z0-9\s]', '', text)
    # 去掉多余空格
    return " ".join(text.split())

def extract_numbers(text):
    """提取字符串里所有的数字，用于硬核校验"""
    # Adventure Island 3 -> {'3'}
    # 2010 Street Fighter -> {'2010'}
    return set(re.findall(r'\d+', text))

def is_match(img_name, db_name):
    """
    判断两个名字是否是同一个游戏
    1. 提取数字，必须完全一致 (防止 Adventure Island 2 匹配到 3)
    2. 计算文字相似度 (模糊匹配)
    """
    clean_img = clean_text(img_name)
    clean_db = clean_text(db_name)
    
    # 1. 数字硬核检查
    nums_img = extract_numbers(clean_img)
    nums_db = extract_numbers(clean_db)
    
    # 如果两边都有数字，且数字集合不相等，直接判死刑
    # 例如: "Mario 2" vs "Mario 3" -> 不匹配
    if nums_img and nums_db and nums_img != nums_db:
        return False, 0

    # 2. 模糊相似度检查 (0.0 - 1.0)
    # 使用 difflib 算法，算出两个字符串有多像
    similarity = SequenceMatcher(None, clean_img, clean_db).ratio()
    
    # 阈值设定：0.85 (85%相似就算匹配)
    # 比如 "snakes revenge" 和 "snake revenge" 相似度很高
    if similarity > 0.85:
        return True, similarity
    
    # 3. 补救措施：如果包含关系非常明显
    # 比如 db="Street Fighter 2010" img="2010 Street Fighter" (顺序不同)
    set_img = set(clean_img.split())
    set_db = set(clean_db.split())
    if set_img == set_db:
        return True, 1.0
        
    return False, similarity

# --- 3. 界面逻辑 ---

class UltraRenamer:
    def __init__(self, root):
        self.root = root
        self.root.title("LaunchBox 终极图片汉化工具")
        self.root.geometry("650x500")
        self.root.configure(bg="#f0f0f0")

        # 样式配置
        label_font = ("微软雅黑", 10)
        entry_bg = "white"

        # 顶部说明
        tk.Label(root, text="LaunchBox 终极图片汉化工具", font=("微软雅黑", 16, "bold"), bg="#f0f0f0").pack(pady=10)

        # 步骤 1
        frame1 = tk.Frame(root, bg="#f0f0f0")
        frame1.pack(fill="x", padx=20, pady=5)
        tk.Label(frame1, text="1. 选择 List.txt (资料表):", bg="#f0f0f0", font=label_font).pack(anchor="w")
        self.entry_list = tk.Entry(frame1, bg=entry_bg)
        self.entry_list.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame1, text="浏览", command=self.sel_list).pack(side="right")

        # 步骤 2
        frame2 = tk.Frame(root, bg="#f0f0f0")
        frame2.pack(fill="x", padx=20, pady=5)
        tk.Label(frame2, text="2. 选择 Images 根目录:", bg="#f0f0f0", font=label_font).pack(anchor="w")
        self.entry_img = tk.Entry(frame2, bg=entry_bg)
        self.entry_img.pack(side="left", fill="x", expand=True, padx=(0, 5))
        tk.Button(frame2, text="浏览", command=self.sel_img).pack(side="right")

        # 大按钮
        self.btn_run = tk.Button(root, text="开始处理", bg="#4CAF50", fg="white", 
                                 font=("微软雅黑", 14, "bold"), height=2, borderwidth=0,
                                 command=self.start_thread)
        self.btn_run.pack(fill="x", padx=40, pady=20)

        # 日志
        tk.Label(root, text="处理日志:", bg="#f0f0f0").pack(anchor="w", padx=20)
        self.log_box = scrolledtext.ScrolledText(root, height=12, state='disabled', font=("Consolas", 9))
        self.log_box.pack(fill="both", expand=True, padx=20, pady=(0, 20))

    def log(self, text):
        self.log_box.config(state='normal')
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)
        self.log_box.config(state='disabled')

    def sel_list(self):
        path = filedialog.askopenfilename(filetypes=[("Text", "*.txt")])
        if path: self.entry_list.delete(0, tk.END); self.entry_list.insert(0, path)

    def sel_img(self):
        path = filedialog.askdirectory()
        if path: self.entry_img.delete(0, tk.END); self.entry_img.insert(0, path)

    def start_thread(self):
        threading.Thread(target=self.process).start()

    def process(self):
        list_file = self.entry_list.get()
        img_root = self.entry_img.get()
        
        if not os.path.exists(list_file) or not os.path.exists(img_root):
            messagebox.showerror("错误", "路径不存在！")
            return

        self.btn_run.config(text="正在处理...", state="disabled", bg="#888")
        self.log("正在加载数据库...")
        
        # 解析 list.txt
        db_entries = []
        try:
            with open(list_file, 'r', encoding='utf-8') as f: content = f.read()
        except:
            with open(list_file, 'r', encoding='gbk') as f: content = f.read()
            
        chunks = content.split('game:')
        for chunk in chunks:
            if not chunk.strip(): continue
            lines = chunk.strip().split('\n')
            cn_name = lines[0].strip()
            
            rom_file = ""
            for l in lines:
                if l.startswith('file:'):
                    rom_file = l.replace('file:', '').strip()
                    break
            
            if rom_file:
                # 去掉后缀 .nes
                clean_rom = os.path.splitext(rom_file)[0]
                db_entries.append({'cn': cn_name, 'rom': clean_rom})

        self.log(f"数据库加载完毕: {len(db_entries)} 个条目")
        self.log("开始扫描图片 (模糊匹配模式)...")
        
        success_count = 0
        
        # 遍历图片
        for root, dirs, files in os.walk(img_root):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.ico')):
                    old_path = os.path.join(root, file)
                    img_name_no_ext = os.path.splitext(file)[0]
                    ext = os.path.splitext(file)[1]
                    
                    # 忽略已经是中文的
                    if any('\u4e00' <= char <= '\u9fff' for char in img_name_no_ext):
                        continue

                    best_match_cn = None
                    highest_score = 0
                    
                    # --- 寻找最佳匹配 ---
                    for entry in db_entries:
                        match, score = is_match(img_name_no_ext, entry['rom'])
                        if match and score > highest_score:
                            highest_score = score
                            best_match_cn = entry['cn']
                            # 如果是满分匹配，直接停止寻找，节省时间
                            if score == 1.0: 
                                break
                    
                    if best_match_cn:
                        # 构造新名字，保留原图的后缀 (-01)
                        suffix = ""
                        s_match = re.search(r'[-_]\d+$', img_name_no_ext)
                        if s_match: suffix = s_match.group(0)
                        
                        new_name = f"{best_match_cn}{suffix}{ext}"
                        new_path = os.path.join(root, new_name)
                        
                        try:
                            if not os.path.exists(new_path):
                                os.rename(old_path, new_path)
                                self.log(f"[√] {file} -> {new_name}")
                                success_count += 1
                        except:
                            self.log(f"[X] 无法重命名: {file}")
                    else:
                        # 没找到匹配，可以取消注释下面这行查看详情
                        # self.log(f"[?] 未匹配: {file}")
                        pass

        self.log("-" * 30)
        self.log(f"全部完成！共处理: {success_count} 张。")
        self.btn_run.config(text="开始处理", state="normal", bg="#4CAF50")
        messagebox.showinfo("成功", f"搞定！共成功改名 {success_count} 张。")

if __name__ == "__main__":
    root = tk.Tk()
    app = UltraRenamer(root)
    root.mainloop()