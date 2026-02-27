#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Minecraft 基岩版行为包/资源包自动配置工具
用户选择存档文件夹后，自动生成 world_behavior_packs.json、world_resource_packs.json
以及对应的 manifest.json 文件，所有 UUID 随机生成并保持对应关系
"""

import os
import json
import uuid
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class MCPackConfigurator:
    def __init__(self, root):
        self.root = root
        self.root.title("Minecraft 基岩版行为包/资源包配置工具")
        self.root.geometry("600x500")
        
        # 配置样式
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        # 创建主框架
        main_frame = ttk.Frame(root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        main_frame.columnconfigure(1, weight=1)
        
        # 标题
        title_label = ttk.Label(
            main_frame,
            text="Minecraft 基岩版行为包/资源包配置工具",
            font=('Arial', 14, 'bold')
        )
        title_label.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # 路径选择部分
        path_frame = ttk.LabelFrame(main_frame, text="存档文件夹路径", padding="10")
        path_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        path_frame.columnconfigure(1, weight=1)
        
        self.path_var = tk.StringVar()
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var)
        self.path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=5)
        
        browse_button = ttk.Button(
            path_frame,
            text="浏览...",
            command=self.browse_folder
        )
        browse_button.grid(row=0, column=2, pady=5)
        
        # 包名称设置
        name_frame = ttk.LabelFrame(main_frame, text="包名称（可选）", padding="10")
        name_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 20))
        name_frame.columnconfigure(1, weight=1)
        
        ttk.Label(name_frame, text="行为包名称:").grid(row=0, column=0, sticky=tk.W)
        self.behavior_name_var = tk.StringVar(value="BEmod")
        ttk.Entry(name_frame, textvariable=self.behavior_name_var).grid(
            row=0, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=5
        )
        
        ttk.Label(name_frame, text="资源包名称:").grid(row=1, column=0, sticky=tk.W)
        self.resource_name_var = tk.StringVar(value="BEpack")
        ttk.Entry(name_frame, textvariable=self.resource_name_var).grid(
            row=1, column=1, sticky=(tk.W, tk.E), padx=(10, 10), pady=5
        )
        
        # 操作按钮
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=3, column=0, columnspan=2, pady=20)
        
        generate_button = ttk.Button(
            button_frame,
            text="生成配置文件",
            command=self.generate_config
        )
        generate_button.pack(side=tk.LEFT, padx=5)
        
        clear_button = ttk.Button(
            button_frame,
            text="清空路径",
            command=self.clear_path
        )
        clear_button.pack(side=tk.LEFT, padx=5)
        
        # 日志输出
        log_frame = ttk.LabelFrame(main_frame, text="操作日志", padding="10")
        log_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 0))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = tk.Text(log_frame, height=10, wrap=tk.WORD)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        scrollbar = ttk.Scrollbar(log_frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.grid(row=0, column=1, sticky=(tk.N, tk.S))
        self.log_text.config(yscrollcommand=scrollbar.set)
        
        main_frame.rowconfigure(4, weight=1)
        
        self.log("欢迎使用 Minecraft 基岩版配置工具！")
        self.log("请选择存档文件夹，然后点击生成配置文件。")
    
    def log(self, message):
        """添加日志信息"""
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def browse_folder(self):
        """浏览文件夹"""
        folder_path = filedialog.askdirectory(title="选择 Minecraft 基岩版存档文件夹")
        if folder_path:
            self.path_var.set(folder_path)
            self.log(f"已选择文件夹: {folder_path}")
    
    def clear_path(self):
        """清空路径"""
        self.path_var.set("")
        self.log("路径已清空")
    
    def generate_config(self):
        """生成配置文件"""
        save_path = self.path_var.get().strip()
        
        if not save_path:
            messagebox.showwarning("警告", "请先选择存档文件夹！")
            return
        
        if not os.path.exists(save_path):
            messagebox.showerror("错误", f"路径不存在: {save_path}")
            return
        
        try:
            self.log(f"开始生成配置文件...")
            self.log(f"目标路径: {save_path}")
            
            # 生成随机 UUID
            behavior_pack_uuid = str(uuid.uuid4())
            behavior_module_uuid = str(uuid.uuid4())
            resource_pack_uuid = str(uuid.uuid4())
            resource_module_uuid = str(uuid.uuid4())
            
            self.log(f"生成的 UUID:")
            self.log(f"  行为包: {behavior_pack_uuid}")
            self.log(f"  行为包模块: {behavior_module_uuid}")
            self.log(f"  资源包: {resource_pack_uuid}")
            self.log(f"  资源包模块: {resource_module_uuid}")
            
            # 创建必要的文件夹结构
            behavior_packs_dir = os.path.join(save_path, "behavior_packs", self.behavior_name_var.get())
            resource_packs_dir = os.path.join(save_path, "resource_packs", self.resource_name_var.get())
            
            os.makedirs(behavior_packs_dir, exist_ok=True)
            os.makedirs(resource_packs_dir, exist_ok=True)
            
            self.log(f"创建文件夹结构完成")
            
            # 生成 world_behavior_packs.json
            world_behavior_packs = [
                {
                    "pack_id": behavior_pack_uuid,
                    "type": "Addon",
                    "version": [1, 0, 0]
                }
            ]
            
            world_behavior_packs_path = os.path.join(save_path, "world_behavior_packs.json")
            with open(world_behavior_packs_path, 'w', encoding='utf-8') as f:
                json.dump(world_behavior_packs, f, indent='\t', ensure_ascii=False)
            
            self.log(f"已生成: world_behavior_packs.json")
            
            # 生成 world_resource_packs.json
            world_resource_packs = [
                {
                    "pack_id": resource_pack_uuid,
                    "type": "Addon",
                    "version": [1, 0, 0]
                }
            ]
            
            world_resource_packs_path = os.path.join(save_path, "world_resource_packs.json")
            with open(world_resource_packs_path, 'w', encoding='utf-8') as f:
                json.dump(world_resource_packs, f, indent='\t', ensure_ascii=False)
            
            self.log(f"已生成: world_resource_packs.json")
            
            # 生成行为包 manifest.json
            behavior_manifest = {
                "format_version": 2,
                "header": {
                    "name": self.behavior_name_var.get(),
                    "description": "行为包",
                    "uuid": behavior_pack_uuid,
                    "version": [1, 0, 0],
                    "min_engine_version": [1, 21, 50]
                },
                "modules": [
                    {
                        "type": "data",
                        "uuid": behavior_module_uuid,
                        "version": [1, 0, 0]
                    }
                ],
                "dependencies": [
                    {
                        "uuid": resource_pack_uuid,
                        "version": [1, 0, 0]
                    }
                ]
            }
            
            behavior_manifest_path = os.path.join(behavior_packs_dir, "manifest.json")
            with open(behavior_manifest_path, 'w', encoding='utf-8') as f:
                json.dump(behavior_manifest, f, indent=2, ensure_ascii=False)
            
            self.log(f"已生成: behavior_packs/{self.behavior_name_var.get()}/manifest.json")
            
            # 生成资源包 manifest.json
            resource_manifest = {
                "format_version": 2,
                "header": {
                    "name": self.resource_name_var.get(),
                    "description": "资源包",
                    "uuid": resource_pack_uuid,
                    "version": [1, 0, 0],
                    "min_engine_version": [1, 21, 50]
                },
                "modules": [
                    {
                        "type": "resources",
                        "uuid": resource_module_uuid,
                        "version": [1, 0, 0]
                    }
                ]
            }
            
            resource_manifest_path = os.path.join(resource_packs_dir, "manifest.json")
            with open(resource_manifest_path, 'w', encoding='utf-8') as f:
                json.dump(resource_manifest, f, indent=2, ensure_ascii=False)
            
            self.log(f"已生成: resource_packs/{self.resource_name_var.get()}/manifest.json")
            
            self.log("\n✓ 所有配置文件生成完成！")
            messagebox.showinfo("成功", "配置文件生成成功！")
            
        except Exception as e:
            error_msg = f"生成配置文件时出错: {str(e)}"
            self.log(f"\n✗ {error_msg}")
            messagebox.showerror("错误", error_msg)


def main():
    root = tk.Tk()
    app = MCPackConfigurator(root)
    root.mainloop()


if __name__ == "__main__":
    main()