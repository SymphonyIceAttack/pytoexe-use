import sys
import os
import time
import json
import pyautogui
import pyperclip
import traceback
import keyboard
from threading import Thread
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QLabel, QComboBox, QLineEdit, QScrollArea,
                               QFileDialog, QTextEdit, QMessageBox, QFrame, QRadioButton, QButtonGroup,
                               QTabWidget, QSpinBox, QCheckBox, QGroupBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon


# --------------------------
# 核心逻辑 (增强版刷课引擎)
# --------------------------

def mouseClick(clickTimes, lOrR, img, reTry, timeout=60):
    """
    reTry: 1 (一次), -1 (无限), >1 (指定次数)
    timeout: 超时时间(秒)，默认60秒。防止无限卡死。
    img: 可以是图片路径，也可以是坐标字符串 "x,y"
    """
    start_time = time.time()

    # 检测是否为坐标模式 (格式: "x,y" 或 "x, y")
    if isinstance(img, str) and ',' in img:
        try:
            x, y = map(int, img.split(','))
            # 坐标模式，直接点击
            if reTry == 1:
                pyautogui.click(x, y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
            elif reTry == -1:
                while True:
                    if timeout and (time.time() - start_time > timeout):
                        print(f"操作超时 ({timeout}秒)")
                        return
                    pyautogui.click(x, y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
                    time.sleep(0.1)
            elif reTry > 1:
                i = 1
                while i < reTry + 1:
                    if timeout and (time.time() - start_time > timeout):
                        print(f"操作超时 ({timeout}秒)")
                        return
                    pyautogui.click(x, y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
                    print(f"重复 {i}")
                    i += 1
                    time.sleep(0.1)
            return
        except ValueError:
            pass  # 坐标格式错误，降级为图片识别模式

    # 图片识别模式 (原有逻辑)
    if reTry == 1:
        while True:
            # 检查超时
            if timeout and (time.time() - start_time > timeout):
                print(f"等待图片 {img} 超时 ({timeout}秒)")
                return  # 或者抛出异常

            try:
                location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x, location.y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
                    break
            except pyautogui.ImageNotFoundException:
                pass  # 没找到，继续重试

            print("未找到匹配图片,0.1秒后重试")
            time.sleep(0.1)
    elif reTry == -1:
        while True:
            # 无限重试通常也需要某种中断机制，这里保留原意但增加超时保护（可选）
            # 如果确实想"死等"，可以把 timeout 设为 None
            if timeout and (time.time() - start_time > timeout):
                print(f"等待图片 {img} 超时 ({timeout}秒)")
                return

            try:
                location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x, location.y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(0.1)
    elif reTry > 1:
        i = 1
        while i < reTry + 1:
            if timeout and (time.time() - start_time > timeout):
                print(f"操作超时 ({timeout}秒)")
                return

            try:
                location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
                if location is not None:
                    pyautogui.click(location.x, location.y, clicks=clickTimes, interval=0.2, duration=0.2, button=lOrR)
                    print("重复")
                    i += 1
            except pyautogui.ImageNotFoundException:
                pass

            time.sleep(0.1)


def mouseMove(img, reTry, timeout=60):
    """
    鼠标悬停（移动但不点击）
    img: 可以是图片路径，也可以是坐标字符串 "x,y"
    """
    start_time = time.time()

    # 检测是否为坐标模式
    if isinstance(img, str) and ',' in img:
        try:
            x, y = map(int, img.split(','))
            pyautogui.moveTo(x, y, duration=0.2)
            return
        except ValueError:
            pass  # 坐标格式错误，降级为图片识别模式

    # 图片识别模式
    while True:
        if timeout and (time.time() - start_time > timeout):
            print(f"等待图片 {img} 超时 ({timeout}秒)")
            return

        try:
            location = pyautogui.locateCenterOnScreen(img, confidence=0.9)
            if location is not None:
                pyautogui.moveTo(location.x, location.y, duration=0.2)
                break
        except pyautogui.ImageNotFoundException:
            pass

        print("未找到匹配图片,0.1秒后重试")
        time.sleep(0.1)


class RPAEngine:
    def __init__(self):
        self.is_running = False
        self.stop_requested = False
        self.hotkey_registered = False
        self.course_count = 0  # 课程计数器
        self.start_time = None  # 开始时间

    def stop(self):
        self.stop_requested = True
        self.is_running = False

    def register_f8_hotkey(self, stop_callback):
        """注册F8热键停止功能"""
        try:
            # 如果已经注册，先移除旧的
            if self.hotkey_registered:
                keyboard.unhook_all_hotkeys()
                self.hotkey_registered = False

            def on_f8_press():
                if self.is_running:
                    stop_callback()

            keyboard.add_hotkey('f8', on_f8_press)
            self.hotkey_registered = True
            return True
        except Exception as e:
            print(f"F8热键注册失败: {e}")
            print("请使用界面上的停止按钮")
            return False

    def unregister_f8_hotkey(self):
        """取消注册F8热键"""
        if self.hotkey_registered:
            keyboard.unhook_all_hotkeys()
            self.hotkey_registered = False

    def run_tasks(self, tasks, loop_forever=False, max_courses=0, callback_msg=None):
        """
        tasks: list of dict, format:
        [
            {"type": 1.0, "value": "1.png", "retry": 1},
            ...
        ]
        value 可以是:
        - 图片路径: "image.png"
        - 坐标字符串: "100,200"
        
        max_courses: 最大课程数，0表示不限制
        """
        self.is_running = True
        self.stop_requested = False
        self.course_count = 0
        self.start_time = time.time()

        try:
            while True:
                # 检查课程数量限制
                if max_courses > 0 and self.course_count >= max_courses:
                    if callback_msg: callback_msg(f"已完成 {max_courses} 门课程，停止执行")
                    break

                self.course_count += 1
                if callback_msg:
                    elapsed_time = int(time.time() - self.start_time)
                    callback_msg(f"=== 第 {self.course_count} 门课程开始 (已运行 {elapsed_time} 秒) ===")

                for idx, task in enumerate(tasks):
                    if self.stop_requested:
                        if callback_msg: callback_msg("任务已停止")
                        return

                    cmd_type = task.get("type")
                    cmd_value = task.get("value")
                    retry = task.get("retry", 1)

                    if callback_msg:
                        callback_msg(f"  步骤 {idx + 1}: {cmd_value}")

                    if cmd_type == 1.0:  # 单击左键
                        mouseClick(1, "left", cmd_value, retry)
                        if callback_msg: callback_msg(f"  ✓ 单击左键: {cmd_value}")

                    elif cmd_type == 2.0:  # 双击左键
                        mouseClick(2, "left", cmd_value, retry)
                        if callback_msg: callback_msg(f"  ✓ 双击左键: {cmd_value}")

                    elif cmd_type == 3.0:  # 右键
                        mouseClick(1, "right", cmd_value, retry)
                        if callback_msg: callback_msg(f"  ✓ 右键单击: {cmd_value}")

                    elif cmd_type == 4.0:  # 输入
                        pyperclip.copy(str(cmd_value))
                        pyautogui.hotkey('ctrl', 'v')
                        time.sleep(0.5)
                        if callback_msg: callback_msg(f"  ✓ 输入文本: {cmd_value}")

                    elif cmd_type == 5.0:  # 等待
                        sleep_time = float(cmd_value)
                        time.sleep(sleep_time)
                        if callback_msg: callback_msg(f"  ✓ 等待 {sleep_time} 秒")

                    elif cmd_type == 6.0:  # 滚轮
                        scroll_val = int(cmd_value)
                        pyautogui.scroll(scroll_val)
                        if callback_msg: callback_msg(f"  ✓ 滚轮滑动 {scroll_val}")

                    elif cmd_type == 7.0:  # 系统按键 (组合键)
                        keys = str(cmd_value).lower().split('+')
                        # 去除空格
                        keys = [k.strip() for k in keys]
                        pyautogui.hotkey(*keys)
                        if callback_msg: callback_msg(f"  ✓ 按键组合: {cmd_value}")

                    elif cmd_type == 8.0:  # 鼠标悬停
                        mouseMove(cmd_value, retry)
                        if callback_msg: callback_msg(f"  ✓ 鼠标悬停: {cmd_value}")

                    elif cmd_type == 9.0:  # 截图保存
                        path = str(cmd_value)
                        # 如果是目录，自动拼接时间戳文件名
                        if os.path.isdir(path):
                            timestamp = time.strftime("%Y%m%d_%H%M%S")
                            filename = os.path.join(path, f"screenshot_{timestamp}.png")
                        else:
                            # 兼容旧逻辑：如果用户直接输入了带文件名的路径
                            filename = path
                            if not filename.endswith(('.png', '.jpg', '.bmp')):
                                filename += '.png'

                        pyautogui.screenshot(filename)
                        if callback_msg: callback_msg(f"  ✓ 截图已保存: {filename}")

                if not loop_forever:
                    break

                if callback_msg: 
                    elapsed_time = int(time.time() - self.start_time)
                    callback_msg(f"第 {self.course_count} 门课程完成 (总耗时 {elapsed_time} 秒)")
                time.sleep(0.5)

        except Exception as e:
            if callback_msg: callback_msg(f"执行出错: {e}")
            traceback.print_exc()
        finally:
            self.is_running = False
            if callback_msg: 
                elapsed_time = int(time.time() - self.start_time)
                callback_msg(f"任务结束！共完成 {self.course_count} 门课程，总耗时 {elapsed_time} 秒")


# --------------------------
# GUI 界面 (刷课专用版)
# --------------------------

# 定义操作类型映射
CMD_TYPES = {
    "左键单击": 1.0,
    "左键双击": 2.0,
    "右键单击": 3.0,
    "输入文本": 4.0,
    "等待(秒)": 5.0,
    "滚轮滑动": 6.0,
    "系统按键": 7.0,
    "鼠标悬停": 8.0,
    "截图保存": 9.0
}

CMD_TYPES_REV = {v: k for k, v in CMD_TYPES.items()}


class WorkerThread(QThread):
    log_signal = Signal(str)
    finished_signal = Signal()

    def __init__(self, engine, tasks, loop_forever, max_courses):
        super().__init__()
        self.engine = engine
        self.tasks = tasks
        self.loop_forever = loop_forever
        self.max_courses = max_courses

    def run(self):
        self.engine.run_tasks(self.tasks, self.loop_forever, self.max_courses, self.log_callback)
        self.finished_signal.emit()

    def log_callback(self, msg):
        self.log_signal.emit(msg)


class TaskRow(QFrame):
    def __init__(self, parent_layout, delete_callback):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.layout = QHBoxLayout(self)
        self.layout.setContentsMargins(5, 5, 5, 5)

        # 操作类型选择
        self.type_combo = QComboBox()
        self.type_combo.addItems(list(CMD_TYPES.keys()))
        self.type_combo.currentTextChanged.connect(self.on_type_changed)
        self.layout.addWidget(self.type_combo)

        # 参数输入区域
        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("参数值 (如图片路径、文本、时间)")
        self.layout.addWidget(self.value_input)

        # 模式切换：坐标/图片 (默认隐藏)
        self.mode_group = QButtonGroup(self)
        self.coord_radio = QRadioButton("坐标")
        self.img_radio = QRadioButton("图片")
        self.img_radio.setChecked(True)  # 默认图片模式
        self.mode_group.addButton(self.coord_radio, 1)
        self.mode_group.addButton(self.img_radio, 2)
        self.mode_group.idToggled.connect(self.on_mode_changed)
        self.layout.addWidget(self.coord_radio)
        self.layout.addWidget(self.img_radio)
        self.coord_radio.setVisible(False)
        self.img_radio.setVisible(False)

        # 坐标拾取按钮 (默认隐藏)
        self.pick_coord_btn = QPushButton("拾取坐标")
        self.pick_coord_btn.clicked.connect(self.pick_coordinate)
        self.pick_coord_btn.setVisible(False)
        self.layout.addWidget(self.pick_coord_btn)

        # 文件选择按钮 (默认隐藏)
        self.file_btn = QPushButton("选择图片")
        self.file_btn.clicked.connect(self.select_file)
        self.file_btn.setVisible(False)  # 默认隐藏，根据类型显示
        self.layout.addWidget(self.file_btn)

        # 重试次数 (默认隐藏)
        self.retry_input = QLineEdit()
        self.retry_input.setPlaceholderText("重试次数 (1=一次, -1=无限)")
        self.retry_input.setText("1")
        self.retry_input.setFixedWidth(100)
        self.retry_input.setVisible(False)  # 默认隐藏，根据类型显示
        self.layout.addWidget(self.retry_input)

        # 删除按钮
        self.del_btn = QPushButton("X")
        self.del_btn.setStyleSheet("color: red; font-weight: bold;")
        self.del_btn.setFixedWidth(30)
        self.del_btn.clicked.connect(lambda: delete_callback(self))
        self.layout.addWidget(self.del_btn)

        parent_layout.addWidget(self)

        # 初始化界面状态（默认选择"左键单击"）
        self.on_type_changed("左键单击")

    def on_type_changed(self, text):
        cmd_type = CMD_TYPES[text]

        # 图片相关操作 (1, 2, 3, 8)
        if cmd_type in [1.0, 2.0, 3.0, 8.0]:
            self.coord_radio.setVisible(True)
            self.img_radio.setVisible(True)
            self.retry_input.setVisible(True)
            # 根据当前选择的模式显示相应按钮
            if self.coord_radio.isChecked():
                self.pick_coord_btn.setVisible(True)
                self.file_btn.setVisible(False)
                self.value_input.setPlaceholderText("坐标 (格式: x,y，如: 100,200)")
            else:
                self.pick_coord_btn.setVisible(False)
                self.file_btn.setVisible(True)
                self.file_btn.setText("选择图片")
                self.value_input.setPlaceholderText("图片路径")
        # 输入 (4)
        elif cmd_type == 4.0:
            self.coord_radio.setVisible(False)
            self.img_radio.setVisible(False)
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("请输入要发送的文本")
        # 等待 (5)
        elif cmd_type == 5.0:
            self.coord_radio.setVisible(False)
            self.img_radio.setVisible(False)
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("等待秒数 (如 1.5)")
        # 滚轮 (6)
        elif cmd_type == 6.0:
            self.coord_radio.setVisible(False)
            self.img_radio.setVisible(False)
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("滚动距离 (正数向上，负数向下)")
        # 系统按键 (7)
        elif cmd_type == 7.0:
            self.coord_radio.setVisible(False)
            self.img_radio.setVisible(False)
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(False)
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("组合键 (如 ctrl+s, alt+tab)")
        # 截图保存 (9)
        elif cmd_type == 9.0:
            self.coord_radio.setVisible(False)
            self.img_radio.setVisible(False)
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(True)
            self.file_btn.setText("选择保存文件夹")
            self.retry_input.setVisible(False)
            self.value_input.setPlaceholderText("保存目录 (如 D:\\Screenshots)")

    def on_mode_changed(self, btn_id, checked):
        """坐标/图片模式切换"""
        if not checked:
            return

        cmd_type = CMD_TYPES[self.type_combo.currentText()]

        if btn_id == 1:  # 坐标模式
            self.pick_coord_btn.setVisible(True)
            self.file_btn.setVisible(False)
            self.value_input.setPlaceholderText("坐标 (格式: x,y，如: 100,200)")
        elif btn_id == 2:  # 图片模式
            self.pick_coord_btn.setVisible(False)
            self.file_btn.setVisible(True)
            self.file_btn.setText("选择图片")
            self.value_input.setPlaceholderText("图片路径")

    def set_data(self, data):
        """用于回填数据"""
        cmd_type = data.get("type")
        value = data.get("value", "")
        retry = data.get("retry", 1)

        # 设置类型 (反向查找文本)
        if cmd_type in CMD_TYPES_REV:
            self.type_combo.setCurrentText(CMD_TYPES_REV[cmd_type])

        # 设置值
        self.value_input.setText(str(value))

        # 设置重试次数
        self.retry_input.setText(str(retry))

        # 智能判断是否为坐标模式 (仅对鼠标操作有效)
        if cmd_type in [1.0, 2.0, 3.0, 8.0] and isinstance(value, str):
            if ',' in value:
                try:
                    # 尝试解析为坐标
                    x, y = map(int, value.split(','))
                    self.coord_radio.setChecked(True)
                except ValueError:
                    self.img_radio.setChecked(True)
            else:
                self.img_radio.setChecked(True)

    def pick_coordinate(self):
        """拾取当前鼠标位置坐标"""
        # 最小化当前窗口，方便用户移动鼠标到目标位置
        from PySide6.QtWidgets import QInputDialog

        # 弹出提示
        QMessageBox.information(self, "拾取坐标",
                                "请移动鼠标到目标位置，然后点击确定。\n"
                                "确定后，程序将记录当前鼠标的坐标。")

        # 获取当前鼠标位置
        x, y = pyautogui.position()
        self.value_input.setText(f"{x},{y}")

        QMessageBox.information(self, "坐标已获取", f"已获取坐标: ({x}, {y})")

    def select_file(self):
        cmd_type = CMD_TYPES[self.type_combo.currentText()]

        # 截图保存 (9.0) -> 选择文件夹
        if cmd_type == 9.0:
            folder = QFileDialog.getExistingDirectory(self, "选择保存文件夹", os.getcwd())
            if folder:
                self.value_input.setText(folder)

        # 其他图片操作 (1, 2, 3, 8) -> 打开文件对话框
        else:
            filename, _ = QFileDialog.getOpenFileName(self, "选择图片", os.getcwd(), "Image Files (*.png *.jpg *.bmp)")
            if filename:
                self.value_input.setText(filename)

    def get_data(self):
        cmd_type = CMD_TYPES[self.type_combo.currentText()]
        value = self.value_input.text()

        # 数据校验与转换
        try:
            if cmd_type in [5.0, 6.0]:
                # 尝试转换为数字，如果失败可能会在运行时报错，这里简单处理
                if not value: value = "0"

            retry = 1
            if self.retry_input.isVisible():
                retry_text = self.retry_input.text()
                if retry_text:
                    retry = int(retry_text)
        except ValueError:
            pass  # 保持默认

        return {
            "type": cmd_type,
            "value": value,
            "retry": retry
        }


class RPAWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🎓 智能刷课助手 - 浏览器自动化工具")
        self.resize(1000, 700)

        # 设置窗口图标
        self.set_app_icon()

        self.engine = RPAEngine()
        self.worker = None
        self.rows = []

        # 主布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # 顶部控制栏
        top_bar = QHBoxLayout()

        self.add_btn = QPushButton("+ 新增指令")
        self.add_btn.clicked.connect(self.add_row)
        top_bar.addWidget(self.add_btn)

        self.save_btn = QPushButton("💾 保存配置")
        self.save_btn.clicked.connect(self.save_config)
        top_bar.addWidget(self.save_btn)

        self.load_btn = QPushButton("📂 导入配置")
        self.load_btn.clicked.connect(self.load_config)
        top_bar.addWidget(self.load_btn)

        top_bar.addStretch()

        # F8提示标签
        f8_label = QLabel("⌨️  提示：运行时按 F8 键可停止任务")
        f8_label.setStyleSheet("color: #666; font-weight: bold; font-style: italic;")
        top_bar.addWidget(f8_label)

        # 循环模式
        self.loop_check = QComboBox()
        self.loop_check.addItems(["执行一次", "循环执行"])
        top_bar.addWidget(self.loop_check)

        # 最大课程数限制
        max_courses_label = QLabel("课程数限制:")
        top_bar.addWidget(max_courses_label)
        self.max_courses_spin = QSpinBox()
        self.max_courses_spin.setRange(0, 9999)
        self.max_courses_spin.setValue(0)
        self.max_courses_spin.setSuffix(" 门 (0=不限制)")
        self.max_courses_spin.setToolTip("设置要完成的课程数量，0表示无限制")
        top_bar.addWidget(self.max_courses_spin)

        self.start_btn = QPushButton("▶️ 开始刷课")
        self.start_btn.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 8px 15px;")
        top_bar.addWidget(self.start_btn)

        self.stop_btn = QPushButton("⏹️ 停止(F8)")
        self.stop_btn.setStyleSheet("background-color: #f44336; color: white; font-weight: bold; padding: 8px 15px;")
        self.stop_btn.clicked.connect(self.stop_task)
        self.stop_btn.setEnabled(False)
        top_bar.addWidget(self.stop_btn)

        main_layout.addLayout(top_bar)

        # 创建标签页
        tab_widget = QTabWidget()

        # 标签页1: 任务配置
        task_tab = QWidget()
        task_layout = QVBoxLayout(task_tab)

        # 使用说明区域
        help_group = QGroupBox("📖 使用说明")
        help_layout = QVBoxLayout()
        help_text = QLabel(
            "1. 点击「新增指令」添加操作步骤\n"
            "2. 支持图片识别和坐标两种模式\n"
            "3. 设置「课程数限制」来控制刷课数量\n"
            "4. 建议先手动操作一遍，截取关键按钮图片\n"
            "5. 运行后会自动最小化窗口，按 F8 可停止"
        )
        help_text.setStyleSheet("color: #555; font-size: 12px;")
        help_layout.addWidget(help_text)
        help_group.setLayout(help_layout)
        task_layout.addWidget(help_group)

        # 快捷操作按钮
        quick_bar = QHBoxLayout()
        quick_template_btn = QPushButton("📋 加载刷课模板")
        quick_template_btn.clicked.connect(self.load_course_template)
        quick_template_btn.setStyleSheet("background-color: #2196F3; color: white;")
        quick_bar.addWidget(quick_template_btn)
        quick_bar.addStretch()
        task_layout.addLayout(quick_bar)

        # 任务列表区域 (滚动)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.task_container = QWidget()
        self.task_layout = QVBoxLayout(self.task_container)
        self.task_layout.addStretch()  # 弹簧，确保添加的行在顶部
        scroll.setWidget(self.task_container)
        task_layout.addWidget(scroll)

        tab_widget.addTab(task_tab, "🎯 任务配置")

        # 标签页2: 统计信息
        stats_tab = QWidget()
        stats_layout = QVBoxLayout(stats_tab)

        stats_group = QGroupBox("📊 实时统计")
        stats_group_layout = QVBoxLayout()

        self.stats_label = QLabel(
            "🎓 课程进度：0 / 0\n"
            "⏱️  运行时长：0 秒\n"
            "📈 平均耗时：0 秒/门\n"
            "🔄 当前状态：待运行"
        )
        self.stats_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #333;")
        stats_group_layout.addWidget(self.stats_label)
        stats_group.setLayout(stats_group_layout)
        stats_layout.addWidget(stats_group)

        stats_layout.addStretch()
        tab_widget.addTab(stats_tab, "📊 统计信息")

        main_layout.addWidget(tab_widget)

        # 日志区域
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setStyleSheet("background-color: #f5f5f5; font-family: Consolas, monospace; font-size: 11px;")
        main_layout.addWidget(QLabel("📝 运行日志:"))
        main_layout.addWidget(self.log_area)

        # 启动定时器更新统计信息
        from PySide6.QtCore import QTimer
        self.stats_timer = QTimer()
        self.stats_timer.timeout.connect(self.update_stats)
        self.stats_timer.start(1000)  # 每秒更新

    def update_stats(self):
        """更新统计信息"""
        if self.engine and self.engine.is_running:
            elapsed = int(time.time() - self.engine.start_time) if self.engine.start_time else 0
            avg_time = elapsed // self.engine.course_count if self.engine.course_count > 0 else 0
            
            max_courses = self.max_courses_spin.value()
            if max_courses == 0:
                progress_text = f"{self.engine.course_count} / ∞"
            else:
                progress_text = f"{self.engine.course_count} / {max_courses}"
            
            status_text = "🔄 运行中..." if not self.engine.stop_requested else "⏹️ 已停止"
            
            self.stats_label.setText(
                f"🎓 课程进度：{progress_text}\n"
                f"⏱️  运行时长：{elapsed} 秒\n"
                f"📈 平均耗时：{avg_time} 秒/门\n"
                f"🔄 当前状态：{status_text}"
            )

    def load_course_template(self):
        """加载刷课模板"""
        # 清空现有行
        for row in self.rows:
            row.deleteLater()
        self.rows.clear()

        # 添加刷课常用模板
        template_tasks = [
            {"type": 1.0, "value": "100,200", "retry": 1},  # 示例：点击课程位置
            {"type": 5.0, "value": "3", "retry": 1},  # 等待3秒
            {"type": 1.0, "value": "100,200", "retry": 1},  # 点击开始学习
            {"type": 5.0, "value": "60", "retry": 1},  # 等待60秒（课程时长）
            {"type": 6.0, "value": "5", "retry": 1},  # 滚轮向下
            {"type": 5.0, "value": "30", "retry": 1},  # 等待30秒
        ]

        for task in template_tasks:
            self.add_row(task)

        QMessageBox.information(self, "模板已加载", "已加载刷课模板！\n\n请根据实际情况修改：\n1. 将坐标改为实际按钮位置\n2. 调整等待时间以匹配课程时长\n3. 如使用图片识别，请截图关键按钮")

    def add_row(self, data=None):
        # 移除底部的弹簧
        self.task_layout.takeAt(self.task_layout.count() - 1)

        row = TaskRow(self.task_layout, self.delete_row)
        if data:
            row.set_data(data)
        self.rows.append(row)

        # 加回弹簧
        self.task_layout.addStretch()

    def delete_row(self, row_widget):
        if row_widget in self.rows:
            self.rows.remove(row_widget)
            row_widget.deleteLater()

    def save_config(self):
        tasks = []
        for row in self.rows:
            data = row.get_data()
            # 允许保存空值，方便后续编辑
            tasks.append(data)

        if not tasks:
            QMessageBox.warning(self, "警告", "没有可保存的配置")
            return

        filename, _ = QFileDialog.getSaveFileName(self, "保存配置", os.getcwd(),
                                                  "JSON Files (*.json);;Text Files (*.txt)")
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(tasks, f, indent=4, ensure_ascii=False)
                QMessageBox.information(self, "成功", "配置已保存！")
            except Exception as e:
                QMessageBox.critical(self, "错误", f"保存失败: {e}")

    def load_config(self):
        filename, _ = QFileDialog.getOpenFileName(self, "导入配置", os.getcwd(),
                                                  "JSON Files (*.json);;Text Files (*.txt)")
        if not filename:
            return

        try:
            with open(filename, 'r', encoding='utf-8') as f:
                tasks = json.load(f)

            if not isinstance(tasks, list):
                raise ValueError("文件格式不正确")

            # 清空现有行
            for row in self.rows:
                row.deleteLater()
            self.rows.clear()

            # 重新添加行
            for task in tasks:
                self.add_row(task)

            QMessageBox.information(self, "成功", f"成功导入 {len(tasks)} 条指令！")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"导入失败: {e}")

    def start_task(self):
        tasks = []
        for row in self.rows:
            data = row.get_data()
            if not data['value']:
                QMessageBox.warning(self, "警告", "请检查有空参数的指令！")
                return
            tasks.append(data)

        if not tasks:
            QMessageBox.warning(self, "警告", "请至少添加一条指令！")
            return

        # 获取课程数限制
        max_courses = self.max_courses_spin.value()

        self.log_area.clear()
        self.log("========== 刷课任务开始 ==========")
        self.log(f"指令数量：{len(tasks)} 条")
        self.log(f"循环模式：{self.loop_check.currentText()}")
        self.log(f"课程限制：{max_courses if max_courses > 0 else '不限制'} 门")
        self.log("按 F8 键可快速停止任务")
        self.log("=" * 40)

        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.add_btn.setEnabled(False)

        # 注册F8热键
        if self.engine.register_f8_hotkey(self.stop_task):
            self.log("F8热键已启用")

        loop = (self.loop_check.currentText() == "循环执行")

        self.worker = WorkerThread(self.engine, tasks, loop, max_courses)
        self.worker.log_signal.connect(self.log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()
        # 开始运行后自动最小化窗口
        self.showMinimized()

    def stop_task(self):
        self.engine.stop()
        self.log("正在停止...")

    def on_finished(self):
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.add_btn.setEnabled(True)

        # 取消注册F8热键
        self.engine.unregister_f8_hotkey()

        self.log("=" * 40)
        self.log(f"任务已结束！共完成 {self.engine.course_count} 门课程")
        
        # 任务完成后自动还原窗口
        self.showNormal()
        self.activateWindow()

    def log(self, msg):
        self.log_area.append(msg)

    def set_app_icon(self):
        """设置应用图标（窗口左上角、任务栏等）"""
        # 支持多种图标路径查找方式
        icon_paths = [
            # 1. 当前目录下的图标文件
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "app_icon.ico"),
            "app_icon.ico",
            # 2. 资源目录
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "app_icon.ico"),
            # 3. 临时目录（PyInstaller打包后的路径）
            getattr(sys, '_MEIPASS', None) and os.path.join(getattr(sys, '_MEIPASS'), "app_icon.ico"),
        ]

        for icon_path in icon_paths:
            if icon_path and os.path.exists(icon_path):
                try:
                    self.setWindowIcon(QIcon(icon_path))
                    print(f"已加载图标: {icon_path}")
                    return
                except Exception as e:
                    print(f"加载图标失败 {icon_path}: {e}")
                    continue

        # 如果找不到图标文件，尝试使用系统默认图标
        print("提示: 未找到图标文件 app_icon.ico")
        print("图标文件应放在与程序相同目录下")

    def closeEvent(self, event):
        """窗口关闭事件：确保线程停止，防止残留"""
        if self.worker and self.worker.isRunning():
            self.engine.stop()
            self.worker.quit()
            self.worker.wait()

        # 取消注册F8热键
        self.engine.unregister_f8_hotkey()

        event.accept()


def main():
    app = QApplication(sys.argv)
    window = RPAWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
