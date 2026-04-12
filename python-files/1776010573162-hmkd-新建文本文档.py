import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
import sys
import yaml
from pathlib import Path

class WanxiangConfigGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("万象拼音配置工具")
        self.root.geometry("550x480")
        self.root.resizable(False, False)
        
        # 获取默认的 Rime 用户文件夹路径
        self.default_path = self.get_default_rime_path()
        self.config_path = tk.StringVar(value=self.default_path)
        self.page_size = tk.IntVar(value=9)
        self.up_key = tk.StringVar(value="comma")
        self.down_key = tk.StringVar(value="period")
        
        self.create_widgets()
        self.auto_load_config()
    
    def get_default_rime_path(self):
        """根据操作系统返回默认的 Rime 用户文件夹路径"""
        if sys.platform == "win32":
            return os.path.join(os.environ.get("APPDATA", ""), "Rime")
        elif sys.platform == "darwin":
            return os.path.join(os.environ.get("HOME", ""), "Library", "Rime")
        else:
            return os.path.join(os.environ.get("HOME", ""), ".config", "rime")
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 配置文件路径选择
        ttk.Label(main_frame, text="Rime 用户文件夹路径：", font=("", 10, "bold")).grid(
            row=0, column=0, sticky=tk.W, pady=(0, 5))
        
        path_frame = ttk.Frame(main_frame)
        path_frame.grid(row=1, column=0, columnspan=2, sticky=tk.EW, pady=(0, 15))
        ttk.Entry(path_frame, textvariable=self.config_path, width=50).pack(side=tk.LEFT, fill=tk.X, expand=True)
        ttk.Button(path_frame, text="浏览", command=self.browse_path, width=8).pack(side=tk.RIGHT, padx=(5, 0))
        
        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # 候选词数量配置
        ttk.Label(main_frame, text="候选词数量", font=("", 11, "bold")).grid(
            row=3, column=0, sticky=tk.W, pady=(0, 10))
        
        size_frame = ttk.Frame(main_frame)
        size_frame.grid(row=4, column=0, columnspan=2, sticky=tk.W, pady=(0, 15))
        ttk.Label(size_frame, text="每页显示：").pack(side=tk.LEFT)
        ttk.Spinbox(size_frame, from_=5, to=10, width=5, textvariable=self.page_size).pack(side=tk.LEFT, padx=5)
        ttk.Label(size_frame, text="个候选词").pack(side=tk.LEFT)
        
        # 分隔线
        ttk.Separator(main_frame, orient="horizontal").grid(
            row=5, column=0, columnspan=2, sticky=tk.EW, pady=10)
        
        # 翻页按键配置
        ttk.Label(main_frame, text="翻页按键配置", font=("", 11, "bold")).grid(
            row=6, column=0, sticky=tk.W, pady=(0, 10))
        
        # 上翻页
        up_frame = ttk.Frame(main_frame)
        up_frame.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(up_frame, text="上翻页按键：").pack(side=tk.LEFT)
        up_combo = ttk.Combobox(up_frame, textvariable=self.up_key, width=12, state="readonly")
        up_combo["values"] = ["comma", "period", "minus", "equal", "bracketleft", "bracketright"]
        up_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(up_frame, text="(comma = 逗号 , )", font=("", 9)).pack(side=tk.LEFT, padx=5)
        
        # 下翻页
        down_frame = ttk.Frame(main_frame)
        down_frame.grid(row=8, column=0, columnspan=2, sticky=tk.W, pady=5)
        ttk.Label(down_frame, text="下翻页按键：").pack(side=tk.LEFT)
        down_combo = ttk.Combobox(down_frame, textvariable=self.down_key, width=12, state="readonly")
        down_combo["values"] = ["comma", "period", "minus", "equal", "bracketleft", "bracketright"]
        down_combo.pack(side=tk.LEFT, padx=5)
        ttk.Label(down_frame, text="(period = 句号 . )", font=("", 9)).pack(side=tk.LEFT, padx=5)
        
        # 常用组合
        preset_frame = ttk.LabelFrame(main_frame, text="快捷预设", padding="10")
        preset_frame.grid(row=9, column=0, columnspan=2, sticky=tk.W, pady=15)
        ttk.Button(preset_frame, text="逗号(,)上翻 · 句号(.)下翻", 
                   command=lambda: self.set_preset("comma", "period")).grid(row=0, column=0, padx=5)
        ttk.Button(preset_frame, text="减号(-)上翻 · 等号(=)下翻", 
                   command=lambda: self.set_preset("minus", "equal")).grid(row=0, column=1, padx=5)
        ttk.Button(preset_frame, text="左括号([)上翻 · 右括号(])下翻", 
                   command=lambda: self.set_preset("bracketleft", "bracketright")).grid(row=0, column=2, padx=5)
        
        # 操作按钮
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=10, column=0, columnspan=2, pady=20)
        ttk.Button(btn_frame, text="读取当前配置", command=self.load_config, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="保存配置", command=self.save_config, width=14).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="查看配置内容", command=self.preview_config, width=14).pack(side=tk.LEFT, padx=5)
        
        # 说明
        ttk.Label(main_frame, text="说明：修改保存后，需在输入法状态栏右键点击「重新部署」生效。", 
                  font=("", 9), foreground="gray").grid(row=11, column=0, columnspan=2, pady=(10, 0))
        
        main_frame.columnconfigure(0, weight=1)
    
    def set_preset(self, up_key, down_key):
        self.up_key.set(up_key)
        self.down_key.set(down_key)
    
    def browse_path(self):
        path = filedialog.askdirectory(title="选择 Rime 用户文件夹", initialdir=self.config_path.get())
        if path:
            self.config_path.set(path)
            self.auto_load_config()
    
    def auto_load_config(self):
        """自动尝试加载配置"""
        config_file = os.path.join(self.config_path.get(), "default.custom.yaml")
        if os.path.exists(config_file):
            self.load_config()
    
    def load_config(self):
        config_file = os.path.join(self.config_path.get(), "default.custom.yaml")
        if not os.path.exists(config_file):
            messagebox.showwarning("文件不存在", f"配置文件不存在：\n{config_file}\n\n将使用默认设置。")
            return
        
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            
            patch_data = data.get("patch", {})
            
            # 读取候选词数量
            if "menu/page_size" in patch_data:
                self.page_size.set(patch_data["menu/page_size"])
            elif "menu" in patch_data and isinstance(patch_data["menu"], dict):
                if "page_size" in patch_data["menu"]:
                    self.page_size.set(patch_data["menu"]["page_size"])
            
            # 读取翻页按键
            bindings = []
            if "key_binder/bindings" in patch_data:
                bindings = patch_data["key_binder/bindings"]
            elif "key_binder" in patch_data and isinstance(patch_data["key_binder"], dict):
                bindings = patch_data["key_binder"].get("bindings", [])
            
            for binding in bindings:
                if binding.get("send") == "Page_Up":
                    self.up_key.set(binding.get("accept", "comma"))
                elif binding.get("send") == "Page_Down":
                    self.down_key.set(binding.get("accept", "period"))
            
            messagebox.showinfo("成功", "配置读取成功！")
        except Exception as e:
            messagebox.showerror("错误", f"读取配置失败：\n{str(e)}")
    
    def save_config(self):
        config_file = os.path.join(self.config_path.get(), "default.custom.yaml")
        
        # 读取现有配置，保留其他用户配置
        existing_data = {}
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    existing_data = yaml.safe_load(f) or {}
            except Exception:
                pass
        
        patch_data = existing_data.get("patch", {})
        
        # 更新候选词数量（使用路径式写法，避免覆盖 menu 下的其他设置）
        patch_data["menu/page_size"] = self.page_size.get()
        
        # 更新翻页按键
        patch_data["key_binder/bindings/+"] = [
            {"when": "has_menu", "accept": self.up_key.get(), "send": "Page_Up"},
            {"when": "has_menu", "accept": self.down_key.get(), "send": "Page_Down"},
        ]
        
        # 构建最终配置
        final_data = existing_data.copy()
        final_data["patch"] = patch_data
        
        try:
            with open(config_file, "w", encoding="utf-8") as f:
                yaml.dump(final_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
            messagebox.showinfo("成功", f"配置已保存到：\n{config_file}\n\n请在输入法状态栏右键点击「重新部署」生效。")
        except Exception as e:
            messagebox.showerror("错误", f"保存配置失败：\n{str(e)}")
    
    def preview_config(self):
        """预览将要生成的配置内容"""
        config_file = os.path.join(self.config_path.get(), "default.custom.yaml")
        preview = f"""【配置文件路径】
{config_file}

【将要写入的 patch 内容】
patch:
  # 候选词数量
  menu/page_size: {self.page_size.get()}
  # 翻页按键
  key_binder/bindings/+:
    - when: has_menu
      accept: {self.up_key.get()}
      send: Page_Up
    - when: has_menu
      accept: {self.down_key.get()}
      send: Page_Down
"""
        messagebox.showinfo("配置预览", preview)


def main():
    root = tk.Tk()
    app = WanxiangConfigGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()