import cv2
import numpy as np
import pygame
import time
from datetime import datetime
import sys
import os
import json
import win32gui
import win32con
import win32api
from PIL import ImageGrab

# Инициализация pygame для звука
pygame.mixer.init()

class ScreenMotionDetector:
    def __init__(self):
        # Параметры детектора
        self.min_area = 100  # Минимальная площадь движущегося объекта
        self.threshold = 30  # Чувствительность (чем меньше, тем чувствительнее)
        self.blur_size = 15  # Размер размытия (должен быть нечётным)
        self.fps = 30
        
        # Переменные для хранения фреймов
        self.first_frame = None
        self.is_recording = False
        self.recording_start = None
        
        # Звук
        self.sound_enabled = True
        self.beep_duration = 300  # мс
        self.beep_frequency = 800  # Гц
        self.beep_sound = None
        self._create_beep_sound()
        
        # Область выделения
        self.roi = None
        self.selecting_roi = False
        self.roi_start = None
        self.roi_end = None
        
        # Счётчик для подавления ложных срабатываний
        self.cooldown_frames = 0
        self.cooldown_max = 15  # Количество кадров между сигналами
        
        # Для выбора области на экране
        self.selection_window = None
        self.selecting = False
        self.start_point = None
        self.end_point = None
        
        # Загружаем настройки
        self.settings_file = "screen_motion_detector_settings.json"
        self.load_settings()
        
        print("=== Детектор движения на экране ===")
        print("\nУправление:")
        print("  ESC - выход")
        print("  SPACE - выбор области (кликни и перетащи мышкой)")
        print("  R - сбросить выбор области")
        print("  S - включить/выключить звук")
        print("  +/- - изменить чувствительность")
        print("  Q - выход")
        print("\nИнструкция:")
        print("1. Нажмите SPACE для выбора области")
        print("2. Кликните левой кнопкой мыши в одном углу области")
        print("3. Перетащите в противоположный угол и отпустите")
        print("4. Движение в выделенной области будет вызывать звуковой сигнал")
        print("\nНажмите SPACE для выбора области...")

    def _create_beep_sound(self):
        """Создаёт звуковой сигнал заранее для оптимизации"""
        try:
            sample_rate = 44100
            duration = self.beep_duration / 1000.0
            frames = int(duration * sample_rate)
            arr = np.array([4096 * np.sin(2.0 * np.pi * self.beep_frequency * x / sample_rate) 
                           for x in range(frames)]).astype(np.int16)
            self.beep_sound = pygame.sndarray.make_sound(arr)
        except Exception as e:
            print(f"⚠️ Ошибка создания звука: {e}")
            self.beep_sound = None

    def create_beep(self):
        """Воспроизводит звуковой сигнал"""
        if not self.sound_enabled:
            return
            
        try:
            if self.beep_sound:
                self.beep_sound.play()
        except Exception as e:
            print(f"Ошибка воспроизведения звука: {e}")

    def select_roi_screen(self):
        """Выбор области на экране с помощью мыши"""
        print("\n📐 Выберите область на экране:")
        print("  - Нажмите и удерживайте левую кнопку мыши")
        print("  - Перетащите для выбора области")
        print("  - Отпустите кнопку для подтверждения")
        print("  - Нажмите ESC для отмены")
        
        # Создаём окно для выбора
        self.selection_window = "Выбор области"
        cv2.namedWindow(self.selection_window, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(self.selection_window, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        # Получаем размер экрана
        screen_width = win32api.GetSystemMetrics(0)
        screen_height = win32api.GetSystemMetrics(1)
        
        # Создаём прозрачное окно
        cv2.setWindowTitle(self.selection_window, "Выберите область")
        
        # Переменные для выбора (используем список для изменения из замыкания)
        roi_selected = [None]
        self.selecting = False
        self.start_point = None
        self.end_point = None
        
        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                self.selecting = True
                self.start_point = (x, y)
                self.end_point = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and self.selecting:
                self.end_point = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:
                self.selecting = False
                self.end_point = (x, y)
                # Вычисляем ROI
                if self.start_point and self.end_point:
                    x1 = min(self.start_point[0], self.end_point[0])
                    y1 = min(self.start_point[1], self.end_point[1])
                    x2 = max(self.start_point[0], self.end_point[0])
                    y2 = max(self.start_point[1], self.end_point[1])
                    
                    width = x2 - x1
                    height = y2 - y1
                    
                    if width > 20 and height > 20:
                        roi_selected[0] = (x1, y1, width, height)
                        print(f"✅ Область выбрана: x={x1}, y={y1}, w={width}, h={height}")
                    else:
                        print("❌ Область слишком маленькая")
        
        cv2.setMouseCallback(self.selection_window, mouse_callback)
        
        # Основной цикл выбора
        while roi_selected[0] is None:
            # Захват экрана
            screenshot = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
            frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            
            # Рисуем прямоугольник выделения
            if self.start_point and self.end_point:
                x1 = min(self.start_point[0], self.end_point[0])
                y1 = min(self.start_point[1], self.end_point[1])
                x2 = max(self.start_point[0], self.end_point[0])
                y2 = max(self.start_point[1], self.end_point[1])
                
                # Затемняем фон вне выделения
                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
                alpha = 0.3
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
                
                # Рисуем рамку выделения
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # Добавляем информацию
                cv2.putText(frame, f"Область: {x2-x1}x{y2-y1}", (x1, y1-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Добавляем инструкцию
            cv2.putText(frame, "Выберите область: нажмите и перетащите мышкой", (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "Нажмите ESC для отмены", (10, 60), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            
            cv2.imshow(self.selection_window, frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("❌ Выбор области отменён")
                break
        
        # Закрываем окно выбора
        try:
            cv2.destroyWindow(self.selection_window)
        except:
            pass
        
        if roi_selected[0]:
            self.roi = tuple(roi_selected[0])  # Приводим к кортежу
            self.first_frame = None
            return True
        return False

    def capture_screen(self):
        """Захватывает текущий экран"""
        screenshot = ImageGrab.grab()
        frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        return frame

    def process_frame(self, frame):
        """Обработка кадра и обнаружение движения"""
        if frame is None:
            return None, 0
        
        # Сохраняем оригинал для отображения
        display_frame = frame.copy()
        
        # Преобразование в оттенки серого
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Размытие для уменьшения шума
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)
        
        # Переменные для хранения информации об области
        roi_active = False
        roi_x, roi_y, roi_w, roi_h = 0, 0, 0, 0
        
        # Если область выбрана, обрезаем кадр
        if self.roi is not None:
            x, y, w, h = self.roi
            
            # Проверяем, что ROI в пределах кадра
            h_frame, w_frame = frame.shape[:2]
            x = max(0, min(x, w_frame-1))
            y = max(0, min(y, h_frame-1))
            w = min(w, w_frame - x)
            h = min(h, h_frame - y)
            
            if w > 0 and h > 0:
                roi_active = True
                roi_x, roi_y, roi_w, roi_h = x, y, w, h
                # Обрезаем для анализа
                gray = gray[y:y+h, x:x+w]
                # Рисуем рамку области на отображаемом кадре
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                status_text = "Область выбрана"
            else:
                status_text = "Ошибка области (слишком маленькая)"
                cv2.putText(display_frame, status_text, (10, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                return display_frame, 0
        else:
            status_text = "Область не выбрана (нажмите SPACE)"
            cv2.putText(display_frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Инициализация первого кадра
        if self.first_frame is None:
            self.first_frame = gray
            return display_frame, 0
        
        # Вычисление разницы между текущим и первым кадром
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Удаление шума
        thresh = cv2.dilate(thresh, None, iterations=2)
        thresh = cv2.erode(thresh, None, iterations=1)
        
        # Поиск контуров
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, 
                                       cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        max_area = 0
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                max_area = max(max_area, area)
                motion_detected = True
                
                # Рисуем контур движения на отображаемом кадре
                if roi_active:
                    # Корректировка координат для отображения на полном кадре
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + roi_x
                        cy = int(M["m01"] / M["m00"]) + roi_y
                        cv2.circle(display_frame, (cx, cy), 10, (0, 0, 255), 2)
        
        # Обновление первого кадра (адаптивный фон)
        if motion_detected:
            alpha = 0.7  # Быстрее обновляем при движении
        else:
            alpha = 0.9  # Медленнее при отсутствии движения
        self.first_frame = cv2.addWeighted(self.first_frame, alpha, gray, 1 - alpha, 0)
        
        # Сигнал при обнаружении движения
        if motion_detected and self.cooldown_frames <= 0:
            self.create_beep()
            self.cooldown_frames = self.cooldown_max
            status_text = "🚨 ДВИЖЕНИЕ ОБНАРУЖЕНО!"
            color = (0, 0, 255)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Движение обнаружено! Площадь: {max_area:.0f} пикс.")
        elif motion_detected:
            self.cooldown_frames -= 1
            status_text = "Движение (ожидание)"
            color = (0, 255, 255)
        else:
            if self.cooldown_frames > 0:
                self.cooldown_frames -= 1
            status_text = "Нет движения"
            color = (0, 255, 0)
        
        # Отображение информации на кадре
        cv2.putText(display_frame, status_text, (10, 30), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        cv2.putText(display_frame, f"Чувствительность: {self.threshold}", (10, 60), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        if roi_active:
            cv2.putText(display_frame, f"Область: {roi_w}x{roi_h}", (10, 90), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(display_frame, f"Звук: {'Вкл' if self.sound_enabled else 'Выкл'}", (10, 120), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
        
        cv2.putText(display_frame, "ESC-выход SPACE-выбор области R-сброс S-звук +/-чувствительность", 
                   (10, display_frame.shape[0]-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return display_frame, max_area

    def save_settings(self):
        """Сохранение настроек в файл"""
        settings = {
            'threshold': self.threshold,
            'min_area': self.min_area,
            'roi': self.roi,
            'sound_enabled': self.sound_enabled,
            'beep_frequency': self.beep_frequency,
            'beep_duration': self.beep_duration
        }
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f)
            print("✅ Настройки сохранены")
        except Exception as e:
            print(f"⚠️ Не удалось сохранить настройки: {e}")

    def load_settings(self):
        """Загрузка настроек из файла"""
        try:
            with open(self.settings_file, 'r') as f:
                settings = json.load(f)
            self.threshold = settings.get('threshold', self.threshold)
            self.min_area = settings.get('min_area', self.min_area)
            self.roi = settings.get('roi', None)
            if self.roi is not None:
                self.roi = tuple(self.roi)  # Приводим к кортежу
            self.sound_enabled = settings.get('sound_enabled', True)
            self.beep_frequency = settings.get('beep_frequency', self.beep_frequency)
            self.beep_duration = settings.get('beep_duration', self.beep_duration)
            print("✅ Настройки загружены")
        except:
            print("ℹ️ Настройки не найдены, используются значения по умолчанию")

    def run(self):
        """Основной цикл программы"""
        print("\n✅ Программа запущена")
        print("Нажмите SPACE для выбора области наблюдения")
        print("Нажмите ESC или Q для выхода")
        
        # Переменные для контроля FPS
        fps_display = 30
        last_frame_time = time.time()
        
        while True:
            # Захват экрана
            frame = self.capture_screen()
            
            # Обработка кадра
            processed_frame, _ = self.process_frame(frame)
            
            # Ограничение FPS
            current_time = time.time()
            time_diff = current_time - last_frame_time
            if time_diff < 1.0 / self.fps:
                time.sleep(1.0 / self.fps - time_diff)
            last_frame_time = time.time()
            
            # Отображение
            cv2.imshow("Детектор движения на экране", processed_frame)
            
            # Обработка клавиш
            key = cv2.waitKey(1) & 0xFF
            
            if key == 27 or key == ord('q') or key == ord('Q'):  # ESC или Q
                break
            elif key == ord(' '):  # SPACE - выбор области
                self.first_frame = None  # Сброс фона
                if self.select_roi_screen():
                    print("✅ Область выбрана, начинаем отслеживание")
                else:
                    print("ℹ️ Выбор области отменён")
            elif key == ord('r') or key == ord('R'):  # Сброс области
                self.roi = None
                self.first_frame = None
                print("🔄 Область сброшена")
            elif key == ord('s') or key == ord('S'):  # Переключение звука
                self.sound_enabled = not self.sound_enabled
                print(f"🔊 Звук: {'Включён' if self.sound_enabled else 'Выключен'}")
            elif key == ord('+') or key == ord('='):  # Увеличение чувствительности
                self.threshold = min(100, self.threshold + 1)
                self.first_frame = None
                print(f"📊 Чувствительность: {self.threshold}")
            elif key == ord('-'):  # Уменьшение чувствительности
                self.threshold = max(1, self.threshold - 1)
                self.first_frame = None
                print(f"📊 Чувствительность: {self.threshold}")
        
        # Сохраняем настройки
        self.save_settings()
        
        # Завершение работы
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("\n👋 Программа завершена")

def main():
    try:
        detector = ScreenMotionDetector()
        detector.run()
    except KeyboardInterrupt:
        print("\n👋 Программа прервана пользователем")
    except Exception as e:
        print(f"\n❌ Произошла ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter для выхода...")

if __name__ == "__main__":
    main()