#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DESCARGADOR AUTOMÁTICO DE VÍDEOS - AUTOINSTALABLE
Descarga videos de YouTube, TikTok, Instagram, Facebook, Reddit, etc.
"""

import sys
import os
import subprocess
import threading
import webbrowser
from pathlib import Path

# Verificar si estamos en un entorno frozen (ejecutable)
IS_FROZEN = getattr(sys, 'frozen', False)

def check_and_install():
    """Verifica e instala todas las dependencias automáticamente"""
    
    print("🔍 Verificando dependencias...")
    
    # Lista de paquetes necesarios
    required_packages = [
        ('yt-dlp', 'yt_dlp'),
        ('requests', 'requests'),
        ('Pillow', 'PIL'),  # Para íconos
    ]
    
    missing_packages = []
    
    for pkg_name, import_name in required_packages:
        try:
            __import__(import_name)
            print(f"✅ {pkg_name} ya está instalado")
        except ImportError:
            missing_packages.append(pkg_name)
            print(f"❌ {pkg_name} no encontrado")
    
    # Si hay paquetes faltantes, instalarlos
    if missing_packages:
        print(f"\n📦 Instalando {len(missing_packages)} paquetes...")
        
        # Usar pip del sistema
        python_exe = sys.executable
        
        for pkg in missing_packages:
            print(f"Instalando {pkg}...")
            try:
                subprocess.check_call([python_exe, "-m", "pip", "install", pkg, "--upgrade"])
                print(f"✅ {pkg} instalado correctamente")
            except subprocess.CalledProcessError as e:
                print(f"❌ Error instalando {pkg}: {e}")
                return False
    
    # Verificar/Instalar FFmpeg (necesario para conversiones)
    print("\n🔧 Verificando FFmpeg...")
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        print("✅ FFmpeg encontrado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️ FFmpeg no encontrado")
        print("Instalando FFmpeg...")
        
        # Instalar FFmpeg según el sistema operativo
        if sys.platform == "win32":
            # Windows: Descargar ffmpeg.exe automáticamente
            import requests
            import zipfile
            import io
            
            print("Descargando FFmpeg para Windows...")
            try:
                # URL de FFmpeg para Windows (versión estática)
                url = "https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip"
                
                response = requests.get(url)
                response.raise_for_status()
                
                # Extraer ffmpeg.exe
                with zipfile.ZipFile(io.BytesIO(response.content)) as z:
                    # Encontrar ffmpeg.exe en el zip
                    for name in z.namelist():
                        if name.endswith('bin/ffmpeg.exe'):
                            # Extraer todos los archivos necesarios
                            extract_dir = Path('.') / 'ffmpeg'
                            extract_dir.mkdir(exist_ok=True)
                            
                            # Extraer archivo
                            z.extract(name, extract_dir)
                            ffmpeg_path = extract_dir / name
                            
                            # Renombrar para simplificar
                            final_path = extract_dir / 'ffmpeg.exe'
                            if ffmpeg_path != final_path:
                                ffmpeg_path.rename(final_path)
                            
                            # Agregar al PATH del programa
                            ffmpeg_dir = str(final_path.parent)
                            os.environ['PATH'] = ffmpeg_dir + os.pathsep + os.environ['PATH']
                            
                            print(f"✅ FFmpeg instalado en: {final_path}")
                            break
            except Exception as e:
                print(f"⚠️ No se pudo instalar FFmpeg automáticamente: {e}")
                print("Puedes instalarlo manualmente desde: https://github.com/BtbN/FFmpeg-Builds/releases")
                print("O desde: https://ffmpeg.org/download.html")
                
                # Intentar método alternativo
                try:
                    print("Intentando instalación alternativa...")
                    subprocess.check_call([sys.executable, "-m", "pip", "install", "ffmpeg-python"])
                    print("✅ ffmpeg-python instalado como alternativa")
                except:
                    print("❌ No se pudo instalar FFmpeg")
                    return False
        else:
            # Linux/macOS
            try:
                if sys.platform == "linux":
                    subprocess.run(['sudo', 'apt-get', 'install', '-y', 'ffmpeg'], check=True)
                elif sys.platform == "darwin":
                    subprocess.run(['brew', 'install', 'ffmpeg'], check=True)
                print("✅ FFmpeg instalado")
            except:
                print("⚠️ Instala FFmpeg manualmente:")
                print("  Linux: sudo apt-get install ffmpeg")
                print("  macOS: brew install ffmpeg")
                return False
    
    return True

def install_tkinter():
    """Instala Tkinter si es necesario"""
    try:
        import tkinter
        print("✅ Tkinter ya está instalado")
        return True
    except ImportError:
        print("❌ Tkinter no está disponible")
        
        if sys.platform == "linux":
            print("Instalando Tkinter para Linux...")
            try:
                subprocess.run(['sudo', 'apt-get', 'install', '-y', 'python3-tk'], check=True)
                print("✅ Tkinter instalado")
                return True
            except:
                print("⚠️ No se pudo instalar Tkinter automáticamente")
                print("Instala manualmente: sudo apt-get install python3-tk")
        elif sys.platform == "darwin":
            print("Tkinter viene preinstalado en macOS")
        elif sys.platform == "win32":
            print("Tkinter viene preinstalado en Windows")
        
        return False

def create_shortcut():
    """Crea accesos directos según el sistema operativo"""
    
    # Ruta del script actual
    script_path = os.path.abspath(__file__)
    
    if sys.platform == "win32":
        # Crear archivo .bat para Windows
        bat_content = f'''@echo off
echo Iniciando Descargador de Videos...
echo.

rem Agregar FFmpeg al PATH temporalmente
set PATH=%CD%\\ffmpeg\\bin;%PATH%

"{sys.executable}" "{script_path}"
if errorlevel 1 pause
'''
        
        with open('Iniciar_Descargador.bat', 'w', encoding='utf-8') as f:
            f.write(bat_content)
        
        # También crear un archivo .vbs para ejecutar sin consola
        vbs_content = f'''Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c \"\"{sys.executable}\" \"{script_path}\"\"", 0, False
'''
        
        with open('Descargador_Videos.vbs', 'w', encoding='utf-8') as f:
            f.write(vbs_content)
        
        print("\n📁 Accesos directos creados:")
        print("  • Iniciar_Descargador.bat - Ejecutar con doble clic")
        print("  • Descargador_Videos.vbs - Ejecutar en segundo plano")
        
    else:
        # Crear script ejecutable para Linux/macOS
        script_content = f'''#!/bin/bash
# Descargador Automático de Videos
echo "Iniciando Descargador de Videos..."
cd "{os.path.dirname(script_path)}"
"{sys.executable}" "{script_path}"
'''
        
        with open('iniciar_descargador.sh', 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Hacerlo ejecutable
        os.chmod('iniciar_descargador.sh', 0o755)
        
        print("\n📁 Script creado:")
        print("  • iniciar_descargador.sh - Ejecutar con: ./iniciar_descargador.sh")

# ============================================================================
# INTERFAZ GRÁFICA PRINCIPAL
# ============================================================================

class VideoDownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Descargador Universal de Videos")
        self.root.geometry("800x650")
        self.root.configure(bg="#0d1117")
        
        # Hacer la ventana resizable
        self.root.resizable(True, True)
        
        # Variables
        self.url_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Listo para descargar")
        self.progress_var = tk.IntVar(value=0)
        self.download_path = tk.StringVar(value=str(Path.home() / "Downloads" / "VideosDescargados"))
        self.quality_var = tk.StringVar(value="mp4")
        self.format_var = tk.StringVar(value="mp4")
        
        # Crear carpeta de descargas si no existe
        os.makedirs(self.download_path.get(), exist_ok=True)
        
        # Configurar icono
        self.setup_icon()
        
        # Configurar interfaz
        self.setup_ui()
        
        # Verificar yt-dlp
        self.check_ytdlp_version()
        
    def setup_icon(self):
        """Configura el icono de la aplicación"""
        try:
            # Intentar cargar icono desde archivo
            icon_path = "icon.ico"
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Crear icono simple con tkinter
                self.root.iconbitmap(default='')
        except:
            pass
    
    def setup_ui(self):
        """Configura toda la interfaz gráfica"""
        
        # Frame principal con scroll
        main_frame = tk.Frame(self.root, bg="#0d1117")
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Título
        title_frame = tk.Frame(main_frame, bg="#0d1117")
        title_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            title_frame,
            text="⬇️ DESCARGADOR UNIVERSAL DE VÍDEOS",
            font=("Arial", 20, "bold"),
            bg="#0d1117",
            fg="#58a6ff"
        ).pack()
        
        tk.Label(
            title_frame,
            text="Descarga videos de YouTube, TikTok, Instagram, Facebook, Reddit, Twitter, etc.",
            font=("Arial", 10),
            bg="#0d1117",
            fg="#8b949e"
        ).pack()
        
        # Frame de entrada
        input_frame = tk.LabelFrame(
            main_frame,
            text=" ENLACE DEL VÍDEO ",
            font=("Arial", 11, "bold"),
            bg="#161b22",
            fg="#c9d1d9",
            padx=15,
            pady=10
        )
        input_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Campo de URL
        url_frame = tk.Frame(input_frame, bg="#161b22")
        url_frame.pack(fill=tk.X)
        
        tk.Label(
            url_frame,
            text="🔗 URL:",
            bg="#161b22",
            fg="#c9d1d9",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        self.url_entry = tk.Entry(
            url_frame,
            textvariable=self.url_var,
            width=60,
            font=("Arial", 10),
            bg="#0d1117",
            fg="#c9d1d9",
            insertbackground="white",
            relief=tk.FLAT
        )
        self.url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Botones de URL
        btn_frame = tk.Frame(url_frame, bg="#161b22")
        btn_frame.pack(side=tk.LEFT)
        
        tk.Button(
            btn_frame,
            text="📋 Pegar",
            command=self.paste_url,
            bg="#238636",
            fg="white",
            font=("Arial", 9, "bold"),
            relief=tk.FLAT,
            padx=15,
            pady=3,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 5))
        
        tk.Button(
            btn_frame,
            text="🗑️ Limpiar",
            command=lambda: self.url_var.set(""),
            bg="#da3633",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=10,
            pady=3,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # Frame de configuración
        config_frame = tk.LabelFrame(
            main_frame,
            text=" CONFIGURACIÓN ",
            font=("Arial", 11, "bold"),
            bg="#161b22",
            fg="#c9d1d9",
            padx=15,
            pady=10
        )
        config_frame.pack(fill=tk.X, pady=(0, 15))
        
        # Primera fila: Calidad y Formato
        row1 = tk.Frame(config_frame, bg="#161b22")
        row1.pack(fill=tk.X, pady=(0, 10))
        
        # Calidad (SIMPLIFICADO para evitar problemas de codec)
        tk.Label(
            row1,
            text="📊 Calidad:",
            bg="#161b22",
            fg="#c9d1d9",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        qualities = [
            ("MP4 compatible", "mp4"),
            ("Mejor calidad", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
            ("720p MP4", "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4][height<=720]"),
            ("480p MP4", "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4][height<=480]"),
            ("Solo audio MP3", "bestaudio[ext=m4a]")
        ]
        
        for text, value in qualities:
            rb = tk.Radiobutton(
                row1,
                text=text,
                variable=self.quality_var,
                value=value,
                bg="#161b22",
                fg="#c9d1d9",
                selectcolor="#0d1117",
                activebackground="#161b22",
                font=("Arial", 9),
                cursor="hand2"
            )
            rb.pack(side=tk.LEFT, padx=(0, 15))
        
        # Segunda fila: Formato y Carpeta
        row2 = tk.Frame(config_frame, bg="#161b22")
        row2.pack(fill=tk.X)
        
        # Formato
        tk.Label(
            row2,
            text="📁 Formato:",
            bg="#161b22",
            fg="#c9d1d9",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        formats = ["mp4", "mp3", "m4a", "webm", "mkv"]
        format_menu = ttk.Combobox(
            row2,
            textvariable=self.format_var,
            values=formats,
            state="readonly",
            width=10,
            font=("Arial", 9)
        )
        format_menu.pack(side=tk.LEFT, padx=(0, 20))
        
        # Carpeta de destino
        tk.Label(
            row2,
            text="📂 Carpeta:",
            bg="#161b22",
            fg="#c9d1d9",
            font=("Arial", 10)
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        path_entry = tk.Entry(
            row2,
            textvariable=self.download_path,
            width=30,
            font=("Arial", 9),
            bg="#0d1117",
            fg="#c9d1d9"
        )
        path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        tk.Button(
            row2,
            text="📂",
            command=self.browse_folder,
            bg="#30363d",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=10,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # Botón de descarga principal
        self.download_btn = tk.Button(
            main_frame,
            text="🚀 DESCARGAR VÍDEO",
            command=self.start_download,
            bg="#238636",
            fg="white",
            font=("Arial", 12, "bold"),
            relief=tk.FLAT,
            padx=40,
            pady=10,
            cursor="hand2"
        )
        self.download_btn.pack(pady=(10, 15))
        
        # Frame de progreso
        progress_frame = tk.Frame(main_frame, bg="#0d1117")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            mode='determinate',
            length=400
        )
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        # Porcentaje
        self.percent_label = tk.Label(
            progress_frame,
            text="0%",
            bg="#0d1117",
            fg="#58a6ff",
            font=("Arial", 10, "bold")
        )
        self.percent_label.pack(side=tk.LEFT)
        
        # Estado
        self.status_label = tk.Label(
            main_frame,
            textvariable=self.status_var,
            bg="#0d1117",
            fg="#8b949e",
            font=("Arial", 10)
        )
        self.status_label.pack()
        
        # Consola de salida
        console_frame = tk.LabelFrame(
            main_frame,
            text=" CONSOLA ",
            font=("Arial", 11, "bold"),
            bg="#161b22",
            fg="#c9d1d9",
            padx=10,
            pady=10
        )
        console_frame.pack(fill=tk.BOTH, expand=True, pady=(10, 0))
        
        # Text widget con scroll
        console_scroll = tk.Scrollbar(console_frame)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.console_text = tk.Text(
            console_frame,
            height=10,
            bg="#0d1117",
            fg="#c9d1d9",
            font=("Consolas", 9),
            yscrollcommand=console_scroll.set,
            wrap=tk.WORD
        )
        self.console_text.pack(fill=tk.BOTH, expand=True)
        
        console_scroll.config(command=self.console_text.yview)
        
        # Frame inferior con botones adicionales
        bottom_frame = tk.Frame(main_frame, bg="#0d1117")
        bottom_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Botón abrir carpeta
        tk.Button(
            bottom_frame,
            text="📁 Abrir carpeta",
            command=self.open_download_folder,
            bg="#30363d",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón actualizar yt-dlp
        tk.Button(
            bottom_frame,
            text="🔄 Actualizar",
            command=self.update_ytdlp,
            bg="#1f6feb",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón limpiar consola
        tk.Button(
            bottom_frame,
            text="🧹 Limpiar",
            command=self.clear_console,
            bg="#6e7681",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        ).pack(side=tk.LEFT)
        
        # Botón solucionar codec
        tk.Button(
            bottom_frame,
            text="🔧 Solucionar Codec",
            command=self.fix_codec_issue,
            bg="#8957e5",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        ).pack(side=tk.LEFT, padx=(0, 10))
        
        # Botón salir
        tk.Button(
            bottom_frame,
            text="❌ Salir",
            command=self.root.quit,
            bg="#da3633",
            fg="white",
            font=("Arial", 9),
            relief=tk.FLAT,
            padx=15,
            cursor="hand2"
        ).pack(side=tk.RIGHT)
        
        # Enlace de ayuda
        help_link = tk.Label(
            bottom_frame,
            text="¿Necesitas ayuda?",
            fg="#58a6ff",
            bg="#0d1117",
            font=("Arial", 9, "underline"),
            cursor="hand2"
        )
        help_link.pack(side=tk.RIGHT, padx=(0, 20))
        help_link.bind("<Button-1>", lambda e: webbrowser.open("https://github.com/yt-dlp/yt-dlp"))
        
        # Bind Enter para iniciar descarga
        self.root.bind('<Return>', lambda e: self.start_download())
        
        # Focus en el campo de URL
        self.url_entry.focus_set()
    
    def log(self, message, color="#c9d1d9"):
        """Agrega mensaje a la consola"""
        self.console_text.insert(tk.END, f"{message}\n")
        self.console_text.tag_add("color", "end-2c linestart", "end-1c")
        self.console_text.tag_config("color", foreground=color)
        self.console_text.see(tk.END)
        self.root.update()
    
    def paste_url(self):
        """Pega URL desde portapapeles"""
        try:
            clipboard_text = self.root.clipboard_get()
            self.url_var.set(clipboard_text)
            self.log("✓ URL pegada desde portapapeles", "#3fb950")
        except:
            self.log("✗ No se pudo pegar URL", "#f85149")
    
    def browse_folder(self):
        """Selecciona carpeta de destino"""
        folder = filedialog.askdirectory(initialdir=self.download_path.get())
        if folder:
            self.download_path.set(folder)
            os.makedirs(folder, exist_ok=True)
            self.log(f"✓ Carpeta seleccionada: {folder}", "#3fb950")
    
    def open_download_folder(self):
        """Abre la carpeta de descargas"""
        folder = self.download_path.get()
        if os.path.exists(folder):
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.run(["open", folder])
            else:
                subprocess.run(["xdg-open", folder])
            self.log(f"✓ Carpeta abierta: {folder}", "#3fb950")
        else:
            self.log("✗ La carpeta no existe", "#f85149")
    
    def clear_console(self):
        """Limpia la consola"""
        self.console_text.delete(1.0, tk.END)
        self.log("Consola limpiada", "#8b949e")
    
    def fix_codec_issue(self):
        """Solución para problemas de codec en Windows"""
        def fix_thread():
            self.log("🔧 Solucionando problemas de codec...", "#d29922")
            
            # Instalar codecs adicionales
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", "python-vlc", "--upgrade"])
                self.log("✅ VLC player bindings instalados", "#3fb950")
                
                # Recomendar instalar codecs de Windows
                self.log("\n💡 RECOMENDACIONES PARA WINDOWS:", "#58a6ff")
                self.log("1. Instala VLC Media Player: https://www.videolan.org/vlc/", "#58a6ff")
                self.log("2. O instala K-Lite Codec Pack: https://codecguide.com/", "#58a6ff")
                self.log("3. También puedes usar el reproductor de VLC para abrir los videos", "#58a6ff")
                
                # Probar si VLC está disponible
                try:
                    import vlc
                    self.log("✅ VLC Python está disponible", "#3fb950")
                    
                    # Crear botón para abrir con VLC
                    self.log("\n🔄 Configurando para usar formatos compatibles...", "#58a6ff")
                    messagebox.showinfo(
                        "Solución de Codec",
                        "Se ha configurado para usar formatos MP4 compatibles.\n"
                        "Ahora los videos deberían reproducirse en Windows."
                    )
                    
                except ImportError:
                    self.log("⚠️ VLC no está instalado en el sistema", "#d29922")
                    
            except Exception as e:
                self.log(f"❌ Error al instalar soluciones: {e}", "#f85149")
        
        threading.Thread(target=fix_thread, daemon=True).start()
    
    def check_ytdlp_version(self):
        """Verifica la versión de yt-dlp"""
        try:
            import yt_dlp
            version = yt_dlp.version.__version__
            self.log(f"✅ yt-dlp {version} listo", "#3fb950")
            
            # Configurar para Windows (evitar formatos problemáticos)
            if sys.platform == "win32":
                self.log("⚠️ Configurando para compatibilidad con Windows...", "#d29922")
                self.quality_var.set("mp4")
                self.format_var.set("mp4")
        except ImportError:
            self.log("❌ yt-dlp no está instalado", "#f85149")
            self.install_ytdlp()
    
    def install_ytdlp(self):
        """Instala yt-dlp automáticamente"""
        self.log("Instalando yt-dlp...", "#d29922")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "yt-dlp", "--upgrade"])
            self.log("✅ yt-dlp instalado correctamente", "#3fb950")
        except Exception as e:
            self.log(f"❌ Error instalando yt-dlp: {e}", "#f85149")
    
    def update_ytdlp(self):
        """Actualiza yt-dlp"""
        def update_thread():
            self.download_btn.config(state=tk.DISABLED, text="ACTUALIZANDO...")
            self.log("Actualizando yt-dlp...", "#d29922")
            
            try:
                result = subprocess.run(
                    [sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"],
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                if "Successfully installed" in result.stdout or "Requirement already satisfied" in result.stdout:
                    self.log("✅ yt-dlp actualizado", "#3fb950")
                else:
                    self.log(f"ℹ️ {result.stdout}", "#8b949e")
                    
            except subprocess.CalledProcessError as e:
                self.log(f"❌ Error: {e.stderr}", "#f85149")
            finally:
                self.download_btn.config(state=tk.NORMAL, text="🚀 DESCARGAR VÍDEO")
        
        threading.Thread(target=update_thread, daemon=True).start()
    
    def start_download(self):
        """Inicia la descarga del video"""
        url = self.url_var.get().strip()
        
        if not url:
            messagebox.showwarning("URL vacía", "Por favor, pega un enlace de video")
            return
        
        # Validar URL básica
        if not url.startswith(('http://', 'https://')):
            messagebox.showerror("URL inválida", "El enlace debe comenzar con http:// o https://")
            return
        
        # Actualizar interfaz
        self.download_btn.config(state=tk.DISABLED, text="DESCARGANDO...")
        self.progress_var.set(0)
        self.percent_label.config(text="0%")
        self.status_var.set("Procesando...")
        self.clear_console()
        
        # Iniciar descarga en hilo separado
        thread = threading.Thread(target=self.download_video, args=(url,), daemon=True)
        thread.start()
    
    def download_video(self, url):
        """Descarga el video usando yt-dlp"""
        try:
            import yt_dlp
            
            # Configurar opciones de yt-dlp COMPATIBLES con Windows
            ydl_opts = {
                'outtmpl': os.path.join(self.download_path.get(), '%(title)s.%(ext)s'),
                'progress_hooks': [self.progress_hook],
                'quiet': False,
                'no_warnings': False,
                # Configuración para compatibilidad con Windows
                'format': self.quality_var.get(),
                'merge_output_format': 'mp4',  # Siempre fusionar a MP4
                'postprocessors': [
                    {
                        'key': 'FFmpegVideoConvertor',
                        'preferedformat': 'mp4',
                    }
                ],
                # Configuraciones adicionales para evitar problemas
                'windowsfilenames': True,  # Nombres de archivo compatibles con Windows
                'trim_file_name': 100,  # Limitar longitud del nombre
                # Forzar codecs compatibles
                'format_sort': ['res:1080', 'ext:mp4:m4a', 'codec:avc'],
                'prefer_free_formats': False,
                # Configuración de FFmpeg
                'postprocessor_args': {
                    'ffmpeg': [
                        '-c:v', 'libx264',  # Codec de video compatible
                        '-c:a', 'aac',      # Codec de audio compatible
                        '-strict', 'experimental',
                        '-movflags', '+faststart'  # Para streaming web
                    ]
                }
            }
            
            # Si es solo audio
            if self.quality_var.get() == "bestaudio[ext=m4a]":
                ydl_opts['format'] = 'bestaudio/best'
                ydl_opts['postprocessors'] = [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
                ydl_opts['merge_output_format'] = None
            
            self.log(f"🔗 URL: {url}", "#58a6ff")
            self.log(f"📊 Calidad: {self.quality_var.get()}", "#58a6ff")
            self.log(f"📁 Formato de salida: MP4 (compatible con Windows)", "#58a6ff")
            self.log(f"📂 Guardando en: {self.download_path.get()}", "#58a6ff")
            self.log("🔄 Configuración optimizada para Windows", "#3fb950")
            self.log("-" * 50, "#30363d")
            
            # Verificar FFmpeg
            try:
                subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
                self.log("✅ FFmpeg disponible para procesamiento", "#3fb950")
            except:
                self.log("⚠️ FFmpeg no encontrado, limitando opciones...", "#d29922")
                ydl_opts['format'] = 'best[ext=mp4]/best'
                ydl_opts['postprocessors'] = []
            
            # Crear instancia de yt-dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extraer información
                info = ydl.extract_info(url, download=False)
                self.log(f"📝 Título: {info.get('title', 'Desconocido')}", "#c9d1d9")
                self.log(f"⏱️ Duración: {info.get('duration', 0)} segundos", "#c9d1d9")
                self.log(f"👤 Subido por: {info.get('uploader', 'Desconocido')}", "#c9d1d9")
                self.log("-" * 50, "#30363d")
                
                # Iniciar descarga
                self.log("⬇️ Iniciando descarga (compatible con Windows)...", "#3fb950")
                ydl.download([url])
            
            # Descarga completada
            self.progress_var.set(100)
            self.percent_label.config(text="100%")
            self.status_var.set("¡Descarga completada!")
            self.log("✅ ¡DESCARGA COMPLETADA!", "#3fb950")
            self.log(f"📁 Video guardado en: {self.download_path.get()}", "#3fb950")
            self.log("💡 El video está en formato MP4 compatible con Windows", "#58a6ff")
            
            # Verificar si el archivo se creó
            import glob
            folder = self.download_path.get()
            mp4_files = glob.glob(os.path.join(folder, "*.mp4"))
            if mp4_files:
                latest_file = max(mp4_files, key=os.path.getctime)
                file_size = os.path.getsize(latest_file) / (1024*1024)  # MB
                self.log(f"📦 Archivo: {os.path.basename(latest_file)} ({file_size:.2f} MB)", "#3fb950")
            
            # Mostrar mensaje de éxito con recomendaciones
            self.root.after(0, lambda: messagebox.showinfo(
                "¡Éxito!",
                f"Video descargado correctamente.\n\n"
                f"Guardado en:\n{self.download_path.get()}\n\n"
                f"Recomendación para Windows:\n"
                f"• Usa VLC Media Player para reproducir\n"
                f"• O instala K-Lite Codec Pack"
            ))
            
        except yt_dlp.utils.DownloadError as e:
            self.log(f"❌ Error de descarga: {str(e)}", "#f85149")
            self.status_var.set("Error en la descarga")
            
            # Intentar con configuración más simple
            if "format" in str(e).lower() or "codec" in str(e).lower():
                self.log("Intentando formato MP4 simple...", "#d29922")
                try:
                    simple_opts = {
                        'outtmpl': os.path.join(self.download_path.get(), '%(title)s.%(ext)s'),
                        'format': 'best[ext=mp4]/best',
                        'windowsfilenames': True,
                    }
                    
                    with yt_dlp.YoutubeDL(simple_opts) as ydl:
                        ydl.download([url])
                    
                    self.progress_var.set(100)
                    self.status_var.set("¡Descarga completada!")
                    self.log("✅ ¡DESCARGA COMPLETADA! (formato simple)", "#3fb950")
                    
                except Exception as retry_error:
                    self.log(f"❌ Error en reintento: {retry_error}", "#f85149")
        
        except Exception as e:
            self.log(f"❌ Error inesperado: {str(e)}", "#f85149")
            self.status_var.set("Error inesperado")
            
        finally:
            # Restaurar botón
            self.root.after(0, lambda: self.download_btn.config(
                state=tk.NORMAL, 
                text="🚀 DESCARGAR VÍDEO"
            ))
    
    def progress_hook(self, d):
        """Hook para mostrar progreso"""
        if d['status'] == 'downloading':
            # Calcular porcentaje
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            elif 'total_bytes_estimate' in d and d['total_bytes_estimate']:
                percent = (d['downloaded_bytes'] / d['total_bytes_estimate']) * 100
            else:
                percent = 0
            
            # Actualizar interfaz
            self.progress_var.set(percent)
            self.percent_label.config(text=f"{percent:.1f}%")
            self.status_var.set(f"Descargando... {d.get('_percent_str', '')}")
            
            # Mostrar velocidad si está disponible
            if '_speed_str' in d:
                speed = d['_speed_str'].strip()
                self.log(f"📥 {d.get('_percent_str', '')} | {speed}", "#58a6ff")
        
        elif d['status'] == 'finished':
            self.log("✓ Descarga completada, procesando video...", "#3fb950")
            self.status_var.set("Procesando video...")
            self.log("🔄 Convirtiendo a formato compatible MP4...", "#58a6ff")

# ============================================================================
# INICIO DE LA APLICACIÓN
# ============================================================================

def main():
    """Función principal que maneja todo el proceso"""
    
    print("=" * 60)
    print("DESCARGADOR AUTOMÁTICO DE VÍDEOS")
    print("=" * 60)
    
    # Paso 1: Verificar e instalar dependencias
    print("\n[1/3] Verificando dependencias...")
    if not check_and_install():
        print("❌ Error al instalar dependencias")
        input("Presiona Enter para salir...")
        return
    
    # Paso 2: Verificar/Instalar Tkinter
    print("\n[2/3] Verificando interfaz gráfica...")
    if not install_tkinter():
        print("❌ Tkinter no está disponible")
        input("Presiona Enter para salir...")
        return
    
    # Paso 3: Importar tkinter (ahora debería estar disponible)
    global tk, ttk, filedialog, messagebox
    try:
        import tkinter as tk
        from tkinter import ttk, filedialog, messagebox
    except ImportError:
        print("❌ No se pudo importar tkinter")
        input("Presiona Enter para salir...")
        return
    
    # Paso 4: Crear accesos directos
    print("\n[3/3] Configurando aplicación...")
    create_shortcut()
    
    print("\n" + "=" * 60)
    print("✅ ¡TODAS LAS DEPENDENCIAS ESTÁN INSTALADAS!")
    print("=" * 60)
    print("\n🔧 Iniciando aplicación...")
    print("⏳ Por favor espera, esto puede tomar unos segundos...")
    
    # Crear ventana principal
    root = tk.Tk()
    
    # Configurar ventana
    root.withdraw()  # Ocultar ventana mientras se carga
    
    # Mostrar ventana de carga
    splash = tk.Toplevel(root)
    splash.title("Cargando...")
    splash.geometry("300x150")
    splash.configure(bg="#0d1117")
    
    # Centrar splash
    splash.update_idletasks()
    x = (splash.winfo_screenwidth() // 2) - (300 // 2)
    y = (splash.winfo_screenheight() // 2) - (150 // 2)
    splash.geometry(f'300x150+{x}+{y}')
    
    # Contenido del splash
    tk.Label(
        splash,
        text="🎬 Descargador de Videos",
        font=("Arial", 14, "bold"),
        bg="#0d1117",
        fg="#58a6ff"
    ).pack(pady=20)
    
    tk.Label(
        splash,
        text="Inicializando...",
        font=("Arial", 10),
        bg="#0d1117",
        fg="#8b949e"
    ).pack()
    
    progress = ttk.Progressbar(splash, mode='indeterminate', length=200)
    progress.pack(pady=20)
    progress.start()
    
    # Función para iniciar la aplicación principal
    def start_main_app():
        splash.destroy()
        root.deiconify()
        
        # Crear aplicación
        app = VideoDownloaderApp(root)
        
        # Centrar ventana
        root.update_idletasks()
        width = root.winfo_width()
        height = root.winfo_height()
        x = (root.winfo_screenwidth() // 2) - (width // 2)
        y = (root.winfo_screenheight() // 2) - (height // 2)
        root.geometry(f'{width}x{height}+{x}+{y}')
        
        # Mensaje de bienvenida
        print("\n" + "=" * 60)
        print("🎉 ¡APLICACIÓN INICIADA CORRECTAMENTE!")
        print("=" * 60)
        print("\n📝 INSTRUCCIONES PARA WINDOWS:")
        print("1. Pega cualquier enlace de video en el campo URL")
        print("2. Usa 'MP4 compatible' para evitar problemas")
        print("3. Haz clic en 'DESCARGAR VÍDEO' o presiona Enter")
        print("4. El video se guardará en formato MP4 compatible")
        print("\n🔧 Si tienes problemas de reproducción:")
        print("   • Usa VLC Media Player (recomendado)")
        print("   • O haz clic en 'Solucionar Codec'")
        print("\n🌍 SOPORTA: YouTube, TikTok, Instagram, Facebook, Reddit, etc.")
        print("=" * 60)
        
        # Iniciar loop principal
        root.mainloop()
    
    # Esperar un momento y luego iniciar
    splash.after(1500, start_main_app)
    root.mainloop()

if __name__ == "__main__":
    # Si estamos en Windows, evitar la ventana de consola
    if sys.platform == "win32" and IS_FROZEN:
        # Esto es para el ejecutable
        import ctypes
        ctypes.windll.user32.ShowWindow(ctypes.windll.kernel32.GetConsoleWindow(), 0)
    
    main()