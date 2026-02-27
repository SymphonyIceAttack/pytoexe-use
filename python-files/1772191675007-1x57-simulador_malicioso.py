import ctypes
import time
import tkinter as tk
import threading
import sys
import os

# En Windows, la librería keyboard funciona sin problemas de permisos
try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("⚠️  Librería 'keyboard' no instalada. Ejecuta: pip install keyboard")

class SimuladorMalicioso:
    def __init__(self):
        self.activo = True
        self.password_correcta = "0000"
        self.es_windows = True  # Forzamos modo Windows
        
    def cambiar_botones_raton(self):
        """Intercambia los botones del ratón (funciona en Windows)"""
        try:
            # 1 intercambia los botones, 0 los restaura
            ctypes.windll.user32.SwapMouseButton(1)
            print("✅ Botones del ratón intercambiados (ahora el derecho es el principal)")
            return True
        except Exception as e:
            print(f"❌ Error al intercambiar botones: {e}")
            return False
        
    def cambiar_idioma_teclado(self):
        """Cambia el idioma del teclado a Árabe (simulado por seguridad)"""
        try:
            # Código para cambiar idioma (solo como referencia educativa)
            # En un caso real, se usaría: ctypes.windll.user32.LoadKeyboardLayoutW()
            
            print("⚠️ [SIMULACIÓN] Se intentaría cambiar el teclado a Árabe")
            print("   Por seguridad, esta función está desactivada")
            print("   En un escenario real, se usaría LoadKeyboardLayoutW()")
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
        
    def restaurar_normal(self):
        """Restaura la configuración normal"""
        try:
            ctypes.windll.user32.SwapMouseButton(0)
            print("\n✅ Configuración restaurada a la normalidad")
            print("   Botones del ratón vuelven a su estado original")
            return True
        except Exception as e:
            print(f"❌ Error al restaurar: {e}")
            return False
        
    def verificar_password(self):
        """Ventana para verificar la contraseña"""
        root = tk.Tk()
        root.title("🔐 VERIFICACIÓN REQUERIDA - SISTEMA BLOQUEADO")
        root.attributes('-topmost', True)  # Siempre al frente
        root.geometry("450x250")
        root.resizable(False, False)
        root.configure(bg='#1a1a1a')
        
        # Centrar ventana en la pantalla
        root.eval('tk::PlaceWindow . center')
        
        resultado = {'verificado': False}
        
        def verificar():
            password = entry.get()
            if password == self.password_correcta:
                resultado['verificado'] = True
                root.destroy()
            else:
                label_error.config(text="❌ CONTRASEÑA INCORRECTA", fg="#ff4444")
                entry.delete(0, tk.END)
                entry.focus()
        
        def cerrar_emergencia():
            """Por si el usuario necesita salir (solo para pruebas)"""
            if tk.messagebox.askyesno("Salida de emergencia", 
                                     "¿Estás seguro? Se perderán los cambios no guardados."):
                resultado['verificado'] = False
                root.destroy()
        
        # Interfaz gráfica
        tk.Label(root, text="⚠️  SISTEMA BLOQUEADO  ⚠️", 
                font=("Arial", 16, "bold"), fg="#ffaa00", bg='#1a1a1a').pack(pady=15)
        
        tk.Label(root, text="Se ha detectado una modificación en la configuración del sistema",
                font=("Arial", 10), fg="#cccccc", bg='#1a1a1a').pack()
        
        tk.Label(root, text="Ingrese la contraseña para restaurar:", 
                font=("Arial", 11), fg="white", bg='#1a1a1a').pack(pady=10)
        
        entry = tk.Entry(root, show="*", font=("Arial", 14), width=15,
                        bg='#333333', fg='white', insertbackground='white',
                        justify='center')
        entry.pack(pady=5)
        entry.focus()
        
        # Botones
        frame_botones = tk.Frame(root, bg='#1a1a1a')
        frame_botones.pack(pady=15)
        
        tk.Button(frame_botones, text="VERIFICAR", command=verificar,
                 bg='#4CAF50', fg='white', font=("Arial", 11, "bold"),
                 width=12, height=1).pack(side='left', padx=5)
        
        tk.Button(frame_botones, text="SALIR (EMERGENCIA)", command=cerrar_emergencia,
                 bg='#666666', fg='white', font=("Arial", 10),
                 width=12, height=1).pack(side='left', padx=5)
        
        label_error = tk.Label(root, text="", font=("Arial", 10), bg='#1a1a1a')
        label_error.pack()
        
        # Información
        info_frame = tk.Frame(root, bg='#2a2a2a')
        info_frame.pack(side='bottom', fill='x', padx=10, pady=10)
        
        tk.Label(info_frame, text="Contraseña por defecto: 0000", 
                font=("Arial", 8), fg="#888888", bg='#2a2a2a').pack()
        
        tk.Label(info_frame, text="Para salir sin contraseña, cierre esta ventana", 
                font=("Arial", 8), fg="#888888", bg='#2a2a2a').pack()
        
        # Vincular teclas
        entry.bind('<Return>', lambda event: verificar())
        root.bind('<Escape>', lambda event: cerrar_emergencia())
        
        # Evitar que se pueda cerrar con Alt+F4 (opcional)
        root.protocol("WM_DELETE_WINDOW", cerrar_emergencia)
        
        root.mainloop()
        return resultado['verificado']
        
    def iniciar_simulacion(self):
        """Inicia la simulación de efectos"""
        # Limpiar pantalla
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*70)
        print(" 🔴 SIMULADOR DE SOFTWARE MALICIOSO - PRÁCTICA EDUCATIVA 🔴".center(70))
        print("="*70)
        print("\n⚠️  ADVERTENCIAS IMPORTANTES:")
        print("   • Este programa es SOLO para fines educativos")
        print("   • Ejecutar ÚNICAMENTE en máquina virtual")
        print("   • No usar en sistemas reales o de terceros")
        print("   • Asegurar tener respaldo de configuración\n")
        
        input("Presiona ENTER para continuar...")
        print("\n" + "-"*70)
        
        print("\n🔄 APLICANDO EFECTOS MALICIOSOS...\n")
        time.sleep(1)
        
        # Aplicar cambios
        self.cambiar_botones_raton()
        time.sleep(0.5)
        self.cambiar_idioma_teclado()
        
        print("\n✅ EFECTOS APLICADOS CORRECTAMENTE")
        print("   • Botones del ratón: INTERCAMBIADOS")
        print("   • Teclado: MODO ÁRABE (simulado)")
        
        print("\n🔑 INSTRUCCIONES PARA RESTAURAR:")
        print("   • Presiona CTRL+SHIFT+R en cualquier momento")
        print("   • Ingresa la contraseña: 0000")
        print("   • O ejecuta el programa nuevamente y elige restaurar\n")
        
        print("-"*70)
        print("⚠️  El programa está activo en segundo plano")
        print("   Mínimiza esta ventana pero NO LA CIERRES")
        print("-"*70 + "\n")
        
        if not KEYBOARD_AVAILABLE:
            print("❌ ERROR: Librería 'keyboard' no instalada")
            print("   Ejecuta este comando en Windows:")
            print("   pip install keyboard")
            input("\nPresiona ENTER para salir...")
            return
        
        def escuchar_comandos():
            """Hilo que escucha el atajo de teclado"""
            while self.activo:
                try:
                    if keyboard.is_pressed('ctrl+shift+r'):
                        print("\n🔍 ATENCIÓN: Se solicitó restaurar sistema")
                        if self.verificar_password():
                            self.restaurar_normal()
                            self.activo = False
                            print("\n✅ Sistema restaurado correctamente")
                            print("   Puedes cerrar esta ventana")
                            time.sleep(3)
                            os._exit(0)
                        else:
                            print("❌ Contraseña incorrecta - Intenta de nuevo")
                    time.sleep(0.3)
                except Exception as e:
                    print(f"⚠️ Error en escucha: {e}")
                    time.sleep(1)
        
        # Iniciar hilo de escucha
        thread = threading.Thread(target=escuchar_comandos, daemon=True)
        thread.start()
        
        # Mantener programa activo
        try:
            while self.activo:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n\n⚠️  PROGRAMA INTERRUMPIDO POR USUARIO")
            respuesta = input("¿Restaurar configuración antes de salir? (s/n): ")
            if respuesta.lower() in ['s', 'si', 'sí', 'y', 'yes']:
                self.restaurar_normal()
            print("\n¡Hasta luego!")

if __name__ == "__main__":
    print("🎯 GENERADOR DE SCRIPT PARA WINDOWS")
    print("Este archivo está diseñado para ejecutarse en Windows\n")
    
    # Verificar si estamos en Windows (pero no detener si no lo estamos)
    if os.name != 'nt':
        print("⚠️  Estás ejecutando esto en Linux, pero el script")
        print("   está diseñado para funcionar en Windows.")
        print("   Puedes continuar, pero algunas funciones fallarán.")
        print("   El objetivo final es copiar este archivo a Windows.\n")
        input("Presiona ENTER para continuar de todas formas...")
    
    simulador = SimuladorMalicioso()
    simulador.iniciar_simulacion()
