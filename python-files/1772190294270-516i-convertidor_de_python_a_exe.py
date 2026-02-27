import os
import sys
import subprocess
import shutil
import tempfile
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox
import webbrowser
import traceback
import re
import importlib
import json
import pkgutil
from pathlib import Path
import site
import hashlib
import requests
import logging
import time

# Configuración de logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)


class ResourceManager:
    """Gestión avanzada de recursos para bibliotecas como Whisper"""
    KNOWN_RESOURCES = {
        'whisper': {
            'assets': [
                'mel_filters.npz',
                'multilingual.tiktoken',
                'gpt2.tiktoken'
            ],
            'paths': [
                'whisper/assets',
                'whisper'
            ],
            'urls': {
                'mel_filters.npz': 'https://github.com/openai/whisper/raw/main/whisper/assets/mel_filters.npz',
                'multilingual.tiktoken': 'https://github.com/openai/whisper/raw/main/whisper/assets/multilingual.tiktoken',
                'gpt2.tiktoken': 'https://github.com/openai/whisper/raw/main/whisper/assets/gpt2.tiktoken'
            }
        },
        'nltk': {
            'paths': ['nltk_data']
        },
        'spacy': {
            'paths': ['spacy/data']
        },
        'transformers': {
            'paths': ['transformers']
        }
    }

    @staticmethod
    def detect_required_libraries(code):
        """Detecta bibliotecas en el código que requieren recursos especiales"""
        detected = set()
        for lib in ResourceManager.KNOWN_RESOURCES.keys():
            pattern = re.compile(rf'^\s*(import {lib}|from {lib}\s+)', re.MULTILINE | re.IGNORECASE)
            if pattern.search(code):
                detected.add(lib)
        return list(detected)

    @staticmethod
    def get_library_path(lib_name):
        """Obtiene la ruta de instalación de una biblioteca"""
        try:
            module = importlib.import_module(lib_name)
            return Path(module.__file__).parent
        except ImportError:
            return None

    @staticmethod
    def find_library_resources(lib_name):
        """Localiza todos los recursos necesarios para una biblioteca"""
        if lib_name not in ResourceManager.KNOWN_RESOURCES:
            return []

        lib_path = ResourceManager.get_library_path(lib_name)
        if not lib_path:
            return []

        resources = []
        lib_config = ResourceManager.KNOWN_RESOURCES[lib_name]

        # Buscar archivos específicos
        if 'assets' in lib_config:
            for asset in lib_config['assets']:
                asset_path = lib_path / asset
                if asset_path.exists():
                    resources.append(str(asset_path))

        # Buscar en rutas específicas
        if 'paths' in lib_config:
            for rel_path in lib_config['paths']:
                path = lib_path / rel_path
                if path.exists() and path.is_dir():
                    for item in path.glob('**/*'):
                        if item.is_file():
                            resources.append(str(item))

        return resources

    @staticmethod
    def download_missing_assets(lib_name, target_dir):
        """Descarga activos faltantes para bibliotecas específicas"""
        if lib_name not in ResourceManager.KNOWN_RESOURCES:
            return False

        lib_config = ResourceManager.KNOWN_RESOURCES[lib_name]
        if 'urls' not in lib_config:
            return False

        downloaded = False
        for asset, url in lib_config['urls'].items():
            # Crear estructura de directorios necesaria para Whisper
            if lib_name == 'whisper':
                asset_dir = Path(target_dir) / 'whisper' / 'assets'
                asset_dir.mkdir(parents=True, exist_ok=True)
                target_path = asset_dir / asset
            else:
                target_path = Path(target_dir) / asset

            if not target_path.exists():
                try:
                    response = requests.get(url, timeout=10)
                    response.raise_for_status()
                    with open(target_path, 'wb') as f:
                        f.write(response.content)
                    downloaded = True
                except Exception as e:
                    logger.error(f"Error downloading {asset}: {str(e)}")
        return downloaded

    @staticmethod
    def create_resource_manifest(resources, output_dir):
        """Crea un archivo de manifiesto con todos los recursos"""
        manifest = {
            "resources": [],
            "path_overrides": {}
        }

        for resource in resources:
            resource_path = Path(resource)
            # Mantener estructura de directorios para Whisper
            if "whisper" in str(resource_path):
                dest_path = "whisper/assets/" + resource_path.name
                manifest["resources"].append({
                    "src": str(resource_path),
                    "dest": dest_path
                })
                manifest["path_overrides"]["WHISPER_ASSETS_PATH"] = "whisper/assets"
            else:
                manifest["resources"].append({
                    "src": str(resource_path),
                    "dest": str(resource_path.name)
                })

        manifest_path = output_dir / "resource_manifest.json"
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2)

        return manifest_path

    @staticmethod
    def generate_resource_loader(manifest_path):
        """Genera un cargador de recursos para incluir en el ejecutable"""
        loader_code = f"""
import os
import sys
import json
import traceback
import shutil
import tempfile

def init_resources():
    # Cargar manifiesto de recursos
    manifest_path = os.path.join(os.path.dirname(__file__), 'resource_manifest.json')
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)

        # Configurar rutas para recursos
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        # Configurar variables de entorno
        for var, path in manifest.get('path_overrides', {{}}).items():
            full_path = os.path.join(base_path, path)
            os.environ[var] = full_path
            print(f"SET {{var}}={{full_path}}")

        # Copiar recursos a ubicación esperada
        for resource in manifest.get('resources', []):
            src = os.path.join(base_path, resource['src'])
            dest = os.path.join(base_path, resource['dest'])

            # Crear directorios si no existen
            os.makedirs(os.path.dirname(dest), exist_ok=True)

            if not os.path.exists(dest):
                shutil.copy2(src, dest)
                print(f"COPIADO: {{src}} -> {{dest}}")

    except Exception as e:
        print(f"Error loading resource manifest: {{str(e)}}")
        traceback.print_exc()

# Inicializar recursos al importar
init_resources()
"""
        return loader_code


class IconConverter:
    """Clase dedicada a la conversión de imágenes a iconos"""

    @staticmethod
    def is_pillow_available():
        """Verifica si Pillow está disponible"""
        try:
            import PIL
            return True
        except ImportError:
            return False

    @staticmethod
    def install_pillow():
        """Instala Pillow automáticamente"""
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pillow"],
                                  stdout=subprocess.PIPE,
                                  stderr=subprocess.PIPE)
            return True
        except Exception as e:
            print(f"Error instalando Pillow: {e}")
            return False

    @staticmethod
    def convert_to_ico(image_path, ico_path=None):
        """
        Convierte cualquier imagen a formato ICO
        Args:
            image_path: Ruta a la imagen de entrada
            ico_path: Ruta de salida para el icono (opcional)
        Returns:
            Ruta del icono creado o None si falla
        """
        # Si Pillow no está disponible, intentar instalarlo
        if not IconConverter.is_pillow_available():
            print("Pillow no encontrado. Intentando instalar...")
            if not IconConverter.install_pillow():
                print("No se pudo instalar Pillow. Instálelo manualmente: pip install pillow")
                return None

        try:
            from PIL import Image

            # Crear ruta para el icono si no se proporciona
            if ico_path is None:
                base_name = os.path.splitext(os.path.basename(image_path))[0]
                ico_path = os.path.join(tempfile.gettempdir(), f"{base_name}.ico")

            # Abrir la imagen
            img = Image.open(image_path)

            # Convertir a RGB si tiene transparencia y no es RGBA
            if img.mode == 'P' and 'transparency' in img.info:
                img = img.convert('RGBA')
            elif img.mode not in ('RGBA', 'LA', 'RGB', 'L'):
                img = img.convert('RGBA' if img.mode == 'P' else 'RGB')

            # Asegurar que la imagen sea cuadrada para iconos
            width, height = img.size
            if width != height:
                # Hacer la imagen cuadrada
                size = max(width, height)
                square_img = Image.new('RGBA', (size, size), (255, 255, 255, 0))
                offset = ((size - width) // 2, (size - height) // 2)
                square_img.paste(img, offset)
                img = square_img
                width = height = size

            # Crear icono con múltiples tamaños (requerido para Windows)
            sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

            # Redimensionar a cada tamaño
            icon_images = []
            for size in sizes:
                resized_img = img.resize(size, Image.Resampling.LANCZOS)
                icon_images.append(resized_img)

            # Guardar como ICO
            img.save(ico_path, format='ICO', sizes=sizes, quality=100)

            print(f"✓ Imagen convertida a icono: {ico_path}")
            return ico_path

        except Exception as e:
            print(f"✗ Error convirtiendo imagen a icono: {e}")
            traceback.print_exc()
            return None

    @staticmethod
    def create_default_icon():
        """Crea un icono por defecto si no se proporciona uno"""
        try:
            from PIL import Image, ImageDraw, ImageFont

            # Crear un icono simple con un círculo y texto "PY"
            size = 256
            img = Image.new('RGBA', (size, size), (30, 136, 229, 255))  # Azul sólido
            draw = ImageDraw.Draw(img)

            # Agregar borde blanco
            draw.rectangle([10, 10, size - 10, size - 10], outline=(255, 255, 255, 255), width=5)

            # Dibujar texto "EXE"
            try:
                # Intentar usar una fuente común
                font_paths = [
                    "C:/Windows/Fonts/arial.ttf",
                    "C:/Windows/Fonts/arialbd.ttf",
                    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
                ]
                font = None
                for font_path in font_paths:
                    if os.path.exists(font_path):
                        font = ImageFont.truetype(font_path, 100)
                        break
                if font is None:
                    # Usar fuente por defecto
                    font = ImageFont.load_default()
            except:
                font = ImageFont.load_default()

            draw.text((size // 2, size // 2), "EXE", fill=(255, 255, 255, 255),
                      font=font, anchor="mm", stroke_width=3, stroke_fill=(0, 0, 0, 255))

            # Guardar como icono
            ico_path = os.path.join(tempfile.gettempdir(), "default_exe_icon.ico")
            img.save(ico_path, format='ICO', sizes=[(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])

            return ico_path
        except Exception as e:
            print(f"Error creando icono por defecto: {e}")
            return None

    @staticmethod
    def validate_and_fix_icon(icon_path):
        """Valida y repara un icono si es necesario para Windows"""
        try:
            from PIL import Image

            # Verificar si el archivo existe
            if not os.path.exists(icon_path):
                return False

            # Verificar si es un ICO válido
            img = Image.open(icon_path)
            if img.format != 'ICO':
                return False

            # Verificar que tenga múltiples tamaños
            if not hasattr(img, 'n_frames') or img.n_frames < 4:
                # Recrear con múltiples tamaños
                img = Image.open(icon_path)

                # Obtener el tamaño original
                width, height = img.size

                # Crear lista de tamaños
                sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]

                # Guardar con múltiples tamaños
                img.save(icon_path, format='ICO', sizes=sizes, quality=100)

            return True
        except Exception as e:
            print(f"Error validando icono: {e}")
            return False


class PythonToEXEConverter:
    def __init__(self, root):
        self.root = root
        self.root.title("Py2Exe Revolucionario")
        self.root.geometry("1000x750")
        self.root.resizable(True, True)
        self.root.configure(bg="#f0f0f0")

        # Variables de estado
        self.conversion_in_progress = False
        self.temp_files = []
        self.output_dir = os.path.abspath("./ejecutables")
        self.author = ""
        self.company = ""
        self.copyright_info = ""
        self.certificate_path = ""
        self.certificate_password = ""
        self.pyinstaller_available = False
        self.resource_manifest_path = ""
        self.resource_loader_path = ""
        self.icon_converter = IconConverter()

        # Variables para icono del editor (compacto)
        self.editor_icon_path = ""          # Ruta del icono seleccionado (puede ser temporal)
        self.editor_icon_preview_photo = None  # Para mantener la referencia de la imagen

        # Crear menú
        self.create_menu()

        # Estilo
        self.setup_styles()

        # Interfaz
        self.create_widgets()

        # Verificar dependencias
        self.check_dependencies()

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)

        # Menú Archivo
        file_menu = tk.Menu(menu_bar, tearoff=0)
        file_menu.add_command(label="Configurar Firma Digital", command=self.configure_signature)
        file_menu.add_command(label="Configurar Carpeta Destino", command=self.configure_output_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        menu_bar.add_cascade(label="Archivo", menu=file_menu)

        # Menú Ayuda
        help_menu = tk.Menu(menu_bar, tearoff=0)
        help_menu.add_command(label="Instrucciones", command=self.show_instructions)
        help_menu.add_command(label="Acerca de", command=self.show_about)
        menu_bar.add_cascade(label="Ayuda", menu=help_menu)

    def setup_styles(self):
        self.style = ttk.Style()

        # Configuración general
        self.style.theme_use('clam')
        self.style.configure(".", background="#f0f0f0", foreground="black", font=("Arial", 9))
        self.style.configure("TFrame", background="#f0f0f0")
        self.style.configure("TNotebook", background="#e0e0e0")

        # Pestañas
        self.style.configure("TNotebook.Tab",
                             background="#d0d0d0",
                             foreground="black",
                             padding=[10, 5],
                             font=("Arial", 9, "bold"))
        self.style.map("TNotebook.Tab",
                       background=[("selected", "#2e7d32")],
                       foreground=[("selected", "white")])

        # Botones
        self.style.configure("TButton",
                             background="#2e7d32",
                             foreground="white",
                             font=("Arial", 10, "bold"),
                             borderwidth=1,
                             padding=6)
        self.style.map("TButton",
                       background=[("active", "#1b5e20"), ("disabled", "#a5d6a7")],
                       foreground=[("active", "white"), ("disabled", "#e0e0e0")])

        # Etiquetas
        self.style.configure("TLabel",
                             background="#f0f0f0",
                             foreground="#212121",
                             font=("Arial", 9))
        self.style.configure("Bold.TLabel",
                             font=("Arial", 9, "bold"),
                             foreground="#000000")
        self.style.configure("Title.TLabel",
                             font=("Arial", 16, "bold"),
                             foreground="#0d47a1")

        # Campos de entrada
        self.style.configure("TEntry",
                             fieldbackground="white",
                             foreground="black",
                             bordercolor="#bdbdbd",
                             lightcolor="#e0e0e0",
                             darkcolor="#e0e0e0")

        # Consola
        self.style.configure("Console.TFrame", background="#1e272c")
        self.style.configure("Console.TLabel",
                             background="#1e272c",
                             foreground="#00ff00")

        # Checkbox
        self.style.configure("TCheckbutton",
                             background="#f0f0f0",
                             foreground="#212121",
                             indicatorbackground="#f0f0f0")
        self.style.map("TCheckbutton",
                       foreground=[("active", "#000000")],
                       indicatorbackground=[("selected", "#2e7d32")])

        # Labelframe
        self.style.configure("TLabelframe",
                             background="#f0f0f0",
                             foreground="#0d47a1")
        self.style.configure("TLabelframe.Label",
                             background="#f0f0f0",
                             foreground="#0d47a1",
                             font=("Arial", 9, "bold"))

        # Barra de progreso
        self.style.configure("TProgressbar",
                             background="#2e7d32",
                             troughcolor="#e0e0e0",
                             thickness=15)

    def create_widgets(self):
        # Usamos grid en la ventana principal para control total
        self.root.grid_rowconfigure(0, weight=1)  # Fila superior (todo el contenido) se expande
        self.root.grid_rowconfigure(1, weight=0)  # Fila del botón NO se expande
        self.root.grid_rowconfigure(2, weight=0)  # Fila de la barra de estado NO se expande
        self.root.grid_columnconfigure(0, weight=1)

        # --- Frame superior que contiene título, pestañas y consola ---
        top_frame = ttk.Frame(self.root)
        top_frame.grid(row=0, column=0, sticky="nsew", padx=20, pady=(20, 0))
        top_frame.grid_rowconfigure(0, weight=0)  # Título
        top_frame.grid_rowconfigure(1, weight=0)  # Separador
        top_frame.grid_rowconfigure(2, weight=1)  # Notebook (se expande)
        top_frame.grid_rowconfigure(3, weight=0)  # Progress frame (oculto)
        top_frame.grid_rowconfigure(4, weight=0)  # Consola (altura fija)
        top_frame.grid_columnconfigure(0, weight=1)

        # Título
        title_frame = ttk.Frame(top_frame)
        title_frame.grid(row=0, column=0, sticky="ew", pady=(0, 15))
        title_label = ttk.Label(title_frame, text="CONVERSOR PYTHON A EXE", style="Title.TLabel")
        title_label.pack(pady=5)
        subtitle_label = ttk.Label(title_frame, text="Convierte tus scripts Python en ejecutables portables con iconos personalizados", style="Bold.TLabel")
        subtitle_label.pack()

        # Separador
        ttk.Separator(top_frame, orient=tk.HORIZONTAL).grid(row=1, column=0, sticky="ew", pady=10)

        # Notebook (pestañas)
        self.notebook = ttk.Notebook(top_frame)
        self.notebook.grid(row=2, column=0, sticky="nsew")

        # Pestaña 1: Convertir archivo
        file_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(file_frame, text="Convertir Archivo")
        self.create_file_tab(file_frame)

        # Pestaña 2: Editor de código
        editor_frame = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(editor_frame, text="Editor de Código")
        self.create_editor_tab(editor_frame)

        # Barra de progreso (inicialmente oculta)
        self.progress_frame = ttk.Frame(top_frame)
        self.progress_frame.grid(row=3, column=0, sticky="ew", pady=(10, 0))
        self.progress_frame.grid_remove()  # Oculto
        self.progress_label = ttk.Label(self.progress_frame, text="Procesando conversión...", font=("Arial", 9, "bold"))
        self.progress_label.pack(anchor="w", padx=5, pady=2)
        self.progress_bar = ttk.Progressbar(self.progress_frame, orient="horizontal", length=100, mode="indeterminate")
        self.progress_bar.pack(fill=tk.X, padx=5, pady=5)

        # Consola de salida
        console_frame = ttk.Frame(top_frame, style="Console.TFrame", padding=10)
        console_frame.grid(row=4, column=0, sticky="ew", pady=(0, 5))
        console_frame.grid_columnconfigure(0, weight=1)
        console_frame.grid_rowconfigure(1, weight=1)
        console_label = ttk.Label(console_frame, text="SALIDA DEL PROCESO:", style="Console.TLabel")
        console_label.grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.console = scrolledtext.ScrolledText(console_frame, bg="#1e272c", fg="#00ff00", height=10, font=("Consolas", 9), insertbackground="white")
        self.console.grid(row=1, column=0, sticky="nsew", padx=5, pady=(0, 5))
        self.console.configure(state=tk.DISABLED)

        # --- BOTÓN "CONVERTIR A EXE" (con marco rojo temporal para depuración) ---
        bottom_frame = tk.Frame(self.root, bg="red", bd=3, relief=tk.RAISED)
        bottom_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=10)
        bottom_frame.grid_columnconfigure(0, weight=1)

        self.convert_btn = ttk.Button(
            bottom_frame,
            text="CONVERTIR A EXE",
            command=self.start_conversion,
            style="TButton"
        )
        self.convert_btn.pack(ipadx=20, ipady=10)

        # Barra de estado (inferior)
        status_frame = ttk.Frame(self.root)
        status_frame.grid(row=2, column=0, sticky="ew")
        self.status_var = tk.StringVar()
        self.status_var.set("Preparado")
        status_bar = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W, background="#e0e0e0", foreground="#000000", font=("Arial", 9))
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, ipady=3)

        print("DEBUG: Botón 'CONVERTIR A EXE' creado y colocado en la fila 1.")

    def create_file_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Selección de archivo
        file_label = ttk.Label(frame,
                               text="Seleccionar archivo Python:",
                               style="Bold.TLabel")
        file_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        file_frame = ttk.Frame(frame)
        file_frame.grid(row=1, column=0, columnspan=3, sticky="we", pady=(0, 15))

        self.file_entry = ttk.Entry(file_frame, width=50)
        self.file_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        browse_btn = ttk.Button(file_frame, text="Examinar", command=self.browse_file)
        browse_btn.pack(side=tk.RIGHT)

        # Opciones
        options_frame = ttk.Frame(frame)
        options_frame.grid(row=2, column=0, columnspan=3, sticky="we", pady=10)

        # Nombre del ejecutable
        ttk.Label(options_frame, text="Nombre del ejecutable:").grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.exe_name = ttk.Entry(options_frame, width=25)
        self.exe_name.grid(row=0, column=1, sticky="w")
        self.exe_name.insert(0, "MiPrograma")

        # Modo de archivo
        self.onefile_var = tk.BooleanVar(value=True)
        onefile_cb = ttk.Checkbutton(
            options_frame,
            text="Un solo archivo (onefile)",
            variable=self.onefile_var,
            style="TCheckbutton"
        )
        onefile_cb.grid(row=1, column=0, sticky="w", pady=5)

        # Consola
        self.console_var = tk.BooleanVar(value=False)
        console_cb = ttk.Checkbutton(
            options_frame,
            text="Ocultar consola (para GUI)",
            variable=self.console_var,
            style="TCheckbutton"
        )
        console_cb.grid(row=1, column=1, sticky="w", pady=5, padx=(20, 0))

        # Ícono
        icon_frame = ttk.LabelFrame(frame, text="Ícono Personalizado", padding=10)
        icon_frame.grid(row=3, column=0, columnspan=3, sticky="we", pady=10)

        # Vista previa del icono (lado izquierdo)
        preview_frame = tk.Frame(icon_frame, width=64, height=64, relief=tk.SUNKEN, borderwidth=2, bg='white')
        preview_frame.pack(side=tk.LEFT, padx=(0, 20))
        preview_frame.pack_propagate(False)

        self.icon_preview_label = tk.Label(preview_frame, bg='white')
        self.icon_preview_label.pack(fill=tk.BOTH, expand=True)

        # Controles del icono (lado derecho)
        controls_frame = ttk.Frame(icon_frame)
        controls_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Campo de entrada para icono
        input_frame = ttk.Frame(controls_frame)
        input_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(input_frame, text="Seleccionar imagen:").pack(side=tk.LEFT, padx=(0, 10))

        self.icon_entry = ttk.Entry(input_frame, width=40)
        self.icon_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        icon_browse_btn = ttk.Button(input_frame, text="Buscar Imagen", command=self.browse_icon)
        icon_browse_btn.pack(side=tk.RIGHT)

        # Botones para iconos
        buttons_frame = ttk.Frame(controls_frame)
        buttons_frame.pack(fill=tk.X)

        default_icon_btn = ttk.Button(buttons_frame, text="Crear Icono Predeterminado",
                                      command=self.create_default_icon_for_file)
        default_icon_btn.pack(side=tk.LEFT, padx=(0, 5))

        clear_icon_btn = ttk.Button(buttons_frame, text="Quitar Icono",
                                    command=self.clear_icon_file)
        clear_icon_btn.pack(side=tk.LEFT)

        # Mensaje informativo
        info_label = ttk.Label(controls_frame,
                               text="Tip: Selecciona cualquier imagen (PNG, JPG, etc.) y se convertirá automáticamente a icono",
                               font=("Arial", 8), foreground="#666666")
        info_label.pack(fill=tk.X, pady=(5, 0))

        # Opciones avanzadas
        adv_frame = ttk.LabelFrame(frame, text="Opciones Avanzadas", padding=10)
        adv_frame.grid(row=4, column=0, columnspan=3, sticky="we", pady=10)

        # Datos adicionales
        ttk.Label(adv_frame, text="Carpeta de datos adicionales:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.data_dir_entry = ttk.Entry(adv_frame, width=30)
        self.data_dir_entry.grid(row=0, column=1, sticky="we", padx=5, pady=2)

        data_dir_btn = ttk.Button(adv_frame, text="Examinar", command=self.browse_data_dir)
        data_dir_btn.grid(row=0, column=2, padx=5, pady=2)

        # Archivos adicionales
        ttk.Label(adv_frame, text="Archivos adicionales:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.add_files_entry = ttk.Entry(adv_frame, width=30)
        self.add_files_entry.grid(row=1, column=1, sticky="we", padx=5, pady=2)

        add_files_btn = ttk.Button(adv_frame, text="Seleccionar", command=self.browse_add_files)
        add_files_btn.grid(row=1, column=2, padx=5, pady=2)

        # Configurar grid
        frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(0, weight=1)
        options_frame.columnconfigure(1, weight=1)

    def create_editor_tab(self, parent):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Editor de código
        editor_label = ttk.Label(frame,
                                 text="Editor de Código Python:",
                                 style="Bold.TLabel")
        editor_label.pack(anchor="w", pady=(0, 5))

        self.editor = scrolledtext.ScrolledText(
            frame,
            bg="white",
            fg="black",
            insertbackground="black",
            font=("Consolas", 11),
            undo=True,
            autoseparators=True,
            maxundo=-1,
            padx=10,
            pady=10,
            wrap=tk.WORD
        )
        self.editor.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Menú contextual para pegar
        self.context_menu = tk.Menu(self.editor, tearoff=0)
        self.context_menu.add_command(label="Pegar", command=self.paste_code)
        self.editor.bind("<Button-3>", self.show_context_menu)

        # Plantilla inicial
        self.editor.insert(tk.END, """# Escribe tu código Python aquí
# Ejemplo básico

import tkinter as tk
from tkinter import messagebox

def main():
    root = tk.Tk()
    root.title("Mi Programa")
    root.geometry("300x200")
    root.configure(bg="#f0f0f0")  # Fondo claro

    label = tk.Label(root, 
                   text="¡Convertido a EXE con éxito!", 
                   font=("Arial", 14),
                   bg="#f0f0f0",  # Fondo claro
                   fg="#212121")   # Texto oscuro
    label.pack(pady=50)

    btn = tk.Button(root, text="Salir", command=root.destroy,
                  bg="#2e7d32",   # Fondo verde
                  fg="white",      # Texto blanco
                  font=("Arial", 10, "bold"))
    btn.pack(pady=10)

    root.mainloop()

if __name__ == "__main__":
    main()
""")

        # --- Barra de herramientas superior (botones + opciones + icono) ---
        toolbar = ttk.Frame(frame)
        toolbar.pack(fill=tk.X, pady=5)

        # Botones izquierda: Limpiar y Cargar Plantilla
        left_buttons = ttk.Frame(toolbar)
        left_buttons.pack(side=tk.LEFT, padx=(0, 5))

        clear_btn = ttk.Button(left_buttons, text="Limpiar Editor", command=self.clear_editor)
        clear_btn.pack(side=tk.LEFT, padx=2)

        template_btn = ttk.Button(left_buttons, text="Cargar Plantilla", command=self.load_template)
        template_btn.pack(side=tk.LEFT, padx=2)

        # Opciones centrales: Nombre + checkboxes
        center_options = ttk.Frame(toolbar)
        center_options.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)

        ttk.Label(center_options, text="Nombre:").pack(side=tk.LEFT, padx=(0, 2))
        self.editor_exe_name = ttk.Entry(center_options, width=12)
        self.editor_exe_name.pack(side=tk.LEFT, padx=(0, 5))
        self.editor_exe_name.insert(0, "EditorApp")

        self.editor_onefile = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            center_options,
            text="Un archivo",
            variable=self.editor_onefile,
            style="TCheckbutton"
        ).pack(side=tk.LEFT, padx=(5, 2))

        self.editor_noconsole = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            center_options,
            text="Sin consola",
            variable=self.editor_noconsole,
            style="TCheckbutton"
        ).pack(side=tk.LEFT, padx=(2, 5))

        # Selector de icono compacto
        icon_selector = ttk.Frame(toolbar)
        icon_selector.pack(side=tk.LEFT, padx=5)

        self.icon_preview_small = tk.Label(icon_selector, width=32, height=32, bg='white', relief=tk.SUNKEN, borderwidth=1)
        self.icon_preview_small.pack(side=tk.LEFT, padx=(0, 2))

        icon_btn = ttk.Button(icon_selector, text="Icono...", command=self.browse_editor_icon_compact, width=8)
        icon_btn.pack(side=tk.LEFT, padx=2)

        clear_icon_btn = ttk.Button(icon_selector, text="X", command=self.clear_editor_icon_compact, width=2)
        clear_icon_btn.pack(side=tk.LEFT, padx=2)

        # Botones derecha: Guardar y Cargar Código
        right_buttons = ttk.Frame(toolbar)
        right_buttons.pack(side=tk.RIGHT)

        save_btn = ttk.Button(right_buttons, text="Guardar Código", command=self.save_code)
        save_btn.pack(side=tk.LEFT, padx=2)

        load_btn = ttk.Button(right_buttons, text="Cargar Código", command=self.load_code)
        load_btn.pack(side=tk.LEFT, padx=2)

        # Variable para almacenar la ruta del icono seleccionado (se usará en la conversión)
        self.editor_icon_path = ""  # Ruta del icono (puede ser temporal)

        # Inicializar vista previa vacía (mostrar texto o nada)
        self.update_editor_icon_preview(None)

    # Métodos para el selector compacto de icono en el editor
    def browse_editor_icon_compact(self):
        """Abre diálogo para seleccionar imagen, la convierte a .ico y actualiza vista previa."""
        icon_path = filedialog.askopenfilename(
            title="Seleccionar imagen para icono",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("Iconos", "*.ico"),
                ("Todos los archivos", "*.*")
            ]
        )
        if not icon_path:
            return

        # Si no es .ico, convertir
        if not icon_path.lower().endswith('.ico'):
            self.log(f"Convirtiendo {icon_path} a icono...")
            converted = self.icon_converter.convert_to_ico(icon_path)
            if converted:
                self.editor_icon_path = converted
                self.temp_files.append(converted)
                self.update_editor_icon_preview(converted)
                self.log(f"Icono listo: {converted}")
            else:
                messagebox.showerror("Error", "No se pudo convertir la imagen a icono.")
        else:
            self.editor_icon_path = icon_path
            self.update_editor_icon_preview(icon_path)
            self.log(f"Icono seleccionado: {icon_path}")

    def clear_editor_icon_compact(self):
        """Elimina el icono seleccionado en el editor."""
        self.editor_icon_path = ""
        self.update_editor_icon_preview(None)
        self.log("Icono eliminado. Se usará el predeterminado si no se especifica otro.")

    def update_editor_icon_preview(self, icon_path):
        """Actualiza la minivista previa del icono (32x32)."""
        try:
            from PIL import Image, ImageTk
            if icon_path and os.path.exists(icon_path):
                img = Image.open(icon_path)
                img_resized = img.resize((32, 32), Image.Resampling.LANCZOS)
                photo = ImageTk.PhotoImage(img_resized)
                self.icon_preview_small.config(image=photo, text="")
                self.icon_preview_small.image = photo  # mantener referencia
            else:
                # Vista previa vacía (blanco)
                self.icon_preview_small.config(image="", text="", bg='white')
                self.icon_preview_small.image = None
        except Exception as e:
            self.log(f"Error actualizando vista previa: {e}")
            self.icon_preview_small.config(image="", text="", bg='white')
            self.icon_preview_small.image = None

    def show_context_menu(self, event):
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def paste_code(self):
        try:
            self.editor.event_generate("<<Paste>>")
        except:
            pass

    def browse_file(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py"), ("All Files", "*.*")]
        )
        if file_path:
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_path)
            exe_name = os.path.splitext(os.path.basename(file_path))[0]
            self.exe_name.delete(0, tk.END)
            self.exe_name.insert(0, exe_name)

    def browse_icon(self):
        icon_path = filedialog.askopenfilename(
            title="Seleccionar imagen para icono",
            filetypes=[
                ("Imágenes", "*.png *.jpg *.jpeg *.bmp *.gif *.tiff *.webp"),
                ("Iconos", "*.ico"),
                ("Todos los archivos", "*.*")
            ]
        )
        if icon_path:
            self.update_icon_preview(icon_path, self.icon_preview_label)

            if not icon_path.lower().endswith('.ico'):
                self.log(f"Convirtiendo {icon_path} a icono...")
                converted_icon = self.icon_converter.convert_to_ico(icon_path)
                if converted_icon:
                    self.icon_entry.delete(0, tk.END)
                    self.icon_entry.insert(0, converted_icon)
                    self.temp_files.append(converted_icon)
                    self.update_icon_preview(converted_icon, self.icon_preview_label)
                    messagebox.showinfo("Conversión exitosa",
                                        f"Imagen convertida a icono:\n{converted_icon}\n\n"
                                        f"El icono se usará para el ejecutable.")
                else:
                    messagebox.showerror("Error",
                                         "No se pudo convertir la imagen a icono.\n"
                                         "Asegúrate de que es una imagen válida.")
            else:
                self.icon_entry.delete(0, tk.END)
                self.icon_entry.insert(0, icon_path)
                self.log(f"Icono seleccionado: {icon_path}")

    def update_icon_preview(self, icon_path, preview_label):
        try:
            from PIL import Image, ImageTk
            img = Image.open(icon_path)
            img_resized = img.resize((64, 64), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img_resized)
            preview_label.config(image=photo, text="")
            preview_label.image = photo
        except Exception as e:
            self.log(f"Error mostrando vista previa: {e}")
            preview_label.config(image=None, text="Vista previa\nno disponible")

    def create_default_icon_for_file(self):
        default_icon = self.icon_converter.create_default_icon()
        if default_icon:
            self.icon_entry.delete(0, tk.END)
            self.icon_entry.insert(0, default_icon)
            self.temp_files.append(default_icon)
            self.update_icon_preview(default_icon, self.icon_preview_label)
            self.log(f"Icono predeterminado creado: {default_icon}")
            messagebox.showinfo("Icono Predeterminado",
                                "Se ha creado un icono predeterminado para tu aplicación.\n"
                                "Puedes usar este icono o seleccionar uno personalizado.")
        else:
            messagebox.showerror("Error", "No se pudo crear el icono predeterminado.")

    def clear_icon_file(self):
        self.icon_entry.delete(0, tk.END)
        self.icon_preview_label.config(image=None, text="")
        self.log("Icono eliminado. Se usará icono por defecto de Windows.")

    def browse_data_dir(self):
        data_dir = filedialog.askdirectory()
        if data_dir:
            self.data_dir_entry.delete(0, tk.END)
            self.data_dir_entry.insert(0, data_dir)

    def browse_add_files(self):
        files = filedialog.askopenfilenames()
        if files:
            self.add_files_entry.delete(0, tk.END)
            self.add_files_entry.insert(0, ";".join(files))

    def configure_output_dir(self):
        new_dir = filedialog.askdirectory()
        if new_dir:
            self.output_dir = new_dir
            self.update_status_bar()
            messagebox.showinfo("Configuración", f"Carpeta de destino actualizada:\n{self.output_dir}")

    def configure_signature(self):
        sign_window = tk.Toplevel(self.root)
        sign_window.title("Configurar Firma Digital")
        sign_window.geometry("500x350")
        sign_window.resizable(False, False)
        sign_window.transient(self.root)
        sign_window.grab_set()

        main_frame = ttk.Frame(sign_window, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(main_frame, text="Firma Digital de la Aplicación", style="Title.TLabel").pack(pady=(0, 15))

        fields_frame = ttk.Frame(main_frame)
        fields_frame.pack(fill=tk.X, pady=5)

        ttk.Label(fields_frame, text="Nombre del Autor:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        author_entry = ttk.Entry(fields_frame, width=40)
        author_entry.grid(row=0, column=1, sticky="we", pady=5)
        author_entry.insert(0, self.author)

        ttk.Label(fields_frame, text="Empresa:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)
        company_entry = ttk.Entry(fields_frame, width=40)
        company_entry.grid(row=1, column=1, sticky="we", pady=5)
        company_entry.insert(0, self.company)

        ttk.Label(fields_frame, text="Copyright:").grid(row=2, column=0, sticky="w", padx=(0, 5), pady=5)
        copyright_entry = ttk.Entry(fields_frame, width=40)
        copyright_entry.grid(row=2, column=1, sticky="we", pady=5)
        copyright_entry.insert(0, self.copyright_info)

        cert_frame = ttk.LabelFrame(main_frame, text="Certificado Digital (Opcional)")
        cert_frame.pack(fill=tk.X, pady=10)

        ttk.Label(cert_frame, text="Certificado PFX:").grid(row=0, column=0, sticky="w", padx=5, pady=2)
        self.cert_entry = ttk.Entry(cert_frame, width=35)
        self.cert_entry.grid(row=0, column=1, sticky="we", padx=5, pady=2)
        self.cert_entry.insert(0, self.certificate_path or "")

        cert_browse_btn = ttk.Button(cert_frame, text="Examinar", command=self.browse_certificate)
        cert_browse_btn.grid(row=0, column=2, padx=5, pady=2)

        ttk.Label(cert_frame, text="Contraseña:").grid(row=1, column=0, sticky="w", padx=5, pady=2)
        self.cert_pass_entry = ttk.Entry(cert_frame, width=35, show="*")
        self.cert_pass_entry.grid(row=1, column=1, sticky="we", padx=5, pady=2)
        self.cert_pass_entry.insert(0, self.certificate_password or "")

        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=15)

        def save_signature():
            self.author = author_entry.get()
            self.company = company_entry.get()
            self.copyright_info = copyright_entry.get()
            self.certificate_path = self.cert_entry.get()
            self.certificate_password = self.cert_pass_entry.get()
            self.update_status_bar()
            sign_window.destroy()
            messagebox.showinfo("Configuración", "Firma digital actualizada")

        ttk.Button(btn_frame, text="Guardar", command=save_signature, style="TButton").pack(side=tk.RIGHT, padx=5)
        ttk.Button(btn_frame, text="Cancelar", command=sign_window.destroy).pack(side=tk.RIGHT, padx=5)

    def browse_certificate(self):
        cert_path = filedialog.askopenfilename(
            filetypes=[("Certificate Files", "*.pfx *.p12"), ("All Files", "*.*")]
        )
        if cert_path:
            self.cert_entry.delete(0, tk.END)
            self.cert_entry.insert(0, cert_path)

    def update_status_bar(self):
        status_info = f"Destino: {self.output_dir} | Autor: {self.author or 'No configurado'}"
        if self.certificate_path:
            status_info += " | Certificado: Configurado"
        self.status_var.set(status_info)

    def clear_editor(self):
        self.editor.delete(1.0, tk.END)

    def load_template(self):
        self.clear_editor()
        self.editor.insert(tk.END, """# Plantilla avanzada con GUI
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import sys
import webbrowser

class Application(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Aplicación Convertida")
        self.geometry("500x350")
        self.resizable(True, True)
        self.configure(bg="#f0f0f0")  # Fondo claro

        self.create_widgets()

    def create_widgets(self):
        # Marco principal
        main_frame = ttk.Frame(self, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Título
        title_label = ttk.Label(
            main_frame, 
            text="¡FUNCIONA PERFECTAMENTE!", 
            font=("Arial", 16, "bold"), 
            foreground="#0d47a1",  # Azul oscuro
            background="#f0f0f0"   # Fondo claro
        )
        title_label.pack(pady=20)

        # Icono
        try:
            self.iconbitmap(self.resource_path("icon.ico"))
        except:
            pass

        # Texto informativo
        info_frame = ttk.Frame(main_frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)

        info_text = tk.Text(
            info_frame, 
            height=8, 
            bg="white",            # Fondo blanco
            fg="black",            # Texto negro
            font=("Arial", 10),
            wrap=tk.WORD,
            padx=10,
            pady=10
        )
        info_text.pack(fill=tk.BOTH, expand=True)
        info_text.insert(tk.END, "Este programa fue convertido de Python a EXE usando el conversor revolucionario.\n\n")
        info_text.insert(tk.END, "Características:\n• Portabilidad completa\n• Interfaz profesional\n• Soporte para recursos externos\n• Rendimiento optimizado")
        info_text.configure(state=tk.DISABLED)

        # Botones
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X, pady=10)

        ttk.Button(btn_frame, text="Abrir Sitio Web", command=self.open_website).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Acerca de", command=self.show_about).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Salir", command=self.destroy).pack(side=tk.RIGHT, padx=5)

    def open_website(self):
        webbrowser.open("https://www.python.org")

    def show_about(self):
        messagebox.showinfo(
            "Acerca de", 
            "Aplicación convertida a EXE\nVersión 1.0\n\n© 2023 Todos los derechos reservados"
        )

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    app = Application()
    app.mainloop()
""")

    def save_code(self):
        file_path = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python Files", "*.py")]
        )
        if file_path:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(self.editor.get(1.0, tk.END))
            messagebox.showinfo("Guardado", "Código guardado exitosamente!")

    def load_code(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Python Files", "*.py")]
        )
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                self.editor.delete(1.0, tk.END)
                self.editor.insert(tk.END, f.read())

    def check_dependencies(self):
        try:
            import PyInstaller
            self.pyinstaller_available = True
            self.log("✓ PyInstaller disponible")
        except ImportError:
            self.log("PyInstaller no encontrado. Instalando...")
            self.install_pyinstaller()

    def install_pyinstaller(self):
        def run_installation():
            try:
                subprocess.check_call(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.log("PyInstaller instalado exitosamente!")
                self.pyinstaller_available = True
            except Exception as e:
                self.log(f"Error instalando PyInstaller: {str(e)}")
                self.log("Por favor instale PyInstaller manualmente con: pip install pyinstaller")
                self.pyinstaller_available = False

        threading.Thread(target=run_installation, daemon=True).start()

    def log(self, message):
        self.console.configure(state=tk.NORMAL)
        self.console.insert(tk.END, message + "\n")
        self.console.see(tk.END)
        self.console.configure(state=tk.DISABLED)
        self.status_var.set(message)

    def start_conversion(self):
        if self.conversion_in_progress:
            return

        if not self.pyinstaller_available:
            messagebox.showerror("Error", "PyInstaller no está disponible. Por favor instálelo manualmente.")
            return

        tab = self.notebook.index(self.notebook.select())

        if tab == 0:  # Pestaña de archivo
            script_path = self.file_entry.get()
            if not os.path.isfile(script_path):
                messagebox.showerror("Error", "Seleccione un archivo Python válido")
                return

            if self.is_converter_script(script_path):
                messagebox.showerror("Error", "No puedes convertir este conversor a EXE desde sí mismo")
                return

            exe_name = self.exe_name.get() or "output"
            onefile = self.onefile_var.get()
            noconsole = self.console_var.get()
            icon_path = self.icon_entry.get()
            data_dir = self.data_dir_entry.get()
            add_files = self.add_files_entry.get().split(";") if self.add_files_entry.get() else []

            final_icon_path = self.process_icon_for_conversion(icon_path, exe_name)

            with open(script_path, 'r', encoding='utf-8') as f:
                code = f.read()

            self.prepare_resources(code, os.path.dirname(script_path))

            self.convert_script(
                script_path,
                exe_name,
                onefile,
                noconsole,
                final_icon_path,
                data_dir,
                add_files
            )

        else:  # Pestaña de editor
            code = self.editor.get(1.0, tk.END)
            if not code.strip():
                messagebox.showerror("Error", "El editor está vacío")
                return

            if self.is_converter_code(code):
                messagebox.showerror("Error", "No puedes convertir este conversor a EXE desde sí mismo")
                return

            exe_name = self.editor_exe_name.get() or "EditorApp"
            onefile = self.editor_onefile.get()
            noconsole = self.editor_noconsole.get()
            # Usar el icono seleccionado en el editor compacto, si existe
            icon_path = self.editor_icon_path

            final_icon_path = self.process_icon_for_conversion(icon_path, exe_name)

            with tempfile.NamedTemporaryFile(suffix=".py", delete=False, mode='w', encoding='utf-8') as tmp:
                tmp.write(code)
                tmp_path = tmp.name
                self.temp_files.append(tmp_path)

            self.prepare_resources(code, os.path.dirname(tmp_path))

            self.convert_script(tmp_path, exe_name, onefile, noconsole, final_icon_path)

    def process_icon_for_conversion(self, icon_path, exe_name):
        if not icon_path or not os.path.exists(icon_path):
            default_icon = self.icon_converter.create_default_icon()
            if default_icon:
                self.log("Usando icono predeterminado para Windows")
                self.log("Nota: Windows puede cachear iconos. Si no se ve el nuevo icono,")
                self.log("prueba a cambiar el nombre del ejecutable o refrescar la carpeta.")
                return default_icon
            return ""

        is_valid_ico = self.icon_converter.validate_and_fix_icon(icon_path)

        if not is_valid_ico and not icon_path.lower().endswith('.ico'):
            self.log(f"Convirtiendo {icon_path} a formato .ico para Windows...")
            converted_icon = self.icon_converter.convert_to_ico(icon_path)

            if converted_icon:
                self.log(f"Icono convertido exitosamente: {converted_icon}")
                self.log("Nota: Windows cachea iconos. Si no se ve el nuevo icono inmediatamente,")
                self.log("prueba a cambiar el nombre del ejecutable o espera unos minutos.")
                self.temp_files.append(converted_icon)
                return converted_icon
            else:
                self.log("No se pudo convertir el icono. Continuando sin icono.")
                return ""

        return icon_path

    def prepare_resources(self, code, base_dir):
        try:
            self.resource_loader_path = None
            self.resource_manifest_path = None

            required_libs = ResourceManager.detect_required_libraries(code)
            if not required_libs:
                self.log("No se detectaron bibliotecas que requieran recursos especiales")
                return

            self.log(f"Bibliotecas que requieren recursos: {', '.join(required_libs)}")

            for lib in required_libs:
                if lib == 'whisper':
                    self.log("Descargando recursos faltantes para Whisper...")
                    (Path(base_dir) / 'whisper' / 'assets').mkdir(parents=True, exist_ok=True)
                    ResourceManager.download_missing_assets(lib, base_dir)

            all_resources = []
            for lib in required_libs:
                lib_resources = ResourceManager.find_library_resources(lib)
                if lib_resources:
                    self.log(f"Recursos encontrados para {lib}:")
                    for resource in lib_resources:
                        self.log(f"  - {resource}")
                    all_resources.extend(lib_resources)

            if not all_resources:
                self.log("No se encontraron recursos adicionales para incluir")
                return

            self.resource_manifest_path = ResourceManager.create_resource_manifest(
                all_resources,
                Path(base_dir)
            )
            self.log(f"Manifiesto de recursos creado: {self.resource_manifest_path}")

            loader_code = ResourceManager.generate_resource_loader(self.resource_manifest_path)
            with tempfile.NamedTemporaryFile(suffix='.py', delete=False, mode='w', encoding='utf-8') as f:
                f.write(loader_code)
                self.resource_loader_path = f.name
                self.temp_files.append(self.resource_loader_path)
            self.log(f"Cargador de recursos generado: {self.resource_loader_path}")

        except Exception as e:
            self.log(f"Error preparando recursos: {str(e)}")
            self.log(traceback.format_exc())

    def is_converter_script(self, script_path):
        current_script = os.path.abspath(__file__)
        selected_script = os.path.abspath(script_path)
        return current_script == selected_script

    def is_converter_code(self, code):
        markers = [
            "class PythonToEXEConverter",
            "CONVERSOR PYTHON A EXE",
            "Py2Exe Revolucionario"
        ]
        return any(marker in code for marker in markers)

    def convert_script(self, script_path, exe_name, onefile, noconsole,
                       icon_path="", data_dir="", add_files=[]):
        self.conversion_in_progress = True
        self.convert_btn.configure(state=tk.DISABLED)

        if not self.progress_frame.winfo_ismapped():
            self.progress_frame.grid()  # Mostrar barra de progreso

        self.progress_bar.start(10)

        self.log("Iniciando conversión...")
        self.log("=" * 50)

        cmd = [
            "pyinstaller",
            "--noconfirm",
            "--clean",
            "--name", exe_name,
            "--distpath", self.output_dir,
            "--workpath", "./build"
        ]

        if onefile:
            cmd.append("--onefile")
        if noconsole:
            cmd.append("--windowed")
        if icon_path and os.path.isfile(icon_path):
            cmd.extend(["--icon", icon_path])
            self.log(f"✓ Usando icono personalizado: {icon_path}")

            if self.icon_converter.validate_and_fix_icon(icon_path):
                self.log("✓ Icono validado para Windows (múltiples tamaños)")
            else:
                self.log("⚠ Advertencia: El icono podría no mostrarse correctamente en Windows")
        else:
            self.log("ℹ No se especificó icono. Windows usará su icono por defecto.")

        if data_dir:
            cmd.extend(["--add-data", f"{data_dir}{os.pathsep}."])
            self.log(f"✓ Incluyendo carpeta de datos: {data_dir}")

        for file in add_files:
            if os.path.exists(file):
                cmd.extend(["--add-data", f"{file}{os.pathsep}."])
                self.log(f"✓ Incluyendo archivo adicional: {file}")

        if self.resource_loader_path and os.path.isfile(self.resource_loader_path):
            cmd.append("--hidden-import=resource_loader")
            cmd.extend(["--add-data", f"{self.resource_loader_path}{os.pathsep}."])
            self.log("✓ Incluyendo cargador de recursos")

        if self.resource_manifest_path and os.path.isfile(self.resource_manifest_path):
            cmd.extend(["--add-data", f"{self.resource_manifest_path}{os.pathsep}."])
            self.log("✓ Incluyendo manifiesto de recursos")

        if self.resource_manifest_path:
            try:
                with open(self.resource_manifest_path, 'r') as f:
                    manifest = json.load(f)
                    for resource in manifest.get('resources', []):
                        src = resource['src']
                        dest = resource['dest']
                        if os.path.exists(src):
                            cmd.extend(["--add-data", f"{src}{os.pathsep}{dest}"])
                            self.log(f"✓ Incluyendo recurso: {src} -> {dest}")
            except Exception as e:
                self.log(f"Error incluyendo recursos del manifiesto: {str(e)}")

        whisper_dir = os.path.join(os.path.dirname(script_path), "whisper")
        if os.path.exists(whisper_dir):
            cmd.extend(["--add-data", f"{whisper_dir}{os.pathsep}whisper"])
            self.log(f"✓ Incluyendo carpeta Whisper: {whisper_dir}")

        if self.resource_loader_path and os.path.isfile(self.resource_loader_path):
            cmd.append("--runtime-hook")
            cmd.append(self.resource_loader_path)
        else:
            self.log("Advertencia: No se encontró el cargador de recursos, no se incluirá el runtime-hook")

        cmd.append(script_path)

        threading.Thread(
            target=self.run_conversion,
            args=(cmd, exe_name, script_path, icon_path),
            daemon=True
        ).start()

    def run_conversion(self, cmd, exe_name, script_path, icon_path=""):
        try:
            self.log(f"Comando PyInstaller:\n{' '.join(cmd)}")
            self.log("=" * 50)

            os.makedirs(self.output_dir, exist_ok=True)

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.log(output.strip())

            exe_path = None
            if process.returncode == 0:
                if "--onefile" in cmd:
                    exe_src = os.path.join(self.output_dir, f"{exe_name}.exe")
                else:
                    exe_src = os.path.join(self.output_dir, exe_name, f"{exe_name}.exe")

                if os.path.exists(exe_src):
                    exe_dest = os.path.join(self.output_dir, f"{exe_name}.exe")

                    if not "--onefile" in cmd:
                        try:
                            shutil.move(exe_src, exe_dest)
                            exe_path = exe_dest
                        except Exception as e:
                            self.log(f"Error moviendo ejecutable: {str(e)}")
                    else:
                        exe_path = exe_src

                    try:
                        shutil.rmtree("./build", ignore_errors=True)
                        if not "--onefile" in cmd:
                            shutil.rmtree(os.path.join(self.output_dir, exe_name), ignore_errors=True)

                        for temp_file in [self.resource_manifest_path, self.resource_loader_path]:
                            if temp_file and os.path.exists(temp_file):
                                os.remove(temp_file)

                        if icon_path and os.path.exists(icon_path) and "temp" in icon_path:
                            try:
                                os.remove(icon_path)
                            except:
                                pass
                    except Exception as e:
                        self.log(f"Error limpiando archivos temporales: {str(e)}")

                    spec_file = f"{exe_name}.spec"
                    if os.path.exists(spec_file):
                        try:
                            os.remove(spec_file)
                        except Exception as e:
                            self.log(f"Error eliminando archivo .spec: {str(e)}")

                    if script_path in self.temp_files:
                        try:
                            os.remove(script_path)
                            self.temp_files.remove(script_path)
                        except Exception as e:
                            self.log(f"Error eliminando script temporal: {str(e)}")

                    if exe_path and os.path.exists(exe_path):
                        self.log("\n" + "=" * 50)
                        self.log("¡CONVERSIÓN EXITOSA!")
                        self.log("=" * 50)
                        self.log(f"✓ Ejecutable creado en: {exe_path}")
                        try:
                            size_mb = round(os.path.getsize(exe_path) / (1024 * 1024), 2)
                            self.log(f"✓ Tamaño del ejecutable: {size_mb} MB")
                        except Exception as e:
                            self.log(f"Error obteniendo tamaño del ejecutable: {str(e)}")

                        self.log("\n📝 IMPORTANTE SOBRE ICONOS EN WINDOWS:")
                        self.log("=" * 40)
                        self.log("Windows cachea los iconos de los archivos. Si el icono no se")
                        self.log("muestra correctamente inmediatamente, intenta lo siguiente:")
                        self.log("1. Cambia el nombre del ejecutable")
                        self.log("2. Mueve el ejecutable a otra carpeta")
                        self.log("3. Espera unos minutos y refresca la carpeta (F5)")
                        self.log("4. Reinicia el Explorador de Windows")
                        self.log("=" * 40)

                        if self.certificate_path and os.path.isfile(self.certificate_path):
                            self.sign_executable(exe_path)

                        response = messagebox.askyesnocancel("Conversión Exitosa",
                                                             f"✓ Conversión completada con éxito!\n"
                                                             f"✓ Ejecutable: {exe_name}.exe\n"
                                                             f"✓ Ubicación: {self.output_dir}\n\n"
                                                             f"¿Qué quieres hacer ahora?\n\n"
                                                             f"• 'Sí' - Abrir carpeta de destino\n"
                                                             f"• 'No' - Mantener el conversor abierto\n"
                                                             f"• 'Cancelar' - Salir del programa")

                        if response is True:
                            try:
                                os.startfile(self.output_dir)
                            except:
                                self.log("No se pudo abrir la carpeta de destino")
                        elif response is None:
                            self.root.quit()

                    else:
                        self.log("Error: El archivo ejecutable no se encuentra en la ruta esperada")
                else:
                    self.log("Error: No se encontró el archivo ejecutable generado")
            else:
                self.log(f"Error en la conversión. Código de salida: {process.returncode}")

        except Exception as e:
            self.log(f"Error inesperado: {str(e)}")
            self.log(traceback.format_exc())
        finally:
            self.conversion_in_progress = False
            self.convert_btn.configure(state=tk.NORMAL)
            self.progress_bar.stop()
            self.progress_frame.grid_remove()

    def sign_executable(self, exe_path):
        self.log("\nAplicando firma digital...")

        signtool_paths = [
            r"C:\Program Files (x86)\Windows Kits\10\bin\10.0.22621.0\x64\signtool.exe",
            r"C:\Program Files (x86)\Windows Kits\10\bin\x64\signtool.exe",
            r"C:\Program Files (x86)\Microsoft SDKs\Windows\v7.1A\Bin\signtool.exe"
        ]

        signtool = None
        for path in signtool_paths:
            if os.path.exists(path):
                signtool = path
                break

        if not signtool:
            self.log("Error: No se encontró signtool. La firma digital no se aplicará.")
            self.log("Instale Windows SDK o busque signtool.exe manualmente.")
            return False

        try:
            cmd = [
                signtool,
                "sign",
                "/f", self.certificate_path,
                "/p", self.certificate_password,
                "/t", "http://timestamp.digicert.com",
                "/v",
                exe_path
            ]

            self.log(f"Comando de firma: {' '.join(cmd)}")

            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                creationflags=subprocess.CREATE_NO_WINDOW
            )

            stdout, stderr = process.communicate()

            if process.returncode == 0:
                self.log("¡Firma digital aplicada exitosamente!")
                return True
            else:
                self.log(f"Error en firma digital (código {process.returncode}):")
                self.log(stdout)
                self.log(stderr)
                return False

        except Exception as e:
            self.log(f"Error aplicando firma digital: {str(e)}")
            return False

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def show_instructions(self):
        instructions = """
        INSTRUCCIONES DE USO - CONVERSOR PYTHON A EXE

        1. CONVERTIR ARCHIVO EXISTENTE:
          - Selecciona un archivo .py usando el botón 'Examinar'
          - Personaliza las opciones de conversión:
            * Nombre del ejecutable
            * Modo un solo archivo (recomendado)
            * Ocultar consola (para aplicaciones GUI)
            * Ícono personalizado (selecciona cualquier imagen)

        2. EDITOR DE CÓDIGO:
          - Escribe o pega tu código Python en el editor
          - Usa las plantillas predefinidas si lo deseas
          - Personaliza las opciones de conversión:
            * Nombre del ejecutable
            * Un solo archivo / Varios archivos
            * Ocultar consola / Mostrar consola
            * Selecciona un icono con el botón 'Icono...' (se convertirá automáticamente)
          - Todo en una sola fila para mayor comodidad

        3. SELECCIÓN DE ICONOS:
          - Haz clic en "Icono..." en la pestaña Editor, o en "Buscar Imagen" en la pestaña Archivo.
          - El diálogo mostrará primero las imágenes (PNG, JPG, etc.)
          - Cualquier imagen seleccionada se convertirá automáticamente a .ico
          - Verás una vista previa del icono en la interfaz
          - Si no seleccionas icono, se creará uno predeterminado automáticamente

        4. PROBLEMA CON ICONOS EN WINDOWS:
          Windows cachea los iconos. Si tu nuevo icono no aparece inmediatamente:
          - Cambia el nombre del ejecutable
          - Mueve el ejecutable a otra carpeta
          - Espera unos minutos y presiona F5 en la carpeta
          - Reinicia el Explorador de Windows (Ctrl+Shift+Esc → Explorer.exe → Reiniciar)

        5. CONFIGURACIÓN (Menú Archivo):
          - Firma Digital: Ingresa tu información como autor
          - Carpeta Destino: Selecciona dónde guardar los ejecutables

        6. RESULTADO:
          - El ejecutable se guardará en la carpeta seleccionada
          - Si configuraste un certificado, se firmará automáticamente
          - Los recursos necesarios se incluirán AUTOMÁTICAMENTE

        DETECCIÓN AUTOMÁTICA DE RECURSOS:
          - El sistema detecta bibliotecas como Whisper, NLTK, spaCy, etc.
          - Incluye automáticamente todos los archivos necesarios
          - Configura el entorno para que la aplicación encuentre los recursos
          - Soluciona el error "No such file or directory" para archivos como mel_filters.npz
        """
        messagebox.showinfo("Instrucciones de Uso", instructions)

    def show_about(self):
        about_info = """
        Py2Exe Revolucionario - Edición Premium

        Versión: 13.0
        Desarrollador: Conversor Avanzado Python a EXE

        Características principales:
        - Conversión de scripts Python a .exe portables
        - Editor de código integrado con menú contextual
        - Firma digital opcional con certificados
        - Conversión AUTOMÁTICA de cualquier imagen a iconos .ico
        - Vista previa de iconos en la interfaz
        - Diseño compacto en la pestaña Editor (todo en una fila)
        - Solución para problemas de caché de iconos en Windows
        - Prevención de recursión
        - DETECCIÓN AUTOMÁTICA DE RECURSOS

        Tecnologías:
        - Python 3.8+
        - PyInstaller con extensiones avanzadas
        - Tkinter para la interfaz gráfica
        - Pillow para conversión automática de imágenes
        - Sistema inteligente de detección de dependencias

        © 2023 Todos los derechos reservados
        """
        messagebox.showinfo("Acerca de", about_info)


def main():
    root = tk.Tk()
    app = PythonToEXEConverter(root)
    root.mainloop()


if __name__ == "__main__":
    main()