import os
import shutil
import time
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
from datetime import datetime
import platform
import hashlib
import json
import webbrowser
import sys
import getpass

# ====================================================================================
#                        ONEVALVE CLEANER - MULTI STYLE
#                             WWW.ONEVALVE.RU
# ====================================================================================

class OneValveCleaner:
    def __init__(self, root):
        self.root = root
        self.root.title("ONEVALVE.RU - System Cleaner")
        self.root.geometry("1300x850")
        self.root.minsize(1100, 700)
        self.root.protocol("WM_DELETE_WINDOW", self.exit_app)
        
        # Settings file
        self.settings_file = os.path.join(os.path.expanduser('~'), '.onevalve_settings.json')
        self.load_settings()
        
        # Current theme
        self.current_theme = self.settings.get('theme', 'steam_dark')
        
        # Apply theme
        self.apply_theme()
        
        self.root.configure(bg=self.colors['bg_main'])
        
        # Current view
        self.current_view = "tools"
        
        # Setup UI
        self.setup_ui()
        
        # Update system info
        self.update_time()
        self.update_disk_info()
        
        # Log startup
        self.log("=" * 80, "info")
        self.log(" ONEVALVE.RU System Cleaner", "accent")
        self.log(f" {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}", "info")
        self.log(f" {platform.system()} {platform.release()} | {os.getlogin()}", "info")
        self.log(f" Тема: {self.colors.get('name', self.current_theme)}", "info")
        
        # Check autostart status
        autostart_enabled = self.check_autostart()
        self.log(f" Автозапуск: {'Включен' if autostart_enabled else 'Выключен'}", "info")
        self.log("=" * 80, "info")
        
    def apply_theme(self):
        """Apply selected theme"""
        themes = {
            # Тёмные темы
            'steam_dark': {
                'name': 'Steam Dark',
                'bg_main': '#171a21',
                'bg_secondary': '#1b1f2b',
                'bg_tertiary': '#2a2e3d',
                'bg_input': '#0e1117',
                'accent': '#2a475e',
                'success': '#4c9c2e',
                'warning': '#d2a038',
                'danger': '#a34c4c',
                'text_primary': '#e6e6e6',
                'text_secondary': '#8f98a0',
                'text_muted': '#5c666f',
                'log_bg': '#0e1117',
                'log_fg': '#98fb98',
                'nav_button_bg': '#1b1f2b',
                'nav_button_fg': '#8f98a0',
                'nav_button_active': '#4c9c2e'
            },
            'discord_dark': {
                'name': 'Discord Dark',
                'bg_main': '#36393f',
                'bg_secondary': '#2f3136',
                'bg_tertiary': '#40444b',
                'bg_input': '#202225',
                'accent': '#5865f2',
                'success': '#57f287',
                'warning': '#fee75c',
                'danger': '#ed4245',
                'text_primary': '#ffffff',
                'text_secondary': '#b9bbbe',
                'text_muted': '#72767d',
                'log_bg': '#202225',
                'log_fg': '#ffffff',
                'nav_button_bg': '#2f3136',
                'nav_button_fg': '#ffffff',
                'nav_button_active': '#5865f2'
            },
            'apple_dark': {
                'name': 'Apple Dark',
                'bg_main': '#1c1c1e',
                'bg_secondary': '#2c2c2e',
                'bg_tertiary': '#3a3a3c',
                'bg_input': '#1c1c1e',
                'accent': '#0a84ff',
                'success': '#30d158',
                'warning': '#ff9f0a',
                'danger': '#ff453a',
                'text_primary': '#ffffff',
                'text_secondary': '#8e8e93',
                'text_muted': '#636366',
                'log_bg': '#1c1c1e',
                'log_fg': '#0a84ff',
                'nav_button_bg': '#2c2c2e',
                'nav_button_fg': '#ffffff',
                'nav_button_active': '#0a84ff'
            },
            'arctic_black': {
                'name': 'Arctic Black',
                'bg_main': '#000000',
                'bg_secondary': '#0a0a0a',
                'bg_tertiary': '#141414',
                'bg_input': '#000000',
                'accent': '#00d4ff',
                'success': '#00ff88',
                'warning': '#ffaa00',
                'danger': '#ff3860',
                'text_primary': '#ffffff',
                'text_secondary': '#888888',
                'text_muted': '#555555',
                'log_bg': '#000000',
                'log_fg': '#00d4ff',
                'nav_button_bg': '#0a0a0a',
                'nav_button_fg': '#888888',
                'nav_button_active': '#00d4ff'
            },
            # Светлые темы
            'arctic_white': {
                'name': 'Arctic White',
                'bg_main': '#e8edf2',
                'bg_secondary': '#f0f4f8',
                'bg_tertiary': '#ffffff',
                'bg_input': '#e8edf2',
                'accent': '#2980b9',
                'success': '#27ae60',
                'warning': '#e67e22',
                'danger': '#e74c3c',
                'text_primary': '#2c3e50',
                'text_secondary': '#7f8c8d',
                'text_muted': '#bdc3c7',
                'log_bg': '#f0f4f8',
                'log_fg': '#2c3e50',
                'nav_button_bg': '#ffffff',
                'nav_button_fg': '#7f8c8d',
                'nav_button_active': '#2980b9'
            },
            'apple_light': {
                'name': 'Apple Light',
                'bg_main': '#f5f5f7',
                'bg_secondary': '#ffffff',
                'bg_tertiary': '#e8e8ed',
                'bg_input': '#f5f5f7',
                'accent': '#007aff',
                'success': '#34c759',
                'warning': '#ff9500',
                'danger': '#ff3b30',
                'text_primary': '#1c1c1e',
                'text_secondary': '#8e8e93',
                'text_muted': '#aeaeb2',
                'log_bg': '#f5f5f7',
                'log_fg': '#1c1c1e',
                'nav_button_bg': '#ffffff',
                'nav_button_fg': '#007aff',
                'nav_button_active': '#007aff'
            }
        }
        
        self.colors = themes.get(self.current_theme, themes['steam_dark'])
        
    def check_autostart(self):
        """Check if autostart is enabled"""
        try:
            if platform.system() == 'Windows':
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                return os.path.exists(shortcut_path)
        except:
            pass
        return False
        
    def enable_autostart(self):
        """Enable autostart on Windows startup"""
        try:
            if platform.system() == 'Windows':
                # Get current script path
                if getattr(sys, 'frozen', False):
                    # Running as compiled exe
                    app_path = sys.executable
                else:
                    # Running as script
                    app_path = sys.executable
                    script_path = os.path.abspath(__file__)
                    app_path = f'"{app_path}" "{script_path}"'
                
                # Create startup shortcut
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                
                # Create shortcut using PowerShell
                powershell_script = f'''
$WScriptShell = New-Object -ComObject WScript.Shell
$Shortcut = $WScriptShell.CreateShortcut("{shortcut_path}")
$Shortcut.TargetPath = "{app_path.split('"')[1] if '"' in app_path else app_path}"
$Shortcut.Arguments = "{app_path.split('"')[2] if app_path.count('"') > 1 else ''}"
$Shortcut.WorkingDirectory = "{os.path.dirname(os.path.abspath(__file__))}"
$Shortcut.Description = "ONEVALVE System Cleaner"
$Shortcut.Save()
'''
                # Execute PowerShell
                with open('temp_ps.ps1', 'w', encoding='utf-8') as f:
                    f.write(powershell_script)
                os.system(f'powershell -ExecutionPolicy Bypass -File "temp_ps.ps1"')
                os.remove('temp_ps.ps1')
                
                self.log(" Автозапуск включен", "success")
                return True
        except Exception as e:
            self.log(f" Ошибка включения автозапуска: {e}", "error")
            return False
            
    def disable_autostart(self):
        """Disable autostart"""
        try:
            if platform.system() == 'Windows':
                startup_folder = os.path.join(os.environ['APPDATA'], 
                                             'Microsoft\\Windows\\Start Menu\\Programs\\Startup')
                shortcut_path = os.path.join(startup_folder, 'ONEVALVE_Cleaner.lnk')
                if os.path.exists(shortcut_path):
                    os.remove(shortcut_path)
                    self.log(" Автозапуск выключен", "success")
                    return True
        except Exception as e:
            self.log(f" Ошибка выключения автозапуска: {e}", "error")
            return False
            
    def toggle_autostart(self):
        """Toggle autostart setting"""
        if self.autostart_var.get():
            # Включаем автозапуск
            if self.enable_autostart():
                self.update_setting('autostart', True)
                messagebox.showinfo("Автозапуск", "Автозапуск программы включен!\nПрограмма будет запускаться при старте Windows.")
            else:
                self.autostart_var.set(False)
                messagebox.showerror("Ошибка", "Не удалось включить автозапуск.\nПопробуйте запустить программу от имени администратора.")
        else:
            # Выключаем автозапуск
            if self.disable_autostart():
                self.update_setting('autostart', False)
                messagebox.showinfo("Автозапуск", "Автозапуск программы выключен.")
            else:
                self.autostart_var.set(True)
                messagebox.showerror("Ошибка", "Не удалось выключить автозапуск.")
        
    def restart_app(self):
        """Restart the application"""
        self.log(" Перезапуск приложения для применения темы...", "warning")
        python = sys.executable
        os.execl(python, python, *sys.argv)
        
    def load_settings(self):
        """Load settings from file"""
        default_settings = {
            'auto_clean': False,
            'delete_to_recycle': True,
            'show_notifications': False,
            'theme': 'steam_dark',
            'clean_temp': True,
            'clean_logs': True,
            'clean_cache': True,
            'backup_path': os.path.expanduser('~\\Documents'),
            'autostart': False
        }
        
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    self.settings = json.load(f)
            else:
                self.settings = default_settings
        except:
            self.settings = default_settings
            
    def save_settings(self):
        """Save settings to file"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except:
            pass
        
    def setup_ui(self):
        """Create interface"""
        
        # Top navigation bar
        self.create_navbar()
        
        # Main content area
        self.main_container = tk.Frame(self.root, bg=self.colors['bg_main'])
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=15, pady=(10, 15))
        
        # Left panel
        self.create_left_panel()
        
        # Right panel
        self.create_right_panel()
        
        # Bottom status bar
        self.create_statusbar()
        
        # Show default view
        self.show_tools_view()
        
    def create_navbar(self):
        """Create navigation bar"""
        self.navbar = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=50)
        self.navbar.pack(fill=tk.X)
        self.navbar.pack_propagate(False)
        
        # Logo
        logo_frame = tk.Frame(self.navbar, bg=self.colors['bg_secondary'])
        logo_frame.pack(side=tk.LEFT, padx=20)
        
        self.logo_label = tk.Label(logo_frame, text=" ONE VALVE", 
                                   font=('Segoe UI', 16, 'bold'),
                                   fg=self.colors['success'], bg=self.colors['bg_secondary'])
        self.logo_label.pack(side=tk.LEFT)
        
        steam_label = tk.Label(logo_frame, text="  CLEANER", 
                               font=('Segoe UI', 16, 'bold'),
                               fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'])
        steam_label.pack(side=tk.LEFT)
        
        # Navigation buttons
        self.nav_buttons = []
        
        # Tools button
        tools_btn = tk.Button(self.navbar, text="ИНСТРУМЕНТЫ", 
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['nav_button_bg'], 
                             fg=self.colors['nav_button_fg'],
                             activebackground=self.colors['bg_secondary'],
                             activeforeground=self.colors['text_primary'],
                             relief=tk.FLAT, cursor='hand2', 
                             borderwidth=0, padx=25, pady=12,
                             command=self.show_tools_view)
        tools_btn.pack(side=tk.LEFT, padx=2)
        self.nav_buttons.append(tools_btn)
        
        # Settings button
        settings_btn = tk.Button(self.navbar, text="НАСТРОЙКИ", 
                                font=('Segoe UI', 10, 'bold'),
                                bg=self.colors['nav_button_bg'], 
                                fg=self.colors['nav_button_fg'],
                                activebackground=self.colors['bg_secondary'],
                                activeforeground=self.colors['text_primary'],
                                relief=tk.FLAT, cursor='hand2', 
                                borderwidth=0, padx=25, pady=12,
                                command=self.show_settings_view)
        settings_btn.pack(side=tk.LEFT, padx=2)
        self.nav_buttons.append(settings_btn)
        
        # Forum button
        forum_btn = tk.Button(self.navbar, text="ФОРУМ", 
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['nav_button_bg'], 
                             fg=self.colors['nav_button_fg'],
                             activebackground=self.colors['bg_secondary'],
                             activeforeground=self.colors['text_primary'],
                             relief=tk.FLAT, cursor='hand2', 
                             borderwidth=0, padx=25, pady=12,
                             command=self.open_forum)
        forum_btn.pack(side=tk.LEFT, padx=2)
        self.nav_buttons.append(forum_btn)
        
        # About button
        about_btn = tk.Button(self.navbar, text="О ПРОГРАММЕ", 
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['nav_button_bg'], 
                             fg=self.colors['nav_button_fg'],
                             activebackground=self.colors['bg_secondary'],
                             activeforeground=self.colors['text_primary'],
                             relief=tk.FLAT, cursor='hand2', 
                             borderwidth=0, padx=25, pady=12,
                             command=self.show_about_view)
        about_btn.pack(side=tk.LEFT, padx=2)
        self.nav_buttons.append(about_btn)
        
        # User info
        user_frame = tk.Frame(self.navbar, bg=self.colors['bg_secondary'])
        user_frame.pack(side=tk.RIGHT, padx=20)
        
        self.user_label = tk.Label(user_frame, text=f" {os.getlogin()}", 
                                   font=('Segoe UI', 9), fg=self.colors['text_secondary'],
                                   bg=self.colors['bg_secondary'])
        self.user_label.pack()
        
    def open_forum(self):
        """Open forum website in default browser"""
        url = "https://onevalve.ru/"
        webbrowser.open(url)
        self.log(f" Открыт сайт: {url}", "info")
        
    def create_left_panel(self):
        """Create left panel with tools"""
        self.left_panel = tk.Frame(self.main_container, bg=self.colors['bg_secondary'], width=340)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        self.left_panel.pack_propagate(False)
        
        # Panel header
        header = tk.Frame(self.left_panel, bg=self.colors['bg_tertiary'], height=45)
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header, text=" ИНСТРУМЕНТЫ ОЧИСТКИ", 
                font=('Segoe UI', 11, 'bold'), fg=self.colors['text_primary'],
                bg=self.colors['bg_tertiary']).pack(side=tk.LEFT, padx=15, pady=10)
        
        # Scrollable area for tools
        self.tools_canvas = tk.Canvas(self.left_panel, bg=self.colors['bg_secondary'], highlightthickness=0)
        tools_scrollbar = ttk.Scrollbar(self.left_panel, orient="vertical", command=self.tools_canvas.yview)
        self.tools_frame = tk.Frame(self.tools_canvas, bg=self.colors['bg_secondary'])
        
        self.tools_frame.bind("<Configure>", lambda e: self.tools_canvas.configure(scrollregion=self.tools_canvas.bbox("all")))
        self.tools_canvas.create_window((0, 0), window=self.tools_frame, anchor="nw", width=320)
        self.tools_canvas.configure(yscrollcommand=tools_scrollbar.set)
        
        self.tools_canvas.pack(side="left", fill="both", expand=True)
        tools_scrollbar.pack(side="right", fill="y")
        
        # Tools buttons
        tools = [
            ("temp", "🗑️", "ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ", "Удаление TEMP, кэша, логов", self.clean_temp_files),
            ("downloads", "📁", "ОЧИСТКА ПАПКИ ЗАГРУЗОК", "Очистка папки Downloads", self.clean_downloads),
            ("duplicates", "🔄", "УДАЛЕНИЕ ДУБЛИКАТОВ", "Поиск и удаление копий", self.clean_duplicates),
            ("old", "📊", "ОЧИСТКА СТАРЫХ ФАЙЛОВ", "Удаление файлов старше 30 дней", self.clean_old_files),
            ("recycle", "🗑️", "ОЧИСТКА КОРЗИНЫ", "Полная очистка корзины", self.clean_recycle_bin),
            ("browser", "🌐", "ОЧИСТКА КЭША БРАУЗЕРОВ", "Chrome, Edge, Firefox", self.clean_browser_cache),
            ("disk", "💾", "СТАТИСТИКА ДИСКА", "Информация о дисках", self.show_disk_stats),
        ]
        
        for tool_id, icon, title, desc, command in tools:
            self.create_tool_button(tool_id, icon, title, desc, command)
        
        # Progress section
        self.create_progress_section()
        
    def create_tool_button(self, tool_id, icon, title, desc, command):
        """Create tool button that executes on click"""
        btn_frame = tk.Frame(self.tools_frame, bg=self.colors['bg_secondary'], height=60)
        btn_frame.pack(fill=tk.X, pady=2, padx=5)
        btn_frame.pack_propagate(False)
        
        def on_enter(e):
            btn_frame.config(bg=self.colors['bg_tertiary'])
            icon_label.config(bg=self.colors['bg_tertiary'])
            title_label.config(bg=self.colors['bg_tertiary'])
            desc_label.config(bg=self.colors['bg_tertiary'])
            
        def on_leave(e):
            btn_frame.config(bg=self.colors['bg_secondary'])
            icon_label.config(bg=self.colors['bg_secondary'])
            title_label.config(bg=self.colors['bg_secondary'])
            desc_label.config(bg=self.colors['bg_secondary'])
        
        def on_click(e):
            command()
        
        btn_frame.bind("<Enter>", on_enter)
        btn_frame.bind("<Leave>", on_leave)
        btn_frame.bind("<Button-1>", on_click)
        
        # Icon
        icon_label = tk.Label(btn_frame, text=icon, font=('Segoe UI', 20),
                             bg=self.colors['bg_secondary'], fg=self.colors['success'])
        icon_label.place(x=12, y=12)
        icon_label.bind("<Enter>", on_enter)
        icon_label.bind("<Leave>", on_leave)
        icon_label.bind("<Button-1>", on_click)
        
        # Title
        title_label = tk.Label(btn_frame, text=title, font=('Segoe UI', 10, 'bold'),
                              bg=self.colors['bg_secondary'], fg=self.colors['text_primary'])
        title_label.place(x=65, y=12)
        title_label.bind("<Enter>", on_enter)
        title_label.bind("<Leave>", on_leave)
        title_label.bind("<Button-1>", on_click)
        
        # Description
        desc_label = tk.Label(btn_frame, text=desc, font=('Segoe UI', 8),
                             bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        desc_label.place(x=65, y=35)
        desc_label.bind("<Enter>", on_enter)
        desc_label.bind("<Leave>", on_leave)
        desc_label.bind("<Button-1>", on_click)
        
    def create_progress_section(self):
        """Create progress section at bottom"""
        progress_frame = tk.Frame(self.left_panel, bg=self.colors['bg_tertiary'], height=100)
        progress_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        progress_frame.pack_propagate(False)
        
        self.progress_label = tk.Label(progress_frame, text="ГОТОВ К РАБОТЕ",
                                      font=('Segoe UI', 9, 'bold'), 
                                      bg=self.colors['bg_tertiary'],
                                      fg=self.colors['success'])
        self.progress_label.pack(pady=(10, 5))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(progress_frame, variable=self.progress_var,
                                           length=280, mode='determinate')
        self.progress_bar.pack(pady=(0, 5), padx=15)
        
        self.progress_status = tk.Label(progress_frame, text="",
                                       font=('Segoe UI', 8), bg=self.colors['bg_tertiary'],
                                       fg=self.colors['text_secondary'])
        self.progress_status.pack()
        
    def create_right_panel(self):
        """Create right panel with stacked views"""
        self.right_panel = tk.Frame(self.main_container, bg=self.colors['bg_secondary'])
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Header
        content_header = tk.Frame(self.right_panel, bg=self.colors['bg_tertiary'], height=45)
        content_header.pack(fill=tk.X, pady=(0, 10))
        
        self.view_title = tk.Label(content_header, text=" КОНСОЛЬ ВЫПОЛНЕНИЯ", 
                                   font=('Segoe UI', 11, 'bold'), fg=self.colors['text_primary'],
                                   bg=self.colors['bg_tertiary'])
        self.view_title.pack(side=tk.LEFT, padx=15)
        
        # Stacked frames
        self.tools_frame_right = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        self.settings_frame = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        self.forum_frame = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        self.about_frame = tk.Frame(self.right_panel, bg=self.colors['bg_secondary'])
        
        # Tools view (log console)
        self.log_text = scrolledtext.ScrolledText(self.tools_frame_right, wrap=tk.WORD,
                                                  font=('Consolas', 10),
                                                  bg=self.colors['log_bg'], 
                                                  fg=self.colors['log_fg'],
                                                  insertbackground='white',
                                                  borderwidth=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Configure tags
        self.log_text.tag_config("success", foreground=self.colors['success'])
        self.log_text.tag_config("error", foreground=self.colors['danger'])
        self.log_text.tag_config("info", foreground=self.colors['text_secondary'])
        self.log_text.tag_config("warning", foreground=self.colors['warning'])
        self.log_text.tag_config("accent", foreground=self.colors['accent'])
        
        # Forum view
        self.create_forum_view()
        
        # About view
        self.create_about_view()
        
        # Settings view
        self.create_settings_view()
        
    def create_forum_view(self):
        """Create forum/web view"""
        forum_inner = tk.Frame(self.forum_frame, bg=self.colors['bg_secondary'])
        forum_inner.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        title = tk.Label(forum_inner, text="ONEVALVE ФОРУМ", 
                        font=('Segoe UI', 18, 'bold'), fg=self.colors['text_primary'],
                        bg=self.colors['bg_secondary'])
        title.pack(pady=(0, 20))
        
        desc = tk.Label(forum_inner, 
                       text="Добро пожаловать на официальный форум ONEVALVE!\n\n"
                            "Здесь вы можете:\n"
                            "• Обсудить работу программы\n"
                            "• Задать вопросы разработчикам\n"
                            "• Сообщить о найденных ошибках\n"
                            "• Предложить новые функции\n"
                            "• Поделиться опытом использования\n\n"
                            "Нажмите на кнопку ниже, чтобы перейти на сайт.",
                       font=('Segoe UI', 11), fg=self.colors['text_secondary'],
                       bg=self.colors['bg_secondary'], justify=tk.LEFT)
        desc.pack(pady=10)
        
        open_btn = tk.Button(forum_inner, text="ПЕРЕЙТИ НА САЙТ ONEVALVE", 
                            command=self.open_forum,
                            font=('Segoe UI', 12, 'bold'),
                            bg=self.colors['success'], fg='white',
                            cursor='hand2', borderwidth=0, padx=30, pady=15)
        open_btn.pack(pady=30)
        
        info = tk.Label(forum_inner, text="onevalve.ru", 
                       font=('Segoe UI', 11), fg=self.colors['accent'],
                       bg=self.colors['bg_secondary'])
        info.pack()
        
    def create_about_view(self):
        """Create about page without email"""
        about_inner = tk.Frame(self.about_frame, bg=self.colors['bg_secondary'])
        about_inner.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # Logo
        logo_frame = tk.Frame(about_inner, bg=self.colors['bg_tertiary'], height=100)
        logo_frame.pack(fill=tk.X, pady=(0, 20))
        logo_frame.pack_propagate(False)
        
        logo_text = tk.Label(logo_frame, text=" ONE VALVE ", 
                            font=('Impact', 32, 'bold'), fg=self.colors['success'],
                            bg=self.colors['bg_tertiary'])
        logo_text.pack(pady=25)
        
        # Title
        title = tk.Label(about_inner, text="Системный Очиститель", 
                        font=('Segoe UI', 18, 'bold'), fg=self.colors['text_primary'],
                        bg=self.colors['bg_secondary'])
        title.pack(pady=(0, 5))
        
        version = tk.Label(about_inner, text="Версия 2026.1.0 | Professional Edition", 
                          font=('Segoe UI', 11), fg=self.colors['text_secondary'],
                          bg=self.colors['bg_secondary'])
        version.pack(pady=(0, 20))
        
        # Description
        desc_frame = tk.LabelFrame(about_inner, text=" О ПРОГРАММЕ ", 
                                   font=('Segoe UI', 11, 'bold'), fg=self.colors['success'],
                                   bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        desc_frame.pack(fill=tk.X, pady=10)
        
        desc_text = """ONE VALVE Cleaner - профессиональный инструмент для очистки системы от мусора и оптимизации работы компьютера.

Основные возможности:
• Очистка временных файлов Windows
• Удаление дубликатов файлов
• Очистка кэша популярных браузеров
• Мониторинг дискового пространства
• Множество стилей оформления

Разработано с заботой о вашем компьютере."""
        
        desc_label = tk.Label(desc_frame, text=desc_text, font=('Segoe UI', 10),
                             fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
                             justify=tk.LEFT, wraplength=800)
        desc_label.pack(anchor=tk.W, padx=20, pady=15)
        
        # Features
        features_frame = tk.LabelFrame(about_inner, text=" ТЕХНОЛОГИИ ", 
                                       font=('Segoe UI', 11, 'bold'), fg=self.colors['success'],
                                       bg=self.colors['bg_secondary'], bd=1, relief=tk.RIDGE)
        features_frame.pack(fill=tk.X, pady=10)
        
        features = "• Многопоточная очистка\n• Безопасное удаление файлов\n• Современный интерфейс\n• Поддержка всех версий Windows"
        
        features_label = tk.Label(features_frame, text=features, font=('Segoe UI', 10),
                                  fg=self.colors['text_secondary'], bg=self.colors['bg_secondary'],
                                  justify=tk.LEFT, wraplength=800)
        features_label.pack(anchor=tk.W, padx=20, pady=15)
        
        # Website link
        site_btn = tk.Button(about_inner, text="ПОСЕТИТЬ САЙТ ONEVALVE", command=self.open_forum,
                            font=('Segoe UI', 11, 'bold'), bg=self.colors['accent'], fg='white',
                            cursor='hand2', borderwidth=0, padx=25, pady=10)
        site_btn.pack(pady=10)
        
        # Copyright
        copyright_label = tk.Label(about_inner, text="© 2026 ONE VALVE. Все права защищены.", 
                                  font=('Segoe UI', 9), fg=self.colors['text_muted'],
                                  bg=self.colors['bg_secondary'])
        copyright_label.pack(pady=(20, 0))
        
    def create_settings_view(self):
        """Create settings panel with scroll wheel support"""
        # Create a canvas with scrollbar for settings
        self.settings_canvas = tk.Canvas(self.settings_frame, bg=self.colors['bg_secondary'], highlightthickness=0)
        settings_scrollbar = ttk.Scrollbar(self.settings_frame, orient="vertical", command=self.settings_canvas.yview)
        self.settings_inner = tk.Frame(self.settings_canvas, bg=self.colors['bg_secondary'])
        
        self.settings_inner.bind("<Configure>", lambda e: self.settings_canvas.configure(scrollregion=self.settings_canvas.bbox("all")))
        self.settings_canvas.create_window((0, 0), window=self.settings_inner, anchor="nw", width=900)
        self.settings_canvas.configure(yscrollcommand=settings_scrollbar.set)
        
        # Bind mouse wheel for scrolling
        def on_mousewheel(event):
            self.settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        self.settings_canvas.bind("<MouseWheel>", on_mousewheel)
        self.settings_inner.bind("<MouseWheel>", on_mousewheel)
        
        self.settings_canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        settings_scrollbar.pack(side="right", fill="y")
        
        # Settings title
        title = tk.Label(self.settings_inner, text="НАСТРОЙКИ ПРОГРАММЫ", 
                        font=('Segoe UI', 16, 'bold'), fg=self.colors['text_primary'],
                        bg=self.colors['bg_secondary'])
        title.pack(anchor=tk.W, pady=(0, 20))
        
        # Appearance settings section
        appearance_frame = tk.LabelFrame(self.settings_inner, text=" ВНЕШНИЙ ВИД ", 
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=self.colors['success'], bg=self.colors['bg_secondary'],
                                      bd=1, relief=tk.RIDGE)
        appearance_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(appearance_frame, text="Выберите тему оформления:", 
                font=('Segoe UI', 10), bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Theme selection
        theme_frame = tk.Frame(appearance_frame, bg=self.colors['bg_secondary'])
        theme_frame.pack(fill=tk.X, padx=20, pady=(0, 10))
        
        self.theme_var = tk.StringVar(value=self.current_theme)
        
        # Create two rows of themes
        themes_list = [
            ("steam_dark", "Steam Dark"),
            ("discord_dark", "Discord Dark"),
            ("apple_dark", "Apple Dark"),
            ("arctic_black", "Arctic Black"),
            ("arctic_white", "Arctic White"),
            ("apple_light", "Apple Light")
        ]
        
        # First row
        row1_frame = tk.Frame(theme_frame, bg=self.colors['bg_secondary'])
        row1_frame.pack(fill=tk.X, pady=5)
        
        for theme_value, theme_name in themes_list[:3]:
            rb = tk.Radiobutton(row1_frame, text=theme_name, variable=self.theme_var, value=theme_value,
                                command=self.change_theme_instant, bg=self.colors['bg_secondary'],
                                fg=self.colors['text_primary'], selectcolor=self.colors['bg_secondary'],
                                activebackground=self.colors['bg_secondary'],
                                font=('Segoe UI', 10))
            rb.pack(side=tk.LEFT, padx=(0, 20))
        
        # Second row
        row2_frame = tk.Frame(theme_frame, bg=self.colors['bg_secondary'])
        row2_frame.pack(fill=tk.X, pady=5)
        
        for theme_value, theme_name in themes_list[3:]:
            rb = tk.Radiobutton(row2_frame, text=theme_name, variable=self.theme_var, value=theme_value,
                                command=self.change_theme_instant, bg=self.colors['bg_secondary'],
                                fg=self.colors['text_primary'], selectcolor=self.colors['bg_secondary'],
                                activebackground=self.colors['bg_secondary'],
                                font=('Segoe UI', 10))
            rb.pack(side=tk.LEFT, padx=(0, 20))
        
        # Preview label
        self.preview_label = tk.Label(appearance_frame, text="", font=('Segoe UI', 9),
                                      bg=self.colors['bg_secondary'], fg=self.colors['text_secondary'])
        self.preview_label.pack(anchor=tk.W, padx=20, pady=(5, 10))
        
        # Restart info
        restart_info = tk.Label(appearance_frame, text="ВНИМАНИЕ: Для применения темы требуется перезапуск программы!", 
                                font=('Segoe UI', 9), fg=self.colors['warning'],
                                bg=self.colors['bg_secondary'])
        restart_info.pack(anchor=tk.W, padx=20, pady=(0, 5))
        
        # Restart button
        restart_btn = tk.Button(appearance_frame, text="ПЕРЕЗАПУСТИТЬ ПРИЛОЖЕНИЕ", 
                               command=self.restart_app,
                               font=('Segoe UI', 10, 'bold'),
                               bg=self.colors['success'], fg='white',
                               cursor='hand2', borderwidth=0, padx=20, pady=8)
        restart_btn.pack(pady=(5, 15))
        
        self.update_preview()
        
        # System settings section
        system_frame = tk.LabelFrame(self.settings_inner, text=" СИСТЕМНЫЕ НАСТРОЙКИ ", 
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=self.colors['success'], bg=self.colors['bg_secondary'],
                                      bd=1, relief=tk.RIDGE)
        system_frame.pack(fill=tk.X, pady=10)
        
        # Autostart
        autostart_frame = tk.Frame(system_frame, bg=self.colors['bg_secondary'])
        autostart_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.autostart_var = tk.BooleanVar(value=self.check_autostart())
        autostart_cb = tk.Checkbutton(autostart_frame, text="Запускать программу при старте Windows",
                                      variable=self.autostart_var,
                                      command=self.toggle_autostart,
                                      bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                      selectcolor=self.colors['bg_secondary'],
                                      activebackground=self.colors['bg_secondary'],
                                      font=('Segoe UI', 10))
        autostart_cb.pack(side=tk.LEFT)
        
        autostart_info = tk.Label(autostart_frame, text="(требуются права администратора для изменения)",
                                  font=('Segoe UI', 8), fg=self.colors['text_muted'],
                                  bg=self.colors['bg_secondary'])
        autostart_info.pack(side=tk.LEFT, padx=(10, 0))
        
        # General settings section
        general_frame = tk.LabelFrame(self.settings_inner, text=" ОБЩИЕ НАСТРОЙКИ ", 
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=self.colors['success'], bg=self.colors['bg_secondary'],
                                      bd=1, relief=tk.RIDGE)
        general_frame.pack(fill=tk.X, pady=10)
        
        # Auto clean
        self.auto_clean_var = tk.BooleanVar(value=self.settings.get('auto_clean', False))
        auto_clean_cb = tk.Checkbutton(general_frame, text="Автоматическая очистка при запуске",
                                       variable=self.auto_clean_var,
                                       command=lambda: self.update_setting('auto_clean', self.auto_clean_var.get()),
                                       bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                       selectcolor=self.colors['bg_secondary'],
                                       activebackground=self.colors['bg_secondary'],
                                       font=('Segoe UI', 10))
        auto_clean_cb.pack(anchor=tk.W, padx=20, pady=10)
        
        # Delete to recycle
        self.recycle_var = tk.BooleanVar(value=self.settings.get('delete_to_recycle', True))
        recycle_cb = tk.Checkbutton(general_frame, text="Перемещать файлы в корзину вместо полного удаления",
                                    variable=self.recycle_var,
                                    command=lambda: self.update_setting('delete_to_recycle', self.recycle_var.get()),
                                    bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                    selectcolor=self.colors['bg_secondary'],
                                    activebackground=self.colors['bg_secondary'],
                                    font=('Segoe UI', 10))
        recycle_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # Cleanup settings section
        cleanup_frame = tk.LabelFrame(self.settings_inner, text=" НАСТРОЙКИ ОЧИСТКИ ", 
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=self.colors['success'], bg=self.colors['bg_secondary'],
                                      bd=1, relief=tk.RIDGE)
        cleanup_frame.pack(fill=tk.X, pady=10)
        
        # Clean temp
        self.clean_temp_var = tk.BooleanVar(value=self.settings.get('clean_temp', True))
        temp_cb = tk.Checkbutton(cleanup_frame, text="Очищать временные файлы",
                                 variable=self.clean_temp_var,
                                 command=lambda: self.update_setting('clean_temp', self.clean_temp_var.get()),
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                 selectcolor=self.colors['bg_secondary'],
                                 activebackground=self.colors['bg_secondary'],
                                 font=('Segoe UI', 10))
        temp_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # Clean logs
        self.clean_logs_var = tk.BooleanVar(value=self.settings.get('clean_logs', True))
        logs_cb = tk.Checkbutton(cleanup_frame, text="Очищать системные логи",
                                 variable=self.clean_logs_var,
                                 command=lambda: self.update_setting('clean_logs', self.clean_logs_var.get()),
                                 bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                 selectcolor=self.colors['bg_secondary'],
                                 activebackground=self.colors['bg_secondary'],
                                 font=('Segoe UI', 10))
        logs_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # Clean cache
        self.clean_cache_var = tk.BooleanVar(value=self.settings.get('clean_cache', True))
        cache_cb = tk.Checkbutton(cleanup_frame, text="Очищать кэш приложений",
                                  variable=self.clean_cache_var,
                                  command=lambda: self.update_setting('clean_cache', self.clean_cache_var.get()),
                                  bg=self.colors['bg_secondary'], fg=self.colors['text_primary'],
                                  selectcolor=self.colors['bg_secondary'],
                                  activebackground=self.colors['bg_secondary'],
                                  font=('Segoe UI', 10))
        cache_cb.pack(anchor=tk.W, padx=20, pady=5)
        
        # Storage path section
        storage_frame = tk.LabelFrame(self.settings_inner, text=" ХРАНИЛИЩЕ ", 
                                      font=('Segoe UI', 12, 'bold'),
                                      fg=self.colors['success'], bg=self.colors['bg_secondary'],
                                      bd=1, relief=tk.RIDGE)
        storage_frame.pack(fill=tk.X, pady=10)
        
        path_frame = tk.Frame(storage_frame, bg=self.colors['bg_secondary'])
        path_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(path_frame, text="Путь для бэкапов:", font=('Segoe UI', 10),
                bg=self.colors['bg_secondary'], fg=self.colors['text_primary']).pack(side=tk.LEFT)
        
        self.backup_path = tk.StringVar(value=self.settings.get('backup_path', os.path.expanduser('~\\Documents')))
        path_entry = tk.Entry(path_frame, textvariable=self.backup_path, width=40,
                              bg=self.colors['bg_input'], fg=self.colors['text_primary'],
                              insertbackground='white', font=('Segoe UI', 10))
        path_entry.pack(side=tk.LEFT, padx=10)
        
        def select_path():
            path = filedialog.askdirectory()
            if path:
                self.backup_path.set(path)
                self.update_setting('backup_path', path)
        
        path_btn = tk.Button(path_frame, text="Выбрать", command=select_path,
                            bg=self.colors['accent'], fg='white', cursor='hand2', 
                            borderwidth=0, padx=15, pady=5, font=('Segoe UI', 9))
        path_btn.pack(side=tk.LEFT)
        
        # Reset settings section
        reset_frame = tk.LabelFrame(self.settings_inner, text=" СБРОС НАСТРОЕК ", 
                                    font=('Segoe UI', 12, 'bold'),
                                    fg=self.colors['danger'], bg=self.colors['bg_secondary'],
                                    bd=1, relief=tk.RIDGE)
        reset_frame.pack(fill=tk.X, pady=10)
        
        reset_info = tk.Label(reset_frame, text="Сбросить все настройки к значениям по умолчанию", 
                             font=('Segoe UI', 10), bg=self.colors['bg_secondary'], 
                             fg=self.colors['text_secondary'])
        reset_info.pack(anchor=tk.W, padx=20, pady=(10, 5))
        
        # Нормальная кнопка сброса
        reset_btn = tk.Button(reset_frame, text="СБРОСИТЬ ВСЕ НАСТРОЙКИ", 
                             command=self.reset_settings,
                             font=('Segoe UI', 10, 'bold'),
                             bg=self.colors['danger'], fg='white',
                             cursor='hand2', borderwidth=0, padx=20, pady=10)
        reset_btn.pack(pady=(5, 15))
        
    def update_preview(self):
        """Update theme preview text"""
        themes_preview = {
            'steam_dark': "Steam Dark: тёмно-синяя тема в стиле Steam",
            'discord_dark': "Discord Dark: тёмно-серая тема в стиле Discord",
            'apple_dark': "Apple Dark: тёмная тема в стиле Apple",
            'arctic_black': "Arctic Black: глубокая чёрная тема с неоновыми акцентами",
            'arctic_white': "Arctic White: светлая тема в стиле арктической белизны",
            'apple_light': "Apple Light: светлая тема в стиле Apple"
        }
        self.preview_label.config(text=themes_preview.get(self.theme_var.get(), "Выберите тему"))
        
    def change_theme_instant(self):
        """Change theme and save, then require restart"""
        new_theme = self.theme_var.get()
        if new_theme != self.current_theme:
            self.current_theme = new_theme
            self.update_setting('theme', new_theme)
            self.update_preview()
            self.log(f" Тема изменена на {new_theme}", "success")
            self.log(" ДЛЯ ПРИМЕНЕНИЯ ТЕМЫ НАЖМИТЕ КНОПКУ ПЕРЕЗАПУСКА!", "warning")
            messagebox.showinfo("Смена темы", 
                               f"Тема изменена на {new_theme}\n\n"
                               "Для полного применения темы нажмите кнопку 'ПЕРЕЗАПУСТИТЬ ПРИЛОЖЕНИЕ'\n"
                               "в разделе настроек 'ВНЕШНИЙ ВИД'.")
        
    def update_setting(self, key, value):
        """Update a setting"""
        self.settings[key] = value
        self.save_settings()
        self.log(f"Настройка {key} изменена на {value}", "info")
        
    def reset_settings(self):
        """Reset all settings to default"""
        result = messagebox.askyesno("Сброс настроек", 
                                     "ВНИМАНИЕ! Это действие сбросит ВСЕ настройки к значениям по умолчанию.\n\n"
                                     "Будут сброшены:\n"
                                     "• Тема оформления (Steam Dark)\n"
                                     "• Настройки очистки\n"
                                     "• Путь для бэкапов\n"
                                     "• Автозапуск (будет выключен)\n\n"
                                     "Продолжить?")
        
        if result:
            # Сброс к значениям по умолчанию
            self.settings = {
                'auto_clean': False,
                'delete_to_recycle': True,
                'show_notifications': False,
                'theme': 'steam_dark',
                'clean_temp': True,
                'clean_logs': True,
                'clean_cache': True,
                'backup_path': os.path.expanduser('~\\Documents'),
                'autostart': False
            }
            self.save_settings()
            
            # Обновление UI переменных
            self.auto_clean_var.set(False)
            self.recycle_var.set(True)
            self.clean_temp_var.set(True)
            self.clean_logs_var.set(True)
            self.clean_cache_var.set(True)
            self.backup_path.set(os.path.expanduser('~\\Documents'))
            self.theme_var.set('steam_dark')
            self.current_theme = 'steam_dark'
            self.autostart_var.set(False)
            self.update_preview()
            
            # Выключаем автозапуск
            self.disable_autostart()
            
            self.log("Настройки сброшены к значениям по умолчанию!", "success")
            self.log(" ДЛЯ ПРИМЕНЕНИЯ ТЕМЫ НАЖМИТЕ ПЕРЕЗАПУСК!", "warning")
            
            messagebox.showinfo("Сброс настроек", 
                               "Настройки успешно сброшены!\n\n"
                               "Для применения темы по умолчанию (Steam Dark) нажмите кнопку перезапуска.")
        
    def show_tools_view(self):
        """Show tools view"""
        self.current_view = "tools"
        self.view_title.config(text=" КОНСОЛЬ ВЫПОЛНЕНИЯ")
        self.tools_frame_right.pack(fill=tk.BOTH, expand=True)
        self.settings_frame.pack_forget()
        self.forum_frame.pack_forget()
        self.about_frame.pack_forget()
        # Update active button color
        for btn in self.nav_buttons:
            if btn.cget('text') == "ИНСТРУМЕНТЫ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
        
    def show_settings_view(self):
        """Show settings view"""
        self.current_view = "settings"
        self.view_title.config(text=" НАСТРОЙКИ ПРОГРАММЫ")
        self.settings_frame.pack(fill=tk.BOTH, expand=True)
        self.tools_frame_right.pack_forget()
        self.forum_frame.pack_forget()
        self.about_frame.pack_forget()
        # Update active button color
        for btn in self.nav_buttons:
            if btn.cget('text') == "НАСТРОЙКИ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
                
    def show_forum_view(self):
        """Show forum view"""
        self.current_view = "forum"
        self.view_title.config(text=" ФОРУМ ONEVALVE")
        self.forum_frame.pack(fill=tk.BOTH, expand=True)
        self.tools_frame_right.pack_forget()
        self.settings_frame.pack_forget()
        self.about_frame.pack_forget()
        # Update active button color
        for btn in self.nav_buttons:
            if btn.cget('text') == "ФОРУМ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
                
    def show_about_view(self):
        """Show about view"""
        self.current_view = "about"
        self.view_title.config(text=" О ПРОГРАММЕ")
        self.about_frame.pack(fill=tk.BOTH, expand=True)
        self.tools_frame_right.pack_forget()
        self.settings_frame.pack_forget()
        self.forum_frame.pack_forget()
        # Update active button color
        for btn in self.nav_buttons:
            if btn.cget('text') == "О ПРОГРАММЕ":
                btn.configure(fg=self.colors['nav_button_active'])
            else:
                btn.configure(fg=self.colors['nav_button_fg'])
        
    def create_statusbar(self):
        """Create status bar"""
        self.statusbar = tk.Frame(self.root, bg=self.colors['bg_secondary'], height=30)
        self.statusbar.pack(fill=tk.X, side=tk.BOTTOM)
        self.statusbar.pack_propagate(False)
        
        self.status_text = tk.Label(self.statusbar, text="● ГОТОВ", 
                                   font=('Segoe UI', 8, 'bold'),
                                   fg=self.colors['success'], bg=self.colors['bg_secondary'])
        self.status_text.pack(side=tk.LEFT, padx=15)
        
        tk.Label(self.statusbar, text="ONEVALVE.RU System Cleaner", 
                font=('Segoe UI', 8), fg=self.colors['text_muted'],
                bg=self.colors['bg_secondary']).pack(side=tk.LEFT, padx=20)
        
        self.time_label = tk.Label(self.statusbar, text="", font=('Segoe UI', 8),
                                  fg=self.colors['text_muted'], bg=self.colors['bg_secondary'])
        self.time_label.pack(side=tk.RIGHT, padx=15)
        
        self.disk_label = tk.Label(self.statusbar, text="", font=('Segoe UI', 8),
                                  fg=self.colors['text_muted'], bg=self.colors['bg_secondary'])
        self.disk_label.pack(side=tk.RIGHT, padx=15)
        
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.config(text=f" {current_time}")
        self.root.after(1000, self.update_time)
        
    def update_disk_info(self):
        """Update disk info"""
        try:
            total, used, free = shutil.disk_usage("C:\\")
            free_gb = free / (1024**3)
            self.disk_label.config(text=f" Свободно: {free_gb:.1f} ГБ")
        except:
            pass
        self.root.after(5000, self.update_disk_info)
        
    def log(self, message, tag=None):
        """Add log message"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        self.log_text.insert(tk.END, formatted, tag)
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def update_progress(self, value, text):
        """Update progress bar"""
        self.progress_var.set(value)
        self.progress_status.config(text=text)
        self.root.update_idletasks()
        
    def run_task(self, func, *args):
        """Run task in thread"""
        def target():
            self.status_text.config(text="● ВЫПОЛНЕНИЕ...", fg=self.colors['warning'])
            self.progress_label.config(text="ВЫПОЛНЕНИЕ...", fg=self.colors['warning'])
            self.root.config(cursor="watch")
            self.update_progress(0, "Запуск...")
            try:
                func(*args)
                self.update_progress(100, "Завершено!")
                self.status_text.config(text="● ГОТОВ", fg=self.colors['success'])
                self.progress_label.config(text="ГОТОВ К РАБОТЕ", fg=self.colors['success'])
            except Exception as e:
                self.log(f"Ошибка: {str(e)}", "error")
                self.status_text.config(text="● ОШИБКА", fg=self.colors['danger'])
                self.progress_label.config(text="ОШИБКА", fg=self.colors['danger'])
            finally:
                self.root.config(cursor="")
                self.root.after(3000, lambda: self.update_progress(0, ""))
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        
    def format_size(self, size):
        """Format size"""
        for unit in ['Б', 'КБ', 'МБ', 'ГБ', 'ТБ']:
            if size < 1024.0:
                return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} ТБ"
        
    # ==================== CLEANING FUNCTIONS ====================
    
    def clean_temp_files(self):
        """Clean temporary files"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ОЧИСТКА ВРЕМЕННЫХ ФАЙЛОВ", "accent")
            
            temp_folders = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                os.path.expanduser('~\\AppData\\Local\\Temp'),
                'C:\\Windows\\Temp',
            ]
            
            extensions = ['.tmp', '.log', '.cache', '.temp', '.old', '.bak']
            deleted_count = 0
            deleted_size = 0
            all_files = []
            
            for folder in temp_folders:
                if folder and os.path.exists(folder):
                    self.log(f" Сканирование: {folder}", "info")
                    for root, dirs, files in os.walk(folder):
                        for file in files:
                            if any(file.lower().endswith(ext) for ext in extensions):
                                all_files.append(os.path.join(root, file))
            
            if all_files:
                self.log(f" Найдено файлов: {len(all_files)}", "info")
                
                for i, file_path in enumerate(all_files):
                    try:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        deleted_count += 1
                        deleted_size += file_size
                        self.update_progress((i + 1) * 100 // len(all_files), 
                                           f"Удаление... {deleted_count}/{len(all_files)}")
                    except:
                        pass
                
                self.log(f" Удалено файлов: {deleted_count}", "success")
                self.log(f" Освобождено: {self.format_size(deleted_size)}", "success")
            else:
                self.log(" Временные файлы не найдены", "success")
            
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def clean_downloads(self):
        """Clean downloads folder"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ОЧИСТКА ПАПКИ ЗАГРУЗОК", "accent")
            
            downloads = os.path.expanduser('~\\Downloads')
            extensions = ['.exe', '.msi', '.tmp', '.crdownload', '.part']
            
            if os.path.exists(downloads):
                files = [f for f in os.listdir(downloads) 
                        if any(f.lower().endswith(ext) for ext in extensions)]
                
                if files:
                    self.log(f" Найдено файлов: {len(files)}", "info")
                    total_size = 0
                    
                    for i, file in enumerate(files):
                        try:
                            path = os.path.join(downloads, file)
                            size = os.path.getsize(path)
                            os.remove(path)
                            total_size += size
                            self.update_progress((i + 1) * 100 // len(files), 
                                               f"Удаление... {i+1}/{len(files)}")
                        except:
                            pass
                    
                    self.log(f" Удалено файлов: {len(files)}", "success")
                    self.log(f" Освобождено: {self.format_size(total_size)}", "success")
                else:
                    self.log(" Папка загрузок чиста", "success")
            else:
                self.log(" Папка загрузок не найдена", "error")
            
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def clean_old_files(self):
        """Clean old files"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ОЧИСТКА СТАРЫХ ФАЙЛОВ", "accent")
            
            days = 30
            folder = os.path.expanduser('~\\Downloads')
            now = time.time()
            deleted = 0
            total_size = 0
            
            self.log(f" Сканирование: {folder}", "info")
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        age = (now - os.path.getmtime(path)) / (24 * 3600)
                        if age > days:
                            size = os.path.getsize(path)
                            os.remove(path)
                            deleted += 1
                            total_size += size
                    except:
                        pass
            
            self.log(f" Удалено файлов: {deleted}", "success")
            self.log(f" Освобождено: {self.format_size(total_size)}", "success")
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def clean_recycle_bin(self):
        """Clean recycle bin"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ОЧИСТКА КОРЗИНЫ", "accent")
            try:
                import ctypes
                ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, 1)
                self.log(" Корзина очищена", "success")
            except Exception as e:
                self.log(f" Ошибка: {e}", "error")
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def show_disk_stats(self):
        """Show disk statistics"""
        def task():
            self.log("=" * 70, "info")
            self.log(" СТАТИСТИКА ДИСКОВ", "accent")
            
            for drive in range(65, 91):
                letter = chr(drive) + ":\\"
                if os.path.exists(letter):
                    try:
                        total, used, free = shutil.disk_usage(letter)
                        percent = (used / total) * 100
                        self.log(f" ДИСК {letter}", "info")
                        self.log(f"    Всего: {self.format_size(total)}", "info")
                        self.log(f"    Занято: {self.format_size(used)} ({percent:.1f}%)", 
                                "warning" if percent > 70 else "success")
                        self.log(f"    Свободно: {self.format_size(free)}", "success")
                        self.log("", None)
                    except:
                        pass
            
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def clean_duplicates(self):
        """Remove duplicates"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ПОИСК ДУБЛИКАТОВ", "accent")
            self.log(" Выполняется поиск...", "warning")
            
            folder = os.path.expanduser('~\\Desktop')
            hashes = {}
            duplicates = []
            
            for root, dirs, files in os.walk(folder):
                for file in files:
                    path = os.path.join(root, file)
                    try:
                        with open(path, 'rb') as f:
                            file_hash = hashlib.md5(f.read()).hexdigest()
                        if file_hash in hashes:
                            duplicates.append(path)
                            self.log(f" Найден дубликат: {file}", "warning")
                        else:
                            hashes[file_hash] = path
                    except:
                        pass
            
            if duplicates:
                for dup in duplicates:
                    try:
                        os.remove(dup)
                    except:
                        pass
                self.log(f" Удалено дубликатов: {len(duplicates)}", "success")
            else:
                self.log(" Дубликатов не найдено", "success")
            
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def clean_browser_cache(self):
        """Clean browser cache"""
        def task():
            self.log("=" * 70, "info")
            self.log(" ОЧИСТКА КЭША БРАУЗЕРОВ", "accent")
            
            browsers = [
                ("Chrome", os.path.expanduser('~\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache')),
                ("Edge", os.path.expanduser('~\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache'))
            ]
            
            for name, path in browsers:
                if os.path.exists(path):
                    try:
                        size = 0
                        for dirpath, dirnames, filenames in os.walk(path):
                            for f in filenames:
                                try:
                                    size += os.path.getsize(os.path.join(dirpath, f))
                                except:
                                    pass
                        shutil.rmtree(path, ignore_errors=True)
                        self.log(f"   {name}: очищено {self.format_size(size)}", "success")
                    except:
                        self.log(f"   {name}: ошибка", "error")
            
            self.log("=" * 70, "info")
        
        self.run_task(task)
        
    def exit_app(self):
        """Exit application"""
        self.log("Завершение работы...")
        self.root.after(500, self.root.destroy)

# ====================================================================================
#                              RUN APPLICATION
# ====================================================================================

if __name__ == "__main__":
    root = tk.Tk()
    app = OneValveCleaner(root)
    root.mainloop()