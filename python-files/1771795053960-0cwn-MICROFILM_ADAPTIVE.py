import os
import sys
import time
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import cv2
import numpy as np
from skimage import filters
from PIL import Image, ImageEnhance, ImageFilter

print("=" * 60)
print("MICROFILM CONVERTER ADAPTIVE - WALEED MAHMOUD 25541")
print("=" * 60)
print("✓ ADAPTIVE ENHANCEMENT ADDED - ANALYZES EACH PAGE")
print("=" * 60)

try:
    import fitz  # PyMuPDF
    from PIL import Image, ImageEnhance
    print("✓ Libraries loaded successfully")
except ImportError as e:
    print(f"✗ Error: {e}")
    input("Press Enter to exit...")
    sys.exit(1)

class MicrofilmAdaptive:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("MICROFILM CONVERTER ADAPTIVE - WALEED MAHMOUD 25541")
        self.root.geometry("900x750")
        self.root.configure(bg='#1a1a1a')
        
        # Colors
        self.bg_color = '#1a1a1a'
        self.frame_color = '#2d2d2d'
        self.list_color = '#3d3d3d'
        self.blue_color = '#0066cc'
        self.green_color = '#00aa00'
        self.yellow_color = '#ffaa00'
        self.red_color = '#ff5555'
        self.purple_color = '#aa00ff'
        
        self.root.configure(bg=self.bg_color)
        
        # Settings
        self.selected_files = []
        self.output_folder = os.path.join(os.getcwd(), "MICROFILM_ADAPTIVE_OUTPUT")
        self.is_processing = False
        self.cancel_flag = False
        
        self.create_ui()
        self.root.mainloop()
    
    def create_ui(self):
        main = tk.Frame(self.root, bg=self.bg_color)
        main.pack(fill=tk.BOTH, expand=True, padx=15, pady=10)
        
        # Header
        header = tk.Frame(main, bg=self.blue_color, height=60)
        header.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(header,
                text="📄 MICROFILM CONVERTER ADAPTIVE",
                font=("Arial", 18, "bold"),
                fg='white',
                bg=self.blue_color).pack(pady=(8, 2))
        
        tk.Label(header,
                text="Developer: Waleed Mahmoud | ID: 25541 | AI-Powered Enhancement",
                font=("Arial", 9),
                fg='#aaddff',
                bg=self.blue_color).pack(pady=(0, 8))
        
        # ===== FILE SELECTION =====
        file_frame = tk.LabelFrame(main,
                                   text=" 1. SELECT PDF FILES ",
                                   font=("Arial", 10, "bold"),
                                   bg=self.frame_color,
                                   fg='white',
                                   padx=10, pady=10)
        file_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.file_list = tk.Listbox(file_frame,
                                     height=4,
                                     font=("Consolas", 9),
                                     bg=self.list_color,
                                     fg='white')
        self.file_list.pack(fill=tk.X, pady=(0, 5))
        
        btn_frame = tk.Frame(file_frame, bg=self.frame_color)
        btn_frame.pack(fill=tk.X)
        
        tk.Button(btn_frame,
                 text="📁 ADD FILES",
                 command=self.select_files,
                 bg=self.blue_color,
                 fg='white',
                 font=("Arial", 9, "bold"),
                 width=12).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(btn_frame,
                 text="🗑️ CLEAR",
                 command=self.clear_files,
                 bg='#666666',
                 fg='white',
                 width=8).pack(side=tk.LEFT)
        
        self.file_count = tk.Label(file_frame,
                                   text="No files selected",
                                   bg=self.frame_color,
                                   fg=self.yellow_color)
        self.file_count.pack(pady=5)
        
        # ===== SETTINGS =====
        settings_frame = tk.LabelFrame(main,
                                       text=" 2. QUALITY SETTINGS ",
                                       font=("Arial", 10, "bold"),
                                       bg=self.frame_color,
                                       fg='white',
                                       padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Output folder
        out_row = tk.Frame(settings_frame, bg=self.frame_color)
        out_row.pack(fill=tk.X, pady=5)
        
        tk.Label(out_row,
                text="Output:",
                font=("Arial", 9),
                bg=self.frame_color,
                fg='white').pack(side=tk.LEFT)
        
        self.output_label = tk.Label(out_row,
                                     text=os.path.basename(self.output_folder),
                                     bg=self.frame_color,
                                     fg=self.yellow_color)
        self.output_label.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        
        tk.Button(out_row,
                 text="📂 BROWSE",
                 command=self.select_output,
                 bg=self.blue_color,
                 fg='white',
                 width=8).pack(side=tk.RIGHT)
        
        # Settings grid
        grid = tk.Frame(settings_frame, bg=self.frame_color)
        grid.pack(fill=tk.X, pady=5)
        
        # Row 1: DPI and Sharpness
        tk.Label(grid,
                text="DPI:",
                font=("Arial", 9, "bold"),
                bg=self.frame_color,
                fg='white').grid(row=0, column=0, padx=(0, 5), pady=5, sticky='w')
        
        self.dpi_var = tk.StringVar(value="600")
        dpi_combo = ttk.Combobox(grid,
                                  textvariable=self.dpi_var,
                                  values=["300", "400", "600", "800", "1200"],
                                  width=8,
                                  state="readonly")
        dpi_combo.grid(row=0, column=1, padx=(0, 15), pady=5, sticky='w')
        
        tk.Label(grid,
                text="Sharpness:",
                font=("Arial", 9, "bold"),
                bg=self.frame_color,
                fg='white').grid(row=0, column=2, padx=(0, 5), pady=5, sticky='w')
        
        self.sharp_var = tk.StringVar(value="MAXIMUM")
        sharp_combo = ttk.Combobox(grid,
                                    textvariable=self.sharp_var,
                                    values=["NORMAL", "HIGH", "MAXIMUM"],
                                    width=10,
                                    state="readonly")
        sharp_combo.grid(row=0, column=3, padx=(0, 5), pady=5, sticky='w')
        
        # Row 2: Color Mode and Compression
        tk.Label(grid,
                text="Color Mode:",
                font=("Arial", 9, "bold"),
                bg=self.frame_color,
                fg='white').grid(row=1, column=0, padx=(0, 5), pady=5, sticky='w')
        
        self.color_var = tk.StringVar(value="PURE BLACK & WHITE (SMALL)")
        color_combo = ttk.Combobox(grid,
                                    textvariable=self.color_var,
                                    values=[
                                        "PURE BLACK & WHITE (FAST)",
                                        "PURE BLACK & WHITE (SMALL)",
                                        "PURE BLACK & WHITE",
                                        "GRAYSCALE"
                                    ],
                                    width=22,
                                    state="readonly")
        color_combo.grid(row=1, column=1, columnspan=2, padx=(0, 5), pady=5, sticky='w')
        
        tk.Label(grid,
                text="Compress:",
                font=("Arial", 9, "bold"),
                bg=self.frame_color,
                fg='white').grid(row=1, column=3, padx=(0, 5), pady=5, sticky='w')
        
        self.compress_var = tk.StringVar(value="MAXIMUM")
        compress_combo = ttk.Combobox(grid,
                                      textvariable=self.compress_var,
                                      values=["NONE", "LIGHT", "MEDIUM", "MAXIMUM"],
                                      width=10,
                                      state="readonly")
        compress_combo.grid(row=1, column=4, padx=(0, 5), pady=5, sticky='w')
        
        # Row 3: ADAPTIVE ENHANCEMENT (الميزة الجديدة)
        tk.Label(grid,
                text="✨ Adaptive AI:",
                font=("Arial", 9, "bold"),
                bg=self.frame_color,
                fg=self.purple_color).grid(row=2, column=0, padx=(0, 5), pady=5, sticky='w')
        
        self.adaptive_var = tk.StringVar(value="ON (Recommended)")
        adaptive_combo = ttk.Combobox(grid,
                                      textvariable=self.adaptive_var,
                                      values=[
                                          "ON (Recommended)",
                                          "OFF (Standard)"
                                      ],
                                      width=18,
                                      state="readonly")
        adaptive_combo.grid(row=2, column=1, columnspan=2, padx=(0, 5), pady=5, sticky='w')
        
        # إضافة شرح مبسط
        note_frame = tk.Frame(settings_frame, bg=self.frame_color)
        note_frame.pack(fill=tk.X, pady=(5, 0))
        
        tk.Label(note_frame,
                text="✨ Adaptive AI: Automatically analyzes each page and adjusts brightness/contrast",
                font=("Arial", 8, "italic"),
                bg=self.frame_color,
                fg=self.purple_color).pack(anchor='w')
        
        tk.Label(note_frame,
                text="   - Dark pages get lightened | Light pages get darkened | Optimal for mixed documents",
                font=("Arial", 7),
                bg=self.frame_color,
                fg='#aaaaaa').pack(anchor='w')
        
        # ===== PROGRESS =====
        progress_frame = tk.LabelFrame(main,
                                       text=" 3. CONVERSION PROGRESS ",
                                       font=("Arial", 10, "bold"),
                                       bg=self.frame_color,
                                       fg='white',
                                       padx=10, pady=10)
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress = ttk.Progressbar(progress_frame, length=400, mode='determinate')
        self.progress.pack(pady=5)
        
        info_frame = tk.Frame(progress_frame, bg=self.frame_color)
        info_frame.pack(fill=tk.X, pady=5)
        
        left = tk.Frame(info_frame, bg=self.frame_color)
        left.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.current_file = tk.Label(left,
                                     text="Current: None",
                                     bg=self.frame_color,
                                     fg='#aaddff',
                                     anchor='w')
        self.current_file.pack(fill=tk.X)
        
        self.current_page = tk.Label(left,
                                     text="Page: 0/0",
                                     bg=self.frame_color,
                                     fg='#ffcc00',
                                     anchor='w')
        self.current_page.pack(fill=tk.X)
        
        right = tk.Frame(info_frame, bg=self.frame_color)
        right.pack(side=tk.RIGHT)
        
        self.percent_label = tk.Label(right,
                                      text="0%",
                                      font=("Arial", 14, "bold"),
                                      bg=self.frame_color,
                                      fg=self.green_color)
        self.percent_label.pack()
        
        self.files_counter = tk.Label(right,
                                      text="Files: 0/0",
                                      bg=self.frame_color,
                                      fg='white')
        self.files_counter.pack()
        
        # ===== BUTTONS =====
        btn_container = tk.Frame(main, bg=self.bg_color)
        btn_container.pack(fill=tk.X, pady=(0, 10))
        
        self.status = tk.Label(btn_container,
                               text="Ready to convert",
                               bg=self.bg_color,
                               fg='white')
        self.status.pack()
        
        button_row = tk.Frame(btn_container, bg=self.bg_color)
        button_row.pack(pady=5)
        
        self.convert_btn = tk.Button(button_row,
                                     text="🚀 START CONVERSION",
                                     command=self.start_conversion,
                                     bg=self.green_color,
                                     fg='white',
                                     font=("Arial", 14, "bold"),
                                     width=20,
                                     height=1,
                                     state=tk.DISABLED,
                                     cursor='hand2')
        self.convert_btn.pack(side=tk.LEFT, padx=5)
        
        self.cancel_btn = tk.Button(button_row,
                                    text="⛔ CANCEL",
                                    command=self.cancel_conversion,
                                    bg=self.red_color,
                                    fg='white',
                                    width=10,
                                    state=tk.DISABLED,
                                    cursor='hand2')
        self.cancel_btn.pack(side=tk.LEFT, padx=5)
        
        # ===== LOG =====
        log_frame = tk.LabelFrame(main,
                                   text=" 4. CONVERSION LOG ",
                                   font=("Arial", 10, "bold"),
                                   bg=self.frame_color,
                                   fg='white',
                                   padx=10, pady=10)
        log_frame.pack(fill=tk.BOTH, expand=True)
        
        self.log = scrolledtext.ScrolledText(log_frame,
                                             height=6,
                                             font=("Consolas", 9),
                                             bg=self.list_color,
                                             fg='white')
        self.log.pack(fill=tk.BOTH, expand=True)
        self.log.config(state=tk.DISABLED)
        
        self.log_message("=" * 60)
        self.log_message("MICROFILM CONVERTER ADAPTIVE - READY")
        self.log_message("✨ NEW: AI-Powered Adaptive Enhancement (Analyzes each page)")
        self.log_message("=" * 60)
    
    def log_message(self, msg):
        self.log.config(state=tk.NORMAL)
        self.log.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see(tk.END)
        self.log.config(state=tk.DISABLED)
    
    def update_progress(self, file_idx, total, page, pages, filename):
        if total > 0 and pages > 0:
            percent = ((file_idx - 1) / total) * 100
            percent += (page / pages) * (100 / total)
        else:
            percent = 0
        
        self.progress['value'] = percent
        self.percent_label.config(text=f"{percent:.1f}%")
        self.files_counter.config(text=f"Files: {file_idx}/{total}")
        
        if filename:
            short = filename[:30] + "..." if len(filename) > 30 else filename
            self.current_file.config(text=f"Current: {short}")
        
        self.current_page.config(text=f"Page: {page}/{pages}")
        self.root.update_idletasks()
    
    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("PDF files", "*.pdf")])
        if files:
            self.selected_files = list(files)
            self.file_list.delete(0, tk.END)
            for f in files:
                self.file_list.insert(tk.END, os.path.basename(f))
            self.file_count.config(text=f"{len(files)} file(s)", fg=self.green_color)
            self.log_message(f"Added {len(files)} file(s)")
            self.update_button()
    
    def clear_files(self):
        self.selected_files = []
        self.file_list.delete(0, tk.END)
        self.file_count.config(text="No files selected", fg=self.yellow_color)
        self.log_message("Cleared files")
        self.update_button()
        self.reset_progress()
    
    def reset_progress(self):
        self.progress['value'] = 0
        self.percent_label.config(text="0%")
        self.files_counter.config(text="Files: 0/0")
        self.current_file.config(text="Current: None")
        self.current_page.config(text="Page: 0/0")
    
    def select_output(self):
        folder = filedialog.askdirectory()
        if folder:
            self.output_folder = folder
            self.output_label.config(text=os.path.basename(folder))
            self.log_message(f"Output folder: {folder}")
        self.update_button()
    
    def update_button(self):
        if self.selected_files and not self.is_processing:
            self.convert_btn.config(state=tk.NORMAL, bg=self.green_color)
            self.log_message("✅ Convert button enabled")
        else:
            self.convert_btn.config(state=tk.DISABLED, bg='#666666')
    
    def cancel_conversion(self):
        self.cancel_flag = True
        self.log_message("⛔ Cancelling...")
        self.cancel_btn.config(state=tk.DISABLED)
    
    def start_conversion(self):
        self.is_processing = True
        self.cancel_flag = False
        self.convert_btn.config(state=tk.DISABLED, text="PROCESSING...", bg=self.yellow_color)
        self.cancel_btn.config(state=tk.NORMAL)
        self.status.config(text="Converting...")
        self.reset_progress()
        
        dpi = int(self.dpi_var.get())
        sharp = self.sharp_var.get()
        color = self.color_var.get()
        compress = self.compress_var.get()
        adaptive = self.adaptive_var.get()
        
        self.log_message("=" * 50)
        self.log_message(f"STARTING CONVERSION")
        self.log_message(f"DPI: {dpi}, Sharpness: {sharp}, Color: {color}")
        self.log_message(f"Compress: {compress}, Adaptive AI: {adaptive}")
        self.log_message("=" * 50)
        
        thread = threading.Thread(target=self.convert_files)
        thread.daemon = True
        thread.start()
    
    def convert_files(self):
        try:
            total = len(self.selected_files)
            success = 0
            saved_files = []
            
            if not os.path.exists(self.output_folder):
                os.makedirs(self.output_folder, exist_ok=True)
            
            for file_idx, input_path in enumerate(self.selected_files, 1):
                if self.cancel_flag:
                    break
                
                filename = os.path.basename(input_path)
                self.log_message(f"Processing {file_idx}/{total}: {filename}")
                
                pdf = fitz.open(input_path)
                pages = len(pdf)
                pdf.close()
                
                output_path = self.convert_file(input_path, file_idx, total, pages)
                if output_path:
                    success += 1
                    saved_files.append(output_path)
                    self.log_message(f"✅ Saved: {os.path.basename(output_path)}")
                else:
                    self.log_message(f"❌ Failed: {filename}")
            
            if self.cancel_flag:
                self.status.config(text="Cancelled")
                self.log_message("⛔ Cancelled")
            else:
                self.status.config(text="Complete!")
                self.progress['value'] = 100
                self.percent_label.config(text="100%")
                
                if success > 0:
                    self.log_message(f"✅ Done: {success}/{total} files")
                    messagebox.showinfo("Success", f"Converted {success}/{total} files\n\n{self.output_folder}")
                    os.startfile(self.output_folder)
                else:
                    messagebox.showerror("Error", "No files were converted")
        
        except Exception as e:
            self.log_message(f"Error: {str(e)}")
            messagebox.showerror("Error", str(e))
        
        finally:
            self.is_processing = False
            self.cancel_btn.config(state=tk.DISABLED)
            self.convert_btn.config(text="🚀 START CONVERSION", bg=self.green_color)
            self.update_button()
    
    def adaptive_enhance(self, img):
        """
        تحليل الصورة وتحسينها تلقائياً
        - الصور الغامقة → تفتيح
        - الصور الفاتحة → تغميق
        - تحسين التباين المحلي
        """
        try:
            # تحويل الصورة لـ numpy array
            img_array = np.array(img)
            
            # تحليل مستوى الإضاءة
            mean_brightness = np.mean(img_array)
            std_brightness = np.std(img_array)
            
            self.log_message(f"   🔍 Analyzing page: Brightness={mean_brightness:.1f}, Contrast={std_brightness:.1f}")
            
            # تطبيق CLAHE (تحسين التباين المحلي)
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(img_array)
            
            # ضبط حسب الإضاءة
            if mean_brightness < 100:  # صفحة غامقة
                # تفتيح أكثر
                enhanced = cv2.addWeighted(enhanced, 1.2, np.zeros_like(enhanced), 0, 30)
                self.log_message(f"   ✨ Dark page detected → Brightening")
            elif mean_brightness > 180:  # صفحة فاتحة جداً
                # تغميق
                enhanced = cv2.addWeighted(enhanced, 0.9, np.zeros_like(enhanced), 0, -20)
                self.log_message(f"   ✨ Light page detected → Darkening")
            else:
                self.log_message(f"   ✨ Balanced page → Standard enhancement")
            
            # تطبيق عتبة تكيفية (Sauvola)
            from skimage import filters
            threshold = filters.threshold_sauvola(enhanced, window_size=25)
            binary = enhanced > threshold
            
            # تحويل النتيجة لصورة PIL
            result = Image.fromarray((binary * 255).astype(np.uint8))
            return result
            
        except Exception as e:
            self.log_message(f"   ⚠️ Adaptive enhancement error: {str(e)[:50]}")
            return img
    
    def convert_file(self, input_path, file_idx, total_files, total_pages):
        try:
            pdf = fitz.open(input_path)
            new_pdf = fitz.open()
            
            dpi = int(self.dpi_var.get())
            sharp = self.sharp_var.get()
            color_mode = self.color_var.get()
            compress = self.compress_var.get()
            adaptive = self.adaptive_var.get()
            
            sharp_map = {"NORMAL": 1.0, "HIGH": 1.5, "MAXIMUM": 2.0}
            sharp_factor = sharp_map.get(sharp, 1.5)
            
            compress_map = {"NONE": 0, "LIGHT": 3, "MEDIUM": 6, "MAXIMUM": 9}
            compress_level = compress_map.get(compress, 0)
            
            # A4 Landscape
            a4_width = int(11.69 * dpi)
            a4_height = int(8.27 * dpi)
            
            for page_num in range(total_pages):
                if self.cancel_flag:
                    break
                
                self.update_progress(file_idx, total_files, page_num + 1, total_pages, os.path.basename(input_path))
                
                page = pdf[page_num]
                
                zoom = dpi / 72
                if "FAST" in color_mode:
                    zoom = zoom * 0.8
                
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat, alpha=False)
                
                img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
                img = img.rotate(-90, expand=True)
                img = img.convert('L')
                
                # ===== التعديل الجديد: التحسين التكيفي =====
                if "ON" in adaptive:
                    self.log_message(f"   🔧 Applying Adaptive AI to page {page_num+1}")
                    img = self.adaptive_enhance(img)
                
                if sharp_factor > 1.0 and "ON" not in adaptive:  # لو الـ Adaptive مش شغال، طبق Sharpness العادي
                    enhancer = ImageEnhance.Sharpness(img)
                    img = enhancer.enhance(sharp_factor)
                
                if "BLACK & WHITE" in color_mode and "ON" not in adaptive:  # لو Adaptive شغال، هو بيطلع B&W بالفعل
                    pixels = list(img.getdata())
                    threshold = 180 if "SMALL" in color_mode else 200
                    bw_pixels = [0 if p < threshold else 255 for p in pixels]
                    bw_img = Image.new('L', img.size)
                    bw_img.putdata(bw_pixels)
                    img = bw_img
                
                temp_dir = tempfile.mkdtemp()
                temp_file = os.path.join(temp_dir, f"page_{page_num}.png")
                
                if compress_level > 0:
                    img.save(temp_file, "PNG", optimize=True, compress_level=compress_level)
                else:
                    img.save(temp_file, "PNG")
                
                new_page = new_pdf.new_page(width=a4_width, height=a4_height)
                
                scale = min(a4_width/img.width, a4_height/img.height)
                new_width = int(img.width * scale)
                new_height = int(img.height * scale)
                
                x_offset = (a4_width - new_width) // 2
                y_offset = (a4_height - new_height) // 2
                
                img_rect = fitz.Rect(x_offset, y_offset, x_offset + new_width, y_offset + new_height)
                new_page.insert_image(img_rect, filename=temp_file)
                
                os.remove(temp_file)
                os.rmdir(temp_dir)
            
            if not self.cancel_flag:
                name = os.path.splitext(os.path.basename(input_path))[0]
                mode = "fast" if "FAST" in color_mode else "small" if "SMALL" in color_mode else "bw"
                adaptive_tag = "_Adaptive" if "ON" in adaptive else ""
                output_path = os.path.join(self.output_folder, f"{name}_{mode}{adaptive_tag}_A4_Landscape.pdf")
                new_pdf.save(output_path, garbage=4, deflate=True)
                new_pdf.close()
                pdf.close()
                return output_path
            
            new_pdf.close()
            pdf.close()
            return None
            
        except Exception as e:
            self.log_message(f"Error: {str(e)[:100]}")
            return None

if __name__ == "__main__":
    app = MicrofilmAdaptive()