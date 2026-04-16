import tkinter as tk
from tkinter import filedialog, simpledialog, ttk, messagebox
from PIL import Image, ImageTk, ImageGrab
import cv2
import numpy as np
import pyautogui
import time
import threading
import logging
from logging.handlers import RotatingFileHandler
import os
import json
import atexit
from datetime import datetime
import shutil
import keyboard
 
class ImageRecognitionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("图像识别与点击")
        self.image_list = []  # 存储 (图像路径, 步骤名称, 相似度, 键盘输入, 鼠标点击坐标, 等待时间, 条件, 跳转步骤)
        self.screenshot_area = None  # 用于存储截图区域
        self.rect = None  # 用于存储 Canvas 上的矩形
        self.start_x = None
        self.start_y = None
        self.canvas = None
        self.running = False  # 控制脚本是否在运行
        self.thread = None  # 用于保存线程
        self.hotkey = '<F1>'  # 默认热键
        self.similarity_threshold = 0.8  # 默认相似度阈值
        self.delay_time = 0.1  # 默认延迟时间
        self.loop_count = 1  # 默认循环次数
        self.screenshot_folder = 'screenshots'  # 截图保存文件夹
        self.paused = False  # 控制脚本是否暂停
        self.copied_item = None
        self.config_filename = 'config.json'  # 默认配置文件名
        self.start_step_index = 0  # 初始化
        self.follow_current_step = tk.BooleanVar(value=False)  # 控制是否跟随当前步骤
        self.only_keyboard_var = tk.BooleanVar(value=False)  # 控制是否只进行键盘操作
        self.init_ui()
        self.tree.image_refs = []  # 初始化 image_refs 属性
        self.init_logging()
        self.bind_arrow_keys()
        self.create_context_menu()
        atexit.register(self.cleanup_on_exit)
        self.hotkey_id = None # 初始化热键id
        self.register_global_hotkey() # 注册全局热键
 
    def init_ui(self):
        # 主框架布局
        self.main_frame = tk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
 
        # 左侧布局：框选截图、运行脚本按钮
        self.left_frame = tk.Frame(self.main_frame)
        self.left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
 
        # 框选截图按钮（微信风格截图）
        self.screenshot_button = tk.Button(self.left_frame, text="框选截图", command=self.prepare_capture_screenshot)
        self.screenshot_button.pack(pady=5)
 
        # 删除选中图片按钮
        self.delete_button = tk.Button(self.left_frame, text="删除图片", command=self.delete_selected_image)
        self.delete_button.pack(pady=5)
 
        # 运行/停止脚本按钮
        self.toggle_run_button = tk.Button(self.left_frame, text="开始运行", command=self.toggle_script)
        self.toggle_run_button.pack(pady=5)
 
        # 保存配置按钮
        self.save_config_button = tk.Button(self.left_frame, text="保存配置", command=self.save_config)
        self.save_config_button.pack(pady=5)
 
        # 设置热键按钮
        self.set_hotkey_button = tk.Button(self.left_frame, text="设置热键", command=self.set_hotkey)
        self.set_hotkey_button.pack(pady=5)
 
        # 手动加载配置按钮
        self.load_config_button = tk.Button(self.left_frame, text="加载配置", command=self.load_config_manually)
        self.load_config_button.pack(pady=5)
 
        # 循环次数输入框
        self.loop_count_label = tk.Label(self.left_frame, text="循环次数:")
        self.loop_count_label.pack(pady=5)
        self.loop_count_entry = tk.Entry(self.left_frame)
        self.loop_count_entry.insert(0, str(self.loop_count))
        self.loop_count_entry.pack(pady=5)
 
        # 添加测试匹配按钮
        self.test_match_button = tk.Button(self.left_frame, text="测试匹配", command=self.test_single_match)
        self.test_match_button.pack(pady=5)
 
        # 添加允许最小化和跟随当前步骤的勾选框
        self.allow_minimize_var = tk.BooleanVar(value=True)  # 默认允许最小化
        self.allow_minimize_checkbox = tk.Checkbutton(self.left_frame, text="允许最小化", variable=self.allow_minimize_var)
        self.allow_minimize_checkbox.pack(side=tk.LEFT, pady=5)
 
        self.follow_step_checkbox = tk.Checkbutton(self.left_frame, text="焦点跟随", variable=self.follow_current_step)
        self.follow_step_checkbox.pack(side=tk.LEFT, pady=5)  # 跟随当前步骤勾选框
 
        # 只键盘操作勾选框
        self.only_keyboard_checkbox = tk.Checkbutton(self.left_frame, text="只键盘操作", variable=self.only_keyboard_var)
        self.only_keyboard_checkbox.pack(side=tk.LEFT, pady=5)
 
        # 右侧布局：框架分为预览区和树形视图区
        self.right_frame = tk.Frame(self.main_frame)
        self.right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
 
        # 创建右侧预览面板
        self.preview_panel = tk.Frame(self.right_frame, width=120, height=120,
                                    relief=tk.GROOVE, borderwidth=1)  # 添加边框效果
        self.preview_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))  # 调整右侧边距
        self.preview_panel.pack_propagate(False)
          
        # 使用更现代的标签样式
        self.preview_label = tk.Label(self.preview_panel, text="图像预览",
                                    font=('Arial', 9), fg='#666666')
        self.preview_label.pack(pady=3)
          
        # 创建预览图像容器
        self.preview_container = tk.Frame(self.preview_panel, 
                                        width=100, height=100,
                                        relief=tk.SUNKEN, borderwidth=1)
        self.preview_container.pack(pady=2)
        self.preview_container.pack_propagate(False)
          
        self.preview_image_label = tk.Label(self.preview_container, bg='#f5f5f5')
        self.preview_image_label.pack(expand=True)
 
        # 使用 Treeview 来显示图片和等待时间（调整包装方式）
        self.tree = ttk.Treeview(self.right_frame, columns=(
            "图片", "步骤名称", "相似度", "键盘输入", "鼠标点击坐标", "等待时间", "条件", "跳转步骤"
        ), show='headings')
        self.tree.heading("图片", text="图片")
        self.tree.heading("步骤名称", text="步骤名称")
        self.tree.heading("相似度", text="相似度")
        self.tree.heading("键盘输入", text="键盘输入")
        self.tree.heading("鼠标点击坐标", text="鼠标点击坐标(F2)")
        self.tree.heading("等待时间", text="等待时间 (毫秒)")
        self.tree.heading("条件", text="条件")
        self.tree.heading("跳转步骤", text="跳转步骤")
 
        # 设置列宽和对齐方式（居中）
        self.tree.column("图片", width=100, anchor='center')
        self.tree.column("步骤名称", width=100, anchor='center')
        self.tree.column("相似度", width=80, anchor='center')
        self.tree.column("键盘输入", width=100, anchor='center')
        self.tree.column("鼠标点击坐标", width=130, anchor='center')
        self.tree.column("等待时间", width=100, anchor='center')
        self.tree.column("条件", width=80, anchor='center')
        self.tree.column("跳转步骤", width=80, anchor='center')
           
        # 创建垂直滚动条
        self.scrollbar = ttk.Scrollbar(self.right_frame, orient="vertical", command=self.tree.yview)
        self.scrollbar.pack(side="right", fill="y")
 
        # 配置 Treeview 使用滚动条并调整其位置
        self.tree.configure(yscrollcommand=self.scrollbar.set)
        self.tree.pack(side="left", fill=tk.BOTH, expand=True)
 
        # 绑定 F2 键获取鼠标位置
        self.root.bind('<F2>', self.get_mouse_position)  
 
        # 初始化上下文菜单
        self.tree.unbind('<Double-1>')
        self.tree.unbind('<Double-3>')
        self.tree.unbind('<Double-2>')
 
        # 为上下文菜单添加此绑定
        self.tree.bind('<Button-3>', self.show_context_menu)  # 右键点击
        self.tree.bind('<Button-1>', self.on_treeview_select)  # 左键点击
 
        # 在 Treeview 创建后添加选择事件绑定
        self.tree.bind('<<TreeviewSelect>>', self.on_treeview_select)
 
    def init_logging(self): # 初始化日志
        handler = RotatingFileHandler('app.log', maxBytes=10*1024*1024, backupCount=5)  # 创建日志文件处理器
        logging.basicConfig(handlers=[handler], level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') # 配置日志格式
 
    def register_global_hotkey(self):
        try:
            def hotkey_callback():
                self.root.after(0, self.toggle_script)  # 使用 after 在主线程中调用
             
            # 解析热键字符串
            hotkey_str = self.hotkey.replace('<', '').replace('>', '').lower()
            keyboard.add_hotkey(hotkey_str, hotkey_callback)
             
            print(f"全局热键已注册：{self.hotkey}")
            logging.info(f"全局热键已注册：{self.hotkey}")
        except Exception as e:
            print(f"注册热键失败: {e}")
            logging.error(f"注册热键失败: {e}")
 
    def unregister_global_hotkey(self):
        try:
           hotkey_str = self.hotkey.replace('<', '').replace('>', '').lower()
           keyboard.remove_hotkey(hotkey_str)
           print(f"全局热键已注销：{self.hotkey}")
           logging.info(f"全局热键已注销：{self.hotkey}")
        except Exception as e:
           print(f"注销全局热键出错：{e}")
           logging.error(f"注销全局热键出错：{e}")
 
 
    def prepare_capture_screenshot(self):
        # 在截图前计算新的步骤编号
        existing_steps = set()
        for item in self.image_list:
            step_name = item[1]
            if step_name.startswith("步骤"):
                try:
                    num = int(step_name[2:])  # 提取"步骤"后面的数字
                    existing_steps.add(num)
                except ValueError:
                    continue
           
        # 找到最小的未使用编号
        new_step_num = 1
        while new_step_num in existing_steps:
            new_step_num += 1
           
        # 保存新步骤编号，供 on_button_release 使用
        self._next_step_num = new_step_num
   
        # 隐藏主窗口
        self.root.withdraw()
        time.sleep(0.5)
   
        # 创建一个全屏幕的透明窗口，用于捕获框选区域
        self.top = tk.Toplevel(self.root)
        self.top.attributes('-fullscreen', True)
        self.top.attributes('-alpha', 0.3)  # 透明度设置
   
        # 在窗口上创建 Canvas
        self.canvas = tk.Canvas(self.top, cursor="cross", bg='grey')
        self.canvas.pack(fill=tk.BOTH, expand=True)
   
        # 绑定鼠标事件
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_button_release)
   
    def on_button_press(self, event):
        # 记录起始点坐标
        self.start_x = event.x
        self.start_y = event.y
        # 如果有之前的矩形，删除
        if self.rect:
            self.canvas.delete(self.rect)
        # 创建新的矩形框
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline='red', width=2)
   
    def on_mouse_drag(self, event):
        # 动态更新矩形框的大小
        cur_x, cur_y = (event.x, event.y)
        self.canvas.coords(self.rect, self.start_x, self.start_y, cur_x, cur_y)
   
    def on_button_release(self, event):
        # 记录终点坐标
        end_x = event.x
        end_y = event.y
 
        # 获取截图区域
        bbox = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
 
        # 使用规则 "截图（时间）.png" 命名截图文件避免重复
        timestamp = datetime.now().strftime("%H%M%S")  # 使用当前时间作为文件名
        screenshot_path = os.path.join(self.screenshot_folder, f"JT_{timestamp}.png")
 
        # 确保截图文件夹存在
        os.makedirs(self.screenshot_folder, exist_ok=True)
 
        # 截图指定区域
        screenshot = ImageGrab.grab(bbox)
        screenshot.save(screenshot_path)
 
        # 计算截图区域的中心坐标
        center_x = (min(self.start_x, end_x) + max(self.start_x, end_x)) // 2
        center_y = (min(self.start_y, end_y) + max(self.start_y, end_y)) // 2
        mouse_click_coordinates = f"{center_x},{center_y}"  # 使用中心坐标
 
        # 更新图像列表
        selected_item = self.tree.selection()  # 获取当前选中的项
        step_name = f"步骤{self._next_step_num}"  # 生成递增的步骤名称
        if selected_item:   
            selected_index = self.tree.index(selected_item[0])  
            self.image_list.insert(selected_index, (screenshot_path, step_name, 0.8, "", mouse_click_coordinates, 100, "", ""))  # 在选中项之前插入新项
        else:
            self.image_list.append((screenshot_path, step_name, 0.8, "", mouse_click_coordinates, 100, "", ""))  # 在列表末尾添加新项
        self.update_image_listbox()  # 更新图像列表框
 
        # 关闭全屏透明窗口
        self.top.destroy()
        self.root.deiconify()
   
    def update_image_listbox(self):
        try:
            # 保存当前预览状态
            current_preview = None
            if hasattr(self.preview_image_label, 'image'):
                current_preview = self.preview_image_label.image
              
            # 保存当前选中的项目
            selected_items = self.tree.selection()
            focused_item = self.tree.focus()
   
            # 清空旧的列表项
            for row in self.tree.get_children():
                self.tree.delete(row)
   
            # 插入新项，显示图片名称和等待时间
            for index, item in enumerate(self.image_list):
                try:
                    if not item or len(item) < 1:  # 检查项目是否有效
                        continue
                       
                    img_path = item[0]
                    if not os.path.exists(img_path):
                        print(f"警告：图像文件不存在 {img_path}")
                        logging.warning(f"图像文件不存在 {img_path}")
                        continue
   
                    # 确保每个项目都有 8 个元素，如果没有，用空字符串填充
                    full_item = list(item)
                    while len(full_item) < 8:
                        full_item.append("")
                       
                    img_path, step_name, similarity_threshold, keyboard_input, mouse_click_coordinates, wait_time, condition, jump_to = full_item
   
                    # 加载图像并创建缩略图
                    try:
                        image = Image.open(img_path)
                        image.thumbnail((50, 50))  # 调整缩略图大小
                        photo = ImageTk.PhotoImage(image)
   
                        # 插入所有数据
                        tree_item = self.tree.insert("", tk.END, values=(
                            os.path.basename(img_path), 
                            step_name, 
                            similarity_threshold, 
                            keyboard_input, 
                            mouse_click_coordinates, 
                            wait_time,
                            condition,
                            jump_to
                        ), image=photo)
                        self.tree.image_refs.append(photo)  # 保持对图像的引用
   
                    except Exception as e:
                        print(f"处理图像时出错 {img_path}: {e}")
                        logging.error(f"处理图像时出错 {img_path}: {e}")
   
                except Exception as e:
                    print(f"处理列表项时出错: {e}")
                    logging.error(f"处理列表项时出错: {e}")
   
            # 恢复选择状态
            if selected_items:
                for item in selected_items:
                    try:
                        self.tree.selection_add(item)
                    except:
                        pass
            if focused_item:
                try:
                    self.tree.focus(focused_item)
                except:
                    pass
   
            # 恢复预览状态
            if current_preview:
                self.preview_image_label.config(image=current_preview)
                self.preview_image_label.image = current_preview
              
        except Exception as e:
            print(f"更新图像列表时出错: {e}")
            logging.error(f"更新图像列表时出错: {e}")
            self.reset_to_initial_state()
   
    def delete_selected_image(self):
        try:
            selected_item = self.tree.selection()
            if not selected_item:
                messagebox.showinfo("提示", "请先选择要删除的项目")
                return
   
            selected_index = self.tree.index(selected_item[0])
            if 0 <= selected_index < len(self.image_list):
                selected_image = self.image_list[selected_index]
                img_path = selected_image[0]
                   
                # 检查是否正在使用配置文件
                if hasattr(self, 'config_filename') and os.path.exists(self.config_filename):
                    # 显示确认对话框
                    result = messagebox.askyesnocancel(
                        "确认删除",
                        f"当正在使用配置文件\n{self.config_filename}\n\n是否删除该步骤并更新配置文件？\n\n选择：\n"
                        f"是 - 删除步骤并更新配置文件（同时删除图片文件）\n"
                        f"否 - 仅删除步骤（保留图片文件）\n"
                        f"取消 - 不执行任何操作"
                    )
                       
                    if result is None:  # 用户点击取消
                        return
                       
                    # 删除图像列表中的项目
                    del self.image_list[selected_index]
                       
                    if result:  # 用户点击是，更新配置文件并删除图片
                        try:
                            # 读取现有配置
                            with open(self.config_filename, 'r') as f:
                                config = json.load(f)
                               
                            # 更新配置中的图像列表
                            config['image_list'] = self.image_list
                               
                            # 保存更新后的配置
                            with open(self.config_filename, 'w') as f:
                                json.dump(config, f)
                                   
                            # 检查是否有其他项目引用相同的图像文件
                            is_referenced = any(item[0] == img_path for item in self.image_list)
                               
                            # 如果没有其他引用，则删除图像文件
                            if not is_referenced and os.path.exists(img_path):
                                try:
                                    os.remove(img_path)
                                    print(f"图像文件已删除: {img_path}")
                                    logging.info(f"图像文件已删除: {img_path}")
                                except Exception as e:
                                    print(f"删除图像文件时出错: {e}")
                                    logging.error(f"删除图像文件时出错: {e}")
                               
                            print(f"配置文件已更新: {self.config_filename}")
                            logging.info(f"配置文件已更新: {self.config_filename}")
                            messagebox.showinfo("成功", "步骤已删除，配置文件已更新，图片已删除")
                        except Exception as e:
                            error_msg = f"更新配置文件时出错: {str(e)}"
                            print(error_msg)
                            logging.error(error_msg)
                            messagebox.showerror("错误", error_msg)
                    else:  # 用户点击否，仅删除步骤，保留图片
                        messagebox.showinfo("成功", "步骤已删除（图片文件已保留）")
                else:
                    # 如果没有使用配置文件，直接删除步骤和图片
                    if messagebox.askyesno("确认删除", "是否删除该步骤和对应的图片文件？"):
                        del self.image_list[selected_index]
                        # 检查是否有其他项目引用相同的图像文件
                        is_referenced = any(item[0] == img_path for item in self.image_list)
                        if not is_referenced and os.path.exists(img_path):
                            try:
                                os.remove(img_path)
                                print(f"图像文件已删除: {img_path}")
                                logging.info(f"图像文件已删除: {img_path}")
                            except Exception as e:
                                print(f"删除图像文件时出错: {e}")
                                logging.error(f"删除图像文件时出错: {e}")
                   
                self.update_image_listbox()
            else:
                print("选中的索引超出范围")
                logging.warning("选中的索引超出范围")
        except Exception as e:
            print(f"删除图像时出错: {e}")
            logging.error(f"删除图像时出错: {e}")
            self.reset_to_initial_state()
   
    def toggle_script(self, event=None):
        if not self.running:
            self.start_step_index = 0  # 确保从第一步开始
            self.start_script_thread()
            self.toggle_run_button.config(text="停止运行")
            if self.allow_minimize_var.get():  # 检查勾选框状态
                self.root.iconify()  # 最小化主窗口
            else:
                self.root.lift()  # 确保主窗口在最上层
                self.root.attributes('-topmost', True)  # 设置为最上层窗口
        else:
            self.stop_script()
            self.toggle_run_button.config(text="开始运行")
            self.root.attributes('-topmost', False)  # 取消最上层设置
   
    def start_script_thread(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_script, daemon=True)
            self.thread.start()
   
    def run_script(self):
        try:
            self.loop_count = int(self.loop_count_entry.get())
            if self.loop_count < 0:
                raise ValueError("循环次数不能为负数")
        except ValueError as e:
            messagebox.showerror("输入错误", f"请输入有效的非负整数作为循环次数: {str(e)}")
            self.running = False
            self.root.after(0, self.update_ui_after_stop)
            return
   
        print(f"开始执行脚本，从步骤 {self.start_step_index} 开始，循环次数：{self.loop_count}")
        logging.info(f"开始执行脚本，从步骤 {self.start_step_index} 开始，循环次数：{self.loop_count}")
   
        current_loop = 0
   
        while self.running and (current_loop < self.loop_count or self.loop_count == 0):
            if self.paused:
                time.sleep(0.1)
                continue
         
            index = self.start_step_index
            while index < len(self.image_list) and self.running:
                # 添加焦点跟随功能
                if self.follow_current_step.get():
                    self.root.after(0, lambda idx=index: self.focus_on_step(idx))
                 
                current_step = self.image_list[index]
                img_path, img_name, similarity_threshold, keyboard_input, mouse_click_coordinates, wait_time = current_step[:6]
                condition = current_step[6] if len(current_step) > 6 else None
                jump_to = current_step[7] if len(current_step) > 7 else None
                 
                # 执行一次图像匹配
                if mouse_click_coordinates and not self.only_keyboard_var.get():
                    match_result = self.match_and_click(img_path, similarity_threshold)
                elif os.path.exists(img_path):
                    match_result = self.match_and_click(img_path, similarity_threshold)
                else:
                     match_result = True if keyboard_input else False # 如果没有鼠标操作且有键盘操作，则默认视为匹配成功，否则为失败
 
                # 等待时间处理
                if wait_time > 0:
                    time.sleep(wait_time / 1000.0)  # 将毫秒转换为秒
 
                # 处理键盘输入中的延时
                if keyboard_input:
                    commands = self.parse_keyboard_input(keyboard_input)
                    for cmd in commands:
                        if isinstance(cmd, float):  # 延时
                            time.sleep(cmd)
                        else:
                            # 处理其他键盘输入
                            pyautogui.press(cmd)
 
                # 处理条件跳转
                if condition and jump_to:
                    should_jump = False
                    if condition == "True" and match_result:
                        should_jump = True
                        print(f"条件为True且匹配成功，从{img_name}跳转到{jump_to}")
                    elif condition == "False" and not match_result:
                        should_jump = True
                        print(f"条件为False且匹配失败，从{img_name}跳转到{jump_to}")
                     
                    if should_jump:
                        # 查找跳转目标步骤的索引
                        for i, step in enumerate(self.image_list):
                            if step[1] == jump_to:
                                index = i
                                break
                        continue
                 
                # 如果没有跳转且匹配失败，则持续尝试匹配
                if not match_result and not (condition and jump_to) and not self.only_keyboard_var.get():
                    while not match_result and self.running:
                        time.sleep(wait_time / 1000.0)
                        if mouse_click_coordinates:
                            match_result = self.match_and_click(img_path, similarity_threshold)
                        elif os.path.exists(img_path):
                            match_result = self.match_and_click(img_path, similarity_threshold)
 
                index += 1
 
            current_loop += 1
 
        self.running = False
        self.root.after(0, self.update_ui_after_stop)
   
    def start_script_thread(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self.run_script, daemon=True)
            self.thread.start()
   
    def stop_script(self):
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=1)  # 等待线程结束，最多等待2秒
            if self.thread.is_alive():
                print("警告：脚本线程未能在1秒内停止")
                logging.warning("脚本线程未能在1秒内停运行")
        self.thread = None
        print("脚本已停止")
        logging.info("脚本已停止")
        self.root.after(0, self.update_ui_after_stop)
   
    def update_ui_after_stop(self):
        self.toggle_run_button.config(text="开始运行")
        self.root.deiconify()  # 恢复主窗口
   
    def move_item_up(self, event=None):
        selected_item = self.tree.selection()   
        if selected_item:
            selected_index = self.tree.index(selected_item[0])
            if selected_index > 0:
                   
                self.image_list[selected_index], self.image_list[selected_index - 1] = self.image_list[selected_index - 1], self.image_list[selected_index]
                self.update_image_listbox()
   
                   
                item_id = self.tree.get_children()[selected_index - 1]
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
   
    def move_item_down(self, event=None):
        selected_item = self.tree.selection()
        if selected_item:
            selected_index = self.tree.index(selected_item[0])
            if selected_index < len(self.image_list) - 1:
                   
                self.image_list[selected_index], self.image_list[selected_index + 1] = self.image_list[selected_index + 1], self.image_list[selected_index]
                self.update_image_listbox()
   
                   
                item_id = self.tree.get_children()[selected_index + 1]
                self.tree.selection_set(item_id)
                self.tree.focus(item_id)
   
    def match_and_click(self, template_path, similarity_threshold):
        # 获取当前步骤的完整信息
        selected_index = next((i for i, item in enumerate(self.image_list) if item[0] == template_path), None)
        if selected_index is not None:
            current_step = self.image_list[selected_index]
            mouse_coordinates = current_step[4]  # 获取鼠标坐标
            keyboard_input = current_step[3]  # 获取键盘输入
        else:
            mouse_coordinates = ""
            keyboard_input = ""
 
        # 获取屏幕截图
        screenshot = pyautogui.screenshot()
        screenshot = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
 
        # 读取模板图像
        template = cv2.imread(template_path)
 
        # 执行模板匹配
        result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
 
        # 如果相似度超过阈值
        if max_val >= similarity_threshold:
            # 先处理鼠标点击
            if mouse_coordinates and not self.only_keyboard_var.get():
                try:
                    
                    if ":" in mouse_coordinates:
                        action, coords, is_dynamic = mouse_coordinates.split(":")
                         
                        # 如果是动态点击
                        if is_dynamic == "1":
                           x, y = max_loc[0] + template.shape[1] // 2, max_loc[1] + template.shape[0] // 2 # 计算动态点击中心
                        else:
                            x, y = map(int, coords.split(","))
                             
                        # 执行相应的鼠标操作
                        if action == "click":
                            pyautogui.click(x, y)
                        elif action == "rightClick":
                            # 使用 pyautogui 来模拟真实的右键点击
                            pyautogui.moveTo(x, y)
                            pyautogui.rightClick()
                        elif action == "doubleClick":
                            pyautogui.doubleClick(x, y)
                        elif action == "mouseDown":
                            pyautogui.mouseDown(x, y)
                        elif action == "mouseUp":
                            pyautogui.mouseUp(x, y)
                    else:
                        # 处理旧格式的坐标（向后兼容）
                        x, y = map(int, mouse_coordinates.split(','))
                        pyautogui.click(x, y)
 
                    print(f"执行鼠标操作：{mouse_coordinates}")
                    logging.info(f"执行鼠标操作：{mouse_coordinates}")
                     
                except Exception as e:
                    print(f"鼠标操作时出错: {e}")
                    logging.error(f"鼠标操作时出错: {e}")
                    return False
 
            # 再处理键盘输入
            if keyboard_input:
                try:
                    time.sleep(0.5)  # 等待点击后的界面响应
                     
                    # 解析并执行键盘输入
                    commands = self.parse_keyboard_input(keyboard_input)
                    for cmd in commands:
                        if isinstance(cmd, tuple) and cmd[0] == "hotkey":
                            keys = cmd[1]
                            pyautogui.hotkey(*keys)
                        elif isinstance(cmd, float):  # 延时
                            time.sleep(cmd)
                        else:  # 普通按键或特殊键
                            pyautogui.press(cmd)
                        time.sleep(0.1)  # 按键间短暂延时
                         
                    print(f"执行键盘输入：{keyboard_input}")
                    logging.info(f"执行键盘输入：{keyboard_input}")
                except Exception as e:
                    print(f"键盘输入时出错: {e}")
                    logging.error(f"键盘输入时出错: {e}")
 
            return True
        else:
            print(f"未找到匹配，最大相似度：{max_val}")
            logging.info(f"未找到匹配，最大相似度：{max_val}")
            return False
   
    def parse_keyboard_input(self, input_str):
        """解析键盘输入字符串，返回命令列表"""
        commands = []
        i = 0
        while i < len(input_str):
            if input_str[i] == '{':
                end = input_str.find('}', i)
                if end != -1:
                    cmd = input_str[i+1:end]
                    if cmd.startswith('delay:'):
                        # 处理延时命令
                        try:
                            delay_ms = int(cmd.split(':')[1])
                            commands.append(float(delay_ms / 1000))
                        except ValueError:
                            print(f"无效的延时值: {cmd}")
                    elif '+' in cmd:
                        # 处理组合键
                        keys = cmd.split('+')
                        commands.append(("hotkey", tuple(keys)))
                    else:
                        # 处理特殊键
                        commands.append(cmd)
                    i = end + 1
                    continue
            # 处理普通字符
            commands.append(input_str[i])
            i += 1
        return commands
 
    def add_special_key(self, key):
        current_entry = self.entry.get()
        self.entry.delete(0, tk.END)
        self.entry.insert(0, current_entry + key)
   
    def edit_keyboard_input(self):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.tree.index(selected_item)
            selected_image = self.image_list[selected_index]
 
            # 创建新窗口但不隐藏主窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("修改键盘输入")
            dialog.transient(self.root)
            dialog.grab_set()
             
            # 创建输入框和标签
            input_frame = tk.Frame(dialog)
            input_frame.pack(fill=tk.X, pady=5)
            tk.Label(input_frame, text="键盘输入:").pack(side=tk.LEFT)
            entry = tk.Entry(input_frame, width=30)
            entry.insert(0, selected_image[3])
            entry.pack(side=tk.LEFT, padx=5)
 
            # 创建特殊键按钮框架
            special_keys_frame = tk.LabelFrame(dialog, text="特殊键", padx=5, pady=5)
            special_keys_frame.pack(fill=tk.X, pady=5)
   
            special_keys = [
                'enter', 'tab', 'space', 'backspace', 'delete',
                'esc', 'home', 'end', 'pageup', 'pagedown',
                'up', 'down', 'left', 'right'
            ]
   
            # 创建特殊键按钮
            for i, key in enumerate(special_keys):
                btn = tk.Button(special_keys_frame, text=key.upper(),
                              command=lambda k=key: add_special_key(f"{{{k}}}"))
                btn.grid(row=i//7, column=i%7, padx=2, pady=2, sticky='ew')
   
            # 创建组合键框架
            combo_keys_frame = tk.LabelFrame(dialog, text="组合键", padx=5, pady=5)
            combo_keys_frame.pack(fill=tk.X, pady=5)
   
            # 创建常用组合键按钮
            combo_keys = [
                ('复制', 'ctrl+c'), ('粘贴', 'ctrl+v'), ('剪切', 'ctrl+x'),
                ('全选', 'ctrl+a'), ('保存', 'ctrl+s'), ('撤销', 'ctrl+z')
            ]
   
            for i, (name, combo) in enumerate(combo_keys):
                btn = tk.Button(combo_keys_frame, text=name,
                              command=lambda c=combo: add_special_key(f"{{{c}}}"))
                btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky='ew')
   
            # 创建修饰键框架
            modifier_keys_frame = tk.LabelFrame(dialog, text="修饰键", padx=5, pady=5)
            modifier_keys_frame.pack(fill=tk.X, pady=5)
   
            modifier_keys = ['ctrl', 'alt', 'shift', 'win']
            for i, key in enumerate(modifier_keys):
                btn = tk.Button(modifier_keys_frame, text=key.upper(),
                              command=lambda k=key: add_special_key(f"{{{k}}}"))
                btn.grid(row=0, column=i, padx=2, pady=2, sticky='ew')
   
            # 创建功能键框架
            function_keys_frame = tk.LabelFrame(dialog, text="功能键", padx=5, pady=5)
            function_keys_frame.pack(fill=tk.X, pady=5)
   
            for i in range(12):
                btn = tk.Button(function_keys_frame, text=f"F{i+1}",
                              command=lambda k=i+1: add_special_key(f"{{f{k}}}"))
                btn.grid(row=i//6, column=i%6, padx=2, pady=2, sticky='ew')
   
            def add_special_key(key):
                current_pos = entry.index(tk.INSERT)
                entry.insert(current_pos, key)
                entry.focus_set()
   
            def save_input():
                new_keyboard_input = entry.get()
                self.image_list[selected_index] = (
                    selected_image[0], selected_image[1], selected_image[2],
                    new_keyboard_input, selected_image[4], selected_image[5],
                    selected_image[6], selected_image[7]
                )
                self.update_image_listbox()
                dialog.destroy()
   
            # 添加说明文本
            help_text = """
支持的输入格式：
1. 普通文本：直接输入
2. 特殊键：使用花括号，如 {enter}, {tab}
3. 组合键：使用加号连接，如 {ctrl+c}, {alt+tab}
4. 按键序列：直接连接，如 {ctrl+c}{enter}
5. 延时：{delay:1000} 表示延时1秒
            """
            tk.Label(dialog, text=help_text, justify=tk.LEFT,
                    font=('Arial', 9)).pack(pady=5)
   
            # 添加保存和取消按钮
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill=tk.X, pady=10)
            tk.Button(button_frame, text="保存", command=save_input).pack(side=tk.RIGHT, padx=5)
            tk.Button(button_frame, text="取消", command=lambda: [dialog.destroy(), self.root.deiconify(), self.root.lift()]).pack(side=tk.RIGHT)
   
            # 居中显示对话框
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
   
    def set_hotkey(self):
        # 创建一个置顶的对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("设置热键")
        dialog.transient(self.root)  # 将对话框设置为主窗口的临时窗口
        dialog.grab_set()  # 模态对话框
        dialog.attributes('-topmost', True)  # 设置窗口置顶
           
        # 创建输入框和标签
        tk.Label(dialog, text="请输入新的热键（例如：<F1>）：").pack(pady=5)
        entry = tk.Entry(dialog)
        entry.insert(0, self.hotkey)
        entry.pack(pady=5)
           
        def save_hotkey():
            new_hotkey = entry.get()
            try:
                self.unregister_global_hotkey() #取消之前的全局热键
                self.hotkey = new_hotkey
                self.register_global_hotkey()
                print(f"热键已更改为 {self.hotkey}")
                logging.info(f"热键已更改为 {self.hotkey}")
                messagebox.showinfo("设置热键", f"热键已更改为 {self.hotkey}")
                dialog.destroy()
            except tk.TclError as e:
                print(f"绑定热键失败: {e}")
                logging.error(f"绑定热键失败: {e}")
                messagebox.showerror("设置热键失败", f"无法绑定热键: {new_hotkey}")
           
        # 添加确定按钮
        tk.Button(dialog, text="确定", command=save_hotkey).pack(pady=10)
           
        # 居中显示对话框
        dialog.geometry("+%d+%d" % (
            self.root.winfo_rootx() + self.root.winfo_width()//2 - dialog.winfo_reqwidth()//2,
            self.root.winfo_rooty() + self.root.winfo_height()//2 - dialog.winfo_reqheight()//2
        ))
   
    def save_config(self):
        config = {
            'hotkey': self.hotkey,
            'similarity_threshold': self.similarity_threshold,
            'delay_time': self.delay_time,
            'loop_count': self.loop_count,
            'image_list': [img for img in self.image_list if os.path.exists(img[0])],
            'only_keyboard': self.only_keyboard_var.get()
        }
        filename = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json")])
        if filename:
            try:
                with open(filename, 'w') as f:
                    json.dump(config, f)
                print(f"配置已保存到 {filename}")
                logging.info(f"配置已保存到 {filename}")
                self.config_filename = filename
                # 添加成功提示
                messagebox.showinfo("保存成功", f"配置已成功保存到:\n{filename}")
            except Exception as e:
                error_msg = f"保存配置时出错: {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                messagebox.showerror("保存失败", error_msg)
   
    def load_config(self):
        try:
            if not os.path.exists(self.config_filename):
                raise FileNotFoundError(f"配置文件不存在: {self.config_filename}")
   
            # 先读取配置文件
            with open(self.config_filename, 'r') as f:
                config = json.load(f)
               
            # 在应用任何更改之前，先验证所有图像文件
            missing_images = []
            for img_data in config.get('image_list', []):
                if not os.path.exists(img_data[0]):
                    missing_images.append(img_data[0])
               
            # 如果有任何图像文件不存在，直接返回，不做任何更改
            if missing_images:
                error_message = f"配置文件中缺少以下图像文件: {', '.join(missing_images)}"
                messagebox.showerror("错误", error_message)
                logging.error(error_message)
                return False
               
            # 只有当所有图像文件都存在时，才应用配置
            self.image_list = config.get('image_list', [])
            self.hotkey = config.get('hotkey', '<F1>')
            self.similarity_threshold = config.get('similarity_threshold', 0.8)
            self.delay_time = config.get('delay_time', 0.1)
            self.loop_count = config.get('loop_count', 1)
            self.only_keyboard_var.set(config.get('only_keyboard', False))
 
            # 清空并重新填充 Treeview
            for item in self.tree.get_children():
                self.tree.delete(item)
               
            for img_data in self.image_list:
                # 确保每个项目都有 8 个元素
                while len(img_data) < 8:
                    img_data = img_data + ("",)
                       
                # 加载图像并创建缩略图
                try:
                    image = Image.open(img_data[0])
                    image.thumbnail((50, 50))
                    photo = ImageTk.PhotoImage(image)
                       
                    # 插入到 Treeview
                    tree_item = self.tree.insert("", tk.END, values=(
                        os.path.basename(img_data[0]),  # 图片名称
                        img_data[1],  # 步骤名称
                        img_data[2],  # 相似度
                        img_data[3],  # 键盘输入
                        img_data[4],  # 鼠标点击坐标
                        img_data[5],  # 等待时间
                        img_data[6],  # 条件
                        img_data[7]   # 跳转步骤
                    ), image=photo)
                    self.tree.image_refs.append(photo)
                except Exception as e:
                    print(f"处理图像时出错 {img_data[0]}: {e}")
                    logging.error(f"处理图像时出错 {img_data[0]}: {e}")
               
            # 更新循环次数输入框
            self.loop_count_entry.delete(0, tk.END)
            self.loop_count_entry.insert(0, str(self.loop_count))
               
             # 取消之前的全局热键， 注册新的全局热键
            self.unregister_global_hotkey()
            self.register_global_hotkey()
               
            print(f"配置已从 {self.config_filename} 加载")
            logging.info(f"配置已从 {self.config_filename} 加载")
               
            # 显示成功消息
            messagebox.showinfo("成功", f"配置已成功加载:\n{self.config_filename}")
            return True
               
        except Exception as e:
            error_message = f"加载配置时出错: {str(e)}"
            print(error_message)
            logging.error(error_message)
            messagebox.showerror("错误", error_message)
            return False
   
    def reset_to_initial_state(self):
        """重置程序到初始状态"""
        try:
            # 重置所有变量到初始值
            self.hotkey = '<F1>'
            self.similarity_threshold = 0.8
            self.delay_time = 0.1
            self.loop_count = 1
            self.image_list = []
            self.running = False
            self.paused = False
            self.start_step_index = 0
            self.only_keyboard_var.set(False)
               
            # 重置界面元素
            self.update_image_listbox()
            self.loop_count_entry.delete(0, tk.END)
            self.loop_count_entry.insert(0, str(self.loop_count))
            self.toggle_run_button.config(text="开始运行")
            self.follow_current_step.set(False)
            self.allow_minimize_var.set(True)
             
            # 清空临时文件
            if os.path.exists(self.screenshot_folder):
                try:
                    shutil.rmtree(self.screenshot_folder)
                    os.makedirs(self.screenshot_folder)
                except Exception as e:
                    print(f"清理截图文件夹时出错: {e}")
                    logging.error(f"清理截图文件夹时出错: {e}")
               
            print("程序已重置为初始状态")
            logging.info("程序已重置为初始状态")
            messagebox.showinfo("重置", "程序已重置为初始状态")
             
            #  取消之前的全局热键， 注册新的全局热键
            self.unregister_global_hotkey()
            self.register_global_hotkey()
        except Exception as e:
            print(f"重置程序状态时出错: {e}")
            logging.error(f"重置程序状态时出错: {e}")
   
    def load_config_manually(self):
        """手动加载配置文件"""
        file_path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json")])
        if file_path:
            # 保存当前配置文件路径
            old_config_filename = self.config_filename
            self.config_filename = file_path
               
            # 尝试加载新配置
            if not self.load_config():
                # 如果加载失败，恢复原来的配置文件路径
                self.config_filename = old_config_filename
                # 重置到初始状态
                self.reset_to_initial_state()
   
    def get_mouse_position(self, event=None):
        # 获取当前鼠标位置
        x, y = pyautogui.position()
        messagebox.showinfo("鼠标位置", f"当前鼠标位置: ({x}, {y})")
   
        # 将鼠标位置存储到当前选中的图像中
        selected_item = self.tree.selection()
        if selected_item:
            selected_index = self.tree.index(selected_item[0])
            selected_image = self.image_list[selected_index]
            self.image_list[selected_index] = (selected_image[0], selected_image[1], selected_image[2], selected_image[3], f"{x},{y}", selected_image[5], selected_image[6], selected_image[7])
            self.update_image_listbox()
   
    def cleanup_on_exit(self):
        try:
            # 退出程序时删除未保存的图像
            if not os.path.exists(self.config_filename):
                for item in self.image_list:
                    img_path = item[0]
                    if os.path.exists(img_path):
                        try:
                            os.remove(img_path)
                            print(f"图像文件已删除: {img_path}")
                            logging.info(f"图像文件已删除: {img_path}")
                        except Exception as e:
                            print(f"删除图像文件时出错: {e}")
                            logging.error(f"删除图像文件时出错: {e}")
            #  取消全局热键
            self.unregister_global_hotkey()
        except Exception as e:
            print(f"清理时出错: {e}")
            logging.error(f"清理时出错: {e}")
            self.reset_to_initial_state()
   
    def bind_arrow_keys(self):
        self.tree.bind('<Up>', self.move_item_up)
        self.tree.bind('<Down>', self.move_item_down)
   
    def move_item_up(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
   
        for item in selected_items:
            index = self.tree.index(item)
            if index > 0:
                self.tree.move(item, '', index - 1)
                self.image_list.insert(index - 1, self.image_list.pop(index))
   
        # 确保第一个选定项目可见
        self.tree.see(selected_items[0])
   
        # 阻止事件传播
        return "break"
   
    def move_item_down(self, event):
        selected_items = self.tree.selection()
        if not selected_items:
            return
   
        for item in reversed(selected_items):
            index = self.tree.index(item)
            if index < len(self.image_list) - 1:
                self.tree.move(item, '', index + 1)
                self.image_list.insert(index + 1, self.image_list.pop(index))
   
        # 确保最后一项可见
        self.tree.see(selected_items[-1])
   
        # 阻止事件传播
        return "break"
   
    def test_single_match(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个项目进行测试")
            return
   
        selected_item = selected_items[0]
        selected_index = self.tree.index(selected_item)
        img_data = self.image_list[selected_index]
           
        # 使用新的解包方式，适应可能存在的额外字段
        img_path, img_name, similarity_threshold = img_data[:3]
   
        # 执行匹配测试
        matched, location = self.match_template(img_path, float(similarity_threshold))
   
        if matched:
            messagebox.showinfo("匹配结果", f"成功匹配到图像 '{img_name}'\n位置: {location}")
        else:
            messagebox.showinfo("匹配结果", f"未能匹配到图像 '{img_name}'")
   
    def match_template(self, template_path, similarity_threshold):
        # 截取当前屏幕
        screenshot = pyautogui.screenshot()
        screenshot = np.array(screenshot)
        screenshot = cv2.cvtColor(screenshot, cv2.COLOR_RGB2BGR)
   
        # 读取模板图像
        template = cv2.imread(template_path, 0)
        if template is None:
            print(f"无法读取图像: {template_path}")
            logging.error(f"无法读取图像: {template_path}")
            return False, None
   
        # 转换截图为灰度图像
        gray_screenshot = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
   
        # 进行模板匹配
        result = cv2.matchTemplate(gray_screenshot, template, cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
   
        if max_val >= similarity_threshold:
            # 计算匹配位置的中心点
            h, w = template.shape
            center_x = max_loc[0] + w // 2
            center_y = max_loc[1] + h // 2
            return True, (center_x, center_y)
        else:
            return False, None
   
    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, postcommand=self.update_context_menu)
        self.context_menu.add_command(label="编辑步骤名称", command=self.edit_image_name)
        self.context_menu.add_command(label="编辑相似度", command=self.edit_similarity_threshold)
        self.context_menu.add_command(label="编辑键盘输入", command=self.edit_keyboard_input)
        self.context_menu.add_command(label="编辑鼠标操作", command=self.edit_mouse_action)  # 添加这一行
        self.context_menu.add_command(label="编辑等待时间", command=self.edit_wait_time)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="复制", command=self.copy_item)
        self.context_menu.add_command(label="粘贴", command=self.paste_item)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="从此步骤开始运行", command=self.start_from_step)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="设置条件跳转", command=self.set_condition_jump)
   
    def update_context_menu(self):
        # 在显示菜单前更新菜单状态
        selected = self.tree.selection()
        # 可以在这里根据选择状态启用/禁用某些菜单项
   
    def start_from_step(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个项目进行操作")
            return
   
        # 获取当前选中的步骤索引
        selected_item = selected_items[0]
        self.start_step_index = self.tree.index(selected_item)  # 使用当前选中的步骤索引
        self.start_script_thread()  # 启动脚本
   
        # 更新按钮文本以指示脚本正在运行
        self.toggle_run_button.config(text="停止运行")
   
    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_clear()
            self.tree.selection_set(item)
            self.tree.focus(item)
            # 使用after方法延迟显示菜单
            self.root.after(1, lambda: self.context_menu.post(event.x_root, event.y_root))
        return "break"
   
    def copy_item(self):
        selected_items = self.tree.selection()
        if selected_items:
            index = self.tree.index(selected_items[0])
            original_item = self.image_list[index]
               
            # 创建像文件的副本
            new_image_path = self.create_image_copy(original_item[0])
               
            # 创建新的元组，使用新的图像路径
            self.copied_item = (new_image_path,) + tuple(original_item[1:])
   
    def create_image_copy(self, original_path):
        # 创建图像文件的副本
        base_name = os.path.basename(original_path)
        name, ext = os.path.splitext(base_name)
        new_name = f"{name}_copy{ext}"
        new_path = os.path.join(self.screenshot_folder, new_name)
        shutil.copy2(original_path, new_path)
        return new_path
       
    def paste_item(self):
        if self.copied_item:
            target = self.tree.focus()
            if target:
                target_index = self.tree.index(target)
                # 使用与复制的项相同的数据创新元组
                new_item = tuple(self.copied_item)
                self.image_list.insert(target_index + 1, new_item)  # 插入到下方
                self.update_image_listbox()
   
    def edit_image_name(self):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.tree.index(selected_item)
            selected_image = self.image_list[selected_index]
   
            new_image_name = simpledialog.askstring("修改步骤名称", "请输入新的步骤名称：", initialvalue=selected_image[1])
            if new_image_name is not None:
                self.image_list[selected_index] = (selected_image[0], new_image_name, selected_image[2], selected_image[3], selected_image[4], selected_image[5], selected_image[6], selected_image[7])
                self.update_image_listbox()
   
    def edit_similarity_threshold(self):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.tree.index(selected_item)
            selected_image = self.image_list[selected_index]
   
            new_similarity_threshold = simpledialog.askfloat("修改相似度", "请输入新的相似度（0.1 - 1.0）：", initialvalue=selected_image[2], minvalue=0.1, maxvalue=1.0)
            if new_similarity_threshold is not None:
                self.image_list[selected_index] = (selected_image[0], selected_image[1], new_similarity_threshold, selected_image[3], selected_image[4], selected_image[5], selected_image[6], selected_image[7])
                self.update_image_listbox()
   
    def edit_wait_time(self):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.tree.index(selected_item)
            selected_image = self.image_list[selected_index]
   
            new_wait_time = simpledialog.askinteger("修改等待时间", "请输入新的等待时间（毫秒）：", initialvalue=selected_image[5])
            if new_wait_time is not None:
                self.image_list[selected_index] = (selected_image[0], selected_image[1], selected_image[2], selected_image[3], selected_image[4], new_wait_time, selected_image[6], selected_image[7])
                self.update_image_listbox()
   
    def set_condition_jump(self):
        selected_items = self.tree.selection()
        if not selected_items:
            messagebox.showwarning("警告", "请先选择一个项目")
            return
   
        selected_item = selected_items[0]
        selected_index = self.tree.index(selected_item)
        selected_image = list(self.image_list[selected_index])  # 转换为列表以便修改
   
        # 创建设置条件跳转的对话框
        dialog = tk.Toplevel(self.root)
        dialog.title("设置条件跳转")
        dialog.geometry("300x150")
        dialog.transient(self.root)
        dialog.grab_set()
        dialog.attributes('-topmost', True)  # 设置窗口置顶
   
        # 条件选择
        condition_frame = tk.Frame(dialog)
        condition_frame.pack(pady=5)
        tk.Label(condition_frame, text="条件:").pack(side=tk.LEFT)
        condition_var = tk.StringVar(value=selected_image[6] if len(selected_image) > 6 else "")
        condition_combo = ttk.Combobox(condition_frame, textvariable=condition_var, values=["True", "False"], width=10)
        condition_combo.pack(side=tk.LEFT)
   
        # 跳转步骤选择
        jump_frame = tk.Frame(dialog)
        jump_frame.pack(pady=5)
        tk.Label(jump_frame, text="跳转到步骤:").pack(side=tk.LEFT)
        jump_var = tk.StringVar(value=selected_image[7] if len(selected_image) > 7 else "")
        step_names = [img[1] for img in self.image_list]  # 获取所有步骤名称
        jump_combo = ttk.Combobox(jump_frame, textvariable=jump_var, values=step_names, width=15)
        jump_combo.pack(side=tk.LEFT)
   
        def save_condition():
            condition = condition_var.get()
            jump_to = jump_var.get()
               
            # 确保选择了有效的条件和跳转步骤
            if not condition or not jump_to:
                messagebox.showwarning("警告", "请选择条件和跳转步骤")
                return
                   
            try:
                # 确保列表长度至少为8
                while len(selected_image) < 8:
                    selected_image.append("")
                   
                # 更新条件和跳转步骤
                selected_image[6] = condition
                selected_image[7] = jump_to
                   
                # 更新 image_list 中的数据
                self.image_list[selected_index] = tuple(selected_image)
                   
                # 立即更新显示
                self.update_image_listbox()
                   
                # 选中更新后的项
                items = self.tree.get_children()
                if selected_index < len(items):
                    self.tree.selection_set(items[selected_index])
                    self.tree.focus(items[selected_index])
                   
                # 打印日志确认更新
                print(f"已更新条件跳转设置：条件={condition}, 跳转到={jump_to}")
                logging.info(f"已更新条件跳转设置：条件={condition}, 跳转到={jump_to}")
                   
                dialog.destroy()
            except Exception as e:
                error_msg = f"保存条件跳转设置时出错: {str(e)}"
                print(error_msg)
                logging.error(error_msg)
                messagebox.showerror("错误", error_msg)
   
        # 保存按钮
        tk.Button(dialog, text="保存", command=save_condition).pack(pady=10)
   
        # 等待窗口绘制完成
        dialog.update_idletasks()
           
        # 计算居中位置
        x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
           
        # 设置窗口位置
        dialog.geometry(f"+{x}+{y}")
   
    def on_treeview_select(self, event):
        """当 Treeview 选择改变时更新预览图像"""
        selected_items = self.tree.selection()
        if not selected_items:
            # 清空预览
            self.preview_image_label.config(image='')
            return
          
        selected_item = selected_items[0]
        selected_index = self.tree.index(selected_item)
          
        try:
            # 获取选中项的图像路径
            img_path = self.image_list[selected_index][0]
              
            # 检查文件是否存在
            if not os.path.exists(img_path):
                self.preview_image_label.config(image='')
                return
              
            # 加载原始图像
            original_image = Image.open(img_path)
              
            # 获取原始尺寸
            original_width, original_height = original_image.size
              
            # 设置最大预览尺寸
            max_width = 90
            max_height = 90
              
            # 计算缩放比例
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)
              
            # 计算新的尺寸
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
              
            # 调整图像大小
            resized_image = original_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # 创建 PhotoImage 对象
            photo = ImageTk.PhotoImage(resized_image)
              
            # 更新预览标签
            self.preview_image_label.config(image=photo)
            self.preview_image_label.image = photo  # 保持引用以防止垃圾回收
              
            # 添加尺寸信息到预览标签
            self.preview_label.config(text=f"图像预览 ({original_width}x{original_height})")
              
        except Exception as e:
            print(f"预览图像时出错: {e}")
            logging.error(f"预览图像时出错: {e}")
            self.preview_image_label.config(image='')
   
    def edit_mouse_action(self):
        selected_items = self.tree.selection()
        if selected_items:
            selected_item = selected_items[0]
            selected_index = self.tree.index(selected_item)
            selected_image = self.image_list[selected_index]
 
            # 创建新窗口但不隐藏主窗口
            dialog = tk.Toplevel(self.root)
            dialog.title("设置鼠标操作")
            dialog.transient(self.root)
            dialog.grab_set()
 
             
            # 创建坐标输入框
            coord_frame = tk.Frame(dialog)
            coord_frame.pack(fill=tk.X, pady=5)
            tk.Label(coord_frame, text="坐标 (x,y):").pack(side=tk.LEFT)
            coord_entry = tk.Entry(coord_frame, width=20)
            coord_entry.pack(side=tk.LEFT, padx=5)
 
            # 解析现有的鼠标操作数据
            current_action = "click"
            current_coords = ""
            current_dynamic = False
              
            if selected_image[4]:  # 如果有现有的鼠标操作数据
                try:
                    if ":" in selected_image[4]:
                        action, coords, dynamic = selected_image[4].split(":")
                        current_action = action
                        current_coords = coords
                        current_dynamic = dynamic == "1"
                    else:
                        current_coords = selected_image[4]
                except:
                    pass
              
            coord_entry.insert(0, current_coords)
 
            # 创建鼠标动作选择框架
            action_frame = tk.LabelFrame(dialog, text="鼠标动作", padx=5, pady=5)
            action_frame.pack(fill=tk.X, pady=5)
 
            # 鼠标动作类型
            action_var = tk.StringVar(value=current_action)
            actions = [
                ("左键单机", "click"),
                ("右键单击", "rightClick"),
                ("双击", "doubleClick"),
                ("按住", "mouseDown"),
                ("释放", "mouseUp")
            ]
 
            for text, value in actions:
                tk.Radiobutton(action_frame, text=text, value=value, 
                              variable=action_var).pack(anchor=tk.W)
                 
            # 添加动态点击勾选框
            dynamic_var = tk.BooleanVar(value=current_dynamic)
            tk.Checkbutton(action_frame, text="动态点击", variable=dynamic_var).pack(anchor=tk.W)
 
            def save_mouse_action():
                try:
                    # 获取坐标
                    coords = coord_entry.get().strip()
                    if not coords or "," not in coords:
                        messagebox.showerror("错误", "请输入有效的坐标 (x,y)")
                        return
  
                    # 验证坐标格式
                    try:
                        x, y = map(int, coords.split(","))
                    except ValueError:
                        messagebox.showerror("错误", "坐标必须是整数")
                        return
  
                    # 获取动作类型
                    action = action_var.get()
                    dynamic = "1" if dynamic_var.get() else "0"
 
                    # 构建鼠标操作字符串
                    mouse_action = f"{action}:{coords}:{dynamic}"
 
                    # 更新图像列表
                    self.image_list[selected_index] = (
                        selected_image[0], selected_image[1], selected_image[2],
                        selected_image[3], mouse_action, selected_image[5],
                        selected_image[6], selected_image[7]
                    )
                    self.update_image_listbox()
                    dialog.destroy()
                except Exception as e:
                    messagebox.showerror("错误", f"保存鼠标操作时出错: {str(e)}")
 
            # 添加说明文本
            help_text = """
支持的鼠标操作：
1. 左键单击：在指定位置单击左键
2. 右键单击：在指定位置单击右键
3. 双击：在指定位置双击左键
4. 按住：按住鼠标左键
5. 释放：释放鼠标左键
  
注意：
- 可以手动修改鼠标位置
- 坐标格式为"x,y"（例如：100,200）
- 勾选“动态点击”后，鼠标点击位置将根据匹配到的图像位置动态确定
        """
            tk.Label(dialog, text=help_text, justify=tk.LEFT,
                    font=('Arial', 9)).pack(pady=5)
 
            # 添加保存和取消按钮
            button_frame = tk.Frame(dialog)
            button_frame.pack(fill=tk.X, pady=10)
            tk.Button(button_frame, text="保存", command=save_mouse_action).pack(side=tk.RIGHT, padx=5)
            tk.Button(button_frame, text="取消", command=lambda: [dialog.destroy(), self.root.deiconify(), self.root.lift()]).pack(side=tk.RIGHT)
 
            # 居中显示对话框
            dialog.update_idletasks()
            x = self.root.winfo_x() + (self.root.winfo_width() - dialog.winfo_width()) // 2
            y = self.root.winfo_y() + (self.root.winfo_height() - dialog.winfo_height()) // 2
            dialog.geometry(f"+{x}+{y}")
  
    def focus_on_step(self, index):
        """实现焦点跟随功能"""
        try:
            items = self.tree.get_children()
            if 0 <= index < len(items):
                self.tree.selection_set(items[index])
                self.tree.focus(items[index])
                self.tree.see(items[index])
        except Exception as e:
            print(f"焦点跟随出错: {e}")
            logging.error(f"焦点跟随出错: {e}")
   
if __name__ == "__main__":
    root = tk.Tk()
    app = ImageRecognitionApp(root)
    root.mainloop()