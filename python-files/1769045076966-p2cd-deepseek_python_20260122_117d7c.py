import tkinter as tk
import random
import math
import time
from tkinter import messagebox

class Mundoroto:
    def __init__(self, root):
        self.root = root
        self.root.title("World Roto - Fast Paced Edition")
        
        # Obtener dimensiones de pantalla
        self.ancho_pantalla = self.root.winfo_screenwidth()
        self.alto_pantalla = self.root.winfo_screenheight()
        
        # Configurar ventana
        self.ancho = min(1600, int(self.ancho_pantalla * 0.9))
        self.alto = min(900, int(self.alto_pantalla * 0.9))
        
        self.root.geometry(f"{self.ancho}x{self.alto}")
        self.root.configure(bg='black')
        
        # Centrar ventana
        self.root.update_idletasks()
        x = (self.ancho_pantalla - self.ancho) // 2
        y = (self.alto_pantalla - self.alto) // 2
        self.root.geometry(f"{self.ancho}x{self.alto}+{x}+{y}")
        
        self.escala = min(self.ancho / 1600, self.alto / 900)
        
        # Estado del juego
        self.en_menu_principal = True
        self.juego_activo = False
        self.pausado = False
        self.fullscreen = False
        self.boss_active = False
        self.boss_health = 0
        self.boss_max_health = 0
        self.enemigos_restantes = 0
        self.enemigos_por_nivel = 12
        
        # Variables del juego
        self.puntuacion = 0
        self.vidas = 3
        self.nivel = 1
        self.nivel_maximo = 9
        self.record = 0
        self.velocidad_juego = 1.0
        self.velocidad_avion = 12 * self.escala
        
        # Power-ups
        self.powerup_disparo = False
        self.powerup_velocidad = False
        self.powerup_escudo = False
        self.powerup_laser = False
        self.powerup_vida = False
        self.max_powerups = 3
        
        # Sistema de balas
        self.balas_maximas = 6
        self.balas_actuales = 6
        self.recarga_activa = False
        self.tiempo_recarga_base = 1.8
        self.tiempo_recarga_actual = 1.8
        self.tiempo_ultimo_disparo = 0
        self.ultima_recarga = 0
        
        # Sistema de enemigos
        self.max_enemigos_simultaneos = 4
        self.tiempo_entre_enemigos = 0.6
        self.ultimo_enemigo = time.time()
        self.enemigos_creados = 0
        
        # Efectos especiales
        self.invulnerable = False
        self.tiempo_invulnerabilidad = 0
        self.efecto_especial = False
        self.tiempo_efecto = 0
        
        # Colores del juego
        self.colores = {
            'fondo': '#0a0a1a',
            'panel': '#151530',
            'avion_cuerpo': '#00cc88',
            'avion_power': '#ffaa00',
            'bala_normal': '#ffff00',
            'bala_power': '#00ffff',
            'bala_laser': '#ff00ff',
            'texto': '#ffffff',
            'texto_destacado': '#ffff00',
            'barra_recarga': '#00ff00',
            'barra_fondo': '#333333',
            'barra_boss': '#ff0000',
            'nivel1': '#00ff00',
            'nivel2': '#00ffff',
            'nivel3': '#ff00ff',
            'nivel4': '#ffff00',
            'nivel5': '#ff0000',
            'boton_normal': '#ff5555',
            'boton_hover': '#ff3333',
            'boton_texto': '#ffffff',
            'menu_fondo': '#000022'
        }
        
        # Crear canvas
        self.canvas = tk.Canvas(root, width=self.ancho, height=self.alto, 
                               bg=self.colores['fondo'], highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        
        # Posición del avión
        self.avion_x = self.ancho // 2
        self.avion_y = self.alto - 100
        
        # Tamaños
        self.tamaño_avion = int(40 * self.escala)
        self.tamaño_bala = int(8 * self.escala)
        
        # Listas de elementos del juego
        self.balas = []
        self.enemigos = []
        self.explosiones = []
        self.powerups = []
        self.efectos = []
        self.estrellas = []
        self.boss_bullets = []
        self.boss_lasers = []
        self.boss_bombs = []
        
        # Control de teclado
        self.teclas_presionadas = set()
        
        # Iniciar menú
        self.mostrar_menu_principal()
        
    def mostrar_menu_principal(self):
        """Muestra el menú principal del juego"""
        self.en_menu_principal = True
        
        # Limpiar canvas
        self.canvas.delete("all")
        
        # Crear fondo estrellado para el menú
        self.crear_fondo_estrellado()
        
        # Título del juego
        self.canvas.create_text(
            self.ancho // 2, self.alto * 0.2,
            text="WORLD ROTO",
            fill='#ffff00',
            font=('Arial', int(70 * self.escala), 'bold'),
            tags='menu'
        )
        
        self.canvas.create_text(
            self.ancho // 2, self.alto * 0.2 + 60,
            text="FAST PACED EDITION",
            fill='#00ffff',
            font=('Arial', int(30 * self.escala), 'italic'),
            tags='menu'
        )
        
        # Crear botones del menú
        btn_ancho = int(300 * self.escala)
        btn_alto = int(60 * self.escala)
        btn_y = self.alto * 0.4
        btn_espacio = btn_alto + 20
        
        # Botón JUGAR
        self.btn_jugar = tk.Button(
            self.root,
            text="🎮 JUGAR",
            command=self.iniciar_juego,
            bg=self.colores['boton_normal'],
            fg=self.colores['boton_texto'],
            activebackground=self.colores['boton_hover'],
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        # Botón CONTROLES
        self.btn_controles = tk.Button(
            self.root,
            text="🎮 CONTROLES",
            command=self.mostrar_controles,
            bg='#5555ff',
            fg=self.colores['boton_texto'],
            activebackground='#3333ff',
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        # Botón RÉCORDS
        self.btn_records = tk.Button(
            self.root,
            text="🏆 RÉCORDS",
            command=self.mostrar_records,
            bg='#ffaa00',
            fg=self.colores['boton_texto'],
            activebackground='#ff8800',
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        # Botón SALIR
        self.btn_salir = tk.Button(
            self.root,
            text="❌ SALIR",
            command=self.salir_juego,
            bg='#555555',
            fg=self.colores['boton_texto'],
            activebackground='#333333',
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        # Posicionar botones
        self.canvas.create_window(
            self.ancho // 2, btn_y,
            window=self.btn_jugar,
            tags='menu'
        )
        
        self.canvas.create_window(
            self.ancho // 2, btn_y + btn_espacio,
            window=self.btn_controles,
            tags='menu'
        )
        
        self.canvas.create_window(
            self.ancho // 2, btn_y + btn_espacio * 2,
            window=self.btn_records,
            tags='menu'
        )
        
        self.canvas.create_window(
            self.ancho // 2, btn_y + btn_espacio * 3,
            window=self.btn_salir,
            tags='menu'
        )
        
        # Información de versión
        self.canvas.create_text(
            self.ancho // 2, self.alto - 30,
            text="v1.0 - Desarrollado con Python y Tkinter",
            fill='#888888',
            font=('Arial', int(12 * self.escala)),
            tags='menu'
        )
        
        # Agregar efectos visuales al menú
        self.animar_menu()
    
    def animar_menu(self):
        """Agrega animaciones al menú principal"""
        if not self.en_menu_principal:
            return
            
        # Crear efecto de partículas
        if random.random() < 0.3:
            x = random.randint(0, self.ancho)
            tamaño = random.uniform(2, 6) * self.escala
            particula = self.canvas.create_oval(
                x, 0, x + tamaño, tamaño,
                fill=random.choice(['#ffff00', '#00ffff', '#ff00ff']),
                outline='', tags='efecto_menu'
            )
            
            # Animar partícula
            self.animar_particula(particula, 0, tamaño)
        
        # Llamar recursivamente para continuar animación
        self.root.after(100, self.animar_menu)
    
    def animar_particula(self, particula_id, y, tamaño):
        """Anima una partícula en el menú"""
        if not self.en_menu_principal:
            self.canvas.delete(particula_id)
            return
            
        y += 3
        self.canvas.move(particula_id, 0, 3)
        
        if y < self.alto:
            self.root.after(30, lambda: self.animar_particula(particula_id, y, tamaño))
        else:
            self.canvas.delete(particula_id)
    
    def mostrar_controles(self):
        """Muestra la pantalla de controles"""
        self.canvas.delete("all")
        self.crear_fondo_estrellado()
        
        # Título
        self.canvas.create_text(
            self.ancho // 2, self.alto * 0.15,
            text="CONTROLES DEL JUEGO",
            fill='#ffff00',
            font=('Arial', int(50 * self.escala), 'bold'),
            tags='controles'
        )
        
        # Controles
        controles_info = [
            ("FLECHAS", "Mover el avión", "← → ↑ ↓"),
            ("ESPACIO", "Disparar", "␣"),
            ("R", "Recargar balas", "R"),
            ("P", "Pausar/Reanudar", "P"),
            ("F", "Pantalla completa", "F"),
            ("ESC", "Salir del juego", "⎋")
        ]
        
        y_pos = self.alto * 0.3
        for tecla, descripcion, simbolo in controles_info:
            self.canvas.create_text(
                self.ancho // 2 - 200, y_pos,
                text=tecla,
                fill='#00ffff',
                font=('Arial', int(28 * self.escala), 'bold'),
                tags='controles',
                anchor='e'
            )
            
            self.canvas.create_text(
                self.ancho // 2 - 180, y_pos,
                text=descripcion,
                fill='#ffffff',
                font=('Arial', int(24 * self.escala)),
                tags='controles',
                anchor='w'
            )
            
            self.canvas.create_text(
                self.ancho - 200, y_pos,
                text=simbolo,
                fill='#ffaa00',
                font=('Arial', int(30 * self.escala)),
                tags='controles',
                anchor='e'
            )
            
            y_pos += 70
        
        # Power-ups
        self.canvas.create_text(
            self.ancho // 2, y_pos + 40,
            text="POWER-UPS",
            fill='#ff00ff',
            font=('Arial', int(40 * self.escala), 'bold'),
            tags='controles'
        )
        
        y_pos += 100
        powerups_info = [
            ("⚡", "DISPARO MEJORADO", "Balas más grandes y potentes"),
            ("↻", "VELOCIDAD", "Avión y recarga más rápidos"),
            ("🛡", "ESCUDO", "Protección contra un impacto"),
            ("🔺", "LÁSER", "Disparos láser devastadores"),
            ("♥", "VIDA EXTRA", "Añade una vida al jugador")
        ]
        
        for simbolo, nombre, desc in powerups_info:
            self.canvas.create_text(
                self.ancho // 2 - 300, y_pos,
                text=simbolo,
                fill='#ffff00',
                font=('Arial', int(32 * self.escala)),
                tags='controles',
                anchor='e'
            )
            
            self.canvas.create_text(
                self.ancho // 2 - 280, y_pos,
                text=nombre,
                fill='#88ff88',
                font=('Arial', int(24 * self.escala), 'bold'),
                tags='controles',
                anchor='w'
            )
            
            self.canvas.create_text(
                self.ancho // 2 + 100, y_pos,
                text=desc,
                fill='#aaaaaa',
                font=('Arial', int(20 * self.escala)),
                tags='controles',
                anchor='w'
            )
            
            y_pos += 50
        
        # Botón VOLVER
        btn_volver = tk.Button(
            self.root,
            text="🔙 VOLVER AL MENÚ",
            command=self.mostrar_menu_principal,
            bg=self.colores['boton_normal'],
            fg=self.colores['boton_texto'],
            activebackground=self.colores['boton_hover'],
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        self.canvas.create_window(
            self.ancho // 2, self.alto - 100,
            window=btn_volver,
            tags='controles'
        )
    
    def mostrar_records(self):
        """Muestra la pantalla de récords"""
        self.canvas.delete("all")
        self.crear_fondo_estrellado()
        
        # Título
        self.canvas.create_text(
            self.ancho // 2, self.alto * 0.15,
            text="RÉCORDS Y ESTADÍSTICAS",
            fill='#ffff00',
            font=('Arial', int(50 * self.escala), 'bold'),
            tags='records'
        )
        
        # Información de récord actual
        self.canvas.create_text(
            self.ancho // 2, self.alto * 0.3,
            text=f"MEJOR PUNTUACIÓN: {self.record:06d}",
            fill='#ffaa00',
            font=('Courier', int(40 * self.escala), 'bold'),
            tags='records'
        )
        
        # Estadísticas del juego
        stats_y = self.alto * 0.4
        estadisticas = [
            ("Nivel máximo alcanzado:", f"NIVEL {self.nivel_maximo}"),
            ("Enemigos por nivel:", str(self.enemigos_por_nivel)),
            ("Vidas iniciales:", "3"),
            ("Balas máximo:", "6"),
            ("Power-ups máx. simultáneos:", "3"),
            ("Total de niveles:", "9")
        ]
        
        for label, valor in estadisticas:
            self.canvas.create_text(
                self.ancho // 2 - 150, stats_y,
                text=label,
                fill='#88ff88',
                font=('Arial', int(24 * self.escala)),
                tags='records',
                anchor='e'
            )
            
            self.canvas.create_text(
                self.ancho // 2 - 130, stats_y,
                text=valor,
                fill='#ffffff',
                font=('Arial', int(24 * self.escala), 'bold'),
                tags='records',
                anchor='w'
            )
            
            stats_y += 50
        
        # Consejos
        self.canvas.create_text(
            self.ancho // 2, stats_y + 40,
            text="CONSEJOS PARA MEJORAR",
            fill='#00ffff',
            font=('Arial', int(32 * self.escala), 'bold'),
            tags='records'
        )
        
        stats_y += 100
        consejos = [
            "• Recarga antes de quedarte sin balas",
            "• Cada 3 niveles hay un jefe más difícil",
            "• Los power-ups aparecen al eliminar enemigos",
            "• Usa el escudo estratégicamente contra jefes",
            "• Mantente en movimiento para evitar disparos"
        ]
        
        for consejo in consejos:
            self.canvas.create_text(
                self.ancho // 2, stats_y,
                text=consejo,
                fill='#cccccc',
                font=('Arial', int(20 * self.escala)),
                tags='records'
            )
            stats_y += 40
        
        # Botón VOLVER
        btn_volver = tk.Button(
            self.root,
            text="🔙 VOLVER AL MENÚ",
            command=self.mostrar_menu_principal,
            bg=self.colores['boton_normal'],
            fg=self.colores['boton_texto'],
            activebackground=self.colores['boton_hover'],
            font=('Arial', int(22 * self.escala), 'bold'),
            relief='raised',
            bd=4,
            padx=30,
            pady=10,
            cursor='hand2'
        )
        
        self.canvas.create_window(
            self.ancho // 2, self.alto - 100,
            window=btn_volver,
            tags='records'
        )
    
    def iniciar_juego(self):
        """Inicia el juego desde el menú"""
        self.en_menu_principal = False
        self.juego_activo = True
        
        # Limpiar canvas
        self.canvas.delete("all")
        
        # Configurar eventos del juego
        self.configurar_eventos()
        
        # Inicializar juego
        self.inicializar_juego()
        
    def configurar_eventos(self):
        self.root.bind('<KeyPress>', self.presionar_tecla)
        self.root.bind('<KeyRelease>', self.soltar_tecla)
        self.root.bind('<space>', self.disparar)
        self.root.bind('<p>', self.pausar_juego)
        self.root.bind('<Escape>', self.salir_al_menu)
        self.root.bind('<f>', self.toggle_fullscreen)
        self.root.bind('<r>', self.recargar_balas)
    
    # ... (el resto del código del juego se mantiene igual desde aquí) ...
    
    def crear_fondo_estrellado(self):
        self.estrellas = []
        num_estrellas = int(100 * (self.ancho * self.alto) / (1600 * 900))
        for _ in range(num_estrellas):
            estrella = {
                'x': random.randint(0, self.ancho),
                'y': random.randint(0, self.alto),
                'tamaño': random.uniform(0.5, 2) * self.escala,
                'velocidad': random.uniform(0.1, 0.3) * self.escala,
                'brillo': random.randint(100, 255),
                'id': None
            }
            self.estrellas.append(estrella)
            
            color = f'#{estrella["brillo"]:02x}{estrella["brillo"]:02x}{estrella["brillo"]:02x}'
            radio = estrella['tamaño']
            estrella['id'] = self.canvas.create_oval(
                estrella['x'] - radio, estrella['y'] - radio,
                estrella['x'] + radio, estrella['y'] + radio,
                fill=color, outline='', tags='fondo'
            )
    
    def crear_interfaz(self):
        panel_alto = int(60 * self.escala)
        self.canvas.create_rectangle(
            0, 0, self.ancho, panel_alto,
            fill=self.colores['panel'], outline='', tags='interfaz'
        )
        
        self.texto_puntuacion = self.canvas.create_text(
            int(120 * self.escala), int(panel_alto/2),
            text=f"SCORE: {self.puntuacion:06d}", 
            fill=self.colores['texto'], 
            font=('Courier', int(18 * self.escala), 'bold'),
            tags='interfaz'
        )
        
        self.corazones = []
        self.actualizar_vidas()
        
        color_nivel = self.colores[f'nivel{min(self.nivel, 5)}']
        self.texto_nivel = self.canvas.create_text(
            int(350 * self.escala), int(panel_alto/2),
            text=f"LEVEL: {self.nivel}/{self.nivel_maximo}", 
            fill=color_nivel,
            font=('Arial', int(16 * self.escala), 'bold'),
            tags='interfaz'
        )
        
        self.texto_record = self.canvas.create_text(
            int(600 * self.escala), int(panel_alto/2),
            text=f"BEST: {self.record:06d}", 
            fill='#ffcc00',
            font=('Courier', int(18 * self.escala), 'bold'),
            tags='interfaz'
        )
        
        self.texto_balas = self.canvas.create_text(
            self.ancho - int(150 * self.escala), int(panel_alto/2),
            text=f"BULLETS: {self.balas_actuales}/{self.balas_maximas}", 
            fill='#ffff00' if self.balas_actuales > 2 else '#ff5555',
            font=('Courier', int(16 * self.escala), 'bold'),
            tags='interfaz'
        )
        
        self.texto_enemigos = self.canvas.create_text(
            self.ancho - int(350 * self.escala), int(panel_alto/2),
            text=f"ENEMIES: {self.enemigos_restantes}", 
            fill='#ffaa00',
            font=('Courier', int(14 * self.escala), 'bold'),
            tags='interfaz'
        )
    
    def crear_indicadores_powerups(self):
        self.indicadores_powerups = {
            'disparo': None,
            'velocidad': None,
            'escudo': None,
            'laser': None,
            'vida': None
        }
        
        x_base = self.ancho - 250
        y_base = 80
        tamaño = int(20 * self.escala)
        
        powerups_info = [
            ('disparo', '#66ffff', '⚡'),
            ('velocidad', '#88ff88', '↻'),
            ('escudo', '#aa88ff', '🛡'),
            ('laser', '#ff00ff', '🔺'),
            ('vida', '#ff66cc', '♥')
        ]
        
        for i, (tipo, color, simbolo) in enumerate(powerups_info):
            x = x_base + i * (tamaño + 15)
            self.indicadores_powerups[tipo] = self.canvas.create_oval(
                x, y_base, x + tamaño, y_base + tamaño,
                fill=color, outline='white', width=2, state='hidden', tags='interfaz'
            )
            self.canvas.create_text(x + tamaño//2, y_base + tamaño//2,
                                  text=simbolo, fill='black', 
                                  font=('Arial', int(10 * self.escala)), tags='interfaz')
    
    def actualizar_indicadores_powerups(self):
        estados = {
            'disparo': self.powerup_disparo,
            'velocidad': self.powerup_velocidad,
            'escudo': self.powerup_escudo,
            'laser': self.powerup_laser,
            'vida': self.powerup_vida
        }
        
        for tipo, activo in estados.items():
            estado = 'normal' if activo else 'hidden'
            self.canvas.itemconfig(self.indicadores_powerups[tipo], state=estado)
    
    def crear_barra_recarga(self):
        ancho_barra = int(250 * self.escala)
        alto_barra = int(20 * self.escala)
        x = self.ancho - ancho_barra - 30
        y = self.alto - 50
        
        self.barra_recarga_fondo = self.canvas.create_rectangle(
            x, y, x + ancho_barra, y + alto_barra,
            fill=self.colores['barra_fondo'], outline='#555555', width=3, tags='interfaz'
        )
        
        self.barra_recarga_progreso = self.canvas.create_rectangle(
            x, y, x, y + alto_barra,
            fill=self.colores['barra_recarga'], outline='', tags='interfaz'
        )
    
    def crear_barra_boss(self):
        if hasattr(self, 'barra_boss_fondo'):
            self.canvas.delete(self.barra_boss_fondo)
            self.canvas.delete(self.barra_boss_vida)
        
        ancho_barra = int(400 * self.escala)
        alto_barra = int(25 * self.escala)
        x = (self.ancho - ancho_barra) // 2
        y = 70
        
        self.barra_boss_fondo = self.canvas.create_rectangle(
            x, y, x + ancho_barra, y + alto_barra,
            fill='#222222', outline='#555555', width=3, tags='boss'
        )
        
        self.barra_boss_vida = self.canvas.create_rectangle(
            x, y, x + ancho_barra, y + alto_barra,
            fill=self.colores['barra_boss'], outline='', tags='boss'
        )
        
        self.texto_boss = self.canvas.create_text(
            self.ancho // 2, y - 20,
            text="BOSS", fill='#ff0000',
            font=('Arial', int(24 * self.escala), 'bold'),
            tags='boss'
        )
    
    def actualizar_barra_boss(self):
        if not self.boss_active:
            return
        
        ancho_barra = int(400 * self.escala)
        x = (self.ancho - ancho_barra) // 2
        
        progreso = self.boss_health / self.boss_max_health
        ancho_vida = int(ancho_barra * progreso)
        
        self.canvas.coords(self.barra_boss_vida,
                          x, 70, x + ancho_vida, 95)
        
        texto_vida = f"BOSS: {self.boss_health}/{self.boss_max_health}"
        self.canvas.itemconfig(self.texto_boss, text=texto_vida)
    
    def dibujar_avion(self):
        tamaño = self.tamaño_avion
        
        self.canvas.delete('avion')
        
        color_cuerpo = self.colores['avion_power'] if self.efecto_especial else self.colores['avion_cuerpo']
        color_detalle = '#ffff00' if self.powerup_disparo else '#00ffaa'
        
        if self.invulnerable:
            if int(time.time() * 10) % 2 == 0:
                color_cuerpo = '#ffffff'
                color_detalle = '#cccccc'
        
        if self.efecto_especial:
            for i in range(3):
                radio = tamaño * (1.2 + i * 0.1)
                self.canvas.create_oval(
                    self.avion_x - radio, self.avion_y - radio,
                    self.avion_x + radio, self.avion_y + radio,
                    fill='', outline='#ffff00', width=2, tags='avion'
                )
        
        if self.powerup_escudo:
            escudo_radio = tamaño * 1.3
            self.canvas.create_oval(
                self.avion_x - escudo_radio, self.avion_y - escudo_radio,
                self.avion_x + escudo_radio, self.avion_y + escudo_radio,
                fill='', outline='#88aaff', width=4, tags='avion'
            )
        
        puntos_cuerpo = [
            self.avion_x, self.avion_y - tamaño * 0.8,
            self.avion_x - tamaño * 0.3, self.avion_y - tamaño * 0.2,
            self.avion_x - tamaño * 0.5, self.avion_y + tamaño * 0.4,
            self.avion_x + tamaño * 0.5, self.avion_y + tamaño * 0.4,
            self.avion_x + tamaño * 0.3, self.avion_y - tamaño * 0.2,
        ]
        
        self.canvas.create_polygon(
            puntos_cuerpo, 
            fill=color_cuerpo,
            outline=color_detalle,
            width=3,
            tags='avion'
        )
        
        self.canvas.create_oval(
            self.avion_x - tamaño * 0.2, self.avion_y - tamaño * 0.6,
            self.avion_x + tamaño * 0.2, self.avion_y - tamaño * 0.2,
            fill='#aaddff', outline='#ffffff', width=2, tags='avion'
        )
        
        self.canvas.create_polygon([
            self.avion_x - tamaño * 0.25, self.avion_y,
            self.avion_x - tamaño * 1.0, self.avion_y - tamaño * 0.3,
            self.avion_x - tamaño * 0.7, self.avion_y,
        ], fill=color_cuerpo, outline=color_detalle, width=2, tags='avion')
        
        self.canvas.create_polygon([
            self.avion_x + tamaño * 0.25, self.avion_y,
            self.avion_x + tamaño * 1.0, self.avion_y - tamaño * 0.3,
            self.avion_x + tamaño * 0.7, self.avion_y,
        ], fill=color_cuerpo, outline=color_detalle, width=2, tags='avion')
        
        for dx in [-tamaño * 0.4, tamaño * 0.4]:
            self.canvas.create_oval(
                self.avion_x + dx - tamaño * 0.15, self.avion_y + tamaño * 0.3,
                self.avion_x + dx + tamaño * 0.15, self.avion_y + tamaño * 0.6,
                fill='#222222', outline='#444444', width=2, tags='avion'
            )
            
            if self.teclas_presionadas:
                intensidad = random.uniform(0.3, 0.6)
                color_propulsion = '#ffff00' if self.powerup_velocidad else '#ff5500'
                for i in range(2):
                    longitud = tamaño * intensidad * (1.3 if self.powerup_velocidad else 1)
                    self.canvas.create_polygon([
                        self.avion_x + dx - tamaño * 0.1, self.avion_y + tamaño * 0.6,
                        self.avion_x + dx, self.avion_y + tamaño * 0.6 + longitud,
                        self.avion_x + dx + tamaño * 0.1, self.avion_y + tamaño * 0.6
                    ], fill=color_propulsion, outline='', tags='avion')
    
    def crear_enemigo_nivel(self):
        if self.boss_active or len(self.enemigos) >= self.max_enemigos_simultaneos or self.enemigos_restantes <= 0:
            return None
        
        tipos_enemigos = ['pequeño', 'mediano', 'grande']
        pesos = [0.5, 0.35, 0.15]
        tipo = random.choices(tipos_enemigos, weights=pesos)[0]
        
        config_enemigos = {
            'pequeño': {'color': '#ff3333', 'vida': 1, 'velocidad': 2.5, 'puntos': 10, 'tamaño': 25, 'disparos_necesarios': 1},
            'mediano': {'color': '#ff9933', 'vida': 2, 'velocidad': 2.0, 'puntos': 20, 'tamaño': 35, 'disparos_necesarios': 2},
            'grande': {'color': '#ff5500', 'vida': 5, 'velocidad': 1.5, 'puntos': 50, 'tamaño': 50, 'disparos_necesarios': 5}
        }
        
        cfg = config_enemigos[tipo]
        
        tamaño = int(cfg['tamaño'] * self.escala)
        x = random.randint(tamaño, self.ancho - tamaño)
        
        enemigo = {
            'x': x,
            'y': -tamaño * 2,
            'tipo': tipo,
            'color': cfg['color'],
            'vida': cfg['vida'],
            'vida_max': cfg['vida'],
            'velocidad': cfg['velocidad'] * self.velocidad_juego,
            'puntos': cfg['puntos'],
            'tamaño': tamaño,
            'disparos_necesarios': cfg['disparos_necesarios'],
            'disparos_recibidos': 0,
            'direccion': random.choice([-1, 1]) * random.uniform(0.2, 0.4),
            'id': None
        }
        
        enemigo['id'] = self.canvas.create_oval(
            x - tamaño, -tamaño * 2 - tamaño,
            x + tamaño, -tamaño * 2 + tamaño,
            fill=enemigo['color'], outline='white', width=2, tags='enemigo'
        )
        
        self.enemigos.append(enemigo)
        self.enemigos_restantes -= 1
        self.enemigos_creados += 1
        self.actualizar_contador_enemigos()
        return enemigo
    
    def crear_boss(self):
        self.boss_active = True
        
        boss_configs = {
            1: {'vida': 48, 'color': '#ff0000', 'tamaño': 80, 'velocidad': 1.2},
            2: {'vida': 64, 'color': '#ff5500', 'tamaño': 85, 'velocidad': 1.3},
            3: {'vida': 85, 'color': '#ffaa00', 'tamaño': 90, 'velocidad': 1.4},
            4: {'vida': 120, 'color': '#ffff00', 'tamaño': 95, 'velocidad': 1.5},
            5: {'vida': 150, 'color': '#ffff55', 'tamaño': 100, 'velocidad': 1.6},
            6: {'vida': 150, 'color': '#ffffaa', 'tamaño': 105, 'velocidad': 1.7},
            7: {'vida': 180, 'color': '#ffffff', 'tamaño': 110, 'velocidad': 1.8},
            8: {'vida': 240, 'color': '#aaffff', 'tamaño': 115, 'velocidad': 1.9},
            9: {'vida': 300, 'color': '#55ffff', 'tamaño': 120, 'velocidad': 2.0}
        }
        
        cfg = boss_configs[min(self.nivel, 9)]
        self.boss_health = cfg['vida']
        self.boss_max_health = cfg['vida']
        
        tamaño = int(cfg['tamaño'] * self.escala)
        self.boss = {
            'x': self.ancho // 2,
            'y': tamaño + 50,
            'tamaño': tamaño,
            'color': cfg['color'],
            'velocidad': cfg['velocidad'] * self.escala,
            'direccion': 1,
            'ultimo_disparo': time.time(),
            'ultimo_laser': time.time(),
            'ultima_bomba': time.time(),
            'id': None
        }
        
        self.boss['id'] = self.canvas.create_oval(
            self.boss['x'] - tamaño, self.boss['y'] - tamaño,
            self.boss['x'] + tamaño, self.boss['y'] + tamaño,
            fill=self.boss['color'], outline='#ffffff', width=4, tags='boss'
        )
        
        self.crear_barra_boss()
        
        for enemigo in self.enemigos:
            self.canvas.delete(enemigo['id'])
        self.enemigos.clear()
    
    def boss_disparar(self):
        tiempo_actual = time.time()
        
        intervalo_disparo = max(0.3, 1.5 - (self.nivel * 0.1))
        
        if tiempo_actual - self.boss['ultimo_disparo'] > intervalo_disparo:
            self.boss['ultimo_disparo'] = tiempo_actual
            
            num_disparos = 1
            if self.nivel >= 2:
                num_disparos = 2
            if self.nivel >= 5:
                num_disparos = 3
            if self.nivel >= 9:
                num_disparos = 8
            
            for i in range(num_disparos):
                if self.nivel >= 5:
                    angulo = math.atan2(self.avion_y - self.boss['y'], self.avion_x - self.boss['x'])
                    if self.nivel >= 6:
                        angulo += random.uniform(-0.2, 0.2)
                else:
                    angulo = math.pi / 2
                
                offset = (i - (num_disparos - 1) / 2) * 40
                boss_bullet = {
                    'x': self.boss['x'] + offset,
                    'y': self.boss['y'] + self.boss['tamaño'],
                    'velocidad': 5 * self.escala,
                    'angulo': angulo,
                    'id': self.canvas.create_oval(0, 0, 0, 0, fill='#ff5555', outline='')
                }
                self.boss_bullets.append(boss_bullet)
    
    def boss_laser(self):
        tiempo_actual = time.time()
        
        if self.nivel >= 3:
            intervalo = max(0.3, 2.0 - (self.nivel * 0.15))
            
            if tiempo_actual - self.boss['ultimo_laser'] > intervalo:
                self.boss['ultimo_laser'] = tiempo_actual
                
                num_lasers = 1
                if self.nivel >= 4:
                    num_lasers = 2
                if self.nivel >= 9:
                    num_lasers = 3
                
                for i in range(num_lasers):
                    offset = (i - (num_lasers - 1) / 2) * 100
                    boss_laser = {
                        'x': self.boss['x'] + offset,
                        'y': self.boss['y'] + self.boss['tamaño'],
                        'ancho': int(15 * self.escala),
                        'alto': self.alto,
                        'id': self.canvas.create_rectangle(0, 0, 0, 0, fill='#ff00ff', outline='')
                    }
                    self.boss_lasers.append(boss_laser)
    
    def boss_bomba(self):
        tiempo_actual = time.time()
        
        if self.nivel >= 9:
            if tiempo_actual - self.boss['ultima_bomba'] > 3.0:
                self.boss['ultima_bomba'] = tiempo_actual
                
                for i in range(3):
                    x = random.randint(100, self.ancho - 100)
                    y = random.randint(100, self.alto // 2)
                    
                    boss_bomba = {
                        'x': x,
                        'y': -50,
                        'velocidad': 3 * self.escala,
                        'tiempo_impacto': tiempo_actual + 2.0,
                        'id': self.canvas.create_oval(0, 0, 0, 0, fill='#ff0000', outline=''),
                        'indicador': self.canvas.create_oval(0, 0, 0, 0, fill='#ff0000', outline='', stipple='gray50')
                    }
                    self.boss_bombs.append(boss_bomba)
    
    def mover_boss(self):
        if not self.boss_active:
            return
        
        self.boss['x'] += self.boss['velocidad'] * self.boss['direccion']
        
        if self.nivel >= 7:
            dx = self.avion_x - self.boss['x']
            dy = self.avion_y - self.boss['y']
            distancia = math.sqrt(dx*dx + dy*dy)
            
            if distancia > 50:
                self.boss['x'] += dx / distancia * self.boss['velocidad'] * 0.5
        
        if self.boss['x'] < self.boss['tamaño'] or self.boss['x'] > self.ancho - self.boss['tamaño']:
            self.boss['direccion'] *= -1
        
        tamaño = self.boss['tamaño']
        self.canvas.coords(self.boss['id'],
            self.boss['x'] - tamaño, self.boss['y'] - tamaño,
            self.boss['x'] + tamaño, self.boss['y'] + tamaño
        )
        
        self.boss_disparar()
        self.boss_laser()
        self.boss_bomba()
    
    def crear_powerup(self, x, y):
        if len(self.powerups) >= self.max_powerups:
            return None
        
        tipos = ['disparo', 'velocidad', 'escudo', 'laser', 'vida']
        tipo = random.choice(tipos)
        
        config_powerups = {
            'disparo': {'color': '#66ffff', 'simbolo': '⚡'},
            'velocidad': {'color': '#88ff88', 'simbolo': '↻'},
            'escudo': {'color': '#aa88ff', 'simbolo': '🛡'},
            'laser': {'color': '#ff00ff', 'simbolo': '🔺'},
            'vida': {'color': '#ff66cc', 'simbolo': '♥'}
        }
        
        cfg = config_powerups[tipo]
        tamaño = int(25 * self.escala)
        
        powerup = {
            'x': x,
            'y': y,
            'tipo': tipo,
            'color': cfg['color'],
            'simbolo': cfg['simbolo'],
            'velocidad': 2.0 * self.velocidad_juego,
            'tamaño': tamaño,
            'id': None,
            'id_simbolo': None
        }
        
        powerup['id'] = self.canvas.create_oval(
            x - tamaño, y - tamaño,
            x + tamaño, y + tamaño,
            fill=powerup['color'], outline='white', width=3, tags='powerup'
        )
        
        powerup['id_simbolo'] = self.canvas.create_text(
            x, y, text=powerup['simbolo'],
            fill='black', font=('Arial', int(tamaño*1.2)), tags='powerup'
        )
        
        self.powerups.append(powerup)
        return powerup
    
    def aplicar_powerup(self, tipo):
        if tipo == 'vida':
            self.vidas = min(3, self.vidas + 1)
            self.actualizar_vidas()
            self.efecto_especial = True
            self.tiempo_efecto = time.time() + 3.0
            
        elif tipo == 'disparo' and not self.powerup_disparo:
            self.powerup_disparo = True
            self.efecto_especial = True
            self.tiempo_efecto = time.time() + 3.0
            
        elif tipo == 'velocidad' and not self.powerup_velocidad:
            self.powerup_velocidad = True
            self.velocidad_avion = min(18 * self.escala, self.velocidad_avion * 1.5)
            self.efecto_especial = True
            self.tiempo_efecto = time.time() + 3.0
            
        elif tipo == 'escudo' and not self.powerup_escudo:
            self.powerup_escudo = True
            self.efecto_especial = True
            self.tiempo_efecto = time.time() + 3.0
            
        elif tipo == 'laser' and not self.powerup_laser:
            self.powerup_laser = True
            self.efecto_especial = True
            self.tiempo_efecto = time.time() + 3.0
        
        self.actualizar_indicadores_powerups()
        return True
    
    def presionar_tecla(self, event):
        if event.keysym in ['Left', 'Right', 'Up', 'Down']:
            self.teclas_presionadas.add(event.keysym)
    
    def soltar_tecla(self, event):
        if event.keysym in self.teclas_presionadas:
            self.teclas_presionadas.remove(event.keysym)
    
    def disparar(self, event=None):
        if not self.juego_activo or self.pausado or self.balas_actuales <= 0:
            return
        
        tiempo_actual = time.time()
        if tiempo_actual - self.tiempo_ultimo_disparo < 0.1:
            return
        
        self.balas_actuales -= 1
        self.tiempo_ultimo_disparo = tiempo_actual
        self.actualizar_contador_balas()
        
        self.crear_efecto_disparo()
        
        if self.powerup_laser:
            tamaño = self.tamaño_bala * 2.5
            color = self.colores['bala_laser']
            daño = 3
        elif self.powerup_disparo:
            tamaño = self.tamaño_bala * 2.0
            color = self.colores['bala_power']
            daño = 2
        else:
            tamaño = self.tamaño_bala
            color = self.colores['bala_normal']
            daño = 1
        
        bala = {
            'x': self.avion_x,
            'y': self.avion_y - self.tamaño_avion * 0.8,
            'velocidad': 30 * self.velocidad_juego,
            'tamaño': tamaño,
            'daño': daño,
            'color': color,
            'id': self.canvas.create_oval(
                self.avion_x - tamaño, self.avion_y - self.tamaño_avion * 0.8 - tamaño,
                self.avion_x + tamaño, self.avion_y - self.tamaño_avion * 0.8 + tamaño,
                fill=color, outline='#ffaa00', width=2, tags='bala'
            )
        }
        self.balas.append(bala)
        
        if self.balas_actuales <= 2 and not self.recarga_activa:
            self.iniciar_recarga()
    
    def crear_efecto_disparo(self):
        color_flash = self.colores['bala_laser'] if self.powerup_laser else self.colores['bala_power'] if self.powerup_disparo else self.colores['bala_normal']
        flash = self.canvas.create_oval(
            self.avion_x - 15, self.avion_y - self.tamaño_avion - 15,
            self.avion_x + 15, self.avion_y - self.tamaño_avion + 15,
            fill=color_flash, outline='', tags='efecto'
        )
        self.root.after(50, lambda: self.canvas.delete(flash))
    
    def recargar_balas(self, event=None):
        if not self.juego_activo or self.pausado or self.recarga_activa:
            return
        
        if self.balas_actuales >= self.balas_maximas:
            return
        
        self.iniciar_recarga()
    
    def iniciar_recarga(self):
        self.recarga_activa = True
        self.ultima_recarga = time.time()
        self.tiempo_recarga_actual = self.tiempo_recarga_base * (0.4 if self.powerup_velocidad else 1)
    
    def finalizar_recarga(self):
        balas_recargar = self.balas_maximas - self.balas_actuales
        self.balas_actuales += balas_recargar
        self.recarga_activa = False
        self.actualizar_contador_balas()
        
        self.crear_explosion(self.avion_x, self.avion_y, 10, '#00ff00')
    
    def actualizar_barra_recarga(self):
        if not self.recarga_activa:
            self.canvas.coords(self.barra_recarga_progreso, 0, 0, 0, 0)
            return
        
        tiempo_transcurrido = time.time() - self.ultima_recarga
        progreso = min(1.0, tiempo_transcurrido / self.tiempo_recarga_actual)
        
        ancho_barra = int(250 * self.escala)
        alto_barra = int(20 * self.escala)
        x = self.ancho - ancho_barra - 30
        y = self.alto - 50
        
        ancho_progreso = int(ancho_barra * progreso)
        self.canvas.coords(self.barra_recarga_progreso,
                          x, y, x + ancho_progreso, y + alto_barra)
        
        if progreso >= 1.0:
            self.finalizar_recarga()
    
    def actualizar_contador_balas(self):
        color = '#ffff00' if self.balas_actuales > 3 else '#ffaa00' if self.balas_actuales > 1 else '#ff5555'
        self.canvas.itemconfig(self.texto_balas,
                              text=f"BULLETS: {self.balas_actuales}/{self.balas_maximas}",
                              fill=color)
    
    def actualizar_contador_enemigos(self):
        self.canvas.itemconfig(self.texto_enemigos,
                              text=f"ENEMIES: {self.enemigos_restantes}",
                              fill='#ffaa00' if self.enemigos_restantes > 5 else '#ffff00' if self.enemigos_restantes > 0 else '#00ff00')
    
    def mover_avion(self):
        velocidad = min(18 * self.escala, self.velocidad_avion * (1.5 if self.powerup_velocidad else 1))
        
        if 'Left' in self.teclas_presionadas and self.avion_x > self.tamaño_avion:
            self.avion_x -= velocidad
        if 'Right' in self.teclas_presionadas and self.avion_x < self.ancho - self.tamaño_avion:
            self.avion_x += velocidad
        if 'Up' in self.teclas_presionadas and self.avion_y > self.tamaño_avion + 80:
            self.avion_y -= velocidad
        if 'Down' in self.teclas_presionadas and self.avion_y < self.alto - self.tamaño_avion:
            self.avion_y += velocidad
        
        if self.efecto_especial and time.time() > self.tiempo_efecto:
            self.efecto_especial = False
        
        self.dibujar_avion()
    
    def actualizar_elementos(self):
        if self.recarga_activa:
            self.actualizar_barra_recarga()
        
        if self.invulnerable:
            if time.time() - self.tiempo_invulnerabilidad > 1.0:
                self.invulnerable = False
        
        for estrella in self.estrellas:
            estrella['y'] += estrella['velocidad'] * self.velocidad_juego
            if estrella['y'] > self.alto:
                estrella['y'] = 0
                estrella['x'] = random.randint(0, self.ancho)
            
            radio = estrella['tamaño']
            self.canvas.coords(estrella['id'],
                estrella['x'] - radio, estrella['y'] - radio,
                estrella['x'] + radio, estrella['y'] + radio
            )
        
        for bala in self.balas[:]:
            bala['y'] -= bala['velocidad']
            
            self.canvas.coords(bala['id'],
                bala['x'] - bala['tamaño'], bala['y'] - bala['tamaño'],
                bala['x'] + bala['tamaño'], bala['y'] + bala['tamaño']
            )
            
            if bala['y'] < -50:
                self.canvas.delete(bala['id'])
                self.balas.remove(bala)
    
    def mover_enemigos(self):
        for enemigo in self.enemigos[:]:
            enemigo['y'] += enemigo['velocidad']
            enemigo['x'] += enemigo['direccion']
            
            tamaño = enemigo['tamaño']
            
            if enemigo['x'] < tamaño or enemigo['x'] > self.ancho - tamaño:
                enemigo['direccion'] *= -1
            
            self.canvas.coords(enemigo['id'],
                enemigo['x'] - tamaño, enemigo['y'] - tamaño,
                enemigo['x'] + tamaño, enemigo['y'] + tamaño
            )
            
            # Si el enemigo pasa de la parte inferior de la pantalla, el jugador pierde vida
            if enemigo['y'] > self.alto + tamaño:
                if not self.invulnerable:
                    self.perder_vida_escape(enemigo['x'], self.alto)
                
                self.canvas.delete(enemigo['id'])
                self.enemigos.remove(enemigo)
    
    def perder_vida_escape(self, x, y):
        if not self.juego_activo:
            return
        
        self.vidas -= 1
        self.actualizar_vidas()
        
        self.crear_explosion(x, y, 30, '#ff0000')
        
        self.invulnerable = True
        self.tiempo_invulnerabilidad = time.time()
        self.efecto_invulnerabilidad()
        
        if self.vidas <= 0:
            self.game_over()
    
    def mover_boss_bullets(self):
        for bullet in self.boss_bullets[:]:
            bullet['x'] += math.cos(bullet['angulo']) * bullet['velocidad']
            bullet['y'] += math.sin(bullet['angulo']) * bullet['velocidad']
            
            tamaño = int(12 * self.escala)
            self.canvas.coords(bullet['id'],
                bullet['x'] - tamaño, bullet['y'] - tamaño,
                bullet['x'] + tamaño, bullet['y'] + tamaño
            )
            
            if (bullet['y'] > self.alto + 50 or bullet['y'] < -50 or 
                bullet['x'] < -50 or bullet['x'] > self.ancho + 50):
                self.canvas.delete(bullet['id'])
                self.boss_bullets.remove(bullet)
    
    def mover_boss_lasers(self):
        for laser in self.boss_lasers[:]:
            self.canvas.coords(laser['id'],
                laser['x'] - laser['ancho']//2, laser['y'],
                laser['x'] + laser['ancho']//2, self.alto
            )
            
            if time.time() - self.boss['ultimo_laser'] > 0.3:
                self.canvas.delete(laser['id'])
                self.boss_lasers.remove(laser)
    
    def mover_boss_bombs(self):
        tiempo_actual = time.time()
        
        for bomba in self.boss_bombs[:]:
            bomba['y'] += bomba['velocidad']
            
            tamaño = int(30 * self.escala)
            self.canvas.coords(bomba['id'],
                bomba['x'] - tamaño, bomba['y'] - tamaño,
                bomba['x'] + tamaño, bomba['y'] + tamaño
            )
            
            tiempo_restante = bomba['tiempo_impacto'] - tiempo_actual
            if tiempo_restante > 0:
                radio_alerta = tamaño * (3 - tiempo_restante)
                self.canvas.coords(bomba['indicador'],
                    bomba['x'] - radio_alerta, bomba['y'] + tamaño*3 - radio_alerta,
                    bomba['x'] + radio_alerta, bomba['y'] + tamaño*3 + radio_alerta
                )
            
            if bomba['y'] > self.alto + 100 or tiempo_actual > bomba['tiempo_impacto']:
                if tiempo_actual > bomba['tiempo_impacto']:
                    self.crear_explosion(bomba['x'], bomba['y'] + tamaño*3, 50, '#ff0000')
                self.canvas.delete(bomba['id'])
                self.canvas.delete(bomba['indicador'])
                self.boss_bombs.remove(bomba)
    
    def mover_powerups(self):
        for powerup in self.powerups[:]:
            powerup['y'] += powerup['velocidad']
            
            tamaño = powerup['tamaño']
            self.canvas.coords(powerup['id'],
                powerup['x'] - tamaño, powerup['y'] - tamaño,
                powerup['x'] + tamaño, powerup['y'] + tamaño
            )
            
            self.canvas.coords(powerup['id_simbolo'],
                powerup['x'], powerup['y']
            )
            
            if powerup['y'] > self.alto + tamaño:
                self.canvas.delete(powerup['id'])
                self.canvas.delete(powerup['id_simbolo'])
                self.powerups.remove(powerup)
    
    def crear_explosion(self, x, y, tamaño, color_base='#ffff00'):
        particulas = random.randint(3, 6)
        for _ in range(particulas):
            angulo = random.uniform(0, math.pi * 2)
            velocidad = random.uniform(1, 4)
            tamaño_part = random.uniform(3, tamaño * 0.3)
            
            color = color_base if color_base != '#ffff00' else random.choice(['#ffff00', '#ffaa00', '#ff5500'])
            
            explosion = {
                'x': x,
                'y': y,
                'dx': math.cos(angulo) * velocidad,
                'dy': math.sin(angulo) * velocidad,
                'tamaño': tamaño_part,
                'color': color,
                'vida': random.randint(10, 20),
                'id': self.canvas.create_oval(0, 0, 0, 0, fill=color, outline='')
            }
            self.explosiones.append(explosion)
    
    def actualizar_explosiones(self):
        for explosion in self.explosiones[:]:
            explosion['vida'] -= 1
            if explosion['vida'] <= 0:
                self.canvas.delete(explosion['id'])
                self.explosiones.remove(explosion)
                continue
            
            explosion['x'] += explosion['dx']
            explosion['y'] += explosion['dy']
            explosion['dx'] *= 0.9
            explosion['dy'] *= 0.9
            
            tamaño = explosion['tamaño'] * (explosion['vida'] / 20)
            self.canvas.coords(explosion['id'],
                explosion['x'] - tamaño, explosion['y'] - tamaño,
                explosion['x'] + tamaño, explosion['y'] + tamaño
            )
    
    def detectar_colision_avion_enemigo(self):
        if self.invulnerable or (self.powerup_escudo and not self.boss_active):
            return
        
        for enemigo in self.enemigos[:]:
            distancia = math.sqrt((self.avion_x - enemigo['x'])**2 + (self.avion_y - enemigo['y'])**2)
            
            if distancia < self.tamaño_avion * 0.8 + enemigo['tamaño']:
                self.perder_vida_contacto(enemigo['x'], enemigo['y'])
                
                self.crear_explosion(enemigo['x'], enemigo['y'], enemigo['tamaño'])
                
                self.canvas.delete(enemigo['id'])
                self.enemigos.remove(enemigo)
                
                break
        
        for bullet in self.boss_bullets[:]:
            distancia = math.sqrt((self.avion_x - bullet['x'])**2 + (self.avion_y - bullet['y'])**2)
            
            if distancia < self.tamaño_avion * 0.8 + 12:
                self.perder_vida_contacto(bullet['x'], bullet['y'])
                
                self.crear_explosion(bullet['x'], bullet['y'], 15)
                
                self.canvas.delete(bullet['id'])
                self.boss_bullets.remove(bullet)
        
        for laser in self.boss_lasers:
            if abs(self.avion_x - laser['x']) < 20 + self.tamaño_avion:
                self.perder_vida_contacto(laser['x'], self.avion_y)
                break
        
        for bomba in self.boss_bombs[:]:
            if time.time() > bomba['tiempo_impacto']:
                distancia = math.sqrt((self.avion_x - bomba['x'])**2 + (self.avion_y - (bomba['y'] + 90))**2)
                
                if distancia < self.tamaño_avion * 0.8 + 50:
                    self.perder_vida_contacto(bomba['x'], bomba['y'] + 90)
    
    def perder_vida_contacto(self, x, y):
        if not self.juego_activo or self.invulnerable:
            return
        
        self.vidas -= 1
        self.actualizar_vidas()
        
        self.crear_explosion(x, y, 30, '#ff0000')
        
        if self.powerup_escudo and not self.boss_active:
            self.powerup_escudo = False
            self.actualizar_indicadores_powerups()
        else:
            self.invulnerable = True
            self.tiempo_invulnerabilidad = time.time()
            self.efecto_invulnerabilidad()
        
        if self.vidas <= 0:
            self.game_over()
    
    def detectar_colisiones_balas(self):
        for bala in self.balas[:]:
            if self.boss_active:
                distancia = math.sqrt((bala['x'] - self.boss['x'])**2 + (bala['y'] - self.boss['y'])**2)
                
                if distancia < self.boss['tamaño'] + bala['tamaño']:
                    self.boss_health -= bala['daño']
                    self.actualizar_barra_boss()
                    
                    self.crear_explosion(bala['x'], bala['y'], 10)
                    
                    self.canvas.delete(bala['id'])
                    self.balas.remove(bala)
                    
                    if self.boss_health <= 0:
                        self.derrotar_boss()
                    continue
            
            for enemigo in self.enemigos[:]:
                distancia = math.sqrt((bala['x'] - enemigo['x'])**2 + (bala['y'] - enemigo['y'])**2)
                
                if distancia < enemigo['tamaño'] + bala['tamaño']:
                    enemigo['disparos_recibidos'] += 1
                    
                    self.crear_explosion(bala['x'], bala['y'], 8)
                    
                    self.canvas.delete(bala['id'])
                    self.balas.remove(bala)
                    
                    if enemigo['disparos_recibidos'] >= enemigo['disparos_necesarios']:
                        self.puntuacion += enemigo['puntos']
                        self.actualizar_puntuacion()
                        
                        self.crear_explosion(enemigo['x'], enemigo['y'], enemigo['tamaño'])
                        
                        if random.random() < 0.25 and len(self.powerups) < self.max_powerups:
                            self.crear_powerup(enemigo['x'], enemigo['y'])
                        
                        self.canvas.delete(enemigo['id'])
                        self.enemigos.remove(enemigo)
                    
                    break
    
    def detectar_colisiones_powerups(self):
        for powerup in self.powerups[:]:
            distancia = math.sqrt((powerup['x'] - self.avion_x)**2 + (powerup['y'] - self.avion_y)**2)
            
            if distancia < self.tamaño_avion * 0.8 + powerup['tamaño']:
                if self.aplicar_powerup(powerup['tipo']):
                    self.crear_explosion(powerup['x'], powerup['y'], 15, powerup['color'])
                    
                    self.canvas.delete(powerup['id'])
                    self.canvas.delete(powerup['id_simbolo'])
                    self.powerups.remove(powerup)
    
    def actualizar_puntuacion(self):
        self.canvas.itemconfig(self.texto_puntuacion,
                              text=f"SCORE: {self.puntuacion:06d}")
        
        if self.puntuacion > self.record:
            self.record = self.puntuacion
            self.canvas.itemconfig(self.texto_record,
                                  text=f"BEST: {self.record:06d}")
    
    def actualizar_vidas(self):
        for corazon in self.corazones:
            self.canvas.delete(corazon)
        self.corazones = []
        
        tamaño = int(25 * self.escala)
        for i in range(3):
            x = int(200 * self.escala) + i * (tamaño + 10)
            y = int(30 * self.escala)
            
            color = '#ff5555' if i < self.vidas else '#555555'
            corazon = self.canvas.create_text(x, y, text='♥',
                                             fill=color,
                                             font=('Arial', int(25 * self.escala)),
                                             tags='interfaz')
            self.corazones.append(corazon)
    
    def efecto_invulnerabilidad(self):
        def parpadear(veces):
            if veces > 0 and self.invulnerable:
                if veces % 2 == 0:
                    self.canvas.itemconfig('avion', state='hidden')
                else:
                    self.canvas.itemconfig('avion', state='normal')
                self.root.after(80, lambda: parpadear(veces - 1))
            else:
                self.canvas.itemconfig('avion', state='normal')
        
        parpadear(10)
    
    def derrotar_boss(self):
        self.puntuacion += self.nivel * 1000
        self.actualizar_puntuacion()
        
        self.crear_explosion(self.boss['x'], self.boss['y'], 100, '#ffff00')
        
        self.canvas.delete(self.boss['id'])
        self.canvas.delete(self.barra_boss_fondo)
        self.canvas.delete(self.barra_boss_vida)
        self.canvas.delete(self.texto_boss)
        
        for bullet in self.boss_bullets:
            self.canvas.delete(bullet['id'])
        self.boss_bullets.clear()
        
        for laser in self.boss_lasers:
            self.canvas.delete(laser['id'])
        self.boss_lasers.clear()
        
        for bomba in self.boss_bombs:
            self.canvas.delete(bomba['id'])
            self.canvas.delete(bomba['indicador'])
        self.boss_bombs.clear()
        
        self.boss_active = False
        
        self.nivel += 1
        if self.nivel > self.nivel_maximo:
            self.nivel = self.nivel_maximo
            self.victoria()
        else:
            self.enemigos_restantes = self.enemigos_por_nivel
            self.enemigos_creados = 0
            self.actualizar_contador_enemigos()
            self.mostrar_mensaje_nivel()
    
    def mostrar_mensaje_nivel(self):
        color_nivel = self.colores[f'nivel{min(self.nivel, 5)}']
        mensaje = self.canvas.create_text(
            self.ancho // 2, self.alto // 3,
            text=f"LEVEL {self.nivel}!",
            fill=color_nivel,
            font=('Arial', int(50 * self.escala), 'bold'),
            tags='mensaje'
        )
        
        self.root.after(1500, lambda: self.canvas.delete('mensaje'))
    
    def game_over(self):
        self.juego_activo = False
        
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto,
                                    fill='#000000', stipple='gray25',
                                    tags='gameover')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2 - 60,
                              text="GAME OVER",
                              fill='#ff0000',
                              font=('Arial', int(70 * self.escala), 'bold'),
                              tags='gameover')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2,
                              text=f"FINAL SCORE: {self.puntuacion:06d}",
                              fill='#ffffff',
                              font=('Courier', int(40 * self.escala)),
                              tags='gameover')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2 + 50,
                              text=f"LEVEL REACHED: {self.nivel}",
                              fill=self.colores[f'nivel{min(self.nivel, 5)}'],
                              font=('Arial', int(30 * self.escala)),
                              tags='gameover')
        
        btn_reiniciar = tk.Button(self.root, text="PLAY AGAIN",
                                 command=self.reiniciar_juego,
                                 bg='#ff5555', fg='white',
                                 font=('Arial', int(18 * self.escala), 'bold'),
                                 relief='raised', padx=25, pady=12,
                                 cursor='hand2')
        
        btn_menu = tk.Button(self.root, text="MENÚ PRINCIPAL",
                            command=self.salir_al_menu,
                            bg='#5555ff', fg='white',
                            font=('Arial', int(18 * self.escala), 'bold'),
                            relief='raised', padx=25, pady=12,
                            cursor='hand2')
        
        self.canvas.create_window(self.ancho // 2 - 120, self.alto // 2 + 120,
                                 window=btn_reiniciar, tags='gameover')
        self.canvas.create_window(self.ancho // 2 + 120, self.alto // 2 + 120,
                                 window=btn_menu, tags='gameover')
    
    def victoria(self):
        self.juego_activo = False
        
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto,
                                    fill='#000000', stipple='gray25',
                                    tags='victoria')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2 - 60,
                              text="VICTORY!",
                              fill='#00ff00',
                              font=('Arial', int(70 * self.escala), 'bold'),
                              tags='victoria')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2,
                              text=f"FINAL SCORE: {self.puntuacion:06d}",
                              fill='#ffffff',
                              font=('Courier', int(40 * self.escala)),
                              tags='victoria')
        
        self.canvas.create_text(self.ancho // 2, self.alto // 2 + 50,
                              text="ALL BOSSES DEFEATED!",
                              fill='#ffff00',
                              font=('Arial', int(30 * self.escala)),
                              tags='victoria')
        
        btn_reiniciar = tk.Button(self.root, text="PLAY AGAIN",
                                 command=self.reiniciar_juego,
                                 bg='#ff5555', fg='white',
                                 font=('Arial', int(18 * self.escala), 'bold'),
                                 relief='raised', padx=25, pady=12,
                                 cursor='hand2')
        
        btn_menu = tk.Button(self.root, text="MENÚ PRINCIPAL",
                            command=self.salir_al_menu,
                            bg='#5555ff', fg='white',
                            font=('Arial', int(18 * self.escala), 'bold'),
                            relief='raised', padx=25, pady=12,
                            cursor='hand2')
        
        self.canvas.create_window(self.ancho // 2 - 120, self.alto // 2 + 120,
                                 window=btn_reiniciar, tags='victoria')
        self.canvas.create_window(self.ancho // 2 + 120, self.alto // 2 + 120,
                                 window=btn_menu, tags='victoria')
    
    def reiniciar_juego(self):
        self.canvas.delete("all")
        
        self.juego_activo = True
        self.pausado = False
        self.boss_active = False
        self.en_menu_principal = False
        
        self.puntuacion = 0
        self.vidas = 3
        self.nivel = 1
        self.velocidad_juego = 1.0
        self.velocidad_avion = 12 * self.escala
        self.invulnerable = False
        self.efecto_especial = False
        
        self.powerup_disparo = False
        self.powerup_velocidad = False
        self.powerup_escudo = False
        self.powerup_laser = False
        self.powerup_vida = False
        
        self.balas_actuales = 6
        self.recarga_activa = False
        self.tiempo_recarga_actual = self.tiempo_recarga_base
        self.tiempo_ultimo_disparo = 0
        self.ultima_recarga = 0
        self.ultimo_enemigo = time.time()
        
        self.avion_x = self.ancho // 2
        self.avion_y = self.alto - 100
        
        self.balas.clear()
        self.enemigos.clear()
        self.explosiones.clear()
        self.powerups.clear()
        self.efectos.clear()
        self.estrellas.clear()
        self.boss_bullets.clear()
        self.boss_lasers.clear()
        self.boss_bombs.clear()
        self.teclas_presionadas.clear()
        
        self.enemigos_restantes = self.enemigos_por_nivel
        self.enemigos_creados = 0
        
        self.inicializar_juego()
    
    def pausar_juego(self, event=None):
        if not self.juego_activo:
            return
            
        self.pausado = not self.pausado
        
        if self.pausado:
            self.canvas.create_text(self.ancho // 2, self.alto // 2,
                                  text="PAUSED",
                                  fill='#ffff00',
                                  font=('Arial', int(60 * self.escala), 'bold'),
                                  tags='pausa')
            
            # Botón para volver al menú desde pausa
            btn_menu_pausa = tk.Button(self.root, text="MENÚ PRINCIPAL",
                                      command=self.salir_al_menu,
                                      bg='#5555ff', fg='white',
                                      font=('Arial', int(16 * self.escala), 'bold'),
                                      relief='raised', padx=20, pady=10,
                                      cursor='hand2')
            self.canvas.create_window(self.ancho // 2, self.alto // 2 + 80,
                                     window=btn_menu_pausa, tags='pausa')
        else:
            self.canvas.delete('pausa')
    
    def salir_al_menu(self, event=None):
        """Vuelve al menú principal"""
        # Limpiar todo
        self.canvas.delete("all")
        self.teclas_presionadas.clear()
        
        # Reiniciar variables del juego
        self.juego_activo = False
        self.pausado = False
        self.boss_active = False
        
        self.balas.clear()
        self.enemigos.clear()
        self.explosiones.clear()
        self.powerups.clear()
        self.efectos.clear()
        self.boss_bullets.clear()
        self.boss_lasers.clear()
        self.boss_bombs.clear()
        
        # Mostrar menú principal
        self.en_menu_principal = True
        self.mostrar_menu_principal()
    
    def salir_juego(self, event=None):
        """Sale completamente del juego"""
        if messagebox.askyesno("Salir", "¿Estás seguro de que quieres salir del juego?"):
            self.root.quit()
            self.root.destroy()
    
    def toggle_fullscreen(self, event=None):
        self.fullscreen = not self.fullscreen
        self.root.attributes('-fullscreen', self.fullscreen)
        
        if not self.fullscreen:
            self.root.geometry(f"{self.ancho}x{self.alto}")
            # Centrar ventana
            self.root.update_idletasks()
            x = (self.ancho_pantalla - self.ancho) // 2
            y = (self.alto_pantalla - self.alto) // 2
            self.root.geometry(f"{self.ancho}x{self.alto}+{x}+{y}")
    
    def generar_enemigo_solitario(self):
        if self.boss_active or not self.juego_activo:
            return
        
        tiempo_actual = time.time()
        
        # Solo crear un enemigo si han pasado 0.6 segundos desde el último
        if tiempo_actual - self.ultimo_enemigo > self.tiempo_entre_enemigos:
            # Solo crear si hay menos de 4 enemigos en pantalla y quedan enemigos por crear
            if len(self.enemigos) < self.max_enemigos_simultaneos and self.enemigos_restantes > 0:
                self.crear_enemigo_nivel()
                self.ultimo_enemigo = tiempo_actual
            
            # Si no quedan enemigos por crear y todos han sido eliminados, pasar al siguiente nivel o boss
            if self.enemigos_restantes <= 0 and len(self.enemigos) == 0 and not self.boss_active:
                if self.nivel % 3 == 0:
                    # Cada 3 niveles aparece un boss
                    self.crear_boss()
                else:
                    # Pasar al siguiente nivel
                    self.nivel += 1
                    if self.nivel > self.nivel_maximo:
                        self.victoria()
                    else:
                        self.enemigos_restantes = self.enemigos_por_nivel
                        self.enemigos_creados = 0
                        self.actualizar_contador_enemigos()
                        self.mostrar_mensaje_nivel()
    
    def ciclo_juego(self):
        if not self.juego_activo or self.pausado:
            self.root.after(33, self.ciclo_juego)
            return
        
        self.generar_enemigo_solitario()
        
        self.mover_avion()
        self.actualizar_elementos()
        self.mover_enemigos()
        
        if self.boss_active:
            self.mover_boss()
            self.mover_boss_bullets()
            self.mover_boss_lasers()
            self.mover_boss_bombs()
            self.actualizar_barra_boss()
        
        self.mover_powerups()
        self.actualizar_explosiones()
        
        self.detectar_colision_avion_enemigo()
        self.detectar_colisiones_balas()
        self.detectar_colisiones_powerups()
        
        self.root.after(33, self.ciclo_juego)
    
    def inicializar_juego(self):
        """Inicializa todos los elementos del juego"""
        self.crear_fondo_estrellado()
        self.crear_interfaz()
        self.dibujar_avion()
        self.crear_barra_recarga()
        self.crear_indicadores_powerups()
        self.enemigos_restantes = self.enemigos_por_nivel
        self.enemigos_creados = 0
        self.iniciar_ciclo_juego()
    
    def iniciar_ciclo_juego(self):
        self.ciclo_juego()

if __name__ == "__main__":
    root = tk.Tk()
    juego = Mundoroto(root)
    root.mainloop()