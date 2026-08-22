import tkinter as tk
from tkinter import ttk
import ctypes
import math
import time

class DPITracker:
    def __init__(self, root):
        self.root = root
        self.root.title("DPI Tracker")
        self.root.geometry("300x180")
        self.root.resizable(False, False)
        self.root.attributes('-topmost', True)
        
        # Style
        self.root.configure(bg='#1a1a1a')
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TLabel', background='#1a1a1a', foreground='#00ff88', font=('Segoe UI', 10))
        style.configure('Header.TLabel', background='#1a1a1a', foreground='#ffffff', font=('Segoe UI', 12, 'bold'))
        style.configure('Value.TLabel', background='#1a1a1a', foreground='#00ff88', font=('Segoe UI', 24, 'bold'))
        
        # Variables
        self.last_x = None
        self.last_y = None
        self.last_time = None
        self.dpi = 0
        self.samples = []
        
        # UI
        self.create_widgets()
        
        # Start tracking
        self.update_dpi()
        
    def create_widgets(self):
        # Title
        title = ttk.Label(self.root, text="MOUSE DPI", style='Header.TLabel')
        title.pack(pady=(15, 5))
        
        # DPI Value
        self.dpi_label = ttk.Label(self.root, text="0", style='Value.TLabel')
        self.dpi_label.pack(pady=5)
        
        # Status
        self.status_label = ttk.Label(self.root, text="Moving mouse...", foreground='#888888')
        self.status_label.pack(pady=5)
        
        # Info
        info = ttk.Label(self.root, text="Windows sensitivity multiplier: 1.0", foreground='#666666', font=('Segoe UI', 8))
        info.pack(pady=5)
        
        # Close button
        close_btn = tk.Button(self.root, text="✕", command=self.root.quit, 
                             bg='#1a1a1a', fg='#666666', border=0, font=('Segoe UI', 12))
        close_btn.place(x=275, y=5)
        
    def get_cursor_pos(self):
        try:
            pt = ctypes.wintypes.POINT()
            ctypes.windll.user32.GetCursorPos(ctypes.byref(pt))
            return pt.x, pt.y
        except:
            return None, None
    
    def get_windows_multiplier(self):
        try:
            # Get Windows pointer speed (1-20, default 10)
            speed = ctypes.windll.user32.SystemParametersInfoW(0x0070, 0, 0, 0)
            # Map to multiplier (notch 6 = 1.0)
            if speed:
                multiplier = 1 + (speed - 10) * 0.1
                return round(multiplier, 2)
        except:
            pass
        return 1.0
    
    def calculate_dpi(self, dx, dy, dt):
        if dt > 0:
            # Calculate distance in pixels per second
            distance = math.sqrt(dx*dx + dy*dy)
            speed = distance / dt
            
            # Convert to DPI (approximate based on typical mouse movement)
            # 1 inch ≈ 2.54 cm, typical mouse movement at 1 second
            # This is an approximation; for exact DPI, use a physical measurement tool
            dpi_estimate = speed * 0.5  # Calibration factor
            
            if dpi_estimate > 100 and dpi_estimate < 10000:
                return int(dpi_estimate)
        return None
    
    def update_dpi(self):
        x, y = self.get_cursor_pos()
        
        if x is not None and y is not None:
            current_time = time.time()
            
            if self.last_x is not None and self.last_time is not None:
                dx = x - self.last_x
                dy = y - self.last_y
                dt = current_time - self.last_time
                
                if dt < 0.1:  # Only sample fast movements
                    dpi = self.calculate_dpi(dx, dy, dt)
                    if dpi and dpi > 100 and dpi < 10000:
                        self.samples.append(dpi)
                        if len(self.samples) > 20:
                            self.samples.pop(0)
                        
                        # Average the samples for stability
                        if self.samples:
                            avg_dpi = int(sum(self.samples) / len(self.samples))
                            self.dpi = avg_dpi
                            self.dpi_label.config(text=f"{avg_dpi}")
                            self.status_label.config(text="Tracking", foreground='#00ff88')
            
            self.last_x = x
            self.last_y = y
            self.last_time = current_time
            
        # Update multiplier info
        mult = self.get_windows_multiplier()
        if mult != 1.0:
            info_text = f"Windows multiplier: {mult}x (Effective: {int(self.dpi * mult)})"
        else:
            info_text = "Windows sensitivity: 1.0x"
        
        # Update info label (find it by text content)
        for child in self.root.winfo_children():
            if isinstance(child, ttk.Label) and child.cget('foreground') == '#666666':
                child.config(text=info_text)
                break
        
        self.root.after(50, self.update_dpi)

if __name__ == "__main__":
    root = tk.Tk()
    app = DPITracker(root)
    root.mainloop()