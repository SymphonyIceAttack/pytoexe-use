# free_crop_16x9_broadcast.py
# Zgjidh lirisht zonën e crop - automatikisht 16:9 - zoom në 1920x1080

import cv2
import numpy as np
import mss
from screeninfo import get_monitors
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import threading
import time

class FreeCrop16x9Broadcast:
    def __init__(self):
        self.monitor = get_monitors()[0]
        self.source_w = self.monitor.width
        self.source_h = self.monitor.height
        
        # Output final
        self.output_w = 1920
        self.output_h = 1080
        
        # Variablat për crop
        self.crop_start_x = 0
        self.crop_start_y = 0
        self.crop_end_x = 0
        self.crop_end_y = 0
        self.crop_rect = None
        self.is_dragging = False
        self.active = False
        
        # Për smooth zoom
        self.current_zoom = None
        self.transition_step = 0
        
        self.setup_ui()
        self.start_capture()
    
    def setup_ui(self):
        self.root = tk.Tk()
        self.root.title("Free Crop 16:9 - Broadcast Zoom Tool")
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.configure(cursor='cross', bg='black')
        
        # Canvas për vizatim
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Eventet e miut
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_down)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_up)
        
        # Eventet e tastierës
        self.root.bind("<Return>", self.apply_crop)
        self.root.bind("<Escape>", lambda e: self.root.quit())
        self.root.bind("<r>", self.reset_crop)
        self.root.bind("<space>", self.toggle_active)
        
        # Panel informativ
        self.create_info_panel()
        
        # Status bar
        self.status_var = tk.StringVar(value="📐 Drag mouse to select 16:9 crop area | [ENTER] Zoom | [R] Reset | [SPACE] Toggle | [ESC] Exit")
        status_bar = tk.Label(self.root, textvariable=self.status_var, fg='#0f0', bg='#000',
                              font=('Consolas', 10), anchor=tk.W)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
    
    def create_info_panel(self):
        panel = tk.Frame(self.root, bg='#1a1a1a', bd=1, relief=tk.RAISED)
        panel.place(x=10, y=10)
        
        info_text = f"""
╔════════════════════════════════════════════════════╗
║  FREE CROP 16:9 → AUTO ZOOM TO 1920×1080         ║
║                                                    ║
║  SOURCE: {self.source_w}×{self.source_h}                    ║
║  OUTPUT: {self.output_w}×{self.output_h}                   ║
║                                                    ║
║  🖱️  Drag mouse freely - maintains 16:9           ║
║  🔍 Automatic zoom to fullscreen                  ║
║  ✨ AI-powered quality enhancement                ║
╠════════════════════════════════════════════════════╣
║  [ENTER] → Apply zoom  │  [R] → Reset            ║
║  [SPACE] → Toggle zoom  │  [ESC] → Exit          ║
╚════════════════════════════════════════════════════╝
        """
        
        lbl = tk.Label(panel, text=info_text, fg='#0f0', bg='#1a1a1a',
                      font=('Consolas', 9), justify=tk.LEFT)
        lbl.pack(padx=10, pady=10)
        
        # Quality selector
        quality_frame = tk.Frame(panel, bg='#1a1a1a')
        quality_frame.pack(pady=5)
        
        tk.Label(quality_frame, text="ZOOM QUALITY:", fg='white', bg='#1a1a1a',
                font=('Arial', 9, 'bold')).pack()
        
        self.quality_var = tk.StringVar(value="Professional Broadcast")
        
        qualities = [
            "Fast (Performance)",
            "Professional Broadcast",
            "Maximum Quality (Slow)"
        ]
        
        for q in qualities:
            rb = tk.Radiobutton(quality_frame, text=q, variable=self.quality_var, value=q,
                                fg='#ddd', bg='#1a1a1a', selectcolor='#333',
                                font=('Arial', 8), anchor=tk.W)
            rb.pack(anchor=tk.W, padx=10)
    
    def enforce_16x9(self, x1, y1, x2, y2):
        """Forcon aspektin 16:9 në zonën e zgjedhur"""
        width = abs(x2 - x1)
        height = int(width * 9 / 16)
        
        # Përcakto qoshet
        left = min(x1, x2)
        top = min(y1, y2)
        
        # Siguro që të mos dalë jashtë ekranit
        if top + height > self.source_h:
            top = self.source_h - height
        if top < 0:
            top = 0
        
        return left, top, width, height
    
    def on_mouse_down(self, event):
        if self.active:
            return
        self.is_dragging = True
        self.crop_start_x = event.x
        self.crop_start_y = event.y
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        
        # Fshi vizatimet e mëparshme
        self.canvas.delete("crop_overlay")
    
    def on_mouse_drag(self, event):
        if not self.is_dragging or self.active:
            return
        
        self.crop_end_x = event.x
        self.crop_end_y = event.y
        
        # Llogarit zonën 16:9
        x, y, w, h = self.enforce_16x9(
            self.crop_start_x, self.crop_start_y,
            self.crop_end_x, self.crop_end_y
        )
        
        self.crop_rect = (x, y, w, h)
        self.draw_crop_overlay()
        
        # Update status
        zoom_factor = self.output_w / w if w > 0 else 0
        self.status_var.set(f"📐 Crop: {w}×{h} | Zoom: {zoom_factor:.2f}x | Position: ({x}, {y})")
    
    def draw_crop_overlay(self):
        self.canvas.delete("crop_overlay")
        
        if self.crop_rect:
            x, y, w, h = self.crop_rect
            
            # Errëso pjesën jashtë crop
            self.canvas.create_rectangle(0, 0, self.source_w, y, 
                                        fill='#000000', stipple='gray50', tags="crop_overlay")
            self.canvas.create_rectangle(0, y+h, self.source_w, self.source_h,
                                        fill='#000000', stipple='gray50', tags="crop_overlay")
            self.canvas.create_rectangle(0, y, x, y+h,
                                        fill='#000000', stipple='gray50', tags="crop_overlay")
            self.canvas.create_rectangle(x+w, y, self.source_w, y+h,
                                        fill='#000000', stipple='gray50', tags="crop_overlay")
            
            # Korniza 16:9
            self.canvas.create_rectangle(x, y, x+w, y+h, outline='#0f0', width=3, tags="crop_overlay")
            
            # Linjat e aspektit
            self.canvas.create_line(x + w//2, y, x + w//2, y+h, fill='#0f0', width=1, dash=(5,5), tags="crop_overlay")
            self.canvas.create_line(x, y + h//2, x+w, y + h//2, fill='#0f0', width=1, dash=(5,5), tags="crop_overlay")
            
            # Tekst info
            zoom_factor = self.output_w / w
            self.canvas.create_text(x + 10, y + 25, 
                                   text=f"16:9 CROP | {w}×{h}\nZOOM → {zoom_factor:.1f}x",
                                   fill='#0f0', anchor='nw', font=('Arial', 10, 'bold'),
                                   tags="crop_overlay")
    
    def on_mouse_up(self, event):
        self.is_dragging = False
    
    def apply_crop(self, event=None):
        if self.crop_rect and not self.active:
            self.active = True
            self.canvas.delete("crop_overlay")
            self.status_var.set("🔍 ZOOM ACTIVE - Live broadcast quality | [SPACE] to stop")
    
    def reset_crop(self, event=None):
        self.active = False
        self.crop_rect = None
        self.canvas.delete("crop_overlay")
        self.status_var.set("📐 Drag mouse to select 16:9 crop area | [ENTER] Zoom | [R] Reset")
    
    def toggle_active(self, event=None):
        self.active = not self.active
        if not self.active:
            self.status_var.set("📐 Zoom paused - Select new area or press [ENTER] to resume")
        else:
            self.status_var.set("🔍 ZOOM ACTIVE - Live broadcast quality")
    
    def apply_quality_enhancement(self, frame):
        quality = self.quality_var.get()
        
        if quality == "Fast (Performance)":
            return frame
        
        elif quality == "Professional Broadcast":
            # Smart sharpening
            kernel = np.array([[-0.5,-0.5,-0.5],
                              [-0.5, 5,-0.5],
                              [-0.5,-0.5,-0.5]]) / 1.5
            frame = cv2.filter2D(frame, -1, kernel)
            # Light denoise
            frame = cv2.bilateralFilter(frame, 3, 30, 30)
            return frame
        
        elif quality == "Maximum Quality (Slow)":
            # AI-like upscaling (Lanczos + Unsharp Mask + Bilateral)
            frame = cv2.bilateralFilter(frame, 5, 50, 50)
            kernel = np.array([[-1,-1,-1],
                              [-1, 9,-1],
                              [-1,-1,-1]])
            frame = cv2.filter2D(frame, -1, kernel)
            # Slight saturation boost
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            hsv[:,:,1] = np.clip(hsv[:,:,1] * 1.1, 0, 255)
            frame = cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
            return frame
        
        return frame
    
    def start_capture(self):
        def capture_loop():
            with mss.mss() as sct:
                fps_counter = 0
                last_time = time.time()
                
                while True:
                    if self.active and self.crop_rect:
                        x, y, w, h = self.crop_rect
                        
                        # Kap zonën e crop
                        capture_area = {"top": y, "left": x, "width": w, "height": h, "mon": 1}
                        img = sct.grab(capture_area)
                        frame = np.array(img)
                        frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                        
                        # Zoom në 1920x1080
                        frame = cv2.resize(frame, (self.output_w, self.output_h), 
                                          interpolation=cv2.INTER_LANCZOS4)
                        
                        # Apliko përmirësimet e cilësisë
                        frame = self.apply_quality_enhancement(frame)
                        
                        # FPS counter
                        fps_counter += 1
                        if time.time() - last_time >= 1.0:
                            fps = fps_counter
                            fps_counter = 0
                            last_time = time.time()
                            cv2.putText(frame, f"ZOOM 16:9 | {fps} FPS", (10, 30),
                                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                        
                        self.update_preview(frame)
                    
                    self.root.update_idletasks()
        
        threading.Thread(target=capture_loop, daemon=True).start()
    
    def update_preview(self, frame):
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        
        if canvas_w > 1 and canvas_h > 1:
            img = img.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
        
        imgtk = ImageTk.PhotoImage(image=img)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=imgtk)
        self.canvas.image = imgtk
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = FreeCrop16x9Broadcast()
    app.run()