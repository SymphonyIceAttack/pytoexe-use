import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import TkinterDnD, DND_FILES
import pyperclip  # 用于复制到剪贴板
import re

def extract_filtered_chat_texts(json_file_path, filter_option, deduplicate):
    try:
        # 读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        messages = data.get('messages', [])
        chat_texts = []

        for message in messages:
            if message.get('type') == 'message':
                text = message.get('text', [])

                # 处理 text 的多种格式（字符串或列表）
                if isinstance(text, list):
                    text = ''.join([part['text'] if isinstance(part, dict) and 'text' in part else part for part in text])
                elif isinstance(text, str):
                    pass  # 保留原始文本

                # 将中文字符、：、#、空格、？、反引号、指定字符串替换成换行符
                replacements = {
                    'V_DataPanBot': '\nV_DataPanBot',
                    'P_DataPanBot': '\nP_DataPanBot',
                    'D_DataPanBot': '\nD_DataPanBot',
                    'v_FilesPan1Bot': '\nv_FilesPan1Bot',
                    'p_FilesPan1Bot': '\np_FilesPan1Bot',
                    'd_FilesPan1Bot': '\nd_FilesPan1Bot',
                    'vi_BAACAg': '\nvi_BAACAg',
                    'v_BAACAg': '\nv_BAACAg',
                    'p_AgACAg': '\np_AgACAg',
                    'd_BQACAg': '\nd_BQACAg',
                    'd_CgACAg': '\nd_CgACAg',
                    'pk_1': '\npk_1',
                    'pk_2': '\npk_2',
                    'vid+': '\nvid+\n',
                    'pic+': '\npic+\n',
                    'doc+': '\ndoc+\n',
                    '=_mda': '=_mda\n',
                    '=_grp': '=_grp\n',
                    '//': '//\n',
                    'newjmqbot_': '\nnewjmqbot_',  # 新增：添加新密文的替换规则
                }

                # 使用正则表达式替换
                text = re.sub(r'([^\x00-\x7F])|[：:#？` )]', '\n', text)
                for old, new in replacements.items():
                    text = text.replace(old, new)

                # 筛选关键词
                keywords = ['vi_BAACAg', 'v_BAACAg', 'p_AgACAg', 'd_BQACAg', 'd_CgACAg',
                            'v_FilesPan1Bot', 'p_FilesPan1Bot', 'd_FilesPan1Bot',
                            'V_DataPanBot', 'D_DataPanBot', 'P_DataPanBot',
                            'pk_', '=_mda', '=_grp', 'showfilesbot_',
                            'newjmqbot_']  # 新增：添加新密文到一级筛选关键词

                # 筛选包含特定关键字的消息（不区分大小写）
                if any(keyword.lower() in text.lower() for keyword in keywords):
                    chat_texts.append(text)  # 只保存文本内容

        # 进行二次筛选，按行进行筛选
        secondary_chat_texts = []
        secondary_keywords = []

        if filter_option == "所有密文":
            secondary_keywords = ['vi_BAACAg', 'v_BAACAg', 'p_AgACAg', 'd_BQACAg', 'd_CgACAg',
                                  'v_FilesPan1Bot', 'p_FilesPan1Bot', 'd_FilesPan1Bot',
                                  'V_DataPanBot', 'D_DataPanBot', 'P_DataPanBot',
                                  'pk_', '=_mda', '=_grp', 'showfilesbot_',
                                  'newjmqbot_']  # 新增：添加新密文到"所有密文"筛选选项
        elif filter_option == "FilesDriveBLGA与旧密文":
            secondary_keywords = ['vi_BAACAg', 'v_BAACAg', 'd_BQACAg', 'd_CgACAg', 'p_AgACAg', 'pk_', 'PK_']
        elif filter_option == "MediaBKbot":
            secondary_keywords = ['=_mda', '=_grp']
        elif filter_option == "showfilesbot":
            secondary_keywords = ['showfilesbot_']
        elif filter_option == "DataPanBot":
            secondary_keywords = ['V_DataPanBot', 'D_DataPanBot', 'P_DataPanBot']
        elif filter_option == "FilesPan1Bot":
            secondary_keywords = ['v_FilesPan1Bot', 'p_FilesPan1Bot', 'd_FilesPan1Bot']

        for text in chat_texts:
            lines = text.split('\n')  # 按行分割
            for line in lines:
                if '.mp4' in line:
                    continue
                if filter_option in ["FilesDriveBLGA与旧密文"]:
                    if any(line.startswith(keyword) for keyword in secondary_keywords):
                        secondary_chat_texts.append(line)  # 只保存符合条件且以关键词开头的行
                else:
                    if any((keyword.lower() in line.lower() if filter_option == "所有密文" or filter_option == "MediaBKbot" or filter_option == "showfilesbot" or filter_option == "DataPanBot" or filter_option == "FilesPan1Bot" else keyword in line) for keyword in secondary_keywords):
                        secondary_chat_texts.append(line)  # 保存符合条件的行

        # 去重
        if deduplicate:
            secondary_chat_texts = list(set(secondary_chat_texts))

        return '\n'.join(secondary_chat_texts)
    except Exception as e:
        messagebox.showerror("错误", f"处理文件时发生错误: {e}")
        return ""


def extract_filtered_chatjy_texts(json_file_path, deduplicate):
    try:
        # 读取 JSON 文件
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)

        messages = data.get('messages', [])
        chat_texts = []

        for message in messages:
            if message.get('type') == 'message':
                text = message.get('text', [])

                # 处理 text 的多种格式（字符串或列表）
                if isinstance(text, list):
                    text = ''.join([part['text'] if isinstance(part, dict) and 'text' in part else part for part in text])
                elif isinstance(text, str):
                    pass  # 保留原始文本

                # 将中文字符、：、#、空格、？、反引号、指定字符串替换成换行符
                replacements = {
                    'V_DataPanBot': '\nV_DataPanBot',
                    'P_DataPanBot': '\nP_DataPanBot',
                    'D_DataPanBot': '\nD_DataPanBot',
                    'v_FilesPan1Bot': '\nv_FilesPan1Bot',
                    'p_FilesPan1Bot': '\np_FilesPan1Bot',
                    'd_FilesPan1Bot': '\nd_FilesPan1Bot',
                    'vi_BAACAg': '\nvi_BAACAg',
                    'v_BAACAg': '\nv_BAACAg',
                    'p_AgACAg': '\np_AgACAg',
                    'd_BQACAg': '\nd_BQACAg',
                    'd_CgACAg': '\nd_CgACAg',
                    'pk_1': '\npk_1',
                    'pk_2': '\npk_2',
                    'vid+': '\nvid+\n',
                    'pic+': '\npic+\n',
                    'doc+': '\ndoc+\n',
                    '=_mda': '=_mda\n',
                    '=_grp': '=_grp\n',
                    'newjmqbot_': '\nnewjmqbot_',  # 新增：密码提取函数中也添加替换规则（可选，确保格式统一）
                }

                for old, new in replacements.items():
                    text = text.replace(old, new)

                # 筛选关键词
                keywords = ['pw', 'pwd', 'Pass', 'Pasword', 'Password', '密码']

                # 筛选包含特定关键字的消息（不区分大小写）
                if any(keyword.lower() in text.lower() for keyword in keywords):
                    chat_texts.append(text)  # 只保存文本内容

        # 进行二次筛选，按行进行筛选
        secondary_chat_texts = []
        for text in chat_texts:
            lines = text.split('\n')  # 按行分割
            for line in lines:
                # 删除行开头的空格
                line = re.sub(r'^\s+', '', line)
                if '.mp4' in line:
                    continue

                # 筛选条件：匹配 pw 或 pwd 后可能有任意文字，再跟 : 或 ：
                if re.search(r'(pw|pwd).*?[:：]', line, re.IGNORECASE):
                    secondary_chat_texts.append(line)

                # 匹配 '密码', 'Pass', 'Pasword', 'Password' 不区分大小写
                elif '密码' in line or 'pass' in line.lower() or 'pasword' in line.lower() or 'password' in line.lower():
                    secondary_chat_texts.append(line)

        # 排除符合正则表达式的内容
        pattern = re.compile(r'((什么|怎么|多少|知道|直接|中文|账号|生存|流量|财富|网盘|搜索词|谁|有|无|没|求|找|不|要|错|破|啥|假|试|想|换|下|在|缓|忘|问|跑|蹲).*(码|解))|((码|解).*(什么|怎么|软件|多少|字典|知道|直接|中文|谁|有|无|没|求|找|不|要|错|破|啥|假|试|想|换|下|在|缓|忘|问|跑))')

        filtered_chat_texts = [line for line in secondary_chat_texts if not pattern.search(line)]

        # 去重
        if deduplicate:
            filtered_chat_texts = list(set(filtered_chat_texts))

        return '\n'.join(filtered_chat_texts)
    except Exception as e:
        messagebox.showerror("错误", f"处理文件时发生错误: {e}")
        return ""


def select_json_file():
    file_path = filedialog.askopenfilename(title="选择 JSON 文件", filetypes=[("JSON Files", "*.json")])
    if file_path:
        json_file_entry.delete("1.0", tk.END)
        json_file_entry.insert(tk.END, file_path)

def select_output_file():
    file_path = filedialog.asksaveasfilename(title="保存 TXT 文件", defaultextension=".txt", filetypes=[("Text Files", "*.txt")])
    if file_path:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(text_area.get("1.0", tk.END))

def run_extraction():
    json_file_path = json_file_entry.get("1.0", tk.END).strip()
    filter_option = filter_var.get()
    deduplicate = deduplicate_var.get()

    if not json_file_path:
        messagebox.showerror("错误", "请确保选择了 JSON 文件。")
        return

    extracted_text = extract_filtered_chat_texts(json_file_path, filter_option, deduplicate)
    if extracted_text:
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, extracted_text)

        # 更新行数显示
        line_count = extracted_text.count('\n') + 1
        line_count_label.config(text=f"行数: {line_count}")

def run_extractionjy():
    json_file_path = json_file_entry.get("1.0", tk.END).strip()
    deduplicate = deduplicate_var.get()

    if not json_file_path:
        messagebox.showerror("错误", "请确保选择了 JSON 文件。")
        return

    extracted_text = extract_filtered_chatjy_texts(json_file_path, deduplicate)
    if extracted_text:
        text_area.delete("1.0", tk.END)
        text_area.insert(tk.END, extracted_text)

        # 更新行数显示
        line_count = extracted_text.count('\n') + 1
        line_count_label.config(text=f"行数: {line_count}")

def copy_to_clipboard():
    pyperclip.copy(text_area.get("1.0", tk.END))
    #messagebox.showinfo("信息", "内容已复制到剪贴板。")

def on_drop(event):
    file_path = event.data.strip('{}')  # 去掉大括号
    json_file_entry.delete("1.0", tk.END)
    json_file_entry.insert(tk.END, file_path)

def on_hover(event):
    event.widget.config(bg="lightgray")  # 鼠标悬停时变为浅灰色

def on_leave(event):
    event.widget.config(bg="#f0f0f0")  # 恢复为按钮的默认颜色

# 创建 GUI 窗口
root = TkinterDnD.Tk()
root.title("TG爬楼神器")
root.geometry("750x530")  # 设置窗口大小

# JSON 文件选择区域
json_frame = tk.Frame(root)
json_frame.pack(pady=15)

json_file_entry = tk.Text(json_frame, height=3, width=70)  # 调整为70字符宽
json_file_entry.pack(side=tk.LEFT)  # 左侧放置文本框

# 添加去重选项
deduplicate_var = tk.BooleanVar(value=True)  # 默认勾选状态
deduplicate_checkbutton = tk.Checkbutton(json_frame, text="去重", variable=deduplicate_var, bg="#f0f0f0", activebackground="#ADD8E6")
deduplicate_checkbutton.pack(side=tk.LEFT, padx=5)

# 按钮
json_button = tk.Button(json_frame, text="JSON 文件\n选择或拖拽", command=select_json_file, width=12, bg="#f0f0f0")  # 按钮
json_button.pack(side=tk.LEFT, padx=5)
json_button.bind("<Enter>", on_hover)
json_button.bind("<Leave>", on_leave)

# 提取、复制和导出按钮
button_frame = tk.Frame(root)
button_frame.pack(pady=0)

# 筛选选项
filter_var = tk.StringVar(value="所有密文")
filter_options = ["所有密文", "FilesDriveBLGA与旧密文", "DataPanBot", "MediaBKbot", "showfilesbot", "FilesPan1Bot"]

# 将筛选选项、提取、复制和导出按钮放在同一行
filter_menu = tk.OptionMenu(button_frame, filter_var, *filter_options)
filter_menu.config(width=12, bg="#f0f0f0", fg="black", font=("黑体", 12), relief="raised")  # 设置选择框样式
filter_menu.pack(side=tk.LEFT, padx=30)
filter_menu.bind("<Enter>", on_hover)
filter_menu.bind("<Leave>", on_leave)

# 将提取、复制和导出按钮放置在同一行
tk.Button(button_frame, text="  提 取 密 文  ", command=run_extraction, relief=tk.RAISED, bg="#f0f0f0").pack(side=tk.LEFT, padx=15)
tk.Button(button_frame, text="  提 取 密 码  ", command=run_extractionjy, relief=tk.RAISED, bg="#f0f0f0").pack(side=tk.LEFT, padx=15)
tk.Button(button_frame, text="  一 键 复 制  ", command=copy_to_clipboard, relief=tk.RAISED, bg="#f0f0f0").pack(side=tk.LEFT, padx=15)
tk.Button(button_frame, text="  导 出 T X T  ", command=select_output_file, relief=tk.RAISED, bg="#f0f0f0").pack(side=tk.LEFT, padx=15)

# 绑定按钮的鼠标悬停事件
for button in button_frame.winfo_children():
    button.bind("<Enter>", on_hover)
    button.bind("<Leave>", on_leave)

# 显示提取内容的文本框和滚动条
text_frame = tk.Frame(root)
text_frame.pack(pady=15)

text_area = tk.Text(text_frame, wrap=tk.WORD, height=25, width=90)  # 设置文本框高度和宽度
text_area.pack(side=tk.LEFT)

scrollbar = tk.Scrollbar(text_frame, command=text_area.yview, width=20)  # 设置滚动条宽度
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
text_area.config(yscrollcommand=scrollbar.set)

# 添加行数显示标签，去掉字体和大小设置
line_intro_frame = tk.Frame(root)
line_intro_frame.pack(pady=5)

line_count_label = tk.Label(line_intro_frame, text="行数: 0", bg="#f0f0f0")
line_count_label.pack(side=tk.LEFT, padx=10)

# 添加介绍文本，与行数标签同一行（可选：这里也可以添加新密文的说明）
intro_label = tk.Label(line_intro_frame, text="提取密文：vi_, v_, d_, p_, pk_, =_mda, =_grp, showfilesbot_, newjmqbot_\n提取密码：pw：, pw:, pwd：, pwd:, 密码                         ")
intro_label.pack(side=tk.LEFT, padx=10)

# 支持拖拽文件
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', on_drop)

root.mainloop()