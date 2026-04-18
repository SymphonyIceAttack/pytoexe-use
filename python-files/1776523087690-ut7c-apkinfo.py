import os
import json
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import threading
import queue

class APKManagerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("APK管理工具")
        self.root.geometry("1000x700")
        
        # 数据存储
        self.app_data = {"database": {"lastScan": "", "files": {}}}
        self.current_file_path = None
        
        # 创建主框架
        self.create_widgets()
        self.load_data()
        
    def create_widgets(self):
        # 主容器
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 按钮区域
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.scan_button = ttk.Button(button_frame, text="扫描APK文件", command=self.start_scan)
        self.scan_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 分割窗口
        paned_window = ttk.PanedWindow(main_frame, orient=tk.HORIZONTAL)
        paned_window.pack(fill=tk.BOTH, expand=True)
        
        # 左侧文件树
        left_frame = ttk.Frame(paned_window)
        paned_window.add(left_frame, weight=1)
        
        left_label = ttk.Label(left_frame, text="文件目录")
        left_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 创建Treeview用于显示文件树
        self.tree = ttk.Treeview(left_frame, columns=("path",), show="tree")
        self.tree.heading("#0", text="文件")
        self.tree.column("#0", width=300)
        
        # 添加滚动条
        tree_scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.tree.bind("<<TreeviewSelect>>", self.on_tree_select)
        
        # 右侧信息面板
        right_frame = ttk.Frame(paned_window)
        paned_window.add(right_frame, weight=2)
        
        right_label = ttk.Label(right_frame, text="APK信息预览")
        right_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 信息编辑区域
        self.info_frame = ttk.Frame(right_frame)
        self.info_frame.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def load_data(self):
        """加载appinfo.json文件"""
        try:
            if os.path.exists("appinfo.json"):
                with open("appinfo.json", 'r', encoding='utf-8') as f:
                    self.app_data = json.load(f)
            else:
                # 创建默认数据结构
                self.app_data = {"database": {"lastScan": "", "files": {}}}
            self.refresh_tree()
        except Exception as e:
            messagebox.showerror("错误", f"加载数据失败: {str(e)}")
    
    def save_data(self):
        """保存数据到appinfo.json"""
        try:
            with open("appinfo.json", 'w', encoding='utf-8') as f:
                json.dump(self.app_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            messagebox.showerror("错误", f"保存数据失败: {str(e)}")
    
    def scan_apks(self):
        """扫描APK文件"""
        self.status_var.set("正在扫描APK文件...")
        
        # 获取当前目录及子目录下的所有APK文件
        current_dir = "."
        scanned_files = {}
        
        for root, dirs, files in os.walk(current_dir):
            for file in files:
                if file.lower().endswith('.apk'):
                    full_path = os.path.join(root, file).replace('\\', '/')
                    
                    # 获取文件信息
                    stat = os.stat(full_path)
                    file_info = {
                        "path": full_path,
                        "displayName": file[:-4],  # 移除.apk扩展名
                        "packageName": "",
                        "versionName": "",
                        "versionCode": 0,
                        "size": stat.st_size,
                        "lastModified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        "exists": True,
                        "isNew": False
                    }
                    
                    scanned_files[full_path] = file_info
        
        # 检查哪些文件已不存在
        existing_files = self.app_data["database"]["files"].copy()
        for path in existing_files:
            if path not in scanned_files:
                # 文件已删除但仍保留记录
                existing_files[path]["exists"] = False
        
        # 合并现有文件和新扫描的文件
        for path, info in scanned_files.items():
            if path in existing_files:
                # 文件已存在，保留原有信息但更新存在状态
                existing_files[path]["exists"] = True
                existing_files[path]["isNew"] = False  # 不再是新文件
            else:
                # 新文件
                info["isNew"] = True
                existing_files[path] = info
        
        # 更新数据
        self.app_data["database"]["files"] = existing_files
        self.app_data["database"]["lastScan"] = datetime.now().isoformat()
        
        # 保存并刷新界面
        self.save_data()
        self.refresh_tree()
        
        self.status_var.set(f"扫描完成！找到 {len(scanned_files)} 个APK文件")
    
    def start_scan(self):
        """启动扫描线程"""
        scan_thread = threading.Thread(target=self.scan_apks, daemon=True)
        scan_thread.start()
    
    def refresh_tree(self):
        """刷新文件树"""
        # 清空现有项目
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 构建树形结构
        files_by_dir = {}
        for path, info in self.app_data["database"]["files"].items():
            directory = os.path.dirname(path) if os.path.dirname(path) else "."
            if directory not in files_by_dir:
                files_by_dir[directory] = []
            files_by_dir[directory].append((path, info))
        
        # 添加到树中
        for directory, files in files_by_dir.items():
            dir_id = self.tree.insert("", "end", text=directory, values=(directory,), open=True)
            for file_path, file_info in files:
                file_name = os.path.basename(file_path)
                # 根据文件状态设置标签
                if not file_info["exists"]:
                    tags = ("missing",)
                elif file_info["isNew"]:
                    tags = ("new",)
                else:
                    tags = ()
                
                self.tree.insert(dir_id, "end", text=file_name, values=(file_path,), tags=tags)
        
        # 配置样式
        self.tree.tag_configure("missing", foreground="red")
        self.tree.tag_configure("new", foreground="green")
    
    def on_tree_select(self, event):
        """处理树形控件选择事件"""
        selection = self.tree.selection()
        if selection:
            item = selection[0]
            if self.tree.item(item)["values"]:  # 确保是文件而不是目录
                file_path = self.tree.item(item)["values"][0]
                self.current_file_path = file_path
                self.show_file_info(file_path)
    
    def show_file_info(self, file_path):
        """显示文件信息"""
        # 清空现有控件
        for widget in self.info_frame.winfo_children():
            widget.destroy()
        
        if file_path not in self.app_data["database"]["files"]:
            return
        
        file_info = self.app_data["database"]["files"][file_path]
        
        # 创建信息编辑表单
        fields = [
            ("displayName", "显示名称"),
            ("packageName", "包名"),
            ("versionName", "版本名"),
            ("versionCode", "版本号"),
            ("size", "文件大小(字节)"),
            ("lastModified", "最后修改时间"),
            ("exists", "文件存在"),
            ("isNew", "是否新文件")
        ]
        
        for i, (key, label) in enumerate(fields):
            ttk.Label(self.info_frame, text=label).grid(row=i, column=0, sticky=tk.W, padx=(0, 10), pady=2)
            
            if key in ["exists", "isNew"]:
                var = tk.BooleanVar(value=file_info[key])
                checkbox = ttk.Checkbutton(
                    self.info_frame, 
                    variable=var,
                    command=lambda k=key, v=var: self.update_file_info(k, v.get())
                )
                checkbox.grid(row=i, column=1, sticky=tk.W, pady=2)
            else:
                var = tk.StringVar(value=str(file_info[key]))
                entry = ttk.Entry(self.info_frame, textvariable=var, width=50)
                entry.grid(row=i, column=1, sticky=tk.EW, pady=2)
                
                # 绑定失去焦点事件来保存更改
                entry.bind("<FocusOut>", lambda e, k=key, v=var: self.update_file_info(k, v.get()))
        
        # 配置列权重以使输入框可以拉伸
        self.info_frame.columnconfigure(1, weight=1)
    
    def update_file_info(self, key, value):
        """更新文件信息"""
        if self.current_file_path and self.current_file_path in self.app_data["database"]["files"]:
            # 尝试转换数值类型
            if key in ["versionCode", "size"]:
                try:
                    value = int(value)
                except ValueError:
                    pass  # 保持原值
            
            self.app_data["database"]["files"][self.current_file_path][key] = value
            self.save_data()

if __name__ == "__main__":
    root = tk.Tk()
    app = APKManagerApp(root)
    root.mainloop()