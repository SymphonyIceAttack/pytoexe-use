import os
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import time
from datetime import datetime

class CleanerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("RVwindows")
        self.root.geometry("700x550")
        self.root.resizable(False, False)
        self.root.configure(bg='#f5f5f5')
        
        # Language
        self.lang = 'vi'
        self.texts = {
            'vi': {
                'title': 'RVwindows',
                'status': 'Sẵn sàng',
                'scan_cache': 'Quét Cache',
                'scan_leftover': 'Quét Rác',
                'empty_folders': 'Xóa Trống',
                'clean_all': 'Dọn Hết',
                'delete': 'Xóa',
                'browse': 'Chọn',
                'folder': 'Thư mục:',
                'log': 'Nhật ký',
                'clear': 'Xóa log',
                'export': 'Xuất log',
                'lang': 'English',
                'found': 'Tìm thấy',
                'files': 'file',
                'deleted': 'Đã xóa',
                'failed': 'Thất bại',
                'freed': 'Giải phóng',
                'complete': 'Hoàn thành',
                'confirm': 'Xác nhận xóa',
                'delete_confirm': 'Xóa {0} file?',
                'no_files': 'Không tìm thấy file'
            },
            'en': {
                'title': 'RVwindows',
                'status': 'Ready',
                'scan_cache': 'Scan Cache',
                'scan_leftover': 'Scan Junk',
                'empty_folders': 'Empty Folders',
                'clean_all': 'Clean All',
                'delete': 'Delete',
                'browse': 'Browse',
                'folder': 'Folder:',
                'log': 'Log',
                'clear': 'Clear Log',
                'export': 'Export Log',
                'lang': 'Tiếng Việt',
                'found': 'Found',
                'files': 'files',
                'deleted': 'Deleted',
                'failed': 'Failed',
                'freed': 'Freed',
                'complete': 'Complete',
                'confirm': 'Confirm Delete',
                'delete_confirm': 'Delete {0} files?',
                'no_files': 'No files found'
            }
        }
        
        self.scanning = False
        self.found_files = []
        self.total_deleted = 0
        self.total_size = 0
        
        self.create_widgets()
        
        self.log("[RVwindows] Started")
        self.log("[RVwindows] Ready")
        
    def t(self, key):
        return self.texts[self.lang][key]
        
    def toggle_lang(self):
        self.lang = 'en' if self.lang == 'vi' else 'vi'
        self.update_ui()
        
    def update_ui(self):
        self.lbl_title.config(text=self.t('title'))
        self.lbl_status.config(text=f"✅ {self.t('status')}")
        self.btn_cache.config(text=f"🗑️ {self.t('scan_cache')}")
        self.btn_leftover.config(text=f"🧹 {self.t('scan_leftover')}")
        self.btn_empty.config(text=f"📁 {self.t('empty_folders')}")
        self.btn_all.config(text=f"⚡ {self.t('clean_all')}")
        self.btn_delete.config(text=f"❌ {self.t('delete')}")
        self.btn_browse.config(text=f"📂 {self.t('browse')}")
        self.lbl_folder.config(text=f"📁 {self.t('folder')}")
        self.lbl_log.config(text=f"📋 {self.t('log')}")
        self.btn_clear.config(text=f"🧹 {self.t('clear')}")
        self.btn_export.config(text=f"💾 {self.t('export')}")
        self.btn_lang.config(text=f"🌐 {self.t('lang')}")
        
    def create_widgets(self):
        main = tk.Frame(self.root, bg='#f5f5f5')
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=15)
        
        # Header
        header = tk.Frame(main, bg='#f5f5f5')
        header.pack(fill=tk.X, pady=(0, 10))
        
        self.lbl_title = tk.Label(header, text="RVwindows", font=('Segoe UI', 20, 'bold'), bg='#f5f5f5', fg='#2c3e50')
        self.lbl_title.pack(side=tk.LEFT)
        
        self.btn_lang = tk.Button(header, text="🌐 English", command=self.toggle_lang,
                                  bg='#3498db', fg='white', font=('Segoe UI', 9), cursor='hand2',
                                  relief='flat', padx=10, pady=2)
        self.btn_lang.pack(side=tk.RIGHT)
        
        # Status
        self.lbl_status = tk.Label(main, text="✅ Sẵn sàng", font=('Segoe UI', 10), bg='#f5f5f5', fg='#27ae60')
        self.lbl_status.pack(anchor=tk.W, pady=(0, 10))
        
        # Folder
        folder_frame = tk.Frame(main, bg='#f5f5f5')
        folder_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_folder = tk.Label(folder_frame, text="📁 Thư mục:", font=('Segoe UI', 10), bg='#f5f5f5')
        self.lbl_folder.pack(side=tk.LEFT)
        
        self.folder_path = tk.StringVar(value=os.path.expanduser("~"))
        entry_folder = tk.Entry(folder_frame, textvariable=self.folder_path, font=('Segoe UI', 10), width=45, relief='solid', bd=1)
        entry_folder.pack(side=tk.LEFT, padx=(10, 5))
        
        self.btn_browse = tk.Button(folder_frame, text="📂 Chọn", command=self.browse_folder,
                                   bg='#3498db', fg='white', font=('Segoe UI', 9), cursor='hand2',
                                   relief='flat', padx=12, pady=2)
        self.btn_browse.pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = tk.Frame(main, bg='#f5f5f5')
        btn_frame.pack(fill=tk.X, pady=10)
        
        self.btn_cache = tk.Button(btn_frame, text="🗑️ Quét Cache", command=self.scan_safe_cache,
                                  bg='#2ecc71', fg='white', font=('Segoe UI', 10), cursor='hand2',
                                  relief='flat', padx=12, pady=5)
        self.btn_cache.pack(side=tk.LEFT, padx=2)
        
        self.btn_leftover = tk.Button(btn_frame, text="🧹 Quét Rác", command=self.scan_leftover_files,
                                     bg='#f39c12', fg='white', font=('Segoe UI', 10), cursor='hand2',
                                     relief='flat', padx=12, pady=5)
        self.btn_leftover.pack(side=tk.LEFT, padx=2)
        
        self.btn_empty = tk.Button(btn_frame, text="📁 Xóa Trống", command=self.delete_empty_folders,
                                  bg='#3498db', fg='white', font=('Segoe UI', 10), cursor='hand2',
                                  relief='flat', padx=12, pady=5)
        self.btn_empty.pack(side=tk.LEFT, padx=2)
        
        self.btn_all = tk.Button(btn_frame, text="⚡ Dọn Hết", command=self.clean_all,
                                bg='#e74c3c', fg='white', font=('Segoe UI', 10, 'bold'), cursor='hand2',
                                relief='flat', padx=12, pady=5)
        self.btn_all.pack(side=tk.LEFT, padx=2)
        
        self.btn_delete = tk.Button(btn_frame, text="❌ Xóa", command=self.confirm_delete,
                                   bg='#e74c3c', fg='white', font=('Segoe UI', 10), cursor='hand2',
                                   relief='flat', padx=12, pady=5, state='disabled')
        self.btn_delete.pack(side=tk.LEFT, padx=2)
        
        # Stats
        stats_frame = tk.Frame(main, bg='#f5f5f5')
        stats_frame.pack(fill=tk.X, pady=5)
        
        self.lbl_stats = tk.Label(stats_frame, text="📊 0 files | 0 MB", font=('Segoe UI', 9), bg='#f5f5f5', fg='#7f8c8d')
        self.lbl_stats.pack(side=tk.LEFT)
        
        # Log
        log_frame = tk.LabelFrame(main, text="📋 Nhật ký", font=('Segoe UI', 10), bg='#f5f5f5', fg='#2c3e50')
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD,
                                                   font=("Consolas", 9), bg='white',
                                                   fg='#2c3e50', insertbackground='#2c3e50',
                                                   relief='flat', bd=1)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log buttons
        log_btn_frame = tk.Frame(main, bg='#f5f5f5')
        log_btn_frame.pack(fill=tk.X, pady=5)
        
        self.btn_clear = tk.Button(log_btn_frame, text="🧹 Xóa log", command=self.clear_log,
                                  bg='#95a5a6', fg='white', font=('Segoe UI', 9), cursor='hand2',
                                  relief='flat', padx=10, pady=2)
        self.btn_clear.pack(side=tk.LEFT, padx=2)
        
        self.btn_export = tk.Button(log_btn_frame, text="💾 Xuất log", command=self.export_log,
                                   bg='#95a5a6', fg='white', font=('Segoe UI', 9), cursor='hand2',
                                   relief='flat', padx=10, pady=2)
        self.btn_export.pack(side=tk.LEFT, padx=2)
        
    def log(self, message):
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.root.update_idletasks()
        
    def clear_log(self):
        self.log_text.delete(1.0, tk.END)
        self.log("Log cleared")
        
    def export_log(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")]
        )
        if file_path:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(self.log_text.get(1.0, tk.END))
            self.log(f"Log exported: {file_path}")
            
    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path.set(folder)
            self.log(f"Selected: {folder}")
            
    def set_status(self, text):
        self.lbl_status.config(text=text)
        self.root.update_idletasks()
        
    def format_size(self, size_bytes):
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
        
    def update_stats(self, count, size):
        self.lbl_stats.config(text=f"📊 {count} files | {self.format_size(size)}")
        
    def enable_delete(self):
        self.btn_delete.config(state='normal')
        
    def disable_delete(self):
        self.btn_delete.config(state='disabled')
        
    def confirm_delete(self):
        if not self.found_files:
            return
        msg = self.t('delete_confirm').format(len(self.found_files))
        if messagebox.askyesno(self.t('confirm'), msg):
            self.delete_found_files()
        
    # ================== SCAN FUNCTIONS ==================
    
    def scan_safe_cache(self):
        if self.scanning:
            return
            
        self.scanning = True
        self.found_files = []
        self.disable_delete()
        self.set_status("🔍 Scanning cache...")
        self.log("Scanning cache...")
        
        def scan():
            try:
                count = 0
                total_size = 0
                user_dir = os.path.expanduser("~")
                app_dir = os.path.dirname(os.path.abspath(__file__))
                
                cache_paths = [
                    f"{user_dir}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Cache",
                    f"{user_dir}\\AppData\\Local\\Google\\Chrome\\User Data\\Default\\Code Cache",
                    f"{user_dir}\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Cache",
                    f"{user_dir}\\AppData\\Local\\Microsoft\\Edge\\User Data\\Default\\Code Cache",
                    f"{user_dir}\\AppData\\Local\\Opera Software\\Opera Stable\\Cache",
                    f"{user_dir}\\AppData\\Local\\Opera Software\\Opera Stable\\Code Cache",
                    f"{user_dir}\\AppData\\Local\\Mozilla\\Firefox\\Profiles",
                    f"{user_dir}\\AppData\\Roaming\\Code\\Cache",
                    f"{user_dir}\\AppData\\Roaming\\Code\\CachedData",
                    f"{user_dir}\\AppData\\Roaming\\discord\\Cache",
                    f"{user_dir}\\AppData\\Roaming\\discord\\Code Cache",
                    f"{user_dir}\\AppData\\Roaming\\ZaloData\\cache",
                    f"{user_dir}\\AppData\\Roaming\\ZaloData\\thumbnails",
                    f"{user_dir}\\AppData\\Local\\Spotify\\Cache",
                    f"{user_dir}\\AppData\\Local\\Temp",
                    f"{user_dir}\\AppData\\Local\\Microsoft\\Windows\\INetCache",
                ]
                
                for cache_path in cache_paths:
                    if not self.scanning:
                        break
                    if os.path.exists(cache_path):
                        self.log(f"Scan: {cache_path}")
                        for root, dirs, files in os.walk(cache_path):
                            if not self.scanning:
                                break
                            if root.startswith(app_dir):
                                continue
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(file_path)
                                    if size > 1024 and size < 50 * 1024 * 1024:
                                        self.found_files.append(file_path)
                                        count += 1
                                        total_size += size
                                except:
                                    pass
                
                self.log(f"{self.t('found')} {count} cache {self.t('files')} ({self.format_size(total_size)})")
                self.update_stats(count, total_size)
                self.set_status(f"✅ {self.t('found')} {count} {self.t('files')}")
                
                if count > 0:
                    self.enable_delete()
                else:
                    messagebox.showinfo("Info", self.t('no_files'))
                
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                self.scanning = False
                
        threading.Thread(target=scan, daemon=True).start()
        
    def scan_leftover_files(self):
        if self.scanning:
            return
            
        self.scanning = True
        self.found_files = []
        self.disable_delete()
        self.set_status("🔍 Scanning junk...")
        self.log("Scanning junk files...")
        
        def scan():
            try:
                count = 0
                total_size = 0
                user_dir = os.path.expanduser("~")
                
                patterns = ['.log', '.old', '.bak', '.dmp', '.tmp', '.temp', '.chk', '.gid', '~$']
                folders = ['Temp', 'tmp', 'cache', 'logs', 'thumbnails', 'crashdumps']
                
                scan_paths = [
                    f"{user_dir}\\AppData\\Local",
                    f"{user_dir}\\AppData\\Roaming",
                ]
                
                for scan_path in scan_paths:
                    if not self.scanning:
                        break
                    if not os.path.exists(scan_path):
                        continue
                        
                    self.log(f"Scan: {scan_path}")
                    for root, dirs, files in os.walk(scan_path):
                        if not self.scanning:
                            break
                        if 'app.py' in files:
                            continue
                            
                        dir_name = os.path.basename(root).lower()
                        if any(f in dir_name for f in folders):
                            for file in files:
                                file_path = os.path.join(root, file)
                                try:
                                    size = os.path.getsize(file_path)
                                    if size > 1024 and size < 100 * 1024 * 1024:
                                        self.found_files.append(file_path)
                                        count += 1
                                        total_size += size
                                except:
                                    pass
                        
                        for file in files:
                            file_path = os.path.join(root, file)
                            if any(p in file_path.lower() for p in patterns):
                                try:
                                    size = os.path.getsize(file_path)
                                    if size > 1024 and size < 100 * 1024 * 1024:
                                        self.found_files.append(file_path)
                                        count += 1
                                        total_size += size
                                except:
                                    pass
                
                self.log(f"{self.t('found')} {count} junk {self.t('files')} ({self.format_size(total_size)})")
                self.update_stats(count, total_size)
                self.set_status(f"✅ {self.t('found')} {count} {self.t('files')}")
                
                if count > 0:
                    self.enable_delete()
                else:
                    messagebox.showinfo("Info", self.t('no_files'))
                
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                self.scanning = False
                
        threading.Thread(target=scan, daemon=True).start()
        
    def delete_empty_folders(self):
        if self.scanning:
            return
            
        self.scanning = True
        self.set_status("📁 Deleting empty folders...")
        self.log("Deleting empty folders...")
        
        def scan():
            try:
                deleted = 0
                scan_path = self.folder_path.get()
                
                for root, dirs, files in os.walk(scan_path, topdown=False):
                    if not self.scanning:
                        break
                    if not dirs and not files:
                        try:
                            os.rmdir(root)
                            deleted += 1
                            self.log(f"Deleted: {root}")
                        except:
                            pass
                
                self.log(f"{self.t('deleted')} {deleted} empty folders")
                self.set_status(f"✅ {self.t('deleted')} {deleted} folders")
                messagebox.showinfo(self.t('complete'), f"{self.t('deleted')} {deleted} empty folders")
                
            except Exception as e:
                self.log(f"Error: {e}")
            finally:
                self.scanning = False
                
        threading.Thread(target=scan, daemon=True).start()
        
    def clean_all(self):
        if self.scanning:
            return
            
        self.log("="*50)
        self.log("START FULL CLEAN")
        self.log("="*50)
        
        # Run all scans sequentially
        self.scan_safe_cache()
        # Wait for first scan to complete
        while self.scanning:
            time.sleep(0.5)
        self.scan_leftover_files()
        while self.scanning:
            time.sleep(0.5)
        self.delete_empty_folders()
        
    def delete_found_files(self):
        self.set_status("🗑️ Deleting...")
        self.log(f"{self.t('deleted')} {len(self.found_files)} {self.t('files')}...")
        
        deleted = 0
        failed = 0
        total_size = 0
        
        for i, file_path in enumerate(self.found_files):
            try:
                size = os.path.getsize(file_path)
                os.remove(file_path)
                deleted += 1
                total_size += size
                if i % 50 == 0:
                    self.log(f"{self.t('deleted')} {i+1}/{len(self.found_files)}")
                    self.root.update()
                    time.sleep(0.01)
            except:
                failed += 1
                
        self.log(f"✅ {self.t('deleted')}: {deleted} | ❌ {self.t('failed')}: {failed} | 💾 {self.t('freed')}: {self.format_size(total_size)}")
        self.total_deleted += deleted
        self.total_size += total_size
        
        self.found_files = []
        self.disable_delete()
        self.update_stats(0, 0)
        self.set_status("✅ Done")
        messagebox.showinfo(self.t('complete'), f"{self.t('deleted')} {deleted} {self.t('files')}\n{self.t('freed')} {self.format_size(total_size)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = CleanerApp(root)
    root.mainloop()