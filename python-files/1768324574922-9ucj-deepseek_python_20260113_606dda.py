"""
🚀 COMPLETE AUTO-UPDATER & AI ERROR CHECKER - WINDOWS EXE VERSION
Version: 5.0.0
Single File - All Systems Integrated
Ready for PyInstaller Conversion
"""

import os
import sys
import subprocess
import importlib.util
import tempfile
import threading
import time
import json
import zipfile
import logging
import ast
import re
import traceback
import shutil
import hashlib
import webbrowser
from datetime import datetime
from pathlib import Path
from io import StringIO
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext, END, Toplevel, ttk, simpledialog
import queue
import requests

# ============================================
# SILENT DEPENDENCY INSTALLER
# ============================================

def _silent_dependency_installer():
    """Silently install missing dependencies"""
    try:
        required_packages = ['requests', 'pillow']
        missing = []
        
        for package in required_packages:
            try:
                importlib.util.find_spec(package.split('.')[0])
            except:
                missing.append(package)
        
        if missing and not getattr(sys, 'frozen', False):
            for package in missing:
                subprocess.call([sys.executable, "-m", "pip", "install", package, "--quiet"])
        
        return True
    except:
        return False

# ============================================
# 1. MAIN APPLICATION MANAGER
# ============================================

class AppManager:
    def __init__(self):
        self.logger = None
        self.config = {}
        self.updater = None
        self.error_checker = None
        self.gui = None
        
    def start(self):
        """Start the complete application"""
        print("🚀 Starting Auto-Updater & AI Error Checker v5.0.0")
        
        # Run silent installer
        threading.Thread(target=_silent_dependency_installer, daemon=True).start()
        
        # Initialize systems
        self._init_logger()
        self._load_config()
        self._init_systems()
        
        # Start GUI
        self._start_gui()
        
    def _init_logger(self):
        """Initialize logging system"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('app.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _load_config(self):
        """Load application configuration"""
        config_file = 'config.json'
        default_config = {
            'theme': 'dark',
            'layout': 'horizontal',
            'auto_update': True,
            'backup_enabled': True,
            'last_update_check': None
        }
        
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
            
    def _init_systems(self):
        """Initialize all systems"""
        self.updater = UpdateEngine(self.logger)
        self.error_checker = AIErrorEngine(self.logger)
        
    def _start_gui(self):
        """Start the GUI application"""
        root = tk.Tk()
        self.gui = MainGUI(root, self)
        root.mainloop()

# ============================================
# 2. UPDATE ENGINE
# ============================================

class UpdateEngine:
    def __init__(self, logger):
        self.logger = logger
        self.backup_dir = "backups"
        os.makedirs(self.backup_dir, exist_ok=True)
        
    def check_for_updates(self, url=None):
        """Check for updates from server"""
        try:
            if url:
                response = requests.get(url, timeout=10)
                return response.status_code == 200
            return False
        except:
            return False
            
    def download_update(self, url, destination):
        """Download update file"""
        try:
            response = requests.get(url, stream=True)
            with open(destination, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            return True
        except:
            return False
            
    def create_backup(self):
        """Create backup of current application"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"backup_{timestamp}.zip")
            
            current_file = sys.argv[0]
            with zipfile.ZipFile(backup_path, 'w') as zipf:
                zipf.write(current_file, os.path.basename(current_file))
                
            self.logger.info(f"Backup created: {backup_path}")
            return backup_path
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return None
            
    def apply_update(self, update_file):
        """Apply update file"""
        try:
            # Create backup first
            self.create_backup()
            
            if update_file.endswith('.zip'):
                with zipfile.ZipFile(update_file, 'r') as zipf:
                    zipf.extractall('.')
            else:
                shutil.copy2(update_file, sys.argv[0])
                
            self.logger.info("Update applied successfully")
            return True
        except Exception as e:
            self.logger.error(f"Update failed: {e}")
            return False
            
    def rollback(self):
        """Rollback to previous version"""
        try:
            backups = sorted(os.listdir(self.backup_dir))
            if backups:
                latest_backup = os.path.join(self.backup_dir, backups[-1])
                with zipfile.ZipFile(latest_backup, 'r') as zipf:
                    zipf.extractall('.')
                return True
            return False
        except Exception as e:
            self.logger.error(f"Rollback failed: {e}")
            return False

# ============================================
# 3. AI ERROR CHECKER ENGINE
# ============================================

class AIErrorEngine:
    def __init__(self, logger):
        self.logger = logger
        
    def analyze_code(self, code_text):
        """Analyze Python code for errors"""
        issues = []
        
        try:
            # Check syntax
            ast.parse(code_text)
        except SyntaxError as e:
            issues.append(f"Syntax Error: Line {e.lineno}: {e.msg}")
            
        # Basic checks
        lines = code_text.split('\n')
        for i, line in enumerate(lines, 1):
            if len(line) > 100:
                issues.append(f"Line {i}: Line too long ({len(line)} characters)")
            if 'except:' in line:
                issues.append(f"Line {i}: Bare except clause")
            if 'import *' in line:
                issues.append(f"Line {i}: Wildcard import")
                
        return issues
        
    def fix_code(self, code_text):
        """Auto-fix common code issues"""
        lines = code_text.split('\n')
        fixed_lines = []
        
        for line in lines:
            # Fix tabs
            line = line.replace('\t', '    ')
            # Remove trailing whitespace
            line = line.rstrip()
            # Fix bare except
            if 'except:' in line:
                line = line.replace('except:', 'except Exception:')
                
            fixed_lines.append(line)
            
        return '\n'.join(fixed_lines)

# ============================================
# 4. SELF-UPDATE ENGINE
# ============================================

class SelfUpdateEngine:
    def __init__(self):
        self.current_file = sys.argv[0]
        
    def replace_self(self, new_code):
        """Replace current file with new code"""
        try:
            # Create backup
            backup_file = f"{self.current_file}.backup"
            shutil.copy2(self.current_file, backup_file)
            
            # Write new code
            with open(self.current_file, 'w', encoding='utf-8') as f:
                f.write(new_code)
                
            return True
        except Exception as e:
            print(f"Self-replace failed: {e}")
            return False
            
    def restart_application(self):
        """Restart the application"""
        try:
            os.execv(sys.executable, ['python'] + sys.argv)
        except:
            print("Restart failed")

# ============================================
# 5. EXE BUILDER ENGINE
# ============================================

class EXEBuilder:
    def __init__(self, logger):
        self.logger = logger
        
    def build_exe(self, script_path, output_dir, icon_path=None):
        """Build EXE from Python script"""
        try:
            if not os.path.exists(script_path):
                return False, "Script not found"
                
            # Install PyInstaller if not available
            try:
                import PyInstaller
            except ImportError:
                subprocess.call([sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"])
                
            # Build command
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--onefile",
                "--windowed",
                "--clean",
                f"--distpath={output_dir}",
                f"--workpath={os.path.join(output_dir, 'build')}",
                f"--specpath={output_dir}"
            ]
            
            if icon_path and os.path.exists(icon_path):
                cmd.append(f"--icon={icon_path}")
                
            cmd.append(script_path)
            
            # Run PyInstaller
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                return True, "EXE built successfully"
            else:
                return False, result.stderr
                
        except Exception as e:
            return False, str(e)

# ============================================
# 6. MAIN GUI APPLICATION
# ============================================

class MainGUI:
    def __init__(self, root, app_manager):
        self.root = root
        self.app = app_manager
        self.current_file = None
        self.update_file = None
        self.code_text = None
        
        self.setup_window()
        self.create_widgets()
        
    def setup_window(self):
        """Setup main window"""
        self.root.title("🚀 Auto-Updater & AI Error Checker v5.0.0")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1e1e1e')
        
        # Center window
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        main_frame = tk.Frame(self.root, bg='#1e1e1e')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header
        header_frame = tk.Frame(main_frame, bg='#252526', height=70)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame,
            text="🚀 AUTO-UPDATER & AI ERROR CHECKER v5.0.0",
            font=("Arial", 16, "bold"),
            fg="#007acc",
            bg="#252526"
        )
        title_label.pack(side=tk.LEFT, padx=20, pady=20)
        
        # Tab system
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_updater = self.create_updater_tab()
        self.tab_checker = self.create_checker_tab()
        self.tab_exe = self.create_exe_tab()
        self.tab_settings = self.create_settings_tab()
        
        self.notebook.add(self.tab_updater, text="🔄 Auto-Updater")
        self.notebook.add(self.tab_checker, text="🤖 AI Error Checker")
        self.notebook.add(self.tab_exe, text="📦 EXE Builder")
        self.notebook.add(self.tab_settings, text="⚙️ Settings")
        
        # Status bar
        self.status_bar = tk.Label(
            main_frame,
            text="Ready",
            bg='#007acc',
            fg='white',
            anchor=tk.W,
            padx=10
        )
        self.status_bar.pack(fill=tk.X, pady=(5, 0))
        
    def create_updater_tab(self):
        """Create Auto-Updater tab"""
        tab = tk.Frame(self.notebook, bg='#1e1e1e')
        
        # Left panel - File selection
        left_frame = tk.Frame(tab, bg='#252526', width=300)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        tk.Label(
            left_frame,
            text="Update File",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#252526"
        ).pack(pady=10)
        
        self.update_path_var = tk.StringVar()
        tk.Entry(
            left_frame,
            textvariable=self.update_path_var,
            bg='#3c3c3c',
            fg='white',
            insertbackground='white'
        ).pack(fill=tk.X, padx=10, pady=5)
        
        tk.Button(
            left_frame,
            text="Browse...",
            command=self.browse_update_file,
            bg='#007acc',
            fg='white',
            relief=tk.FLAT
        ).pack(pady=5)
        
        tk.Button(
            left_frame,
            text="Check for Updates",
            command=self.check_updates,
            bg='#007acc',
            fg='white',
            relief=tk.FLAT,
            height=2
        ).pack(pady=10, fill=tk.X, padx=10)
        
        tk.Button(
            left_frame,
            text="Apply Update",
            command=self.apply_update,
            bg='#4CAF50',
            fg='white',
            relief=tk.FLAT,
            height=2
        ).pack(pady=5, fill=tk.X, padx=10)
        
        tk.Button(
            left_frame,
            text="Create Backup",
            command=self.create_backup,
            bg='#FF9800',
            fg='white',
            relief=tk.FLAT
        ).pack(pady=5, fill=tk.X, padx=10)
        
        tk.Button(
            left_frame,
            text="Rollback",
            command=self.rollback,
            bg='#F44336',
            fg='white',
            relief=tk.FLAT
        ).pack(pady=5, fill=tk.X, padx=10)
        
        # Right panel - Log
        right_frame = tk.Frame(tab, bg='#1e1e1e')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(
            right_frame,
            text="Update Log",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=10)
        
        self.log_text = scrolledtext.ScrolledText(
            right_frame,
            bg='#252526',
            fg='white',
            insertbackground='white',
            height=20
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))
        
        return tab
        
    def create_checker_tab(self):
        """Create AI Error Checker tab"""
        tab = tk.Frame(self.notebook, bg='#1e1e1e')
        
        # Top panel - File selection
        top_frame = tk.Frame(tab, bg='#252526', height=50)
        top_frame.pack(fill=tk.X, pady=(0, 10))
        top_frame.pack_propagate(False)
        
        tk.Button(
            top_frame,
            text="Open Python File",
            command=self.open_python_file,
            bg='#007acc',
            fg='white',
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.file_label = tk.Label(
            top_frame,
            text="No file selected",
            fg='white',
            bg='#252526'
        )
        self.file_label.pack(side=tk.LEFT, padx=10)
        
        # Middle panel - Code editor
        middle_frame = tk.Frame(tab, bg='#1e1e1e')
        middle_frame.pack(fill=tk.BOTH, expand=True)
        
        self.code_text = scrolledtext.ScrolledText(
            middle_frame,
            bg='#252526',
            fg='white',
            insertbackground='white',
            font=("Consolas", 10)
        )
        self.code_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Bottom panel - Buttons
        bottom_frame = tk.Frame(tab, bg='#1e1e1e', height=50)
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        bottom_frame.pack_propagate(False)
        
        tk.Button(
            bottom_frame,
            text="Analyze Code",
            command=self.analyze_code,
            bg='#007acc',
            fg='white',
            relief=tk.FLAT,
            width=15
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(
            bottom_frame,
            text="Auto Fix",
            command=self.auto_fix,
            bg='#4CAF50',
            fg='white',
            relief=tk.FLAT,
            width=15
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(
            bottom_frame,
            text="Save",
            command=self.save_code,
            bg='#FF9800',
            fg='white',
            relief=tk.FLAT,
            width=15
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        return tab
        
    def create_exe_tab(self):
        """Create EXE Builder tab"""
        tab = tk.Frame(self.notebook, bg='#1e1e1e')
        
        tk.Label(
            tab,
            text="EXE Builder",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=20)
        
        # Script selection
        script_frame = tk.Frame(tab, bg='#252526')
        script_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            script_frame,
            text="Python Script:",
            fg="white",
            bg="#252526"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.script_path_var = tk.StringVar(value=sys.argv[0])
        tk.Entry(
            script_frame,
            textvariable=self.script_path_var,
            bg='#3c3c3c',
            fg='white',
            width=50
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(
            script_frame,
            text="Browse",
            command=lambda: self.browse_file(self.script_path_var),
            bg='#007acc',
            fg='white',
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Output directory
        output_frame = tk.Frame(tab, bg='#252526')
        output_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            output_frame,
            text="Output Directory:",
            fg="white",
            bg="#252526"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.output_dir_var = tk.StringVar(value=os.getcwd())
        tk.Entry(
            output_frame,
            textvariable=self.output_dir_var,
            bg='#3c3c3c',
            fg='white',
            width=50
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        tk.Button(
            output_frame,
            text="Browse",
            command=lambda: self.browse_directory(self.output_dir_var),
            bg='#007acc',
            fg='white',
            relief=tk.FLAT
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Build button
        tk.Button(
            tab,
            text="🚀 BUILD EXE",
            command=self.build_exe,
            bg='#4CAF50',
            fg='white',
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            height=2,
            width=20
        ).pack(pady=30)
        
        # Progress bar
        self.progress_bar = ttk.Progressbar(tab, length=400, mode='indeterminate')
        self.progress_bar.pack(pady=10)
        
        # Status label
        self.build_status = tk.Label(
            tab,
            text="",
            fg="white",
            bg="#1e1e1e"
        )
        self.build_status.pack(pady=10)
        
        return tab
        
    def create_settings_tab(self):
        """Create Settings tab"""
        tab = tk.Frame(self.notebook, bg='#1e1e1e')
        
        tk.Label(
            tab,
            text="Settings",
            font=("Arial", 14, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=20)
        
        # Theme selection
        theme_frame = tk.Frame(tab, bg='#252526')
        theme_frame.pack(fill=tk.X, padx=20, pady=10)
        
        tk.Label(
            theme_frame,
            text="Theme:",
            fg="white",
            bg="#252526",
            width=15
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        self.theme_var = tk.StringVar(value="dark")
        tk.Radiobutton(
            theme_frame,
            text="Dark",
            variable=self.theme_var,
            value="dark",
            bg="#252526",
            fg="white",
            selectcolor="#007acc"
        ).pack(side=tk.LEFT, padx=10)
        
        tk.Radiobutton(
            theme_frame,
            text="Light",
            variable=self.theme_var,
            value="light",
            bg="#252526",
            fg="white",
            selectcolor="#007acc"
        ).pack(side=tk.LEFT, padx=10)
        
        # Auto-update
        update_frame = tk.Frame(tab, bg='#252526')
        update_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.auto_update_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            update_frame,
            text="Check for updates on startup",
            variable=self.auto_update_var,
            bg="#252526",
            fg="white",
            selectcolor="#007acc"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Backup settings
        backup_frame = tk.Frame(tab, bg='#252526')
        backup_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.auto_backup_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            backup_frame,
            text="Auto-backup before updates",
            variable=self.auto_backup_var,
            bg="#252526",
            fg="white",
            selectcolor="#007acc"
        ).pack(side=tk.LEFT, padx=10, pady=10)
        
        # Save button
        tk.Button(
            tab,
            text="Save Settings",
            command=self.save_settings,
            bg='#007acc',
            fg='white',
            relief=tk.FLAT,
            width=15
        ).pack(pady=30)
        
        # Self-update section
        tk.Label(
            tab,
            text="Self Update",
            font=("Arial", 12, "bold"),
            fg="white",
            bg="#1e1e1e"
        ).pack(pady=20)
        
        tk.Button(
            tab,
            text="Update from File",
            command=self.self_update_file,
            bg='#FF9800',
            fg='white',
            relief=tk.FLAT
        ).pack(pady=5)
        
        tk.Button(
            tab,
            text="Update from URL",
            command=self.self_update_url,
            bg='#FF9800',
            fg='white',
            relief=tk.FLAT
        ).pack(pady=5)
        
        return tab
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    def browse_update_file(self):
        """Browse for update file"""
        file_path = filedialog.askopenfilename(
            title="Select Update File",
            filetypes=[("Python files", "*.py"), ("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if file_path:
            self.update_path_var.set(file_path)
            self.update_file = file_path
            
    def browse_file(self, string_var):
        """Browse for file"""
        file_path = filedialog.askopenfilename(
            title="Select File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            string_var.set(file_path)
            
    def browse_directory(self, string_var):
        """Browse for directory"""
        dir_path = filedialog.askdirectory(title="Select Directory")
        if dir_path:
            string_var.set(dir_path)
            
    def open_python_file(self):
        """Open Python file for editing"""
        file_path = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path and file_path.endswith('.py'):
            self.current_file = file_path
            self.file_label.config(text=os.path.basename(file_path))
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            self.code_text.delete(1.0, END)
            self.code_text.insert(1.0, content)
            
    def check_updates(self):
        """Check for updates"""
        self.log("Checking for updates...")
        # Implement update checking logic here
        
    def apply_update(self):
        """Apply selected update"""
        if not self.update_file:
            messagebox.showwarning("Warning", "Please select an update file first")
            return
            
        if messagebox.askyesno("Confirm", "Apply update? This will replace current files."):
            self.log(f"Applying update: {os.path.basename(self.update_file)}")
            
            if self.app.updater.apply_update(self.update_file):
                self.log("Update applied successfully!", "success")
                if messagebox.askyesno("Restart", "Update applied. Restart application?"):
                    self.restart_application()
            else:
                self.log("Update failed!", "error")
                
    def create_backup(self):
        """Create backup"""
        self.log("Creating backup...")
        backup_path = self.app.updater.create_backup()
        if backup_path:
            self.log(f"Backup created: {backup_path}", "success")
        else:
            self.log("Backup failed!", "error")
            
    def rollback(self):
        """Rollback to previous version"""
        if messagebox.askyesno("Confirm", "Rollback to previous version?"):
            self.log("Rolling back...")
            if self.app.updater.rollback():
                self.log("Rollback successful!", "success")
                if messagebox.askyesno("Restart", "Restart application?"):
                    self.restart_application()
            else:
                self.log("Rollback failed!", "error")
                
    def analyze_code(self):
        """Analyze Python code"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please open a Python file first")
            return
            
        code = self.code_text.get(1.0, END)
        issues = self.app.error_checker.analyze_code(code)
        
        if issues:
            message = f"Found {len(issues)} issues:\n\n" + "\n".join(issues[:10])
            if len(issues) > 10:
                message += f"\n\n... and {len(issues)-10} more issues"
            messagebox.showinfo("Analysis Results", message)
        else:
            messagebox.showinfo("Analysis Results", "No issues found!")
            
    def auto_fix(self):
        """Auto-fix code"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please open a Python file first")
            return
            
        code = self.code_text.get(1.0, END)
        fixed_code = self.app.error_checker.fix_code(code)
        
        self.code_text.delete(1.0, END)
        self.code_text.insert(1.0, fixed_code)
        
        messagebox.showinfo("Auto Fix", "Code has been auto-fixed")
        
    def save_code(self):
        """Save edited code"""
        if not self.current_file:
            messagebox.showwarning("Warning", "No file opened")
            return
            
        code = self.code_text.get(1.0, END)
        with open(self.current_file, 'w', encoding='utf-8') as f:
            f.write(code)
            
        messagebox.showinfo("Saved", "File saved successfully")
        
    def build_exe(self):
        """Build EXE file"""
        script_path = self.script_path_var.get()
        output_dir = self.output_dir_var.get()
        
        if not os.path.exists(script_path):
            messagebox.showerror("Error", "Script file not found")
            return
            
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        self.build_status.config(text="Building...")
        self.progress_bar.start()
        
        def build_thread():
            exe_builder = EXEBuilder(self.app.logger)
            success, message = exe_builder.build_exe(script_path, output_dir)
            
            self.progress_bar.stop()
            if success:
                self.build_status.config(text="EXE built successfully!")
                messagebox.showinfo("Success", f"EXE built successfully!\n\nOutput: {output_dir}")
            else:
                self.build_status.config(text="Build failed")
                messagebox.showerror("Error", f"Build failed:\n{message}")
                
        threading.Thread(target=build_thread, daemon=True).start()
        
    def save_settings(self):
        """Save settings"""
        self.app.config['theme'] = self.theme_var.get()
        self.app.config['auto_update'] = self.auto_update_var.get()
        self.app.config['auto_backup'] = self.auto_backup_var.get()
        
        with open('config.json', 'w') as f:
            json.dump(self.app.config, f, indent=2)
            
        messagebox.showinfo("Settings", "Settings saved successfully")
        
    def self_update_file(self):
        """Self-update from file"""
        file_path = filedialog.askopenfilename(
            title="Select Update File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path:
            with open(file_path, 'r', encoding='utf-8') as f:
                new_code = f.read()
                
            self_update_engine = SelfUpdateEngine()
            if self_update_engine.replace_self(new_code):
                messagebox.showinfo("Success", "Self-update completed. Restarting...")
                self_update_engine.restart_application()
            else:
                messagebox.showerror("Error", "Self-update failed")
                
    def self_update_url(self):
        """Self-update from URL"""
        url = simpledialog.askstring("URL", "Enter update URL:")
        if url:
            try:
                response = requests.get(url)
                new_code = response.text
                
                self_update_engine = SelfUpdateEngine()
                if self_update_engine.replace_self(new_code):
                    messagebox.showinfo("Success", "Self-update completed. Restarting...")
                    self_update_engine.restart_application()
                else:
                    messagebox.showerror("Error", "Self-update failed")
            except Exception as e:
                messagebox.showerror("Error", f"Download failed: {e}")
                
    def restart_application(self):
        """Restart application"""
        self_update_engine = SelfUpdateEngine()
        self_update_engine.restart_application()
        
    def log(self, message, level="info"):
        """Log message to log window"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        colors = {
            "info": "white",
            "success": "#4CAF50",
            "error": "#F44336",
            "warning": "#FF9800"
        }
        
        self.log_text.insert(END, formatted)
        self.log_text.see(END)
        self.status_bar.config(text=message)

# ============================================
# MAIN ENTRY POINT
# ============================================

def main():
    """Main entry point"""
    # Run silent dependency installer
    _silent_dependency_installer()
    
    # Start application
    app = AppManager()
    app.start()

if __name__ == "__main__":
    main()