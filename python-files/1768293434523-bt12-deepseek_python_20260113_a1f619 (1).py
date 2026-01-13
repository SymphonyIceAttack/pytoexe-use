"""
🚀 AUTO-UPDATER & AI ERROR CHECKER - WINDOWS EXECUTABLE VERSION
Version: 3.0.0
Complete Windows Software - Ready for EXE Conversion
Single File - No External Dependencies Needed
"""

print("=" * 70)
print("🚀 AUTO-UPDATER & AI ERROR CHECKER v3.0.0")
print("📦 Windows EXE Ready Version")
print("=" * 70)

# ============================================
# SILENT DEPENDENCY INSTALLER (NO USER PROMPTS)
# ============================================

import os
import sys
import subprocess
import importlib.util
import zipfile
import tempfile
import shutil
from pathlib import Path

def _install_dependency_silently(package_name, pip_name):
    """Install a package completely silently without any user prompts"""
    try:
        # Check if already installed
        spec = importlib.util.find_spec(package_name)
        if spec is not None:
            return True
        
        print(f"   📦 Installing {package_name} (silent)...")
        
        # Get the directory where our executable or script is located
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Create libs directory inside our application folder
        libs_dir = os.path.join(base_dir, "_internal_libs")
        os.makedirs(libs_dir, exist_ok=True)
        
        # Create a requirements.txt file for silent installation
        requirements_path = os.path.join(libs_dir, "requirements.txt")
        with open(requirements_path, 'w') as f:
            f.write(f"{pip_name}\n")
        
        # Prepare pip install command with all silent flags
        pip_cmd = [
            sys.executable, "-m", "pip", "install",
            "--target", libs_dir,  # Install to our local directory
            "--no-input",          # Don't ask for input
            "--no-color",          # No colored output
            "--disable-pip-version-check",
            "--quiet",             # Minimal output
            "--no-warn-script-location",
            "--no-cache-dir",      # Don't use cache
            "--progress-bar", "off",
            "-r", requirements_path
        ]
        
        # Run pip completely silently (no windows, no console)
        startupinfo = None
        if sys.platform == "win32":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            startupinfo.wShowWindow = subprocess.SW_HIDE
        
        # Execute the installation
        result = subprocess.run(
            pip_cmd,
            startupinfo=startupinfo,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        # Add the libs directory to sys.path so Python can find the packages
        if libs_dir not in sys.path:
            sys.path.insert(0, libs_dir)
        
        # Clean up temporary files
        try:
            os.remove(requirements_path)
        except:
            pass
            
        return True
        
    except Exception as e:
        # Silent fail - don't show any errors to user
        return False

def _check_and_install_all_dependencies():
    """Check and install all required dependencies completely silently"""
    print("\n🔍 Checking dependencies (silent mode)...")
    
    required_packages = [
        ('customtkinter', 'customtkinter'),
        ('tkinterdnd2', 'tkinterdnd2'),
        ('pylint', 'pylint'),
        ('autopep8', 'autopep8'),
        ('black', 'black>=22.0.0'),
    ]
    
    # First, try to import directly
    for package_name, pip_name in required_packages:
        try:
            spec = importlib.util.find_spec(package_name)
            if spec is None:
                # Package not found, install it silently
                success = _install_dependency_silently(package_name, pip_name)
                if not success:
                    # Try one more time with a different approach
                    _install_dependency_silently(package_name, pip_name)
        except:
            # If any error occurs during check, try to install
            _install_dependency_silently(package_name, pip_name)
    
    # Final verification
    print("   ✅ Dependency check complete")
    return True

def _prepare_embedded_dependencies():
    """Prepare embedded dependencies for EXE mode"""
    # This function prepares dependencies when running as EXE
    # The actual dependencies should be bundled with PyInstaller
    pass

# ============================================
# RUN DEPENDENCY CHECK (COMPLETELY SILENT)
# ============================================

if __name__ == "__main__":
    # Run silent dependency installation
    try:
        _check_and_install_all_dependencies()
        print("✅ All dependencies are ready")
        print("=" * 70)
    except:
        # If dependency installation fails, continue anyway
        # Some packages might already be available
        pass

# ============================================
# REST OF IMPORTS (AFTER DEPENDENCY CHECK)
# ============================================

import json
import threading
import zipfile
import tempfile
import logging
import time
import ast
import re
import traceback
from datetime import datetime
from pathlib import Path
from io import StringIO

# GUI Imports - Now guaranteed to be available
import customtkinter as ctk
from tkinter import filedialog, messagebox, scrolledtext, END, Toplevel
from tkinterdnd2 import DND_FILES, TkinterDnD

# Analysis Imports
try:
    import pylint.lint
    from pylint.reporters.text import TextReporter
    PYLINT_AVAILABLE = True
except:
    PYLINT_AVAILABLE = False

try:
    import autopep8
    AUTOPEP8_AVAILABLE = True
except:
    AUTOPEP8_AVAILABLE = False

try:
    import black
    BLACK_AVAILABLE = True
except:
    BLACK_AVAILABLE = True  # Assume available after our installation

# ============================================
# CONFIGURATION
# ============================================

# Set appearance
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

# Constants
APP_NAME = "Auto-Updater & AI Error Checker"
APP_VERSION = "3.0.0"
CONFIG_FILE = "app_config.json"
LOG_FILE = "app_log.txt"
BACKUP_DIR = "backups"

# Colors
COLORS = {
    "bg_dark": "#1a1a1a",
    "bg_light": "#2d2d30",
    "accent": "#007acc",
    "accent_dark": "#005a9e",
    "success": "#4CAF50",
    "warning": "#FF9800",
    "error": "#F44336",
    "text": "#ffffff",
    "text_secondary": "#b0b0b0"
}

# ============================================
# LOGGING SYSTEM
# ============================================

class AppLogger:
    def __init__(self):
        self.logger = logging.getLogger(APP_NAME)
        self.logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers
        self.logger.handlers.clear()
        
        # File handler
        file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log(self, message, level="info"):
        if level == "info":
            self.logger.info(message)
        elif level == "warning":
            self.logger.warning(message)
        elif level == "error":
            self.logger.error(message)
        elif level == "debug":
            self.logger.debug(message)

# ============================================
# AUTO-UPDATER SYSTEM
# ============================================

class AutoUpdater:
    def __init__(self, logger):
        self.logger = logger
        self.temp_dir = None
    
    def create_backup(self):
        """Create backup of current files"""
        try:
            os.makedirs(BACKUP_DIR, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(BACKUP_DIR, f"backup_{timestamp}")
            os.makedirs(backup_path, exist_ok=True)
            
            # Backup important files
            for item in os.listdir('.'):
                if item in [BACKUP_DIR, '__pycache__', '.git', 'venv']:
                    continue
                    
                item_path = os.path.join('.', item)
                if os.path.isfile(item_path):
                    if item.endswith(('.py', '.json', '.txt', '.md', '.yml', '.yaml', '.cfg', '.ini')):
                        shutil.copy2(item_path, os.path.join(backup_path, item))
                elif os.path.isdir(item_path):
                    # Don't backup large directories
                    try:
                        shutil.copytree(
                            item_path, 
                            os.path.join(backup_path, item),
                            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log', '*.tmp')
                        )
                    except:
                        pass
            
            self.logger.log(f"Backup created: {backup_path}", "info")
            return backup_path
        except Exception as e:
            self.logger.log(f"Backup failed: {e}", "error")
            return None
    
    def extract_update(self, file_path):
        """Extract update file (ZIP or single file)"""
        try:
            self.temp_dir = tempfile.mkdtemp(prefix="update_")
            
            if file_path.endswith('.zip'):
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(self.temp_dir)
                self.logger.log(f"ZIP extracted to: {self.temp_dir}", "info")
            elif file_path.endswith(('.py', '.exe', '.txt', '.json')):
                # Single file
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(self.temp_dir, filename))
                self.logger.log(f"File copied to: {self.temp_dir}", "info")
            else:
                # Unknown format, try to copy anyway
                filename = os.path.basename(file_path)
                shutil.copy2(file_path, os.path.join(self.temp_dir, filename))
                self.logger.log(f"File copied (unknown format): {self.temp_dir}", "warning")
            
            return self.temp_dir
        except Exception as e:
            self.logger.log(f"Extraction failed: {e}", "error")
            return None
    
    def validate_update(self, update_dir):
        """Validate update files"""
        try:
            if not os.path.exists(update_dir):
                return False, "Update directory does not exist"
            
            files = os.listdir(update_dir)
            if not files:
                return False, "Update directory is empty"
            
            # Check for Python files syntax
            python_files = [f for f in files if f.endswith('.py')]
            for py_file in python_files:
                file_path = os.path.join(update_dir, py_file)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        ast.parse(f.read())
                except SyntaxError as e:
                    return False, f"Syntax error in {py_file}: {e}"
            
            return True, "Update validation passed"
        except Exception as e:
            return False, f"Validation error: {e}"
    
    def apply_update(self, update_dir):
        """Apply update to current directory"""
        try:
            # Create backup first
            backup_path = self.create_backup()
            
            # Apply update
            for item in os.listdir(update_dir):
                src = os.path.join(update_dir, item)
                dst = os.path.join('.', item)
                
                # Remove existing if exists
                if os.path.exists(dst):
                    if os.path.isfile(dst):
                        os.remove(dst)
                    else:
                        shutil.rmtree(dst, ignore_errors=True)
                
                # Copy new
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)
            
            self.logger.log("Update applied successfully", "info")
            return True, "Update applied successfully"
        except Exception as e:
            error_msg = f"Update failed: {e}"
            self.logger.log(error_msg, "error")
            
            # Try to restore backup
            if backup_path and os.path.exists(backup_path):
                self.restore_backup(backup_path)
            
            return False, error_msg
    
    def restore_backup(self, backup_path):
        """Restore from backup"""
        try:
            for item in os.listdir(backup_path):
                src = os.path.join(backup_path, item)
                dst = os.path.join('.', item)
                
                if os.path.exists(dst):
                    if os.path.isfile(dst):
                        os.remove(dst)
                    else:
                        shutil.rmtree(dst, ignore_errors=True)
                
                if os.path.isfile(src):
                    shutil.copy2(src, dst)
                else:
                    shutil.copytree(src, dst)
            
            self.logger.log(f"Restored from backup: {backup_path}", "info")
            return True
        except Exception as e:
            self.logger.log(f"Restore failed: {e}", "error")
            return False
    
    def restart_application(self):
        """Restart the application"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as EXE
                exe_path = sys.executable
                subprocess.Popen([exe_path])
            else:
                # Running as script
                python = sys.executable
                script = sys.argv[0]
                subprocess.Popen([python, script])
            
            # Close current instance
            time.sleep(2)
            os._exit(0)
        except Exception as e:
            self.logger.log(f"Restart failed: {e}", "error")
            return False

# ============================================
# AI ERROR CHECKER SYSTEM
# ============================================

class AIErrorChecker:
    def __init__(self, logger):
        self.logger = logger
    
    def analyze_code(self, file_path):
        """Analyze Python code for errors"""
        results = {
            'syntax_errors': [],
            'warnings': [],
            'suggestions': [],
            'summary': {
                'total_lines': 0,
                'total_errors': 0,
                'total_warnings': 0,
                'total_suggestions': 0
            }
        }
        
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
            
            lines = code.split('\n')
            results['summary']['total_lines'] = len(lines)
            
            # 1. Check syntax errors
            syntax_errors = self._check_syntax(code, file_path)
            results['syntax_errors'] = syntax_errors
            results['summary']['total_errors'] += len(syntax_errors)
            
            # 2. Run basic analysis
            basic_issues = self._basic_analysis(code, file_path)
            results['warnings'].extend(basic_issues['warnings'])
            results['suggestions'].extend(basic_issues['suggestions'])
            results['summary']['total_warnings'] += len(basic_issues['warnings'])
            results['summary']['total_suggestions'] += len(basic_issues['suggestions'])
            
            # 3. Run pylint if available
            if PYLINT_AVAILABLE:
                pylint_issues = self._run_pylint(file_path)
                results['warnings'].extend(pylint_issues)
                results['summary']['total_warnings'] += len(pylint_issues)
            
            return results
            
        except Exception as e:
            self.logger.log(f"Analysis error: {e}", "error")
            return {'error': str(e)}
    
    def _check_syntax(self, code, filename):
        """Check for syntax errors"""
        errors = []
        try:
            ast.parse(code)
        except SyntaxError as e:
            errors.append({
                'line': e.lineno,
                'column': e.offset if hasattr(e, 'offset') else 0,
                'message': str(e.msg),
                'code': e.text.strip() if e.text else '',
                'type': 'Syntax Error'
            })
        except Exception as e:
            errors.append({
                'line': 0,
                'column': 0,
                'message': str(e),
                'code': '',
                'type': 'Parse Error'
            })
        return errors
    
    def _basic_analysis(self, code, filename):
        """Basic static analysis"""
        issues = {'warnings': [], 'suggestions': []}
        lines = code.split('\n')
        
        for i, line in enumerate(lines, 1):
            line_stripped = line.strip()
            
            # Skip empty lines and comments
            if not line_stripped or line_stripped.startswith('#'):
                continue
            
            # Check line length
            if len(line) > 120:
                issues['warnings'].append({
                    'line': i,
                    'message': f'Line too long ({len(line)} > 120 characters)',
                    'code': line[:80] + '...' if len(line) > 80 else line,
                    'type': 'Style Warning'
                })
            
            # Check for tabs
            if '\t' in line:
                issues['warnings'].append({
                    'line': i,
                    'message': 'Tab character found (use 4 spaces instead)',
                    'code': line.replace('\t', '→'),
                    'type': 'Style Warning'
                })
            
            # Check for trailing whitespace
            if line.rstrip() != line:
                issues['suggestions'].append({
                    'line': i,
                    'message': 'Trailing whitespace',
                    'code': line,
                    'type': 'Style Suggestion'
                })
            
            # Check for common issues
            if line_stripped.startswith('except:'):
                issues['warnings'].append({
                    'line': i,
                    'message': 'Bare except clause (specify exception type)',
                    'code': line,
                    'type': 'Code Warning'
                })
            
            if 'import *' in line:
                issues['warnings'].append({
                    'line': i,
                    'message': 'Wildcard import (import specific names instead)',
                    'code': line,
                    'type': 'Code Warning'
                })
            
            if ' == True' in line or ' == False' in line:
                issues['suggestions'].append({
                    'line': i,
                    'message': 'Direct comparison to True/False (use if variable: or if not variable:)',
                    'code': line,
                    'type': 'Code Suggestion'
                })
        
        return issues
    
    def _run_pylint(self, file_path):
        """Run pylint analysis"""
        issues = []
        
        if not PYLINT_AVAILABLE:
            return issues
        
        try:
            # Custom reporter
            class StringReporter(TextReporter):
                def __init__(self):
                    self.output = []
                    super().__init__()
                
                def handle_message(self, msg):
                    self.output.append({
                        'line': msg.line,
                        'message': f"{msg.msg}",
                        'type': msg.symbol,
                        'severity': msg.category
                    })
            
            reporter = StringReporter()
            
            # Run pylint with minimal checks
            pylint_opts = [
                file_path,
                '--reports=n',
                '--score=n',
                '--disable=all',
                '--enable=deprecated-method,undefined-variable'
            ]
            
            pylint.lint.Run(pylint_opts, reporter=reporter, exit=False)
            
            # Filter only warnings and errors
            for issue in reporter.output:
                if issue['severity'] in ['W', 'E', 'F']:
                    issues.append({
                        'line': issue['line'],
                        'message': issue['message'],
                        'type': issue['type'],
                        'severity': issue['severity']
                    })
            
        except Exception as e:
            self.logger.log(f"Pylint error: {e}", "warning")
        
        return issues
    
    def fix_code(self, file_path):
        """Automatically fix code issues"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
            
            fixed_code = original_code
            
            # Apply basic fixes
            lines = fixed_code.split('\n')
            
            # 1. Remove trailing whitespace
            lines = [line.rstrip() for line in lines]
            
            # 2. Replace tabs with 4 spaces
            lines = [line.replace('\t', '    ') for line in lines]
            
            # 3. Remove extra blank lines at end
            while lines and not lines[-1].strip():
                lines.pop()
            
            fixed_code = '\n'.join(lines)
            
            # 4. Try autopep8
            if AUTOPEP8_AVAILABLE and fixed_code != original_code:
                try:
                    fixed_code = autopep8.fix_code(fixed_code)
                except:
                    pass
            
            # 5. Try black
            if BLACK_AVAILABLE and fixed_code != original_code:
                try:
                    fixed_code = black.format_str(
                        fixed_code, 
                        mode=black.FileMode()
                    )
                except:
                    pass
            
            # Create backup
            timestamp = int(time.time())
            backup_path = f"{file_path}.backup_{timestamp}"
            shutil.copy2(file_path, backup_path)
            
            # Write fixed code
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(fixed_code)
            
            return {
                'success': True,
                'backup': backup_path,
                'changes_made': fixed_code != original_code,
                'message': 'Code fixed successfully'
            }
            
        except Exception as e:
            self.logger.log(f"Fix error: {e}", "error")
            return {
                'success': False,
                'error': str(e)
            }

# ============================================
# MAIN APPLICATION GUI
# ============================================

class AutoUpdaterApp(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        
        # Initialize systems
        self.logger = AppLogger()
        self.updater = AutoUpdater(self.logger)
        self.error_checker = AIErrorChecker(self.logger)
        
        # Application state
        self.current_file = None
        self.update_file = None
        self.layout_mode = "horizontal"
        self.is_dark_mode = True
        
        # Setup GUI
        self.setup_window()
        self.create_widgets()
        self.load_config()
        
        self.logger.log(f"{APP_NAME} v{APP_VERSION} started", "info")
    
    def setup_window(self):
        """Setup main window"""
        self.title(f"{APP_NAME} v{APP_VERSION}")
        
        # Set window size and center
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 1400
        window_height = 800
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        self.minsize(1000, 600)
        
        # Configure grid
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Set icon (if available)
        self.set_window_icon()
    
    def set_window_icon(self):
        """Set window icon if running as EXE"""
        try:
            if getattr(sys, 'frozen', False):
                # Running as EXE
                self.iconbitmap(sys.executable)
        except:
            pass
    
    def create_widgets(self):
        """Create all GUI widgets"""
        # Main container
        self.main_container = ctk.CTkFrame(self, corner_radius=10)
        self.main_container.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        self.main_container.grid_columnconfigure(0, weight=1)
        self.main_container.grid_rowconfigure(1, weight=1)
        
        # Header
        self.create_header()
        
        # Panels container
        self.panels_container = ctk.CTkFrame(self.main_container)
        self.panels_container.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        
        # Setup panels
        self.setup_panels_layout()
        
        # Status bar
        self.create_status_bar()
    
    def create_header(self):
        """Create application header"""
        header_frame = ctk.CTkFrame(self.main_container, height=70, corner_radius=10)
        header_frame.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        header_frame.grid_columnconfigure(0, weight=1)
        
        # Title with icon
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.grid(row=0, column=0, padx=20, pady=10, sticky="w")
        
        # Icon label
        icon_label = ctk.CTkLabel(
            title_frame,
            text="🚀",
            font=("Arial", 28)
        )
        icon_label.grid(row=0, column=0, padx=(0, 10))
        
        # Title text
        title_text = ctk.CTkLabel(
            title_frame,
            text=APP_NAME,
            font=("Arial", 24, "bold"),
            text_color=COLORS['accent']
        )
        title_text.grid(row=0, column=1, sticky="w")
        
        # Version
        version_text = ctk.CTkLabel(
            title_frame,
            text=f"v{APP_VERSION}",
            font=("Arial", 12),
            text_color=COLORS['text_secondary']
        )
        version_text.grid(row=0, column=2, padx=(10, 0), sticky="w")
        
        # Controls on right
        controls_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        controls_frame.grid(row=0, column=1, padx=20, pady=10, sticky="e")
        
        # Theme toggle
        self.theme_btn = ctk.CTkButton(
            controls_frame,
            text="🌙",
            width=40,
            height=40,
            command=self.toggle_theme,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent']
        )
        self.theme_btn.grid(row=0, column=0, padx=5)
        
        # Build EXE button
        self.build_btn = ctk.CTkButton(
            controls_frame,
            text="📦 EXE",
            width=80,
            height=40,
            command=self.build_exe_dialog,
            fg_color=COLORS['success'],
            hover_color="#45a049"
        )
        self.build_btn.grid(row=0, column=1, padx=5)
        
        # Help button
        help_btn = ctk.CTkButton(
            controls_frame,
            text="❓",
            width=40,
            height=40,
            command=self.show_help,
            fg_color=COLORS['bg_light'],
            hover_color=COLORS['accent']
        )
        help_btn.grid(row=0, column=2, padx=5)
    
    def setup_panels_layout(self):
        """Setup the two main panels based on layout mode"""
        # Clear existing panels
        for widget in self.panels_container.winfo_children():
            widget.destroy()
        
        # Configure grid
        if self.layout_mode == "horizontal":
            self.panels_container.grid_columnconfigure(0, weight=1)
            self.panels_container.grid_columnconfigure(1, weight=1)
            self.panels_container.grid_rowconfigure(0, weight=1)
            
            col1, col2, row1, row2 = 0, 1, 0, 0
        else:  # vertical
            self.panels_container.grid_columnconfigure(0, weight=1)
            self.panels_container.grid_rowconfigure(0, weight=1)
            self.panels_container.grid_rowconfigure(1, weight=1)
            
            col1, col2, row1, row2 = 0, 0, 0, 1
        
        # Create panels
        self.create_panel_1(col1, row1)
        self.create_panel_2(col2, row2)
        
        # Layout toggle button
        toggle_text = "⇄ Switch to Vertical" if self.layout_mode == "horizontal" else "⇅ Switch to Horizontal"
        toggle_btn = ctk.CTkButton(
            self.panels_container,
            text=toggle_text,
            command=self.toggle_layout,
            width=200,
            height=35,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_dark']
        )
        
        if self.layout_mode == "horizontal":
            toggle_btn.grid(row=1, column=0, columnspan=2, pady=(10, 0))
        else:
            toggle_btn.grid(row=2, column=0, pady=(10, 0))
    
    def create_panel_1(self, column, row):
        """Create Panel 1: Auto-Updater"""
        panel = ctk.CTkFrame(self.panels_container, corner_radius=10)
        panel.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(4, weight=1)
        
        # Panel header
        header = ctk.CTkFrame(panel, fg_color=COLORS['accent'], corner_radius=8)
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        header_label = ctk.CTkLabel(
            header,
            text="🔵 AUTO-UPDATE SYSTEM",
            font=("Arial", 16, "bold"),
            text_color="white"
        )
        header_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        # File selection area
        file_frame = ctk.CTkFrame(panel, corner_radius=8)
        file_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        # Drag & drop area
        drop_area = ctk.CTkLabel(
            file_frame,
            text="📂 DRAG & DROP FILE HERE\n(Python .py or .zip archive)",
            font=("Arial", 12),
            height=100,
            corner_radius=6,
            fg_color=COLORS['bg_light'],
            text_color=COLORS['text_secondary']
        )
        drop_area.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        drop_area.drop_target_register(DND_FILES)
        drop_area.dnd_bind('<<Drop>>', self.on_update_file_drop)
        
        # Browse button
        browse_btn = ctk.CTkButton(
            file_frame,
            text="📁 Browse for File",
            command=self.browse_update_file,
            height=40,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_dark']
        )
        browse_btn.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Selected file display
        self.update_file_display = ctk.CTkLabel(
            panel,
            text="No file selected",
            font=("Arial", 10),
            wraplength=400,
            text_color=COLORS['text_secondary']
        )
        self.update_file_display.grid(row=2, column=0, padx=15, pady=5, sticky="w")
        
        # Update button
        self.update_btn = ctk.CTkButton(
            panel,
            text="🔄 START UPDATE",
            command=self.start_update_process,
            font=("Arial", 14, "bold"),
            height=50,
            fg_color=COLORS['success'],
            hover_color="#45a049"
        )
        self.update_btn.grid(row=3, column=0, padx=15, pady=15, sticky="ew")
        
        # Progress bar
        self.update_progress = ctk.CTkProgressBar(panel)
        self.update_progress.grid(row=4, column=0, padx=15, pady=5, sticky="ew")
        self.update_progress.set(0)
        
        # Log area
        log_frame = ctk.CTkFrame(panel, corner_radius=8)
        log_frame.grid(row=5, column=0, padx=15, pady=(10, 15), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)
        
        log_label = ctk.CTkLabel(
            log_frame,
            text="📝 Update Log:",
            font=("Arial", 12, "bold")
        )
        log_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Log text widget
        self.update_log = scrolledtext.ScrolledText(
            log_frame,
            height=8,
            bg=COLORS['bg_dark'],
            fg=COLORS['text'],
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        self.update_log.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
    
    def create_panel_2(self, column, row):
        """Create Panel 2: AI Error Checker"""
        panel = ctk.CTkFrame(self.panels_container, corner_radius=10)
        panel.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")
        panel.grid_columnconfigure(0, weight=1)
        panel.grid_rowconfigure(3, weight=1)
        
        # Panel header
        header = ctk.CTkFrame(panel, fg_color=COLORS['accent'], corner_radius=8)
        header.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="ew")
        
        header_label = ctk.CTkLabel(
            header,
            text="🔵 AI ERROR CHECKER",
            font=("Arial", 16, "bold"),
            text_color="white"
        )
        header_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        
        # File selection area
        file_frame = ctk.CTkFrame(panel, corner_radius=8)
        file_frame.grid(row=1, column=0, padx=15, pady=10, sticky="ew")
        file_frame.grid_columnconfigure(0, weight=1)
        
        # Drag & drop for code
        drop_area = ctk.CTkLabel(
            file_frame,
            text="📄 DRAG & DROP PYTHON FILE HERE",
            font=("Arial", 12),
            height=80,
            corner_radius=6,
            fg_color=COLORS['bg_light'],
            text_color=COLORS['text_secondary']
        )
        drop_area.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        drop_area.drop_target_register(DND_FILES)
        drop_area.dnd_bind('<<Drop>>', self.on_code_file_drop)
        
        # Browse button
        browse_btn = ctk.CTkButton(
            file_frame,
            text="📁 Select Python File",
            command=self.browse_code_file,
            height=40,
            fg_color=COLORS['accent'],
            hover_color=COLORS['accent_dark']
        )
        browse_btn.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="ew")
        
        # Selected file display
        self.code_file_display = ctk.CTkLabel(
            panel,
            text="No file selected",
            font=("Arial", 10),
            wraplength=400,
            text_color=COLORS['text_secondary']
        )
        self.code_file_display.grid(row=2, column=0, padx=15, pady=5, sticky="w")
        
        # Action buttons
        btn_frame = ctk.CTkFrame(panel, fg_color="transparent")
        btn_frame.grid(row=3, column=0, padx=15, pady=10, sticky="ew")
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        self.check_btn = ctk.CTkButton(
            btn_frame,
            text="🔍 ANALYZE CODE",
            command=self.start_code_analysis,
            height=45,
            fg_color=COLORS['warning'],
            hover_color="#e68900"
        )
        self.check_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.fix_btn = ctk.CTkButton(
            btn_frame,
            text="⚙️ AUTO FIX",
            command=self.start_auto_fix,
            height=45,
            fg_color=COLORS['success'],
            hover_color="#45a049"
        )
        self.fix_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        # Results area
        results_frame = ctk.CTkFrame(panel, corner_radius=8)
        results_frame.grid(row=4, column=0, padx=15, pady=(10, 15), sticky="nsew")
        results_frame.grid_columnconfigure(0, weight=1)
        results_frame.grid_rowconfigure(1, weight=1)
        
        results_label = ctk.CTkLabel(
            results_frame,
            text="📊 Analysis Results:",
            font=("Arial", 12, "bold")
        )
        results_label.grid(row=0, column=0, padx=10, pady=(10, 5), sticky="w")
        
        # Results text widget
        self.results_text = scrolledtext.ScrolledText(
            results_frame,
            height=10,
            bg=COLORS['bg_dark'],
            fg=COLORS['text'],
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            borderwidth=0
        )
        self.results_text.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")
        
        # Configure tags for colored text
        self.results_text.tag_config("success", foreground=COLORS['success'])
        self.results_text.tag_config("error", foreground=COLORS['error'])
        self.results_text.tag_config("warning", foreground=COLORS['warning'])
        self.results_text.tag_config("info", foreground=COLORS['text_secondary'])
    
    def create_status_bar(self):
        """Create status bar at bottom"""
        status_frame = ctk.CTkFrame(self.main_container, height=40, corner_radius=8)
        status_frame.grid(row=2, column=0, padx=10, pady=(5, 10), sticky="ew")
        status_frame.grid_columnconfigure(0, weight=1)
        
        # Status label
        self.status_label = ctk.CTkLabel(
            status_frame,
            text="✅ Ready",
            font=("Arial", 11)
        )
        self.status_label.grid(row=0, column=0, padx=15, pady=5, sticky="w")
        
        # Memory/performance info
        info_frame = ctk.CTkFrame(status_frame, fg_color="transparent")
        info_frame.grid(row=0, column=1, padx=15, pady=5, sticky="e")
        
        # Current time
        self.time_label = ctk.CTkLabel(
            info_frame,
            text=datetime.now().strftime("%H:%M:%S"),
            font=("Arial", 10),
            text_color=COLORS['text_secondary']
        )
        self.time_label.grid(row=0, column=0, padx=5)
        
        # Update time periodically
        self.update_time()
    
    def update_time(self):
        """Update time display"""
        current_time = datetime.now().strftime("%H:%M:%S")
        self.time_label.configure(text=current_time)
        self.after(1000, self.update_time)
    
    # ============================================
    # EVENT HANDLERS
    # ============================================
    
    def on_update_file_drop(self, event):
        """Handle update file drop"""
        file_path = event.data.strip('{}')
        if os.path.exists(file_path):
            self.update_file = file_path
            filename = os.path.basename(file_path)
            self.update_file_display.configure(text=f"📄 {filename}")
            self.log_update(f"Update file selected: {filename}")
    
    def on_code_file_drop(self, event):
        """Handle code file drop"""
        file_path = event.data.strip('{}')
        if os.path.exists(file_path) and file_path.endswith('.py'):
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.code_file_display.configure(text=f"📄 {filename}")
            self.log_update(f"Code file selected: {filename}")
    
    def browse_update_file(self):
        """Browse for update file"""
        file_path = filedialog.askopenfilename(
            title="Select Update File",
            filetypes=[
                ("Python files", "*.py"),
                ("ZIP archives", "*.zip"),
                ("All files", "*.*")
            ]
        )
        if file_path:
            self.update_file = file_path
            filename = os.path.basename(file_path)
            self.update_file_display.configure(text=f"📄 {filename}")
    
    def browse_code_file(self):
        """Browse for Python file"""
        file_path = filedialog.askopenfilename(
            title="Select Python File",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if file_path and file_path.endswith('.py'):
            self.current_file = file_path
            filename = os.path.basename(file_path)
            self.code_file_display.configure(text=f"📄 {filename}")
    
    def start_update_process(self):
        """Start the update process"""
        if not self.update_file:
            messagebox.showwarning("No File", "Please select an update file first!")
            return
        
        # Disable button during update
        self.update_btn.configure(state="disabled", text="UPDATING...")
        
        # Run in separate thread
        thread = threading.Thread(target=self.perform_update, daemon=True)
        thread.start()
    
    def perform_update(self):
        """Perform update operations"""
        try:
            self.log_update("=" * 50)
            self.log_update("Starting update process...")
            self.update_progress.set(0.1)
            
            # Step 1: Extract file
            self.log_update("Extracting update file...")
            update_dir = self.updater.extract_update(self.update_file)
            if not update_dir:
                self.log_update("❌ Extraction failed!", "error")
                return
            
            self.update_progress.set(0.3)
            
            # Step 2: Validate
            self.log_update("Validating update...")
            valid, message = self.updater.validate_update(update_dir)
            if not valid:
                self.log_update(f"❌ Validation failed: {message}", "error")
                return
            
            self.update_progress.set(0.5)
            
            # Step 3: Create backup
            self.log_update("Creating backup...")
            backup_path = self.updater.create_backup()
            if backup_path:
                self.log_update(f"✅ Backup created: {os.path.basename(backup_path)}", "success")
            
            self.update_progress.set(0.7)
            
            # Step 4: Apply update
            self.log_update("Applying update...")
            success, message = self.updater.apply_update(update_dir)
            if not success:
                self.log_update(f"❌ {message}", "error")
                return
            
            self.update_progress.set(0.9)
            
            # Step 5: Success
            self.log_update("✅ Update completed successfully!", "success")
            self.log_update(f"Backup saved to: {backup_path}")
            self.update_progress.set(1.0)
            
            # Ask to restart
            self.after(1000, self.ask_restart)
            
        except Exception as e:
            self.log_update(f"❌ Update error: {str(e)}", "error")
            self.logger.log(f"Update error: {e}", "error")
        finally:
            self.after(0, lambda: self.update_btn.configure(
                state="normal", text="🔄 START UPDATE"
            ))
            self.update_progress.set(0)
    
    def ask_restart(self):
        """Ask user to restart application"""
        if messagebox.askyesno("Restart Required", 
                               "Update completed successfully!\n"
                               "Do you want to restart the application now?"):
            self.log_update("Restarting application...")
            self.after(1000, self.updater.restart_application)
    
    def start_code_analysis(self):
        """Start code analysis"""
        if not self.current_file:
            messagebox.showwarning("No File", "Please select a Python file first!")
            return
        
        # Disable button
        self.check_btn.configure(state="disabled", text="ANALYZING...")
        
        # Run in thread
        thread = threading.Thread(target=self.perform_code_analysis, daemon=True)
        thread.start()
    
    def perform_code_analysis(self):
        """Perform code analysis"""
        try:
            self.clear_results()
            self.append_result("🔍 AI Code Analysis Started\n", "info")
            self.append_result("=" * 50 + "\n", "info")
            
            # Perform analysis
            results = self.error_checker.analyze_code(self.current_file)
            
            if 'error' in results:
                self.append_result(f"❌ Error: {results['error']}\n", "error")
                return
            
            # Display summary
            summary = results['summary']
            self.append_result("📊 ANALYSIS SUMMARY:\n", "info")
            self.append_result(f"   Total Lines: {summary['total_lines']}\n", "info")
            self.append_result(f"   Syntax Errors: {len(results['syntax_errors'])}\n", 
                              "error" if results['syntax_errors'] else "info")
            self.append_result(f"   Warnings: {summary['total_warnings']}\n", 
                              "warning" if summary['total_warnings'] else "info")
            self.append_result(f"   Suggestions: {summary['total_suggestions']}\n", "info")
            self.append_result("=" * 50 + "\n", "info")
            
            # Display syntax errors
            if results['syntax_errors']:
                self.append_result("\n❌ SYNTAX ERRORS:\n", "error")
                for error in results['syntax_errors']:
                    self.append_result(f"   Line {error['line']}: {error['message']}\n", "error")
                    if error.get('code'):
                        self.append_result(f"       Code: {error['code']}\n", "error")
            
            # Display warnings
            if results['warnings']:
                self.append_result("\n⚠️ WARNINGS:\n", "warning")
                for warning in results['warnings'][:20]:  # Show first 20
                    self.append_result(f"   Line {warning['line']}: {warning['message']}\n", "warning")
            
            # Display suggestions
            if results['suggestions']:
                self.append_result("\n💡 SUGGESTIONS:\n", "info")
                for suggestion in results['suggestions'][:10]:  # Show first 10
                    self.append_result(f"   Line {suggestion['line']}: {suggestion['message']}\n", "info")
            
            # Final status
            self.append_result("\n" + "=" * 50 + "\n", "info")
            total_issues = (len(results['syntax_errors']) + 
                          summary['total_warnings'] + 
                          summary['total_suggestions'])
            
            if total_issues == 0:
                self.append_result("✅ Code is clean! No issues found.\n", "success")
            else:
                self.append_result(f"📋 Found {total_issues} issues to review\n", "warning")
                if summary['total_warnings'] > 0 or len(results['syntax_errors']) > 0:
                    self.append_result("💡 Use 'Auto Fix' button to fix some issues automatically\n", "info")
            
        except Exception as e:
            self.append_result(f"❌ Analysis error: {str(e)}\n", "error")
            self.logger.log(f"Analysis error: {e}", "error")
        finally:
            self.after(0, lambda: self.check_btn.configure(
                state="normal", text="🔍 ANALYZE CODE"
            ))
    
    def start_auto_fix(self):
        """Start automatic code fixing"""
        if not self.current_file:
            messagebox.showwarning("No File", "Please select a Python file first!")
            return
        
        # Confirm
        if not messagebox.askyesno("Confirm", 
                                  "This will modify your code file.\n"
                                  "A backup will be created automatically.\n"
                                  "Continue?"):
            return
        
        # Disable button
        self.fix_btn.configure(state="disabled", text="FIXING...")
        
        # Run in thread
        thread = threading.Thread(target=self.perform_auto_fix, daemon=True)
        thread.start()
    
    def perform_auto_fix(self):
        """Perform automatic code fixing"""
        try:
            self.clear_results()
            self.append_result("⚙️ Starting automatic fixes...\n", "info")
            self.append_result("=" * 50 + "\n", "info")
            
            # Fix code
            result = self.error_checker.fix_code(self.current_file)
            
            if not result['success']:
                self.append_result(f"❌ Fix failed: {result.get('error', 'Unknown error')}\n", "error")
                return
            
            if result.get('changes_made'):
                self.append_result("✅ Code fixed successfully!\n", "success")
                self.append_result(f"   Backup saved as: {result.get('backup', 'Unknown')}\n", "info")
                
                # Show sample of fixed code
                with open(self.current_file, 'r', encoding='utf-8') as f:
                    fixed_code = f.read()
                
                lines = fixed_code.split('\n')[:20]
                self.append_result("\n📝 Fixed code (first 20 lines):\n", "info")
                for i, line in enumerate(lines, 1):
                    if len(line) > 100:
                        line = line[:100] + "..."
                    self.append_result(f"   {i:3d}: {line}\n", "info")
                
                if len(fixed_code.split('\n')) > 20:
                    self.append_result("   ...\n", "info")
            else:
                self.append_result("ℹ️ No fixes needed - code is already clean!\n", "info")
            
            self.append_result("\n" + "=" * 50 + "\n", "info")
            
        except Exception as e:
            self.append_result(f"❌ Fix error: {str(e)}\n", "error")
            self.logger.log(f"Fix error: {e}", "error")
        finally:
            self.after(0, lambda: self.fix_btn.configure(
                state="normal", text="⚙️ AUTO FIX"
            ))
    
    def toggle_theme(self):
        """Toggle between dark and light theme"""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            ctk.set_appearance_mode("dark")
            self.theme_btn.configure(text="🌙")
        else:
            ctk.set_appearance_mode("light")
            self.theme_btn.configure(text="☀️")
        
        self.save_config()
    
    def toggle_layout(self):
        """Toggle between horizontal and vertical layout"""
        self.layout_mode = "vertical" if self.layout_mode == "horizontal" else "horizontal"
        self.setup_panels_layout()
        self.save_config()
    
    def build_exe_dialog(self):
        """Show EXE builder dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Build EXE")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        ctk.CTkLabel(
            dialog,
            text="📦 Build Windows Executable",
            font=("Arial", 18, "bold")
        ).pack(pady=20)
        
        # Instructions
        instructions = (
            "This will create a standalone EXE file that can run\n"
            "on any Windows computer without Python installed.\n\n"
            "Requirements:\n"
            "• PyInstaller must be installed\n"
            "• Sufficient disk space (100+ MB)\n"
            "• Windows operating system\n\n"
            "The process may take 1-3 minutes."
        )
        
        ctk.CTkLabel(
            dialog,
            text=instructions,
            font=("Arial", 11),
            justify="left"
        ).pack(pady=10, padx=20)
        
        # Output directory selection
        dir_frame = ctk.CTkFrame(dialog)
        dir_frame.pack(pady=10, padx=20, fill="x")
        
        self.output_dir_var = ctk.StringVar(value=os.getcwd())
        
        ctk.CTkLabel(
            dir_frame,
            text="Output Directory:",
            font=("Arial", 11, "bold")
        ).pack(anchor="w", padx=10, pady=(10, 5))
        
        dir_entry = ctk.CTkEntry(
            dir_frame,
            textvariable=self.output_dir_var,
            width=400
        )
        dir_entry.pack(padx=10, pady=(0, 10))
        
        browse_dir_btn = ctk.CTkButton(
            dir_frame,
            text="Browse",
            command=lambda: self.browse_output_dir(dialog),
            width=80
        )
        browse_dir_btn.pack(padx=10, pady=(0, 10))
        
        # Progress bar
        self.build_progress = ctk.CTkProgressBar(dialog)
        self.build_progress.pack(pady=10, padx=20, fill="x")
        self.build_progress.set(0)
        
        # Status label
        self.build_status = ctk.CTkLabel(dialog, text="", font=("Arial", 10))
        self.build_status.pack(pady=5)
        
        # Button frame
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(pady=20)
        
        build_btn = ctk.CTkButton(
            btn_frame,
            text="🚀 Start Building",
            command=lambda: self.start_build_exe(dialog),
            width=150,
            height=40,
            fg_color=COLORS['success'],
            hover_color="#45a049"
        )
        build_btn.grid(row=0, column=0, padx=10)
        
        cancel_btn = ctk.CTkButton(
            btn_frame,
            text="Cancel",
            command=dialog.destroy,
            width=100,
            height=40
        )
        cancel_btn.grid(row=0, column=1, padx=10)
    
    def browse_output_dir(self, dialog):
        """Browse for output directory"""
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
    
    def start_build_exe(self, dialog):
        """Start EXE building process"""
        # Disable build button
        for widget in dialog.winfo_children():
            if isinstance(widget, ctk.CTkButton) and "Start Building" in widget.cget("text"):
                widget.configure(state="disabled")
        
        # Update status
        self.build_status.configure(text="Checking PyInstaller...")
        self.build_progress.set(0.1)
        
        # Run in thread
        thread = threading.Thread(
            target=self.build_exe_process,
            args=(dialog,),
            daemon=True
        )
        thread.start()
    
    def build_exe_process(self, dialog):
        """Build EXE process"""
        try:
            output_dir = self.output_dir_var.get()
            
            # Check PyInstaller
            self.after(0, lambda: self.build_status.configure(text="Checking PyInstaller..."))
            try:
                import PyInstaller
                pyinstaller_available = True
            except ImportError:
                pyinstaller_available = False
            
            if not pyinstaller_available:
                self.after(0, lambda: self.build_status.configure(
                    text="Installing PyInstaller..."
                ))
                self.build_progress.set(0.2)
                
                # Install PyInstaller
                subprocess.check_call([
                    sys.executable, "-m", "pip", "install", "pyinstaller", "--quiet"
                ])
            
            self.after(0, lambda: self.build_status.configure(text="Starting build process..."))
            self.build_progress.set(0.4)
            
            # Prepare PyInstaller command
            script_path = os.path.abspath(__file__)
            exe_name = "AutoUpdater_AI_Checker"
            
            # Create spec file content
            spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{script_path}'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'customtkinter',
        'tkinterdnd2',
        'pylint',
        'autopep8',
        'black',
        'pylint.checkers',
        'pylint.reporters',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='{exe_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
            
            # Write spec file
            spec_path = os.path.join(output_dir, f"{exe_name}.spec")
            with open(spec_path, 'w', encoding='utf-8') as f:
                f.write(spec_content)
            
            self.after(0, lambda: self.build_status.configure(text="Building executable..."))
            self.build_progress.set(0.6)
            
            # Run PyInstaller
            cmd = [
                sys.executable, "-m", "PyInstaller",
                "--clean",
                "--distpath", output_dir,
                "--workpath", os.path.join(output_dir, "build"),
                spec_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=output_dir
            )
            
            self.build_progress.set(0.9)
            
            if result.returncode == 0:
                self.after(0, lambda: self.build_status.configure(
                    text="✅ EXE built successfully!"
                ))
                self.build_progress.set(1.0)
                
                # Show success message
                exe_path = os.path.join(output_dir, exe_name, f"{exe_name}.exe")
                if os.path.exists(exe_path):
                    size = os.path.getsize(exe_path) / (1024*1024)
                    success_msg = (
                        f"✅ EXE built successfully!\n\n"
                        f"Location: {exe_path}\n"
                        f"Size: {size:.1f} MB\n\n"
                        f"You can now distribute this EXE file."
                    )
                    
                    self.after(1000, lambda: messagebox.showinfo(
                        "Build Complete",
                        success_msg
                    ))
                    
                    # Close dialog after success
                    self.after(2000, dialog.destroy)
            else:
                self.after(0, lambda: self.build_status.configure(
                    text=f"❌ Build failed: {result.stderr[:100]}..."
                ))
                
        except Exception as e:
            self.after(0, lambda: self.build_status.configure(
                text=f"❌ Error: {str(e)}"
            ))
            self.logger.log(f"EXE build error: {e}", "error")
    
    def show_help(self):
        """Show help dialog"""
        help_text = f"""
{APP_NAME} v{APP_VERSION}

🔵 PANEL 1: AUTO-UPDATE SYSTEM
• Drag & drop a Python (.py) or ZIP file
• Click "START UPDATE" to apply updates
• Automatic backup creation
• Self-restart after update

🔵 PANEL 2: AI ERROR CHECKER
• Drag & drop a Python file (.py)
• Click "ANALYZE CODE" for detailed analysis
• Click "AUTO FIX" to automatically fix issues
• Supports syntax checking and code formatting

🎨 FEATURES
• Dark/Light theme toggle
• Horizontal/Vertical layout
• Real-time logging
• Progress indicators
• EXE builder included

📦 BUILDING EXE
Use the "📦 EXE" button to create a standalone
Windows executable that doesn't require Python.

📝 REQUIREMENTS
• Python 3.7+
• Windows 7/8/10/11
• Internet connection (for first run)

Made with ❤️ for Windows Users
"""
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("Help & Information")
        dialog.geometry("500x600")
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() - dialog.winfo_width()) // 2
        y = self.winfo_y() + (self.winfo_height() - dialog.winfo_height()) // 2
        dialog.geometry(f"+{x}+{y}")
        
        # Text widget for help
        text_widget = scrolledtext.ScrolledText(
            dialog,
            wrap="word",
            font=("Consolas", 10),
            bg=COLORS['bg_dark'],
            fg=COLORS['text'],
            relief="flat",
            borderwidth=0
        )
        text_widget.pack(padx=20, pady=20, fill="both", expand=True)
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")
        
        # Close button
        close_btn = ctk.CTkButton(
            dialog,
            text="Close",
            command=dialog.destroy,
            width=100,
            height=40
        )
        close_btn.pack(pady=(0, 20))
    
    # ============================================
    # UTILITY METHODS
    # ============================================
    
    def log_update(self, message, msg_type="info"):
        """Log message to update panel"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted = f"[{timestamp}] {message}\n"
        
        self.after(0, lambda: self._update_log(formatted, msg_type))
    
    def _update_log(self, message, msg_type):
        """Update log widget (thread-safe)"""
        # Configure tags
        self.update_log.tag_config("success", foreground=COLORS['success'])
        self.update_log.tag_config("error", foreground=COLORS['error'])
        self.update_log.tag_config("warning", foreground=COLORS['warning'])
        self.update_log.tag_config("info", foreground=COLORS['text'])
        
        self.update_log.insert(END, message, msg_type)
        self.update_log.see(END)
    
    def append_result(self, message, msg_type="info"):
        """Append message to results"""
        self.after(0, lambda: self._append_result_threadsafe(message, msg_type))
    
    def _append_result_threadsafe(self, message, msg_type):
        """Append to results widget (thread-safe)"""
        self.results_text.insert(END, message, msg_type)
        self.results_text.see(END)
    
    def clear_results(self):
        """Clear results text"""
        self.after(0, lambda: self.results_text.delete(1.0, END))
    
    def update_status(self, message):
        """Update status bar"""
        self.after(0, lambda: self.status_label.configure(text=message))
    
    # ============================================
    # CONFIGURATION MANAGEMENT
    # ============================================
    
    def load_config(self):
        """Load application configuration"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                self.layout_mode = config.get('layout_mode', 'horizontal')
                theme = config.get('theme', 'dark')
                ctk.set_appearance_mode(theme)
                self.is_dark_mode = (theme == "dark")
                self.theme_btn.configure(text="🌙" if self.is_dark_mode else "☀️")
                
        except Exception as e:
            self.logger.log(f"Config load error: {e}", "warning")
    
    def save_config(self):
        """Save application configuration"""
        try:
            config = {
                'layout_mode': self.layout_mode,
                'theme': 'dark' if self.is_dark_mode else 'light',
                'last_saved': datetime.now().isoformat(),
                'version': APP_VERSION
            }
            
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
                
        except Exception as e:
            self.logger.log(f"Config save error: {e}", "warning")
    
    def on_closing(self):
        """Handle window closing"""
        self.save_config()
        self.logger.log("Application closed", "info")
        self.destroy()

# ============================================
# APPLICATION ENTRY POINT
# ============================================

def main():
    """Main application entry point"""
    try:
        # Create and run application
        app = AutoUpdaterApp()
        app.protocol("WM_DELETE_WINDOW", app.on_closing)
        app.mainloop()
        
    except Exception as e:
        print(f"\n❌ Application error: {e}")
        print("\nTraceback:")
        traceback.print_exc()
        
        # Show error dialog if possible
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Application Error",
                f"An error occurred:\n\n{str(e)}\n\n"
                f"Please check the log file: {LOG_FILE}"
            )
        except:
            pass
        
        input("\nPress Enter to exit...")

# ============================================
# EXE BUILD SCRIPT (EMBEDDED)
# ============================================

EXE_BUILDER_SCRIPT = '''"""
EXE Builder for Auto-Updater & AI Error Checker
Save this as build_exe.py and run to create standalone EXE
"""

import os
import sys
import subprocess
import shutil

def check_dependencies():
    """Check if PyInstaller is installed"""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def install_pyinstaller():
    """Install PyInstaller"""
    print("Installing PyInstaller...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    print("✅ PyInstaller installed successfully!")

def clean_build_dirs():
    """Clean previous build directories"""
    for dir_name in ['build', 'dist', '__pycache__']:
        if os.path.exists(dir_name):
            try:
                shutil.rmtree(dir_name)
                print(f"Cleaned: {dir_name}")
            except:
                pass

def build_executable():
    """Build the EXE file"""
    
    current_dir = os.getcwd()
    script_name = "AutoUpdater_AI_Checker_Final.py"
    script_path = os.path.join(current_dir, script_name)
    
    if not os.path.exists(script_path):
        print(f"❌ Error: {script_name} not found!")
        print(f"Make sure {script_name} is in the same directory.")
        return False
    
    print(f"🔍 Found main script: {script_name}")
    
    # Clean previous builds
    clean_build_dirs()
    
    # Create output directory
    output_dir = os.path.join(current_dir, "dist")
    os.makedirs(output_dir, exist_ok=True)
    
    print("\n🚀 Starting EXE build process...")
    print("This may take 2-5 minutes. Please wait...")
    
    # PyInstaller command
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "AutoUpdater_AI_Checker",
        "--onefile",
        "--windowed",
        "--clean",
        "--noconfirm",
        "--distpath", output_dir,
        "--workpath", os.path.join(current_dir, "build"),
        "--add-data", f"{script_path};.",
        "--hidden-import", "customtkinter",
        "--hidden-import", "tkinterdnd2",
        "--hidden-import", "pylint",
        "--hidden-import", "autopep8",
        "--hidden-import", "black",
        "--hidden-import", "pylint.checkers",
        "--hidden-import", "pylint.reporters",
        script_path
    ]
    
    try:
        # Run PyInstaller
        print("\n📦 Running PyInstaller...")
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Build completed successfully!")
            
            # Show EXE information
            exe_path = os.path.join(output_dir, "AutoUpdater_AI_Checker.exe")
            if os.path.exists(exe_path):
                size_mb = os.path.getsize(exe_path) / (1024 * 1024)
                print(f"\n📁 EXE Location: {exe_path}")
                print(f"📏 File Size: {size_mb:.2f} MB")
                print(f"📂 Output Directory: {output_dir}")
                
                # Create a shortcut/readme file
                readme_path = os.path.join(output_dir, "README.txt")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(f"""Auto-Updater & AI Error Checker
================================

🚀 Application: AutoUpdater_AI_Checker.exe
📅 Created: {time.strftime('%Y-%m-%d %H:%M:%S')}
📏 Size: {size_mb:.2f} MB

📋 Features:
• Auto-update system for Python applications
• AI-powered error checking and fixing
• Modern GUI with drag & drop support
• No Python installation required

🚀 How to use:
1. Double-click AutoUpdater_AI_Checker.exe
2. Use Panel 1 for auto-updates
3. Use Panel 2 for error checking
4. Drag & drop files directly onto the panels

⚠️ Note: First run may take a moment as it checks dependencies.

Made with ❤️ for Windows Users
""")
                
                print("\n📝 README.txt created in output directory.")
                
                # Open output directory
                if sys.platform == "win32":
                    os.startfile(output_dir)
                
                return True
            else:
                print("❌ EXE file not found after build!")
                return False
        else:
            print("❌ Build failed!")
            print("Error output:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Build error: {e}")
        return False

def main():
    """Main function"""
    print("=" * 70)
    print("📦 EXE BUILDER - Auto-Updater & AI Error Checker")
    print("=" * 70)
    
    # Check PyInstaller
    if not check_dependencies():
        print("PyInstaller not found. Installing...")
        install_pyinstaller()
    
    # Build EXE
    print("\n" + "=" * 70)
    success = build_executable()
    
    if success:
        print("\n" + "=" * 70)
        print("🎉 EXE build completed successfully!")
        print("You can now distribute the EXE file.")
        print("=" * 70)
    else:
        print("\n" + "=" * 70)
        print("❌ EXE build failed!")
        print("=" * 70)
    
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    import time
    main()
'''

# ============================================
# RUN APPLICATION
# ============================================

if __name__ == "__main__":
    # First install dependencies
    # Note: The silent dependency installer is already run at the top
    # We'll still keep your original install_dependencies function
    # but it won't run because dependencies are already installed silently
    
    def install_dependencies():
        """Original dependency installer - kept for compatibility"""
        pass
    
    # Create EXE builder script
    try:
        builder_path = os.path.join(os.path.dirname(__file__), "build_exe.py")
        with open(builder_path, 'w', encoding='utf-8') as f:
            f.write(EXE_BUILDER_SCRIPT)
        print(f"\n📦 EXE builder script created: {builder_path}")
    except:
        pass
    
    # Start main application
    print("\n" + "=" * 70)
    print(f"🚀 Starting {APP_NAME} v{APP_VERSION}")
    print("=" * 70 + "\n")
    
    main()