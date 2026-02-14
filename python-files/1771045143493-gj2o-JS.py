#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON/SRT 转 TXT/SRT 字幕转换器 - 独立GUI版本
支持 JSON 转 SRT/TXT，以及 SRT 转 TXT（纯文本）
"""

import json
import os
import re
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter import scrolledtext
import sys

class JSONToSRTConverter:
    def __init__(self):
        self.srt_template = "{index}\n{start_time} --> {end_time}\n{text}\n\n"
    
    # ========== JSON 相关方法（原有）==========
    def microseconds_to_srt_time(self, microseconds):
        seconds = microseconds / 1000000
        td = timedelta(seconds=seconds)
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        milliseconds = td.microseconds // 1000
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def extract_text_from_content(self, content_json):
        try:
            content_data = json.loads(content_json)
            return content_data.get("text", "")
        except:
            match = re.search(r'"text":"([^"]+)"', content_json)
            if match:
                return match.group(1)
            return ""
    
    def extract_subtitles(self, data):
        subtitles = []
        if 'materials' in data and 'texts' in data['materials']:
            texts = data['materials']['texts']
            if 'tracks' in data:
                for track in data['tracks']:
                    if track.get('type') == 'text' and 'segments' in track:
                        for segment in track['segments']:
                            if 'material_id' in segment and 'target_timerange' in segment:
                                material_id = segment['material_id']
                                for text_item in texts:
                                    if text_item.get('id') == material_id:
                                        text_content = ""
                                        if 'content' in text_item:
                                            text_content = self.extract_text_from_content(text_item['content'])
                                        elif 'words' in text_item and 'text' in text_item['words']:
                                            text_content = "".join(text_item['words']['text'])
                                        timerange = segment['target_timerange']
                                        start_time = timerange.get('start', 0)
                                        duration = timerange.get('duration', 0)
                                        end_time = start_time + duration
                                        subtitles.append({
                                            'start': start_time,
                                            'end': end_time,
                                            'text': text_content
                                        })
                                        break
            if not subtitles:
                for text_item in texts:
                    if 'words' in text_item and 'text' in text_item['words'] and 'start_time' in text_item['words']:
                        words = text_item['words']['text']
                        start_times = text_item['words']['start_time']
                        end_times = text_item['words']['end_time']
                        if words and start_times and end_times:
                            start_time = start_times[0]
                            end_time = end_times[-1]
                            text_content = "".join(words)
                            subtitles.append({
                                'start': start_time,
                                'end': end_time,
                                'text': text_content
                            })
        subtitles.sort(key=lambda x: x['start'])
        return subtitles
    
    def process_json_file(self, json_path, output_path=None):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if output_path is None:
                output_path = os.path.splitext(json_path)[0] + '.srt'
            subtitles = self.extract_subtitles(data)
            srt_content = ""
            for i, subtitle in enumerate(subtitles, 1):
                start_srt = self.microseconds_to_srt_time(subtitle['start'])
                end_srt = self.microseconds_to_srt_time(subtitle['end'])
                srt_content += self.srt_template.format(
                    index=i,
                    start_time=start_srt,
                    end_time=end_srt,
                    text=subtitle['text']
                )
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(srt_content)
            return True, f"成功转换SRT！共转换了 {len(subtitles)} 条字幕\n保存到: {output_path}"
        except Exception as e:
            return False, f"转换过程中出现错误: {str(e)}"
    
    def json_to_txt(self, json_path, output_path=None):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if output_path is None:
                output_path = os.path.splitext(json_path)[0] + '.txt'
            subtitles = self.extract_subtitles(data)
            text_lines = [sub['text'] for sub in subtitles if sub['text'].strip()]
            txt_content = "\n".join(text_lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            return True, f"成功转换TXT！共提取了 {len(text_lines)} 条字幕文本\n保存到: {output_path}"
        except Exception as e:
            return False, f"转换过程中出现错误: {str(e)}"
    
    def batch_convert_json(self, folder_path, target_format='srt'):
        if not os.path.isdir(folder_path):
            return False, f"错误：{folder_path} 不是有效的文件夹"
        json_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.json')]
        if not json_files:
            return False, f"在 {folder_path} 中没有找到JSON文件"
        success_count = 0
        results = []
        for json_file in json_files:
            json_path = os.path.join(folder_path, json_file)
            if target_format == 'srt':
                output_path = os.path.splitext(json_path)[0] + '.srt'
                success, message = self.process_json_file(json_path, output_path)
            else:  # txt
                output_path = os.path.splitext(json_path)[0] + '.txt'
                success, message = self.json_to_txt(json_path, output_path)
            if success:
                success_count += 1
                results.append(f"✓ {json_file} - 转换成功")
            else:
                results.append(f"✗ {json_file} - 转换失败")
        summary = f"\n批量转换完成！成功转换 {success_count}/{len(json_files)} 个文件\n"
        return True, summary + "\n".join(results)
    
    # ========== 新增 SRT 转 TXT 方法 ==========
    def extract_text_from_srt(self, srt_content):
        """解析 SRT 内容，返回每一条字幕的文本列表（段落内换行合并为空格）"""
        lines = srt_content.splitlines()
        subtitles = []
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if not line:
                i += 1
                continue
            # 检查是否为数字序号（且下一行包含时间轴标记）
            if line.isdigit() and i + 1 < len(lines) and '-->' in lines[i+1]:
                i += 2  # 跳过序号和时间轴
                text_lines = []
                while i < len(lines):
                    current = lines[i].strip()
                    if not current or (current.isdigit() and i+1 < len(lines) and '-->' in lines[i+1]):
                        break
                    text_lines.append(current)
                    i += 1
                if text_lines:
                    subtitles.append(' '.join(text_lines))  # 合并多行为一个段落
            else:
                i += 1
        return subtitles

    def srt_to_txt(self, srt_path, output_path=None):
        """将单个 SRT 文件转换为 TXT 纯文本"""
        try:
            with open(srt_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if output_path is None:
                output_path = os.path.splitext(srt_path)[0] + '.txt'
            text_lines = self.extract_text_from_srt(content)
            txt_content = "\n".join(text_lines)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(txt_content)
            return True, f"成功转换TXT！共提取了 {len(text_lines)} 条字幕\n保存到: {output_path}"
        except Exception as e:
            return False, f"转换过程中出现错误: {str(e)}"

    def batch_convert_srt_to_txt(self, folder_path):
        """批量将文件夹内所有 .srt 文件转换为 .txt"""
        if not os.path.isdir(folder_path):
            return False, f"错误：{folder_path} 不是有效的文件夹"
        srt_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.srt')]
        if not srt_files:
            return False, f"在 {folder_path} 中没有找到SRT文件"
        success_count = 0
        results = []
        for srt_file in srt_files:
            srt_path = os.path.join(folder_path, srt_file)
            output_path = os.path.splitext(srt_path)[0] + '.txt'
            success, message = self.srt_to_txt(srt_path, output_path)
            if success:
                success_count += 1
                results.append(f"✓ {srt_file} -> {os.path.basename(output_path)}")
            else:
                results.append(f"✗ {srt_file} - 转换失败")
        summary = f"\n批量转换完成！成功转换 {success_count}/{len(srt_files)} 个文件\n"
        return True, summary + "\n".join(results)


class JSONToSRTGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON/SRT 转 TXT/SRT 字幕转换器 v2.0")
        self.root.geometry("700x750")
        
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        self.converter = JSONToSRTConverter()
        self.setup_ui()
    
    def setup_ui(self):
        bg_color = "#f0f0f0"
        button_color = "#4CAF50"
        button_hover = "#45a049"
        
        self.root.configure(bg=bg_color)
        
        # 标题
        title_frame = tk.Frame(self.root, bg=bg_color)
        title_frame.pack(pady=20)
        tk.Label(title_frame, text="JSON/SRT 转 TXT/SRT 字幕转换器", 
                font=("微软雅黑", 18, "bold"), bg=bg_color).pack()
        tk.Label(title_frame, text="支持剪映等软件的 JSON 字幕以及标准 SRT 文件 | 可输出 SRT 或纯文本 TXT", 
                font=("微软雅黑", 10), fg="gray", bg=bg_color).pack()
        
        # ========== JSON 转换区域（原有）==========
        frame_json = tk.LabelFrame(self.root, text="JSON 转 SRT / TXT", font=("微软雅黑", 11),
                                   bg=bg_color, padx=15, pady=15)
        frame_json.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(frame_json, text="选择JSON文件:", bg=bg_color, font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.json_path_var = tk.StringVar()
        json_entry = tk.Entry(frame_json, textvariable=self.json_path_var, width=50, font=("微软雅黑", 9))
        json_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(frame_json, text="浏览...", command=self.browse_json,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white", relief=tk.RAISED).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(frame_json, text="输出文件:", bg=bg_color, font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.json_output_var = tk.StringVar()
        json_output_entry = tk.Entry(frame_json, textvariable=self.json_output_var, width=50, font=("微软雅黑", 9))
        json_output_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(frame_json, text="浏览...", command=self.browse_json_output,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white", relief=tk.RAISED).grid(row=1, column=3, padx=5, pady=5)
        
        btn_frame_json = tk.Frame(frame_json, bg=bg_color)
        btn_frame_json.grid(row=2, column=0, columnspan=4, pady=15)
        tk.Button(btn_frame_json, text="转 SRT", command=self.convert_json_to_srt,
                 font=("微软雅黑", 11, "bold"), bg=button_color, fg="white",
                 padx=20, pady=5, relief=tk.RAISED).pack(side=tk.LEFT, padx=10)
        tk.Button(btn_frame_json, text="转 TXT", command=self.convert_json_to_txt,
                 font=("微软雅黑", 11, "bold"), bg="#FF9800", fg="white",
                 padx=20, pady=5, relief=tk.RAISED).pack(side=tk.LEFT, padx=10)
        
        # ========== 新增 SRT 转 TXT 区域 ==========
        frame_srt = tk.LabelFrame(self.root, text="SRT 转 TXT 纯文本", font=("微软雅黑", 11),
                                  bg=bg_color, padx=15, pady=15)
        frame_srt.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(frame_srt, text="选择SRT文件:", bg=bg_color, font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.srt_path_var = tk.StringVar()
        srt_entry = tk.Entry(frame_srt, textvariable=self.srt_path_var, width=50, font=("微软雅黑", 9))
        srt_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(frame_srt, text="浏览...", command=self.browse_srt,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white", relief=tk.RAISED).grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(frame_srt, text="输出TXT文件:", bg=bg_color, font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        self.srt_output_var = tk.StringVar()
        srt_output_entry = tk.Entry(frame_srt, textvariable=self.srt_output_var, width=50, font=("微软雅黑", 9))
        srt_output_entry.grid(row=1, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(frame_srt, text="浏览...", command=self.browse_srt_output,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white", relief=tk.RAISED).grid(row=1, column=3, padx=5, pady=5)
        
        btn_frame_srt = tk.Frame(frame_srt, bg=bg_color)
        btn_frame_srt.grid(row=2, column=0, columnspan=4, pady=10)
        tk.Button(btn_frame_srt, text="转换为 TXT", command=self.convert_srt_to_txt,
                 font=("微软雅黑", 11, "bold"), bg="#FF9800", fg="white",
                 padx=20, pady=5, relief=tk.RAISED).pack()
        
        # ========== 批量转换区域 ==========
        frame_batch = tk.LabelFrame(self.root, text="批量转换", font=("微软雅黑", 11),
                                    bg=bg_color, padx=15, pady=15)
        frame_batch.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(frame_batch, text="选择文件夹:", bg=bg_color, font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        self.batch_folder_var = tk.StringVar()
        batch_entry = tk.Entry(frame_batch, textvariable=self.batch_folder_var, width=50, font=("微软雅黑", 9))
        batch_entry.grid(row=0, column=1, padx=5, pady=5, columnspan=2)
        tk.Button(frame_batch, text="浏览...", command=self.browse_batch_folder,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white", relief=tk.RAISED).grid(row=0, column=3, padx=5, pady=5)
        
        batch_btn_frame = tk.Frame(frame_batch, bg=bg_color)
        batch_btn_frame.grid(row=1, column=0, columnspan=4, pady=10)
        tk.Button(batch_btn_frame, text="批量 JSON 转 SRT", command=self.batch_json_to_srt,
                 font=("微软雅黑", 9, "bold"), bg="#4CAF50", fg="white",
                 padx=10, pady=3, relief=tk.RAISED).pack(side=tk.LEFT, padx=5)
        tk.Button(batch_btn_frame, text="批量 JSON 转 TXT", command=self.batch_json_to_txt,
                 font=("微软雅黑", 9, "bold"), bg="#FF9800", fg="white",
                 padx=10, pady=3, relief=tk.RAISED).pack(side=tk.LEFT, padx=5)
        tk.Button(batch_btn_frame, text="批量 SRT 转 TXT", command=self.batch_srt_to_txt,
                 font=("微软雅黑", 9, "bold"), bg="#FF5722", fg="white",
                 padx=10, pady=3, relief=tk.RAISED).pack(side=tk.LEFT, padx=5)
        
        # 状态显示区域
        status_frame = tk.Frame(self.root, bg=bg_color)
        status_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        tk.Label(status_frame, text="转换状态:", bg=bg_color, font=("微软雅黑", 10, "bold")).pack(anchor=tk.W)
        self.status_text = scrolledtext.ScrolledText(status_frame, height=8,
                                                    font=("Consolas", 9), wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 底部信息
        bottom_frame = tk.Frame(self.root, bg=bg_color)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        tk.Label(bottom_frame, text="© 2025 JSON/SRT 转换器 | 支持剪映、PR 等软件字幕导出",
                font=("微软雅黑", 8), fg="gray", bg=bg_color).pack()
    
    # ---------- 文件浏览回调 ----------
    def browse_json(self):
        filename = filedialog.askopenfilename(title="选择JSON文件", filetypes=[("JSON文件", "*.json")])
        if filename:
            self.json_path_var.set(filename)
            self.json_output_var.set(os.path.splitext(filename)[0] + '.srt')
    
    def browse_json_output(self):
        filename = filedialog.asksaveasfilename(title="保存文件", defaultextension=".srt",
                                                filetypes=[("SRT字幕", "*.srt"), ("文本文件", "*.txt")])
        if filename:
            self.json_output_var.set(filename)
    
    def browse_srt(self):
        filename = filedialog.askopenfilename(title="选择SRT文件", filetypes=[("SRT文件", "*.srt")])
        if filename:
            self.srt_path_var.set(filename)
            self.srt_output_var.set(os.path.splitext(filename)[0] + '.txt')
    
    def browse_srt_output(self):
        filename = filedialog.asksaveasfilename(title="保存TXT文件", defaultextension=".txt",
                                                filetypes=[("文本文件", "*.txt")])
        if filename:
            self.srt_output_var.set(filename)
    
    def browse_batch_folder(self):
        folder = filedialog.askdirectory(title="选择文件夹")
        if folder:
            self.batch_folder_var.set(folder)
    
    # ---------- 日志 ----------
    def log_message(self, message):
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        self.status_text.delete(1.0, tk.END)
    
    # ---------- 转换操作 ----------
    def convert_json_to_srt(self):
        json_path = self.json_path_var.get().strip()
        output_path = self.json_output_var.get().strip() or None
        if not json_path:
            messagebox.showwarning("警告", "请选择JSON文件")
            return
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始转换SRT: {os.path.basename(json_path)}")
        self.log_message("=" * 50)
        success, message = self.converter.process_json_file(json_path, output_path)
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "SRT字幕转换完成！")
        else:
            messagebox.showerror("错误", message)
    
    def convert_json_to_txt(self):
        json_path = self.json_path_var.get().strip()
        output_path = self.json_output_var.get().strip() or None
        if not json_path:
            messagebox.showwarning("警告", "请选择JSON文件")
            return
        if not output_path:
            output_path = os.path.splitext(json_path)[0] + '.txt'
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始转换TXT: {os.path.basename(json_path)}")
        self.log_message("=" * 50)
        success, message = self.converter.json_to_txt(json_path, output_path)
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "纯文本转换完成！")
        else:
            messagebox.showerror("错误", message)
    
    def convert_srt_to_txt(self):
        srt_path = self.srt_path_var.get().strip()
        output_path = self.srt_output_var.get().strip() or None
        if not srt_path:
            messagebox.showwarning("警告", "请选择SRT文件")
            return
        if not output_path:
            output_path = os.path.splitext(srt_path)[0] + '.txt'
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始转换TXT: {os.path.basename(srt_path)}")
        self.log_message("=" * 50)
        success, message = self.converter.srt_to_txt(srt_path, output_path)
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "纯文本转换完成！")
        else:
            messagebox.showerror("错误", message)
    
    def batch_json_to_srt(self):
        folder = self.batch_folder_var.get().strip()
        if not folder:
            messagebox.showwarning("警告", "请选择文件夹")
            return
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始批量转换JSON -> SRT: {folder}")
        self.log_message("=" * 50)
        success, message = self.converter.batch_convert_json(folder, target_format='srt')
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "批量转换SRT完成！")
        else:
            messagebox.showerror("错误", message)
    
    def batch_json_to_txt(self):
        folder = self.batch_folder_var.get().strip()
        if not folder:
            messagebox.showwarning("警告", "请选择文件夹")
            return
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始批量转换JSON -> TXT: {folder}")
        self.log_message("=" * 50)
        success, message = self.converter.batch_convert_json(folder, target_format='txt')
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "批量转换TXT完成！")
        else:
            messagebox.showerror("错误", message)
    
    def batch_srt_to_txt(self):
        folder = self.batch_folder_var.get().strip()
        if not folder:
            messagebox.showwarning("警告", "请选择文件夹")
            return
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始批量转换SRT -> TXT: {folder}")
        self.log_message("=" * 50)
        success, message = self.converter.batch_convert_srt_to_txt(folder)
        self.log_message("\n" + ("✅ " if success else "❌ ") + message)
        if success:
            messagebox.showinfo("成功", "批量转换TXT完成！")
        else:
            messagebox.showerror("错误", message)


def main():
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    root = tk.Tk()
    app = JSONToSRTGUI(root)
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    root.mainloop()

if __name__ == "__main__":
    main()