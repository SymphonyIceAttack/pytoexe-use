import tkinter as tk
from tkinter import ttk, messagebox
import os
import subprocess
import ctypes
from ctypes import wintypes
import json
import shutil
import re

# 尝试导入现代 Windows UI 库
try:
    import sv_ttk
    HAS_SV_TTK = True
except ImportError:
    HAS_SV_TTK = False

from PIL import Image, ImageTk, ImageWin

# ================= 核心逻辑：API与备份 (与上版保持一致) =================
# ... (省略底层常量定义，保持紧凑) ...
SHGFI_ICON = 0x000000100
SHGFI_SMALLICON = 0x000000001
SHGFI_USEFILEATTRIBUTES = 0x000000010

class SHFILEINFOW(ctypes.Structure):
    _fields_ = [
        ("hIcon", wintypes.HANDLE),
        ("iIcon", ctypes.c_int),
        ("dwAttributes", wintypes.DWORD),
        ("szDisplayName", wintypes.WCHAR * wintypes.MAX_PATH),
        ("szTypeName", wintypes.WCHAR * 80)
    ]

SHGetFileInfoW = ctypes.windll.shell32.SHGetFileInfoW
DestroyIcon = ctypes.windll.user32.DestroyIcon
icon_cache = {}

def get_native_icon_image(filepath):
    ext = os.path.splitext(filepath)[1].lower()
    if ext in icon_cache: return icon_cache[ext]
    sfi = SHFILEINFOW()
    flags = SHGFI_ICON | SHGFI_SMALLICON
    if not os.path.exists(filepath): flags |= SHGFI_USEFILEATTRIBUTES
    res = SHGetFileInfoW(filepath, 0x80, ctypes.byref(sfi), ctypes.sizeof(sfi), flags)
    tk_image = None
    if sfi.hIcon:
        try:
            pil_image = ImageWin.from_handle(sfi.hIcon).convert("RGBA")
            tk_image = ImageTk.PhotoImage(pil_image)
            if ext and not os.path.isdir(filepath): icon_cache[ext] = tk_image
        except Exception: pass
        finally: DestroyIcon(sfi.hIcon)
    return tk_image

class BackupManager:
    def __init__(self):
        self.appdata_path = os.path.join(os.environ['APPDATA'], 'DesktopCleanerApp')
        self.backup_dir = os.path.join(self.appdata_path, 'Backups')
        self.registry_file = os.path.join(self.appdata_path, 'backup_registry.json')
        os.makedirs(self.backup_dir, exist_ok=True)
        self.registry = self.load_registry()

    def load_registry(self):
        if os.path.exists(self.registry_file):
            try:
                with open(self.registry_file, 'r', encoding='utf-8') as f: return json.load(f)
            except: pass
        return {}

    def save_registry(self):
        with open(self.registry_file, 'w', encoding='utf-8') as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)

    def backup_file(self, source_path):
        if not os.path.exists(source_path) or os.path.isdir(source_path): return
        safe_filename = re.sub(r'[\\/:*?"<>|]', '_', source_path.replace(':','_'))
        backup_path = os.path.join(self.backup_dir, safe_filename)
        try:
            shutil.copy2(source_path, backup_path)
            self.registry[source_path] = backup_path
            self.save_registry()
        except: pass

    def clean_unused_backups(self, current_whitelist):
        whitelisted_paths = set(current_whitelist)
        for path in list(self.registry.keys()):
            if path not in whitelisted_paths:
                backup_file = self.registry.get(path)
                if backup_file and os.path.exists(backup_file):
                    try: os.remove(backup_file)
                    except: pass
                del self.registry[path]
        self.save_registry()

    def generate_restore_script_block(self):
        if not self.registry: return ""
        registry_json_ps = self.registry_file.replace("'", "''")
        return f"""
Write-Output "检查防误删机制..."
if (Test-Path '{registry_json_ps}') {{
    $registry = Get-Content '{registry_json_ps}' -Encoding UTF8 | ConvertFrom-Json
    foreach ($sourcePath in $registry.PSObject.Properties.Name) {{
        $backupPath = $registry.$sourcePath
        if ((-not (Test-Path $sourcePath)) -and (Test-Path $backupPath)) {{
            $parentDir = Split-Path $sourcePath -Parent
            if (-not (Test-Path $parentDir)) {{ New-Item -Path $parentDir -ItemType Directory -Force }}
            Copy-Item -Path $backupPath -Destination $sourcePath -Force
        }}
    }}
}}
"""

def get_desktop_paths():
    paths = []
    for csidl in [16, 25]:
        path_buf = ctypes.create_unicode_buffer(wintypes.MAX_PATH)
        ctypes.windll.shell32.SHGetFolderPathW(0, csidl, 0, 0, path_buf)
        if path_buf.value: paths.append(path_buf.value)
    return paths

def get_task_info(task_name="AutoDesktopCleaner"):
    try:
        result = subprocess.run(f'schtasks /query /tn "{task_name}" /fo LIST /v', 
                                shell=True, capture_output=True, text=True, encoding='gbk')
        if result.returncode != 0: return None
        info = {}
        for line in result.stdout.split('\n'):
            if ":" in line:
                key, _, val = line.partition(":")
                info[key.strip()] = val.strip()
        return info
    except: return None


# ================= 全新现代 GUI 界面 =================

class DesktopCleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("桌面清理管家")
        self.root.geometry("650x700")
        
        # 应用现代主题
        if HAS_SV_TTK:
            sv_ttk.set_theme("light")
        else:
            style = ttk.Style()
            if 'vista' in style.theme_names(): style.theme_use('vista')

        self.backup_mgr = BackupManager()
        self.icon_folder = get_native_icon_image(os.environ['WINDIR'])
        
        self.setup_ui()
        self.refresh_task_status()

    def setup_ui(self):
        # 1. 顶部标题区域 (去除了大块背景色，改用干净的留白和现代字体)
        header = ttk.Frame(self.root, padding=(25, 20, 25, 10))
        header.pack(fill=tk.X)
        ttk.Label(header, text="桌面清理管家", font=("Segoe UI", 20, "bold")).pack(side=tk.LEFT)
        ttk.Label(header, text="v5.1", font=("Segoe UI", 10), foreground="#888888").pack(side=tk.LEFT, padx=10, pady=(10,0))

        # 2. 选项卡容器
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        self.tab_setup = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_setup, text=" 保护名单设置 ")
        self.setup_tab_setup()

        self.tab_manage = ttk.Frame(self.notebook, padding=15)
        self.notebook.add(self.tab_manage, text=" 系统状态管理 ")
        self.setup_tab_manage()

    def setup_tab_setup(self):
        # 提示文案
        ttk.Label(self.tab_setup, text="勾选的文件将被安全保留，并自动享有【防误删恢复】保护。", 
                  font=("Segoe UI", 10), foreground="#666666").pack(anchor="w", pady=(0, 10))
        
        # 顶部工具栏 (全选/刷新)
        toolbar = ttk.Frame(self.tab_setup)
        toolbar.pack(fill=tk.X, pady=(0, 5))
        ttk.Button(toolbar, text="全选", command=self.tree_set_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="清除选择", command=self.tree_set_none).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="🔄 重新扫描", command=self.load_items_to_tree).pack(side=tk.RIGHT)

        # 核心：无边框现代树形列表
        tree_frame = ttk.Frame(self.tab_setup)
        tree_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.tree = ttk.Treeview(tree_frame, columns=('Path'), show='tree', selectmode='extended')
        v_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=v_scroll.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        v_scroll.pack(side="right", fill="y")

        # 底部控制区 (左右布局，更具现代感)
        bottom_frame = ttk.Frame(self.tab_setup, padding=(0, 15, 0, 0))
        bottom_frame.pack(fill=tk.X)
        
        # 左侧：时间选择
        time_frame = ttk.Frame(bottom_frame)
        time_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.hour_var = tk.StringVar(value="18")
        self.min_var = tk.StringVar(value="00")
        
        ttk.Label(time_frame, text="每日自动清理时间:", font=("Segoe UI", 10)).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Spinbox(time_frame, from_=0, to=23, textvariable=self.hour_var, width=3, font=("Segoe UI", 11)).pack(side=tk.LEFT)
        ttk.Label(time_frame, text=":", font=("Segoe UI", 12, "bold")).pack(side=tk.LEFT, padx=3)
        ttk.Spinbox(time_frame, from_=0, to=59, textvariable=self.min_var, width=3, font=("Segoe UI", 11)).pack(side=tk.LEFT)

        # 右侧：保存按钮 (使用 Accent 强调色)
        btn_style = "Accent.TButton" if HAS_SV_TTK else "TButton"
        ttk.Button(bottom_frame, text="保存并启用保护", style=btn_style, command=self.save_and_apply).pack(side=tk.RIGHT)

        self.load_items_to_tree()

    def setup_tab_manage(self):
        # 居中对齐的状态展示页
        container = ttk.Frame(self.tab_manage, padding=40)
        container.pack(fill=tk.BOTH, expand=True)

        self.status_icon = ttk.Label(container, text="", font=("Segoe UI Emoji", 50))
        self.status_icon.pack(pady=(20, 10))

        self.status_text = ttk.Label(container, text="", font=("Segoe UI", 18, "bold"))
        self.status_text.pack(pady=5)

        self.detail_text = ttk.Label(container, text="", font=("Segoe UI", 11), foreground="#666666", justify="center")
        self.detail_text.pack(pady=10)

        # 停用按钮
        self.btn_delete = ttk.Button(container, text="🛑 停用并彻底删除计划", command=self.delete_task, state=tk.DISABLED)
        self.btn_delete.pack(pady=(30, 10))
        
        ttk.Button(container, text="刷新状态", command=self.refresh_task_status).pack()

    # ================= 业务逻辑 =================

    def load_items_to_tree(self):
        for item in self.tree.get_children(): self.tree.delete(item)
        
        # 核心修复：创建一个字典来持久化存放当前树中用到的所有图片对象，防止垃圾回收
        self.tree_keep_alive = {} 

        # 辅助函数：安全地插入图片
        def safe_insert(parent, index, text, img_obj, values=()):
            kwargs = {"text": text, "open": True}
            if img_obj:
                kwargs["image"] = img_obj
                # 将图片对象 ID 作为键存入字典，确保持有引用
                self.tree_keep_alive[str(img_obj)] = img_obj
            if values:
                kwargs["values"] = values
            return self.tree.insert(parent, index, **kwargs)

        # 插入根节点
        root_personal = safe_insert('', 'end', " 个人桌面 (您的专属文件)", self.icon_folder)
        root_public = safe_insert('', 'end', " 公共桌面 (软件全局快捷方式)", self.icon_folder)
        
        existing_whitelist = self.backup_mgr.registry.keys()
        
        for desktop_path in get_desktop_paths():
            is_public = "Public" in desktop_path
            parent = root_public if is_public else root_personal
            
            if not os.path.exists(desktop_path): continue
            try:
                files = sorted(os.listdir(desktop_path), key=lambda s: s.lower())
                for f in files:
                    if f.lower() == "desktop.ini": continue
                    full_path = os.path.join(desktop_path, f)
                    is_dir = os.path.isdir(full_path)
                    
                    img = self.icon_folder if is_dir else get_native_icon_image(full_path)
                    
                    # 使用安全插入
                    item_id = safe_insert(parent, 'end', f" {f}", img, values=(full_path,))
                    
                    # 只有在初次加载且没有保存过名单时，或该路径在旧名单中时才勾选
                    if not existing_whitelist or full_path in existing_whitelist:
                        self.tree.selection_add(item_id)
            except Exception as e:
                print(f"扫描出错: {e}")
                
    def tree_set_all(self):
        for root_id in self.tree.get_children():
            for child_id in self.tree.get_children(root_id):
                self.tree.selection_add(child_id)

    def tree_set_none(self):
        for root_id in self.tree.get_children():
            for child_id in self.tree.get_children(root_id):
                self.tree.selection_remove(child_id)

    def get_tree_whitelist(self):
        keep_paths = []
        for root_id in self.tree.get_children():
            for child_id in self.tree.get_children(root_id):
                if child_id in self.tree.selection():
                    keep_paths.append(self.tree.item(child_id, 'values')[0])
        return keep_paths

    def refresh_task_status(self):
        info = get_task_info()
        if info:
            self.status_icon.config(text="✅", foreground="#107c10")
            self.status_text.config(text="系统保护中", foreground="#107c10")
            time_val = info.get("下次运行时间", "未知")
            self.detail_text.config(text=f"每天 {self.hour_var.get()}:{self.min_var.get()} 执行清理\n下次自动检查: {time_val}")
            self.btn_delete.config(state=tk.NORMAL)
        else:
            self.status_icon.config(text="💤", foreground="#888888")
            self.status_text.config(text="自动清理未开启", foreground="#333333")
            self.detail_text.config(text="前往“保护名单设置”配置并保存以启用自动清理。")
            self.btn_delete.config(state=tk.DISABLED)

    def save_and_apply(self):
        if get_task_info() and not messagebox.askyesno("确认修改", "系统中已存在清理计划，是否覆盖？"):
            return

        try:
            whitelist_paths = self.get_tree_whitelist()
            keep_names = [os.path.basename(p) for p in whitelist_paths]
            
            self.backup_mgr.clean_unused_backups(whitelist_paths)
            for path in whitelist_paths: self.backup_mgr.backup_file(path)
            
            restore_block = self.backup_mgr.generate_restore_script_block()
            keep_names_ps = ",\n".join([f'"{name}"' for name in keep_names])
            desktop_paths_ps = ",\n".join([f'"{p}"' for p in get_desktop_paths()])
            
            ps_content = f"""
$keepNamesList = @({keep_names_ps})
$desktopFolders = @({desktop_paths_ps})
{restore_block}
foreach ($path in $desktopFolders) {{
    if (Test-Path $path) {{
        Get-ChildItem -Path $path -Exclude "desktop.ini" | Where-Object {{ 
            $keepNamesList -notcontains $_.Name 
        }} | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    }}
}}
"""
            ps_file = os.path.join(self.backup_mgr.appdata_path, 'clean_desktop.ps1')
            with open(ps_file, 'w', encoding='utf-8') as f: f.write(ps_content)

            run_time = f"{int(self.hour_var.get()):02d}:{int(self.min_var.get()):02d}"
            cmd = f'schtasks /create /tn "AutoDesktopCleaner" /tr "powershell.exe -WindowStyle Hidden -ExecutionPolicy Bypass -File \\"{ps_file}\\"" /sc daily /st {run_time} /rl HIGHEST /f'
            
            if subprocess.run(cmd, shell=True, capture_output=True).returncode == 0:
                messagebox.showinfo("成功", f"设置已保存！\n\n系统每天 {run_time} 自动打扫桌面。")
                self.refresh_task_status()
                self.notebook.select(self.tab_manage)
            else:
                raise Exception("权限被拒绝")
        except Exception as e:
            messagebox.showerror("失败", f"无法写入系统任务，请尝试【以管理员身份运行】。\n\n详情: {e}")

    def delete_task(self):
        if messagebox.askyesno("停用确认", "确定要停用并删除该自动清理任务吗？"):
            if subprocess.run('schtasks /delete /tn "AutoDesktopCleaner" /f', shell=True, capture_output=True).returncode == 0:
                if messagebox.askyesno("清理备份", "是否同时删除 AppData 中的文件备份数据？"):
                     try:
                         shutil.rmtree(self.backup_mgr.backup_dir)
                         if os.path.exists(self.backup_mgr.registry_file): os.remove(self.backup_mgr.registry_file)
                         self.backup_mgr = BackupManager()
                     except: pass
                self.refresh_task_status()
                self.load_items_to_tree()
            else:
                messagebox.showerror("错误", "停用失败。")

if __name__ == "__main__":
    root = tk.Tk()
    app = DesktopCleanerApp(root)
    root.mainloop()