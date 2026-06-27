import cv2
import numpy as np
import pygame
import time
from datetime import datetime
import sys
import json
import win32api
from PIL import ImageGrab

# Инициализация pygame для звука
pygame.mixer.init()


class ScreenMotionDetector:
    def __init__(self):
        # Параметры
        self.min_area = 100
        self.threshold = 30
        self.blur_size = 15
        self.fps = 30
        
        self.first_frame = None
        self.roi = None
        self.sound_enabled = True
        self.beep_duration = 300
        self.beep_frequency = 800
        self.beep_sound = None
        self.cooldown_frames = 0
        self.cooldown_max = 15
        
        self.settings_file = "screen_motion_detector_settings.json"
        self._create_beep_sound()
        self.load_settings()
        
        print("=== Детектор движения на экране ===")
        print("\nУправление:")
        print("  ESC/Q - выход")
        print("  SPACE - выбор области")
        print("  R     - сброс области")
        print("  S     - вкл/выкл звук")
        print("  +/-   - чувствительность")
        print("\nНажмите SPACE для выбора области...")

    def _create_beep_sound(self):
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
        if not self.sound_enabled or not self.beep_sound:
            return
        try:
            self.beep_sound.play()
        except:
            pass

    def select_roi_screen(self):
        """Улучшенный выбор области"""
        print("\n📐 Выберите область на экране (перетащите мышкой)...")
        
        window_name = "Выбор области"
        cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        try:
            screen_width = win32api.GetSystemMetrics(0)
            screen_height = win32api.GetSystemMetrics(1)
        except:
            screen_width, screen_height = 1920, 1080  # fallback

        roi_selected = [None]
        start_point = [None]
        end_point = [None]
        selecting = [False]

        def mouse_callback(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                selecting[0] = True
                start_point[0] = (x, y)
                end_point[0] = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and selecting[0]:
                end_point[0] = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:
                selecting[0] = False
                end_point[0] = (x, y)
                if start_point[0] and end_point[0]:
                    x1 = min(start_point[0][0], end_point[0][0])
                    y1 = min(start_point[0][1], end_point[0][1])
                    x2 = max(start_point[0][0], end_point[0][0])
                    y2 = max(start_point[0][1], end_point[0][1])
                    w, h = x2 - x1, y2 - y1
                    if w > 30 and h > 30:
                        roi_selected[0] = (x1, y1, w, h)
                        print(f"✅ Область выбрана: {w}x{h} в ({x1}, {y1})")
                    else:
                        print("❌ Область слишком маленькая")

        cv2.setMouseCallback(window_name, mouse_callback)

        while roi_selected[0] is None:
            try:
                screenshot = ImageGrab.grab(bbox=(0, 0, screen_width, screen_height))
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            except Exception as e:
                print(f"Ошибка захвата экрана: {e}")
                break

            # Рисование выделения
            if start_point[0] and end_point[0]:
                x1 = min(start_point[0][0], end_point[0][0])
                y1 = min(start_point[0][1], end_point[0][1])
                x2 = max(start_point[0][0], end_point[0][0])
                y2 = max(start_point[0][1], end_point[0][1])

                overlay = frame.copy()
                cv2.rectangle(overlay, (x1, y1), (x2, y2), (0, 0, 0), -1)
                cv2.addWeighted(overlay, 0.35, frame, 0.65, 0, frame)
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 3)

                cv2.putText(frame, f"{x2-x1}x{y2-y1}", (x1, y1-15),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

            cv2.putText(frame, "Перетащите мышкой • ESC — отмена", (20, 50),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)

            cv2.imshow(window_name, frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                print("❌ Выбор отменён")
                break

        cv2.destroyWindow(window_name)
        
        if roi_selected[0]:
            self.roi = roi_selected[0]
            self.first_frame = None
            return True
        return False

    def capture_screen(self):
        try:
            screenshot = ImageGrab.grab()
            return cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Ошибка захвата: {e}")
            return None

    def process_frame(self, frame):
        if frame is None:
            return None, 0

        display_frame = frame.copy()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (self.blur_size, self.blur_size), 0)

        roi_active = False
        roi_x, roi_y, roi_w, roi_h = 0, 0, 0, 0

        if self.roi:
            x, y, w, h = self.roi
            h_frame, w_frame = frame.shape[:2]
            x = max(0, min(x, w_frame - 1))
            y = max(0, min(y, h_frame - 1))
            w = min(w, w_frame - x)
            h = min(h, h_frame - y)

            if w > 30 and h > 30:
                roi_active = True
                roi_x, roi_y, roi_w, roi_h = x, y, w, h
                gray = gray[y:y+h, x:x+w]
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            else:
                self.roi = None

        if self.first_frame is None:
            self.first_frame = gray
            return display_frame, 0

        # Детекция движения
        frame_delta = cv2.absdiff(self.first_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)
        thresh = cv2.erode(thresh, None, iterations=1)

        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        motion_detected = False
        max_area = 0

        for contour in contours:
            area = cv2.contourArea(contour)
            if area > self.min_area:
                max_area = max(max_area, area)
                motion_detected = True
                if roi_active:
                    M = cv2.moments(contour)
                    if M["m00"] != 0:
                        cx = int(M["m10"] / M["m00"]) + roi_x
                        cy = int(M["m01"] / M["m00"]) + roi_y
                        cv2.circle(display_frame, (cx, cy), 12, (0, 0, 255), 2)

        # Адаптивное обновление фона
        alpha = 0.65 if motion_detected else 0.92
        self.first_frame = cv2.addWeighted(self.first_frame, alpha, gray, 1 - alpha, 0)

        # Сигнал
        if motion_detected and self.cooldown_frames <= 0:
            self.create_beep()
            self.cooldown_frames = self.cooldown_max
            status = "🚨 ДВИЖЕНИЕ ОБНАРУЖЕНО!"
            color = (0, 0, 255)
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Движение! Площадь: {max_area:.0f}")
        elif motion_detected:
            self.cooldown_frames = max(0, self.cooldown_frames - 1)
            status = "Движение..."
            color = (0, 165, 255)
        else:
            self.cooldown_frames = max(0, self.cooldown_frames - 1)
            status = "Ожидание"
            color = (0, 255, 0)

        # Интерфейс
        cv2.putText(display_frame, status, (15, 35), cv2.FONT_HERSHEY_SIMPLEX, 0.85, color, 2)
        cv2.putText(display_frame, f"Чувств.: {self.threshold}", (15, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)
        
        if roi_active:
            cv2.putText(display_frame, f"Область: {roi_w}x{roi_h}", (15, 100), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)
        
        cv2.putText(display_frame, f"Звук: {'ON' if self.sound_enabled else 'OFF'}", (15, 130), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 1)

        cv2.putText(display_frame, "ESC/Q-выход  SPACE-область  R-сброс  S-звук  +/- чувств.", 
                   (15, display_frame.shape[0]-20), cv2.FONT_HERSHEY_SIMPLEX, 0.55, (200, 200, 200), 1)

        return display_frame, max_area

    def save_settings(self):
        settings = {
            'threshold': self.threshold,
            'min_area': self.min_area,
            'roi': self.roi,
            'sound_enabled': self.sound_enabled,
            'beep_frequency': self.beep_frequency,
            'beep_duration': self.beep_duration
        }
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(settings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Не удалось сохранить настройки: {e}")

    def load_settings(self):
        try:
            with open(self.settings_file, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            self.threshold = settings.get('threshold', self.threshold)
            self.min_area = settings.get('min_area', self.min_area)
            self.roi = settings.get('roi')
            if self.roi:
                self.roi = tuple(self.roi)
            self.sound_enabled = settings.get('sound_enabled', True)
            print("✅ Настройки загружены")
        except:
            pass

    def run(self):
        print("\n✅ Запущен")
        last_frame_time = time.time()

        while True:
            frame = self.capture_screen()
            if frame is None:
                time.sleep(0.1)
                continue

            processed_frame, _ = self.process_frame(frame)

            # FPS контроль
            delay = 1.0 / self.fps - (time.time() - last_frame_time)
            if delay > 0:
                time.sleep(delay)
            last_frame_time = time.time()

            cv2.imshow("Детектор движения на экране", processed_frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q'), ord('Q')):
                break
            elif key == ord(' '):
                self.first_frame = None
                self.select_roi_screen()
            elif key in (ord('r'), ord('R')):
                self.roi = None
                self.first_frame = None
                print("🔄 Область сброшена")
            elif key in (ord('s'), ord('S')):
                self.sound_enabled = not self.sound_enabled
                print(f"🔊 Звук: {'Вкл' if self.sound_enabled else 'Выкл'}")
            elif key in (ord('+'), ord('=')):
                self.threshold = min(100, self.threshold + 2)
                self.first_frame = None
            elif key == ord('-'):
                self.threshold = max(5, self.threshold - 2)
                self.first_frame = None

        self.save_settings()
        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("\n👋 Завершено")


if __name__ == "__main__":
    try:
        detector = ScreenMotionDetector()
        detector.run()
    except KeyboardInterrupt:
        print("\n👋 Прервано")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        import traceback
        traceback.print_exc()
        input("Нажмите Enter...")