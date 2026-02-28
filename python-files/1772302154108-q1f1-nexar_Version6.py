import tkinter as tk
from tkinter import messagebox, ttk
import threading
import time
import logging
import winsound
import pyautogui
import cv2
import numpy as np
from pynput import keyboard, mouse
import win32api
import win32con
from PIL import Image, ImageDraw, ImageFont, ImageTk
import random
import os
import json

# ===================== LOGGING CONFIGURATION =====================
logging.basicConfig(
    filename='nexar.log',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ===================== GENERAL CONFIG ============================
LICENSE_FILE = "nexar_license.txt"
SETTINGS_FILE = "nexar_settings.json"
VALID_LICENSES = [
    "nexar-dafs8finjsf9i-8j79hef78h",
    "nexar-dai9junmdami-ada9iujda",
    "nexar-daimidjm-d9jadu9nadwoim",
    "nexar-dmiad4fewf-rwu8df8jii9fdk",
    "nexar-dj89adj09kda-0k9ada9mid",
    "nexar-dja89mu998jd-98jdnud9nu",
    "nexar-278uzjdaw9jdn9uk9-dk982"
]

SCREEN_WIDTH, SCREEN_HEIGHT = pyautogui.size()
x, y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2

INITIAL_COLOR_RGB = (224, 224, 224)

def rgb_to_hsv(rgb_color):
    color_bgr = np.uint8([[rgb_color[::-1]]])  
    color_hsv = cv2.cvtColor(color_bgr, cv2.COLOR_BGR2HSV)[0][0]
    return tuple(int(v) for v in color_hsv)

INITIAL_COLOR_HSV = rgb_to_hsv(INITIAL_COLOR_RGB)

TOLERANCE_H = 10
TOLERANCE_S = 10
TOLERANCE_V = 10
CHECK_INTERVAL = 0.1
SHOOT_INTERVAL = 0.1

clicking_enabled = False
stop_script = False
right_button_pressed = False
lock = threading.Lock()

# Settings
settings = {
    "black_background": False
}

def load_settings():
    global settings
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, 'r') as f:
                settings = json.load(f)
        except:
            settings = {"black_background": False}
    else:
        settings = {"black_background": False}

def save_settings():
    try:
        with open(SETTINGS_FILE, 'w') as f:
            json.dump(settings, f)
    except:
        pass

# ================== KEYBOARD / MOUSE LISTENERS ==================
def on_press(key):
    global clicking_enabled
    try:
        if key == keyboard.Key.insert:
            with lock:
                clicking_enabled = not clicking_enabled
                if clicking_enabled:
                    winsound.Beep(1000, 150)
                else:
                    winsound.Beep(500, 150)
    except AttributeError:
        pass

def on_click(x_click, y_click, button, pressed):
    global right_button_pressed
    if button == mouse.Button.right:
        with lock:
            right_button_pressed = pressed

def start_keyboard_listener():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def start_mouse_listener():
    with mouse.Listener(on_click=on_click) as listener:
        listener.join()

def get_pixel_color_hsv(px, py):
    try:
        color_rgb = pyautogui.pixel(px, py)
        bgr = np.uint8([[color_rgb[::-1]]])
        color_hsv = cv2.cvtColor(bgr, cv2.COLOR_BGR2HSV)[0][0]
        return tuple(int(v) for v in color_hsv)
    except Exception as e:
        logging.error(f"get_pixel_color_hsv({px}, {py}) - Error: {e}")
        return None

def is_color_initial(color_hsv):
    if color_hsv is None:
        return False
    c_h, c_s, c_v = color_hsv
    i_h, i_s, i_v = INITIAL_COLOR_HSV
    hue_diff = abs(c_h - i_h)
    hue_diff = min(hue_diff, 180 - hue_diff)
    sat_diff = abs(c_s - i_s)
    val_diff = abs(c_v - i_v)
    return (hue_diff <= TOLERANCE_H and sat_diff <= TOLERANCE_S and val_diff <= TOLERANCE_V)

def shoot():
    try:
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
        time.sleep(0.01)
        win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    except Exception as e:
        logging.error(f"[Shoot] Error: {e}")

def main_loop():
    global stop_script
    kb = threading.Thread(target=start_keyboard_listener, daemon=True)
    ms = threading.Thread(target=start_mouse_listener, daemon=True)
    kb.start()
    ms.start()
    try:
        while not stop_script:
            with lock:
                local_on = clicking_enabled
                local_rp = right_button_pressed
            if local_on and local_rp:
                current_hsv = get_pixel_color_hsv(x, y)
                if current_hsv is not None and not is_color_initial(current_hsv):
                    shoot()
                    time.sleep(SHOOT_INTERVAL)
            time.sleep(CHECK_INTERVAL)
    except Exception as e:
        logging.error(f"[Error] Exception: {e}")
        stop_script = True

# ========================== MATRIX BACKGROUND ===========================
class MatrixBackground:
    def __init__(self, width=600, height=500):
        self.width = width
        self.height = height
        self.characters = "01#@$%&*+-=[]{}|;:,.?!/\\~`^"
        self.columns = width // 12
        self.drops = [random.uniform(0, self.height) for _ in range(self.columns)]
        self.speeds = [random.uniform(2, 5) for _ in range(self.columns)]
        try:
            self.font = ImageFont.truetype("arial.ttf", 16)
        except:
            try:
                self.font = ImageFont.truetype("courier.ttf", 16)
            except:
                self.font = ImageFont.load_default()
    
    def update(self):
        for i in range(self.columns):
            self.drops[i] += self.speeds[i]
            if self.drops[i] > self.height:
                self.drops[i] = 0
                self.speeds[i] = random.uniform(2, 5)
    
    def get_frame(self):
        img = Image.new('RGB', (self.width, self.height), color=(0, 0, 0))
        draw = ImageDraw.Draw(img)
        for i in range(self.columns):
            y = int(self.drops[i])
            if 0 <= y < self.height:
                char = random.choice(self.characters)
                brightness = max(50, 255 - abs(y - self.height // 2) // 2)
                draw.text((i * 12, y), char, fill=(0, brightness, 0), font=self.font)
        return img

# ========================== LICENSE GATE ===========================
class NexarLicenseGate:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXAR - License Required")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#000000')
        self.matrix = MatrixBackground(600, 500)
        self.matrix_running = True

        self.canvas = tk.Canvas(root, bg='#000000', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_img = None

        self.overlay_frame = tk.Frame(root, bg='#000a00', relief=tk.FLAT, bd=0)
        self.canvas.create_window(300, 250, window=self.overlay_frame, width=420, height=260)
        
        content = tk.Frame(self.overlay_frame, bg='#000a00', padx=30, pady=30)
        content.pack(expand=True, fill=tk.BOTH)
        
        tk.Label(
            content, text="NEXAR", font=("Arial", 32, "bold"),
            fg='#00ff00', bg='#000a00'
        ).pack(pady=(0, 5))
        
        tk.Label(
            content, text="Enter License Key to unlock", font=("Arial", 11),
            fg='#00ff55', bg='#000a00'
        ).pack(pady=(0, 15))
        
        tk.Label(
            content, text="License Key:", font=("Arial", 11), fg="#00ff00", bg='#000a00'
        ).pack(anchor='w')
        
        self.entry = tk.Entry(
            content, font=("Arial", 12), bg="#001a00", fg="#00ff00", 
            insertbackground="#00ff00", bd=2, relief=tk.SOLID
        )
        self.entry.pack(fill=tk.X, pady=(5, 10))
        self.entry.bind('<Return>', lambda e: self.try_unlock())

        self.errorlabel = tk.Label(content, text="", fg="#ff3333", bg='#000a00', font=("Arial", 10))
        self.errorlabel.pack(pady=(0, 10))
        
        button_frame = tk.Frame(content, bg='#000a00')
        button_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.unlock_btn = tk.Button(
            button_frame, text="CHECK LICENSE", command=self.try_unlock,
            font=("Arial", 12, "bold"), bg="#003700", fg="#00ff00",
            activebackground="#1a6600", activeforeground="#00ffff",
            relief=tk.RAISED, bd=3, padx=20, pady=10, cursor="hand2"
        )
        self.unlock_btn.pack(fill=tk.X)
        
        self.start_matrix()

    def start_matrix(self):
        self.animation_thread = threading.Thread(target=self.run_matrix, daemon=True)
        self.animation_thread.start()

    def run_matrix(self):
        while self.matrix_running:
            try:
                self.matrix.update()
                frame = self.matrix.get_frame()
                self.bg_img = ImageTk.PhotoImage(frame)
                self.canvas.create_image(0, 0, anchor="nw", image=self.bg_img)
                self.root.update_idletasks()
                time.sleep(0.05)
            except:
                pass

    def try_unlock(self):
        lic = self.entry.get().strip()
        if not lic:
            self.errorlabel.config(text="X Please enter a license key")
            return
            
        if lic in VALID_LICENSES:
            with open(LICENSE_FILE, "w") as f:
                f.write(lic)
            self.errorlabel.config(text="+ License verified! Launching...", fg="#00ff00")
            self.matrix_running = False
            self.root.after(500, self.launch_app)
        else:
            self.errorlabel.config(text="X Invalid License Key", fg="#ff3333")
            self.entry.delete(0, tk.END)

    def launch_app(self):
        self.root.destroy()
        root2 = tk.Tk()
        NexarApp(root2)
        root2.mainloop()

# ========================== MAIN NEXAR APP ===========================
class NexarApp:
    def __init__(self, root):
        self.root = root
        self.root.title("NEXAR")
        self.root.geometry("600x500")
        self.root.resizable(False, False)
        self.root.configure(bg='#000000')
        self.matrix = MatrixBackground(600, 500)
        self.matrix_running = True
        
        self.canvas = tk.Canvas(root, bg='#000000', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.bg_img = None

        # Create notebook for tabs
        self.notebook = ttk.Notebook(root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=0, pady=0)
        
        # Configure notebook style
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#000a00', borderwidth=0)
        style.configure('TNotebook.Tab', background='#000a00', foreground='#00ff00', padding=[30, 10])
        style.map('TNotebook.Tab', background=[("selected", "#001a00"), ("active", "#000a00")])
        style.configure('TNotebook.Client', background='#000a00')
        
        # Create canvas for matrix background (behind tabs)
        self.bg_canvas = tk.Canvas(root, bg='#000000', highlightthickness=0)
        self.bg_canvas.place(x=0, y=0, relwidth=1, relheight=1)
        
        # Create overlay for matrix
        self.overlay_frame = tk.Frame(root, bg='#000a00')
        self.bg_canvas.create_window(300, 250, window=self.overlay_frame, width=600, height=500)
        
        # Tab 1: Main
        main_frame = tk.Frame(self.notebook, bg='#000a00')
        self.notebook.add(main_frame, text="MAIN")
        self.setup_main_tab(main_frame)
        
        # Tab 2: Settings
        settings_frame = tk.Frame(self.notebook, bg='#000a00')
        self.notebook.add(settings_frame, text="SETTINGS")
        self.setup_settings_tab(settings_frame)
        
        # Raise notebook to front
        self.notebook.lift()
        
        self.script_thread = None
        self.start_matrix()
        self.start_script()
        self.update_status()

    def setup_main_tab(self, parent):
        """Setup main tab content."""
        main_frame = tk.Frame(parent, bg='#000a00', padx=16, pady=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            main_frame, text="NEXAR", font=("Arial", 26, "bold"),
            fg='#00ff00', bg='#000a00'
        ).pack(pady=(0, 6))
        
        tk.Label(
            main_frame, text="========================", font=("Courier", 11),
            fg="#00bb00", bg="#000a00"
        ).pack()
        
        tk.Label(
            main_frame,
            text="Press 'Insert' -> Enable/Disable\nHold Right Mouse -> Shoot on target",
            justify="center",
            font=("Courier", 11), fg='#00ff00', bg='#000a00'
        ).pack(pady=5)
        
        tk.Label(
            main_frame, text="Status: Working", font=("Arial", 13, "bold"),
            fg="#00ff85", bg="#000a00"
        ).pack(pady=10)
        
        self.label_status = tk.Label(
            main_frame, text="Status: OFFLINE [*]", font=("Arial", 13, "bold"),
            fg="#ff2222", bg="#000a00"
        )
        self.label_status.pack(pady=3)
        
        tk.Frame(main_frame, height=2, bg='#00ff00').pack(fill=tk.X, pady=9)
        
        tk.Button(
            main_frame, text="TERMINATE", command=self.on_closing,
            font=("Arial", 11, "bold"), bg="#1a0000", fg="#ff0000",
            activebackground="#330000", activeforeground="#ff5555",
            relief=tk.FLAT, padx=12, pady=6, cursor="hand2"
        ).pack(fill=tk.X)

    def setup_settings_tab(self, parent):
        """Setup settings tab with background toggle."""
        settings_frame = tk.Frame(parent, bg='#000a00', padx=20, pady=20)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        tk.Label(
            settings_frame, text="SETTINGS", font=("Arial", 20, "bold"),
            fg='#00ff00', bg='#000a00'
        ).pack(pady=(0, 30))
        
        # Black background toggle
        toggle_frame = tk.Frame(settings_frame, bg='#000a00')
        toggle_frame.pack(fill=tk.X, pady=10)
        
        toggle_btn = tk.Button(
            toggle_frame, text="BACKGROUND BLACK", command=self.toggle_black_background,
            font=("Arial", 12, "bold"), bg="#003700", fg="#00ff00",
            activebackground="#1a6600", activeforeground="#00ffff",
            relief=tk.RAISED, bd=3, padx=15, pady=8, cursor="hand2"
        )
        toggle_btn.pack(fill=tk.X)
        
        # Info box with rounded appearance
        info_frame = tk.Frame(settings_frame, bg='#001a00', relief=tk.RAISED, bd=2)
        info_frame.pack(fill=tk.X, pady=(20, 0), padx=5)
        
        info_inner = tk.Frame(info_frame, bg='#000a00', padx=15, pady=12)
        info_inner.pack(fill=tk.BOTH, expand=True, padx=2, pady=2)
        
        status_text = "ENABLED" if settings["black_background"] else "DISABLED"
        status_color = "#00ff00" if settings["black_background"] else "#ff5555"
        
        tk.Label(
            info_inner, text=f"Status: {status_text}", font=("Arial", 11, "bold"),
            fg=status_color, bg='#000a00'
        ).pack(anchor='w', pady=(0, 8))
        
        tk.Label(
            info_inner, 
            text="When activated, creates a black overlay\non the window location only.\n\n"
                 "Effect: Only affects this monitor/window,\nnot your entire screen.",
            justify="left",
            font=("Courier", 10), fg='#00dd00', bg='#000a00'
        ).pack(anchor='w')
        
        self.status_label_settings = tk.Label(
            info_inner, text=f"Status: {status_text}", font=("Arial", 11, "bold"),
            fg=status_color, bg='#000a00'
        )
        # Store reference for updates
        self.info_status_label = tk.Label(
            info_inner, text=f"Status: {status_text}", font=("Arial", 11, "bold"),
            fg=status_color, bg='#000a00'
        )
        self.info_status_label.pack(anchor='w', pady=(8, 0))

    def toggle_black_background(self):
        """Toggle black background setting."""
        global settings
        settings["black_background"] = not settings["black_background"]
        save_settings()
        
        # Update info label
        status_text = "ENABLED" if settings["black_background"] else "DISABLED"
        status_color = "#00ff00" if settings["black_background"] else "#ff5555"
        
        # Show notification
        messagebox.showinfo(
            "Settings Updated",
            f"Black Background: {status_text}\n\nThe overlay will be applied to the window area."
        )

    def start_matrix(self):
        self.animation_thread = threading.Thread(target=self.run_matrix, daemon=True)
        self.animation_thread.start()

    def run_matrix(self):
        while self.matrix_running and not stop_script:
            try:
                self.matrix.update()
                frame = self.matrix.get_frame()
                self.bg_img = ImageTk.PhotoImage(frame)
                self.bg_canvas.create_image(0, 0, anchor="nw", image=self.bg_img)
                
                # Create black overlay if enabled
                if settings["black_background"]:
                    self.bg_canvas.create_rectangle(
                        0, 0, 600, 500, 
                        fill='#000000', outline='#000000'
                    )
                
                self.root.update_idletasks()
                time.sleep(0.05)
            except:
                pass

    def start_script(self):
        global stop_script
        if self.script_thread is None or not self.script_thread.is_alive():
            stop_script = False
            self.script_thread = threading.Thread(target=main_loop, daemon=True)
            self.script_thread.start()

    def update_status(self):
        with lock:
            local_on = clicking_enabled
        if local_on:
            self.label_status.config(text="Status: ONLINE [+]", fg='#00ff00')
        else:
            self.label_status.config(text="Status: OFFLINE [*]", fg='#ff0000')
        if not stop_script:
            self.root.after(500, self.update_status)

    def on_closing(self):
        self.stop_script()
        self.matrix_running = False
        self.root.destroy()

    def stop_script(self):
        global stop_script
        stop_script = True

def main():
    load_settings()
    
    # Check if license already saved
    if os.path.exists(LICENSE_FILE):
        try:
            with open(LICENSE_FILE) as f:
                license_saved = f.read().strip()
            if license_saved in VALID_LICENSES:
                root = tk.Tk()
                NexarApp(root)
                root.mainloop()
                return
        except:
            pass
    
    # Show license gate
    root = tk.Tk()
    NexarLicenseGate(root)
    root.mainloop()

if __name__ == "__main__":
    main()