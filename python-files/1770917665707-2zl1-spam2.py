import pyautogui
import pyperclip
import time
import threading
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import platform
import os
import random
from datetime import datetime

class MegaSpamToolbox:
    def __init__(self, root):
        self.root = root
        self.root.title("🤖 MEGA SPAM TOOLBOX - INSTANT SEND FIXED")
        self.root.geometry("950x850")
        self.root.resizable(True, True)
        self.root.configure(bg='#1a1a2e')
        
        # Variables
        self.is_running = False
        self.stop_spam = False
        self.total_sent = 0
        
        # Color scheme
        self.bg_color = '#1a1a2e'
        self.card_color = '#16213e'
        self.accent_color = '#0f3460'
        self.button_color = '#e94560'
        self.success_color = '#4CAF50'
        self.text_color = '#ffffff'
        
        self.setup_ui()
        
    def setup_ui(self):
        # ========== MAIN CANVAS WITH SCROLLBAR ==========
        main_canvas = tk.Canvas(self.root, bg=self.bg_color, highlightthickness=0)
        main_scrollbar = tk.Scrollbar(self.root, orient="vertical", command=main_canvas.yview)
        main_canvas.configure(yscrollcommand=main_scrollbar.set)
        
        main_canvas.pack(side="left", fill="both", expand=True)
        main_scrollbar.pack(side="right", fill="y")
        
        scrollable_frame = tk.Frame(main_canvas, bg=self.bg_color)
        scrollable_frame.bind("<Configure>", lambda e: main_canvas.configure(scrollregion=main_canvas.bbox("all")))
        
        def on_mousewheel(event):
            main_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        
        def on_enter(event):
            main_canvas.bind_all("<MouseWheel>", on_mousewheel)
        
        def on_leave(event):
            main_canvas.unbind_all("<MouseWheel>")
        
        scrollable_frame.bind("<Enter>", on_enter)
        scrollable_frame.bind("<Leave>", on_leave)
        
        canvas_window = main_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=main_canvas.winfo_width())
        
        def configure_canvas(event):
            main_canvas.itemconfig(canvas_window, width=event.width)
        main_canvas.bind('<Configure>', configure_canvas)
        
        # ========== MAIN CONTAINER ==========
        main_frame = tk.Frame(scrollable_frame, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # ========== HEADER ==========
        header_frame = tk.Frame(main_frame, bg=self.bg_color)
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        title_label = tk.Label(header_frame, 
                              text="⚡ MEGA SPAM TOOLBOX - INSTANT SEND ⚡", 
                              font=('Arial', 20, 'bold'),
                              bg=self.bg_color,
                              fg='#ffffff')
        title_label.pack()
        
        subtitle_label = tk.Label(header_frame,
                                text="✅ FIXED: Messages appear INSTANTLY | Zero Delay Technology",
                                font=('Arial', 11),
                                bg=self.bg_color,
                                fg='#4CAF50')
        subtitle_label.pack()
        
        # ========== TOOL SELECTION CARD ==========
        tool_card = self.create_card(main_frame, "🎯 SELECT YOUR TOOL")
        tool_card.pack(fill=tk.X, pady=(0, 20))
        
        tool_container = tk.Frame(tool_card, bg=self.card_color)
        tool_container.pack(padx=20, pady=20)
        
        tk.Label(tool_container, text="Choose Tool:", 
                font=('Arial', 12, 'bold'),
                bg=self.card_color, 
                fg=self.text_color).pack(anchor='w')
        
        self.tool_var = tk.StringVar()
        tools = [
            "📱 Tool 1: Normal Spam - Simple Message Repeat",
            "🔄 Tool 2: Line Rotation - Send Lines in Sequence", 
            "🔢 Tool 3: Numbered Spam - Auto Numbering System",
            "🎲 Tool 4: Random Mix - Smart Message Combiner"
        ]
        
        tool_dropdown = ttk.Combobox(tool_container, 
                                    textvariable=self.tool_var,
                                    values=tools,
                                    state='readonly',
                                    width=70,
                                    font=('Arial', 11))
        tool_dropdown.pack(pady=(10, 5))
        tool_dropdown.current(0)
        tool_dropdown.bind('<<ComboboxSelected>>', self.on_tool_change)
        
        self.tool_desc_var = tk.StringVar(value="📱 Normal Spam: Sends the same message repeatedly - INSTANT SEND")
        tool_desc = tk.Label(tool_container, 
                           textvariable=self.tool_desc_var,
                           font=('Arial', 10, 'italic'),
                           bg=self.card_color,
                           fg='#a0d0ff')
        tool_desc.pack(pady=(10, 0))
        
        # ========== MESSAGE INPUT CARD ==========
        msg_card = self.create_card(main_frame, "💬 MESSAGE INPUT")
        msg_card.pack(fill=tk.X, pady=(0, 20))
        
        msg_container = tk.Frame(msg_card, bg=self.card_color)
        msg_container.pack(padx=20, pady=20)
        
        tk.Label(msg_container, text="Enter your message/lines below:",
                font=('Arial', 11, 'bold'),
                bg=self.card_color,
                fg=self.text_color).pack(anchor='w')
        
        text_frame = tk.Frame(msg_container, bg=self.card_color)
        text_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        self.message_text = scrolledtext.ScrolledText(text_frame,
                                                     height=6,
                                                     width=70,
                                                     font=('Arial', 11),
                                                     wrap=tk.WORD,
                                                     bg='#0a0e1a',
                                                     fg='#ffffff',
                                                     insertbackground='white',
                                                     relief=tk.FLAT,
                                                     borderwidth=2)
        self.message_text.pack(fill=tk.BOTH, expand=True)
        
        self.char_count_var = tk.StringVar(value="Characters: 0 | Lines: 0")
        char_label = tk.Label(msg_container, 
                            textvariable=self.char_count_var,
                            font=('Arial', 9),
                            bg=self.card_color,
                            fg='#a0a0a0')
        char_label.pack(anchor='e', pady=(5, 0))
        
        self.message_text.bind('<KeyRelease>', self.update_char_count)
        
        # ========== CONTROL PANEL CARD ==========
        control_card = self.create_card(main_frame, "⚙️ CONTROL PANEL")
        control_card.pack(fill=tk.X, pady=(0, 20))
        
        control_container = tk.Frame(control_card, bg=self.card_color)
        control_container.pack(padx=20, pady=20)
        
        # Input Grid
        input_frame = tk.Frame(control_container, bg=self.card_color)
        input_frame.pack(fill=tk.X)
        
        # Row 1: Start Delay
        tk.Label(input_frame, text="⏰ Start Delay:", 
                font=('Arial', 10),
                bg=self.card_color,
                fg=self.text_color).grid(row=0, column=0, sticky='w', padx=10, pady=10)
        
        self.start_delay = tk.IntVar(value=3)  # Reduced to 3 seconds
        delay_spinbox = tk.Spinbox(input_frame, from_=1, to=30,
                                  textvariable=self.start_delay,
                                  width=10, font=('Arial', 10),
                                  bg='#0a0e1a', fg='white',
                                  relief=tk.FLAT, buttonbackground='#0f3460')
        delay_spinbox.grid(row=0, column=1, padx=10, pady=10)
        tk.Label(input_frame, text="seconds", 
                font=('Arial', 9),
                bg=self.card_color,
                fg='#a0a0a0').grid(row=0, column=2, sticky='w', padx=5, pady=10)
        
        # Row 2: How Many Times
        tk.Label(input_frame, text="🔢 How Many Times:", 
                font=('Arial', 10),
                bg=self.card_color,
                fg=self.text_color).grid(row=1, column=0, sticky='w', padx=10, pady=10)
        
        self.repeat_count = tk.IntVar(value=100)
        count_spinbox = tk.Spinbox(input_frame, from_=1, to=9999,
                                  textvariable=self.repeat_count,
                                  width=10, font=('Arial', 10),
                                  bg='#0a0e1a', fg='white',
                                  relief=tk.FLAT, buttonbackground='#0f3460')
        count_spinbox.grid(row=1, column=1, padx=10, pady=10)
        tk.Label(input_frame, text="messages", 
                font=('Arial', 9),
                bg=self.card_color,
                fg='#a0a0a0').grid(row=1, column=2, sticky='w', padx=5, pady=10)
        
        # Row 3: Delay Between (INSTANT OPTION ADDED)
        tk.Label(input_frame, text="⏱️ Delay Between:", 
                font=('Arial', 10),
                bg=self.card_color,
                fg=self.text_color).grid(row=2, column=0, sticky='w', padx=10, pady=10)
        
        self.msg_delay = tk.DoubleVar(value=0.01)  # REDUCED to 0.01 for INSTANT send
        delay_between = tk.Spinbox(input_frame, from_=0.0, to=1.0, increment=0.01,
                                  textvariable=self.msg_delay,
                                  width=10, font=('Arial', 10),
                                  bg='#0a0e1a', fg='white',
                                  relief=tk.FLAT, buttonbackground='#0f3460')
        delay_between.grid(row=2, column=1, padx=10, pady=10)
        tk.Label(input_frame, text="seconds", 
                font=('Arial', 9),
                bg=self.card_color,
                fg='#a0a0a0').grid(row=2, column=2, sticky='w', padx=5, pady=10)
        
        # Speed Presets - ADDED INSTANT OPTION
        speed_frame = tk.Frame(control_container, bg=self.card_color)
        speed_frame.pack(pady=(15, 0))
        
        tk.Label(speed_frame, text="⚡ Speed Presets:", 
                font=('Arial', 10, 'bold'),
                bg=self.card_color,
                fg=self.text_color).pack(side=tk.LEFT, padx=(0, 10))
        
        speeds = [("🐢 Slow", 0.2), ("⚡ Normal", 0.05), ("🚀 Fast", 0.02), ("💨 INSTANT", 0.005)]
        for text, value in speeds:
            btn = tk.Button(speed_frame, text=text,
                          bg='#0f3460', fg='white',
                          font=('Arial', 9),
                          relief=tk.FLAT, padx=10, cursor='hand2',
                          command=lambda v=value: self.msg_delay.set(v))
            btn.pack(side=tk.LEFT, padx=5)
        
        # INSTANT SEND HINT
        instant_hint = tk.Label(control_container,
                               text="⚡ INSTANT MODE: Set delay to 0.005 for messages that appear immediately!",
                               font=('Arial', 9, 'bold'),
                               bg=self.card_color,
                               fg='#FFD700')
        instant_hint.pack(pady=(10, 0))
        
        # ========== ACTION BUTTONS ==========
        action_card = self.create_card(main_frame, "🎮 ACTION CENTER")
        action_card.pack(fill=tk.X, pady=(0, 20))
        
        action_container = tk.Frame(action_card, bg=self.card_color)
        action_container.pack(pady=20)
        
        btn_frame = tk.Frame(action_container, bg=self.card_color)
        btn_frame.pack()
        
        # Send Button
        self.send_btn = tk.Button(btn_frame, 
                                 text="📤 SEND MESSAGES",
                                 font=('Arial', 14, 'bold'),
                                 bg='#4CAF50',
                                 fg='white',
                                 width=20,
                                 height=2,
                                 relief=tk.FLAT,
                                 cursor='hand2',
                                 command=self.start_spamming)
        self.send_btn.pack(side=tk.LEFT, padx=10)
        
        # Stop Button
        self.stop_btn = tk.Button(btn_frame,
                                 text="⏹️ STOP",
                                 font=('Arial', 14, 'bold'),
                                 bg='#e94560',
                                 fg='white',
                                 width=15,
                                 height=2,
                                 relief=tk.FLAT,
                                 cursor='hand2',
                                 state=tk.DISABLED,
                                 command=self.stop_spamming)
        self.stop_btn.pack(side=tk.LEFT, padx=10)
        
        # Clear Button
        self.clear_btn = tk.Button(btn_frame,
                                  text="🗑️ CLEAR",
                                  font=('Arial', 12, 'bold'),
                                  bg='#7f8c8d',
                                  fg='white',
                                  width=12,
                                  height=1,
                                  relief=tk.FLAT,
                                  cursor='hand2',
                                  command=self.clear_all)
        self.clear_btn.pack(side=tk.LEFT, padx=10)
        
        # ========== PROGRESS & STATUS ==========
        progress_card = self.create_card(main_frame, "📊 PROGRESS TRACKER")
        progress_card.pack(fill=tk.X)
        
        progress_container = tk.Frame(progress_card, bg=self.card_color)
        progress_container.pack(padx=20, pady=20)
        
        # Progress Bar
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("green.Horizontal.TProgressbar",
                       background='#4CAF50',
                       troughcolor='#0a0e1a',
                       bordercolor='#0a0e1a',
                       lightcolor='#4CAF50',
                       darkcolor='#4CAF50')
        
        self.progress = ttk.Progressbar(progress_container,
                                       style="green.Horizontal.TProgressbar",
                                       length=700,
                                       mode='determinate')
        self.progress.pack(pady=(0, 15))
        
        status_frame = tk.Frame(progress_container, bg=self.card_color)
        status_frame.pack(fill=tk.X)
        
        self.status_label = tk.Label(status_frame,
                                    text="✅ Ready to spam - INSTANT MODE ACTIVE",
                                    font=('Arial', 11, 'bold'),
                                    bg=self.card_color,
                                    fg='#4CAF50')
        self.status_label.pack(side=tk.LEFT)
        
        self.counter_var = tk.StringVar(value="0/0 messages sent")
        counter_label = tk.Label(status_frame,
                               textvariable=self.counter_var,
                               font=('Arial', 11, 'bold'),
                               bg=self.card_color,
                               fg='#ffffff')
        counter_label.pack(side=tk.RIGHT)
        
        self.large_counter_var = tk.StringVar(value="0/100")
        large_counter = tk.Label(progress_container,
                               textvariable=self.large_counter_var,
                               font=('Arial', 24, 'bold'),
                               bg=self.card_color,
                               fg='#4CAF50')
        large_counter.pack(pady=(10, 0))
        
        self.total_sent_var = tk.StringVar(value="Total Messages Sent This Session: 0")
        total_label = tk.Label(progress_container,
                             textvariable=self.total_sent_var,
                             font=('Arial', 10),
                             bg=self.card_color,
                             fg='#a0a0a0')
        total_label.pack(pady=(5, 0))
        
        # Load default message
        self.load_default_message()
        self.update_char_count()
        
    def create_card(self, parent, title):
        """Create modern card"""
        card = tk.Frame(parent, bg=self.accent_color,
                       highlightbackground='#0a0e1a',
                       highlightthickness=2,
                       relief=tk.FLAT)
        
        header = tk.Frame(card, bg='#0f3460', height=40)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        tk.Label(header, text=title,
                font=('Arial', 12, 'bold'),
                bg='#0f3460',
                fg='white').pack(side=tk.LEFT, padx=15, pady=8)
        
        return card
    
    def on_tool_change(self, event=None):
        """Update tool description"""
        tool = self.tool_var.get()
        descriptions = {
            "📱 Tool 1: Normal Spam - Simple Message Repeat": "📱 NORMAL SPAM: Sends the same message repeatedly - INSTANT SEND",
            "🔄 Tool 2: Line Rotation - Send Lines in Sequence": "🔄 LINE ROTATION: Sends each line one by one in sequence - INSTANT SEND",
            "🔢 Tool 3: Numbered Spam - Auto Numbering System": "🔢 NUMBERED SPAM: Automatically adds numbers (1., 2., 3.) - INSTANT SEND",
            "🎲 Tool 4: Random Mix - Smart Message Combiner": "🎲 RANDOM MIX: Randomly combines words - INSTANT SEND"
        }
        self.tool_desc_var.set(descriptions.get(tool, ""))
        self.update_char_count()
    
    def update_char_count(self, event=None):
        """Update character and line count"""
        text = self.message_text.get('1.0', tk.END).strip()
        chars = len(text)
        lines = len(text.split('\n')) if text else 0
        self.char_count_var.set(f"Characters: {chars} | Lines: {lines}")
    
    def load_default_message(self):
        """Load default message"""
        default_msg = """Hello! This is an INSTANT message!
Messages now appear immediately - No delay!
Try the INSTANT mode for fastest sending."""
        self.message_text.insert('1.0', default_msg)
    
    def generate_messages(self):
        """Generate messages based on selected tool"""
        tool = self.tool_var.get()
        text = self.message_text.get('1.0', tk.END).strip()
        total = self.repeat_count.get()
        messages = []
        
        # TOOL 1: NORMAL SPAM
        if "Tool 1" in tool:
            for i in range(total):
                messages.append(text)
        
        # TOOL 2: LINE ROTATION
        elif "Tool 2" in tool:
            lines = [line.strip() for line in text.split('\n') if line.strip()]
            if not lines:
                lines = [text]
            for i in range(total):
                messages.append(lines[i % len(lines)])
        
        # TOOL 3: NUMBERED SPAM
        elif "Tool 3" in tool:
            for i in range(total):
                messages.append(f"{i+1}. {text}")
        
        # TOOL 4: RANDOM MIX
        elif "Tool 4" in tool:
            words = text.split()
            for i in range(total):
                if words:
                    random.shuffle(words)
                    random_msg = ' '.join(words[:min(3, len(words))])
                    messages.append(f"🎲 {random_msg}")
                else:
                    messages.append(f"🎲 #{i+1}")
        
        return messages
    
    def start_spamming(self):
        """Start spamming"""
        if not self.is_running:
            text = self.message_text.get('1.0', tk.END).strip()
            if not text:
                messagebox.showerror("Error", "❌ Please enter a message!")
                return
            
            self.is_running = True
            self.stop_spam = False
            self.total_sent = 0
            
            self.send_btn.config(state=tk.DISABLED, bg='#2d6a4f')
            self.stop_btn.config(state=tk.NORMAL)
            
            self.status_label.config(text="⏳ Preparing...", fg='#FFC107')
            self.large_counter_var.set(f"0/{self.repeat_count.get()}")
            self.counter_var.set(f"0/{self.repeat_count.get()} messages sent")
            
            spam_thread = threading.Thread(target=self.spam_messages, daemon=True)
            spam_thread.start()
    
    def stop_spamming(self):
        """Stop spamming"""
        self.stop_spam = True
        self.status_label.config(text="⏹️ Stopping...", fg='#e94560')
    
    def spam_messages(self):
        """Main spam function - OPTIMIZED FOR INSTANT SEND"""
        try:
            total = self.repeat_count.get()
            messages = self.generate_messages()
            
            self.progress['maximum'] = total
            self.progress['value'] = 0
            
            # FIXED: Reduced countdown to 1 second
            for i in range(min(self.start_delay.get(), 3), 0, -1):
                if self.stop_spam:
                    return
                self.status_label.config(text=f"⏳ Starting in {i} seconds...")
                self.large_counter_var.set(f"0/{total}")
                time.sleep(1)
            
            self.status_label.config(text="🚀 Sending INSTANT messages...", fg='#4CAF50')
            
            # FIXED: Ultra-fast sending with minimal delays
            for i in range(total):
                if self.stop_spam:
                    break
                
                message = messages[i]
                
                # OPTIMIZED: Minimal delays for instant appearance
                pyperclip.copy(message)
                time.sleep(0.001)  # 1ms delay
                self.paste_text()
                time.sleep(0.001)  # 1ms delay
                pyautogui.press('enter')
                
                self.total_sent += 1
                
                # Update UI less frequently for speed
                if i % 5 == 0 or i == total - 1:
                    self.progress['value'] = i + 1
                    self.large_counter_var.set(f"{i+1}/{total}")
                    self.counter_var.set(f"{i+1}/{total} messages sent")
                    self.total_sent_var.set(f"Total Messages Sent This Session: {self.total_sent}")
                    self.root.update_idletasks()
                
                time.sleep(self.msg_delay.get())
            
            if not self.stop_spam:
                self.status_label.config(text="✅ Complete! All messages sent INSTANTLY!", fg='#4CAF50')
                messagebox.showinfo("Success", f"✅ Successfully sent {total} messages INSTANTLY!")
            else:
                self.status_label.config(text="⏹️ Stopped by user", fg='#e94560')
            
        except Exception as e:
            messagebox.showerror("Error", f"❌ Error: {str(e)}")
            self.status_label.config(text="❌ Error occurred!", fg='#e94560')
        finally:
            self.is_running = False
            self.send_btn.config(state=tk.NORMAL, bg='#4CAF50')
            self.stop_btn.config(state=tk.DISABLED)
    
    def paste_text(self):
        """OPTIMIZED paste function"""
        try:
            if platform.system() == "Darwin":
                pyautogui.hotkey('command', 'v')
            else:
                # FIXED: Direct key press for faster paste
                pyautogui.keyDown('ctrl')
                pyautogui.press('v')
                pyautogui.keyUp('ctrl')
        except:
            pass
    
    def clear_all(self):
        """Clear all inputs"""
        self.message_text.delete('1.0', tk.END)
        self.load_default_message()
        self.start_delay.set(3)
        self.repeat_count.set(100)
        self.msg_delay.set(0.01)
        self.total_sent = 0
        self.total_sent_var.set("Total Messages Sent This Session: 0")
        self.counter_var.set("0/0 messages sent")
        self.large_counter_var.set("0/100")
        self.progress['value'] = 0
        self.status_label.config(text="✅ Cleared - INSTANT MODE READY", fg='#4CAF50')
        self.update_char_count()

def main():
    root = tk.Tk()
    app = MegaSpamToolbox(root)
    
    def on_closing():
        if app.is_running:
            if messagebox.askyesno("Quit", "⚠️ Spamming in progress! Quit anyway?"):
                app.stop_spam = True
                root.destroy()
        else:
            root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

if __name__ == "__main__":
    main()