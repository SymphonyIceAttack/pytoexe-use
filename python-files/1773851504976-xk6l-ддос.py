#!/usr/bin/env python3
"""
WINDOWS DDoS SIMULATOR - ИСПРАВЛЕННАЯ ВЕРСИЯ
Полностью безопасная визуальная симуляция
Никаких реальных пакетов не отправляется!
Остановка: Ctrl+P или Ctrl+Q
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import threading
import time
import sys
import math
import psutil
import platform
from datetime import datetime, timedelta
import os
import socket
import json


class DDoSSimulator:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🛡️ WINDOWS DDoS SIMULATOR v5.4 - ИСПРАВЛЕННАЯ")
        self.root.geometry("1280x720")

        # Установка иконки (если есть)
        try:
            self.root.iconbitmap(default='icon.ico')
        except:
            pass

        # Настройки окна
        self.root.configure(bg='#0a0a0f')

        # База данных сайтов
        self.sites_database = self.create_sites_database()

        # Экономическая система
        self.coins = 500
        self.total_coins_earned = 0
        self.bots = 50
        self.bot_level = 1
        self.attack_speed = 1.0
        self.bot_power = 1.0

        # База цен
        self.base_prices = {
            "bot": 75,
            "bot_level": 800,
            "attack_speed": 500,
            "bot_power": 600,
            "auto_attack": 2000,
            "double_coins": 3000,
        }

        # Текущие цены
        self.shop_prices = self.base_prices.copy()

        # Количество купленных предметов
        self.purchased_count = {
            "bot": 0,
            "bot_level": 0,
            "attack_speed": 0,
            "bot_power": 0,
        }

        # Улучшения
        self.auto_attack = False
        self.double_coins = False

        # Переменные состояния
        self.running = True
        self.attack_active = False
        self.attack_type = "SYN Flood"
        self.current_site = "Google"
        self.target_ip = self.sites_database["Google"]["ip"]
        self.target_domain = "google.com"
        self.target_port = 443
        self.packets_sent = 0
        self.bytes_sent = 0
        self.attack_power = 0
        self.attack_duration = self.calculate_attack_duration()
        self.attack_end_time = None
        self.attack_start_time = None
        self.last_earnings_update = 0
        self.total_earnings_this_attack = 0

        # График
        self.graph_data = [0] * 60

        # Перехват горячих клавиш
        self.root.bind('<Control-p>', self.emergency_stop)
        self.root.bind('<Control-P>', self.emergency_stop)
        self.root.bind('<Control-q>', self.emergency_stop)
        self.root.bind('<Control-Q>', self.emergency_stop)
        self.root.bind('<F1>', self.show_help)
        self.root.bind('<F2>', self.open_shop)
        self.root.bind('<F5>', lambda e: self.start_attack())
        self.root.bind('<F6>', lambda e: self.stop_attack())

        # Создание интерфейса
        self.create_menu()
        self.create_ui()

        # Запуск обновлений
        self.update_stats()
        self.update_graph()
        self.update_resources()

        # Загрузка сохранения
        self.load_game()

    def calculate_earnings(self):
        """Расчет заработка монет"""
        base_earnings = max(1, int(self.coins / 3))
        variation = random.uniform(0.8, 1.2)
        earnings = int(base_earnings * variation)
        return max(1, earnings)

    def calculate_attack_duration(self):
        """Расчет длительности атаки"""
        base_duration = 300
        bot_factor = max(0.2, 1.0 - (self.bots / 500))
        duration = int(base_duration * bot_factor)
        return max(15, min(300, duration))

    def calculate_attack_power_increment(self):
        """Расчет прироста мощности"""
        base_increment = random.uniform(0.1, 0.3)
        return base_increment * self.bot_power * (1 + self.bot_level * 0.15)

    def calculate_packet_increment(self):
        """Расчет количества пакетов"""
        base_packets = random.randint(1000, 5000)
        return int(base_packets * self.attack_speed * (1 + self.bots / 300))

    def get_item_price(self, item_id):
        """Получение текущей цены предмета"""
        base = self.base_prices[item_id]
        count = self.purchased_count.get(item_id, 0)

        if item_id in ["bot", "bot_level", "attack_speed", "bot_power"]:
            multiplier = 1 + (count * 0.15)
            return int(base * multiplier)
        else:
            return base

    def create_sites_database(self):
        """Создание базы данных сайтов"""
        sites = {}

        def get_ip(domain):
            try:
                return socket.gethostbyname(domain)
            except:
                return "0.0.0.0"

        government_sites = {
            "РКН": {"domains": ["rkn.gov.ru"], "country": "Russia", "server": "Роскомнадзор", "difficulty": 100},
            "Госуслуги": {"domains": ["gosuslugi.ru"], "country": "Russia", "server": "Минцифры РФ", "difficulty": 95},
            "Кремль": {"domains": ["kremlin.ru"], "country": "Russia", "server": "Администрация Президента",
                       "difficulty": 98},
            "Правительство РФ": {"domains": ["government.ru"], "country": "Russia", "server": "Правительство РФ",
                                 "difficulty": 97},
            "Минобороны": {"domains": ["mil.ru"], "country": "Russia", "server": "Минобороны РФ", "difficulty": 96},
            "ФНС": {"domains": ["nalog.ru"], "country": "Russia", "server": "ФНС России", "difficulty": 90},
            "МВД": {"domains": ["mvd.ru"], "country": "Russia", "server": "МВД РФ", "difficulty": 94},
            "ФСБ": {"domains": ["fsb.ru"], "country": "Russia", "server": "ФСБ России", "difficulty": 99},
        }

        search_engines = {
            "Google": {"domains": ["google.com"], "country": "USA", "server": "Google LLC", "difficulty": 95},
            "Yandex": {"domains": ["yandex.ru"], "country": "Russia", "server": "Yandex LLC", "difficulty": 90},
            "Bing": {"domains": ["bing.com"], "country": "USA", "server": "Microsoft", "difficulty": 88},
        }

        social_networks = {
            "Facebook": {"domains": ["facebook.com"], "country": "USA", "server": "Meta Platforms", "difficulty": 96},
            "Instagram": {"domains": ["instagram.com"], "country": "USA", "server": "Meta Platforms", "difficulty": 95},
            "Twitter/X": {"domains": ["twitter.com"], "country": "USA", "server": "X Corp", "difficulty": 90},
            "TikTok": {"domains": ["tiktok.com"], "country": "China", "server": "ByteDance", "difficulty": 93},
            "VK": {"domains": ["vk.com"], "country": "Russia", "server": "VKontakte", "difficulty": 85},
            "Telegram": {"domains": ["telegram.org"], "country": "UAE", "server": "Telegram Messenger",
                         "difficulty": 88},
        }

        all_sites = {**government_sites, **search_engines, **social_networks}

        for name, info in all_sites.items():
            info["ip"] = get_ip(info["domains"][0])
            info["ports"] = [80, 443]

        return all_sites

    def create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Start Attack", command=self.start_attack, accelerator="F5")
        file_menu.add_command(label="Stop Attack", command=self.stop_attack, accelerator="F6")
        file_menu.add_command(label="Shop", command=self.open_shop, accelerator="F2")
        file_menu.add_separator()
        file_menu.add_command(label="Save Game", command=self.save_game)
        file_menu.add_command(label="Load Game", command=self.load_game)
        file_menu.add_separator()
        file_menu.add_command(label="Reset Game", command=self.reset_game)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.emergency_stop, accelerator="Ctrl+P")

        sites_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Sites", menu=sites_menu)

        categories = {
            "🏛️ Government Russia": [],
            "🔍 Search Engines": [],
            "👥 Social Networks": [],
        }

        for site, info in sorted(self.sites_database.items()):
            if site in ["РКН", "Госуслуги", "Кремль", "Правительство РФ", "Минобороны", "ФНС", "МВД", "ФСБ"]:
                categories["🏛️ Government Russia"].append(site)
            elif site in ["Google", "Yandex", "Bing"]:
                categories["🔍 Search Engines"].append(site)
            else:
                categories["👥 Social Networks"].append(site)

        for category, sites in categories.items():
            if sites:
                menu = tk.Menu(sites_menu, tearoff=0)
                sites_menu.add_cascade(label=f"{category} ({len(sites)})", menu=menu)

                for site in sorted(sites):
                    info = self.sites_database[site]
                    menu.add_command(
                        label=f"{site} ({info['domains'][0]}) [难度 {info['difficulty']}]",
                        command=lambda s=site: self.update_site_info(s)
                    )

        attack_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Attack", menu=attack_menu)

        attack_types = ["SYN Flood", "UDP Flood", "HTTP Flood", "ICMP Flood",
                        "DNS Amplification", "Slowloris", "Ping of Death"]

        self.attack_var = tk.StringVar(value="SYN Flood")
        for at in attack_types:
            attack_menu.add_radiobutton(label=at, variable=self.attack_var, value=at,
                                        command=self.change_attack)

        attack_menu.add_separator()
        attack_menu.add_command(label="Random Attack", command=self.random_attack)

        shop_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Shop", menu=shop_menu)
        shop_menu.add_command(label="Open Shop", command=self.open_shop, accelerator="F2")
        shop_menu.add_separator()
        shop_menu.add_command(label="Buy Bot", command=lambda: self.buy_item("bot"))
        shop_menu.add_command(label="Upgrade Bot Level", command=lambda: self.buy_item("bot_level"))
        shop_menu.add_command(label="Upgrade Attack Speed", command=lambda: self.buy_item("attack_speed"))
        shop_menu.add_command(label="Upgrade Bot Power", command=lambda: self.buy_item("bot_power"))
        shop_menu.add_command(label="Auto Attack", command=lambda: self.buy_item("auto_attack"))
        shop_menu.add_command(label="Double Coins", command=lambda: self.buy_item("double_coins"))

        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="How to Play", command=self.show_howto)
        help_menu.add_command(label="Documentation", command=self.show_docs)
        help_menu.add_command(label="About", command=self.show_about)
        help_menu.add_separator()
        help_menu.add_command(label="Hotkeys", command=self.show_help, accelerator="F1")

    def create_ui(self):
        """Создание интерфейса"""
        # Верхняя панель
        title_frame = tk.Frame(self.root, bg='#1a1a2a', height=80)
        title_frame.pack(fill=tk.X)

        title = tk.Label(
            title_frame,
            text="🛡️ WINDOWS DDoS SIMULATOR v5.4 - ИСПРАВЛЕННАЯ",
            font=("Consolas", 16, "bold"),
            fg='#00ff88',
            bg='#1a1a2a'
        )
        title.pack(pady=5)

        # Экономическая панель
        econ_frame = tk.Frame(title_frame, bg='#1a1a2a')
        econ_frame.pack(fill=tk.X, padx=10, pady=5)

        # Монеты
        coins_frame = tk.Frame(econ_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        coins_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(coins_frame, text="💰", font=("Arial", 14), bg='#2a2a3a', fg='gold').pack(side=tk.LEFT, padx=5)
        self.coins_label = tk.Label(coins_frame, text=f"{self.coins}", font=("Arial", 14, "bold"),
                                    bg='#2a2a3a', fg='gold')
        self.coins_label.pack(side=tk.LEFT, padx=5)

        # Боты
        bots_frame = tk.Frame(econ_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        bots_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(bots_frame, text="🤖", font=("Arial", 14), bg='#2a2a3a', fg='cyan').pack(side=tk.LEFT, padx=5)
        self.bots_label = tk.Label(bots_frame, text=f"{self.bots}", font=("Arial", 14, "bold"),
                                   bg='#2a2a3a', fg='cyan')
        self.bots_label.pack(side=tk.LEFT, padx=5)

        # Уровень ботов
        level_frame = tk.Frame(econ_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        level_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(level_frame, text="📊 Lvl", font=("Arial", 12), bg='#2a2a3a', fg='lime').pack(side=tk.LEFT, padx=5)
        self.bot_level_label = tk.Label(level_frame, text=f"{self.bot_level}", font=("Arial", 14, "bold"),
                                        bg='#2a2a3a', fg='lime')
        self.bot_level_label.pack(side=tk.LEFT, padx=5)

        # Скорость атаки
        speed_frame = tk.Frame(econ_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        speed_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(speed_frame, text="⚡ Speed", font=("Arial", 10), bg='#2a2a3a', fg='yellow').pack(side=tk.LEFT, padx=5)
        self.speed_label = tk.Label(speed_frame, text=f"{self.attack_speed:.1f}x", font=("Arial", 12, "bold"),
                                    bg='#2a2a3a', fg='yellow')
        self.speed_label.pack(side=tk.LEFT, padx=5)

        # Мощность
        power_frame = tk.Frame(econ_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        power_frame.pack(side=tk.LEFT, padx=10)

        tk.Label(power_frame, text="💪 Power", font=("Arial", 10), bg='#2a2a3a', fg='orange').pack(side=tk.LEFT, padx=5)
        self.power_label = tk.Label(power_frame, text=f"{self.bot_power:.1f}x", font=("Arial", 12, "bold"),
                                    bg='#2a2a3a', fg='orange')
        self.power_label.pack(side=tk.LEFT, padx=5)

        # Кнопка магазина
        shop_btn = tk.Button(
            econ_frame,
            text="🛒 МАГАЗИН (F2)",
            bg='gold',
            fg='black',
            font=("Arial", 10, "bold"),
            command=self.open_shop
        )
        shop_btn.pack(side=tk.RIGHT, padx=10)

        # Информация о сайте
        self.site_info_label = tk.Label(
            title_frame,
            text=f"📍 Google | Server: Google LLC | Country: USA | 难度: 95",
            font=("Consolas", 10),
            fg='#8888ff',
            bg='#1a1a2a'
        )
        self.site_info_label.pack()

        # Панель управления
        control_frame = tk.Frame(self.root, bg='#0f0f1a', height=50)
        control_frame.pack(fill=tk.X)

        self.start_btn = tk.Button(
            control_frame,
            text="🚀 START ATTACK (F5)",
            bg='#00aa00',
            fg='white',
            font=("Arial", 10, "bold"),
            command=self.start_attack,
            width=15
        )
        self.start_btn.pack(side=tk.LEFT, padx=10, pady=10)

        self.stop_btn = tk.Button(
            control_frame,
            text="🛑 STOP ATTACK (F6)",
            bg='#aa0000',
            fg='white',
            font=("Arial", 10, "bold"),
            command=self.stop_attack,
            width=15,
            state=tk.DISABLED
        )
        self.stop_btn.pack(side=tk.LEFT, padx=5, pady=10)

        tk.Label(control_frame, text="Site:", fg='white', bg='#0f0f1a',
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=10)

        quick_sites = list(self.sites_database.keys())[:20]
        self.site_combo = ttk.Combobox(
            control_frame,
            values=quick_sites,
            state="readonly",
            width=20
        )
        self.site_combo.set("Google")
        self.site_combo.pack(side=tk.LEFT, padx=5)
        self.site_combo.bind('<<ComboboxSelected>>', self.on_site_change)

        tk.Label(control_frame, text="Attack:", fg='white', bg='#0f0f1a',
                 font=("Arial", 10)).pack(side=tk.LEFT, padx=20)

        self.attack_combo = ttk.Combobox(
            control_frame,
            values=["SYN Flood", "UDP Flood", "HTTP Flood", "ICMP Flood",
                    "DNS Amplification", "Slowloris", "Ping of Death"],
            state="readonly",
            width=20
        )
        self.attack_combo.set("SYN Flood")
        self.attack_combo.pack(side=tk.LEFT, padx=5)
        self.attack_combo.bind('<<ComboboxSelected>>', self.on_attack_change)

        self.status_label = tk.Label(
            control_frame,
            text="⏸️ READY",
            fg='#00ff00',
            bg='#0f0f1a',
            font=("Arial", 10, "bold")
        )
        self.status_label.pack(side=tk.RIGHT, padx=20)

        # Основной контейнер
        main_frame = tk.Frame(self.root, bg='#0a0a0f')
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Левая панель
        left_panel = tk.Frame(main_frame, bg='#1a1a2a', width=400)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)

        # Целевая информация
        target_frame = tk.LabelFrame(left_panel, text="🎯 TARGET", fg='#00ff00', bg='#1a1a2a',
                                     font=("Consolas", 12, "bold"))
        target_frame.pack(fill=tk.X, padx=10, pady=10)

        domain_frame = tk.Frame(target_frame, bg='#1a1a2a')
        domain_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(domain_frame, text="Domain:", fg='#8888ff', bg='#1a1a2a',
                 font=("Consolas", 10)).pack(side=tk.LEFT)

        self.domain_label = tk.Label(domain_frame, text="google.com", fg='#00ff00', bg='#1a1a2a',
                                     font=("Consolas", 10, "bold"))
        self.domain_label.pack(side=tk.LEFT, padx=10)

        ip_frame = tk.Frame(target_frame, bg='#1a1a2a')
        ip_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(ip_frame, text="IP Address:", fg='#8888ff', bg='#1a1a2a',
                 font=("Consolas", 10)).pack(side=tk.LEFT)

        self.ip_entry = tk.Entry(ip_frame, width=15, font=("Consolas", 10))
        self.ip_entry.insert(0, self.target_ip)
        self.ip_entry.config(state='readonly')
        self.ip_entry.pack(side=tk.LEFT, padx=10)

        port_frame = tk.Frame(target_frame, bg='#1a1a2a')
        port_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(port_frame, text="Port:", fg='#8888ff', bg='#1a1a2a',
                 font=("Consolas", 10)).pack(side=tk.LEFT)

        self.port_combo = ttk.Combobox(port_frame, values=[80, 443], width=10)
        self.port_combo.set(443)
        self.port_combo.pack(side=tk.LEFT, padx=10)
        self.port_combo.bind('<<ComboboxSelected>>', lambda e: self.select_port(int(self.port_combo.get())))

        difficulty_frame = tk.Frame(target_frame, bg='#1a1a2a')
        difficulty_frame.pack(fill=tk.X, padx=10, pady=5)

        tk.Label(difficulty_frame, text="Difficulty:", fg='#8888ff', bg='#1a1a2a',
                 font=("Consolas", 10)).pack(side=tk.LEFT)

        self.difficulty_label = tk.Label(difficulty_frame, text="95", fg='#ff4444', bg='#1a1a2a',
                                         font=("Consolas", 10, "bold"))
        self.difficulty_label.pack(side=tk.LEFT, padx=10)

        # Статистика
        stats_frame = tk.LabelFrame(left_panel, text="📊 STATISTICS", fg='#00ff00', bg='#1a1a2a',
                                    font=("Consolas", 12, "bold"))
        stats_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.stats_labels = {}
        stats_items = [
            ("packets", "Packets Sent:", "0"),
            ("bytes", "Data Transferred:", "0 MB"),
            ("speed", "Attack Speed:", "0 Mbps"),
            ("power", "Attack Power:", "0%"),
            ("time", "Attack Time:", "00:00:00"),
            ("response", "Server Response:", "NORMAL"),
            ("remaining", "Time Remaining:", "∞"),
            ("earnings", "This Attack:", "0"),
        ]

        for key, label, value in stats_items:
            frame = tk.Frame(stats_frame, bg='#1a1a2a')
            frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(frame, text=label, fg='#aaaaaa', bg='#1a1a2a',
                     font=("Consolas", 10), width=20, anchor='w').pack(side=tk.LEFT)

            self.stats_labels[key] = tk.Label(frame, text=value, fg='#00ff00', bg='#1a1a2a',
                                              font=("Consolas", 10, "bold"), anchor='w')
            self.stats_labels[key].pack(side=tk.LEFT, padx=10)

        # Правая панель
        right_panel = tk.Frame(main_frame, bg='#1a1a2a')
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5)

        graph_frame = tk.LabelFrame(right_panel, text="📈 ATTACK GRAPH", fg='#00ff00', bg='#1a1a2a',
                                    font=("Consolas", 12, "bold"))
        graph_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        self.graph_canvas = tk.Canvas(graph_frame, bg='#000000', height=150, highlightthickness=0)
        self.graph_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        log_frame = tk.LabelFrame(right_panel, text="📋 ATTACK LOGS", fg='#00ff00', bg='#1a1a2a',
                                  font=("Consolas", 12, "bold"))
        log_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        log_controls = tk.Frame(log_frame, bg='#1a1a2a')
        log_controls.pack(fill=tk.X, padx=5, pady=5)

        tk.Button(log_controls, text="Clear Logs", command=self.clear_logs,
                  bg='#333333', fg='white').pack(side=tk.RIGHT)

        self.log_text = tk.Text(
            log_frame,
            bg='#000000',
            fg='#00ff00',
            font=("Consolas", 9),
            wrap=tk.WORD,
            height=12
        )
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)

        bottom_frame = tk.Frame(self.root, bg='#1a1a2a', height=30)
        bottom_frame.pack(fill=tk.X, side=tk.BOTTOM)

        system_info = f"OS: {platform.system()} {platform.release()} | Python: {platform.python_version()}"
        tk.Label(bottom_frame, text=system_info, fg='#666666', bg='#1a1a2a',
                 font=("Consolas", 8)).pack(side=tk.LEFT, padx=10)

        sites_count = len(self.sites_database)
        tk.Label(bottom_frame, text=f"📋 {sites_count} sites loaded", fg='#666666', bg='#1a1a2a',
                 font=("Consolas", 8)).pack(side=tk.LEFT, padx=20)

        tk.Label(bottom_frame, text="F2-Shop | F5-Start | F6-Stop | Ctrl+P-Exit | F1-Help",
                 fg='#666666', bg='#1a1a2a', font=("Consolas", 8)).pack(side=tk.RIGHT, padx=10)

        self.add_log("🚀 DDoS Simulator v5.4 initialized")
        self.add_log(f"🎯 Current target: Google ({self.target_domain})")
        self.add_log(f"💰 Starting coins: {self.coins}")
        self.add_log(f"🤖 Starting bots: {self.bots}")
        self.add_log("⚠️ SIMULATION MODE - No real packets are sent")

    def open_shop(self, event=None):
        """Открытие магазина"""
        shop_window = tk.Toplevel(self.root)
        shop_window.title("🛒 DDoS SHOP")
        shop_window.geometry("550x650")
        shop_window.configure(bg='#1a1a2a')
        shop_window.resizable(False, False)

        title = tk.Label(shop_window, text="🛒 МАГАЗИН УЛУЧШЕНИЙ",
                         font=("Arial", 16, "bold"), fg='gold', bg='#1a1a2a')
        title.pack(pady=10)

        balance_frame = tk.Frame(shop_window, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
        balance_frame.pack(pady=10, padx=20, fill=tk.X)

        tk.Label(balance_frame, text="💰 Ваш баланс:", font=("Arial", 12),
                 bg='#2a2a3a', fg='white').pack(side=tk.LEFT, padx=10, pady=5)
        balance_label = tk.Label(balance_frame, text=f"{self.coins}", font=("Arial", 16, "bold"),
                                 bg='#2a2a3a', fg='gold')
        balance_label.pack(side=tk.LEFT, padx=10, pady=5)

        canvas = tk.Canvas(shop_window, bg='#1a1a2a', highlightthickness=0)
        scrollbar = tk.Scrollbar(shop_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#1a1a2a')

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        items = [
            ("🤖 Купить бота", "bot", self.get_item_price("bot"),
             f"➕ Добавляет одного бота\nТекущее количество: {self.bots}\nКуплено: {self.purchased_count['bot']}",
             "Купить бота"),

            ("📊 Апгрейд уровня ботов", "bot_level", self.get_item_price("bot_level"),
             f"⚡ Увеличивает мощность всех ботов\nТекущий уровень: {self.bot_level}\n+15% к урону\nКуплено: {self.purchased_count['bot_level']}",
             "Повысить уровень"),

            ("⚡ Ускорение атаки", "attack_speed", self.get_item_price("attack_speed"),
             f"🚀 Увеличивает скорость отправки пакетов\nТекущий множитель: {self.attack_speed:.1f}x\n+0.2x к скорости\nКуплено: {self.purchased_count['attack_speed']}",
             "Ускорить атаку"),

            ("💪 Мощность ботов", "bot_power", self.get_item_price("bot_power"),
             f"🔥 Увеличивает урон от атаки\nТекущий множитель: {self.bot_power:.1f}x\n+0.3x к мощности\nКуплено: {self.purchased_count['bot_power']}",
             "Увеличить мощность"),

            ("🤖 Автоматическая атака", "auto_attack", self.shop_prices["auto_attack"],
             f"🔄 Атака запускается автоматически при выборе сайта\nСтатус: {'✅' if self.auto_attack else '❌'}\nЦена фиксированная",
             "Включить автоатаку"),

            ("💰 Двойные монеты", "double_coins", self.shop_prices["double_coins"],
             f"💸 Получайте в 2 раза больше монет за атаки\nСтатус: {'✅' if self.double_coins else '❌'}\nЦена фиксированная",
             "Включить двойные монеты"),
        ]

        for name, item_id, price, desc, btn_text in items:
            item_frame = tk.Frame(scrollable_frame, bg='#2a2a3a', relief=tk.RAISED, borderwidth=2)
            item_frame.pack(fill=tk.X, padx=10, pady=5)

            header_frame = tk.Frame(item_frame, bg='#2a2a3a')
            header_frame.pack(fill=tk.X, padx=10, pady=5)

            tk.Label(header_frame, text=name, font=("Arial", 12, "bold"),
                     bg='#2a2a3a', fg='gold').pack(side=tk.LEFT)

            price_label = tk.Label(header_frame, text=f"{price}💰", font=("Arial", 12, "bold"),
                                   bg='#2a2a3a', fg='lime')
            price_label.pack(side=tk.RIGHT)

            desc_label = tk.Label(item_frame, text=desc, font=("Arial", 9),
                                  bg='#2a2a3a', fg='#aaaaaa', justify=tk.LEFT)
            desc_label.pack(fill=tk.X, padx=10, pady=5)

            buy_btn = tk.Button(
                item_frame,
                text=btn_text,
                bg='#4a4a5a',
                fg='white',
                command=lambda i=item_id, w=shop_window, bl=balance_label: self.buy_item_from_shop(i, w, bl)
            )
            buy_btn.pack(pady=5)

        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

    def buy_item_from_shop(self, item_id, shop_window, balance_label):
        """Покупка предмета из магазина"""
        price = self.get_item_price(item_id) if item_id in self.purchased_count else self.shop_prices[item_id]

        if self.coins < price:
            messagebox.showerror("Ошибка", f"Недостаточно монет! Нужно {price}💰")
            return False

        if item_id in self.purchased_count:
            self.purchased_count[item_id] += 1

        if item_id == "bot":
            self.bots += 1
            self.coins -= price
            self.add_log(f"🤖 Куплен бот! Всего ботов: {self.bots}")

        elif item_id == "bot_level":
            self.bot_level += 1
            self.coins -= price
            self.add_log(f"📊 Уровень ботов повышен до {self.bot_level}")

        elif item_id == "attack_speed":
            self.attack_speed += 0.2
            self.coins -= price
            self.add_log(f"⚡ Скорость атаки увеличена до {self.attack_speed:.1f}x")

        elif item_id == "bot_power":
            self.bot_power += 0.3
            self.coins -= price
            self.add_log(f"💪 Мощность ботов увеличена до {self.bot_power:.1f}x")

        elif item_id == "auto_attack":
            if not self.auto_attack:
                self.auto_attack = True
                self.coins -= price
                self.add_log("🤖 Автоматическая атака активирована")
                self.start_auto_attack()
            else:
                messagebox.showinfo("Инфо", "Автоатака уже активирована!")
                return False

        elif item_id == "double_coins":
            if not self.double_coins:
                self.double_coins = True
                self.coins -= price
                self.add_log("💰 Двойные монеты активированы")
            else:
                messagebox.showinfo("Инфо", "Двойные монеты уже активированы!")
                return False

        self.update_econ_display()
        self.update_attack_duration()
        balance_label.config(text=f"{self.coins}")

        shop_window.destroy()
        self.open_shop()

        return True

    def start_auto_attack(self):
        """Запуск автоматической атаки"""
        if self.auto_attack and not self.attack_active:
            self.start_attack()

    def update_econ_display(self):
        """Обновление экономического дисплея"""
        self.coins_label.config(text=f"{self.coins}")
        self.bots_label.config(text=f"{self.bots}")
        self.bot_level_label.config(text=f"{self.bot_level}")
        self.speed_label.config(text=f"{self.attack_speed:.1f}x")
        self.power_label.config(text=f"{self.bot_power:.1f}x")

    def update_attack_duration(self):
        """Обновление длительности атаки"""
        self.attack_duration = self.calculate_attack_duration()

    def on_site_change(self, event):
        """Обработка смены сайта"""
        site = self.site_combo.get()
        self.update_site_info(site)

        if self.attack_active:
            self.stop_attack()

        self.reset_attack_stats()

        if self.auto_attack:
            self.start_attack()

    def update_site_info(self, site_name):
        """Обновление информации о сайте"""
        if site_name in self.sites_database:
            site = self.sites_database[site_name]
            self.current_site = site_name
            self.target_domain = site["domains"][0]
            self.target_ip = site["ip"]

            self.site_info_label.config(
                text=f"📍 {site_name} | Server: {site['server']} | Country: {site['country']} | 难度: {site['difficulty']}"
            )
            self.ip_entry.config(state='normal')
            self.ip_entry.delete(0, tk.END)
            self.ip_entry.insert(0, self.target_ip)
            self.ip_entry.config(state='readonly')
            self.domain_label.config(text=self.target_domain)
            self.difficulty_label.config(text=str(site['difficulty']))

            port_menu = self.port_combo['menu']
            port_menu.delete(0, 'end')
            for port in site["ports"]:
                port_menu.add_command(
                    label=port,
                    command=lambda p=port: self.select_port(p)
                )
            self.port_combo.set(site["ports"][0])
            self.target_port = site["ports"][0]

            self.add_log(f"🌐 Target changed to: {site_name} ({self.target_domain})")
            self.add_log(f"📍 Server location: {site['country']} | Difficulty: {site['difficulty']}")

    def select_port(self, port):
        """Выбор порта"""
        self.target_port = port
        self.port_combo.set(port)

    def start_attack(self):
        """Запуск атаки"""
        if not self.attack_active:
            self.attack_active = True
            self.attack_duration = self.calculate_attack_duration()
            self.attack_end_time = time.time() + self.attack_duration
            self.attack_power = 0
            self.attack_start_time = time.time()
            self.total_earnings_this_attack = 0
            self.last_earnings_update = time.time()

            self.start_btn.config(state=tk.DISABLED)
            self.stop_btn.config(state=tk.NORMAL)
            self.status_label.config(text="🔥 ATTACK IN PROGRESS", fg='#ff0000')

            self.add_log(f"🚀 Attack started: {self.attack_combo.get()}")
            self.add_log(f"🎯 Target: {self.current_site} ({self.target_domain})")
            self.add_log(f"📍 IP: {self.target_ip}:{self.target_port}")
            self.add_log(f"🤖 Bots engaged: {self.bots} (Level {self.bot_level})")
            self.add_log(f"⚡ Speed: {self.attack_speed:.1f}x | Power: {self.bot_power:.1f}x")
            self.add_log(f"⏱️ Estimated duration: {self.attack_duration} seconds")

    def stop_attack(self):
        """Остановка атаки"""
        if self.attack_active:
            self.attack_active = False
            self.attack_end_time = None

            if self.total_earnings_this_attack > 0:
                self.coins += self.total_earnings_this_attack
                self.total_coins_earned += self.total_earnings_this_attack
                self.add_log(f"💰💰💰 ФИНАЛ: Заработано {self.total_earnings_this_attack} монет!")

            self.start_btn.config(state=tk.NORMAL)
            self.stop_btn.config(state=tk.DISABLED)
            self.status_label.config(text="⏸️ STOPPED", fg='#ffff00')
            self.add_log("🛑 Attack stopped manually")

            self.update_econ_display()

    def update_stats(self):
        """Обновление статистики - ГЛАВНАЯ ФУНКЦИЯ"""
        if self.running:
            if self.attack_active:
                # Проверка завершения атаки
                if self.attack_end_time and time.time() >= self.attack_end_time:
                    self.attack_complete()
                else:
                    # Обновляем статистику каждые 100ms
                    packet_increment = self.calculate_packet_increment()
                    self.packets_sent += packet_increment
                    self.bytes_sent += packet_increment * random.randint(500, 1500)

                    power_increment = self.calculate_attack_power_increment()
                    self.attack_power = min(100, self.attack_power + power_increment)

                    # Обновляем график
                    self.graph_data.pop(0)
                    self.graph_data.append(self.attack_power)

                    # Заработок монет
                    current_time = time.time()
                    if current_time - self.last_earnings_update >= 3:
                        earnings = self.calculate_earnings()

                        if self.double_coins:
                            earnings *= 2

                        self.total_earnings_this_attack += earnings
                        self.last_earnings_update = current_time

                        percent = (earnings / max(1, self.coins)) * 100
                        self.add_log(f"💰 +{earnings} монет ({percent:.1f}% от баланса)", "#FFD700")

                    # Обновляем ВСЕ метки статистики
                    if self.stats_labels:
                        self.stats_labels['packets'].config(text=f"{self.packets_sent:,}")

                        bytes_mb = self.bytes_sent / (1024 * 1024)
                        self.stats_labels['bytes'].config(text=f"{bytes_mb:.2f} MB")

                        speed = (self.bytes_sent * 8) / (1024 * 1024) / ((time.time() - self.attack_start_time) + 1)
                        self.stats_labels['speed'].config(text=f"{speed:.2f} Mbps")

                        self.stats_labels['power'].config(text=f"{self.attack_power:.1f}%")

                        elapsed = int(time.time() - self.attack_start_time)
                        hours = elapsed // 3600
                        minutes = (elapsed % 3600) // 60
                        seconds = elapsed % 60
                        self.stats_labels['time'].config(text=f"{hours:02d}:{minutes:02d}:{seconds:02d}")

                        if self.attack_end_time:
                            remaining = int(self.attack_end_time - time.time())
                            if remaining > 0:
                                mins = remaining // 60
                                secs = remaining % 60
                                self.stats_labels['remaining'].config(text=f"{mins:02d}:{secs:02d}")

                                if remaining < 10:
                                    self.stats_labels['remaining'].config(fg='#ff0000')
                                elif remaining < 30:
                                    self.stats_labels['remaining'].config(fg='#ffaa00')
                                else:
                                    self.stats_labels['remaining'].config(fg='#00ff00')

                        # Статус сервера
                        remaining_time = self.attack_end_time - time.time() if self.attack_end_time else 0
                        site_difficulty = self.sites_database[self.current_site]['difficulty']
                        effective_power = self.attack_power * self.bot_power * (1 + self.bot_level * 0.15)

                        if remaining_time < 10:
                            self.stats_labels['response'].config(text="DYING", fg='#ff0000')
                        elif effective_power > site_difficulty * 0.9:
                            self.stats_labels['response'].config(text="CRITICAL", fg='#ff0000')
                        elif effective_power > site_difficulty * 0.7:
                            self.stats_labels['response'].config(text="DEGRADED", fg='#ffaa00')
                        elif effective_power > site_difficulty * 0.4:
                            self.stats_labels['response'].config(text="SLOW", fg='#ffff00')
                        else:
                            self.stats_labels['response'].config(text="NORMAL", fg='#00ff00')

                        self.stats_labels['earnings'].config(text=f"{self.total_earnings_this_attack}")

                    # Генерация случайных логов
                    if random.random() > 0.9:
                        self.generate_random_log()

            # Продолжаем цикл обновления
            self.root.after(100, self.update_stats)

    def attack_complete(self):
        """Завершение атаки"""
        self.attack_active = False
        self.attack_end_time = None

        if self.total_earnings_this_attack > 0:
            self.coins += self.total_earnings_this_attack
            self.total_coins_earned += self.total_earnings_this_attack

        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_label.config(text="✅ COMPLETED", fg='#00ff00')

        self.add_log("✅ Attack completed successfully!")
        self.add_log(f"💰💰💰 ИТОГО ЗА АТАКУ: {self.total_earnings_this_attack} монет!")
        self.add_log(f"📊 Пакетов: {self.packets_sent:,}, Мощность: {self.attack_power:.1f}%")

        self.update_econ_display()
        self.reset_attack_stats()

    def reset_attack_stats(self):
        """Сброс статистики атаки"""
        self.packets_sent = 0
        self.bytes_sent = 0
        self.attack_power = 0
        self.total_earnings_this_attack = 0
        self.graph_data = [0] * 60

        if self.stats_labels:
            self.stats_labels['packets'].config(text="0")
            self.stats_labels['bytes'].config(text="0 MB")
            self.stats_labels['speed'].config(text="0 Mbps")
            self.stats_labels['power'].config(text="0%")
            self.stats_labels['time'].config(text="00:00:00")
            self.stats_labels['remaining'].config(text="∞")
            self.stats_labels['earnings'].config(text="0")

    def change_attack(self):
        """Смена типа атаки"""
        self.attack_type = self.attack_var.get()
        if self.attack_active:
            self.add_log(f"🔄 Attack type changed to: {self.attack_type}")

    def on_attack_change(self, event):
        self.attack_type = self.attack_combo.get()
        if self.attack_active:
            self.add_log(f"🔄 Attack type changed to: {self.attack_type}")

    def random_attack(self):
        """Случайный тип атаки"""
        types = ["SYN Flood", "UDP Flood", "HTTP Flood", "ICMP Flood",
                 "DNS Amplification", "Slowloris", "Ping of Death"]
        self.attack_type = random.choice(types)
        self.attack_combo.set(self.attack_type)
        self.add_log(f"🎲 Random attack selected: {self.attack_type}")

    def reset_game(self):
        """Полный сброс игры"""
        if messagebox.askyesno("Сброс", "Вы уверены? Весь прогресс будет потерян!"):
            self.coins = 500
            self.total_coins_earned = 0
            self.bots = 50
            self.bot_level = 1
            self.attack_speed = 1.0
            self.bot_power = 1.0
            self.auto_attack = False
            self.double_coins = False

            self.shop_prices = self.base_prices.copy()
            self.purchased_count = {
                "bot": 0,
                "bot_level": 0,
                "attack_speed": 0,
                "bot_power": 0,
            }

            self.reset_attack_stats()
            self.update_econ_display()
            self.update_attack_duration()
            self.add_log("📊 Game reset to initial state")

    def update_graph(self):
        """Обновление графика"""
        if self.running:
            self.graph_canvas.delete("all")

            width = self.graph_canvas.winfo_width()
            height = self.graph_canvas.winfo_height()

            if width > 10 and height > 10:
                for i in range(0, 101, 20):
                    y = height - (i / 100) * height
                    self.graph_canvas.create_line(0, y, width, y, fill='#333333', width=1)

                points = []
                for i, value in enumerate(self.graph_data):
                    x = (i / len(self.graph_data)) * width
                    y = height - (value / 100) * height
                    points.append((x, y))

                for i in range(len(points) - 1):
                    x1, y1 = points[i]
                    x2, y2 = points[i + 1]

                    if self.attack_active and self.attack_end_time:
                        remaining = self.attack_end_time - time.time()
                        if remaining < 10:
                            color = '#ff0000'
                        elif remaining < 30:
                            color = '#ffaa00'
                        else:
                            color = '#00ff00'
                    else:
                        color = '#00ff00'

                    self.graph_canvas.create_line(x1, y1, x2, y2, fill=color, width=2)

                current = self.graph_data[-1]
                self.graph_canvas.create_text(10, 10, text=f"{current:.1f}%",
                                              fill='#00ff00', anchor='nw')

            self.root.after(200, self.update_graph)

    def update_resources(self):
        """Обновление ресурсов"""
        if self.running:
            try:
                cpu = psutil.cpu_percent()
                memory = psutil.virtual_memory().percent
                self.root.title(f"🛡️ DDoS Simulator | Coins: {self.coins} | Bots: {self.bots} | CPU: {cpu}%")
            except:
                pass
            self.root.after(2000, self.update_resources)

    def generate_random_log(self):
        """Генерация лога"""
        site = self.current_site

        logs = [
            (f"💥 Critical hit on {site} servers!", "#ff0000"),
            (f"🤖 Bot swarm attacking {site} with {self.bots} bots", "#00ff00"),
            (f"⚡ Attack speed: {self.attack_speed:.1f}x", "#ffff00"),
            (f"💪 Bot power: {self.bot_power:.1f}x (Level {self.bot_level})", "#ffaa00"),
            (f"🔄 {self.bots} bots synchronized attack", "#00ff00"),
            (f"🎯 Target difficulty: {self.sites_database[site]['difficulty']}", "#8888ff"),
        ]

        log, color = random.choice(logs)
        self.add_log(log, color)

    def add_log(self, message, color='#00ff00'):
        """Добавление лога"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] {message}\n")
        self.log_text.see('end')

        if float(self.log_text.index('end-1c')) > 1000:
            self.log_text.delete(1.0, 2.0)

    def clear_logs(self):
        """Очистка логов"""
        self.log_text.delete(1.0, tk.END)
        self.add_log("📋 Logs cleared")

    def save_game(self):
        """Сохранение игры"""
        save_data = {
            "coins": self.coins,
            "total_coins_earned": self.total_coins_earned,
            "bots": self.bots,
            "bot_level": self.bot_level,
            "attack_speed": self.attack_speed,
            "bot_power": self.bot_power,
            "auto_attack": self.auto_attack,
            "double_coins": self.double_coins,
            "purchased_count": self.purchased_count,
        }

        try:
            with open("ddos_save.json", "w") as f:
                json.dump(save_data, f)
            self.add_log("💾 Game saved successfully")
            messagebox.showinfo("Сохранение", "Игра сохранена!")
        except:
            messagebox.showerror("Ошибка", "Не удалось сохранить игру")

    def load_game(self):
        """Загрузка игры"""
        try:
            with open("ddos_save.json", "r") as f:
                save_data = json.load(f)

            self.coins = save_data["coins"]
            self.total_coins_earned = save_data["total_coins_earned"]
            self.bots = save_data["bots"]
            self.bot_level = save_data["bot_level"]
            self.attack_speed = save_data["attack_speed"]
            self.bot_power = save_data["bot_power"]
            self.auto_attack = save_data["auto_attack"]
            self.double_coins = save_data["double_coins"]
            self.purchased_count = save_data.get("purchased_count", {
                "bot": 0,
                "bot_level": 0,
                "attack_speed": 0,
                "bot_power": 0,
            })

            self.update_econ_display()
            self.update_attack_duration()
            self.add_log("💾 Game loaded successfully")

        except FileNotFoundError:
            pass
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить игру: {e}")

    def show_howto(self):
        """Как играть"""
        howto = """
        🎮 КАК ИГРАТЬ В DDoS SIMULATOR v5.4

        💰 СИСТЕМА МОНЕТ:
        • Каждые 3 секунды: +1/3 от баланса
        • Пример: 500 монет → +~167 каждые 3 сек
        • Двойные монеты (x2) в магазине

        🤖 БОТЫ:
        • Больше ботов = быстрее атака
        • Уровень ботов = +15% урона за уровень
        • Скорость = +0.2x пакетов/сек
        • Мощность = +0.3x урона

        ⏱️ ВРЕМЯ АТАКИ:
        • 50 ботов = 270 сек
        • 250 ботов = 150 сек
        • 500 ботов = 60 сек
        """
        messagebox.showinfo("How to Play", howto)

    def show_docs(self):
        """Документация"""
        docs = f"""
        WINDOWS DDoS SIMULATOR v5.4

        Особенности:
        • Доход: 1/3 от баланса каждые 3 сек
        • Прогрессивный рост богатства
        • Магазин с растущими ценами
        • Система уровней ботов
        • 25+ реальных сайтов

        База данных: {len(self.sites_database)} сайтов
        """
        messagebox.showinfo("Documentation", docs)

    def show_about(self):
        """О программе"""
        about = f"""
        WINDOWS DDoS SIMULATOR v5.4
        Исправленная версия

        {platform.system()} {platform.release()}
        Python {platform.python_version()}

        ⚠️ ТОЛЬКО ДЛЯ ОБУЧЕНИЯ ⚠️

        • Полностью безопасная симуляция
        • Никаких реальных пакетов
        • Экономическая стратегия
        """
        messagebox.showinfo("About", about)

    def show_help(self, event=None):
        """Помощь"""
        help_text = """
        ГОРЯЧИЕ КЛАВИШИ:

        F2        - Магазин
        F5        - Старт атаки
        F6        - Стоп атаки
        Ctrl+P    - Выход с сохранением
        F1        - Помощь
        """
        messagebox.showinfo("Hotkeys", help_text)

    def emergency_stop(self, event=None):
        """Экстренная остановка"""
        self.save_game()
        self.running = False
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def run(self):
        """Запуск"""
        sites_count = len(self.sites_database)
        print("\n" + "=" * 70)
        print("🛡️ WINDOWS DDoS SIMULATOR v5.4 - ИСПРАВЛЕННАЯ")
        print("=" * 70)
        print("⚠️  SIMULATION MODE - No real packets are sent")
        print("⚠️  For educational purposes only")
        print("=" * 70)
        print(f"📋 Available sites: {sites_count} real websites")
        print(f"💰 Starting coins: {self.coins}")
        print(f"🤖 Starting bots: {self.bots}")
        print(f"💰 +1/3 от баланса каждые 3 секунды!")
        print("🛑 Press Ctrl+P to exit")
        print("=" * 70)

        try:
            self.root.mainloop()
        except KeyboardInterrupt:
            self.emergency_stop()


if __name__ == "__main__":
    try:
        import psutil
    except ImportError:
        print("Installing required library: psutil")
        os.system("pip install psutil")
        import psutil

    sim = DDoSSimulator()
    sim.run()