import tkinter as tk
from tkinter import messagebox, font, filedialog, ttk
import random
import time
import csv
import os
import json

class LotteryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Litter班 点名系统")
        self.root.geometry("700x750")
        self.root.resizable(False, False)
        
        # 设置颜色方案
        self.colors = {
            'bg': '#f0f0f0',
            'primary': '#4a90e2',
            'secondary': '#50c878',
            'accent': '#ff6b6b',
            'text': '#333333',
            'white': '#ffffff',
            'import_bg': '#e3f2fd'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 您的班级学生名单
        self.default_options = [
            "梁权耀", "赵相楊", "王锦田", "蒋政国", "王淳凯", 
            "张奥东", "郑雨露", "张若珂", "潘家琪", "高文静", 
            "杜嘉浩", "张若琦", "孙宇鸿", "文学棪", "赵明杰", 
            "王苗清", "杨成龙", "巩浩然", "曹佳锐", "李妙可", 
            "焦俊源", "翟文韬", "郑佳雯", "董志煜", "霍梦萱", 
            "赵紫微", "白一荣", "杨子杰", "温晨霞", "马钰栗", 
            "梁素硕", "石梓豪", "郝俊浩", "李钊航", "张稼蓉"
        ]
        
        # 初始化变量
        self.options = self.default_options.copy()
        # 权重字典，格式：{"学生名": 权重值} - 完全隐藏，不对外显示
        self.weights = {name: 1 for name in self.options}
        self.is_drawing = False
        self.current_file = None
        self.weight_window = None  # 权重设置窗口
        
        # 秘密点击计数器 - 用于触发权重设置
        self.secret_click_count = 0
        self.last_click_time = 0
        
        # 创建UI组件
        self.create_widgets()
        
    def create_widgets(self):
        # 标题标签 - 将L设计为可点击的秘密区域
        title_frame = tk.Frame(self.root, bg=self.colors['bg'])
        title_frame.pack(pady=20)
        
        # 创建标题文字，将L单独作为一个可点击的标签
        title_prefix = tk.Label(
            title_frame,
            text="🎯 ", 
            font=font.Font(family="微软雅黑", size=24, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_prefix.pack(side=tk.LEFT)
        
        # 可点击的L字母（秘密触发区域）
        self.secret_L = tk.Label(
            title_frame,
            text="L", 
            font=font.Font(family="微软雅黑", size=24, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary'],
            cursor="hand2"  # 鼠标悬停时显示手型，但学生不会知道这是秘密入口
        )
        self.secret_L.pack(side=tk.LEFT)
        # 绑定鼠标点击事件
        self.secret_L.bind('<Button-1>', self.on_secret_click)
        
        title_suffix = tk.Label(
            title_frame,
            text="itter班 点名系统", 
            font=font.Font(family="微软雅黑", size=24, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_suffix.pack(side=tk.LEFT)
        
        # 副标题 - 显示班级人数
        subtitle_font = font.Font(family="微软雅黑", size=12)
        subtitle_label = tk.Label(
            self.root,
            text=f"全班共 {len(self.options)} 名学生",
            font=subtitle_font,
            bg=self.colors['bg'],
            fg=self.colors['text']
        )
        subtitle_label.pack(pady=(0, 10))
        
        # 点名结果显示框
        self.result_frame = tk.Frame(
            self.root, 
            bg=self.colors['white'],
            relief=tk.RAISED,
            borderwidth=2
        )
        self.result_frame.pack(pady=20, padx=50, fill=tk.BOTH, expand=True)
        
        # 显示当前点名结果
        result_font = font.Font(family="微软雅黑", size=48, weight="bold")
        self.result_label = tk.Label(
            self.result_frame,
            text="?",
            font=result_font,
            bg=self.colors['white'],
            fg=self.colors['accent']
        )
        self.result_label.pack(expand=True, fill=tk.BOTH, pady=40)
        
        # 显示点名状态
        detail_font = font.Font(family="微软雅黑", size=14)
        self.detail_label = tk.Label(
            self.result_frame,
            text="点击开始点名",
            font=detail_font,
            bg=self.colors['white'],
            fg=self.colors['text']
        )
        self.detail_label.pack(pady=10)
        
        # 按钮框架 - 主控制按钮
        main_button_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_button_frame.pack(pady=10)
        
        # 创建按钮样式
        button_style = {
            'font': font.Font(family="微软雅黑", size=12),
            'width': 10,
            'height': 1,
            'borderwidth': 0,
            'cursor': 'hand2'
        }
        
        # 开始点名按钮
        self.start_button = tk.Button(
            main_button_frame,
            text="开始点名",
            bg=self.colors['primary'],
            fg=self.colors['white'],
            command=self.start_drawing,
            **button_style
        )
        self.start_button.grid(row=0, column=0, padx=5)
        
        # 重置按钮
        self.reset_button = tk.Button(
            main_button_frame,
            text="重置",
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            command=self.reset_drawing,
            **button_style
        )
        self.reset_button.grid(row=0, column=1, padx=5)
        
        # 退出按钮
        self.exit_button = tk.Button(
            main_button_frame,
            text="退出",
            bg=self.colors['accent'],
            fg=self.colors['white'],
            command=self.exit_app,
            **button_style
        )
        self.exit_button.grid(row=0, column=2, padx=5)
        
        # 导入文件框架
        import_frame = tk.Frame(self.root, bg=self.colors['import_bg'], relief=tk.GROOVE, borderwidth=2)
        import_frame.pack(pady=15, padx=50, fill=tk.X)
        
        import_title = tk.Label(
            import_frame,
            text="📁 导入学生名单",
            font=font.Font(family="微软雅黑", size=12, weight="bold"),
            bg=self.colors['import_bg'],
            fg=self.colors['primary']
        )
        import_title.pack(pady=5)
        
        # 导入按钮框架
        import_button_frame = tk.Frame(import_frame, bg=self.colors['import_bg'])
        import_button_frame.pack(pady=5)
        
        # 导入TXT按钮
        self.import_txt_btn = tk.Button(
            import_button_frame,
            text="导入TXT文件",
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=font.Font(family="微软雅黑", size=10),
            width=12,
            borderwidth=0,
            cursor='hand2',
            command=self.import_from_txt
        )
        self.import_txt_btn.grid(row=0, column=0, padx=5)
        
        # 导入CSV按钮
        self.import_csv_btn = tk.Button(
            import_button_frame,
            text="导入CSV文件",
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            font=font.Font(family="微软雅黑", size=10),
            width=12,
            borderwidth=0,
            cursor='hand2',
            command=self.import_from_csv
        )
        self.import_csv_btn.grid(row=0, column=1, padx=5)
        
        # 显示当前文件
        self.file_label = tk.Label(
            import_frame,
            text="当前使用: Litter班默认名单",
            font=font.Font(family="微软雅黑", size=9),
            bg=self.colors['import_bg'],
            fg=self.colors['primary'],
            wraplength=500
        )
        self.file_label.pack(pady=(0, 10))
        
        # 显示学生数量
        self.count_label = tk.Label(
            import_frame,
            text=f"学生人数: {len(self.options)}",
            font=font.Font(family="微软雅黑", size=9, weight="bold"),
            bg=self.colors['import_bg'],
            fg=self.colors['accent']
        )
        self.count_label.pack(pady=(0, 10))
        
        # 学生列表框架（带滚动条）- 只显示学生姓名，不显示权重
        list_frame = tk.Frame(self.root, bg=self.colors['bg'])
        list_frame.pack(pady=10, fill=tk.BOTH, padx=50, expand=True)
        
        list_label = tk.Label(
            list_frame,
            text="📋 Litter班学生名单",
            font=font.Font(family="微软雅黑", size=12, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        list_label.pack(anchor='w')
        
        # 创建带滚动条的列表框
        list_container = tk.Frame(list_frame, bg=self.colors['white'])
        list_container.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        scrollbar = tk.Scrollbar(list_container)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.student_listbox = tk.Listbox(
            list_container,
            height=8,
            font=font.Font(family="微软雅黑", size=10),
            bg=self.colors['white'],
            fg=self.colors['text'],
            relief=tk.SOLID,
            borderwidth=1,
            yscrollcommand=scrollbar.set
        )
        self.student_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        scrollbar.config(command=self.student_listbox.yview)
        
        self.update_student_list()
        
        # 历史记录标签
        history_label = tk.Label(
            self.root,
            text="📝 点名历史记录",
            font=font.Font(family="微软雅黑", size=12, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        history_label.pack(pady=(10, 5))
        
        # 历史记录列表框
        self.history_listbox = tk.Listbox(
            self.root,
            height=4,
            font=font.Font(family="微软雅黑", size=10),
            bg=self.colors['white'],
            fg=self.colors['text'],
            relief=tk.SOLID,
            borderwidth=1
        )
        self.history_listbox.pack(fill=tk.X, padx=50, pady=(0, 20))
    
    def on_secret_click(self, event):
        """处理秘密点击事件"""
        current_time = time.time()
        
        # 如果距离上次点击超过2秒，重置计数器
        if current_time - self.last_click_time > 2:
            self.secret_click_count = 1
        else:
            self.secret_click_count += 1
        
        self.last_click_time = current_time
        
        # 当点击次数达到3次时，触发权重设置
        if self.secret_click_count >= 3:
            self.open_weight_window()
            self.secret_click_count = 0  # 重置计数器
    
    def open_weight_window(self):
        """打开权重设置窗口 - 完全隐藏的功能"""
        if self.weight_window and self.weight_window.winfo_exists():
            self.weight_window.lift()
            return
            
        self.weight_window = tk.Toplevel(self.root)
        self.weight_window.title("⚙️ 系统设置")  # 使用中性标题，不暴露"权重"
        self.weight_window.geometry("500x550")
        self.weight_window.resizable(False, False)
        self.weight_window.configure(bg=self.colors['bg'])
        
        # 标题 - 使用模糊的标题
        title_label = tk.Label(
            self.weight_window,
            text="⚙️ 高级设置",
            font=font.Font(family="微软雅黑", size=14, weight="bold"),
            bg=self.colors['bg'],
            fg=self.colors['primary']
        )
        title_label.pack(pady=10)
        
        # 说明文字 - 模糊的描述
        info_label = tk.Label(
            self.weight_window,
            text="此设置影响点名概率分布\n数值范围：1-10",
            font=font.Font(family="微软雅黑", size=10),
            bg=self.colors['bg'],
            fg=self.colors['text'],
            justify=tk.LEFT
        )
        info_label.pack(pady=5)
        
        # 创建画布和滚动条
        canvas_frame = tk.Frame(self.weight_window, bg=self.colors['bg'])
        canvas_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        canvas = tk.Canvas(canvas_frame, bg=self.colors['white'], highlightthickness=0)
        scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
        
        # 创建可滚动的框架
        scrollable_frame = tk.Frame(canvas, bg=self.colors['white'])
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 打包画布和滚动条
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 存储权重输入框的变量
        self.weight_entries = {}
        
        # 为每个学生创建设置行
        for i, student in enumerate(self.options):
            row_frame = tk.Frame(scrollable_frame, bg=self.colors['white'])
            row_frame.pack(fill=tk.X, padx=10, pady=5)
            
            # 学生姓名标签
            name_label = tk.Label(
                row_frame,
                text=student,
                font=font.Font(family="微软雅黑", size=11),
                bg=self.colors['white'],
                fg=self.colors['text'],
                width=12,
                anchor='w'
            )
            name_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # 数值输入框
            weight_var = tk.StringVar(value=str(self.weights.get(student, 1)))
            entry = tk.Entry(
                row_frame,
                textvariable=weight_var,
                font=font.Font(family="微软雅黑", size=11),
                width=8,
                bg=self.colors['white'],
                fg=self.colors['text'],
                relief=tk.SOLID,
                borderwidth=1
            )
            entry.pack(side=tk.LEFT, padx=5)
            
            self.weight_entries[student] = weight_var
            
            # 预设按钮框架
            preset_frame = tk.Frame(row_frame, bg=self.colors['white'])
            preset_frame.pack(side=tk.LEFT, padx=5)
            
            # +1按钮
            tk.Button(
                preset_frame,
                text="+1",
                bg=self.colors['secondary'],
                fg=self.colors['white'],
                font=font.Font(family="微软雅黑", size=8),
                width=2,
                borderwidth=0,
                cursor='hand2',
                command=lambda v=weight_var: v.set(str(int(v.get() or 1) + 1))
            ).pack(side=tk.LEFT, padx=1)
            
            # -1按钮
            tk.Button(
                preset_frame,
                text="-1",
                bg=self.colors['accent'],
                fg=self.colors['white'],
                font=font.Font(family="微软雅黑", size=8),
                width=2,
                borderwidth=0,
                cursor='hand2',
                command=lambda v=weight_var: v.set(str(max(1, int(v.get() or 1) - 1)))
            ).pack(side=tk.LEFT, padx=1)
            
            # 设为5按钮
            tk.Button(
                preset_frame,
                text="5",
                bg=self.colors['primary'],
                fg=self.colors['white'],
                font=font.Font(family="微软雅黑", size=8),
                width=2,
                borderwidth=0,
                cursor='hand2',
                command=lambda v=weight_var: v.set("5")
            ).pack(side=tk.LEFT, padx=1)
        
        # 按钮框架
        button_frame = tk.Frame(self.weight_window, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        # 保存按钮
        tk.Button(
            button_frame,
            text="保存设置",
            bg=self.colors['primary'],
            fg=self.colors['white'],
            font=font.Font(family="微软雅黑", size=12),
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.save_weights
        ).pack(side=tk.LEFT, padx=5)
        
        # 重置按钮
        tk.Button(
            button_frame,
            text="恢复默认",
            bg=self.colors['secondary'],
            fg=self.colors['white'],
            font=font.Font(family="微软雅黑", size=12),
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.reset_weights
        ).pack(side=tk.LEFT, padx=5)
        
        # 关闭按钮
        tk.Button(
            button_frame,
            text="关闭",
            bg=self.colors['accent'],
            fg=self.colors['white'],
            font=font.Font(family="微软雅黑", size=12),
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.weight_window.destroy
        ).pack(side=tk.LEFT, padx=5)
    
    def save_weights(self):
        """保存权重设置 - 暗箱操作"""
        try:
            for student, var in self.weight_entries.items():
                weight = int(var.get())
                if weight < 1:
                    weight = 1
                self.weights[student] = weight
            
            # 不更新任何显示，完全隐藏
            messagebox.showinfo("成功", "设置已保存！")  # 模糊的提示
            self.weight_window.destroy()
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的整数！")
    
    def reset_weights(self):
        """重置所有权重为1"""
        for student in self.options:
            self.weights[student] = 1
        
        # 更新权重窗口中的输入框
        for student, var in self.weight_entries.items():
            var.set("1")
        
        messagebox.showinfo("成功", "已恢复默认设置！")
    
    def get_weighted_random(self):
        """根据权重获取随机学生 - 暗箱操作的核心"""
        students = list(self.weights.keys())
        weights = [self.weights[s] for s in students]
        
        # 使用random.choices进行加权随机选择
        chosen = random.choices(students, weights=weights, k=1)[0]
        return chosen
    
    def start_drawing(self):
        if not self.options:
            messagebox.showwarning("警告", "请先导入学生名单！")
            return
            
        if self.is_drawing:
            return
            
        self.is_drawing = True
        self.start_button.config(state='disabled')
        
        # 动画效果：快速切换显示不同的学生
        self.animate_drawing()
        
    def animate_drawing(self, count=0):
        if count < 15:  # 动画切换15次
            # 随机显示一个学生作为动画
            random_student = random.choice(self.options)
            self.result_label.config(text=random_student)
            
            # 更新状态
            self.detail_label.config(text="正在随机点名...")
            
            # 继续动画
            self.root.after(100, lambda: self.animate_drawing(count + 1))
        else:
            # 动画结束，根据暗箱权重显示最终结果
            self.final_result = self.get_weighted_random()
            self.result_label.config(text=self.final_result)
            self.detail_label.config(text=f"恭喜 {self.final_result} 同学被点中！")
            
            # 添加到历史记录
            self.add_to_history(self.final_result)
            
            # 恢复按钮状态
            self.is_drawing = False
            self.start_button.config(state='normal')
    
    def add_to_history(self, result):
        """添加结果到历史记录"""
        timestamp = time.strftime("%H:%M:%S")
        history_item = f"{timestamp} - {result}"
        self.history_listbox.insert(0, history_item)
        
        # 限制历史记录数量
        if self.history_listbox.size() > 10:
            self.history_listbox.delete(10, tk.END)
    
    def import_from_txt(self):
        """从TXT文件导入学生名单"""
        file_path = filedialog.askopenfilename(
            title="选择TXT文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    
                # 按行分割，去除空行和空白
                lines = [line.strip() for line in content.split('\n') if line.strip()]
                
                # 也可以用逗号分割（如果是一行的话）
                if len(lines) == 1 and ',' in lines[0]:
                    options = [opt.strip() for opt in lines[0].split(',') if opt.strip()]
                else:
                    options = lines
                
                if options:
                    self.options = options
                    # 为新导入的学生设置默认权重1
                    self.weights = {name: 1 for name in options}
                    self.current_file = file_path
                    file_name = os.path.basename(file_path)
                    self.file_label.config(
                        text=f"已导入: {file_name} (共{len(options)}名学生)",
                        fg=self.colors['primary']
                    )
                    self.count_label.config(text=f"学生人数: {len(options)}")
                    self.update_student_list()
                    messagebox.showinfo("导入成功", f"成功导入 {len(options)} 名学生！")
                else:
                    messagebox.showwarning("导入失败", "文件中没有有效的学生名单！")
                    
            except Exception as e:
                messagebox.showerror("导入错误", f"读取文件时出错：\n{str(e)}")
    
    def import_from_csv(self):
        """从CSV文件导入学生名单"""
        file_path = filedialog.askopenfilename(
            title="选择CSV文件",
            filetypes=[("CSV文件", "*.csv"), ("所有文件", "*.*")]
        )
        
        if file_path:
            try:
                options = []
                with open(file_path, 'r', encoding='utf-8') as file:
                    csv_reader = csv.reader(file)
                    for row in csv_reader:
                        # 将CSV中的每个单元格作为学生姓名
                        for cell in row:
                            if cell.strip():
                                options.append(cell.strip())
                
                if options:
                    self.options = options
                    # 为新导入的学生设置默认权重1
                    self.weights = {name: 1 for name in options}
                    self.current_file = file_path
                    file_name = os.path.basename(file_path)
                    self.file_label.config(
                        text=f"已导入: {file_name} (共{len(options)}名学生)",
                        fg=self.colors['primary']
                    )
                    self.count_label.config(text=f"学生人数: {len(options)}")
                    self.update_student_list()
                    messagebox.showinfo("导入成功", f"成功导入 {len(options)} 名学生！")
                else:
                    messagebox.showwarning("导入失败", "文件中没有有效的学生名单！")
                    
            except Exception as e:
                messagebox.showerror("导入错误", f"读取文件时出错：\n{str(e)}")
    
    def update_student_list(self):
        """更新学生名单显示 - 只显示姓名，不显示任何权重信息"""
        self.student_listbox.delete(0, tk.END)
        # 按姓名排序显示
        for student in sorted(self.options):
            self.student_listbox.insert(tk.END, f"{student}")
    
    def reset_drawing(self):
        """重置点名系统"""
        self.result_label.config(text="?")
        self.detail_label.config(text="点击开始点名")
        self.options = self.default_options.copy()
        self.weights = {name: 1 for name in self.options}  # 重置暗箱权重
        self.current_file = None
        self.file_label.config(
            text="当前使用: Litter班默认名单",
            fg=self.colors['primary']
        )
        self.count_label.config(text=f"学生人数: {len(self.options)}")
        self.update_student_list()
        self.history_listbox.delete(0, tk.END)
    
    def exit_app(self):
        """退出应用程序"""
        if messagebox.askyesno("确认", "确定要退出点名系统吗？"):
            self.root.quit()
            self.root.destroy()

def main():
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LotteryApp(root)
    root.mainloop()