import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import subprocess
import webbrowser
from datetime import datetime

class WindowsToolbox:
    def __init__(self, root):
        self.root = root
        self.root.title("Windows工具箱")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        

        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建标签页
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # 创建软件安装标签页
        self.software_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.software_frame, text="软件安装")
        
        # 创建系统设置标签页
        self.system_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.system_frame, text="系统设置")
        
        # 创建工具标签页
        self.tools_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tools_frame, text="实用工具")
        
        # 创建关于标签页
        self.about_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.about_frame, text="关于")
        
        # 初始化各个标签页
        self.init_software_tab()
        self.init_system_tab()
        self.init_tools_tab()
        self.init_about_tab()
        
    def init_software_tab(self):
        # 软件列表
        self.software_list = {
            "Google Chrome": {
                "url": "https://dl.google.com/chrome/install/latest/chrome_installer.exe",
                "description": "谷歌浏览器",
                "category": "浏览器"
            },
            "Mozilla Firefox": {
                "url": "https://download.mozilla.org/?product=firefox-latest&os=win64&lang=zh-CN",
                "description": "火狐浏览器",
                "category": "浏览器"
            },
            "Notepad++": {
                "url": "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.5/npp.8.6.5.Installer.x64.exe",
                "description": "代码编辑器",
                "category": "开发工具"
            },
            "Visual Studio Code": {
                "url": "https://code.visualstudio.com/sha/download?build=stable&os=win32-x64-user",
                "description": "微软代码编辑器",
                "category": "开发工具"
            },
            "7-Zip": {
                "url": "https://www.7-zip.org/a/7z2407-x64.exe",
                "description": "压缩软件",
                "category": "实用工具"
            },
            "VLC Media Player": {
                "url": "https://get.videolan.org/vlc/3.0.20/win64/vlc-3.0.20-win64.exe",
                "description": "媒体播放器",
                "category": "媒体工具"
            },
            "LibreOffice": {
                "url": "https://download.documentfoundation.org/libreoffice/stable/24.2.4/win/x86_64/LibreOffice_24.2.4_Win_x86-64.msi",
                "description": "办公软件",
                "category": "办公工具"
            },
            "Git": {
                "url": "https://github.com/git-for-windows/git/releases/download/v2.45.2.windows.1/Git-2.45.2-64-bit.exe",
                "description": "版本控制工具",
                "category": "开发工具"
            }
        }
        
        # 分类列表
        categories = list(set([sw["category"] for sw in self.software_list.values()]))
        categories.insert(0, "全部")
        
        # 创建搜索和分类框架
        search_frame = ttk.Frame(self.software_frame, padding="10")
        search_frame.pack(fill=tk.X, pady=5)
        
        # 搜索框
        ttk.Label(search_frame, text="搜索软件:").pack(side=tk.LEFT, padx=5)
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=30)
        search_entry.pack(side=tk.LEFT, padx=5)
        ttk.Button(search_frame, text="搜索", command=self.filter_software).pack(side=tk.LEFT, padx=5)
        
        # 分类下拉框
        ttk.Label(search_frame, text="分类:").pack(side=tk.LEFT, padx=5)
        self.category_var = tk.StringVar(value="全部")
        category_combobox = ttk.Combobox(search_frame, textvariable=self.category_var, values=categories, state="readonly")
        category_combobox.pack(side=tk.LEFT, padx=5)
        category_combobox.bind("<<ComboboxSelected>>", lambda e: self.filter_software())
        
        # 软件列表框架
        list_frame = ttk.Frame(self.software_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 软件列表
        self.software_tree = ttk.Treeview(list_frame, columns=("name", "description", "category"), show="headings")
        self.software_tree.heading("name", text="软件名称")
        self.software_tree.heading("description", text="描述")
        self.software_tree.heading("category", text="分类")
        self.software_tree.column("name", width=150)
        self.software_tree.column("description", width=300)
        self.software_tree.column("category", width=100)
        
        # 滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.software_tree.yview)
        self.software_tree.configure(yscroll=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.software_tree.pack(fill=tk.BOTH, expand=True)
        
        # 按钮框架
        button_frame = ttk.Frame(self.software_frame, padding="10")
        button_frame.pack(fill=tk.X, pady=5)
        
        # 安装按钮
        ttk.Button(button_frame, text="安装选中软件", command=self.install_software).pack(side=tk.LEFT, padx=5)
        
        # 刷新按钮
        ttk.Button(button_frame, text="刷新列表", command=self.load_software_list).pack(side=tk.LEFT, padx=5)
        
        # 加载软件列表
        self.load_software_list()
        
    def load_software_list(self):
        # 清空现有列表
        for item in self.software_tree.get_children():
            self.software_tree.delete(item)
        
        # 添加软件到列表
        for name, info in self.software_list.items():
            self.software_tree.insert("", tk.END, values=(name, info["description"], info["category"]))
        
    def filter_software(self):
        # 清空现有列表
        for item in self.software_tree.get_children():
            self.software_tree.delete(item)
        
        # 获取搜索关键词和分类
        search_term = self.search_var.get().lower()
        category = self.category_var.get()
        
        # 过滤并添加软件
        for name, info in self.software_list.items():
            if (search_term in name.lower() or search_term in info["description"].lower()) and \
               (category == "全部" or info["category"] == category):
                self.software_tree.insert("", tk.END, values=(name, info["description"], info["category"]))
        
    def install_software(self):
        selected_items = self.software_tree.selection()
        if not selected_items:
            messagebox.showinfo("提示", "请选择要安装的软件")
            return
        
        for item in selected_items:
            values = self.software_tree.item(item, "values")
            software_name = values[0]
            
            if software_name in self.software_list:
                info = self.software_list[software_name]
                url = info["url"]
                
                try:
                    messagebox.showinfo("开始安装", f"正在下载并安装 {software_name}...")
                    
                    # 下载文件
                    import tempfile
                    import urllib.request
                    
                    temp_dir = tempfile.gettempdir()
                    file_name = os.path.basename(url)
                    file_path = os.path.join(temp_dir, file_name)
                    
                    # 下载文件
                    urllib.request.urlretrieve(url, file_path)
                    
                    # 运行安装程序
                    subprocess.Popen([file_path])
                    
                    messagebox.showinfo("安装提示", f"{software_name} 安装程序已启动，请按照提示完成安装")
                    
                except Exception as e:
                    messagebox.showerror("安装失败", f"安装 {software_name} 时出错: {str(e)}")
        
    def init_system_tab(self):
        # 系统设置框架
        settings_frame = ttk.Frame(self.system_frame, padding="10")
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # 系统设置列表
        settings_list = [
            {"name": "显示设置", "command": self.open_display_settings},
            {"name": "声音设置", "command": self.open_sound_settings},
            {"name": "网络设置", "command": self.open_network_settings},
            {"name": "电源设置", "command": self.open_power_settings},
            {"name": "设备管理器", "command": self.open_device_manager},
            {"name": "控制面板", "command": self.open_control_panel},
            {"name": "任务管理器", "command": self.open_task_manager},
            {"name": "系统信息", "command": self.open_system_info},
            {"name": "磁盘管理", "command": self.open_disk_management},
            {"name": "服务管理", "command": self.open_services},
        ]
        
        # 创建设置按钮网格
        for i, setting in enumerate(settings_list):
            row = i // 2
            col = i % 2
            ttk.Button(settings_frame, text=setting["name"], command=setting["command"], width=20).grid(
                row=row, column=col, padx=10, pady=10, sticky="nsew"
            )
        
        # 配置网格布局
        for i in range(len(settings_list) // 2 + 1):
            settings_frame.rowconfigure(i, weight=1)
        for i in range(2):
            settings_frame.columnconfigure(i, weight=1)
        
    def open_display_settings(self):
        subprocess.run(["ms-settings:display"])
    
    def open_sound_settings(self):
        subprocess.run(["ms-settings:sound"])
    
    def open_network_settings(self):
        subprocess.run(["ms-settings:network"])
    
    def open_power_settings(self):
        subprocess.run(["ms-settings:powersleep"])
    
    def open_device_manager(self):
        subprocess.run(["devmgmt.msc"])
    
    def open_control_panel(self):
        subprocess.run(["control"])
    
    def open_task_manager(self):
        subprocess.run(["taskmgr"])
    
    def open_system_info(self):
        subprocess.run(["msinfo32"])
    
    def open_disk_management(self):
        subprocess.run(["diskmgmt.msc"])
    
    def open_services(self):
        subprocess.run(["services.msc"])
    
    def init_tools_tab(self):
        # 工具框架
        tools_frame = ttk.Frame(self.tools_frame, padding="10")
        tools_frame.pack(fill=tk.BOTH, expand=True)
        
        # 工具列表
        tools_list = [
            {"name": "清理临时文件", "command": self.clean_temp_files},
            {"name": "系统垃圾清理", "command": self.clean_system_junk},
            {"name": "检查系统更新", "command": self.check_windows_update},
            {"name": "创建系统还原点", "command": self.create_system_restore_point},
            {"name": "磁盘碎片整理", "command": self.defragment_disk},
            {"name": "网络故障诊断", "command": self.network_diagnostics},
            {"name": "系统文件检查", "command": self.sfc_scan},
            {"name": "磁盘错误检查", "command": self.chkdsk},
        ]
        
        # 创建工具按钮网格
        for i, tool in enumerate(tools_list):
            row = i // 2
            col = i % 2
            ttk.Button(tools_frame, text=tool["name"], command=tool["command"], width=25).grid(
                row=row, column=col, padx=10, pady=10, sticky="nsew"
            )
        
        # 配置网格布局
        for i in range(len(tools_list) // 2 + 1):
            tools_frame.rowconfigure(i, weight=1)
        for i in range(2):
            tools_frame.columnconfigure(i, weight=1)
        
    def clean_temp_files(self):
        try:
            # 清理临时文件夹
            temp_dir = os.environ.get("TEMP")
            if temp_dir:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        try:
                            os.remove(os.path.join(root, file))
                        except:
                            pass
                    for dir in dirs:
                        try:
                            os.rmdir(os.path.join(root, dir))
                        except:
                            pass
            messagebox.showinfo("清理完成", "临时文件清理完成")
        except Exception as e:
            messagebox.showerror("清理失败", f"清理临时文件时出错: {str(e)}")
    
    def clean_system_junk(self):
        try:
            # 运行磁盘清理
            subprocess.run(["cleanmgr", "/sagerun:1"])
        except Exception as e:
            messagebox.showerror("清理失败", f"系统垃圾清理时出错: {str(e)}")
    
    def check_windows_update(self):
        try:
            subprocess.run(["ms-settings:windowsupdate"])
        except Exception as e:
            messagebox.showerror("打开失败", f"打开Windows更新时出错: {str(e)}")
    
    def create_system_restore_point(self):
        try:
            # 创建系统还原点
            restore_name = f"Windows工具箱创建 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            subprocess.run(["wmic", "shadowcopy", "call", "create", f"Volume=C:\\", f"Description={restore_name}"])
            messagebox.showinfo("创建成功", f"系统还原点 '{restore_name}' 创建成功")
        except Exception as e:
            messagebox.showerror("创建失败", f"创建系统还原点时出错: {str(e)}")
    
    def defragment_disk(self):
        try:
            subprocess.run(["dfrgui"])
        except Exception as e:
            messagebox.showerror("打开失败", f"打开磁盘碎片整理时出错: {str(e)}")
    
    def network_diagnostics(self):
        try:
            subprocess.run(["ms-settings:network-diagnostics"])
        except Exception as e:
            messagebox.showerror("打开失败", f"打开网络诊断时出错: {str(e)}")
    
    def sfc_scan(self):
        try:
            # 运行系统文件检查
            import tempfile
            batch_file = tempfile.mktemp(".bat")
            with open(batch_file, "w") as f:
                f.write("sfc /scannow\npause")
            subprocess.Popen([batch_file], shell=True)
        except Exception as e:
            messagebox.showerror("执行失败", f"运行系统文件检查时出错: {str(e)}")
    
    def chkdsk(self):
        try:
            # 运行磁盘错误检查
            import tempfile
            batch_file = tempfile.mktemp(".bat")
            with open(batch_file, "w") as f:
                f.write("chkdsk C: /f /r\npause")
            subprocess.Popen([batch_file], shell=True)
        except Exception as e:
            messagebox.showerror("执行失败", f"运行磁盘错误检查时出错: {str(e)}")
    
    def init_about_tab(self):
        # 关于框架
        about_frame = ttk.Frame(self.about_frame, padding="20")
        about_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        ttk.Label(about_frame, text="Windows工具箱", font=("Arial", 24, "bold")).pack(pady=20)
        
        # 版本信息
        ttk.Label(about_frame, text="版本: 1.0.0", font=("Arial", 12)).pack(pady=5)
        
        # 描述
        ttk.Label(about_frame, text="一个用于Windows系统的实用工具箱，", font=("Arial", 12)).pack(pady=5)
        ttk.Label(about_frame, text="包含软件安装、系统设置和实用工具功能。", font=("Arial", 12)).pack(pady=5)
        
        # 版权信息
        ttk.Label(about_frame, text="© 2026 Windows Toolbox", font=("Arial", 10)).pack(pady=20)
        
        # 链接
        link_frame = ttk.Frame(about_frame)
        link_frame.pack(pady=10)
        
        def open_github():
            webbrowser.open("https://github.com")
        
        ttk.Button(link_frame, text="访问GitHub", command=open_github).pack(side=tk.LEFT, padx=10)
        
        def open_website():
            webbrowser.open("https://example.com")
        
        ttk.Button(link_frame, text="官方网站", command=open_website).pack(side=tk.LEFT, padx=10)

if __name__ == "__main__":
    root = tk.Tk()
    app = WindowsToolbox(root)
    root.mainloop()