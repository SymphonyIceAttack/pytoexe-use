import cv2
import numpy as np
import pygame
import time
import json
import win32api
from PIL import ImageGrab
from datetime import datetime

pygame.mixer.init()


class ScreenMotionDetector:
    def __init__(self):
        self.min_area = 80
        self.threshold = 25
        self.blur_size = 15
        self.fps = 20

        self.first_frame = None
        self.roi = None
        self.sound_enabled = True
        self.beep_sound = None
        self.cooldown_frames = 0
        self.cooldown_max = 10

        self._create_beep()
        self.load_settings()
        print("=== Детектор движения на экране ===")
        print("SPACE - выбрать область | R - сброс | S - звук | +/- - чувствительность | ESC - выход\n")

    def _create_beep(self):
        try:
            sample_rate = 44100
            duration = 0.3
            frames = int(duration * sample_rate)
            arr = np.array([4096 * np.sin(2 * np.pi * 800 * x / sample_rate) 
                           for x in range(frames)]).astype(np.int16)
            self.beep_sound = pygame.sndarray.make_sound(arr)
        except:
            self.beep_sound = None

    def create_beep(self):
        if self.sound_enabled and self.beep_sound:
            try:
                self.beep_sound.play()
            except:
                pass

    def select_roi_screen(self):
        print("📐 Выделите нужную область мышкой...")
        win_name = "Выбор области"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.setWindowProperty(win_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

        try:
            w = win32api.GetSystemMetrics(0)
            h = win32api.GetSystemMetrics(1)
        except:
            w, h = 1920, 1080

        roi = [None]
        start = [None]
        end = [None]
        selecting = [False]

        def mouse(event, x, y, flags, param):
            if event == cv2.EVENT_LBUTTONDOWN:
                selecting[0] = True
                start[0] = (x, y)
            elif event == cv2.EVENT_MOUSEMOVE and selecting[0]:
                end[0] = (x, y)
            elif event == cv2.EVENT_LBUTTONUP:
                selecting[0] = False
                if start[0] and end[0]:
                    x1 = min(start[0][0], end[0][0])
                    y1 = min(start[0][1], end[0][1])
                    x2 = max(start[0][0], end[0][0])
                    y2 = max(start[0][1], end[0][1])
                    if x2 - x1 > 40 and y2 - y1 > 40:
                        roi[0] = (x1, y1, x2-x1, y2-y1)

        cv2.setMouseCallback(win_name, mouse)

        while roi[0] is None:
            try:
                frame = cv2.cvtColor(np.array(ImageGrab.grab(bbox=(0,0,w,h))), cv2.COLOR_RGB2BGR)
            except:
                continue

            if start[0] and end[0]:
                x1,y1 = min(start[0][0],end[0][0]), min(start[0][1],end[0][1])
                x2,y2 = max(start[0][0],end[0][0]), max(start[0][1],end[0][1])
                overlay = frame.copy()
                cv2.rectangle(overlay,(x1,y1),(x2,y2),(0,0,0),-1)
                cv2.addWeighted(overlay,0.4,frame,0.6,0,frame)
                cv2.rectangle(frame,(x1,y1),(x2,y2),(0,255,0),3)

            cv2.putText(frame,"Выделите область (ESC - отмена)",(30,60),cv2.FONT_HERSHEY_SIMPLEX,1,(0,255,255),2)
            cv2.imshow(win_name, frame)
            if cv2.waitKey(1) & 0xFF == 27:
                break

        cv2.destroyAllWindows()
        if roi[0]:
            self.roi = roi[0]
            self.first_frame = None
            print("✅ Область выбрана")
            return True
        return False

    def run(self):
        print("Программа запущена...")
        last_time = time.time()

        while True:
            try:
                screenshot = ImageGrab.grab()
                frame = cv2.cvtColor(np.array(screenshot), cv2.COLOR_RGB2BGR)
            except:
                time.sleep(0.1)
                continue

            # Обработка
            display = frame.copy()
            gray = cv2.GaussianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (self.blur_size, self.blur_size), 0)

            if self.roi:
                x,y,w,h = self.roi
                fh,fw = frame.shape[:2]
                x = max(0,min(x,fw-1))
                y = max(0,min(y,fh-1))
                w = min(w, fw-x)
                h = min(h, fh-y)
                if w > 40 and h > 40:
                    gray_roi = gray[y:y+h, x:x+w]
                    cv2.rectangle(display, (x,y), (x+w,y+h), (0,255,0), 2)
                    gray = gray_roi
                else:
                    self.roi = None

            if self.first_frame is None:
                self.first_frame = gray.copy()
            else:
                delta = cv2.absdiff(self.first_frame, gray)
                thresh = cv2.dilate(cv2.threshold(delta, self.threshold, 255, cv2.THRESH_BINARY)[1], None, iterations=2)

                motion = False
                for cnt in cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[0]:
                    if cv2.contourArea(cnt) > self.min_area:
                        motion = True
                        if self.roi:
                            M = cv2.moments(cnt)
                            if M["m00"] != 0:
                                cx = int(M["m10"]/M["m00"]) + self.roi[0]
                                cy = int(M["m01"]/M["m00"]) + self.roi[1]
                                cv2.circle(display, (cx,cy), 12, (0,0,255), 2)
                        break

                if motion and self.cooldown_frames <= 0:
                    self.create_beep()
                    self.cooldown_frames = self.cooldown_max
                    cv2.putText(display, "🚨 ДВИЖЕНИЕ!", (20,50), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0,0,255), 3)
                elif motion:
                    self.cooldown_frames -= 1
                else:
                    self.cooldown_frames = max(0, self.cooldown_frames-1)

                alpha = 0.5 if motion else 0.9
                self.first_frame = cv2.addWeighted(self.first_frame, alpha, gray, 1-alpha, 0)

            cv2.putText(display, f"Чувств: {self.threshold}", (20,90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,255,255), 1)
            cv2.imshow("Детектор движения", display)

            # Управление
            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord('q')):
                break
            elif key == ord(' '):
                self.first_frame = None
                self.select_roi_screen()
            elif key in (ord('r'), ord('R')):
                self.roi = None
                self.first_frame = None
            elif key in (ord('s'), ord('S')):
                self.sound_enabled = not self.sound_enabled
            elif key in (ord('+'), ord('=')):
                self.threshold = min(60, self.threshold + 3)
            elif key == ord('-'):
                self.threshold = max(5, self.threshold - 3)

            time.sleep(max(0, 1/self.fps - (time.time() - last_time)))
            last_time = time.time()

        cv2.destroyAllWindows()
        pygame.mixer.quit()
        print("Программа завершена")


if __name__ == "__main__":
    try:
        detector = ScreenMotionDetector()
        detector.run()
    except Exception as e:
        print(f"Ошибка: {e}")
        input("Нажмите Enter...")