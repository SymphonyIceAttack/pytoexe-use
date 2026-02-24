import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance
import os

class A4PrinterApp:
    def __init__(self, root):
        self.root = root
        self.root.title("A4 Kağıt Yazdırma Programı")
        self.root.geometry("1000x800")
        self.root.configure(bg='#f0f0f0')
        
        self.original_image = None
        self.processed_image = None
        self.display_image = None
        self.orientation = tk.StringVar(value="dikey")
        self.scale_percent = tk.DoubleVar(value=100)
        self.contrast = tk.DoubleVar(value=1.0)
        self.brightness = tk.DoubleVar(value=1.0)
        self.sharpness = tk.DoubleVar(value=1.0)
        
        # A4 boyutları (300 DPI)
        self.A4_WIDTH_PORTRAIT = 2480
        self.A4_HEIGHT_PORTRAIT = 3508
        self.A4_WIDTH_LANDSCAPE = 3508
        self.A4_HEIGHT_LANDSCAPE = 2480
        
        self.setup_ui()
        
    def setup_ui(self):
        title = tk.Label(self.root, text="A4 Kağıt Yazdırma Programı", 
                        font=('Arial', 20, 'bold'), bg='#f0f0f0', fg='#333')
        title.pack(pady=20)
        
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # Sol panel
        left_panel = tk.Frame(main_frame, bg='#f0f0f0', width=300)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=10)
        
        upload_btn = tk.Button(left_panel, text="📷 Resim Yükle", 
                            command=self.load_image,
                            font=('Arial', 12, 'bold'),
                            bg='#4CAF50', fg='white',
                            width=20, height=2)
        upload_btn.pack(pady=10)
        
        # Ayarlar
        settings_frame = tk.LabelFrame(left_panel, text="A4 Kağıt Ayarları", 
                                     font=('Arial', 11, 'bold'),
                                     bg='#f0f0f0', padx=10, pady=10)
        settings_frame.pack(fill=tk.X, pady=10)
        
        tk.Label(settings_frame, text="Kağıt Yönü:", bg='#f0f0f0').pack(anchor=tk.W)
        
        tk.Radiobutton(settings_frame, text="Dikey", 
                      variable=self.orientation, value="dikey",
                      bg='#f0f0f0', command=self.update_preview).pack(anchor=tk.W)
        tk.Radiobutton(settings_frame, text="Yatay", 
                      variable=self.orientation, value="yatay",
                      bg='#f0f0f0', command=self.update_preview).pack(anchor=tk.W)
        
        tk.Label(settings_frame, text="Ölçekleme (%):", bg='#f0f0f0').pack(anchor=tk.W, pady=(10,0))
        tk.Scale(settings_frame, from_=10, to=150, orient=tk.HORIZONTAL, 
                variable=self.scale_percent, command=lambda x: self.update_preview()).pack(fill=tk.X)
        
        tk.Label(settings_frame, text="Kontrast:", bg='#f0f0f0').pack(anchor=tk.W)
        tk.Scale(settings_frame, from_=0.5, to=2.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.contrast, 
                command=lambda x: self.update_preview()).pack(fill=tk.X)
        
        tk.Label(settings_frame, text="Parlaklık:", bg='#f0f0f0').pack(anchor=tk.W)
        tk.Scale(settings_frame, from_=0.5, to=2.0, resolution=0.1,
                orient=tk.HORIZONTAL, variable=self.brightness,
                command=lambda x: self.update_preview()).pack(fill=tk.X)
        
        # Butonlar
        print_btn = tk.Button(left_panel, text="🖨 Yazdır",
                             command=self.print_image,
                             font=('Arial', 12, 'bold'),
                             bg='#FF5722', fg='white',
                             width=18, height=2)
        print_btn.pack(pady=10)
        
        save_btn = tk.Button(left_panel, text="💾 Kaydet",
                            command=self.save_image,
                            font=('Arial', 10),
                            bg='#9C27B0', fg='white',
                            width=18, height=1)
        save_btn.pack(pady=5)
        
        # Sağ panel - Önizleme
        right_panel = tk.Frame(main_frame, bg='white', bd=2, relief=tk.SUNKEN)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10)
        
        self.canvas = tk.Canvas(right_panel, bg='#e0e0e0', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.canvas.create_text(300, 300, text="Resim yüklemek için\\n'Resim Yükle' butonuna tıklayın",
                             font=('Arial', 14), fill='#666', justify=tk.CENTER)
        
        self.info_label = tk.Label(self.root, text="Hazır - Resim yükleyin",
                                  font=('Arial', 10), bg='#f0f0f0', fg='#666')
        self.info_label.pack(pady=10)
        
    def load_image(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Resim dosyaları", "*.png *.jpg *.jpeg *.bmp"), ("Tüm dosyalar", "*.*")]
        )
        
        if file_path:
            try:
                self.original_image = Image.open(file_path)
                self.info_label.config(text=f"Yüklenen: {os.path.basename(file_path)}")
                self.update_preview()
            except Exception as e:
                messagebox.showerror("Hata", f"Resim yüklenirken hata: {str(e)}")
    
    def process_image(self):
        if self.original_image is None:
            return None
        
        img = self.original_image.copy()
        
        # RGB'ye çevir
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            if img.mode in ('RGBA', 'LA'):
                background.paste(img, mask=img.split()[-1])
                img = background
            else:
                img = img.convert('RGB')
        
        # Otomatik temizleme (yazı/çizim için)
        gray = img.convert('L')
        img = gray.point(lambda x: 0 if x < 128 else 255, '1')
        img = img.convert('RGB')
        
        # Kullanıcı ayarları
        enhancer = ImageEnhance.Contrast(img)
        img = enhancer.enhance(self.contrast.get())
        
        enhancer = ImageEnhance.Brightness(img)
        img = enhancer.enhance(self.brightness.get())
        
        return img
    
    def fit_to_a4(self, img):
        if self.orientation.get() == "dikey":
            a4_width, a4_height = self.A4_WIDTH_PORTRAIT, self.A4_HEIGHT_PORTRAIT
        else:
            a4_width, a4_height = self.A4_WIDTH_LANDSCAPE, self.A4_HEIGHT_LANDSCAPE
        
        scale = self.scale_percent.get() / 100.0
        img_width, img_height = img.size
        
        margin = 100
        max_width = a4_width - (2 * margin)
        max_height = a4_height - (2 * margin)
        
        ratio = min(max_width / img_width, max_height / img_height) * scale
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        a4_canvas = Image.new('RGB', (a4_width, a4_height), (255, 255, 255))
        x = (a4_width - new_width) // 2
        y = (a4_height - new_height) // 2
        a4_canvas.paste(img_resized, (x, y))
        
        return a4_canvas
    
    def update_preview(self):
        if self.original_image is None:
            return
        
        processed = self.process_image()
        if processed is None:
            return
        
        self.processed_image = self.fit_to_a4(processed)
        
        canvas_width = self.canvas.winfo_width() or 600
        canvas_height = self.canvas.winfo_height() or 800
        
        preview_width = canvas_width - 40
        preview_height = canvas_height - 40
        
        img_width, img_height = self.processed_image.size
        ratio = min(preview_width / img_width, preview_height / img_height)
        
        new_width = int(img_width * ratio)
        new_height = int(img_height * ratio)
        
        preview_img = self.processed_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        self.display_image = ImageTk.PhotoImage(preview_img)
        
        self.canvas.delete("all")
        x = (canvas_width - new_width) // 2
        y = (canvas_height - new_height) // 2
        
        self.canvas.create_rectangle(x-5, y-5, x+new_width+5, y+new_height+5,
                                    fill='white', outline='#ccc', width=2)
        self.canvas.create_image(x + new_width//2, y + new_height//2, image=self.display_image)
        
        orientation_text = "Dikey" if self.orientation.get() == "dikey" else "Yatay"
        self.info_label.config(text=f"A4 {orientation_text} | Yazdırmaya hazır")
    
    def print_image(self):
        if self.processed_image is None:
            messagebox.showwarning("Uyarı", "Önce bir resim yükleyin!")
            return
        
        try:
            temp_path = os.path.join(os.path.expanduser("~"), "temp_a4_print.png")
            self.processed_image.save(temp_path, 'PNG', dpi=(300, 300))
            
            if os.name == 'nt':
                os.startfile(temp_path, "print")
                messagebox.showinfo("Yazdırma", "Yazdırma diyaloğu açıldı.\\nKağıt boyutunu A4 olarak ayarlayın!")
            else:
                messagebox.showinfo("Bilgi", f"Dosya kaydedildi: {temp_path}")
        except Exception as e:
            messagebox.showerror("Hata", f"Yazdırma hatası: {str(e)}")
    
    def save_image(self):
        if self.processed_image is None:
            messagebox.showwarning("Uyarı", "Önce bir resim yükleyin!")
            return
        
        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPEG", "*.jpg"), ("PDF", "*.pdf")]
        )
        
        if file_path:
            try:
                if file_path.lower().endswith('.pdf'):
                    self.processed_image.save(file_path, 'PDF', resolution=300.0)
                else:
                    self.processed_image.save(file_path, dpi=(300, 300))
                messagebox.showinfo("Başarılı", f"Kaydedildi: {file_path}")
            except Exception as e:
                messagebox.showerror("Hata", f"Kaydetme hatası: {str(e)}")

if __name__ == "__main__":
    root = tk.Tk()
    app = A4PrinterApp(root)
    root.mainloop()