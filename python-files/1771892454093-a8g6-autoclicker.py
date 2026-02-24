import tkinter as tk
from tkinter import ttk, messagebox
import pyautogui
import keyboard
import threading
import time
import random
import win32gui
import win32con
import win32api
import json
import os
import sys
import math
from collections import deque

# Configuration pour cacher la console
if sys.platform == 'win32':
    try:
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    except:
        pass

class RandomizationEngine:
    """Moteur de randomisation avancé"""
    
    def __init__(self):
        self.click_history = deque(maxlen=100)
        self.last_click_time = 0
        self.pattern_detection = []
        
    def gaussian_random(self, mean, std_dev):
        """Distribution gaussienne approximative sans numpy"""
        # Utilisation de la méthode de Box-Muller pour générer une distribution gaussienne
        u1 = random.random()
        u2 = random.random()
        z = math.sqrt(-2.0 * math.log(u1)) * math.cos(2.0 * math.pi * u2)
        return mean + z * std_dev
    
    def poisson_random(self, lambda_param):
        """Distribution de Poisson approximative"""
        # Algorithme simple pour Poisson
        L = math.exp(-lambda_param)
        k = 0
        p = 1.0
        while p > L:
            k += 1
            p *= random.random()
        return k - 1
    
    def beta_random(self, alpha, beta, scale):
        """Distribution Beta approximative"""
        # Approximation simple de la distribution Beta
        x = random.random()
        # Transformation simple
        if alpha > 1 and beta > 1:
            return math.pow(x, 1/alpha) * scale
        else:
            return x * scale
    
    def natural_click_pattern(self, base_cps, intensity=1.0):
        """
        Simule un pattern de clic humain avec :
        - Micro-pauses
        - Variations de rythme
        - Fatigue progressive
        - Bursts aléatoires
        """
        # Facteur de fatigue (les clics ralentissent avec le temps)
        fatigue = 1.0
        if len(self.click_history) > 20:
            recent_clicks = sum(1 for t in self.click_history 
                              if time.time() - t < 2)
            if recent_clicks > 15:
                fatigue = 0.85  # Ralentissement après clics rapides
        
        # Pattern de burst (rafales de clics)
        burst_chance = random.random()
        if burst_chance < 0.1:  # 10% de chance d'avoir un burst
            burst_multiplier = random.uniform(1.5, 2.5)
            return base_cps * burst_multiplier * fatigue
        
        # Pattern normal avec variation naturelle
        variation = random.uniform(0.7, 1.3)
        return base_cps * variation * fatigue
    
    def human_delay(self, base_delay, randomness):
        """
        Calcule un délai qui imite le comportement humain
        """
        # Délai de base avec différentes distributions
        delay_type = random.randint(0, 3)
        
        if delay_type == 0:
            # Distribution uniforme (aléatoire simple)
            variation = random.uniform(-randomness, randomness)
            return max(0.001, base_delay + variation)
            
        elif delay_type == 1:
            # Distribution gaussienne (plus naturelle)
            std_dev = base_delay * randomness
            return max(0.001, self.gaussian_random(base_delay, std_dev))
            
        elif delay_type == 2:
            # Distribution Beta (asymétrique)
            alpha = random.uniform(2, 5)
            beta = random.uniform(2, 5)
            return max(0.001, self.beta_random(alpha, beta, base_delay * 2))
            
        else:
            # Pattern naturel avec micro-pauses
            natural_cps = self.natural_click_pattern(1.0/base_delay, randomness)
            return max(0.001, 1.0 / natural_cps)
    
    def should_miss_click(self, miss_chance):
        """Simule des clics manqués (comme un humain)"""
        return random.random() < miss_chance
    
    def double_click_chance(self, double_chance):
        """Simule des doubles clics accidentels"""
        return random.random() < double_chance
    
    def record_click(self):
        """Enregistre un clic pour l'analyse de pattern"""
        self.click_history.append(time.time())

class AutoClickerSpectre:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AutoClicker Spectre v4.0")
        self.window.geometry("750x750")
        self.window.resizable(False, False)
        self.window.configure(bg='#0a0a0a')
        
        # Configuration
        self.config_file = "spectre_config.json"
        
        # Variables avancées
        self.is_clicking = False
        self.cps_target = 10
        self.randomize_percent = 20
        self.click_key = 'f'
        self.click_button = 'left'
        self.click_mode = 'continuous'
        self.mouse_position = 'current'
        self.fixed_x = 500
        self.fixed_y = 500
        self.target_window = None
        self.window_list = []
        self.click_count = 0
        self.start_time = 0
        self.hold_mode = False
        self.dark_mode = True
        
        # Paramètres de randomisation avancée
        self.randomization_engine = RandomizationEngine()
        self.randomization_mode = 'natural'  # 'simple', 'gaussian', 'natural', 'human'
        self.miss_chance = 0.0  # Chance de rater un clic (0-5%)
        self.double_click_chance = 0.0  # Chance de double clic accidentel (0-3%)
        self.burst_frequency = 0.1  # Fréquence des bursts (0-20%)
        self.fatigue_enabled = False  # Fatigue progressive
        self.micro_pauses = False  # Micro-pauses naturelles
        
        # Charger configuration
        self.load_config()
        
        self.setup_gui()
        self.setup_hotkey()
        self.refresh_windows()
        
        # Protection contre la fermeture accidentelle
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def setup_gui(self):
        # Container principal
        container = tk.Frame(self.window, bg='#0a0a0a')
        container.pack(fill='both', expand=True, padx=20, pady=15)
        
        # Header
        header = tk.Frame(container, bg='#0a0a0a')
        header.pack(fill='x', pady=(0, 15))
        
        title_frame = tk.Frame(header, bg='#0a0a0a')
        title_frame.pack(side='left')
        
        title = tk.Label(title_frame, text="👻 AutoClicker Spectre", 
                        font=('Segoe UI', 26, 'bold'), bg='#0a0a0a', fg='#7a00ff')
        title.pack()
        
        subtitle = tk.Label(title_frame, text="Randomisation avancée intégrée", 
                          font=('Segoe UI', 8, 'italic'), bg='#0a0a0a', fg='#4a4a4a')
        subtitle.pack()
        
        # Statistiques
        self.stats_frame = tk.Frame(header, bg='#1a1a1a', relief='solid', bd=1)
        self.stats_frame.pack(side='right')
        
        self.stats_label = tk.Label(self.stats_frame, text="Clics: 0 | 0.0/s", 
                                   font=('Segoe UI', 10, 'bold'), bg='#1a1a1a', fg='#7a00ff',
                                   padx=15, pady=5)
        self.stats_label.pack()
        
        # Notebook
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('TNotebook', background='#0a0a0a', borderwidth=0)
        style.configure('TNotebook.Tab', background='#1a1a1a', foreground='#7a00ff',
                       padding=[25, 10], font=('Segoe UI', 10, 'bold'))
        style.map('TNotebook.Tab', background=[('selected', '#7a00ff')],
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(container)
        self.notebook.pack(fill='both', expand=True)
        
        # Création des onglets
        self.create_tab_vitesse()
        self.create_tab_randomization()  # Nouvel onglet
        self.create_tab_position()
        self.create_tab_fenetre()
        self.create_tab_controles()
        self.create_tab_profils()
        
        # Status bar
        self.create_status_bar(container)
        
        # Démarrer la mise à jour des stats
        self.update_stats()
        
    def create_tab_vitesse(self):
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='⚡ Vitesse')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Mode de clic
        mode_frame = tk.LabelFrame(content, text="🎮 Mode de clic", 
                                  bg='#1a1a1a', fg='#7a00ff', 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', padx=15, pady=10)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        self.mode_var = tk.StringVar(value='continuous')
        
        modes = [
            ('♾️ Continu', 'continuous'),
            ('🔂 Simple', 'single'),
            ('🔁 Double', 'double')
        ]
        
        mode_container = tk.Frame(mode_frame, bg='#1a1a1a')
        mode_container.pack()
        
        for i, (text, value) in enumerate(modes):
            rb = tk.Radiobutton(mode_container, text=text, variable=self.mode_var,
                              value=value, command=self.update_mode,
                              bg='#2a2a2a', fg='white', selectcolor='#7a00ff',
                              activebackground='#7a00ff', 
                              font=('Segoe UI', 10, 'bold'),
                              indicatoron=False, width=15, pady=8,
                              relief='flat', bd=0, cursor='hand2')
            rb.pack(side='left', padx=5)
        
        # CPS
        cps_frame = tk.LabelFrame(content, text="⚡ CPS (Clicks par seconde)", 
                                 bg='#1a1a1a', fg='#7a00ff', 
                                 font=('Segoe UI', 10, 'bold'),
                                 relief='flat', padx=15, pady=10)
        cps_frame.pack(fill='x', pady=(0, 15))
        
        self.cps_label = tk.Label(cps_frame, text=f"{self.cps_target} CPS", 
                                 font=('Segoe UI', 24, 'bold'), bg='#1a1a1a', fg='#7a00ff')
        self.cps_label.pack(pady=(0, 10))
        
        slider_frame = tk.Frame(cps_frame, bg='#1a1a1a')
        slider_frame.pack(fill='x')
        
        tk.Label(slider_frame, text="1", font=('Segoe UI', 9), 
                bg='#1a1a1a', fg='#666').pack(side='left', padx=(0, 5))
        
        self.cps_slider = tk.Scale(slider_frame, from_=1, to=100, orient='horizontal',
                                  command=self.update_cps, bg='#1a1a1a', fg='white',
                                  troughcolor='#2a2a2a', activebackground='#7a00ff',
                                  highlightthickness=0, relief='flat',
                                  font=('Segoe UI', 9), width=15)
        self.cps_slider.set(self.cps_target)
        self.cps_slider.pack(side='left', fill='x', expand=True)
        
        tk.Label(slider_frame, text="100", font=('Segoe UI', 9), 
                bg='#1a1a1a', fg='#666').pack(side='left', padx=(5, 0))
        
    def create_tab_randomization(self):
        """Onglet dédié à la randomisation avancée"""
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='🎲 Randomisation')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Mode de randomisation
        mode_frame = tk.LabelFrame(content, text="🎯 Mode de randomisation", 
                                  bg='#1a1a1a', fg='#7a00ff', 
                                  font=('Segoe UI', 10, 'bold'),
                                  relief='flat', padx=15, pady=10)
        mode_frame.pack(fill='x', pady=(0, 15))
        
        self.rand_mode_var = tk.StringVar(value='natural')
        
        rand_modes = [
            ('📊 Simple', 'simple'),
            ('📈 Gaussienne', 'gaussian'),
            ('🌿 Naturel', 'natural'),
            ('👤 Humain', 'human')
        ]
        
        rand_container = tk.Frame(mode_frame, bg='#1a1a1a')
        rand_container.pack()
        
        for text, value in rand_modes:
            rb = tk.Radiobutton(rand_container, text=text, variable=self.rand_mode_var,
                              value=value, command=self.update_rand_mode,
                              bg='#2a2a2a', fg='white', selectcolor='#7a00ff',
                              activebackground='#7a00ff', 
                              font=('Segoe UI', 9, 'bold'),
                              indicatoron=False, width=12, pady=6,
                              relief='flat', bd=0, cursor='hand2')
            rb.pack(side='left', padx=3)
        
        # Intensité de randomisation
        intensity_frame = tk.LabelFrame(content, text="📊 Intensité", 
                                       bg='#1a1a1a', fg='#7a00ff', 
                                       font=('Segoe UI', 10, 'bold'),
                                       relief='flat', padx=15, pady=10)
        intensity_frame.pack(fill='x', pady=(0, 15))
        
        self.random_label = tk.Label(intensity_frame, text=f"±{self.randomize_percent}%", 
                                    font=('Segoe UI', 22, 'bold'), bg='#1a1a1a', fg='#ffaa00')
        self.random_label.pack(pady=(0, 10))
        
        slider_frame = tk.Frame(intensity_frame, bg='#1a1a1a')
        slider_frame.pack(fill='x')
        
        tk.Label(slider_frame, text="0%", font=('Segoe UI', 9), 
                bg='#1a1a1a', fg='#666').pack(side='left', padx=(0, 5))
        
        self.random_slider = tk.Scale(slider_frame, from_=0, to=100, orient='horizontal',
                                     command=self.update_random, bg='#1a1a1a', fg='white',
                                     troughcolor='#2a2a2a', activebackground='#ffaa00',
                                     highlightthickness=0, relief='flat',
                                     font=('Segoe UI', 9), width=15)
        self.random_slider.set(self.randomize_percent)
        self.random_slider.pack(side='left', fill='x', expand=True)
        
        tk.Label(slider_frame, text="100%", font=('Segoe UI', 9), 
                bg='#1a1a1a', fg='#666').pack(side='left', padx=(5, 0))
        
        # Options avancées
        advanced_frame = tk.LabelFrame(content, text="🔧 Options avancées", 
                                      bg='#1a1a1a', fg='#7a00ff', 
                                      font=('Segoe UI', 10, 'bold'),
                                      relief='flat', padx=15, pady=10)
        advanced_frame.pack(fill='x', pady=(0, 15))
        
        # Clics manqués
        miss_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        miss_frame.pack(fill='x', pady=5)
        
        tk.Label(miss_frame, text="Chance de clic manqué:", 
                font=('Segoe UI', 9), bg='#1a1a1a', fg='white').pack(side='left')
        
        self.miss_slider = tk.Scale(miss_frame, from_=0, to=5, orient='horizontal',
                                   command=self.update_miss_chance, bg='#1a1a1a', 
                                   fg='white', troughcolor='#2a2a2a', 
                                   activebackground='#ff4444',
                                   highlightthickness=0, relief='flat',
                                   length=150, width=10, resolution=0.1)
        self.miss_slider.set(self.miss_chance * 100)
        self.miss_slider.pack(side='right')
        
        self.miss_label = tk.Label(miss_frame, text=f"{self.miss_chance*100:.1f}%", 
                                  font=('Segoe UI', 9, 'bold'), bg='#1a1a1a', fg='#ff4444',
                                  width=6)
        self.miss_label.pack(side='right', padx=(10, 0))
        
        # Double clics accidentels
        double_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        double_frame.pack(fill='x', pady=5)
        
        tk.Label(double_frame, text="Chance de double clic:", 
                font=('Segoe UI', 9), bg='#1a1a1a', fg='white').pack(side='left')
        
        self.double_slider = tk.Scale(double_frame, from_=0, to=3, orient='horizontal',
                                     command=self.update_double_chance, bg='#1a1a1a', 
                                     fg='white', troughcolor='#2a2a2a', 
                                     activebackground='#ffaa00',
                                     highlightthickness=0, relief='flat',
                                     length=150, width=10, resolution=0.1)
        self.double_slider.set(self.double_click_chance * 100)
        self.double_slider.pack(side='right')
        
        self.double_label = tk.Label(double_frame, text=f"{self.double_click_chance*100:.1f}%", 
                                    font=('Segoe UI', 9, 'bold'), bg='#1a1a1a', fg='#ffaa00',
                                    width=6)
        self.double_label.pack(side='right', padx=(10, 0))
        
        # Fréquence des bursts
        burst_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        burst_frame.pack(fill='x', pady=5)
        
        tk.Label(burst_frame, text="Fréquence des bursts:", 
                font=('Segoe UI', 9), bg='#1a1a1a', fg='white').pack(side='left')
        
        self.burst_slider = tk.Scale(burst_frame, from_=0, to=20, orient='horizontal',
                                    command=self.update_burst_frequency, bg='#1a1a1a', 
                                    fg='white', troughcolor='#2a2a2a', 
                                    activebackground='#7a00ff',
                                    highlightthickness=0, relief='flat',
                                    length=150, width=10, resolution=1)
        self.burst_slider.set(self.burst_frequency * 100)
        self.burst_slider.pack(side='right')
        
        self.burst_label = tk.Label(burst_frame, text=f"{self.burst_frequency*100:.0f}%", 
                                   font=('Segoe UI', 9, 'bold'), bg='#1a1a1a', fg='#7a00ff',
                                   width=6)
        self.burst_label.pack(side='right', padx=(10, 0))
        
        # Checkboxes
        check_frame = tk.Frame(advanced_frame, bg='#1a1a1a')
        check_frame.pack(fill='x', pady=(10, 5))
        
        self.fatigue_var = tk.BooleanVar(value=self.fatigue_enabled)
        fatigue_check = tk.Checkbutton(check_frame, text="😮‍💨 Fatigue progressive", 
                                      variable=self.fatigue_var, 
                                      command=self.update_fatigue,
                                      bg='#1a1a1a', fg='white', selectcolor='#1a1a1a',
                                      activebackground='#1a1a1a', 
                                      font=('Segoe UI', 9))
        fatigue_check.pack(side='left', padx=(0, 20))
        
        self.pause_var = tk.BooleanVar(value=self.micro_pauses)
        pause_check = tk.Checkbutton(check_frame, text="⏸️ Micro-pauses", 
                                    variable=self.pause_var,
                                    command=self.update_micro_pauses,
                                    bg='#1a1a1a', fg='white', selectcolor='#1a1a1a',
                                    activebackground='#1a1a1a', 
                                    font=('Segoe UI', 9))
        pause_check.pack(side='left')
        
        # Visualisation en temps réel
        viz_frame = tk.LabelFrame(content, text="📈 Visualisation en temps réel", 
                                 bg='#1a1a1a', fg='#7a00ff', 
                                 font=('Segoe UI', 10, 'bold'),
                                 relief='flat', padx=15, pady=10)
        viz_frame.pack(fill='both', expand=True, pady=(15, 0))
        
        self.viz_label = tk.Label(viz_frame, 
                                 text="Les statistiques s'afficheront ici quand l'autoclicker tourne", 
                                 font=('Segoe UI', 9), bg='#2a2a2a', fg='#888',
                                 pady=30, relief='solid', bd=1)
        self.viz_label.pack(fill='x')
        
    def create_tab_position(self):
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='📍 Position')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Mode de position
        pos_frame = tk.LabelFrame(content, text="🎯 Mode de position", 
                                 bg='#1a1a1a', fg='#7a00ff', 
                                 font=('Segoe UI', 10, 'bold'),
                                 relief='flat', padx=15, pady=10)
        pos_frame.pack(fill='x', pady=(0, 15))
        
        self.pos_var = tk.StringVar(value='current')
        
        pos_container = tk.Frame(pos_frame, bg='#1a1a1a')
        pos_container.pack()
        
        rb1 = tk.Radiobutton(pos_container, text="🖱️ Position actuelle", 
                            variable=self.pos_var, value='current',
                            command=self.update_position_mode,
                            bg='#2a2a2a', fg='white', selectcolor='#7a00ff',
                            activebackground='#7a00ff', 
                            font=('Segoe UI', 10, 'bold'),
                            indicatoron=False, width=20, pady=8,
                            relief='flat', bd=0, cursor='hand2')
        rb1.pack(side='left', padx=5)
        
        rb2 = tk.Radiobutton(pos_container, text="📌 Position fixe", 
                            variable=self.pos_var, value='fixed',
                            command=self.update_position_mode,
                            bg='#2a2a2a', fg='white', selectcolor='#7a00ff',
                            activebackground='#7a00ff', 
                            font=('Segoe UI', 10, 'bold'),
                            indicatoron=False, width=20, pady=8,
                            relief='flat', bd=0, cursor='hand2')
        rb2.pack(side='left', padx=5)
        
        # Position fixe
        self.fixed_pos_frame = tk.Frame(pos_frame, bg='#1a1a1a')
        self.fixed_pos_frame.pack(fill='x', pady=(15, 0))
        
        tk.Label(self.fixed_pos_frame, text="X:", font=('Segoe UI', 10, 'bold'),
                bg='#1a1a1a', fg='white').pack(side='left', padx=(0, 5))
        
        self.x_entry = tk.Entry(self.fixed_pos_frame, width=8, font=('Segoe UI', 10),
                               bg='#2a2a2a', fg='white', relief='flat',
                               insertbackground='white')
        self.x_entry.insert(0, str(self.fixed_x))
        self.x_entry.pack(side='left', padx=(0, 15))
        
        tk.Label(self.fixed_pos_frame, text="Y:", font=('Segoe UI', 10, 'bold'),
                bg='#1a1a1a', fg='white').pack(side='left', padx=(0, 5))
        
        self.y_entry = tk.Entry(self.fixed_pos_frame, width=8, font=('Segoe UI', 10),
                               bg='#2a2a2a', fg='white', relief='flat',
                               insertbackground='white')
        self.y_entry.insert(0, str(self.fixed_y))
        self.y_entry.pack(side='left', padx=(0, 15))
        
        self.get_pos_btn = tk.Button(self.fixed_pos_frame, text="📌 Capturer", 
                                     command=self.capture_position,
                                     bg='#7a00ff', fg='white', 
                                     font=('Segoe UI', 9, 'bold'),
                                     relief='flat', padx=10, pady=3,
                                     activebackground='#5a00bf',
                                     cursor='hand2')
        self.get_pos_btn.pack(side='left')
        
        # Aperçu en temps réel
        preview_frame = tk.LabelFrame(content, text="👁️ Aperçu", 
                                     bg='#1a1a1a', fg='#7a00ff', 
                                     font=('Segoe UI', 10, 'bold'),
                                     relief='flat', padx=15, pady=10)
        preview_frame.pack(fill='both', expand=True, pady=(15, 0))
        
        self.preview_label = tk.Label(preview_frame, 
                                     text="Position actuelle: X: 0, Y: 0", 
                                     font=('Segoe UI', 12), bg='#2a2a2a', fg='#7a00ff',
                                     pady=20, relief='solid', bd=1)
        self.preview_label.pack(fill='x')
        
        # Démarrer la mise à jour de l'aperçu
        self.update_preview()
        
    def create_tab_fenetre(self):
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='🎯 Fenêtre')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=30, pady=30)
        
        # Titre
        tk.Label(content, text="🎯 Cliquer sur une fenêtre en arrière-plan", 
                font=('Segoe UI', 14, 'bold'), bg='#1a1a1a', fg='#7a00ff').pack(pady=(0, 20))
        
        tk.Label(content, text="Sélectionnez une fenêtre pour que l'autoclicker\nfonctionne même si elle n'est pas au premier plan", 
                font=('Segoe UI', 10), bg='#1a1a1a', fg='#888',
                justify='center').pack(pady=(0, 30))
        
        # Sélecteur
        selector_frame = tk.Frame(content, bg='#1a1a1a')
        selector_frame.pack(fill='x', pady=(0, 20))
        
        self.window_combo = ttk.Combobox(selector_frame, 
                                        font=('Segoe UI', 11),
                                        state='readonly')
        self.window_combo.pack(side='left', fill='x', expand=True, padx=(0, 10))
        self.window_combo.bind('<<ComboboxSelected>>', self.on_window_select)
        
        refresh_btn = tk.Button(selector_frame, text="🔄 Rafraîchir", 
                               command=self.refresh_windows,
                               bg='#2a2a2a', fg='white', 
                               font=('Segoe UI', 11, 'bold'),
                               relief='flat', padx=15, pady=10,
                               activebackground='#7a00ff',
                               cursor='hand2')
        refresh_btn.pack(side='left')
        
        # Info
        info_frame = tk.Frame(content, bg='#2a2a2a', relief='solid', bd=1)
        info_frame.pack(fill='x', pady=(20, 0))
        
        tk.Label(info_frame, text="💡 Conseil", 
                font=('Segoe UI', 10, 'bold'), bg='#2a2a2a', fg='#7a00ff').pack(pady=(10, 5))
        
        tk.Label(info_frame, text="Si 'Aucune' est sélectionné, l'autoclicker\nfonctionnera normalement sur la fenêtre active", 
                font=('Segoe UI', 9), bg='#2a2a2a', fg='#aaa',
                justify='center').pack(pady=(0, 10))
        
        # Option de maintien
        hold_frame = tk.Frame(content, bg='#1a1a1a')
        hold_frame.pack(fill='x', pady=(20, 0))
        
        self.hold_var = tk.BooleanVar(value=self.hold_mode)
        hold_check = tk.Checkbutton(hold_frame, text="🔒 Mode maintien (clic continu)", 
                                    variable=self.hold_var, command=self.update_hold_mode,
                                    bg='#1a1a1a', fg='white', selectcolor='#1a1a1a',
                                    activebackground='#1a1a1a', 
                                    font=('Segoe UI', 10))
        hold_check.pack()
        
    def create_tab_controles(self):
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='⌨️ Contrôles')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # === Bouton de souris ===
        mouse_frame = tk.LabelFrame(content, text="🖱️ Bouton de Souris", 
                                   bg='#1a1a1a', fg='#7a00ff', 
                                   font=('Segoe UI', 10, 'bold'),
                                   relief='flat', padx=15, pady=10)
        mouse_frame.pack(fill='x', pady=(0, 15))
        
        button_container = tk.Frame(mouse_frame, bg='#1a1a1a')
        button_container.pack()
        
        self.button_var = tk.StringVar(value=self.click_button)
        
        buttons = [
            ('◀ Clic Gauche', 'left'),
            ('Clic Droit ▶', 'right'),
            ('🖱️ Clic Milieu', 'middle')
        ]
        
        for text, value in buttons:
            rb = tk.Radiobutton(button_container, text=text, variable=self.button_var,
                              value=value, command=lambda v=value: self.set_button(v),
                              bg='#2a2a2a', fg='white', selectcolor='#7a00ff',
                              activebackground='#7a00ff', 
                              font=('Segoe UI', 10, 'bold'),
                              indicatoron=False, width=15, pady=10,
                              relief='flat', bd=0, cursor='hand2')
            rb.pack(side='left', padx=5)
        
        # === Touche d'activation ===
        key_frame = tk.LabelFrame(content, text="⌨️ Touche d'Activation", 
                                 bg='#1a1a1a', fg='#7a00ff', 
                                 font=('Segoe UI', 10, 'bold'),
                                 relief='flat', padx=15, pady=10)
        key_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(key_frame, text="Touche actuelle", 
                font=('Segoe UI', 9), bg='#1a1a1a', fg='#888').pack(pady=(0, 10))
        
        self.key_display = tk.Label(key_frame, text=self.click_key.upper(), 
                                    font=('Segoe UI', 28, 'bold'), 
                                    bg='#2a2a2a', fg='#7a00ff',
                                    width=5, relief='solid', bd=2, pady=10)
        self.key_display.pack(pady=(0, 15))
        
        change_btn = tk.Button(key_frame, text="🔧 Modifier la touche", 
                              command=self.change_key,
                              bg='#2a2a2a', fg='white', 
                              font=('Segoe UI', 10, 'bold'),
                              relief='flat', padx=25, pady=10,
                              activebackground='#7a00ff',
                              cursor='hand2')
        change_btn.pack()
        
        # === Raccourcis supplémentaires ===
        shortcuts_frame = tk.LabelFrame(content, text="🔑 Raccourcis", 
                                       bg='#1a1a1a', fg='#7a00ff', 
                                       font=('Segoe UI', 10, 'bold'),
                                       relief='flat', padx=15, pady=10)
        shortcuts_frame.pack(fill='x')
        
        shortcuts_text = f"""
        • [{self.click_key.upper()}] : Démarrer/Arrêter
        • [ESC] : Arrêt d'urgence
        • [Ctrl + Q] : Quitter l'application
        """
        
        tk.Label(shortcuts_frame, text=shortcuts_text, 
                font=('Segoe UI', 10), bg='#1a1a1a', fg='#aaa',
                justify='left').pack()
        
    def create_tab_profils(self):
        tab = tk.Frame(self.notebook, bg='#1a1a1a')
        self.notebook.add(tab, text='💾 Profils')
        content = tk.Frame(tab, bg='#1a1a1a')
        content.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Liste des profils
        list_frame = tk.Frame(content, bg='#1a1a1a')
        list_frame.pack(fill='both', expand=True)
        
        tk.Label(list_frame, text="💾 Gestion des profils", 
                font=('Segoe UI', 14, 'bold'), bg='#1a1a1a', fg='#7a00ff').pack(pady=(0, 20))
        
        # Treeview pour les profils
        columns = ('#1', '#2')
        self.profile_tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=5)
        self.profile_tree.heading('#1', text='Nom du profil')
        self.profile_tree.heading('#2', text='CPS')
        self.profile_tree.column('#1', width=200)
        self.profile_tree.column('#2', width=100)
        
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.profile_tree.yview)
        self.profile_tree.configure(yscrollcommand=scrollbar.set)
        
        self.profile_tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Boutons
        btn_frame = tk.Frame(content, bg='#1a1a1a')
        btn_frame.pack(fill='x', pady=(15, 0))
        
        tk.Button(btn_frame, text="💾 Sauvegarder", 
                 command=self.save_profile,
                 bg='#7a00ff', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', padx=20, pady=8,
                 activebackground='#5a00bf',
                 cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="📂 Charger", 
                 command=self.load_profile,
                 bg='#2a2a2a', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', padx=20, pady=8,
                 activebackground='#7a00ff',
                 cursor='hand2').pack(side='left', padx=5)
        
        tk.Button(btn_frame, text="🗑️ Supprimer", 
                 command=self.delete_profile,
                 bg='#ff4444', fg='white', 
                 font=('Segoe UI', 10, 'bold'),
                 relief='flat', padx=20, pady=8,
                 activebackground='#ff0000',
                 cursor='hand2').pack(side='left', padx=5)
        
        # Charger les profils existants
        self.load_profile_list()
        
    def create_status_bar(self, container):
        status_container = tk.Frame(container, bg='#0a0a0a')
        status_container.pack(fill='x', pady=(15, 0))
        
        # Barre de statut
        self.status_label = tk.Label(status_container, text="⏸ INACTIF", 
                                    font=('Segoe UI', 14, 'bold'), bg='#1a1a1a', fg='#4a4a4a',
                                    pady=12, relief='solid', bd=1)
        self.status_label.pack(fill='x')
        
        # Info et contrôles
        info_frame = tk.Frame(status_container, bg='#0a0a0a')
        info_frame.pack(fill='x', pady=(5, 0))
        
        self.info_label = tk.Label(info_frame, text=f"Appuyez sur [{self.click_key.upper()}] pour démarrer", 
                                  font=('Segoe UI', 9), bg='#0a0a0a', fg='#666')
        self.info_label.pack(side='left')
        
        # Bouton d'arrêt d'urgence
        emergency_btn = tk.Button(info_frame, text="🛑 ARRÊT D'URGENCE", 
                                 command=self.emergency_stop,
                                 bg='#ff4444', fg='white', 
                                 font=('Segoe UI', 9, 'bold'),
                                 relief='flat', padx=10, pady=2,
                                 activebackground='#ff0000',
                                 cursor='hand2')
        emergency_btn.pack(side='right')
        
    def update_stats(self):
        """Met à jour les statistiques en direct"""
        if self.is_clicking:
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                cps_actuel = self.click_count / elapsed
                self.stats_label.config(text=f"Clics: {self.click_count} | {cps_actuel:.1f}/s")
                
                # Mettre à jour la visualisation
                self.update_randomization_viz()
        
        self.window.after(100, self.update_stats)
        
    def update_randomization_viz(self):
        """Met à jour la visualisation de la randomisation"""
        if hasattr(self, 'viz_label') and self.is_clicking:
            # Créer un petit graphique ASCII simple
            if len(self.randomization_engine.click_history) > 5:
                recent = list(self.randomization_engine.click_history)[-20:]
                if len(recent) > 1:
                    intervals = []
                    for i in range(1, len(recent)):
                        intervals.append(recent[i] - recent[i-1])
                    
                    if intervals:
                        avg = sum(intervals) / len(intervals)
                        min_int = min(intervals)
                        max_int = max(intervals)
                        variation = ((max_int - min_int) / avg) * 100
                        
                        self.viz_label.config(
                            text=f"📊 Statistiques de randomisation en direct:\n"
                                 f"Intervalle moyen: {avg*1000:.1f}ms\n"
                                 f"Min: {min_int*1000:.1f}ms | Max: {max_int*1000:.1f}ms\n"
                                 f"Variation: {variation:.1f}%"
                        )
        
    def update_preview(self):
        """Met à jour l'aperçu de la position de la souris"""
        try:
            x, y = pyautogui.position()
            self.preview_label.config(text=f"Position actuelle: X: {x}, Y: {y}")
        except:
            pass
        self.window.after(100, self.update_preview)
        
    def update_position_mode(self):
        self.mouse_position = self.pos_var.get()
        if self.mouse_position == 'fixed':
            self.fixed_pos_frame.pack(fill='x', pady=(15, 0))
        else:
            self.fixed_pos_frame.pack_forget()
            
    def capture_position(self):
        try:
            x, y = pyautogui.position()
            self.x_entry.delete(0, tk.END)
            self.y_entry.delete(0, tk.END)
            self.x_entry.insert(0, str(x))
            self.y_entry.insert(0, str(y))
            self.fixed_x = x
            self.fixed_y = y
        except:
            pass
            
    def update_mode(self):
        self.click_mode = self.mode_var.get()
        
    def update_hold_mode(self):
        self.hold_mode = self.hold_var.get()
        
    # Méthodes pour la randomisation avancée
    def update_rand_mode(self):
        self.randomization_mode = self.rand_mode_var.get()
        
    def update_miss_chance(self, value):
        self.miss_chance = float(value) / 100.0
        self.miss_label.config(text=f"{self.miss_chance*100:.1f}%")
        
    def update_double_chance(self, value):
        self.double_click_chance = float(value) / 100.0
        self.double_label.config(text=f"{self.double_click_chance*100:.1f}%")
        
    def update_burst_frequency(self, value):
        self.burst_frequency = float(value) / 100.0
        self.burst_label.config(text=f"{self.burst_frequency*100:.0f}%")
        
    def update_fatigue(self):
        self.fatigue_enabled = self.fatigue_var.get()
        
    def update_micro_pauses(self):
        self.micro_pauses = self.pause_var.get()
        
    def refresh_windows(self):
        self.window_list = []
        
        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd) and win32gui.GetWindowText(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title and title != "AutoClicker Spectre v4.0":
                    self.window_list.append((title, hwnd))
        
        win32gui.EnumWindows(callback, None)
        
        window_titles = ["Aucune (mode normal)"] + [w[0] for w in self.window_list]
        self.window_combo['values'] = window_titles
        self.window_combo.current(0)
        
    def on_window_select(self, event):
        selection = self.window_combo.current()
        if selection == 0:
            self.target_window = None
        else:
            self.target_window = self.window_list[selection - 1][1]
        
    def update_cps(self, value):
        self.cps_target = int(float(value))
        self.cps_label.config(text=f"{self.cps_target} CPS")
        
    def update_random(self, value):
        self.randomize_percent = int(float(value))
        self.random_label.config(text=f"±{self.randomize_percent}%")
        
    def set_button(self, button):
        self.click_button = button
        
    def change_key(self):
        dialog = tk.Toplevel(self.window)
        dialog.title("Changer la touche")
        dialog.geometry("400x200")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="⌨️ Appuyez sur une touche", 
                font=('Segoe UI', 16, 'bold'), bg='#1a1a1a', fg='#7a00ff').pack(pady=50)
        
        tk.Label(dialog, text="(ESC pour annuler)", 
                font=('Segoe UI', 10), bg='#1a1a1a', fg='#666').pack()
        
        def on_key(event):
            if event.keysym.lower() == 'escape':
                dialog.destroy()
                return
                
            keyboard.unhook_all()
            self.click_key = event.keysym.lower()
            self.key_display.config(text=self.click_key.upper())
            self.info_label.config(text=f"Appuyez sur [{self.click_key.upper()}] pour démarrer")
            self.setup_hotkey()
            dialog.destroy()
        
        dialog.bind('<Key>', on_key)
        
    def setup_hotkey(self):
        keyboard.unhook_all()
        keyboard.on_press_key(self.click_key, lambda _: self.toggle_clicking())
        keyboard.on_press_key('esc', lambda _: self.emergency_stop())
        keyboard.add_hotkey('ctrl+q', self.on_closing)
        
    def emergency_stop(self):
        """Arrêt d'urgence"""
        if self.is_clicking:
            self.is_clicking = False
            self.status_label.config(text="⏸ ARRÊT URGENCE", fg='#ff4444')
            self.info_label.config(text="Arrêt d'urgence activé", fg='#ff4444')
            self.click_count = 0
            
    def toggle_clicking(self):
        self.is_clicking = not self.is_clicking
        if self.is_clicking:
            self.status_label.config(text="▶ ACTIF", fg='#7a00ff')
            self.info_label.config(text=f"Appuyez sur [{self.click_key.upper()}] pour arrêter", fg='#7a00ff')
            self.click_count = 0
            self.start_time = time.time()
            threading.Thread(target=self.click_loop, daemon=True).start()
        else:
            self.status_label.config(text="⏸ INACTIF", fg='#4a4a4a')
            self.info_label.config(text=f"Appuyez sur [{self.click_key.upper()}] pour démarrer", fg='#666')
            
    def perform_click(self):
        """Effectue un clic selon la configuration"""
        try:
            # Vérifier la position
            if self.mouse_position == 'fixed':
                try:
                    self.fixed_x = int(self.x_entry.get())
                    self.fixed_y = int(self.y_entry.get())
                except:
                    pass
                win32api.SetCursorPos((self.fixed_x, self.fixed_y))
            
            # Effectuer le clic
            if self.target_window:
                # Clic sur fenêtre en arrière-plan
                lparam = win32api.MAKELONG(self.fixed_x, self.fixed_y)
                
                if self.click_button == 'left':
                    win32api.SendMessage(self.target_window, win32con.WM_LBUTTONDOWN, 0, lparam)
                    time.sleep(0.001)
                    win32api.SendMessage(self.target_window, win32con.WM_LBUTTONUP, 0, lparam)
                elif self.click_button == 'right':
                    win32api.SendMessage(self.target_window, win32con.WM_RBUTTONDOWN, 0, lparam)
                    time.sleep(0.001)
                    win32api.SendMessage(self.target_window, win32con.WM_RBUTTONUP, 0, lparam)
                else:  # middle
                    win32api.SendMessage(self.target_window, win32con.WM_MBUTTONDOWN, 0, lparam)
                    time.sleep(0.001)
                    win32api.SendMessage(self.target_window, win32con.WM_MBUTTONUP, 0, lparam)
            else:
                # Clic normal
                if self.click_button == 'left':
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0)
                    time.sleep(0.001)
                    win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0)
                elif self.click_button == 'right':
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN, 0, 0)
                    time.sleep(0.001)
                    win32api.mouse_event(win32con.MOUSEEVENTF_RIGHTUP, 0, 0)
                else:  # middle
                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEDOWN, 0, 0)
                    time.sleep(0.001)
                    win32api.mouse_event(win32con.MOUSEEVENTF_MIDDLEUP, 0, 0)
            
            self.click_count += 1
            self.randomization_engine.record_click()
            
        except Exception as e:
            print(f"Erreur de clic: {e}")
            
    def calculate_delay(self):
        """Calcule le délai avec la randomisation avancée"""
        base_delay = 1.0 / self.cps_target
        
        # Utiliser le moteur de randomisation selon le mode
        if self.randomization_mode == 'simple':
            variation = base_delay * (self.randomize_percent / 100)
            random_offset = random.uniform(-variation, variation)
            delay = max(0.001, base_delay + random_offset)
            
        elif self.randomization_mode == 'gaussian':
            std_dev = base_delay * (self.randomize_percent / 100)
            delay = max(0.001, self.randomization_engine.gaussian_random(base_delay, std_dev))
            
        elif self.randomization_mode == 'natural':
            delay = self.randomization_engine.human_delay(base_delay, self.randomize_percent / 100)
            
        else:  # human
            delay = self.randomization_engine.human_delay(base_delay, self.randomize_percent / 100)
            
            # Ajouter des micro-pauses si activé
            if self.micro_pauses and random.random() < 0.05:  # 5% de chance
                delay += random.uniform(0.01, 0.05)  # Micro-pause de 10-50ms
                
        return max(0.001, delay)
            
    def click_loop(self):
        while self.is_clicking:
            # Vérifier les clics manqués
            if self.randomization_engine.should_miss_click(self.miss_chance):
                time.sleep(0.001)
                continue
                
            # Calculer le délai
            delay = self.calculate_delay()
            
            # Mode de clic
            if self.click_mode == 'continuous':
                self.perform_click()
                
                # Vérifier les doubles clics accidentels
                if self.randomization_engine.double_click_chance(self.double_click_chance):
                    time.sleep(0.02)  # Petit délai entre les doubles clics
                    self.perform_click()
                    
                if self.hold_mode:
                    time.sleep(delay)
                else:
                    time.sleep(delay)
                    
            elif self.click_mode == 'single':
                if not hasattr(self, '_single_clicked'):
                    self.perform_click()
                    self._single_clicked = True
                    time.sleep(0.1)
                    
            elif self.click_mode == 'double':
                self.perform_click()
                time.sleep(0.05)
                self.perform_click()
                time.sleep(delay)
            
    def save_profile(self):
        """Sauvegarde le profil actuel"""
        dialog = tk.Toplevel(self.window)
        dialog.title("Sauvegarder le profil")
        dialog.geometry("300x150")
        dialog.configure(bg='#1a1a1a')
        dialog.transient(self.window)
        dialog.grab_set()
        
        tk.Label(dialog, text="Nom du profil:", 
                font=('Segoe UI', 11), bg='#1a1a1a', fg='white').pack(pady=(20, 5))
        
        entry = tk.Entry(dialog, font=('Segoe UI', 11), bg='#2a2a2a', fg='white',
                        relief='flat', insertbackground='white')
        entry.pack(pady=(0, 15), padx=20, fill='x')
        
        def save():
            name = entry.get().strip()
            if name:
                try:
                    # Charger les profils existants
                    profiles = {}
                    if os.path.exists(self.config_file):
                        with open(self.config_file, 'r') as f:
                            profiles = json.load(f)
                    
                    # Sauvegarder le profil avec tous les paramètres
                    profiles[name] = {
                        'cps': self.cps_target,
                        'randomize': self.randomize_percent,
                        'button': self.click_button,
                        'mode': self.click_mode,
                        'position_mode': self.mouse_position,
                        'fixed_x': self.fixed_x,
                        'fixed_y': self.fixed_y,
                        'hold_mode': self.hold_mode,
                        'randomization_mode': self.randomization_mode,
                        'miss_chance': self.miss_chance,
                        'double_click_chance': self.double_click_chance,
                        'burst_frequency': self.burst_frequency,
                        'fatigue_enabled': self.fatigue_enabled,
                        'micro_pauses': self.micro_pauses
                    }
                    
                    with open(self.config_file, 'w') as f:
                        json.dump(profiles, f, indent=4)
                    
                    self.load_profile_list()
                    dialog.destroy()
                    messagebox.showinfo("Succès", f"Profil '{name}' sauvegardé!")
                    
                except Exception as e:
                    messagebox.showerror("Erreur", f"Impossible de sauvegarder: {e}")
            else:
                messagebox.showwarning("Attention", "Veuillez entrer un nom de profil")
        
        tk.Button(dialog, text="Sauvegarder", command=save,
                 bg='#7a00ff', fg='white', font=('Segoe UI', 10, 'bold'),
                 relief='flat', padx=20, pady=8, cursor='hand2').pack()
        
    def load_profile(self):
        """Charge le profil sélectionné"""
        selection = self.profile_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un profil")
            return
        
        profile_name = self.profile_tree.item(selection[0])['values'][0]
        
        try:
            with open(self.config_file, 'r') as f:
                profiles = json.load(f)
            
            if profile_name in profiles:
                profile = profiles[profile_name]
                
                # Appliquer les paramètres de base
                self.cps_target = profile['cps']
                self.randomize_percent = profile['randomize']
                self.click_button = profile['button']
                self.click_mode = profile['mode']
                self.mouse_position = profile['position_mode']
                self.fixed_x = profile['fixed_x']
                self.fixed_y = profile['fixed_y']
                self.hold_mode = profile.get('hold_mode', False)
                
                # Appliquer les nouveaux paramètres de randomisation
                self.randomization_mode = profile.get('randomization_mode', 'natural')
                self.miss_chance = profile.get('miss_chance', 0.0)
                self.double_click_chance = profile.get('double_click_chance', 0.0)
                self.burst_frequency = profile.get('burst_frequency', 0.1)
                self.fatigue_enabled = profile.get('fatigue_enabled', False)
                self.micro_pauses = profile.get('micro_pauses', False)
                
                # Mettre à jour l'interface
                self.cps_slider.set(self.cps_target)
                self.cps_label.config(text=f"{self.cps_target} CPS")
                self.random_slider.set(self.randomize_percent)
                self.random_label.config(text=f"±{self.randomize_percent}%")
                self.button_var.set(self.click_button)
                self.mode_var.set(self.click_mode)
                self.pos_var.set(self.mouse_position)
                self.x_entry.delete(0, tk.END)
                self.x_entry.insert(0, str(self.fixed_x))
                self.y_entry.delete(0, tk.END)
                self.y_entry.insert(0, str(self.fixed_y))
                self.hold_var.set(self.hold_mode)
                
                # Mettre à jour les contrôles de randomisation
                self.rand_mode_var.set(self.randomization_mode)
                self.miss_slider.set(self.miss_chance * 100)
                self.miss_label.config(text=f"{self.miss_chance*100:.1f}%")
                self.double_slider.set(self.double_click_chance * 100)
                self.double_label.config(text=f"{self.double_click_chance*100:.1f}%")
                self.burst_slider.set(self.burst_frequency * 100)
                self.burst_label.config(text=f"{self.burst_frequency*100:.0f}%")
                self.fatigue_var.set(self.fatigue_enabled)
                self.pause_var.set(self.micro_pauses)
                
                self.update_position_mode()
                
                messagebox.showinfo("Succès", f"Profil '{profile_name}' chargé!")
                
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le profil: {e}")
            
    def delete_profile(self):
        """Supprime le profil sélectionné"""
        selection = self.profile_tree.selection()
        if not selection:
            messagebox.showwarning("Attention", "Veuillez sélectionner un profil")
            return
        
        profile_name = self.profile_tree.item(selection[0])['values'][0]
        
        if messagebox.askyesno("Confirmation", f"Supprimer le profil '{profile_name}'?"):
            try:
                with open(self.config_file, 'r') as f:
                    profiles = json.load(f)
                
                if profile_name in profiles:
                    del profiles[profile_name]
                    
                    with open(self.config_file, 'w') as f:
                        json.dump(profiles, f, indent=4)
                    
                    self.load_profile_list()
                    messagebox.showinfo("Succès", f"Profil '{profile_name}' supprimé!")
                    
            except Exception as e:
                messagebox.showerror("Erreur", f"Impossible de supprimer le profil: {e}")
                
    def load_profile_list(self):
        """Charge la liste des profils"""
        for item in self.profile_tree.get_children():
            self.profile_tree.delete(item)
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    profiles = json.load(f)
                
                for name, config in profiles.items():
                    if name != 'last_profile':
                        self.profile_tree.insert('', 'end', values=(name, f"{config['cps']} CPS"))
                    
        except:
            pass
            
    def load_config(self):
        """Charge la configuration sauvegardée"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    
                # Charger le dernier profil utilisé
                last_profile = config.get('last_profile')
                if last_profile and last_profile in config:
                    profile = config[last_profile]
                    self.cps_target = profile.get('cps', 10)
                    self.randomize_percent = profile.get('randomize', 20)
                    self.click_button = profile.get('button', 'left')
                    self.click_mode = profile.get('mode', 'continuous')
                    self.mouse_position = profile.get('position_mode', 'current')
                    self.fixed_x = profile.get('fixed_x', 500)
                    self.fixed_y = profile.get('fixed_y', 500)
                    self.hold_mode = profile.get('hold_mode', False)
                    
                    # Charger les paramètres de randomisation
                    self.randomization_mode = profile.get('randomization_mode', 'natural')
                    self.miss_chance = profile.get('miss_chance', 0.0)
                    self.double_click_chance = profile.get('double_click_chance', 0.0)
                    self.burst_frequency = profile.get('burst_frequency', 0.1)
                    self.fatigue_enabled = profile.get('fatigue_enabled', False)
                    self.micro_pauses = profile.get('micro_pauses', False)
                    
        except:
            pass
            
    def save_config(self):
        """Sauvegarde la configuration actuelle"""
        try:
            config = {}
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
            
            # Sauvegarder comme dernier profil
            config['last_profile'] = 'default'
            config['default'] = {
                'cps': self.cps_target,
                'randomize': self.randomize_percent,
                'button': self.click_button,
                'mode': self.click_mode,
                'position_mode': self.mouse_position,
                'fixed_x': self.fixed_x,
                'fixed_y': self.fixed_y,
                'hold_mode': self.hold_mode,
                'randomization_mode': self.randomization_mode,
                'miss_chance': self.miss_chance,
                'double_click_chance': self.double_click_chance,
                'burst_frequency': self.burst_frequency,
                'fatigue_enabled': self.fatigue_enabled,
                'micro_pauses': self.micro_pauses
            }
            
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
                
        except:
            pass
            
    def on_closing(self):
        """Fermeture propre de l'application"""
        if self.is_clicking:
            self.is_clicking = False
            time.sleep(0.1)
        
        self.save_config()
        keyboard.unhook_all()
        self.window.destroy()
        
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = AutoClickerSpectre()
    app.run()