"""
COLORBOT COM CLIQUE - Move o mouse fisicamente quando você clica
Funciona em QUALQUER jogo/programa
"""

import cv2
import numpy as np
import pyautogui
import mss
import time
import keyboard
import win32api
import win32con
import math
import tkinter as tk
from tkinter import ttk
import threading
from datetime import datetime
import json

pyautogui.FAILSAFE = False

class ColorBotGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("ColorBot Tester - Anti-Cheat Test")
        self.root.geometry("400x600")
        self.root.configure(bg='#1a1a2e')
        self.root.attributes('-topmost', True)
        
        # Variáveis
        self.enabled = False
        self.running = True
        self.snap_count = 0
        self.detection_count = 0
        
        # Configurações
        self.target_color = "red"
        self.search_radius = 200
        self.smooth_aim = False
        self.trigger_key = 'ctrl'  # Tecla que vai ativar
        
        # Cores em HSV
        self.colors = {
            'red': [
                ([0, 100, 100], [10, 255, 255]),
                ([160, 100, 100], [179, 255, 255])
            ],
            'green': [([40, 40, 40], [80, 255, 255])],
            'blue': [([100, 100, 100], [130, 255, 255])],
            'yellow': [([20, 100, 100], [30, 255, 255])],
            'purple': [([130, 50, 50], [160, 255, 255])],
            'orange': [([10, 100, 100], [20, 255, 255])],
            'pink': [([140, 50, 50], [170, 255, 255])],
            'cyan': [([80, 100, 100], [100, 255, 255])]
        }
        
        # Tela
        self.screen_width = pyautogui.size().width
        self.screen_height = pyautogui.size().height
        self.center_x = self.screen_width // 2
        self.center_y = self.screen_height // 2
        
        self.sct = mss.mss()
        
        # Logs
        self.logs = []
        
        self.setup_ui()
        self.setup_hotkeys()
        
    def setup_ui(self):
        """Configura interface gráfica"""
        
        # Título
        title = tk.Label(self.root, text="🎯 COLORBOT TESTER", 
                         font=("Arial", 16, "bold"), 
                         bg='#1a1a2e', fg='#ff6b6b')
        title.pack(pady=10)
        
        # Subtítulo
        subtitle = tk.Label(self.root, text="Ferramenta de Teste para Anti-Cheat", 
                           font=("Arial", 10), bg='#1a1a2e', fg='#888')
        subtitle.pack()
        
        # Frame de status
        status_frame = tk.Frame(self.root, bg='#1a1a2e')
        status_frame.pack(pady=15)
        
        self.status_label = tk.Label(status_frame, text="● INATIVO", 
                                     font=("Arial", 14, "bold"),
                                     bg='#1a1a2e', fg='#ff6b6b')
        self.status_label.pack()
        
        # Frame de configurações
        config_frame = tk.LabelFrame(self.root, text="Configurações", 
                                     bg='#16213e', fg='white', font=("Arial", 11))
        config_frame.pack(padx=20, pady=10, fill='x')
        
        # Cor alvo
        tk.Label(config_frame, text="Cor Alvo:", bg='#16213e', fg='white').grid(row=0, column=0, sticky='w', padx=10, pady=5)
        self.color_var = tk.StringVar(value='red')
        color_menu = ttk.Combobox(config_frame, textvariable=self.color_var, 
                                   values=['red', 'green', 'blue', 'yellow', 'purple', 'orange', 'pink', 'cyan'],
                                   state='readonly', width=15)
        color_menu.grid(row=0, column=1, padx=10, pady=5)
        color_menu.bind('<<ComboboxSelected>>', self.on_color_change)
        
        # Raio de busca
        tk.Label(config_frame, text="Raio de Busca (px):", bg='#16213e', fg='white').grid(row=1, column=0, sticky='w', padx=10, pady=5)
        self.radius_var = tk.IntVar(value=200)
        radius_scale = tk.Scale(config_frame, from_=50, to=400, orient='horizontal', 
                                variable=self.radius_var, bg='#16213e', fg='white',
                                length=150)
        radius_scale.grid(row=1, column=1, padx=10, pady=5)
        radius_scale.bind('<ButtonRelease-1>', self.on_radius_change)
        
        self.radius_label = tk.Label(config_frame, text="200px", bg='#16213e', fg='#ff6b6b')
        self.radius_label.grid(row=1, column=2, padx=5)
        
        # Tipo de movimento
        tk.Label(config_frame, text="Tipo de Movimento:", bg='#16213e', fg='white').grid(row=2, column=0, sticky='w', padx=10, pady=5)
        self.movement_var = tk.StringVar(value='instant')
        instant_radio = tk.Radiobutton(config_frame, text="Snap Instantâneo (MUITO SUSPEITO)", 
                                       variable=self.movement_var, value='instant',
                                       bg='#16213e', fg='#ff6b6b', selectcolor='#16213e')
        instant_radio.grid(row=2, column=1, columnspan=2, sticky='w', padx=10)
        
        smooth_radio = tk.Radiobutton(config_frame, text="Movimento Suave", 
                                      variable=self.movement_var, value='smooth',
                                      bg='#16213e', fg='white', selectcolor='#16213e')
        smooth_radio.grid(row=3, column=1, columnspan=2, sticky='w', padx=10)
        
        # Tecla de ativação
        tk.Label(config_frame, text="Tecla para Ativar:", bg='#16213e', fg='white').grid(row=4, column=0, sticky='w', padx=10, pady=5)
        self.key_var = tk.StringVar(value='ctrl')
        key_menu = ttk.Combobox(config_frame, textvariable=self.key_var,
                                 values=['ctrl', 'alt', 'shift', 'x', 'c', 'v'],
                                 state='readonly', width=10)
        key_menu.grid(row=4, column=1, sticky='w', padx=10, pady=5)
        key_menu.bind('<<ComboboxSelected>>', self.on_key_change)
        
        # Botão de ativação
        self.toggle_btn = tk.Button(self.root, text="🔴 ATIVAR MODO TESTE", 
                                    command=self.toggle_mode,
                                    bg='#ff6b6b', fg='white', font=("Arial", 12, "bold"),
                                    height=2)
        self.toggle_btn.pack(padx=20, pady=10, fill='x')
        
        # Frame de estatísticas
        stats_frame = tk.LabelFrame(self.root, text="Estatísticas", 
                                    bg='#16213e', fg='white')
        stats_frame.pack(padx=20, pady=10, fill='x')
        
        self.snap_label = tk.Label(stats_frame, text="Snaps Realizados: 0", 
                                   bg='#16213e', fg='#ff6b6b', font=("Arial", 12))
        self.snap_label.pack(pady=5)
        
        self.detection_label = tk.Label(stats_frame, text="Cores Detectadas: 0", 
                                       bg='#16213e', fg='#ff6b6b', font=("Arial", 12))
        self.detection_label.pack(pady=5)
        
        self.last_offset_label = tk.Label(stats_frame, text="Último Offset: -", 
                                         bg='#16213e', fg='white')
        self.last_offset_label.pack(pady=5)
        
        self.last_distance_label = tk.Label(stats_frame, text="Última Distância: -", 
                                           bg='#16213e', fg='white')
        self.last_distance_label.pack(pady=5)
        
        # Área de logs
        log_frame = tk.LabelFrame(self.root, text="Logs", bg='#16213e', fg='white')
        log_frame.pack(padx=20, pady=10, fill='both', expand=True)
        
        self.log_text = tk.Text(log_frame, height=12, bg='#0f0f1a', fg='#ccc', 
                                font=("Consolas", 9), wrap='word')
        self.log_text.pack(padx=5, pady=5, fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(self.log_text)
        scrollbar.pack(side='right', fill='y')
        self.log_text.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.log_text.yview)
        
        # Rodapé
        footer = tk.Label(self.root, text="Pressione a tecla configurada para ativar o aim", 
                          bg='#1a1a2e', fg='#666', font=("Arial", 9))
        footer.pack(pady=5)
        
    def add_log(self, message, color='white'):
        """Adiciona log com timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        
        self.log_text.insert('end', log_entry)
        self.log_text.see('end')
        
        # Limita logs
        if int(self.log_text.index('end-1c').split('.')[0]) > 200:
            self.log_text.delete('1.0', '50.0')
        
        self.logs.append(log_entry)
    
    def on_color_change(self, event):
        self.target_color = self.color_var.get()
        self.add_log(f"Cor alvo alterada para: {self.target_color}", '#ff6b6b')
    
    def on_radius_change(self, event):
        self.search_radius = self.radius_var.get()
        self.radius_label.config(text=f"{self.search_radius}px")
        self.add_log(f"Raio de busca alterado para: {self.search_radius}px", '#ff6b6b')
    
    def on_key_change(self, event):
        self.trigger_key = self.key_var.get()
        self.setup_hotkeys()
        self.add_log(f"Tecla de ativação alterada para: {self.trigger_key}", '#ff6b6b')
    
    def toggle_mode(self):
        self.enabled = not self.enabled
        if self.enabled:
            self.status_label.config(text="● ATIVO", fg='#4caf50')
            self.toggle_btn.config(text="🔴 DESATIVAR MODO TESTE", bg='#dc3545')
            self.add_log("⚠️ MODO DE TESTE ATIVADO!", '#ff6b6b')
            self.add_log("⚠️ Quando você pressionar a tecla, o mouse vai se mover!", '#ff6b6b')
            self.add_log("⚠️ SEU ANTI-CHEAT DEVE DETECTAR ESTE COMPORTAMENTO!", '#ff6b6b')
        else:
            self.status_label.config(text="● INATIVO", fg='#ff6b6b')
            self.toggle_btn.config(text="🟢 ATIVAR MODO TESTE", bg='#ff6b6b')
            self.add_log("Modo de teste desativado", '#888')
    
    def setup_hotkeys(self):
        """Configura hotkey para ativar o aim"""
        try:
            keyboard.remove_hotkey('ctrl')
            keyboard.remove_hotkey('alt')
            keyboard.remove_hotkey('shift')
            keyboard.remove_hotkey('x')
            keyboard.remove_hotkey('c')
            keyboard.remove_hotkey('v')
        except:
            pass
        
        # Registra nova hotkey
        keyboard.add_hotkey(self.trigger_key, self.on_trigger_press)
        self.add_log(f"Hotkey configurada: {self.trigger_key.upper()}", '#4caf50')
    
    def on_trigger_press(self):
        """Função chamada quando a tecla é pressionada"""
        if not self.enabled:
            return
        
        self.add_log(f"🎯 Tecla {self.trigger_key.upper()} pressionada! Procurando cor {self.target_color}...", '#ff6b6b')
        
        # Encontra a cor mais próxima
        target = self.find_closest_color()
        
        if target:
            self.detection_count += 1
            self.detection_label.config(text=f"Cores Detectadas: {self.detection_count}")
            
            target_x, target_y, area, distance = target
            self.add_log(f"✅ Cor encontrada! Posição: ({target_x}, {target_y}) | Distância: {distance}px", '#4caf50')
            
            # Move o mouse
            self.move_mouse_to_target(target_x, target_y, distance)
        else:
            self.add_log(f"❌ Nenhuma cor {self.target_color} encontrada no raio de {self.search_radius}px", '#ff6b6b')
    
    def find_closest_color(self):
        """Encontra a cor mais próxima do centro da tela"""
        
        # Captura área ao redor do centro
        left = self.center_x - self.search_radius
        top = self.center_y - self.search_radius
        width = self.search_radius * 2
        height = self.search_radius * 2
        
        left = max(0, left)
        top = max(0, top)
        width = min(width, self.screen_width - left)
        height = min(height, self.screen_height - top)
        
        monitor = {'left': left, 'top': top, 'width': width, 'height': height}
        screenshot = self.sct.grab(monitor)
        frame = np.array(screenshot)
        
        if frame is None or frame.size == 0:
            return None
        
        height, width = frame.shape[:2]
        center_frame_x = width // 2
        center_frame_y = height // 2
        
        # Converte para HSV
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # Cria máscara da cor alvo
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        color_ranges = self.colors.get(self.target_color, self.colors['red'])
        
        for lower, upper in color_ranges:
            lower = np.array(lower)
            upper = np.array(upper)
            mask = cv2.bitwise_or(mask, cv2.inRange(hsv, lower, upper))
        
        # Limpa ruído
        mask = cv2.medianBlur(mask, 5)
        
        # Encontra contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        best_target = None
        best_distance = float('inf')
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < 50:  # Ignora pixels soltos
                continue
            
            M = cv2.moments(contour)
            if M["m00"] != 0:
                cx = int(M["m10"] / M["m00"])
                cy = int(M["m01"] / M["m00"])
                
                distance = math.sqrt((cx - center_frame_x) ** 2 + (cy - center_frame_y) ** 2)
                
                if distance < best_distance:
                    best_distance = distance
                    best_target = (left + cx, top + cy, area, int(distance))
        
        return best_target
    
    def move_mouse_to_target(self, target_x, target_y, distance):
        """Move o mouse fisicamente para o alvo"""
        
        # Calcula offset
        offset_x = target_x - self.center_x
        offset_y = target_y - self.center_y
        
        self.snap_count += 1
        self.snap_label.config(text=f"Snaps Realizados: {self.snap_count}")
        self.last_offset_label.config(text=f"Último Offset: ({offset_x}, {offset_y})")
        self.last_distance_label.config(text=f"Última Distância: {distance}px")
        
        movement_type = self.movement_var.get()
        
        if movement_type == 'instant':
            # MOVIMENTO INSTANTÂNEO - Seu anti-cheat DEVE detectar!
            self.add_log(f"⚡ SNAP INSTANTÂNEO! Offset: ({offset_x}, {offset_y}) | Distância: {distance}px", '#ff6b6b')
            self.add_log(f"⚠️ Seu anti-cheat deve detectar este movimento em MENOS DE 1ms!", '#ff6b6b')
            
            # Move o mouse instantaneamente
            win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, offset_x, offset_y, 0, 0)
            
        else:
            # Movimento suave (ainda suspeito)
            self.add_log(f"🔄 Movimento suave para offset: ({offset_x}, {offset_y})", '#ffaa44')
            
            steps = max(5, min(20, int(abs(offset_x) / 10) + int(abs(offset_y) / 10)))
            for i in range(steps):
                step_x = offset_x * (i + 1) // steps - offset_x * i // steps
                step_y = offset_y * (i + 1) // steps - offset_y * i // steps
                win32api.mouse_event(win32con.MOUSEEVENTF_MOVE, step_x, step_y, 0, 0)
                time.sleep(0.002)
        
        # Alerta se muitos snaps
        if self.snap_count >= 5:
            self.add_log(f"⚠️⚠️ {self.snap_count} SNAPS REALIZADOS! Seu anti-cheat DEVE ter marcado como SUSPEITO! ⚠️⚠️", '#ff0000')
    
    def run(self):
        """Inicia o programa"""
        self.add_log("🎮 ColorBot Tester iniciado!", '#4caf50')
        self.add_log(f"📐 Tela: {self.screen_width}x{self.screen_height}", '#888')
        self.add_log(f"🎯 Centro: ({self.center_x}, {self.center_y})", '#888')
        self.add_log(f"🔴 Cor alvo: {self.target_color}", '#ff6b6b')
        self.add_log(f"⌨️ Tecla para ativar: {self.trigger_key.upper()}", '#ff6b6b')
        self.add_log("")
        self.add_log("⚠️ INSTRUÇÕES:", '#ffaa44')
        self.add_log("1. Clique em ATIVAR MODO TESTE", '#ffaa44')
        self.add_log("2. Abra seu jogo", '#ffaa44')
        self.add_log(f"3. Pressione a tecla {self.trigger_key.upper()} para ativar o aim", '#ffaa44')
        self.add_log("4. O mouse vai se mover automaticamente para a cor mais próxima!", '#ffaa44')
        self.add_log("")
        self.add_log("🔴 SEU ANTI-CHEAT DEVE DETECTAR ESTE COMPORTAMENTO!", '#ff6b6b')
        
        # Inicia o loop do tkinter
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()
    
    def on_close(self):
        """Fecha o programa"""
        self.running = False
        self.root.destroy()

if __name__ == "__main__":
    print("""
    ╔═══════════════════════════════════════════════════════╗
    ║     COLORBOT TESTER - Move o mouse fisicamente!       ║
    ║          Ferramenta de Teste para Anti-Cheat          ║
    ╚═══════════════════════════════════════════════════════╝
    """)
    
    print("Este programa VAI MOVER O SEU MOUSE quando você pressionar a tecla!")
    print("Certifique-se de que seu jogo está aberto e em foco.\n")
    
    gui = ColorBotGUI()
    gui.run()