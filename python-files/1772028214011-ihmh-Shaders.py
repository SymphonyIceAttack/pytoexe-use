import os
import shutil
import re
import threading
import tkinter as tk
import sys
import ctypes
from tkinter import filedialog, messagebox, scrolledtext

# ==========================================
# 核心补丁：安全隐藏控制台 (防止闪退)
# ==========================================
def hide_console_safely():
    """
    先静音输出流，再隐藏窗口。
    这是解决在线打包exe闪退的唯一代码级方案。
    """
    # 1. 定义一个“垃圾桶”，把所有日志丢进去，防止报错
    class DevNull:
        def write(self, msg): pass
        def flush(self): pass
    
    # 2. 将标准输出重定向到“垃圾桶”
    sys.stdout = DevNull()
    sys.stderr = DevNull()

    # 3. 安全隐藏窗口 (使用 ShowWindow 而不是 FreeConsole，更稳定)
    try:
        kernel32 = ctypes.WinDLL('kernel32')
        user32 = ctypes.WinDLL('user32')
        hWnd = kernel32.GetConsoleWindow()
        if hWnd:
            user32.ShowWindow(hWnd, 0) # 0 = SW_HIDE (彻底隐藏)
    except:
        pass

# 程序一启动，立即执行隐藏
hide_console_safely()

# ==========================================
# 主程序逻辑 (保持不变)
# ==========================================

class ShaderExtractorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RetroArch Shader 提取工具 v2.5 (无黑框版)")
        self.root.geometry("680x520")

        # 样式设置
        btn_font = ("Microsoft YaHei", 11, "bold")
        lbl_font = ("Microsoft YaHei", 9)
        
        # 顶部提示
        tk.Label(root, text="第一步：选择你自定义的 .slangp 预设的文件夹\n第二步：选择原始 shaders_slang 巨大根目录\n第三步：选择输出位置", 
                 justify="left", fg="#555", font=lbl_font).pack(pady=15)

        # 按钮区域
        self.btn_start = tk.Button(root, text="选择文件夹并开始提取", command=self.start_process, 
                                   font=btn_font, bg="#4CAF50", fg="white", height=2, cursor="hand2")
        self.btn_start.pack(pady=5, fill='x', padx=30)

        self.lbl_status = tk.Label(root, text="等待开始...", fg="blue", font=lbl_font)
        self.lbl_status.pack(pady=5)

        # 日志窗口
        self.log_text = scrolledtext.ScrolledText(root, state='disabled', height=18, font=("Consolas", 9))
        self.log_text.pack(padx=10, pady=5, fill='both', expand=True)

        # 内部变量
        self.presets_dir = ""
        self.source_root = ""
        self.output_dir = ""
        self.processed_files = set()
        self.total_copied = 0

    def log(self, message):
        """向界面输出日志"""
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')
        self.root.update()

    def start_process(self):
        """按钮点击事件"""
        self.presets_dir = filedialog.askdirectory(title="1/3 选择 .slangp 预设文件夹")
        if not self.presets_dir: return

        self.source_root = filedialog.askdirectory(title="2/3 选择 shaders_slang 根目录")
        if not self.source_root: return

        self.output_dir = filedialog.askdirectory(title="3/3 选择输出文件夹")
        if not self.output_dir: return

        self.btn_start.config(state='disabled', text="正在提取中...", bg="#999999")
        self.processed_files.clear()
        self.total_copied = 0
        self.log("=== 开始全能提取 ===")
        
        threading.Thread(target=self.run_extraction, daemon=True).start()

    def run_extraction(self):
        try:
            slangp_found = False
            for root, dirs, files in os.walk(self.presets_dir):
                for file in files:
                    if file.endswith(".slangp"):
                        slangp_found = True
                        preset_path = os.path.join(root, file)
                        self.log(f"--> 分析预设: {file}")
                        
                        rel_preset_path = os.path.relpath(preset_path, self.presets_dir)
                        dest_preset_path = os.path.join(self.output_dir, rel_preset_path)
                        os.makedirs(os.path.dirname(dest_preset_path), exist_ok=True)
                        shutil.copy2(preset_path, dest_preset_path)

                        self.parse_and_copy_dependencies(preset_path)

            if not slangp_found:
                self.log("[错误] 未找到 .slangp 文件！")
            else:
                self.log(f"\n=== 提取完成! 共 {self.total_copied} 个文件 ===")
                messagebox.showinfo("成功", f"提取完成！\n请查看输出目录。")

        except Exception as e:
            self.log(f"[严重错误] {str(e)}")
            messagebox.showerror("出错", str(e))
        finally:
            self.btn_start.config(state='normal', text="选择文件夹并开始提取", bg="#4CAF50")
            self.lbl_status.config(text="任务结束")

    def smart_find_file(self, ref_path, preset_dir):
        # 1. 尝试相对路径
        path_a = os.path.normpath(os.path.join(preset_dir, ref_path))
        if os.path.exists(path_a): return path_a

        # 2. 尝试去大包里找
        clean_ref = ref_path.replace("\\", "/").replace("../", "").replace("./", "")
        clean_ref_no_prefix = re.sub(r'^shaders_slang/', '', clean_ref, flags=re.IGNORECASE)

        # 尝试直接拼接
        path_b = os.path.normpath(os.path.join(self.source_root, clean_ref))
        if os.path.exists(path_b): return path_b
        
        # 尝试去前缀拼接
        path_c = os.path.normpath(os.path.join(self.source_root, clean_ref_no_prefix))
        if os.path.exists(path_c): return path_c

        # 尝试去掉第一层目录拼接
        parts = clean_ref.split("/")
        if len(parts) > 1:
            path_d = os.path.normpath(os.path.join(self.source_root, *parts[1:]))
            if os.path.exists(path_d): return path_d

        return None

    def copy_file_recursive(self, src_path):
        if not src_path: return
        abs_src = os.path.abspath(src_path)
        if abs_src in self.processed_files: return
        self.processed_files.add(abs_src)

        try:
            rel_path = os.path.relpath(abs_src, self.source_root)
            if rel_path.startswith(".."): rel_path = os.path.basename(abs_src)
        except:
            rel_path = os.path.basename(abs_src)

        dest_path = os.path.join(self.output_dir, rel_path)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        try:
            shutil.copy2(abs_src, dest_path)
            self.total_copied += 1
        except Exception:
            pass

        if src_path.lower().endswith(('.slang', '.h', '.glsl', '.inc')):
            self.scan_internal_includes(src_path)

    def scan_internal_includes(self, file_path):
        include_pattern = re.compile(r'#include\s+"([^"]+)"')
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                matches = include_pattern.findall(content)
                curr_dir = os.path.dirname(file_path)
                for include_rel in matches:
                    real_path = self.smart_find_file(include_rel, curr_dir)
                    if real_path: self.copy_file_recursive(real_path)
        except Exception:
            pass

    def parse_and_copy_dependencies(self, preset_path):
        # 匹配所有带后缀的文件引用
        path_pattern = re.compile(r'=\s*["\']([^"\']+\.(?:slang|glsl|png|jpg|jpeg|h|inc))["\']', re.IGNORECASE)
        try:
            with open(preset_path, 'r', encoding='utf-8') as f:
                for line in f:
                    match = path_pattern.search(line)
                    if match:
                        rel_ref = match.group(1)
                        real_path = self.smart_find_file(rel_ref, os.path.dirname(preset_path))
                        if real_path: self.copy_file_recursive(real_path)
                        else: self.log(f"[丢失] 找不到文件: {rel_ref}")
        except Exception:
            pass

if __name__ == "__main__":
    root = tk.Tk()
    app = ShaderExtractorApp(root)
    root.mainloop()