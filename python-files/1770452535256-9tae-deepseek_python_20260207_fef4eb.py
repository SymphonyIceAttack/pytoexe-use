#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
JSON转SRT字幕转换器 - 独立GUI版本
"""

import json
import os
import re
from datetime import timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import sys

class JSONToSRTConverter:
    def __init__(self):
        self.srt_template = "{index}\n{start_time} --> {end_time}\n{text}\n\n"
    
    def microseconds_to_srt_time(self, microseconds):
        """将微秒转换为SRT时间格式 (HH:MM:SS,mmm)"""
        seconds = microseconds / 1000000
        td = timedelta(seconds=seconds)
        
        hours = td.seconds // 3600
        minutes = (td.seconds % 3600) // 60
        seconds = td.seconds % 60
        milliseconds = td.microseconds // 1000
        
        return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"
    
    def extract_text_from_content(self, content_json):
        """从content字段提取纯文本"""
        try:
            content_data = json.loads(content_json)
            return content_data.get("text", "")
        except:
            match = re.search(r'"text":"([^"]+)"', content_json)
            if match:
                return match.group(1)
            return ""
    
    def process_json_file(self, json_path, output_path=None):
        """处理JSON文件并生成SRT"""
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if output_path is None:
                output_path = os.path.splitext(json_path)[0] + '.srt'
            
            subtitles = []
            
            # 提取字幕信息
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
            
            return True, f"成功转换！共转换了 {len(subtitles)} 条字幕\n保存到: {output_path}"
            
        except FileNotFoundError:
            return False, f"错误：找不到文件 {json_path}"
        except json.JSONDecodeError:
            return False, f"错误：{json_path} 不是有效的JSON文件"
        except Exception as e:
            return False, f"转换过程中出现错误: {str(e)}"
    
    def batch_convert(self, folder_path):
        """批量转换文件夹中的所有JSON文件"""
        if not os.path.isdir(folder_path):
            return False, f"错误：{folder_path} 不是有效的文件夹"
        
        json_files = [f for f in os.listdir(folder_path) if f.lower().endswith('.json')]
        
        if not json_files:
            return False, f"在 {folder_path} 中没有找到JSON文件"
        
        success_count = 0
        results = []
        for json_file in json_files:
            json_path = os.path.join(folder_path, json_file)
            output_path = os.path.splitext(json_path)[0] + '.srt'
            
            success, message = self.process_json_file(json_path, output_path)
            if success:
                success_count += 1
                results.append(f"✓ {json_file} - 转换成功")
            else:
                results.append(f"✗ {json_file} - 转换失败")
        
        summary = f"\n批量转换完成！成功转换 {success_count}/{len(json_files)} 个文件\n"
        return True, summary + "\n".join(results)


class JSONToSRTGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JSON 转 SRT 字幕转换器 v1.0")
        self.root.geometry("600x500")
        
        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap('icon.ico')
        except:
            pass
        
        self.converter = JSONToSRTConverter()
        
        self.setup_ui()
    
    def setup_ui(self):
        # 设置主题颜色
        bg_color = "#f0f0f0"
        button_color = "#4CAF50"
        button_hover = "#45a049"
        
        self.root.configure(bg=bg_color)
        
        # 标题
        title_frame = tk.Frame(self.root, bg=bg_color)
        title_frame.pack(pady=20)
        
        tk.Label(title_frame, text="JSON 转 SRT 字幕转换器", 
                font=("微软雅黑", 18, "bold"), bg=bg_color).pack()
        tk.Label(title_frame, text="支持剪映等视频编辑软件的字幕JSON格式", 
                font=("微软雅黑", 10), fg="gray", bg=bg_color).pack()
        
        # 单文件转换区域
        frame1 = tk.LabelFrame(self.root, text="单文件转换", font=("微软雅黑", 11),
                              bg=bg_color, padx=15, pady=15)
        frame1.pack(pady=10, padx=20, fill=tk.X)
        
        # JSON文件选择
        tk.Label(frame1, text="选择JSON文件:", bg=bg_color, 
                font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.json_path_var = tk.StringVar()
        json_entry = tk.Entry(frame1, textvariable=self.json_path_var, 
                             width=50, font=("微软雅黑", 9))
        json_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame1, text="浏览...", command=self.browse_json,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white",
                 relief=tk.RAISED).grid(row=0, column=2, padx=5, pady=5)
        
        # 输出文件选择
        tk.Label(frame1, text="输出SRT文件:", bg=bg_color,
                font=("微软雅黑", 10)).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.output_path_var = tk.StringVar()
        output_entry = tk.Entry(frame1, textvariable=self.output_path_var,
                               width=50, font=("微软雅黑", 9))
        output_entry.grid(row=1, column=1, padx=5, pady=5)
        
        tk.Button(frame1, text="浏览...", command=self.browse_output,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white",
                 relief=tk.RAISED).grid(row=1, column=2, padx=5, pady=5)
        
        # 单文件转换按钮
        convert_btn = tk.Button(frame1, text="开始转换", command=self.convert_single,
                               font=("微软雅黑", 11, "bold"), bg=button_color, fg="white",
                               padx=20, pady=5, relief=tk.RAISED)
        convert_btn.grid(row=2, column=0, columnspan=3, pady=15)
        
        # 批量转换区域
        frame2 = tk.LabelFrame(self.root, text="批量转换", font=("微软雅黑", 11),
                              bg=bg_color, padx=15, pady=15)
        frame2.pack(pady=10, padx=20, fill=tk.X)
        
        tk.Label(frame2, text="选择文件夹（转换所有JSON文件）:", bg=bg_color,
                font=("微软雅黑", 10)).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        self.folder_path_var = tk.StringVar()
        folder_entry = tk.Entry(frame2, textvariable=self.folder_path_var,
                               width=50, font=("微软雅黑", 9))
        folder_entry.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Button(frame2, text="浏览...", command=self.browse_folder,
                 font=("微软雅黑", 9), bg="#2196F3", fg="white",
                 relief=tk.RAISED).grid(row=0, column=2, padx=5, pady=5)
        
        # 批量转换按钮
        batch_btn = tk.Button(frame2, text="批量转换", command=self.batch_convert,
                             font=("微软雅黑", 11, "bold"), bg="#FF9800", fg="white",
                             padx=20, pady=5, relief=tk.RAISED)
        batch_btn.grid(row=1, column=0, columnspan=3, pady=15)
        
        # 状态显示区域
        status_frame = tk.Frame(self.root, bg=bg_color)
        status_frame.pack(pady=20, padx=20, fill=tk.BOTH, expand=True)
        
        tk.Label(status_frame, text="转换状态:", bg=bg_color,
                font=("微软雅黑", 10, "bold")).pack(anchor=tk.W)
        
        # 创建滚动文本框显示状态
        from tkinter import scrolledtext
        self.status_text = scrolledtext.ScrolledText(status_frame, height=8,
                                                    font=("Consolas", 9),
                                                    wrap=tk.WORD)
        self.status_text.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 底部信息
        bottom_frame = tk.Frame(self.root, bg=bg_color)
        bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        tk.Label(bottom_frame, text="© 2023 JSON转SRT转换器 | 支持剪映、PR等软件字幕导出",
                font=("微软雅黑", 8), fg="gray", bg=bg_color).pack()
    
    def browse_json(self):
        filename = filedialog.askopenfilename(
            title="选择JSON文件",
            filetypes=[("JSON文件", "*.json"), ("所有文件", "*.*")]
        )
        if filename:
            self.json_path_var.set(filename)
            base_name = os.path.splitext(filename)[0]
            self.output_path_var.set(base_name + '.srt')
    
    def browse_output(self):
        filename = filedialog.asksaveasfilename(
            title="保存SRT文件",
            defaultextension=".srt",
            filetypes=[("SRT字幕文件", "*.srt"), ("所有文件", "*.*")]
        )
        if filename:
            self.output_path_var.set(filename)
    
    def browse_folder(self):
        folder = filedialog.askdirectory(title="选择包含JSON文件的文件夹")
        if folder:
            self.folder_path_var.set(folder)
    
    def log_message(self, message):
        """在状态框中添加消息"""
        self.status_text.insert(tk.END, message + "\n")
        self.status_text.see(tk.END)
        self.root.update()
    
    def clear_log(self):
        """清空状态框"""
        self.status_text.delete(1.0, tk.END)
    
    def convert_single(self):
        json_path = self.json_path_var.get().strip()
        output_path = self.output_path_var.get().strip()
        
        if not json_path:
            messagebox.showwarning("警告", "请选择JSON文件")
            return
        
        if not output_path:
            output_path = None
        
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始转换: {os.path.basename(json_path)}")
        self.log_message("=" * 50)
        
        try:
            success, message = self.converter.process_json_file(json_path, output_path)
            if success:
                self.log_message("\n✅ " + message)
                messagebox.showinfo("成功", "字幕转换完成！")
            else:
                self.log_message("\n❌ " + message)
                messagebox.showerror("错误", message)
        except Exception as e:
            error_msg = f"转换过程中出现错误:\n{str(e)}"
            self.log_message("\n❌ " + error_msg)
            messagebox.showerror("错误", error_msg)
    
    def batch_convert(self):
        folder_path = self.folder_path_var.get().strip()
        
        if not folder_path:
            messagebox.showwarning("警告", "请选择文件夹")
            return
        
        self.clear_log()
        self.log_message("=" * 50)
        self.log_message(f"开始批量转换文件夹: {folder_path}")
        self.log_message("=" * 50)
        
        try:
            success, message = self.converter.batch_convert(folder_path)
            if success:
                self.log_message("\n✅ " + message)
                messagebox.showinfo("成功", "批量转换完成！")
            else:
                self.log_message("\n❌ " + message)
                messagebox.showerror("错误", message)
        except Exception as e:
            error_msg = f"批量转换过程中出现错误:\n{str(e)}"
            self.log_message("\n❌ " + error_msg)
            messagebox.showerror("错误", error_msg)


def main():
    # 设置中文字体（Windows系统）
    if sys.platform == 'win32':
        try:
            from ctypes import windll
            windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
    
    root = tk.Tk()
    app = JSONToSRTGUI(root)
    
    # 居中显示窗口
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'{width}x{height}+{x}+{y}')
    
    root.mainloop()


if __name__ == "__main__":
    main()