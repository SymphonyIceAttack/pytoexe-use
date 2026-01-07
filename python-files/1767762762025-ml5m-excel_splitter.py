#!/usr/bin/env python
# coding: utf-8

# In[1]:


"""
西部大区 - 业务支持部 - 文件分发小程序
功能:根据选定字段将Excel文件拆分为多个子文件
版本:1.0
"""

import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from pathlib import Path
import sys


class ExcelSplitterApp:
    """Excel拆分工具主类"""
    
    # 麦肯锡配色方案
    COLORS = {
        'primary': '#003A70',      # 麦肯锡深蓝
        'secondary': '#00A3E0',    # 麦肯锡亮蓝
        'accent': '#FFB81C',       # 黄色强调
        'success': '#00A878',      # 成功绿
        'bg': '#F5F7FA',           # 浅灰背景
        'white': '#FFFFFF',
        'text_dark': '#2C3E50',
        'text_light': '#6C757D',
        'border': '#E1E8ED'
    }
    
    def __init__(self, root):
        self.root = root
        self.root.title("西部大区 - 业务支持部 - 文件分发小程序")
        self.root.geometry("800x850")
        self.root.resizable(True, True)
        self.root.configure(bg=self.COLORS['bg'])
        
        # 设置窗口图标(如果有ico文件)
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        self.file_path = None
        self.df = None
        self.output_dir = None
        
        self.setup_ui()
        self.center_window()
    
    def center_window(self):
        """窗口居中显示"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def setup_ui(self):
        """设置用户界面 - 麦肯锡风格"""
        
        # 顶部区域 - 深蓝色
        header_frame = tk.Frame(self.root, bg=self.COLORS['primary'], height=90)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Logo和标题区域
        title_container = tk.Frame(header_frame, bg=self.COLORS['primary'])
        title_container.place(relx=0.5, rely=0.5, anchor='center')
        
        # 主标题
        tk.Label(title_container, 
                text="文件分发小程序", 
                font=("微软雅黑", 18, "bold"), 
                bg=self.COLORS['primary'], 
                fg=self.COLORS['white']).pack()
        
        # 副标题
        tk.Label(title_container, 
                text="西部大区 · 业务支持部", 
                font=("微软雅黑", 10, "bold"), 
                bg=self.COLORS['primary'], 
                fg=self.COLORS['white']).pack(pady=(3, 0))
        
        # 主容器 - 卡片式设计
        main_container = tk.Frame(self.root, bg=self.COLORS['bg'])
        main_container.pack(fill=tk.BOTH, expand=True, padx=30, pady=20)
        
        # 0. 快速操作区 - 启动按钮
        action_card = self.create_card(main_container, "快速操作")
        action_card.pack(fill=tk.X, pady=(0, 15))
        
        action_content = tk.Frame(action_card, bg=self.COLORS['white'])
        action_content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        button_container = tk.Frame(action_content, bg=self.COLORS['white'])
        button_container.pack(fill=tk.X, pady=10)
        
        self.split_button = tk.Button(button_container, 
                                      text="执行文件拆分", 
                                      command=self.split_file,
                                      width=30, 
                                      height=2,
                                      bg=self.COLORS['success'],
                                      fg=self.COLORS['white'],
                                      font=("微软雅黑", 12, "bold"),
                                      relief=tk.FLAT,
                                      cursor="hand2",
                                      state=tk.DISABLED,
                                      disabledforeground=self.COLORS['white'],
                                      activebackground=self.COLORS['primary'],
                                      activeforeground=self.COLORS['white'])
        self.split_button.pack()
        
        tip_label = tk.Label(action_content,
                            text="提示: 请先完成下方两个步骤后,再点击此按钮执行拆分 (文件将自动保存至源文件所在目录)",
                            bg=self.COLORS['white'],
                            fg=self.COLORS['text_light'],
                            font=("微软雅黑", 8))
        tip_label.pack(pady=(8, 0))
        
        # 1. 文件选择卡片
        file_card = self.create_card(main_container, "步骤 1: 选择Excel文件")
        file_card.pack(fill=tk.X, pady=(0, 15))
        
        file_content = tk.Frame(file_card, bg=self.COLORS['white'])
        file_content.pack(fill=tk.X, padx=20, pady=(0, 15))
        
        file_select_frame = tk.Frame(file_content, bg=self.COLORS['white'])
        file_select_frame.pack(fill=tk.X, pady=5)
        
        self.file_label = tk.Label(file_select_frame, 
                                   text="请选择要拆分的Excel文件", 
                                   bg=self.COLORS['white'],
                                   fg=self.COLORS['text_light'],
                                   relief=tk.SOLID,
                                   borderwidth=1,
                                   anchor=tk.W, 
                                   padx=15, 
                                   height=2,
                                   font=("微软雅黑", 9))
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        file_btn = tk.Button(file_select_frame, 
                            text="选择文件", 
                            command=self.select_file,
                            width=14, 
                            height=2,
                            bg=self.COLORS['secondary'],
                            fg=self.COLORS['white'],
                            font=("微软雅黑", 9, "bold"),
                            relief=tk.FLAT,
                            cursor="hand2",
                            activebackground=self.COLORS['primary'],
                            activeforeground=self.COLORS['white'])
        file_btn.pack(side=tk.RIGHT)
        
        # 2. 字段选择卡片
        field_card = self.create_card(main_container, "步骤 2: 选择拆分字段")
        field_card.pack(fill=tk.BOTH, expand=True, pady=(0, 15))
        
        field_content = tk.Frame(field_card, bg=self.COLORS['white'])
        field_content.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 15))
        
        tk.Label(field_content, 
                text="从下列字段中选择一个作为拆分依据:", 
                bg=self.COLORS['white'],
                fg=self.COLORS['text_light'],
                font=("微软雅黑", 9)).pack(anchor=tk.W, pady=(5, 8))
        
        # 列表框容器
        listbox_container = tk.Frame(field_content, 
                                     bg=self.COLORS['white'],
                                     relief=tk.SOLID,
                                     borderwidth=1)
        listbox_container.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = tk.Scrollbar(listbox_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.field_listbox = tk.Listbox(listbox_container, 
                                        height=10,
                                        font=("微软雅黑", 9),
                                        yscrollcommand=scrollbar.set,
                                        relief=tk.FLAT,
                                        borderwidth=0,
                                        selectbackground=self.COLORS['secondary'],
                                        selectforeground=self.COLORS['white'],
                                        activestyle='none')
        self.field_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.config(command=self.field_listbox.yview)
        
        # 选中提示
        select_info_frame = tk.Frame(field_content, bg=self.COLORS['white'])
        select_info_frame.pack(fill=tk.X, pady=(10, 0))
        
        tk.Label(select_info_frame, 
                text="● ", 
                bg=self.COLORS['white'],
                fg=self.COLORS['secondary'],
                font=("Arial", 12)).pack(side=tk.LEFT)
        
        self.selected_field_label = tk.Label(select_info_frame, 
                                             text="当前未选择字段", 
                                             bg=self.COLORS['white'],
                                             fg=self.COLORS['text_dark'],
                                             font=("微软雅黑", 9))
        self.selected_field_label.pack(side=tk.LEFT)
        
        self.field_listbox.bind('<<ListboxSelect>>', self.on_field_select)
        
        # 状态栏 - 简洁设计
        status_container = tk.Frame(self.root, bg=self.COLORS['white'], height=40)
        status_container.pack(side=tk.BOTTOM, fill=tk.X)
        status_container.pack_propagate(False)
        
        self.status_label = tk.Label(status_container, 
                                     text="系统就绪", 
                                     anchor=tk.W, 
                                     padx=30,
                                     bg=self.COLORS['white'],
                                     fg=self.COLORS['text_light'],
                                     font=("微软雅黑", 9))
        self.status_label.pack(fill=tk.BOTH, expand=True)
    
    def create_card(self, parent, title):
        """创建卡片容器"""
        card = tk.Frame(parent, bg=self.COLORS['white'], relief=tk.FLAT)
        
        # 卡片标题
        title_frame = tk.Frame(card, bg=self.COLORS['white'])
        title_frame.pack(fill=tk.X, padx=20, pady=(15, 10))
        
        # 标题左侧装饰条
        tk.Frame(title_frame, 
                bg=self.COLORS['accent'], 
                width=4, 
                height=20).pack(side=tk.LEFT, padx=(0, 10))
        
        tk.Label(title_frame, 
                text=title, 
                font=("微软雅黑", 11, "bold"),
                bg=self.COLORS['white'],
                fg=self.COLORS['text_dark']).pack(side=tk.LEFT)
        
        # 添加底部边框
        tk.Frame(card, bg=self.COLORS['border'], height=1).pack(side=tk.BOTTOM, fill=tk.X)
        
        return card
    
    def on_field_select(self, event):
        """字段选择事件"""
        selection = self.field_listbox.curselection()
        if selection:
            field_name = self.field_listbox.get(selection[0])
            self.selected_field_label.config(
                text=f"已选择字段: {field_name}",
                fg=self.COLORS['secondary'],
                font=("微软雅黑", 9, "bold")
            )
    
    def select_file(self):
        """选择Excel文件"""
        file_path = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[
                ("Excel文件", "*.xlsx *.xls"),
                ("Excel 2007+", "*.xlsx"),
                ("Excel 97-2003", "*.xls"),
                ("所有文件", "*.*")
            ]
        )
        
        if file_path:
            self.file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(
                text=f"📄 {filename}",
                fg=self.COLORS['text_dark'],
                font=("微软雅黑", 9, "bold")
            )
            self.status_label.config(text=f"正在读取文件: {filename}")
            self.root.update()
            self.load_excel_fields()
    
    def load_excel_fields(self):
        """载入Excel字段"""
        try:
            # 读取Excel文件
            self.df = pd.read_excel(self.file_path)
            
            if self.df.empty:
                messagebox.showwarning("警告", "Excel文件为空!")
                self.status_label.config(text="系统就绪")
                return
            
            # 清空并填充字段列表
            self.field_listbox.delete(0, tk.END)
            for col in self.df.columns:
                self.field_listbox.insert(tk.END, f"  {col}")
            
            self.split_button.config(
                state=tk.NORMAL,
                bg=self.COLORS['success']
            )
            
            rows = len(self.df)
            cols = len(self.df.columns)
            self.status_label.config(text=f"✓ 文件载入成功 | {rows} 行 × {cols} 列")
            
            messagebox.showinfo("文件载入成功", 
                              f"数据统计:\n\n"
                              f"• 数据行数: {rows:,}\n"
                              f"• 字段数量: {cols}\n"
                              f"• 文件大小: {os.path.getsize(self.file_path) / 1024:.1f} KB")
            
        except Exception as e:
            messagebox.showerror("读取失败", f"无法读取文件:\n\n{str(e)}")
            self.split_button.config(state=tk.DISABLED)
            self.status_label.config(text="文件读取失败")
    
    def select_output_dir(self):
        """选择输出目录"""
        dir_path = filedialog.askdirectory(title="选择输出目录")
        if dir_path:
            self.output_dir = dir_path
            if len(dir_path) > 50:
                display_path = "..." + dir_path[-47:]
            else:
                display_path = dir_path
            self.output_label.config(
                text=f"📁 {display_path}",
                fg=self.COLORS['text_dark'],
                font=("微软雅黑", 9, "bold")
            )
    
    def split_file(self):
        """执行文件拆分"""
        # 检查是否选择了字段
        selection = self.field_listbox.curselection()
        if not selection:
            messagebox.showwarning("操作提示", "请先选择一个拆分字段")
            return
        
        field_name = self.field_listbox.get(selection[0]).strip()
        
        # 确认操作
        unique_values = self.df[field_name].nunique()
        result = messagebox.askyesno(
            "确认执行", 
            f"拆分信息:\n\n"
            f"• 拆分字段: {field_name}\n"
            f"• 唯一值数量: {unique_values}\n"
            f"• 将生成文件: {unique_values} 个\n"
            f"• 输出位置: 源文件所在目录\n\n"
            f"是否继续执行?"
        )
        
        if not result:
            return
        
        # 输出到源文件目录
        output_dir = os.path.dirname(self.file_path)
        
        # 创建子文件夹
        base_name = Path(self.file_path).stem
        output_folder = os.path.join(output_dir, f"{base_name}_拆分结果")
        os.makedirs(output_folder, exist_ok=True)
        
        try:
            self.status_label.config(text="正在执行拆分...")
            self.split_button.config(state=tk.DISABLED, bg=self.COLORS['text_light'])
            self.root.update()
            
            # 按字段分组并保存
            grouped = self.df.groupby(field_name)
            file_count = 0
            
            for name, group in grouped:
                # 处理文件名中的特殊字符
                safe_name = str(name).replace('/', '_').replace('\\', '_').replace(':', '_')
                safe_name = safe_name.replace('*', '_').replace('?', '_').replace('"', '_')
                safe_name = safe_name.replace('<', '_').replace('>', '_').replace('|', '_')
                
                output_file = os.path.join(output_folder, f"{base_name}_{safe_name}.xlsx")
                group.to_excel(output_file, index=False, engine='openpyxl')
                file_count += 1
                
                self.status_label.config(text=f"拆分进度: {file_count}/{unique_values}")
                self.root.update()
            
            self.status_label.config(text=f"✓ 拆分完成 | 已生成 {file_count} 个文件")
            self.split_button.config(state=tk.NORMAL, bg=self.COLORS['success'])
            
            messagebox.showinfo("执行完成", 
                              f"文件拆分成功!\n\n"
                              f"• 生成文件数: {file_count}\n"
                              f"• 保存位置:\n  {output_folder}")
            
            # 询问是否打开输出文件夹
            if messagebox.askyesno("操作提示", "是否打开输出文件夹?"):
                if sys.platform == 'win32':
                    os.startfile(output_folder)
                elif sys.platform == 'darwin':
                    os.system(f'open "{output_folder}"')
                else:
                    os.system(f'xdg-open "{output_folder}"')
                
        except Exception as e:
            self.split_button.config(state=tk.NORMAL, bg=self.COLORS['success'])
            self.status_label.config(text="拆分失败")
            messagebox.showerror("执行失败", f"文件拆分失败:\n\n{str(e)}")


def main():
    # —— 强制验证：确认 Python 已执行 ——
    print("STEP 1: Python 已执行")

    root = tk.Tk()

    # —— 关键兜底：显式显示窗口 ——
    root.withdraw()            # 先隐藏
    root.update_idletasks()     # 强制刷新 Tk 状态

    # 设置一个绝对安全的位置和尺寸
    root.geometry("800x850+200+100")

    root.deiconify()            # 再显示
    root.lift()
    root.focus_force()
    root.attributes('-topmost', True)
    root.after(500, lambda: root.attributes('-topmost', False))

    print("STEP 2: Tk 窗口已创建")

    app = ExcelSplitterApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


# In[ ]:




