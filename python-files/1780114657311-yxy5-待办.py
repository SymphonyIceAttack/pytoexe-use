import tkinter as tk
from tkinter import font, messagebox
import csv
import os
from datetime import datetime

class TodoApp:
    def __init__(self, root):
        self.root = root
        self.root.title("待办清单")
        self.root.configure(bg='black')
        
        # 设置窗口大小和位置
        self.root.geometry("550x650+200+100")
        self.root.minsize(400, 500)
        
        # 解决模糊问题：设置高DPI支持
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # 数据文件路径
        self.data_file = "todo_list.csv"
        
        # 默认字体设置
        self.current_font_family = "Microsoft YaHei"
        self.current_font_size = 20
        
        # 主框架
        main_frame = tk.Frame(root, bg='black')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=12, pady=(12, 8))
        
        # 顶部工具栏
        toolbar = tk.Frame(main_frame, bg='black')
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # 标题
        title_label = tk.Label(
            toolbar, 
            text="待办清单", 
            bg='black', 
            fg='#ffffff',
            font=('Microsoft YaHei', 30, 'bold')
        )
        title_label.pack(side=tk.LEFT)
        
        # 字体调整按钮
        self.font_btn = tk.Button(
            toolbar,
            text="字体设置",
            bg='#2d2d2d',
            fg='white',
            font=('Microsoft YaHei', 9),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.open_font_settings
        )
        self.font_btn.pack(side=tk.RIGHT, padx=5)
        
        # 清空已完成按钮
        self.clear_btn = tk.Button(
            toolbar,
            text="清空已完成",
            bg='#2d2d2d',
            fg='white',
            font=('Microsoft YaHei', 9),
            relief=tk.FLAT,
            cursor="hand2",
            command=self.clear_completed
        )
        self.clear_btn.pack(side=tk.RIGHT, padx=5)
        
        # 待办列表容器 (带滚动条)
        list_container = tk.Frame(main_frame, bg='black')
        list_container.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(list_container, bg='black', highlightthickness=0)
        scrollbar = tk.Scrollbar(list_container, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg='black')
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 存储任务 (frame, var, checkbox, text)
        self.tasks = []
        
        # 底部输入栏
        input_frame = tk.Frame(root, bg='black')
        input_frame.pack(fill=tk.X, padx=12, pady=(0, 12))
        
        self.entry = tk.Entry(
            input_frame, 
            bg='#1e1e1e', 
            fg='white', 
            insertbackground='white',
            font=(self.current_font_family, self.current_font_size),
            relief=tk.FLAT,
            highlightthickness=1,
            highlightcolor='#00ff00',
            highlightbackground='#333'
        )
        self.entry.pack(fill=tk.X, padx=5, pady=8, ipady=8)
        self.entry.bind("<Return>", self.add_task)
        self.entry.focus()
        

        # 鼠标滚轮支持
        self._bind_mousewheel()
        
        # 更新canvas宽度
        self.update_canvas_width()
        self.root.bind("<Configure>", lambda e: self.update_canvas_width())
        
        # 加载保存的数据
        self.load_tasks()
        
        # 绑定窗口关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
    
    def _bind_mousewheel(self):
        def on_mousewheel(event):
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        
        self.canvas.bind_all("<MouseWheel>", on_mousewheel)
    
    def update_canvas_width(self):
        """更新canvas中frame的宽度"""
        if self.canvas.winfo_width() > 0:
            self.canvas.itemconfig(1, width=self.canvas.winfo_width())
    
    def open_font_settings(self):
        """打开字体设置窗口"""
        font_window = tk.Toplevel(self.root)
        font_window.title("字体设置")
        font_window.configure(bg='#2d2d2d')
        font_window.geometry("350x250+300+200")
        font_window.resizable(True,True)
        
        # 字体列表
        font_families = sorted(list(font.families()))
        available_fonts = []
        for f in font_families:
            if any(name in f.lower() for name in ['yahei', 'hei', 'song', 'kai', 'pingfang', 'microsoft']):
                available_fonts.append(f)
        
        # 如果没有找到中文字体，添加一些常用字体
        if not available_fonts:
            available_fonts = ['Microsoft YaHei', 'SimHei', 'SimSun', 'Arial', 'Helvetica']
        
        # 字体选择
        tk.Label(font_window, text="字体:", bg='#2d2d2d', fg='white', font=('Arial', 10)).pack(pady=(15, 5))
        font_var = tk.StringVar(value=self.current_font_family)
        font_combo = tk.ttk.Combobox(font_window, textvariable=font_var, values=available_fonts, width=25)
        font_combo.pack(pady=5)
        
        # 字号选择
        tk.Label(font_window, text="字号:", bg='#2d2d2d', fg='white', font=('Arial', 10)).pack(pady=(10, 5))
        size_var = tk.IntVar(value=self.current_font_size)
        size_spinbox = tk.Spinbox(font_window, from_=8, to=100, textvariable=size_var, width=10,
                                   bg='#1e1e1e', fg='white', buttonbackground='#2d2d2d')
        size_spinbox.pack(pady=5)
        
        # 预览
        tk.Label(font_window, text="预览:", bg='#2d2d2d', fg='white', font=('Arial', 10)).pack(pady=(10, 5))
        preview_label = tk.Label(font_window, text="示例文字 Sample Text", bg='#2d2d2d', fg='#00ff00',
                                  font=(self.current_font_family, self.current_font_size))
        preview_label.pack(pady=5)
        
        def update_preview(*args):
            preview_label.config(font=(font_var.get(), size_var.get()))
        
        font_var.trace('w', update_preview)
        size_var.trace('w', update_preview)
        
        def apply_font():
            self.current_font_family = font_var.get()
            self.current_font_size = size_var.get()
            # 更新所有任务的字体
            for frame, var, checkbox, text in self.tasks:
                checkbox.config(font=(self.current_font_family, self.current_font_size))
            # 更新输入框字体
            self.entry.config(font=(self.current_font_family, self.current_font_size))
            font_window.destroy()
            self.save_tasks()  # 保存字体设置
        
        # 按钮
        btn_frame = tk.Frame(font_window, bg='#2d2d2d')
        btn_frame.pack(pady=15)
        tk.Button(btn_frame, text="应用", command=apply_font, bg='#00ff00', fg='black',
                  font=('Arial', 10), relief=tk.FLAT, padx=20).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="取消", command=font_window.destroy, bg='#555', fg='white',
                  font=('Arial', 10), relief=tk.FLAT, padx=20).pack(side=tk.LEFT, padx=5)
        
        # 居中显示
        font_window.transient(self.root)
        font_window.grab_set()
    
    def add_task(self, event=None):
        text = self.entry.get().strip()
        if text:
            self.entry.delete(0, tk.END)
            self.create_task_row(text, completed=False)
            self.entry.focus()
            # 滚动到底部
            self.root.after(10, lambda: self.canvas.yview_moveto(1.0))
            self.save_tasks()
    
    def create_task_row(self, text, completed=False):
        row_frame = tk.Frame(self.scrollable_frame, bg='black')
        
        var = tk.BooleanVar(value=completed)
        
        cb = tk.Checkbutton(
            row_frame,
            text=text,
            variable=var,
            bg='black',
            fg='#666666' if completed else 'white',
            selectcolor='black',
            activebackground='#2d2d2d',
            activeforeground='white',
            font=(self.current_font_family, self.current_font_size),
            anchor='w',
            padx=12,
            pady=10,
            cursor="hand2"
        )
        cb.pack(fill=tk.X, padx=8, pady=3)
        
        # 保存任务
        self.tasks.append((row_frame, var, cb, text))
        
        if completed:
            # 已完成的任务放到末尾
            row_frame.pack(fill=tk.X, pady=1)
        else:
            # 未完成的任务插到合适位置（所有未完成之后，已完成之前）
            self._insert_task_row(row_frame)
        
        # 绑定勾选事件
        var.trace_add('write', lambda *args, f=row_frame, v=var, c=cb, t=text: self.on_task_toggle(f, v, c, t))
    
    def _insert_task_row(self, frame):
        """将未完成任务插入到合适位置"""
        # 找到最后一个未完成的任务
        insert_index = len(self.tasks)
        for i, (f, v, c, t) in enumerate(self.tasks):
            if v.get():  # 已完成的任务
                insert_index = i
                break
        
        # 重新打包所有任务
        for i, (f, v, c, t) in enumerate(self.tasks):
            f.pack_forget()
        
        for i, (f, v, c, t) in enumerate(self.tasks):
            if i == insert_index and frame not in [ff for ff, _, _, _ in self.tasks]:
                frame.pack(fill=tk.X, pady=1)
            f.pack(fill=tk.X, pady=1)
    
    def on_task_toggle(self, frame, var, checkbox, text):
        if var.get():
            # 勾选：移动到列表底部
            checkbox.config(fg='#666666')
            # 移动到底部
            for i, (f, v, c, t) in enumerate(self.tasks):
                if f == frame:
                    self.tasks.pop(i)
                    break
            self.tasks.append((frame, var, checkbox, text))
            
            # 重新打包
            for f, v, c, t in self.tasks:
                f.pack_forget()
            for f, v, c, t in self.tasks:
                f.pack(fill=tk.X, pady=1)
        else:
            # 取消勾选：移动到未完成任务区域（顶部）
            checkbox.config(fg='white')
            # 移除当前位置
            for i, (f, v, c, t) in enumerate(self.tasks):
                if f == frame:
                    self.tasks.pop(i)
                    break
            
            # 找到插入位置（第一个已完成的任务之前）
            insert_index = len(self.tasks)
            for i, (f, v, c, t) in enumerate(self.tasks):
                if v.get():
                    insert_index = i
                    break
            
            # 插入到合适位置
            self.tasks.insert(insert_index, (frame, var, checkbox, text))
            
            # 重新打包
            for f, v, c, t in self.tasks:
                f.pack_forget()
            for f, v, c, t in self.tasks:
                f.pack(fill=tk.X, pady=1)
        
        self.save_tasks()
    
    def clear_completed(self):
        """清空所有已完成的任务"""
        if messagebox.askyesno("确认", "确定要清空所有已完成的任务吗？"):
            self.tasks = [(f, v, c, t) for f, v, c, t in self.tasks if not v.get()]
            # 重新打包
            for f, v, c, t in self.tasks:
                f.pack_forget()
            for f, v, c, t in self.tasks:
                f.pack(fill=tk.X, pady=1)
            self.save_tasks()
    
    def save_tasks(self):
        """保存任务到CSV文件"""
        try:
            with open(self.data_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['任务内容', '是否完成', '字体', '字号'])
                for frame, var, checkbox, text in self.tasks:
                    writer.writerow([text, var.get(), self.current_font_family, self.current_font_size])
        except Exception as e:
            print(f"保存失败: {e}")
    
    def load_tasks(self):
        """从CSV文件加载任务"""
        if not os.path.exists(self.data_file):
            return
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader, None)
                
                for row in reader:
                    if len(row) >= 2:
                        text = row[0]
                        completed = row[1].lower() == 'true'
                        # 如果有字体设置，恢复字体
                        if len(row) >= 4:
                            try:
                                self.current_font_family = row[2]
                                self.current_font_size = int(row[3])
                            except:
                                pass
                        self.create_task_row(text, completed)
        except Exception as e:
            print(f"加载失败: {e}")
    
    def on_closing(self):
        """窗口关闭时的处理"""
        self.save_tasks()
        self.root.destroy()
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    # 导入ttk用于ComboBox
    import tkinter.ttk as ttk
    
    root = tk.Tk()
    app = TodoApp(root)
    app.run()