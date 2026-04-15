# software_optimizacion.py
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import hashlib
import json
import os
import subprocess
import psutil
from PIL import Image, ImageTk
import shutil
from datetime import datetime
import threading
import webbrowser

class GameOptimizer:
    def __init__(self, root):
        self.root = root
        self.root.title("Game Optimizer Pro")
        self.root.geometry("1200x700")
        self.root.configure(bg='#1a1a2e')
        
        self.usuario_actual = None
        self.es_premium = False
        self.claves_premium = self.cargar_claves()
        self.usuarios = self.cargar_usuarios()
        self.juegos_detectados = []
        self.foto_perfil = None
        
        self.mostrar_login()
    
    def cargar_usuarios(self):
        if os.path.exists("usuarios.json"):
            with open("usuarios.json", "r") as f:
                return json.load(f)
        return {}
    
    def guardar_usuarios(self):
        with open("usuarios.json", "w") as f:
            json.dump(self.usuarios, f)
    
    def cargar_claves(self):
        if os.path.exists("claves_premium.json"):
            with open("claves_premium.json", "r") as f:
                return json.load(f)
        return {}
    
    def guardar_claves(self):
        with open("claves_premium.json", "w") as f:
            json.dump(self.claves_premium, f)
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def mostrar_login(self):
        self.limpiar_ventana()
        
        frame = tk.Frame(self.root, bg='#16213e')
        frame.pack(expand=True)
        
        tk.Label(frame, text="Game Optimizer Pro", font=("Arial", 24, "bold"), 
                bg='#16213e', fg='#e94560').pack(pady=20)
        
        tk.Label(frame, text="Usuario:", bg='#16213e', fg='white').pack()
        entry_user = tk.Entry(frame, width=30)
        entry_user.pack(pady=5)
        
        tk.Label(frame, text="Contraseña:", bg='#16213e', fg='white').pack()
        entry_pass = tk.Entry(frame, width=30, show="*")
        entry_pass.pack(pady=5)
        
        btn_frame = tk.Frame(frame, bg='#16213e')
        btn_frame.pack(pady=10)
        
        tk.Button(btn_frame, text="Login", command=lambda: self.login(entry_user.get(), entry_pass.get()),
                 bg='#e94560', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Registro", command=self.mostrar_registro,
                 bg='#0f3460', fg='white').pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Google", command=self.login_google,
                 bg='#4285f4', fg='white').pack(side=tk.LEFT, padx=5)
    
    def login(self, user, password):
        if user in self.usuarios and self.usuarios[user]["password"] == self.hash_password(password):
            self.usuario_actual = user
            self.es_premium = self.usuarios[user].get("premium", False)
            self.detectar_juegos()
            self.mostrar_menu_principal()
        else:
            messagebox.showerror("Error", "Credenciales incorrectas")
    
    def login_google(self):
        # Simulación de login con Google
        messagebox.showinfo("Google Login", "Demo: Redirigiendo a Google...\n(Implementar OAuth real requeriría backend)")
        # Aquí iría la integración real con Google OAuth
        self.usuario_actual = "usuario_google_temp"
        self.usuarios[self.usuario_actual] = {"password": "google_auth", "premium": False}
        self.guardar_usuarios()
        self.mostrar_menu_principal()
    
    def mostrar_registro(self):
        self.limpiar_ventana()
        
        frame = tk.Frame(self.root, bg='#16213e')
        frame.pack(expand=True)
        
        tk.Label(frame, text="Registro", font=("Arial", 20, "bold"), 
                bg='#16213e', fg='#e94560').pack(pady=20)
        
        tk.Label(frame, text="Usuario:", bg='#16213e', fg='white').pack()
        entry_user = tk.Entry(frame)
        entry_user.pack(pady=5)
        
        tk.Label(frame, text="Contraseña:", bg='#16213e', fg='white').pack()
        entry_pass = tk.Entry(frame, show="*")
        entry_pass.pack(pady=5)
        
        tk.Label(frame, text="Confirmar:", bg='#16213e', fg='white').pack()
        entry_confirm = tk.Entry(frame, show="*")
        entry_confirm.pack(pady=5)
        
        def registrar():
            user = entry_user.get()
            password = entry_pass.get()
            confirm = entry_confirm.get()
            
            if not user or not password:
                messagebox.showerror("Error", "Complete todos los campos")
                return
            
            if password != confirm:
                messagebox.showerror("Error", "Las contraseñas no coinciden")
                return
            
            if user in self.usuarios:
                messagebox.showerror("Error", "Usuario ya existe")
                return
            
            self.usuarios[user] = {
                "password": self.hash_password(password),
                "premium": False,
                "fecha_registro": str(datetime.now())
            }
            self.guardar_usuarios()
            messagebox.showinfo("Éxito", "Usuario registrado")
            self.mostrar_login()
        
        tk.Button(frame, text="Registrar", command=registrar,
                 bg='#e94560', fg='white').pack(pady=10)
        tk.Button(frame, text="Volver", command=self.mostrar_login,
                 bg='#0f3460', fg='white').pack()
    
    def mostrar_menu_principal(self):
        self.limpiar_ventana()
        
        # Panel izquierdo - Menú
        menu_frame = tk.Frame(self.root, bg='#0f3460', width=200)
        menu_frame.pack(side=tk.LEFT, fill=tk.Y)
        menu_frame.pack_propagate(False)
        
        # Foto de perfil
        self.foto_label = tk.Label(menu_frame, bg='#0f3460')
        self.foto_label.pack(pady=10)
        self.actualizar_foto_perfil()
        
        tk.Button(menu_frame, text="Cambiar foto", command=self.cambiar_foto,
                 bg='#16213e', fg='white').pack(pady=5)
        
        tk.Button(menu_frame, text="🎮 Optimizar Juegos", command=self.optimizar,
                 bg='#e94560', fg='white', font=("Arial", 12)).pack(fill=tk.X, pady=5)
        tk.Button(menu_frame, text="💎 VIP / Premium", command=self.mostrar_vip,
                 bg='#e94560', fg='white', font=("Arial", 12)).pack(fill=tk.X, pady=5)
        tk.Button(menu_frame, text="🎯 Mis Juegos", command=self.mostrar_juegos,
                 bg='#e94560', fg='white', font=("Arial", 12)).pack(fill=tk.X, pady=5)
        
        if self.usuario_actual == "admin":
            tk.Button(menu_frame, text="🔧 Admin Tools", command=self.admin_panel,
                     bg='#f39c12', fg='white', font=("Arial", 12)).pack(fill=tk.X, pady=5)
        
        tk.Button(menu_frame, text="🚪 Cerrar Sesión", command=self.mostrar_login,
                 bg='#2c3e50', fg='white', font=("Arial", 12)).pack(fill=tk.X, pady=5)
        
        # Panel derecho - Contenido
        self.content_frame = tk.Frame(self.root, bg='#1a1a2e')
        self.content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(self.content_frame, text=f"Bienvenido {self.usuario_actual}", 
                font=("Arial", 18), bg='#1a1a2e', fg='white').pack(pady=20)
        
        if self.es_premium:
            tk.Label(self.content_frame, text="⭐ MODO PREMIUM ACTIVO ⭐", 
                    font=("Arial", 14), bg='#1a1a2e', fg='gold').pack()
    
    def cambiar_foto(self):
        archivo = filedialog.askopenfilename(filetypes=[("PNG files", "*.png")])
        if archivo:
            # Crear directorio de perfiles
            os.makedirs("perfiles", exist_ok=True)
            destino = f"perfiles/{self.usuario_actual}_foto.png"
            shutil.copy(archivo, destino)
            self.actualizar_foto_perfil()
    
    def actualizar_foto_perfil(self):
        foto_path = f"perfiles/{self.usuario_actual}_foto.png"
        if os.path.exists(foto_path):
            img = Image.open(foto_path)
            img = img.resize((100, 100), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.foto_label.config(image=photo)
            self.foto_label.image = photo
    
    def detectar_juegos(self):
        # Detectar juegos comunes instalados
        rutas_comunes = [
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            os.path.expanduser("~\\AppData\\Local")
        ]
        
        juegos = ["Steam", "Epic Games", "Battle.net", "Riot Games", "Minecraft"]
        
        self.juegos_detectados = []
        for ruta in rutas_comunes:
            if os.path.exists(ruta):
                for juego in juegos:
                    if os.path.exists(os.path.join(ruta, juego)):
                        self.juegos_detectados.append(juego)
        
        # Guardar detección
        if self.usuario_actual:
            self.usuarios[self.usuario_actual]["juegos_detectados"] = self.juegos_detectados
            self.guardar_usuarios()
    
    def optimizar(self):
        if not self.es_premium and self.usuario_actual != "admin":
            messagebox.showwarning("Premium", "Esta función es solo para usuarios Premium")
            return
        
        messagebox.showinfo("Optimizando", "Cerrando procesos innecesarios...")
        
        # Cerrar procesos que consumen recursos
        procesos_innecesarios = ["spotify.exe", "discord.exe", "chrome.exe", "firefox.exe"]
        for proc in psutil.process_iter(['name']):
            try:
                if proc.info['name'].lower() in procesos_innecesarios:
                    proc.terminate()
            except:
                pass
        
        # Dar alta prioridad al juego (ejemplo)
        for proc in psutil.process_iter(['name']):
            try:
                if any(game.lower() in proc.info['name'].lower() for game in ["game", "fortnite", "valorant"]):
                    proc.nice(psutil.HIGH_PRIORITY_CLASS)
            except:
                pass
        
        messagebox.showinfo("Optimización", "Optimización completada!\nRecuerda mantener el software abierto mientras juegas")
    
    def mostrar_vip(self):
        self.limpiar_contenido()
        
        tk.Label(self.content_frame, text="Membresía Premium", font=("Arial", 20, "bold"),
                bg='#1a1a2e', fg='gold').pack(pady=20)
        
        if self.es_premium:
            tk.Label(self.content_frame, text="✅ Ya eres usuario Premium!", 
                    font=("Arial", 16), bg='#1a1a2e', fg='green').pack(pady=20)
            return
        
        tk.Label(self.content_frame, text="Beneficios Premium:", 
                font=("Arial", 14), bg='#1a1a2e', fg='white').pack()
        beneficios = ["• Optimización avanzada de juegos", "• Prioridad en procesos", "• Sin publicidad", "• Soporte prioritario"]
        for b in beneficios:
            tk.Label(self.content_frame, text=b, bg='#1a1a2e', fg='white').pack()
        
        tk.Label(self.content_frame, text="\nPrecio: $5 USD (único pago)", 
                font=("Arial", 12), bg='#1a1a2e', fg='white').pack(pady=10)
        
        # PayPal (demo - redirige a PayPal)
        def pagar_paypal():
            webbrowser.open("https://www.paypal.com/donate/?hosted_button_id=DEMO")
            messagebox.showinfo("PayPal", "Donación realizada. Enviaremos tu clave al correo en 24h")
        
        tk.Button(self.content_frame, text="💳 Pagar con PayPal", command=pagar_paypal,
                 bg='#0070ba', fg='white', font=("Arial", 12)).pack(pady=10)
        
        # Canjear clave
        tk.Label(self.content_frame, text="\n¿Ya tienes una clave? Canjéala:", 
                bg='#1a1a2e', fg='white').pack()
        entry_clave = tk.Entry(self.content_frame, width=30)
        entry_clave.pack(pady=5)
        
        def canjear():
            clave = entry_clave.get()
            if clave in self.claves_premium and not self.claves_premium[clave]["usado"]:
                self.claves_premium[clave]["usado"] = True
                self.claves_premium[clave]["usuario"] = self.usuario_actual
                self.usuarios[self.usuario_actual]["premium"] = True
                self.es_premium = True
                self.guardar_claves()
                self.guardar_usuarios()
                messagebox.showinfo("Éxito", "¡Premium activado!")
                self.mostrar_menu_principal()
            else:
                messagebox.showerror("Error", "Clave inválida o ya usada")
        
        tk.Button(self.content_frame, text="Canjear Clave", command=canjear,
                 bg='#e94560', fg='white').pack(pady=5)
    
    def mostrar_juegos(self):
        self.limpiar_contenido()
        
        tk.Label(self.content_frame, text="Mis Juegos Detectados", font=("Arial", 18, "bold"),
                bg='#1a1a2e', fg='white').pack(pady=20)
        
        if not self.juegos_detectados:
            tk.Label(self.content_frame, text="No se detectaron juegos instalados", 
                    bg='#1a1a2e', fg='white').pack()
        else:
            for juego in self.juegos_detectados:
                tk.Label(self.content_frame, text=f"✅ {juego}", 
                        bg='#1a1a2e', fg='lightgreen', font=("Arial", 12)).pack()
        
        tk.Button(self.content_frame, text="Actualizar lista", command=self.detectar_juegos,
                 bg='#0f3460', fg='white').pack(pady=10)
    
    def admin_panel(self):
        if self.usuario_actual != "admin":
            messagebox.showerror("Acceso denegado", "Solo administradores")
            return
        
        self.limpiar_contenido()
        
        tk.Label(self.content_frame, text="Panel de Administración", font=("Arial", 20, "bold"),
                bg='#1a1a2e', fg='red').pack(pady=20)
        
        # Generar clave premium
        tk.Label(self.content_frame, text="Generar nueva clave Premium:", 
                bg='#1a1a2e', fg='white').pack()
        
        def generar_clave():
            import random, string
            clave = ''.join(random.choices(string.ascii_uppercase + string.digits, k=16))
            self.claves_premium[clave] = {
                "creada": str(datetime.now()),
                "usado": False,
                "usuario": None
            }
            self.guardar_claves()
            messagebox.showinfo("Clave generada", f"Clave: {clave}\nCopia esta clave para distribuir")
        
        tk.Button(self.content_frame, text="Generar Nueva Clave", command=generar_clave,
                 bg='#e94560', fg='white', font=("Arial", 12)).pack(pady=10)
        
        # Listar claves
        tk.Label(self.content_frame, text="\nClaves generadas:", 
                bg='#1a1a2e', fg='white').pack()
        
        texto_claves = tk.Text(self.content_frame, height=10, width=50)
        texto_claves.pack(pady=10)
        
        for clave, info in self.claves_premium.items():
            estado = "Usada" if info["usado"] else "Disponible"
            usuario = info.get("usuario", "N/A")
            texto_claves.insert(tk.END, f"{clave} - {estado} - Usuario: {usuario}\n")
        
        # Usuarios registrados
        tk.Label(self.content_frame, text="\nUsuarios registrados:", 
                bg='#1a1a2e', fg='white').pack()
        
        texto_usuarios = tk.Text(self.content_frame, height=8, width=50)
        texto_usuarios.pack(pady=10)
        
        for user, data in self.usuarios.items():
            premium = "Premium" if data.get("premium") else "Free"
            texto_usuarios.insert(tk.END, f"{user} - {premium}\n")
    
    def limpiar_contenido(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

# Crear usuario admin por defecto
def setup_admin():
    if not os.path.exists("usuarios.json"):
        usuarios = {}
    else:
        with open("usuarios.json", "r") as f:
            usuarios = json.load(f)
    
    if "admin" not in usuarios:
        usuarios["admin"] = {
            "password": hashlib.sha256("admin123".encode()).hexdigest(),
            "premium": True
        }
        with open("usuarios.json", "w") as f:
            json.dump(usuarios, f)

if __name__ == "__main__":
    setup_admin()
    root = tk.Tk()
    app = GameOptimizer(root)
    root.mainloop()