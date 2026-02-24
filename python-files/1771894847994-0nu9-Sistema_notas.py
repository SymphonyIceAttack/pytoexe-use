import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
import os
from datetime import datetime
import hashlib
import json
import csv
from pathlib import Path
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
import sys

# Configuración de customtkinter
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class SistemaNotasUniversidad:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Sistema de Gestión de Notas - IULAPF")
        self.root.geometry("1200x700")
        
        try:
            # Para desarrollo (archivo .ico en la misma carpeta)
            if getattr(sys, 'frozen', False):
                # Si está empaquetado como ejecutable
                base_path = sys._MEIPASS
            else:
                # Si está ejecutando desde código fuente
                base_path = os.path.dirname(os.path.abspath(__file__))
            
            icon_path = os.path.join(base_path, "icono.ico")
            
            # Para tkinter normal (no todos los sistemas soportan .ico en customtkinter)
            self.root.iconbitmap(icon_path)
            
        except Exception as e:
            print(f"No se pudo cargar el icono: {e}")

        # Variables globales
        self.profesor_actual = None
        self.ruta_db = None
        self.df_estudiantes = None
        self.df_profesores = None
        
        # Estado de la base de datos
        self.db_cargada = False
        
        # Estilos
        self.colores = {
            "azul_principal": "#178236",
            "azul_secundario": "#2A9689",
            "blanco": "#FFFFFF",
            "gris_claro": "#F8FAFC",
            "gris_medio": "#E2E8F0",
            "verde": "#2A9689",
            "rojo": "#82181A"
        }
        
        # Configurar fuente
        self.fuente_principal = ("Segoe UI", 12)
        self.fuente_titulo = ("Segoe UI", 16, "bold")
        
        # Inicializar entradas y componentes
        self.entries_login = {}
        self.entries_registro = {}
        self.entries_estudiante = {}
        self.tree_notas = None
        self.entries_modulos = []
        self.tree_editar = None
        self.entry_edit_nombre = None
        self.entry_edit_cedula = None
        self.combo_tipo_cedula_registro = None
        self.combo_tipo_cedula_estudiante = None
        self.combo_tipo_cedula_edit = None
        
        self.inicializar_sistema()
    
    def actualizar_estado_db(self):
        """Actualiza el estado de la base de datos en la interfaz"""
        if hasattr(self, 'lbl_estado_db'):
            if self.ruta_db and self.db_cargada:
                nombre_db = os.path.basename(self.ruta_db)
                self.lbl_estado_db.configure(
                    text=f"✓ Base de datos: {nombre_db}",
                    text_color=self.colores["verde"]
                )
            else:
                self.lbl_estado_db.configure(
                    text="✗ Base de datos no cargada",
                    text_color=self.colores["rojo"]
                )
    
    def inicializar_sistema(self):
        """Inicializa el sistema mostrando la pantalla de inicio"""
        self.limpiar_pantalla()
        
        # Frame principal
        frame_principal = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame_principal.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Logo/título
        titulo_frame = ctk.CTkFrame(frame_principal, fg_color=self.colores["azul_principal"], height=100)
        titulo_frame.pack(fill="x", pady=(0, 10))
        
        titulo = ctk.CTkLabel(
            titulo_frame,
            text="INSTITUTO UNIVERSITARIO LATINOAMERICANO\nDE AGROECOLOGÍA PAULO FREIRE",
            font=("Segoe UI", 20, "bold"),
            text_color=self.colores["blanco"],
            justify="center"
        )
        titulo.pack(pady=20)
        
        # Estado de la base de datos
        estado_frame = ctk.CTkFrame(frame_principal, fg_color=self.colores["gris_claro"], height=40)
        estado_frame.pack(fill="x", pady=(0, 20))
        estado_frame.pack_propagate(False)
        
        self.lbl_estado_db = ctk.CTkLabel(
            estado_frame,
            text="✗ Base de datos no cargada",
            font=("Segoe UI", 12),
            text_color=self.colores["rojo"]
        )
        self.lbl_estado_db.pack(pady=10)
        
        # Actualizar estado
        self.actualizar_estado_db()
        
        # Frame de opciones
        opciones_frame = ctk.CTkFrame(frame_principal, fg_color=self.colores["gris_claro"])
        opciones_frame.pack(expand=True, fill="both", padx=100, pady=20)
        
        # Título de opciones
        subtitulo = ctk.CTkLabel(
            opciones_frame,
            text="SISTEMA DE GESTIÓN DE NOTAS",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        subtitulo.pack(pady=(30, 20))
        
        # Botones
        btn_iniciar = ctk.CTkButton(
            opciones_frame,
            text="INICIAR SESIÓN",
            command=self.mostrar_login,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            height=40,
            width=250
        )
        btn_iniciar.pack(pady=10)
        
        btn_registrar = ctk.CTkButton(
            opciones_frame,
            text="REGISTRAR PROFESOR",
            command=self.mostrar_registro_profesor,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            height=40,
            width=250
        )
        btn_registrar.pack(pady=10)
        
        btn_crear_db = ctk.CTkButton(
            opciones_frame,
            text="CREAR NUEVA BASE DE DATOS",
            command=self.crear_base_datos,
            font=self.fuente_principal,
            fg_color=self.colores["verde"],
            hover_color="#059669",
            height=40,
            width=250
        )
        btn_crear_db.pack(pady=10)
        
        btn_cargar_db = ctk.CTkButton(
            opciones_frame,
            text="CARGAR BASE DE DATOS EXISTENTE",
            command=self.cargar_base_datos,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            height=40,
            width=250
        )
        btn_cargar_db.pack(pady=10)
        
        btn_salir = ctk.CTkButton(
            opciones_frame,
            text="SALIR",
            command=self.root.quit,
            font=self.fuente_principal,
            fg_color=self.colores["rojo"],
            hover_color="#DC2626",
            height=40,
            width=250
        )
        btn_salir.pack(pady=20)
    
    def limpiar_pantalla(self):
        """Limpia todos los widgets de la pantalla"""
        for widget in self.root.winfo_children():
            widget.destroy()
    
    def crear_base_datos(self):
        """Crea un nuevo archivo Excel para la base de datos"""
        ruta = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="Guardar base de datos",
            initialfile="base_datos_notas.xlsx"
        )
        
        if ruta:
            try:
                # Crear DataFrames vacíos con tipos de datos correctos
                df_profesores = pd.DataFrame(columns=[
                    'nombre', 'cedula', 'tipo_cedula', 'carrera', 'semestre', 'materia',
                    'usuario', 'contrasena_hash', 'pregunta', 'respuesta_hash'
                ])
                
                df_estudiantes = pd.DataFrame(columns=[
                    'nombre', 'cedula', 'tipo_cedula', 'carrera', 'semestre', 'materia',
                    'profesor_cedula', 'profesor_tipo_cedula', 'modulo1', 'modulo2', 'modulo3', 'modulo4',
                    'nota_final', 'estado', 'fecha_registro'
                ])
                
                # Especificar tipos de datos para evitar problemas
                df_profesores = df_profesores.astype({
                    'nombre': 'object',
                    'cedula': 'object',
                    'tipo_cedula': 'object',
                    'carrera': 'object',
                    'semestre': 'object',
                    'materia': 'object',
                    'usuario': 'object',
                    'contrasena_hash': 'object',
                    'pregunta': 'object',
                    'respuesta_hash': 'object'
                })
                
                df_estudiantes = df_estudiantes.astype({
                    'nombre': 'object',
                    'cedula': 'object',
                    'tipo_cedula': 'object',
                    'carrera': 'object',
                    'semestre': 'object',
                    'materia': 'object',
                    'profesor_cedula': 'object',
                    'profesor_tipo_cedula': 'object',
                    'modulo1': 'float64',
                    'modulo2': 'float64',
                    'modulo3': 'float64',
                    'modulo4': 'float64',
                    'nota_final': 'float64',
                    'estado': 'object',
                    'fecha_registro': 'object'
                })
                
                # Guardar en Excel con múltiples hojas
                with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
                    df_profesores.to_excel(writer, sheet_name='profesores', index=False)
                    df_estudiantes.to_excel(writer, sheet_name='estudiantes', index=False)
                
                # Cargar la base de datos recién creada
                self.ruta_db = ruta
                self.df_profesores = df_profesores
                self.df_estudiantes = df_estudiantes
                self.db_cargada = True
                
                messagebox.showinfo("Éxito", f"Base de datos creada y cargada:\n{ruta}")
                self.actualizar_estado_db()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo crear la base de datos: {str(e)}")
    
    def guardar_estudiantes(self):
        """Guarda los estudiantes en la base de datos"""
        if self.ruta_db and self.df_estudiantes is not None:
            try:
                with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    self.df_estudiantes.to_excel(writer, sheet_name='estudiantes', index=False)
                messagebox.showinfo("Éxito", "Estudiantes guardados correctamente.")
            except ValueError as ve:
                messagebox.showerror("Error", f"Error al guardar estudiantes: {ve}")
            except PermissionError:
                messagebox.showerror("Error", "El archivo está abierto en otro programa. Ciérrelo e intente nuevamente.")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {e}")
        else:
            messagebox.showwarning("Advertencia", "No hay base de datos cargada o estudiantes para guardar.")

    def cargar_base_datos(self):
        """Carga la base de datos desde un archivo Excel"""
        ruta = filedialog.askopenfilename(
            filetypes=[("Excel files", "*.xlsx"), ("Excel files", "*.xls"), ("All files", "*.*")],
            title="Seleccionar base de datos"
        )

        if ruta:
            try:
                self.ruta_db = ruta
                excel_file = pd.ExcelFile(ruta)
                hojas_requeridas = {'profesores', 'estudiantes'}
                hojas_existentes = set(excel_file.sheet_names)

                if not hojas_requeridas.issubset(hojas_existentes):
                    self.crear_estructura_db(ruta)
                else:
                    # Forzar tipos de datos correctos al cargar
                    self.df_profesores = pd.read_excel(ruta, sheet_name='profesores', dtype={
                        'nombre': str,
                        'cedula': str,
                        'tipo_cedula': str,
                        'carrera': str,
                        'semestre': str,
                        'materia': str,
                        'usuario': str,
                        'contrasena_hash': str,
                        'pregunta': str,
                        'respuesta_hash': str
                    })
                    
                    self.df_estudiantes = pd.read_excel(ruta, sheet_name='estudiantes', dtype={
                        'nombre': str,
                        'cedula': str,
                        'tipo_cedula': str,
                        'carrera': str,
                        'semestre': str,
                        'materia': str,
                        'profesor_cedula': str,
                        'profesor_tipo_cedula': str,
                        'modulo1': float,
                        'modulo2': float,
                        'modulo3': float,
                        'modulo4': float,
                        'nota_final': float,
                        'estado': str,
                        'fecha_registro': str
                    })

                self.db_cargada = True
                messagebox.showinfo("Éxito", "Base de datos cargada correctamente")
                self.actualizar_estado_db()
                return True

            except FileNotFoundError:
                messagebox.showerror("Error", "Archivo no encontrado.")
            except pd.errors.ExcelFileError:
                messagebox.showerror("Error", "El archivo seleccionado no es válido.")
            except Exception as e:
                messagebox.showerror("Error", f"Error inesperado: {e}")
        return False
    
    def crear_estructura_db(self, ruta):
        """Crea la estructura básica de la base de datos"""
        df_profesores = pd.DataFrame(columns=[
            'nombre', 'cedula', 'tipo_cedula', 'carrera', 'semestre', 'materia',
            'usuario', 'contrasena_hash', 'pregunta', 'respuesta_hash'
        ])
        
        df_estudiantes = pd.DataFrame(columns=[
            'nombre', 'cedula', 'tipo_cedula', 'carrera', 'semestre', 'materia',
            'profesor_cedula', 'profesor_tipo_cedula', 'modulo1', 'modulo2', 'modulo3', 'modulo4',
            'nota_final', 'estado', 'fecha_registro'
        ])
        
        # Especificar tipos de datos
        df_profesores = df_profesores.astype({
            'nombre': 'object',
            'cedula': 'object',
            'tipo_cedula': 'object',
            'carrera': 'object',
            'semestre': 'object',
            'materia': 'object',
            'usuario': 'object',
            'contrasena_hash': 'object',
            'pregunta': 'object',
            'respuesta_hash': 'object'
        })
        
        df_estudiantes = df_estudiantes.astype({
            'nombre': 'object',
            'cedula': 'object',
            'tipo_cedula': 'object',
            'carrera': 'object',
            'semestre': 'object',
            'materia': 'object',
            'profesor_cedula': 'object',
            'profesor_tipo_cedula': 'object',
            'modulo1': 'float64',
            'modulo2': 'float64',
            'modulo3': 'float64',
            'modulo4': 'float64',
            'nota_final': 'float64',
            'estado': 'object',
            'fecha_registro': 'object'
        })
        
        with pd.ExcelWriter(ruta, engine='openpyxl') as writer:
            df_profesores.to_excel(writer, sheet_name='profesores', index=False)
            df_estudiantes.to_excel(writer, sheet_name='estudiantes', index=False)
        
        self.df_profesores = df_profesores
        self.df_estudiantes = df_estudiantes
    
    def hash_password(self, password):
        """Crea un hash SHA-256 de la contraseña"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def validar_cedula(self, cedula, tipo_cedula):
        """Valida formato de cédula según el tipo"""
        try:
            if tipo_cedula == "V":
                # Venezolano: exactamente 7-8 dígitos numéricos
                if len(cedula) < 7 or len(cedula) > 8 or not cedula.isdigit():
                    return False
            elif tipo_cedula == "E":
                # Extranjero: máximo 15 caracteres alfanuméricos, letras mayúsculas
                if len(cedula) > 15:
                    return False
                # Verificar que sea alfanumérico
                if not cedula.isalnum():
                    return False
                # Convertir a mayúsculas para validación (se guardará así)
                cedula = cedula.upper()
            return True
        except:
            return False
    
    def mostrar_login(self):
        """Muestra la pantalla de inicio de sesión"""
        # Verificar si hay base de datos cargada
        if not self.db_cargada:
            respuesta = messagebox.askyesno(
                "Base de datos no cargada",
                "Para iniciar sesión necesita una base de datos. ¿Desea cargar una ahora?"
            )
            if respuesta:
                if not self.cargar_base_datos():
                    return
            else:
                return
        
        self.limpiar_pantalla()
        
        frame = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=50, pady=50)
        
        # Título
        titulo = ctk.CTkLabel(
            frame,
            text="INICIAR SESIÓN",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(20, 40))
        
        # Mostrar base de datos actual
        if self.ruta_db:
            nombre_db = os.path.basename(self.ruta_db)
            lbl_db = ctk.CTkLabel(
                frame,
                text=f"Base de datos: {nombre_db}",
                font=("Segoe UI", 11),
                text_color=self.colores["azul_principal"]
            )
            lbl_db.pack(pady=(0, 20))
        
        # Frame de formulario
        form_frame = ctk.CTkFrame(frame, fg_color=self.colores["gris_claro"])
        form_frame.pack(expand=True, fill="both", padx=100, pady=20)
        
        # Campos
        campos = [
            ("Usuario", "entry_usuario"),
            ("Contraseña", "entry_contrasena")
        ]
        
        for i, (label_text, key) in enumerate(campos):
            lbl = ctk.CTkLabel(
                form_frame,
                text=label_text + ":",
                font=self.fuente_principal,
                text_color=self.colores["azul_principal"]
            )
            lbl.grid(row=i, column=0, padx=20, pady=15, sticky="e")
            
            if "contraseña" in label_text.lower():
                entry = ctk.CTkEntry(
                    form_frame,
                    font=self.fuente_principal,
                    width=300,
                    show="*"
                )
            else:
                entry = ctk.CTkEntry(
                    form_frame,
                    font=self.fuente_principal,
                    width=300
                )
            
            entry.grid(row=i, column=1, padx=20, pady=15, sticky="w")
            self.entries_login[key] = entry
        
        # Botones
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.grid(row=len(campos), column=0, columnspan=2, pady=30)
        
        btn_iniciar = ctk.CTkButton(
            btn_frame,
            text="INICIAR SESIÓN",
            command=self.iniciar_sesion,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            width=150
        )
        btn_iniciar.pack(side="left", padx=10)
        
        btn_recuperar = ctk.CTkButton(
            btn_frame,
            text="RECUPERAR CONTRASEÑA",
            command=self.mostrar_recuperar_contrasena,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            width=150
        )
        btn_recuperar.pack(side="left", padx=10)
        
        btn_volver = ctk.CTkButton(
            btn_frame,
            text="VOLVER",
            command=self.inicializar_sistema,
            font=self.fuente_principal,
            fg_color="#6B7280",
            hover_color="#4B5563",
            width=150
        )
        btn_volver.pack(side="left", padx=10)
    
    def mostrar_recuperar_contrasena(self):
        """Muestra ventana para recuperar contraseña"""
        if not self.db_cargada:
            messagebox.showwarning("Advertencia", "Primero debe cargar una base de datos")
            return
        
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Recuperar Contraseña")
        ventana.geometry("720x1024")
        ventana.transient(self.root)
        ventana.grab_set()
        
        frame = ctk.CTkFrame(ventana, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        titulo = ctk.CTkLabel(
            frame,
            text="RECUPERAR CONTRASEÑA",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=20)
        
        # Información de base de datos
        if self.ruta_db:
            nombre_db = os.path.basename(self.ruta_db)
            lbl_db_info = ctk.CTkLabel(
                frame,
                text=f"Base de datos: {nombre_db}",
                font=("Segoe UI", 10),
                text_color=self.colores["gris_medio"]
            )
            lbl_db_info.pack(pady=(0, 10))
        
        # Campos
        lbl_usuario = ctk.CTkLabel(
            frame,
            text="Usuario:",
            font=self.fuente_principal
        )
        lbl_usuario.pack(pady=5)
        
        entry_usuario = ctk.CTkEntry(frame, width=300)
        entry_usuario.pack(pady=5)
        
        lbl_pregunta = ctk.CTkLabel(
            frame,
            text="Pregunta de seguridad:",
            font=self.fuente_principal
        )
        lbl_pregunta.pack(pady=5)
        
        lbl_pregunta_texto = ctk.CTkLabel(
            frame,
            text="[Ingrese usuario para ver la pregunta]",
            font=self.fuente_principal,
            text_color=self.colores["azul_principal"],
            wraplength=400
        )
        lbl_pregunta_texto.pack(pady=5)
        
        lbl_respuesta = ctk.CTkLabel(
            frame,
            text="Respuesta:",
            font=self.fuente_principal
        )
        lbl_respuesta.pack(pady=5)
        
        entry_respuesta = ctk.CTkEntry(frame, width=300)
        entry_respuesta.pack(pady=5)
        
        lbl_nueva = ctk.CTkLabel(
            frame,
            text="Nueva Contraseña:",
            font=self.fuente_principal
        )
        lbl_nueva.pack(pady=5)
        
        entry_nueva = ctk.CTkEntry(frame, width=300, show="*")
        entry_nueva.pack(pady=5)
        
        lbl_confirmar = ctk.CTkLabel(
            frame,
            text="Confirmar Nueva Contraseña:",
            font=self.fuente_principal
        )
        lbl_confirmar.pack(pady=5)
        
        entry_confirmar = ctk.CTkEntry(frame, width=300, show="*")
        entry_confirmar.pack(pady=5)
        
        def buscar_usuario():
            usuario = entry_usuario.get().strip()
            if not usuario:
                messagebox.showwarning("Advertencia", "Ingrese un usuario")
                return
            
            # Buscar usuario en la base de datos cargada
            if self.df_profesores is None or self.df_profesores.empty:
                messagebox.showerror("Error", "No hay profesores registrados en la base de datos")
                return
            
            profesor = self.df_profesores[self.df_profesores['usuario'] == usuario]
            
            if len(profesor) == 0:
                messagebox.showerror("Error", "Usuario no encontrado")
                return
            
            lbl_pregunta_texto.configure(text=profesor.iloc[0]['pregunta'])
        
        def recuperar():
            usuario = entry_usuario.get().strip()
            respuesta = entry_respuesta.get().strip()
            nueva_contrasena = entry_nueva.get().strip()
            confirmar_contrasena = entry_confirmar.get().strip()
            
            if not all([usuario, respuesta, nueva_contrasena, confirmar_contrasena]):
                messagebox.showwarning("Advertencia", "Complete todos los campos")
                return
            
            if nueva_contrasena != confirmar_contrasena:
                messagebox.showwarning("Advertencia", "Las contraseñas no coinciden")
                return
            
            if len(nueva_contrasena) < 6:
                messagebox.showwarning("Advertencia", "La contraseña debe tener al menos 6 caracteres")
                return
            
            # Buscar profesor
            profesor_idx = self.df_profesores[self.df_profesores['usuario'] == usuario].index
            
            if len(profesor_idx) == 0:
                messagebox.showerror("Error", "Usuario no encontrado")
                return
            
            # Verificar respuesta
            respuesta_hash = self.hash_password(respuesta)
            profesor = self.df_profesores.loc[profesor_idx[0]]
            
            if profesor['respuesta_hash'] != respuesta_hash:
                messagebox.showerror("Error", "Respuesta incorrecta")
                return
            
            # Actualizar contraseña
            self.df_profesores.loc[profesor_idx[0], 'contrasena_hash'] = self.hash_password(nueva_contrasena)
            
            # Guardar cambios en el archivo
            try:
                with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    self.df_profesores.to_excel(writer, sheet_name='profesores', index=False)
                
                messagebox.showinfo("Éxito", "Contraseña actualizada correctamente")
                ventana.destroy()
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo actualizar la contraseña: {str(e)}")
        
        btn_buscar = ctk.CTkButton(
            frame,
            text="BUSCAR USUARIO",
            command=buscar_usuario,
            fg_color=self.colores["azul_secundario"],
            width=200
        )
        btn_buscar.pack(pady=10)
        
        btn_recuperar = ctk.CTkButton(
            frame,
            text="RECUPERAR",
            command=recuperar,
            fg_color=self.colores["verde"],
            width=200
        )
        btn_recuperar.pack(pady=5)
        
        btn_cancelar = ctk.CTkButton(
            frame,
            text="CANCELAR",
            command=ventana.destroy,
            fg_color="#6B7280",
            width=200
        )
        btn_cancelar.pack(pady=5)
    
    def iniciar_sesion(self):
        """Valida las credenciales del profesor"""
        usuario = self.entries_login["entry_usuario"].get().strip()
        contrasena = self.entries_login["entry_contrasena"].get().strip()
        
        if not usuario or not contrasena:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        # Verificar que hay base de datos cargada
        if not self.db_cargada or self.df_profesores is None:
            messagebox.showerror("Error", "No hay base de datos cargada")
            return
        
        # Buscar usuario
        profesor = self.df_profesores[self.df_profesores['usuario'] == usuario]
        
        if len(profesor) == 0:
            messagebox.showerror("Error", "Usuario no encontrado")
            return
        
        contrasena_hash = self.hash_password(contrasena)
        
        if profesor.iloc[0]['contrasena_hash'] != contrasena_hash:
            messagebox.showerror("Error", "Contraseña incorrecta")
            return
        
        self.profesor_actual = profesor.iloc[0]
        self.mostrar_menu_principal()
    
    def mostrar_registro_profesor(self):
        """Muestra el formulario de registro de profesor"""
        # Verificar si hay base de datos cargada
        if not self.db_cargada:
            respuesta = messagebox.askyesno(
                "Base de datos no cargada",
                "Para registrar un profesor necesita una base de datos. ¿Desea crear o cargar una ahora?"
            )
            if respuesta:
                # Mostrar opciones
                opcion = messagebox.askquestion(
                    "Seleccionar opción",
                    "¿Qué desea hacer?\n\nSí: Crear nueva base de datos\nNo: Cargar base de datos existente"
                )
                if opcion == 'yes':
                    self.crear_base_datos()
                else:
                    self.cargar_base_datos()
                
                if not self.db_cargada:
                    return
            else:
                return
        
        self.limpiar_pantalla()
        
        frame = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame,
            text="REGISTRO DE PROFESOR",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(20, 10))
        
        # Mostrar base de datos actual
        if self.ruta_db:
            nombre_db = os.path.basename(self.ruta_db)
            lbl_db = ctk.CTkLabel(
                frame,
                text=f"Base de datos: {nombre_db}",
                font=("Segoe UI", 11),
                text_color=self.colores["verde"]
            )
            lbl_db.pack(pady=(0, 20))
        
        # Frame con scroll
        canvas = tk.Canvas(frame, bg=self.colores["blanco"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ctk.CTkFrame(canvas, fg_color=self.colores["gris_claro"])
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True, padx=(0, 5))
        scrollbar.pack(side="right", fill="y")
        
        # Campos del formulario
        campos = [
            ("Nombre y Apellido", "entry_nombre"),
            ("Cédula de Identidad", "entry_cedula"),
            ("Carrera", "entry_carrera"),
            ("Semestre", "entry_semestre"),
            ("Materia", "entry_materia"),
            ("Usuario", "entry_usuario"),
            ("Contraseña", "entry_contrasena"),
            ("Confirmar Contraseña", "entry_confirmar"),
            ("Pregunta de Seguridad", "entry_pregunta"),
            ("Respuesta de Seguridad", "entry_respuesta")
        ]
        
        # Primero creamos todos los labels y entries
        row_index = 0
        for i, (label_text, key) in enumerate(campos):
            # Label
            lbl = ctk.CTkLabel(
                scrollable_frame,
                text=label_text + ":",
                font=self.fuente_principal,
                text_color=self.colores["azul_principal"]
            )
            lbl.grid(row=row_index, column=0, padx=20, pady=10, sticky="e")
            
            # Para el campo de cédula, agregamos combo box de tipo
            if "Cédula" in label_text:
                # Frame para contener tipo y número
                cedula_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
                cedula_frame.grid(row=row_index, column=1, padx=20, pady=10, sticky="w")
                
                # Combo box para tipo de cédula (V o E)
                self.combo_tipo_cedula_registro = ctk.CTkComboBox(
                    cedula_frame,
                    values=["V", "E"],
                    width=60,
                    font=self.fuente_principal,
                    state="readonly"
                )
                self.combo_tipo_cedula_registro.set("V")  # Valor por defecto
                self.combo_tipo_cedula_registro.pack(side="left", padx=(0, 5))
                
                # Entry para el número de cédula (más ancho para extranjeros)
                entry = ctk.CTkEntry(
                    cedula_frame,
                    font=self.fuente_principal,
                    width=230
                )
                entry.pack(side="left")
                self.entries_registro[key] = entry
            else:
                # Para otros campos, entry normal
                if "contraseña" in label_text.lower() and "confirmar" not in label_text.lower():
                    entry = ctk.CTkEntry(
                        scrollable_frame,
                        font=self.fuente_principal,
                        width=300,
                        show="*"
                    )
                elif "confirmar" in label_text.lower():
                    entry = ctk.CTkEntry(
                        scrollable_frame,
                        font=self.fuente_principal,
                        width=300,
                        show="*"
                    )
                else:
                    entry = ctk.CTkEntry(
                        scrollable_frame,
                        font=self.fuente_principal,
                        width=300
                    )
                entry.grid(row=row_index, column=1, padx=20, pady=10, sticky="w")
                self.entries_registro[key] = entry
            
            row_index += 1
        
        # Botones
        btn_frame = ctk.CTkFrame(scrollable_frame, fg_color="transparent")
        btn_frame.grid(row=row_index, column=0, columnspan=2, pady=30)
        
        btn_registrar = ctk.CTkButton(
            btn_frame,
            text="REGISTRAR",
            command=self.registrar_profesor,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            width=150
        )
        btn_registrar.pack(side="left", padx=10)
        
        btn_volver = ctk.CTkButton(
            btn_frame,
            text="VOLVER",
            command=self.inicializar_sistema,
            font=self.fuente_principal,
            fg_color="#6B7280",
            hover_color="#4B5563",
            width=150
        )
        btn_volver.pack(side="left", padx=10)
    
    def registrar_profesor(self):
        """Registra un nuevo profesor en la base de datos"""
        # Obtener valores
        datos = {}
        for key, entry in self.entries_registro.items():
            datos[key.replace("entry_", "")] = entry.get().strip()
        
        # Obtener tipo de cédula
        tipo_cedula = self.combo_tipo_cedula_registro.get()
        
        # Validaciones
        if not all(datos.values()):
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        # Validar cédula según el tipo
        if not self.validar_cedula(datos['cedula'], tipo_cedula):
            if tipo_cedula == "V":
                messagebox.showwarning("Advertencia", "Cédula venezolana inválida. Debe tener 7 u 8 dígitos numéricos")
            else:
                messagebox.showwarning("Advertencia", "Cédula de extranjero inválida. Máximo 15 caracteres alfanuméricos (solo letras mayúsculas y números)")
            return
        
        # Para extranjeros, asegurar que las letras estén en mayúsculas
        if tipo_cedula == "E":
            datos['cedula'] = datos['cedula'].upper()
        
        if datos['contrasena'] != datos['confirmar']:
            messagebox.showwarning("Advertencia", "Las contraseñas no coinciden")
            return
        
        if len(datos['contrasena']) < 6:
            messagebox.showwarning("Advertencia", "La contraseña debe tener al menos 6 caracteres")
            return
        
        # Crear cédula completa con tipo
        cedula_completa = f"{tipo_cedula}-{datos['cedula']}"
        
        # Verificar si ya existe la cédula o usuario
        if not self.df_profesores.empty:
            # Comparar cédula completa
            if cedula_completa in self.df_profesores['cedula'].astype(str).values:
                messagebox.showwarning("Advertencia", "Ya existe un profesor con esta cédula")
                return
            
            if datos['usuario'] in self.df_profesores['usuario'].values:
                messagebox.showwarning("Advertencia", "El nombre de usuario ya está en uso")
                return
        
        # Crear nuevo registro
        nuevo_profesor = {
            'nombre': datos['nombre'],
            'cedula': cedula_completa,
            'tipo_cedula': tipo_cedula,
            'carrera': datos['carrera'],
            'semestre': datos['semestre'],
            'materia': datos['materia'],
            'usuario': datos['usuario'],
            'contrasena_hash': self.hash_password(datos['contrasena']),
            'pregunta': datos['pregunta'],
            'respuesta_hash': self.hash_password(datos['respuesta'])
        }
        
        # Agregar a DataFrame
        self.df_profesores = pd.concat([self.df_profesores, pd.DataFrame([nuevo_profesor])], ignore_index=True)
        
        # Guardar en Excel
        try:
            with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                self.df_profesores.to_excel(writer, sheet_name='profesores', index=False)
            
            messagebox.showinfo("Éxito", "Profesor registrado exitosamente")
            self.inicializar_sistema()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el registro: {str(e)}")
    
    def mostrar_menu_principal(self):
        """Muestra el menú principal después del login"""
        self.limpiar_pantalla()
        
        # Frame principal
        frame_principal = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame_principal.pack(fill="both", expand=True)
        
        # Barra superior
        barra_superior = ctk.CTkFrame(frame_principal, fg_color=self.colores["azul_principal"], height=100)
        barra_superior.pack(fill="x", pady=(0, 20))
        barra_superior.pack_propagate(False)
        
        # Información del profesor
        info_frame = ctk.CTkFrame(barra_superior, fg_color="transparent")
        info_frame.pack(side="left", fill="both", expand=True, padx=20, pady=10)
        
        lbl_nombre = ctk.CTkLabel(
            info_frame,
            text=f"Profesor: {self.profesor_actual['nombre']}",
            font=("Segoe UI", 14, "bold"),
            text_color=self.colores["blanco"]
        )
        lbl_nombre.pack(anchor="w")
        
        lbl_info = ctk.CTkLabel(
            info_frame,
            text=f"{self.profesor_actual['carrera']} | Semestre: {self.profesor_actual['semestre']} | Materia: {self.profesor_actual['materia']}",
            font=("Segoe UI", 12),
            text_color=self.colores["blanco"]
        )
        lbl_info.pack(anchor="w", pady=(5, 0))
        
        # Información de base de datos
        if self.ruta_db:
            nombre_db = os.path.basename(self.ruta_db)
            lbl_db = ctk.CTkLabel(
                info_frame,
                text=f"Base de datos: {nombre_db}",
                font=("Segoe UI", 10),
                text_color=self.colores["blanco"]
            )
            lbl_db.pack(anchor="w", pady=(5, 0))
        
        btn_cerrar = ctk.CTkButton(
            barra_superior,
            text="CERRAR SESIÓN",
            command=self.inicializar_sistema,
            font=self.fuente_principal,
            fg_color=self.colores["rojo"],
            hover_color="#DC2626",
            width=120
        )
        btn_cerrar.pack(side="right", padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame_principal,
            text="MENÚ PRINCIPAL",
            font=("Segoe UI", 24, "bold"),
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(0, 40))
        
        # Frame de botones
        botones_frame = ctk.CTkFrame(frame_principal, fg_color=self.colores["gris_claro"])
        botones_frame.pack(expand=True, fill="both", padx=100, pady=20)
        
        # Botones del menú
        opciones = [
            (" REGISTRAR ESTUDIANTES", self.mostrar_registro_estudiante),
            (" EDITAR ESTUDIANTES", self.mostrar_editar_estudiante),
            (" ELIMINAR ESTUDIANTE", self.mostrar_eliminar_estudiante),
            (" CARGAR NOTAS", self.mostrar_cargar_notas),
            (" GENERAR REPORTES", self.generar_reporte),
            (" VER TODOS LOS REGISTROS", self.mostrar_todos_registros),
            (" BORRAR TODOS LOS REGISTROS", self.borrar_todos_registros),
            (" GUARDAR CAMBIOS", self.guardar_cambios)
        ]
        
        for i, (texto, comando) in enumerate(opciones):
            btn = ctk.CTkButton(
                botones_frame,
                text=texto,
                command=comando,
                font=self.fuente_principal,
                fg_color=self.colores["azul_secundario"],
                hover_color=self.colores["azul_principal"],
                height=45,
                width=300
            )
            btn.grid(row=i//2, column=i%2, padx=20, pady=15)
    
    def cargar_datos_estudiantes(self):
        """Carga los datos de estudiantes desde la base de datos"""
        if not self.db_cargada or self.ruta_db is None:
            messagebox.showwarning("Advertencia", "No hay base de datos cargada")
            return False
        
        try:
            # Forzar tipos de datos correctos al cargar
            self.df_estudiantes = pd.read_excel(self.ruta_db, sheet_name='estudiantes', dtype={
                'nombre': str,
                'cedula': str,
                'tipo_cedula': str,
                'carrera': str,
                'semestre': str,
                'materia': str,
                'profesor_cedula': str,
                'profesor_tipo_cedula': str,
                'modulo1': float,
                'modulo2': float,
                'modulo3': float,
                'modulo4': float,
                'nota_final': float,
                'estado': str,
                'fecha_registro': str
            })
            
            # Filtrar por profesor actual (comparar cédula completa)
            if 'profesor_cedula' in self.df_estudiantes.columns:
                profesor_cedula_completa = self.profesor_actual['cedula']
                self.df_estudiantes = self.df_estudiantes[
                    self.df_estudiantes['profesor_cedula'].astype(str) == profesor_cedula_completa
                ]
            return True
        except Exception as e:
            # Si no hay estudiantes, crear DataFrame vacío con tipos correctos
            self.df_estudiantes = pd.DataFrame(columns=[
                'nombre', 'cedula', 'tipo_cedula', 'carrera', 'semestre', 'materia',
                'profesor_cedula', 'profesor_tipo_cedula', 'modulo1', 'modulo2', 'modulo3', 'modulo4',
                'nota_final', 'estado', 'fecha_registro'
            ]).astype({
                'nombre': 'object',
                'cedula': 'object',
                'tipo_cedula': 'object',
                'carrera': 'object',
                'semestre': 'object',
                'materia': 'object',
                'profesor_cedula': 'object',
                'profesor_tipo_cedula': 'object',
                'modulo1': 'float64',
                'modulo2': 'float64',
                'modulo3': 'float64',
                'modulo4': 'float64',
                'nota_final': 'float64',
                'estado': 'object',
                'fecha_registro': 'object'
            })
            return True
    
    def mostrar_registro_estudiante(self):
        """Muestra formulario para registrar estudiante"""
        self.limpiar_pantalla()
        
        frame = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame,
            text="REGISTRO DE ESTUDIANTE",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(20, 30))
        
        # Frame de formulario
        form_frame = ctk.CTkFrame(frame, fg_color=self.colores["gris_claro"])
        form_frame.pack(expand=True, fill="both", padx=100, pady=20)
        
        # Campos
        # Label para nombre
        lbl_nombre = ctk.CTkLabel(
            form_frame,
            text="Nombre y Apellido:",
            font=self.fuente_principal,
            text_color=self.colores["azul_principal"]
        )
        lbl_nombre.grid(row=0, column=0, padx=20, pady=15, sticky="e")
        
        entry_nombre = ctk.CTkEntry(
            form_frame,
            font=self.fuente_principal,
            width=300
        )
        entry_nombre.grid(row=0, column=1, padx=20, pady=15, sticky="w")
        self.entries_estudiante["entry_nombre"] = entry_nombre
        
        # Label para cédula (con tipo)
        lbl_cedula = ctk.CTkLabel(
            form_frame,
            text="Cédula:",
            font=self.fuente_principal,
            text_color=self.colores["azul_principal"]
        )
        lbl_cedula.grid(row=1, column=0, padx=20, pady=15, sticky="e")
        
        # Frame para cédula
        cedula_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        cedula_frame.grid(row=1, column=1, padx=20, pady=15, sticky="w")
        
        # Combo box para tipo de cédula
        self.combo_tipo_cedula_estudiante = ctk.CTkComboBox(
            cedula_frame,
            values=["V", "E"],
            width=60,
            font=self.fuente_principal,
            state="readonly"
        )
        self.combo_tipo_cedula_estudiante.set("V")  # Valor por defecto
        self.combo_tipo_cedula_estudiante.pack(side="left", padx=(0, 5))
        
        # Entry para número de cédula (más ancho para extranjeros)
        entry_cedula = ctk.CTkEntry(
            cedula_frame,
            font=self.fuente_principal,
            width=230
        )
        entry_cedula.pack(side="left")
        self.entries_estudiante["entry_cedula"] = entry_cedula
        
        # Información fija (del profesor)
        info_labels = [
            ("Carrera:", self.profesor_actual['carrera']),
            ("Semestre:", self.profesor_actual['semestre']),
            ("Materia:", self.profesor_actual['materia']),
            ("Profesor:", self.profesor_actual['nombre'])
        ]
        
        for i, (label, valor) in enumerate(info_labels, start=2):
            lbl = ctk.CTkLabel(
                form_frame,
                text=label,
                font=self.fuente_principal,
                text_color=self.colores["azul_principal"]
            )
            lbl.grid(row=i, column=0, padx=20, pady=10, sticky="e")
            
            lbl_valor = ctk.CTkLabel(
                form_frame,
                text=valor,
                font=self.fuente_principal,
                text_color=self.colores["azul_principal"]
            )
            lbl_valor.grid(row=i, column=1, padx=20, pady=10, sticky="w")
        
        # Botones
        btn_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        btn_frame.grid(row=2 + len(info_labels), column=0, columnspan=2, pady=30)
        
        btn_registrar = ctk.CTkButton(
            btn_frame,
            text="REGISTRAR",
            command=self.registrar_estudiante,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            width=150
        )
        btn_registrar.pack(side="left", padx=10)
        
        btn_volver = ctk.CTkButton(
            btn_frame,
            text="VOLVER",
            command=self.mostrar_menu_principal,
            font=self.fuente_principal,
            fg_color="#6B7280",
            hover_color="#4B5563",
            width=150
        )
        btn_volver.pack(side="left", padx=10)
    
    def registrar_estudiante(self):
        """Registra un nuevo estudiante"""
        nombre = self.entries_estudiante["entry_nombre"].get().strip()
        cedula_numero = self.entries_estudiante["entry_cedula"].get().strip()
        tipo_cedula = self.combo_tipo_cedula_estudiante.get()
        
        if not nombre or not cedula_numero:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        # Validar cédula según el tipo
        if not self.validar_cedula(cedula_numero, tipo_cedula):
            if tipo_cedula == "V":
                messagebox.showwarning("Advertencia", "Cédula venezolana inválida. Debe tener 7 u 8 dígitos numéricos")
            else:
                messagebox.showwarning("Advertencia", "Cédula de extranjero inválida. Máximo 15 caracteres alfanuméricos (solo letras mayúsculas y números)")
            return
        
        # Para extranjeros, asegurar que las letras estén en mayúsculas
        if tipo_cedula == "E":
            cedula_numero = cedula_numero.upper()
        
        # Crear cédula completa
        cedula_completa = f"{tipo_cedula}-{cedula_numero}"
        profesor_cedula_completa = self.profesor_actual['cedula']
        
        # Verificar que la cédula del estudiante no sea igual a la del profesor
        if cedula_completa == profesor_cedula_completa:
            messagebox.showwarning("Advertencia", 
                              "La cédula del estudiante no puede ser igual a la del profesor.\n"
                              f"Cédula del profesor: {profesor_cedula_completa}")
            return
        
        # Cargar datos si no están cargados
        if not self.cargar_datos_estudiantes():
            messagebox.showerror("Error", "No se pudo cargar la base de datos")
            return
        
        if not self.df_estudiantes.empty:
            # Buscar si ya existe la cédula para este profesor
            existente = self.df_estudiantes[
                (self.df_estudiantes['cedula'].astype(str) == cedula_completa) & 
                (self.df_estudiantes['profesor_cedula'].astype(str) == profesor_cedula_completa)
            ]
            
            if len(existente) > 0:
                messagebox.showwarning("Advertencia", "Ya existe un usuario con esta Cédula!")
                return
        
        # Crear nuevo registro
        nuevo_estudiante = {
            'nombre': nombre,
            'cedula': cedula_completa,
            'tipo_cedula': tipo_cedula,
            'carrera': str(self.profesor_actual['carrera']),
            'semestre': str(self.profesor_actual['semestre']),
            'materia': str(self.profesor_actual['materia']),
            'profesor_cedula': profesor_cedula_completa,
            'profesor_tipo_cedula': self.profesor_actual['tipo_cedula'],
            'modulo1': 0.0,
            'modulo2': 0.0,
            'modulo3': 0.0,
            'modulo4': 0.0,
            'nota_final': 0.0,
            'estado': 'No evaluado',
            'fecha_registro': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        # Agregar a DataFrame
        self.df_estudiantes = pd.concat([self.df_estudiantes, pd.DataFrame([nuevo_estudiante])], ignore_index=True)
        
        # Guardar inmediatamente en la base de datos
        try:
            # Cargar todos los estudiantes existentes
            df_todos_estudiantes = pd.read_excel(self.ruta_db, sheet_name='estudiantes', dtype={
                'cedula': str,
                'profesor_cedula': str
            })
            
            # Eliminar duplicados (si existe) y agregar el nuevo
            df_todos_estudiantes = df_todos_estudiantes[
                ~((df_todos_estudiantes['cedula'].astype(str) == cedula_completa) & 
                  (df_todos_estudiantes['profesor_cedula'].astype(str) == profesor_cedula_completa))
            ]
            
            df_todos_estudiantes = pd.concat([df_todos_estudiantes, pd.DataFrame([nuevo_estudiante])], ignore_index=True)
            
            # Guardar
            with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_todos_estudiantes.to_excel(writer, sheet_name='estudiantes', index=False)
            
            messagebox.showinfo("Éxito", "Estudiante registrado exitosamente")
            self.mostrar_menu_principal()
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar el estudiante: {str(e)}")
    
    def mostrar_cargar_notas(self):
        """Muestra interfaz para cargar notas de estudiantes"""
        if not self.cargar_datos_estudiantes():
            messagebox.showerror("Error", "No hay estudiantes registrados")
            self.mostrar_menu_principal()
            return
        
        self.limpiar_pantalla()
        
        frame = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame,
            text="CARGAR NOTAS DE ESTUDIANTES",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(20, 30))
        
        # Frame principal con scroll
        main_frame = ctk.CTkFrame(frame, fg_color=self.colores["gris_claro"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Crear Treeview para mostrar estudiantes
        columns = ('Nombre y Apellido', 'Cédula', 'Módulo 1', 'Módulo 2', 'Módulo 3', 'Módulo 4', 'Nota Final', 'Estado')
        
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview
        self.tree_notas = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=15
        )
        
        v_scrollbar.config(command=self.tree_notas.yview)
        h_scrollbar.config(command=self.tree_notas.xview)
        
        # Configurar columnas
        column_widths = [200, 120, 80, 80, 80, 80, 100, 100]
        for col, width in zip(columns, column_widths):
            self.tree_notas.heading(col, text=col)
            self.tree_notas.column(col, width=width, anchor='center')
        
        self.tree_notas.pack(fill='both', expand=True)
        
        # Cargar datos
        self.actualizar_treeview_notas()
        
        # Frame para editar notas
        edit_frame = ctk.CTkFrame(main_frame, fg_color=self.colores["gris_claro"])
        edit_frame.pack(fill="x", padx=10, pady=10)
        
        # Labels y entries para editar
        lbl_modulos = ["Módulo 1 (0-20):", "Módulo 2 (0-20):", "Módulo 3 (0-20):", "Módulo 4 (0-20):"]
        self.entries_modulos = []
        
        for i, lbl_text in enumerate(lbl_modulos):
            lbl = ctk.CTkLabel(
                edit_frame,
                text=lbl_text,
                font=self.fuente_principal
            )
            lbl.grid(row=0, column=i*2, padx=5, pady=5)
            
            entry = ctk.CTkEntry(
                edit_frame,
                width=80,
                font=self.fuente_principal
            )
            entry.grid(row=0, column=i*2+1, padx=5, pady=5)
            self.entries_modulos.append(entry)
        
        # Botones
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        btn_actualizar = ctk.CTkButton(
            btn_frame,
            text="ACTUALIZAR NOTAS",
            command=self.actualizar_notas_estudiante,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            hover_color=self.colores["azul_principal"],
            width=150
        )
        btn_actualizar.pack(side="left", padx=5)
        
        btn_guardar = ctk.CTkButton(
            btn_frame,
            text="GUARDAR TODO",
            command=self.guardar_cambios,
            font=self.fuente_principal,
            fg_color=self.colores["verde"],
            hover_color="#059669",
            width=150
        )
        btn_guardar.pack(side="left", padx=5)
        
        btn_volver = ctk.CTkButton(
            btn_frame,
            text="VOLVER",
            command=self.mostrar_menu_principal,
            font=self.fuente_principal,
            fg_color="#6B7280",
            hover_color="#4B5563",
            width=150
        )
        btn_volver.pack(side="left", padx=5)
        
        # Vincular selección
        self.tree_notas.bind('<<TreeviewSelect>>', self.seleccionar_estudiante_notas)
    
    def actualizar_treeview_notas(self):
        """Actualiza el Treeview con los datos de estudiantes"""
        # Limpiar treeview
        for item in self.tree_notas.get_children():
            self.tree_notas.delete(item)
        
        # Insertar datos
        for _, estudiante in self.df_estudiantes.iterrows():
            valores = (
                estudiante['nombre'],
                estudiante['cedula'],
                f"{estudiante['modulo1']:.2f}",
                f"{estudiante['modulo2']:.2f}",
                f"{estudiante['modulo3']:.2f}",
                f"{estudiante['modulo4']:.2f}",
                f"{estudiante['nota_final']:.2f}",
                estudiante['estado']
            )
            self.tree_notas.insert('', 'end', values=valores)
    
    def seleccionar_estudiante_notas(self, event):
        """Carga los datos del estudiante seleccionado en los entries"""
        seleccion = self.tree_notas.selection()
        if not seleccion:
            return
        
        item = self.tree_notas.item(seleccion[0])
        cedula = item['values'][1]
        
        # Filtrar estudiante
        estudiante_df = self.df_estudiantes[self.df_estudiantes['cedula'].astype(str) == cedula]
        
        if len(estudiante_df) == 0:
            return
        
        estudiante = estudiante_df.iloc[0]
        
        # Cargar notas en los entries
        for i, entry in enumerate(self.entries_modulos):
            entry.delete(0, 'end')
            entry.insert(0, f"{estudiante[f'modulo{i+1}']:.2f}")
    
    def calcular_nota_final(self, modulos):
        """
        Calcula la nota final basada en los 4 módulos (25% cada uno)
        Cada módulo se califica sobre 20 puntos
        """
        # Verificar que todos los módulos estén dentro del rango 0-20
        for nota in modulos:
            if nota < 0 or nota > 20:
                return None
        
        # Cada módulo vale 25% (0.25) de la nota final
        # Nota final = (M1 * 0.25) + (M2 * 0.25) + (M3 * 0.25) + (M4 * 0.25)
        # Que es lo mismo que: (M1 + M2 + M3 + M4) / 4
        nota_final = sum(modulos) / 4
        
        # Redondear a 2 decimales
        return round(nota_final, 2)
    
    def actualizar_notas_estudiante(self):
        """Actualiza las notas del estudiante seleccionado"""
        seleccion = self.tree_notas.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un estudiante")
            return
        
        item = self.tree_notas.item(seleccion[0])
        cedula = item['values'][1]
        
        # Obtener notas de los entries
        try:
            modulos = []
            for i, entry in enumerate(self.entries_modulos):
                valor_texto = entry.get().strip()
                if not valor_texto:  # Si está vacío, usar 0
                    valor = 0.0
                else:
                    valor = float(valor_texto)
                
                if valor < 0 or valor > 20:
                    messagebox.showwarning("Advertencia", f"Módulo {i+1} debe estar entre 0 y 20")
                    return
                modulos.append(valor)
        except ValueError:
            messagebox.showwarning("Advertencia", "Ingrese valores numéricos válidos (ej: 15.5, 18, 12.75)")
            return
        
        # Calcular nota final
        nota_final = self.calcular_nota_final(modulos)
        
        if nota_final is None:
            messagebox.showwarning("Advertencia", "Error al calcular la nota final")
            return
        
        # Determinar estado (aprobado si nota >= 10)
        estado = "Aprobado" if nota_final >= 10 else "Reprobado"
        
        # Encontrar índice del estudiante
        indices = self.df_estudiantes.index[self.df_estudiantes['cedula'].astype(str) == cedula].tolist()
        
        if not indices:
            messagebox.showerror("Error", "Estudiante no encontrado")
            return
        
        idx = indices[0]
        
        # Actualizar DataFrame asegurando tipos correctos
        for i in range(1, 5):
            self.df_estudiantes.at[idx, f'modulo{i}'] = float(modulos[i-1])
        
        self.df_estudiantes.at[idx, 'nota_final'] = float(nota_final)
        self.df_estudiantes.at[idx, 'estado'] = estado
        
        # Actualizar treeview
        self.actualizar_treeview_notas()
        
        # Mostrar información de la nota
        info_text = f"Notas actualizadas:\n"
        for i, nota in enumerate(modulos, 1):
            info_text += f"Módulo {i}: {nota:.2f}/20\n"
        info_text += f"\nNota Final: {nota_final:.2f}/20\nEstado: {estado}"
        
        messagebox.showinfo("Éxito", info_text)
    
    def mostrar_editar_estudiante(self):
        """Muestra interfaz para editar datos de estudiantes"""
        if not self.cargar_datos_estudiantes():
            messagebox.showerror("Error", "No hay estudiantes registrados")
            self.mostrar_menu_principal()
            return
        
        self.limpiar_pantalla()
        
        frame = ctk.CTkFrame(self.root, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Título
        titulo = ctk.CTkLabel(
            frame,
            text="EDITAR DATOS DE ESTUDIANTE",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=(20, 30))
        
        # Frame principal
        main_frame = ctk.CTkFrame(frame, fg_color=self.colores["gris_claro"])
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Treeview para seleccionar estudiante
        tree_frame = ctk.CTkFrame(main_frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ('Nombre', 'Cédula', 'Carrera', 'Semestre', 'Materia', 'Nota Final', 'Estado')
        self.tree_editar = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        # Configurar columnas
        column_widths = [200, 120, 150, 80, 150, 100, 100]
        for col, width in zip(columns, column_widths):
            self.tree_editar.heading(col, text=col)
            self.tree_editar.column(col, width=width)
        
        self.tree_editar.pack(fill='both', expand=True)
        
        # Cargar datos
        self.actualizar_treeview_editar()
        
        # Frame para editar
        edit_frame = ctk.CTkFrame(main_frame, fg_color=self.colores["gris_claro"])
        edit_frame.pack(fill="x", padx=10, pady=10)
        
        # Campos para editar
        lbl_nombre = ctk.CTkLabel(edit_frame, text="Nombre:", font=self.fuente_principal)
        lbl_nombre.grid(row=0, column=0, padx=5, pady=5, sticky="e")
        
        self.entry_edit_nombre = ctk.CTkEntry(edit_frame, width=300, font=self.fuente_principal)
        self.entry_edit_nombre.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        
        lbl_cedula = ctk.CTkLabel(edit_frame, text="Cédula:", font=self.fuente_principal)
        lbl_cedula.grid(row=1, column=0, padx=5, pady=5, sticky="e")
        
        # Frame para cédula con tipo
        cedula_frame = ctk.CTkFrame(edit_frame, fg_color="transparent")
        cedula_frame.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        
        # Combo box para tipo de cédula
        self.combo_tipo_cedula_edit = ctk.CTkComboBox(
            cedula_frame,
            values=["V", "E"],
            width=60,
            font=self.fuente_principal,
            state="readonly"
        )
        self.combo_tipo_cedula_edit.pack(side="left", padx=(0, 5))
        
        # Entry para número de cédula (más ancho para extranjeros)
        self.entry_edit_cedula = ctk.CTkEntry(
            cedula_frame,
            width=230,
            font=self.fuente_principal
        )
        self.entry_edit_cedula.pack(side="left")
        
        # Botones
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        btn_actualizar = ctk.CTkButton(
            btn_frame,
            text="ACTUALIZAR",
            command=self.actualizar_datos_estudiante,
            font=self.fuente_principal,
            fg_color=self.colores["azul_secundario"],
            width=150
        )
        btn_actualizar.pack(side="left", padx=5)
        
        btn_guardar = ctk.CTkButton(
            btn_frame,
            text="GUARDAR",
            command=self.guardar_cambios,
            font=self.fuente_principal,
            fg_color=self.colores["verde"],
            width=150
        )
        btn_guardar.pack(side="left", padx=5)
        
        btn_volver = ctk.CTkButton(
            btn_frame,
            text="VOLVER",
            command=self.mostrar_menu_principal,
            font=self.fuente_principal,
            fg_color="#6B7280",
            width=150
        )
        btn_volver.pack(side="left", padx=5)
        
        # Vincular selección
        self.tree_editar.bind('<<TreeviewSelect>>', self.seleccionar_estudiante_editar)
    
    def actualizar_treeview_editar(self):
        """Actualiza el Treeview de edición"""
        for item in self.tree_editar.get_children():
            self.tree_editar.delete(item)
        
        for _, estudiante in self.df_estudiantes.iterrows():
            valores = (
                estudiante['nombre'],
                estudiante['cedula'],
                estudiante['carrera'],
                estudiante['semestre'],
                estudiante['materia'],
                f"{estudiante['nota_final']:.2f}",
                estudiante['estado']
            )
            self.tree_editar.insert('', 'end', values=valores)
    
    def seleccionar_estudiante_editar(self, event):
        """Carga datos del estudiante seleccionado para editar"""
        seleccion = self.tree_editar.selection()
        if not seleccion:
            return
        
        item = self.tree_editar.item(seleccion[0])
        cedula_completa = item['values'][1]
        
        # Filtrar estudiante
        estudiante_df = self.df_estudiantes[self.df_estudiantes['cedula'].astype(str) == cedula_completa]
        
        if len(estudiante_df) == 0:
            return
        
        estudiante = estudiante_df.iloc[0]
        
        # Extraer tipo y número de cédula
        if '-' in cedula_completa:
            tipo, numero = cedula_completa.split('-', 1)
        else:
            tipo = "V"
            numero = cedula_completa
        
        self.combo_tipo_cedula_edit.set(tipo)
        
        self.entry_edit_nombre.delete(0, 'end')
        self.entry_edit_nombre.insert(0, estudiante['nombre'])
        
        self.entry_edit_cedula.delete(0, 'end')
        self.entry_edit_cedula.insert(0, numero)
    
    def actualizar_datos_estudiante(self):
        """Actualiza los datos del estudiante seleccionado"""
        seleccion = self.tree_editar.selection()
        if not seleccion:
            messagebox.showwarning("Advertencia", "Seleccione un estudiante")
            return
        
        item = self.tree_editar.item(seleccion[0])
        cedula_original = item['values'][1]
        
        nombre = self.entry_edit_nombre.get().strip()
        cedula_numero = self.entry_edit_cedula.get().strip()
        tipo_cedula = self.combo_tipo_cedula_edit.get()
        
        if not nombre or not cedula_numero:
            messagebox.showwarning("Advertencia", "Complete todos los campos")
            return
        
        # Validar cédula según el tipo
        if not self.validar_cedula(cedula_numero, tipo_cedula):
            if tipo_cedula == "V":
                messagebox.showwarning("Advertencia", "Cédula venezolana inválida. Debe tener 7 u 8 dígitos numéricos")
            else:
                messagebox.showwarning("Advertencia", "Cédula de extranjero inválida. Máximo 15 caracteres alfanuméricos (solo letras mayúsculas y números)")
            return
        
        # Para extranjeros, asegurar que las letras estén en mayúsculas
        if tipo_cedula == "E":
            cedula_numero = cedula_numero.upper()
        
        # Crear cédula completa
        cedula_nueva = f"{tipo_cedula}-{cedula_numero}"
        profesor_cedula_completa = self.profesor_actual['cedula']
        
        # Verificar que la cédula del estudiante no sea igual a la del profesor
        if cedula_nueva == profesor_cedula_completa:
            messagebox.showwarning("Advertencia", 
                              "La cédula del estudiante no puede ser igual a la del profesor")
            return
        
        # Verificar si la nueva cédula ya existe (excepto para este mismo estudiante)
        if cedula_nueva != cedula_original:
            existente = self.df_estudiantes[
                (self.df_estudiantes['cedula'].astype(str) == cedula_nueva) & 
                (self.df_estudiantes['profesor_cedula'].astype(str) == profesor_cedula_completa)
            ]
            if len(existente) > 0:
                messagebox.showwarning("Advertencia", "Ya existe un estudiante con esta cédula")
                return
        
        # Encontrar índice del estudiante
        indices = self.df_estudiantes.index[self.df_estudiantes['cedula'].astype(str) == cedula_original].tolist()
        
        if not indices:
            messagebox.showerror("Error", "Estudiante no encontrado")
            return
        
        idx = indices[0]
        
        # Actualizar DataFrame asegurando tipos correctos
        self.df_estudiantes.at[idx, 'nombre'] = nombre
        self.df_estudiantes.at[idx, 'cedula'] = cedula_nueva
        self.df_estudiantes.at[idx, 'tipo_cedula'] = tipo_cedula
        
        # Actualizar treeview
        self.actualizar_treeview_editar()
        
        messagebox.showinfo("Éxito", "Datos actualizados correctamente")
    
    def mostrar_eliminar_estudiante(self):
        """Muestra interfaz para eliminar estudiante"""
        if not self.cargar_datos_estudiantes():
            messagebox.showerror("Error", "No hay estudiantes registrados")
            self.mostrar_menu_principal()
            return
        
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Eliminar Estudiante")
        ventana.geometry("600x400")
        ventana.transient(self.root)
        ventana.grab_set()
        
        frame = ctk.CTkFrame(ventana, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        titulo = ctk.CTkLabel(
            frame,
            text="ELIMINAR ESTUDIANTE",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=20)
        
        # Treeview
        tree_frame = ctk.CTkFrame(frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        columns = ('Nombre', 'Cédula', 'Carrera', 'Nota Final', 'Estado')
        tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        tree.pack(fill='both', expand=True)
        
        # Cargar datos
        for _, estudiante in self.df_estudiantes.iterrows():
            valores = (
                estudiante['nombre'],
                estudiante['cedula'],
                estudiante['carrera'],
                f"{estudiante['nota_final']:.2f}",
                estudiante['estado']
            )
            tree.insert('', 'end', values=valores)
        
        def eliminar():
            seleccion = tree.selection()
            if not seleccion:
                messagebox.showwarning("Advertencia", "Seleccione un estudiante")
                return
            
            if not messagebox.askyesno("Confirmar", "¿Está seguro de eliminar este estudiante?"):
                return
            
            item = tree.item(seleccion[0])
            cedula = item['values'][1]
            
            # Eliminar del DataFrame (comparación de strings)
            self.df_estudiantes = self.df_estudiantes[self.df_estudiantes['cedula'].astype(str) != cedula]
            
            # Guardar cambios inmediatamente
            try:
                self.guardar_cambios()
                messagebox.showinfo("Éxito", "Estudiante eliminado correctamente")
                ventana.destroy()
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar los cambios: {str(e)}")
        
        # Botones
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        btn_eliminar = ctk.CTkButton(
            btn_frame,
            text="ELIMINAR",
            command=eliminar,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            width=150
        )
        btn_eliminar.pack(side="left", padx=10)
        
        btn_cancelar = ctk.CTkButton(
            btn_frame,
            text="CANCELAR",
            command=ventana.destroy,
            fg_color="#6B7280",
            width=150
        )
        btn_cancelar.pack(side="left", padx=10)
    
    def mostrar_todos_registros(self):
        """Muestra todos los registros de estudiantes en una ventana"""
        if not self.cargar_datos_estudiantes():
            messagebox.showerror("Error", "No hay estudiantes registrados")
            return
        
        ventana = ctk.CTkToplevel(self.root)
        ventana.title("Todos los Registros")
        ventana.geometry("1000x600")
        
        frame = ctk.CTkFrame(ventana, fg_color=self.colores["blanco"])
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        titulo = ctk.CTkLabel(
            frame,
            text="REGISTROS DE ESTUDIANTES",
            font=self.fuente_titulo,
            text_color=self.colores["azul_principal"]
        )
        titulo.pack(pady=10)
        
        # Treeview con scroll
        tree_frame = ctk.CTkFrame(frame)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Scrollbars
        v_scrollbar = ttk.Scrollbar(tree_frame)
        v_scrollbar.pack(side='right', fill='y')
        
        h_scrollbar = ttk.Scrollbar(tree_frame, orient='horizontal')
        h_scrollbar.pack(side='bottom', fill='x')
        
        # Treeview
        columns = ('Nombre y Apellido', 'Cédula', 'Carrera', 'Semestre', 'Materia', 
                  'M1', 'M2', 'M3', 'M4', 'Nota Final', 'Estado', 'Fecha Registro')
        
        tree = ttk.Treeview(
            tree_frame,
            columns=columns,
            show='headings',
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            height=20
        )
        
        v_scrollbar.config(command=tree.yview)
        h_scrollbar.config(command=tree.xview)
        
        # Configurar columnas
        column_widths = [150, 100, 120, 70, 120, 50, 50, 50, 50, 80, 80, 120]
        for col, width in zip(columns, column_widths):
            tree.heading(col, text=col)
            tree.column(col, width=width, anchor='center')
        
        tree.pack(fill='both', expand=True)
        
        # Insertar datos
        for _, estudiante in self.df_estudiantes.iterrows():
            valores = (
                estudiante['nombre'],
                estudiante['cedula'],
                estudiante['carrera'],
                estudiante['semestre'],
                estudiante['materia'],
                f"{estudiante['modulo1']:.2f}",
                f"{estudiante['modulo2']:.2f}",
                f"{estudiante['modulo3']:.2f}",
                f"{estudiante['modulo4']:.2f}",
                f"{estudiante['nota_final']:.2f}",
                estudiante['estado'],
                estudiante['fecha_registro']
            )
            tree.insert('', 'end', values=valores)
        
        # Estadísticas
        aprobados = len(self.df_estudiantes[self.df_estudiantes['estado'] == 'Aprobado'])
        reprobados = len(self.df_estudiantes[self.df_estudiantes['estado'] == 'Reprobado'])
        total = len(self.df_estudiantes)
        
        stats_frame = ctk.CTkFrame(frame, fg_color=self.colores["gris_claro"])
        stats_frame.pack(fill="x", padx=10, pady=10)
        
        stats_text = f"Total: {total} | Aprobados: {aprobados} | Reprobados: {reprobados}"
        lbl_stats = ctk.CTkLabel(
            stats_frame,
            text=stats_text,
            font=self.fuente_principal,
            text_color=self.colores["azul_principal"]
        )
        lbl_stats.pack(pady=10)
    
    def borrar_todos_registros(self):
        """Elimina todos los registros de estudiantes del profesor actual"""
        if not messagebox.askyesno("Confirmar", 
                                  "¿Está seguro de eliminar TODOS los registros de estudiantes?\nEsta acción no se puede deshacer."):
            return
        
        if not self.cargar_datos_estudiantes():
            return
        
        # Mantener solo los registros de otros profesores
        if self.ruta_db:
            try:
                df_total = pd.read_excel(self.ruta_db, sheet_name='estudiantes', dtype={'profesor_cedula': str})
                profesor_cedula_completa = self.profesor_actual['cedula']
                df_filtrado = df_total[df_total['profesor_cedula'].astype(str) != profesor_cedula_completa]
                
                with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                    df_filtrado.to_excel(writer, sheet_name='estudiantes', index=False)
                
                self.df_estudiantes = pd.DataFrame()
                messagebox.showinfo("Éxito", "Todos los registros han sido eliminados")
                
            except Exception as e:
                messagebox.showerror("Error", f"No se pudieron eliminar los registros: {str(e)}")
    
    def guardar_cambios(self):
        """Guarda todos los cambios en la base de datos"""
        if self.ruta_db is None:
            messagebox.showwarning("Advertencia", "No hay base de datos cargada")
            return
        
        try:
            # Cargar todos los estudiantes existentes en la base de datos
            df_total_estudiantes = pd.read_excel(self.ruta_db, sheet_name='estudiantes', dtype={
                'cedula': str,
                'profesor_cedula': str
            })
            
            # Filtrar para eliminar los registros del profesor actual
            profesor_cedula_completa = self.profesor_actual['cedula']
            df_otros_profesores = df_total_estudiantes[
                df_total_estudiantes['profesor_cedula'].astype(str) != profesor_cedula_completa
            ]
            
            # Asegurar que nuestros estudiantes tengan los tipos correctos
            if not self.df_estudiantes.empty:
                self.df_estudiantes['cedula'] = self.df_estudiantes['cedula'].astype(str)
                self.df_estudiantes['profesor_cedula'] = self.df_estudiantes['profesor_cedula'].astype(str)
            
            # Agregar los estudiantes actuales del profesor
            df_final = pd.concat([df_otros_profesores, self.df_estudiantes], ignore_index=True)
            
            # Guardar en el archivo Excel
            with pd.ExcelWriter(self.ruta_db, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                df_final.to_excel(writer, sheet_name='estudiantes', index=False)
            
            messagebox.showinfo("Éxito", "Cambios guardados correctamente")
            
        except PermissionError:
            messagebox.showerror("Error", "El archivo está abierto en otro programa. Ciérrelo e intente nuevamente.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudieron guardar los cambios: {str(e)}")
    
    def generar_reporte(self):
        """Genera un reporte PDF con los datos de los estudiantes"""
        if not self.cargar_datos_estudiantes() or self.df_estudiantes.empty:
            messagebox.showerror("Error", "No hay estudiantes para generar reporte")
            return
        
        # Pedir ubicación para guardar el reporte
        ruta = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            title="Guardar reporte como"
        )
        
        if not ruta:
            return
        
        try:
            # Crear documento PDF
            doc = SimpleDocTemplate(ruta, pagesize=letter)
            elements = []
            
            # Estilos
            styles = getSampleStyleSheet()
            estilo_titulo = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=16,
                textColor=colors.HexColor(self.colores["azul_principal"]),
                alignment=1  # Centrado
            )
            
            estilo_subtitulo = ParagraphStyle(
                'CustomSubtitle',
                parent=styles['Heading2'],
                fontSize=12,
                textColor=colors.HexColor(self.colores["azul_principal"])
            )
            
            estilo_normal = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=10
            )
            
            # Título principal
            titulo = Paragraph("INSTITUTO UNIVERSITARIO LATINOAMERICANO<br/>DE AGROECOLOGÍA PAULO FREIRE", estilo_titulo)
            elements.append(titulo)
            elements.append(Spacer(1, 20))
            
            # Información del profesor
            info_profesor = f"""
            <b>PROFESOR:</b> {self.profesor_actual['nombre']}<br/>
            <b>CÉDULA:</b> {self.profesor_actual['cedula']}<br/>
            <b>CARRERA:</b> {self.profesor_actual['carrera']}<br/>
            <b>SEMESTRE:</b> {self.profesor_actual['semestre']}<br/>
            <b>MATERIA:</b> {self.profesor_actual['materia']}<br/>
            <b>FECHA DEL REPORTE:</b> {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}
            """
            
            info_paragraph = Paragraph(info_profesor, estilo_normal)
            elements.append(info_paragraph)
            elements.append(Spacer(1, 30))
            
            # Tabla de estudiantes
            datos_tabla = [['Nombre y Apellido', 'Cédula', 'MÓDULO 1', 'MÓDULO 2', 'MÓDULO 3', 'MÓDULO 4', 'Nota Final', 'Estado']]
            
            for _, estudiante in self.df_estudiantes.iterrows():
                fila = [
                    estudiante['nombre'],
                    estudiante['cedula'],
                    f"{estudiante['modulo1']:.2f}",
                    f"{estudiante['modulo2']:.2f}",
                    f"{estudiante['modulo3']:.2f}",
                    f"{estudiante['modulo4']:.2f}",
                    f"{estudiante['nota_final']:.2f}",
                    estudiante['estado']
                ]
                datos_tabla.append(fila)
            
            # Crear tabla
            tabla = Table(datos_tabla)
            estilo_tabla = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor(self.colores["blanco"])),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
            ])
            
            # Aplicar estilos alternados a las filas
            for i in range(1, len(datos_tabla)):
                if i % 2 == 0:
                    estilo_tabla.add('BACKGROUND', (0, i), (-1, i), colors.whitesmoke)
            
            tabla.setStyle(estilo_tabla)
            elements.append(tabla)
            elements.append(Spacer(1, 30))
            
            # Estadísticas
            aprobados = len(self.df_estudiantes[self.df_estudiantes['estado'] == 'Aprobado'])
            reprobados = len(self.df_estudiantes[self.df_estudiantes['estado'] == 'Reprobado'])
            total = len(self.df_estudiantes)
            
            stats_text = f"""
            <b>RESUMEN ESTADÍSTICO:</b><br/>
            Total de Estudiantes: {total}<br/>
            Estudiantes Aprobados: {aprobados}<br/>
            Estudiantes Reprobados: {reprobados}<br/>
            Porcentaje de Aprobación: {(aprobados/total*100 if total > 0 else 0):.2f}%
            """
            
            stats_paragraph = Paragraph(stats_text, estilo_normal)
            elements.append(stats_paragraph)
            
            # Pie de página
            elements.append(Spacer(1, 50))
            footer = Paragraph(f"Reporte generado por el Sistema de Gestión de Notas IULAPF", 
                             ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=1))
            elements.append(footer)
            
            # Generar PDF
            doc.build(elements)
            messagebox.showinfo("Éxito", f"Reporte generado exitosamente:\n{ruta}")
            
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo generar el reporte: {str(e)}")
    
    def ejecutar(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()

if __name__ == "__main__":
    # Instalar dependencias si no están instaladas
    try:
        import customtkinter
        import pandas
        import openpyxl
        import reportlab
    except ImportError:
        print("Instalando dependencias...")
        import subprocess
        import sys
        
        subprocess.check_call([sys.executable, "-m", "pip", "install", 
                             "customtkinter", "pandas", "openpyxl", "reportlab"])
        
        print("Dependencias instaladas. Reinicie la aplicación.")
        sys.exit(1)
    
    app = SistemaNotasUniversidad()
    app.ejecutar()