# sistema_adulto_mayor.py - Sistema de Control y Protección del Adulto Mayor
# Versión COMPLETA con cambio de contraseña, recuperación y mantenimiento de BD

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import os
import sys
import hashlib
import base64
import random
import string
import shutil

class DatabaseEncryptor:
    """Clase para manejar la encriptación simple de la base de datos"""
    
    def __init__(self, db_path, password):
        self.db_path = db_path
        self.db_enc_path = db_path + '.enc'
        self.password = password
    
    def _simple_encrypt(self, data):
        key = hashlib.sha256(self.password.encode()).digest()
        key_length = len(key)
        data_bytes = data if isinstance(data, bytes) else data.encode('utf-8')
        
        result = bytearray()
        for i, byte in enumerate(data_bytes):
            result.append(byte ^ key[i % key_length])
        
        return base64.b64encode(bytes(result))
    
    def _simple_decrypt(self, encrypted_data):
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            key = hashlib.sha256(self.password.encode()).digest()
            key_length = len(key)
            
            result = bytearray()
            for i, byte in enumerate(encrypted_bytes):
                result.append(byte ^ key[i % key_length])
            
            return bytes(result)
        except:
            return None
    
    def encrypt_database(self):
        if not os.path.exists(self.db_path):
            return False
        
        with open(self.db_path, 'rb') as f:
            data = f.read()
        
        encrypted_data = self._simple_encrypt(data)
        
        with open(self.db_enc_path, 'wb') as f:
            f.write(encrypted_data)
        
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        return True
    
    def decrypt_database(self):
        if not os.path.exists(self.db_enc_path):
            return False
        
        with open(self.db_enc_path, 'rb') as f:
            encrypted_data = f.read()
        
        decrypted_data = self._simple_decrypt(encrypted_data)
        
        if decrypted_data is None:
            return False
        
        with open(self.db_path, 'wb') as f:
            f.write(decrypted_data)
        return True
    
    def cleanup_decrypted(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except:
                pass

class SistemaAdultoMayor:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("🏥 Sistema de Control y Protección del Adulto Mayor - MINSAP V1.0")
        self.root.geometry("1400x750")
        self.root.configure(bg='#f0f0f0')
        
        self.center_window()
        self.get_installation_path()
        
        self.usuario_actual = None
        self.usuario_rol = None
        self.usuario_id = None
        self.db_encryptor = None
        self.conn = None
        self.cursor = None
        
        self.mostrar_login()
        self.root.mainloop()
    
    def center_window(self):
        self.root.update_idletasks()
        width = 1400
        height = 750
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
    
    def get_installation_path(self):
        if getattr(sys, 'frozen', False):
            self.base_path = os.path.dirname(sys.executable)
        else:
            self.base_path = os.path.dirname(os.path.abspath(__file__))
        
        self.data_path = os.path.join(self.base_path, '.minsap_data')
        if not os.path.exists(self.data_path):
            os.makedirs(self.data_path)
            if sys.platform == 'win32':
                try:
                    import ctypes
                    ctypes.windll.kernel32.SetFileAttributesW(self.data_path, 2)
                except:
                    pass
        
        self.db_path = os.path.join(self.data_path, 'adulto_mayor.db')
        self.backup_path = os.path.join(self.data_path, 'backups')
        if not os.path.exists(self.backup_path):
            os.makedirs(self.backup_path)
    
    def init_database(self, master_password):
        try:
            self.db_encryptor = DatabaseEncryptor(self.db_path, master_password)
            
            if self.db_encryptor.decrypt_database():
                self.connect_database()
                return True
            
            self.connect_database()
            
            # Tabla de usuarios
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE,
                    password TEXT,
                    nombre_completo TEXT,
                    rol TEXT,
                    fecha_creacion TEXT,
                    ultimo_cambio TEXT,
                    pregunta_seguridad TEXT,
                    respuesta_seguridad TEXT,
                    activo BOOLEAN DEFAULT 1
                )
            ''')
            
            # Tabla de adultos mayores
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS adultos_mayores (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tipo_registro TEXT,
                    numero INTEGER,
                    nombre TEXT,
                    apellidos TEXT,
                    fecha_nacimiento TEXT,
                    direccion TEXT,
                    app TEXT,
                    situacion_social TEXT,
                    grupo_dispensarial TEXT,
                    cmf INTEGER,
                    telefono TEXT,
                    contacto_emergencia TEXT,
                    tiene_cuidador BOOLEAN DEFAULT 0,
                    nombre_cuidador TEXT,
                    telefono_cuidador TEXT,
                    fecha_registro TEXT,
                    ultima_visita TEXT,
                    observaciones TEXT
                )
            ''')
            
            # Tabla de backup log
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS backup_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    tipo TEXT,
                    descripcion TEXT,
                    usuario TEXT
                )
            ''')
            
            # Tabla de mantenimiento log
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS mantenimiento_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fecha TEXT,
                    operacion TEXT,
                    detalles TEXT,
                    usuario TEXT
                )
            ''')
            
            # Usuario administrador por defecto
            self.cursor.execute("SELECT COUNT(*) FROM usuarios")
            if self.cursor.fetchone()[0] == 0:
                hashed = hashlib.sha256("adminglove123".encode()).hexdigest()
                pregunta = "¿Cuál es su color favorito?"
                respuesta = hashlib.sha256("azul".encode()).hexdigest()
                self.cursor.execute('''
                    INSERT INTO usuarios (username, password, nombre_completo, rol, fecha_creacion, 
                                         ultimo_cambio, pregunta_seguridad, respuesta_seguridad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', ("admin", hashed, "Administrador del Sistema", "ADMIN", 
                      datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%Y-%m-%d"),
                      pregunta, respuesta))
            
            self.conn.commit()
            self.disconnect_database()
            self.db_encryptor.encrypt_database()
            return True
            
        except Exception as e:
            print(f"Error: {e}")
            return False
    
    def connect_database(self):
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.cursor = self.conn.cursor()
            return True
        except:
            return False
    
    def disconnect_database(self):
        try:
            if self.conn:
                self.conn.close()
            if self.db_encryptor and os.path.exists(self.db_path):
                self.db_encryptor.encrypt_database()
                if os.path.exists(self.db_path):
                    os.remove(self.db_path)
        except:
            pass
    
    def registrar_mantenimiento(self, operacion, detalles):
        """Registrar operación de mantenimiento"""
        try:
            self.cursor.execute('''
                INSERT INTO mantenimiento_log (fecha, operacion, detalles, usuario)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), operacion, detalles, self.usuario_actual['username']))
            self.conn.commit()
        except:
            pass
    
    # ==================== LOGIN ====================
    
    def mostrar_login(self):
        self.limpiar_ventana()
        
        main_frame = tk.Frame(self.root, bg='#2c3e50')
        main_frame.pack(fill='both', expand=True)
        
        card = tk.Frame(main_frame, bg='white', relief='flat', bd=0)
        card.place(relx=0.5, rely=0.5, anchor='center', width=450, height=600)
        
        top_bar = tk.Frame(card, bg='#3498db', height=8)
        top_bar.pack(fill='x')
        
        tk.Label(card, text="👴", font=('Segoe UI', 56), bg='white').pack(pady=20)
        tk.Label(card, text="Sistema de Control del Adulto Mayor V1.0", font=('Segoe UI', 16, 'bold'), 
                bg='white', fg='#2c3e50').pack()
        tk.Label(card, text="Ministerio de Salud Pública", font=('Segoe UI', 10), 
                bg='white', fg='#7f8c8d').pack(pady=(0, 20))
        
        frame_user = tk.Frame(card, bg='white')
        frame_user.pack(fill='x', padx=40, pady=5)
        tk.Label(frame_user, text="Usuario", font=('Segoe UI', 11), bg='white', anchor='w').pack(fill='x')
        self.entry_usuario = tk.Entry(frame_user, font=('Segoe UI', 11), relief='solid', bd=1)
        self.entry_usuario.pack(fill='x', pady=(5, 0), ipady=8)
        
        frame_pass = tk.Frame(card, bg='white')
        frame_pass.pack(fill='x', padx=40, pady=5)
        tk.Label(frame_pass, text="Contraseña", font=('Segoe UI', 11), bg='white', anchor='w').pack(fill='x')
        self.entry_password = tk.Entry(frame_pass, font=('Segoe UI', 11), show="●", relief='solid', bd=1)
        self.entry_password.pack(fill='x', pady=(5, 0), ipady=8)
        
        btn_login = tk.Button(card, text="INICIAR SESIÓN", command=self.login,
                             font=('Segoe UI', 12, 'bold'), bg='#3498db', fg='white',
                             relief='flat', padx=30, pady=10, cursor='hand2')
        btn_login.pack(pady=15)
        
        btn_forgot = tk.Button(card, text="¿Olvidó su contraseña?", command=self.recuperar_contrasena,
                               font=('Segoe UI', 9), bg='white', fg='#e74c3c', 
                               relief='flat', cursor='hand2')
        btn_forgot.pack()
        
        tk.Label(card, text="Desarrollado por el grupo de informática del PolRLPeña", 
                font=('Segoe UI', 9), bg='white', fg='#95a5a6').pack(pady=10)
        
        self.entry_password.bind('<Return>', lambda e: self.login())
        self.entry_usuario.focus()
    
    def login(self):
        usuario = self.entry_usuario.get().strip()
        master_password = self.entry_password.get()
        
        if not usuario or not master_password:
            messagebox.showwarning("Campos vacíos", "Complete todos los campos")
            return
        
        if not self.init_database(master_password):
            messagebox.showerror("Error", "Contraseña incorrecta o base de datos corrupta")
            return
        
        self.connect_database()
        
        hashed = hashlib.sha256(master_password.encode()).hexdigest()
        
        self.cursor.execute('''
            SELECT id, username, nombre_completo, rol FROM usuarios 
            WHERE username = ? AND password = ? AND activo = 1
        ''', (usuario, hashed))
        
        user = self.cursor.fetchone()
        
        if user:
            self.usuario_actual = {'id': user[0], 'username': user[1], 'nombre': user[2], 'rol': user[3]}
            self.usuario_id = user[0]
            self.usuario_rol = user[3]
            self.disconnect_database()
            self.mostrar_principal()
        else:
            self.disconnect_database()
            messagebox.showerror("Error", "Usuario o contraseña incorrectos")
    
    # ==================== RECUPERAR CONTRASEÑA ====================
    
    def recuperar_contrasena(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Recuperar Contraseña")
        dialog.geometry("450x400")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'450x400+{x}+{y}')
        
        tk.Label(dialog, text="Recuperar Contraseña", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        frame = tk.Frame(dialog, bg='white', padx=30, pady=30)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Usuario:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_user = tk.Entry(frame, font=('Segoe UI', 11), relief='solid', bd=1)
        entry_user.pack(fill='x', pady=(0, 15), ipady=5)
        
        def verificar_pregunta():
            usuario = entry_user.get().strip()
            if not usuario:
                messagebox.showwarning("Error", "Ingrese el usuario")
                return
            
            self.connect_database()
            self.cursor.execute('''
                SELECT pregunta_seguridad FROM usuarios WHERE username = ? AND activo = 1
            ''', (usuario,))
            result = self.cursor.fetchone()
            
            if not result:
                self.disconnect_database()
                messagebox.showerror("Error", "Usuario no encontrado")
                return
            
            pregunta = result[0]
            
            resp_dialog = tk.Toplevel(dialog)
            resp_dialog.title("Pregunta de Seguridad")
            resp_dialog.geometry("450x300")
            resp_dialog.configure(bg='white')
            resp_dialog.transient(dialog)
            resp_dialog.grab_set()
            
            x2 = (resp_dialog.winfo_screenwidth() // 2) - (450 // 2)
            y2 = (resp_dialog.winfo_screenheight() // 2) - (300 // 2)
            resp_dialog.geometry(f'450x300+{x2}+{y2}')
            
            tk.Label(resp_dialog, text="Verificación de Seguridad", font=('Segoe UI', 14, 'bold'),
                    bg='#2c3e50', fg='white', pady=15).pack(fill='x')
            
            frame2 = tk.Frame(resp_dialog, bg='white', padx=30, pady=30)
            frame2.pack(fill='both', expand=True)
            
            tk.Label(frame2, text=f"Pregunta: {pregunta}", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 10))
            entry_respuesta = tk.Entry(frame2, font=('Segoe UI', 11), relief='solid', bd=1, show="●")
            entry_respuesta.pack(fill='x', pady=(0, 20), ipady=5)
            
            def validar_respuesta():
                respuesta = entry_respuesta.get().strip()
                if not respuesta:
                    messagebox.showwarning("Error", "Ingrese la respuesta")
                    return
                
                hashed_respuesta = hashlib.sha256(respuesta.encode()).hexdigest()
                
                self.cursor.execute('''
                    SELECT id FROM usuarios WHERE username = ? AND respuesta_seguridad = ?
                ''', (usuario, hashed_respuesta))
                
                if self.cursor.fetchone():
                    nueva = self.generar_contrasena_temporal()
                    hashed_nueva = hashlib.sha256(nueva.encode()).hexdigest()
                    
                    self.cursor.execute('''
                        UPDATE usuarios SET password = ?, ultimo_cambio = ? WHERE username = ?
                    ''', (hashed_nueva, datetime.now().strftime("%Y-%m-%d"), usuario))
                    self.conn.commit()
                    
                    messagebox.showinfo("Éxito", f"Su nueva contraseña temporal es:\n\n{nueva}\n\nPor favor cámbiela al iniciar sesión")
                    resp_dialog.destroy()
                    dialog.destroy()
                else:
                    messagebox.showerror("Error", "Respuesta incorrecta")
            
            tk.Button(frame2, text="Verificar", command=validar_respuesta,
                     bg='#27ae60', fg='white', font=('Segoe UI', 11), padx=20, pady=8, cursor='hand2').pack()
            
            self.disconnect_database()
        
        tk.Button(frame, text="Continuar", command=verificar_pregunta,
                 bg='#3498db', fg='white', font=('Segoe UI', 11), padx=20, pady=8, cursor='hand2').pack()
    
    def generar_contrasena_temporal(self):
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(8))
    
    # ==================== CAMBIAR CONTRASEÑA ====================
    
    def cambiar_contrasena(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Cambiar Contraseña")
        dialog.geometry("450x500")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'450x500+{x}+{y}')
        
        tk.Label(dialog, text="Cambiar Contraseña", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        frame = tk.Frame(dialog, bg='white', padx=30, pady=30)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Contraseña Actual:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_actual = tk.Entry(frame, font=('Segoe UI', 11), relief='solid', bd=1, show="●")
        entry_actual.pack(fill='x', pady=(0, 15), ipady=5)
        
        tk.Label(frame, text="Nueva Contraseña:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_nueva = tk.Entry(frame, font=('Segoe UI', 11), relief='solid', bd=1, show="●")
        entry_nueva.pack(fill='x', pady=(0, 15), ipady=5)
        
        tk.Label(frame, text="Confirmar Nueva Contraseña:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_confirmar = tk.Entry(frame, font=('Segoe UI', 11), relief='solid', bd=1, show="●")
        entry_confirmar.pack(fill='x', pady=(0, 20), ipady=5)
        
        def guardar_cambio():
            actual = entry_actual.get()
            nueva = entry_nueva.get()
            confirmar = entry_confirmar.get()
            
            if not actual or not nueva or not confirmar:
                messagebox.showwarning("Error", "Complete todos los campos")
                return
            
            if nueva != confirmar:
                messagebox.showerror("Error", "Las nuevas contraseñas no coinciden")
                return
            
            if len(nueva) < 6:
                messagebox.showerror("Error", "La contraseña debe tener al menos 6 caracteres")
                return
            
            self.connect_database()
            
            hashed_actual = hashlib.sha256(actual.encode()).hexdigest()
            
            self.cursor.execute('''
                SELECT id FROM usuarios WHERE id = ? AND password = ?
            ''', (self.usuario_id, hashed_actual))
            
            if not self.cursor.fetchone():
                self.disconnect_database()
                messagebox.showerror("Error", "Contraseña actual incorrecta")
                return
            
            hashed_nueva = hashlib.sha256(nueva.encode()).hexdigest()
            
            self.cursor.execute('''
                UPDATE usuarios SET password = ?, ultimo_cambio = ? WHERE id = ?
            ''', (hashed_nueva, datetime.now().strftime("%Y-%m-%d"), self.usuario_id))
            self.conn.commit()
            
            self.registrar_mantenimiento("CAMBIO_CONTRASENA", f"Usuario {self.usuario_actual['username']} cambió su contraseña")
            
            self.disconnect_database()
            messagebox.showinfo("Éxito", "Contraseña cambiada correctamente")
            dialog.destroy()
        
        tk.Button(frame, text="Guardar Cambios", command=guardar_cambio,
                 bg='#27ae60', fg='white', font=('Segoe UI', 11), padx=20, pady=8, cursor='hand2').pack(fill='x')
        
        tk.Button(frame, text="Cancelar", command=dialog.destroy,
                 bg='#95a5a6', fg='white', font=('Segoe UI', 11), padx=20, pady=8, cursor='hand2').pack(fill='x', pady=(10, 0))
    
    def configurar_pregunta_seguridad(self):
        """Configurar pregunta de seguridad para el usuario actual"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Configurar Pregunta de Seguridad")
        dialog.geometry("450x400")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (450 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'450x400+{x}+{y}')
        
        tk.Label(dialog, text="Configurar Pregunta de Seguridad", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        frame = tk.Frame(dialog, bg='white', padx=30, pady=30)
        frame.pack(fill='both', expand=True)
        
        preguntas = [
            "¿Cuál es su color favorito?",
            "¿Nombre de su primera mascota?",
            "¿Ciudad donde nació?",
            "¿Nombre de su madre?",
            "¿Nombre de su padre?",
            "¿Mejor amigo de la infancia?",
            "¿Marca de su primer carro?",
            "¿Comida favorita?"
        ]
        
        tk.Label(frame, text="Seleccione una pregunta:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        combo_pregunta = ttk.Combobox(frame, values=preguntas, state='readonly', font=('Segoe UI', 11))
        combo_pregunta.pack(fill='x', pady=(0, 15), ipady=5)
        
        tk.Label(frame, text="Respuesta:", font=('Segoe UI', 11)).pack(anchor='w', pady=(0, 5))
        entry_respuesta = tk.Entry(frame, font=('Segoe UI', 11), relief='solid', bd=1, show="●")
        entry_respuesta.pack(fill='x', pady=(0, 20), ipady=5)
        
        def guardar():
            pregunta = combo_pregunta.get()
            respuesta = entry_respuesta.get().strip()
            
            if not pregunta or not respuesta:
                messagebox.showwarning("Error", "Complete todos los campos")
                return
            
            hashed_respuesta = hashlib.sha256(respuesta.encode()).hexdigest()
            
            self.connect_database()
            self.cursor.execute('''
                UPDATE usuarios SET pregunta_seguridad = ?, respuesta_seguridad = ?
                WHERE id = ?
            ''', (pregunta, hashed_respuesta, self.usuario_id))
            self.conn.commit()
            self.disconnect_database()
            
            messagebox.showinfo("Éxito", "Pregunta de seguridad configurada correctamente")
            dialog.destroy()
        
        tk.Button(frame, text="Guardar", command=guardar,
                 bg='#27ae60', fg='white', font=('Segoe UI', 11), padx=20, pady=8, cursor='hand2').pack()
    
    # ==================== MANTENIMIENTO DE BD (SOLO ADMIN) ====================
    
    def panel_mantenimiento(self):
        """Panel de mantenimiento de base de datos - Solo administrador"""
        if self.usuario_rol != 'ADMIN':
            messagebox.showerror("Acceso Denegado", "Solo el administrador puede acceder al mantenimiento")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Mantenimiento de Base de Datos")
        dialog.geometry("800x600")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f'800x600+{x}+{y}')
        
        tk.Label(dialog, text="Mantenimiento de Base de Datos", font=('Segoe UI', 18, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        # Frame principal con scroll
        canvas = tk.Canvas(dialog, bg='white')
        vsb = ttk.Scrollbar(dialog, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        main_frame = tk.Frame(canvas, bg='white')
        canvas.create_window((0, 0), window=main_frame, anchor='nw', width=780)
        
        # Sección Backup
        backup_frame = tk.LabelFrame(main_frame, text="📦 BACKUP", font=('Segoe UI', 12, 'bold'), padx=15, pady=15)
        backup_frame.pack(fill='x', padx=20, pady=10)
        
        btn_frame = tk.Frame(backup_frame, bg='white')
        btn_frame.pack()
        
        tk.Button(btn_frame, text="💾 Crear Backup", command=self.crear_backup,
                 bg='#27ae60', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame, text="🔄 Restaurar Backup", command=self.restaurar_backup,
                 bg='#f39c12', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame, text="📋 Ver Backups", command=self.ver_backups,
                 bg='#3498db', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        
        # Sección Optimización
        optimizar_frame = tk.LabelFrame(main_frame, text="🔧 OPTIMIZACIÓN", font=('Segoe UI', 12, 'bold'), padx=15, pady=15)
        optimizar_frame.pack(fill='x', padx=20, pady=10)
        
        btn_frame2 = tk.Frame(optimizar_frame, bg='white')
        btn_frame2.pack()
        
        tk.Button(btn_frame2, text="🗜️ Optimizar Base de Datos (VACUUM)", command=self.optimizar_bd,
                 bg='#3498db', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame2, text="✓ Verificar Integridad", command=self.verificar_integridad,
                 bg='#9b59b6', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame2, text="📊 Ver Tamaño de BD", command=self.ver_tamano_bd,
                 bg='#1abc9c', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        
        # Sección Limpieza
        limpieza_frame = tk.LabelFrame(main_frame, text="🗑️ LIMPIEZA", font=('Segoe UI', 12, 'bold'), padx=15, pady=15)
        limpieza_frame.pack(fill='x', padx=20, pady=10)
        
        btn_frame3 = tk.Frame(limpieza_frame, bg='white')
        btn_frame3.pack()
        
        tk.Button(btn_frame3, text="🧹 Limpiar Registros Antiguos", command=self.limpiar_registros_antiguos,
                 bg='#e67e22', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame3, text="📤 Exportar Estructura", command=self.exportar_estructura,
                 bg='#16a085', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame3, text="📋 Ver Log de Mantenimiento", command=self.ver_log_mantenimiento,
                 bg='#8e44ad', fg='white', font=('Segoe UI', 10), padx=20, pady=8, cursor='hand2').pack(side='left', padx=10)
        
        # Información de la BD
        info_frame = tk.LabelFrame(main_frame, text="ℹ️ INFORMACIÓN", font=('Segoe UI', 12, 'bold'), padx=15, pady=15)
        info_frame.pack(fill='x', padx=20, pady=10)
        
        self.info_text = tk.Text(info_frame, height=8, font=('Courier', 9), bg='#f8f9fa')
        self.info_text.pack(fill='x', padx=10, pady=10)
        
        def actualizar_info():
            self.info_text.delete(1.0, tk.END)
            self.connect_database()
            
            self.cursor.execute("SELECT COUNT(*) FROM usuarios")
            total_usuarios = self.cursor.fetchone()[0]
            
            self.cursor.execute("SELECT COUNT(*) FROM adultos_mayores")
            total_adultos = self.cursor.fetchone()[0]
            
            self.disconnect_database()
            
            tamano = self.ver_tamano_bd(return_only=True)
            
            info = f"""
📊 ESTADÍSTICAS DE LA BASE DE DATOS

• Total de usuarios: {total_usuarios}
• Total de adultos mayores: {total_adultos}
• Tamaño de la base de datos: {tamano}
• Ubicación: {self.data_path}
• Última optimización: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
            self.info_text.insert(1.0, info)
            self.info_text.config(state='disabled')
        
        actualizar_info()
        
        tk.Button(main_frame, text="Cerrar", command=dialog.destroy,
                 bg='#95a5a6', fg='white', font=('Segoe UI', 11), padx=30, pady=10, cursor='hand2').pack(pady=20)
        
        main_frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    
    def crear_backup(self):
        """Crear backup de la base de datos"""
        try:
            self.connect_database()
            
            fecha = datetime.now().strftime("%Y%m%d_%H%M%S")
            nombre_backup = f"backup_{fecha}.db"
            ruta_backup = os.path.join(self.backup_path, nombre_backup)
            
            # Crear backup
            shutil.copy2(self.db_path, ruta_backup)
            
            # Registrar en log
            self.cursor.execute('''
                INSERT INTO backup_log (fecha, tipo, descripcion, usuario)
                VALUES (?, ?, ?, ?)
            ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "BACKUP", 
                  f"Backup creado: {nombre_backup}", self.usuario_actual['username']))
            self.conn.commit()
            
            self.registrar_mantenimiento("BACKUP", f"Backup creado: {nombre_backup}")
            
            self.disconnect_database()
            messagebox.showinfo("Éxito", f"Backup creado correctamente\n\n{ruta_backup}")
            
        except Exception as e:
            self.disconnect_database()
            messagebox.showerror("Error", f"Error al crear backup: {str(e)}")
    
    def restaurar_backup(self):
        """Restaurar backup seleccionado"""
        backups = [f for f in os.listdir(self.backup_path) if f.startswith("backup_") and f.endswith(".db")]
        
        if not backups:
            messagebox.showwarning("Sin backups", "No hay backups disponibles")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Restaurar Backup")
        dialog.geometry("500x400")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'500x400+{x}+{y}')
        
        tk.Label(dialog, text="Seleccionar Backup", font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        frame.pack(fill='both', expand=True)
        
        tk.Label(frame, text="Backups disponibles:", font=('Segoe UI', 11)).pack(anchor='w')
        
        listbox = tk.Listbox(frame, height=10, font=('Segoe UI', 10))
        listbox.pack(fill='both', expand=True, pady=10)
        
        for b in sorted(backups, reverse=True):
            info = os.path.getsize(os.path.join(self.backup_path, b))
            info_mb = info / (1024 * 1024)
            listbox.insert(tk.END, f"{b} ({info_mb:.2f} MB)")
        
        def restaurar():
            selection = listbox.curselection()
            if not selection:
                messagebox.showwarning("Selección", "Seleccione un backup")
                return
            
            if not messagebox.askyesno("Confirmar", "¿Restaurar backup? Se perderán los cambios actuales"):
                return
            
            selected = listbox.get(selection[0])
            nombre_backup = selected.split(" ")[0]
            ruta_backup = os.path.join(self.backup_path, nombre_backup)
            
            try:
                self.disconnect_database()
                
                # Eliminar BD actual si existe
                if os.path.exists(self.db_enc_path):
                    os.remove(self.db_enc_path)
                
                # Copiar backup y encriptar
                shutil.copy2(ruta_backup, self.db_path)
                self.db_encryptor.encrypt_database()
                
                self.connect_database()
                self.cursor.execute('''
                    INSERT INTO backup_log (fecha, tipo, descripcion, usuario)
                    VALUES (?, ?, ?, ?)
                ''', (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "RESTAURACION", 
                      f"Restaurado desde: {nombre_backup}", self.usuario_actual['username']))
                self.conn.commit()
                
                self.registrar_mantenimiento("RESTAURACION", f"Restaurado desde: {nombre_backup}")
                
                self.disconnect_database()
                messagebox.showinfo("Éxito", "Backup restaurado correctamente")
                dialog.destroy()
                
                messagebox.showinfo("Reinicio", "El sistema se reiniciará para aplicar los cambios")
                self.root.quit()
                
            except Exception as e:
                messagebox.showerror("Error", f"Error al restaurar: {str(e)}")
        
        tk.Button(frame, text="Restaurar", command=restaurar,
                 bg='#f39c12', fg='white', padx=20, pady=8, cursor='hand2').pack()
    
    def ver_backups(self):
        """Ver lista de backups"""
        backups = [f for f in os.listdir(self.backup_path) if f.startswith("backup_") and f.endswith(".db")]
        
        if not backups:
            messagebox.showinfo("Backups", "No hay backups disponibles")
            return
        
        texto = "📋 BACKUPS DISPONIBLES\n\n"
        for b in sorted(backups, reverse=True):
            info = os.path.getsize(os.path.join(self.backup_path, b))
            info_mb = info / (1024 * 1024)
            fecha = b.replace("backup_", "").replace(".db", "")
            texto += f"📁 {b}\n   Fecha: {fecha[:8]} {fecha[9:15]}\n   Tamaño: {info_mb:.2f} MB\n\n"
        
        messagebox.showinfo("Backups", texto)
    
    def optimizar_bd(self):
        """Optimizar base de datos (VACUUM)"""
        if messagebox.askyesno("Confirmar", "¿Optimizar base de datos? Esto puede tardar unos segundos"):
            try:
                self.connect_database()
                self.cursor.execute("VACUUM")
                self.conn.commit()
                
                self.registrar_mantenimiento("OPTIMIZACION", "Base de datos optimizada con VACUUM")
                
                self.disconnect_database()
                messagebox.showinfo("Éxito", "Base de datos optimizada correctamente")
            except Exception as e:
                self.disconnect_database()
                messagebox.showerror("Error", f"Error al optimizar: {str(e)}")
    
    def verificar_integridad(self):
        """Verificar integridad de la base de datos"""
        try:
            self.connect_database()
            self.cursor.execute("PRAGMA integrity_check")
            result = self.cursor.fetchone()
            
            self.registrar_mantenimiento("VERIFICACION", "Verificación de integridad realizada")
            
            self.disconnect_database()
            
            if result and result[0] == "ok":
                messagebox.showinfo("Integridad", "✅ La base de datos está íntegra y sin errores")
            else:
                messagebox.showwarning("Integridad", f"⚠️ Se encontraron problemas:\n{result[0] if result else 'Error'}")
        except Exception as e:
            self.disconnect_database()
            messagebox.showerror("Error", f"Error al verificar: {str(e)}")
    
    def ver_tamano_bd(self, return_only=False):
        """Ver tamaño de la base de datos"""
        try:
            if os.path.exists(self.db_enc_path):
                tamaño = os.path.getsize(self.db_enc_path)
                tamaño_mb = tamaño / (1024 * 1024)
                resultado = f"{tamaño_mb:.2f} MB"
                
                if not return_only:
                    self.connect_database()
                    self.cursor.execute("SELECT COUNT(*) FROM adultos_mayores")
                    total = self.cursor.fetchone()[0]
                    self.disconnect_database()
                    
                    messagebox.showinfo("Tamaño de BD", f"📊 Base de datos encriptada\n\n• Tamaño: {tamaño_mb:.2f} MB\n• Registros: {total}\n• Ubicación: {self.data_path}")
                
                return resultado
            else:
                return "0 MB"
        except:
            return "Error"
    
    def limpiar_registros_antiguos(self):
        """Limpiar registros antiguos (más de 5 años sin visitas)"""
        if not messagebox.askyesno("Confirmar", "¿Eliminar adultos mayores sin visitas en los últimos 5 años?"):
            return
        
        try:
            self.connect_database()
            fecha_limite = (datetime.now() - timedelta(days=5*365)).strftime("%Y-%m-%d")
            
            self.cursor.execute('''
                SELECT COUNT(*) FROM adultos_mayores 
                WHERE ultima_visita IS NULL OR ultima_visita < ?
            ''', (fecha_limite,))
            a_eliminar = self.cursor.fetchone()[0]
            
            if a_eliminar == 0:
                self.disconnect_database()
                messagebox.showinfo("Limpieza", "No hay registros antiguos para eliminar")
                return
            
            if messagebox.askyesno("Confirmar", f"Se eliminarán {a_eliminar} registros. ¿Continuar?"):
                self.cursor.execute('''
                    DELETE FROM adultos_mayores 
                    WHERE ultima_visita IS NULL OR ultima_visita < ?
                ''', (fecha_limite,))
                self.conn.commit()
                
                self.registrar_mantenimiento("LIMPIEZA", f"Eliminados {a_eliminar} registros antiguos")
                
                self.disconnect_database()
                messagebox.showinfo("Éxito", f"Se eliminaron {a_eliminar} registros antiguos")
                self.cargar_lista()
                self.cargar_estadisticas()
        except Exception as e:
            self.disconnect_database()
            messagebox.showerror("Error", f"Error al limpiar: {str(e)}")
    
    def exportar_estructura(self):
        """Exportar estructura de la base de datos a SQL"""
        filename = filedialog.asksaveasfilename(defaultextension=".sql", filetypes=[("SQL files", "*.sql")])
        if not filename:
            return
        
        try:
            self.connect_database()
            
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("-- Estructura de Base de Datos - Sistema Adulto Mayor\n")
                f.write(f"-- Exportado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # Exportar estructura de tablas
                self.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                for row in self.cursor.fetchall():
                    if row[0]:
                        f.write(row[0] + ";\n\n")
            
            self.registrar_mantenimiento("EXPORTAR_ESTRUCTURA", f"Estructura exportada a {filename}")
            
            self.disconnect_database()
            messagebox.showinfo("Éxito", f"Estructura exportada a {filename}")
        except Exception as e:
            self.disconnect_database()
            messagebox.showerror("Error", str(e))
    
    def ver_log_mantenimiento(self):
        """Ver log de mantenimiento"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Log de Mantenimiento")
        dialog.geometry("800x500")
        dialog.configure(bg='white')
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (800 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'800x500+{x}+{y}')
        
        tk.Label(dialog, text="Registro de Mantenimiento", font=('Segoe UI', 14, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        text_area = tk.Text(dialog, font=('Courier', 10), wrap='word', padx=20, pady=20)
        text_area.pack(fill='both', expand=True)
        
        self.connect_database()
        self.cursor.execute('''
            SELECT fecha, operacion, detalles, usuario FROM mantenimiento_log 
            ORDER BY id DESC LIMIT 100
        ''')
        
        texto = "📋 REGISTRO DE MANTENIMIENTO\n\n"
        for row in self.cursor.fetchall():
            texto += f"[{row[0]}] {row[1]}\n   Usuario: {row[3]}\n   Detalles: {row[2]}\n\n"
        
        self.disconnect_database()
        
        text_area.insert(1.0, texto)
        text_area.config(state='disabled')
    
    # ==================== INTERFAZ PRINCIPAL ====================
    
    def mostrar_principal(self):
        self.limpiar_ventana()
        self.connect_database()
        
        # Header
        header_frame = tk.Frame(self.root, bg='#2c3e50', height=70)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="👴 Sistema de Control del Adulto Mayor V1.0", 
                font=('Segoe UI', 16, 'bold'), bg='#2c3e50', fg='white').pack(side='left', padx=20, pady=15)
        
        user_frame = tk.Frame(header_frame, bg='#2c3e50')
        user_frame.pack(side='right', padx=20)
        
        tk.Label(user_frame, text=f"👤 {self.usuario_actual['nombre']} ({self.usuario_rol})", 
                font=('Segoe UI', 10), bg='#2c3e50', fg='white').pack(side='left', padx=10)
        tk.Label(user_frame, text=f"📅 {datetime.now().strftime('%d/%m/%Y')}", 
                font=('Segoe UI', 10), bg='#2c3e50', fg='white').pack(side='left', padx=10)
        
        # Menú de usuario
        btn_menu = tk.Menubutton(user_frame, text="⚙️ Menú", font=('Segoe UI', 9),
                                 bg='#34495e', fg='white', relief='flat', padx=15, pady=3, cursor='hand2')
        btn_menu.pack(side='left', padx=10)
        
        menu = tk.Menu(btn_menu, tearoff=0)
        btn_menu.config(menu=menu)
        menu.add_command(label="🔐 Cambiar Contraseña", command=self.cambiar_contrasena)
        menu.add_command(label="❓ Configurar Pregunta de Seguridad", command=self.configurar_pregunta_seguridad)
        menu.add_separator()
        
        if self.usuario_rol == 'ADMIN':
            menu.add_command(label="👥 Gestionar Usuarios", command=self.gestionar_usuarios)
            menu.add_command(label="🔧 Mantenimiento de BD", command=self.panel_mantenimiento)
            menu.add_separator()
        
        menu.add_command(label="🚪 Cerrar Sesión", command=self.salir_sistema)
        
        # Tarjetas de estadísticas
        stats_frame = tk.Frame(self.root, bg='#ecf0f1', height=100)
        stats_frame.pack(fill='x', padx=10, pady=5)
        stats_frame.pack_propagate(False)
        
        categorias = [
            ('Total Adultos', '#3498db'),
            ('Ancianos Solos', '#e74c3c'),
            ('Postrados', '#f39c12'),
            ('Combatientes', '#27ae60'),
            ('Centenarios', '#9b59b6'),
            ('Alertas Activas', '#e67e22')
        ]
        
        self.stats_labels = {}
        for i, (cat, color) in enumerate(categorias):
            card = tk.Frame(stats_frame, bg='white', relief='raised', bd=1)
            card.pack(side='left', expand=True, fill='both', padx=3, pady=5)
            
            tk.Label(card, text=cat, font=('Segoe UI', 9), bg='white', fg='#7f8c8d').pack(pady=(5, 0))
            label_valor = tk.Label(card, text="0", font=('Segoe UI', 20, 'bold'), bg='white', fg=color)
            label_valor.pack(pady=2)
            self.stats_labels[cat] = label_valor
        
        # Filtros y tabla
        main_frame = tk.Frame(self.root, bg='#f0f0f0')
        main_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Panel filtros
        filter_frame = tk.LabelFrame(main_frame, text="Filtros", font=('Segoe UI', 10, 'bold'))
        filter_frame.pack(side='left', fill='y', padx=(0, 10))
        
        filter_inner = tk.Frame(filter_frame, bg='#f0f0f0', padx=15, pady=15)
        filter_inner.pack(fill='both', expand=True)
        
        tk.Label(filter_inner, text="Tipo:").pack(anchor='w', pady=(0, 5))
        self.filtro_tipo = ttk.Combobox(filter_inner, values=['Todos', 'ANCIANO_SOLO', 'POSTRADO', 'COMBATIENTE', 'CENTENARIO'], 
                                        state='readonly', width=20)
        self.filtro_tipo.set('Todos')
        self.filtro_tipo.pack(fill='x', pady=(0, 15))
        self.filtro_tipo.bind('<<ComboboxSelected>>', lambda e: self.cargar_lista())
        
        tk.Label(filter_inner, text="CMF:").pack(anchor='w', pady=(0, 5))
        self.filtro_cmf = ttk.Combobox(filter_inner, values=['Todos'] + list(range(1, 25)), state='readonly', width=20)
        self.filtro_cmf.set('Todos')
        self.filtro_cmf.pack(fill='x', pady=(0, 15))
        self.filtro_cmf.bind('<<ComboboxSelected>>', lambda e: self.cargar_lista())
        
        tk.Label(filter_inner, text="Buscar:").pack(anchor='w', pady=(0, 5))
        self.search_var = tk.StringVar()
        self.search_var.trace('w', lambda *args: self.cargar_lista())
        tk.Entry(filter_inner, textvariable=self.search_var, width=20).pack(fill='x')
        
        tk.Button(filter_inner, text="🔍 Buscar", command=self.cargar_lista,
                 bg='#3498db', fg='white', pady=5, cursor='hand2').pack(fill='x', pady=15)
        tk.Button(filter_inner, text="🔄 Limpiar", command=self.limpiar_filtros,
                 bg='#95a5a6', fg='white', pady=5, cursor='hand2').pack(fill='x')
        
        # Tabla
        right_frame = tk.Frame(main_frame, bg='#f0f0f0')
        right_frame.pack(side='left', fill='both', expand=True)
        
        toolbar = tk.Frame(right_frame, bg='#f0f0f0', height=40)
        toolbar.pack(fill='x', pady=(0, 10))
        toolbar.pack_propagate(False)
        
        botones = [
            ("➕ Nuevo", self.nuevo_adulto, '#27ae60'),
            ("📥 Importar", self.importar_excel, '#3498db'),
            ("📤 Exportar", self.exportar_excel, '#9b59b6'),
            ("✏️ Editar", self.editar_adulto, '#f39c12'),
            ("🗑️ Eliminar", self.eliminar_adulto, '#e74c3c')
        ]
        
        for texto, comando, color in botones:
            tk.Button(toolbar, text=texto, command=comando,
                     bg=color, fg='white', font=('Segoe UI', 9), padx=15, cursor='hand2').pack(side='left', padx=2)
        
        columns = ('ID', 'Tipo', 'Nombre', 'Edad', 'Dirección', 'CMF', 'APP', 'Situación', 'Última Visita')
        self.tree = ttk.Treeview(right_frame, columns=columns, show='headings', height=22)
        
        for col in columns:
            self.tree.heading(col, text=col)
            widths = {'ID': 50, 'Tipo': 100, 'Nombre': 200, 'Edad': 50, 'Dirección': 180, 
                     'CMF': 50, 'APP': 150, 'Situación': 120, 'Última Visita': 100}
            self.tree.column(col, width=widths.get(col, 100))
        
        vsb = ttk.Scrollbar(right_frame, orient='vertical', command=self.tree.yview)
        hsb = ttk.Scrollbar(right_frame, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        hsb.pack(side='bottom', fill='x')
        
        self.tree.bind('<Double-1>', self.on_double_click)
        
        # Barra de estado
        status_frame = tk.Frame(self.root, bg='#2c3e50', height=30)
        status_frame.pack(side='bottom', fill='x')
        status_frame.pack_propagate(False)
        
        tk.Label(status_frame, text="✅ Sistema listo | 🔒 Datos encriptados", 
                font=('Segoe UI', 9), bg='#2c3e50', fg='white').pack(side='left', padx=10, pady=5)
        
        self.count_label = tk.Label(status_frame, text="", font=('Segoe UI', 9), bg='#2c3e50', fg='white')
        self.count_label.pack(side='right', padx=10, pady=5)
        
        self.cargar_estadisticas()
        self.cargar_lista()
    
    def salir_sistema(self):
        if messagebox.askyesno("Salir", "¿Está seguro?"):
            self.disconnect_database()
            self.mostrar_login()
    
    def limpiar_filtros(self):
        self.filtro_tipo.set('Todos')
        self.filtro_cmf.set('Todos')
        self.search_var.set('')
        self.cargar_lista()
    
    def cargar_estadisticas(self):
        self.cursor.execute("SELECT COUNT(*) FROM adultos_mayores")
        self.stats_labels['Total Adultos'].config(text=str(self.cursor.fetchone()[0]))
        
        for tipo in ['ANCIANO_SOLO', 'POSTRADO', 'COMBATIENTE', 'CENTENARIO']:
            self.cursor.execute("SELECT COUNT(*) FROM adultos_mayores WHERE tipo_registro = ?", (tipo,))
            nombre = {'ANCIANO_SOLO': 'Ancianos Solos', 'POSTRADO': 'Postrados', 
                     'COMBATIENTE': 'Combatientes', 'CENTENARIO': 'Centenarios'}[tipo]
            self.stats_labels[nombre].config(text=str(self.cursor.fetchone()[0]))
        
        fecha_limite = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        self.cursor.execute("SELECT COUNT(*) FROM adultos_mayores WHERE ultima_visita IS NULL OR ultima_visita < ?", (fecha_limite,))
        self.stats_labels['Alertas Activas'].config(text=str(self.cursor.fetchone()[0]))
    
    def cargar_lista(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        query = """SELECT id, tipo_registro, nombre, apellidos, fecha_nacimiento, direccion, cmf, app, situacion_social, ultima_visita 
                   FROM adultos_mayores WHERE 1=1"""
        params = []
        
        if self.filtro_tipo.get() != 'Todos':
            query += " AND tipo_registro = ?"
            params.append(self.filtro_tipo.get())
        
        if self.filtro_cmf.get() != 'Todos':
            query += " AND cmf = ?"
            params.append(int(self.filtro_cmf.get()))
        
        search = self.search_var.get().strip()
        if search:
            query += " AND (nombre LIKE ? OR apellidos LIKE ? OR direccion LIKE ?)"
            params.extend([f'%{search}%', f'%{search}%', f'%{search}%'])
        
        query += " ORDER BY id"
        
        self.cursor.execute(query, params)
        
        for row in self.cursor.fetchall():
            edad = ""
            if row[4]:
                try:
                    if '/' in str(row[4]):
                        fecha = datetime.strptime(str(row[4]), "%d/%m/%y")
                    else:
                        fecha = datetime.strptime(str(row[4]), "%y%m%d")
                    edad = datetime.now().year - fecha.year
                except:
                    edad = "?"
            
            tipo_nombre = {'ANCIANO_SOLO': 'Anciano Solo', 'POSTRADO': 'Postrado', 
                          'COMBATIENTE': 'Combatiente', 'CENTENARIO': 'Centenario'}.get(row[1], row[1])
            
            self.tree.insert('', 'end', values=(
                row[0], tipo_nombre, f"{row[2]} {row[3]}", edad, (row[5] or '-')[:30], 
                row[6] or '-', (row[7] or '-')[:20], (row[8] or '-')[:15], row[9] or 'Sin visitas'
            ))
        
        self.count_label.config(text=f"📊 Total: {len(self.tree.get_children())} registros")
    
    def on_double_click(self, event):
        selection = self.tree.selection()
        if selection:
            adulto_id = self.tree.item(selection[0])['values'][0]
            self.ver_detalle(adulto_id)
    
    def ver_detalle(self, adulto_id):
        self.cursor.execute('''
            SELECT tipo_registro, numero, nombre, apellidos, fecha_nacimiento, direccion, 
                   app, situacion_social, grupo_dispensarial, cmf, telefono, contacto_emergencia,
                   tiene_cuidador, nombre_cuidador, telefono_cuidador, fecha_registro,
                   ultima_visita, observaciones
            FROM adultos_mayores WHERE id = ?
        ''', (adulto_id,))
        
        adulto = self.cursor.fetchone()
        if not adulto:
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title(f"Detalle - {adulto[2]} {adulto[3]}")
        dialog.geometry("550x600")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (600 // 2)
        dialog.geometry(f'550x600+{x}+{y}')
        
        tk.Label(dialog, text="Detalle del Adulto Mayor", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        text_area = tk.Text(dialog, font=('Courier', 10), wrap='word', padx=20, pady=20)
        text_area.pack(fill='both', expand=True)
        
        tipo_nombre = {'ANCIANO_SOLO': 'Anciano Solo', 'POSTRADO': 'Postrado', 
                      'COMBATIENTE': 'Combatiente', 'CENTENARIO': 'Centenario'}.get(adulto[0], adulto[0])
        
        detalle = f"""
╔══════════════════════════════════════════════════════════════╗
║                 DATOS DEL ADULTO MAYOR                        ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  ID: {adulto_id}
║  Tipo: {tipo_nombre}
║  Número: {adulto[1] or 'N/A'}
║                                                              ║
║  👤 DATOS PERSONALES                                         ║
║  Nombre: {adulto[2]} {adulto[3]}
║  Fecha Nac.: {adulto[4] or 'No registrada'}
║                                                              ║
║  🏠 DOMICILIO                                                ║
║  Dirección: {adulto[5] or 'No registrada'}
║  CMF: {adulto[9] or 'No registrado'}
║                                                              ║
║  🏥 SALUD                                                    ║
║  APP: {adulto[6] or 'Ninguna'}
║  Grupo Disp.: {adulto[8] or 'No registrado'}
║  Situación: {adulto[7] or 'No registrada'}
║                                                              ║
║  📞 CONTACTOS                                                ║
║  Teléfono: {adulto[10] or 'No registrado'}
║  Contacto Emergencia: {adulto[11] or 'No registrado'}
║                                                              ║
║  👨‍👩‍👦 CUIDADOR                                               ║
║  Tiene Cuidador: {'✓ Sí' if adulto[12] else '✗ No'}
║  Nombre: {adulto[13] or '-'}
║  Teléfono: {adulto[14] or '-'}
║                                                              ║
║  📅 SEGUIMIENTO                                              ║
║  Última Visita: {adulto[16] or 'Sin visitas'}
║  Fecha Registro: {adulto[15] or 'No registrada'}
║                                                              ║
║  📝 OBSERVACIONES                                            ║
║  {adulto[17] or 'Sin observaciones'}
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        text_area.insert(1.0, detalle)
        text_area.config(state='disabled')
        
        btn_frame = tk.Frame(dialog, bg='white')
        btn_frame.pack(fill='x', pady=10)
        
        tk.Button(btn_frame, text="Registrar Visita", command=lambda: [dialog.destroy(), self.registrar_visita(adulto_id)],
                 bg='#27ae60', fg='white', padx=20, cursor='hand2').pack(side='left', padx=10)
        tk.Button(btn_frame, text="Cerrar", command=dialog.destroy,
                 bg='#95a5a6', fg='white', padx=20, cursor='hand2').pack(side='right', padx=10)
    
    def registrar_visita(self, adulto_id):
        fecha = simpledialog.askstring("Visita", "Fecha (YYYY-MM-DD):", 
                                        initialvalue=datetime.now().strftime("%Y-%m-%d"))
        if fecha:
            self.cursor.execute("UPDATE adultos_mayores SET ultima_visita = ? WHERE id = ?", (fecha, adulto_id))
            self.conn.commit()
            messagebox.showinfo("Éxito", "Visita registrada")
            self.cargar_lista()
            self.cargar_estadisticas()
    
    # ==================== CRUD ====================
    
    def nuevo_adulto(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Nuevo Adulto Mayor")
        dialog.geometry("550x650")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (550 // 2)
        y = (dialog.winfo_screenheight() // 2) - (650 // 2)
        dialog.geometry(f'550x650+{x}+{y}')
        
        canvas = tk.Canvas(dialog, bg='white')
        vsb = ttk.Scrollbar(dialog, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        canvas.pack(side='left', fill='both', expand=True)
        vsb.pack(side='right', fill='y')
        
        frame = tk.Frame(canvas, bg='white')
        canvas.create_window((0, 0), window=frame, anchor='nw')
        
        tk.Label(frame, text="Registro de Adulto Mayor", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        main_frame = tk.Frame(frame, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        campos = [
            ("Tipo *", "tipo", ['ANCIANO_SOLO', 'POSTRADO', 'COMBATIENTE', 'CENTENARIO']),
            ("Nombres *", "nombre", None),
            ("Apellidos *", "apellidos", None),
            ("Fecha Nac. (DD/MM/AA)", "fecha_nac", None),
            ("Dirección", "direccion", None),
            ("APP", "app", None),
            ("Situación Social", "situacion", None),
            ("Grupo Dispensarial", "grupo", None),
            ("CMF", "cmf", None),
            ("Teléfono", "telefono", None),
            ("Contacto Emergencia", "contacto", None),
            ("¿Tiene Cuidador?", "cuidador_check", None),
            ("Nombre Cuidador", "nombre_cuidador", None),
            ("Teléfono Cuidador", "telefono_cuidador", None),
            ("Observaciones", "obs", None)
        ]
        
        entries = {}
        
        for label, key, options in campos:
            tk.Label(main_frame, text=label, font=('Segoe UI', 10, 'bold'), 
                    bg='white', anchor='w').pack(fill='x', pady=(10, 0))
            
            if options:
                entry = ttk.Combobox(main_frame, values=options, state='readonly')
                entry.set(options[0])
                entry.pack(fill='x', pady=(5, 0))
            elif key == "cuidador_check":
                entry = tk.BooleanVar()
                tk.Checkbutton(main_frame, variable=entry, bg='white').pack(anchor='w', pady=(5, 0))
            elif key == "obs":
                entry = tk.Text(main_frame, height=4, relief='solid', bd=1)
                entry.pack(fill='x', pady=(5, 0))
            else:
                entry = tk.Entry(main_frame, relief='solid', bd=1)
                entry.pack(fill='x', pady=(5, 0))
            
            entries[key] = entry
        
        def guardar():
            if not entries['nombre'].get().strip() or not entries['apellidos'].get().strip():
                messagebox.showwarning("Error", "Nombre y Apellidos son obligatorios")
                return
            
            tipo = entries['tipo'].get()
            self.cursor.execute("SELECT COALESCE(MAX(numero), 0) + 1 FROM adultos_mayores WHERE tipo_registro = ?", (tipo,))
            numero = self.cursor.fetchone()[0]
            
            self.cursor.execute('''
                INSERT INTO adultos_mayores 
                (tipo_registro, numero, nombre, apellidos, fecha_nacimiento, direccion, app,
                 situacion_social, grupo_dispensarial, cmf, telefono, contacto_emergencia,
                 tiene_cuidador, nombre_cuidador, telefono_cuidador, observaciones, fecha_registro)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                tipo, numero, entries['nombre'].get().strip(), entries['apellidos'].get().strip(),
                entries['fecha_nac'].get() or None, entries['direccion'].get() or None,
                entries['app'].get() or None, entries['situacion'].get() or None,
                entries['grupo'].get() or None, int(entries['cmf'].get()) if entries['cmf'].get() else None,
                entries['telefono'].get() or None, entries['contacto'].get() or None,
                1 if entries['cuidador_check'].get() else 0,
                entries['nombre_cuidador'].get() or None, entries['telefono_cuidador'].get() or None,
                entries['obs'].get(1.0, 'end').strip() or None, datetime.now().strftime("%Y-%m-%d")
            ))
            
            self.conn.commit()
            messagebox.showinfo("Éxito", "Registrado correctamente")
            dialog.destroy()
            self.cargar_lista()
            self.cargar_estadisticas()
        
        btn_frame = tk.Frame(main_frame, bg='white')
        btn_frame.pack(fill='x', pady=20)
        
        tk.Button(btn_frame, text="Guardar", command=guardar,
                 bg='#27ae60', fg='white', padx=30, pady=8, cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Cancelar", command=dialog.destroy,
                 bg='#e74c3c', fg='white', padx=30, pady=8, cursor='hand2').pack(side='left', padx=5)
        
        frame.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))
    
    def editar_adulto(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Seleccione un adulto")
            return
        messagebox.showinfo("Info", "Para editar, haga doble clic en el registro y luego use 'Registrar Visita'")
    
    def eliminar_adulto(self):
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("Selección", "Seleccione un adulto")
            return
        
        adulto_id = self.tree.item(selection[0])['values'][0]
        nombre = self.tree.item(selection[0])['values'][2]
        
        if messagebox.askyesno("Confirmar", f"¿Eliminar a {nombre}?"):
            self.cursor.execute("DELETE FROM adultos_mayores WHERE id = ?", (adulto_id,))
            self.conn.commit()
            self.cargar_lista()
            self.cargar_estadisticas()
            messagebox.showinfo("Éxito", "Eliminado")
    
    # ==================== GESTIÓN USUARIOS ====================
    
    def gestionar_usuarios(self):
        if self.usuario_rol != 'ADMIN':
            messagebox.showerror("Acceso", "Solo administrador")
            return
        
        dialog = tk.Toplevel(self.root)
        dialog.title("Gestión de Usuarios")
        dialog.geometry("700x500")
        dialog.configure(bg='white')
        dialog.transient(self.root)
        dialog.grab_set()
        
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (700 // 2)
        y = (dialog.winfo_screenheight() // 2) - (500 // 2)
        dialog.geometry(f'700x500+{x}+{y}')
        
        tk.Label(dialog, text="Gestión de Usuarios", font=('Segoe UI', 16, 'bold'),
                bg='#2c3e50', fg='white', pady=15).pack(fill='x')
        
        main_frame = tk.Frame(dialog, bg='white', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # Formulario nuevo usuario
        form_frame = tk.LabelFrame(main_frame, text="Nuevo Usuario")
        form_frame.pack(fill='x', pady=10)
        
        form_inner = tk.Frame(form_frame, padx=15, pady=15)
        form_inner.pack(fill='x')
        
        tk.Label(form_inner, text="Usuario:").grid(row=0, column=0, padx=5, pady=5)
        entry_user = tk.Entry(form_inner)
        entry_user.grid(row=0, column=1, padx=5, pady=5)
        
        tk.Label(form_inner, text="Contraseña:").grid(row=0, column=2, padx=5, pady=5)
        entry_pass = tk.Entry(form_inner, show="●")
        entry_pass.grid(row=0, column=3, padx=5, pady=5)
        
        tk.Label(form_inner, text="Nombre:").grid(row=1, column=0, padx=5, pady=5)
        entry_nombre = tk.Entry(form_inner, width=40)
        entry_nombre.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky='ew')
        
        tk.Label(form_inner, text="Rol:").grid(row=2, column=0, padx=5, pady=5)
        rol_combo = ttk.Combobox(form_inner, values=['ADMIN', 'MEDICO', 'ENFERMERA', 'AUXILIAR'], state='readonly', width=17)
        rol_combo.set('AUXILIAR')
        rol_combo.grid(row=2, column=1, padx=5, pady=5)
        
        preguntas = ["¿Cuál es su color favorito?", "¿Nombre de su primera mascota?", "¿Ciudad donde nació?", "¿Nombre de su madre?"]
        
        tk.Label(form_inner, text="Pregunta Seguridad:").grid(row=3, column=0, padx=5, pady=5)
        pregunta_combo = ttk.Combobox(form_inner, values=preguntas, state='readonly', width=30)
        pregunta_combo.set(preguntas[0])
        pregunta_combo.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        
        tk.Label(form_inner, text="Respuesta:").grid(row=4, column=0, padx=5, pady=5)
        entry_respuesta = tk.Entry(form_inner, width=30, show="●")
        entry_respuesta.grid(row=4, column=1, columnspan=2, padx=5, pady=5, sticky='ew')
        
        def crear_usuario():
            username = entry_user.get().strip()
            password = entry_pass.get()
            nombre = entry_nombre.get().strip()
            rol = rol_combo.get()
            pregunta = pregunta_combo.get()
            respuesta = entry_respuesta.get().strip()
            
            if not username or not password or not nombre or not respuesta:
                messagebox.showwarning("Error", "Complete todos los campos")
                return
            
            hashed_pass = hashlib.sha256(password.encode()).hexdigest()
            hashed_resp = hashlib.sha256(respuesta.encode()).hexdigest()
            
            try:
                self.cursor.execute('''
                    INSERT INTO usuarios (username, password, nombre_completo, rol, fecha_creacion, 
                                         ultimo_cambio, pregunta_seguridad, respuesta_seguridad)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (username, hashed_pass, nombre, rol, datetime.now().strftime("%Y-%m-%d"),
                      datetime.now().strftime("%Y-%m-%d"), pregunta, hashed_resp))
                self.conn.commit()
                messagebox.showinfo("Éxito", "Usuario creado")
                entry_user.delete(0, 'end')
                entry_pass.delete(0, 'end')
                entry_nombre.delete(0, 'end')
                entry_respuesta.delete(0, 'end')
                cargar_usuarios()
            except:
                messagebox.showerror("Error", "Usuario ya existe")
        
        tk.Button(form_inner, text="Crear Usuario", command=crear_usuario,
                 bg='#27ae60', fg='white', padx=15, cursor='hand2').grid(row=4, column=3, padx=5, pady=5)
        
        # Lista de usuarios
        list_frame = tk.LabelFrame(main_frame, text="Usuarios")
        list_frame.pack(fill='both', expand=True, pady=10)
        
        columns = ('ID', 'Usuario', 'Nombre', 'Rol', 'Fecha', 'Estado')
        tree_usuarios = ttk.Treeview(list_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree_usuarios.heading(col, text=col)
            tree_usuarios.column(col, width=100)
        
        tree_usuarios.pack(fill='both', expand=True, padx=5, pady=5)
        
        def cargar_usuarios():
            for item in tree_usuarios.get_children():
                tree_usuarios.delete(item)
            
            self.cursor.execute("SELECT id, username, nombre_completo, rol, fecha_creacion, activo FROM usuarios WHERE id != 1")
            for row in self.cursor.fetchall():
                estado = "Activo" if row[5] else "Inactivo"
                tree_usuarios.insert('', 'end', values=(row[0], row[1], row[2], row[3], row[4], estado))
        
        def desactivar():
            sel = tree_usuarios.selection()
            if not sel:
                return
            uid = tree_usuarios.item(sel[0])['values'][0]
            if messagebox.askyesno("Confirmar", "¿Desactivar usuario?"):
                self.cursor.execute("UPDATE usuarios SET activo = 0 WHERE id = ?", (uid,))
                self.conn.commit()
                cargar_usuarios()
        
        btn_frame = tk.Frame(main_frame)
        btn_frame.pack(fill='x')
        
        tk.Button(btn_frame, text="Actualizar", command=cargar_usuarios,
                 bg='#3498db', fg='white', padx=15, cursor='hand2').pack(side='left', padx=5)
        tk.Button(btn_frame, text="Desactivar", command=desactivar,
                 bg='#e74c3c', fg='white', padx=15, cursor='hand2').pack(side='left', padx=5)
        
        cargar_usuarios()
    
    # ==================== IMPORTAR/EXPORTAR ====================
    
    def importar_excel(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel", "*.xlsx *.xls")])
        if not filename:
            return
        
        try:
            excel_file = pd.ExcelFile(filename)
            tipos = {
                'BASE DE DATOS DE ANCIANOS SOLOS': 'ANCIANO_SOLO',
                'BASE DE DATOS DE POSTRADOS': 'POSTRADO',
                'BASE DE DATOS DE COMBATIENTES': 'COMBATIENTE',
                'BASE DE DATOS DE CENTENARIOS': 'CENTENARIO'
            }
            
            total = 0
            for sheet_name, tipo in tipos.items():
                if sheet_name in excel_file.sheet_names:
                    df = pd.read_excel(filename, sheet_name=sheet_name, header=3)
                    for _, row in df.iterrows():
                        if pd.notna(row.get('Nombres y Apellidos')):
                            fecha = row.get('FECHA DE N')
                            if pd.notna(fecha) and isinstance(fecha, (int, float)):
                                fecha = f"{int(fecha):06d}"
                                if len(fecha) == 6:
                                    fecha = f"{fecha[:2]}/{fecha[2:4]}/{fecha[4:]}"
                            
                            nombre_completo = str(row.get('Nombres y Apellidos', ''))
                            partes = nombre_completo.split(' ', 1)
                            nombre = partes[0]
                            apellidos = partes[1] if len(partes) > 1 else ''
                            
                            self.cursor.execute('''
                                INSERT INTO adultos_mayores 
                                (tipo_registro, numero, nombre, apellidos, fecha_nacimiento, direccion, app, 
                                 situacion_social, grupo_dispensarial, cmf, fecha_registro)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ''', (
                                tipo,
                                int(row.get('No', 0)) if pd.notna(row.get('No')) else None,
                                nombre, apellidos, fecha if fecha else None,
                                row.get('DIRECCIÓN') if pd.notna(row.get('DIRECCIÓN')) else None,
                                row.get('APP') if pd.notna(row.get('APP')) else None,
                                row.get('SITUACIÓN SOCIAL') if pd.notna(row.get('SITUACIÓN SOCIAL')) else None,
                                row.get('GRUPO DISPENSARIAL') if pd.notna(row.get('GRUPO DISPENSARIAL')) else None,
                                int(row.get('CMF', 0)) if pd.notna(row.get('CMF')) else None,
                                datetime.now().strftime("%Y-%m-%d")
                            ))
                            total += 1
            
            self.conn.commit()
            messagebox.showinfo("Éxito", f"Importados {total} registros")
            self.cargar_lista()
            self.cargar_estadisticas()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def exportar_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel", "*.xlsx")])
        if not filename:
            return
        
        try:
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                tipos = ['ANCIANO_SOLO', 'POSTRADO', 'COMBATIENTE', 'CENTENARIO']
                nombres = ['BASE DE DATOS DE ANCIANOS SOLOS', 'BASE DE DATOS DE POSTRADOS',
                          'BASE DE DATOS DE COMBATIENTES', 'BASE DE DATOS DE CENTENARIOS']
                
                for tipo, nombre_hoja in zip(tipos, nombres):
                    self.cursor.execute('''
                        SELECT numero, nombre, apellidos, fecha_nacimiento, direccion, app, 
                               situacion_social, grupo_dispensarial, cmf
                        FROM adultos_mayores WHERE tipo_registro = ? ORDER BY numero
                    ''', (tipo,))
                    
                    datos = self.cursor.fetchall()
                    if datos:
                        df = pd.DataFrame(datos, columns=['No', 'Nombre', 'Apellido', 'FECHA DE N', 'DIRECCIÓN', 
                                                         'APP', 'SITUACIÓN SOCIAL', 'GRUPO DISPENSARIAL', 'CMF'])
                        df['Nombres y Apellidos'] = df['Nombre'] + ' ' + df['Apellido']
                        df = df.drop(['Nombre', 'Apellido'], axis=1)
                        df = df[['No', 'Nombres y Apellidos', 'FECHA DE N', 'DIRECCIÓN', 'APP', 
                                'SITUACIÓN SOCIAL', 'GRUPO DISPENSARIAL', 'CMF']]
                        df.to_excel(writer, sheet_name=nombre_hoja, index=False, startrow=3)
                        
                        ws = writer.sheets[nombre_hoja]
                        for col_idx, col_name in enumerate(['No', 'Nombres y Apellidos', 'FECHA DE N', 
                                                           'DIRECCIÓN', '', 'APP', 'SITUACIÓN SOCIAL', '', 
                                                           'GRUPO DISPENSARIAL', '', 'CMF'], 1):
                            ws.cell(row=1, column=col_idx, value=col_name)
            
            messagebox.showinfo("Éxito", f"Exportado a {filename}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def limpiar_ventana(self):
        for widget in self.root.winfo_children():
            widget.destroy()

if __name__ == '__main__':
    app = SistemaAdultoMayor()