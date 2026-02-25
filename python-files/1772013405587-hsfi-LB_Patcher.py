import xml.etree.ElementTree as ET
import os
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
import threading
import ctypes
import sys
import re  # 引入正则库用于模糊匹配

# --- 1. 自动隐藏黑框 ---
def hide_console():
    if sys.platform == 'win32':
        try:
            ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
        except:
            pass
hide_console()

# --- 2. 核心工具：强制缩进 ---
def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

# --- 3. 新增：智能简化文件名 (模糊匹配核心) ---
def simplify_name(filename):
    # 1. 去掉扩展名，转小写
    name = os.path.splitext(filename)[0].lower()
    # 2. 去掉所有括号内容 (USA), [CN], (v1.0) 等
    name = re.sub(r'\(.*?\)', '', name)
    name = re.sub(r'\[.*?\]', '', name)
    # 3. 去掉特殊符号和空格，只保留字母数字
    name = re.sub(r'[^a-z0-9]', '', name)
    return name

# --- 4. 界面与逻辑 ---
class XMLFinalFix:
    def __init__(self, root):
        self.root = root
        self.root.title("LaunchBox XML 汉化修复工具 (智能模糊匹配版)")
        self.root.geometry("700x600")
        
        tk.Label(root, text="LaunchBox XML 终极汉化工具", font=("微软雅黑", 16, "bold"), fg="#D32F2F").pack(pady=10)
        tk.Label(root, text="升级：支持忽略 (USA) 等后缀进行模糊匹配，解决PS2匹配率低的问题", font=("微软雅黑", 9), fg="#555").pack()
        
        # XML
        f1 = tk.Frame(root, pady=5); f1.pack(fill="x", padx=20)
        tk.Label(f1, text="1. 原版 XML (LaunchBox能正常读取的):", anchor="w").pack(fill="x")
        self.entry_xml = tk.Entry(f1); self.entry_xml.pack(side="left", fill="x", expand=True)
        tk.Button(f1, text="浏览", command=self.sel_xml).pack(side="right")

        # List
        f2 = tk.Frame(root, pady=5); f2.pack(fill="x", padx=20)
        tk.Label(f2, text="2. 中文资料 List.txt:", anchor="w").pack(fill="x")
        self.entry_list = tk.Entry(f2); self.entry_list.pack(side="left", fill="x", expand=True)
        tk.Button(f2, text="浏览", command=self.sel_list).pack(side="right")

        # 选项
        f_opts = tk.Frame(root); f_opts.pack(pady=5)
        self.var_notes = tk.BooleanVar(value=True)
        self.var_fuzzy = tk.BooleanVar(value=True)
        tk.Checkbutton(f_opts, text="更新简介 (Notes)", variable=self.var_notes).pack(side="left", padx=10)
        tk.Checkbutton(f_opts, text="启用模糊匹配 (忽略括号/版本号)", variable=self.var_fuzzy, fg="blue").pack(side="left", padx=10)

        self.btn_run = tk.Button(root, text="开始处理 (智能匹配)", bg="#0078D7", fg="white", 
                                 font=("微软雅黑", 12, "bold"), height=2, command=self.start_thread)
        self.btn_run.pack(fill="x", padx=40, pady=15)

        self.log_box = scrolledtext.ScrolledText(root, height=12)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=10)

    def log(self, text):
        self.log_box.insert(tk.END, text + "\n")
        self.log_box.see(tk.END)

    def sel_xml(self):
        p = filedialog.askopenfilename(filetypes=[("XML", "*.xml")])
        if p: self.entry_xml.delete(0, tk.END); self.entry_xml.insert(0, p)
    
    def sel_list(self):
        p = filedialog.askopenfilename(filetypes=[("TXT", "*.txt")])
        if p: self.entry_list.delete(0, tk.END); self.entry_list.insert(0, p)

    def start_thread(self):
        threading.Thread(target=self.run).start()

    def parse_list(self, list_path):
        smart_db = {} # 精确匹配库
        fuzzy_db = {} # 模糊匹配库
        
        try:
            with open(list_path, 'r', encoding='utf-8') as f: content = f.read()
        except:
            with open(list_path, 'r', encoding='gbk') as f: content = f.read()
        
        for chunk in content.split('game:'):
            if not chunk.strip(): continue
            lines = chunk.strip().split('\n')
            title = lines[0].strip()
            rom_file = ""
            desc = ""
            for l in lines:
                if l.startswith('file:'): rom_file = l.replace('file:', '').strip()
                elif l.startswith('description:'): desc = l.replace('description:', '').strip()
            
            if rom_file:
                # 1. 存入精确匹配库
                clean_exact = os.path.splitext(rom_file)[0].lower()
                data = {'title': title, 'notes': desc}
                smart_db[clean_exact] = data
                
                # 2. 存入模糊匹配库
                clean_fuzzy = simplify_name(rom_file)
                if clean_fuzzy:
                    fuzzy_db[clean_fuzzy] = data

        return smart_db, fuzzy_db

    def run(self):
        xml_path = self.entry_xml.get()
        list_path = self.entry_list.get()
        
        if not os.path.exists(xml_path) or not os.path.exists(list_path):
            messagebox.showerror("错误", "路径不存在")
            return

        self.btn_run.config(state="disabled", text="正在读取...")
        
        # 1. 提取头文件
        original_header = ""
        try:
            with open(xml_path, 'r', encoding='utf-8') as f:
                original_header = f.readline().strip()
            if not original_header.startswith("<?xml"):
                 original_header = '<?xml version="1.0" standalone="yes"?>'
            self.log(f"头文件: {original_header}")
        except:
            original_header = '<?xml version="1.0" standalone="yes"?>'

        # 2. 解析资料库
        self.log("正在解析 List.txt (构建索引)...")
        db_exact, db_fuzzy = self.parse_list(list_path)
        self.log(f"资料库加载完成。精确条目: {len(db_exact)}, 模糊条目: {len(db_fuzzy)}")

        # 3. 解析 XML
        try:
            tree = ET.parse(xml_path)
            root = tree.getroot()
        except Exception as e:
            messagebox.showerror("XML 损坏", f"错误: {e}")
            return

        # 4. 匹配和修改
        count = 0
        use_fuzzy = self.var_fuzzy.get()
        
        for game in root.findall('Game'):
            path_node = game.find('ApplicationPath')
            if path_node is None or path_node.text is None: continue
            
            rom_name = os.path.basename(path_node.text)
            rom_clean_exact = os.path.splitext(rom_name)[0].lower()
            
            matched_data = None
            
            # 第一轮：精确匹配
            if rom_clean_exact in db_exact:
                matched_data = db_exact[rom_clean_exact]
            # 第二轮：模糊匹配 (如果开启且第一轮没匹配上)
            elif use_fuzzy:
                rom_clean_fuzzy = simplify_name(rom_name)
                if rom_clean_fuzzy in db_fuzzy:
                    matched_data = db_fuzzy[rom_clean_fuzzy]
            
            if matched_data:
                # 修改标题
                title_node = game.find('Title')
                if title_node is None: title_node = ET.SubElement(game, 'Title')
                title_node.text = matched_data['title']
                
                # 修改简介
                if self.var_notes.get():
                    notes_node = game.find('Notes')
                    if notes_node is None: notes_node = ET.SubElement(game, 'Notes')
                    notes_node.text = matched_data['notes']
                
                count += 1
        
        self.log(f"已修改 {count} 个游戏信息。")

        # 5. 保存
        indent(root)
        save_path = xml_path.replace('.xml', '_CHINESE.xml')
        try:
            xml_str = ET.tostring(root, encoding='utf-8').decode('utf-8')
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(original_header + "\n")
                f.write(xml_str)
            
            self.log(f"保存成功: {save_path}")
            messagebox.showinfo("成功", f"修复完成！共匹配 {count} 个游戏。\n请用新文件替换原 XML。")
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
        
        self.btn_run.config(state="normal", text="开始处理 (智能匹配)")

if __name__ == "__main__":
    root = tk.Tk()
    app = XMLFinalFix(root)
    root.mainloop()