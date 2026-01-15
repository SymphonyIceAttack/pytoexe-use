import tkinter as tk
from tkinter import ttk, messagebox
import time
import sys
import platform

# Detectar sistema operativo para sonido
SISTEMA_OPERATIVO = platform.system()

class CronometroCompleto:
    def __init__(self, root):
        self.root = root
        self.root.title("Cronómetro Pro v2.0")
        self.root.geometry("450x650")
        self.root.resizable(False, False)
        
        # Variables del cronómetro
        self.corriendo = False
        self.inicio_tiempo = 0
        self.tiempo_transcurrido = 0
        self.vueltas = []
        
        # Variables del temporizador
        self.temporizador_corriendo = False
        self.tiempo_objetivo = 0
        self.tiempo_restante = 0
        self.temporizador_pausado = False
        self.tiempo_pausa = 0
        
        # Variables para estadísticas
        self.mejor_tiempo = None
        self.promedio_tiempo = None
        
        self.crear_interfaz()
        self.actualizar_display()
    
    def crear_interfaz(self):
        """Crea la interfaz gráfica del cronómetro"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="15")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        titulo = tk.Label(main_frame, text="⏱ Cronómetro Pro v2.0", 
                         font=('Arial', 14, 'bold'), fg='#333333')
        titulo.pack(pady=(0, 10))
        
        # NOTEBOOK (pestañas)
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Pestañas
        tab_cronometro = ttk.Frame(notebook, padding="10")
        tab_temporizador = ttk.Frame(notebook, padding="10")
        
        notebook.add(tab_cronometro, text="⏱ Cronómetro")
        notebook.add(tab_temporizador, text="⏰ Temporizador")
        
        self.crear_pestana_cronometro(tab_cronometro)
        self.crear_pestana_temporizador(tab_temporizador)
        
        # Barra de estado
        estado_frame = ttk.Frame(main_frame, relief=tk.SUNKEN)
        estado_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.estado_var = tk.StringVar(value="⏹ Listo")
        estado_label = tk.Label(estado_frame, textvariable=self.estado_var,
                               font=('Arial', 10, 'bold'), 
                               fg='blue',
                               anchor=tk.W, padx=10)
        estado_label.pack(fill=tk.X)
    
    def crear_pestana_cronometro(self, parent):
        """Crea la pestaña del cronómetro"""
        # Display principal
        self.tiempo_var = tk.StringVar(value="00:00:00.00")
        tiempo_display = tk.Label(parent, textvariable=self.tiempo_var,
                                 font=('Consolas', 28, 'bold'),
                                 bg='black', fg='#00FF00',
                                 width=15, height=2, relief=tk.RAISED)
        tiempo_display.pack(pady=(0, 15))
        
        # Botones principales
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(pady=10)
        
        self.btn_iniciar = ttk.Button(btn_frame, text="▶ Iniciar", 
                                     command=self.iniciar_cronometro)
        self.btn_iniciar.grid(row=0, column=0, padx=5)
        
        self.btn_pausar = ttk.Button(btn_frame, text="⏸ Pausar", 
                                    command=self.pausar_cronometro, 
                                    state='disabled')
        self.btn_pausar.grid(row=0, column=1, padx=5)
        
        self.btn_reiniciar = ttk.Button(btn_frame, text="⏹ Reiniciar", 
                                       command=self.reiniciar_cronometro)
        self.btn_reiniciar.grid(row=0, column=2, padx=5)
        
        # Botones secundarios
        btn_frame2 = ttk.Frame(parent)
        btn_frame2.pack(pady=5)
        
        ttk.Button(btn_frame2, text="⏱ Toma Tiempo", 
                  command=self.tomar_tiempo).grid(row=0, column=0, padx=5)
        
        ttk.Button(btn_frame2, text="📊 Ver Vueltas", 
                  command=self.mostrar_vueltas).grid(row=0, column=1, padx=5)
        
        ttk.Button(btn_frame2, text="🧹 Limpiar", 
                  command=self.limpiar_vueltas).grid(row=0, column=2, padx=5)
        
        # Lista de vueltas
        vuelta_frame = ttk.LabelFrame(parent, text="⏱ Tiempos Registrados", padding="5")
        vuelta_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        columns = ('#', 'Tiempo', 'Diferencia')
        self.tree = ttk.Treeview(vuelta_frame, columns=columns, show='headings', height=8)
        
        self.tree.heading('#', text='#')
        self.tree.heading('Tiempo', text='Tiempo Total')
        self.tree.heading('Diferencia', text='Diferencia')
        
        self.tree.column('#', width=40)
        self.tree.column('Tiempo', width=120)
        self.tree.column('Diferencia', width=120)
        
        scrollbar = ttk.Scrollbar(vuelta_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def crear_pestana_temporizador(self, parent):
        """Crea la pestaña del temporizador"""
        # Display del temporizador
        self.temp_tiempo_var = tk.StringVar(value="00:00:00")
        temp_display = tk.Label(parent, textvariable=self.temp_tiempo_var,
                               font=('Consolas', 32, 'bold'),
                               bg='black', fg='#FFA500',
                               width=15, height=2, relief=tk.RAISED)
        temp_display.pack(pady=(0, 15))
        
        # Configurar tiempo
        config_frame = ttk.LabelFrame(parent, text="🕐 Configurar Tiempo", padding="10")
        config_frame.pack(pady=10, fill=tk.X)
        
        ttk.Label(config_frame, text="Horas:").grid(row=0, column=0, padx=5)
        self.horas_var = tk.StringVar(value="0")
        spin_horas = ttk.Spinbox(config_frame, from_=0, to=23, width=5,
                                textvariable=self.horas_var)
        spin_horas.grid(row=0, column=1, padx=5)
        
        ttk.Label(config_frame, text="Minutos:").grid(row=0, column=2, padx=5)
        self.minutos_var = tk.StringVar(value="1")
        spin_minutos = ttk.Spinbox(config_frame, from_=0, to=59, width=5,
                                  textvariable=self.minutos_var)
        spin_minutos.grid(row=0, column=3, padx=5)
        
        ttk.Label(config_frame, text="Segundos:").grid(row=0, column=4, padx=5)
        self.segundos_var = tk.StringVar(value="0")
        spin_segundos = ttk.Spinbox(config_frame, from_=0, to=59, width=5,
                                   textvariable=self.segundos_var)
        spin_segundos.grid(row=0, column=5, padx=5)
        
        # Botones del temporizador
        btn_temp_frame = ttk.Frame(parent)
        btn_temp_frame.pack(pady=10)
        
        self.btn_iniciar_temp = ttk.Button(btn_temp_frame, text="▶ Iniciar Temporizador",
                                          command=self.iniciar_temporizador)
        self.btn_iniciar_temp.grid(row=0, column=0, padx=5)
        
        self.btn_pausar_temp = ttk.Button(btn_temp_frame, text="⏸ Pausar",
                                         command=self.pausar_temporizador, state='disabled')
        self.btn_pausar_temp.grid(row=0, column=1, padx=5)
        
        self.btn_detener_temp = ttk.Button(btn_temp_frame, text="⏹ Detener",
                                          command=self.detener_temporizador)
        self.btn_detener_temp.grid(row=0, column=2, padx=5)
        
        # Información
        self.temp_info_var = tk.StringVar(value="No hay temporizador programado")
        temp_info_label = tk.Label(parent, textvariable=self.temp_info_var,
                                  font=('Arial', 9), fg='gray')
        temp_info_label.pack(pady=5)
    
    def formato_tiempo(self, segundos):
        """Convierte segundos a formato HH:MM:SS.ms"""
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = segundos % 60
        return f"{horas:02d}:{minutos:02d}:{segs:05.2f}"
    
    def formato_tiempo_temp(self, segundos):
        """Convierte segundos a formato HH:MM:SS para temporizador"""
        horas = int(segundos // 3600)
        minutos = int((segundos % 3600) // 60)
        segs = int(segundos % 60)
        return f"{horas:02d}:{minutos:02d}:{segs:02d}"
    
    # ========== FUNCIONES CRONÓMETRO ==========
    
    def actualizar_tiempo_cronometro(self):
        """Actualiza el display del cronómetro"""
        if self.corriendo:
            tiempo_actual = time.time() - self.inicio_tiempo + self.tiempo_transcurrido
            self.tiempo_var.set(self.formato_tiempo(tiempo_actual))
            self.root.after(50, self.actualizar_tiempo_cronometro)
    
    def actualizar_display(self):
        """Actualiza la información en pantalla"""
        if not self.corriendo:
            tiempo_mostrar = self.tiempo_transcurrido if self.tiempo_transcurrido > 0 else 0
            self.tiempo_var.set(self.formato_tiempo(tiempo_mostrar))
    
    def iniciar_cronometro(self):
        """Inicia el cronómetro"""
        if not self.corriendo:
            self.corriendo = True
            self.inicio_tiempo = time.time()
            self.estado_var.set("▶ Cronómetro corriendo...")
            self.btn_iniciar.config(state='disabled')
            self.btn_pausar.config(state='normal')
            self.actualizar_tiempo_cronometro()
    
    def pausar_cronometro(self):
        """Pausa el cronómetro"""
        if self.corriendo:
            self.corriendo = False
            self.tiempo_transcurrido += time.time() - self.inicio_tiempo
            self.estado_var.set("⏸ Cronómetro pausado")
            self.btn_iniciar.config(state='normal')
            self.btn_pausar.config(state='disabled')
            self.actualizar_display()
    
    def reiniciar_cronometro(self):
        """Reinicia el cronómetro"""
        self.corriendo = False
        self.tiempo_transcurrido = 0
        self.inicio_tiempo = 0
        self.estado_var.set("⏹ Cronómetro reiniciado")
        self.btn_iniciar.config(state='normal')
        self.btn_pausar.config(state='disabled')
        self.actualizar_display()
    
    def tomar_tiempo(self):
        """Toma un tiempo (vuelta)"""
        if self.corriendo or self.tiempo_transcurrido > 0:
            if self.corriendo:
                tiempo_actual = time.time() - self.inicio_tiempo + self.tiempo_transcurrido
            else:
                tiempo_actual = self.tiempo_transcurrido
            
            if self.vueltas:
                ultimo_tiempo = self.vueltas[-1]['tiempo']
                diferencia = tiempo_actual - ultimo_tiempo
            else:
                diferencia = tiempo_actual
            
            vuelta_num = len(self.vueltas) + 1
            self.vueltas.append({
                'numero': vuelta_num,
                'tiempo': tiempo_actual,
                'diferencia': diferencia
            })
            
            self.actualizar_lista_vueltas()
            self.estado_var.set(f"⏱ Tiempo #{vuelta_num} registrado")
    
    def actualizar_lista_vueltas(self):
        """Actualiza la lista de vueltas en el Treeview"""
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        for i, vuelta in enumerate(self.vueltas):
            tiempo_str = self.formato_tiempo(vuelta['tiempo'])
            diff_str = self.formato_diferencia(vuelta['diferencia'])
            
            if i == 0:
                diff_str = "-"
            elif vuelta['diferencia'] > 0:
                diff_str = f"+{diff_str}"
            
            self.tree.insert('', tk.END, values=(
                vuelta['numero'],
                tiempo_str,
                diff_str
            ))
    
    def formato_diferencia(self, segundos):
        """Formato para diferencias de tiempo"""
        if segundos < 60:
            return f"{segundos:.2f}s"
        elif segundos < 3600:
            minutos = segundos // 60
            segs = segundos % 60
            return f"{int(minutos)}m {segs:.1f}s"
        else:
            horas = segundos // 3600
            minutos = (segundos % 3600) // 60
            return f"{int(horas)}h {int(minutos)}m"
    
    def mostrar_vueltas(self):
        """Muestra estadísticas de las vueltas"""
        if not self.vueltas:
            self.estado_var.set("📊 No hay tiempos registrados")
            return
        
        total_vueltas = len(self.vueltas)
        if total_vueltas > 1:
            mejor_tiempo = min(vuelta['diferencia'] for vuelta in self.vueltas[1:])
            promedio = sum(vuelta['diferencia'] for vuelta in self.vueltas[1:]) / (total_vueltas - 1)
            stats = f"📊 Estadísticas: {total_vueltas} tiempos | Mejor: {self.formato_diferencia(mejor_tiempo)} | Promedio: {self.formato_diferencia(promedio)}"
        else:
            stats = f"📊 Total: {total_vueltas} tiempo registrado"
        
        self.estado_var.set(stats)
    
    def limpiar_vueltas(self):
        """Limpia todos los tiempos registrados"""
        self.vueltas = []
        self.actualizar_lista_vueltas()
        self.estado_var.set("🧹 Tiempos limpiados")
    
    # ========== FUNCIONES TEMPORIZADOR ==========
    
    def iniciar_temporizador(self):
        """Inicia el temporizador"""
        if not self.temporizador_corriendo:
            try:
                horas = int(self.horas_var.get())
                minutos = int(self.minutos_var.get())
                segundos = int(self.segundos_var.get())
                
                self.tiempo_objetivo = horas * 3600 + minutos * 60 + segundos
                
                if self.tiempo_objetivo <= 0:
                    messagebox.showwarning("Advertencia", "El tiempo debe ser mayor a 0")
                    return
                
                self.tiempo_restante = self.tiempo_objetivo
                self.temporizador_corriendo = True
                
                # Actualizar información
                tiempo_programado = self.formato_tiempo_temp(self.tiempo_objetivo)
                self.temp_info_var.set(f"⏰ Programado: {tiempo_programado} - Finaliza a las {time.strftime('%H:%M:%S', time.localtime(time.time() + self.tiempo_objetivo))}")
                
                self.estado_var.set("⏰ Temporizador iniciado")
                self.btn_iniciar_temp.config(state='disabled')
                self.btn_pausar_temp.config(state='normal')
                
                self.actualizar_temporizador()
                
            except ValueError:
                messagebox.showerror("Error", "Ingrese valores numéricos válidos")
    
    def actualizar_temporizador(self):
        """Actualiza el display del temporizador"""
        if self.temporizador_corriendo and self.tiempo_restante > 0:
            # Cambiar color cuando quedan 10 segundos o menos
            if self.tiempo_restante <= 10:
                self.temp_tiempo_var.set(f"⏰ {self.formato_tiempo_temp(self.tiempo_restante)}")
            else:
                self.temp_tiempo_var.set(self.formato_tiempo_temp(self.tiempo_restante))
            
            self.tiempo_restante -= 1
            self.root.after(1000, self.actualizar_temporizador)
        
        elif self.temporizador_corriendo and self.tiempo_restante <= 0:
            self.temporizador_finalizado()
    
    def temporizador_finalizado(self):
        """Se ejecuta cuando el temporizador termina"""
        self.temporizador_corriendo = False
        
        # Restaurar botones
        self.btn_iniciar_temp.config(state='normal')
        self.btn_pausar_temp.config(state='disabled')
        
        # Mostrar información del temporizador que finalizó
        tiempo_programado = self.formato_tiempo_temp(self.tiempo_objetivo)
        self.temp_info_var.set(f"✅ Temporizador finalizado: estaba programado para {tiempo_programado}")
        self.estado_var.set("⏰ Temporizador finalizado - ¡TIEMPO TERMINADO!")
        
        # Mostrar mensaje estilo "batería baja"
        self.mostrar_alarma_bateria_baja()
    
    def mostrar_alarma_bateria_baja(self):
        """Muestra la alarma estilo 'batería baja' cuando se acaba el tiempo"""
        # Crear ventana emergente
        alarma_window = tk.Toplevel(self.root)
        alarma_window.title("Alarma")
        alarma_window.geometry("350x200")
        alarma_window.resizable(False, False)
        alarma_window.transient(self.root)
        alarma_window.grab_set()
        
        # Hacer que la ventana sea siempre visible
        alarma_window.attributes('-topmost', True)
        
        # Centrar la ventana
        alarma_window.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 50,
            self.root.winfo_rooty() + 50
        ))
        
        # Configurar contenido
        frame = ttk.Frame(alarma_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # Icono de batería (simulado con texto)
        battery_icon = """
        ╔══════════════════════════╗
        ║    ████████████▒▒▒▒▒▒    ║
        ║    ████████████▒▒▒▒▒▒    ║
        ║    ████████████▒▒▒▒▒▒    ║
        ║    ████████████▒▒▒▒▒▒    ║
        ║    ████████████▒▒▒▒▒▒    ║
        ║                          ║
        ║   ¡SE ACABÓ EL TIEMPO!   ║
        ╚══════════════════════════╝
        """
        
        # Mostrar icono de batería
        ttk.Label(frame, text="⚠️ ¡ALERTA! ⚠️", 
                 font=('Arial', 14, 'bold'), 
                 foreground='red').pack(pady=(0, 10))
        
        # Mostrar mensaje de batería baja
        tiempo_programado = self.formato_tiempo_temp(self.tiempo_objetivo)
        mensaje = f"""¡El temporizador ha finalizado!

⏰ Tiempo programado: {tiempo_programado}
⏰ Hora de inicio: {time.strftime('%H:%M:%S', time.localtime(time.time() - self.tiempo_objetivo))}
⏰ Hora de finalización: {time.strftime('%H:%M:%S')}

¡Es hora de tomar acción!"""
        
        ttk.Label(frame, text=mensaje, 
                 font=('Arial', 10),
                 justify=tk.LEFT).pack(pady=10)
        
        # Botón para cerrar
        btn_cerrar = ttk.Button(frame, text="Aceptar", 
                               command=alarma_window.destroy,
                               style='Alarma.TButton')
        btn_cerrar.pack(pady=10)
        
        # Configurar estilo para el botón de alarma
        style = ttk.Style()
        style.configure('Alarma.TButton', 
                       foreground='white',
                       background='red',
                       font=('Arial', 10, 'bold'))
        
        # Hacer parpadear la ventana
        self.hacer_parpadear(alarma_window)
        
        # Reproducir sonido (si está disponible)
        self.reproducir_sonido_alarma()
    
    def hacer_parpadear(self, ventana):
        """Hace parpadear la ventana de alarma"""
        def alternar_color():
            actual_bg = ventana.cget('bg')
            nuevo_bg = '#FFCCCC' if actual_bg == 'SystemButtonFace' else 'SystemButtonFace'
            ventana.configure(bg=nuevo_bg)
            ventana.after(500, alternar_color)
        
        alternar_color()
    
    def reproducir_sonido_alarma(self):
        """Intenta reproducir un sonido de alarma"""
        try:
            # Para Windows
            if SISTEMA_OPERATIVO == 'Windows':
                import winsound
                for _ in range(5):
                    winsound.Beep(1000, 300)
                    time.sleep(0.2)
            # Para macOS
            elif SISTEMA_OPERATIVO == 'Darwin':
                import os
                os.system('afplay /System/Library/Sounds/Ping.aiff')
            # Para Linux
            elif SISTEMA_OPERATIVO == 'Linux':
                import os
                os.system('beep -f 1000 -l 300')
        except:
            # Si no se puede reproducir sonido, al menos hacer el sonido del sistema
            self.root.bell()
            for _ in range(3):
                self.root.update()
                time.sleep(0.3)
    
    def pausar_temporizador(self):
        """Pausa el temporizador"""
        if self.temporizador_corriendo:
            self.temporizador_corriendo = False
            self.temporizador_pausado = True
            self.tiempo_pausa = self.tiempo_restante
            self.estado_var.set("⏸ Temporizador pausado")
            self.btn_iniciar_temp.config(state='normal')
            self.btn_pausar_temp.config(state='disabled')
    
    def detener_temporizador(self):
        """Detiene el temporizador"""
        self.temporizador_corriendo = False
        self.tiempo_restante = 0
        self.temp_tiempo_var.set("00:00:00")
        self.temp_info_var.set("No hay temporizador programado")
        self.estado_var.set("⏹ Temporizador detenido")
        self.btn_iniciar_temp.config(state='normal')
        self.btn_pausar_temp.config(state='disabled')

def main():
    root = tk.Tk()
    app = CronometroCompleto(root)
    root.mainloop()

if __name__ == "__main__":
    main()