"""
Free and open-source auto clicker program
with file management for recordings, loop playback, auto-save, and hotkey minimization.
All rights belong to Bilibili CZH-Technology.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import time
import json
import os
import webbrowser
import shutil
from datetime import datetime
from pynput import mouse, keyboard
from pynput.mouse import Button
from pynput.keyboard import Key

class AutoClickerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("CZH-Connector")
        self.root.geometry("800x500")
        self.root.resizable(True, True)

        # Get the script's directory
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

        # Define folders
        self.settings_dir = os.path.join(self.base_dir, "settings")
        self.recordings_dir = os.path.join(self.base_dir, "recordings")

        # Self-check: ensure folders exist
        self.self_check()

        # File paths
        self.config_file = os.path.join(self.settings_dir, "config.json")

        # Global variables
        self.clicking_active = False
        self.recording_active = False
        self.click_target_count = 0
        self.click_current_count = 0
        self.click_interval = 100
        self.mouse_button = Button.left

        self.current_file = None          # Currently selected recording file path
        self.recorded_events = []         # Events of current file
        self.last_record_time = None
        self.recording_listener = None
        self.hotkey_listener = None
        self.playback_thread = None
        self.playback_stop = False

        # Build UI
        self.create_notebook()
        self.create_connector_tab()
        self.create_playback_tab()
        self.create_about_tab()

        # Load saved settings
        self.load_config()

        # Start global hotkey listener
        self.start_hotkey_listener()

        # Save on close
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    # ==================== Self-check ====================
    def self_check(self):
        """Check if required folders exist; create them if not."""
        try:
            os.makedirs(self.settings_dir, exist_ok=True)
            os.makedirs(self.recordings_dir, exist_ok=True)
            print("Self-check: All folders are ready.")
        except Exception as e:
            print(f"Self-check warning: {e}")

    # ==================== File I/O ====================
    def load_config(self):
        """Load configuration file if it exists."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.click_count_entry.delete(0, tk.END)
                self.click_count_entry.insert(0, str(config.get('click_count', 0)))
                self.interval_entry.delete(0, tk.END)
                self.interval_entry.insert(0, str(config.get('interval', 100)))
                btn = config.get('button', 'left')
                self.click_method_var.set(btn)
            except Exception as e:
                print("Failed to load config:", e)

    def save_config(self):
        """Save current settings to configuration file."""
        try:
            try:
                click_count = int(self.click_count_entry.get() or 0)
            except ValueError:
                click_count = 0
            try:
                interval = self.get_valid_interval()
            except ValueError:
                interval = 100

            config = {
                'click_count': click_count,
                'interval': interval,
                'button': self.click_method_var.get()
            }
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print("Failed to save config:", e)

    def load_events_from_file(self, file_path):
        """Load events from a JSON file and update the UI."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if isinstance(data, list):
                self.recorded_events = data
                self.refresh_event_list()
                return True
            else:
                messagebox.showerror("错误", f"{os.path.basename(file_path)} 格式不正确，应为事件列表")
                return False
        except Exception as e:
            messagebox.showerror("加载失败", str(e))
            return False

    def save_current_events(self):
        """Save current events to the currently selected file."""
        if not self.current_file:
            return False
        try:
            with open(self.current_file, 'w', encoding='utf-8') as f:
                json.dump(self.recorded_events, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            messagebox.showerror("保存失败", str(e))
            return False

    # ==================== UI Construction ====================
    def create_notebook(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=5, pady=5)

    def create_connector_tab(self):
        self.connector_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.connector_frame, text="连点器")

        ttk.Label(self.connector_frame, text="点击次数:").grid(row=0, column=0, sticky='w', padx=10, pady=10)
        self.click_count_entry = ttk.Entry(self.connector_frame, width=10)
        self.click_count_entry.grid(row=0, column=1, sticky='w', padx=5, pady=10)
        self.click_count_entry.insert(0, "0")
        ttk.Label(self.connector_frame, text="(0为无限)").grid(row=0, column=2, sticky='w', padx=5, pady=10)

        ttk.Label(self.connector_frame, text="间隔(ms):").grid(row=1, column=0, sticky='w', padx=10, pady=10)
        self.interval_entry = ttk.Entry(self.connector_frame, width=10)
        self.interval_entry.grid(row=1, column=1, sticky='w', padx=5, pady=10)
        self.interval_entry.insert(0, "100")
        self.interval_entry.bind('<FocusOut>', self.validate_interval)

        self.click_method_var = tk.StringVar(value="left")
        ttk.Label(self.connector_frame, text="点击方式:").grid(row=2, column=0, sticky='w', padx=10, pady=10)
        ttk.Radiobutton(self.connector_frame, text="左键", variable=self.click_method_var,
                        value="left").grid(row=2, column=1, sticky='w', padx=5)
        ttk.Radiobutton(self.connector_frame, text="右键", variable=self.click_method_var,
                        value="right").grid(row=2, column=2, sticky='w', padx=5)

        self.click_status_label = ttk.Label(self.connector_frame, text="● 停止", foreground="red")
        self.click_status_label.grid(row=3, column=0, columnspan=2, sticky='w', padx=10, pady=10)

        ttk.Label(self.connector_frame, text="按 F8 开始/结束连击").grid(row=3, column=2, columnspan=2, padx=10, pady=10)

        self.toggle_click_btn = ttk.Button(self.connector_frame, text="开始连击 (F8)",
                                           command=self.toggle_clicking)
        self.toggle_click_btn.grid(row=4, column=0, columnspan=3, pady=10)

        self.connector_frame.columnconfigure(3, weight=1)

    def validate_interval(self, event=None):
        """Ensure interval is at least 1 ms."""
        try:
            val = int(self.interval_entry.get())
            if val < 1:
                raise ValueError
        except ValueError:
            self.interval_entry.delete(0, tk.END)
            self.interval_entry.insert(0, "1")
            messagebox.showwarning("输入错误", "点击间隔最小为1毫秒，已自动设为1毫秒。")

    def get_valid_interval(self):
        """Return a valid interval integer (>=1)."""
        try:
            val = int(self.interval_entry.get())
            if val < 1:
                return 1
            return val
        except ValueError:
            return 100

    def create_playback_tab(self):
        self.playback_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.playback_frame, text="回放")

        # Left panel: file list
        left_panel = ttk.Frame(self.playback_frame, width=200)
        left_panel.pack(side='left', fill='y', padx=5, pady=5)

        ttk.Label(left_panel, text="录制文件列表", font=('微软雅黑', 10, 'bold')).pack(anchor='w')
        self.file_listbox = tk.Listbox(left_panel, height=15)
        self.file_listbox.pack(fill='both', expand=True, pady=5)
        self.file_listbox.bind('<<ListboxSelect>>', self.on_file_select)

        # Buttons for file operations
        btn_frame = ttk.Frame(left_panel)
        btn_frame.pack(fill='x', pady=5)
        ttk.Button(btn_frame, text="新建", command=self.new_file).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="重命名", command=self.rename_file).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="删除", command=self.delete_file).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="导入", command=self.import_file).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="导出", command=self.export_file).pack(side='left', padx=2)
        ttk.Button(btn_frame, text="刷新", command=self.refresh_file_list).pack(side='left', padx=2)

        # Right panel: event list and controls
        right_panel = ttk.Frame(self.playback_frame)
        right_panel.pack(side='right', fill='both', expand=True, padx=5, pady=5)

        # Create a frame to hold Treeview and scrollbars
        tree_frame = ttk.Frame(right_panel)
        tree_frame.pack(fill='both', expand=True)

        # Treeview columns
        columns = ('#', '按键', 'X', 'Y', '延迟(ms)')
        self.tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=12)
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=80, anchor='center')
        self.tree.column('#', width=40)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Grid layout for Treeview and scrollbars
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)

        self.tree.bind('<Button-3>', self.delete_selected_event)

        # Control buttons
        ctrl_frame = ttk.Frame(right_panel)
        ctrl_frame.pack(fill='x', pady=5)

        self.rec_btn = ttk.Button(ctrl_frame, text="录制 (F7)", command=self.toggle_recording)
        self.rec_btn.pack(side='left', padx=2)
        self.play_btn = ttk.Button(ctrl_frame, text="回放", command=self.start_playback)
        self.play_btn.pack(side='left', padx=2)
        self.stop_btn = ttk.Button(ctrl_frame, text="停止", command=self.stop_playback, state='disabled')
        self.stop_btn.pack(side='left', padx=2)
        self.loop_var = tk.BooleanVar()
        self.loop_cb = ttk.Checkbutton(ctrl_frame, text="循环播放", variable=self.loop_var)
        self.loop_cb.pack(side='left', padx=10)

        self.clear_btn = ttk.Button(ctrl_frame, text="清空事件", command=self.clear_events)
        self.clear_btn.pack(side='right', padx=2)

        self.rec_status_label = ttk.Label(ctrl_frame, text="● 停止录制", foreground="red")
        self.rec_status_label.pack(side='right', padx=10)

        # Initial file list refresh
        self.refresh_file_list()

    def create_about_tab(self):
        about_frame = ttk.Frame(self.notebook)
        self.notebook.add(about_frame, text="关于")

        part1 = "本软件是免费开源的连击器程序，\n最终的所有权归以下人员：\n"
        label1 = tk.Label(about_frame, text=part1, justify='left', font=('微软雅黑', 10))
        label1.pack(padx=20, pady=(20,0), anchor='w')

        # Bilibili link
        bilibili_frame = ttk.Frame(about_frame)
        bilibili_frame.pack(padx=20, pady=0, anchor='w')
        bullet1 = tk.Label(bilibili_frame, text="· ", font=('微软雅黑', 10))
        bullet1.pack(side='left')
        bilibili_link = tk.Label(bilibili_frame, text="B站 CZH-Technology",
                                 font=('微软雅黑', 10, 'underline'),
                                 fg='blue', cursor='hand2')
        bilibili_link.pack(side='left')
        bilibili_link.bind('<Button-1>', lambda e: webbrowser.open('https://b23.tv/3lbRheH'))

        # Kuaishou link
        kuaishou_frame = ttk.Frame(about_frame)
        kuaishou_frame.pack(padx=20, pady=0, anchor='w')
        bullet2 = tk.Label(kuaishou_frame, text="· ", font=('微软雅黑', 10))
        bullet2.pack(side='left')
        kuaishou_link = tk.Label(kuaishou_frame, text="快手 广东细节1",
                                 font=('微软雅黑', 10, 'underline'),
                                 fg='blue', cursor='hand2')
        kuaishou_link.pack(side='left')
        kuaishou_link.bind('<Button-1>', lambda e: webbrowser.open('https://v.kuaishou.com/KY60ewMV'))

        # Douyin link
        douyin_frame = ttk.Frame(about_frame)
        douyin_frame.pack(padx=20, pady=0, anchor='w')
        bullet3 = tk.Label(douyin_frame, text="· ", font=('微软雅黑', 10))
        bullet3.pack(side='left')
        douyin_link = tk.Label(douyin_frame, text="抖音 广东细节1",
                               font=('微软雅黑', 10, 'underline'),
                               fg='blue', cursor='hand2')
        douyin_link.pack(side='left')
        douyin_link.bind('<Button-1>', lambda e: webbrowser.open('https://v.douyin.com/D_Uim35Wqek'))

        # Simplified features
        features = """
功能说明：
- 连点器：F8 开始/停止自动点击（当前鼠标位置）
- 回放：F7 开始/停止录制鼠标点击；支持文件管理、循环播放
- 自动保存：设置和录制事件在退出时自动保存
        """
        label2 = tk.Label(about_frame, text=features, justify='left', font=('微软雅黑', 10))
        label2.pack(padx=20, pady=(10,10), anchor='w')

        version_label = tk.Label(about_frame, text="Ver. 1.06", justify='right', font=('微软雅黑', 9), fg='gray')
        version_label.pack(side='bottom', padx=20, pady=10, anchor='se')

    # ==================== File Management ====================
    def refresh_file_list(self):
        """Refresh the file listbox with all .json files in recordings folder."""
        self.file_listbox.delete(0, tk.END)
        try:
            files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
            files.sort()
            for f in files:
                self.file_listbox.insert(tk.END, f)
            if files:
                self.file_listbox.selection_set(0)
                self.on_file_select()
            else:
                self.current_file = None
                self.recorded_events.clear()
                self.refresh_event_list()
        except Exception as e:
            messagebox.showerror("刷新失败", str(e))

    def on_file_select(self, event=None):
        """Handle file selection from listbox."""
        selection = self.file_listbox.curselection()
        if selection:
            filename = self.file_listbox.get(selection[0])
            self.current_file = os.path.join(self.recordings_dir, filename)
            if not self.load_events_from_file(self.current_file):
                # If load fails, clear events
                self.recorded_events.clear()
                self.refresh_event_list()
        else:
            self.current_file = None
            self.recorded_events.clear()
            self.refresh_event_list()

    def new_file(self):
        """Create a new empty recording file."""
        name = simpledialog.askstring("新建文件", "请输入文件名（不含扩展名）:")
        if not name:
            return
        # Clean filename
        name = "".join(c for c in name if c.isalnum() or c in " _-")
        if not name:
            name = "录制"
        filename = f"{name}.json"
        filepath = os.path.join(self.recordings_dir, filename)
        if os.path.exists(filepath):
            if not messagebox.askyesno("确认", f"文件 {filename} 已存在，是否覆盖？"):
                return
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            self.refresh_file_list()
            # Select the new file
            files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
            if filename in files:
                idx = files.index(filename)
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(idx)
                self.on_file_select()
            messagebox.showinfo("成功", f"已创建文件 {filename}")
        except Exception as e:
            messagebox.showerror("创建失败", str(e))

    def rename_file(self):
        """Rename the currently selected file."""
        if not self.current_file:
            messagebox.showwarning("提示", "请先选择一个文件")
            return
        old_name = os.path.basename(self.current_file)
        new_name = simpledialog.askstring("重命名", "请输入新文件名（不含扩展名）:", initialvalue=old_name.replace('.json',''))
        if not new_name:
            return
        new_name = "".join(c for c in new_name if c.isalnum() or c in " _-")
        if not new_name:
            new_name = "录制"
        new_filename = f"{new_name}.json"
        new_path = os.path.join(self.recordings_dir, new_filename)
        if os.path.exists(new_path):
            messagebox.showerror("错误", f"文件 {new_filename} 已存在")
            return
        try:
            os.rename(self.current_file, new_path)
            self.refresh_file_list()
            # Select renamed file
            files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
            if new_filename in files:
                idx = files.index(new_filename)
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(idx)
                self.on_file_select()
            messagebox.showinfo("成功", "重命名成功")
        except Exception as e:
            messagebox.showerror("重命名失败", str(e))

    def delete_file(self):
        """Delete the currently selected file."""
        if not self.current_file:
            messagebox.showwarning("提示", "请先选择一个文件")
            return
        if messagebox.askyesno("确认", f"确定删除文件 {os.path.basename(self.current_file)} 吗？"):
            try:
                os.remove(self.current_file)
                self.current_file = None
                self.recorded_events.clear()
                self.refresh_event_list()
                self.refresh_file_list()
                messagebox.showinfo("成功", "文件已删除")
            except Exception as e:
                messagebox.showerror("删除失败", str(e))

    def import_file(self):
        """Import an external JSON file into recordings folder."""
        file_path = filedialog.askopenfilename(
            title="选择录制文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if not file_path:
            return
        # Copy to recordings folder with unique name
        base_name = os.path.basename(file_path)
        dest_path = os.path.join(self.recordings_dir, base_name)
        if os.path.exists(dest_path):
            base, ext = os.path.splitext(base_name)
            counter = 1
            new_name = f"{base} ({counter}){ext}"
            while os.path.exists(os.path.join(self.recordings_dir, new_name)):
                counter += 1
                new_name = f"{base} ({counter}){ext}"
            dest_path = os.path.join(self.recordings_dir, new_name)
        try:
            shutil.copy2(file_path, dest_path)
            self.refresh_file_list()
            # Select the imported file
            files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
            filename = os.path.basename(dest_path)
            if filename in files:
                idx = files.index(filename)
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(idx)
                self.on_file_select()
            messagebox.showinfo("成功", f"已导入文件 {os.path.basename(dest_path)}")
        except Exception as e:
            messagebox.showerror("导入失败", str(e))

    def export_file(self):
        """Export the currently selected file to external location."""
        if not self.current_file:
            messagebox.showwarning("提示", "请先选择一个文件")
            return
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            initialfile=os.path.basename(self.current_file),
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        if save_path:
            try:
                shutil.copy2(self.current_file, save_path)
                messagebox.showinfo("成功", f"已导出到 {os.path.basename(save_path)}")
            except Exception as e:
                messagebox.showerror("导出失败", str(e))

    def clear_events(self):
        """Clear all events in the current file."""
        if not self.current_file:
            messagebox.showwarning("提示", "请先选择一个文件")
            return
        if self.recorded_events and messagebox.askyesno("确认", "确定清空当前文件的所有事件吗？"):
            self.recorded_events.clear()
            self.refresh_event_list()
            self.save_current_events()
            messagebox.showinfo("成功", "事件已清空")

    def delete_selected_event(self, event):
        """Delete selected event from the treeview."""
        if not self.current_file:
            return
        selected = self.tree.selection()
        if selected:
            index = self.tree.index(selected[0])
            if messagebox.askyesno("确认", "删除选中事件？"):
                del self.recorded_events[index]
                self.refresh_event_list()
                self.save_current_events()

    def refresh_event_list(self):
        """Refresh the treeview with current events."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        for idx, ev in enumerate(self.recorded_events):
            self.tree.insert('', 'end', values=(
                idx + 1,
                ev['button'],
                ev['x'],
                ev['y'],
                ev['delay']
            ))

    # ==================== Recording Logic ====================
    def toggle_recording(self):
        """Toggle recording state. Creates new file if no file selected."""
        if self.recording_active:
            self.stop_recording()
        else:
            self.start_recording()

    def start_recording(self):
        """Start recording: create a new timestamped file and begin listening."""
        if self.recording_active:
            return

        # Create new file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"录制_{timestamp}.json"
        filepath = os.path.join(self.recordings_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
            self.current_file = filepath
            self.recorded_events = []
            self.refresh_event_list()
            self.refresh_file_list()
            # Select the new file in listbox
            files = [f for f in os.listdir(self.recordings_dir) if f.endswith('.json')]
            if filename in files:
                idx = files.index(filename)
                self.file_listbox.selection_clear(0, tk.END)
                self.file_listbox.selection_set(idx)
        except Exception as e:
            messagebox.showerror("创建文件失败", str(e))
            return

        # Start recording
        self.last_record_time = time.time()
        self.recording_active = True
        self.rec_status_label.config(text="● 录制中", foreground="green")
        self.rec_btn.config(text="停止录制 (F7)")

        def on_click(x, y, button, pressed):
            if not self.recording_active:
                return False
            if pressed:
                now = time.time()
                delay = 0
                if self.last_record_time is not None:
                    delay = int((now - self.last_record_time) * 1000)
                self.last_record_time = now

                btn_str = 'left' if button == mouse.Button.left else 'right'
                event = {
                    'button': btn_str,
                    'x': x,
                    'y': y,
                    'delay': delay
                }
                self.root.after(0, self.add_recorded_event, event)

        self.recording_listener = mouse.Listener(on_click=on_click)
        self.recording_listener.daemon = True
        self.recording_listener.start()

    def add_recorded_event(self, event):
        """Add an event to current recording and save to file."""
        self.recorded_events.append(event)
        self.refresh_event_list()
        self.save_current_events()

    def stop_recording(self):
        """Stop recording and save."""
        self.recording_active = False
        if self.recording_listener and self.recording_listener.is_alive():
            self.recording_listener.stop()
        self.rec_status_label.config(text="● 停止录制", foreground="red")
        self.rec_btn.config(text="录制 (F7)")
        if self.current_file:
            self.save_current_events()

    # ==================== Playback Logic ====================
    def start_playback(self):
        """Start playback of current events, optionally loop."""
        if not self.recorded_events:
            messagebox.showinfo("提示", "没有可回放的事件")
            return
        if self.playback_thread and self.playback_thread.is_alive():
            # Already playing, stop first
            self.stop_playback()
            return

        self.playback_stop = False
        self.play_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.playback_thread = threading.Thread(target=self.playback_loop, daemon=True)
        self.playback_thread.start()

    def playback_loop(self):
        """Play events in a loop based on loop flag."""
        controller = mouse.Controller()
        while not self.playback_stop:
            for ev in self.recorded_events:
                if self.playback_stop:
                    break
                controller.position = (ev['x'], ev['y'])
                time.sleep(0.01)
                button = Button.left if ev['button'] == 'left' else Button.right
                controller.click(button)
                if ev['delay'] > 0:
                    time.sleep(ev['delay'] / 1000.0)
            if not self.loop_var.get():
                break
        self.root.after(0, self.playback_finished)

    def playback_finished(self):
        """Callback when playback stops."""
        self.play_btn.config(state='normal')
        self.stop_btn.config(state='disabled')
        if not self.playback_stop:
            messagebox.showinfo("回放", "回放完成")

    def stop_playback(self):
        """Stop ongoing playback."""
        self.playback_stop = True
        if self.playback_thread and self.playback_thread.is_alive():
            self.playback_thread.join(timeout=0.5)

    # ==================== Global Hotkey Listener ====================
    def start_hotkey_listener(self):
        def on_press(key):
            try:
                if key == Key.f8:
                    self.root.after(0, self.toggle_clicking)
                elif key == Key.f7:
                    self.root.after(0, self.toggle_recording)
            except AttributeError:
                pass
        listener = keyboard.Listener(on_press=on_press)
        listener.daemon = True
        listener.start()
        self.hotkey_listener = listener

    # ---------- Clicking Logic (with minimize) ----------
    def toggle_clicking(self):
        self.root.iconify()
        if self.clicking_active:
            self.stop_clicking()
        else:
            self.start_clicking()

    def start_clicking(self):
        try:
            count = int(self.click_count_entry.get())
        except ValueError:
            count = 0
            self.click_count_entry.delete(0, tk.END)
            self.click_count_entry.insert(0, "0")
        interval = self.get_valid_interval()
        self.click_target_count = count
        self.click_interval = interval
        self.click_current_count = count if count > 0 else 0
        self.clicking_active = True

        self.click_status_label.config(text="● 连击中", foreground="green")
        self.toggle_click_btn.config(text="停止连击 (F8)")
        self.click_task()

    def click_task(self):
        if not self.clicking_active:
            return
        button = Button.left if self.click_method_var.get() == "left" else Button.right
        controller = mouse.Controller()
        controller.click(button)

        if self.click_target_count > 0:
            self.click_current_count -= 1
            if self.click_current_count <= 0:
                self.stop_clicking()
                return

        self.root.after(self.click_interval, self.click_task)

    def stop_clicking(self):
        self.clicking_active = False
        self.click_status_label.config(text="● 停止", foreground="red")
        self.toggle_click_btn.config(text="开始连击 (F8)")

    # ---------- Cleanup ----------
    def on_close(self):
        self.save_config()
        if self.recording_active:
            self.stop_recording()
        self.stop_playback()
        self.clicking_active = False
        if self.recording_listener and self.recording_listener.is_alive():
            self.recording_listener.stop()
        if self.hotkey_listener and self.hotkey_listener.is_alive():
            self.hotkey_listener.stop()
        self.root.destroy()

if __name__ == "__main__":
    AutoClickerApp()