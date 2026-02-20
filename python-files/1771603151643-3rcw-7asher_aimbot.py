import tkinter as tk
from tkinter import messagebox
import pyautogui
import keyboard
import mouse
import cv2
import numpy as np
import mss
import threading
import time
import json
import os
import sys
import win32gui
import win32con

# ===================================================
# 7asher Color AimBot - الإصدار الكامل
# 7asherStore.com
# ===================================================

class ColorAimbotGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("7asher Color AimBot - 7asherStore.com")
        self.root.geometry("500x700")
        self.root.resizable(False, False)
        self.root.configure(bg='#1a1a1a')
        
        # منع التقاط الشاشة
        self.set_anti_screenshot()
        
        # متغيرات البرنامج
        self.aimbot_active = False
        self.safety_mode = False
        self.show_fov = True
        self.aimbot_thread = None
        self.fov_window = None
        
        # إعدادات اللون
        self.color_code = tk.StringVar(value="0xff5ffb")
        self.tolerance = tk.IntVar(value=19)
        
        # إعدادات FOV
        self.fov_radius = tk.IntVar(value=226)
        
        # إعدادات التصويب
        self.vertical_offset = tk.IntVar(value=116)
        self.aim_speed = tk.IntVar(value=4)
        self.trigger_var = tk.StringVar(value="Both")
        
        # تحميل الإعدادات المحفوظة
        self.load_settings()
        
        # بناء الواجهة
        self.setup_ui()
        
        # اختصارات الكيبورد
        self.setup_hotkeys()
        
        # حماية الخروج
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def set_anti_screenshot(self):
        """حماية النافذة من التصوير"""
        try:
            hwnd = self.root.winfo_id()
            extended_style = win32con.WS_EX_LAYERED | win32con.WS_EX_TRANSPARENT | win32con.WS_EX_TOOLWINDOW
            win32gui.SetWindowLong(hwnd, win32con.GWL_EXSTYLE, extended_style)
            win32gui.SetLayeredWindowAttributes(hwnd, 0, 255, win32con.LWA_ALPHA)
        except:
            pass

    def setup_ui(self):
        """بناء واجهة المستخدم"""
        
        # الإطار الرئيسي
        main_frame = tk.Frame(self.root, bg='#1a1a1a')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # ===== الهيدر =====
        header_frame = tk.Frame(main_frame, bg='#2d2d2d', height=60)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(header_frame, 
                              text="7asher Color AimBot", 
                              font=('Arial', 18, 'bold'), 
                              fg='#ff6b6b', 
                              bg='#2d2d2d')
        title_label.pack(pady=(10, 0))
        
        store_label = tk.Label(header_frame, 
                              text="7asherStore.com", 
                              font=('Arial', 10), 
                              fg='#888888', 
                              bg='#2d2d2d')
        store_label.pack()
        
        # ===== أزرار التحكم =====
        control_frame = tk.Frame(main_frame, bg='#1a1a1a')
        control_frame.pack(fill=tk.X, pady=5)
        
        # زر تشغيل/إيقاف الـ Aimbot
        self.aimbot_button = tk.Button(control_frame, 
                                      text="▶ Disable Aimbot", 
                                      command=self.toggle_aimbot,
                                      bg='#4CAF50', 
                                      fg='white', 
                                      font=('Arial', 11, 'bold'),
                                      relief=tk.FLAT, 
                                      padx=20, 
                                      pady=8)
        self.aimbot_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # زر وضع الأمان
        safety_frame = tk.Frame(control_frame, bg='#1a1a1a')
        safety_frame.pack(side=tk.LEFT)
        
        safety_label = tk.Label(safety_frame, 
                               text="Safety Mode:", 
                               font=('Arial', 10), 
                               fg='#cccccc', 
                               bg='#1a1a1a')
        safety_label.pack(anchor='w')
        
        self.safety_button = tk.Button(safety_frame, 
                                      text="OFF", 
                                      command=self.toggle_safety,
                                      bg='#f44336', 
                                      fg='white',
                                      font=('Arial', 9, 'bold'),
                                      relief=tk.FLAT, 
                                      width=6)
        self.safety_button.pack()
        
        # ===== إعدادات اللون =====
        color_frame = tk.LabelFrame(main_frame, 
                                   text="TARGET COLOR", 
                                   font=('Arial', 12, 'bold'),
                                   fg='#ff6b6b', 
                                   bg='#1a1a1a', 
                                   bd=2, 
                                   relief=tk.GROOVE)
        color_frame.pack(fill=tk.X, pady=10)
        
        # Color Code
        code_frame = tk.Frame(color_frame, bg='#1a1a1a')
        code_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(code_frame, 
                text="Color Code:", 
                font=('Arial', 10),
                fg='#cccccc', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        self.color_entry = tk.Entry(code_frame, 
                                   textvariable=self.color_code,
                                   font=('Arial', 10), 
                                   width=15,
                                   bg='#333333', 
                                   fg='#ffffff', 
                                   bd=0)
        self.color_entry.pack(side=tk.LEFT, padx=10)
        
        self.apply_color_btn = tk.Button(code_frame, 
                                        text="Apply",
                                        command=self.apply_color,
                                        bg='#4CAF50', 
                                        fg='white',
                                        font=('Arial', 8, 'bold'),
                                        relief=tk.FLAT, 
                                        width=6)
        self.apply_color_btn.pack(side=tk.LEFT)
        
        # معاينة اللون
        self.color_preview = tk.Label(code_frame, 
                                     bg='#ff5ffb',
                                     width=3, 
                                     height=1, 
                                     relief=tk.SUNKEN)
        self.color_preview.pack(side=tk.LEFT, padx=10)
        
        # Tolerance
        tolerance_frame = tk.Frame(color_frame, bg='#1a1a1a')
        tolerance_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(tolerance_frame, 
                text="Tolerance:", 
                font=('Arial', 10),
                fg='#cccccc', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        self.tolerance_scale = tk.Scale(tolerance_frame, 
                                       from_=1, to=30,
                                       orient=tk.HORIZONTAL, 
                                       variable=self.tolerance,
                                       length=200, 
                                       bg='#1a1a1a', 
                                       fg='#ffffff',
                                       highlightbackground='#333333')
        self.tolerance_scale.pack(side=tk.LEFT, padx=10)
        
        tk.Label(tolerance_frame, 
                text="(1-30)", 
                font=('Arial', 8),
                fg='#666666', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        # ===== إعدادات FOV =====
        fov_frame = tk.LabelFrame(main_frame, 
                                 text="FOV SETTINGS", 
                                 font=('Arial', 12, 'bold'),
                                 fg='#ff6b6b', 
                                 bg='#1a1a1a', 
                                 bd=2, 
                                 relief=tk.GROOVE)
        fov_frame.pack(fill=tk.X, pady=10)
        
        # FOV Radius
        radius_frame = tk.Frame(fov_frame, bg='#1a1a1a')
        radius_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(radius_frame, 
                text="FOV Radius:", 
                font=('Arial', 10),
                fg='#cccccc', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        self.fov_scale = tk.Scale(radius_frame, 
                                 from_=50, to=500,
                                 orient=tk.HORIZONTAL, 
                                 variable=self.fov_radius,
                                 length=200, 
                                 bg='#1a1a1a', 
                                 fg='#ffffff',
                                 highlightbackground='#333333')
        self.fov_scale.pack(side=tk.LEFT, padx=10)
        
        tk.Label(radius_frame, 
                text="pixels", 
                font=('Arial', 8),
                fg='#666666', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        # Show FOV Circle
        fov_check_frame = tk.Frame(fov_frame, bg='#1a1a1a')
        fov_check_frame.pack(fill=tk.X, padx=10, pady=5)
        
        self.fov_var = tk.BooleanVar(value=True)
        fov_check = tk.Checkbutton(fov_check_frame, 
                                  text="Show FOV Circle",
                                  variable=self.fov_var, 
                                  command=self.toggle_fov_circle,
                                  bg='#1a1a1a', 
                                  fg='#cccccc',
                                  selectcolor='#333333', 
                                  activebackground='#1a1a1a')
        fov_check.pack(side=tk.LEFT)
        
        # ===== إعدادات التصويب =====
        aim_frame = tk.LabelFrame(main_frame, 
                                 text="AIM SETTINGS", 
                                 font=('Arial', 12, 'bold'),
                                 fg='#ff6b6b', 
                                 bg='#1a1a1a', 
                                 bd=2, 
                                 relief=tk.GROOVE)
        aim_frame.pack(fill=tk.X, pady=10)
        
        # Vertical Offset
        offset_frame = tk.Frame(aim_frame, bg='#1a1a1a')
        offset_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(offset_frame, 
                text="Vertical Offset:", 
                font=('Arial', 10),
                fg='#cccccc', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        self.offset_scale = tk.Scale(offset_frame, 
                                    from_=-200, to=200,
                                    orient=tk.HORIZONTAL, 
                                    variable=self.vertical_offset,
                                    length=200, 
                                    bg='#1a1a1a', 
                                    fg='#ffffff',
                                    highlightbackground='#333333')
        self.offset_scale.pack(side=tk.LEFT, padx=10)
        
        tk.Label(offset_frame, 
                text="pixels", 
                font=('Arial', 8),
                fg='#666666', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        # Aim Speed
        speed_frame = tk.Frame(aim_frame, bg='#1a1a1a')
        speed_frame.pack(fill=tk.X, padx=10, pady=5)
        
        tk.Label(speed_frame, 
                text="Aim Speed:", 
                font=('Arial', 10),
                fg='#cccccc', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        self.speed_scale = tk.Scale(speed_frame, 
                                   from_=1, to=7,
                                   orient=tk.HORIZONTAL, 
                                   variable=self.aim_speed,
                                   length=200, 
                                   bg='#1a1a1a', 
                                   fg='#ffffff',
                                   highlightbackground='#333333')
        self.speed_scale.pack(side=tk.LEFT, padx=10)
        
        tk.Label(speed_frame, 
                text="(1-7)", 
                font=('Arial', 8),
                fg='#666666', 
                bg='#1a1a1a').pack(side=tk.LEFT)
        
        # ===== TRIGGER MODE =====
        trigger_frame = tk.LabelFrame(main_frame, 
                                     text="TRIGGER MODE", 
                                     font=('Arial', 12, 'bold'),
                                     fg='#ff6b6b', 
                                     bg='#1a1a1a', 
                                     bd=2, 
                                     relief=tk.GROOVE)
        trigger_frame.pack(fill=tk.X, pady=10)
        
        trigger_buttons_frame = tk.Frame(trigger_frame, bg='#1a1a1a')
        trigger_buttons_frame.pack(pady=10)
        
        right_click = tk.Radiobutton(trigger_buttons_frame, 
                                    text="Right Click",
                                    variable=self.trigger_var, 
                                    value="Right Click",
                                    bg='#1a1a1a', 
                                    fg='#cccccc',
                                    selectcolor='#333333', 
                                    activebackground='#1a1a1a')
        right_click.pack(side=tk.LEFT, padx=10)
        
        left_click = tk.Radiobutton(trigger_buttons_frame, 
                                   text="Left Click",
                                   variable=self.trigger_var, 
                                   value="Left Click",
                                   bg='#1a1a1a', 
                                   fg='#cccccc',
                                   selectcolor='#333333', 
                                   activebackground='#1a1a1a')
        left_click.pack(side=tk.LEFT, padx=10)
        
        both = tk.Radiobutton(trigger_buttons_frame, 
                             text="Both",
                             variable=self.trigger_var, 
                             value="Both",
                             bg='#1a1a1a', 
                             fg='#cccccc',
                             selectcolor='#333333', 
                             activebackground='#1a1a1a')
        both.pack(side=tk.LEFT, padx=10)
        
        # ===== الفوتر =====
        footer_frame = tk.Frame(main_frame, bg='#2d2d2d', height=40)
        footer_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        footer_frame.pack_propagate(False)
        
        footer_label = tk.Label(footer_frame, 
                               text="Anti-Screenshot Protected | Auto-Save Enabled",
                               font=('Arial', 9), 
                               fg='#4CAF50', 
                               bg='#2d2d2d')
        footer_label.pack(pady=10)

    def toggle_aimbot(self):
        """تشغيل/إيقاف الـ Aimbot"""
        self.aimbot_active = not self.aimbot_active
        
        if self.aimbot_active:
            self.aimbot_button.config(text="⏸ Enable Aimbot", bg='#f44336')
            self.aimbot_thread = threading.Thread(target=self.aimbot_loop, daemon=True)
            self.aimbot_thread.start()
        else:
            self.aimbot_button.config(text="▶ Disable Aimbot", bg='#4CAF50')

    def toggle_safety(self):
        """تبديل وضع الأمان"""
        self.safety_mode = not self.safety_mode
        
        if self.safety_mode:
            self.safety_button.config(text="ON", bg='#4CAF50')
            self.root.withdraw()
        else:
            self.safety_button.config(text="OFF", bg='#f44336')
            self.root.deiconify()

    def apply_color(self):
        """تطبيق لون جديد"""
        color = self.color_code.get()
        if color.startswith('0x'):
            hex_color = color.replace('0x', '#')
            self.color_preview.config(bg=hex_color)
            messagebox.showinfo("نجاح", f"تم تطبيق اللون: {color}")

    def toggle_fov_circle(self):
        """إظهار/إخفاء دائرة FOV"""
        self.show_fov = self.fov_var.get()
        if self.show_fov:
            self.create_fov_circle()
        else:
            if self.fov_window:
                self.fov_window.destroy()
                self.fov_window = None

    def create_fov_circle(self):
        """إنشاء دائرة FOV"""
        if self.fov_window:
            self.fov_window.destroy()
        
        self.fov_window = tk.Toplevel(self.root)
        self.fov_window.overrideredirect(True)
        self.fov_window.attributes('-topmost', True)
        self.fov_window.attributes('-transparentcolor', 'white')
        
        x = self.root.winfo_screenwidth() // 2 - self.fov_radius.get()
        y = self.root.winfo_screenheight() // 2 - self.fov_radius.get()
        size = self.fov_radius.get() * 2 + 10
        
        self.fov_window.geometry(f"{size}x{size}+{x}+{y}")
        
        canvas = tk.Canvas(self.fov_window, 
                          width=size, 
                          height=size, 
                          bg='white', 
                          highlightthickness=0)
        canvas.pack()
        
        canvas.create_oval(5, 5, size-5, size-5, 
                          outline='red', width=2)

    def aimbot_loop(self):
        """الحلقة الرئيسية للـ Aimbot"""
        screen_width, screen_height = pyautogui.size()
        center_x, center_y = screen_width // 2, screen_height // 2
        
        # تحويل اللون
        color_hex = self.color_code.get().replace('0x', '')
        if len(color_hex) == 6:
            color_bgr = tuple(int(color_hex[i:i+2], 16) for i in (4, 2, 0))
        else:
            color_bgr = (255, 0, 255)  # لون افتراضي
        
        with mss.mss() as sct:
            while self.aimbot_active:
                try:
                    # منطقة المسح
                    left = center_x - self.fov_radius.get()
                    top = center_y - self.fov_radius.get()
                    
                    monitor = {
                        "left": left,
                        "top": top,
                        "width": self.fov_radius.get() * 2,
                        "height": self.fov_radius.get() * 2
                    }
                    
                    # التقاط الشاشة
                    img = sct.grab(monitor)
                    img_np = np.array(img)
                    
                    # تحويل الصورة
                    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_BGRA2BGR)
                    
                    # البحث عن اللون
                    lower = np.array([max(0, c - self.tolerance.get()) for c in color_bgr])
                    upper = np.array([min(255, c + self.tolerance.get()) for c in color_bgr])
                    
                    mask = cv2.inRange(img_bgr, lower, upper)
                    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                    
                    if contours:
                        largest = max(contours, key=cv2.contourArea)
                        if cv2.contourArea(largest) > 30:
                            M = cv2.moments(largest)
                            if M["m00"] > 0:
                                target_x = int(M["m10"] / M["m00"])
                                target_y = int(M["m01"] / M["m00"])
                                
                                # تطبيق Vertical Offset
                                target_y += self.vertical_offset.get()
                                
                                # الإحداثيات المطلقة
                                absolute_x = left + target_x
                                absolute_y = top + target_y
                                
                                # التحقق من وضع الزناد
                                should_aim = False
                                if self.trigger_var.get() == "Right Click" and mouse.is_pressed('right'):
                                    should_aim = True
                                elif self.trigger_var.get() == "Left Click" and mouse.is_pressed('left'):
                                    should_aim = True
                                elif self.trigger_var.get() == "Both":
                                    if mouse.is_pressed('right') or mouse.is_pressed('left'):
                                        should_aim = True
                                
                                if should_aim:
                                    # تحريك الفأرة
                                    pyautogui.moveTo(absolute_x, absolute_y, 
                                                   duration=0.01/self.aim_speed.get())
                    
                    time.sleep(0.01)
                    
                except Exception as e:
                    print(f"خطأ: {e}")
                    time.sleep(0.1)

    def setup_hotkeys(self):
        """اختصارات الكيبورد"""
        keyboard.on_press_key('insert', lambda _: self.toggle_aimbot())
        keyboard.on_press_key('home', lambda _: self.toggle_safety())

    def load_settings(self):
        """تحميل الإعدادات"""
        try:
            if os.path.exists('aimbot_settings.json'):
                with open('aimbot_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.color_code.set(settings.get('color', '0xff5ffb'))
                    self.tolerance.set(settings.get('tolerance', 19))
                    self.fov_radius.set(settings.get('fov', 226))
                    self.vertical_offset.set(settings.get('offset', 116))
                    self.aim_speed.set(settings.get('speed', 4))
                    self.trigger_var.set(settings.get('trigger', 'Both'))
        except:
            pass

    def save_settings(self):
        """حفظ الإعدادات"""
        settings = {
            'color': self.color_code.get(),
            'tolerance': self.tolerance.get(),
            'fov': self.fov_radius.get(),
            'offset': self.vertical_offset.get(),
            'speed': self.aim_speed.get(),
            'trigger': self.trigger_var.get()
        }
        with open('aimbot_settings.json', 'w') as f:
            json.dump(settings, f)

    def on_closing(self):
        """عند إغلاق البرنامج"""
        self.aimbot_active = False
        self.save_settings()
        if self.fov_window:
            self.fov_window.destroy()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = ColorAimbotGUI(root)
    root.mainloop()