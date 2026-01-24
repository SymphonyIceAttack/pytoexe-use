import tkinter as tk
import random
from math import sqrt, cos, sin, radians
import wave
import struct
import tempfile
import os
from threading import Thread
import time  # Añadido para manejar el tiempo

class SistemaSonido:
    """Sistema de sonidos 8-bit/chiptune para el juego"""
    
    @staticmethod
    def generar_onda_seno(frecuencia, duracion=0.1, volumen=0.3, sample_rate=44100):
        """Genera una onda seno simple"""
        samples = int(sample_rate * duracion)
        datos = []
        
        for i in range(samples):
            # Onda seno con envelope ADSR simple
            t = i / sample_rate
            envelope = 1.0
            
            # Envelope ADSR básico
            if t < duracion * 0.1:  # Attack
                envelope = t / (duracion * 0.1)
            elif t > duracion * 0.7:  # Release
                envelope = 1.0 - ((t - duracion * 0.7) / (duracion * 0.3))
            
            valor = envelope * volumen * sin(2 * 3.14159 * frecuencia * t)
            datos.append(valor)
        
        return datos
    
    @staticmethod
    def generar_onda_cuadrada(frecuencia, duracion=0.1, volumen=0.3, sample_rate=44100):
        """Genera una onda cuadrada (típica chiptune)"""
        samples = int(sample_rate * duracion)
        datos = []
        
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0
            
            if t < duracion * 0.1:
                envelope = t / (duracion * 0.1)
            elif t > duracion * 0.7:
                envelope = 1.0 - ((t - duracion * 0.7) / (duracion * 0.3))
            
            # Onda cuadrada
            valor = envelope * volumen * (1.0 if sin(2 * 3.14159 * frecuencia * t) > 0 else -1.0)
            datos.append(valor)
        
        return datos
    
    @staticmethod
    def generar_onda_triangular(frecuencia, duracion=0.1, volumen=0.3, sample_rate=44100):
        """Genera una onda triangular"""
        samples = int(sample_rate * duracion)
        datos = []
        
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0
            
            if t < duracion * 0.1:
                envelope = t / (duracion * 0.1)
            elif t > duracion * 0.7:
                envelope = 1.0 - ((t - duracion * 0.7) / (duracion * 0.3))
            
            # Onda triangular
            phase = (frecuencia * t) % 1.0
            valor = envelope * volumen * (4 * abs(phase - 0.5) - 1)
            datos.append(valor)
        
        return datos
    
    @staticmethod
    def generar_ruido_blanco(duracion=0.1, volumen=0.2, sample_rate=44100):
        """Genera ruido blanco para explosiones"""
        samples = int(sample_rate * duracion)
        datos = []
        
        for i in range(samples):
            t = i / sample_rate
            envelope = 1.0
            
            if t < duracion * 0.05:  # Attack rápido
                envelope = t / (duracion * 0.05)
            elif t > duracion * 0.3:  # Release más largo
                envelope = 1.0 - ((t - duracion * 0.3) / (duracion * 0.7))
            
            valor = envelope * volumen * (random.random() * 2 - 1)
            datos.append(valor)
        
        return datos
    
    @staticmethod
    def generar_acorde(frecuencia_base, duracion=0.2, tipo="mayor", volumen=0.25):
        """Genera acordes simples"""
        if tipo == "mayor":
            frecuencias = [frecuencia_base, frecuencia_base * 1.25, frecuencia_base * 1.5]
        elif tipo == "menor":
            frecuencias = [frecuencia_base, frecuencia_base * 1.2, frecuencia_base * 1.5]
        else:  # quinta
            frecuencias = [frecuencia_base, frecuencia_base * 1.5]
        
        # Mezclar ondas
        datos_finales = None
        for i, freq in enumerate(frecuencias):
            datos = SistemaSonido.generar_onda_cuadrada(freq, duracion, volumen * 0.7)
            
            if datos_finales is None:
                datos_finales = datos
            else:
                for j in range(len(datos)):
                    datos_finales[j] += datos[j]
        
        # Normalizar
        if datos_finales:
            max_val = max(abs(min(datos_finales)), abs(max(datos_finales)))
            if max_val > 0:
                for i in range(len(datos_finales)):
                    datos_finales[i] /= max_val
                    datos_finales[i] *= volumen
        
        return datos_finales or []
    
    @staticmethod
    def crear_archivo_wav(datos, sample_rate=44100, nombre="sonido.wav"):
        """Crea un archivo WAV temporal con los datos de sonido"""
        # Normalizar datos
        max_val = max(abs(min(datos)), abs(max(datos))) if datos else 1
        if max_val > 1:
            datos = [d/max_val for d in datos]
        
        # Crear archivo temporal
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
        temp_file.close()
        
        with wave.open(temp_file.name, 'w') as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convertir a bytes
            frames = []
            for sample in datos:
                # Limitar entre -1 y 1
                sample = max(-1.0, min(1.0, sample))
                # Convertir a 16-bit
                sample_int = int(sample * 32767)
                frames.append(struct.pack('<h', sample_int))
            
            wav_file.writeframes(b''.join(frames))
        
        return temp_file.name
    
    @staticmethod
    def reproducir_sonido_async(ruta_archivo):
        """Reproduce un sonido en segundo plano (asíncrono)"""
        def reproducir():
            try:
                import winsound
                winsound.PlaySound(ruta_archivo, winsound.SND_FILENAME | winsound.SND_ASYNC)
                # Esperar un momento antes de eliminar el archivo
                # para asegurar que se haya cargado
                time.sleep(0.1)
                # Eliminar archivo después de reproducir
                if os.path.exists(ruta_archivo):
                    os.unlink(ruta_archivo)
            except Exception as e:
                print(f"Error reproduciendo sonido: {e}")
                # Si falla, intentar eliminar el archivo
                try:
                    if os.path.exists(ruta_archivo):
                        os.unlink(ruta_archivo)
                except:
                    pass
        
        # Ejecutar en hilo separado
        thread = Thread(target=reproducir)
        thread.daemon = True
        thread.start()

class SonidosJuego:
    """Clase que maneja todos los sonidos del juego"""
    
    def __init__(self):
        self.sonidos_generados = {}
        self.cargar_sonidos()
    
    def cargar_sonidos(self):
        """Genera y carga todos los sonidos del juego"""
        print("🎵 Generando sonidos 8-bit...")
        
        # 1. MOVIMIENTO
        self.sonidos_generados['movimiento'] = SistemaSonido.generar_onda_cuadrada(
            440, 0.08, 0.15  # A4, corto, suave
        )
        
        # 2. CORRER
        self.sonidos_generados['correr'] = SistemaSonido.generar_onda_cuadrada(
            660, 0.12, 0.2  # E5, un poco más largo
        )
        
        # 3. COLISIÓN (daño)
        self.sonidos_generados['colision'] = SistemaSonido.generar_acorde(
            220, 0.3, "menor", 0.3  # Acorde menor suave
        )
        
        # 4. RECOGER LLAVE
        self.sonidos_generados['recoger_llave'] = SistemaSonido.generar_acorde(
            523.25, 0.4, "mayor", 0.25  # C5 mayor brillante
        )
        
        # 5. COMPLETAR NIVEL (¡éxito!)
        self.sonidos_generados['completar_nivel'] = self.generar_sonido_victoria()
        
        # 6. EXPLOSIÓN OBSTÁCULO
        self.sonidos_generados['explosion_obstaculo'] = SistemaSonido.generar_ruido_blanco(
            0.15, 0.25
        )
        
        # 7. EXPLOSIÓN PANTALLA COMPLETA
        self.sonidos_generados['explosion_pantalla'] = self.generar_sonido_explosion_espectacular()
        
        # 8. GAME OVER
        self.sonidos_generados['game_over'] = self.generar_sonido_game_over()
        
        # 9. DESVANECIMIENTO
        self.sonidos_generados['desvanecimiento'] = SistemaSonido.generar_onda_triangular(
            329.63, 0.5, 0.2  # E4, largo, suave
        )
        
        # 10. PASO DE NIVEL (transición)
        self.sonidos_generados['paso_nivel'] = self.generar_sonido_transicion()
        
        print("✅ Sonidos generados correctamente!")
    
    def generar_sonido_victoria(self):
        """Sonido especial para completar nivel"""
        datos = []
        
        # Secuencia ascendente de acordes
        frecuencias = [261.63, 329.63, 392.00, 523.25]  # C4, E4, G4, C5
        duracion_nota = 0.15
        
        for freq in frecuencias:
            nota = SistemaSonido.generar_acorde(freq, duracion_nota, "mayor", 0.2)
            datos.extend(nota)
        
        return datos
    
    def generar_sonido_explosion_espectacular(self):
        """Sonido espectacular para explosión pantalla completa"""
        datos = []
        
        # Mezcla de ruido y tonos descendentes
        ruido = SistemaSonido.generar_ruido_blanco(0.3, 0.3)
        
        # Tono descendente (glissando)
        tono_descendente = []
        freq_inicial = 440
        freq_final = 110
        duracion = 0.3
        samples = int(44100 * duracion)
        
        for i in range(samples):
            t = i / samples
            freq_actual = freq_inicial + (freq_final - freq_inicial) * t
            envelope = 1.0 - t  # Decae linealmente
            
            valor = envelope * 0.2 * sin(2 * 3.14159 * freq_actual * t)
            tono_descendente.append(valor)
        
        # Mezclar ruido y tono
        max_len = max(len(ruido), len(tono_descendente))
        for i in range(max_len):
            valor = 0
            if i < len(ruido):
                valor += ruido[i]
            if i < len(tono_descendente):
                valor += tono_descendente[i] * 0.7
            datos.append(valor)
        
        return datos
    
    def generar_sonido_game_over(self):
        """Sonido triste para Game Over"""
        datos = []
        
        # Secuencia descendente melancólica
        frecuencias = [392.00, 329.63, 293.66, 261.63]  # G4, E4, D4, C4
        duracion_nota = 0.25
        
        for freq in frecuencias:
            nota = SistemaSonido.generar_acorde(freq, duracion_nota, "menor", 0.25)
            datos.extend(nota)
        
        # Ruido final suave
        ruido_final = SistemaSonido.generar_ruido_blanco(0.2, 0.15)
        max_len = max(len(datos), len(ruido_final))
        
        for i in range(max_len):
            valor = 0
            if i < len(datos):
                valor += datos[i]
            if i < len(ruido_final):
                valor += ruido_final[i]
            
            if i < len(datos):
                datos[i] = valor
            else:
                datos.append(valor)
        
        return datos
    
    def generar_sonido_transicion(self):
        """Sonido de transición entre niveles"""
        datos = []
        
        # Arpegio ascendente
        frecuencias = [261.63, 329.63, 392.00, 523.25, 659.25]  # C4, E4, G4, C5, E5
        duracion_nota = 0.08
        
        for freq in frecuencias:
            nota = SistemaSonido.generar_onda_cuadrada(freq, duracion_nota, 0.18)
            datos.extend(nota)
        
        return datos
    
    def reproducir(self, nombre_sonido):
        """Reproduce un sonido por su nombre"""
        if nombre_sonido in self.sonidos_generados:
            try:
                # Crear archivo WAV temporal
                archivo_wav = SistemaSonido.crear_archivo_wav(
                    self.sonidos_generados[nombre_sonido]
                )
                
                # Reproducir en segundo plano
                SistemaSonido.reproducir_sonido_async(archivo_wav)
                
            except Exception as e:
                print(f"⚠️ Error reproduciendo sonido {nombre_sonido}: {e}")
        else:
            print(f"⚠️ Sonido no encontrado: {nombre_sonido}")

class JuegoBolita:
    def __init__(self):
        self.ventana = tk.Tk()
        self.ventana.title("Bolita en Circuitos - Con Sonido 8-bit!")
        
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
        
        # Inicializar sistema de sonido
        print("🔊 Inicializando sistema de sonido...")
        self.sonidos = SonidosJuego()
        
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
        
        # Sistema de partículas OPTIMIZADO
        self.particulas = []
        self.max_particulas = 50
        self.max_explosion_particulas = 200
        self.tiempo_particula = 0
        self.ultimo_sonido_movimiento = time.time() * 1000  # Inicializar con tiempo actual
        
        # Sistema de explosiones mejorado
        self.explosion_activa = False
        self.explosion_particulas = []
        self.explosion_timer = None
        self.fase_explosion = 0
        self.obstaculos_a_explotar = []
        
        # Límites de partículas por efecto
        self.max_particulas_desvanecimiento = 30
        self.max_particulas_obstaculo = 30
        self.max_particulas_pantalla = 150
        
        # Selección de personaje
        self.personajes = [
            {"nombre": "Bolita Roja", "color": "#FF6B6B", "radio": 20},
            {"nombre": "Bolita Azul", "color": "#4ECDC4", "radio": 18},
            {"nombre": "Bolita Verde", "color": "#6BFF6B", "radio": 22},
            {"nombre": "Bolita Amarilla", "color": "#FFD166", "radio": 19},
            {"nombre": "Bolita Rosa", "color": "#FF6BFF", "radio": 21}
        ]
        self.personaje_actual = 0
        
        # Colores para explosiones
        self.colores_explosion = ["#FF6B6B", "#FFD166", "#4ECDC4", "#6BFF6B", "#FF6BFF", "#FFFFFF", "#FFA500"]
        
        # Colores
        self.color_fondo = "#1A1A2E"
        self.color_meta = "#FFD166"
        self.color_texto = "#FFFFFF"
        self.color_sombra = "#333333"
        self.color_llave = "#FF6B6B"
        self.color_energia_llena = "#4ECDC4"
        self.color_energia_vacia = "#FF6B6B"
        
        # Configurar canvas con optimización
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
        
        # Variable para controlar el bucle del juego
        self.bucle_activo = False
        
        # Cache de colores para optimización
        self.color_cache = {}
    
    # ============================================
    # SISTEMA DE SONIDOS INTEGRADO
    # ============================================
    
    def reproducir_sonido_movimiento(self):
        """Reproduce sonido de movimiento con límite de frecuencia"""
        ahora = time.time() * 1000  # Convertir a milisegundos
        if ahora - self.ultimo_sonido_movimiento > 150:  # 150ms entre sonidos
            self.sonidos.reproducir('movimiento')
            self.ultimo_sonido_movimiento = ahora
    
    def reproducir_sonido_correr(self):
        """Reproduce sonido de correr"""
        self.sonidos.reproducir('correr')
    
    def reproducir_sonido_colision(self):
        """Reproduce sonido de colisión"""
        self.sonidos.reproducir('colision')
    
    def reproducir_sonido_recoger_llave(self):
        """Reproduce sonido al recoger llave"""
        self.sonidos.reproducir('recoger_llave')
    
    def reproducir_sonido_explosion_obstaculo(self):
        """Reproduce sonido de explosión de obstáculo"""
        self.sonidos.reproducir('explosion_obstaculo')
    
    def reproducir_sonido_explosion_pantalla(self):
        """Reproduce sonido de explosión pantalla completa"""
        self.sonidos.reproducir('explosion_pantalla')
    
    def reproducir_sonido_desvanecimiento(self):
        """Reproduce sonido de desvanecimiento"""
        self.sonidos.reproducir('desvanecimiento')
    
    def reproducir_sonido_completar_nivel(self):
        """Reproduce sonido de completar nivel"""
        self.sonidos.reproducir('completar_nivel')
    
    def reproducir_sonido_paso_nivel(self):
        """Reproduce sonido de transición entre niveles"""
        self.sonidos.reproducir('paso_nivel')
    
    def reproducir_sonido_game_over(self):
        """Reproduce sonido de Game Over"""
        self.sonidos.reproducir('game_over')
    
    # ============================================
    # MENÚ PRINCIPAL
    # ============================================
    
    def mostrar_menu(self):
        """Muestra el menú principal"""
        self.en_menu = True
        self.juego_activo = False
        self.en_game_over = False
        self.bucle_activo = False
        self.canvas.delete("all")
        
        # Título con emoji de altavoz
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.2,
            text="🎮 BOLITA EN CIRCUITOS 🔊",
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
        
        # Instrucciones con icono de sonido
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.85,
            text="🔊 SONIDO 8-BIT ACTIVADO\n← → ↑ ↓ o WASD: Mover\nQ: Correr (usa energía)\nP o Espacio: Pausa\nR: Reiniciar\nESC: Menú",
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
    
    # ============================================
    # INICIAR JUEGO (con sonido)
    # ============================================
    
    def iniciar_juego(self):
        """Inicia el juego desde el menú"""
        print("INICIANDO JUEGO...")
        print("🔊 Sistema de sonido listo!")
        
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
        self.fase_explosion = 0
        
        # Resetear sistemas
        self.energia_actual = self.energia_maxima
        self.corriendo = False
        self.velocidad_actual = self.velocidad_normal
        self.particulas = []
        self.explosion_particulas = []
        self.obstaculos_a_explotar = []
        self.ultimo_sonido_movimiento = time.time() * 1000  # Resetear tiempo
        
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
        
        # Sonido de inicio
        self.reproducir_sonido_paso_nivel()
        
        # Iniciar bucle
        self.bucle_activo = True
        self.ultimo_tiempo = self.ventana.after(0, self.actualizar_juego)
    
    # ============================================
    # CREACIÓN DE ELEMENTOS
    # ============================================
    
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
            'radio': 25,
            'emoji': "🏁"
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
    
    # ============================================
    # SISTEMA DE PARTÍCULAS
    # ============================================
    
    def crear_particula_explosion(self, x, y, es_obstaculo=False):
        color = random.choice(self.colores_explosion)
        
        if es_obstaculo:
            vel_min, vel_max = 3, 8
            vida_min, vida_max = 30, 60
        else:
            vel_min, vel_max = 4, 10
            vida_min, vida_max = 40, 80
        
        angulo = random.uniform(0, 2 * 3.14159)
        velocidad = random.uniform(vel_min, vel_max)
        
        particula = {
            'x': x,
            'y': y,
            'radio': random.randint(2, 5),
            'color': color,
            'vel_x': cos(angulo) * velocidad,
            'vel_y': sin(angulo) * velocidad,
            'vida': random.randint(vida_min, vida_max),
            'vida_max': vida_max,
            'alpha': 1.0,
            'gravedad': random.uniform(0.1, 0.2),
            'es_explosion': True
        }
        
        return particula
    
    def crear_explosion_obstaculo(self, x, y):
        # Reproducir sonido de explosión
        self.reproducir_sonido_explosion_obstaculo()
        
        # Crear partículas
        particulas_a_crear = min(self.max_particulas_obstaculo, 
                                30 - len(self.explosion_particulas))
        
        if particulas_a_crear <= 0:
            return
            
        for _ in range(particulas_a_crear):
            particula = self.crear_particula_explosion(x, y, es_obstaculo=True)
            self.explosion_particulas.append(particula)
    
    def crear_explosion_pantalla_completa(self):
        # Reproducir sonido espectacular
        self.reproducir_sonido_explosion_pantalla()
        
        # Crear partículas
        espacio_disponible = self.max_particulas_pantalla - len(self.explosion_particulas)
        if espacio_disponible <= 0:
            return
        
        particulas_centro = min(80, espacio_disponible // 2)
        for _ in range(particulas_centro):
            x = self.ancho // 2 + random.randint(-50, 50)
            y = self.alto // 2 + random.randint(-50, 50)
            particula = self.crear_particula_explosion(x, y, es_obstaculo=False)
            self.explosion_particulas.append(particula)
        
        particulas_bordes = min(40, espacio_disponible - particulas_centro)
        for _ in range(particulas_bordes):
            x = random.randint(0, self.ancho)
            y = random.randint(0, self.alto)
            particula = self.crear_particula_explosion(x, y, es_obstaculo=False)
            self.explosion_particulas.append(particula)
    
    def actualizar_particulas(self):
        # Partículas normales
        if len(self.particulas) > self.max_particulas:
            self.particulas = self.particulas[-self.max_particulas:]
        
        particulas_vivas = []
        for particula in self.particulas:
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 1
            
            if particula['vida'] > 0:
                particula['alpha'] = particula['vida'] / 40.0
                particula['vel_x'] *= 0.95
                particula['vel_y'] *= 0.95
                particulas_vivas.append(particula)
        
        self.particulas = particulas_vivas
        
        # Partículas de explosión
        if len(self.explosion_particulas) > self.max_explosion_particulas:
            self.explosion_particulas = sorted(
                self.explosion_particulas, 
                key=lambda p: p['vida'], 
                reverse=True
            )[:self.max_explosion_particulas]
        
        explosion_vivas = []
        for particula in self.explosion_particulas:
            particula['vel_y'] += particula['gravedad']
            particula['x'] += particula['vel_x']
            particula['y'] += particula['vel_y']
            particula['vida'] -= 2
            
            if particula['vida'] > 0:
                particula['alpha'] = particula['vida'] / particula['vida_max']
                particula['vel_x'] *= 0.97
                particula['vel_y'] *= 0.97
                
                if particula['alpha'] > 0.05:
                    explosion_vivas.append(particula)
        
        self.explosion_particulas = explosion_vivas
        
        # Crear partículas de movimiento
        if (self.mover_izquierda or self.mover_derecha or 
            self.mover_arriba or self.mover_abajo):
            self.tiempo_particula += 1
            if self.tiempo_particula >= (3 if self.corriendo else 6):
                if len(self.particulas) < self.max_particulas // 2:
                    particula = self.crear_particula_movimiento()
                    if particula:
                        self.particulas.append(particula)
                self.tiempo_particula = 0
    
    def crear_particula_movimiento(self):
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
            'x': self.bolita['x'] + dx * self.bolita['radio'],
            'y': self.bolita['y'] + dy * self.bolita['radio'],
            'radio': random.randint(1, 3),
            'color': self.color_bolita,
            'vel_x': -dx * random.uniform(0.5, 1.5),
            'vel_y': -dy * random.uniform(0.5, 1.5),
            'vida': random.randint(15, 25),
            'alpha': 1.0,
            'es_explosion': False
        }
        
        return particula
    
    def dibujar_particulas(self):
        if len(self.explosion_particulas) > 50:
            self.dibujar_particulas_lote(self.explosion_particulas)
        else:
            for particula in self.explosion_particulas:
                if particula['alpha'] > 0:
                    self.dibujar_particula(particula)
        
        if len(self.particulas) > 20:
            self.dibujar_particulas_lote(self.particulas)
        else:
            for particula in self.particulas:
                if particula['alpha'] > 0:
                    self.dibujar_particula(particula)
    
    def dibujar_particulas_lote(self, particulas):
        for particula in particulas:
            if particula['alpha'] > 0:
                if len(particulas) > 30:
                    self.canvas.create_oval(
                        particula['x'] - particula['radio'],
                        particula['y'] - particula['radio'],
                        particula['x'] + particula['radio'],
                        particula['y'] + particula['radio'],
                        fill=particula['color'],
                        outline=""
                    )
                else:
                    self.dibujar_particula(particula)
    
    def dibujar_particula(self, particula):
        try:
            cache_key = f"{particula['color']}_{int(particula['alpha']*100)}"
            if cache_key not in self.color_cache:
                color = self.canvas.winfo_rgb(particula['color'])
                r = int(color[0] / 256 * particula['alpha'])
                g = int(color[1] / 256 * particula['alpha'])
                b = int(color[2] / 256 * particula['alpha'])
                
                r = max(1, min(255, r))
                g = max(1, min(255, g))
                b = max(1, min(255, b))
                
                self.color_cache[cache_key] = f'#{r:02x}{g:02x}{b:02x}'
            
            color_alpha = self.color_cache[cache_key]
            
            self.canvas.create_oval(
                particula['x'] - particula['radio'],
                particula['y'] - particula['radio'],
                particula['x'] + particula['radio'],
                particula['y'] + particula['radio'],
                fill=color_alpha,
                outline=""
            )
        except:
            self.canvas.create_oval(
                particula['x'] - particula['radio'],
                particula['y'] - particula['radio'],
                particula['x'] + particula['radio'],
                particula['y'] + particula['radio'],
                fill=particula['color'],
                outline=""
            )
    
    # ============================================
    # EFECTO ESPECTACULAR CON SONIDO
    # ============================================
    
    def efecto_completar_nivel(self):
        """EFECTO ESPECTACULAR con sonidos integrados"""
        print("🎆 INICIANDO EFECTO ESPECTACULAR!")
        
        # Sonido de completar nivel
        self.reproducir_sonido_completar_nivel()
        
        # Limpiar partículas
        self.particulas = []
        self.explosion_particulas = []
        
        # Detener bucle normal
        self.juego_activo = False
        self.explosion_activa = True
        self.pausado = True
        self.fase_explosion = 0
        
        # Guardar obstáculos para explosiones
        self.obstaculos_a_explotar = self.obstaculos.copy()
        
        # FASE 1: Desvanecimiento
        self.iniciar_desvanecimiento_jugador()
    
    def iniciar_desvanecimiento_jugador(self):
        """FASE 1: Desvanecimiento con sonido"""
        print("🌫️ FASE 1: Desvanecimiento del jugador...")
        
        # Sonido de desvanecimiento
        self.reproducir_sonido_desvanecimiento()
        
        def desvanecer(paso=0):
            if paso < 15:
                self.bolita['alpha'] = 1.0 - (paso / 15.0)
                
                if paso % 3 == 0 and len(self.particulas) < self.max_particulas_desvanecimiento:
                    self.crear_particulas_desvanecimiento()
                
                self.dibujar_interfaz_juego_simple()
                self.ventana.after(60, lambda: desvanecer(paso + 1))
            else:
                self.fase_explosion = 1
                self.iniciar_explosion_obstaculos(0)
        
        desvanecer()
    
    def crear_particulas_desvanecimiento(self):
        if len(self.particulas) >= self.max_particulas_desvanecimiento:
            return
            
        for _ in range(3):
            angulo = random.uniform(0, 2 * 3.14159)
            distancia = random.uniform(0, self.bolita['radio'])
            
            particula = {
                'x': self.bolita['x'] + cos(angulo) * distancia,
                'y': self.bolita['y'] + sin(angulo) * distancia,
                'radio': random.randint(1, 3),
                'color': self.color_bolita,
                'vel_x': cos(angulo) * random.uniform(0.5, 1.5),
                'vel_y': sin(angulo) * random.uniform(0.5, 1.5),
                'vida': random.randint(20, 30),
                'alpha': 0.5,
                'es_explosion': False
            }
            self.particulas.append(particula)
    
    def iniciar_explosion_obstaculos(self, index):
        if index == 0:
            print("💥 FASE 2: Explosión de obstáculos...")
        
        if not self.obstaculos_a_explotar:
            self.fase_explosion = 2
            self.ventana.after(300, self.iniciar_explosion_pantalla_completa)
            return
        
        # Explotar varios obstáculos a la vez
        obstaculos_por_lote = min(2, len(self.obstaculos_a_explotar))
        for _ in range(obstaculos_por_lote):
            if self.obstaculos_a_explotar:
                obstaculo = self.obstaculos_a_explotar.pop(0)
                
                if obstaculo['tipo'] == 'rectangulo':
                    x, y = obstaculo['x'], obstaculo['y']
                elif obstaculo['tipo'] == 'circulo':
                    x, y = obstaculo['x'], obstaculo['y']
                else:
                    x = (obstaculo['x1'] + obstaculo['x2']) // 2
                    y = (obstaculo['y1'] + obstaculo['y2']) // 2
                
                self.crear_explosion_obstaculo(x, y)
        
        self.actualizar_particulas()
        self.dibujar_interfaz_juego_simple()
        
        if self.obstaculos_a_explotar:
            delay = max(80, 300 // len(self.obstaculos))
            self.ventana.after(delay, lambda: self.iniciar_explosion_obstaculos(index + obstaculos_por_lote))
        else:
            self.ventana.after(300, self.iniciar_explosion_pantalla_completa)
    
    def iniciar_explosion_pantalla_completa(self):
        print("💥💥💥 FASE 3: Explosión pantalla completa!")
        self.fase_explosion = 2
        
        # Crear explosión
        self.crear_explosion_pantalla_completa()
        
        # Dibujar
        self.dibujar_interfaz_juego_simple()
        
        # Esperar y terminar
        self.ventana.after(800, self.finalizar_efecto_nivel)
    
    def finalizar_efecto_nivel(self):
        print("✨ Finalizando efecto espectacular...")
        
        # Limpiar todo
        self.particulas = []
        self.explosion_particulas = []
        self.color_cache = {}
        
        # Restaurar jugador
        self.bolita['alpha'] = 1.0
        self.bolita['x'] = self.ancho // 2
        self.bolita['y'] = self.alto - 100
        
        # Avanzar nivel
        self.nivel += 1
        self.puntos += 100 * self.nivel
        
        # Resetear
        self.tiene_llave = False
        self.llave = None
        self.explosion_activa = False
        self.fase_explosion = 0
        self.pausado = False
        
        # Nuevos elementos
        self.crear_meta()
        self.crear_llave()
        self.crear_obstaculos()
        
        # Sonido de transición
        self.reproducir_sonido_paso_nivel()
        
        # Mostrar mensaje
        self.mostrar_mensaje_temporal(f"¡NIVEL {self.nivel} COMPLETADO!\nPuntos: {self.puntos}", 1500)
        
        # Reiniciar bucle
        self.juego_activo = True
        self.bucle_activo = True
        print(f"🎮 NIVEL {self.nivel} INICIADO")
        
        self.actualizar_juego()
    
    # ============================================
    # FUNCIONES DE DIBUJO (optimizadas)
    # ============================================
    
    def dibujar_interfaz_juego_simple(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto, fill=self.color_fondo, outline="")
        self.dibujar_particulas()
        self.dibujar_meta()
        
        if self.bolita['alpha'] > 0.1:
            self.dibujar_bolita_simple()
        
        if self.explosion_activa:
            self.dibujar_estado_explosion()
    
    def dibujar_interfaz_juego(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto, fill=self.color_fondo, outline="")
        self.dibujar_particulas()
        self.dibujar_meta()
        
        if self.llave and not self.llave['recolectada']:
            self.dibujar_llave()
        
        if not self.explosion_activa or self.fase_explosion == 0:
            self.dibujar_obstaculos()
        
        self.dibujar_bolita()
        
        if not self.explosion_activa:
            self.dibujar_panel_informacion()
            self.dibujar_barra_energia()
        elif self.fase_explosion < 2:
            self.dibujar_estado_explosion()
    
    def dibujar_bolita_simple(self):
        x, y, r = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        alpha = self.bolita['alpha']
        
        if alpha > 0:
            self.canvas.create_oval(
                x - r + 2, y - r + 2,
                x + r + 2, y + r + 2,
                fill=self.color_sombra,
                outline=""
            )
            
            self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=self.color_bolita,
                outline="white",
                width=1
            )
    
    def dibujar_bolita(self):
        x, y, r = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        
        if self.bolita['alpha'] <= 0:
            return
            
        try:
            self.canvas.create_oval(
                x - r + 3, y - r + 3,
                x + r + 3, y + r + 3,
                fill=self.color_sombra,
                outline=self.color_sombra
            )
            
            self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=self.color_bolita,
                outline="white",
                width=2
            )
            
            if self.corriendo and not self.explosion_activa:
                self.canvas.create_oval(
                    x - r - 4, y - r - 4,
                    x + r + 4, y + r + 4,
                    outline="#FFD166",
                    width=1
                )
        except:
            self.canvas.create_oval(
                x - r, y - r,
                x + r, y + r,
                fill=self.color_bolita,
                outline="white",
                width=2
            )
    
    def dibujar_estado_explosion(self):
        fases = ["Desvaneciendo...", "Explosiones...", "¡ESPECTACULAR!"]
        if self.fase_explosion < len(fases):
            self.canvas.create_text(
                self.ancho // 2,
                self.alto - 50,
                text=f"🎆 {fases[self.fase_explosion]}",
                fill="#FFD166",
                font=("Arial", 16, "bold")
            )
    
    def dibujar_panel_informacion(self):
        self.canvas.create_rectangle(
            10, 10, 300, 55,
            fill="#000000",
            outline="white",
            width=1
        )
        
        self.canvas.create_text(
            60, 25,
            text=f"Puntos: {self.puntos}",
            fill=self.color_texto,
            font=("Arial", 12, "bold")
        )
        
        self.canvas.create_text(
            60, 40,
            text=f"Nivel: {self.nivel}",
            fill=self.color_texto,
            font=("Arial", 12, "bold")
        )
        
        self.canvas.create_text(
            180, 25,
            text=f"Vidas: {self.vidas}",
            fill=self.color_texto,
            font=("Arial", 12, "bold")
        )
        
        for i in range(min(self.vidas, 5)):
            x = 180 + (i * 25)
            y = 40
            self.canvas.create_text(
                x, y,
                text="❤️",
                fill="#FF6B6B",
                font=("Arial", 14)
            )
    
    def dibujar_barra_energia(self):
        barra_x = 10
        barra_y = 65
        barra_ancho = 150
        barra_alto = 15
        
        self.canvas.create_rectangle(
            barra_x, barra_y,
            barra_x + barra_ancho, barra_y + barra_alto,
            fill="#333333",
            outline="white",
            width=1
        )
        
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
    
    def dibujar_meta(self):
        x, y = self.meta['x'], self.meta['y']
        emoji = self.meta['emoji']
        
        self.canvas.create_text(
            x, y,
            text=emoji,
            fill="#FFD166" if self.tiene_llave or self.nivel < 10 else "#888888",
            font=("Arial", 40)
        )
    
    def dibujar_llave(self):
        x, y = self.llave['x'], self.llave['y']
        self.canvas.create_text(
            x, y,
            text=self.llave['emoji'],
            fill=self.llave['color'],
            font=("Arial", 24)
        )
    
    def dibujar_obstaculos(self):
        for obstaculo in self.obstaculos:
            if obstaculo['tipo'] == 'rectangulo':
                self.canvas.create_rectangle(
                    obstaculo['x'] - obstaculo['ancho']//2,
                    obstaculo['y'] - obstaculo['alto']//2,
                    obstaculo['x'] + obstaculo['ancho']//2,
                    obstaculo['y'] + obstaculo['alto']//2,
                    fill=obstaculo['color'],
                    outline="white",
                    width=1
                )
                self.canvas.create_text(
                    obstaculo['x'], obstaculo['y'],
                    text=obstaculo['emoji'],
                    fill="black",
                    font=("Arial", 16)
                )
            elif obstaculo['tipo'] == 'circulo':
                self.canvas.create_oval(
                    obstaculo['x'] - obstaculo['radio'],
                    obstaculo['y'] - obstaculo['radio'],
                    obstaculo['x'] + obstaculo['radio'],
                    obstaculo['y'] + obstaculo['radio'],
                    fill=obstaculo['color'],
                    outline="white",
                    width=1
                )
                self.canvas.create_text(
                    obstaculo['x'], obstaculo['y'],
                    text=obstaculo['emoji'],
                    fill="black",
                    font=("Arial", 16)
                )
            else:
                self.canvas.create_line(
                    obstaculo['x1'], obstaculo['y1'],
                    obstaculo['x2'], obstaculo['y2'],
                    fill=obstaculo['color'],
                    width=3
                )
    
    # ============================================
    # LÓGICA DEL JUEGO (con sonidos integrados)
    # ============================================
    
    def verificar_colision_llave(self):
        if not self.llave or self.llave['recolectada']:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        lx, ly = self.llave['x'], self.llave['y']
        
        distancia = sqrt((bx - lx)**2 + (by - ly)**2)
        
        if distancia <= br + 20:
            self.llave['recolectada'] = True
            self.tiene_llave = True
            # Sonido al recoger llave
            self.reproducir_sonido_recoger_llave()
            return True
        return False
    
    def actualizar_bolita(self):
        if not self.juego_activo or self.pausado or self.explosion_activa:
            return
        
        velocidad = self.velocidad_carrera if self.corriendo else self.velocidad_normal
        
        # Sonido de movimiento
        if (self.mover_izquierda or self.mover_derecha or 
            self.mover_arriba or self.mover_abajo):
            self.reproducir_sonido_movimiento()
        
        # Sonido de correr
        if self.corriendo and (self.mover_izquierda or self.mover_derecha or 
                              self.mover_arriba or self.mover_abajo):
            self.reproducir_sonido_correr()
        
        if self.mover_izquierda and self.bolita['x'] > self.bolita['radio']:
            self.bolita['x'] -= velocidad
        if self.mover_derecha and self.bolita['x'] < self.ancho - self.bolita['radio']:
            self.bolita['x'] += velocidad
        if self.mover_arriba and self.bolita['y'] > self.bolita['radio'] + 70:
            self.bolita['y'] -= velocidad
        if self.mover_abajo and self.bolita['y'] < self.alto - self.bolita['radio']:
            self.bolita['y'] += velocidad
    
    def mover_obstaculos(self):
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
        if self.explosion_activa:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        
        for obstaculo in self.obstaculos:
            if obstaculo['tipo'] == 'circulo':
                dx = bx - obstaculo['x']
                dy = by - obstaculo['y']
                distancia = sqrt(dx*dx + dy*dy)
                
                if distancia <= br + obstaculo['radio']:
                    # Sonido de colisión
                    self.reproducir_sonido_colision()
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
                    self.reproducir_sonido_colision()
                    return True
                    
            else:
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
                    self.reproducir_sonido_colision()
                    return True
        
        return False
    
    def verificar_meta(self):
        if self.explosion_activa:
            return False
            
        bx, by, br = self.bolita['x'], self.bolita['y'], self.bolita['radio']
        mx, my = self.meta['x'], self.meta['y']
        
        distancia = sqrt((bx - mx)**2 + (by - my)**2)
        
        if distancia <= br + 35:
            if self.nivel >= 10 and not self.tiene_llave:
                return False
            return True
        return False
    
    def mostrar_mensaje_temporal(self, texto, duracion):
        fondo = self.canvas.create_rectangle(
            self.ancho // 2 - 150,
            self.alto // 2 - 30,
            self.ancho // 2 + 150,
            self.alto // 2 + 30,
            fill="#000000",
            outline="white",
            width=1
        )
        
        texto_id = self.canvas.create_text(
            self.ancho // 2,
            self.alto // 2,
            text=texto,
            fill=self.color_texto,
            font=("Arial", 14, "bold"),
            justify="center"
        )
        
        self.ventana.after(duracion, lambda: self.canvas.delete(fondo) or self.canvas.delete(texto_id))
    
    def mostrar_game_over(self):
        self.en_game_over = True
        self.juego_activo = False
        self.bucle_activo = False
        self.canvas.delete("all")
        
        # Sonido de Game Over
        self.reproducir_sonido_game_over()
        
        self.canvas.create_rectangle(0, 0, self.ancho, self.alto, fill="#000000")
        
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.3,
            text="💀 GAME OVER 💀",
            fill="#FF6B6B",
            font=("Arial", 40, "bold")
        )
        
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.45,
            text=f"Puntuación: {self.puntos}\nNivel alcanzado: {self.nivel}",
            fill=self.color_texto,
            font=("Arial", 20),
            justify="center"
        )
        
        btn_reiniciar = self.canvas.create_rectangle(
            self.ancho // 2 - 80, self.alto * 0.6,
            self.ancho // 2 + 80, self.alto * 0.6 + 40,
            fill="#4ECDC4",
            outline="white",
            width=1,
            tags="btn_reiniciar"
        )
        
        self.canvas.create_text(
            self.ancho // 2,
            self.alto * 0.6 + 20,
            text="REINICIAR",
            fill="white",
            font=("Arial", 16, "bold"),
            tags="btn_reiniciar_text"
        )
        
        self.canvas.tag_bind("btn_reiniciar", "<Button-1>", lambda e: self.iniciar_juego())
        self.canvas.tag_bind("btn_reiniciar_text", "<Button-1>", lambda e: self.iniciar_juego())
    
    def actualizar_juego(self):
        if not self.bucle_activo:
            return
            
        if self.juego_activo and not self.pausado and not self.en_menu and not self.en_game_over:
            self.actualizar_energia()
            self.actualizar_particulas()
            
            if not self.explosion_activa:
                self.actualizar_bolita()
                self.mover_obstaculos()
                
                if self.nivel >= 10 and self.llave and not self.llave['recolectada']:
                    if self.verificar_colision_llave():
                        pass
                
                if self.verificar_colision():
                    self.perder_vida()
                    self.ventana.after(16, self.actualizar_juego)
                    return
                
                if self.verificar_meta():
                    self.efecto_completar_nivel()
                    return
            
            self.dibujar_interfaz_juego()
        
        # Mantener el bucle activo
        if self.bucle_activo:
            self.ventana.after(33, self.actualizar_juego)  # ~30 FPS
    
    def actualizar_energia(self):
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
    
    def perder_vida(self):
        self.vidas -= 1
        
        if self.vidas <= 0:
            self.mostrar_game_over()
        else:
            # Efecto de daño con sonido
            for _ in range(10):
                particula = self.crear_particula_explosion(
                    self.bolita['x'], self.bolita['y'], es_obstaculo=True
                )
                self.explosion_particulas.append(particula)
            
            self.bolita['x'] = self.ancho // 2
            self.bolita['y'] = self.alto - 100
    
    def tecla_presionada(self, event):
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
        
        if tecla in ['left', 'a']:
            self.mover_izquierda = True
        elif tecla in ['right', 'd']:
            self.mover_derecha = True
        elif tecla in ['up', 'w']:
            self.mover_arriba = True
        elif tecla in ['down', 's']:
            self.mover_abajo = True
    
    def tecla_soltada(self, event):
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
        self.ventana.mainloop()

if __name__ == "__main__":
    print("=" * 50)
    print("🎮 BOLITA EN CIRCUITOS - CON SONIDO 8-BIT! 🔊")
    print("=" * 50)
    juego = JuegoBolita()
    juego.iniciar()