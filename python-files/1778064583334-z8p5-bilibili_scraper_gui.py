"""
B站视频数据采集程序 - GUI版本
功能：可视化界面，支持暂停/继续、重试机制、自定义设置
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import pandas as pd
from bilibili_api import video
from bilibili_api.exceptions import ResponseCodeException
import re
import asyncio
import threading
import time
import os
from datetime import datetime
from pathlib import Path

class BilibiliScraperGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("B站视频数据采集工具 v2.0")
        self.root.geometry("800x700")
        self.root.resizable(True, True)
        
        # 状态变量
        self.is_running = False
        self.is_paused = False
        self.should_stop = False
        self.video_list = []
        self.current_index = 0
        self.total_videos = 0
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
        # 默认设置
        self.input_file = r'C:\Users\win11\Desktop\b站\b站.xlsx'
        self.output_dir = r'C:\Users\win11\Desktop\b站'
        self.delay = 1.0
        self.max_retries = 3
        
        self.setup_ui()
        
    def setup_ui(self):
        """设置UI界面"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # ===== 文件设置区域 =====
        file_frame = ttk.LabelFrame(main_frame, text="文件设置", padding="10")
        file_frame.pack(fill=tk.X, pady=5)
        
        # 输入文件
        ttk.Label(file_frame, text="输入Excel:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.input_entry = ttk.Entry(file_frame, width=50)
        self.input_entry.insert(0, self.input_file)
        self.input_entry.grid(row=0, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_input_file).grid(row=0, column=2, pady=5)
        
        # 输出目录
        ttk.Label(file_frame, text="保存目录:").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.output_entry = ttk.Entry(file_frame, width=50)
        self.output_entry.insert(0, self.output_dir)
        self.output_entry.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(file_frame, text="浏览...", command=self.browse_output_dir).grid(row=1, column=2, pady=5)
        
        # ===== 采集设置区域 =====
        settings_frame = ttk.LabelFrame(main_frame, text="采集设置", padding="10")
        settings_frame.pack(fill=tk.X, pady=5)
        
        # 请求延时
        ttk.Label(settings_frame, text="请求延时(秒):").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.delay_var = tk.StringVar(value="2.0")
        ttk.Entry(settings_frame, textvariable=self.delay_var, width=15).grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        # 最大重试次数
        ttk.Label(settings_frame, text="最大重试次数:").grid(row=0, column=2, sticky=tk.W, pady=5, padx=(20,0))
        self.retry_var = tk.StringVar(value="3")
        ttk.Entry(settings_frame, textvariable=self.retry_var, width=15).grid(row=0, column=3, sticky=tk.W, padx=5, pady=5)
        
        # 并发数
        ttk.Label(settings_frame, text="并发数:").grid(row=0, column=4, sticky=tk.W, pady=5, padx=(20,0))
        self.concurrency_var = tk.StringVar(value="1")
        ttk.Entry(settings_frame, textvariable=self.concurrency_var, width=15).grid(row=0, column=5, sticky=tk.W, padx=5, pady=5)
        
        # 采集范围设置
        range_frame = ttk.Frame(settings_frame)
        range_frame.grid(row=1, column=0, columnspan=6, sticky=tk.W, pady=5)
        
        ttk.Label(range_frame, text="采集范围:").pack(side=tk.LEFT)
        self.start_pos_var = tk.StringVar(value="1")
        ttk.Entry(range_frame, textvariable=self.start_pos_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(range_frame, text=" 到 ").pack(side=tk.LEFT)
        self.end_pos_var = tk.StringVar(value="全部")
        ttk.Entry(range_frame, textvariable=self.end_pos_var, width=8).pack(side=tk.LEFT, padx=5)
        ttk.Label(range_frame, text="(填\"全部\"表示到结尾)").pack(side=tk.LEFT, padx=5)
        
        # ===== 控制按钮区域 =====
        control_frame = ttk.Frame(main_frame)
        control_frame.pack(fill=tk.X, pady=10)
        
        self.start_btn = ttk.Button(control_frame, text="▶ 开始", command=self.start_scraping, width=12)
        self.start_btn.pack(side=tk.LEFT, padx=5)
        
        self.pause_btn = ttk.Button(control_frame, text="⏸ 暂停", command=self.toggle_pause, width=12, state=tk.DISABLED)
        self.pause_btn.pack(side=tk.LEFT, padx=5)
        
        self.stop_btn = ttk.Button(control_frame, text="⏹ 停止", command=self.stop_scraping, width=12, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=5)
        
        self.export_btn = ttk.Button(control_frame, text="💾 导出数据", command=self.export_data, width=12, state=tk.DISABLED)
        self.export_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== 进度显示区域 =====
        progress_frame = ttk.LabelFrame(main_frame, text="采集进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=5)
        
        self.progress_var = tk.StringVar(value="就绪")
        ttk.Label(progress_frame, textvariable=self.progress_var, font=('微软雅黑', 10)).pack(anchor=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate', length=500)
        self.progress_bar.pack(fill=tk.X, pady=5)
        
        # 统计信息
        self.stats_label = ttk.Label(progress_frame, text="总任务: 0 | 成功: 0 | 失败: 0 | 跳过: 0")
        self.stats_label.pack(anchor=tk.W)
        
        # ===== 日志区域 =====
        log_frame = ttk.LabelFrame(main_frame, text="运行日志", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=15, width=100, font=('Consolas', 9))
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        # 状态栏
        self.status_var = tk.StringVar(value="就绪")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
    def log(self, message):
        """添加日志"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def browse_input_file(self):
        """选择输入文件"""
        filename = filedialog.askopenfilename(
            title="选择Excel文件",
            filetypes=[("Excel文件", "*.xlsx *.xls"), ("所有文件", "*.*")]
        )
        if filename:
            self.input_file = filename
            self.input_entry.delete(0, tk.END)
            self.input_entry.insert(0, filename)
            self.log(f"已选择输入文件: {filename}")
            
    def browse_output_dir(self):
        """选择输出目录"""
        directory = filedialog.askdirectory(title="选择保存目录")
        if directory:
            self.output_dir = directory
            self.output_entry.delete(0, tk.END)
            self.output_entry.insert(0, directory)
            self.log(f"已选择输出目录: {directory}")
            
    def validate_settings(self):
        """验证设置"""
        try:
            self.delay = float(self.delay_var.get())
            self.max_retries = int(self.retry_var.get())
            self.concurrency = int(self.concurrency_var.get())
        except ValueError:
            messagebox.showerror("错误", "请输入有效的数字！")
            return False
        return True
        
    def toggle_pause(self):
        """暂停/继续切换"""
        if self.is_paused:
            self.is_paused = False
            self.pause_btn.config(text="⏸ 暂停")
            self.log("已继续采集...")
        else:
            self.is_paused = True
            self.pause_btn.config(text="▶ 继续")
            self.log("已暂停采集...")
            
    def start_scraping(self):
        """开始采集"""
        if not self.validate_settings():
            return
            
        # 读取设置
        self.input_file = self.input_entry.get()
        self.output_dir = self.output_entry.get()
        
        if not os.path.exists(self.input_file):
            messagebox.showerror("错误", "输入文件不存在！")
            return
            
        # 重置状态
        self.is_running = True
        self.is_paused = False
        self.should_stop = False
        self.video_list = []
        self.current_index = 0
        
        # 更新按钮状态
        self.start_btn.config(state=tk.DISABLED)
        self.pause_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.NORMAL)
        self.export_btn.config(state=tk.DISABLED)
        
        self.log("=" * 50)
        self.log("开始采集视频数据...")
        
        # 在新线程中运行采集
        self.scraper_thread = threading.Thread(target=self.run_scraper, daemon=True)
        self.scraper_thread.start()
        
    def run_scraper(self):
        """运行采集任务"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(self.scraping_task())
        except Exception as e:
            self.log(f"采集出错: {str(e)}")
        finally:
            loop.close()
        self.root.after(0, self.on_scraping_complete)
        
    async def scraping_task(self):
        """异步采集任务"""
        # 读取Excel文件
        self.root.after(0, lambda: self.log(f"读取文件: {self.input_file}"))
        
        try:
            df_input = pd.read_excel(self.input_file)
            urls = df_input.iloc[:, 0].dropna().tolist()
            self.root.after(0, lambda: self.log(f"共找到 {len(urls)} 个视频链接"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("错误", f"读取Excel失败: {str(e)}"))
            return
        
        # 提取BV号
        bvids = []
        for url in urls:
            bvid = self.extract_bvid(str(url))
            if bvid:
                bvids.append(bvid)
        
        # 处理采集范围
        try:
            start_pos = int(self.start_pos_var.get()) - 1  # 转为0索引
            end_pos_str = self.end_pos_var.get().strip()
            if end_pos_str.lower() == '全部':
                end_pos = len(bvids)
            else:
                end_pos = int(end_pos_str)
        except ValueError:
            start_pos = 0
            end_pos = len(bvids)
        
        # 限制范围
        start_pos = max(0, start_pos)
        end_pos = min(len(bvids), end_pos)
        bvids = bvids[start_pos:end_pos]
        
        self.root.after(0, lambda: self.log(f"范围设置: 第{start_pos+1}个 到 第{end_pos}个，共{len(bvids)}个视频"))
        
        # 初始化CSV文件（实时保存）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        self.csv_file = os.path.join(self.output_dir, f'视频数据_{timestamp}.csv')
        csv_columns = [
            'BV号', 'AV号', '标题', '作者', '作者UID',
            '发布时间', '发布时间格式化',
            '视频数量', '时长(秒)', '时长格式化', '标签',
            '播放量', '点赞数', '点赞率(%)',
            '投币数', '收藏数', '分享数', '弹幕数', '评论数',
            '视频状态', '链接'
        ]
        with open(self.csv_file, 'w', newline='', encoding='utf-8-sig') as f:
            f.write(','.join(csv_columns) + '\n')
        self.root.after(0, lambda: self.log(f"CSV已创建: {self.csv_file}"))
        
        total = len(bvids)
        self.total_videos = total
        self.success_count = 0
        self.fail_count = 0
        self.skip_count = 0
        
        self.root.after(0, lambda: self.progress_bar.config(maximum=total))
        
        for i, bvid in enumerate(bvids):
            if self.should_stop:
                self.root.after(0, lambda: self.log("用户停止了采集"))
                break
                
            # 等待直到暂停解除
            while self.is_paused and not self.should_stop:
                await asyncio.sleep(0.1)
                
            if self.should_stop:
                break
                
            self.current_index = i
            self.root.after(0, lambda idx=i, bv=bvid: self.progress_var.set(f"正在采集 [{idx+1}/{total}]: {bv}"))
            
            # 获取数据（带重试）
            stats = await self.get_video_with_retry(bvid)
            
            if stats:
                self.video_list.append(stats)
                self.success_count += 1
                # 实时保存到CSV
                row = [str(stats.get(col, '')) for col in csv_columns]
                with open(self.csv_file, 'a', encoding='utf-8-sig') as f:
                    f.write(','.join(row) + '\n')
                title = stats['标题'][:20] if stats['标题'] else '无标题'
                views = f"{stats['播放量']:,}"
                self.root.after(0, lambda t=title, v=views: self.log(f"✓ 成功: {t}... (播放:{v})"))
            elif stats is None:
                self.skip_count += 1
                self.root.after(0, lambda bv=bvid: self.log(f"⊘ 跳过: {bv}"))
            else:
                self.fail_count += 1
                self.root.after(0, lambda bv=bvid: self.log(f"✗ 失败: {bv}"))
                
            # 更新进度条
            self.root.after(0, lambda idx=i: self.progress_bar.config(value=idx + 1))
            self.root.after(0, lambda: self.stats_label.config(
                text=f"总任务: {total} | 成功: {self.success_count} | 失败: {self.fail_count} | 跳过: {self.skip_count}"))
            
            # 延时
            if i < total - 1 and not self.should_stop:
                await asyncio.sleep(self.delay)
        
    async def get_video_with_retry(self, bvid):
        """带重试机制的获取视频数据"""
        for attempt in range(self.max_retries):
            try:
                return await self.get_video_details(bvid)
            except ResponseCodeException as e:
                if attempt < self.max_retries - 1:
                    self.root.after(0, lambda a=attempt+1, e=e: self.log(f"  重试 ({a}/{self.max_retries}): {e.msg}"))
                    await asyncio.sleep(2)
                else:
                    return None
            except Exception as e:
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(1)
                else:
                    return None
        return None
        
    def extract_bvid(self, url):
        """从URL中提取BV号"""
        match = re.search(r'BV[a-zA-Z0-9]+', url)
        return match.group(0) if match else None
        
    async def get_video_details(self, bvid):
        """获取视频详细信息"""
        v = video.Video(bvid=bvid)
        
        info = await v.get_info()
        stat = info.get('stat', {})
        
        # 获取标签
        try:
            tags = await v.get_tags()
            tag_names = '|'.join([t['tag_name'] for t in tags]) if tags else ''
        except:
            tag_names = ''
            
        # 获取分P信息
        try:
            pages = await v.get_pages()
            page_info = f"共{len(pages)}P" if pages else "单P"
        except:
            page_info = "单P"
            
        # 获取关联视频
        try:
            related = await v.get_related()
            related_count = len(related) if related else 0
        except:
            related_count = 0
            
        # 计算点赞率
        view_count = stat.get('view', 0)
        like_count = stat.get('like', 0)
        like_rate = round(like_count / view_count * 100, 2) if view_count > 0 else 0
        
        # 时长格式化
        duration = info.get('duration', 0)
        duration_str = self.format_duration(duration)
        
        # 分区信息
        tname = info.get('tname', '')
        
        # 权限信息
        rights = info.get('rights', {})
        no_reprint = '禁止转载' if rights.get('no_reprint', 0) == 1 else '可转载'
        is_original = '原创' if info.get('copyright', 0) == 1 else '转载'
        
        # 字幕信息
        subtitle = info.get('subtitle', {})
        subtitle_info = subtitle.get('subtitles', [])
        has_subtitle = '有' if subtitle_info else '无'
        subtitle_langs = '|'.join([s.get('lan_doc', '') for s in subtitle_info]) if subtitle_info else ''
        
        # 获取UP主信息
        owner = info.get('owner', {})

        # 视频状态
        state = info.get('state', 0)
        state_text = self.get_state_text(state)

        return {
            'BV号': bvid,
            'AV号': info.get('aid', ''),
            '标题': info.get('title', ''),
            '作者': owner.get('name', ''),
            '作者UID': owner.get('mid', ''),
            '发布时间': info.get('pubdate', ''),
            '发布时间格式化': datetime.fromtimestamp(info.get('pubdate', 0)).strftime('%Y/%m/%d %H:%M:%S') if info.get('pubdate', 0) else '',
            '视频数量': info.get('videos', 1),
            '时长(秒)': duration,
            '时长格式化': duration_str,
            '标签': tag_names,
            '播放量': view_count,
            '点赞数': like_count,
            '点赞率(%)': like_rate,
            '投币数': stat.get('coin', 0),
            '收藏数': stat.get('favorite', 0),
            '分享数': stat.get('share', 0),
            '弹幕数': stat.get('danmaku', 0),
            '评论数': stat.get('reply', 0),
            '视频状态': state_text,
            '链接': f'https://www.bilibili.com/video/{bvid}'
        }
        
    def format_duration(self, seconds):
        """格式化时长"""
        if seconds:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            if hours > 0:
                return f"{hours}:{minutes:02d}:{secs:02d}"
            return f"{minutes}:{secs:02d}"
        return ''
        
    def get_state_text(self, state):
        """视频状态说明"""
        state_map = {
            0: '正常', 1: '失效', -1: '审核中', -2: '已删除',
            -3: '私有', -4: '前置取消', -5: '会员提前看', -6: '付费'
        }
        return state_map.get(state, str(state))
        
    def on_scraping_complete(self):
        """采集完成回调"""
        self.is_running = False
        self.start_btn.config(state=tk.NORMAL)
        self.pause_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.DISABLED)
        self.export_btn.config(state=tk.NORMAL if self.video_list else tk.DISABLED)
        
        self.log("=" * 50)
        self.log(f"采集完成！成功: {self.success_count} | 失败: {self.fail_count} | 跳过: {self.skip_count}")
        self.progress_var.set("采集完成")
        self.status_var.set(f"就绪 - 最后采集: {self.success_count}/{getattr(self, 'total_videos', 0)}")
        
    def stop_scraping(self):
        """停止采集"""
        self.should_stop = True
        self.is_paused = False
        self.log("正在停止采集...")
        
    def export_data(self):
        """导出数据 - 将实时保存的CSV转为XLSX"""
        if not self.video_list and not hasattr(self, 'csv_file'):
            messagebox.showwarning("警告", "没有可导出的数据！")
            return
        
        # CSV转XLSX
        csv_file = getattr(self, 'csv_file', None)
        if csv_file and os.path.exists(csv_file):
            xlsx_file = csv_file.replace('.csv', '.xlsx')
            df = pd.read_csv(csv_file, dtype=str).fillna('')
            df.to_excel(xlsx_file, index=False, engine='openpyxl')
            self.log(f"已保存XLSX: {xlsx_file}")
            messagebox.showinfo("完成", f"数据已导出！\n\n位置: {xlsx_file}")
        else:
            messagebox.showwarning("警告", "CSV文件不存在！")

def main():
    root = tk.Tk()
    app = BilibiliScraperGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
