#!/usr/bin/env python3
# PROFESSIONAL MEDIA DOWNLOADER PRO
# Created by: CYBER CAPTAIN 👑
# Features: 10+ Themes | Bigger Quality List | Clean Values | ETA/Speed Explained

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
import queue
import os
import json
import time
import sys
import subprocess
import webbrowser
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageTk
import requests
from io import BytesIO

try:
    import yt_dlp
except ImportError:
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'yt-dlp'])
    import yt_dlp

# ========== CONSTANTS ==========
HISTORY_FILE = 'download_history.json'
CONFIG_FILE = 'downloader_config.json'
DEFAULT_SAVE_PATH = str(Path.home() / 'Desktop' / 'Downloads')

# ========== 10+ THEMES ==========
THEMES = {
    'dark': {
        'name': '🌙 Dark Mode',
        'bg': '#1e1e1e', 'fg': '#ffffff', 'accent': '#007acc',
        'entry_bg': '#2d2d2d', 'select': '#0e639c'
    },
    'hacker': {
        'name': '💚 Hacker Green',
        'bg': '#0a0a0a', 'fg': '#00ff66', 'accent': '#008844',
        'entry_bg': '#001a00', 'select': '#00aa44'
    },
    'modern': {
        'name': '🎨 Modern Light',
        'bg': '#f5f5f5', 'fg': '#333333', 'accent': '#2196f3',
        'entry_bg': '#ffffff', 'select': '#1976d2'
    },
    'red': {
        'name': '🔴 Red Alert',
        'bg': '#1a0000', 'fg': '#ff6666', 'accent': '#cc0000',
        'entry_bg': '#2a0000', 'select': '#ff3333'
    },
    'blue': {
        'name': '💙 Blue Ocean',
        'bg': '#00081a', 'fg': '#66ccff', 'accent': '#0066cc',
        'entry_bg': '#001133', 'select': '#3399ff'
    },
    'purple': {
        'name': '💜 Purple Haze',
        'bg': '#0a001a', 'fg': '#cc99ff', 'accent': '#8800cc',
        'entry_bg': '#15002a', 'select': '#aa66ff'
    },
    'orange': {
        'name': '🧡 Orange Blaze',
        'bg': '#1a0a00', 'fg': '#ffaa66', 'accent': '#cc6600',
        'entry_bg': '#2a1500', 'select': '#ff8844'
    },
    'cyan': {
        'name': '💎 Cyan Dream',
        'bg': '#001a1a', 'fg': '#66ffff', 'accent': '#00cccc',
        'entry_bg': '#002a2a', 'select': '#44ffff'
    },
    'pink': {
        'name': '💖 Pink Candy',
        'bg': '#1a001a', 'fg': '#ff99cc', 'accent': '#cc3399',
        'entry_bg': '#2a002a', 'select': '#ff66bb'
    },
    'gold': {
        'name': '👑 Gold Royal',
        'bg': '#1a1500', 'fg': '#ffdd66', 'accent': '#ccaa00',
        'entry_bg': '#2a2000', 'select': '#ffcc33'
    },
    'matrix': {
        'name': '💚 Matrix Code',
        'bg': '#000000', 'fg': '#33ff33', 'accent': '#00aa00',
        'entry_bg': '#001100', 'select': '#00ff00'
    }
}

# ========== DATA CLASSES ==========
class DownloadJob:
    def __init__(self, url, platform, quality, title="Unknown"):
        self.url = url
        self.platform = platform
        self.quality = quality
        self.title = title
        self.status = "Queued"
        self.progress = "0%"
        self.speed = "0 KB/s"
        self.eta = "--"
        self.downloaded = "0 MB"
        self.total = "--"
        self.pause = False
        self.cancel = False
        self.iid = None
        self.start_time = None
        self.end_time = None
        self.ydl_instance = None

class DownloadHistory:
    def __init__(self):
        self.load()
    
    def load(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, 'r') as f:
                    self.entries = json.load(f)
            except:
                self.entries = []
        else:
            self.entries = []
    
    def save(self):
        with open(HISTORY_FILE, 'w') as f:
            json.dump(self.entries, f, indent=2)
    
    def add(self, url, title, platform, quality, status, size="Unknown"):
        self.entries.insert(0, {
            'time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'url': url,
            'title': title[:100],
            'platform': platform,
            'quality': quality,
            'status': status,
            'size': size
        })
        if len(self.entries) > 500:
            self.entries = self.entries[:500]
        self.save()

history = DownloadHistory()
updates = queue.Queue()
active_jobs = []

# ========== MAIN APPLICATION ==========
class ModernDownloader(tk.Tk):
    def __init__(self):
        super().__init__()
        
        self.title("Media Downloader Pro - CYBER CAPTAIN")
        
        # Get screen size
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        # FULL SCREEN - 100% display
        self.geometry(f"{screen_width}x{screen_height}+0+0")
        self.minsize(1200, 600)
        
        self.load_config()
        self.current_theme = self.config_data.get('theme', 'hacker')
        self.colors = THEMES[self.current_theme]
        self.current_preview_info = None
        
        self.setup_ui()
        self.after(100, self.poll_updates)
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r') as f:
                    self.config_data = json.load(f)
            except:
                self.config_data = {'theme': 'hacker', 'save_path': DEFAULT_SAVE_PATH}
        else:
            self.config_data = {'theme': 'hacker', 'save_path': DEFAULT_SAVE_PATH}
    
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config_data, f, indent=2)
    
    def center_window(self):
        self.update_idletasks()
        x = (self.winfo_screenwidth() // 2) - (self.winfo_width() // 2)
        y = (self.winfo_screenheight() // 2) - (self.winfo_height() // 2)
        self.geometry(f"{self.winfo_width()}x{self.winfo_height()}+{x}+{y}")
    
    def setup_ui(self):
        self.configure(bg=self.colors['bg'])
        
        # Top Bar
        top_bar = tk.Frame(self, bg=self.colors['accent'], height=70)
        top_bar.pack(fill='x')
        top_bar.pack_propagate(False)
        
        title_label = tk.Label(top_bar, text="⚡ MEDIA DOWNLOADER PRO", 
                               font=('Segoe UI', 18, 'bold'), 
                               bg=self.colors['accent'], fg='white')
        title_label.pack(side='left', padx=20, pady=15)
        
        creator_label = tk.Label(top_bar, text="👑 Created by: CYBER CAPTAIN", 
                                 font=('Segoe UI', 11, 'italic'), 
                                 bg=self.colors['accent'], fg='#ffd700')
        creator_label.pack(side='right', padx=20)
        
        # Theme Selection Dropdown
        theme_frame = tk.Frame(top_bar, bg=self.colors['accent'])
        theme_frame.pack(side='right', padx=10)
        
        tk.Label(theme_frame, text="🎨 Theme:", bg=self.colors['accent'], 
                fg='white', font=('Segoe UI', 11)).pack(side='left')
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        theme_menu = ttk.Combobox(theme_frame, textvariable=self.theme_var, 
                                   values=list(THEMES.keys()), state='readonly',
                                   width=15, font=('Segoe UI', 9))
        theme_menu.pack(side='left', padx=5)
        theme_menu.bind('<<ComboboxSelected>>', self.change_theme)
        
        # Main Container
        main_container = tk.Frame(self, bg=self.colors['bg'])
        main_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Left Panel
        left_panel = tk.Frame(main_container, bg=self.colors['bg'])
        left_panel.pack(side='left', fill='both', expand=True)
        
        # URL Input Section
        url_frame = tk.LabelFrame(left_panel, text="📎 Download URL", 
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Segoe UI', 11, 'bold'))
        url_frame.pack(fill='x', pady=(0, 10))
        
        self.url_entry = tk.Entry(url_frame, font=('Segoe UI', 11),
                                   bg=self.colors['entry_bg'], fg=self.colors['fg'],
                                   insertbackground=self.colors['fg'],
                                   relief='flat', highlightthickness=1,
                                   highlightcolor=self.colors['accent'])
        self.url_entry.pack(fill='x', padx=10, pady=10)
        self.url_entry.bind('<KeyRelease>', lambda e: self.fetch_preview())
        
        # Platform Selection
        platform_frame = tk.Frame(url_frame, bg=self.colors['bg'])
        platform_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Label(platform_frame, text="Platform:", bg=self.colors['bg'], 
                fg=self.colors['fg']).pack(side='left')
        
        self.platform_var = tk.StringVar(value="auto")
        platforms = [("🤖 Auto", "auto"), ("▶️ YouTube", "youtube"), 
                     ("📱 TikTok", "tiktok"), ("📸 Instagram", "instagram"), 
                     ("👍 Facebook", "facebook"), ("🐦 Twitter", "twitter")]
        
        for text, value in platforms:
            tk.Radiobutton(platform_frame, text=text, value=value,
                          variable=self.platform_var, bg=self.colors['bg'],
                          fg=self.colors['fg'], selectcolor=self.colors['bg'],
                          activebackground=self.colors['bg']).pack(side='left', padx=5)
        
        # Action Buttons
        action_frame = tk.Frame(url_frame, bg=self.colors['bg'])
        action_frame.pack(fill='x', padx=10, pady=(0, 10))
        
        tk.Button(action_frame, text="🔍 Fetch Info", command=self.fetch_preview,
                 bg=self.colors['accent'], fg='white', font=('Segoe UI', 10),
                 cursor='hand2', relief='flat', padx=20).pack(side='left', padx=5)
        
        tk.Button(action_frame, text="⬇️ Download", command=self.add_download,
                 bg='#28a745', fg='white', font=('Segoe UI', 10, 'bold'),
                 cursor='hand2', relief='flat', padx=20).pack(side='left', padx=5)
        
        tk.Button(action_frame, text="📁 Save Path", command=self.choose_path,
                 bg=self.colors['accent'], fg='white', font=('Segoe UI', 10),
                 cursor='hand2', relief='flat', padx=20).pack(side='left', padx=5)
        
        self.path_label = tk.Label(url_frame, text=f"💾 Save to: {self.config_data['save_path']}",
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Segoe UI', 9))
        self.path_label.pack(anchor='w', padx=10, pady=(0, 10))
        
        # Downloads List - BIGGER ROWS
        downloads_frame = tk.LabelFrame(left_panel, text="📥 Active Downloads",
                                         bg=self.colors['bg'], fg=self.colors['fg'],
                                         font=('Segoe UI', 11, 'bold'))
        downloads_frame.pack(fill='both', expand=True)
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("Treeview", background=self.colors['entry_bg'],
                       foreground=self.colors['fg'], fieldbackground=self.colors['entry_bg'],
                       font=('Segoe UI', 10), rowheight=28)
        style.configure("Treeview.Heading", background=self.colors['accent'],
                       foreground='white', font=('Segoe UI', 11, 'bold'))
        style.map('Treeview', background=[('selected', self.colors['select'])])
        
        columns = ('Title', 'Progress', 'Speed', 'ETA', 'Size', 'Status')
        self.tree = ttk.Treeview(downloads_frame, columns=columns, show='headings', height=14)
        
        col_widths = {'Title': 400, 'Progress': 100, 'Speed': 120, 'ETA': 100, 'Size': 120, 'Status': 100}
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=col_widths[col], anchor='w' if col == 'Title' else 'center')
        
        tree_scroll = ttk.Scrollbar(downloads_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        self.tree.pack(side='left', fill='both', expand=True, padx=5, pady=5)
        tree_scroll.pack(side='right', fill='y', pady=5)
        
        self.tree.bind('<<TreeviewSelect>>', self.on_row_select)
        
        # Download controls
        control_frame = tk.Frame(downloads_frame, bg=self.colors['bg'])
        control_frame.pack(fill='x', padx=5, pady=5)
        
        buttons = [
            ('⏸️ Pause', self.pause_download, '#ffc107'),
            ('▶️ Resume', self.resume_download, '#28a745'),
            ('❌ Cancel', self.cancel_and_remove, '#dc3545'),
            ('🧹 Clear All', self.clear_all, '#6c757d')
        ]
        
        for text, cmd, color in buttons:
            btn = tk.Button(control_frame, text=text, command=cmd,
                           bg=color, fg='white', font=('Segoe UI', 10),
                           cursor='hand2', relief='flat', padx=20)
            btn.pack(side='left', padx=5)
        
        # Right Panel - Auto adjust width based on screen
        right_panel_width = int(self.winfo_screenwidth() * 0.3)
        right_panel = tk.Frame(main_container, bg=self.colors['bg'], width=right_panel_width)
        right_panel.pack(side='right', fill='y', padx=(10, 0))
        right_panel.pack_propagate(False)
        
        notebook = ttk.Notebook(right_panel)
        notebook.pack(fill='both', expand=True)
        
        # Preview Tab
        preview_tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(preview_tab, text="🎬 Preview")
        
        thumb_height = int(self.winfo_screenheight() * 0.25)
        self.thumbnail_frame = tk.Frame(preview_tab, bg=self.colors['entry_bg'],
                                        width=right_panel_width-20, height=thumb_height)
        self.thumbnail_frame.pack(pady=10, padx=10)
        self.thumbnail_frame.pack_propagate(False)
        
        self.thumbnail_label = tk.Label(self.thumbnail_frame, bg=self.colors['entry_bg'],
                                        text="🎬\nNo Preview", font=('Arial', 40),
                                        fg=self.colors['fg'])
        self.thumbnail_label.pack(expand=True, fill='both')
        
        info_frame = tk.LabelFrame(preview_tab, text="📊 Video Info & Download Terms",
                                   bg=self.colors['bg'], fg=self.colors['fg'],
                                   font=('Segoe UI', 10, 'bold'))
        info_frame.pack(fill='both', expand=True, padx=10, pady=5)
        
        self.info_text = tk.Text(info_frame, bg=self.colors['entry_bg'],
                                 fg=self.colors['fg'], font=('Segoe UI', 10),
                                 wrap='word', height=10, relief='flat')
        self.info_text.pack(fill='both', expand=True, padx=5, pady=5)
        
        help_text = "\n\n📌 TERMS EXPLANATION:\n• ETA = Estimated Time Arrival (time remaining)\n• Speed = Download speed (MB/s or KB/s)\n• Progress = Percentage completed"
        self.info_text.insert(tk.END, help_text)
        self.info_text.config(state='disabled')
        
        quality_frame = tk.LabelFrame(preview_tab, text="🎯 Available Qualities (Click to Select)",
                                      bg=self.colors['bg'], fg=self.colors['fg'],
                                      font=('Segoe UI', 10, 'bold'))
        quality_frame.pack(fill='x', padx=10, pady=10)
        
        quality_list_frame = tk.Frame(quality_frame, bg=self.colors['bg'])
        quality_list_frame.pack(fill='x', padx=5, pady=5)
        
        self.quality_listbox = tk.Listbox(quality_list_frame, bg=self.colors['entry_bg'],
                                          fg=self.colors['fg'], height=8,
                                          font=('Segoe UI', 11), selectmode='single',
                                          exportselection=False)
        self.quality_listbox.pack(side='left', fill='x', expand=True)
        
        quality_scroll = tk.Scrollbar(quality_list_frame, orient='vertical', 
                                       command=self.quality_listbox.yview)
        quality_scroll.pack(side='right', fill='y')
        self.quality_listbox.config(yscrollcommand=quality_scroll.set)
        
        # History Tab
        history_tab = tk.Frame(notebook, bg=self.colors['bg'])
        notebook.add(history_tab, text="📜 History")
        
        self.history_listbox = tk.Listbox(history_tab, bg=self.colors['entry_bg'],
                                          fg=self.colors['fg'], font=('Segoe UI', 10),
                                          selectmode='single', height=20)
        self.history_listbox.pack(fill='both', expand=True, padx=5, pady=5)
        
        hist_scroll = tk.Scrollbar(self.history_listbox)
        hist_scroll.pack(side='right', fill='y')
        self.history_listbox.config(yscrollcommand=hist_scroll.set)
        hist_scroll.config(command=self.history_listbox.yview)
        
        hist_btn_frame = tk.Frame(history_tab, bg=self.colors['bg'])
        hist_btn_frame.pack(fill='x', padx=5, pady=5)
        
        tk.Button(hist_btn_frame, text="🔄 Refresh", command=self.refresh_history,
                 bg=self.colors['accent'], fg='white', cursor='hand2',
                 font=('Segoe UI', 9)).pack(side='left', padx=5)
        
        tk.Button(hist_btn_frame, text="🗑️ Clear All", command=self.clear_history,
                 bg='#dc3545', fg='white', cursor='hand2',
                 font=('Segoe UI', 9)).pack(side='left', padx=5)
        
        tk.Button(hist_btn_frame, text="📋 Copy URL", command=self.copy_history_url,
                 bg=self.colors['accent'], fg='white', cursor='hand2',
                 font=('Segoe UI', 9)).pack(side='left', padx=5)
        
        self.refresh_history()
    
    def change_theme(self, event=None):
        new_theme = self.theme_var.get()
        self.current_theme = new_theme
        self.colors = THEMES[new_theme]
        self.config_data['theme'] = new_theme
        self.save_config()
        messagebox.showinfo("🎨 THEME CHANGED", 
                           f"Theme changed to {THEMES[new_theme]['name']}\nRestart application for full effect.")
    
    def format_speed(self, speed_str):
        if not speed_str:
            return "0 KB/s"
        clean = speed_str.strip()
        if 'MiB' in clean:
            clean = clean.replace('MiB/s', 'MB/s')
        elif 'KiB' in clean:
            clean = clean.replace('KiB/s', 'KB/s')
        return clean
    
    def format_eta(self, eta_str):
        if not eta_str or eta_str == '--':
            return '--'
        clean = eta_str.strip()
        if ':' in clean:
            return clean
        return clean
    
    def on_row_select(self, event):
        job = self.get_selected_job()
        if job:
            self.info_text.config(state='normal')
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(tk.END, f"📥 DOWNLOAD INFO:\n\n"
                                          f"🎬 Title: {job.title}\n"
                                          f"🔗 URL: {job.url[:80]}...\n"
                                          f"⚙️ Quality: {job.quality}\n"
                                          f"📱 Platform: {job.platform}\n"
                                          f"📊 Status: {job.status}\n"
                                          f"📈 Progress: {job.progress}\n"
                                          f"⚡ Speed: {self.format_speed(job.speed)}\n"
                                          f"⏰ ETA: {self.format_eta(job.eta)}\n\n"
                                          f"📌 TERMS:\n"
                                          f"• ETA = Time remaining until completion\n"
                                          f"• Speed = Download speed (higher = faster)\n"
                                          f"• Progress = % of file downloaded")
            self.info_text.config(state='disabled')
            
            if job.url:
                self.fetch_thumbnail_for_job(job.url)
    
    def fetch_thumbnail_for_job(self, url):
        def fetch():
            try:
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': 'in_playlist',
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    thumb_url = info.get('thumbnail')
                    
                    if not thumb_url and 'entries' in info and info['entries']:
                        first = info['entries'][0]
                        thumb_url = first.get('thumbnail')
                    
                    if thumb_url:
                        self._load_thumbnail(thumb_url)
            except:
                pass
        
        threading.Thread(target=fetch, daemon=True).start()
    
    def choose_path(self):
        path = filedialog.askdirectory()
        if path:
            self.config_data['save_path'] = path
            self.save_config()
            self.path_label.config(text=f"💾 Save to: {path}")
    
    def fetch_preview(self):
        url = self.url_entry.get().strip()
        if not url:
            return
        
        self.thumbnail_label.config(text="🔄\nLoading...")
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Fetching video information...\n\n📌 TERMS EXPLANATION:\n• ETA = Estimated Time Arrival (time remaining)\n• Speed = Download speed (MB/s or KB/s)\n• Progress = Percentage completed")
        self.info_text.config(state='disabled')
        self.quality_listbox.delete(0, tk.END)
        
        threading.Thread(target=self._fetch_info, args=(url,), daemon=True).start()
    
    def _fetch_info(self, url):
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                if 'entries' in info:
                    self.after(0, lambda: self._display_playlist_info(info))
                else:
                    self.after(0, lambda: self._display_video_info(info))
                    
        except Exception as e:
            self.after(0, lambda: self._show_error(str(e)))
    
    def _display_video_info(self, info):
        title = info.get('title', 'Unknown')
        duration = info.get('duration', 0)
        mins, secs = divmod(duration, 60) if duration else (0, 0)
        views = info.get('view_count', 0)
        likes = info.get('like_count', 0)
        uploader = info.get('uploader', 'Unknown')
        webpage_url = info.get('webpage_url', '')
        
        platform_icon = "📺"
        if 'tiktok' in webpage_url.lower():
            platform_icon = "📱 TikTok"
        elif 'instagram' in webpage_url.lower():
            platform_icon = "📸 Instagram"
        elif 'facebook' in webpage_url.lower():
            platform_icon = "👍 Facebook"
        elif 'twitter' in webpage_url.lower() or 'x.com' in webpage_url.lower():
            platform_icon = "🐦 Twitter"
        
        info_text = f"""{platform_icon} TITLE:
{title}

⏱️ DURATION: {mins}:{secs:02d}
👁️ VIEWS: {views:,}
👍 LIKES: {likes:,}
📺 CHANNEL: {uploader}

📌 DOWNLOAD TERMS:
• ETA = Estimated time remaining
• Speed = Current download speed
• Progress = % completed
"""
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state='disabled')
        
        formats = []
        if 'formats' in info:
            seen = set()
            for f in info['formats']:
                height = f.get('height')
                if height and height <= 2160:
                    format_str = f"🎬 {height}p"
                    if format_str not in seen:
                        seen.add(format_str)
                        formats.append(format_str)
        
        formats.sort(key=lambda x: int(x.replace('🎬 ', '').replace('p', '')))
        
        if formats:
            formats.append("━━━━━━━━━━━━━━━")
        formats.append("🎵 Audio Only (MP3)")
        
        self.quality_listbox.delete(0, tk.END)
        for fmt in formats:
            self.quality_listbox.insert(tk.END, fmt)
        
        if formats:
            self.quality_listbox.selection_set(0)
        
        thumb_url = info.get('thumbnail')
        if thumb_url:
            self._load_thumbnail(thumb_url)
        
        self.current_preview_info = info
    
    def _display_playlist_info(self, info):
        entries = info.get('entries', [])
        total = len(entries)
        
        info_text = f"""📁 PLAYLIST: {info.get('title', 'Unknown')}

📋 TOTAL VIDEOS: {total}

📌 DOWNLOAD TERMS:
• ETA = Estimated time remaining
• Speed = Current download speed
• Progress = % completed
"""
        
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, info_text)
        self.info_text.config(state='disabled')
        
        self.quality_listbox.delete(0, tk.END)
        self.quality_listbox.insert(tk.END, "🎬 Best Quality")
        self.quality_listbox.insert(tk.END, "🎬 1080p")
        self.quality_listbox.insert(tk.END, "🎬 720p")
        self.quality_listbox.insert(tk.END, "🎬 480p")
        self.quality_listbox.insert(tk.END, "━━━━━━━━━━━━━━━")
        self.quality_listbox.insert(tk.END, "🎵 Audio Only")
        self.quality_listbox.selection_set(0)
        
        if entries and len(entries) > 0:
            first = entries[0]
            thumb_url = first.get('thumbnail')
            if thumb_url:
                self._load_thumbnail(thumb_url)
        
        self.current_preview_info = info
    
    def _load_thumbnail(self, url):
        def load():
            try:
                response = requests.get(url, timeout=10)
                img = Image.open(BytesIO(response.content))
                # Auto resize based on screen
                thumb_width = int(self.winfo_screenwidth() * 0.25)
                thumb_height = int(self.winfo_screenheight() * 0.2)
                img = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                self.after(0, lambda: self._set_thumbnail(photo))
            except:
                pass
        
        threading.Thread(target=load, daemon=True).start()
    
    def _set_thumbnail(self, photo):
        self.thumbnail_label.config(image=photo, text='')
        self.thumbnail_label.image = photo
    
    def _show_error(self, error):
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"❌ Error: {error[:200]}")
        self.info_text.config(state='disabled')
        self.thumbnail_label.config(text="❌\nFailed", font=('Arial', 30))
    
    def add_download(self):
        url = self.url_entry.get().strip()
        if not url:
            messagebox.showwarning("No URL", "Please enter a URL")
            return
        
        selection = self.quality_listbox.curselection()
        if selection:
            quality = self.quality_listbox.get(selection[0])
            quality = quality.replace("🎬 ", "").replace("🎵 ", "").replace("━━━━━━━━━━━━━━━", "best")
        else:
            quality = "best"
        
        title = "Fetching..."
        if self.current_preview_info:
            title = self.current_preview_info.get('title', 'Unknown Video')[:60]
        
        platform = self.platform_var.get()
        
        job = DownloadJob(url, platform, quality, title)
        active_jobs.append(job)
        
        job.iid = self.tree.insert('', 0, values=(title, "0%", "0 KB/s", "--", "0 MB", "Queued"))
        
        threading.Thread(target=self._download_worker, args=(job,), daemon=True).start()
        
        self.url_entry.delete(0, tk.END)
        self.thumbnail_label.config(text="🎬\nNo Preview", font=('Arial', 40))
        self.info_text.config(state='normal')
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, "Ready for next download...")
        self.info_text.config(state='disabled')
        self.quality_listbox.delete(0, tk.END)
    
    def _download_worker(self, job):
        save_path = self.config_data['save_path']
        os.makedirs(save_path, exist_ok=True)
        
        is_audio = "Audio" in job.quality or "audio" in job.quality.lower()
        
        if is_audio:
            fmt = 'bestaudio/best'
        elif job.quality == "best" or job.quality == "Best Quality" or "━━" in job.quality:
            fmt = 'bestvideo+bestaudio/best'
        elif job.quality == "Audio Only" or "Audio Only (MP3)" in job.quality:
            fmt = 'bestaudio/best'
            is_audio = True
        else:
            height = job.quality.replace('p', '').replace('🎬 ', '')
            fmt = f'bestvideo[height<={height}]+bestaudio/best'
        
        opts = {
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'format': fmt,
            'merge_output_format': 'mp4',
            'continuedl': True,
            'progress_hooks': [self._make_hook(job)],
            'quiet': True,
            'no_warnings': True,
        }
        
        if is_audio:
            opts['postprocessors'] = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
        
        if job.platform == 'tiktok':
            opts['extractor_args'] = {'tiktok': {'download': {'no_watermark': True}}}
        elif job.platform == 'instagram':
            opts['extractor_args'] = {'instagram': {'download': {'no_watermark': True}}}
        
        job.start_time = time.time()
        
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                job.ydl_instance = ydl
                ydl.download([job.url])
            
            if not job.cancel:
                job.status = "Completed"
                job.progress = "100%"
                job.end_time = time.time()
                updates.put(job)
                history.add(job.url, job.title, job.platform, job.quality, "✅ Completed")
            
        except Exception as e:
            if not job.cancel:
                job.status = "Failed"
                updates.put(job)
                history.add(job.url, job.title, job.platform, job.quality, f"❌ Failed")
    
    def _make_hook(self, job):
        def hook(d):
            if job.cancel:
                raise Exception("Download cancelled")
            
            while job.pause:
                time.sleep(0.2)
                if job.cancel:
                    raise Exception("Download cancelled")
            
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    percent = (downloaded / total) * 100
                    job.progress = f"{percent:.1f}%"
                    downloaded_mb = downloaded / 1048576
                    total_mb = total / 1048576
                    job.downloaded = f"{downloaded_mb:.1f}"
                    job.total = f"{total_mb:.1f}"
                
                raw_speed = d.get('_speed_str', '0 KB/s').strip()
                job.speed = self.format_speed(raw_speed)
                job.eta = self.format_eta(d.get('_eta_str', '--').strip())
                job.status = "Downloading"
                updates.put(job)
                
            elif d['status'] == 'finished':
                job.status = "Processing"
                updates.put(job)
        
        return hook
    
    def poll_updates(self):
        while not updates.empty():
            job = updates.get()
            if job.iid:
                size_display = f"{job.downloaded}/{job.total} MB" if job.total != "--" else job.downloaded
                values = (
                    job.title[:50],
                    job.progress,
                    job.speed,
                    job.eta,
                    size_display,
                    job.status
                )
                self.tree.item(job.iid, values=values)
        
        self.after(250, self.poll_updates)
    
    def get_selected_job(self):
        selection = self.tree.selection()
        if not selection:
            return None
        for job in active_jobs:
            if job.iid == selection[0]:
                return job
        return None
    
    def pause_download(self):
        job = self.get_selected_job()
        if job:
            job.pause = True
            job.status = "Paused"
            updates.put(job)
    
    def resume_download(self):
        job = self.get_selected_job()
        if job:
            job.pause = False
            job.status = "Resuming..."
            updates.put(job)
    
    def cancel_and_remove(self):
        job = self.get_selected_job()
        if job:
            job.cancel = True
            job.status = "Cancelled"
            updates.put(job)
            
            if job.iid and self.tree.exists(job.iid):
                self.tree.delete(job.iid)
            if job in active_jobs:
                active_jobs.remove(job)
            history.add(job.url, job.title, job.platform, job.quality, "❌ Cancelled")
            messagebox.showinfo("Cancelled", f"Download cancelled: {job.title[:50]}")
    
    def clear_all(self):
        if messagebox.askyesno("Clear All", "Cancel and remove all downloads?"):
            for job in active_jobs:
                job.cancel = True
            for item in self.tree.get_children():
                self.tree.delete(item)
            active_jobs.clear()
    
    def refresh_history(self):
        self.history_listbox.delete(0, tk.END)
        for entry in history.entries[:100]:
            status_icon = "✅" if "Completed" in entry['status'] else "❌" if "Failed" in entry['status'] else "⏸️"
            display = f"{status_icon} [{entry['time']}] {entry['title'][:50]}"
            self.history_listbox.insert(tk.END, display)
    
    def clear_history(self):
        if messagebox.askyesno("Clear History", "Delete all download history?"):
            history.entries = []
            history.save()
            self.refresh_history()
    
    def copy_history_url(self):
        selection = self.history_listbox.curselection()
        if selection:
            entry = history.entries[selection[0]]
            self.clipboard_clear()
            self.clipboard_append(entry['url'])
            messagebox.showinfo("Copied", "URL copied to clipboard!")

if __name__ == "__main__":
    app = ModernDownloader()
    app.mainloop()