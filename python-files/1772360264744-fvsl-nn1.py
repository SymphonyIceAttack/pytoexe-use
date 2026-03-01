import sys
import threading
import tkinter as tk
from tkinter import messagebox
import re
import pythoncom
import requests
import time
from PIL import ImageGrab
import numpy as np
from paddleocr import PaddleOCR
import win32com.client as win32
import logging
from typing import List, Dict, Optional, Set, Tuple
import json
import os
from datetime import datetime

# 配置日志
logging.basicConfig(
    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s',
    level=logging.INFO,
    filename='app.log',
    filemode='a'
)


class DataRecord:
    """数据记录管理器，按局次跟踪已写入的数据"""

    def __init__(self, record_file="written_records.json"):
        self.record_file = record_file
        # 格式: {局次: {姓名: [数据哈希列表]}}
        self.written_records = {}
        self.current_game_id = None  # 当前局次ID
        self.load_records()

    def load_records(self):
        """加载历史记录"""
        try:
            if os.path.exists(self.record_file):
                with open(self.record_file, 'r', encoding='utf-8') as f:
                    self.written_records = json.load(f)
                logging.info(f"已加载 {len(self.written_records)} 局历史记录")
        except Exception as e:
            logging.error(f"加载历史记录失败: {e}")
            self.written_records = {}

    def save_records(self):
        """保存历史记录"""
        try:
            # 只保留最近20局记录，避免文件过大
            if len(self.written_records) > 20:
                # 按局次排序，删除最早的
                sorted_keys = sorted(self.written_records.keys())
                for key in sorted_keys[:-20]:
                    del self.written_records[key]

            with open(self.record_file, 'w', encoding='utf-8') as f:
                json.dump(self.written_records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"保存历史记录失败: {e}")

    def create_data_hash(self, name: str, data_str: str) -> str:
        """创建数据哈希值用于唯一标识"""
        # 使用姓名+清理后的数据字符串
        clean_data = data_str.replace("哈", "").strip()
        key = f"{name}_{clean_data}"
        # 返回简单的哈希值
        return str(abs(hash(key)) % (10 ** 8))

    def start_new_game(self, game_id: str):
        """开始新的一局"""
        self.current_game_id = game_id
        # 为该局次创建空记录
        if game_id not in self.written_records:
            self.written_records[game_id] = {}
        logging.info(f"开始新局次: {game_id}")

    def is_data_written(self, name: str, data_str: str) -> bool:
        """检查当前局次中数据是否已经写入过"""
        if not self.current_game_id:
            return False

        if self.current_game_id not in self.written_records:
            return False

        if name not in self.written_records[self.current_game_id]:
            return False

        data_hash = self.create_data_hash(name, data_str)
        return data_hash in self.written_records[self.current_game_id][name]

    def add_record(self, name: str, data_str: str):
        """添加新的写入记录"""
        if not self.current_game_id:
            return

        if self.current_game_id not in self.written_records:
            self.written_records[self.current_game_id] = {}

        if name not in self.written_records[self.current_game_id]:
            self.written_records[self.current_game_id][name] = []

        data_hash = self.create_data_hash(name, data_str)
        self.written_records[self.current_game_id][name].append({
            "hash": data_hash,
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "data": data_str
        })
        self.save_records()


class Niu:
    def __init__(self, id: int = 0, userName: str = '', date: str = ''):
        self.id = id
        self.userName = userName
        self.date = date

    def __repr__(self):
        return f"Niu(id={self.id}, userName={self.userName}, date={self.date})"


class Result:
    def __init__(self, code: int = 0, message: str = '', data: Optional[Dict] = None):
        self.code = code
        self.message = message
        self.data = [Niu(**data)] if data else []

    def __repr__(self):
        return f"Result(code={self.code}, message={self.message}, data={self.data})"


class OverlayWindow:
    """显示识别区域的透明窗口"""

    def __init__(self, bbox: tuple):
        self.bbox = bbox  # (x1, y1, x2, y2)
        self.window = None

    def show(self):
        """显示透明窗口"""
        if self.window is None:
            self.window = tk.Tk()
            self.window.attributes('-alpha', 0.3)
            self.window.attributes('-topmost', True)
            self.window.overrideredirect(True)
            self.window.attributes('-toolwindow', True)
            self.window.attributes('-disabled', True)

            width = self.bbox[2] - self.bbox[0]
            height = self.bbox[3] - self.bbox[1]
            self.window.geometry(f"{width}x{height}+{self.bbox[0]}+{self.bbox[1]}")

            canvas = tk.Canvas(self.window, bg='black', highlightthickness=0)
            canvas.pack(fill=tk.BOTH, expand=True)
            canvas.create_rectangle(0, 0, width, height, outline='red', width=2)
            self.window.protocol("WM_DELETE_WINDOW", lambda: None)

    def hide(self):
        """隐藏透明窗口"""
        if self.window:
            self.window.destroy()
            self.window = None


class App:
    def __init__(self, root):
        self.root = root
        self.userName = ''
        self.appending = False
        self.quantiMSG = []
        self.quanyuan = []
        self.zhuangxuan = ''
        self.read_range = None
        self.ocr = PaddleOCR(
            use_gpu=False,  # 强制使用 CPU
            use_textline_orientation=False,
            lang='ch'
        )
        self.ws = None
        self.recognition_area = (50, 153, 220, 968)
        self.overlay = OverlayWindow(self.recognition_area)
        self.is_paused = False
        self.thread = None
        self.should_exit = False
        self.recognition_active = False
        self.excel_lock = threading.Lock()
        self.data_record = DataRecord()  # 数据记录管理器
        self.game_data_cache = set()  # 当前局次的数据缓存
        self.setup_ui()
        self.init_excel()

        # 定期清理旧记录（每天一次）
        self.cleanup_interval = 24 * 3600  # 24小时
        self.last_cleanup_time = time.time()

    def setup_ui(self):
        """初始化UI界面"""
        window_width = 400
        window_height = 200
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (window_width // 2)
        y = (screen_height // 2) - (window_height // 2)

        self.root.geometry(f'{window_width}x{window_height}+{x}+{y}')
        self.root.title("卡密验证")
        self.root.protocol("WM_DELETE_WINDOW", self.quit_app)
        self.create_login_window()

    def init_excel(self):
        """初始化Excel连接"""
        try:
            pythoncom.CoInitialize()
            self.excel = win32.GetObject(None, "Excel.Application")
            wb = self.excel.ActiveWorkbook
            self.ws = wb.Worksheets('录入')
        except Exception as e:
            messagebox.showerror("表格错误！", "请检查表格配置")
            logging.error(f"Excel初始化失败: {e}")
            sys.exit()

    def get_excel_data(self) -> bool:
        """实时获取Excel数据（强制刷新）"""
        with self.excel_lock:
            try:
                # 读取B列数据并过滤空值
                range_data = self.ws.Range("B8:B300").Value
                if not range_data:
                    logging.warning("Excel数据为空")
                    self.quanyuan = []
                    return False

                self.quanyuan = []
                for cell in range_data:
                    if cell and str(cell[0]).strip():
                        self.quanyuan.append([str(cell[0]).strip()])

                logging.info(f"已刷新姓名列表，共{len(self.quanyuan)}人")
                return True
            except Exception as e:
                logging.error(f"更新姓名列表失败: {e}")
                return False

    def verify_user(self, userName: str) -> Optional[Result]:
        """验证用户"""
        try:
            response = requests.get(
                "http://111.170.150.56:8085/getCode",
                params={"userName": userName},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            result_obj = Result(
                code=data['code'],
                message=data['message'],
                data=data.get('data')
            )

            if result_obj.code == 0:
                if not self.get_excel_data():
                    return None
                self.userName = userName
                return result_obj
            else:
                messagebox.showinfo("过期", "已到期")
                return None

        except requests.RequestException as e:
            messagebox.showinfo("网络错误", f"请求失败: {e}")
            logging.error(f"网络请求失败: {e}")
            return None

    def check_user_validity(self) -> bool:
        """检查用户有效性（强制版）"""
        try:
            start_time = time.time()
            response = requests.get(
                "http://111.170.150.56:8085/getCode",
                params={"userName": self.userName},
                timeout=5
            )
            response.raise_for_status()
            data = response.json()

            # 强制转换为Result对象
            result = Result(
                code=data['code'],
                message=data['message'],
                data=data.get('data')
            )

            logging.info(f"验证请求耗时: {time.time() - start_time:.2f}s, 结果: {result}")

            if result.code != 0:  # 0表示有效，非0表示过期
                messagebox.showerror("账号到期", f"账号已过期！原因: {result.message}")
                self.quit_app()
                return False
            return True

        except Exception as e:
            logging.error(f"验证请求失败: {e}")
            return True  # 网络错误时暂时允许继续使用

    def create_login_window(self):
        """创建登录窗口"""
        self.label = tk.Label(self.root, text="请输入卡密：")
        self.label.pack(pady=20)

        self.entry = tk.Entry(self.root)
        self.entry.pack(pady=10)

        self.login_btn = tk.Button(self.root, text="确认", command=self.verify_code)
        self.login_btn.pack()

    def verify_code(self):
        """验证卡密"""
        code = self.entry.get().strip()
        if not code:
            messagebox.showwarning("输入错误", "卡密不能为空")
            return

        result = self.verify_user(code)
        if result is not None:
            messagebox.showinfo("成功", "卡密验证成功!")
            self.overlay.show()  # 登录成功后才显示透明窗口
            self.open_main_window()

    def open_main_window(self):
        """打开主窗口"""
        for widget in self.root.winfo_children():
            widget.destroy()

        self.root.geometry('500x400')
        self.root.title('内容识别输出窗口')

        # 添加状态信息显示
        self.status_label = tk.Label(self.root, text="状态: 等待开始", fg="blue")
        self.status_label.pack(pady=5)

        # 添加当前局次显示
        self.game_label = tk.Label(self.root, text="当前局次: 未开始", fg="green")
        self.game_label.pack(pady=5)

        self.output_text = tk.Text(self.root, bg='black', fg='white', height=10, width=50)
        self.output_text.pack(pady=10)

        # 添加统计信息显示
        stats_frame = tk.Frame(self.root)
        stats_frame.pack(pady=5)

        self.total_label = tk.Label(stats_frame, text="总识别: 0")
        self.total_label.pack(side=tk.LEFT, padx=10)

        self.new_label = tk.Label(stats_frame, text="新写入: 0")
        self.new_label.pack(side=tk.LEFT, padx=10)

        self.skipped_label = tk.Label(stats_frame, text="已跳过: 0")
        self.skipped_label.pack(side=tk.LEFT, padx=10)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=10)

        self.start_button = tk.Button(btn_frame, text="开始识别", command=self.start_recognition)
        self.start_button.pack(side=tk.LEFT, padx=10)

        self.pause_button = tk.Button(btn_frame, text="暂停识别", command=self.pause_recognition)
        self.pause_button.pack(side=tk.LEFT, padx=10)

        # 添加清除记录按钮
        self.clear_btn = tk.Button(btn_frame, text="清除记录", command=self.clear_records)
        self.clear_btn.pack(side=tk.LEFT, padx=10)

        self.quit_button = tk.Button(btn_frame, text="退出", command=self.quit_app)
        self.quit_button.pack(side=tk.RIGHT, padx=10)

        # 初始化统计计数器
        self.total_count = 0
        self.new_count = 0
        self.skipped_count = 0

    def clear_records(self):
        """清除所有记录"""
        if messagebox.askyesno("确认", "确定要清除所有历史记录吗？"):
            self.data_record.written_records = {}
            self.data_record.save_records()
            self.game_data_cache.clear()
            messagebox.showinfo("成功", "历史记录已清除")
            logging.info("用户清除了所有历史记录")

    def start_recognition(self):
        """开始识别"""
        if not self.recognition_active:
            self.recognition_active = True
            self.is_paused = False
            self.start_button.config(state=tk.DISABLED)
            self.pause_button.config(state=tk.NORMAL)
            self.status_label.config(text="状态: 识别中", fg="green")

            self.thread = threading.Thread(
                target=self._real_recognition_loop,
                daemon=True
            )
            self.thread.start()
            self.output_text.insert(tk.END, "识别已启动...\n")
            logging.info("识别功能已启动")

    def pause_recognition(self):
        """暂停识别"""
        if self.recognition_active:
            self.is_paused = not self.is_paused
            state = "已暂停" if self.is_paused else "已恢复"
            color = "orange" if self.is_paused else "green"
            self.pause_button.config(text="暂停识别" if not self.is_paused else "继续识别")
            self.status_label.config(text=f"状态: {state}", fg=color)
            self.output_text.insert(tk.END, f"识别{state}...\n")
            logging.info(f"识别{state}")

    def _real_recognition_loop(self):
        """独立的识别线程"""
        pythoncom.CoInitialize()

        while self.recognition_active and not self.should_exit:
            if self.is_paused:
                time.sleep(0.5)
                continue

            try:
                start_time = time.time()
                text = self.get_screen_text()

                if text and text.strip():
                    self.total_count += 1
                    self.root.after(0, self._update_counters)

                    logging.info(f"OCR耗时: {time.time() - start_time:.2f}s, 识别内容: {text}")

                    # 将UI更新提交到主线程
                    self.root.after(0, lambda t=text: self._process_ocr_text(t))

                time.sleep(0.7)  # 关键控制：识别间隔

                # 定期清理旧记录
                current_time = time.time()
                if current_time - self.last_cleanup_time > self.cleanup_interval:
                    self.data_record.clear_old_records(days=1)
                    self.last_cleanup_time = current_time

            except Exception as e:
                logging.error(f"识别线程错误: {e}")

        pythoncom.CoUninitialize()

    def _update_counters(self):
        """更新统计计数器显示"""
        self.total_label.config(text=f"总识别: {self.total_count}")
        self.new_label.config(text=f"新写入: {self.new_count}")
        self.skipped_label.config(text=f"已跳过: {self.skipped_count}")

    def _process_ocr_text(self, text):
        """处理OCR识别的文本"""
        try:
            # 更新输出文本框
            self.output_text.insert(tk.END, f"{text}\n")
            self.output_text.see(tk.END)

            # 每处理5次消息就检查一次到期状态
            if self.total_count % 5 == 0:
                if not self.check_user_validity():
                    return

            # 处理识别到的消息
            newMsg = text.split()
            if '管理员' in newMsg:
                newMsg.remove('管理员')
            self.strMsg = newMsg

            # 处理消息
            self.process_messages()

        except Exception as e:
            logging.error(f"处理OCR文本失败: {e}")

    def get_screen_text(self) -> str:
        for _ in range(2):
            try:
                pic = ImageGrab.grab(bbox=self.recognition_area)
                img_np = np.array(pic)
                result = self.ocr.ocr(img_np, cls=False)
                if result and result[0] and isinstance(result[0], list):
                    texts = [line[1][0] for line in result[0] if line[1] and line[1][0]]
                    return ' '.join(texts)
                else:
                    return ""
            except Exception as e:
                logging.error(f"截图识别失败（重试中）: {e}")
                time.sleep(0.1)
        return ""

    def process_messages(self):
        """处理识别到的消息"""
        if not self.strMsg or len(self.strMsg) < 2:
            return

        # 检测庄选指令 - 修复数组越界问题
        for i in range(len(self.strMsg)):
            if '推图' in self.strMsg[i]:
                # 检查当前词是否包含"庄选"
                if '庄选' in self.strMsg[i]:
                    matches = re.findall(r"\d+", self.strMsg[i])
                    if matches:
                        self._handle_new_game(matches[0])
                # 检查下一个词是否存在且包含"庄选"
                elif i + 1 < len(self.strMsg) and '庄选' in self.strMsg[i + 1]:
                    matches = re.findall(r"\d+", self.strMsg[i + 1])
                    if matches:
                        self._handle_new_game(matches[0])

        # 只有检测到庄选后才处理数据
        if self.appending:
            i = 0
            while i < len(self.strMsg):
                current_word = self.strMsg[i]

                # 检查下一个词是否存在
                if i + 1 < len(self.strMsg):
                    next_word = self.strMsg[i + 1]

                    # 验证逻辑：中文姓名 + 数字组合
                    if re.fullmatch(r"^[\u4e00-\u9fa5]+$", current_word) and re.search(r'\d', next_word):
                        self._process_single_data(current_word, next_word)
                        i += 2  # 跳过已处理的数据
                        continue

                i += 1

    def _handle_new_game(self, zhuangxuan_num: str):
        """处理新的一局开始"""
        if self.zhuangxuan != zhuangxuan_num:
            # 清空当前局次的缓存
            self.game_data_cache.clear()
            self.zhuangxuan = zhuangxuan_num
            self.appending = True

            # 为这一局创建新的记录
            game_id = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_庄{zhuangxuan_num}"
            self.data_record.start_new_game(game_id)

            # 更新UI显示
            self.root.after(0, lambda: self.game_label.config(
                text=f"当前局次: 庄选{zhuangxuan_num}",
                fg="red"
            ))

            # 写入庄选到Excel
            try:
                self.ws.Cells(2, 15).Value = zhuangxuan_num
                logging.info(f"新局开始，庄选: {zhuangxuan_num}")

                # 在UI中显示新局开始
                self.root.after(0, lambda: self.output_text.insert(
                    tk.END, f"\n=== 新局开始: 庄选{zhuangxuan_num} ===\n"
                ))
            except Exception as e:
                logging.error(f"写入庄选失败: {e}")

    def _process_single_data(self, name: str, data_str: str):
        """处理单个数据条目（避免重复写入）"""
        try:
            self.ws.Cells(2, 15).Value = self.zhuangxuan

            # === 格式验证：必须包含至少一个分隔符（/ - *），末尾可带一个“哈” ===
            if not re.match(r'^\d+(?:[-/*+.\\;,]\d+)+哈?$', data_str):
                logging.info(f"忽略不符合格式的数据: {name} {data_str}")
                return

            # 原有哈字符位置验证（可选保留）
            has_ha = data_str.endswith('哈')
            if '哈' in data_str and not has_ha:
                logging.warning(f"无效哈字符位置: {name} {data_str}")
                return
            clean_str = data_str.rstrip('哈')

            # 创建唯一标识用于去重
            unique_key = f"{name}_{data_str}"

            # 检查是否在当前局次中已处理过
            if unique_key in self.game_data_cache:
                self.skipped_count += 1
                self.root.after(0, self._update_counters)
                logging.info(f"当前局次已处理，跳过: {name} - {data_str}")
                return

            # 检查是否已写入过（历史记录）
            if self.data_record.is_data_written(name, data_str):
                self.skipped_count += 1
                self.root.after(0, self._update_counters)
                logging.info(f"历史记录已存在，跳过: {name} - {data_str}")
                return

            # 提取所有数字部分
            number_pattern = r'\d+'
            numbers = re.findall(number_pattern, clean_str)

            if not numbers:
                logging.warning(f"未找到数字: {name} {data_str}")
                return

            # 第一个数字串处理
            first_number = numbers[0]

            # 查找姓名所在行
            try:
                found = self.ws.Range("B:B").Find(name, LookAt=1)
                if not found:
                    logging.warning(f"未找到姓名: {name}")
                    return

                row = found.Row

                # 先清空该行的C-G列
                self.ws.Range(f"C{row}:G{row}").Value = [["" for _ in range(5)]]

                # CDE列处理（第一个数字串的前3位）
                for i, char in enumerate(first_number[:3]):
                    self.ws.Cells(row, 3 + i).Value = char

                # F列处理（第二个数字串，如果没有"哈"）
                if len(numbers) >= 2 and not has_ha:
                    self.ws.Cells(row, 6).Value = numbers[1]

                # G列处理（如果有"哈"或者有第三个数字串）
                if has_ha and len(numbers) >= 2:
                    self.ws.Cells(row, 7).Value = numbers[1]
                elif len(numbers) >= 3:
                    self.ws.Cells(row, 7).Value = numbers[2]

                # 记录已处理的数据
                self.game_data_cache.add(unique_key)
                self.data_record.add_record(name, data_str)
                self.new_count += 1
                self.root.after(0, self._update_counters)

                logging.info(
                    f"新数据写入 {name}: C-E={first_number[:3]} | F={numbers[1] if len(numbers) >= 2 and not has_ha else ''} | G={numbers[-1] if len(numbers) >= 2 else ''}")

                # 在UI中显示新数据标记
                self.root.after(0, lambda: self.output_text.insert(
                    tk.END, f"[新数据] {name}: {data_str}\n"
                ))

            except Exception as e:
                logging.error(f"写入Excel失败 {name} {data_str}: {e}")
                self.root.after(0, lambda: messagebox.showwarning(
                    "写入失败", f"{name} 数据写入失败\n{e}"
                ))

        except Exception as e:
            logging.error(f"处理失败 {name} {data_str}: {e}")
            # 不弹出错误框，只记录日志，避免干扰
    def quit_app(self):
        """安全退出"""
        self.recognition_active = False
        self.should_exit = True

        # 保存退出时的统计信息
        stats = {
            "total_recognized": self.total_count,
            "new_written": self.new_count,
            "skipped": self.skipped_count,
            "current_game": self.zhuangxuan,
            "exit_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "user": self.userName
        }

        with open("exit_stats.log", "a", encoding="utf-8") as f:
            f.write(json.dumps(stats, ensure_ascii=False) + "\n")

        self.overlay.hide()
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=1)

        try:
            if self.excel:
                pythoncom.CoUninitialize()
        except:
            pass

        self.root.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    app = App(root)
    try:
        root.mainloop()
    except KeyboardInterrupt:
        app.quit_app()