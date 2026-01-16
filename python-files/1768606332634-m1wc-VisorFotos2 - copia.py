import sys, os
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QLabel, QSlider,
    QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, 
    QDialog, QTextEdit, QScrollArea
)
from PySide6.QtCore import (
    Qt, QTimer, QUrl, QSize, QByteArray
)
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPixmap, QTransform, QMovie
from PySide6.QtSvg import QSvgRenderer
import random
from datetime import datetime
import json

# -------- ICONOS SVG --------
ICONS = {
    'prev': '''<svg viewBox="0 0 24 24" fill="white"><path d="M6 6h2v12H6zm3.5 6l8.5 6V6z"/></svg>''',
    'next': '''<svg viewBox="0 0 24 24" fill="white"><path d="M6 18l8.5-6L6 6v12zM16 6v12h2V6h-2z"/></svg>''',
    'info': '''<svg viewBox="0 0 24 24" fill="white"><path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>''',
    'shuffle': '''<svg viewBox="0 0 24 24" fill="white"><path d="M10.59 9.17L5.41 4 4 5.41l5.17 5.17 1.42-1.41zM14.5 4l2.04 2.04L4 18.59 5.41 20 17.96 7.46 20 9.5V4h-5.5zm.33 9.41l-1.41 1.41 3.13 3.13L14.5 20H20v-5.5l-2.04 2.04-3.13-3.13z"/></svg>''',
    'delete': '''<svg viewBox="0 0 24 24" fill="white"><path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/></svg>''',
    'playlist': '''<svg viewBox="0 0 24 24" fill="white"><path d="M15 6H3v2h12V6zm0 4H3v2h12v-2zM3 16h8v-2H3v2zM17 6v8.18c-.31-.11-.65-.18-1-.18-1.66 0-3 1.34-3 3s1.34 3 3 3 3-1.34 3-3V8h3V6h-5z"/></svg>''',
    'copy': '''<svg viewBox="0 0 24 24" fill="white"><path d="M16 1H4c-1.1 0-2 .9-2 2v14h2V3h12V1zm3 4H8c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h11c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H8V7h11v14z"/></svg>''',
    'cut': '''<svg viewBox="0 0 24 24" fill="white"><path d="M9.64 7.64c.23-.5.36-1.05.36-1.64 0-2.21-1.79-4-4-4S2 3.79 2 6s1.79 4 4 4c.59 0 1.14-.13 1.64-.36L10 12l-2.36 2.36C7.14 14.13 6.59 14 6 14c-2.21 0-4 1.79-4 4s1.79 4 4 4 4-1.79 4-4c0-.59-.13-1.14-.36-1.64L12 14l7 7h3v-1L9.64 7.64zM6 8c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm0 12c-1.1 0-2-.89-2-2s.9-2 2-2 2 .89 2 2-.9 2-2 2zm6-7.5c-.28 0-.5-.22-.5-.5s.22-.5.5-.5.5.22.5.5-.22.5-.5.5zM19 3l-6 6 2 2 7-7V3z"/></svg>''',
    'sort_name': '''<svg viewBox="0 0 24 24" fill="white"><path d="M3 18h6v-2H3v2zM3 6v2h18V6H3zm0 7h12v-2H3v2z"/></svg>''',
    'sort_size': '''<svg viewBox="0 0 24 24" fill="white"><path d="M3 15h18v2H3v-2zm0 4h18v2H3v-2zm0-8h18v2H3v-2zm0-6v2h18V5H3z"/></svg>''',
    'rotate_left': '''<svg viewBox="0 0 24 24" fill="white"><path d="M7.11 8.53L5.7 7.11C4.8 8.27 4.24 9.61 4.07 11h2.02c.14-.87.49-1.72 1.02-2.47zM6.09 13H4.07c.17 1.39.72 2.73 1.62 3.89l1.41-1.42c-.52-.75-.87-1.59-1.01-2.47zm1.01 5.32c1.16.9 2.51 1.44 3.9 1.61V17.9c-.87-.15-1.71-.49-2.46-1.03L7.1 18.32zM13 4.07V1L8.45 5.55 13 10V6.09c2.84.48 5 2.94 5 5.91s-2.16 5.43-5 5.91v2.02c3.95-.49 7-3.85 7-7.93s-3.05-7.44-7-7.93z"/></svg>''',
    'rotate_right': '''<svg viewBox="0 0 24 24" fill="white"><path d="M15.55 5.55L11 1v3.07C7.06 4.56 4 7.92 4 12s3.05 7.44 7 7.93v-2.02c-2.84-.48-5-2.94-5-5.91s2.16-5.43 5-5.91V10l4.55-4.45zM19.93 11c-.17-1.39-.72-2.73-1.62-3.89l-1.42 1.42c.54.75.88 1.6 1.02 2.47h2.02zM13 17.9v2.02c1.39-.17 2.74-.71 3.9-1.61l-1.44-1.44c-.75.54-1.59.89-2.46 1.03zm3.89-2.42l1.42 1.41c.9-1.16 1.45-2.5 1.62-3.89h-2.02c-.14.87-.48 1.72-1.02 2.48z"/></svg>''',
    'zoom_in': '''<svg viewBox="0 0 24 24" fill="white"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zm2.5-4h-2v2H9v-2H7V9h2V7h1v2h2v1z"/></svg>''',
    'zoom_out': '''<svg viewBox="0 0 24 24" fill="white"><path d="M15.5 14h-.79l-.28-.27C15.41 12.59 16 11.11 16 9.5 16 5.91 13.09 3 9.5 3S3 5.91 3 9.5 5.91 16 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14zM7 9h5v1H7z"/></svg>''',
    'fit': '''<svg viewBox="0 0 24 24" fill="white"><path d="M9 11H7v2h2v-2zm4 0h-2v2h2v-2zm4 0h-2v2h2v-2zm2-7h-1V2h-2v2H8V2H6v2H5c-1.11 0-1.99.9-1.99 2L3 20c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"/></svg>''',
    'slideshow': '''<svg viewBox="0 0 24 24" fill="white"><path d="M10 8v8l5-4-5-4zm9-5H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V5h14v14z"/></svg>''',
}

def create_icon_from_svg(svg_string, size=24):
    """Crea un QIcon desde un string SVG"""
    renderer = QSvgRenderer(QByteArray(svg_string.encode()))
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter)
    painter.end()
    return QIcon(pixmap)

# -------- CONFIG --------
BG = "#0d0d0f"
IMAGES_DIR = r"C:\Users\Alonso\Desktop\ControCenter\Capturas"
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "photo_viewer_config.json")

# -------- VISOR DE FOTOS --------
class VisorFotos(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1200, 700)
        self.setWindowTitle("Visor de Fotos")
        self.setStyleSheet(f"background:{BG};")
        
        # Variables de imagen
        self.current_pixmap = None
        self.current_movie = None
        self.zoom_factor = 1.0
        self.rotation_angle = 0
        self.fit_to_window = True
        
        # Slideshow
        self.slideshow_active = False
        self.slideshow_timer = QTimer()
        self.slideshow_timer.timeout.connect(self.next_image)
        self.slideshow_interval = 3000
        
        # Layout principal
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Panel izquierdo (visor)
        left_panel = QWidget()
        dv = QVBoxLayout(left_panel)
        dv.setContentsMargins(20, 12, 20, 12)

        # Header
        header = QHBoxLayout()
        self.lbl_name = QLabel("Sin imagen")
        self.lbl_name.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.lbl_name.setStyleSheet("color:white;")
        header.addWidget(self.lbl_name)
        header.addStretch()
        
        dv.addLayout(header)
        
        # Notificación flotante
        self.notif_label = QLabel(self)
        self.notif_label.setStyleSheet("""
            background: #11998e;
            color: white;
            padding: 10px 15px;
            border-radius: 8px;
            font-size: 11px;
            font-weight: bold;
        """)
        self.notif_label.setAlignment(Qt.AlignCenter)
        self.notif_label.hide()
        self.notif_label.raise_()

        # Área de imagen con scroll
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setAlignment(Qt.AlignCenter)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background: #1c1c1e; }")
        # Ocultar scrollbars por defecto, solo mostrar cuando hay zoom
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background: #1c1c1e;")
        self.image_label.setScaledContents(False)
        self.image_label.setFocusPolicy(Qt.NoFocus)  # Asegurar que no capture el foco
        self.scroll_area.setWidget(self.image_label)
        
        dv.addWidget(self.scroll_area, stretch=1)

        # Cargar imágenes
        self.images = []
        self.original_images = []
        self.cargar_imagenes()
        self.image_index = 0
        self.shuffle_mode = False
        
        # Cargar configuración
        self.load_config()

        # Controles
        ctr = QHBoxLayout()
        
        # Botón anterior
        self.btn_prev = QPushButton()
        self.btn_prev.setIcon(create_icon_from_svg(ICONS['prev'], 20))
        self.btn_prev.setIconSize(QSize(20, 20))
        self.btn_prev.setFixedSize(44, 34)
        self.btn_prev.setFocusPolicy(Qt.NoFocus)
        self.btn_prev.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_prev.clicked.connect(self.prev_image)
        ctr.addWidget(self.btn_prev)
        ctr.addSpacing(8)
        
        # Botón siguiente
        self.btn_next = QPushButton()
        self.btn_next.setIcon(create_icon_from_svg(ICONS['next'], 20))
        self.btn_next.setIconSize(QSize(20, 20))
        self.btn_next.setFixedSize(44, 34)
        self.btn_next.setFocusPolicy(Qt.NoFocus)
        self.btn_next.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_next.clicked.connect(self.next_image)
        ctr.addWidget(self.btn_next)
        ctr.addSpacing(8)
        
        # Botón rotar izquierda
        self.btn_rotate_left = QPushButton()
        self.btn_rotate_left.setIcon(create_icon_from_svg(ICONS['rotate_left'], 20))
        self.btn_rotate_left.setIconSize(QSize(20, 20))
        self.btn_rotate_left.setFixedSize(44, 34)
        self.btn_rotate_left.setFocusPolicy(Qt.NoFocus)
        self.btn_rotate_left.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_rotate_left.clicked.connect(self.rotate_left)
        ctr.addWidget(self.btn_rotate_left)
        ctr.addSpacing(8)
        
        # Botón rotar derecha
        self.btn_rotate_right = QPushButton()
        self.btn_rotate_right.setIcon(create_icon_from_svg(ICONS['rotate_right'], 20))
        self.btn_rotate_right.setIconSize(QSize(20, 20))
        self.btn_rotate_right.setFixedSize(44, 34)
        self.btn_rotate_right.setFocusPolicy(Qt.NoFocus)
        self.btn_rotate_right.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_rotate_right.clicked.connect(self.rotate_right)
        ctr.addWidget(self.btn_rotate_right)
        ctr.addSpacing(8)
        
        # Botón zoom in
        self.btn_zoom_in = QPushButton()
        self.btn_zoom_in.setIcon(create_icon_from_svg(ICONS['zoom_in'], 20))
        self.btn_zoom_in.setIconSize(QSize(20, 20))
        self.btn_zoom_in.setFixedSize(44, 34)
        self.btn_zoom_in.setFocusPolicy(Qt.NoFocus)
        self.btn_zoom_in.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        ctr.addWidget(self.btn_zoom_in)
        ctr.addSpacing(8)
        
        # Botón zoom out
        self.btn_zoom_out = QPushButton()
        self.btn_zoom_out.setIcon(create_icon_from_svg(ICONS['zoom_out'], 20))
        self.btn_zoom_out.setIconSize(QSize(20, 20))
        self.btn_zoom_out.setFixedSize(44, 34)
        self.btn_zoom_out.setFocusPolicy(Qt.NoFocus)
        self.btn_zoom_out.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        ctr.addWidget(self.btn_zoom_out)
        ctr.addSpacing(8)
        
        # Botón ajustar a ventana
        self.btn_fit = QPushButton()
        self.btn_fit.setIcon(create_icon_from_svg(ICONS['fit'], 20))
        self.btn_fit.setIconSize(QSize(20, 20))
        self.btn_fit.setFixedSize(44, 34)
        self.btn_fit.setCheckable(True)
        self.btn_fit.setChecked(True)
        self.btn_fit.setFocusPolicy(Qt.NoFocus)
        self.btn_fit.setStyleSheet("""
            QPushButton {background:#1c1c1e;border-radius:10px;}
            QPushButton:checked {background:#36d1dc;}
        """)
        self.btn_fit.clicked.connect(self.toggle_fit)
        ctr.addWidget(self.btn_fit)
        ctr.addSpacing(8)
        
        # Botón info
        self.btn_info = QPushButton()
        self.btn_info.setIcon(create_icon_from_svg(ICONS['info'], 20))
        self.btn_info.setIconSize(QSize(20, 20))
        self.btn_info.setFixedSize(44, 34)
        self.btn_info.setFocusPolicy(Qt.NoFocus)
        self.btn_info.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_info.clicked.connect(self.show_image_info)
        ctr.addWidget(self.btn_info)
        ctr.addSpacing(8)
        
        # Botón copiar
        self.btn_copy = QPushButton()
        self.btn_copy.setIcon(create_icon_from_svg(ICONS['copy'], 20))
        self.btn_copy.setIconSize(QSize(20, 20))
        self.btn_copy.setFixedSize(44, 34)
        self.btn_copy.setFocusPolicy(Qt.NoFocus)
        self.btn_copy.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_copy.clicked.connect(self.copy_image_path)
        ctr.addWidget(self.btn_copy)
        ctr.addSpacing(8)
        
        # Botón cortar
        self.btn_cut = QPushButton()
        self.btn_cut.setIcon(create_icon_from_svg(ICONS['cut'], 20))
        self.btn_cut.setIconSize(QSize(20, 20))
        self.btn_cut.setFixedSize(44, 34)
        self.btn_cut.setFocusPolicy(Qt.NoFocus)
        self.btn_cut.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_cut.clicked.connect(self.cut_image)
        ctr.addWidget(self.btn_cut)
        ctr.addSpacing(8)
        
        # Botón shuffle
        self.btn_shuffle = QPushButton()
        self.btn_shuffle.setIcon(create_icon_from_svg(ICONS['shuffle'], 20))
        self.btn_shuffle.setIconSize(QSize(20, 20))
        self.btn_shuffle.setFixedSize(44, 34)
        self.btn_shuffle.setCheckable(True)
        self.btn_shuffle.setFocusPolicy(Qt.NoFocus)
        self.btn_shuffle.setStyleSheet("""
            QPushButton {background:#1c1c1e;border-radius:10px;}
            QPushButton:checked {background:#11998e;}
        """)
        self.btn_shuffle.clicked.connect(self.toggle_shuffle)
        ctr.addWidget(self.btn_shuffle)
        ctr.addSpacing(8)
        
        # Botón slideshow
        self.btn_slideshow = QPushButton()
        self.btn_slideshow.setIcon(create_icon_from_svg(ICONS['slideshow'], 20))
        self.btn_slideshow.setIconSize(QSize(20, 20))
        self.btn_slideshow.setFixedSize(44, 34)
        self.btn_slideshow.setCheckable(True)
        self.btn_slideshow.setFocusPolicy(Qt.NoFocus)
        self.btn_slideshow.setStyleSheet("""
            QPushButton {background:#1c1c1e;border-radius:10px;}
            QPushButton:checked {background:#ee0979;}
        """)
        self.btn_slideshow.clicked.connect(self.toggle_slideshow)
        ctr.addWidget(self.btn_slideshow)
        ctr.addSpacing(8)
        
        # Botón delete
        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(create_icon_from_svg(ICONS['delete'].replace('fill="white"', 'fill="#ff4444"'), 20))
        self.btn_delete.setIconSize(QSize(20, 20))
        self.btn_delete.setFixedSize(44, 34)
        self.btn_delete.setFocusPolicy(Qt.NoFocus)
        self.btn_delete.setStyleSheet("background:#1c1c1e;border-radius:10px;")
        self.btn_delete.clicked.connect(self.delete_image)
        ctr.addWidget(self.btn_delete)
        ctr.addSpacing(8)
        
        # Tamaño de imagen
        self.btn_size = QPushButton("---")
        self.btn_size.setFixedSize(80, 34)
        self.btn_size.setFocusPolicy(Qt.NoFocus)
        self.btn_size.setStyleSheet("background:#1c1c1e;color:#aaaaaa;border-radius:10px;font-size:9px;font-weight:bold;")
        self.btn_size.setEnabled(False)
        ctr.addWidget(self.btn_size)
        ctr.addSpacing(8)
        
        # Botón playlist
        self.btn_playlist = QPushButton()
        self.btn_playlist.setIcon(create_icon_from_svg(ICONS['playlist'], 20))
        self.btn_playlist.setIconSize(QSize(20, 20))
        self.btn_playlist.setFixedSize(44, 34)
        self.btn_playlist.setCheckable(True)
        self.btn_playlist.setFocusPolicy(Qt.NoFocus)
        self.btn_playlist.setStyleSheet("""
            QPushButton {background:#1c1c1e;border-radius:10px;}
            QPushButton:checked {background:#5b86e5;}
        """)
        self.btn_playlist.clicked.connect(self.toggle_playlist)
        ctr.addWidget(self.btn_playlist)
        
        ctr.addStretch()
        
        dv.addLayout(ctr)

        # Playlist
        playlist_container = QWidget()
        playlist_container.setFixedWidth(250)
        playlist_container.hide()
        playlist_layout = QVBoxLayout(playlist_container)
        playlist_layout.setContentsMargins(0, 0, 0, 0)
        
        # Toolbar playlist
        toolbar = QWidget()
        toolbar.setFixedHeight(40)
        toolbar.setStyleSheet("background:#2c2c2e;")
        toolbar_layout = QHBoxLayout(toolbar)
        
        btn_sort_name = QPushButton("Nombre")
        btn_sort_name.setIcon(create_icon_from_svg(ICONS['sort_name'], 14))
        btn_sort_name.setIconSize(QSize(14, 14))
        btn_sort_name.setFixedHeight(30)
        btn_sort_name.setStyleSheet("background:#3c3c3e;color:#cccccc;border-radius:5px;padding:0 10px;")
        btn_sort_name.clicked.connect(lambda: self.ordenar_playlist('nombre'))
        toolbar_layout.addWidget(btn_sort_name)
        
        btn_sort_size = QPushButton("Tamaño")
        btn_sort_size.setIcon(create_icon_from_svg(ICONS['sort_size'], 14))
        btn_sort_size.setIconSize(QSize(14, 14))
        btn_sort_size.setFixedHeight(30)
        btn_sort_size.setStyleSheet("background:#3c3c3e;color:#cccccc;border-radius:5px;padding:0 10px;")
        btn_sort_size.clicked.connect(lambda: self.ordenar_playlist('tamaño'))
        toolbar_layout.addWidget(btn_sort_size)
        
        playlist_layout.addWidget(toolbar)
        
        self.playlist_widget = QListWidget()
        self.playlist_widget.setStyleSheet("""
            QListWidget {
                background: #1c1c1e;
                color: white;
                padding: 10px;
                font-size: 12px;
                border: none;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 5px;
            }
            QListWidget::item:hover {
                background: #2c2c2e;
            }
            QListWidget::item:selected {
                background: #2c2c2e;
                border-left: 3px solid #36d1dc;
            }
        """)
        self.playlist_widget.itemClicked.connect(self.select_from_playlist)
        playlist_layout.addWidget(self.playlist_widget)
        
        self.playlist_container = playlist_container
        
        main_layout.addWidget(left_panel)
        main_layout.addWidget(playlist_container)
        
        # Asegurar que la ventana principal capture el foco y los eventos de teclado
        self.setFocusPolicy(Qt.StrongFocus)
        
        # Cargar primera imagen
        if self.images:
            self.cargar_imagen(0)

    def cargar_imagenes(self):
        """Carga todas las imágenes de la carpeta especificada"""
        if not os.path.exists(IMAGES_DIR):
            print(f"La carpeta {IMAGES_DIR} no existe. Creándola...")
            try:
                os.makedirs(IMAGES_DIR)
            except Exception as e:
                print(f"Error al crear la carpeta: {e}")
        
        if os.path.exists(IMAGES_DIR):
            extensiones = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff', '.svg')
            try:
                archivos = os.listdir(IMAGES_DIR)
                self.images = [
                    os.path.join(IMAGES_DIR, f)
                    for f in archivos
                    if f.lower().endswith(extensiones)
                ]
                self.original_images = self.images.copy()
                print(f"Se cargaron {len(self.images)} imágenes desde {IMAGES_DIR}")
            except Exception as e:
                print(f"Error al leer la carpeta: {e}")
                self.images = []
                self.original_images = []
        else:
            self.images = []
            self.original_images = []
            print("No se pudo acceder a la carpeta de imágenes")

    def cargar_imagen(self, idx):
        """Carga y muestra una imagen"""
        if not self.images or idx >= len(self.images):
            return
        
        self.image_index = idx
        path = self.images[self.image_index]
        
        # Detener animación previa
        if self.current_movie:
            self.current_movie.stop()
            self.current_movie.deleteLater()
            self.current_movie = None
        
        # Resetear transformaciones
        self.zoom_factor = 1.0
        self.rotation_angle = 0
        
        # Verificar si es imagen animada
        if path.lower().endswith(('.gif', '.webp')):
            movie = QMovie(path)
            if movie.isValid() and movie.frameCount() > 1:
                self.current_movie = movie
                self.image_label.setMovie(self.current_movie)
                self.current_movie.start()
                self.current_pixmap = None
            else:
                self.load_static_image(path)
        else:
            self.load_static_image(path)
        
        self.lbl_name.setText(os.path.basename(path))
        self.actualizar_tamano_imagen(path)
        self.actualizar_playlist()
    
    def load_static_image(self, path):
        """Carga una imagen estática"""
        self.current_pixmap = QPixmap(path)
        if not self.current_pixmap.isNull():
            self.display_image()
        else:
            self.image_label.setText("Error al cargar imagen")
            self.image_label.setStyleSheet("color:white;font-size:14px;")
    
    def display_image(self):
        """Muestra la imagen con las transformaciones aplicadas"""
        if not self.current_pixmap:
            return
        
        # Aplicar rotación
        transform = QTransform().rotate(self.rotation_angle)
        rotated = self.current_pixmap.transformed(transform, Qt.SmoothTransformation)
        
        # Aplicar zoom
        if self.fit_to_window:
            # Ajustar a ventana - sin scrollbars
            available_size = self.scroll_area.viewport().size()
            # Reducir un poco para evitar scrollbars innecesarias
            available_size.setWidth(available_size.width() - 2)
            available_size.setHeight(available_size.height() - 2)
            
            scaled = rotated.scaled(
                available_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
            # Ocultar scrollbars cuando está ajustado a ventana
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        else:
            # Zoom manual - mostrar scrollbars si es necesario
            new_size = rotated.size() * self.zoom_factor
            scaled = rotated.scaled(new_size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            # Mostrar scrollbars solo cuando hay zoom
            self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        self.image_label.setPixmap(scaled)
    
    def show_notification(self, message):
        """Muestra notificación en esquina superior derecha"""
        self.notif_label.setText(message)
        notif_width = 250
        notif_height = 60
        x = self.width() - notif_width - 20
        y = 20
        self.notif_label.setGeometry(x, y, notif_width, notif_height)
        self.notif_label.show()
        self.notif_label.raise_()
        QTimer.singleShot(2000, self.notif_label.hide)
    
    def actualizar_tamano_imagen(self, path):
        """Actualiza el botón de tamaño"""
        try:
            size_bytes = os.path.getsize(path)
            size_mb = size_bytes / (1024 * 1024)
            if size_mb >= 1:
                self.btn_size.setText(f"{size_mb:.1f} MB")
            else:
                size_kb = size_bytes / 1024
                self.btn_size.setText(f"{size_kb:.1f} KB")
        except:
            self.btn_size.setText("--- KB")

    def show_image_info(self):
        """Muestra información de la imagen"""
        if not self.images or self.image_index >= len(self.images):
            return
        
        image_path = self.images[self.image_index]
        size_bytes = os.path.getsize(image_path)
        size_mb = size_bytes / (1024 * 1024)
        size_kb = size_bytes / 1024
        
        if self.current_pixmap and not self.current_pixmap.isNull():
            width = self.current_pixmap.width()
            height = self.current_pixmap.height()
            dimensions = f"{width} x {height} px"
        else:
            dimensions = "N/A"
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Información de la Imagen")
        dialog.setMinimumSize(450, 320)
        dialog.setStyleSheet("background:#1c1c1e;color:white;")
        
        layout = QVBoxLayout(dialog)
        
        text = QTextEdit()
        text.setReadOnly(True)
        text.setStyleSheet("background:#2c2c2e;color:white;border:none;padding:10px;")
        
        size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{size_kb:.2f} KB"
        
        info_text = f"""
<b>Nombre:</b> {os.path.basename(image_path)}<br>
<b>Ubicación:</b> {os.path.dirname(image_path)}<br>
<b>Tamaño:</b> {size_str}<br>
<b>Dimensiones:</b> {dimensions}<br>
<b>Formato:</b> {os.path.splitext(image_path)[1].upper()}<br>
        """
        
        text.setHtml(info_text)
        layout.addWidget(text)
        
        close_btn = QPushButton("Cerrar")
        close_btn.clicked.connect(dialog.close)
        close_btn.setStyleSheet("background:#36d1dc;color:white;padding:8px;border-radius:5px;")
        layout.addWidget(close_btn)
        
        dialog.exec()

    def actualizar_playlist(self):
        """Actualiza la playlist"""
        self.playlist_widget.clear()
        for i, image in enumerate(self.images):
            nombre = os.path.splitext(os.path.basename(image))[0]
            item = QListWidgetItem(f"{i + 1}. {nombre}")
            
            if i == self.image_index:
                item.setForeground(QColor("#ffffff"))
                font = item.font()
                font.setBold(True)
                item.setFont(font)
            
            self.playlist_widget.addItem(item)
        
        if 0 <= self.image_index < self.playlist_widget.count():
            self.playlist_widget.setCurrentRow(self.image_index)

    def toggle_playlist(self):
        """Muestra/oculta playlist"""
        if self.playlist_container.isVisible():
            self.playlist_container.hide()
            self.btn_playlist.setChecked(False)
        else:
            self.actualizar_playlist()
            self.playlist_container.show()
            self.btn_playlist.setChecked(True)

    def ordenar_playlist(self, criterio):
        """Ordena la playlist"""
        if not self.images:
            return
        
        current_image = self.images[self.image_index] if self.images else None
        
        if criterio == 'nombre':
            self.images.sort(key=lambda x: os.path.basename(x).lower())
        elif criterio == 'tamaño':
            self.images.sort(key=lambda x: os.path.getsize(x) if os.path.exists(x) else 0, reverse=True)
        
        self.original_images = self.images.copy()
        
        if current_image and current_image in self.images:
            self.image_index = self.images.index(current_image)
        else:
            self.image_index = 0
        
        self.actualizar_playlist()
        self.cargar_imagen(self.image_index)

    def select_from_playlist(self, item):
        """Selecciona imagen desde playlist"""
        index = self.playlist_widget.row(item)
        if 0 <= index < len(self.images):
            self.cargar_imagen(index)

    def next_image(self):
        """Siguiente imagen"""
        if not self.images:
            return
        
        if len(self.images) == 1:
            self.image_index = 0
        elif self.shuffle_mode:
            available = [i for i in range(len(self.images)) if i != self.image_index]
            if available:
                self.image_index = random.choice(available)
        else:
            self.image_index = (self.image_index + 1) % len(self.images)
        
        self.cargar_imagen(self.image_index)
    
    def prev_image(self):
        """Imagen anterior"""
        if not self.images:
            return
        
        if len(self.images) == 1:
            self.image_index = 0
        elif self.shuffle_mode:
            available = [i for i in range(len(self.images)) if i != self.image_index]
            if available:
                self.image_index = random.choice(available)
        else:
            self.image_index = (self.image_index - 1) % len(self.images)
        
        self.cargar_imagen(self.image_index)
    
    def toggle_shuffle(self):
        """Toggle shuffle"""
        self.shuffle_mode = self.btn_shuffle.isChecked()
        
        if self.shuffle_mode:
            current_image = self.images[self.image_index] if self.images else None
            self.images = self.original_images.copy()
            random.shuffle(self.images)
            if current_image and current_image in self.images:
                self.image_index = self.images.index(current_image)
        else:
            current_image = self.images[self.image_index] if self.images else None
            self.images = self.original_images.copy()
            if current_image and current_image in self.images:
                self.image_index = self.images.index(current_image)
        
        self.actualizar_playlist()
    
    def toggle_slideshow(self):
        """Toggle slideshow"""
        self.slideshow_active = self.btn_slideshow.isChecked()
        
        if self.slideshow_active:
            self.slideshow_timer.start(self.slideshow_interval)
        else:
            self.slideshow_timer.stop()
    
    def rotate_left(self):
        """Rotar izquierda"""
        if not self.current_pixmap:
            return
        self.rotation_angle = (self.rotation_angle - 90) % 360
        self.display_image()
    
    def rotate_right(self):
        """Rotar derecha"""
        if not self.current_pixmap:
            return
        self.rotation_angle = (self.rotation_angle + 90) % 360
        self.display_image()
    
    def zoom_in(self):
        """Aumentar zoom"""
        if self.fit_to_window:
            self.fit_to_window = False
            self.btn_fit.setChecked(False)
        
        self.zoom_factor = min(5.0, self.zoom_factor + 0.25)
        self.display_image()
    
    def zoom_out(self):
        """Reducir zoom"""
        if self.fit_to_window:
            self.fit_to_window = False
            self.btn_fit.setChecked(False)
        
        self.zoom_factor = max(0.1, self.zoom_factor - 0.25)
        self.display_image()
    
    def toggle_fit(self):
        """Toggle ajustar a ventana"""
        self.fit_to_window = self.btn_fit.isChecked()
        if self.fit_to_window:
            self.zoom_factor = 1.0
        self.display_image()
    
    def delete_image(self):
        """Eliminar imagen"""
        if not self.images or self.image_index >= len(self.images):
            return
        
        current_path = self.images[self.image_index]
        
        if self.current_movie:
            self.current_movie.stop()
            self.current_movie.deleteLater()
            self.current_movie = None
        
        QTimer.singleShot(200, lambda: self.eliminar_archivo(current_path))

    def eliminar_archivo(self, path):
        """Elimina archivo físicamente"""
        try:
            if os.path.exists(path):
                os.remove(path)
            
            if path in self.images:
                self.images.remove(path)
            if path in self.original_images:
                self.original_images.remove(path)
            
            self.actualizar_playlist()
            self.show_notification("✓ Imagen eliminada")
            
            if self.images:
                if self.image_index >= len(self.images):
                    self.image_index = 0
                QTimer.singleShot(300, lambda: self.cargar_imagen(self.image_index))
            else:
                self.lbl_name.setText("No hay más imágenes")
                self.image_label.clear()
                self.image_label.setText("No hay imágenes")
        except Exception as e:
            print(f"Error al eliminar: {e}")
            self.show_notification("✗ Error al eliminar")
    
    def copy_image_path(self):
        """Copiar imagen al portapapeles"""
        if not self.images or self.image_index >= len(self.images):
            return
        
        image_path = self.images[self.image_index]
        
        # Copiar la imagen al portapapeles usando QImage
        clipboard = QApplication.clipboard()
        image = QPixmap(image_path).toImage()
        
        if not image.isNull():
            clipboard.setImage(image)
            
            # Feedback visual
            original_style = self.btn_copy.styleSheet()
            self.btn_copy.setStyleSheet("background:#36d1dc;border-radius:10px;")
            QTimer.singleShot(200, lambda: self.btn_copy.setStyleSheet(original_style))
            
            self.show_notification("✓ Imagen copiada")
        else:
            self.show_notification("✗ Error al copiar")
    
    def cut_image(self):
        """Cortar imagen (copiar y marcar para eliminar)"""
        if not self.images or self.image_index >= len(self.images):
            return
        
        image_path = self.images[self.image_index]
        
        # Copiar la imagen al portapapeles usando QImage
        clipboard = QApplication.clipboard()
        image = QPixmap(image_path).toImage()
        
        if not image.isNull():
            clipboard.setImage(image)
            
            # Feedback visual
            original_style = self.btn_cut.styleSheet()
            self.btn_cut.setStyleSheet("background:#ee0979;border-radius:10px;")
            QTimer.singleShot(200, lambda: self.btn_cut.setStyleSheet(original_style))
            
            self.show_notification("✓ Imagen cortada")
        else:
            self.show_notification("✗ Error al cortar")

    def load_config(self):
        """Cargar configuración"""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.slideshow_interval = config.get('slideshow_interval', 3000)
        except Exception as e:
            print(f"Error cargando config: {e}")
            self.slideshow_interval = 3000
    
    def save_config(self):
        """Guardar configuración"""
        try:
            config = {
                'slideshow_interval': self.slideshow_interval
            }
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"Error guardando config: {e}")
    
    def closeEvent(self, event):
        """Al cerrar"""
        self.save_config()
        if self.current_movie:
            self.current_movie.stop()
        event.accept()
    
    def resizeEvent(self, event):
        """Al redimensionar"""
        super().resizeEvent(event)
        if self.fit_to_window and self.current_pixmap:
            QTimer.singleShot(10, self.display_image)
    
    def keyPressEvent(self, event):
        """Eventos de teclado"""
        # Flechas izquierda/derecha para navegar entre imágenes
        if event.key() == Qt.Key_Left:
            self.prev_image()
            event.accept()
        elif event.key() == Qt.Key_Right:
            self.next_image()
            event.accept()
        # Flechas arriba/abajo para zoom
        elif event.key() == Qt.Key_Up:
            self.zoom_in()
            event.accept()
        elif event.key() == Qt.Key_Down:
            self.zoom_out()
            event.accept()
        # Otros atajos
        elif event.key() == Qt.Key_Plus or event.key() == Qt.Key_Equal:
            self.zoom_in()
            event.accept()
        elif event.key() == Qt.Key_Minus:
            self.zoom_out()
            event.accept()
        elif event.key() == Qt.Key_Space:
            self.toggle_slideshow()
            event.accept()
        elif event.key() == Qt.Key_R:
            self.rotate_right()
            event.accept()
        elif event.key() == Qt.Key_Delete:
            self.delete_image()
            event.accept()
        else:
            super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    visor = VisorFotos()
    visor.show()
    sys.exit(app.exec())