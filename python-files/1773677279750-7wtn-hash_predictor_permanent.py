"""
SHA HASH PREDICTOR WITH AUTO-SEED GENERATION
LIFETIME VERSION - NO EXPIRY - PERMANENT LICENSE
Created: 2024
This software has no time limits, no expiry date, and works forever.
"""

import hashlib
import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
import random
import json
import os
import sys
from datetime import datetime
import secrets
import webbrowser

class PermanentHashPredictor:
    """
    PERMANENT APPLICATION - NEVER EXPIRES
    No time bombs, no expiry checks, no validation servers
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("⚡ SHA HASH PREDICTOR - LIFETIME EDITION ⚡")
        self.root.geometry("900x700")
        self.root.resizable(False, False)
        
        # Set window icon (optional - you can add your own .ico file)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass
        
        # Configure colors - Professional dark theme
        self.root.configure(bg='#0a0a0a')
        
        # Application state (persists forever)
        self.server_seed = self.generate_server_seed()
        self.client_seed = self.load_client_seed()  # Load saved seed
        self.nonce = self.load_nonce()  # Load saved nonce
        self.predictions = self.load_history()  # Load prediction history
        self.auto_predict = False
        self.theme_color = '#00ffff'  # Default cyan theme
        
        # Setup UI
        self.setup_ui()
        self.update_displays()
        
        # Show license info (permanent)
        self.show_license_notice()
        
    def generate_server_seed(self):
        """Generate cryptographically secure server seed"""
        return secrets.token_hex(32)
    
    def load_client_seed(self):
        """Load saved client seed or create default"""
        try:
            if os.path.exists('predictor_config.json'):
                with open('predictor_config.json', 'r') as f:
                    config = json.load(f)
                    return config.get('client_seed', '00000000000000000000000000000000')
        except:
            pass
        return '00000000000000000000000000000000'
    
    def load_nonce(self):
        """Load saved nonce"""
        try:
            if os.path.exists('predictor_config.json'):
                with open('predictor_config.json', 'r') as f:
                    config = json.load(f)
                    return config.get('nonce', 0)
        except:
            pass
        return 0
    
    def load_history(self):
        """Load prediction history"""
        try:
            if os.path.exists('predictor_history.json'):
                with open('predictor_history.json', 'r') as f:
                    return json.load(f)
        except:
            pass
        return []
    
    def save_state(self):
        """Save application state (permanent storage)"""
        try:
            # Save config
            config = {
                'client_seed': self.client_seed,
                'nonce': self.nonce,
                'last_saved': str(datetime.now())
            }
            with open('predictor_config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            # Save history (last 1000 predictions)
            with open('predictor_history.json', 'w') as f:
                json.dump(self.predictions[-1000:], f, indent=2)
        except:
            pass
    
    def setup_ui(self):
        # Main container
        main_frame = tk.Frame(self.root, bg='#0a0a0a', padx=30, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Header with lifetime badge
        header_frame = tk.Frame(main_frame, bg='#0a0a0a')
        header_frame.pack(fill='x', pady=(0, 20))
        
        # Title
        title_label = tk.Label(
            header_frame,
            text="🔮 SHA HASH PREDICTOR",
            font=('Arial', 24, 'bold'),
            fg='#00ffff',
            bg='#0a0a0a'
        )
        title_label.pack()
        
        # Lifetime badge
        badge_frame = tk.Frame(header_frame, bg='#00aa00', padx=10, pady=5)
        badge_frame.pack(pady=5)
        
        badge_label = tk.Label(
            badge_frame,
            text="⚡ LIFETIME LICENSE - ACTIVATED PERMANENTLY ⚡",
            font=('Arial', 10, 'bold'),
            fg='white',
            bg='#00aa00'
        )
        badge_label.pack()
        
        # Server Seed Section
        seed_frame = self.create_section(
            main_frame, 
            "🎲 SERVER SEED (AUTO-GENERATED)",
            "#ffaa00"
        )
        seed_frame.pack(fill='x', pady=5)
        
        # Server seed display
        seed_display_frame = tk.Frame(seed_frame, bg='#1a1a1a')
        seed_display_frame.pack(fill='x', pady=5)
        
        self.seed_display = tk.Text(
            seed_display_frame,
            height=2,
            font=('Courier', 10),
            bg='#000000',
            fg='#00ff00',
            wrap=tk.WORD,
            relief='flat'
        )
        self.seed_display.pack(side='left', fill='x', expand=True, padx=(0, 5))
        
        # Seed buttons
        seed_btn_frame = tk.Frame(seed_display_frame, bg='#1a1a1a')
        seed_btn_frame.pack(side='right')
        
        self.create_button(seed_btn_frame, "🔄 New", self.regenerate_seed, '#ffaa00', width=8)
        self.create_button(seed_btn_frame, "📋 Copy", self.copy_seed, '#333333', width=8)
        
        # Client Seed Section
        client_frame = self.create_section(
            main_frame,
            "🎯 CLIENT SEED (YOUR PERSONAL SEED)",
            "#00aaff"
        )
        client_frame.pack(fill='x', pady=5)
        
        client_input_frame = tk.Frame(client_frame, bg='#1a1a1a')
        client_input_frame.pack(fill='x', pady=5)
        
        self.client_entry = tk.Entry(
            client_input_frame,
            font=('Courier', 11),
            bg='#000000',
            fg='#00aaff',
            insertbackground='white',
            relief='flat'
        )
        self.client_entry.pack(side='left', fill='x', expand=True, padx=(0, 5))
        self.client_entry.insert(0, self.client_seed)
        
        self.create_button(client_input_frame, "Set Seed", self.set_client_seed, '#00aaff')
        
        # Nonce Counter
        nonce_frame = tk.Frame(client_frame, bg='#1a1a1a')
        nonce_frame.pack(fill='x', pady=5)
        
        tk.Label(
            nonce_frame,
            text="Current Nonce:",
            font=('Arial', 11),
            fg='#aaaaaa',
            bg='#1a1a1a'
        ).pack(side='left')
        
        self.nonce_label = tk.Label(
            nonce_frame,
            text=str(self.nonce),
            font=('Arial', 16, 'bold'),
            fg='#ffff00',
            bg='#1a1a1a'
        )
        self.nonce_label.pack(side='left', padx=10)
        
        self.create_button(nonce_frame, "Reset Nonce", self.reset_nonce, '#ff6600')
        
        # Prediction Zone
        pred_frame = self.create_section(
            main_frame,
            "🔮 PREDICTION ZONE",
            "#ff00ff",
            expand=True
        )
        pred_frame.pack(fill='both', expand=True, pady=10)
        
        # Current Hash
        hash_frame = tk.Frame(pred_frame, bg='#1a1a1a')
        hash_frame.pack(fill='x', pady=5)
        
        tk.Label(
            hash_frame,
            text="Current Hash:",
            font=('Arial', 10),
            fg='#aaaaaa',
            bg='#1a1a1a'
        ).pack(anchor='w')
        
        self.hash_display = tk.Text(
            hash_frame,
            height=2,
            font=('Courier', 9),
            bg='#000000',
            fg='#ff00ff',
            wrap=tk.WORD,
            relief='flat'
        )
        self.hash_display.pack(fill='x', pady=2)
        
        # BIG PREDICTION NUMBER
        number_frame = tk.Frame(pred_frame, bg='#1a1a1a')
        number_frame.pack(fill='x', pady=15)
        
        tk.Label(
            number_frame,
            text="🎰 PREDICTED NUMBER:",
            font=('Arial', 18, 'bold'),
            fg='#00ff00',
            bg='#1a1a1a'
        ).pack()
        
        # Large prediction display
        self.prediction_display = tk.Label(
            number_frame,
            text="???",
            font=('Arial', 56, 'bold'),
            fg='#ffff00',
            bg='#000000',
            width=8,
            height=2,
            relief='ridge',
            bd=5
        )
        self.prediction_display.pack(pady=15)
        
        # Control Buttons
        btn_frame = tk.Frame(pred_frame, bg='#1a1a1a')
        btn_frame.pack(pady=10)
        
        self.predict_btn = self.create_button(
            btn_frame,
            "🎯 PREDICT NEXT NUMBER",
            self.predict_next,
            '#00aa00',
            font_size=14,
            padx=30,
            pady=12,
            width=20
        )
        self.predict_btn.pack(side='left', padx=5)
        
        self.auto_btn = self.create_button(
            btn_frame,
            "⚡ AUTO MODE",
            self.toggle_auto,
            '#ffaa00',
            font_size=12,
            padx=20,
            pady=8,
            width=12
        )
        self.auto_btn.pack(side='left', padx=5)
        
        # Statistics
        stats_frame = tk.Frame(pred_frame, bg='#1a1a1a')
        stats_frame.pack(fill='x', pady=5)
        
        self.stats_label = tk.Label(
            stats_frame,
            text=f"Total Predictions: {len(self.predictions)} | Last Nonce: {self.nonce-1 if self.nonce > 0 else 0}",
            font=('Arial', 10),
            fg='#aaaaaa',
            bg='#1a1a1a'
        )
        self.stats_label.pack()
        
        # History
        history_frame = tk.Frame(pred_frame, bg='#1a1a1a')
        history_frame.pack(fill='x', pady=5)
        
        tk.Label(
            history_frame,
            text="Recent Predictions:",
            font=('Arial', 10, 'bold'),
            fg='#aaaaaa',
            bg='#1a1a1a'
        ).pack(anchor='w')
        
        self.history_text = tk.Text(
            history_frame,
            height=4,
            font=('Courier', 9),
            bg='#000000',
            fg='#888888',
            wrap=tk.WORD,
            relief='flat'
        )
        self.history_text.pack(fill='x', pady=2)
        
        # Footer with permanent license
        footer_frame = tk.Frame(main_frame, bg='#0a0a0a')
        footer_frame.pack(side='bottom', fill='x', pady=10)
        
        license_text = tk.Label(
            footer_frame,
            text="✓ PERMANENT LICENSE - ACTIVATED FOREVER - NO EXPIRY ✓",
            font=('Arial', 9, 'bold'),
            fg='#00ff00',
            bg='#0a0a0a'
        )
        license_text.pack()
        
        copyright_text = tk.Label(
            footer_frame,
            text="This software has no time limits. Use indefinitely on any computer.",
            font=('Arial', 8),
            fg='#666666',
            bg='#0a0a0a'
        )
        copyright_text.pack()
    
    def create_section(self, parent, title, color, expand=False):
        """Create a labeled section frame"""
        frame = tk.LabelFrame(
            parent,
            text=title,
            font=('Arial', 11, 'bold'),
            fg=color,
            bg='#1a1a1a',
            padx=15,
            pady=10
        )
        return frame
    
    def create_button(self, parent, text, command, color, font_size=10, padx=10, pady=5, width=None):
        """Create styled button"""
        btn = tk.Button(
            parent,
            text=text,
            command=command,
            bg=color,
            fg='white' if color != '#ffaa00' else 'black',
            font=('Arial', font_size, 'bold'),
            padx=padx,
            pady=pady,
            width=width,
            relief='raised',
            bd=2
        )
        return btn
    
    def show_license_notice(self):
        """Show permanent license notification (only once)"""
        if not os.path.exists('.license_shown'):
            messagebox.showinfo(
                "PERMANENT LICENSE ACTIVATED",
                "✅ This software has been activated with a PERMANENT license.\n\n"
                "• No expiry date\n"
                "• No time limits\n"
                "• Works forever\n"
                "• Can be used on any computer\n"
                "• No activation required\n\n"
                "Thank you for using SHA Hash Predictor!"
            )
            # Create flag file
            with open('.license_shown', 'w') as f:
                f.write('shown')
    
    def update_displays(self):
        """Update all displays"""
        self.seed_display.delete('1.0', tk.END)
        self.seed_display.insert('1.0', self.server_seed)
        self.nonce_label.config(text=str(self.nonce))
        self.update_history()
        self.update_stats()
    
    def regenerate_seed(self):
        """Generate new server seed"""
        self.server_seed = self.generate_server_seed()
        self.nonce = 0
        self.predictions = []
        self.update_displays()
        self.prediction_display.config(text="???", fg='#ffff00')
        self.hash_display.delete('1.0', tk.END)
        self.save_state()
        messagebox.showinfo("Seed Regenerated", "New server seed generated!\nNonce reset to 0.")
    
    def copy_seed(self):
        """Copy seed to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.server_seed)
        messagebox.showinfo("Copied", "Server seed copied to clipboard!")
    
    def set_client_seed(self):
        """Set custom client seed"""
        new_seed = self.client_entry.get().strip()
        if len(new_seed) < 4:
            messagebox.showerror("Error", "Client seed must be at least 4 characters")
            return
        self.client_seed = new_seed
        self.nonce = 0
        self.predictions = []
        self.update_displays()
        self.prediction_display.config(text="???")
        self.hash_display.delete('1.0', tk.END)
        self.save_state()
        messagebox.showinfo("Client Seed Set", f"Client seed set to: {new_seed}\nNonce reset to 0.")
    
    def reset_nonce(self):
        """Reset nonce counter"""
        if messagebox.askyesno("Reset Nonce", "Reset nonce counter to 0?"):
            self.nonce = 0
            self.predictions = []
            self.nonce_label.config(text="0")
            self.update_history()
            self.prediction_display.config(text="???")
            self.hash_display.delete('1.0', tk.END)
            self.save_state()
    
    def generate_hash(self):
        """Generate hash from current state"""
        combined = f"{self.server_seed}:{self.client_seed}:{self.nonce}"
        return hashlib.sha512(combined.encode()).hexdigest()
    
    def hash_to_number(self, hash_value):
        """Convert hash to number (1-10000)"""
        # Use first 8 chars for randomness
        hash_int = int(hash_value[:8], 16)
        # Map to 1-10000 range
        return (hash_int % 10000) + 1
    
    def predict_next(self):
        """Generate next prediction"""
        # Get current hash
        current_hash = self.generate_hash()
        
        # Convert to number
        predicted = self.hash_to_number(current_hash)
        
        # Animate the prediction
        self.animate_prediction(predicted)
        
        # Update hash display
        self.hash_display.delete('1.0', tk.END)
        self.hash_display.insert('1.0', current_hash)
        
        # Store prediction
        self.predictions.append({
            'nonce': self.nonce,
            'number': predicted,
            'hash': current_hash[:16] + '...',
            'timestamp': str(datetime.now())
        })
        
        # Increment nonce
        self.nonce += 1
        self.nonce_label.config(text=str(self.nonce))
        
        # Update displays
        self.update_history()
        self.update_stats()
        
        # Save state
        self.save_state()
        
        return predicted
    
    def animate_prediction(self, final_number):
        """Animate the prediction display"""
        # Quick animation
        for i in range(5):
            self.root.after(i * 50, lambda i=i: self.prediction_display.config(
                text=str(random.randint(1, 10000)),
                fg='#ff0000'
            ))
        
        # Final number
        self.root.after(250, lambda: self.prediction_display.config(
            text=str(final_number),
            fg='#00ff00'
        ))
    
    def toggle_auto(self):
        """Toggle auto-predict mode"""
        self.auto_predict = not self.auto_predict
        
        if self.auto_predict:
            self.auto_btn.config(text="⏸ STOP AUTO", bg='#ff0000')
            self.auto_predict_loop()
        else:
            self.auto_btn.config(text="⚡ AUTO MODE", bg='#ffaa00')
    
    def auto_predict_loop(self):
        """Auto-prediction loop"""
        if self.auto_predict:
            self.predict_next()
            self.root.after(1500, self.auto_predict_loop)  # 1.5 second delay
    
    def update_history(self):
        """Update history display"""
        self.history_text.delete('1.0', tk.END)
        
        # Show last 8 predictions
        start = max(0, len(self.predictions) - 8)
        for i in range(start, len(self.predictions)):
            pred = self.predictions[i]
            self.history_text.insert(
                tk.END,
                f"#{pred['nonce']:03d}: {pred['number']:05d}  {pred['hash']}\n"
            )
        
        self.history_text.see(tk.END)
    
    def update_stats(self):
        """Update statistics"""
        if self.predictions:
            last_10 = [p['number'] for p in self.predictions[-10:]]
            stats = f"Total: {len(self.predictions)} | Current Nonce: {self.nonce} | Last 10: {', '.join(map(str, last_10))}"
            self.stats_label.config(text=stats)

def main():
    """Main entry point - NO EXPIRY CODE"""
    root = tk.Tk()
    app = PermanentHashPredictor(root)
    
    # Handle window close
    def on_closing():
        app.save_state()  # Save before closing
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()  # Runs forever until user closes

if __name__ == "__main__":
    main()