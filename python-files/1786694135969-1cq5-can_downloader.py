# -*- coding: utf-8 -*-
"""
Created on Fri Aug 14 09:11:52 2026

@author: xshen3
"""

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
辉景CAN数据批量下载工具 - GUI桌面版 v1.6 (修复时间解析)
"""

import requests
import os
import re
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox

# ========== 核心下载类 ==========
class CANDownloader:
    def __init__(self, base_url, username, password, save_dir, file_type, max_workers=2):
        self.base_url = base_url
        self.username = username
        self.password = password
        self.save_dir = save_dir
        self.file_type = file_type
        self.max_workers = max_workers
        self.is_running = False
        self.should_stop = False
        self.current_progress = {}
        self.partial_files = []
        
        if file_type == "dat":
            self.extensions = [".dat"]
        elif file_type == "blf":
            self.extensions = [".blf"]
        else:
            self.extensions = [".dat", ".blf"]
        
        os.makedirs(save_dir, exist_ok=True)
    
    def stop(self):
        self.should_stop = True
        self.is_running = False
    
    def parse_size(self, size_str):
        """解析文件大小，支持多种格式"""
        if size_str is None:
            return 0
        if isinstance(size_str, (int, float)):
            return int(size_str)
        if not size_str:
            return 0
        size_str = str(size_str).strip()
        
        # 尝试直接转换为数字
        try:
            return int(float(size_str))
        except ValueError:
            pass
        
        # 尝试解析带单位的字符串
        units = {'B': 1, 'KB': 1024, 'MB': 1024 * 1024, 'GB': 1024 * 1024 * 1024}
        match = re.match(r'([\d.]+)\s*([A-Za-z]+)', size_str)
        if match:
            value = float(match.group(1))
            unit = match.group(2).upper()
            if unit in units:
                return int(value * units[unit])
        return 0
    
    def get_all_files(self, callback=None):
        all_files = []
        offset = 0
        limit = 100
        
        while True:
            if self.should_stop:
                if callback:
                    callback("⏹ 已停止获取文件列表", "warning")
                break
                
            if callback:
                callback(f"获取文件列表... offset={offset}")
            url = f"{self.base_url}/dataList?guid=test&sort=date&order=desc&offset={offset}&limit={limit}"
            try:
                resp = requests.get(url, auth=(self.username, self.password), timeout=10)
                data = resp.json()
            except Exception as e:
                if callback:
                    callback(f"❌ 获取失败: {e}")
                break
            
            rows = data.get("rows", [])
            if not rows:
                break
            all_files.extend(rows)
            offset += limit
            total = int(data.get("total", 0))
            if offset >= total:
                break
        
        return all_files
    
    def parse_file_time(self, filename):
        """解析文件名中的时间戳"""
        # 匹配模式: 2026-08-14-05_45_xx_xx 或 2026-08-14-05_45_xx
        pattern = r'(\d{4}-\d{2}-\d{2}-\d{2}_\d{2}_\d{2}(?:_\d{2})?)'
        match = re.search(pattern, filename)
        if not match:
            return None
        
        time_str = match.group(1)
        # 替换下划线为冒号，但保留最后的毫秒部分
        parts = time_str.split('_')
        if len(parts) < 3:
            return None
        
        # parts[0] = "2026-08-14-05" (日期+小时)
        # parts[1] = "45" (分钟)
        # parts[2] = "xx" (秒)
        date_hour = parts[0]
        minute = parts[1]
        second = parts[2] if len(parts) > 2 else "00"
        
        # 分离日期和小时
        date_hour_parts = date_hour.rsplit('-', 1)
        if len(date_hour_parts) != 2:
            return None
        
        date_str = date_hour_parts[0]  # "2026-08-14"
        hour_str = date_hour_parts[1]  # "05"
        
        # 构建完整时间字符串
        time_str_full = f"{date_str} {hour_str}:{minute}:{second}"
        
        try:
            return datetime.strptime(time_str_full, "%Y-%m-%d %H:%M:%S")
        except ValueError as e:
            return None
    
    def filter_by_time(self, files, start_str, stop_str, callback=None):
        try:
            start = datetime.strptime(start_str, "%Y-%m-%d %H:%M")
            stop = datetime.strptime(stop_str, "%Y-%m-%d %H:%M")
        except ValueError:
            if callback:
                callback("❌ 时间格式错误！")
            return []
        
        # ★★★ 添加调试日志 ★★★
        callback(f"🔍 开始筛选时间范围: {start} ~ {stop}")
        
        unique_files = {}
        filtered = []
        total = len(files)
        sample_count = 0  # 用于显示样例
        
        for i, f in enumerate(files, 1):
            if self.should_stop:
                if callback:
                    callback("⏹ 已停止筛选", "warning")
                break
                
            name = f.get("name", "")
            if not name:
                continue
            
            allowed = False
            for ext in self.extensions:
                if name.endswith(ext):
                    allowed = True
                    break
            if not allowed:
                continue
            
            if i % 100 == 0 and callback:
                callback(f"筛选进度: {i}/{total}")
            
            file_time = self.parse_file_time(name)
            if file_time is None:
                # ★★★ 显示前几个无法解析的文件名，帮助调试 ★★★
                if sample_count < 5:
                    callback(f"⚠️ 无法解析时间: {name}", "warning")
                    sample_count += 1
                continue
            
            # ★★★ 显示前几个成功解析的时间 ★★★
            if sample_count < 5:
                callback(f"✅ 解析成功: {name} -> {file_time}")
                sample_count += 1
            
            if start <= file_time <= stop:
                if name not in unique_files:
                    unique_files[name] = f
                    filtered.append(f)
        
        callback(f"🔍 筛选完成，找到 {len(filtered)} 个匹配文件")
        return filtered
    
    def format_size(self, size_bytes):
        if size_bytes < 1024:
            return f"{size_bytes}B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes/1024:.1f}KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes/1024/1024:.1f}MB"
        else:
            return f"{size_bytes/1024/1024/1024:.2f}GB"
    
    def download_file(self, file_info, index, total, callback=None):
        name = file_info["name"]
        url = file_info.get("url", f"{self.base_url}/dataFile?guid=test&file={name}")
        save_path = os.path.join(self.save_dir, name)
        
        if self.should_stop:
            return False
        
        # 只检查文件是否存在
        if os.path.exists(save_path):
            local_size = os.path.getsize(save_path)
            if local_size > 0:
                if callback:
                    callback(f"[{index}/{total}] ⏭️ 已存在，跳过: {name}")
                return True
            else:
                if callback:
                    callback(f"[{index}/{total}] ⚠️ 文件为空，重新下载: {name}")
                try:
                    os.remove(save_path)
                except:
                    pass
        
        try:
            if callback:
                size_str = file_info.get("size", "0")
                server_size = self.parse_size(size_str)
                callback(f"[{index}/{total}] ⬇️ 开始下载: {name} ({self.format_size(server_size)})")
            
            resp = requests.get(url, stream=True, auth=(self.username, self.password), timeout=60)
            if resp.status_code != 200:
                if callback:
                    callback(f"[{index}/{total}] ❌ HTTP {resp.status_code}: {name}")
                return False
            
            content_length = resp.headers.get('content-length')
            total_size = int(content_length) if content_length else 0
            
            temp_path = save_path + ".tmp"
            
            with open(temp_path, 'wb') as f:
                downloaded = 0
                last_update = 0
                start_time = time.time()
                
                for chunk in resp.iter_content(chunk_size=8192):
                    if self.should_stop:
                        if callback:
                            callback(f"[{index}/{total}] ⏹ 已停止下载: {name}", "warning")
                        f.close()
                        if os.path.exists(temp_path):
                            try:
                                os.remove(temp_path)
                                if callback:
                                    callback(f"[{index}/{total}] 🗑️ 已删除未完成的文件: {name}", "warning")
                            except Exception as e:
                                if callback:
                                    callback(f"[{index}/{total}] ⚠️ 删除临时文件失败: {e}", "warning")
                        return False
                    
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        current_time = time.time()
                        if current_time - last_update > 0.2:
                            last_update = current_time
                            
                            if total_size > 0:
                                progress = (downloaded / total_size) * 100
                                elapsed = current_time - start_time
                                speed = downloaded / elapsed if elapsed > 0 else 0
                                
                                progress_msg = (f"[{index}/{total}] 📊 {progress:.1f}% "
                                              f"({self.format_size(downloaded)}/{self.format_size(total_size)}) "
                                              f"⚡ {self.format_size(speed)}/s")
                                
                                if callback:
                                    callback(progress_msg, is_progress=True)
            
            if os.path.exists(temp_path):
                if os.path.exists(save_path):
                    try:
                        os.remove(temp_path)
                        if callback:
                            callback(f"[{index}/{total}] ⚠️ 目标文件已存在，跳过: {name}")
                        return True
                    except:
                        pass
                else:
                    os.rename(temp_path, save_path)
            
            if callback:
                callback(f"[{index}/{total}] ✅ 完成: {name}")
            return True
            
        except Exception as e:
            if callback:
                callback(f"[{index}/{total}] ❌ 失败: {name} - {e}")
            temp_path = save_path + ".tmp"
            if os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    if callback:
                        callback(f"[{index}/{total}] 🗑️ 已删除未完成的文件: {name}", "warning")
                except:
                    pass
            return False
    
    def start_download(self, start_time, stop_time, callback=None):
        self.is_running = True
        self.should_stop = False
        self.partial_files = []
        
        if callback:
            callback("=" * 60)
            callback(f"📅 时间范围: {start_time} ~ {stop_time}")
            callback("=" * 60)
        
        all_files = self.get_all_files(callback)
        
        if self.should_stop:
            if callback:
                callback("⏹ 已停止下载", "warning")
            self.is_running = False
            return
        
        if not all_files:
            if callback:
                callback("❌ 未获取到任何文件")
            self.is_running = False
            return
        
        if callback:
            callback(f"✅ 共获取到 {len(all_files)} 个文件记录")
        
        target_files = self.filter_by_time(all_files, start_time, stop_time, callback)
        
        if self.should_stop:
            if callback:
                callback("⏹ 已停止下载", "warning")
            self.is_running = False
            return
        
        if not target_files:
            if callback:
                callback(f"❌ 未找到符合条件的文件")
                callback("💡 提示: 请检查文件名中的时间格式是否匹配")
                callback("💡 文件名格式应为: xxx_YYYY-MM-DD-HH_MM_SS_xxx.dat")
            self.is_running = False
            return
        
        if callback:
            callback(f"📋 时间范围内共找到 {len(target_files)} 个文件")
            callback("")
        
        # 只按文件名匹配
        download_list = []
        existing_list = []
        existing_size = 0
        
        local_files = set()
        if os.path.exists(self.save_dir):
            for f in os.listdir(self.save_dir):
                if f.endswith('.tmp'):
                    try:
                        os.remove(os.path.join(self.save_dir, f))
                        if callback:
                            callback(f"🧹 清理临时文件: {f}", "warning")
                    except:
                        pass
                    continue
                for ext in self.extensions:
                    if f.endswith(ext):
                        local_files.add(f)
                        break
        
        if callback:
            callback(f"📂 本地已有匹配文件: {len(local_files)} 个")
        
        for f in target_files:
            name = f["name"]
            save_path = os.path.join(self.save_dir, name)
            
            if name in local_files or os.path.exists(save_path):
                try:
                    if os.path.getsize(save_path) > 0:
                        existing_list.append(name)
                        existing_size += os.path.getsize(save_path)
                        continue
                    else:
                        if callback:
                            callback(f"⚠️ 文件为空: {name}，将重新下载", "warning")
                        try:
                            os.remove(save_path)
                        except:
                            pass
                except:
                    pass
            
            download_list.append(f)
        
        target_files = download_list
        
        if callback:
            if existing_list:
                callback("")
                callback(f"⏭️ ✅ 已存在的文件: {len(existing_list)} 个 ({self.format_size(existing_size)})，将跳过")
                display_count = min(len(existing_list), 20)
                for name in existing_list[:display_count]:
                    callback(f"   📁 {name}")
                if len(existing_list) > display_count:
                    callback(f"   ... 还有 {len(existing_list) - display_count} 个文件")
            
            callback("")
        
        if not target_files:
            if callback:
                callback("🎉 所有文件都已下载完成！无需再次下载")
                callback(f"📁 保存位置: {self.save_dir}")
                callback("=" * 60)
            self.is_running = False
            return
        
        total_size = 0
        for f in target_files:
            total_size += self.parse_size(f.get("size", 0))
        
        if callback:
            callback(f"📥 需要下载: {len(target_files)} 个文件")
            callback(f"💾 总大小约 {self.format_size(total_size)}")
            callback("-" * 60)
            callback("🚀 开始下载...")
            callback("")
        
        success = 0
        failed = 0
        stopped = False
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(self.download_file, f, i, len(target_files), callback): f
                for i, f in enumerate(target_files, 1)
            }
            
            for future in as_completed(futures):
                if self.should_stop:
                    stopped = True
                    for f in futures:
                        f.cancel()
                    break
                
                try:
                    result = future.result()
                    if result:
                        success += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    if callback:
                        callback(f"❌ 任务异常: {e}")
                
                if callback and not self.should_stop:
                    total_done = success + failed
                    callback(f"📈 总进度: {total_done}/{len(target_files)} 已完成", is_progress=True)
        
        if stopped or self.should_stop:
            if callback:
                callback("")
                callback("🧹 正在清理未完成的临时文件...", "warning")
            
            cleaned_count = 0
            for filename in os.listdir(self.save_dir):
                if filename.endswith('.tmp'):
                    temp_path = os.path.join(self.save_dir, filename)
                    try:
                        os.remove(temp_path)
                        cleaned_count += 1
                    except:
                        pass
            
            if cleaned_count > 0 and callback:
                callback(f"🗑️ 已清理 {cleaned_count} 个临时文件", "warning")
        
        if callback:
            callback("")
            callback("=" * 60)
            if stopped or self.should_stop:
                callback("⏹ 下载已停止！", "warning")
                callback(f"  ✅ 已完成: {success} 个")
                callback(f"  ⏸ 未完成: {failed} 个")
            else:
                callback("📊 下载完成！")
                callback(f"  ✅ 成功: {success} 个")
                callback(f"  ❌ 失败: {failed} 个")
            callback(f"  📁 保存位置: {self.save_dir}")
            callback("=" * 60)
        
        self.is_running = False
        return success, failed


# ========== 自定义日期时间输入框 ==========
class DateEntry(ttk.Frame):
    """固定格式的日期输入框 (YYYY-MM-DD)"""
    def __init__(self, master, initial_value=None, **kwargs):
        super().__init__(master, **kwargs)
        
        ttk.Label(self, text="年", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 2))
        self.year_entry = ttk.Entry(self, width=5, justify='center', font=('Arial', 10))
        self.year_entry.pack(side=tk.LEFT)
        ttk.Label(self, text="-", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self, text="月", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 2))
        self.month_entry = ttk.Entry(self, width=3, justify='center', font=('Arial', 10))
        self.month_entry.pack(side=tk.LEFT)
        ttk.Label(self, text="-", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self, text="日", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 2))
        self.day_entry = ttk.Entry(self, width=3, justify='center', font=('Arial', 10))
        self.day_entry.pack(side=tk.LEFT)
        
        if initial_value:
            self.set(initial_value)
        else:
            now = datetime.now()
            self.set(now.strftime("%Y-%m-%d"))
        
        self.year_entry.bind('<KeyRelease>', self._on_key_release)
        self.month_entry.bind('<KeyRelease>', self._on_key_release)
        self.day_entry.bind('<KeyRelease>', self._on_key_release)
        
        self.year_entry.bind('<FocusIn>', lambda e: self.year_entry.select_range(0, tk.END))
        self.month_entry.bind('<FocusIn>', lambda e: self.month_entry.select_range(0, tk.END))
        self.day_entry.bind('<FocusIn>', lambda e: self.day_entry.select_range(0, tk.END))
    
    def _on_key_release(self, event):
        widget = event.widget
        current = widget.get()
        
        if current and not current.isdigit():
            cleaned = ''.join(filter(str.isdigit, current))
            widget.delete(0, tk.END)
            widget.insert(0, cleaned)
            return
        
        if widget == self.year_entry and len(current) >= 4:
            self.month_entry.focus()
            self.month_entry.select_range(0, tk.END)
        elif widget == self.month_entry and len(current) >= 2:
            self.day_entry.focus()
            self.day_entry.select_range(0, tk.END)
        elif widget == self.day_entry and len(current) >= 2:
            self.master.focus()
    
    def get(self):
        year = self.year_entry.get().strip()
        month = self.month_entry.get().strip()
        day = self.day_entry.get().strip()
        
        if not year or not month or not day:
            return ""
        
        year = year.zfill(4)
        month = month.zfill(2)
        day = day.zfill(2)
        
        return f"{year}-{month}-{day}"
    
    def set(self, value):
        if isinstance(value, datetime):
            value = value.strftime("%Y-%m-%d")
        parts = value.split('-')
        if len(parts) == 3:
            self.year_entry.delete(0, tk.END)
            self.year_entry.insert(0, parts[0])
            self.month_entry.delete(0, tk.END)
            self.month_entry.insert(0, parts[1])
            self.day_entry.delete(0, tk.END)
            self.day_entry.insert(0, parts[2])


class TimeEntry(ttk.Frame):
    """固定格式的时间输入框 (HH:MM)"""
    def __init__(self, master, initial_value=None, **kwargs):
        super().__init__(master, **kwargs)
        
        ttk.Label(self, text="时", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 2))
        self.hour_entry = ttk.Entry(self, width=3, justify='center', font=('Arial', 10))
        self.hour_entry.pack(side=tk.LEFT)
        ttk.Label(self, text=":", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=2)
        
        ttk.Label(self, text="分", font=('Arial', 9)).pack(side=tk.LEFT, padx=(0, 2))
        self.minute_entry = ttk.Entry(self, width=3, justify='center', font=('Arial', 10))
        self.minute_entry.pack(side=tk.LEFT)
        
        if initial_value:
            self.set(initial_value)
        else:
            now = datetime.now()
            self.set(now.strftime("%H:%M"))
        
        self.hour_entry.bind('<KeyRelease>', self._on_key_release)
        self.minute_entry.bind('<KeyRelease>', self._on_key_release)
        
        self.hour_entry.bind('<FocusIn>', lambda e: self.hour_entry.select_range(0, tk.END))
        self.minute_entry.bind('<FocusIn>', lambda e: self.minute_entry.select_range(0, tk.END))
    
    def _on_key_release(self, event):
        widget = event.widget
        current = widget.get()
        
        if current and not current.isdigit():
            cleaned = ''.join(filter(str.isdigit, current))
            widget.delete(0, tk.END)
            widget.insert(0, cleaned)
            return
        
        if widget == self.hour_entry and len(current) >= 2:
            self.minute_entry.focus()
            self.minute_entry.select_range(0, tk.END)
        elif widget == self.minute_entry and len(current) >= 2:
            self.master.focus()
    
    def get(self):
        hour = self.hour_entry.get().strip()
        minute = self.minute_entry.get().strip()
        
        if not hour or not minute:
            return ""
        
        hour = hour.zfill(2)
        minute = minute.zfill(2)
        
        try:
            h = int(hour)
            m = int(minute)
            if 0 <= h <= 23 and 0 <= m <= 59:
                return f"{hour}:{minute}"
        except ValueError:
            pass
        return ""
    
    def set(self, value):
        if isinstance(value, datetime):
            value = value.strftime("%H:%M")
        parts = value.split(':')
        if len(parts) == 2:
            self.hour_entry.delete(0, tk.END)
            self.hour_entry.insert(0, parts[0])
            self.minute_entry.delete(0, tk.END)
            self.minute_entry.insert(0, parts[1])


# ========== GUI界面类 ==========
class CANDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🚗 辉景CAN数据批量下载工具 v1.6")
        
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        win_width = min(int(screen_width * 0.85), 1200)
        win_height = min(int(screen_height * 0.85), 900)
        
        x = (screen_width - win_width) // 2
        y = (screen_height - win_height) // 2
        
        self.root.geometry(f"{win_width}x{win_height}+{x}+{y}")
        self.root.minsize(800, 600)
        self.root.resizable(True, True)
        
        main_frame = ttk.Frame(root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        main_frame.columnconfigure(0, weight=1)
        
        title = ttk.Label(main_frame, text="🚗 辉景CAN数据批量下载工具 v1.6", 
                          font=('Arial', 14, 'bold'))
        title.grid(row=0, column=0, pady=(0, 10), sticky=tk.W)
        
        top_frame = ttk.Frame(main_frame)
        top_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        top_frame.columnconfigure(0, weight=1)
        
        bottom_frame = ttk.Frame(main_frame)
        bottom_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        bottom_frame.columnconfigure(0, weight=1)
        bottom_frame.rowconfigure(0, weight=1)
        
        main_frame.rowconfigure(1, weight=0)
        main_frame.rowconfigure(2, weight=1)
        
        # ===== 1. 设备连接 =====
        frame1 = ttk.LabelFrame(top_frame, text="🔗 设备连接", padding="8")
        frame1.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        row1 = ttk.Frame(frame1)
        row1.pack(fill=tk.X)
        
        ttk.Label(row1, text="设备IP:").pack(side=tk.LEFT, padx=(0, 5))
        self.ip_entry = ttk.Entry(row1, width=18)
        self.ip_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.ip_entry.insert(0, "http://192.168.6.1")
        
        ttk.Label(row1, text="用户名:").pack(side=tk.LEFT, padx=(0, 5))
        self.user_entry = ttk.Entry(row1, width=12)
        self.user_entry.pack(side=tk.LEFT, padx=(0, 15))
        self.user_entry.insert(0, "12345678")
        
        ttk.Label(row1, text="密码:").pack(side=tk.LEFT, padx=(0, 5))
        self.pwd_entry = ttk.Entry(row1, width=12, show="*")
        self.pwd_entry.pack(side=tk.LEFT)
        self.pwd_entry.insert(0, "12345678")
        
        # ===== 2. 时间范围 =====
        frame2 = ttk.LabelFrame(top_frame, text="📅 时间范围", padding="8")
        frame2.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        row2_start = ttk.Frame(frame2)
        row2_start.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(row2_start, text="开始:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 8))
        self.start_date = DateEntry(row2_start)
        self.start_date.pack(side=tk.LEFT, padx=(0, 10))
        self.start_date.set(datetime.now().strftime("%Y-%m-%d"))
        
        self.start_time = TimeEntry(row2_start)
        self.start_time.pack(side=tk.LEFT)
        self.start_time.set("00:00")
        
        row2_stop = ttk.Frame(frame2)
        row2_stop.pack(fill=tk.X)
        
        ttk.Label(row2_stop, text="结束:", font=('Arial', 10, 'bold')).pack(side=tk.LEFT, padx=(0, 8))
        self.stop_date = DateEntry(row2_stop)
        self.stop_date.pack(side=tk.LEFT, padx=(0, 10))
        self.stop_date.set(datetime.now().strftime("%Y-%m-%d"))
        
        self.stop_time = TimeEntry(row2_stop)
        self.stop_time.pack(side=tk.LEFT)
        self.stop_time.set("00:00")
        
        hint_frame = ttk.Frame(frame2)
        hint_frame.pack(fill=tk.X, pady=(5, 0))
        ttk.Label(hint_frame, text="💡 按顺序输入: 年→月→日→时→分，自动跳转", 
                  font=('Arial', 9), foreground="gray").pack(side=tk.LEFT)
        
        # ===== 3. 保存位置 =====
        frame3 = ttk.LabelFrame(top_frame, text="💾 保存设置", padding="8")
        frame3.grid(row=2, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        frame3.columnconfigure(1, weight=1)
        
        row3 = ttk.Frame(frame3)
        row3.pack(fill=tk.X)
        
        ttk.Label(row3, text="保存目录:").pack(side=tk.LEFT, padx=(0, 8))
        self.save_entry = ttk.Entry(row3)
        self.save_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
        self.save_entry.insert(0, r"D:\CAN_DATA")
        
        ttk.Button(row3, text="浏览...", command=self.browse_folder).pack(side=tk.LEFT)
        
        # ===== 4. 文件类型 =====
        frame4 = ttk.LabelFrame(top_frame, text="📄 文件类型", padding="8")
        frame4.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 8))
        
        self.file_type_var = tk.StringVar(value="dat")
        row4 = ttk.Frame(frame4)
        row4.pack(fill=tk.X)
        
        ttk.Radiobutton(row4, text="仅 .dat", variable=self.file_type_var, 
                        value="dat").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(row4, text="仅 .blf", variable=self.file_type_var, 
                        value="blf").pack(side=tk.LEFT, padx=(0, 20))
        ttk.Radiobutton(row4, text="全部 (.dat + .blf)", variable=self.file_type_var, 
                        value="all").pack(side=tk.LEFT)
        
        # ===== 5. 下载设置 + 按钮 =====
        frame5 = ttk.LabelFrame(top_frame, text="⚙️ 下载设置 & 控制", padding="8")
        frame5.grid(row=4, column=0, sticky=(tk.W, tk.E))
        
        row5 = ttk.Frame(frame5)
        row5.pack(fill=tk.X)
        
        left_frame = ttk.Frame(row5)
        left_frame.pack(side=tk.LEFT)
        
        ttk.Label(left_frame, text="并发线程:").pack(side=tk.LEFT, padx=(0, 8))
        self.thread_var = tk.StringVar(value="1")
        ttk.Spinbox(left_frame, from_=1, to=3, width=4, textvariable=self.thread_var).pack(side=tk.LEFT)
        ttk.Label(left_frame, text="(建议1-3)").pack(side=tk.LEFT, padx=(8, 0))
        
        btn_frame = ttk.Frame(row5)
        btn_frame.pack(side=tk.RIGHT)
        
        self.start_btn = ttk.Button(btn_frame, text="🚀 开始下载", 
                                    command=self.start_download, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        self.stop_btn = ttk.Button(btn_frame, text="⏹ 停止", 
                                   command=self.stop_download, state=tk.DISABLED, width=12)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 8))
        
        ttk.Button(btn_frame, text="🗑 清空日志", command=self.clear_log, width=12).pack(side=tk.LEFT)
        
        # ===== 6. 日志区域 =====
        frame_log = ttk.LabelFrame(bottom_frame, text="📋 下载日志 (实时进度)", padding="5")
        frame_log.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        frame_log.columnconfigure(0, weight=1)
        frame_log.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(frame_log, wrap=tk.WORD, 
                                                   font=('Consolas', 9))
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        self.log_text.tag_config("info", foreground="black")
        self.log_text.tag_config("success", foreground="green")
        self.log_text.tag_config("error", foreground="red")
        self.log_text.tag_config("warning", foreground="orange")
        self.log_text.tag_config("progress", foreground="blue")
        
        # ===== 7. 状态栏 =====
        self.status_var = tk.StringVar(value="✅ 就绪")
        status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                               relief=tk.SUNKEN, anchor=tk.W)
        status_bar.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        self.downloader = None
        self.download_thread = None
        self.last_progress_line = None
        
        self.log("🚗 辉景CAN数据批量下载工具 v1.6 已启动", "info")
        self.log(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "info")
        self.log("=" * 60, "info")
        self.log("💡 仅按文件名匹配，自动跳过已下载的文件", "info")
        self.log("💡 中断下载时自动删除未完成的临时文件", "info")
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择保存目录")
        if folder:
            self.save_entry.delete(0, tk.END)
            self.save_entry.insert(0, folder)
    
    def log(self, message, tag="info", is_progress=False):
        if is_progress:
            if self.last_progress_line is not None:
                self.log_text.delete(f"end-2l", "end-1c")
            self.log_text.insert(tk.END, message + "\n", tag)
            self.last_progress_line = True
        else:
            self.log_text.insert(tk.END, message + "\n", tag)
            self.last_progress_line = False
        
        self.log_text.see(tk.END)
        self.root.update_idletasks()
    
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.last_progress_line = None
    
    def stop_download(self):
        if self.downloader:
            self.log("⏹ 正在停止下载...", "warning")
            self.status_var.set("⏹ 正在停止...")
            self.stop_btn.config(state=tk.DISABLED)
            self.downloader.stop()
    
    def start_download(self):
        base_url = self.ip_entry.get().strip()
        username = self.user_entry.get().strip()
        password = self.pwd_entry.get().strip()
        save_dir = self.save_entry.get().strip()
        file_type = self.file_type_var.get()
        
        start_date = self.start_date.get()
        start_time = self.start_time.get()
        stop_date = self.stop_date.get()
        stop_time = self.stop_time.get()
        
        start_datetime = f"{start_date} {start_time}"
        stop_datetime = f"{stop_date} {stop_time}"
        
        try:
            max_workers = int(self.thread_var.get())
        except ValueError:
            max_workers = 2
        
        if not base_url:
            messagebox.showerror("错误", "请输入设备IP地址")
            return
        if not save_dir:
            messagebox.showerror("错误", "请选择保存目录")
            return
        if not start_date or not start_time:
            messagebox.showerror("错误", "请完整输入开始时间")
            return
        if not stop_date or not stop_time:
            messagebox.showerror("错误", "请完整输入结束时间")
            return
        
        try:
            datetime.strptime(start_datetime, "%Y-%m-%d %H:%M")
            datetime.strptime(stop_datetime, "%Y-%m-%d %H:%M")
        except ValueError as e:
            messagebox.showerror("错误", f"时间格式错误！请检查输入\n{str(e)}")
            return
        
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("🔄 下载中...")
        self.last_progress_line = None
        
        self.clear_log()
        self.log("=" * 60, "info")
        self.log(f"📅 时间范围: {start_datetime} ~ {stop_datetime}", "info")
        self.log(f"📁 保存目录: {save_dir}", "info")
        self.log(f"📄 文件类型: {file_type}", "info")
        self.log(f"🔢 并发线程: {max_workers}", "info")
        self.log("=" * 60, "info")
        self.log("💡 点击 '停止' 按钮可随时中断下载", "info")
        self.log("💡 中断后自动删除未完成的临时文件", "info")
        self.log("💡 仅按文件名匹配，已下载的文件会被跳过", "info")
        
        self.downloader = CANDownloader(
            base_url, username, password, save_dir, file_type, max_workers
        )
        
        def download_task():
            try:
                self.downloader.start_download(
                    start_datetime, stop_datetime, callback=self.log
                )
            except Exception as e:
                self.log(f"❌ 异常: {e}", "error")
            finally:
                self.root.after(0, self.finish_download)
        
        self.download_thread = threading.Thread(target=download_task, daemon=True)
        self.download_thread.start()
    
    def finish_download(self):
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("✅ 就绪")
        self.downloader = None
        self.last_progress_line = None


# ========== 启动 ==========
if __name__ == "__main__":
    root = tk.Tk()
    app = CANDownloaderGUI(root)
    root.mainloop()