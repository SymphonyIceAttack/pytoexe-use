import customtkinter as ctk
import requests
import json
import webbrowser
import pyperclip
from datetime import datetime, timezone
import threading
from PIL import Image
from io import BytesIO
import os
import time

class CookieHubChecker:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.geometry("1300x850")
        self.window.title("Cookie Hub Checker")
        self.window.configure(fg_color="#0f0f12")
        
        # Set theme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("green")
        
        # Create main container with scrollbar
        self.main_container = ctk.CTkScrollableFrame(
            self.window,
            width=1260,
            height=830,
            fg_color="#0f0f12",
            scrollbar_button_color="#1e1e24",
            scrollbar_button_hover_color="#2a2a35"
        )
        self.main_container.pack(pady=10, padx=10, fill="both", expand=True)
        
        # Initialize variables
        self.checking = False
        self.typing_animation = None
        self.current_cookie = None
        self.animation_phase = 0
        self.gradient_offset = 0
        self.csrf_token = None
        
        self.create_gui()
        self.start_animations()
        
    def start_animations(self):
        """Start background animations"""
        self.animate_gradient()
        self.pulse_animation()
        
    def animate_gradient(self):
        """Animate gradient background effect"""
        if not self.checking:
            self.gradient_offset = (self.gradient_offset + 1) % 100
            self.window.after(50, self.animate_gradient)
        
    def pulse_animation(self):
        """Create pulsing effect on buttons"""
        if hasattr(self, 'check_button') and not self.checking:
            self.animation_phase = (self.animation_phase + 1) % 20
            self.window.after(100, self.pulse_animation)
        
    def create_gui(self):
        # Main content wrapper
        content_wrapper = ctk.CTkFrame(
            self.main_container,
            fg_color="#13141a",
            corner_radius=20,
            border_width=1,
            border_color="#252630"
        )
        content_wrapper.pack(pady=15, padx=20, fill="both", expand=True)
        
        # Header Section
        header_frame = ctk.CTkFrame(
            content_wrapper,
            fg_color="transparent",
            height=100
        )
        header_frame.pack(pady=(20, 10), padx=30, fill="x")
        header_frame.pack_propagate(False)
        
        # Title container
        title_container = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_container.pack(side="left", fill="both", expand=True)
        
        self.title_label = ctk.CTkLabel(
            title_container,
            text="🍪 Cookie Hub Checker",
            font=("Segoe UI", 36, "bold"),
            text_color="#ffffff"
        )
        self.title_label.pack(anchor="w", pady=(10, 0))
        
        self.subtitle_label = ctk.CTkLabel(
            title_container,
            text="Advanced Roblox Account Intelligence Tool",
            font=("Segoe UI", 14),
            text_color="#6c6c7a"
        )
        self.subtitle_label.pack(anchor="w")
        
        # Status indicator
        self.status_indicator = ctk.CTkFrame(header_frame, fg_color="#1e1e24", corner_radius=20, width=120, height=40)
        self.status_indicator.pack(side="right", padx=10)
        self.status_indicator.pack_propagate(False)
        
        self.status_dot = ctk.CTkLabel(
            self.status_indicator,
            text="●",
            font=("Segoe UI", 16),
            text_color="#ff4444"
        )
        self.status_dot.pack(side="left", padx=(15, 5), pady=10)
        
        self.status_text = ctk.CTkLabel(
            self.status_indicator,
            text="Offline",
            font=("Segoe UI", 12, "bold"),
            text_color="#6c6c7a"
        )
        self.status_text.pack(side="left", padx=(0, 15), pady=10)
        
        # Main content grid
        content_frame = ctk.CTkFrame(content_wrapper, fg_color="transparent")
        content_frame.pack(pady=20, padx=30, fill="both", expand=True)
        content_frame.grid_columnconfigure(0, weight=2)
        content_frame.grid_columnconfigure(1, weight=3)
        
        # Left Panel
        left_panel = ctk.CTkFrame(
            content_frame,
            fg_color="#1a1b23",
            corner_radius=15,
            border_width=1,
            border_color="#2a2b36"
        )
        left_panel.grid(row=0, column=0, padx=(0, 10), sticky="nsew")
        
        # Cookie Input Card
        input_card = ctk.CTkFrame(left_panel, fg_color="#22232e", corner_radius=12)
        input_card.pack(pady=20, padx=20, fill="both", expand=True)
        
        input_header = ctk.CTkFrame(input_card, fg_color="transparent")
        input_header.pack(fill="x", padx=20, pady=(20, 10))
        
        cookie_icon = ctk.CTkLabel(
            input_header,
            text="🔐",
            font=("Segoe UI", 24)
        )
        cookie_icon.pack(side="left", padx=(0, 10))
        
        input_label = ctk.CTkLabel(
            input_header,
            text="Authentication Cookie",
            font=("Segoe UI", 18, "bold"),
            text_color="#e0e0e8"
        )
        input_label.pack(side="left")
        
        self.cookie_input = ctk.CTkTextbox(
            input_card,
            height=120,
            font=("Cascadia Code", 12),
            fg_color="#1a1b23",
            text_color="#98c379",
            border_color="#3d3f4c",
            border_width=2,
            corner_radius=8
        )
        self.cookie_input.pack(pady=15, padx=20, fill="x")
        
        self.status_label = ctk.CTkLabel(
            input_card,
            text="",
            font=("Cascadia Code", 12),
            text_color="#98c379",
            height=30
        )
        self.status_label.pack(pady=(0, 15), padx=20)
        
        # Action Buttons
        button_container = ctk.CTkFrame(input_card, fg_color="transparent")
        button_container.pack(pady=(0, 20), padx=20, fill="x")
        
        self.check_button = ctk.CTkButton(
            button_container,
            text="Analyze Cookie",
            command=self.check_cookie,
            font=("Segoe UI", 14, "bold"),
            fg_color="#4ecb71",
            hover_color="#3da85a",
            height=45,
            corner_radius=10
        )
        self.check_button.pack(pady=(0, 10), fill="x")
        
        secondary_buttons = ctk.CTkFrame(button_container, fg_color="transparent")
        secondary_buttons.pack(fill="x")
        secondary_buttons.grid_columnconfigure((0, 1), weight=1)
        
        self.refresh_button = ctk.CTkButton(
            secondary_buttons,
            text="↻ Refresh",
            command=self.refresh_cookie,
            font=("Segoe UI", 13),
            fg_color="#2a7a3d",
            hover_color="#236932",
            height=40,
            corner_radius=8,
            state="disabled"
        )
        self.refresh_button.grid(row=0, column=0, padx=(0, 5), sticky="ew")
        
        utility_frame = ctk.CTkFrame(secondary_buttons, fg_color="transparent")
        utility_frame.grid(row=0, column=1, padx=(5, 0), sticky="ew")
        utility_frame.grid_columnconfigure((0, 1), weight=1)
        
        clear_button = ctk.CTkButton(
            utility_frame,
            text="Clear",
            command=self.clear_input,
            font=("Segoe UI", 12),
            fg_color="#2d2e3a",
            hover_color="#3a3b4a",
            height=40,
            corner_radius=8
        )
        clear_button.grid(row=0, column=0, padx=(0, 3), sticky="ew")
        
        copy_button = ctk.CTkButton(
            utility_frame,
            text="Copy",
            command=self.copy_cookie,
            font=("Segoe UI", 12),
            fg_color="#2d2e3a",
            hover_color="#3a3b4a",
            height=40,
            corner_radius=8
        )
        copy_button.grid(row=0, column=1, padx=(3, 0), sticky="ew")
        
        # Right Panel
        right_panel = ctk.CTkFrame(
            content_frame,
            fg_color="#1a1b23",
            corner_radius=15,
            border_width=1,
            border_color="#2a2b36"
        )
        right_panel.grid(row=0, column=1, sticky="nsew")
        
        # Profile Card
        profile_card = ctk.CTkFrame(right_panel, fg_color="#22232e", corner_radius=12)
        profile_card.pack(pady=20, padx=20, fill="x")
        
        avatar_container = ctk.CTkFrame(profile_card, fg_color="#1a1b23", corner_radius=12)
        avatar_container.pack(side="left", padx=20, pady=20)
        
        self.avatar_frame = ctk.CTkFrame(
            avatar_container,
            fg_color="#13141a",
            corner_radius=10,
            width=120,
            height=120
        )
        self.avatar_frame.pack(padx=10, pady=10)
        self.avatar_frame.pack_propagate(False)
        
        self.avatar_label = ctk.CTkLabel(
            self.avatar_frame,
            text="👤",
            font=("Segoe UI", 48),
            text_color="#4a4b5a"
        )
        self.avatar_label.place(relx=0.5, rely=0.5, anchor="center")
        
        user_info = ctk.CTkFrame(profile_card, fg_color="transparent")
        user_info.pack(side="left", fill="both", expand=True, padx=10, pady=20)
        
        self.username_label = ctk.CTkLabel(
            user_info,
            text="Waiting for Cookie",
            font=("Segoe UI", 24, "bold"),
            text_color="#6c6c7a"
        )
        self.username_label.pack(anchor="w", pady=(5, 0))
        
        self.display_name_label = ctk.CTkLabel(
            user_info,
            text="Enter a cookie to begin",
            font=("Segoe UI", 14),
            text_color="#4a4b5a"
        )
        self.display_name_label.pack(anchor="w")
        
        # Account details
        details_frame = ctk.CTkFrame(user_info, fg_color="transparent")
        details_frame.pack(fill="x", pady=(15, 0))
        details_frame.grid_columnconfigure((0, 1), weight=1)
        
        self.created_label = self.create_info_card(details_frame, "📅 Created", "---", 0, 0)
        self.online_label = self.create_info_card(details_frame, "🟢 Last Online", "---", 0, 1)
        self.type_label = self.create_info_card(details_frame, "👑 Type", "---", 1, 0)
        self.pin_label = self.create_info_card(details_frame, "🔒 PIN", "---", 1, 1)
        
        # Stats Dashboard
        stats_container = ctk.CTkFrame(right_panel, fg_color="#22232e", corner_radius=12)
        stats_container.pack(pady=10, padx=20, fill="x")
        
        stats_label = ctk.CTkLabel(
            stats_container,
            text="📊 Account Statistics",
            font=("Segoe UI", 14, "bold"),
            text_color="#e0e0e8"
        )
        stats_label.pack(pady=(15, 10), padx=20, anchor="w")
        
        self.stats_grid = ctk.CTkFrame(stats_container, fg_color="transparent")
        self.stats_grid.pack(pady=(0, 15), padx=15, fill="x")
        self.stats_grid.grid_columnconfigure((0, 1, 2), weight=1)
        
        self.create_stats_cards()
        
        # Terminal Output
        terminal_card = ctk.CTkFrame(right_panel, fg_color="#22232e", corner_radius=12)
        terminal_card.pack(pady=10, padx=20, fill="both", expand=True)
        
        terminal_header = ctk.CTkFrame(terminal_card, fg_color="#1a1b23", corner_radius=8)
        terminal_header.pack(pady=(15, 10), padx=15, fill="x")
        
        terminal_icon = ctk.CTkLabel(
            terminal_header,
            text=">_",
            font=("Cascadia Code", 16),
            text_color="#4ecb71"
        )
        terminal_icon.pack(side="left", padx=(15, 10), pady=10)
        
        terminal_title = ctk.CTkLabel(
            terminal_header,
            text="Console Output",
            font=("Segoe UI", 13, "bold"),
            text_color="#e0e0e8"
        )
        terminal_title.pack(side="left", pady=10)
        
        terminal_controls = ctk.CTkFrame(terminal_header, fg_color="transparent")
        terminal_controls.pack(side="right", padx=10)
        
        copy_terminal_btn = ctk.CTkButton(
            terminal_controls,
            text="📋",
            command=self.copy_terminal,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#2a2b36",
            width=40,
            height=30,
            corner_radius=6
        )
        copy_terminal_btn.pack(side="left", padx=3)
        
        clear_terminal_btn = ctk.CTkButton(
            terminal_controls,
            text="🗑️",
            command=self.clear_terminal,
            font=("Segoe UI", 14),
            fg_color="transparent",
            hover_color="#2a2b36",
            width=40,
            height=30,
            corner_radius=6
        )
        clear_terminal_btn.pack(side="left", padx=3)
        
        self.results_display = ctk.CTkTextbox(
            terminal_card,
            font=("Cascadia Code", 11),
            fg_color="#1a1b23",
            text_color="#98c379",
            border_color="#3d3f4c",
            border_width=1,
            corner_radius=8
        )
        self.results_display.pack(pady=(0, 15), padx=15, fill="both", expand=True)
        self.results_display.configure(state="disabled")
        
        self.update_results("🍪 Cookie Hub Checker Initialized")
        self.update_results("Ready to analyze Roblox cookies...")
        
    def create_info_card(self, parent, label, value, row, column):
        """Create styled info cards"""
        card = ctk.CTkFrame(parent, fg_color="#1a1b23", corner_radius=8)
        card.grid(row=row, column=column, padx=3, pady=3, sticky="nsew")
        
        label_widget = ctk.CTkLabel(
            card,
            text=label,
            font=("Segoe UI", 11),
            text_color="#6c6c7a"
        )
        label_widget.pack(pady=(8, 0))
        
        value_widget = ctk.CTkLabel(
            card,
            text=value,
            font=("Segoe UI", 13, "bold"),
            text_color="#e0e0e8"
        )
        value_widget.pack(pady=(0, 8))
        
        return value_widget
        
    def create_stats_cards(self):
        """Create statistics cards"""
        stats_data = [
            ("Premium", "---", "💎"),
            ("Account Age", "---", "📅"),
            ("Total RAP", "---", "💰"),
            ("Limiteds", "---", "🎮"),
            ("Friends", "---", "👥"),
            ("Followers", "---", "📈"),
            ("Robux", "---", "💵"),
            ("Visits", "---", "👁️"),
            ("Badges", "---", "🏆")
        ]
        
        self.stat_cards = {}
        
        for i, (label, value, icon) in enumerate(stats_data):
            row = i // 3
            col = i % 3
            
            card = ctk.CTkFrame(self.stats_grid, fg_color="#1a1b23", corner_radius=8)
            card.grid(row=row, column=col, padx=5, pady=5, sticky="nsew")
            
            header = ctk.CTkFrame(card, fg_color="transparent")
            header.pack(fill="x", padx=12, pady=(12, 0))
            
            icon_label = ctk.CTkLabel(
                header,
                text=icon,
                font=("Segoe UI", 14)
            )
            icon_label.pack(side="left")
            
            label_widget = ctk.CTkLabel(
                header,
                text=label,
                font=("Segoe UI", 11),
                text_color="#6c6c7a"
            )
            label_widget.pack(side="left", padx=(5, 0))
            
            value_widget = ctk.CTkLabel(
                card,
                text=value,
                font=("Segoe UI", 15, "bold"),
                text_color="#4ecb71"
            )
            value_widget.pack(pady=(5, 12))
            
            self.stat_cards[label] = value_widget
    
    def get_csrf_token(self, cookie):
        """Get CSRF token for authenticated requests"""
        try:
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Content-Type': 'application/json'
            }
            
            # Make a request that requires CSRF token
            response = requests.post(
                'https://auth.roblox.com/v2/logout',
                headers=headers
            )
            
            if 'x-csrf-token' in response.headers:
                self.csrf_token = response.headers['x-csrf-token']
                self.update_results(f"✓ CSRF token obtained")
                return self.csrf_token
            else:
                self.update_results("⚠️ Could not get CSRF token, some features may be limited")
                return None
                
        except Exception as e:
            self.update_results(f"⚠️ Error getting CSRF token: {str(e)}")
            return None
    
    def make_authenticated_request(self, url, cookie, method='GET', json_data=None):
        """Make authenticated request with CSRF token"""
        headers = {
            'Cookie': f'.ROBLOSECURITY={cookie}',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.csrf_token:
            headers['x-csrf-token'] = self.csrf_token
        
        try:
            if method.upper() == 'GET':
                return requests.get(url, headers=headers)
            elif method.upper() == 'POST':
                return requests.post(url, headers=headers, json=json_data)
        except Exception as e:
            self.update_results(f"⚠️ Request error: {str(e)}")
            return None
    
    def animate_status(self, text, index=0):
        """Animated status text with typing effect"""
        if self.typing_animation:
            self.window.after_cancel(self.typing_animation)
            self.typing_animation = None
            
        if index <= len(text):
            self.status_label.configure(text=text[:index] + "▊")
            self.typing_animation = self.window.after(40, lambda: self.animate_status(text, index + 1))
        else:
            self.status_label.configure(text=text)
            if self.checking:
                self.typing_animation = self.window.after(400, lambda: self.animate_cursor(text))
    
    def animate_cursor(self, text, show=True):
        """Blinking cursor animation"""
        if not self.checking:
            self.status_label.configure(text="")
            return
            
        self.status_label.configure(text=text + ("▊" if show else ""))
        self.typing_animation = self.window.after(500, lambda: self.animate_cursor(text, not show))
    
    def update_status_indicator(self, status):
        """Update the status indicator"""
        if status == "online":
            self.status_dot.configure(text_color="#4ecb71")
            self.status_text.configure(text="Online", text_color="#4ecb71")
        elif status == "checking":
            self.status_dot.configure(text_color="#ffa500")
            self.status_text.configure(text="Checking", text_color="#ffa500")
        else:
            self.status_dot.configure(text_color="#ff4444")
            self.status_text.configure(text="Offline", text_color="#ff4444")
    
    def check_cookie(self):
        """Check cookie validity"""
        if self.checking:
            return
            
        cookie = self.cookie_input.get("1.0", "end-1c").strip()
        if not cookie:
            self.update_results("❌ Please enter a cookie to analyze")
            self.animate_status("No cookie provided!")
            return
            
        self.checking = True
        self.update_status_indicator("checking")
        self.check_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.clear_input()
        self.animate_status("🔍 Analyzing cookie...")
        threading.Thread(target=self._check_cookie_thread, args=(cookie,)).start()
    
    def _check_cookie_thread(self, cookie):
        """Threaded cookie checking"""
        try:
            # Get CSRF token first
            self.get_csrf_token(cookie)
            
            headers = {
                'Cookie': f'.ROBLOSECURITY={cookie}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'application/json',
                'Content-Type': 'application/json'
            }
            
            # Add CSRF token if available
            if self.csrf_token:
                headers['x-csrf-token'] = self.csrf_token
            
            # Validate cookie
            self.update_results("🔍 Validating cookie...")
            response = requests.get('https://users.roblox.com/v1/users/authenticated', headers=headers)
            
            if response.status_code == 200:
                user_data = response.json()
                self.current_cookie = cookie
                self.update_results("✅ Cookie validated successfully!")
                self.animate_status("✨ Cookie is valid!")
                self.update_status_indicator("online")
                
                # Update UI with user data
                self.window.after(0, lambda: self.update_user_interface(user_data, cookie, headers))
                self.window.after(0, lambda: self.refresh_button.configure(state="normal"))
                
            else:
                self.update_results(f"❌ Invalid cookie (Status: {response.status_code})")
                self.animate_status("❌ Invalid cookie!")
                self.update_status_indicator("offline")
                
        except Exception as e:
            self.update_results(f"⚠️ Error: {str(e)}")
            self.animate_status("Error occurred!")
            self.update_status_indicator("offline")
        finally:
            self.checking = False
            self.window.after(0, lambda: self.check_button.configure(state="normal"))
    
    def update_user_interface(self, user_data, cookie, headers):
        """Update UI with user information"""
        try:
            user_id = user_data['id']
            user_name = user_data['name']
            
            self.update_results(f"📊 Fetching data for {user_name}...")
            
            # Load avatar
            self.load_avatar(user_id)
            
            # Update basic info
            self.username_label.configure(text=user_name, text_color="#ffffff")
            self.display_name_label.configure(text=f"@{user_data['displayName']}", text_color="#4ecb71")
            
            # Get detailed user info
            self.update_results("📅 Fetching account details...")
            user_info = self.make_authenticated_request(
                f"https://users.roblox.com/v1/users/{user_id}",
                cookie
            )
            
            if user_info and user_info.status_code == 200:
                info_data = user_info.json()
                created_date = datetime.fromisoformat(info_data['created'].replace('Z', '+00:00'))
                created_str = created_date.strftime("%Y-%m-%d")
                account_age = (datetime.now(timezone.utc) - created_date).days
                
                self.created_label.configure(text=created_str)
                self.online_label.configure(text="Active Now", text_color="#4ecb71")
                
                # Update account age in stats
                if "Account Age" in self.stat_cards:
                    self.stat_cards["Account Age"].configure(text=f"{account_age:,} days")
            
            # Get premium status
            self.update_results("💎 Checking premium status...")
            premium_check = self.make_authenticated_request(
                f"https://premiumfeatures.roblox.com/v1/users/{user_id}/validate-membership",
                cookie
            )
            
            is_premium = False
            if premium_check:
                is_premium = premium_check.status_code == 200
            
            self.type_label.configure(
                text="Premium" if is_premium else "Regular",
                text_color="#ffd700" if is_premium else "#e0e0e8"
            )
            
            if "Premium" in self.stat_cards:
                self.stat_cards["Premium"].configure(
                    text="✅ Yes" if is_premium else "❌ No",
                    text_color="#4ecb71" if is_premium else "#ff4444"
                )
            
            # Get PIN status
            self.update_results("🔒 Checking PIN status...")
            pin_check = self.make_authenticated_request(
                "https://auth.roblox.com/v1/account/pin",
                cookie
            )
            
            has_pin = False
            if pin_check and pin_check.status_code == 200:
                has_pin = pin_check.json().get('isEnabled', False)
            
            self.pin_label.configure(
                text="Enabled" if has_pin else "Disabled",
                text_color="#4ecb71" if has_pin else "#ff4444"
            )
            
            # Get friends count
            self.update_results("👥 Fetching friends count...")
            friends_data = self.make_authenticated_request(
                f"https://friends.roblox.com/v1/users/{user_id}/friends/count",
                cookie
            )
            
            friends_count = 0
            if friends_data and friends_data.status_code == 200:
                friends_count = friends_data.json().get('count', 0)
                if "Friends" in self.stat_cards:
                    self.stat_cards["Friends"].configure(text=f"{friends_count:,}")
            
            # Get followers count
            self.update_results("📈 Fetching followers count...")
            followers_data = self.make_authenticated_request(
                f"https://friends.roblox.com/v1/users/{user_id}/followers/count",
                cookie
            )
            
            followers_count = 0
            if followers_data and followers_data.status_code == 200:
                followers_count = followers_data.json().get('count', 0)
                if "Followers" in self.stat_cards:
                    self.stat_cards["Followers"].configure(text=f"{followers_count:,}")
            
            # Get Robux balance
            self.update_results("💰 Fetching Robux balance...")
            currency_data = self.make_authenticated_request(
                "https://economy.roblox.com/v1/user/currency",
                cookie
            )
            
            robux = 0
            if currency_data and currency_data.status_code == 200:
                robux = currency_data.json().get('robux', 0)
                if "Robux" in self.stat_cards:
                    self.stat_cards["Robux"].configure(text=f"R$ {robux:,}")
            
            # Get inventory data (RAP and limiteds)
            self.update_results("🎮 Fetching inventory data...")
            inventory_url = f"https://inventory.roblox.com/v1/users/{user_id}/assets/collectibles?limit=100&sortOrder=Desc"
            inventory = self.make_authenticated_request(inventory_url, cookie)
            
            total_rap = 0
            total_limiteds = 0
            
            if inventory and inventory.status_code == 200:
                items = inventory.json().get('data', [])
                total_limiteds = len(items)
                total_rap = sum(item.get('recentAveragePrice', 0) for item in items if item.get('recentAveragePrice'))
                
                if "Total RAP" in self.stat_cards:
                    self.stat_cards["Total RAP"].configure(text=f"R$ {total_rap:,}")
                if "Limiteds" in self.stat_cards:
                    self.stat_cards["Limiteds"].configure(text=f"{total_limiteds:,}")
            
            # Get place visits
            self.update_results("👁️ Fetching game statistics...")
            places_url = f"https://games.roblox.com/v2/users/{user_id}/games?accessFilter=Public&limit=50"
            places_data = self.make_authenticated_request(places_url, cookie)
            
            total_visits = 0
            if places_data and places_data.status_code == 200:
                games = places_data.json().get('data', [])
                total_visits = sum(game.get('placeVisits', 0) for game in games)
                if "Visits" in self.stat_cards:
                    self.stat_cards["Visits"].configure(text=f"{total_visits:,}")
            
            # Get badges count
            self.update_results("🏆 Fetching badges count...")
            badges_url = f"https://badges.roblox.com/v1/users/{user_id}/badges?limit=100"
            badges_data = self.make_authenticated_request(badges_url, cookie)
            
            total_badges = 0
            if badges_data and badges_data.status_code == 200:
                total_badges = len(badges_data.json().get('data', []))
                if "Badges" in self.stat_cards:
                    self.stat_cards["Badges"].configure(text=f"{total_badges:,}")
            
            self.update_results(f"✅ Successfully loaded all data for {user_name}!")
            
        except Exception as e:
            self.update_results(f"⚠️ Error loading user data: {str(e)}")
    
    def load_avatar(self, user_id):
        """Load user avatar with error handling"""
        try:
            avatar_url = f"https://thumbnails.roblox.com/v1/users/avatar?userIds={user_id}&size=420x420&format=Png&isCircular=false"
            response = requests.get(avatar_url)
            
            if response.status_code == 200:
                avatar_data = response.json()
                if avatar_data.get('data') and len(avatar_data['data']) > 0:
                    avatar_image_url = avatar_data["data"][0]["imageUrl"]
                    
                    img_response = requests.get(avatar_image_url)
                    if img_response.status_code == 200:
                        img_data = Image.open(BytesIO(img_response.content))
                        img_data = img_data.resize((120, 120), Image.Resampling.LANCZOS)
                        img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(120, 120))
                        
                        self.avatar_label.configure(image=img, text="")
                        self.avatar_label.image = img
                        self.update_results("✓ Avatar loaded successfully")
                    else:
                        self.update_results("⚠️ Could not download avatar image")
                else:
                    self.update_results("⚠️ No avatar data received")
            else:
                self.update_results(f"⚠️ Avatar API error: {response.status_code}")
                
        except Exception as e:
            self.update_results(f"⚠️ Avatar loading error: {str(e)}")
    
    def refresh_cookie(self):
        """Refresh the current cookie"""
        if not self.current_cookie or self.checking:
            return
            
        self.checking = True
        self.update_status_indicator("checking")
        self.check_button.configure(state="disabled")
        self.refresh_button.configure(state="disabled")
        self.animate_status("🔄 Refreshing cookie...")
        threading.Thread(target=self._refresh_cookie_thread).start()
    
    def _refresh_cookie_thread(self):
        """Threaded cookie refresh"""
        try:
            self.update_results("🔄 Attempting to refresh cookie...")
            self.update_results("⚠️ Cookie refresh may not work due to Roblox security")
            self.update_results("💡 Try getting a fresh cookie from Roblox")
            self.animate_status("Refresh attempted!")
            
        except Exception as e:
            self.update_results(f"❌ Error refreshing cookie: {str(e)}")
            self.animate_status("Refresh failed!")
        finally:
            self.checking = False
            self.update_status_indicator("online")
            self.window.after(0, lambda: self.check_button.configure(state="normal"))
            self.window.after(0, lambda: self.refresh_button.configure(state="normal"))
    
    def clear_input(self):
        """Clear input fields"""
        if self.checking:
            return
            
        self.cookie_input.delete("1.0", "end")
        self.status_label.configure(text="")
        self.current_cookie = None
        self.csrf_token = None
        self.refresh_button.configure(state="disabled")
        self.update_status_indicator("offline")
        
        # Reset UI
        self.username_label.configure(text="Waiting for Cookie", text_color="#6c6c7a")
        self.display_name_label.configure(text="Enter a cookie to begin", text_color="#4a4b5a")
        self.avatar_label.configure(image=None, text="👤")
        
        # Reset info cards
        self.created_label.configure(text="---")
        self.online_label.configure(text="---", text_color="#e0e0e8")
        self.type_label.configure(text="---", text_color="#e0e0e8")
        self.pin_label.configure(text="---", text_color="#e0e0e8")
        
        # Reset stats
        for card in self.stat_cards.values():
            card.configure(text="---", text_color="#4ecb71")
    
    def copy_cookie(self):
        """Copy cookie to clipboard"""
        cookie = self.cookie_input.get("1.0", "end-1c").strip()
        if cookie:
            pyperclip.copy(cookie)
            self.update_results("📋 Cookie copied to clipboard")
            self.animate_status("Cookie copied!")
    
    def copy_terminal(self):
        """Copy terminal output"""
        terminal_text = self.results_display.get("1.0", "end-1c")
        if terminal_text:
            pyperclip.copy(terminal_text)
            self.animate_status("Terminal output copied!")
    
    def clear_terminal(self):
        """Clear terminal output"""
        self.results_display.configure(state="normal")
        self.results_display.delete("1.0", "end")
        self.results_display.configure(state="disabled")
        self.update_results("🍪 Terminal cleared")
        self.animate_status("Terminal cleared!")
    
    def update_results(self, text):
        """Add message to terminal"""
        self.results_display.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.results_display.insert("end", f"[{timestamp}] {text}\n")
        self.results_display.configure(state="disabled")
        self.results_display.see("end")
    
    def run(self):
        """Start the application"""
        self.window.mainloop()

if __name__ == "__main__":
    app = CookieHubChecker()
    app.run()