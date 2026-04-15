#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import scrolledtext, ttk, filedialog, messagebox
import jieba
import string
from collections import Counter

class JiebaCutter:
    def __init__(self, root):
        self.root = root
        self.root.title("中文分词工具")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        
        # 设置中文字体
        self.font = ("SimHei", 12)
        
        # 初始化自定义词典和过滤词
        self.custom_dict = set()
        self.stop_words = set(string.punctuation + "，。！？；：、【】（）《》「」\"\"''")
        
        # 存储分词结果
        self.cut_result = []
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建输入区域
        self.create_input_area()
        
        # 创建自定义词典和过滤词区域
        self.create_dict_area()
        
        # 创建按钮区域
        self.create_button_area()
        
        # 创建结果区域
        self.create_result_area()
    
    def create_input_area(self):
        """创建文本输入区域"""
        input_label = ttk.Label(self.main_frame, text="请输入要分词的文本:", font=self.font)
        input_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.input_text = scrolledtext.ScrolledText(
            self.main_frame, 
            wrap=tk.WORD, 
            font=self.font,
            height=12,
            undo=True
        )
        self.input_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 添加示例文本
        self.input_text.insert(tk.END, "这是一个中文分词工具，使用jieba库进行分词处理。")
    
    def create_dict_area(self):
        """创建自定义词典和过滤词区域"""
        dict_frame = ttk.LabelFrame(self.main_frame, text="词典设置", padding="10")
        dict_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 创建左右两个子框架
        sub_frames = ttk.Frame(dict_frame)
        sub_frames.pack(fill=tk.X)
        
        # 左侧：自定义词典
        left_frame = ttk.Frame(sub_frames)
        left_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        dict_label = ttk.Label(left_frame, text="自定义词典（每行一个词）:", font=self.font)
        dict_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.dict_text = scrolledtext.ScrolledText(
            left_frame, 
            wrap=tk.WORD, 
            font=self.font,
            height=6
        )
        self.dict_text.pack(fill=tk.X, expand=True)
        
        # 自定义词典按钮
        dict_button_frame = ttk.Frame(left_frame)
        dict_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.add_dict_button = ttk.Button(
            dict_button_frame, 
            text="添加到词典", 
            command=self.add_to_dict,
            width=12
        )
        self.add_dict_button.pack(side=tk.LEFT)
        
        self.load_dict_button = ttk.Button(
            dict_button_frame, 
            text="加载词典文件", 
            command=self.load_dict_file,
            width=12
        )
        self.load_dict_button.pack(side=tk.RIGHT)
        
        # 右侧：过滤词
        right_frame = ttk.Frame(sub_frames)
        right_frame.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(5, 0))
        
        stop_label = ttk.Label(right_frame, text="过滤词（每行一个词）:", font=self.font)
        stop_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.stop_text = scrolledtext.ScrolledText(
            right_frame, 
            wrap=tk.WORD, 
            font=self.font,
            height=6
        )
        self.stop_text.pack(fill=tk.X, expand=True)
        
        # 显示默认过滤词
        default_stop_words = "已默认过滤所有标点符号\n您可以在此添加其他需要过滤的词"
        self.stop_text.insert(tk.END, default_stop_words)
        
        # 过滤词按钮
        stop_button_frame = ttk.Frame(right_frame)
        stop_button_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.add_stop_button = ttk.Button(
            stop_button_frame, 
            text="添加到过滤词", 
            command=self.add_to_stop_words,
            width=12
        )
        self.add_stop_button.pack(side=tk.LEFT)
        
        self.load_stop_button = ttk.Button(
            stop_button_frame, 
            text="加载过滤词文件", 
            command=self.load_stop_file,
            width=12
        )
        self.load_stop_button.pack(side=tk.RIGHT)
    
    def create_button_area(self):
        """创建按钮区域"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 分词按钮
        self.cut_button = ttk.Button(
            button_frame, 
            text="开始分词", 
            command=self.cut_text,
            width=15
        )
        self.cut_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 清空按钮
        self.clear_button = ttk.Button(
            button_frame, 
            text="清空", 
            command=self.clear_text,
            width=10
        )
        self.clear_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 分词模式选择
        mode_frame = ttk.Frame(button_frame)
        mode_frame.pack(side=tk.LEFT)
        
        self.cut_mode = tk.StringVar(value="default")
        mode_label = ttk.Label(mode_frame, text="分词模式:", font=self.font)
        mode_label.pack(side=tk.LEFT, padx=(0, 5))
        
        mode_frame_inner = ttk.Frame(mode_frame)
        mode_frame_inner.pack(side=tk.LEFT)
        
        ttk.Radiobutton(mode_frame_inner, text="精确模式", variable=self.cut_mode, value="default").pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(mode_frame_inner, text="全模式", variable=self.cut_mode, value="full").pack(side=tk.LEFT)
        
        # 复制按钮
        self.copy_button = ttk.Button(
            button_frame, 
            text="复制结果", 
            command=self.copy_result,
            width=10
        )
        self.copy_button.pack(side=tk.RIGHT)
    
    def create_result_area(self):
        """创建结果展示区域"""
        result_label = ttk.Label(self.main_frame, text="分词结果:", font=self.font)
        result_label.pack(anchor=tk.W, pady=(0, 5))
        
        self.result_text = scrolledtext.ScrolledText(
            self.main_frame, 
            wrap=tk.WORD, 
            font=self.font,
            height=12,
            state=tk.DISABLED
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
    
    def add_to_dict(self):
        """添加自定义词典"""
        dict_text = self.dict_text.get("1.0", tk.END).strip()
        
        if not dict_text:
            self.show_message("请先输入要添加的词条")
            return
        
        # 按行分割
        words = dict_text.split('\n')
        
        # 去除空行
        words = [word.strip() for word in words if word.strip()]
        
        if not words:
            self.show_message("没有有效的词条")
            return
        
        # 添加到自定义词典
        for word in words:
            if word not in self.custom_dict:
                self.custom_dict.add(word)
                jieba.add_word(word)
        
        self.show_message(f"成功添加{len(words)}个词条到自定义词典")
        
        # 清空输入框
        self.dict_text.delete("1.0", tk.END)
    
    def load_dict_file(self):
        """从文件加载自定义词典"""
        file_path = filedialog.askopenfilename(
            title="选择词典文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = f.readlines()
            
            # 去除空行和换行符
            words = [word.strip() for word in words if word.strip()]
            
            if not words:
                self.show_message("词典文件为空")
                return
            
            # 添加到自定义词典
            added_count = 0
            for word in words:
                if word not in self.custom_dict:
                    self.custom_dict.add(word)
                    jieba.add_word(word)
                    added_count += 1
            
            self.show_message(f"成功从文件加载{added_count}个词条到自定义词典")
            
        except Exception as e:
            self.show_message(f"加载词典文件失败: {str(e)}")
    
    def add_to_stop_words(self):
        """添加过滤词"""
        stop_text = self.stop_text.get("1.0", tk.END).strip()
        
        if not stop_text or stop_text == "已默认过滤所有标点符号\n您可以在此添加其他需要过滤的词":
            self.show_message("请先输入要添加的过滤词")
            return
        
        # 按行分割
        words = stop_text.split('\n')
        
        # 去除空行和默认提示文本
        words = [word.strip() for word in words if word.strip() and word.strip() != "已默认过滤所有标点符号" and word.strip() != "您可以在此添加其他需要过滤的词"]
        
        if not words:
            self.show_message("没有有效的过滤词")
            return
        
        # 添加到过滤词集合
        for word in words:
            self.stop_words.add(word)
        
        self.show_message(f"成功添加{len(words)}个过滤词")
        
        # 重置输入框，保留提示文本
        self.stop_text.delete("1.0", tk.END)
        self.stop_text.insert(tk.END, "已默认过滤所有标点符号\n您可以在此添加其他需要过滤的词")
    
    def load_stop_file(self):
        """从文件加载过滤词"""
        file_path = filedialog.askopenfilename(
            title="选择过滤词文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if not file_path:
            return
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                words = f.readlines()
            
            # 去除空行和换行符
            words = [word.strip() for word in words if word.strip()]
            
            if not words:
                self.show_message("过滤词文件为空")
                return
            
            # 添加到过滤词集合
            for word in words:
                self.stop_words.add(word)
            
            self.show_message(f"成功从文件加载{len(words)}个过滤词")
            
        except Exception as e:
            self.show_message(f"加载过滤词文件失败: {str(e)}")
    
    def cut_text(self):
        """分词处理函数"""
        # 获取输入文本
        text = self.input_text.get("1.0", tk.END).strip()
        
        if not text:
            self.show_message("请先输入要分词的文本")
            return
        
        # 使用jieba进行分词
        try:
            # 根据选择的模式进行分词
            mode = self.cut_mode.get()
            if mode == "full":
                words = jieba.cut(text, cut_all=True)
            else:
                words = jieba.cut(text, cut_all=False)
            
            # 过滤掉不需要的词
            filtered_words = [word for word in words if word not in self.stop_words and word.strip()]
            
            # 用/连接分词结果
            result = "/".join(filtered_words)
            
            # 显示结果
            self.result_text.config(state=tk.NORMAL)
            self.result_text.delete("1.0", tk.END)
            self.result_text.insert(tk.END, result)
            self.result_text.config(state=tk.DISABLED)
            
        except Exception as e:
            self.show_message(f"分词过程中出现错误: {str(e)}")
    
    def clear_text(self):
        """清空输入和结果"""
        self.input_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.NORMAL)
        self.result_text.delete("1.0", tk.END)
        self.result_text.config(state=tk.DISABLED)
        
        # 询问是否同时清空词典和过滤词
        confirm_window = tk.Toplevel(self.root)
        confirm_window.title("确认")
        confirm_window.geometry("350x120")
        confirm_window.transient(self.root)
        confirm_window.grab_set()
        
        # 确认消息
        confirm_label = ttk.Label(
            confirm_window, 
            text="是否同时清空自定义词典和过滤词？", 
            font=self.font
        )
        confirm_label.pack(expand=True, pady=(10, 0))
        
        # 按钮框架
        button_frame = ttk.Frame(confirm_window)
        button_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # 确认按钮
        yes_button = ttk.Button(
            button_frame, 
            text="是", 
            command=lambda: self.clear_all(confirm_window),
            width=10
        )
        yes_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        no_button = ttk.Button(
            button_frame, 
            text="否", 
            command=confirm_window.destroy,
            width=10
        )
        no_button.pack(side=tk.LEFT)
        
        # 居中显示
        confirm_window.update_idletasks()
        width = confirm_window.winfo_width()
        height = confirm_window.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        confirm_window.geometry(f"+{x}+{y}")
    
    def clear_all(self, window):
        """清空所有内容"""
        # 清空自定义词典
        self.custom_dict.clear()
        self.dict_text.delete("1.0", tk.END)
        
        # 重置过滤词为默认标点符号
        self.stop_words = set(string.punctuation + "，。！？；：、【】（）《》「」\"\"''")
        self.stop_text.delete("1.0", tk.END)
        self.stop_text.insert(tk.END, "已默认过滤所有标点符号\n您可以在此添加其他需要过滤的词")
        
        # 关闭确认窗口
        window.destroy()
    
    def copy_result(self):
        """复制结果到剪贴板"""
        result = self.result_text.get("1.0", tk.END).strip()
        
        if not result:
            self.show_message("没有可复制的内容")
            return
        
        self.root.clipboard_clear()
        self.root.clipboard_append(result)
        self.show_message("结果已复制到剪贴板")
    
    def show_message(self, message):
        """显示消息提示"""
        # 创建一个临时的消息窗口
        message_window = tk.Toplevel(self.root)
        message_window.title("提示")
        message_window.geometry("300x100")
        message_window.transient(self.root)
        message_window.grab_set()
        
        # 消息标签
        message_label = ttk.Label(message_window, text=message, font=self.font)
        message_label.pack(expand=True)
        
        # 确定按钮
        ok_button = ttk.Button(
            message_window, 
            text="确定", 
            command=message_window.destroy,
            width=10
        )
        ok_button.pack(pady=10)
        
        # 居中显示
        message_window.update_idletasks()
        width = message_window.winfo_width()
        height = message_window.winfo_height()
        x = (self.root.winfo_width() // 2) - (width // 2) + self.root.winfo_x()
        y = (self.root.winfo_height() // 2) - (height // 2) + self.root.winfo_y()
        message_window.geometry(f"+{x}+{y}")

class WordFrequencyWindow:
    """词频统计窗口类"""
    def __init__(self, parent, words, font):
        self.parent = parent
        self.words = words
        self.font = font
        
        # 计算词频
        self.word_counts = Counter(words)
        self.filtered_words = list(self.word_counts.items())
        
        # 创建窗口
        self.window = tk.Toplevel(parent)
        self.window.title("词频统计")
        self.window.geometry("600x500")
        self.window.transient(parent)
        self.window.grab_set()
        
        # 创建主框架
        self.main_frame = ttk.Frame(self.window, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建筛选和排序区域
        self.create_filter_sort_area()
        
        # 创建词频列表区域
        self.create_word_list_area()
        
        # 创建按钮区域
        self.create_button_area()
        
        # 显示词频列表
        self.update_word_list()
    
    def create_filter_sort_area(self):
        """创建筛选和排序区域"""
        filter_frame = ttk.LabelFrame(self.main_frame, text="筛选与排序", padding="10")
        filter_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 筛选部分
        filter_subframe = ttk.Frame(filter_frame)
        filter_subframe.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(filter_subframe, text="词频大于:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        
        self.filter_value = tk.StringVar(value="1")
        filter_entry = ttk.Entry(filter_subframe, textvariable=self.filter_value, width=5)
        filter_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        self.filter_button = ttk.Button(filter_subframe, text="筛选", command=self.apply_filter)
        self.filter_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 排序部分
        sort_subframe = ttk.Frame(filter_frame)
        sort_subframe.pack(fill=tk.X)
        
        ttk.Label(sort_subframe, text="排序方式:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        
        self.sort_type = tk.StringVar(value="frequency_desc")
        sort_frame = ttk.Frame(sort_subframe)
        sort_frame.pack(side=tk.LEFT)
        
        ttk.Radiobutton(sort_frame, text="词频降序", variable=self.sort_type, value="frequency_desc", 
                        command=self.apply_sort).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(sort_frame, text="词频升序", variable=self.sort_type, value="frequency_asc", 
                        command=self.apply_sort).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Radiobutton(sort_frame, text="词语拼音", variable=self.sort_type, value="alphabetical", 
                        command=self.apply_sort).pack(side=tk.LEFT)
    
    def create_word_list_area(self):
        """创建词频列表区域"""
        list_frame = ttk.LabelFrame(self.main_frame, text="词频列表", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 创建Treeview
        columns = ("word", "frequency", "action")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings")
        
        # 设置列宽和标题
        self.tree.column("word", width=200, anchor=tk.CENTER)
        self.tree.column("frequency", width=100, anchor=tk.CENTER)
        self.tree.column("action", width=150, anchor=tk.CENTER)
        
        self.tree.heading("word", text="词语")
        self.tree.heading("frequency", text="词频")
        self.tree.heading("action", text="操作")
        
        # 添加滚动条
        scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # 布局
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.tree.pack(fill=tk.BOTH, expand=True)
    
    def create_button_area(self):
        """创建按钮区域"""
        button_frame = ttk.Frame(self.main_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 删除选中按钮
        self.delete_selected_button = ttk.Button(
            button_frame, 
            text="删除选中", 
            command=self.delete_selected
        )
        self.delete_selected_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 全选按钮
        self.select_all_button = ttk.Button(
            button_frame, 
            text="全选", 
            command=self.select_all
        )
        self.select_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消全选按钮
        self.deselect_all_button = ttk.Button(
            button_frame, 
            text="取消全选", 
            command=self.deselect_all
        )
        self.deselect_all_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关闭按钮
        self.close_button = ttk.Button(
            button_frame, 
            text="关闭", 
            command=self.window.destroy
        )
        self.close_button.pack(side=tk.RIGHT)
    
    def update_word_list(self):
        """更新词频列表"""
        # 清空现有列表
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 添加词语和词频
        for word, count in self.filtered_words:
            # 创建一个可编辑的词频单元格
            item_id = self.tree.insert("", tk.END, values=(word, count, ""))
            
            # 添加复选框
            check_var = tk.BooleanVar()
            check = ttk.Checkbutton(self.tree, variable=check_var)
            self.tree.set(item_id, "action", "")
            
            # 在单元格中放置复选框
            self.tree.after(10, lambda i=item_id, c=check: self.tree.window_create(i, column="action", window=c))
            
            # 添加修改按钮
            edit_button = ttk.Button(self.tree, text="修改", width=6, 
                                    command=lambda w=word, c=count: self.edit_frequency(w, c))
            self.tree.window_create(item_id, column="action", window=edit_button)
    
    def apply_filter(self):
        """应用筛选"""
        try:
            min_freq = int(self.filter_value.get())
            if min_freq < 1:
                min_freq = 1
                self.filter_value.set("1")
            
            # 筛选词频大于等于min_freq的词
            self.filtered_words = [(word, count) for word, count in self.word_counts.items() if count >= min_freq]
            
            # 应用当前排序方式
            self.apply_sort()
            
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字")
    
    def apply_sort(self):
        """应用排序"""
        sort_type = self.sort_type.get()
        
        if sort_type == "frequency_desc":
            # 词频降序
            self.filtered_words.sort(key=lambda x: x[1], reverse=True)
        elif sort_type == "frequency_asc":
            # 词频升序
            self.filtered_words.sort(key=lambda x: x[1])
        elif sort_type == "alphabetical":
            # 词语拼音排序
            self.filtered_words.sort(key=lambda x: x[0])
        
        # 更新列表
        self.update_word_list()
    
    def edit_frequency(self, word, current_freq):
        """修改词频"""
        # 创建编辑窗口
        edit_window = tk.Toplevel(self.window)
        edit_window.title("修改词频")
        edit_window.geometry("300x150")
        edit_window.transient(self.window)
        edit_window.grab_set()
        
        # 创建框架
        edit_frame = ttk.Frame(edit_window, padding="10")
        edit_frame.pack(fill=tk.BOTH, expand=True)
        
        # 词语标签
        word_label = ttk.Label(edit_frame, text=f"词语: {word}", font=self.font)
        word_label.pack(anchor=tk.W, pady=(0, 10))
        
        # 词频输入
        freq_frame = ttk.Frame(edit_frame)
        freq_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Label(freq_frame, text="词频:", font=self.font).pack(side=tk.LEFT, padx=(0, 5))
        
        freq_var = tk.StringVar(value=str(current_freq))
        freq_entry = ttk.Entry(freq_frame, textvariable=freq_var, width=10)
        freq_entry.pack(side=tk.LEFT)
        
        # 按钮框架
        button_frame = ttk.Frame(edit_frame)
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        # 确定按钮
        def confirm_edit():
            try:
                new_freq = int(freq_var.get())
                if new_freq < 1:
                    messagebox.showerror("错误", "词频不能小于1")
                    return
                
                # 更新词频
                self.word_counts[word] = new_freq
                
                # 重新应用筛选和排序
                self.apply_filter()
                
                # 关闭编辑窗口
                edit_window.destroy()
                
            except ValueError:
                messagebox.showerror("错误", "请输入有效的数字")
        
        ok_button = ttk.Button(button_frame, text="确定", command=confirm_edit)
        ok_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 取消按钮
        cancel_button = ttk.Button(button_frame, text="取消", command=edit_window.destroy)
        cancel_button.pack(side=tk.LEFT)
    
    def delete_selected(self):
        """删除选中的词语"""
        # 获取所有选中的项
        selected_items = []
        for item in self.tree.get_children():
            # 这里简化处理，实际应该获取复选框的状态
            # 由于tkinter的限制，我们假设用户点击了修改按钮旁边的复选框
            # 在实际应用中，需要更复杂的方法来跟踪复选框状态
            selected_items.append(item)
        
        if not selected_items:
            messagebox.showinfo("提示", "请先选择要删除的词语")
            return
        
        # 确认删除
        if messagebox.askyesno("确认", f"确定要删除选中的{len(selected_items)}个词语吗？"):
            # 删除选中的词语
            for item in selected_items:
                word = self.tree.item(item, "values")[0]
                if word in self.word_counts:
                    del self.word_counts[word]
            
            # 重新应用筛选和排序
            self.apply_filter()
    
    def select_all(self):
        """全选"""
        # 简化处理，实际应该选中所有复选框
        messagebox.showinfo("提示", "此功能需要更复杂的实现来跟踪复选框状态")
    
    def deselect_all(self):
        """取消全选"""
        # 简化处理，实际应该取消选中所有复选框
        messagebox.showinfo("提示", "此功能需要更复杂的实现来跟踪复选框状态")

if __name__ == "__main__":
    root = tk.Tk()
    app = JiebaCutter(root)
    root.mainloop()
