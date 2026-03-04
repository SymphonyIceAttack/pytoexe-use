import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from pathlib import Path
import threading
from queue import Queue
import configparser
import atexit

class FileCopyTool:
    def __init__(self, root):
        self.root = root
        self.root.title("文件批量搜索复制工具（仅PDF格式_二级→三级层级匹配版）")
        self.root.geometry("800x650")
        self.root.resizable(False, False)

        # 初始化变量
        self.search_folder = tk.StringVar()
        self.new_folder_name = tk.StringVar(value="PDF图纸")
        self.log_text = None
        self.copy_queue = Queue()  # 复制任务队列
        self.copied_count = 0
        self.failed_count = 0
        self.skipped_count = 0  # 跳过的文件计数
        self.found_keywords = set()
        self.processed_files = set()  # 避免重复复制
        self.lock = threading.Lock()  # 线程锁

        # 配置文件相关
        self.config_path = Path.home() / ".file_copy_tool_pdf.ini"
        self.config = configparser.ConfigParser()
        self._load_config()
        atexit.register(self._save_config)

        # 初始化界面
        self._create_widgets()

    def _load_config(self):
        """加载配置文件中的搜索文件夹路径"""
        try:
            if self.config_path.exists():
                self.config.read(self.config_path, encoding="utf-8")
                last_folder = self.config.get("General", "last_search_folder", fallback="")
                if last_folder and os.path.exists(last_folder):
                    self.search_folder.set(last_folder)
                    self._log(f"已恢复上次搜索文件夹：{last_folder}")
        except Exception as e:
            self._log(f"加载配置失败：{str(e)}")

    def _save_config(self):
        """保存当前搜索文件夹到配置文件"""
        try:
            if not self.config.has_section("General"):
                self.config.add_section("General")
            current_folder = self.search_folder.get()
            if current_folder and os.path.exists(current_folder):
                self.config.set("General", "last_search_folder", current_folder)
            with open(self.config_path, "w", encoding="utf-8") as f:
                self.config.write(f)
        except Exception as e:
            self._log(f"保存配置失败：{str(e)}")

    def _create_widgets(self):
        # 1. 搜索文件夹选择区
        frame1 = tk.Frame(self.root, padx=10, pady=10)
        frame1.pack(fill=tk.X)
        tk.Label(frame1, text="搜索文件夹：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W)
        tk.Entry(frame1, textvariable=self.search_folder, width=50, font=("微软雅黑", 10)).grid(row=0, column=1, padx=5)
        tk.Button(frame1, text="浏览", command=self._select_search_folder, font=("微软雅黑", 10)).grid(row=0, column=2)

        # 2. 关键词输入区 - 明确PDF格式+层级匹配提示
        frame2 = tk.Frame(self.root, padx=10, pady=10)
        frame2.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame2, text="批量关键词（每行一个，仅PDF格式，二级前4→三级前8匹配）：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W)
        self.file_name_text = scrolledtext.ScrolledText(frame2, width=80, height=10, font=("微软雅黑", 10))
        self.file_name_text.grid(row=1, column=0, columnspan=3, pady=5)

        # 3. 新文件夹命名区
        frame3 = tk.Frame(self.root, padx=10, pady=10)
        frame3.pack(fill=tk.X)
        tk.Label(frame3, text="桌面新文件夹名称：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W)
        tk.Entry(frame3, textvariable=self.new_folder_name, width=50, font=("微软雅黑", 10)).grid(row=0, column=1, padx=5)

        # 4. 执行按钮区
        frame4 = tk.Frame(self.root, padx=10, pady=10)
        frame4.pack(fill=tk.X)
        self.start_btn = tk.Button(frame4, text="开始搜索复制PDF", command=self._start_copy_thread,
                  font=("微软雅黑", 10), bg="#4CAF50", fg="white", width=20)
        self.start_btn.pack()

        # 5. 日志区
        frame5 = tk.Frame(self.root, padx=10, pady=10)
        frame5.pack(fill=tk.BOTH, expand=True)
        tk.Label(frame5, text="操作日志：", font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W)
        self.log_text = scrolledtext.ScrolledText(frame5, width=80, height=12, font=("微软雅黑", 9), state=tk.DISABLED)
        self.log_text.grid(row=1, column=0, columnspan=3, pady=5)

    def _select_search_folder(self):
        """选择搜索文件夹"""
        folder = filedialog.askdirectory(title="选择要搜索的文件夹")
        if folder:
            self.search_folder.set(folder)
            self._save_config()
            self._log(f"已选择搜索文件夹：{folder}")

    def _log(self, msg):
        """线程安全的日志输出"""
        self.root.after(0, lambda: self._safe_log(msg))

    def _safe_log(self, msg):
        """实际执行日志写入（在主线程）"""
        self.log_text.config(state=tk.NORMAL)
        self.log_text.insert(tk.END, f"{msg}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state=tk.DISABLED)

    def _get_target_keywords(self):
        """获取关键词（极简处理）"""
        text = self.file_name_text.get("1.0", tk.END).strip()
        if not text:
            return []
        return [line.strip() for line in text.split("\n") if line.strip()]

    def _copy_worker(self, new_folder_path):
        """多线程复制工作函数"""
        while not self.copy_queue.empty():
            try:
                source_file, keyword = self.copy_queue.get()
                if source_file in self.processed_files:
                    self.copy_queue.task_done()
                    continue
                
                file_name = os.path.basename(source_file)
                target_file = os.path.join(new_folder_path, file_name)

                if os.path.exists(target_file):
                    with self.lock:
                        self.skipped_count += 1
                        self.processed_files.add(source_file)
                    self._log(f"⏭️ 跳过重复PDF：{file_name}（目标文件夹已存在）")
                    self.copy_queue.task_done()
                    continue

                shutil.copy2(source_file, target_file)
                with self.lock:
                    self.copied_count += 1
                    self.found_keywords.add(keyword)
                    self.processed_files.add(source_file)
                self._log(f"✅ 成功复制PDF：{os.path.basename(source_file)}")
                
            except Exception as e:
                with self.lock:
                    self.failed_count += 1
                self._log(f"❌ PDF复制失败 {os.path.basename(source_file)}：{str(e)}")
            finally:
                self.copy_queue.task_done()

    def _search_files(self, search_path, keywords):
        """
        核心逻辑：固定二级→三级层级匹配 + 仅PDF格式过滤
        1. 保留原固定层级匹配规则（二级前4→三级前8）
        2. 仅搜索.pdf后缀文件（忽略大小写，兼容PDF/Pdf等）
        3. 其余智能兜底、日志统计等功能完全保留
        """
        self._log("开始【仅PDF格式_二级→三级层级】精准极速搜索...")
        total_level2_match = 0  # 二级目录前4字符匹配数
        total_level3_match = 0  # 三级目录前8字符匹配数

        # 遍历所有关键词，按固定层级递进匹配
        for kw in keywords:
            # 提取匹配标识，不足则取全部
            kw_4 = kw[:4].lower() if len(kw) >= 4 else kw.lower()  # 二级目录匹配标识（前4）
            kw_8 = kw[:8].lower() if len(kw) >= 8 else kw.lower()  # 三级目录匹配标识（前8）
            self._log(f"🔍 关键词【{kw}】→ 二级匹配：{kw_4} | 三级匹配：{kw_8}（仅PDF）")

            # ---------------------- 第一步：获取搜索目录下的所有二级目录 ----------------------
            level2_dirs = []  # 搜索目录的所有二级目录路径
            for first_item in os.listdir(search_path):
                first_item_path = os.path.join(search_path, first_item)
                if os.path.isdir(first_item_path):  # 一级子目录（搜索目录的直接子目录）
                    for second_item in os.listdir(first_item_path):
                        second_item_path = os.path.join(first_item_path, second_item)
                        if os.path.isdir(second_item_path):  # 二级目录（一级子目录的直接子目录）
                            level2_dirs.append((second_item, second_item_path))  # (目录名, 目录路径)

            if not level2_dirs:
                self._log(f"⚠️  搜索目录下无二级目录，全局搜索PDF文件兜底")
                # 兜底：全局搜索含完整关键词的PDF文件
                for root_dir, _, files in os.walk(search_path, followlinks=True):
                    for file in files:
                        # 过滤PDF格式（忽略大小写）
                        if file.lower().endswith(".pdf"):
                            file_base = os.path.splitext(file)[0]
                            if kw in file_base:
                                self.copy_queue.put((os.path.join(root_dir, file), kw))
                continue

            # ---------------------- 第二步：二级目录匹配前4字符（一级匹配） ----------------------
            matched_level2 = []  # 匹配成功的二级目录路径
            for dir_name, dir_path in level2_dirs:
                if kw_4 in dir_name.lower():
                    matched_level2.append(dir_path)

            if matched_level2:
                total_level2_match += len(matched_level2)
                self._log(f"✅ 二级目录【前4字符】匹配到 {len(matched_level2)} 个目标目录")
                matched_level3 = []  # 匹配成功的三级目录路径

                # ---------------------- 第三步：三级目录匹配前8字符（二级匹配） ----------------------
                for l2_path in matched_level2:
                    # 仅获取当前二级目录下的三级目录（固定层级，不递归）
                    for third_item in os.listdir(l2_path):
                        third_item_path = os.path.join(l2_path, third_item)
                        if os.path.isdir(third_item_path):  # 三级目录（二级目录的直接子目录）
                            if kw_8 in third_item.lower():
                                matched_level3.append(third_item_path)

                # ---------------------- 第四步：根据三级目录匹配结果处理（仅PDF） ----------------------
                if matched_level3:
                    # 三级目录匹配成功 → 仅在这些三级目录内搜索PDF文件
                    total_level3_match += len(matched_level3)
                    self._log(f"✅ 三级目录【前8字符】匹配到 {len(matched_level3)} 个目标目录，搜索PDF文件")
                    for l3_path in matched_level3:
                        for root_dir, _, files in os.walk(l3_path, followlinks=True):
                            for file in files:
                                if file.lower().endswith(".pdf"):  # 过滤PDF格式
                                    file_base = os.path.splitext(file)[0]
                                    if kw in file_base:
                                        self.copy_queue.put((os.path.join(root_dir, file), kw))
                else:
                    # 三级目录无匹配 → 回退到二级匹配目录内搜索PDF
                    self._log(f"⚠️  三级目录未匹配，回退到二级目录内搜索PDF文件")
                    for l2_path in matched_level2:
                        for root_dir, _, files in os.walk(l2_path, followlinks=True):
                            for file in files:
                                if file.lower().endswith(".pdf"):  # 过滤PDF格式
                                    file_base = os.path.splitext(file)[0]
                                    if kw in file_base:
                                        self.copy_queue.put((os.path.join(root_dir, file), kw))
            else:
                # 二级目录无匹配 → 全局搜索PDF文件兜底
                self._log(f"⚠️  二级目录未匹配，全局搜索PDF文件兜底")
                for root_dir, _, files in os.walk(search_path, followlinks=True):
                    for file in files:
                        if file.lower().endswith(".pdf"):  # 过滤PDF格式
                            file_base = os.path.splitext(file)[0]
                            if kw in file_base:
                                self.copy_queue.put((os.path.join(root_dir, file), kw))

        # 打印层级匹配统计结果
        self._log(f"📌 匹配完成：二级{total_level2_match}个 | 三级{total_level3_match}个 | 待复制PDF总数：{self.copy_queue.qsize()}")

    def _start_copy_thread(self):
        """启动多线程搜索和复制（避免界面卡死）"""
        self.start_btn.config(state=tk.DISABLED)
        # 重置统计数据
        self.copied_count = 0
        self.failed_count = 0
        self.skipped_count = 0
        self.found_keywords = set()
        self.processed_files.clear()
        # 清空日志
        self.log_text.config(state=tk.NORMAL)
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state=tk.DISABLED)

        # 1. 基础校验
        search_path = self.search_folder.get()
        if not search_path or not os.path.exists(search_path):
            messagebox.showerror("错误", "请选择有效的搜索文件夹！")
            self.start_btn.config(state=tk.NORMAL)
            return

        keywords = self._get_target_keywords()
        if not keywords:
            messagebox.showerror("错误", "请输入至少一个关键词！")
            self.start_btn.config(state=tk.NORMAL)
            return

        new_folder_name = self.new_folder_name.get().strip()
        if not new_folder_name:
            messagebox.showerror("错误", "新文件夹名称不能为空！")
            self.start_btn.config(state=tk.NORMAL)
            return

        # 2. 创建目标文件夹
        new_folder_path = Path.home() / "Desktop" / new_folder_name
        try:
            os.makedirs(new_folder_path, exist_ok=True)
            self._log(f"PDF目标文件夹：{new_folder_path}")
        except Exception as e:
            messagebox.showerror("错误", f"创建文件夹失败：{str(e)}")
            self.start_btn.config(state=tk.NORMAL)
            return

        # 3. 启动主任务线程
        def main_task():
            self._search_files(search_path, keywords)
            
            # 启动4个复制线程
            threads = []
            for _ in range(4):
                t = threading.Thread(target=self._copy_worker, args=(new_folder_path,))
                t.daemon = True
                t.start()
                threads.append(t)
            
            # 等待所有复制任务完成
            self.copy_queue.join()
            
            # 统计结果
            not_found = [kw for kw in keywords if kw not in self.found_keywords]
            result = f"✅ PDF复制完成！\n成功：{self.copied_count} 个\n失败：{self.failed_count} 个\n跳过：{self.skipped_count} 个"
            if not_found:
                result += f"\n\n未找到的关键词：\n{chr(10).join(not_found)}"
            
            # 主线程弹窗提示
            self.root.after(0, lambda: messagebox.showinfo("完成", result))
            self.root.after(0, lambda: self.start_btn.config(state=tk.NORMAL))
            # 日志写入最终统计
            self._log(f"\n===== PDF最终统计 =====")
            self._log(f"成功复制PDF：{self.copied_count} 个")
            self._log(f"复制失败：{self.failed_count} 个")
            self._log(f"跳过重复：{self.skipped_count} 个")
            if not_found:
                self._log(f"未找到关键词：{', '.join(not_found)}")

        threading.Thread(target=main_task, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = FileCopyTool(root)
    root.mainloop()
