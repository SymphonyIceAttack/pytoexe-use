import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
import ctypes
import sys
import locale
from datetime import datetime
import shutil
import stat

# ===================== 全局配置与基础适配 =====================
# 强制设置UTF-8编码，解决打包后中文乱码
def set_utf8_encoding():
    try:
        locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')
    except:
        try:
            locale.setlocale(locale.LC_ALL, '')
        except:
            pass
    os.environ['PYTHONIOENCODING'] = 'utf-8'
    os.environ['LC_ALL'] = 'zh_CN.UTF-8'

# 适配打包后的路径
def get_app_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

# 初始化基础配置
set_utf8_encoding()
CONFIG_FILE = os.path.join(get_app_dir(), "项目文件夹工具配置.ini")
DEFAULT_SUB_FOLDERS = ["资料", "参考图", "CAD", "效果图", "其他信息"]
MAX_PATH_LENGTH = 260
SETTING_WINDOW = None  # 控制设置弹窗唯一

# Windows高DPI适配
def adapt_high_dpi():
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except:
            pass

# ===================== 工具函数 =====================
# 清理输入中的无效空格/字符
def clean_input_text(text):
    text = text.replace('　', ' ').strip()  # 全角空格转半角+去首尾
    text = re.sub(r'\s+', ' ', text)       # 合并连续空格
    return text

# 读取配置（容错）
def load_history_config():
    config = {"last_city": "", "last_path": "", "custom_subfolders": ",".join(DEFAULT_SUB_FOLDERS)}
    if not os.path.exists(CONFIG_FILE):
        return config
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or "=" not in line:
                    continue
                key, value = line.split("=", 1)
                config[key.strip()] = value.strip()
    except:
        pass
    return config

# 保存配置（容错）
def save_history_config(city, save_path, subfolders):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            f.write(f"last_city={city}\n")
            f.write(f"last_path={save_path}\n")
            f.write(f"custom_subfolders={subfolders}\n")
    except:
        pass

# 路径长度校验（兼容UNC）
def check_path_length(base_path, folder_name):
    full_path = os.path.join(base_path, folder_name)
    if full_path.startswith('\\\\'):
        unc_prefix = full_path.split('\\', 3)[0:3]
        unc_prefix = '\\'.join(unc_prefix)
        real_path = full_path[len(unc_prefix):]
        return len(real_path) < MAX_PATH_LENGTH, full_path
    return len(full_path) < MAX_PATH_LENGTH, full_path

# 检查磁盘状态（空间/只读）
def check_disk_status(path):
    try:
        # 检查是否可写
        test_file = os.path.join(path, f"_{datetime.now().timestamp()}.tmp")
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except PermissionError:
        return False, "路径为只读模式，无写入权限"
    except OSError as e:
        if "no space" in str(e).lower() or "磁盘满" in str(e):
            return False, "磁盘空间不足，无法创建文件夹"
        return False, f"磁盘异常：{str(e)}"
    return True, ""

# 解析日期（兼容纯数字/带文字）
def parse_date(text):
    text = clean_input_text(text)
    # 兼容纯8位数字（20260312）
    if re.match(r'^\d{8}$', text):
        try:
            year = int(text[:4])
            month = int(text[4:6])
            day = int(text[6:8])
            return datetime(year, month, day)
        except:
            return None
    # 兼容带年月日的格式
    nums = re.findall(r'\d+', text)
    if len(nums) < 3:
        return None
    try:
        year, month, day = map(int, nums[:3])
        return datetime(year, month, day)
    except:
        return None

# ===================== 核心功能 =====================
def select_save_path():
    selected_path = filedialog.askdirectory(title="选择项目文件夹生成位置")
    if selected_path:
        path_input.delete(0, tk.END)
        path_input.insert(0, selected_path)
        path_input.xview_moveto(1)

# 自定义子文件夹（单例弹窗）
def open_subfolder_settings():
    global SETTING_WINDOW
    if SETTING_WINDOW and SETTING_WINDOW.winfo_exists():
        SETTING_WINDOW.lift()
        return
    
    SETTING_WINDOW = tk.Toplevel(main_window)
    SETTING_WINDOW.title("自定义子文件夹")
    SETTING_WINDOW.geometry("400x200")
    SETTING_WINDOW.resizable(False, False)
    SETTING_WINDOW.grab_set()

    # 弹窗关闭时重置标记
    def on_close():
        global SETTING_WINDOW
        SETTING_WINDOW = None
        SETTING_WINDOW.destroy()
    SETTING_WINDOW.protocol("WM_DELETE_WINDOW", on_close)

    tk.Label(SETTING_WINDOW, text="自定义子文件夹（逗号分隔，全角/半角均可）：", font=("微软雅黑", 10)).pack(padx=20, pady=10, anchor="w")
    sub_input = tk.Text(SETTING_WINDOW, font=("微软雅黑", 10), width=50, height=4)
    sub_input.pack(padx=20, pady=5)
    sub_input.insert("1.0", sub_folder_config.get("custom_subfolders", ",".join(DEFAULT_SUB_FOLDERS)))

    def save_sub_setting():
        sub_text = sub_input.get("1.0", tk.END).strip()
        if not sub_text:
            messagebox.showerror("错误", "子文件夹不能为空", parent=SETTING_WINDOW)
            return
        sub_text = sub_text.replace("，", ",").replace('　', ' ')
        sub_folder_config["custom_subfolders"] = sub_text
        save_history_config(city_input.get().strip(), path_input.get().strip(), sub_text)
        messagebox.showinfo("成功", "子文件夹配置已保存", parent=SETTING_WINDOW)
        on_close()

    tk.Button(SETTING_WINDOW, text="保存配置", font=("微软雅黑", 10), command=save_sub_setting).pack(pady=10)

# 核心创建逻辑（终极版）
def create_project_folder(event=None):
    create_btn.config(state=tk.DISABLED, bg="#888888")
    main_window.update_idletasks()

    try:
        # 1. 获取并清理输入
        date_text = clean_input_text(date_input.get())
        project_city = clean_input_text(city_input.get())
        project_name = clean_input_text(name_input.get())
        base_path = path_input.get().strip()

        # 2. 非空校验
        if not all([date_text, project_city, project_name, base_path]):
            messagebox.showerror("输入错误", "请填写完整的项目信息（日期、城市、名称、路径均不能为空）")
            return

        # 3. 路径校验
        if not os.path.isdir(base_path):
            tip = "共享路径无权限/不存在" if base_path.startswith('\\\\') else "路径不存在"
            messagebox.showerror("路径错误", tip)
            return
        
        # 4. 磁盘状态校验
        disk_ok, disk_msg = check_disk_status(base_path)
        if not disk_ok:
            messagebox.showerror("磁盘错误", disk_msg)
            return

        # 5. 非法字符校验
        invalid_chars = r'[\\/:*?"<>|]'
        if re.search(invalid_chars, project_city) or re.search(invalid_chars, project_name):
            messagebox.showerror("输入错误", "禁止包含 \\ / : * ? \" < > | 等非法字符")
            return

        # 6. 日期解析
        date_obj = parse_date(date_text)
        if not date_obj or not (2000 <= date_obj.year <= 2030):
            messagebox.showerror("日期错误", "日期无效（支持2000-2030年，格式：20260312/2026年3月12日）")
            return
        date_str = date_obj.strftime("%Y%m%d")

        # 7. 路径长度校验
        main_folder_name = f"{date_str}-{project_city}-{project_name}"
        path_valid, full_path = check_path_length(base_path, main_folder_name)
        if not path_valid:
            messagebox.showerror("路径过长", f"路径超Windows限制（{MAX_PATH_LENGTH}字符），请简化名称/路径")
            return

        # 8. 重复校验
        if os.path.exists(full_path):
            messagebox.showerror("创建失败", f"文件夹已存在：{main_folder_name}")
            return

        # 9. 解析子文件夹
        try:
            sub_text = sub_folder_config["custom_subfolders"].replace("，", ",").replace('　', ' ')
            sub_folder_list = [clean_input_text(f) for f in sub_text.split(",") if clean_input_text(f)]
            if not sub_folder_list:
                sub_folder_list = DEFAULT_SUB_FOLDERS
        except:
            sub_folder_list = DEFAULT_SUB_FOLDERS

        # 10. 执行创建（带回滚）
        create_success = False
        try:
            os.makedirs(full_path, exist_ok=False)
            for folder in sub_folder_list:
                sub_path = os.path.join(full_path, folder)
                os.makedirs(sub_path, exist_ok=False)
            create_success = True
        except PermissionError:
            messagebox.showerror("权限错误", "无写入权限，请换路径/关闭杀毒软件")
        except OSError as e:
            messagebox.showerror("系统错误", f"创建失败：{str(e)}")
        except Exception as e:
            messagebox.showerror("未知错误", f"出错：{str(e)}")
        finally:
            if not create_success and os.path.exists(full_path):
                try:
                    # 处理只读文件的删除
                    def remove_readonly(func, path, excinfo):
                        os.chmod(path, stat.S_IWRITE)
                        func(path)
                    shutil.rmtree(full_path, onerror=remove_readonly)
                except:
                    pass

        # 11. 成功处理
        if create_success:
            save_history_config(project_city, base_path, sub_folder_config["custom_subfolders"])
            if messagebox.askyesno("创建成功", f"创建完成！\n{full_path}\n\n是否打开文件夹？"):
                os.startfile(full_path)
            city_input.delete(0, tk.END)
            name_input.delete(0, tk.END)
            city_input.focus_set()
    finally:
        create_btn.config(state=tk.NORMAL, bg="#2d78f4")

# ===================== UI搭建 =====================
adapt_high_dpi()
sub_folder_config = load_history_config()

main_window = tk.Tk()
main_window.title("装修项目文件夹创建工具 V3.2（终极稳定版）")
main_window.geometry("680x360")
main_window.resizable(False, False)

# 全局样式
main_font = ("微软雅黑", 12)
small_font = ("微软雅黑", 10)
padding = {"padx": 20, "pady": 10}

# 1. 日期行
tk.Label(main_window, text="创建日期：", font=main_font).grid(row=0, column=0, sticky="e", **padding)
date_input = tk.Entry(main_window, font=main_font, width=20)
date_input.grid(row=0, column=1, sticky="w", **padding)
now = datetime.now()
date_input.insert(0, f"{now.year}年 {now.month}月{now.day}日")

# 2. 城市行
tk.Label(main_window, text="项目城市：", font=main_font).grid(row=1, column=0, sticky="e", **padding)
city_input = tk.Entry(main_window, font=main_font, width=35)
city_input.grid(row=1, column=1, columnspan=2, sticky="w", **padding)
city_input.insert(0, sub_folder_config.get("last_city", ""))

# 3. 名称行
tk.Label(main_window, text="项目名称：", font=main_font).grid(row=2, column=0, sticky="e", **padding)
name_input = tk.Entry(main_window, font=main_font, width=35)
name_input.grid(row=2, column=1, columnspan=2, sticky="w", **padding)

# 4. 路径行（失焦校验）
def validate_path(event):
    path = path_input.get().strip()
    if path and not os.path.isdir(path):
        messagebox.showwarning("路径警告", "路径不存在/无权限，请重新选择")
        path_input.focus_set()

tk.Label(main_window, text="生成路径：", font=main_font).grid(row=3, column=0, sticky="e", **padding)
path_input = tk.Entry(main_window, font=main_font, width=30)
path_input.grid(row=3, column=1, sticky="w", **padding)
path_input.bind("<FocusOut>", validate_path)
tk.Button(main_window, text="选择路径", font=small_font, command=select_save_path).grid(row=3, column=2, sticky="w", padx=(0,20))

# 默认路径
default_path = sub_folder_config.get("last_path", "")
if not default_path or not os.path.isdir(default_path):
    default_path = os.path.join(os.path.expanduser("~"), "Desktop")
path_input.insert(0, default_path)
path_input.xview_moveto(1)

# 5. 按钮行
button_frame = tk.Frame(main_window)
button_frame.grid(row=4, column=0, columnspan=3, pady=20)

create_btn = tk.Button(
    button_frame,
    text="一键创建项目文件夹",
    font=("微软雅黑", 13, "bold"),
    bg="#2d78f4",
    fg="white",
    width=22,
    relief="flat",
    command=create_project_folder
)
create_btn.pack(side="left", padx=10)

setting_btn = tk.Button(
    button_frame,
    text="自定义子文件夹",
    font=main_font,
    width=15,
    command=open_subfolder_settings
)
setting_btn.pack(side="left", padx=10)

# 快捷键+关闭保存
main_window.bind("<Return>", create_project_folder)
def on_close():
    save_history_config(city_input.get().strip(), path_input.get().strip(), sub_folder_config.get("custom_subfolders", ",".join(DEFAULT_SUB_FOLDERS)))
    main_window.destroy()
main_window.protocol("WM_DELETE_WINDOW", on_close)

city_input.focus_set()
main_window.mainloop()
