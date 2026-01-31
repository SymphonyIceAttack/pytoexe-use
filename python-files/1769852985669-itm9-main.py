import cv2
import numpy as np
import tkinter as tk
from tkinter import filedialog, ttk
import threading
import queue
import os
import random

class ObjectASCIIVideoGUI:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Object-Filling ASCII Video Converter")
        self.root.geometry("1400x900")
        
        # Настройки
        self.width = 100
        self.contrast = 1.0
        self.brightness = 0
        self.mode = "adaptive"
        self.invert_colors = False  # Инверсия только символов
        
        # Параметры для заполнения объектов
        self.fill_objects = True
        self.min_object_size = 10
        self.edge_detection = True
        self.last_num_objects = 0
        
        # Наборы символов
        self.setup_characters()
        
        # Переменные
        self.video_source = None
        self.cap = None
        self.playing = False
        self.current_frame = None
        self.frame_queue = queue.Queue(maxsize=1)
        self.update_thread = None
        
        # Создаем GUI
        self.setup_gui()
        
    def setup_characters(self):
        """Наборы символов для разных режимов"""
        # Один набор символов для обоих режимов
        # Инверсия будет достигаться логикой выбора символов, а не разными наборами
        self.fill_chars = [' ', '░', '▒', '▓', '█']
        self.edge_chars = ['·', '+', 'x', 'X', '#']
        
        self.ascii_fill = [' ', '.', ':', 'o', 'O', '0', '@']
        self.ascii_edge = ['.', ',', '+', '*', 'x', 'X', '#']
        
        self.unicode_detailed = [' ', '▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
    def setup_gui(self):
        """Настройка интерфейса"""
        control_frame = tk.Frame(self.root)
        control_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=5)
        
        display_frame = tk.Frame(self.root)
        display_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Левая часть: настройки и предпросмотр
        left_frame = tk.Frame(display_frame, width=450)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)
        
        # Фрейм для инверсии
        invert_frame = tk.LabelFrame(left_frame, text="ИНВЕРСИЯ СИМВОЛОВ", 
                                   font=("Arial", 10, "bold"), fg="purple")
        invert_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Кнопка инверсии
        self.invert_button = tk.Button(invert_frame, text="⚫ Инвертировать символы", 
                                      command=self.toggle_invert, width=22,
                                      bg="lightgray", activebackground="gray")
        self.invert_button.pack(pady=5)
        
        # Индикатор и объяснение
        self.invert_status = tk.Label(invert_frame, text="Режим: Обычный\n(темные пиксели → темные символы)", 
                                     font=("Arial", 9), justify=tk.LEFT)
        self.invert_status.pack(pady=2)
        
        # Настройки заполнения объектов
        tk.Label(left_frame, text="НАСТРОЙКИ ЗАПОЛНЕНИЯ ОБЪЕКТОВ", 
                font=("Arial", 12, "bold"), fg="blue").pack(pady=5)
        
        fill_frame = tk.Frame(left_frame, relief=tk.RIDGE, borderwidth=2)
        fill_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Включение/выключение заполнения
        self.fill_var = tk.BooleanVar(value=True)
        tk.Checkbutton(fill_frame, text="Заполнять объекты", 
                      variable=self.fill_var,
                      command=self.toggle_fill).pack(anchor=tk.W, padx=5, pady=2)
        
        # Детектирование краев
        self.edge_var = tk.BooleanVar(value=True)
        tk.Checkbutton(fill_frame, text="Детектировать края", 
                      variable=self.edge_var,
                      command=self.toggle_edges).pack(anchor=tk.W, padx=5, pady=2)
        
        # Минимальный размер объекта
        tk.Label(fill_frame, text="Мин. размер объекта:").pack(anchor=tk.W, padx=5, pady=2)
        self.size_scale = tk.Scale(fill_frame, from_=5, to=100, 
                                  orient=tk.HORIZONTAL, length=200)
        self.size_scale.set(self.min_object_size)
        self.size_scale.pack(anchor=tk.W, padx=5, pady=2)
        
        # Тип заполнения
        tk.Label(fill_frame, text="Тип заполнения:").pack(anchor=tk.W, padx=5, pady=2)
        self.fill_type_var = tk.StringVar(value="solid")
        
        fill_types = [
            ("Сплошное", "solid"),
            ("Градиентное", "gradient"),
            ("Текстурированное", "texture"),
            ("Контуры", "contour")
        ]
        
        for text, ftype in fill_types:
            tk.Radiobutton(fill_frame, text=text, variable=self.fill_type_var, 
                          value=ftype).pack(anchor=tk.W, padx=20)
        
        # Предпросмотр обработки
        tk.Label(left_frame, text="ПРЕДПРОСМОТР ОБРАБОТКИ", 
                font=("Arial", 11), fg="green").pack(pady=(10, 5))
        
        preview_frame = tk.Frame(left_frame)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.preview_text1 = tk.Text(preview_frame, height=8, width=40,
                                    font=("Courier", 6), bg="white", fg="black")
        self.preview_text1.pack(fill=tk.X, pady=2)
        
        tk.Label(preview_frame, text="Оригинал").pack()
        
        self.preview_text2 = tk.Text(preview_frame, height=8, width=40,
                                    font=("Courier", 6), bg="white", fg="black")
        self.preview_text2.pack(fill=tk.X, pady=2)
        
        tk.Label(preview_frame, text="Контуры").pack()
        
        self.preview_text3 = tk.Text(preview_frame, height=8, width=40,
                                    font=("Courier", 6), bg="white", fg="black")
        self.preview_text3.pack(fill=tk.X, pady=2)
        
        tk.Label(preview_frame, text="Заполнение").pack()
        
        # Правая часть: основной ASCII вывод
        right_frame = tk.Frame(display_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        tk.Label(right_frame, text="ASCII ВИДЕО С ЗАПОЛНЕНИЕМ ОБЪЕКТОВ", 
                font=("Arial", 12, "bold"), fg="red").pack(pady=5)
        
        # Информационная панель
        info_frame = tk.Frame(right_frame)
        info_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.info_label = tk.Label(info_frame, 
                                  text="Режим: Заполнение объектов | Контуры: Вкл",
                                  font=("Arial", 10))
        self.info_label.pack()
        
        # Текстовый виджет для ASCII (фон всегда белый)
        text_frame = tk.Frame(right_frame, relief=tk.SUNKEN, borderwidth=2)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        v_scrollbar = tk.Scrollbar(text_frame)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        h_scrollbar = tk.Scrollbar(text_frame, orient=tk.HORIZONTAL)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.ascii_text = tk.Text(
            text_frame, 
            bg="white",  # Фон всегда белый
            fg="black",  # Текст всегда черный
            font=("Courier New", 7),
            yscrollcommand=v_scrollbar.set,
            xscrollcommand=h_scrollbar.set,
            wrap=tk.NONE,
            state=tk.NORMAL
        )
        self.ascii_text.pack(fill=tk.BOTH, expand=True)
        
        v_scrollbar.config(command=self.ascii_text.yview)
        h_scrollbar.config(command=self.ascii_text.xview)
        
        # Панель управления
        self.create_control_panel(control_frame)
        
        # Статус бар
        self.status_bar = tk.Label(self.root, text="Готово к работе", 
                                 bd=1, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
    
    def create_control_panel(self, parent):
        """Создание панели управления"""
        # Кнопки выбора источника
        source_frame = tk.LabelFrame(parent, text="Источник", padx=10, pady=5)
        source_frame.pack(side=tk.LEFT, padx=5)
        
        tk.Button(source_frame, text="📷 Веб-камера", command=self.use_camera, 
                 width=15).pack(side=tk.LEFT, padx=5)
        tk.Button(source_frame, text="📁 Видеофайл", command=self.select_file, 
                 width=15).pack(side=tk.LEFT, padx=5)
        
        # Кнопки управления
        control_frame = tk.LabelFrame(parent, text="Управление", padx=10, pady=5)
        control_frame.pack(side=tk.LEFT, padx=5)
        
        self.play_button = tk.Button(control_frame, text="▶ Воспроизвести", 
                                    command=self.toggle_play, width=15)
        self.play_button.pack(side=tk.LEFT, padx=5)
        
        tk.Button(control_frame, text="⏸ Пауза", command=self.pause, 
                 width=10).pack(side=tk.LEFT, padx=5)
        tk.Button(control_frame, text="⏹ Стоп", command=self.stop, 
                 width=10).pack(side=tk.LEFT, padx=5)
        
        # Настройки изображения
        settings_frame = tk.LabelFrame(parent, text="Настройки", padx=10, pady=5)
        settings_frame.pack(side=tk.LEFT, padx=5)
        
        # Порог бинаризации
        tk.Label(settings_frame, text="Порог (0-255):").pack(anchor=tk.W)
        self.threshold_scale = tk.Scale(settings_frame, from_=0, to=255, 
                                       orient=tk.HORIZONTAL, length=150)
        self.threshold_scale.set(128)
        self.threshold_scale.pack(anchor=tk.W)
        
        # Ширина
        tk.Label(settings_frame, text="Ширина ASCII:").pack(anchor=tk.W)
        self.width_scale = tk.Scale(settings_frame, from_=60, to=200, 
                                   orient=tk.HORIZONTAL, length=150,
                                   command=self.update_width)
        self.width_scale.set(self.width)
        self.width_scale.pack(anchor=tk.W)
        
        # Контраст
        tk.Label(settings_frame, text="Контраст:").pack(anchor=tk.W)
        self.contrast_scale = tk.Scale(settings_frame, from_=0.5, to=2.0,
                                      orient=tk.HORIZONTAL, length=150,
                                      resolution=0.1, command=self.update_contrast)
        self.contrast_scale.set(self.contrast)
        self.contrast_scale.pack(anchor=tk.W)
        
        # Режимы символов
        mode_frame = tk.LabelFrame(parent, text="Символы", padx=10, pady=5)
        mode_frame.pack(side=tk.LEFT, padx=5)
        
        self.mode_var = tk.StringVar(value="adaptive")
        
        modes = [
            ("Заполнение Unicode", "adaptive"),
            ("Заполнение ASCII", "ascii"),
            ("Детализированный", "detailed"),
            ("Контуры только", "edges_only")
        ]
        
        for text, mode in modes:
            tk.Radiobutton(mode_frame, text=text, variable=self.mode_var, 
                          value=mode, command=self.update_mode).pack(anchor=tk.W)
    
    def toggle_invert(self):
        """Переключение инверсии символов (НЕ изображения!)"""
        self.invert_colors = not self.invert_colors
        
        # Обновляем кнопку и статус
        if self.invert_colors:
            self.invert_button.config(text="⚪ Обычный режим", bg="black", fg="white")
            self.invert_status.config(
                text="Режим: ИНВЕРТИРОВАННЫЙ\n(светлые пиксели → темные символы)",
                fg="red"
            )
        else:
            self.invert_button.config(text="⚫ Инвертировать символы", bg="lightgray", fg="black")
            self.invert_status.config(
                text="Режим: Обычный\n(темные пиксели → темные символы)",
                fg="green"
            )
        
        # Обновляем отображение если есть текущий кадр
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def toggle_fill(self):
        self.fill_objects = self.fill_var.get()
        self.update_info_label()
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def toggle_edges(self):
        self.edge_detection = self.edge_var.get()
        self.update_info_label()
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def update_info_label(self):
        fill_status = "Вкл" if self.fill_objects else "Выкл"
        edge_status = "Вкл" if self.edge_detection else "Выкл"
        invert_status = "Вкл" if self.invert_colors else "Выкл"
        self.info_label.config(
            text=f"Заполнение: {fill_status} | Контуры: {edge_status} | Инверсия: {invert_status}"
        )
    
    def update_mode(self):
        self.mode = self.mode_var.get()
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def update_width(self, value):
        self.width = int(value)
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def update_contrast(self, value):
        self.contrast = float(value)
        if self.current_frame is not None:
            self.process_and_display_frame(self.current_frame)
    
    def select_file(self):
        filename = filedialog.askopenfilename(
            title="Выберите видеофайл",
            filetypes=[("Видео файлы", "*.mp4 *.avi *.mov *.mkv *.flv *.wmv")]
        )
        
        if filename:
            self.stop()
            self.video_source = filename
            self.status_bar.config(text=f"Файл: {os.path.basename(filename)}")
            
            self.cap = cv2.VideoCapture(filename)
            if self.cap.isOpened():
                self.play_button.config(state=tk.NORMAL)
                self.show_first_frame()
    
    def use_camera(self):
        self.stop()
        self.video_source = 0
        self.status_bar.config(text="Веб-камера")
        
        self.cap = cv2.VideoCapture(0)
        if self.cap.isOpened():
            self.play_button.config(state=tk.NORMAL)
            self.show_first_frame()
        else:
            self.status_bar.config(text="Ошибка: не удалось открыть камеру")
    
    def show_first_frame(self):
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                self.process_and_display_frame(frame)
    
    def detect_objects(self, binary_image):
        """Обнаружение объектов на бинарном изображении"""
        contours, _ = cv2.findContours(binary_image, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        object_mask = np.zeros_like(binary_image)
        edge_mask = np.zeros_like(binary_image)
        
        min_size = self.size_scale.get()
        large_contours = []
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > min_size:
                large_contours.append(contour)
                cv2.drawContours(object_mask, [contour], -1, 255, thickness=cv2.FILLED)
                cv2.drawContours(edge_mask, [contour], -1, 255, thickness=2)
        
        return object_mask, edge_mask, len(large_contours)
    
    def fill_object_interior(self, gray_image, object_mask, fill_type="solid"):
        """Заполнение внутренней части объектов"""
        if not self.fill_objects:
            return gray_image.copy()
            
        object_area = object_mask > 0
        
        if not np.any(object_area):
            return gray_image.copy()
        
        filled = gray_image.copy()
        
        if fill_type == "solid":
            object_pixels = gray_image[object_area]
            if len(object_pixels) > 0:
                mean_brightness = np.mean(object_pixels)
                filled[object_area] = mean_brightness
                
        elif fill_type == "gradient":
            y_indices, x_indices = np.where(object_area)
            if len(y_indices) > 0:
                center_y = np.mean(y_indices)
                center_x = np.mean(x_indices)
                
                for i, j in zip(y_indices, x_indices):
                    dist = np.sqrt((i - center_y)**2 + (j - center_x)**2)
                    max_dist = np.sqrt(center_y**2 + center_x**2)
                    if max_dist > 0:
                        brightness = 255 * (dist / max_dist)
                        filled[i, j] = np.clip(brightness, 0, 255)
                        
        elif fill_type == "texture":
            for i in range(filled.shape[0]):
                for j in range(filled.shape[1]):
                    if object_area[i, j]:
                        if (i // 4 + j // 4) % 2 == 0:
                            filled[i, j] = 100
                        else:
                            filled[i, j] = 200
        
        return filled
    
    def create_preview(self, image, width=40, title=""):
        """Создание предпросмотра"""
        if image is None or image.size == 0:
            return f"{title}\n(нет данных)"
            
        height = int(width * image.shape[0] / image.shape[1] / 2)
        if height <= 0:
            height = 1
            
        try:
            resized = cv2.resize(image, (width, height))
        except:
            return f"{title}\n(ошибка масштабирования)"
        
        threshold = self.threshold_scale.get()
        
        lines = []
        for row in resized:
            line_chars = []
            for pixel in row:
                # ПРЕВЬЮ ВСЕГДА ОТОБРАЖАЕТ ОРИГИНАЛЬНУЮ ЛОГИКУ
                # (не зависит от инверсии символов)
                if pixel < threshold:
                    line_chars.append('█')  # Темный символ для темного пикселя
                else:
                    line_chars.append(' ')  # Светлый символ для светлого пикселя
            lines.append(''.join(line_chars))
        
        if title:
            lines.insert(0, title.center(width))
        
        return '\n'.join(lines)
    
    def process_frame_with_objects(self, frame):
        """Основная обработка кадра"""
        try:
            # Конвертируем в grayscale
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
            
            # Применяем коррекции (НИКАКОЙ ИНВЕРСИИ ИЗОБРАЖЕНИЯ!)
            gray = np.clip(gray * self.contrast, 0, 255).astype(np.uint8)
            
            # Бинаризация для обнаружения объектов
            threshold = self.threshold_scale.get()
            _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
            
            # Для обнаружения объектов инвертируем (объекты белые на черном фоне)
            binary_inv = cv2.bitwise_not(binary)
            
            # Обнаруживаем объекты
            object_mask, edge_mask, num_objects = self.detect_objects(binary_inv)
            self.last_num_objects = num_objects
            
            # Создаем предпросмотры (всегда оригинальные)
            preview1 = self.create_preview(gray, 40, "Оригинал")
            
            if self.edge_detection and edge_mask is not None:
                contour_img = gray.copy()
                contour_img[edge_mask > 0] = 0
                preview2 = self.create_preview(contour_img, 40, "Контуры")
            else:
                preview2 = self.create_preview(binary, 40, "Бинарное")
            
            if self.fill_objects and object_mask is not None:
                fill_type = self.fill_type_var.get()
                filled_img = self.fill_object_interior(gray, object_mask, fill_type)
                
                if self.edge_detection and edge_mask is not None:
                    filled_img[edge_mask > 0] = 0
                
                preview3 = self.create_preview(filled_img, 40, "Заполнение")
                final_img = filled_img
            else:
                preview3 = self.create_preview(gray, 40, "Без заполнения")
                final_img = gray
            
            # Создаем ASCII из финального изображения
            ascii_result = self.frame_to_ascii(
                final_img, 
                edge_mask if (self.edge_detection and edge_mask is not None) else None
            )
            
            return ascii_result, preview1, preview2, preview3, num_objects
            
        except Exception as e:
            print(f"Ошибка обработки кадра: {e}")
            simple_ascii = "Ошибка обработки\nПопробуйте другие настройки"
            return simple_ascii, "Ошибка", "Ошибка", "Ошибка", 0
    
    def frame_to_ascii(self, gray_image, edge_mask=None):
        """Конвертация в ASCII с возможностью инверсии символов"""
        try:
            if gray_image is None:
                return "Нет изображения"
                
            height = int(self.width * gray_image.shape[0] / gray_image.shape[1] / 1.8)
            if height <= 0:
                height = 1
                
            resized = cv2.resize(gray_image, (self.width, height))
            
            # Если есть маска краев, масштабируем ее
            edge_resized = None
            if edge_mask is not None:
                edge_resized = cv2.resize(edge_mask, (self.width, height))
                edge_resized = edge_resized > 0
            
            # Выбираем набор символов (один и тот же для обоих режимов)
            if self.mode == "ascii":
                fill_chars = self.ascii_fill
                edge_chars = self.ascii_edge
            elif self.mode == "detailed":
                fill_chars = self.unicode_detailed
                edge_chars = ['·', '+', '×', '✱', '✶']
            elif self.mode == "edges_only":
                fill_chars = [' ']
                edge_chars = ['.', '+', 'x', 'X', '#', '█']
            else:  # adaptive
                fill_chars = self.fill_chars
                edge_chars = self.edge_chars
            
            # Создаем ASCII
            ascii_lines = []
            for i in range(resized.shape[0]):
                line_chars = []
                for j in range(resized.shape[1]):
                    pixel = resized[i, j]
                    
                    # Проверяем, является ли это краем
                    is_edge = False
                    if edge_resized is not None and j < edge_resized.shape[1] and edge_resized[i, j]:
                        is_edge = True
                        char_set = edge_chars
                    else:
                        char_set = fill_chars
                    
                    # КЛЮЧЕВАЯ РАЗНИЦА: логика выбора символа в зависимости от инверсии
                    normalized = pixel / 255.0
                    
                    if self.invert_colors:
                        # ИНВЕРТИРОВАННЫЙ РЕЖИМ: светлые пиксели → темные символы
                        # normalized = 1 (белый) → индекс 0 (самый темный символ)
                        # normalized = 0 (черный) → последний индекс (самый светлый символ)
                        index = int((1 - normalized) * (len(char_set) - 1))
                    else:
                        # ОБЫЧНЫЙ РЕЖИМ: темные пиксели → темные символы
                        # normalized = 0 (черный) → индекс 0 (самый темный символ)
                        # normalized = 1 (белый) → последний индекс (самый светлый символ)
                        index = int(normalized * (len(char_set) - 1))
                    
                    index = max(0, min(index, len(char_set) - 1))
                    line_chars.append(char_set[index])
                
                ascii_lines.append(''.join(line_chars))
            
            # Добавляем информацию
            fill_status = "Вкл" if self.fill_objects else "Выкл"
            edge_status = "Вкл" if self.edge_detection else "Выкл"
            invert_status = "ИНВЕРСИЯ" if self.invert_colors else "Обычный"
            
            info1 = f" Объекты: {self.last_num_objects} | Режим: {invert_status} "
            info2 = f" Заполнение: {fill_status} | Контуры: {edge_status} "
            info3 = f" Ширина: {self.width} | Порог: {self.threshold_scale.get()} "
            
            separator = "═" * min(self.width, 80)
            
            result = []
            result.extend(ascii_lines)
            result.append(separator)
            result.append(info1.center(min(self.width, 80)))
            result.append(info2.center(min(self.width, 80)))
            result.append(info3.center(min(self.width, 80)))
            
            return '\n'.join(result)
            
        except Exception as e:
            return f"Ошибка конвертации: {str(e)}"
    
    def process_and_display_frame(self, frame):
        try:
            self.current_frame = frame.copy()
            
            ascii_art, preview1, preview2, preview3, num_objects = self.process_frame_with_objects(frame)
            
            # Обновляем предпросмотры
            for text_widget, preview in [
                (self.preview_text1, preview1),
                (self.preview_text2, preview2),
                (self.preview_text3, preview3)
            ]:
                text_widget.delete(1.0, tk.END)
                text_widget.insert(1.0, preview)
            
            # Обновляем основной ASCII
            self.ascii_text.delete(1.0, tk.END)
            self.ascii_text.insert(1.0, ascii_art)
            self.ascii_text.see(1.0)
            
            # Обновляем статус
            self.status_bar.config(
                text=f"Объектов: {num_objects} | "
                     f"Заполнение: {'Вкл' if self.fill_objects else 'Выкл'} | "
                     f"Контуры: {'Вкл' if self.edge_detection else 'Выкл'} | "
                     f"Инверсия: {'Вкл' if self.invert_colors else 'Выкл'}"
            )
            
        except Exception as e:
            self.status_bar.config(text=f"Ошибка: {str(e)}")
            print(f"Ошибка отображения: {e}")
    
    def toggle_play(self):
        if not self.playing:
            self.play()
        else:
            self.pause()
    
    def play(self):
        if self.cap and not self.playing:
            self.playing = True
            self.play_button.config(text="⏸ Пауза")
            
            self.update_thread = threading.Thread(target=self.update_frames, daemon=True)
            self.update_thread.start()
            
            self.update_display()
    
    def pause(self):
        if self.playing:
            self.playing = False
            self.play_button.config(text="▶ Воспроизвести")
    
    def stop(self):
        self.playing = False
        self.play_button.config(text="▶ Воспроизвести")
        
        if self.cap:
            self.cap.release()
            self.cap = None
        
        # Очищаем все текстовые поля
        for text_widget in [self.ascii_text, self.preview_text1, self.preview_text2, self.preview_text3]:
            text_widget.delete(1.0, tk.END)
        
        self.current_frame = None
        self.last_num_objects = 0
    
    def update_frames(self):
        while self.playing and self.cap:
            ret, frame = self.cap.read()
            
            if not ret:
                if isinstance(self.video_source, str):
                    self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    continue
                else:
                    break
            
            try:
                self.frame_queue.put(frame, timeout=0.1)
            except queue.Full:
                pass
            except Exception as e:
                print(f"Ошибка очереди: {e}")
    
    def update_display(self):
        try:
            frame = None
            while True:
                frame = self.frame_queue.get_nowait()
        except queue.Empty:
            pass
        except Exception as e:
            print(f"Ошибка получения кадра: {e}")
        
        if frame is not None:
            self.process_and_display_frame(frame)
        
        if self.playing:
            self.root.after(30, self.update_display)
    
    def run(self):
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        self.playing = False
        if self.cap:
            self.cap.release()
        self.root.destroy()


# Запуск программы
if __name__ == "__main__":
    print("=" * 70)
    print("ASCII Video Converter с ИНВЕРСИЕЙ СИМВОЛОВ")
    print("Белые пиксели → темные символы | Фон всегда белый")
    print("=" * 70)
    
    try:
        import cv2
        import numpy as np
    except ImportError:
        print("Ошибка: установите библиотеки:")
        print("pip install opencv-python numpy")
        exit(1)
    
    app = ObjectASCIIVideoGUI()
    app.run()