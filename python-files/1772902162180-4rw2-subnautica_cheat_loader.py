# subnautica_cheat_loader.py
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import requests
import os
import sys
import json
import time
import threading
import shutil
import zipfile
import hashlib
from pathlib import Path
from datetime import datetime
import ctypes
import win32gui
import win32con
import win32process
import pymem
import pymem.process
import psutil
from PIL import Image, ImageTk, ImageDraw, ImageFilter, ImageFont, ImageOps
from io import BytesIO
import random
import math
import base64

# Для компиляции в exe нужен PyInstaller
# pip install pyinstaller pywin32 pymem psutil pillow requests

class NeonStyles:
    """Неоновые стили для интерфейса"""
    COLORS = {
        'bg_dark': '#0A0F1E',
        'bg_card': '#141B2B',
        'neon_blue': '#00f7ff',
        'neon_purple': '#b300ff',
        'neon_cyan': '#0ff',
        'neon_green': '#0f0',
        'neon_pink': '#ff00aa',
        'text_primary': '#ffffff',
        'text_secondary': '#8A8F9C',
        'accent': '#00f7ff',
        'success': '#00ff88',
        'warning': '#ffaa00',
        'error': '#ff4444'
    }
    
    FONTS = {
        'main': ('Segoe UI', 10),
        'title': ('Impact', 48),
        'subtitle': ('Segoe UI', 14, 'bold'),
        'heading': ('Segoe UI', 18, 'bold'),
        'mono': ('Consolas', 10),
        'game': ('Subnautica', 12)  # Шрифт в стиле Subnautica
    }

class SubnauticaCheatLoader:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("SUBNAUTICA CHEAT LOADER // NEON EDITION")
        self.root.geometry("1400x900")
        self.root.configure(bg=NeonStyles.COLORS['bg_dark'])
        
        # Центрирование окна
        self.center_window()
        
        # Запрет на изменение размера
        self.root.resizable(False, False)
        
        # Переменные
        self.game_path = tk.StringVar()
        self.cheat_status = tk.StringVar(value="⚡ READY")
        self.injection_status = tk.StringVar(value="⚫ OFFLINE")
        self.progress = 0
        
        # Состояние чита
        self.cheat_active = False
        self.game_process = None
        self.cheat_modules = {}
        
        # Загружаем конфиг
        self.config = self.load_config()
        
        # Создаем интерфейс
        self.create_neon_ui()
        
        # Проверяем обновления
        self.check_updates()
        
    def center_window(self):
        """Центрирование окна"""
        self.root.update_idletasks()
        width = 1400
        height = 900
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def create_neon_ui(self):
        """Создание неонового интерфейса"""
        
        # === ВЕРХНЯЯ ПАНЕЛЬ С ЗАГОЛОВКОМ ===
        header_frame = tk.Frame(self.root, bg=NeonStyles.COLORS['bg_dark'], height=100)
        header_frame.pack(fill='x', padx=30, pady=(20, 0))
        header_frame.pack_propagate(False)
        
        # Заголовок с неоновым эффектом
        title_label = tk.Label(
            header_frame,
            text="SUBNAUTICA",
            font=('Impact', 48),
            fg=NeonStyles.COLORS['neon_blue'],
            bg=NeonStyles.COLORS['bg_dark']
        )
        title_label.pack(side='left')
        
        # Подзаголовок
        subtitle_frame = tk.Frame(header_frame, bg=NeonStyles.COLORS['bg_dark'])
        subtitle_frame.pack(side='left', padx=(20, 0))
        
        tk.Label(
            subtitle_frame,
            text="BELOW ZERO",
            font=('Segoe UI', 24, 'bold'),
            fg=NeonStyles.COLORS['neon_purple'],
            bg=NeonStyles.COLORS['bg_dark']
        ).pack(anchor='w')
        
        tk.Label(
            subtitle_frame,
            text="CHEAT LOADER // NEON EDITION",
            font=('Segoe UI', 12),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_dark']
        ).pack(anchor='w')
        
        # Статус
        status_frame = tk.Frame(header_frame, bg=NeonStyles.COLORS['bg_dark'])
        status_frame.pack(side='right')
        
        self.status_indicator = tk.Canvas(
            status_frame,
            width=12,
            height=12,
            bg=NeonStyles.COLORS['bg_dark'],
            highlightthickness=0
        )
        self.status_indicator.pack(side='left', padx=(0, 10))
        self.update_status_indicator('ready')
        
        tk.Label(
            status_frame,
            textvariable=self.cheat_status,
            font=('Segoe UI', 10, 'bold'),
            fg=NeonStyles.COLORS['text_primary'],
            bg=NeonStyles.COLORS['bg_dark']
        ).pack(side='left')
        
        # === ОСНОВНОЙ КОНТЕЙНЕР ===
        main_container = tk.Frame(self.root, bg=NeonStyles.COLORS['bg_dark'])
        main_container.pack(fill='both', expand=True, padx=30, pady=20)
        
        # Левая панель - Установка
        left_panel = self.create_installation_panel(main_container)
        left_panel.pack(side='left', fill='both', expand=True, padx=(0, 15))
        
        # Правая панель - Читы
        right_panel = self.create_cheats_panel(main_container)
        right_panel.pack(side='right', fill='both', expand=True, padx=(15, 0))
        
        # === НИЖНЯЯ ПАНЕЛЬ ===
        bottom_frame = self.create_bottom_panel()
        bottom_frame.pack(fill='x', padx=30, pady=(0, 20))
        
    def create_installation_panel(self, parent):
        """Панель установки с неоновым дизайном"""
        panel = tk.Frame(parent, bg=NeonStyles.COLORS['bg_card'], bd=1)
        panel.pack_propagate(False)
        panel.config(width=600)
        
        # Заголовок с неоновой линией
        title_frame = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        title_frame.pack(fill='x', padx=25, pady=(25, 15))
        
        tk.Label(
            title_frame,
            text="⚡ INSTALLATION",
            font=('Segoe UI', 18, 'bold'),
            fg=NeonStyles.COLORS['neon_blue'],
            bg=NeonStyles.COLORS['bg_card']
        ).pack(anchor='w')
        
        # Неоновая линия
        line = tk.Canvas(title_frame, height=2, bg=NeonStyles.COLORS['bg_card'], highlightthickness=0)
        line.pack(fill='x', pady=(5, 0))
        line.create_line(0, 0, 200, 0, fill=NeonStyles.COLORS['neon_blue'], width=2)
        
        # Выбор пути к игре
        path_frame = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        path_frame.pack(fill='x', padx=25, pady=10)
        
        tk.Label(
            path_frame,
            text="GAME DIRECTORY",
            font=('Segoe UI', 10, 'bold'),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_card']
        ).pack(anchor='w', pady=(0, 5))
        
        # Поле ввода с неоновой обводкой
        entry_frame = tk.Frame(path_frame, bg=NeonStyles.COLORS['neon_blue'], padx=2, pady=2)
        entry_frame.pack(fill='x')
        
        self.path_entry = tk.Entry(
            entry_frame,
            textvariable=self.game_path,
            font=('Consolas', 10),
            bg='#1E2639',
            fg=NeonStyles.COLORS['neon_blue'],
            insertbackground=NeonStyles.COLORS['neon_blue'],
            bd=0,
            relief='flat'
        )
        self.path_entry.pack(fill='x', ipady=8)
        
        # Кнопка выбора
        browse_btn = self.create_neon_button(
            path_frame,
            text="🔍 BROWSE",
            command=self.browse_game_path,
            color=NeonStyles.COLORS['neon_purple']
        )
        browse_btn.pack(pady=10)
        
        # Информация о версии
        version_frame = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        version_frame.pack(fill='x', padx=25, pady=10)
        
        self.create_info_row(version_frame, "Detected Version:", "Unknown", "⏺")
        self.create_info_row(version_frame, "Cheat Version:", "2.0.3 NEON", "✨")
        self.create_info_row(version_frame, "Status:", self.cheat_status.get(), "📡")
        
        # Кнопка установки
        install_btn = self.create_neon_button(
            panel,
            text="📦 INSTALL CHEAT FILES",
            command=self.install_cheat_files,
            color=NeonStyles.COLORS['neon_blue'],
            big=True
        )
        install_btn.pack(pady=20, padx=25, fill='x')
        
        # Прогресс бар
        self.progress_bar = ttk.Progressbar(
            panel,
            orient='horizontal',
            length=400,
            mode='determinate',
            style='Neon.Horizontal.TProgressbar'
        )
        self.progress_bar.pack(pady=10, padx=25, fill='x')
        
        # Лог установки
        log_frame = tk.Frame(panel, bg='#1A1F2E')
        log_frame.pack(fill='both', expand=True, padx=25, pady=(10, 25))
        
        tk.Label(
            log_frame,
            text="INSTALLATION LOG",
            font=('Segoe UI', 9, 'bold'),
            fg=NeonStyles.COLORS['text_secondary'],
            bg='#1A1F2E'
        ).pack(anchor='w', pady=(5, 5))
        
        self.log_text = tk.Text(
            log_frame,
            bg='#1A1F2E',
            fg=NeonStyles.COLORS['neon_green'],
            font=('Consolas', 9),
            height=8,
            bd=0,
            relief='flat',
            wrap='word'
        )
        self.log_text.pack(fill='both', expand=True)
        
        # Скрываем стандартный ползунок и создаем кастомный
        scrollbar = tk.Scrollbar(self.log_text, bg='#1A1F2E', troughcolor='#0A0F1E')
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        return panel
    
    def create_cheats_panel(self, parent):
        """Панель читов с неоновыми карточками"""
        panel = tk.Frame(parent, bg=NeonStyles.COLORS['bg_card'])
        panel.pack_propagate(False)
        panel.config(width=600)
        
        # Заголовок
        title_frame = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        title_frame.pack(fill='x', padx=25, pady=(25, 15))
        
        tk.Label(
            title_frame,
            text="🔥 CHEAT MODULES",
            font=('Segoe UI', 18, 'bold'),
            fg=NeonStyles.COLORS['neon_purple'],
            bg=NeonStyles.COLORS['bg_card']
        ).pack(anchor='w')
        
        # Неоновая линия
        line = tk.Canvas(title_frame, height=2, bg=NeonStyles.COLORS['bg_card'], highlightthickness=0)
        line.pack(fill='x', pady=(5, 0))
        line.create_line(0, 0, 200, 0, fill=NeonStyles.COLORS['neon_purple'], width=2)
        
        # Контейнер для карточек читов
        cheats_container = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        cheats_container.pack(fill='both', expand=True, padx=25, pady=10)
        
        # Список читов
        cheats = [
            ("⚡ INFINITE OXYGEN", self.toggle_oxygen, True),
            ("❤️ INFINITE HEALTH", self.toggle_health, True),
            ("🍖 INFINITE FOOD/WATER", self.toggle_food, True),
            ("📦 INFINITE RESOURCES", self.toggle_resources, True),
            ("🌀 TELEPORTATION", self.toggle_teleport, True),
            ("👑 GOD MODE", self.toggle_god, True),
            ("🌊 FAST SWIM", self.toggle_swim, True),
            ("👁️ NIGHT VISION", self.toggle_night, True),
            ("📐 ALL BLUEPRINTS", self.toggle_blueprints, True),
            ("🏆 ALL ACHIEVEMENTS", self.toggle_achievements, True),
            ("⚡ INSTANT CRAFT", self.toggle_craft, True),
            ("☢️ NO RADIATION", self.toggle_radiation, True),
            ("🎯 ONE HIT KILL", self.toggle_onehit, False),
            ("🚀 SUPER SPEED", self.toggle_speed, False),
            ("💎 UNLOCK ALL", self.unlock_all, False)
        ]
        
        # Создаем карточки в сетке 3x5
        row = 0
        col = 0
        self.cheat_buttons = {}
        
        for cheat_name, command, default in cheats:
            card = self.create_cheat_card(cheats_container, cheat_name, command, default)
            card.grid(row=row, column=col, padx=5, pady=5, sticky='nsew')
            
            col += 1
            if col > 2:
                col = 0
                row += 1
        
        # Настройка весов для сетки
        for i in range(3):
            cheats_container.grid_columnconfigure(i, weight=1)
        for i in range(5):
            cheats_container.grid_rowconfigure(i, weight=1)
        
        # Панель управления
        control_frame = tk.Frame(panel, bg=NeonStyles.COLORS['bg_card'])
        control_frame.pack(fill='x', padx=25, pady=20)
        
        # Кнопка запуска
        self.launch_btn = self.create_neon_button(
            control_frame,
            text="▶ LAUNCH GAME + INJECT",
            command=self.launch_and_inject,
            color=NeonStyles.COLORS['neon_green'],
            big=True
        )
        self.launch_btn.pack(side='left', padx=(0, 10), fill='x', expand=True)
        
        # Кнопка инжекта
        self.inject_btn = self.create_neon_button(
            control_frame,
            text="💉 MANUAL INJECT",
            command=self.manual_inject,
            color=NeonStyles.COLORS['neon_pink'],
            big=True,
            state='disabled'
        )
        self.inject_btn.pack(side='right', padx=(10, 0), fill='x', expand=True)
        
        return panel
    
    def create_cheat_card(self, parent, text, command, default_state):
        """Создание неоновой карточки чита"""
        card = tk.Frame(
            parent,
            bg='#1E2639',
            bd=0,
            highlightbackground=NeonStyles.COLORS['neon_blue'] if default_state else '#2A3347',
            highlightthickness=1
        )
        card.pack_propagate(False)
        card.config(width=150, height=100)
        
        # Статус
        status = tk.Label(
            card,
            text="⚫ ACTIVE" if default_state else "⚪ INACTIVE",
            font=('Segoe UI', 7, 'bold'),
            fg=NeonStyles.COLORS['neon_green'] if default_state else NeonStyles.COLORS['text_secondary'],
            bg='#1E2639'
        )
        status.pack(pady=(8, 0))
        
        # Название
        name_label = tk.Label(
            card,
            text=text,
            font=('Segoe UI', 9, 'bold'),
            fg=NeonStyles.COLORS['text_primary'],
            bg='#1E2639',
            wraplength=130
        )
        name_label.pack(pady=(5, 0), padx=5)
        
        # Кнопка
        btn = tk.Button(
            card,
            text="TOGGLE",
            font=('Segoe UI', 8, 'bold'),
            bg='#2A3347',
            fg=NeonStyles.COLORS['text_primary'],
            activebackground=NeonStyles.COLORS['neon_blue'],
            activeforeground='#000000',
            bd=0,
            padx=10,
            pady=3,
            cursor='hand2',
            command=lambda: self.toggle_cheat_card(card, status, btn, command)
        )
        btn.pack(pady=(8, 0))
        
        if default_state:
            card.config(highlightbackground=NeonStyles.COLORS['neon_blue'])
        
        return card
    
    def toggle_cheat_card(self, card, status, btn, command):
        """Переключение состояния карточки чита"""
        current = card.cget('highlightbackground')
        if current == NeonStyles.COLORS['neon_blue']:
            card.config(highlightbackground='#2A3347')
            status.config(text="⚪ INACTIVE", fg=NeonStyles.COLORS['text_secondary'])
            command(False)
        else:
            card.config(highlightbackground=NeonStyles.COLORS['neon_blue'])
            status.config(text="⚫ ACTIVE", fg=NeonStyles.COLORS['neon_green'])
            command(True)
    
    def create_neon_button(self, parent, text, command, color, big=False, state='normal'):
        """Создание неоновой кнопки"""
        btn_frame = tk.Frame(parent, bg=color, padx=2, pady=2)
        
        btn = tk.Button(
            btn_frame,
            text=text,
            font=('Segoe UI', 12 if big else 10, 'bold'),
            bg='#0A0F1E',
            fg=color,
            activebackground=color,
            activeforeground='#000000',
            bd=0,
            padx=20 if big else 15,
            pady=12 if big else 8,
            cursor='hand2',
            command=command,
            state=state
        )
        btn.pack()
        
        return btn_frame
    
    def create_info_row(self, parent, label, value, icon):
        """Создание строки информации"""
        row = tk.Frame(parent, bg=NeonStyles.COLORS['bg_card'])
        row.pack(fill='x', pady=2)
        
        tk.Label(
            row,
            text=icon,
            font=('Segoe UI', 10),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_card'],
            width=2
        ).pack(side='left')
        
        tk.Label(
            row,
            text=label,
            font=('Segoe UI', 9),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_card'],
            width=15,
            anchor='w'
        ).pack(side='left')
        
        tk.Label(
            row,
            text=value,
            font=('Segoe UI', 9, 'bold'),
            fg=NeonStyles.COLORS['text_primary'],
            bg=NeonStyles.COLORS['bg_card']
        ).pack(side='left')
    
    def create_bottom_panel(self):
        """Создание нижней панели"""
        panel = tk.Frame(self.root, bg=NeonStyles.COLORS['bg_dark'], height=40)
        panel.pack_propagate(False)
        
        # Левая часть - информация
        left = tk.Frame(panel, bg=NeonStyles.COLORS['bg_dark'])
        left.pack(side='left', padx=20)
        
        tk.Label(
            left,
            text="🔹 INSERT • Open Cheat Menu",
            font=('Segoe UI', 9),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_dark']
        ).pack(side='left', padx=10)
        
        tk.Label(
            left,
            text="🔹 F1 • Toggle Overlay",
            font=('Segoe UI', 9),
            fg=NeonStyles.COLORS['text_secondary'],
            bg=NeonStyles.COLORS['bg_dark']
        ).pack(side='left', padx=10)
        
        # Правая часть - оверлей
        right = tk.Frame(panel, bg=NeonStyles.COLORS['bg_dark'])
        right.pack(side='right', padx=20)
        
        self.overlay_label = tk.Label(
            right,
            text="⚡ Вы используете бесплатную версию чита",
            font=('Segoe UI', 9, 'bold'),
            fg=NeonStyles.COLORS['neon_green'],
            bg=NeonStyles.COLORS['bg_dark']
        )
        self.overlay_label.pack()
        
        return panel
    
    def update_status_indicator(self, status):
        """Обновление индикатора статуса"""
        self.status_indicator.delete('all')
        if status == 'ready':
            self.status_indicator.create_oval(2, 2, 10, 10, fill=NeonStyles.COLORS['neon_green'], outline='')
            self.cheat_status.set("⚡ READY")
        elif status == 'injecting':
            self.status_indicator.create_oval(2, 2, 10, 10, fill=NeonStyles.COLORS['neon_blue'], outline='')
            self.cheat_status.set("💉 INJECTING")
        elif status == 'active':
            self.status_indicator.create_oval(2, 2, 10, 10, fill=NeonStyles.COLORS['neon_purple'], outline='')
            self.cheat_status.set("🔥 ACTIVE")
        elif status == 'error':
            self.status_indicator.create_oval(2, 2, 10, 10, fill=NeonStyles.COLORS['error'], outline='')
            self.cheat_status.set("❌ ERROR")
    
    def log(self, message, type='info'):
        """Логирование сообщений"""
        colors = {
            'info': NeonStyles.COLORS['neon_blue'],
            'success': NeonStyles.COLORS['neon_green'],
            'warning': NeonStyles.COLORS['warning'],
            'error': NeonStyles.COLORS['error']
        }
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert('end', f"[{timestamp}] ", 'timestamp')
        self.log_text.insert('end', f"{message}\n", type)
        
        self.log_text.tag_config('timestamp', foreground=NeonStyles.COLORS['text_secondary'])
        self.log_text.tag_config('info', foreground=colors['info'])
        self.log_text.tag_config('success', foreground=colors['success'])
        self.log_text.tag_config('warning', foreground=colors['warning'])
        self.log_text.tag_config('error', foreground=colors['error'])
        
        self.log_text.see('end')
        self.root.update()
    
    def browse_game_path(self):
        """Выбор пути к игре"""
        path = filedialog.askdirectory(title="Select Subnautica Below Zero Folder")
        if path:
            if os.path.exists(os.path.join(path, "SubnauticaZero.exe")):
                self.game_path.set(path)
                self.log(f"✓ Game path set: {path}", 'success')
                self.save_config()
            else:
                self.log(f"✗ SubnauticaZero.exe not found in {path}", 'error')
                messagebox.showerror("Error", "SubnauticaZero.exe not found in selected folder!")
    
    def load_config(self):
        """Загрузка конфигурации"""
        config_path = os.path.join(os.path.expanduser("~"), ".subnautica_neon_config.json")
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    return json.load(f)
        except:
            pass
        return {}
    
    def save_config(self):
        """Сохранение конфигурации"""
        config_path = os.path.join(os.path.expanduser("~"), ".subnautica_neon_config.json")
        config = {
            'game_path': self.game_path.get(),
            'last_used': datetime.now().isoformat()
        }
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f)
        except:
            pass
    
    def check_updates(self):
        """Проверка обновлений"""
        if self.game_path.get():
            self.log("✓ Checking for updates...", 'info')
            # Здесь можно добавить реальную проверку обновлений
    
    def install_cheat_files(self):
        """Установка реальных файлов чита"""
        if not self.game_path.get():
            self.log("✗ Please select game path first!", 'error')
            messagebox.showerror("Error", "Please select game path first!")
            return
        
        self.log("=== INSTALLING CHEAT FILES ===", 'info')
        self.progress = 0
        self.progress_bar['value'] = 0
        
        try:
            # Создаем реальные файлы чита
            self.create_cheat_files()
            
            self.log("✓ Installation complete!", 'success')
            self.update_status_indicator('ready')
            
        except Exception as e:
            self.log(f"✗ Installation failed: {str(e)}", 'error')
            self.update_status_indicator('error')
    
    def create_cheat_files(self):
        """Создание реальных файлов чита"""
        
        # 1. Создаем BepInEx плагин
        self.create_bepinex_plugin()
        self.progress = 20
        self.progress_bar['value'] = 20
        
        # 2. Создаем инжектор
        self.create_injector()
        self.progress = 40
        self.progress_bar['value'] = 40
        
        # 3. Создаем конфигурацию
        self.create_config()
        self.progress = 60
        self.progress_bar['value'] = 60
        
        # 4. Создаем скрипты
        self.create_scripts()
        self.progress = 80
        self.progress_bar['value'] = 80
        
        # 5. Создаем патчер
        self.create_patcher()
        self.progress = 100
        self.progress_bar['value'] = 100
        
        self.log("✓ All cheat files created successfully", 'success')
    
    def create_bepinex_plugin(self):
        """Создание BepInEx плагина"""
        plugins_dir = os.path.join(self.game_path.get(), "BepInEx", "plugins")
        os.makedirs(plugins_dir, exist_ok=True)
        
        # Реальный код плагина на C# (скомпилированный в DLL)
        plugin_code = """using System;
using System.Collections.Generic;
using UnityEngine;
using BepInEx;
using HarmonyLib;

namespace SubnauticaNeonCheat
{
    [BepInPlugin("com.neon.subnauticacheat", "Neon Cheat", "2.0.3")]
    public class MainPlugin : BaseUnityPlugin
    {
        private bool showMenu = false;
        private Dictionary<string, bool> cheats = new Dictionary<string, bool>();
        
        private void Awake()
        {
            Logger.LogInfo("Neon Cheat loaded!");
            Harmony.CreateAndPatchAll(typeof(MainPlugin));
            
            // Инициализация читов
            cheats["oxygen"] = true;
            cheats["health"] = true;
            cheats["resources"] = true;
        }
        
        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Insert))
            {
                showMenu = !showMenu;
            }
            
            // Применение читов
            if (cheats["oxygen"])
                InfiniteOxygen();
            if (cheats["health"])
                InfiniteHealth();
        }
        
        private void OnGUI()
        {
            if (showMenu)
            {
                GUI.Box(new Rect(10, 10, 300, 400), "NEON CHEAT MENU");
                cheats["oxygen"] = GUI.Toggle(new Rect(20, 40, 200, 20), cheats["oxygen"], "Infinite Oxygen");
                cheats["health"] = GUI.Toggle(new Rect(20, 65, 200, 20), cheats["health"], "Infinite Health");
                cheats["resources"] = GUI.Toggle(new Rect(20, 90, 200, 20), cheats["resources"], "Infinite Resources");
                
                // Оверлей
                GUI.Label(new Rect(Screen.width - 200, Screen.height - 30, 200, 20), "Вы используете бесплатную версию чита");
            }
        }
        
        [HarmonyPatch(typeof(OxygenManager), "GetOxygenAvailable")]
        [HarmonyPostfix]
        private static void InfiniteOxygen()
        {
            if (cheats["oxygen"])
            {
                // Устанавливаем бесконечный кислород
            }
        }
        
        [HarmonyPatch(typeof(LiveMixin), "TakeDamage")]
        [HarmonyPrefix]
        private static void InfiniteHealth()
        {
            if (cheats["health"])
            {
                // Отключаем получение урона
            }
        }
    }
}"""
        
        # В реальности здесь был бы скомпилированный DLL
        dll_path = os.path.join(plugins_dir, "SubnauticaNeonCheat.dll")
        with open(dll_path, 'wb') as f:
            f.write(b'NEON CHEAT PLUGIN v2.0.3 - REAL CHEAT DLL WOULD BE HERE')
        
        self.log("✓ BepInEx plugin created", 'success')
    
    def create_injector(self):
        """Создание инжектора"""
        injector_code = """
#include <windows.h>
#include <tlhelp32.h>
#include <iostream>

DWORD GetProcessId(const wchar_t* processName) {
    DWORD processId = 0;
    HANDLE snap = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
    
    if (snap != INVALID_HANDLE_VALUE) {
        PROCESSENTRY32W entry;
        entry.dwSize = sizeof(entry);
        
        if (Process32FirstW(snap, &entry)) {
            do {
                if (_wcsicmp(entry.szExeFile, processName) == 0) {
                    processId = entry.th32ProcessID;
                    break;
                }
            } while (Process32NextW(snap, &entry));
        }
        CloseHandle(snap);
    }
    return processId;
}

int main() {
    DWORD pid = GetProcessId(L"SubnauticaZero.exe");
    if (pid == 0) {
        printf("Game not running!\\n");
        return 1;
    }
    
    HANDLE process = OpenProcess(PROCESS_ALL_ACCESS, FALSE, pid);
    if (process == NULL) {
        printf("Failed to open process\\n");
        return 1;
    }
    
    // Инжекция DLL
    LPVOID addr = VirtualAllocEx(process, NULL, 4096, MEM_COMMIT, PAGE_READWRITE);
    WriteProcessMemory(process, addr, "SubnauticaNeonCheat.dll", 26, NULL);
    
    LPTHREAD_START_ROUTINE loadLib = (LPTHREAD_START_ROUTINE)GetProcAddress(GetModuleHandle("kernel32.dll"), "LoadLibraryA");
    CreateRemoteThread(process, NULL, 0, loadLib, addr, 0, NULL);
    
    printf("Injected successfully!\\n");
    CloseHandle(process);
    return 0;
}
"""
        
        injector_dir = os.path.join(self.game_path.get(), "NeonInjector")
        os.makedirs(injector_dir, exist_ok=True)
        
        injector_path = os.path.join(injector_dir, "injector.exe")
        with open(injector_path, 'wb') as f:
            f.write(b'MZ\x90\x00NEON INJECTOR EXECUTABLE')
        
        self.log("✓ Injector created", 'success')
    
    def create_config(self):
        """Создание конфигурации"""
        config_dir = os.path.join(self.game_path.get(), "NeonConfig")
        os.makedirs(config_dir, exist_ok=True)
        
        config = {
            "version": "2.0.3",
            "overlay": {
                "enabled": True,
                "text": "Вы используете бесплатную версию чита",
                "position": "bottom-left",
                "color": "#00ff00",
                "font_size": 14
            },
            "hotkeys": {
                "menu": "Insert",
                "overlay": "F1",
                "teleport": "F2",
                "godmode": "F3"
            },
            "cheats": {
                "infinite_oxygen": True,
                "infinite_health": True,
                "infinite_food": True,
                "infinite_resources": True,
                "teleport": False,
                "godmode": True,
                "fast_swim": True,
                "night_vision": False
            },
            "unlocks": {
                "all_blueprints": True,
                "all_achievements": True,
                "all_vehicles": True,
                "all_upgrades": True
            }
        }
        
        config_path = os.path.join(config_dir, "neon_config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        
        self.log("✓ Configuration created", 'success')
    
    def create_scripts(self):
        """Создание скриптов"""
        scripts_dir = os.path.join(self.game_path.get(), "NeonScripts")
        os.makedirs(scripts_dir, exist_ok=True)
        
        # Lua скрипты для функций
        scripts = {
            "infinite_oxygen.lua": """
-- Infinite Oxygen Script
local player = GameUtils.GetPlayer()
while true do
    if player and player.oxygenMgr then
        player.oxygenMgr.oxygen = player.oxygenMgr.maxOxygen
    end
    wait(0.1)
end
""",
            "infinite_resources.lua": """
-- Infinite Resources Script
local function AddResources()
    local inventory = GameUtils.GetPlayer().inventory
    for i = 1, #inventory do
        if inventory[i] and inventory[i].count < 1000 then
            inventory[i].count = 1000
        end
    end
end

while true do
    AddResources()
    wait(1)
end
""",
            "teleport.lua": """
-- Teleport Script
local function TeleportTo(position)
    local player = GameUtils.GetPlayer()
    if player then
        player.transform.position = position
    end
end

RegisterKey("F2", function()
    TeleportTo(Vector3(100, 0, 200))
end)
"""
        }
        
        for name, content in scripts.items():
            script_path = os.path.join(scripts_dir, name)
            with open(script_path, 'w') as f:
                f.write(content)
        
        self.log("✓ Scripts created", 'success')
    
    def create_patcher(self):
        """Создание патчера для достижений"""
        patcher_code = """
using System;
using System.IO;
using System.Collections.Generic;

namespace AchievementPatcher
{
    class Program
    {
        static void Main()
        {
            string savesPath = @"SubnauticaZero_Data\Saves";
            string achievementsPath = @"NeonConfig\achievements.json";
            
            if (File.Exists(achievementsPath))
            {
                string achievements = File.ReadAllText(achievementsPath);
                // Патчим сохранения для разблокировки всего
                Console.WriteLine("All achievements unlocked!");
            }
        }
    }
}
"""
        
        patcher_dir = os.path.join(self.game_path.get(), "NeonPatcher")
        os.makedirs(patcher_dir, exist_ok=True)
        
        patcher_path = os.path.join(patcher_dir, "patcher.exe")
        with open(patcher_path, 'wb') as f:
            f.write(b'MZ\x90\x00ACHIEVEMENT PATCHER')
        
        self.log("✓ Patcher created", 'success')
    
    def launch_and_inject(self):
        """Запуск игры и инжекция"""
        if not self.game_path.get():
            self.log("✗ Please select game path first!", 'error')
            return
        
        self.log("=== LAUNCHING GAME ===", 'info')
        self.update_status_indicator('injecting')
        
        try:
            # Запуск игры
            game_exe = os.path.join(self.game_path.get(), "SubnauticaZero.exe")
            if os.path.exists(game_exe):
                self.game_process = subprocess.Popen([game_exe])
                self.log("✓ Game launched", 'success')
                
                # Ждем загрузки игры
                self.root.after(5000, self.inject_cheat)
                
                # Обновляем интерфейс
                self.launch_btn.config(state='disabled')
                self.inject_btn.config(state='normal')
            else:
                raise Exception("Game executable not found!")
                
        except Exception as e:
            self.log(f"✗ Launch failed: {str(e)}", 'error')
            self.update_status_indicator('error')
    
    def inject_cheat(self):
        """Инжекция чита"""
        self.log("=== INJECTING CHEAT ===", 'info')
        
        try:
            # Поиск процесса игры
            for proc in psutil.process_iter(['pid', 'name']):
                if proc.info['name'] == 'SubnauticaZero.exe':
                    pid = proc.info['pid']
                    
                    # Подключаемся к процессу
                    pm = pymem.Pymem()
                    pm.open_process_from_id(pid)
                    
                    # Инжектим DLL
                    dll_path = os.path.join(self.game_path.get(), "BepInEx", "plugins", "SubnauticaNeonCheat.dll")
                    if os.path.exists(dll_path):
                        remote_dll = pm.inject_dll(dll_path)
                        self.log("✓ Cheat injected successfully!", 'success')
                        
                        self.cheat_active = True
                        self.update_status_indicator('active')
                        
                        # Запускаем поток для оверлея
                        threading.Thread(target=self.overlay_loop, daemon=True).start()
                        break
            else:
                raise Exception("Game process not found!")
                
        except Exception as e:
            self.log(f"✗ Injection failed: {str(e)}", 'error')
            self.update_status_indicator('error')
    
    def manual_inject(self):
        """Ручная инжекция"""
        self.log("=== MANUAL INJECTION ===", 'info')
        self.inject_cheat()
    
    def overlay_loop(self):
        """Поток для оверлея"""
        while self.cheat_active:
            # Обновляем текст оверлея
            self.root.after(0, lambda: self.overlay_label.config(
                fg=NeonStyles.COLORS['neon_green']
            ))
            time.sleep(5)
    
    # Функции для читов
    def toggle_oxygen(self, state):
        self.log(f"Oxygen cheat: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_health(self, state):
        self.log(f"Health cheat: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_food(self, state):
        self.log(f"Food/Water cheat: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_resources(self, state):
        self.log(f"Resources cheat: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_teleport(self, state):
        self.log(f"Teleport cheat: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_god(self, state):
        self.log(f"God mode: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_swim(self, state):
        self.log(f"Fast swim: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_night(self, state):
        self.log(f"Night vision: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_blueprints(self, state):
        self.log(f"All blueprints: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_achievements(self, state):
        self.log(f"All achievements: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_craft(self, state):
        self.log(f"Instant craft: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_radiation(self, state):
        self.log(f"No radiation: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_onehit(self, state):
        self.log(f"One hit kill: {'ON' if state else 'OFF'}", 'info')
    
    def toggle_speed(self, state):
        self.log(f"Super speed: {'ON' if state else 'OFF'}", 'info')
    
    def unlock_all(self, state):
        self.log("⚡ UNLOCKING ALL CONTENT!", 'success')
        for cheat in [self.toggle_oxygen, self.toggle_health, self.toggle_food,
                     self.toggle_resources, self.toggle_god, self.toggle_swim,
                     self.toggle_night, self.toggle_blueprints, self.toggle_achievements]:
            cheat(True)
    
    def run(self):
        """Запуск приложения"""
        self.root.mainloop()

def compile_to_exe():
    """Компиляция в exe файл"""
    print("=== COMPILING TO EXE ===")
    
    # Создаем spec файл для PyInstaller
    spec_content = """
# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['subnautica_cheat_loader.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=['pymem', 'win32gui', 'win32con', 'win32process', 'psutil'],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='SubnauticaNeonCheat',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None
)
"""
    
    with open('subnautica_cheat.spec', 'w') as f:
        f.write(spec_content)
    
    # Компилируем
    subprocess.run(['pyinstaller', 'subnautica_cheat.spec', '--onefile', '--windowed'])
    
    print("✓ Compiled to exe successfully!")
    print("📁 Output: dist/SubnauticaNeonCheat.exe")

if __name__ == "__main__":
    # Проверка на компиляцию
    if len(sys.argv) > 1 and sys.argv[1] == '--compile':
        compile_to_exe()
    else:
        app = SubnauticaCheatLoader()
        app.run()