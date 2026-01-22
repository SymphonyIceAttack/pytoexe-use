import tkinter as tk
import random
from math import sqrt, cos, sin, radians

class JuegoBolita:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Bolita en Circuitos - Mejorado")
        
        # Obtener dimensiones de pantalla
        self.ancho_pantalla = self.ventana.winfo_screenwidth()
        self.alto_pantalla = self.ventana.winfo_screenheight()
        
        # Dimensiones del juego (80% de la pantalla)
        self.ancho = int(self.ancho_pantalla * 0.8)
        self.alto = int(self.alto_pantalla * 0.8)
        
        # Centrar ventana
        x = (self.ancho_pantalla - self.ancho) // 2
        y = (self.alto_pantalla - self.alto) // 2
        self.ventana.geometry(f"{self.ancho}x{self.alto}+{x}+{y}")
        
        # Variables del juego
        self.velocidad_normal = 6
        self.velocidad_carrera = 10
        self.velocidad_actual = self.velocidad_normal
        self.puntos = 0
        self.nivel = 1
        self.vidas = 3
        self.juego_activo = False
        self.pausado = False
        self.en_menu = True
        self.en_game_over = False
        self.tiene_llave = False
        
        # Sistema de energía para correr
        self.energia_maxima = 100
        self.energia_actual = self.energia_maxima
        self.recarga_energia = 0.5
        self.gasto_energia = 1.5
        self.corriendo = False
        
        # Sistema de partículas
        self.particulas = []
        self.max_particulas = 20
        self.tiempo_particula = 0
        
        # Sistema de explosiones
        self.explosion_activa = False
        self.explosion_particulas = []
        self.explosion_timer = None
        
        # Selección de personaje
        self.personajes = [
            {"nombre": "Bolita Roja", "color": "#FF6B6B", "radio": 20},
            {"nombre": "Bolita Azul", "color": "#4ECDC4", "radio": 18},
            {"nombre": "Bolita Verde", "color": "#6BFF6B", "radio": 22},
            {"nombre": "Bolita Amarilla", "color": "#FFD166", "radio": 19},
            {"nombre": "Bolita Rosa", "color": "#FF6BFF", "radio": 21}
        ]
        self.personaje_actual = 0
        
        # Colores
        self.color_fondo = "#1A1A2E"
        self.color_meta = "#FFD166"
        self.color_texto = "#FFFFFF"
        self.color_sombra = "#333333"
        self.color_llave = "#FF6B6B"
        self.color_energia_llena = "#4ECDC4"
        self.color_energia_vacia = "#FF6B6B"
        
        # Configurar canvas
        self.canvas = tk.Canvas(
            self.ventana, 
            width=self.ancho, 
            height=self.alto,
            bg=self.color_fondo,
            highlightthickness=0
        )
        self.canvas.pack(fill="both", expand=True)
        
        # Iniciar en el menú
        self.mostrar_menu()
        
        # Configurar controles
        self.ventana.bind("<KeyPress>", self.tecla_presionada)
        self.ventana.bind("<KeyRelease>", self.tecla_soltada)
        
        # Variables de movimiento
        self.mover_izquierda = False
        self.mover_derecha = False
        self.mover_arriba = False
        self.mover_abajo = False
        
        # Referencias a elementos del juego
        self.obstaculos = []
        self.llave = None
        
    def mostrar_menu(self):
        """Muestra el menú principal"""
        self.en_menu = True
        self.juego_activo = False
        self.en_game_over = False
        self.canvas.delete("all")
        
        # Título
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.2,
            text="🎮 BOLITA EN CIRCUITOS 🎮",
            fill="#FF6B6B",
            font=("Arial", 36, "bold"),
            justify="center"
        )
        
        # Selección de personaje
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.35,
            text="SELECCIONA TU PERSONAJE",
            fill=self.color_texto,
            font=("Arial", 20, "bold"),
            justify="center"
        )
        
        # Dibujar personajes
        personaje_width = 100
        start_x = self.ancho // 2 - (len(self.personajes) * personaje_width) // 2
        
        self.personaje_rects = []
        for i, personaje in enumerate(self.personajes):
            x = start_x + i * personaje_width + personaje_width // 2
            y = self.alto * 0.45
            
            # Dibujar personaje
            radio = personaje["radio"]
            borde_color = "white" if i == self.personaje_actual else self.color_fondo
            
            self.canvas.create_oval(
                x - radio - 5, y - radio - 5,
                x + radio + 5, y + radio + 5,
                fill=borde_color,
                outline=borde_color,
                width=2,
                tags=f"personaje_{i}"
            )
            
            self.canvas.create_oval(
                x - radio, y - radio,
                x + radio, y + radio,
                fill=personaje["color"],
                outline=personaje["color"],
                tags=f"personaje_{i}"
            )
            
            texto_color = "white" if i == self.personaje_actual else "#888888"
            self.canvas.create_text(
                x, y + radio + 20,
                text=personaje["nombre"],
                fill=texto_color,
                font=("Arial", 10, "bold"),
                tags=f"personaje_{i}"
            )
            
            self.personaje_rects.append({
                "x1": x - radio - 15,
                "y1": y - radio - 15,
                "x2": x + radio + 15,
                "y2": y + radio + 40,
                "index": i
            })
        
        # Controles
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.55,
            text="← → Flechas para cambiar personaje",
            fill="#888888",
            font=("Arial", 12),
            justify="center"
        )
        
        # Botón de jugar
        btn_jugar_x1 = self.ancho // 2 - 100
        btn_jugar_y1 = self.alto * 0.65
        btn_jugar_x2 = self.ancho // 2 + 100
        btn_jugar_y2 = self.alto * 0.65 + 50
        
        self.btn_jugar_id = self.canvas.create_rectangle(
            btn_jugar_x1, btn_jugar_y1,
            btn_jugar_x2, btn_jugar_y2,
            fill="#4ECDC4",
            outline="white",
            width=2,
            tags="btn_jugar"
        )
        
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.65 + 25,
            text="🎮 JUGAR 🎮",
            fill="white",
            font=("Arial", 20, "bold"),
            tags="btn_jugar_text"
        )
        
        # Instrucciones
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.85,
            text="CONTROLES:\n← → ↑ ↓ o WASD: Mover\nQ: Correr (usa energía)\nP o Espacio: Pausa\nR: Reiniciar\nESC: Menú",
            fill="#888888",
            font=("Arial", 12),
            justify="center"
        )
        
        # Vincular clics
        self.canvas.tag_bind("btn_jugar", "<Button-1>", lambda e: self.iniciar_juego())
        self.canvas.tag_bind("btn_jugar_text", "<Button-1>", lambda e: self.iniciar_juego())
        
        for i in range(len(self.personajes)):
            self.canvas.tag_bind(f"personaje_{i}", "<Button-1>", 
                                lambda e, idx=i: self.seleccionar_personaje(idx))
    
    def seleccionar_personaje(self, index):
        """Selecciona un personaje"""
        self.personaje_actual = index
        self.actualizar_seleccion_personaje()
    
    def actualizar_seleccion_personaje(self):
        """Actualiza la visualización de la selección de personaje"""
        for i in range(len(self.personajes)):
            items = self.canvas.find_withtag(f"personaje_{i}")
            for item in items:
                item_type = self.canvas.type(item)
                if item_type == "oval":
                    coords = self.canvas.coords(item)
                    size = coords[2] - coords[0]
                    if size > 40:  # Es el borde exterior
                        if i == self.personaje_actual:
                            self.canvas.itemconfig(item, fill="white", outline="white")
                        else:
                            self.canvas.itemconfig(item, fill=self.color_fondo, outline=self.color_fondo)
                elif item_type == "text":
                    if i == self.personaje_actual:
                        self.canvas.itemconfig(item, fill="white")
                    else:
                        self.canvas.itemconfig(item, fill="#888888")
    
    def iniciar_juego(self):
        """Inicia el juego desde el menú"""
        print("INICIANDO JUEGO...")
        
        # Cancelar timers
        if self.explosion_timer:
            self.ventana.after_cancel(self.explosion_timer)
            self.explosion_timer = None
        
        self.en_menu = False
        self.juego_activo = True
        self.pausado = False
        self.en_game_over = False
        self.puntos = 0
        self.nivel = 1
        self.vidas = 3
        self.tiene_llave = False
        self.explosion_activa = False
        
        # Resetear sistemas
        self.energia_actual = self.energia_maxima
        self.corriendo = False
        self.velocidad_actual = self.velocidad_normal
        self.particulas = []
        self.explosion_particulas = []
        
        # Resetear controles
        self.mover_izquierda = False
        self.mover_derecha = False
        self.mover_arriba = False
        self.mover_abajo = False
        
        # Configurar personaje
        personaje = self.personajes[self.personaje_actual]
        self.color_bolita = personaje["color"]
        self.radio_bolita = personaje["radio"]
        self.color_obstaculo = "#4ECDC4" if self.color_bolita != "#4ECDC4" else "#FF6B6B"
        
        # Crear elementos
        self.crear_bolita()
        self.crear_meta()
        self.crear_llave()
        self.obstaculos = []
        self.crear_obstaculos()
        
        # Iniciar bucle
        self.actualizar_juego()
    
    def crear_bolita(self):
        """Crea la bolita del jugador"""
        self.bolita = {
            'x': self.ancho // 2,
            'y': self.alto - 100,
            'radio': self.radio_bolita,
            'color': self.color_bolita,
            'alpha': 1.0
        }
    
    def crear_meta(self):
        """Crea la meta (ahora es una bandera)"""
        self.meta = {
            'x': self.ancho // 2,
            'y': 80,
            'radio': 25,  # Radio para colisiones
            'emoji': "🏁"  # Emoji de bandera
        }
    
    def crear_llave(self):
        """Crea una llave para el nivel 10"""
        if self.nivel >= 10:
            self.llave = {
                'x': random.randint(150, self.ancho - 150),
                'y': random.randint(200, self.alto - 200),
                'radio': 15,
                'color': self.color_llave,
                'recolectada': False,
                'emoji': "🔑"
            }
        else:
            self.llave = None
    
    def crear_obstaculos(self):
        """Crea obstáculos para el nivel actual"""
        self.obstaculos.clear()
        num_obstaculos = min(5 + self.nivel * 2, 15)
        
        spawn_seguro = {
            'x': self.ancho // 2,
            'y': self.alto - 100,
            'radio': self.radio_bolita + 50
        }
        
        for _ in range(num_obstaculos):
            intentos = 0
            obstaculo_creado = False
            
            while intentos < 30 and not obstaculo_creado:
                tipo = random.choice(["rectangulo", "circulo", "linea"])
                distancia_minima = 200
                
                if tipo == "rectangulo":
                    x = random.randint(100, self.ancho - 100)
                    y = random.randint(150, self.alto - 150)
                    ancho = random.randint(40, 80)
                    alto = random.randint(40, 80)
                    
                    distancia_x = abs(x - spawn_seguro['x'])
                    distancia_y = abs(y - spawn_seguro['y'])
                    distancia_total = sqrt(distancia_x**2 + distancia_y**2)
                    
                    if distancia_total > distancia_minima:
                        obstaculo = {
                            'tipo': 'rectangulo',
                            'x': x, 'y': y,
                            'ancho': ancho, 'alto': alto,
                            'vel_x': random.uniform(-2, 2) * (self.nivel * 0.5),
                            'vel_y': random.uniform(-2, 2) * (self.nivel * 0.5),
                            'emoji': random.choice(["🟥", "🟦", "🟩", "🟨"])
                        }
                        obstaculo_creado = True
                            
                elif tipo == "circulo":
                    x = random.randint(100, self.ancho - 100)
                    y = random.randint(150, self.alto - 150)
                    radio = random.randint(25, 40)
                    
                    distancia = sqrt((x - spawn_seguro['x'])**2 + (y - spawn_seguro['y'])**2)
                    
                    if distancia > distancia_minima + radio + spawn_seguro['radio']:
                        obstaculo = {
                            'tipo': 'circulo',
                            'x': x, 'y': y,
                            'radio': radio,
                            'vel_x': random.uniform(-2, 2) * (self.nivel * 0.5),
                            'vel_y': random.uniform(-2, 2) * (self.nivel * 0.5),
                            'emoji': random.choice(["🔴", "🔵", "🟢", "🟡"])
                        }
                        obstaculo_creado = True
                        
                else:  # linea
                    x1 = random.randint(100, self.ancho - 200)
                    y1 = random.randint(150, self.alto - 150)
                    x2 = x1 + random.randint(80, 150)
                    y2 = y1 + random.randint(-50, 50)
                    
                    distancia_p1 = sqrt((x1 - spawn_seguro['x'])**2 + (y1 - spawn_seguro['y'])**2)
                    distancia_p2 = sqrt((x2 - spawn_seguro['x'])**2 + (y2 - spawn_seguro['y'])**2)
                    
                    if distancia_p1 > distancia_minima and distancia_p2 > distancia_minima:
                        obstaculo = {
                            'tipo': 'linea',
                            'x1': x1, 'y1': y1,
                            'x2': x2, 'y2': y2,
                            'vel_x': random.uniform(-1, 1) * (self.nivel * 0.3),
                            'vel_y': random.uniform(-1, 1) * (self.nivel * 0.3),
                            'emoji': "➖"
                        }
                        obstaculo_creado = True
                
                intentos += 1
            
            if not obstaculo_creado:
                cuadrantes = [
                    (100, 100, self.ancho//2 - 50, self.alto//2 - 50),
                    (self.ancho//2 + 50, 100, self.ancho - 100, self.alto//2 - 50),
                    (100, self.alto//2 + 50, self.ancho//2 - 50, self.alto - 100),
                ]
                
                cuadrante = random.choice(cuadrantes)
                x = random.randint(int(cuadrante[0]), int(cuadrante[2]))
                y = random.randint(int(cuadrante[1]), int(cuadrante[3]))
                
                if tipo == "rectangulo":
                    obstaculo = {
                        'tipo': 'rectangulo',
                        'x': x, 'y': y,
                        'ancho': random.randint(40, 80),
                        'alto': random.randint(40, 80),
                        'vel_x': random.uniform(-2, 2) * (self.nivel * 0.5),
                        'vel_y': random.uniform(-2, 2) * (self.nivel * 0.5),
                        'emoji': random.choice(["🟥", "🟦", "🟩", "🟨"])
                    }
                elif tipo == "circulo":
                    obstaculo = {
                        'tipo': 'circulo',
                        'x': x, 'y': y,
                        'radio': random.randint(25, 40),
                        'vel_x': random.uniform(-2, 2) * (self.nivel * 0.5),
                        'vel_y': random.uniform(-2, 2) * (self.nivel * 0.5),
                        'emoji': random.choice(["🔴", "🔵", "🟢", "🟡"])
                    }
                else:
                    obstaculo = {
                        'tipo': 'linea',
                        'x1': x, 'y1': y,
                        'x2': x + random.randint(80, 150),
                        'y2': y + random.randint(-50, 50),
                        'vel_x': random.uniform(-1, 1) * (self.nivel * 0.3),
                        'vel_y': random.uniform(-1, 1) * (self.nivel * 0.3),
                        'emoji': "➖"
                    }
            
            obstaculo['color'] = self.color_obstaculo
            self.obstaculos.append(obstaculo)
    
    def crear_particula(self, x, y, color=None, es_explosion=False):
        """Crea una nueva partícula"""
        if not color:
            color = self.color_bolita
            
        if es_explosion:
            # Partículas de explosión
            particula = {
                'x': x,
                'y': y,
                'radio': random.randint(3, 8),
                'color': random.choice(["#FF6B6B", "#FFD166", "#4ECDC4", "#FFFFFF"]),
                'vel_x': random.uniform(-8, 8),
                'vel_y': random.uniform(-8, 8),
                'vida': random.randint(30, 60),
                'alpha': 1.0,
                'es_explosion': True
            }
        else:
            # Partículas normales de movimiento
            dx = 0
            dy = 0
            if self.mover_izquierda: dx += 1
            if self.mover_derecha: dx -= 1
            if self.mover_arriba: dy += 1
            if self.mover_abajo: dy -= 1
            
            if dx == 0 and dy == 0:
                return None
                
            magnitud = sqrt(dx*dx + dy*dy)
            if magnitud > 0:
                dx /= magnitud
                dy /= magnitud
            
            particula = {
                'x': x + dx * self.bolita['radio'],
                'y': y + dy * self.bolita['radio'],
                'radio': random.randint(2, 5),
                'color': color,
                'vel_x': -dx * random.uniform(1, 3),
                'vel_y': -dy * random.uniform(1, 3),
                'vida': random.randint(20, 40),
                'alpha': 1.0,
                'es_explosion': False
            }
        
        return particula
    
    def crear_explosion_obstaculo(self, x, y):
        """Crea una explosión en la posición de un obstáculo"""
        for _ in range(30):  # Muchas partículas para explosión
            particula = self.crear_particula(x, y, es_explosion=True)
            if particula:
                self.explosion_particulas.append(particula)
    
    def crear_explosion_pantalla_completa(self):
        """Crea una explosión que cubre toda la pantalla"""
        for _ in range(100):  # Muchas partículas por toda la pantalla
            x = random.randint(0, self.ancho)
            y = random.randint(0, self.alto)
            particula = self.crear_particula(x, y, es_explosion=True)
            if particula:
                self.explosion_particulas.append(particula)
    
    def actualizar_particulas(self):
        """Actualiza todas las partículas"""
        # Partículas normales
        particulas_vivas = []
        for particula in self.particulas:
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 1
            particula['alpha'] = particula['vida'] / 40.0
            particula['vel_x'] *= 0.95
            particula['vel_y'] *= 0.95
            
            if particula['vida'] > 0:
                particulas_vivas.append(particula)
        self.particulas = particulas_vivas
        
        # Partículas de explosión
        explosion_vivas = []
        for particula in self.explosion_particulas:
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 1
            particula['alpha'] = particula['vida'] / 60.0
            
            # Las explosiones no tienen rozamiento, solo gravedad
            particula['vel_y'] += 0.2  # Gravedad
            
            if particula['vida'] > 0:
                explosion_vivas.append(particula)
        self.explosion_particulas = explosion_vivas
        
        # Crear nuevas partículas de movimiento
        if (self.mover_izquierda or self.mover_derecha or 
            self.mover_arriba or self.mover_abajo):
            self.tiempo_particula += 1
            if self.tiempo_particula >= (2 if self.corriendo else 4):
                particula = self.crear_particula(self.bolita['x'], self.bolita['y'])
                if particula:
                    self.particulas.append(particula)
                self.tiempo_particula = 0
    
    def dibujar_particulas(self):
        """Dibuja todas las partículas"""
        for particula in self.particulas + self.explosion_particulas:
            alpha = max(0, min(1, particula['alpha']))
            color = self.canvas.winfo_rgb(particula['color'])
            r = int(color[0] / 256 * alpha)
            g = int(color[1] / 256 * alpha)
            b = int(color[2] / 256 * alpha)
            color_alpha = f'#{r:02x}{g:02x}{b:02x}'
            
            self.canvas.create_oval(
                particula['x'] - particula['radio'],
                particula['y'] - particula['radio'],
                particula['x'] + particula['radio'],
                particula['y'] + particula['radio'],
                fill=color_alpha,
                outline=""
            )
    
    def actualizar_energia(self):
        """Actualiza la barra de energía"""
        if not self.juego_activo or self.pausado:
            return
            
        if self.corriendo:
            self.energia_actual -= self.gasto_energia
            if self.energia_actual <= 0:
                self.energia_actual = 0
                self.corriendo = False
                self.velocidad_actual = self.velocidad_normal
        else:
            if self.energia_actual < self.energia_maxima:
                self.energia_actual += self.recarga_energia
                if self.energia_actual > self.energia_maxima:
                    self.energia_actual = self.energia_maxima
    
    def dibujar_interfaz_juego(self):
        """Dibuja la interfaz del juego"""
        self.canvas.delete("all")
        
        # Dibujar fondo
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto, fill=self.color_fondo, outline="")
        
        # Dibujar partículas (primero para que estén detrás)
        self.dibujar_particulas()
        
        # Dibujar meta (bandera)
        self.dibujar_meta()
        
        # Dibujar llave si existe
        if self.llave and not self.llave['recolectada']:
            self.dibujar_llave()
        
        # Dibujar obstáculos (con emojis)
        self.dibujar_obstaculos()
        
        # Dibujar bolita (con efecto de desvanecimiento si es necesario)
        self.dibujar_bolita()
        
        # Panel de información
        self.dibujar_panel_informacion()
        
        # Barra de energía
        self.dibujar_barra_energia()
    
    def dibujar_panel_informacion(self):
        """Dibuja el panel de información"""
        self.canvas.create_rectangle(
            10, 10, 350, 60,
            fill="#000000",
            outline="white",
            width=2
        )
        
        self.canvas.create_text(
            60, 25,
            text=f"Puntos: {self.puntos}",
            fill=self.color_texto,
            font=("Arial", 14, "bold")
        )
        
        self.canvas.create_text(
            60, 45,
            text=f"Nivel: {self.nivel}",
            fill=self.color_texto,
            font=("Arial", 14, "bold")
        )
        
        self.canvas.create_text(
            200, 25,
            text=f"Vidas: {self.vidas}",
            fill=self.color_texto,
            font=("Arial", 14, "bold")
        )
        
        # Corazones
        for i in range(min(self.vidas, 5)):
            x = 200 + (i * 30)
            y = 45
            self.canvas.create_text(
                x, y,
                text="❤️",
                fill="#FF6B6B",
                font=("Arial", 16)
            )
        
        # Icono de llave
        if self.nivel >= 10:
            x_llave = 300
            y_llave = 25
            
            if self.tiene_llave:
                self.canvas.create_text(
                    x_llave, y_llave,
                    text="🗝️✅",
                    fill="#6BFF6B",
                    font=("Arial", 16)
                )
            else:
                self.canvas.create_text(
                    x_llave, y_llave,
                    text="🗝️❌",
                    fill="#888888",
                    font=("Arial", 16)
                )
    
    def dibujar_barra_energia(self):
        """Dibuja la barra de energía"""
        barra_x = 10
        barra_y = 70
        barra_ancho = 200
        barra_alto = 20
        
        # Fondo
        self.canvas.create_rectangle(
            barra_x, barra_y,
            barra_x + barra_ancho, barra_y + barra_alto,
            fill="#333333",
            outline="white",
            width=1
        )
        
        # Energía
        energia_porcentaje = self.energia_actual / self.energia_maxima
        energia_ancho = barra_ancho * energia_porcentaje
        
        if energia_porcentaje > 0.5:
            color_energia = self.color_energia_llena
        elif energia_porcentaje > 0.2:
            color_energia = "#FFD166"
        else:
            color_energia = self.color_energia_vacia
        
        self.canvas.create_rectangle(
            barra_x, barra_y,
            barra_x + energia_ancho, barra_y + barra_alto,
            fill=color_energia,
            outline=""
        )
        
        # Texto
        self.canvas.create_text(
            barra_x + barra_ancho // 2,
            barra_y + barra_alto // 2,
            text=f"ENERGÍA: {int(self.energia_actual)}%",
            fill="white",
            font=("Arial", 10, "bold")
        )
        
        # Modo
        modo = "🏃 CORRIENDO" if self.corriendo else "🚶 CAMINANDO"
        color_modo = "#FF6B6B" if self.corriendo else "#4ECDC4"
        
        self.canvas.create_text(
            barra_x + barra_ancho + 80,
            barra_y + barra_alto // 2,
            text=modo,
            fill=color_modo,
            font=("Arial", 10, "bold")
        )
    
    def dibujar_bolita(self):
        """Dibuja la bolita"""
        x, y, r = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        alpha = self.bolita['alpha']
        
        # Calcular color con alpha
        color = self.canvas.winfo_rgb(self.bolita['color'])
        r_color = int(color[0] / 256 * alpha)
        g_color = int(color[1] / 256 * alpha)
        b_color = int(color[2] / 256 * alpha)
        color_alpha = f'#{r_color:02x}{g_color:02x}{b_color:02x}'
        
        # Sombra (también con alpha)
        shadow_alpha = alpha * 0.7
        r_shadow = int(51 * shadow_alpha)  # #333333 = rgb(51,51,51)
        shadow_color = f'#{r_shadow:02x}{r_shadow:02x}{r_shadow:02x}'
        
        self.canvas.create_oval(
            x - r + 3, y - r + 3,
            x + r + 3, y + r + 3,
            fill=shadow_color,
            outline=shadow_color
        )
        
        # Bolita principal
        self.canvas.create_oval(
            x - r, y - r,
            x + r, y + r,
            fill=color_alpha,
            outline="white",
            width=2
        )
        
        # Efecto de velocidad
        if self.corriendo:
            for i in range(3):
                offset = i * 3
                self.canvas.create_oval(
                    x - r - offset, y - r - offset,
                    x + r + offset, y + r + offset,
                    outline="#FFD166",
                    width=1
                )
    
    def dibujar_meta(self):
        """Dibuja la meta (bandera)"""
        x, y = self.meta['x'], self.meta['y']
        emoji = self.meta['emoji']
        
        # Bandera con efecto
        self.canvas.create_text(
            x, y,
            text=emoji,
            fill="#FFD166" if self.tiene_llave or self.nivel < 10 else "#888888",
            font=("Arial", 48)
        )
        
        # Base de la bandera
        self.canvas.create_rectangle(
            x - 5, y + 20,
            x + 5, y + 50,
            fill="#8B4513",  # Marrón
            outline=""
        )
        
        # Texto "META"
        texto = "🏁 META ABIERTA 🏁" if self.tiene_llave or self.nivel < 10 else "🏁 META CERRADA 🏁"
        color_texto = "#FFD166" if self.tiene_llave or self.nivel < 10 else "#888888"
        
        self.canvas.create_text(
            x, y - 40,
            text=texto,
            fill=color_texto,
            font=("Arial", 14, "bold")
        )
    
    def dibujar_llave(self):
        """Dibuja la llave"""
        x, y = self.llave['x'], self.llave['y']
        
        self.canvas.create_text(
            x, y,
            text=self.llave['emoji'],
            fill=self.llave['color'],
            font=("Arial", 32)
        )
        
        # Efecto brillante
        for i in range(2):
            offset = i * 2
            self.canvas.create_text(
                x, y,
                text="✨",
                fill="#FFD166",
                font=("Arial", 16)
            )
    
    def dibujar_obstaculos(self):
        """Dibuja todos los obstáculos"""
        for obstaculo in self.obstaculos:
            if obstaculo['tipo'] == 'rectangulo':
                # Fondo del obstáculo
                self.canvas.create_rectangle(
                    obstaculo['x'] - obstaculo['ancho']//2,
                    obstaculo['y'] - obstaculo['alto']//2,
                    obstaculo['x'] + obstaculo['ancho']//2,
                    obstaculo['y'] + obstaculo['alto']//2,
                    fill=obstaculo['color'],
                    outline="white",
                    width=2
                )
                # Emoji encima
                self.canvas.create_text(
                    obstaculo['x'], obstaculo['y'],
                    text=obstaculo['emoji'],
                    fill="black",
                    font=("Arial", 20)
                )
                
            elif obstaculo['tipo'] == 'circulo':
                # Fondo del obstáculo
                self.canvas.create_oval(
                    obstaculo['x'] - obstaculo['radio'],
                    obstaculo['y'] - obstaculo['radio'],
                    obstaculo['x'] + obstaculo['radio'],
                    obstaculo['y'] + obstaculo['radio'],
                    fill=obstaculo['color'],
                    outline="white",
                    width=2
                )
                # Emoji encima
                self.canvas.create_text(
                    obstaculo['x'], obstaculo['y'],
                    text=obstaculo['emoji'],
                    fill="black",
                    font=("Arial", 20)
                )
                
            else:  # linea
                self.canvas.create_line(
                    obstaculo['x1'], obstaculo['y1'],
                    obstaculo['x2'], obstaculo['y2'],
                    fill=obstaculo['color'],
                    width=4
                )
                # Emoji en el centro
                cx = (obstaculo['x1'] + obstaculo['x2']) // 2
                cy = (obstaculo['y1'] + obstaculo['y2']) // 2
                self.canvas.create_text(
                    cx, cy,
                    text=obstaculo['emoji'],
                    fill="white",
                    font=("Arial", 16)
                )
    
    def verificar_colision_llave(self):
        """Verifica si recoge la llave"""
        if not self.llave or self.llave['recolectada']:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        lx, ly = self.llave['x'], self.llave['y']
        
        distancia = sqrt((bx - lx)**2 + (by - ly)**2)
        
        if distancia <= br + 25:  # Radio aproximado del emoji
            self.llave['recolectada'] = True
            self.tiene_llave = True
            # Efecto de recolección
            self.crear_explosion_obstaculo(lx, ly)
            return True
            
        return False
    
    def actualizar_bolita(self):
        """Actualiza la posición de la bolita"""
        if not self.juego_activo or self.pausado or self.explosion_activa:
            return
        
        velocidad = self.velocidad_carrera if self.corriendo else self.velocidad_normal
        
        if self.mover_izquierda and self.bolita['x'] > self.bolita['radio']:
            self.bolita['x'] -= velocidad
        if self.mover_derecha and self.bolita['x'] < self.ancho - self.bolita['radio']:
            self.bolita['x'] += velocidad
        if self.mover_arriba and self.bolita['y'] > self.bolita['radio'] + 70:
            self.bolita['y'] -= velocidad
        if self.mover_abajo and self.bolita['y'] < self.alto - self.bolita['radio']:
            self.bolita['y'] += velocidad
    
    def mover_obstaculos(self):
        """Mueve los obstáculos"""
        if self.explosion_activa:
            return
            
        for obstaculo in self.obstaculos:
            if 'x' in obstaculo:
                obstaculo['x'] += obstaculo['vel_x']
            if 'y' in obstaculo:
                obstaculo['y'] += obstaculo['vel_y']
            
            if 'x1' in obstaculo:
                obstaculo['x1'] += obstaculo['vel_x']
                obstaculo['x2'] += obstaculo['vel_x']
                obstaculo['y1'] += obstaculo['vel_y']
                obstaculo['y2'] += obstaculo['vel_y']
            
            if 'x' in obstaculo:
                radio_ancho = obstaculo.get('radio', obstaculo.get('ancho', 0)//2)
                if (obstaculo['x'] - radio_ancho <= 20 or 
                    obstaculo['x'] + radio_ancho >= self.ancho - 20):
                    obstaculo['vel_x'] *= -1
            
            if 'y' in obstaculo:
                radio_alto = obstaculo.get('radio', obstaculo.get('alto', 0)//2)
                if (obstaculo['y'] - radio_alto <= 70 or 
                    obstaculo['y'] + radio_alto >= self.alto - 20):
                    obstaculo['vel_y'] *= -1
    
    def verificar_colision(self):
        """Verifica colisiones con obstáculos"""
        if self.explosion_activa:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        
        for obstaculo in self.obstaculos:
            if obstaculo['tipo'] == 'circulo':
                dx = bx - obstaculo['x']
                dy = by - obstaculo['y']
                distancia = sqrt(dx*dx + dy*dy)
                
                if distancia <= br + obstaculo['radio']:
                    return True
                    
            elif obstaculo['tipo'] == 'rectangulo':
                rect_x = obstaculo['x'] - obstaculo['ancho']//2
                rect_y = obstaculo['y'] - obstaculo['alto']//2
                rect_w = obstaculo['ancho']
                rect_h = obstaculo['alto']
                
                closest_x = max(rect_x, min(bx, rect_x + rect_w))
                closest_y = max(rect_y, min(by, rect_y + rect_h))
                
                distancia = sqrt((bx - closest_x)**2 + (by - closest_y)**2)
                
                if distancia <= br:
                    return True
                    
            else:  # linea
                x1, y1, x2, y2 = obstaculo['x1'], obstaculo['y1'], obstaculo['x2'], obstaculo['y2']
                
                A = bx - x1
                B = by - y1
                C = x2 - x1
                D = y2 - y1
                
                dot = A * C + B * D
                len_sq = C * C + D * D
                param = dot / len_sq if len_sq != 0 else -1
                
                if param < 0:
                    xx, yy = x1, y1
                elif param > 1:
                    xx, yy = x2, y2
                else:
                    xx = x1 + param * C
                    yy = y1 + param * D
                
                distancia = sqrt((bx - xx)**2 + (by - yy)**2)
                
                if distancia <= br + 2:
                    return True
        
        return False
    
    def verificar_meta(self):
        """Verifica si llega a la meta"""
        if self.explosion_activa:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        mx, my = self.meta['x'], self.meta['y']
        
        distancia = sqrt((bx - mx)**2 + (by - my)**2)
        
        if distancia <= br + 40:  # Radio de la bandera
            if self.nivel >= 10 and not self.tiene_llave:
                self.mostrar_mensaje_temporal("¡Necesitas la llave! 🔑", 1500)
                return False
            return True
        return False
    
    def efecto_completar_nivel(self):
        """Efecto especial al completar un nivel"""
        self.explosion_activa = True
        
        # 1. Desvanecer al jugador
        def desvanecer_jugador():
            if self.bolita['alpha'] > 0:
                self.bolita['alpha'] -= 0.05
                self.ventana.after(50, desvanecer_jugador)
            else:
                # 2. Explosionar todos los obstáculos
                for obstaculo in self.obstaculos:
                    x = obstaculo.get('x', (obstaculo.get('x1', 0) + obstaculo.get('x2', 0)) / 2)
                    y = obstaculo.get('y', (obstaculo.get('y1', 0) + obstaculo.get('y2', 0)) / 2)
                    self.crear_explosion_obstaculo(x, y)
                
                # 3. Explosión en toda la pantalla
                self.crear_explosion_pantalla_completa()
                
                # 4. Esperar y avanzar nivel
                self.ventana.after(1500, self.completar_transicion_nivel)
        
        desvanecer_jugador()
    
    def completar_transicion_nivel(self):
        """Completa la transición al siguiente nivel"""
        # Avanzar nivel
        self.nivel += 1
        self.puntos += 100 * self.nivel
        
        # Resetear jugador
        self.bolita['alpha'] = 1.0
        self.bolita['x'] = self.ancho // 2
        self.bolita['y'] = self.alto - 100
        
        # Resetear llave
        self.tiene_llave = False
        self.llave = None
        
        # Limpiar explosiones
        self.explosion_particulas = []
        self.explosion_activa = False
        
        # Crear nuevos elementos
        self.crear_meta()
        self.crear_llave()
        self.crear_obstaculos()
        
        # Continuar juego
        self.actualizar_juego()
    
    def mostrar_mensaje_temporal(self, texto, duracion):
        """Muestra un mensaje temporal"""
        fondo = self.canvas.create_rectangle(
            self.ancho // 2 - 200,
            self.alto // 2 - 40,
            self.ancho // 2 + 200,
            self.alto // 2 + 40,
            fill="#000000",
            outline="white",
            width=2
        )
        
        texto_id = self.canvas.create_text(
            self.ancho // 2,
            self.alto // 2,
            text=texto,
            fill=self.color_texto,
            font=("Arial", 16, "bold"),
            justify="center"
        )
        
        self.ventana.after(duracion, lambda: self.canvas.delete(fondo) or self.canvas.delete(texto_id))
    
    def mostrar_game_over(self):
        """Muestra pantalla de Game Over"""
        self.en_game_over = True
        self.juego_activo = False
        self.canvas.delete("all")
        
        # Fondo
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto, fill="#000000")
        
        # Título
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.3,
            text="💀 GAME OVER 💀",
            fill="#FF6B6B",
            font=("Arial", 48, "bold")
        )
        
        # Estadísticas
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.45,
            text=f"Puntuación: {self.puntos}\nNivel alcanzado: {self.nivel}",
            fill=self.color_texto,
            font=("Arial", 24),
            justify="center"
        )
        
        # Botón reiniciar
        btn_reiniciar_x1 = self.ancho // 2 - 100
        btn_reiniciar_y1 = self.alto * 0.6
        btn_reiniciar_x2 = self.ancho // 2 + 100
        btn_reiniciar_y2 = self.alto * 0.6 + 50
        
        btn_reiniciar = self.canvas.create_rectangle(
            btn_reiniciar_x1, btn_reiniciar_y1,
            btn_reiniciar_x2, btn_reiniciar_y2,
            fill="#4ECDC4",
            outline="white",
            width=2,
            tags="btn_reiniciar"
        )
        
        self.canvas.create_text(
            self.ancho // 2,
            btn_reiniciar_y1 + 25,
            text="🔄 REINICIAR",
            fill="white",
            font=("Arial", 20, "bold"),
            tags="btn_reiniciar_text"
        )
        
        # Botón menú
        btn_menu_y1 = btn_reiniciar_y1 + 70
        btn_menu_y2 = btn_menu_y1 + 50
        
        btn_menu = self.canvas.create_rectangle(
            btn_reiniciar_x1, btn_menu_y1,
            btn_reiniciar_x2, btn_menu_y2,
            fill="#FFD166",
            outline="white",
            width=2,
            tags="btn_menu"
        )
        
        self.canvas.create_text(
            self.ancho // 2,
            btn_menu_y1 + 25,
            text="🏠 MENÚ",
            fill="black",
            font=("Arial", 20, "bold"),
            tags="btn_menu_text"
        )
        
        # Vincular clics
        self.canvas.tag_bind("btn_reiniciar", "<Button-1>", lambda e: self.iniciar_juego())
        self.canvas.tag_bind("btn_reiniciar_text", "<Button-1>", lambda e: self.iniciar_juego())
        self.canvas.tag_bind("btn_menu", "<Button-1>", lambda e: self.mostrar_menu())
        self.canvas.tag_bind("btn_menu_text", "<Button-1>", lambda e: self.mostrar_menu())
    
    def actualizar_juego(self):
        """Bucle principal del juego"""
        if not self.juego_activo or self.pausado or self.en_menu:
            if not self.en_game_over:
                self.ventana.after(16, self.actualizar_juego)
            return
        
        # Actualizar sistemas
        self.actualizar_energia()
        self.actualizar_particulas()
        
        if not self.explosion_activa:
            self.actualizar_bolita()
            self.mover_obstaculos()
            
            # Verificar llave
            if self.nivel >= 10 and self.llave and not self.llave['recolectada']:
                if self.verificar_colision_llave():
                    self.mostrar_mensaje_temporal("¡Llave conseguida! 🔑", 1500)
            
            # Verificar colisiones
            if self.verificar_colision():
                self.perder_vida()
                self.ventana.after(16, self.actualizar_juego)
                return
            
            # Verificar meta
            if self.verificar_meta():
                self.efecto_completar_nivel()
                return
        
        # Dibujar todo
        self.dibujar_interfaz_juego()
        
        # Continuar bucle
        self.ventana.after(16, self.actualizar_juego)
    
    def perder_vida(self):
        """Resta una vida"""
        self.vidas -= 1
        
        if self.vidas <= 0:
            self.mostrar_game_over()
        else:
            # Efecto de daño
            for _ in range(20):
                self.explosion_particulas.append(self.crear_particula(
                    self.bolita['x'], self.bolita['y'], es_explosion=True
                ))
            
            # Reposicionar
            self.bolita['x'] = self.ancho // 2
            self.bolita['y'] = self.alto - 100
    
    def tecla_presionada(self, event):
        """Maneja teclas presionadas"""
        tecla = event.keysym.lower()
        
        if tecla == 'escape':
            self.mostrar_menu()
            return
        
        if self.en_menu:
            if tecla in ['left', 'a']:
                self.personaje_actual = (self.personaje_actual - 1) % len(self.personajes)
                self.actualizar_seleccion_personaje()
            elif tecla in ['right', 'd']:
                self.personaje_actual = (self.personaje_actual + 1) % len(self.personajes)
                self.actualizar_seleccion_personaje()
            elif tecla in ['return', 'space']:
                self.iniciar_juego()
            return
        
        if self.en_game_over:
            if tecla == 'r':
                self.iniciar_juego()
            elif tecla == 'escape':
                self.mostrar_menu()
            return
        
        if tecla == 'r':
            self.iniciar_juego()
            return
        
        if tecla == 'q':
            if self.energia_actual > 10 and not self.corriendo and not self.explosion_activa:
                self.corriendo = True
                self.velocidad_actual = self.velocidad_carrera
            return
        
        if tecla == 'p' or tecla == 'space':
            if not self.en_game_over:
                self.pausado = not self.pausado
            return
        
        if not self.juego_activo or self.pausado or self.en_game_over or self.explosion_activa:
            return
        
        # Controles de movimiento
        if tecla in ['left', 'a']:
            self.mover_izquierda = True
        elif tecla in ['right', 'd']:
            self.mover_derecha = True
        elif tecla in ['up', 'w']:
            self.mover_arriba = True
        elif tecla in ['down', 's']:
            self.mover_abajo = True
    
    def tecla_soltada(self, event):
        """Maneja teclas soltadas"""
        tecla = event.keysym.lower()
        
        if tecla == 'q':
            self.corriendo = False
            self.velocidad_actual = self.velocidad_normal
        
        if tecla in ['left', 'a']:
            self.mover_izquierda = False
        elif tecla in ['right', 'd']:
            self.mover_derecha = False
        elif tecla in ['up', 'w']:
            self.mover_arriba = False
        elif tecla in ['down', 's']:
            self.mover_abajo = False
    
    def iniciar(self):
        """Inicia la aplicación"""
        self.ventana.mainloop()

# Ejecutar el juego
if __name__ == "__main__":
    juego = JuegoBolita()
    juego.iniciar()