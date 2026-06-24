"""
Álbum de Recuerdos Preescolar
Jardín de Niños "Francisco I. Madero"
Grupo: 3° de preescolar

Aplicación completa para crear álbumes digitales escolares.
"""

import os
import json
import shutil
import tempfile
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import *
from tkinter import ttk, filedialog, messagebox, colorchooser, font
from PIL import Image, ImageTk, ImageDraw, ImageFont
import reportlab
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, PageBreak, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import threading
import subprocess
import sys

# ==================== CONFIGURACIÓN ====================
APP_NAME = "Álbum de Recuerdos Preescolar"
APP_VERSION = "1.0"
DEFAULT_FONT = "Segoe UI"
COLORS = {
    "primary": "#FF6B6B",
    "secondary": "#4ECDC4",
    "accent": "#FFE66D",
    "light": "#FFF8E7",
    "dark": "#2C3E50",
    "success": "#2ECC71",
    "warning": "#F39C12",
    "danger": "#E74C3C",
    "purple": "#9B59B6",
    "pink": "#FF85A2",
    "blue": "#74B9FF",
    "orange": "#FF9F43",
    "green": "#55EFC4",
}

# ==================== MODELO DE DATOS ====================
class AlbumData:
    """Gestor de datos del álbum"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        self.project_path = None
        self.project_name = "Nuevo Álbum"
        self.cover = {
            "logo": None,  # ruta de la imagen
            "school_name": "Jardín de Niños 'Francisco I. Madero'",
            "group_name": "3° de preescolar",
            "cycle": "2025-2026",
            "teacher": "",
            "background": None,  # ruta de la imagen
            "title": "Álbum de Recuerdos",
            "subtitle": "Un año de aprendizaje y diversión"
        }
        self.students = {}  # {id: {name, photo, phrase, photos: []}}
        self.activities = {}  # {id: {name, date, description, background, photos: []}}
        self.photos = {}  # {id: {path, caption, tags: {students: [], activities: []}}}
        self.next_student_id = 1
        self.next_activity_id = 1
        self.next_photo_id = 1
        self.photo_map = {}  # path -> photo_id
    
    def to_dict(self):
        return {
            "project_name": self.project_name,
            "cover": self.cover,
            "students": self.students,
            "activities": self.activities,
            "photos": self.photos,
            "next_student_id": self.next_student_id,
            "next_activity_id": self.next_activity_id,
            "next_photo_id": self.next_photo_id,
        }
    
    def from_dict(self, data):
        self.project_name = data.get("project_name", "Nuevo Álbum")
        self.cover = data.get("cover", self.cover)
        self.students = data.get("students", {})
        self.activities = data.get("activities", {})
        self.photos = data.get("photos", {})
        self.next_student_id = data.get("next_student_id", 1)
        self.next_activity_id = data.get("next_activity_id", 1)
        self.next_photo_id = data.get("next_photo_id", 1)
        # Rebuild photo map
        self.photo_map = {}
        for pid, pdata in self.photos.items():
            self.photo_map[pdata.get("path", "")] = pid
    
    def add_student(self, name, photo_path=None, phrase=""):
        sid = str(self.next_student_id)
        self.students[sid] = {
            "name": name,
            "photo": photo_path,
            "phrase": phrase,
            "photos": []
        }
        self.next_student_id += 1
        return sid
    
    def update_student(self, sid, name=None, photo_path=None, phrase=None):
        if sid in self.students:
            if name is not None:
                self.students[sid]["name"] = name
            if photo_path is not None:
                self.students[sid]["photo"] = photo_path
            if phrase is not None:
                self.students[sid]["phrase"] = phrase
    
    def delete_student(self, sid):
        if sid in self.students:
            # Remove student from photo tags
            for pid, pdata in self.photos.items():
                if sid in pdata.get("tags", {}).get("students", []):
                    pdata["tags"]["students"].remove(sid)
            del self.students[sid]
            return True
        return False
    
    def add_activity(self, name, date="", description="", background=None):
        aid = str(self.next_activity_id)
        self.activities[aid] = {
            "name": name,
            "date": date,
            "description": description,
            "background": background,
            "photos": []
        }
        self.next_activity_id += 1
        return aid
    
    def update_activity(self, aid, name=None, date=None, description=None, background=None):
        if aid in self.activities:
            if name is not None:
                self.activities[aid]["name"] = name
            if date is not None:
                self.activities[aid]["date"] = date
            if description is not None:
                self.activities[aid]["description"] = description
            if background is not None:
                self.activities[aid]["background"] = background
    
    def delete_activity(self, aid):
        if aid in self.activities:
            for pid, pdata in self.photos.items():
                if aid in pdata.get("tags", {}).get("activities", []):
                    pdata["tags"]["activities"].remove(aid)
            del self.activities[aid]
            return True
        return False
    
    def add_photo(self, path, caption=""):
        # Check if already exists
        if path in self.photo_map:
            return self.photo_map[path]
        pid = str(self.next_photo_id)
        self.photos[pid] = {
            "path": path,
            "caption": caption,
            "tags": {
                "students": [],
                "activities": []
            }
        }
        self.photo_map[path] = pid
        self.next_photo_id += 1
        return pid
    
    def tag_photo_with_student(self, photo_id, student_id):
        if photo_id in self.photos and student_id in self.students:
            if student_id not in self.photos[photo_id]["tags"]["students"]:
                self.photos[photo_id]["tags"]["students"].append(student_id)
                # Add to student's photos
                if student_id in self.students:
                    if photo_id not in self.students[student_id]["photos"]:
                        self.students[student_id]["photos"].append(photo_id)
            return True
        return False
    
    def tag_photo_with_activity(self, photo_id, activity_id):
        if photo_id in self.photos and activity_id in self.activities:
            if activity_id not in self.photos[photo_id]["tags"]["activities"]:
                self.photos[photo_id]["tags"]["activities"].append(activity_id)
                # Add to activity's photos
                if activity_id in self.activities:
                    if photo_id not in self.activities[activity_id]["photos"]:
                        self.activities[activity_id]["photos"].append(photo_id)
            return True
        return False
    
    def untag_photo_from_student(self, photo_id, student_id):
        if photo_id in self.photos and student_id in self.students:
            if student_id in self.photos[photo_id]["tags"]["students"]:
                self.photos[photo_id]["tags"]["students"].remove(student_id)
                if student_id in self.students and photo_id in self.students[student_id]["photos"]:
                    self.students[student_id]["photos"].remove(photo_id)
            return True
        return False
    
    def untag_photo_from_activity(self, photo_id, activity_id):
        if photo_id in self.photos and activity_id in self.activities:
            if activity_id in self.photos[photo_id]["tags"]["activities"]:
                self.photos[photo_id]["tags"]["activities"].remove(activity_id)
                if activity_id in self.activities and photo_id in self.activities[activity_id]["photos"]:
                    self.activities[activity_id]["photos"].remove(photo_id)
            return True
        return False
    
    def get_student_photos(self, student_id):
        if student_id in self.students:
            return self.students[student_id].get("photos", [])
        return []
    
    def get_activity_photos(self, activity_id):
        if activity_id in self.activities:
            return self.activities[activity_id].get("photos", [])
        return []
    
    def get_photo_path(self, photo_id):
        if photo_id in self.photos:
            return self.photos[photo_id].get("path", "")
        return None
    
    def save(self, filepath):
        data = self.to_dict()
        # Convert paths to relative if possible
        if self.project_path:
            base_dir = os.path.dirname(self.project_path)
            # Convert cover paths
            for key in ["logo", "background"]:
                if data["cover"].get(key):
                    try:
                        data["cover"][key] = os.path.relpath(data["cover"][key], base_dir)
                    except:
                        pass
            # Convert student photos
            for sid, sdata in data["students"].items():
                if sdata.get("photo"):
                    try:
                        sdata["photo"] = os.path.relpath(sdata["photo"], base_dir)
                    except:
                        pass
            # Convert activity backgrounds
            for aid, adata in data["activities"].items():
                if adata.get("background"):
                    try:
                        adata["background"] = os.path.relpath(adata["background"], base_dir)
                    except:
                        pass
            # Convert photo paths
            for pid, pdata in data["photos"].items():
                if pdata.get("path"):
                    try:
                        pdata["path"] = os.path.relpath(pdata["path"], base_dir)
                    except:
                        pass
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self.project_path = filepath
        return True
    
    def load(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        base_dir = os.path.dirname(filepath)
        # Convert relative paths to absolute
        if data.get("cover"):
            for key in ["logo", "background"]:
                if data["cover"].get(key):
                    path = data["cover"][key]
                    if not os.path.isabs(path):
                        path = os.path.join(base_dir, path)
                    if os.path.exists(path):
                        data["cover"][key] = path
                    else:
                        data["cover"][key] = None
        if data.get("students"):
            for sid, sdata in data["students"].items():
                if sdata.get("photo"):
                    path = sdata["photo"]
                    if not os.path.isabs(path):
                        path = os.path.join(base_dir, path)
                    if os.path.exists(path):
                        sdata["photo"] = path
                    else:
                        sdata["photo"] = None
        if data.get("activities"):
            for aid, adata in data["activities"].items():
                if adata.get("background"):
                    path = adata["background"]
                    if not os.path.isabs(path):
                        path = os.path.join(base_dir, path)
                    if os.path.exists(path):
                        adata["background"] = path
                    else:
                        adata["background"] = None
        if data.get("photos"):
            for pid, pdata in data["photos"].items():
                if pdata.get("path"):
                    path = pdata["path"]
                    if not os.path.isabs(path):
                        path = os.path.join(base_dir, path)
                    if os.path.exists(path):
                        pdata["path"] = path
                    else:
                        pdata["path"] = None
        self.from_dict(data)
        self.project_path = filepath
        # Rebuild photo map
        self.photo_map = {}
        for pid, pdata in self.photos.items():
            if pdata.get("path"):
                self.photo_map[pdata["path"]] = pid
        return True

# ==================== UTILIDADES ====================
def resize_image(path, size=(200, 200), crop=True):
    """Redimensiona una imagen manteniendo proporción o recortando"""
    try:
        img = Image.open(path)
        if crop:
            # Recortar al centro
            img.thumbnail(size, Image.Resampling.LANCZOS)
            # Crear un canvas del tamaño exacto
            new_img = Image.new('RGB', size, (255, 255, 255))
            x = (size[0] - img.width) // 2
            y = (size[1] - img.height) // 2
            new_img.paste(img, (x, y))
            return new_img
        else:
            img.thumbnail(size, Image.Resampling.LANCZOS)
            return img
    except Exception as e:
        print(f"Error al cargar imagen: {e}")
        return None

def create_thumbnail(path, size=(100, 100)):
    """Crea una miniatura de la imagen"""
    return resize_image(path, size, crop=True)

def get_image_tk(path, size=(200, 200)):
    """Carga una imagen y la convierte a PhotoImage de Tkinter"""
    try:
        img = resize_image(path, size, crop=True)
        if img:
            return ImageTk.PhotoImage(img)
    except:
        pass
    return None

def get_image_tk_fit(path, size=(200, 200)):
    """Carga una imagen y la convierte a PhotoImage de Tkinter (sin recortar)"""
    try:
        img = resize_image(path, size, crop=False)
        if img:
            return ImageTk.PhotoImage(img)
    except:
        pass
    return None

def get_image_tk_from_pil(img, size=(200, 200)):
    """Convierte una imagen PIL a PhotoImage de Tkinter"""
    try:
        img.thumbnail(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(img)
    except:
        return None

def create_default_avatar(size=(200, 200)):
    """Crea un avatar por defecto con iniciales"""
    img = Image.new('RGB', size, (200, 200, 200))
    draw = ImageDraw.Draw(img)
    # Dibujar un círculo
    draw.ellipse([10, 10, size[0]-10, size[1]-10], fill=(100, 149, 237), outline=(70, 130, 180), width=3)
    # Dibujar una figura simple
    center = size[0] // 2
    # Cabeza
    head_radius = size[0] // 6
    draw.ellipse([center-head_radius, size[1]//4-head_radius, center+head_radius, size[1]//4+head_radius], fill=(255, 255, 255))
    # Cuerpo
    draw.ellipse([center-size[0]//4, size[1]//2, center+size[0]//4, size[1]-20], fill=(255, 255, 255))
    return img

def create_default_logo(size=(200, 200)):
    """Crea un logo por defecto"""
    img = Image.new('RGB', size, (255, 248, 231))
    draw = ImageDraw.Draw(img)
    # Marco decorativo
    draw.rectangle([10, 10, size[0]-10, size[1]-10], outline=(255, 107, 107), width=8)
    draw.rectangle([20, 20, size[0]-20, size[1]-20], outline=(78, 205, 196), width=4)
    # Texto
    try:
        font = ImageFont.truetype("arial.ttf", 28)
    except:
        font = ImageFont.load_default()
    draw.text((size[0]//2, size[1]//2-20), "🏫", fill=(255, 107, 107), anchor="mm", font=font)
    draw.text((size[0]//2, size[1]//2+30), "Mi Jardín", fill=(44, 62, 80), anchor="mm", font=font)
    return img

# ==================== VENTANA PRINCIPAL ====================
class AlbumApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1200x750")
        self.root.minsize(1000, 650)
        
        # Icono de la ventana (usando emoji)
        self.root.iconbitmap(default=None)
        
        # Estilo
        self.setup_styles()
        
        # Datos
        self.data = AlbumData()
        self.current_view = "cover"  # cover, students, activities, preview
        
        # Variables de UI
        self.photo_cache = {}  # cache para imágenes Tkinter
        
        # Construir UI
        self.build_ui()
        
        # Cargar configuraciones por defecto
        self.setup_default_cover()
        
        # Estado
        self.modified = False
        
        # Bind eventos
        self.root.bind("<Control-s>", lambda e: self.save_project())
        self.root.bind("<Control-o>", lambda e: self.open_project())
        self.root.bind("<Control-n>", lambda e: self.new_project())
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Mostrar mensaje de bienvenida
        self.show_welcome()
    
    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        # Colores personalizados
        style.configure('Title.TLabel', font=('Segoe UI', 24, 'bold'), foreground=COLORS["dark"])
        style.configure('Heading.TLabel', font=('Segoe UI', 16, 'bold'), foreground=COLORS["primary"])
        style.configure('Subheading.TLabel', font=('Segoe UI', 12), foreground=COLORS["dark"])
        style.configure('Card.TFrame', background='white', relief='raised', borderwidth=2)
        style.configure('Primary.TButton', font=('Segoe UI', 10, 'bold'), background=COLORS["primary"])
        style.configure('Success.TButton', font=('Segoe UI', 10, 'bold'), background=COLORS["success"])
        style.configure('Warning.TButton', font=('Segoe UI', 10, 'bold'), background=COLORS["warning"])
        
        # Colores para botones (usando ttk con colores personalizados)
        self.root.option_add('*TButton*background', COLORS["primary"])
        self.root.option_add('*TButton*foreground', 'white')
    
    def build_ui(self):
        # Contenedor principal
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=BOTH, expand=True)
        
        # Barra de herramientas superior
        self.build_toolbar()
        
        # Panel de contenido (scrollable)
        self.content_canvas = Canvas(self.main_frame, bg=COLORS["light"], highlightthickness=0)
        self.content_canvas.pack(side=LEFT, fill=BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(self.main_frame, orient=VERTICAL, command=self.content_canvas.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.content_canvas.configure(yscrollcommand=scrollbar.set)
        
        # Frame interior para contenido
        self.content_frame = ttk.Frame(self.content_canvas)
        self.content_canvas.create_window((0, 0), window=self.content_frame, anchor=NW)
        
        self.content_frame.bind("<Configure>", lambda e: self.content_canvas.configure(scrollregion=self.content_canvas.bbox("all")))
        
        # Barra de estado
        self.status_bar = ttk.Label(self.root, text="Listo", relief=SUNKEN, anchor=W)
        self.status_bar.pack(side=BOTTOM, fill=X)
    
    def build_toolbar(self):
        toolbar = ttk.Frame(self.main_frame, relief=RAISED, borderwidth=1)
        toolbar.pack(side=TOP, fill=X, padx=5, pady=5)
        
        # Botones principales
        buttons = [
            ("📁 Nuevo", self.new_project),
            ("📂 Abrir", self.open_project),
            ("💾 Guardar", self.save_project),
            ("👦 Alumnos", self.show_students_view),
            ("🎯 Actividades", self.show_activities_view),
            ("🖼️ Fotos", self.show_photos_view),
            ("👀 Vista Previa", self.show_preview),
            ("📄 Crear PDF", self.export_pdf),
        ]
        
        for text, cmd in buttons:
            btn = ttk.Button(toolbar, text=text, command=cmd, style='Primary.TButton')
            btn.pack(side=LEFT, padx=2, pady=2)
        
        # Separador
        ttk.Separator(toolbar, orient=VERTICAL).pack(side=LEFT, fill=Y, padx=5, pady=2)
        
        # Nombre del proyecto
        self.project_name_label = ttk.Label(toolbar, text="📒 Nuevo Álbum", font=('Segoe UI', 10, 'bold'))
        self.project_name_label.pack(side=LEFT, padx=10)
        
        # Botón de portada
        ttk.Button(toolbar, text="🏠 Portada", command=self.show_cover_view, style='Warning.TButton').pack(side=LEFT, padx=2)
    
    def clear_content(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()
    
    def set_status(self, message):
        self.status_bar.config(text=message)
        self.root.update_idletasks()
    
    def show_welcome(self):
        self.clear_content()
        frame = ttk.Frame(self.content_frame)
        frame.pack(fill=BOTH, expand=True, padx=40, pady=40)
        
        # Título grande
        title = ttk.Label(frame, text="🌸 Álbum de Recuerdos Preescolar", style='Title.TLabel')
        title.pack(pady=20)
        
        subtitle = ttk.Label(frame, text="Jardín de Niños 'Francisco I. Madero' · 3° de preescolar", 
                            font=('Segoe UI', 14), foreground=COLORS["dark"])
        subtitle.pack(pady=5)
        
        # Imagen decorativa (usando emojis grandes)
        emoji_frame = ttk.Frame(frame)
        emoji_frame.pack(pady=30)
        ttk.Label(emoji_frame, text="📚 🎨 ✏️ 📸", font=('Segoe UI', 48)).pack()
        
        # Descripción
        desc = ttk.Label(frame, text="Bienvenido al creador de álbumes digitales.\n"
                         "Crea hermosos recuerdos para tus alumnos con fotos, actividades y diseños personalizados.",
                         font=('Segoe UI', 12), foreground=COLORS["dark"], justify=CENTER)
        desc.pack(pady=20)
        
        # Botones de acción rápida
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        ttk.Button(btn_frame, text="📁 Nuevo Álbum", command=self.new_project, 
                  style='Primary.TButton', width=20).pack(side=LEFT, padx=10)
        ttk.Button(btn_frame, text="📂 Abrir Álbum", command=self.open_project, 
                  style='Success.TButton', width=20).pack(side=LEFT, padx=10)
        
        # Consejos
        tips = ttk.Label(frame, text="💡 Consejo: Comienza creando la portada con el logo y los datos del jardín.",
                        font=('Segoe UI', 10), foreground=COLORS["purple"])
        tips.pack(pady=30)
    
    def setup_default_cover(self):
        """Configura la portada con valores por defecto"""
        self.data.cover["school_name"] = "Jardín de Niños 'Francisco I. Madero'"
        self.data.cover["group_name"] = "3° de preescolar"
        self.data.cover["cycle"] = "2025-2026"
        self.data.cover["teacher"] = ""
        self.data.cover["title"] = "Álbum de Recuerdos"
        self.data.cover["subtitle"] = "Un año de aprendizaje y diversión"
    
    # ==================== VISTA DE PORTADA ====================
    def show_cover_view(self):
        self.current_view = "cover"
        self.clear_content()
        
        # Título
        header = ttk.Frame(self.content_frame)
        header.pack(fill=X, padx=20, pady=10)
        ttk.Label(header, text="🏠 Portada del Álbum", style='Heading.TLabel').pack(side=LEFT)
        
        # Contenido principal
        main = ttk.Frame(self.content_frame)
        main.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Panel izquierdo: formulario
        left = ttk.Frame(main)
        left.pack(side=LEFT, fill=BOTH, expand=True, padx=(0, 20))
        
        # Logo
        logo_frame = ttk.LabelFrame(left, text="Logo", padding=10)
        logo_frame.pack(fill=X, pady=5)
        
        logo_container = ttk.Frame(logo_frame)
        logo_container.pack()
        
        self.logo_label = ttk.Label(logo_container, text="🖼️ Sin logo", relief=SUNKEN, width=30, height=10)
        self.logo_label.pack(pady=5)
        
        logo_btn_frame = ttk.Frame(logo_frame)
        logo_btn_frame.pack(pady=5)
        ttk.Button(logo_btn_frame, text="Cargar Logo", command=self.load_logo).pack(side=LEFT, padx=5)
        ttk.Button(logo_btn_frame, text="Quitar Logo", command=self.remove_logo).pack(side=LEFT, padx=5)
        
        # Datos del jardín
        info_frame = ttk.LabelFrame(left, text="Información", padding=10)
        info_frame.pack(fill=X, pady=5)
        
        # Nombre del jardín
        ttk.Label(info_frame, text="Nombre del Jardín:").grid(row=0, column=0, sticky=W, pady=2)
        self.school_name_var = StringVar(value=self.data.cover["school_name"])
        ttk.Entry(info_frame, textvariable=self.school_name_var, width=40).grid(row=0, column=1, sticky=W, pady=2, padx=5)
        
        # Grupo
        ttk.Label(info_frame, text="Grupo:").grid(row=1, column=0, sticky=W, pady=2)
        self.group_name_var = StringVar(value=self.data.cover["group_name"])
        ttk.Entry(info_frame, textvariable=self.group_name_var, width=40).grid(row=1, column=1, sticky=W, pady=2, padx=5)
        
        # Ciclo escolar
        ttk.Label(info_frame, text="Ciclo Escolar:").grid(row=2, column=0, sticky=W, pady=2)
        self.cycle_var = StringVar(value=self.data.cover["cycle"])
        ttk.Entry(info_frame, textvariable=self.cycle_var, width=40).grid(row=2, column=1, sticky=W, pady=2, padx=5)
        
        # Maestro
        ttk.Label(info_frame, text="Maestro(a):").grid(row=3, column=0, sticky=W, pady=2)
        self.teacher_var = StringVar(value=self.data.cover["teacher"])
        ttk.Entry(info_frame, textvariable=self.teacher_var, width=40).grid(row=3, column=1, sticky=W, pady=2, padx=5)
        
        # Título y subtítulo
        ttk.Label(info_frame, text="Título:").grid(row=4, column=0, sticky=W, pady=2)
        self.title_var = StringVar(value=self.data.cover["title"])
        ttk.Entry(info_frame, textvariable=self.title_var, width=40).grid(row=4, column=1, sticky=W, pady=2, padx=5)
        
        ttk.Label(info_frame, text="Subtítulo:").grid(row=5, column=0, sticky=W, pady=2)
        self.subtitle_var = StringVar(value=self.data.cover["subtitle"])
        ttk.Entry(info_frame, textvariable=self.subtitle_var, width=40).grid(row=5, column=1, sticky=W, pady=2, padx=5)
        
        # Fondo
        bg_frame = ttk.LabelFrame(left, text="Fondo de Portada", padding=10)
        bg_frame.pack(fill=X, pady=5)
        
        bg_container = ttk.Frame(bg_frame)
        bg_container.pack()
        self.bg_label = ttk.Label(bg_container, text="🖼️ Sin fondo", relief=SUNKEN, width=30, height=6)
        self.bg_label.pack(pady=5)
        
        bg_btn_frame = ttk.Frame(bg_frame)
        bg_btn_frame.pack(pady=5)
        ttk.Button(bg_btn_frame, text="Cargar Fondo", command=self.load_background).pack(side=LEFT, padx=5)
        ttk.Button(bg_btn_frame, text="Quitar Fondo", command=self.remove_background).pack(side=LEFT, padx=5)
        
        # Botón de actualizar
        ttk.Button(left, text="✅ Actualizar Portada", command=self.update_cover, style='Success.TButton').pack(pady=10)
        
        # Panel derecho: Vista previa de portada
        right = ttk.Frame(main)
        right.pack(side=RIGHT, fill=BOTH, expand=True)
        
        preview_frame = ttk.LabelFrame(right, text="Vista Previa", padding=10)
        preview_frame.pack(fill=BOTH, expand=True)
        
        self.cover_preview = ttk.Label(preview_frame, text="🖼️ Portada", relief=SUNKEN, anchor=CENTER)
        self.cover_preview.pack(fill=BOTH, expand=True, padx=10, pady=10)
        
        # Cargar logo y fondo si existen
        self.update_cover_preview()
    
    def load_logo(self):
        path = filedialog.askopenfilename(
            title="Seleccionar logo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.data.cover["logo"] = path
            self.update_cover_preview()
            self.modified = True
            self.set_status("Logo cargado")
    
    def remove_logo(self):
        self.data.cover["logo"] = None
        self.update_cover_preview()
        self.modified = True
        self.set_status("Logo eliminado")
    
    def load_background(self):
        path = filedialog.askopenfilename(
            title="Seleccionar fondo",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.data.cover["background"] = path
            self.update_cover_preview()
            self.modified = True
            self.set_status("Fondo cargado")
    
    def remove_background(self):
        self.data.cover["background"] = None
        self.update_cover_preview()
        self.modified = True
        self.set_status("Fondo eliminado")
    
    def update_cover(self):
        self.data.cover["school_name"] = self.school_name_var.get()
        self.data.cover["group_name"] = self.group_name_var.get()
        self.data.cover["cycle"] = self.cycle_var.get()
        self.data.cover["teacher"] = self.teacher_var.get()
        self.data.cover["title"] = self.title_var.get()
        self.data.cover["subtitle"] = self.subtitle_var.get()
        self.modified = True
        self.update_cover_preview()
        self.set_status("Portada actualizada")
        messagebox.showinfo("Éxito", "Portada actualizada correctamente")
    
    def update_cover_preview(self):
        """Actualiza la vista previa de la portada"""
        try:
            # Tamaño de la vista previa
            preview_size = (500, 350)
            
            # Crear imagen de portada
            img = Image.new('RGB', preview_size, (255, 248, 231))
            draw = ImageDraw.Draw(img)
            
            # Fondo
            if self.data.cover["background"] and os.path.exists(self.data.cover["background"]):
                try:
                    bg = Image.open(self.data.cover["background"])
                    bg = bg.resize(preview_size, Image.Resampling.LANCZOS)
                    img = bg
                    draw = ImageDraw.Draw(img)
                except:
                    pass
            
            # Marco decorativo
            draw.rectangle([10, 10, preview_size[0]-10, preview_size[1]-10], outline=(255, 107, 107), width=5)
            draw.rectangle([20, 20, preview_size[0]-20, preview_size[1]-20], outline=(78, 205, 196), width=3)
            
            # Logo
            logo_img = None
            if self.data.cover["logo"] and os.path.exists(self.data.cover["logo"]):
                try:
                    logo = Image.open(self.data.cover["logo"])
                    logo_size = (80, 80)
                    logo.thumbnail(logo_size, Image.Resampling.LANCZOS)
                    logo_img = logo
                except:
                    pass
            
            if logo_img:
                x = (preview_size[0] - logo_img.width) // 2
                y = 30
                img.paste(logo_img, (x, y), logo_img if logo_img.mode == 'RGBA' else None)
                title_y = y + logo_img.height + 15
            else:
                # Emoji como logo
                try:
                    font = ImageFont.truetype("seguisym.ttf", 60) if os.path.exists("seguisym.ttf") else ImageFont.load_default()
                except:
                    font = ImageFont.load_default()
                draw.text((preview_size[0]//2, 40), "🏫", fill=(255, 107, 107), anchor="mm", font=font)
                title_y = 110
            
            # Título principal
            try:
                title_font = ImageFont.truetype("arial.ttf", 28)
            except:
                title_font = ImageFont.load_default()
            title = self.data.cover["title"] or "Álbum de Recuerdos"
            draw.text((preview_size[0]//2, title_y), title, fill=(44, 62, 80), anchor="mm", font=title_font)
            
            # Subtítulo
            try:
                sub_font = ImageFont.truetype("arial.ttf", 16)
            except:
                sub_font = ImageFont.load_default()
            subtitle = self.data.cover["subtitle"] or "Un año de aprendizaje y diversión"
            draw.text((preview_size[0]//2, title_y + 35), subtitle, fill=(100, 100, 100), anchor="mm", font=sub_font)
            
            # Información del jardín
            try:
                info_font = ImageFont.truetype("arial.ttf", 14)
            except:
                info_font = ImageFont.load_default()
            school = self.data.cover["school_name"] or "Jardín de Niños"
            draw.text((preview_size[0]//2, preview_size[1] - 90), school, fill=(44, 62, 80), anchor="mm", font=info_font)
            
            group = self.data.cover["group_name"] or ""
            cycle = self.data.cover["cycle"] or ""
            info_text = f"{group}  •  {cycle}".strip(" •")
            draw.text((preview_size[0]//2, preview_size[1] - 60), info_text, fill=(100, 100, 100), anchor="mm", font=info_font)
            
            if self.data.cover["teacher"]:
                teacher = f"Maestro(a): {self.data.cover['teacher']}"
                draw.text((preview_size[0]//2, preview_size[1] - 30), teacher, fill=(100, 100, 100), anchor="mm", font=info_font)
            
            # Convertir a PhotoImage
            photo = ImageTk.PhotoImage(img)
            self.cover_preview.config(image=photo)
            self.cover_preview.image = photo
            
        except Exception as e:
            self.cover_preview.config(text=f"Error al generar vista previa: {str(e)}")
            print(f"Error en preview: {e}")
    
    # ==================== VISTA DE ALUMNOS ====================
    def show_students_view(self):
        self.current_view = "students"
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill=X, padx=20, pady=10)
        ttk.Label(header, text="👦 Alumnos", style='Heading.TLabel').pack(side=LEFT)
        ttk.Button(header, text="➕ Agregar Alumno", command=self.add_student_dialog, style='Primary.TButton').pack(side=RIGHT)
        
        # Grid de alumnos
        self.students_grid = ttk.Frame(self.content_frame)
        self.students_grid.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self.refresh_students_grid()
    
    def refresh_students_grid(self):
        for widget in self.students_grid.winfo_children():
            widget.destroy()
        
        if not self.data.students:
            ttk.Label(self.students_grid, text="No hay alumnos registrados.\nHaz clic en 'Agregar Alumno' para comenzar.",
                     font=('Segoe UI', 12), foreground=COLORS["dark"], justify=CENTER).pack(pady=40)
            return
        
        # Mostrar en un grid
        row = 0
        col = 0
        max_cols = 4
        
        for sid, sdata in self.data.students.items():
            card = ttk.Frame(self.students_grid, style='Card.TFrame', relief=RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=10, pady=10, sticky=N)
            
            # Foto
            photo_frame = ttk.Frame(card)
            photo_frame.pack(pady=5)
            
            if sdata.get("photo") and os.path.exists(sdata["photo"]):
                img = get_image_tk(sdata["photo"], (120, 120))
                if img:
                    label = ttk.Label(photo_frame, image=img)
                    label.image = img
                    label.pack()
                else:
                    ttk.Label(photo_frame, text="📷", font=('Segoe UI', 48)).pack()
            else:
                ttk.Label(photo_frame, text="👤", font=('Segoe UI', 48)).pack()
            
            # Nombre
            ttk.Label(card, text=sdata["name"], font=('Segoe UI', 12, 'bold')).pack(pady=2)
            
            # Frase
            if sdata.get("phrase"):
                ttk.Label(card, text=f"💬 {sdata['phrase']}", font=('Segoe UI', 9), foreground=COLORS["purple"]).pack()
            
            # Botones
            btn_frame = ttk.Frame(card)
            btn_frame.pack(pady=5)
            ttk.Button(btn_frame, text="📷 Fotos", 
                      command=lambda sid=sid: self.manage_student_photos(sid)).pack(side=LEFT, padx=2)
            ttk.Button(btn_frame, text="✏️ Editar", 
                      command=lambda sid=sid: self.edit_student_dialog(sid)).pack(side=LEFT, padx=2)
            ttk.Button(btn_frame, text="🗑️", 
                      command=lambda sid=sid: self.delete_student(sid)).pack(side=LEFT, padx=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_student_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Agregar Alumno")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text="Agregar Nuevo Alumno", style='Heading.TLabel').pack(pady=10)
        
        # Nombre
        ttk.Label(frame, text="Nombre del alumno:").pack(anchor=W, pady=(10, 2))
        name_var = StringVar()
        ttk.Entry(frame, textvariable=name_var, width=40).pack(fill=X, pady=2)
        
        # Frase
        ttk.Label(frame, text="Frase de recuerdo (opcional):").pack(anchor=W, pady=(10, 2))
        phrase_var = StringVar()
        ttk.Entry(frame, textvariable=phrase_var, width=40).pack(fill=X, pady=2)
        
        # Foto
        ttk.Label(frame, text="Foto del alumno (opcional):").pack(anchor=W, pady=(10, 2))
        photo_path_var = StringVar()
        photo_frame = ttk.Frame(frame)
        photo_frame.pack(fill=X, pady=2)
        ttk.Entry(photo_frame, textvariable=photo_path_var, width=30).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(photo_frame, text="📂", command=lambda: self.browse_photo(photo_path_var)).pack(side=LEFT, padx=5)
        
        # Vista previa de la foto
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(pady=10)
        preview_label = ttk.Label(preview_frame, text="Sin foto", relief=SUNKEN, width=20, height=5)
        preview_label.pack()
        
        def update_preview(*args):
            path = photo_path_var.get()
            if path and os.path.exists(path):
                img = get_image_tk(path, (100, 100))
                if img:
                    preview_label.config(image=img, text="")
                    preview_label.image = img
                    return
            preview_label.config(image="", text="Sin foto")
            preview_label.image = None
        
        photo_path_var.trace('w', update_preview)
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        def save_student():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "Por favor ingresa el nombre del alumno.")
                return
            photo = photo_path_var.get() if photo_path_var.get() else None
            phrase = phrase_var.get().strip()
            sid = self.data.add_student(name, photo, phrase)
            self.modified = True
            self.refresh_students_grid()
            self.set_status(f"Alumno '{name}' agregado")
            dialog.destroy()
            messagebox.showinfo("Éxito", f"Alumno '{name}' agregado correctamente.")
        
        ttk.Button(btn_frame, text="Guardar", command=save_student, style='Success.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def edit_student_dialog(self, sid):
        sdata = self.data.students.get(sid)
        if not sdata:
            return
        
        dialog = Toplevel(self.root)
        dialog.title(f"Editar Alumno - {sdata['name']}")
        dialog.geometry("400x450")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text=f"Editar: {sdata['name']}", style='Heading.TLabel').pack(pady=10)
        
        # Nombre
        ttk.Label(frame, text="Nombre del alumno:").pack(anchor=W, pady=(10, 2))
        name_var = StringVar(value=sdata["name"])
        ttk.Entry(frame, textvariable=name_var, width=40).pack(fill=X, pady=2)
        
        # Frase
        ttk.Label(frame, text="Frase de recuerdo:").pack(anchor=W, pady=(10, 2))
        phrase_var = StringVar(value=sdata.get("phrase", ""))
        ttk.Entry(frame, textvariable=phrase_var, width=40).pack(fill=X, pady=2)
        
        # Foto
        ttk.Label(frame, text="Foto del alumno:").pack(anchor=W, pady=(10, 2))
        photo_path_var = StringVar(value=sdata.get("photo", ""))
        photo_frame = ttk.Frame(frame)
        photo_frame.pack(fill=X, pady=2)
        ttk.Entry(photo_frame, textvariable=photo_path_var, width=30).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(photo_frame, text="📂", command=lambda: self.browse_photo(photo_path_var)).pack(side=LEFT, padx=5)
        
        # Vista previa
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(pady=10)
        preview_label = ttk.Label(preview_frame, text="Sin foto", relief=SUNKEN, width=20, height=5)
        preview_label.pack()
        
        def update_preview(*args):
            path = photo_path_var.get()
            if path and os.path.exists(path):
                img = get_image_tk(path, (100, 100))
                if img:
                    preview_label.config(image=img, text="")
                    preview_label.image = img
                    return
            preview_label.config(image="", text="Sin foto")
            preview_label.image = None
        
        photo_path_var.trace('w', update_preview)
        update_preview()
        
        def save_changes():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "Por favor ingresa el nombre del alumno.")
                return
            photo = photo_path_var.get() if photo_path_var.get() else None
            phrase = phrase_var.get().strip()
            self.data.update_student(sid, name, photo, phrase)
            self.modified = True
            self.refresh_students_grid()
            self.set_status(f"Alumno '{name}' actualizado")
            dialog.destroy()
            messagebox.showinfo("Éxito", f"Alumno '{name}' actualizado correctamente.")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Guardar", command=save_changes, style='Success.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def delete_student(self, sid):
        sdata = self.data.students.get(sid)
        if not sdata:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar al alumno '{sdata['name']}'?\nEsta acción no se puede deshacer."):
            self.data.delete_student(sid)
            self.modified = True
            self.refresh_students_grid()
            self.set_status(f"Alumno '{sdata['name']}' eliminado")
            messagebox.showinfo("Éxito", f"Alumno '{sdata['name']}' eliminado.")
    
    def manage_student_photos(self, sid):
        """Ventana para gestionar fotos de un alumno"""
        sdata = self.data.students.get(sid)
        if not sdata:
            return
        
        dialog = Toplevel(self.root)
        dialog.title(f"Fotos de {sdata['name']}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=BOTH, expand=True)
        
        header = ttk.Frame(frame)
        header.pack(fill=X)
        ttk.Label(header, text=f"📷 Fotos de {sdata['name']}", style='Heading.TLabel').pack(side=LEFT)
        ttk.Button(header, text="➕ Agregar Foto", 
                  command=lambda: self.add_photo_to_student(sid, dialog)).pack(side=RIGHT)
        
        # Grid de fotos
        photos_frame = ttk.Frame(frame)
        photos_frame.pack(fill=BOTH, expand=True, pady=10)
        
        # Mostrar fotos
        photo_ids = self.data.get_student_photos(sid)
        if not photo_ids:
            ttk.Label(photos_frame, text="Este alumno no tiene fotos aún.\nHaz clic en 'Agregar Foto' para añadir imágenes.",
                     font=('Segoe UI', 11), foreground=COLORS["dark"]).pack(pady=40)
        else:
            # Grid de fotos
            row = 0
            col = 0
            for pid in photo_ids:
                if pid not in self.data.photos:
                    continue
                pdata = self.data.photos[pid]
                path = pdata.get("path")
                if not path or not os.path.exists(path):
                    continue
                
                photo_card = ttk.Frame(photos_frame, relief=RAISED, borderwidth=1)
                photo_card.grid(row=row, column=col, padx=5, pady=5, sticky=N)
                
                img = get_image_tk(path, (100, 100))
                if img:
                    label = ttk.Label(photo_card, image=img)
                    label.image = img
                    label.pack()
                else:
                    ttk.Label(photo_card, text="📷", font=('Segoe UI', 36)).pack()
                
                # Botón quitar
                ttk.Button(photo_card, text="✖", 
                          command=lambda pid=pid: self.remove_photo_from_student(sid, pid, dialog)).pack()
                
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        
        # Cerrar
        ttk.Button(frame, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def add_photo_to_student(self, sid, parent_dialog):
        path = filedialog.askopenfilename(
            title="Seleccionar foto para el alumno",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            # Agregar foto al sistema
            pid = self.data.add_photo(path)
            self.data.tag_photo_with_student(pid, sid)
            self.modified = True
            self.set_status(f"Foto agregada al alumno")
            # Actualizar la ventana
            parent_dialog.destroy()
            self.manage_student_photos(sid)
            messagebox.showinfo("Éxito", "Foto agregada correctamente.")
    
    def remove_photo_from_student(self, sid, pid, parent_dialog):
        if messagebox.askyesno("Confirmar", "¿Quitar esta foto del alumno?"):
            self.data.untag_photo_from_student(pid, sid)
            self.modified = True
            parent_dialog.destroy()
            self.manage_student_photos(sid)
            self.set_status("Foto quitada del alumno")
    
    def browse_photo(self, var):
        path = filedialog.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            var.set(path)
    
    # ==================== VISTA DE ACTIVIDADES ====================
    def show_activities_view(self):
        self.current_view = "activities"
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill=X, padx=20, pady=10)
        ttk.Label(header, text="🎯 Actividades", style='Heading.TLabel').pack(side=LEFT)
        ttk.Button(header, text="➕ Agregar Actividad", command=self.add_activity_dialog, style='Primary.TButton').pack(side=RIGHT)
        
        # Grid de actividades
        self.activities_grid = ttk.Frame(self.content_frame)
        self.activities_grid.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self.refresh_activities_grid()
    
    def refresh_activities_grid(self):
        for widget in self.activities_grid.winfo_children():
            widget.destroy()
        
        if not self.data.activities:
            ttk.Label(self.activities_grid, text="No hay actividades registradas.\nHaz clic en 'Agregar Actividad' para comenzar.",
                     font=('Segoe UI', 12), foreground=COLORS["dark"], justify=CENTER).pack(pady=40)
            return
        
        row = 0
        col = 0
        max_cols = 2
        
        for aid, adata in self.data.activities.items():
            card = ttk.Frame(self.activities_grid, style='Card.TFrame', relief=RAISED, borderwidth=2)
            card.grid(row=row, column=col, padx=15, pady=15, sticky=N, ipadx=10, ipady=10)
            
            # Fondo de actividad (vista previa pequeña)
            bg_frame = ttk.Frame(card, height=80, width=200)
            bg_frame.pack(pady=5)
            bg_frame.pack_propagate(False)
            
            if adata.get("background") and os.path.exists(adata["background"]):
                img = get_image_tk(adata["background"], (200, 80))
                if img:
                    label = ttk.Label(bg_frame, image=img)
                    label.image = img
                    label.pack()
                else:
                    ttk.Label(bg_frame, text="🎨 Sin fondo", font=('Segoe UI', 10)).pack()
            else:
                ttk.Label(bg_frame, text="🎨 Sin fondo", font=('Segoe UI', 10)).pack()
            
            # Nombre
            ttk.Label(card, text=adata["name"], font=('Segoe UI', 14, 'bold')).pack(pady=2)
            
            # Fecha
            if adata.get("date"):
                ttk.Label(card, text=f"📅 {adata['date']}", font=('Segoe UI', 10), foreground=COLORS["dark"]).pack()
            
            # Descripción (truncada)
            desc = adata.get("description", "")
            if len(desc) > 60:
                desc = desc[:60] + "..."
            if desc:
                ttk.Label(card, text=desc, font=('Segoe UI', 9), foreground=COLORS["dark"], wraplength=200).pack(pady=2)
            
            # Cantidad de fotos
            photo_count = len(adata.get("photos", []))
            ttk.Label(card, text=f"📷 {photo_count} fotos", font=('Segoe UI', 9), foreground=COLORS["blue"]).pack()
            
            # Botones
            btn_frame = ttk.Frame(card)
            btn_frame.pack(pady=5)
            ttk.Button(btn_frame, text="📷 Fotos", 
                      command=lambda aid=aid: self.manage_activity_photos(aid)).pack(side=LEFT, padx=2)
            ttk.Button(btn_frame, text="✏️ Editar", 
                      command=lambda aid=aid: self.edit_activity_dialog(aid)).pack(side=LEFT, padx=2)
            ttk.Button(btn_frame, text="🗑️", 
                      command=lambda aid=aid: self.delete_activity(aid)).pack(side=LEFT, padx=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_activity_dialog(self):
        dialog = Toplevel(self.root)
        dialog.title("Agregar Actividad")
        dialog.geometry("450x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text="Agregar Nueva Actividad", style='Heading.TLabel').pack(pady=10)
        
        # Nombre
        ttk.Label(frame, text="Nombre de la actividad:").pack(anchor=W, pady=(10, 2))
        name_var = StringVar()
        ttk.Entry(frame, textvariable=name_var, width=40).pack(fill=X, pady=2)
        
        # Fecha
        ttk.Label(frame, text="Fecha:").pack(anchor=W, pady=(10, 2))
        date_var = StringVar()
        ttk.Entry(frame, textvariable=date_var, width=40).pack(fill=X, pady=2)
        ttk.Label(frame, text="Ej: 15 de marzo de 2026", font=('Segoe UI', 8), foreground=COLORS["dark"]).pack(anchor=W)
        
        # Descripción
        ttk.Label(frame, text="Descripción:").pack(anchor=W, pady=(10, 2))
        desc_var = StringVar()
        ttk.Entry(frame, textvariable=desc_var, width=40).pack(fill=X, pady=2)
        
        # Fondo
        ttk.Label(frame, text="Fondo personalizado (opcional):").pack(anchor=W, pady=(10, 2))
        bg_var = StringVar()
        bg_frame = ttk.Frame(frame)
        bg_frame.pack(fill=X, pady=2)
        ttk.Entry(bg_frame, textvariable=bg_var, width=30).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(bg_frame, text="📂", command=lambda: self.browse_photo(bg_var)).pack(side=LEFT, padx=5)
        
        # Vista previa del fondo
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(pady=10)
        preview_label = ttk.Label(preview_frame, text="Sin fondo", relief=SUNKEN, width=30, height=6)
        preview_label.pack()
        
        def update_preview(*args):
            path = bg_var.get()
            if path and os.path.exists(path):
                img = get_image_tk(path, (200, 100))
                if img:
                    preview_label.config(image=img, text="")
                    preview_label.image = img
                    return
            preview_label.config(image="", text="Sin fondo")
            preview_label.image = None
        
        bg_var.trace('w', update_preview)
        
        # Botones
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        
        def save_activity():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "Por favor ingresa el nombre de la actividad.")
                return
            date = date_var.get().strip()
            desc = desc_var.get().strip()
            bg = bg_var.get() if bg_var.get() else None
            aid = self.data.add_activity(name, date, desc, bg)
            self.modified = True
            self.refresh_activities_grid()
            self.set_status(f"Actividad '{name}' agregada")
            dialog.destroy()
            messagebox.showinfo("Éxito", f"Actividad '{name}' agregada correctamente.")
        
        ttk.Button(btn_frame, text="Guardar", command=save_activity, style='Success.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def edit_activity_dialog(self, aid):
        adata = self.data.activities.get(aid)
        if not adata:
            return
        
        dialog = Toplevel(self.root)
        dialog.title(f"Editar Actividad - {adata['name']}")
        dialog.geometry("450x550")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text=f"Editar: {adata['name']}", style='Heading.TLabel').pack(pady=10)
        
        # Nombre
        ttk.Label(frame, text="Nombre de la actividad:").pack(anchor=W, pady=(10, 2))
        name_var = StringVar(value=adata["name"])
        ttk.Entry(frame, textvariable=name_var, width=40).pack(fill=X, pady=2)
        
        # Fecha
        ttk.Label(frame, text="Fecha:").pack(anchor=W, pady=(10, 2))
        date_var = StringVar(value=adata.get("date", ""))
        ttk.Entry(frame, textvariable=date_var, width=40).pack(fill=X, pady=2)
        
        # Descripción
        ttk.Label(frame, text="Descripción:").pack(anchor=W, pady=(10, 2))
        desc_var = StringVar(value=adata.get("description", ""))
        ttk.Entry(frame, textvariable=desc_var, width=40).pack(fill=X, pady=2)
        
        # Fondo
        ttk.Label(frame, text="Fondo personalizado:").pack(anchor=W, pady=(10, 2))
        bg_var = StringVar(value=adata.get("background", ""))
        bg_frame = ttk.Frame(frame)
        bg_frame.pack(fill=X, pady=2)
        ttk.Entry(bg_frame, textvariable=bg_var, width=30).pack(side=LEFT, fill=X, expand=True)
        ttk.Button(bg_frame, text="📂", command=lambda: self.browse_photo(bg_var)).pack(side=LEFT, padx=5)
        
        # Vista previa
        preview_frame = ttk.Frame(frame)
        preview_frame.pack(pady=10)
        preview_label = ttk.Label(preview_frame, text="Sin fondo", relief=SUNKEN, width=30, height=6)
        preview_label.pack()
        
        def update_preview(*args):
            path = bg_var.get()
            if path and os.path.exists(path):
                img = get_image_tk(path, (200, 100))
                if img:
                    preview_label.config(image=img, text="")
                    preview_label.image = img
                    return
            preview_label.config(image="", text="Sin fondo")
            preview_label.image = None
        
        bg_var.trace('w', update_preview)
        update_preview()
        
        def save_changes():
            name = name_var.get().strip()
            if not name:
                messagebox.showwarning("Advertencia", "Por favor ingresa el nombre de la actividad.")
                return
            date = date_var.get().strip()
            desc = desc_var.get().strip()
            bg = bg_var.get() if bg_var.get() else None
            self.data.update_activity(aid, name, date, desc, bg)
            self.modified = True
            self.refresh_activities_grid()
            self.set_status(f"Actividad '{name}' actualizada")
            dialog.destroy()
            messagebox.showinfo("Éxito", f"Actividad '{name}' actualizada correctamente.")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Guardar", command=save_changes, style='Success.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    def delete_activity(self, aid):
        adata = self.data.activities.get(aid)
        if not adata:
            return
        if messagebox.askyesno("Confirmar", f"¿Eliminar la actividad '{adata['name']}'?\nEsta acción no se puede deshacer."):
            self.data.delete_activity(aid)
            self.modified = True
            self.refresh_activities_grid()
            self.set_status(f"Actividad '{adata['name']}' eliminada")
            messagebox.showinfo("Éxito", f"Actividad '{adata['name']}' eliminada.")
    
    def manage_activity_photos(self, aid):
        adata = self.data.activities.get(aid)
        if not adata:
            return
        
        dialog = Toplevel(self.root)
        dialog.title(f"Fotos de {adata['name']}")
        dialog.geometry("600x500")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=15)
        frame.pack(fill=BOTH, expand=True)
        
        header = ttk.Frame(frame)
        header.pack(fill=X)
        ttk.Label(header, text=f"📷 Fotos de {adata['name']}", style='Heading.TLabel').pack(side=LEFT)
        ttk.Button(header, text="➕ Agregar Foto", 
                  command=lambda: self.add_photo_to_activity(aid, dialog)).pack(side=RIGHT)
        
        photos_frame = ttk.Frame(frame)
        photos_frame.pack(fill=BOTH, expand=True, pady=10)
        
        photo_ids = self.data.get_activity_photos(aid)
        if not photo_ids:
            ttk.Label(photos_frame, text="Esta actividad no tiene fotos aún.\nHaz clic en 'Agregar Foto' para añadir imágenes.",
                     font=('Segoe UI', 11), foreground=COLORS["dark"]).pack(pady=40)
        else:
            row = 0
            col = 0
            for pid in photo_ids:
                if pid not in self.data.photos:
                    continue
                pdata = self.data.photos[pid]
                path = pdata.get("path")
                if not path or not os.path.exists(path):
                    continue
                
                photo_card = ttk.Frame(photos_frame, relief=RAISED, borderwidth=1)
                photo_card.grid(row=row, column=col, padx=5, pady=5, sticky=N)
                
                img = get_image_tk(path, (100, 100))
                if img:
                    label = ttk.Label(photo_card, image=img)
                    label.image = img
                    label.pack()
                else:
                    ttk.Label(photo_card, text="📷", font=('Segoe UI', 36)).pack()
                
                ttk.Button(photo_card, text="✖", 
                          command=lambda pid=pid: self.remove_photo_from_activity(aid, pid, dialog)).pack()
                
                col += 1
                if col >= 4:
                    col = 0
                    row += 1
        
        ttk.Button(frame, text="Cerrar", command=dialog.destroy).pack(pady=10)
    
    def add_photo_to_activity(self, aid, parent_dialog):
        path = filedialog.askopenfilename(
            title="Seleccionar foto para la actividad",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            pid = self.data.add_photo(path)
            self.data.tag_photo_with_activity(pid, aid)
            self.modified = True
            self.set_status(f"Foto agregada a la actividad")
            parent_dialog.destroy()
            self.manage_activity_photos(aid)
            messagebox.showinfo("Éxito", "Foto agregada correctamente.")
    
    def remove_photo_from_activity(self, aid, pid, parent_dialog):
        if messagebox.askyesno("Confirmar", "¿Quitar esta foto de la actividad?"):
            self.data.untag_photo_from_activity(pid, aid)
            self.modified = True
            parent_dialog.destroy()
            self.manage_activity_photos(aid)
            self.set_status("Foto quitada de la actividad")
    
    # ==================== VISTA DE FOTOS ====================
    def show_photos_view(self):
        self.current_view = "photos"
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill=X, padx=20, pady=10)
        ttk.Label(header, text="🖼️ Todas las Fotos", style='Heading.TLabel').pack(side=LEFT)
        ttk.Button(header, text="➕ Agregar Foto", command=self.add_photo_global, style='Primary.TButton').pack(side=RIGHT)
        
        # Grid de fotos
        self.photos_grid = ttk.Frame(self.content_frame)
        self.photos_grid.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        self.refresh_photos_grid()
    
    def refresh_photos_grid(self):
        for widget in self.photos_grid.winfo_children():
            widget.destroy()
        
        if not self.data.photos:
            ttk.Label(self.photos_grid, text="No hay fotos en el álbum.\nAgrega fotos desde la sección de alumnos o actividades.",
                     font=('Segoe UI', 12), foreground=COLORS["dark"], justify=CENTER).pack(pady=40)
            return
        
        row = 0
        col = 0
        max_cols = 5
        
        for pid, pdata in self.data.photos.items():
            path = pdata.get("path")
            if not path or not os.path.exists(path):
                continue
            
            card = ttk.Frame(self.photos_grid, relief=RAISED, borderwidth=1)
            card.grid(row=row, column=col, padx=5, pady=5, sticky=N)
            
            img = get_image_tk(path, (120, 120))
            if img:
                label = ttk.Label(card, image=img)
                label.image = img
                label.pack()
            else:
                ttk.Label(card, text="📷", font=('Segoe UI', 36)).pack()
            
            # Tags
            tags_text = ""
            if pdata.get("tags", {}).get("students"):
                tags_text += f"👦 {len(pdata['tags']['students'])} alumnos "
            if pdata.get("tags", {}).get("activities"):
                tags_text += f"🎯 {len(pdata['tags']['activities'])} actividades"
            if tags_text:
                ttk.Label(card, text=tags_text, font=('Segoe UI', 8), foreground=COLORS["dark"]).pack()
            
            # Botón para etiquetar
            ttk.Button(card, text="🏷️ Etiquetar", 
                      command=lambda pid=pid: self.tag_photo_dialog(pid)).pack(pady=2)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def add_photo_global(self):
        path = filedialog.askopenfilename(
            title="Seleccionar foto",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.webp"), ("Todos los archivos", "*.*")]
        )
        if path:
            self.data.add_photo(path)
            self.modified = True
            self.refresh_photos_grid()
            self.set_status("Foto agregada")
            messagebox.showinfo("Éxito", "Foto agregada correctamente.\nAhora puedes etiquetarla con alumnos o actividades.")
    
    def tag_photo_dialog(self, pid):
        pdata = self.data.photos.get(pid)
        if not pdata:
            return
        
        dialog = Toplevel(self.root)
        dialog.title("Etiquetar Foto")
        dialog.geometry("450x400")
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding=20)
        frame.pack(fill=BOTH, expand=True)
        
        ttk.Label(frame, text="🏷️ Etiquetar Foto", style='Heading.TLabel').pack(pady=10)
        
        # Vista previa
        path = pdata.get("path")
        if path and os.path.exists(path):
            img = get_image_tk(path, (150, 150))
            if img:
                ttk.Label(frame, image=img).pack()
                frame.image = img
        
        # Alumnos
        ttk.Label(frame, text="Etiquetar con alumnos:", font=('Segoe UI', 10, 'bold')).pack(anchor=W, pady=(10, 5))
        student_frame = ttk.Frame(frame)
        student_frame.pack(fill=X, pady=2)
        
        current_students = pdata.get("tags", {}).get("students", [])
        for sid, sdata in self.data.students.items():
            var = BooleanVar(value=sid in current_students)
            cb = ttk.Checkbutton(student_frame, text=sdata["name"], variable=var)
            cb.pack(anchor=W)
            # Guardar referencia
            if not hasattr(frame, 'student_vars'):
                frame.student_vars = {}
            frame.student_vars[sid] = var
        
        # Actividades
        ttk.Label(frame, text="Etiquetar con actividades:", font=('Segoe UI', 10, 'bold')).pack(anchor=W, pady=(10, 5))
        activity_frame = ttk.Frame(frame)
        activity_frame.pack(fill=X, pady=2)
        
        current_activities = pdata.get("tags", {}).get("activities", [])
        for aid, adata in self.data.activities.items():
            var = BooleanVar(value=aid in current_activities)
            cb = ttk.Checkbutton(activity_frame, text=adata["name"], variable=var)
            cb.pack(anchor=W)
            if not hasattr(frame, 'activity_vars'):
                frame.activity_vars = {}
            frame.activity_vars[aid] = var
        
        def save_tags():
            # Actualizar etiquetas de alumnos
            if hasattr(frame, 'student_vars'):
                for sid, var in frame.student_vars.items():
                    if var.get():
                        self.data.tag_photo_with_student(pid, sid)
                    else:
                        self.data.untag_photo_from_student(pid, sid)
            
            if hasattr(frame, 'activity_vars'):
                for aid, var in frame.activity_vars.items():
                    if var.get():
                        self.data.tag_photo_with_activity(pid, aid)
                    else:
                        self.data.untag_photo_from_activity(pid, aid)
            
            self.modified = True
            self.refresh_photos_grid()
            self.set_status("Etiquetas actualizadas")
            dialog.destroy()
            messagebox.showinfo("Éxito", "Etiquetas actualizadas correctamente.")
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=20)
        ttk.Button(btn_frame, text="Guardar", command=save_tags, style='Success.TButton').pack(side=LEFT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=dialog.destroy).pack(side=LEFT, padx=5)
    
    # ==================== VISTA PREVIA ====================
    def show_preview(self):
        self.current_view = "preview"
        self.clear_content()
        
        header = ttk.Frame(self.content_frame)
        header.pack(fill=X, padx=20, pady=10)
        ttk.Label(header, text="👀 Vista Previa del Álbum", style='Heading.TLabel').pack(side=LEFT)
        
        ttk.Button(header, text="📄 Generar PDF", command=self.export_pdf, style='Primary.TButton').pack(side=RIGHT, padx=5)
        ttk.Button(header, text="🔄 Actualizar", command=self.show_preview, style='Warning.TButton').pack(side=RIGHT, padx=5)
        
        # Área de vista previa
        preview_frame = ttk.Frame(self.content_frame)
        preview_frame.pack(fill=BOTH, expand=True, padx=20, pady=10)
        
        # Vista previa de páginas
        notebook = ttk.Notebook(preview_frame)
        notebook.pack(fill=BOTH, expand=True)
        
        # Portada
        cover_tab = ttk.Frame(notebook)
        notebook.add(cover_tab, text="🏠 Portada")
        self.preview_cover(cover_tab)
        
        # Alumnos
        students_tab = ttk.Frame(notebook)
        notebook.add(students_tab, text="👦 Alumnos")
        self.preview_students(students_tab)
        
        # Actividades
        activities_tab = ttk.Frame(notebook)
        notebook.add(activities_tab, text="🎯 Actividades")
        self.preview_activities(activities_tab)
    
    def preview_cover(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        # Simular portada
        preview_size = (500, 350)
        img = Image.new('RGB', preview_size, (255, 248, 231))
        draw = ImageDraw.Draw(img)
        
        # Fondo
        if self.data.cover.get("background") and os.path.exists(self.data.cover["background"]):
            try:
                bg = Image.open(self.data.cover["background"])
                bg = bg.resize(preview_size, Image.Resampling.LANCZOS)
                img = bg
                draw = ImageDraw.Draw(img)
            except:
                pass
        
        # Marco
        draw.rectangle([10, 10, preview_size[0]-10, preview_size[1]-10], outline=(255, 107, 107), width=5)
        draw.rectangle([20, 20, preview_size[0]-20, preview_size[1]-20], outline=(78, 205, 196), width=3)
        
        # Logo
        if self.data.cover.get("logo") and os.path.exists(self.data.cover["logo"]):
            try:
                logo = Image.open(self.data.cover["logo"])
                logo.thumbnail((80, 80), Image.Resampling.LANCZOS)
                x = (preview_size[0] - logo.width) // 2
                y = 30
                img.paste(logo, (x, y), logo if logo.mode == 'RGBA' else None)
                title_y = y + logo.height + 15
            except:
                title_y = 100
        else:
            try:
                font = ImageFont.truetype("seguisym.ttf", 60) if os.path.exists("seguisym.ttf") else ImageFont.load_default()
            except:
                font = ImageFont.load_default()
            draw.text((preview_size[0]//2, 40), "🏫", fill=(255, 107, 107), anchor="mm", font=font)
            title_y = 110
        
        # Título
        try:
            title_font = ImageFont.truetype("arial.ttf", 28)
        except:
            title_font = ImageFont.load_default()
        title = self.data.cover.get("title", "Álbum de Recuerdos")
        draw.text((preview_size[0]//2, title_y), title, fill=(44, 62, 80), anchor="mm", font=title_font)
        
        # Subtítulo
        try:
            sub_font = ImageFont.truetype("arial.ttf", 16)
        except:
            sub_font = ImageFont.load_default()
        subtitle = self.data.cover.get("subtitle", "")
        draw.text((preview_size[0]//2, title_y + 35), subtitle, fill=(100, 100, 100), anchor="mm", font=sub_font)
        
        # Información
        try:
            info_font = ImageFont.truetype("arial.ttf", 14)
        except:
            info_font = ImageFont.load_default()
        school = self.data.cover.get("school_name", "")
        draw.text((preview_size[0]//2, preview_size[1] - 90), school, fill=(44, 62, 80), anchor="mm", font=info_font)
        
        group = self.data.cover.get("group_name", "")
        cycle = self.data.cover.get("cycle", "")
        info_text = f"{group}  •  {cycle}".strip(" •")
        draw.text((preview_size[0]//2, preview_size[1] - 60), info_text, fill=(100, 100, 100), anchor="mm", font=info_font)
        
        if self.data.cover.get("teacher"):
            teacher = f"Maestro(a): {self.data.cover['teacher']}"
            draw.text((preview_size[0]//2, preview_size[1] - 30), teacher, fill=(100, 100, 100), anchor="mm", font=info_font)
        
        photo = ImageTk.PhotoImage(img)
        label = ttk.Label(frame, image=photo)
        label.image = photo
        label.pack()
    
    def preview_students(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=RIGHT, fill=Y)
        
        canvas = Canvas(frame, yscrollcommand=scroll.set, bg=COLORS["light"], highlightthickness=0)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=canvas.yview)
        
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor=NW)
        
        if not self.data.students:
            ttk.Label(inner, text="No hay alumnos para mostrar.", font=('Segoe UI', 12)).pack(pady=20)
        else:
            for sid, sdata in self.data.students.items():
                card = ttk.Frame(inner, relief=RAISED, borderwidth=2, padding=10)
                card.pack(fill=X, pady=5)
                
                # Foto
                photo_frame = ttk.Frame(card)
                photo_frame.pack(side=LEFT, padx=10)
                if sdata.get("photo") and os.path.exists(sdata["photo"]):
                    img = get_image_tk(sdata["photo"], (60, 60))
                    if img:
                        label = ttk.Label(photo_frame, image=img)
                        label.image = img
                        label.pack()
                    else:
                        ttk.Label(photo_frame, text="👤", font=('Segoe UI', 36)).pack()
                else:
                    ttk.Label(photo_frame, text="👤", font=('Segoe UI', 36)).pack()
                
                # Info
                info_frame = ttk.Frame(card)
                info_frame.pack(side=LEFT, fill=X, expand=True, padx=10)
                ttk.Label(info_frame, text=sdata["name"], font=('Segoe UI', 14, 'bold')).pack(anchor=W)
                if sdata.get("phrase"):
                    ttk.Label(info_frame, text=f"💬 {sdata['phrase']}", font=('Segoe UI', 10), foreground=COLORS["purple"]).pack(anchor=W)
                photo_count = len(sdata.get("photos", []))
                ttk.Label(info_frame, text=f"📷 {photo_count} fotos", font=('Segoe UI', 9), foreground=COLORS["blue"]).pack(anchor=W)
        
        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    def preview_activities(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=BOTH, expand=True, padx=20, pady=20)
        
        scroll = ttk.Scrollbar(frame)
        scroll.pack(side=RIGHT, fill=Y)
        
        canvas = Canvas(frame, yscrollcommand=scroll.set, bg=COLORS["light"], highlightthickness=0)
        canvas.pack(side=LEFT, fill=BOTH, expand=True)
        scroll.config(command=canvas.yview)
        
        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor=NW)
        
        if not self.data.activities:
            ttk.Label(inner, text="No hay actividades para mostrar.", font=('Segoe UI', 12)).pack(pady=20)
        else:
            for aid, adata in self.data.activities.items():
                card = ttk.Frame(inner, relief=RAISED, borderwidth=2, padding=10)
                card.pack(fill=X, pady=5)
                
                # Fondo miniatura
                bg_frame = ttk.Frame(card, width=80, height=60)
                bg_frame.pack(side=LEFT, padx=10)
                bg_frame.pack_propagate(False)
                if adata.get("background") and os.path.exists(adata["background"]):
                    img = get_image_tk(adata["background"], (80, 60))
                    if img:
                        label = ttk.Label(bg_frame, image=img)
                        label.image = img
                        label.pack()
                    else:
                        ttk.Label(bg_frame, text="🎨", font=('Segoe UI', 24)).pack()
                else:
                    ttk.Label(bg_frame, text="🎨", font=('Segoe UI', 24)).pack()
                
                # Info
                info_frame = ttk.Frame(card)
                info_frame.pack(side=LEFT, fill=X, expand=True, padx=10)
                ttk.Label(info_frame, text=adata["name"], font=('Segoe UI', 14, 'bold')).pack(anchor=W)
                if adata.get("date"):
                    ttk.Label(info_frame, text=f"📅 {adata['date']}", font=('Segoe UI', 10), foreground=COLORS["dark"]).pack(anchor=W)
                if adata.get("description"):
                    desc = adata["description"]
                    if len(desc) > 100:
                        desc = desc[:100] + "..."
                    ttk.Label(info_frame, text=desc, font=('Segoe UI', 9), foreground=COLORS["dark"]).pack(anchor=W)
                photo_count = len(adata.get("photos", []))
                ttk.Label(info_frame, text=f"📷 {photo_count} fotos", font=('Segoe UI', 9), foreground=COLORS["blue"]).pack(anchor=W)
        
        inner.update_idletasks()
        canvas.configure(scrollregion=canvas.bbox("all"))
    
    # ==================== EXPORTAR PDF ====================
    def export_pdf(self):
        if not self.data.students and not self.data.activities:
            messagebox.showwarning("Advertencia", "El álbum está vacío.\nAgrega alumnos y actividades antes de generar el PDF.")
            return
        
        # Preguntar dónde guardar
        default_name = f"Album_{self.data.cover.get('group_name', 'Preescolar').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
        filepath = filedialog.asksaveasfilename(
            title="Guardar PDF",
            defaultextension=".pdf",
            initialfile=default_name,
            filetypes=[("PDF", "*.pdf"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        
        self.set_status("Generando PDF...")
        self.root.config(cursor="watch")
        self.root.update()
        
        try:
            # Ejecutar en un hilo separado
            threading.Thread(target=self._generate_pdf, args=(filepath,), daemon=True).start()
        except Exception as e:
            self.root.config(cursor="")
            messagebox.showerror("Error", f"Error al generar PDF: {str(e)}")
            self.set_status("Error al generar PDF")
    
    def _generate_pdf(self, filepath):
        try:
            doc = SimpleDocTemplate(filepath, pagesize=letter,
                                   rightMargin=72, leftMargin=72,
                                   topMargin=72, bottomMargin=72)
            
            styles = getSampleStyleSheet()
            # Estilos personalizados
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Title'],
                fontSize=24,
                alignment=TA_CENTER,
                spaceAfter=20,
                textColor=colors.HexColor('#2C3E50')
            )
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=18,
                alignment=TA_CENTER,
                spaceAfter=12,
                textColor=colors.HexColor('#FF6B6B')
            )
            normal_style = ParagraphStyle(
                'CustomNormal',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_LEFT,
                spaceAfter=6
            )
            center_style = ParagraphStyle(
                'CustomCenter',
                parent=styles['Normal'],
                fontSize=12,
                alignment=TA_CENTER,
                spaceAfter=6
            )
            
            story = []
            
            # ===== PORTADA =====
            # Logo
            if self.data.cover.get("logo") and os.path.exists(self.data.cover["logo"]):
                try:
                    logo = RLImage(self.data.cover["logo"], width=1.5*inch, height=1.5*inch)
                    logo.hAlign = 'CENTER'
                    story.append(logo)
                    story.append(Spacer(1, 20))
                except:
                    pass
            
            # Título
            title = self.data.cover.get("title", "Álbum de Recuerdos")
            story.append(Paragraph(title, title_style))
            
            subtitle = self.data.cover.get("subtitle", "")
            if subtitle:
                story.append(Paragraph(subtitle, center_style))
                story.append(Spacer(1, 20))
            
            # Información del jardín
            school = self.data.cover.get("school_name", "")
            if school:
                story.append(Paragraph(school, center_style))
            
            group = self.data.cover.get("group_name", "")
            cycle = self.data.cover.get("cycle", "")
            if group or cycle:
                info_text = f"{group}  •  {cycle}".strip(" •")
                story.append(Paragraph(info_text, center_style))
            
            teacher = self.data.cover.get("teacher", "")
            if teacher:
                story.append(Paragraph(f"Maestro(a): {teacher}", center_style))
            
            # Fecha de generación
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Generado: {datetime.now().strftime('%d de %B de %Y')}", center_style))
            
            story.append(PageBreak())
            
            # ===== ÍNDICE DE ALUMNOS =====
            story.append(Paragraph("👦 Nuestros Alumnos", heading_style))
            story.append(Spacer(1, 10))
            
            # Tabla de alumnos
            if self.data.students:
                student_data = []
                student_data.append(["#", "Nombre", "Frase"])
                for idx, (sid, sdata) in enumerate(self.data.students.items(), 1):
                    student_data.append([
                        str(idx),
                        sdata["name"],
                        sdata.get("phrase", "")[:40] + ("..." if len(sdata.get("phrase", "")) > 40 else "")
                    ])
                
                table = Table(student_data, colWidths=[0.5*inch, 2.5*inch, 3*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#FF6B6B')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(table)
            else:
                story.append(Paragraph("No hay alumnos registrados.", center_style))
            
            story.append(PageBreak())
            
            # ===== PÁGINAS DE ALUMNOS =====
            for sid, sdata in self.data.students.items():
                # Nombre del alumno
                story.append(Paragraph(f"⭐ {sdata['name']}", heading_style))
                story.append(Spacer(1, 5))
                
                # Frase
                if sdata.get("phrase"):
                    story.append(Paragraph(f"💬 {sdata['phrase']}", center_style))
                    story.append(Spacer(1, 10))
                
                # Foto del alumno
                if sdata.get("photo") and os.path.exists(sdata["photo"]):
                    try:
                        img = RLImage(sdata["photo"], width=2*inch, height=2*inch)
                        img.hAlign = 'CENTER'
                        story.append(img)
                        story.append(Spacer(1, 10))
                    except:
                        pass
                
                # Fotos del alumno (miniaturas)
                photo_ids = sdata.get("photos", [])
                if photo_ids:
                    story.append(Paragraph("📷 Fotos de recuerdos:", normal_style))
                    # Grid de fotos
                    row_data = []
                    row = []
                    for pid in photo_ids[:12]:  # Máximo 12 fotos por alumno
                        if pid in self.data.photos:
                            path = self.data.photos[pid].get("path")
                            if path and os.path.exists(path):
                                try:
                                    img = RLImage(path, width=1.5*inch, height=1.5*inch)
                                    row.append(img)
                                    if len(row) >= 3:
                                        row_data.append(row)
                                        row = []
                                except:
                                    pass
                    if row:
                        row_data.append(row)
                    
                    for row in row_data:
                        # Crear tabla para la fila de imágenes
                        if row:
                            img_table = Table([row], colWidths=[1.7*inch]*len(row))
                            img_table.setStyle(TableStyle([
                                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                ('TOPPADDING', (0, 0), (-1, -1), 5),
                            ]))
                            story.append(img_table)
                else:
                    story.append(Paragraph("📷 No hay fotos para este alumno.", center_style))
                
                story.append(PageBreak())
            
            # ===== ACTIVIDADES =====
            story.append(Paragraph("🎯 Nuestras Actividades", heading_style))
            story.append(Spacer(1, 10))
            
            if self.data.activities:
                # Índice de actividades
                activity_data = []
                activity_data.append(["#", "Actividad", "Fecha", "Descripción"])
                for idx, (aid, adata) in enumerate(self.data.activities.items(), 1):
                    activity_data.append([
                        str(idx),
                        adata["name"],
                        adata.get("date", ""),
                        adata.get("description", "")[:60] + ("..." if len(adata.get("description", "")) > 60 else "")
                    ])
                
                table = Table(activity_data, colWidths=[0.4*inch, 1.8*inch, 1.2*inch, 2.5*inch])
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4ECDC4')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 11),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('GRID', (0, 0), (-1, -1), 1, colors.grey),
                    ('FONTSIZE', (0, 1), (-1, -1), 9),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                story.append(table)
                story.append(Spacer(1, 20))
                
                # Páginas detalladas de actividades
                for aid, adata in self.data.activities.items():
                    story.append(Paragraph(f"🎯 {adata['name']}", heading_style))
                    story.append(Spacer(1, 5))
                    
                    if adata.get("date"):
                        story.append(Paragraph(f"📅 {adata['date']}", center_style))
                    if adata.get("description"):
                        story.append(Paragraph(adata["description"], normal_style))
                    
                    story.append(Spacer(1, 10))
                    
                    # Fondo de actividad (opcional)
                    if adata.get("background") and os.path.exists(adata["background"]):
                        try:
                            bg_img = RLImage(adata["background"], width=5*inch, height=3*inch)
                            bg_img.hAlign = 'CENTER'
                            story.append(bg_img)
                            story.append(Spacer(1, 10))
                        except:
                            pass
                    
                    # Fotos de la actividad
                    photo_ids = adata.get("photos", [])
                    if photo_ids:
                        story.append(Paragraph("📷 Fotos de la actividad:", normal_style))
                        row_data = []
                        row = []
                        for pid in photo_ids[:12]:
                            if pid in self.data.photos:
                                path = self.data.photos[pid].get("path")
                                if path and os.path.exists(path):
                                    try:
                                        img = RLImage(path, width=1.5*inch, height=1.5*inch)
                                        row.append(img)
                                        if len(row) >= 3:
                                            row_data.append(row)
                                            row = []
                                    except:
                                        pass
                        if row:
                            row_data.append(row)
                        
                        for row in row_data:
                            if row:
                                img_table = Table([row], colWidths=[1.7*inch]*len(row))
                                img_table.setStyle(TableStyle([
                                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                                    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
                                    ('TOPPADDING', (0, 0), (-1, -1), 5),
                                ]))
                                story.append(img_table)
                    else:
                        story.append(Paragraph("📷 No hay fotos para esta actividad.", center_style))
                    
                    story.append(PageBreak())
            else:
                story.append(Paragraph("No hay actividades registradas.", center_style))
            
            # ===== CONTRAPORTADA =====
            story.append(PageBreak())
            story.append(Paragraph("🌸 Fin del Álbum", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph("Jardín de Niños 'Francisco I. Madero'", center_style))
            story.append(Paragraph("3° de preescolar", center_style))
            story.append(Spacer(1, 30))
            story.append(Paragraph("📚 Recuerdos que perduran para siempre", center_style))
            
            # Construir PDF
            doc.build(story)
            
            # Completado
            self.root.after(0, lambda: self._pdf_completed(filepath))
            
        except Exception as e:
            self.root.after(0, lambda: self._pdf_error(str(e)))
    
    def _pdf_completed(self, filepath):
        self.root.config(cursor="")
        self.set_status(f"PDF generado: {filepath}")
        messagebox.showinfo("Éxito", f"¡PDF generado correctamente!\n\nArchivo guardado en:\n{filepath}\n\n¿Deseas abrirlo?")
        if messagebox.askyesno("Abrir PDF", "¿Deseas abrir el PDF ahora?"):
            try:
                os.startfile(filepath)
            except:
                webbrowser.open(filepath)
    
    def _pdf_error(self, error):
        self.root.config(cursor="")
        self.set_status("Error al generar PDF")
        messagebox.showerror("Error", f"Error al generar PDF:\n{error}")
    
    # ==================== PROYECTO: GUARDAR / ABRIR / NUEVO ====================
    def new_project(self):
        if self.modified:
            if not messagebox.askyesno("Confirmar", "Hay cambios sin guardar. ¿Deseas continuar sin guardar?"):
                return
        self.data.reset()
        self.modified = False
        self.project_name_label.config(text="📒 Nuevo Álbum")
        self.set_status("Nuevo proyecto creado")
        self.show_welcome()
        messagebox.showinfo("Éxito", "Nuevo álbum creado.\nComienza configurando la portada.")
    
    def save_project(self):
        if not self.data.students and not self.data.activities and not self.data.cover.get("logo"):
            if not messagebox.askyesno("Confirmar", "El álbum está vacío. ¿Deseas guardar de todas formas?"):
                return
        
        if self.data.project_path:
            filepath = self.data.project_path
        else:
            default_name = f"Album_{self.data.cover.get('group_name', 'Preescolar').replace(' ', '_')}.album"
            filepath = filedialog.asksaveasfilename(
                title="Guardar Proyecto",
                defaultextension=".album",
                initialfile=default_name,
                filetypes=[("Álbum", "*.album"), ("Todos los archivos", "*.*")]
            )
            if not filepath:
                return
        
        try:
            self.data.save(filepath)
            self.modified = False
            self.project_name_label.config(text=f"📒 {os.path.basename(filepath)}")
            self.set_status(f"Proyecto guardado: {filepath}")
            messagebox.showinfo("Éxito", f"Proyecto guardado correctamente en:\n{filepath}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al guardar: {str(e)}")
    
    def open_project(self):
        if self.modified:
            if not messagebox.askyesno("Confirmar", "Hay cambios sin guardar. ¿Deseas continuar sin guardar?"):
                return
        
        filepath = filedialog.askopenfilename(
            title="Abrir Proyecto",
            filetypes=[("Álbum", "*.album"), ("Todos los archivos", "*.*")]
        )
        if not filepath:
            return
        
        try:
            self.data.load(filepath)
            self.modified = False
            self.project_name_label.config(text=f"📒 {os.path.basename(filepath)}")
            self.set_status(f"Proyecto abierto: {filepath}")
            
            # Actualizar vistas
            self.show_welcome()
            messagebox.showinfo("Éxito", f"Proyecto cargado correctamente.\nAlumnos: {len(self.data.students)}\nActividades: {len(self.data.activities)}")
        except Exception as e:
            messagebox.showerror("Error", f"Error al abrir: {str(e)}")
    
    def on_close(self):
        if self.modified:
            if messagebox.askyesno("Confirmar", "Hay cambios sin guardar. ¿Deseas guardar antes de salir?"):
                self.save_project()
        self.root.destroy()

# ==================== INICIO ====================
if __name__ == "__main__":
    root = Tk()
    app = AlbumApp(root)
    root.mainloop()