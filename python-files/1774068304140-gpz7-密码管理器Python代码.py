#!/usr/bin/env python3
# 指定脚本解释器为 Python 3

# ------------------- 导入必要的模块 -------------------
import os
# 导入操作系统接口模块，用于文件和路径操作
import json
# 导入 JSON 模块，用于将数据序列化为 JSON 格式
import base64
# 导入 base64 模块，用于对密钥进行 base64 编码
import csv
# 导入 CSV 模块，用于导出密码库为 CSV 文件
import getpass
# 导入 getpass 模块（虽然后面未使用，但保留）
import random
# 导入 random 模块，用于在密码长度范围内随机选择长度
import tkinter as tk
# 导入 tkinter 并简写为 tk，用于创建图形界面
from tkinter import ttk, messagebox, simpledialog, filedialog
# 从 tkinter 导入子模块：ttk（主题控件）、messagebox（消息框）、simpledialog（简单对话框）、filedialog（文件对话框）
from datetime import datetime
# 导入 datetime 模块，用于生成导出文件的时间戳
from secrets import choice, randbelow
# 从 secrets 模块导入安全的随机选择函数，用于生成密码
from string import ascii_uppercase, ascii_lowercase, digits, punctuation
# 导入字符串常量：大写字母、小写字母、数字、标点符号，用于密码生成

# 尝试导入加密库 cryptography 中的相关模块
try:
    from cryptography.fernet import Fernet
    # Fernet 是对称加密的简单封装
    from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
    # Scrypt 是密钥派生函数，用于从主密码派生加密密钥
except ImportError:
    # 如果导入失败（未安装 cryptography），弹出错误提示并退出程序
    messagebox.showerror("错误", "需要cryptography库，请安装：pip install cryptography")
    exit(1)

# ------------------- 常量定义 -------------------
DB_FILE = "passwords.enc"
# 加密数据库文件名
SALT_SIZE = 16
# 盐的字节长度（16字节）
KEY_LENGTH = 32
# 派生密钥的长度（32字节，对应 Fernet 的密钥要求）
SCRYPT_N = 2**14
# scrypt 算法的 CPU/内存成本参数（2^14 = 16384）
SCRYPT_R = 8
# scrypt 算法的块大小参数
SCRYPT_P = 1
# scrypt 算法的并行化参数
DEFAULT_MIN_LEN = 8
# 默认密码最小长度
DEFAULT_MAX_LEN = 16
# 默认密码最大长度

# ------------------- 资源路径处理函数（兼容 PyInstaller 打包） -------------------
def resource_path(relative_path):
    # 定义函数，输入相对路径，返回适合当前运行环境的绝对路径
    try:
        # 尝试获取 PyInstaller 创建的临时文件夹路径 _MEIPASS
        base_path = sys._MEIPASS
        # 如果存在，说明程序是打包后的 exe 在运行
    except Exception:
        # 如果不存在，说明是在开发环境中运行
        base_path = os.path.dirname(os.path.abspath(__file__))
        # 获取当前脚本所在目录作为基础路径
    return os.path.join(base_path, relative_path)
    # 将基础路径与相对路径拼接并返回

# ------------------- 密码强度检测函数 -------------------
def check_password_strength(password):
    # 输入密码字符串，返回强度等级和描述信息
    length = len(password)
    # 获取密码长度
    has_upper = any(c.isupper() for c in password)
    # 判断是否包含大写字母
    has_lower = any(c.islower() for c in password)
    # 判断是否包含小写字母
    has_digit = any(c.isdigit() for c in password)
    # 判断是否包含数字
    has_symbol = any(c in punctuation for c in password)
    # 判断是否包含标点符号
    char_types = sum([has_upper, has_lower, has_digit, has_symbol])
    # 计算包含的字符类型数量

    # 根据规则评定强度
    if length < 8:
        return 'weak', "长度过短（至少8位）"
        # 长度不足8位为弱密码
    if char_types == 1:
        return 'weak', "仅包含一种字符类型"
        # 只有一种字符类型为弱密码
    if length >= 12 and char_types >= 3:
        return 'strong', "强密码"
        # 长度≥12且类型≥3为强密码
    if length >= 8 and char_types >= 2:
        return 'medium', "中等强度"
        # 长度≥8且类型≥2为中等强度
    return 'weak', "不符合强度要求"
    # 其他情况为弱密码

def require_medium_or_strong(password):
    # 判断密码是否至少为中等强度，返回布尔值
    strength, msg = check_password_strength(password)
    # 调用强度检测函数获取等级和消息
    if strength in ('medium', 'strong'):
        # 如果等级为中等或强
        return True
        # 返回 True（允许通过）
    return False
    # 否则返回 False（强度不足）

# ------------------- 密码生成函数 -------------------
def generate_password(length, use_upper=True, use_lower=True, use_digits=True, use_symbols=True):
    # 生成指定长度的随机密码，可设置是否包含各类字符，默认全包含
    chars = ""
    # 初始化字符池为空字符串
    if use_upper: chars += ascii_uppercase
    # 如果需要大写字母，将大写字母常量加入字符池
    if use_lower: chars += ascii_lowercase
    # 如果需要小写字母，将小写字母常量加入字符池
    if use_digits: chars += digits
    # 如果需要数字，将数字常量加入字符池
    if use_symbols: chars += punctuation
    # 如果需要符号，将标点常量加入字符池
    if not chars:
        # 如果字符池为空（所有类型都禁用）
        return ""
        # 返回空字符串

    password = []
    # 初始化密码列表，用于逐步构建密码字符
    # 保证至少包含每个启用的字符集的一个字符
    if use_upper: password.append(choice(ascii_uppercase))
    # 如果启用大写，从大写字母中随机选一个加入列表
    if use_lower: password.append(choice(ascii_lowercase))
    # 如果启用小写，从小写字母中随机选一个加入列表
    if use_digits: password.append(choice(digits))
    # 如果启用数字，从数字中随机选一个加入列表
    if use_symbols: password.append(choice(punctuation))
    # 如果启用符号，从符号中随机选一个加入列表

    for _ in range(length - len(password)):
        # 循环填充剩余长度，循环次数 = 目标长度 - 已添加的字符数
        password.append(choice(chars))
        # 从字符池中随机选一个字符加入列表

    # 打乱列表顺序，避免固定格式
    for i in range(len(password)-1, 0, -1):
        # 从最后一个元素开始向前遍历
        j = randbelow(i+1)
        # 生成一个 0 到 i 之间的随机索引（使用 secrets.randbelow 保证安全）
        password[i], password[j] = password[j], password[i]
        # 交换位置，实现随机打乱

    return "".join(password)
    # 将字符列表连接成字符串并返回

def get_password_length():
    # 弹出一个对话框让用户输入最小/最大长度，返回一个在范围内的随机长度
    dialog = tk.Toplevel()
    # 创建一个顶级窗口作为对话框
    dialog.title("密码长度范围")
    # 设置对话框标题
    dialog.geometry("300x150")
    # 设置窗口大小为 300x150 像素
    dialog.transient()   # 设为父窗口的临时窗口，不指定父窗口时可能无效，但保留
    # 通常需要指定父窗口，但这里简单处理
    dialog.grab_set()    # 设置模态，阻止与其他窗口交互

    tk.Label(dialog, text="最小长度 (默认8):").pack(pady=5)
    # 在对话框中添加标签，提示输入最小长度，并垂直间距5
    min_entry = tk.Entry(dialog)
    # 创建单行输入框用于输入最小长度
    min_entry.pack()
    # 将输入框添加到窗口
    min_entry.insert(0, "8")
    # 在输入框中预填默认值 8

    tk.Label(dialog, text="最大长度 (默认16):").pack(pady=5)
    # 添加标签提示输入最大长度
    max_entry = tk.Entry(dialog)
    # 创建最大长度输入框
    max_entry.pack()
    # 添加到窗口
    max_entry.insert(0, "16")
    # 预填默认值 16

    result = [8]
    # 创建一个列表作为可变对象，用于在内部函数中修改并返回结果，默认8

    def on_ok():
        # 定义“确定”按钮的回调函数
        min_len = min_entry.get().strip()
        # 获取最小长度输入框的内容并去除首尾空格
        max_len = max_entry.get().strip()
        # 获取最大长度输入框的内容并去除首尾空格
        min_len = int(min_len) if min_len.isdigit() else 8
        # 如果输入是数字，转换为整数，否则使用默认值8
        max_len = int(max_len) if max_len.isdigit() else 16
        # 如果输入是数字，转换为整数，否则使用默认值16
        if min_len > max_len:
            # 如果最小长度大于最大长度
            min_len, max_len = max_len, min_len
            # 交换两者，保证范围有效
        if min_len < 8:
            # 如果最小长度小于8
            min_len = 8
            # 强制设为8（安全下限）
        if max_len < min_len:
            # 如果最大长度小于最小长度（可能由于上述强制调整导致）
            max_len = min_len
            # 使最大长度等于最小长度
        result[0] = random.randint(min_len, max_len)
        # 在范围内随机选择一个整数，存入 result 列表的第一个元素
        dialog.destroy()
        # 关闭对话框

    tk.Button(dialog, text="确定", command=on_ok).pack(pady=10)
    # 创建“确定”按钮，点击时调用 on_ok 函数，并添加垂直间距10
    dialog.wait_window()
    # 等待该窗口关闭，程序在此阻塞直到对话框销毁
    return result[0]
    # 返回用户选择的随机长度

# ------------------- 加密数据库操作函数 -------------------
def derive_key(master_password, salt):
    # 从主密码和盐派生加密密钥
    kdf = Scrypt(salt=salt, length=KEY_LENGTH, n=SCRYPT_N, r=SCRYPT_R, p=SCRYPT_P)
    # 创建 Scrypt 对象，传入盐、目标长度、成本参数
    key = kdf.derive(master_password.encode())
    # 使用主密码（编码为字节）派生密钥，得到原始密钥字节
    return base64.urlsafe_b64encode(key)
    # 将原始密钥进行 URL 安全的 base64 编码，返回 Fernet 可用的密钥

def encrypt_data(data, key):
    # 加密数据（字典），返回加密后的字节串
    fernet = Fernet(key)
    # 创建 Fernet 加密器对象，传入密钥
    json_str = json.dumps(data, indent=2, ensure_ascii=False)
    # 将字典转换为格式化的 JSON 字符串，ensure_ascii=False 以保留非 ASCII 字符
    return fernet.encrypt(json_str.encode())
    # 将 JSON 字符串编码为字节，然后加密并返回

def decrypt_data(encrypted_data, key):
    # 解密数据，返回原始字典
    fernet = Fernet(key)
    # 创建 Fernet 解密器对象
    decrypted = fernet.decrypt(encrypted_data)
    # 解密数据，得到字节串
    return json.loads(decrypted.decode())
    # 将字节串解码为字符串，再解析为 JSON 字典并返回

def load_db(master_password):
    # 加载数据库，返回条目列表和盐
    db_path = resource_path(DB_FILE)
    # 获取数据库文件的完整路径（使用 resource_path 适应打包环境）
    if not os.path.exists(db_path):
        # 如果文件不存在（首次运行）
        salt = os.urandom(SALT_SIZE)
        # 生成随机盐
        key = derive_key(master_password, salt)
        # 派生密钥
        entries = []
        # 初始化空条目列表
        encrypted = encrypt_data(entries, key)
        # 加密空列表
        with open(db_path, "wb") as f:
            # 以二进制写入模式打开文件
            f.write(salt + encrypted)
            # 将盐和加密数据依次写入文件
        return entries, salt
        # 返回空条目列表和盐

    # 文件存在时的处理
    with open(db_path, "rb") as f:
        # 以二进制读取模式打开文件
        data = f.read()
        # 读取全部内容
    salt = data[:SALT_SIZE]
    # 提取前 SALT_SIZE 字节作为盐
    encrypted_data = data[SALT_SIZE:]
    # 剩余部分为加密数据
    key = derive_key(master_password, salt)
    # 使用用户提供的主密码和文件中提取的盐派生密钥
    entries = decrypt_data(encrypted_data, key)
    # 解密数据得到条目列表
    return entries, salt
    # 返回条目列表和盐

def save_db(entries, master_password, salt):
    # 保存数据库，将条目列表加密后写入文件
    db_path = resource_path(DB_FILE)
    # 获取数据库文件路径
    key = derive_key(master_password, salt)
    # 派生密钥（使用相同的盐）
    encrypted = encrypt_data(entries, key)
    # 加密条目列表
    with open(db_path, "wb") as f:
        # 以二进制写入模式打开文件
        f.write(salt + encrypted)
        # 将盐和加密数据写入文件（覆盖原有内容）

# ------------------- 主界面类 PasswordManagerApp -------------------
class PasswordManagerApp:
    def __init__(self, root):
        # 构造函数，接收 Tk 根窗口对象
        self.root = root
        # 保存根窗口引用
        self.root.title("密码管理器")
        # 设置窗口标题
        self.root.geometry("700x500")
        # 设置窗口初始大小
        self.master_pwd = None
        # 初始化主密码变量为 None
        self.salt = None
        # 初始化盐变量为 None
        self.entries = []
        # 初始化条目列表为空

        # 先弹出主密码输入窗口
        self.show_login()
        # 调用 show_login 方法显示登录对话框

    def show_login(self):
        # 显示登录对话框（输入主密码）
        login_win = tk.Toplevel(self.root)
        # 创建一个顶级窗口，父窗口为 self.root
        login_win.title("登录")
        # 设置登录窗口标题
        login_win.geometry("300x150")
        # 设置登录窗口大小
        login_win.transient(self.root)
        # 设置为根窗口的临时窗口，通常位于父窗口之上
        login_win.grab_set()
        # 设置为模态，阻止与其他窗口交互

        tk.Label(login_win, text="请输入主密码:").pack(pady=10)
        # 在登录窗口中添加标签，提示输入主密码，垂直间距10
        pwd_entry = tk.Entry(login_win, show="*")
        # 创建密码输入框，显示为星号
        pwd_entry.pack(pady=5)
        # 添加输入框到窗口，垂直间距5
        pwd_entry.focus()
        # 让输入框获得焦点，方便直接输入

        def on_login():
            # 定义“登录”按钮的回调函数
            master_pwd = pwd_entry.get()
            # 获取输入框中的主密码
            if not master_pwd:
                # 如果密码为空
                messagebox.showerror("错误", "主密码不能为空")
                # 弹出错误提示
                return
                # 返回，不继续处理
            try:
                # 尝试加载数据库
                self.entries, self.salt = load_db(master_pwd)
                # 调用 load_db 加载条目和盐，并保存到实例变量
                self.master_pwd = master_pwd
                # 保存主密码到实例变量
                login_win.destroy()
                # 关闭登录窗口
                self.build_main_ui()
                # 构建主界面
                self.refresh_list()
                # 刷新条目列表
            except Exception as e:
                # 如果发生异常（如密码错误）
                messagebox.showerror("错误", f"登录失败: {e}")
                # 弹出错误信息

        tk.Button(login_win, text="登录", command=on_login).pack(pady=10)
        # 创建“登录”按钮，点击时调用 on_login 函数，并添加垂直间距
        login_win.protocol("WM_DELETE_WINDOW", self.root.quit)
        # 设置窗口关闭协议，如果用户直接关闭登录窗口，则退出整个程序

    def build_main_ui(self):
        # 构建主界面（登录成功后调用）
        main_frame = ttk.Frame(self.root, padding="10")
        # 创建主题框架，放置在根窗口中，内边距10像素
        main_frame.pack(fill=tk.BOTH, expand=True)
        # 将框架填充整个窗口，并允许扩展

        # 左侧：Treeview 显示条目列表
        list_frame = ttk.LabelFrame(main_frame, text="密码条目", padding="5")
        # 创建标签框架，标题为“密码条目”，内边距5
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 将标签框架放置在 main_frame 左侧，填充并扩展

        columns = ('service', 'username')
        # 定义 Treeview 的两列：服务名和用户名
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', selectmode='browse')
        # 创建 Treeview 控件，显示列标题，选择模式为浏览（单选）
        self.tree.heading('service', text='服务')
        # 设置 'service' 列标题为“服务”
        self.tree.heading('username', text='用户名')
        # 设置 'username' 列标题为“用户名”
        self.tree.column('service', width=150)
        # 设置 'service' 列宽度为150像素
        self.tree.column('username', width=150)
        # 设置 'username' 列宽度为150像素

        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        # 创建垂直滚动条，绑定到 Treeview 的垂直滚动
        self.tree.configure(yscrollcommand=scrollbar.set)
        # 设置 Treeview 的垂直滚动命令为滚动条的 set 方法
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        # 将滚动条放置在 list_frame 右侧，填充 Y 方向
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        # 将 Treeview 放置在滚动条左侧，填充并扩展

        # 右侧：按钮区域
        btn_frame = ttk.Frame(main_frame, padding="10")
        # 创建按钮框架，放置在 main_frame 右侧，内边距10
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y)
        # 将按钮框架放置在右侧，填充 Y 方向

        # 创建多个按钮，并设置点击事件
        ttk.Button(btn_frame, text="查看详情", command=self.view_entry).pack(pady=5, fill=tk.X)
        # “查看详情”按钮，点击调用 view_entry 方法，垂直间距5，水平填充
        ttk.Button(btn_frame, text="添加条目", command=self.add_entry).pack(pady=5, fill=tk.X)
        # “添加条目”按钮，点击调用 add_entry
        ttk.Button(btn_frame, text="编辑条目", command=self.edit_entry).pack(pady=5, fill=tk.X)
        # “编辑条目”按钮，点击调用 edit_entry
        ttk.Button(btn_frame, text="删除条目", command=self.delete_entry).pack(pady=5, fill=tk.X)
        # “删除条目”按钮，点击调用 delete_entry
        ttk.Button(btn_frame, text="搜索", command=self.search_entry).pack(pady=5, fill=tk.X)
        # “搜索”按钮，点击调用 search_entry
        ttk.Button(btn_frame, text="导出", command=self.export_entries).pack(pady=5, fill=tk.X)
        # “导出”按钮，点击调用 export_entries
        ttk.Button(btn_frame, text="生成密码", command=self.generate_pwd).pack(pady=5, fill=tk.X)
        # “生成密码”按钮，点击调用 generate_pwd
        ttk.Button(btn_frame, text="退出", command=self.root.quit).pack(pady=20, fill=tk.X)
        # “退出”按钮，点击退出程序，垂直间距20

    def refresh_list(self):
        # 刷新 Treeview 中的条目列表，根据 self.entries 更新显示
        for row in self.tree.get_children():
            # 遍历 Treeview 中所有现有的行
            self.tree.delete(row)
            # 删除每一行，清空列表
        for entry in self.entries:
            # 遍历 self.entries 中的每个条目
            self.tree.insert('', tk.END, values=(entry['service'], entry['username']))
            # 在 Treeview 末尾插入新行，显示服务名和用户名

    def get_selected_index(self):
        # 获取当前在 Treeview 中选中条目的索引（对应 self.entries 中的索引）
        selected = self.tree.selection()
        # 获取选中的行 ID 列表
        if not selected:
            # 如果没有选中任何行
            return None
            # 返回 None
        # 通过 Treeview 的 index 方法获取该行在控件中的索引
        index = self.tree.index(selected[0])
        # 获取第一个选中行的索引（因为是单选）
        return index
        # 返回索引

    def view_entry(self):
        # 查看条目详情
        idx = self.get_selected_index()
        # 获取选中条目的索引
        if idx is None:
            # 如果没有选中条目
            messagebox.showinfo("提示", "请先选择一个条目")
            # 弹出提示信息
            return
            # 返回
        entry = self.entries[idx]
        # 根据索引获取条目字典
        info = f"服务: {entry['service']}\n用户名: {entry['username']}\n密码: {entry['password']}\n备注: {entry['notes']}"
        # 格式化信息字符串
        messagebox.showinfo("条目详情", info)
        # 弹出信息框显示详情

    def add_entry(self):
        # 添加新条目
        AddEditDialog(self, None)
        # 创建 AddEditDialog 对话框，传入 app 对象和 None（表示添加模式）

    def edit_entry(self):
        # 编辑条目
        idx = self.get_selected_index()
        # 获取选中条目的索引
        if idx is None:
            # 如果没有选中
            messagebox.showinfo("提示", "请先选择一个条目")
            # 提示
            return
        AddEditDialog(self, idx)
        # 创建 AddEditDialog 对话框，传入 app 对象和索引（编辑模式）

    def delete_entry(self):
        # 删除条目
        idx = self.get_selected_index()
        # 获取选中条目的索引
        if idx is None:
            # 如果没有选中
            return
            # 返回
        entry = self.entries[idx]
        # 获取条目字典
        if messagebox.askyesno("确认删除", f"确定要删除 '{entry['service']}' 吗？"):
            # 弹出确认对话框，询问是否删除，如果用户点击“是”
            del self.entries[idx]
            # 从列表中删除该条目
            save_db(self.entries, self.master_pwd, self.salt)
            # 保存数据库
            self.refresh_list()
            # 刷新列表显示

    def search_entry(self):
        # 搜索条目
        keyword = simpledialog.askstring("搜索", "请输入搜索关键词（服务名或用户名）:")
        # 弹出简单字符串输入对话框，获取关键词
        if not keyword:
            # 如果用户取消或未输入
            return
            # 返回
        results = []
        # 初始化结果列表，元素为 (索引, 条目)
        for i, e in enumerate(self.entries):
            # 遍历所有条目，i 为索引，e 为条目字典
            if keyword.lower() in e['service'].lower() or keyword.lower() in e['username'].lower():
                # 如果关键词（转为小写）在服务名或用户名（转为小写）中
                results.append((i, e))
                # 将索引和条目添加到结果列表
        if not results:
            # 如果没有匹配结果
            messagebox.showinfo("搜索结果", "未找到匹配条目")
            # 提示未找到
            return
        # 如果有匹配结果，简单处理：如果只有一个结果，显示详情；否则列出所有匹配项
        if len(results) == 1:
            # 只有一个结果
            idx, entry = results[0]
            # 获取索引和条目
            info = f"服务: {entry['service']}\n用户名: {entry['username']}\n密码: {entry['password']}\n备注: {entry['notes']}"
            # 格式化详情
            messagebox.showinfo("条目详情", info)
            # 显示详情
        else:
            # 多个结果
            msg = "找到多个匹配条目:\n"
            # 初始化消息字符串
            for i, (idx, e) in enumerate(results):
                # 遍历结果，i 用于显示序号
                msg += f"{i+1}. {e['service']} ({e['username']})\n"
                # 追加序号、服务名和用户名
            messagebox.showinfo("搜索结果", msg)
            # 显示结果列表

    def export_entries(self):
        # 导出密码库为 TXT 或 CSV
        if not self.entries:
            # 如果没有条目
            messagebox.showinfo("提示", "没有条目可导出")
            # 提示
            return
        filetypes = [("文本文件", "*.txt"), ("CSV文件", "*.csv")]
        # 定义文件类型过滤选项
        filename = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=filetypes)
        # 弹出“另存为”对话框，让用户选择保存位置和文件名，默认扩展名为 .txt
        if not filename:
            # 如果用户取消
            return
            # 返回
        try:
            # 尝试写入文件
            if filename.endswith('.txt'):
                # 如果文件名以 .txt 结尾
                with open(filename, 'w', encoding='utf-8') as f:
                    # 以写入模式打开文本文件，使用 UTF-8 编码
                    for entry in self.entries:
                        # 遍历每个条目
                        f.write(f"服务: {entry['service']}\n用户名: {entry['username']}\n密码: {entry['password']}\n备注: {entry['notes']}\n{'-'*30}\n")
                        # 写入格式化的条目信息，并用分隔线隔开
            else:
                # 否则假设为 CSV
                with open(filename, 'w', newline='', encoding='utf-8-sig') as f:
                    # 以写入模式打开 CSV 文件，使用 UTF-8 with BOM 编码（Excel 兼容）
                    writer = csv.writer(f)
                    # 创建 CSV 写入器
                    writer.writerow(['服务', '用户名', '密码', '备注'])
                    # 写入表头
                    for entry in self.entries:
                        # 遍历条目
                        writer.writerow([entry['service'], entry['username'], entry['password'], entry['notes']])
                        # 写入数据行
            messagebox.showinfo("成功", f"导出成功：{filename}")
            # 弹出成功提示
        except Exception as e:
            # 如果发生异常
            messagebox.showerror("错误", f"导出失败：{e}")
            # 显示错误信息

    def generate_pwd(self):
        # 生成随机密码并显示
        length = get_password_length()
        # 调用 get_password_length 获取随机长度（通过对话框）
        pwd = generate_password(length)
        # 生成指定长度的密码
        messagebox.showinfo("生成的密码", f"密码: {pwd}")
        # 弹出信息框显示密码

# ------------------- 添加/编辑对话框类 AddEditDialog -------------------
class AddEditDialog:
    def __init__(self, app, idx):
        # 构造函数，接收主应用对象 app 和条目索引 idx（None 表示添加，否则编辑）
        self.app = app
        # 保存主应用对象引用
        self.idx = idx
        # 保存索引
        if idx is not None:
            # 如果是编辑模式
            self.entry = app.entries[idx]
            # 获取要编辑的条目字典
        else:
            # 如果是添加模式
            self.entry = {'service':'', 'username':'', 'password':'', 'notes':''}
            # 创建一个空条目字典

        self.dialog = tk.Toplevel(app.root)
        # 创建一个顶级窗口作为对话框，父窗口为主应用根窗口
        self.dialog.title("编辑条目" if idx is not None else "添加条目")
        # 根据模式设置窗口标题
        self.dialog.geometry("400x350")
        # 设置窗口大小
        self.dialog.transient(app.root)
        # 设置为父窗口的临时窗口
        self.dialog.grab_set()
        # 模态，禁止与其他窗口交互

        # 服务名称输入
        tk.Label(self.dialog, text="服务名称:").grid(row=0, column=0, sticky='e', padx=5, pady=5)
        # 标签，位于第0行第0列，右对齐，边距5
        self.service_var = tk.StringVar(value=self.entry['service'])
        # 创建字符串变量，绑定到条目的服务名
        tk.Entry(self.dialog, textvariable=self.service_var, width=30).grid(row=0, column=1, padx=5, pady=5)
        # 输入框，宽度30，绑定到 service_var，位于第0行第1列

        # 用户名输入
        tk.Label(self.dialog, text="用户名:").grid(row=1, column=0, sticky='e', padx=5, pady=5)
        self.username_var = tk.StringVar(value=self.entry['username'])
        tk.Entry(self.dialog, textvariable=self.username_var, width=30).grid(row=1, column=1, padx=5, pady=5)

        # 密码输入（带生成按钮）
        tk.Label(self.dialog, text="密码:").grid(row=2, column=0, sticky='e', padx=5, pady=5)
        self.password_var = tk.StringVar(value=self.entry['password'])
        # 密码字符串变量
        pwd_frame = tk.Frame(self.dialog)
        # 创建一个框架用于放置密码输入框和生成按钮，使它们在同一行
        pwd_frame.grid(row=2, column=1, sticky='w')
        # 将框架放置在第2行第1列，左对齐
        tk.Entry(pwd_frame, textvariable=self.password_var, width=20, show="*").pack(side=tk.LEFT)
        # 在框架中添加密码输入框，宽度20，显示星号，左对齐
        tk.Button(pwd_frame, text="生成", command=self.generate_pwd).pack(side=tk.LEFT, padx=5)
        # 在框架中添加“生成”按钮，点击时调用 generate_pwd 方法，左对齐，左侧间距5

        # 备注输入
        tk.Label(self.dialog, text="备注:").grid(row=3, column=0, sticky='e', padx=5, pady=5)
        self.notes_var = tk.StringVar(value=self.entry['notes'])
        tk.Entry(self.dialog, textvariable=self.notes_var, width=30).grid(row=3, column=1, padx=5, pady=5)

        # 密码强度提示标签
        self.strength_label = tk.Label(self.dialog, text="密码强度: ", fg="blue")
        # 创建标签，初始文字为“密码强度:”，蓝色
        self.strength_label.grid(row=4, column=0, columnspan=2, pady=5)
        # 放置在第4行，跨两列，垂直间距5

        # 绑定密码变量变化时的追踪函数
        self.password_var.trace('w', self.update_strength)
        # 当 password_var 的值发生变化时（写操作），调用 update_strength 方法
        self.update_strength()
        # 初始调用一次，显示当前密码强度

        # 按钮框架（保存/取消）
        btn_frame = tk.Frame(self.dialog)
        # 创建按钮框架
        btn_frame.grid(row=5, column=0, columnspan=2, pady=10)
        # 放置在第5行，跨两列，垂直间距10
        tk.Button(btn_frame, text="保存", command=self.save).pack(side=tk.LEFT, padx=10)
        # 保存按钮，点击调用 save 方法，左对齐，左右边距10
        tk.Button(btn_frame, text="取消", command=self.dialog.destroy).pack(side=tk.LEFT)
        # 取消按钮，点击关闭对话框，左对齐

    def update_strength(self, *args):
        # 更新密码强度标签
        pwd = self.password_var.get()
        # 获取当前密码字符串
        if not pwd:
            # 如果密码为空
            self.strength_label.config(text="密码强度: 未设置")
            # 设置标签文字为“未设置”
            return
        strength, msg = check_password_strength(pwd)
        # 调用强度检测函数，获取等级和消息
        # 根据等级设置颜色
        color = {"weak":"red", "medium":"orange", "strong":"green"}.get(strength, "black")
        # 使用字典映射：弱-红色，中-橙色，强-绿色，默认黑色
        self.strength_label.config(text=f"密码强度: {strength} - {msg}", fg=color)
        # 更新标签文字和前景色

    def generate_pwd(self):
        # 生成随机密码并填入密码输入框
        length = get_password_length()
        # 调用 get_password_length 获取随机长度
        pwd = generate_password(length)
        # 生成密码
        self.password_var.set(pwd)
        # 将生成的密码设置到 password_var，从而更新输入框

    def save(self):
        # 保存条目
        service = self.service_var.get().strip()
        # 获取服务名并去除首尾空格
        username = self.username_var.get().strip()
        # 获取用户名
        password = self.password_var.get().strip()
        # 获取密码
        notes = self.notes_var.get().strip()
        # 获取备注

        if not service or not username:
            # 如果服务名或用户名为空
            messagebox.showerror("错误", "服务名和用户名不能为空")
            # 弹出错误提示
            return
            # 返回
        if not password:
            # 如果密码为空
            messagebox.showerror("错误", "密码不能为空")
            return
        # 强度检查
        if not require_medium_or_strong(password):
            # 如果密码强度不足
            messagebox.showerror("错误", "密码强度不足，请使用更强的密码")
            return

        new_entry = {
            "service": service,
            "username": username,
            "password": password,
            "notes": notes
        }
        # 创建新的条目字典

        if self.idx is None:
            # 如果是添加模式
            self.app.entries.append(new_entry)
            # 将新条目添加到主应用的条目列表末尾
        else:
            # 如果是编辑模式
            self.app.entries[self.idx] = new_entry
            # 替换指定索引的条目

        save_db(self.app.entries, self.app.master_pwd, self.app.salt)
        # 调用保存函数，将更新后的列表加密保存
        self.app.refresh_list()
        # 刷新主界面的列表显示
        self.dialog.destroy()
        # 关闭对话框

# ------------------- 主程序入口 -------------------
if __name__ == "__main__":
    import sys
    # 导入 sys 模块（resource_path 函数中会用到，但之前可能未导入，这里补上）
    root = tk.Tk()
    # 创建 Tkinter 根窗口
    root.withdraw()
    # 隐藏根窗口（先显示登录窗口）
    app = PasswordManagerApp(root)
    # 创建 PasswordManagerApp 实例，传入根窗口
    root.deiconify()
    # 登录成功后（或至少构建界面后）显示根窗口
    root.mainloop()
    # 进入 Tkinter 事件主循环，等待用户操作