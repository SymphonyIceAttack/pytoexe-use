import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, ttk, font, colorchooser
import re
import time
import random

class TabTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("多标签文本编辑器")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)

        # ========== 等级系统配置 ==========
        self.level_thresholds = [
            ("新生 I", 0), ("新生 II", 100), ("新生 III", 200),
            ("见习 I", 300), ("见习 II", 400), ("见习 III", 500),
            ("下忍 I", 600), ("下忍 II", 700), ("下忍 III", 800),
            ("中忍 I", 900), ("中忍 II", 1000), ("中忍 III", 1100),
            ("上忍 I", 1200), ("上忍 II", 1300), ("上忍 III", 1400),
            ("暗部 I", 1500), ("暗部 II", 1600), ("暗部 III", 1700),
            ("影 I", 1800), ("影 II", 1900), ("影 III", 2000),
            ("超影", 2400),      # 最高级阈值
        ]
        self.total_score = 0
        self.last_char_count = {}

        # ---------- 防刷分参数 ----------
        self.MAX_SCORE_PER_SECOND = 30
        self.last_score_time = 0
        self.score_buffer = 0
        self._buffer_scheduled = False   # 标志是否有待处理的缓冲

        # ---------- 防篡改校验 ----------
        self._score_key = random.randint(1, 2**31-1)
        self._score_checksum = self.total_score ^ self._score_key

        # ========== 界面设置 ==========
        style = ttk.Style()
        style.theme_use('clam')

        self.current_font_family = "SimSun"
        self.current_font_size = 12
        self.unnamed_count = 1

        # 菜单栏
        menubar = tk.Menu(root)
        root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="新建", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="打开", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="保存", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="另存为", command=self.save_as, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="关闭当前标签", command=self.close_current_tab, accelerator="Ctrl+W")
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit_editor, accelerator="Ctrl+Q")

        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="编辑", menu=edit_menu)
        # 合并查找/替换菜单项，仍保留Ctrl+H快捷键直接聚焦替换框（不显示在菜单）
        edit_menu.add_command(label="查找/替换", command=self.find_replace, accelerator="Ctrl+F")
        # 可选的提示：如果用户想直接替换，可用Ctrl+H
        # 不添加菜单项避免冗余，但保留快捷键

        format_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="格式", menu=format_menu)
        format_menu.add_command(label="选择字体", command=self.choose_font)
        self.word_wrap_var = tk.BooleanVar(value=True)
        format_menu.add_checkbutton(label="自动换行", variable=self.word_wrap_var, command=self.toggle_word_wrap)

        # 标签页
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=1)
        self.notebook.bind("<Button-3>", self.show_notebook_context_menu)  # 右键弹出菜单

        # ========== 状态栏 ==========
        status_frame = ttk.Frame(root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)

        self.cursor_label = ttk.Label(status_frame, text="行: 1 列: 1", anchor=tk.W, width=15)
        self.cursor_label.pack(side=tk.LEFT, padx=5)

        self.selection_label = ttk.Label(status_frame, text="选中: 0", anchor=tk.W, width=10)
        self.selection_label.pack(side=tk.LEFT, padx=5)

        self.total_chars_label = ttk.Label(status_frame, text="总字符: 0", anchor=tk.W, width=12)
        self.total_chars_label.pack(side=tk.LEFT, padx=5)

        self.encoding_label = ttk.Label(status_frame, text="UTF-8", anchor=tk.W, width=8)
        self.encoding_label.pack(side=tk.LEFT, padx=5)

        # 经验条和等级放在右侧
        self.level_label = ttk.Label(status_frame, text="", width=25, anchor=tk.CENTER)
        self.level_label.pack(side=tk.RIGHT, padx=5)

        self.exp_bar = ttk.Progressbar(status_frame, length=200, mode='determinate')
        self.exp_bar.pack(side=tk.RIGHT, padx=5)

        # 绑定快捷键
        self._bind_shortcuts()

        # 创建第一个标签页
        self.new_file()

        # 初始化等级显示
        self.update_level_display()

        # 启动光标/选中区域更新
        self._update_status_info()

    # ---------- 等级系统核心 ----------
    def _validate_score(self):
        """验证分数是否被篡改，若不一致则重置为0"""
        if (self.total_score ^ self._score_key) != self._score_checksum:
            messagebox.showwarning("检测到篡改", "分数已被外部修改，已重置为0。")
            self.total_score = 0
            self._score_checksum = 0 ^ self._score_key
            self.update_level_display()

    def get_current_level_info(self):
        """返回 (等级名称, 当前等级阈值, 下一级阈值)"""
        self._validate_score()
        current_level = self.level_thresholds[0][0]
        current_th = 0
        next_th = self.level_thresholds[1][1] if len(self.level_thresholds) > 1 else 0
        for i, (name, th) in enumerate(self.level_thresholds):
            if self.total_score >= th:
                current_level = name
                current_th = th
                if i + 1 < len(self.level_thresholds):
                    next_th = self.level_thresholds[i+1][1]
                else:
                    next_th = th
            else:
                break
        return current_level, current_th, next_th

    def update_level_display(self):
        """更新状态栏的等级文本和进度条"""
        self._validate_score()
        level_name, current_th, next_th = self.get_current_level_info()
        if next_th == current_th:
            progress = 100
            display = f"{level_name} {self.total_score}"
        else:
            progress = (self.total_score - current_th) / (next_th - current_th) * 100
            display = f"{level_name} {self.total_score}/{next_th}"
        self.level_label.config(text=display)
        self.exp_bar['value'] = progress

    def add_score(self, increment):
        """增加分数，带防刷分机制"""
        if increment <= 0:
            return

        now = time.time()
        time_diff = now - self.last_score_time

        if time_diff >= 1.0:
            # 超过1秒，直接加入
            self.total_score += increment
            self.last_score_time = now
        else:
            # 1秒内，如果单次增量超过阈值，则暂存
            if increment > self.MAX_SCORE_PER_SECOND:
                allowed = self.MAX_SCORE_PER_SECOND
                self.total_score += allowed
                self.score_buffer += increment - allowed
                if not self._buffer_scheduled:
                    self.root.after(1000, self.process_score_buffer)
                    self._buffer_scheduled = True
            else:
                self.total_score += increment
        # 更新校验
        self._score_checksum = self.total_score ^ self._score_key
        self.update_level_display()

    def process_score_buffer(self):
        """处理缓存的分数（每秒调用一次）"""
        if self.score_buffer > 0:
            add_now = min(self.score_buffer, self.MAX_SCORE_PER_SECOND)
            self.total_score += add_now
            self.score_buffer -= add_now
            self._score_checksum = self.total_score ^ self._score_key
            self.update_level_display()
            if self.score_buffer > 0:
                self.root.after(1000, self.process_score_buffer)
            else:
                self._buffer_scheduled = False
        else:
            self._buffer_scheduled = False

    # ---------- 文本修改事件 ----------
    def on_text_modified(self, frame, event):
        """统一的修改事件处理：统计字数 + 标记修改"""
        text_widget = frame.text
        if not text_widget.edit_modified():
            return

        # 计算字符数变化
        content = text_widget.get(1.0, tk.END)
        current_count = len(content) - 1  # 去掉末尾换行
        last_count = self.last_char_count.get(text_widget, 0)

        # 检查是否应该忽略本次修改（仅用于打开文件等初始插入）
        ignore = getattr(text_widget, 'ignore_next_modification', False)
        if ignore:
            # 只更新计数，不加分
            self.last_char_count[text_widget] = current_count
            text_widget.ignore_next_modification = False
        else:
            # 正常加分（只加增加的部分）
            if current_count > last_count:
                increase = current_count - last_count
                self.add_score(increase)
            self.last_char_count[text_widget] = current_count

        # 标记文件已修改
        if not frame.is_modified:
            frame.is_modified = True
            self.update_tab_title(frame)

        text_widget.edit_modified(False)

    # ---------- 快捷键绑定 ----------
    def _bind_shortcuts(self):
        self.root.bind("<Control-n>", lambda e: self.new_file())
        self.root.bind("<Control-o>", lambda e: self.open_file())
        self.root.bind("<Control-s>", lambda e: self.save_file())
        self.root.bind("<Control-S>", lambda e: self.save_as())
        self.root.bind("<Control-w>", lambda e: self.close_current_tab())
        self.root.bind("<Control-q>", lambda e: self.quit_editor())
        self.root.bind("<Control-f>", lambda e: self.find_replace())
        self.root.bind("<Control-h>", lambda e: self.find_replace(replace_focus=True))  # 保留快捷键

    # ---------- 标签页操作 ----------
    def get_current_tab(self):
        try:
            return self.notebook.nametowidget(self.notebook.select())
        except:
            return None

    def get_text_widget(self):
        tab = self.get_current_tab()
        return tab.text if tab else None

    def get_file_path(self):
        tab = self.get_current_tab()
        return getattr(tab, 'file_path', None) if tab else None

    def set_file_path(self, path):
        tab = self.get_current_tab()
        if tab:
            setattr(tab, 'file_path', path)

    def update_tab_title(self, frame=None):
        if frame is None:
            frame = self.get_current_tab()
        if not frame:
            return
        path = getattr(frame, 'file_path', None)
        base = path.split('/')[-1] if path else getattr(frame, 'unnamed', '未命名')
        if getattr(frame, 'is_modified', False):
            base = '*' + base
        self.notebook.tab(frame, text=base)

    def show_notebook_context_menu(self, event):
        """在Notebook标签上右键弹出菜单"""
        try:
            index = self.notebook.index("@%d,%d" % (event.x, event.y))
        except tk.TclError:
            return
        frame = self.notebook.children.values()[index]  # 根据索引获取frame
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="关闭", command=lambda: self.close_tab(frame))
        menu.add_command(label="关闭其他", command=lambda: self.close_other_tabs(frame))
        menu.add_command(label="保存", command=lambda: self.save_tab(frame))
        menu.tk_popup(event.x_root, event.y_root)

    def close_other_tabs(self, keep_frame):
        for frame in list(self.notebook.winfo_children()):
            if frame != keep_frame:
                self.close_tab(frame)

    def save_tab(self, frame):
        self.notebook.select(frame)
        self.save_file()

    # ---------- 文件操作 ----------
    def new_file(self):
        frame = ttk.Frame(self.notebook)
        text_area = scrolledtext.ScrolledText(frame, undo=True,
                                              font=(self.current_font_family, self.current_font_size),
                                              wrap=tk.WORD if self.word_wrap_var.get() else tk.NONE)
        text_area.pack(fill=tk.BOTH, expand=1)

        frame.text = text_area
        frame.file_path = None
        frame.is_modified = False
        frame.unnamed = f"未命名{self.unnamed_count}"
        self.unnamed_count += 1

        # 绑定修改事件
        text_area.bind("<<Modified>>", lambda e, f=frame: self.on_text_modified(f, e))

        # 添加右键菜单
        self._add_right_click_menu(text_area)

        # 初始化字符计数
        content = text_area.get(1.0, tk.END)
        self.last_char_count[text_area] = len(content) - 1

        self.notebook.add(frame, text=frame.unnamed)
        self.notebook.select(frame)

    def _add_right_click_menu(self, text_widget):
        menu = tk.Menu(text_widget, tearoff=0)
        menu.add_command(label="撤销", command=lambda: text_widget.event_generate("<<Undo>>"))
        menu.add_command(label="重做", command=lambda: text_widget.event_generate("<<Redo>>"))
        menu.add_separator()
        menu.add_command(label="剪切", command=lambda: text_widget.event_generate("<<Cut>>"))
        menu.add_command(label="复制", command=lambda: text_widget.event_generate("<<Copy>>"))
        menu.add_command(label="粘贴", command=lambda: text_widget.event_generate("<<Paste>>"))
        menu.add_separator()
        menu.add_command(label="全选", command=lambda: text_widget.event_generate("<<SelectAll>>"))
        menu.add_separator()
        # 新增：查找选中文本
        menu.add_command(label="查找选中文本", command=lambda: self.find_replace_with_selection(text_widget))
        # 新增：加粗
        menu.add_command(label="加粗", command=lambda: self.toggle_bold(text_widget))
        # 新增：颜色子菜单
        color_menu = tk.Menu(menu, tearoff=0)
        colors = [("红色", "red"), ("绿色", "green"), ("蓝色", "blue"), ("黄色", "yellow"), ("紫色", "purple")]
        for name, code in colors:
            color_menu.add_command(label=name, command=lambda c=code: self.apply_color(text_widget, c))
        color_menu.add_separator()
        color_menu.add_command(label="自定义...", command=lambda: self.choose_color(text_widget))
        menu.add_cascade(label="颜色", menu=color_menu)
        # 原有的查找/替换（可选，但为了保持一致性，保留）
        menu.add_separator()
        menu.add_command(label="查找/替换", command=self.find_replace)

        def show_menu(event):
            # 记录鼠标位置，供查找选中文本时使用
            text_widget.last_right_click = (event.x_root, event.y_root)
            menu.tk_popup(event.x_root, event.y_root)

        text_widget.bind("<Button-3>", show_menu)

    def find_replace_with_selection(self, text_widget):
        """右键查找选中文本：获取选中内容，打开查找窗口并自动填入"""
        try:
            selected = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            selected = ""
        # 获取右键点击时的屏幕坐标
        x, y = getattr(text_widget, 'last_right_click', (None, None))
        self.find_replace(initial_text=selected, position=(x, y))

    def toggle_bold(self, text_widget):
        """为选中文本切换粗体样式"""
        try:
            start = text_widget.index(tk.SEL_FIRST)
            end = text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            return
        # 检查是否已经有粗体标签
        tags = text_widget.tag_names(start)
        bold_tag = "bold"
        if bold_tag in text_widget.tag_names() and bold_tag in tags:
            # 如果已有粗体，移除
            text_widget.tag_remove(bold_tag, start, end)
        else:
            # 添加粗体标签
            text_widget.tag_add(bold_tag, start, end)
            text_widget.tag_configure(bold_tag, font=(self.current_font_family, self.current_font_size, "bold"))

    def apply_color(self, text_widget, color):
        """为选中文本应用颜色"""
        try:
            start = text_widget.index(tk.SEL_FIRST)
            end = text_widget.index(tk.SEL_LAST)
        except tk.TclError:
            return
        # 创建或复用颜色标签（按颜色名称命名）
        tag_name = f"color_{color}"
        if tag_name not in text_widget.tag_names():
            text_widget.tag_configure(tag_name, foreground=color)
        # 移除其他颜色标签（避免冲突）
        for t in text_widget.tag_names():
            if t.startswith("color_") and t != tag_name:
                text_widget.tag_remove(t, start, end)
        text_widget.tag_add(tag_name, start, end)

    def choose_color(self, text_widget):
        """打开颜色选择器，应用自定义颜色"""
        color_code = colorchooser.askcolor(title="选择颜色", parent=self.root)[1]
        if color_code:
            self.apply_color(text_widget, color_code)

    def open_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt")], parent=self.root)
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8", errors='replace') as f:
                    content = f.read()
                self.new_file()
                frame = self.get_current_tab()
                text_widget = frame.text
                # 设置忽略标志，避免打开文件的内容被加分
                text_widget.ignore_next_modification = True
                text_widget.insert(tk.END, content)
                frame.file_path = file_path
                frame.is_modified = False
                text_widget.edit_modified(False)
                self.update_tab_title(frame)
                self.last_char_count[text_widget] = len(content)
            except Exception as e:
                messagebox.showerror("错误", f"无法打开文件：{e}", parent=self.root)

    def save_file(self):
        path = self.get_file_path()
        if path is None:
            self.save_as()
        else:
            self._save_to_path(path)

    def save_as(self):
        file_path = filedialog.asksaveasfilename(defaultextension=".txt",
                                                 filetypes=[("所有文件", "*.*"), ("文本文件", "*.txt")],
                                                 parent=self.root)
        if file_path:
            self._save_to_path(file_path)
            self.set_file_path(file_path)
            frame = self.get_current_tab()
            frame.unnamed = None
            self.update_tab_title(frame)

    def _save_to_path(self, path):
        try:
            content = self.get_text_widget().get(1.0, tk.END)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            frame = self.get_current_tab()
            frame.is_modified = False
            frame.text.edit_modified(False)
            self.update_tab_title(frame)
            self.cursor_label.config(text=f"已保存到 {path.split('/')[-1]}")
        except Exception as e:
            messagebox.showerror("错误", f"无法保存文件：{e}", parent=self.root)

    def close_tab(self, frame):
        if not frame:
            return
        if getattr(frame, 'is_modified', False):
            result = messagebox.askyesnocancel("保存文件", f"文件 {self.notebook.tab(frame, 'text')} 已修改，是否保存？",
                                               parent=self.root)
            if result is None:
                return
            elif result:
                self.notebook.select(frame)
                self.save_file()
        if frame.text in self.last_char_count:
            del self.last_char_count[frame.text]
        self.notebook.forget(frame)
        frame.destroy()
        if not self.notebook.winfo_children():
            self.new_file()

    def close_current_tab(self):
        self.close_tab(self.get_current_tab())

    def quit_editor(self):
        if not messagebox.askyesno("退出", "确定要退出程序吗？", parent=self.root):
            return
        for frame in self.notebook.winfo_children():
            self.notebook.select(frame)
            if getattr(frame, 'is_modified', False):
                result = messagebox.askyesnocancel("保存文件", f"文件 {self.notebook.tab(frame, 'text')} 已修改，是否保存？",
                                                   parent=self.root)
                if result is None:
                    return
                elif result:
                    self.save_file()
        self.root.destroy()

    # ---------- 查找替换 ----------
    def find_replace(self, replace_focus=False, initial_text="", position=None):
        """
        打开查找/替换窗口
        :param replace_focus: 是否聚焦替换框
        :param initial_text: 预置的查找文本
        :param position: (x, y) 屏幕坐标，用于定位窗口
        """
        text_widget = self.get_text_widget()
        if not text_widget:
            return

        top = tk.Toplevel(self.root)
        top.title("查找/替换")
        top.transient(self.root)
        top.grab_set()
        top.resizable(False, False)

        # 如果提供了位置，将窗口移动到该位置
        if position and position[0] is not None and position[1] is not None:
            top.geometry(f"+{position[0]}+{position[1]}")
        else:
            # 默认居中
            top.update_idletasks()
            x = (top.winfo_screenwidth() - top.winfo_reqwidth()) // 2
            y = (top.winfo_screenheight() - top.winfo_reqheight()) // 2
            top.geometry(f"+{x}+{y}")

        # 主框架使用ttk
        main_frame = ttk.Frame(top, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        ttk.Label(main_frame, text="查找:").grid(row=0, column=0, sticky=tk.E, padx=5, pady=5)
        find_entry = ttk.Entry(main_frame, width=30)
        find_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=3, sticky=tk.W)
        if initial_text:
            find_entry.insert(0, initial_text)
            find_entry.select_range(0, tk.END)

        ttk.Label(main_frame, text="替换:").grid(row=1, column=0, sticky=tk.E, padx=5, pady=5)
        replace_entry = ttk.Entry(main_frame, width=30)
        replace_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=3, sticky=tk.W)

        # 选项
        case_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(main_frame, text="区分大小写", variable=case_var).grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5)

        direction_var = tk.StringVar(value="down")
        ttk.Radiobutton(main_frame, text="向下", variable=direction_var, value="down").grid(row=2, column=3, sticky=tk.W)
        ttk.Radiobutton(main_frame, text="向上", variable=direction_var, value="up").grid(row=2, column=4, sticky=tk.W)

        def remove_highlights():
            text_widget.tag_remove('found', '1.0', tk.END)
            text_widget.tag_remove('all_matches', '1.0', tk.END)

        def highlight_all():
            remove_highlights()
            find_text = find_entry.get()
            if not find_text:
                return
            start = '1.0'
            while True:
                pos = text_widget.search(find_text, start, stopindex=tk.END, nocase=not case_var.get())
                if not pos:
                    break
                end = f"{pos}+{len(find_text)}c"
                text_widget.tag_add('all_matches', pos, end)
                start = end
            text_widget.tag_config('all_matches', background='light blue')

        def find_next():
            remove_highlights()
            find_text = find_entry.get()
            if not find_text:
                return
            try:
                if direction_var.get() == "down":
                    start = text_widget.index(tk.SEL_FIRST) if text_widget.tag_ranges(tk.SEL) else text_widget.index(tk.INSERT)
                else:
                    # 向上搜索需要处理，简单实现：从光标前开始搜索
                    cursor = text_widget.index(tk.INSERT)
                    start = "1.0"
                    stop = cursor
            except tk.TclError:
                start = text_widget.index(tk.INSERT)

            if direction_var.get() == "down":
                pos = text_widget.search(find_text, start, stopindex=tk.END, nocase=not case_var.get())
                if not pos:
                    pos = text_widget.search(find_text, '1.0', stopindex=tk.END, nocase=not case_var.get())
            else:
                # 向上搜索：需要逆向查找，这里简化：先找全部，取最后一个在光标前的
                pos = None
                last_pos = None
                p = '1.0'
                while True:
                    p = text_widget.search(find_text, p, stopindex=tk.END, nocase=not case_var.get())
                    if not p:
                        break
                    if text_widget.compare(p, "<", start):
                        last_pos = p
                    else:
                        break
                    p = f"{p}+1c"
                pos = last_pos

            if pos:
                end = f"{pos}+{len(find_text)}c"
                text_widget.tag_add('found', pos, end)
                text_widget.tag_config('found', background='yellow')
                text_widget.mark_set(tk.INSERT, end)
                text_widget.see(pos)
            else:
                messagebox.showinfo("查找", "未找到匹配项", parent=top)

        def replace_current():
            find_text = find_entry.get()
            replace_text = replace_entry.get()
            if not find_text:
                return
            try:
                selected = text_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                if selected == find_text or (not case_var.get() and selected.lower() == find_text.lower()):
                    text_widget.delete(tk.SEL_FIRST, tk.SEL_LAST)
                    text_widget.insert(tk.INSERT, replace_text)
                    text_widget.mark_set(tk.INSERT, f"{tk.INSERT}+{len(replace_text)}c")
            except tk.TclError:
                pass
            find_next()

        def replace_all():
            find_text = find_entry.get()
            replace_text = replace_entry.get()
            if not find_text:
                return
            remove_highlights()
            # 为避免破坏撤销栈过深，这里使用一次性替换，但保留撤销步骤为一个整体
            text_widget.edit_separator()
            content = text_widget.get(1.0, tk.END)
            if case_var.get():
                new_content = content.replace(find_text, replace_text)
            else:
                pattern = re.compile(re.escape(find_text), re.IGNORECASE)
                new_content = pattern.sub(replace_text, content)
            text_widget.delete(1.0, tk.END)
            text_widget.insert(1.0, new_content)
            text_widget.edit_separator()
            find_next()

        # 按钮行
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=5, pady=10)

        ttk.Button(btn_frame, text="查找下一个", command=find_next).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="替换", command=replace_current).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="替换全部", command=replace_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="全部高亮", command=highlight_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="关闭", command=top.destroy).pack(side=tk.LEFT, padx=2)

        if replace_focus:
            replace_entry.focus_set()
        else:
            find_entry.focus_set()

    # ---------- 字体选择 ----------
    def choose_font(self):
        font_window = tk.Toplevel(self.root)
        font_window.title("选择字体")
        font_window.geometry("400x300")
        font_window.resizable(False, False)
        font_window.transient(self.root)
        font_window.grab_set()

        main_frame = ttk.Frame(font_window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="字体:").grid(row=0, column=0, sticky=tk.W, pady=5)
        font_list = sorted(list(font.families()))
        font_combo = ttk.Combobox(main_frame, values=font_list, state="readonly", width=30)
        font_combo.set(self.current_font_family)
        font_combo.grid(row=0, column=1, pady=5, padx=5)

        ttk.Label(main_frame, text="大小:").grid(row=1, column=0, sticky=tk.W, pady=5)
        size_spin = ttk.Spinbox(main_frame, from_=6, to=72, width=10)
        size_spin.set(self.current_font_size)
        size_spin.grid(row=1, column=1, sticky=tk.W, pady=5, padx=5)

        preview_text = "AaBbCc 中文示例 123"
        preview_label = ttk.Label(main_frame, text=preview_text, anchor=tk.CENTER, relief=tk.SUNKEN, padding=10)
        preview_label.grid(row=2, column=0, columnspan=2, pady=10, sticky=tk.EW)

        def update_preview(event=None):
            try:
                f = (font_combo.get(), int(size_spin.get()))
                preview_label.config(font=f)
            except:
                pass

        font_combo.bind("<<ComboboxSelected>>", update_preview)
        size_spin.bind("<KeyRelease>", update_preview)
        update_preview()

        def apply_font():
            self.current_font_family = font_combo.get()
            self.current_font_size = int(size_spin.get())
            for tab in self.notebook.winfo_children():
                tab.text.config(font=(self.current_font_family, self.current_font_size))
            font_window.destroy()

        ttk.Button(main_frame, text="应用", command=apply_font).grid(row=3, column=0, columnspan=2, pady=10)

    # ---------- 自动换行切换 ----------
    def toggle_word_wrap(self):
        wrap_mode = tk.WORD if self.word_wrap_var.get() else tk.NONE
        for tab in self.notebook.winfo_children():
            tab.text.config(wrap=wrap_mode)

    # ---------- 状态栏信息更新 ----------
    def _update_status_info(self):
        text = self.get_text_widget()
        if text:
            try:
                # 光标位置
                line, col = text.index(tk.INSERT).split(".")
                self.cursor_label.config(text=f"行: {line} 列: {int(col)+1}")

                # 选中字符数
                try:
                    sel_start, sel_end = text.tag_ranges(tk.SEL)
                    sel_text = text.get(sel_start, sel_end)
                    sel_len = len(sel_text)
                except (ValueError, AttributeError):
                    sel_len = 0
                self.selection_label.config(text=f"选中: {sel_len}")

                # 总字符数
                content = text.get(1.0, tk.END)
                total = len(content) - 1
                self.total_chars_label.config(text=f"总字符: {total}")
            except:
                pass
        self.root.after(200, self._update_status_info)

if __name__ == "__main__":
    root = tk.Tk()
    editor = TabTextEditor(root)
    root.mainloop()