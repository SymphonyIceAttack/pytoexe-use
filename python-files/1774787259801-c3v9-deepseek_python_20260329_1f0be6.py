import cv2
import numpy as np
import pyautogui
import mss
import keyboard
import win32api
import win32con
import threading
import tkinter as tk
from tkinter import ttk
from math import sqrt, dist
from time import sleep, time
import colorsys

class OfflineAimbot:
    def __init__(self):
        # Configurações de tela
        self.sct = mss.mss()
        self.monitor = {"top": 0, "left": 0, "width": 1920, "height": 1080}
        
        # Configurações do aimbot
        self.aimbot_active = False
        self.esp_active = False
        self.aim_mode = "hybrid"  # head, chest, hybrid
        self.aim_fov = 250  # Campo de visão em pixels
        self.aim_smooth = 3  # Suavidade (1=instantâneo, 20=muito suave)
        self.lock_delay = 0.05  # Delay entre movimentos (segundos)
        self.target_priority = "head_first"  # head_first ou chest_first
        
        # Configurações de cor (ajustáveis)
        self.color_ranges = {
            "enemy_red": [([0, 50, 50], [10, 255, 255]), ([160, 50, 50], [179, 255, 255])],
            "enemy_blue": [([100, 50, 50], [130, 255, 255])],
            "enemy_green": [([40, 50, 50], [80, 255, 255])]
        }
        self.active_color = "enemy_red"
        
        # Dados de performance
        self.shots_fired = 0
        self.hits = 0
        self.last_target = None
        
        # Inicia thread do aimbot
        self.running = True
        self.aimbot_thread = threading.Thread(target=self.aimbot_loop, daemon=True)
        
    def setup_panel(self):
        """Cria o painel flutuante de controle"""
        self.panel = tk.Tk()
        self.panel.title("🎯 OFFLINE AIMBOT PRO")
        self.panel.geometry("350x600")
        self.panel.attributes('-topmost', True)
        self.panel.configure(bg='#1e1e1e')
        
        # Estilo
        style = ttk.Style()
        style.theme_use('clam')
        
        # Título
        title = tk.Label(self.panel, text="AIMBOT & ESP SYSTEM", 
                        font=("Arial", 16, "bold"), bg='#1e1e1e', fg='#00ff00')
        title.pack(pady=10)
        
        warning = tk.Label(self.panel, text="⚠️ APENAS PARA JOGOS OFFLINE/SINGLE-PLAYER ⚠️", 
                          font=("Arial", 9), bg='#1e1e1e', fg='#ff6600')
        warning.pack()
        
        separator = ttk.Separator(self.panel, orient='horizontal')
        separator.pack(fill='x', pady=10)
        
        # Frame de controles principais
        control_frame = tk.Frame(self.panel, bg='#1e1e1e')
        control_frame.pack(pady=10)
        
        # Botão Aimbot
        self.btn_aim = tk.Button(control_frame, text="🔴 AIMBOT: DESLIGADO", 
                                 bg='#333333', fg='white', font=("Arial", 11, "bold"),
                                 width=25, height=2, command=self.toggle_aimbot)
        self.btn_aim.pack(pady=5)
        
        # Botão ESP
        self.btn_esp = tk.Button(control_frame, text="👁️ ESP: DESLIGADO", 
                                bg='#333333', fg='white', font=("Arial", 11, "bold"),
                                width=25, height=2, command=self.toggle_esp)
        self.btn_esp.pack(pady=5)
        
        # Modo de mira
        mode_frame = tk.LabelFrame(self.panel, text="🎯 MODO DE MIRA", 
                                   bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        mode_frame.pack(pady=10, padx=20, fill='x')
        
        self.mode_var = tk.StringVar(value="hybrid")
        
        tk.Radiobutton(mode_frame, text="Só Cabeça", variable=self.mode_var, 
                      value="head", bg='#1e1e1e', fg='white', selectcolor='#1e1e1e',
                      command=self.change_mode).pack(anchor='w', padx=10, pady=2)
        
        tk.Radiobutton(mode_frame, text="Só Peito", variable=self.mode_var, 
                      value="chest", bg='#1e1e1e', fg='white', selectcolor='#1e1e1e',
                      command=self.change_mode).pack(anchor='w', padx=10, pady=2)
        
        tk.Radiobutton(mode_frame, text="Híbrido (1 peito + resto cabeça)", 
                      variable=self.mode_var, value="hybrid", 
                      bg='#1e1e1e', fg='white', selectcolor='#1e1e1e',
                      command=self.change_mode).pack(anchor='w', padx=10, pady=2)
        
        # Prioridade
        priority_frame = tk.LabelFrame(self.panel, text="📊 PRIORIDADE", 
                                       bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        priority_frame.pack(pady=10, padx=20, fill='x')
        
        self.priority_var = tk.StringVar(value="head_first")
        
        tk.Radiobutton(priority_frame, text="Cabeça primeiro", variable=self.priority_var, 
                      value="head_first", bg='#1e1e1e', fg='white',
                      command=self.change_priority).pack(anchor='w', padx=10, pady=2)
        
        tk.Radiobutton(priority_frame, text="Peito primeiro", variable=self.priority_var, 
                      value="chest_first", bg='#1e1e1e', fg='white',
                      command=self.change_priority).pack(anchor='w', padx=10, pady=2)
        
        # Sliders
        fov_frame = tk.LabelFrame(self.panel, text="🎯 CAMPO DE VISÃO (FOV)", 
                                  bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        fov_frame.pack(pady=10, padx=20, fill='x')
        
        self.fov_var = tk.IntVar(value=250)
        fov_slider = tk.Scale(fov_frame, from_=50, to=500, orient='horizontal',
                             variable=self.fov_var, bg='#1e1e1e', fg='white',
                             length=250, command=self.update_fov)
        fov_slider.pack(pady=5)
        self.fov_label = tk.Label(fov_frame, text=f"FOV: {self.fov_var.get()}px", 
                                  bg='#1e1e1e', fg='#00ff00')
        self.fov_label.pack()
        
        smooth_frame = tk.LabelFrame(self.panel, text="✨ SUAVIDADE", 
                                     bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        smooth_frame.pack(pady=10, padx=20, fill='x')
        
        self.smooth_var = tk.IntVar(value=3)
        smooth_slider = tk.Scale(smooth_frame, from_=1, to=20, orient='horizontal',
                                variable=self.smooth_var, bg='#1e1e1e', fg='white',
                                length=250, command=self.update_smooth)
        smooth_slider.pack(pady=5)
        self.smooth_label = tk.Label(smooth_frame, text=f"Suavidade: {self.smooth_var.get()}", 
                                     bg='#1e1e1e', fg='#00ff00')
        self.smooth_label.pack()
        
        # Cor de detecção
        color_frame = tk.LabelFrame(self.panel, text="🎨 COR DOS INIMIGOS", 
                                    bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        color_frame.pack(pady=10, padx=20, fill='x')
        
        tk.Button(color_frame, text="Vermelho", bg='#ff0000', fg='white',
                 command=lambda: self.set_color("enemy_red")).pack(side='left', padx=5, pady=5, expand=True)
        tk.Button(color_frame, text="Azul", bg='#0000ff', fg='white',
                 command=lambda: self.set_color("enemy_blue")).pack(side='left', padx=5, pady=5, expand=True)
        tk.Button(color_frame, text="Verde", bg='#00ff00', fg='black',
                 command=lambda: self.set_color("enemy_green")).pack(side='left', padx=5, pady=5, expand=True)
        
        # Estatísticas
        stats_frame = tk.LabelFrame(self.panel, text="📊 ESTATÍSTICAS", 
                                    bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        stats_frame.pack(pady=10, padx=20, fill='x')
        
        self.stats_label = tk.Label(stats_frame, text="Aguardando...", 
                                    bg='#1e1e1e', fg='#00ff00', font=("Arial", 9))
        self.stats_label.pack(pady=5)
        
        # Hotkeys
        hotkey_frame = tk.LabelFrame(self.panel, text="⌨️ HOTKEYS", 
                                     bg='#1e1e1e', fg='white', font=("Arial", 10, "bold"))
        hotkey_frame.pack(pady=10, padx=20, fill='x')
        
        hotkeys = [
            "F1 - Ligar/Desligar Aimbot",
            "F2 - Ligar/Desligar ESP",
            "F3 - Alternar Modo de Mira",
            "F4 - Alternar Prioridade",
            "F5 - Atirar (modo semi-auto)"
        ]
        
        for hk in hotkeys:
            tk.Label(hotkey_frame, text=hk, bg='#1e1e1e', fg='#aaaaaa', 
                    font=("Arial", 8)).pack(anchor='w', padx=10)
        
        # Status
        self.status_label = tk.Label(self.panel, text="✅ PRONTO", 
                                     bg='#1e1e1e', fg='#00ff00', font=("Arial", 10, "bold"))
        self.status_label.pack(pady=10)
        
    def detect_enemies(self, frame):
        """Detecta inimigos no frame usando faixas de cor"""
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
        
        # Aplica as faixas de cor selecionada
        ranges = self.color_ranges.get(self.active_color, [])
        for lower, upper in ranges:
            lower = np.array(lower)
            upper = np.array(upper)
            mask_temp = cv2.inRange(hsv, lower, upper)
            mask = cv2.bitwise_or(mask, mask_temp)
        
        # Limpa a máscara
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        
        # Encontra contornos
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        enemies = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > 150:  # Filtra ruído pequeno
                x, y, w, h = cv2.boundingRect(contour)
                
                # Calcula pontos da cabeça e peito
                head_x = x + w // 2
                head_y = y + h // 4
                chest_x = x + w // 2
                chest_y = y + h // 2
                
                enemies.append({
                    'bbox': (x, y, w, h),
                    'head': (head_x, head_y),
                    'chest': (chest_x, chest_y),
                    'area': area,
                    'distance': sqrt(w**2 + h**2)  # Distância aproximada
                })
        
        return enemies
    
    def get_target_point(self, enemy):
        """Retorna o ponto de mira baseado no modo atual"""
        if self.aim_mode == "head":
            return enemy['head']
        elif self.aim_mode == "chest":
            return enemy['chest']
        else:  # hybrid - 1 peito, resto cabeça
            # Simula "1 peito e o resto de capa" - 20% chance de mirar no peito
            import random
            if random.random() < 0.2:  # 20% das vezes mira no peito
                return enemy['chest']
            else:
                return enemy['head']
    
    def get_closest_enemy(self, enemies, center_x, center_y):
        """Encontra o inimigo mais próximo do centro da mira"""
        if not enemies:
            return None
        
        closest = None
        min_distance = self.aim_fov
        
        for enemy in enemies:
            target_point = self.get_target_point(enemy)
            distance = sqrt((target_point[0] - center_x)**2 + (target_point[1] - center_y)**2)
            
            if distance < min_distance:
                min_distance = distance
                closest = enemy
        
        return closest
    
    def move_mouse_smooth(self, target_x, target_y):
        """Move o mouse suavemente até o alvo"""
        current_x, current_y = pyautogui.position()
        
        dx = target_x - current_x
        dy = target_y - current_y
        
        # Não move se estiver muito perto
        if abs(dx) < 5 and abs(dy) < 5:
            return
        
        steps = max(1, self.aim_smooth)
        for i in range(1, steps + 1):
            step_x = current_x + (dx * i / steps)
            step_y = current_y + (dy * i / steps)
            win32api.SetCursorPos((int(step_x), int(step_y)))
            sleep(0.001)
    
    def draw_esp(self, frame, enemies, center_x, center_y):
        """Desenha as linhas e informações dos inimigos na tela"""
        esp_frame = frame.copy()
        
        for enemy in enemies:
            x, y, w, h = enemy['bbox']
            head_x, head_y = enemy['head']
            chest_x, chest_y = enemy['chest']
            distance = enemy['distance']
            
            # Linha do centro até o inimigo
            cv2.line(esp_frame, (center_x, center_y), (head_x, head_y), (0, 255, 0), 2)
            
            # Retângulo ao redor do inimigo
            cv2.rectangle(esp_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Cabeça (círculo)
            cv2.circle(esp_frame, (head_x, head_y), 5, (0, 0, 255), -1)
            
            # Peito (quadrado)
            cv2.rectangle(esp_frame, (chest_x - 5, chest_y - 5), (chest_x + 5, chest_y + 5), (255, 0, 0), -1)
            
            # Distância
            dist_text = f"{int(distance)}px"
            cv2.putText(esp_frame, dist_text, (x, y - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
            
            # Barra de vida (simulada)
            health_percent = 1.0  # 100%
            health_width = int(w * health_percent)
            cv2.rectangle(esp_frame, (x, y + h + 5), (x + health_width, y + h + 10), (0, 255, 0), -1)
            cv2.rectangle(esp_frame, (x, y + h + 5), (x + w, y + h + 10), (0, 0, 255), 1)
        
        # Desenha o campo de visão (FOV)
        cv2.circle(esp_frame, (center_x, center_y), self.aim_fov, (255, 255, 0), 1)
        
        # Desenha a mira central
        cv2.line(esp_frame, (center_x - 20, center_y), (center_x - 5, center_y), (255, 255, 255), 2)
        cv2.line(esp_frame, (center_x + 20, center_y), (center_x + 5, center_y), (255, 255, 255), 2)
        cv2.line(esp_frame, (center_x, center_y - 20), (center_x, center_y - 5), (255, 255, 255), 2)
        cv2.line(esp_frame, (center_x, center_y + 20), (center_x, center_y + 5), (255, 255, 255), 2)
        
        return esp_frame
    
    def aimbot_loop(self):
        """Loop principal do aimbot"""
        while self.running:
            if self.aimbot_active:
                # Captura a tela
                img = self.sct.grab(self.monitor)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                
                # Detecta inimigos
                enemies = self.detect_enemies(frame)
                
                # Centro da tela
                center_x = self.monitor["width"] // 2
                center_y = self.monitor["height"] // 2
                
                # ESP (se ativado)
                if self.esp_active and enemies:
                    esp_frame = self.draw_esp(frame, enemies, center_x, center_y)
                    # Redimensiona para visualização
                    esp_frame_small = cv2.resize(esp_frame, (640, 360))
                    cv2.imshow("ESP - OFFLINE MODE", esp_frame_small)
                    cv2.waitKey(1)
                elif self.esp_active:
                    # Mostra apenas a mira
                    frame_with_crosshair = frame.copy()
                    cv2.line(frame_with_crosshair, (center_x - 20, center_y), (center_x - 5, center_y), (255, 255, 255), 2)
                    cv2.line(frame_with_crosshair, (center_x + 20, center_y), (center_x + 5, center_y), (255, 255, 255), 2)
                    cv2.line(frame_with_crosshair, (center_x, center_y - 20), (center_x, center_y - 5), (255, 255, 255), 2)
                    cv2.line(frame_with_crosshair, (center_x, center_y + 20), (center_x, center_y + 5), (255, 255, 255), 2)
                    frame_small = cv2.resize(frame_with_crosshair, (640, 360))
                    cv2.imshow("ESP - OFFLINE MODE", frame_small)
                    cv2.waitKey(1)
                
                # Aimbot
                if enemies:
                    closest = self.get_closest_enemy(enemies, center_x, center_y)
                    if closest:
                        target_point = self.get_target_point(closest)
                        self.move_mouse_smooth(target_point[0], target_point[1])
                        self.last_target = closest
                        self.update_stats(True)
                    else:
                        self.update_stats(False)
                else:
                    self.update_stats(False)
            
            sleep(self.lock_delay)
    
    def toggle_aimbot(self):
        """Liga/desliga o aimbot"""
        self.aimbot_active = not self.aimbot_active
        status = "LIGADO 🟢" if self.aimbot_active else "DESLIGADO 🔴"
        color = "#00ff00" if self.aimbot_active else "#333333"
        self.btn_aim.config(text=f"🎯 AIMBOT: {status}", bg=color)
        self.status_label.config(text=f"Aimbot {status}", fg='#00ff00' if self.aimbot_active else '#ff0000')
        self.update_panel_status()
    
    def toggle_esp(self):
        """Liga/desliga o ESP"""
        self.esp_active = not self.esp_active
        status = "LIGADO 🟢" if self.esp_active else "DESLIGADO 🔴"
        color = "#00ff00" if self.esp_active else "#333333"
        self.btn_esp.config(text=f"👁️ ESP: {status}", bg=color)
        
        if not self.esp_active:
            cv2.destroyWindow("ESP - OFFLINE MODE")
    
    def change_mode(self):
        """Muda o modo de mira"""
        self.aim_mode = self.mode_var.get()
        mode_names = {"head": "Cabeça", "chest": "Peito", "hybrid": "Híbrido (1 peito)"}
        self.status_label.config(text=f"Modo: {mode_names[self.aim_mode]}", fg='#00ff00')
    
    def change_priority(self):
        """Muda a prioridade de mira"""
        self.target_priority = self.priority_var.get()
    
    def update_fov(self, val):
        """Atualiza o campo de visão"""
        self.aim_fov = int(val)
        self.fov_label.config(text=f"FOV: {self.aim_fov}px")
    
    def update_smooth(self, val):
        """Atualiza a suavidade"""
        self.aim_smooth = int(val)
        self.smooth_label.config(text=f"Suavidade: {self.aim_smooth}")
    
    def set_color(self, color_name):
        """Muda a cor de detecção"""
        self.active_color = color_name
        colors = {"enemy_red": "Vermelho", "enemy_blue": "Azul", "enemy_green": "Verde"}
        self.status_label.config(text=f"Cor: {colors[color_name]}", fg='#00ff00')
    
    def update_stats(self, hit):
        """Atualiza as estatísticas"""
        if hit:
            self.hits += 1
        self.shots_fired += 1
        
        if self.shots_fired % 10 == 0:  # Atualiza a cada 10 frames
            accuracy = (self.hits / self.shots_fired * 100) if self.shots_fired > 0 else 0
            self.stats_label.config(text=f"Acertos: {self.hits} | Tiros: {self.shots_fired} | Precisão: {accuracy:.1f}%")
    
    def update_panel_status(self):
        """Atualiza o status no painel"""
        status_text = f"Aimbot: {'ON' if self.aimbot_active else 'OFF'} | ESP: {'ON' if self.esp_active else 'OFF'}"
        self.status_label.config(text=status_text)
    
    def setup_hotkeys(self):
        """Configura as teclas de atalho"""
        keyboard.add_hotkey('F1', self.toggle_aimbot)
        keyboard.add_hotkey('F2', self.toggle_esp)
        keyboard.add_hotkey('F3', lambda: self.mode_var.set(
            "head" if self.mode_var.get() == "chest" else 
            "chest" if self.mode_var.get() == "hybrid" else "hybrid"
        ))
        keyboard.add_hotkey('F4', lambda: self.priority_var.set(
            "head_first" if self.priority_var.get() == "chest_first" else "chest_first"
        ))
        keyboard.add_hotkey('F5', lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0))
        keyboard.add_hotkey('F5', lambda: win32api.mouse_event(win32con.MOUSEEVENTF_LEFTUP, 0, 0, 0, 0), suppress=False, timeout=0.05)
    
    def run(self):
        """Inicia o programa"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║          OFFLINE AIMBOT PRO - APENAS PARA JOGOS OFFLINE      ║
╠══════════════════════════════════════════════════════════════╣
║  ✅ Mira que GRUDA na cabeça                                 ║
║  ✅ Linhas ESP nos oponentes                                ║
║  ✅ Modo Híbrido (1 peito + resto cabeça)                   ║
║  ✅ Painel flutuante completo                               ║
║                                                              ║
║  ⚠️  NUNCA use em jogos online! Isso é para DIVERTIR        ║
║     em jogos single-player como campanhas, vs bots, etc.    ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        self.setup_panel()
        self.setup_hotkeys()
        self.aimbot_thread.start()
        
        # Inicia o loop do tkinter
        self.panel.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.panel.mainloop()
    
    def on_closing(self):
        """Fecha o programa corretamente"""
        self.running = False
        self.aimbot_active = False
        cv2.destroyAllWindows()
        self.panel.destroy()

if __name__ == "__main__":
    # Instala as dependências se não tiver
    import subprocess
    import sys
    
    deps = ['opencv-python', 'pyautogui', 'mss', 'keyboard', 'pywin32', 'numpy']
    for dep in deps:
        try:
            __import__(dep.replace('-', '_'))
        except ImportError:
            print(f"Instalando {dep}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", dep])
    
    app = OfflineAimbot()
    app.run()