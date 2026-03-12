#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import subprocess
import threading
import os
import sys
import platform
import tempfile

class BatchRunner:
    def __init__(self, root):
        self.root = root
        self.root.title("Cross-Platform Batch File Runner")
        self.root.geometry("1000x600")
        self.root.minsize(800, 500)
        
        # Initialize attributes first
        self.process = None
        self.batch_files = []
        
        # CRITICAL FIX: Get the correct directory whether running as script or EXE
        if getattr(sys, 'frozen', False):
            # Running as compiled EXE
            self.current_dir = os.path.dirname(sys.executable)
            self.running_mode = "EXE"
        else:
            # Running as Python script
            self.current_dir = os.path.dirname(os.path.abspath(__file__))
            self.running_mode = "Script"
        
        self.terminal = None  # Will be set later
        
        # Detect OS and set appropriate settings
        self.detect_os()
        
        # Configure style
        self.root.configure(bg='#2d2d2d')
        
        # Create main frames
        self.create_left_frame()
        self.create_right_frame()  # Create terminal FIRST
        
        # Now print system info (after terminal exists)
        self.print_system_info()
        
    def detect_os(self):
        """Detect operating system and set appropriate flags"""
        self.os_name = platform.system()
        self.os_version = platform.release()
        self.is_windows = self.os_name == "Windows"
        self.is_linux = self.os_name == "Linux"
        self.is_mac = self.os_name == "Darwin"  # macOS
        
        # Set command prefix based on OS
        if self.is_windows:
            self.shell_cmd = ['cmd.exe', '/c']
            self.has_admin = self.check_windows_admin()
        elif self.is_linux:
            self.shell_cmd = ['wine', 'cmd', '/c']
            self.has_admin = False  # Linux doesn't need "Run as Admin" for Wine
            self.check_wine()
        elif self.is_mac:
            self.shell_cmd = ['wine', 'cmd', '/c']  # Assuming Wine is installed on Mac
            self.has_admin = False
            self.check_wine()
        else:
            self.shell_cmd = ['cmd', '/c']
            self.has_admin = False
            
    def check_windows_admin(self):
        """Check if running as admin on Windows"""
        try:
            import ctypes
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
            
    def check_wine(self):
        """Check if Wine is installed on Linux/Mac"""
        try:
            result = subprocess.run(['which', 'wine'], capture_output=True, text=True)
            if result.returncode == 0:
                self.wine_path = result.stdout.strip()
                wine_version = subprocess.run(['wine', '--version'], capture_output=True, text=True)
                self.wine_version = wine_version.stdout.strip() if wine_version.returncode == 0 else "Unknown"
                return True
            else:
                self.wine_path = None
                self.wine_version = None
                return False
        except Exception:
            self.wine_path = None
            self.wine_version = None
            return False
            
    def print_system_info(self):
        """Print system information to terminal"""
        if not self.terminal:
            return
            
        self.print_to_terminal("="*60, 'prompt')
        self.print_to_terminal("  CROSS-PLATFORM BATCH FILE RUNNER", 'prompt')
        self.print_to_terminal(f"  OS: {self.os_name} {self.os_version}", 'output')
        self.print_to_terminal(f"  Running Mode: {self.running_mode}", 'system')
        
        if self.is_windows:
            admin_status = "YES (Administrator)" if self.has_admin else "NO (Limited)"
            self.print_to_terminal(f"  Admin Mode: {admin_status}", 'output')
            self.print_to_terminal("  Running batch files directly on Windows", 'command')
        elif self.is_linux:
            if hasattr(self, 'wine_path') and self.wine_path:
                self.print_to_terminal(f"  Wine: {self.wine_version}", 'wine')
                self.print_to_terminal("  Running batch files via Wine on Linux", 'command')
            else:
                self.print_to_terminal("  ⚠ Wine not detected! Install with: sudo apt install wine", 'error')
        elif self.is_mac:
            if hasattr(self, 'wine_path') and self.wine_path:
                self.print_to_terminal(f"  Wine: {self.wine_version}", 'wine')
                self.print_to_terminal("  Running batch files via Wine on macOS", 'command')
            else:
                self.print_to_terminal("  ⚠ Wine not detected! Install with: brew install wine", 'error')
        
        self.print_to_terminal(f"  Working Directory: {self.current_dir}", 'output')
        
        # List all files in directory to verify
        self.print_to_terminal("\n  Files in directory:", 'system')
        try:
            files = os.listdir(self.current_dir)
            batch_count = 0
            for f in sorted(files):
                if f.lower().endswith('.bat'):
                    self.print_to_terminal(f"    ✅ {f}", 'command')
                    batch_count += 1
                elif os.path.isfile(os.path.join(self.current_dir, f)):
                    self.print_to_terminal(f"       {f}", 'output')
            self.print_to_terminal(f"\n  Found {batch_count} batch file(s)", 'system')
        except Exception as e:
            self.print_to_terminal(f"  Error listing files: {str(e)}", 'error')
        
        self.print_to_terminal("="*60, 'prompt')
        
    def create_left_frame(self):
        """Create left frame with buttons"""
        left_frame = tk.Frame(self.root, bg='#333333', width=250)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=2, pady=2)
        left_frame.pack_propagate(False)
        
        # Title
        title_text = "BATCH RUNNER"
        if self.is_windows:
            title_text += " (Windows)"
        elif self.is_linux:
            title_text += " (Linux + Wine)"
        elif self.is_mac:
            title_text += " (macOS + Wine)"
            
        title = tk.Label(left_frame, text=title_text, 
                         bg='#333333', fg='white', 
                         font=('Arial', 12, 'bold'))
        title.pack(pady=15)
        
        # OS Indicator
        os_colors = {'Windows': '#00adef', 'Linux': '#ffaa00', 'Darwin': '#999999'}
        os_color = os_colors.get(self.os_name, '#ffffff')
        
        os_label = tk.Label(left_frame, text=f"🖥️  {self.os_name}", 
                           bg='#333333', fg=os_color, 
                           font=('Arial', 10, 'bold'))
        os_label.pack(pady=2)
        
        # Show current directory (truncated if too long)
        dir_display = self.current_dir
        if len(dir_display) > 30:
            dir_display = "..." + dir_display[-27:]
        dir_label = tk.Label(left_frame, text=dir_display, 
                            bg='#333333', fg='#888888', 
                            font=('Arial', 8))
        dir_label.pack(pady=2)
        
        # Separator
        ttk.Separator(left_frame, orient='horizontal').pack(fill=tk.X, padx=10, pady=5)
        
        # Buttons frame with scrollbar
        canvas = tk.Canvas(left_frame, bg='#333333', highlightthickness=0)
        scrollbar = tk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#333333')
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(10, 0))
        scrollbar.pack(side="right", fill="y")
        
        # Store reference to scrollable frame
        self.button_frame = scrollable_frame
        
        # Add Batch Files Section
        section_title = tk.Label(self.button_frame, text="AVAILABLE BATCH FILES", 
                                  bg='#333333', fg='#ffaa00', 
                                  font=('Arial', 10, 'bold'))
        section_title.pack(pady=5)
        
        # Scan for batch files in current directory
        self.scan_batch_files()
        
        # Add buttons for each batch file
        self.refresh_buttons()
        
        # Control buttons at bottom of left frame
        control_frame = tk.Frame(left_frame, bg='#333333')
        control_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # Refresh button
        refresh_btn = tk.Button(control_frame, text="🔄 Refresh List", 
                                command=self.refresh_batch_list,
                                bg='#555555', fg='white', 
                                font=('Arial', 9))
        refresh_btn.pack(fill=tk.X, padx=10, pady=2)
        
        # Clear Output button
        clear_btn = tk.Button(control_frame, text="🗑️ Clear Output", 
                              command=self.clear_output,
                              bg='#555555', fg='white', 
                              font=('Arial', 9))
        clear_btn.pack(fill=tk.X, padx=10, pady=2)
        
        # Stop Process button
        self.stop_btn = tk.Button(control_frame, text="⏹️ Stop Process", 
                                  command=self.stop_process,
                                  bg='#aa3333', fg='white', 
                                  font=('Arial', 9), state=tk.DISABLED)
        self.stop_btn.pack(fill=tk.X, padx=10, pady=2)
        
        # Admin notice for Windows
        if self.is_windows and not self.has_admin:
            admin_note = tk.Label(control_frame, text="⚠ Not running as Admin\nSome batch files may fail", 
                                 bg='#333333', fg='#ffaa00', 
                                 font=('Arial', 8))
            admin_note.pack(pady=5)
        
    def create_right_frame(self):
        """Create right frame with embedded terminal"""
        right_frame = tk.Frame(self.root, bg='#1e1e1e')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        # Terminal header
        header_frame = tk.Frame(right_frame, bg='#0a0a0a', height=30)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        # Terminal title with dots
        dots_frame = tk.Frame(header_frame, bg='#0a0a0a')
        dots_frame.pack(side=tk.LEFT, padx=10)
        
        for color in ['#ff5f56', '#ffbd2e', '#27c93f']:
            dot = tk.Canvas(dots_frame, width=12, height=12, bg='#0a0a0a', highlightthickness=0)
            dot.create_oval(2, 2, 10, 10, fill=color, outline='')
            dot.pack(side=tk.LEFT, padx=2)
        
        # Title based on OS
        if self.is_windows:
            term_title = "Windows Command Prompt"
        elif self.is_linux:
            term_title = "Linux + Wine CMD"
        elif self.is_mac:
            term_title = "macOS + Wine CMD"
        else:
            term_title = "Command Prompt"
            
        tk.Label(header_frame, text=term_title, 
                 bg='#0a0a0a', fg='#cccccc', font=('Consolas', 9)).pack(side=tk.LEFT, padx=10)
        
        # Terminal output area
        self.terminal = scrolledtext.ScrolledText(
            right_frame, 
            bg='#1e1e1e', 
            fg='#00ff00', 
            font=('Consolas', 10),
            insertbackground='#00ff00',
            wrap=tk.WORD,
            height=20,
            padx=10,
            pady=10
        )
        self.terminal.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Configure tags for different output types
        self.terminal.tag_config('prompt', foreground='#00ff00')
        self.terminal.tag_config('command', foreground='#ffff00')
        self.terminal.tag_config('output', foreground='#ffffff')
        self.terminal.tag_config('error', foreground='#ff5555')
        self.terminal.tag_config('wine', foreground='#ffaa00')
        self.terminal.tag_config('system', foreground='#00aaff')
        
        # Input frame
        input_frame = tk.Frame(right_frame, bg='#1e1e1e')
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.input_entry = tk.Entry(input_frame, bg='#2d2d2d', fg='#00ff00', 
                                     font=('Consolas', 10), insertbackground='#00ff00')
        self.input_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        self.input_entry.bind('<Return>', self.send_input)
        self.input_entry.config(state=tk.DISABLED)
        
        send_btn = tk.Button(input_frame, text="Send", command=self.send_input,
                             bg='#555555', fg='white', font=('Arial', 9))
        send_btn.pack(side=tk.RIGHT, padx=5)
        
    def scan_batch_files(self):
        """Scan current directory for .bat files"""
        try:
            # Change to the application directory to ensure we're in the right place
            os.chdir(self.current_dir)
            
            # Scan for .bat files
            self.batch_files = [f for f in os.listdir(self.current_dir) 
                               if f.lower().endswith('.bat')]
            
            # Sort alphabetically
            self.batch_files.sort()
            
        except Exception as e:
            if self.terminal:
                self.print_to_terminal(f"Error scanning directory: {str(e)}", 'error')
            self.batch_files = []
        
    def refresh_buttons(self):
        """Refresh the batch file buttons"""
        # Clear existing buttons (except section title)
        for widget in self.button_frame.winfo_children():
            if widget.winfo_class() == 'Button' and widget.cget('text') != "Refresh List":
                widget.destroy()
        
        # Create new buttons
        if not self.batch_files:
            label = tk.Label(self.button_frame, text="No .bat files found", 
                           bg='#333333', fg='#ff5555', font=('Arial', 9))
            label.pack(pady=10)
            
            # Show current directory
            dir_label = tk.Label(self.button_frame, text=f"Looking in:\n{self.current_dir}", 
                                bg='#333333', fg='#888888', font=('Arial', 8), justify=tk.CENTER)
            dir_label.pack(pady=5)
            
            # Offer to create a sample batch file
            create_btn = tk.Button(self.button_frame, text="+ Create Sample Batch File",
                                  command=self.create_sample_batch,
                                  bg='#444444', fg='#00ff00',
                                  font=('Arial', 9))
            create_btn.pack(pady=5)
        else:
            for batch_file in self.batch_files:
                btn = tk.Button(self.button_frame, 
                              text=f"▶ {batch_file}",
                              command=lambda f=batch_file: self.run_batch_file(f),
                              bg='#444444', fg='white',
                              font=('Arial', 9),
                              height=1,
                              anchor='w',
                              padx=10)
                btn.pack(fill=tk.X, padx=10, pady=2)
    
    def create_sample_batch(self):
        """Create a sample batch file for testing"""
        sample_path = os.path.join(self.current_dir, "sample_test.bat")
        sample_content = """@echo off
echo ========================================
echo     SAMPLE BATCH FILE FOR TESTING
echo ========================================
echo.
echo Current Directory: %cd%
echo.
echo System Information:
systeminfo | findstr /B /C:"OS Name" /C:"OS Version"
echo.
echo Date: %date%
echo Time: %time%
echo.
echo This is a test batch file running on:
if exist "C:\\Windows" (
    echo Native Windows
) else (
    echo Wine on Linux/Mac
)
echo.
echo Press any key to continue...
pause >nul
echo.
echo ========================================
echo           TEST COMPLETED!
echo ========================================
pause
"""
        try:
            with open(sample_path, 'w') as f:
                f.write(sample_content)
            self.scan_batch_files()
            self.refresh_buttons()
            if self.terminal:
                self.print_to_terminal("✓ Created sample_test.bat", 'system')
        except Exception as e:
            if self.terminal:
                self.print_to_terminal(f"Error creating sample: {str(e)}", 'error')
    
    def refresh_batch_list(self):
        """Refresh the list of batch files"""
        self.scan_batch_files()
        self.refresh_buttons()
        if self.terminal:
            self.print_to_terminal("\n✓ Batch file list refreshed", 'system')
            # Show count
            self.print_to_terminal(f"  Found {len(self.batch_files)} batch file(s) in:", 'system')
            self.print_to_terminal(f"  {self.current_dir}", 'output')
    
    def run_batch_file(self, filename):
        """Run a batch file using appropriate method for the OS"""
        filepath = os.path.join(self.current_dir, filename)
        
        if not os.path.exists(filepath):
            if self.terminal:
                self.print_to_terminal(f"\n❌ Error: {filename} not found!", 'error')
                self.print_to_terminal(f"  Looked in: {self.current_dir}", 'output')
            return
        
        # Check if Wine is needed and available on non-Windows
        if not self.is_windows and not hasattr(self, 'wine_path'):
            self.check_wine()
            if not hasattr(self, 'wine_path') or not self.wine_path:
                if self.terminal:
                    self.print_to_terminal("\n❌ Wine not installed! Please install Wine first:", 'error')
                    if self.is_linux:
                        self.print_to_terminal("   sudo apt update", 'command')
                        self.print_to_terminal("   sudo apt install wine", 'command')
                    elif self.is_mac:
                        self.print_to_terminal("   brew install wine", 'command')
                return
        
        if self.terminal:
            self.print_to_terminal(f"\n{'='*50}", 'prompt')
            self.print_to_terminal(f"▶ EXECUTING: {filename}", 'command')
            self.print_to_terminal(f"  File path: {filepath}", 'output')
            self.print_to_terminal(f"  OS Mode: {self.os_name}", 'system')
            
            if self.is_windows:
                self.print_to_terminal(f"  Admin: {'YES' if self.has_admin else 'NO'}", 'system')
            else:
                self.print_to_terminal(f"  Wine: {getattr(self, 'wine_version', 'Unknown')}", 'wine')
            
            self.print_to_terminal(f"{'='*50}\n", 'prompt')
        
        # Enable stop button
        self.stop_btn.config(state=tk.NORMAL)
        self.input_entry.config(state=tk.NORMAL)
        
        # Run in thread to prevent GUI freezing
        thread = threading.Thread(target=self._run_process, args=(filepath,))
        thread.daemon = True
        thread.start()
    
    def _run_process(self, filepath):
        """Run the process in a separate thread"""
        try:
            if self.is_windows:
                # CRITICAL FIX: Force the batch file to run in the same console
                # Create a temporary wrapper script to handle the batch file
                wrapper_content = f"""@echo off
title Running {os.path.basename(filepath)}
echo [INFO] Starting batch file in integrated console...
echo.
call "{filepath}"
echo.
if errorlevel 1 (
    echo [ERROR] Batch file exited with code %errorlevel%
) else (
    echo [SUCCESS] Batch file completed successfully
)
echo.
echo Press Ctrl+C or close this window to continue...
"""
                
                # Create temporary wrapper
                temp_dir = tempfile.gettempdir()
                wrapper_path = os.path.join(temp_dir, f"wrapper_{os.getpid()}.bat")
                
                with open(wrapper_path, 'w') as f:
                    f.write(wrapper_content)
                
                # Run with cmd /k to keep console open
                cmd = ['cmd.exe', '/k', wrapper_path]
                
                # Start process with CREATE_NO_WINDOW flag to prevent new window
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    env={**os.environ, 'PROMPT': '$P$G'}  # Set prompt
                )
            else:
                # Linux/Mac: Run through Wine
                cmd = ['wine', 'cmd', '/c', filepath]
                self.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.PIPE,
                    text=True,
                    bufsize=1,
                    universal_newlines=True
                )
            
            # Read output in real-time
            def read_output():
                while True:
                    # Read stdout
                    output = self.process.stdout.readline()
                    if output == '' and self.process.poll() is not None:
                        break
                    if output and self.terminal:
                        self.root.after(0, self.print_to_terminal, output.rstrip(), 'output')
                
                # Read any remaining output
                remaining_out, remaining_err = self.process.communicate()
                if remaining_out and self.terminal:
                    for line in remaining_out.split('\n'):
                        if line.strip():
                            self.root.after(0, self.print_to_terminal, line.rstrip(), 'output')
                
                # Check for errors
                if remaining_err and self.terminal:
                    if not self.is_windows and "fixme" in remaining_err.lower():
                        self.root.after(0, self.print_to_terminal, f"\n⚠ WINE MESSAGES:", 'wine')
                        for line in remaining_err.split('\n'):
                            if line.strip():
                                self.root.after(0, self.print_to_terminal, f"   {line.strip()}", 'wine')
                    elif remaining_err.strip():
                        self.root.after(0, self.print_to_terminal, f"\n❌ ERROR:\n{remaining_err}", 'error')
                
                # Clean up temp wrapper on Windows
                if self.is_windows and os.path.exists(wrapper_path):
                    try:
                        os.remove(wrapper_path)
                    except:
                        pass
                
                # Process completed
                return_code = self.process.poll()
                self.root.after(0, self.process_completed, return_code)
            
            thread = threading.Thread(target=read_output)
            thread.daemon = True
            thread.start()
            
        except Exception as e:
            if self.terminal:
                self.root.after(0, self.print_to_terminal, f"\n❌ Error running process: {str(e)}", 'error')
            self.root.after(0, self.process_completed, -1)
    
    def process_completed(self, return_code):
        """Handle process completion"""
        self.stop_btn.config(state=tk.DISABLED)
        self.input_entry.config(state=tk.DISABLED)
        self.process = None
        
        if self.terminal:
            self.print_to_terminal(f"\n{'='*50}", 'prompt')
            if return_code == 0:
                self.print_to_terminal("✓ PROCESS COMPLETED SUCCESSFULLY", 'prompt')
            else:
                self.print_to_terminal(f"⚠ PROCESS COMPLETED WITH CODE: {return_code}", 'error')
            self.print_to_terminal(f"{'='*50}\n", 'prompt')
            self.print_to_terminal("You can now select another batch file to run.", 'system')
    
    def send_input(self, event=None):
        """Send input to the running process"""
        if self.process and self.process.poll() is None:
            user_input = self.input_entry.get()
            if user_input:
                if self.terminal:
                    self.print_to_terminal(f"> {user_input}", 'command')
                try:
                    self.process.stdin.write(user_input + '\n')
                    self.process.stdin.flush()
                except:
                    if self.terminal:
                        self.print_to_terminal("❌ Cannot send input - process may have ended", 'error')
                self.input_entry.delete(0, tk.END)
    
    def stop_process(self):
        """Stop the currently running process"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            if self.terminal:
                self.print_to_terminal("\n⚠ PROCESS TERMINATED BY USER", 'error')
            self.process_completed(-1)
    
    def clear_output(self):
        """Clear the terminal output"""
        if self.terminal:
            self.terminal.delete(1.0, tk.END)
    
    def print_to_terminal(self, text, tag='output'):
        """Print text to the terminal with specified tag"""
        if self.terminal:
            self.terminal.insert(tk.END, text + '\n', tag)
            self.terminal.see(tk.END)

def main():
    root = tk.Tk()
    app = BatchRunner(root)
    root.mainloop()

if __name__ == "__main__":
    # Make script executable on Linux/Mac
    if platform.system() != "Windows":
        try:
            os.chmod(sys.argv[0], 0o755)
        except:
            pass
    main()