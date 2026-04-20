import cv2
import numpy as np
import mss
import time
import threading
from pynput import mouse

class ScreenTracker:
    def __init__(self):
        self.lower_color = np.array([0, 120, 70])
        self.upper_color = np.array([10, 255, 255])

        self.min_area = 800
        self.smoothing = 0.25

        self.roi_size = 300
        self.max_roi_size = 600
        self.lost_timeout = 1.0

        self.tracking_enabled = False
        self.last_toggle_time = 0
        self.toggle_delay = 0.3

        self.smoothed_x = None
        self.smoothed_y = None
        self.last_seen_time = 0

        self.frame = None
        self.lock = threading.Lock()

        self.sct = mss.mss()
        self.full_monitor = self.sct.monitors[1]
        self.monitor = self.full_monitor.copy()

        self.create_gui()

        self.running = True
        threading.Thread(target=self.capture_loop, daemon=True).start()

        mouse.Listener(on_click=self.on_click).start()

    def create_gui(self):
        cv2.namedWindow("Controls", cv2.WINDOW_NORMAL)

        cv2.createTrackbar("H Min", "Controls", 0, 179, lambda x: None)
        cv2.createTrackbar("H Max", "Controls", 10, 179, lambda x: None)
        cv2.createTrackbar("S Min", "Controls", 120, 255, lambda x: None)
        cv2.createTrackbar("S Max", "Controls", 255, 255, lambda x: None)
        cv2.createTrackbar("V Min", "Controls", 70, 255, lambda x: None)
        cv2.createTrackbar("V Max", "Controls", 255, 255, lambda x: None)

        cv2.createTrackbar("Min Area", "Controls", 800, 5000, lambda x: None)
        cv2.createTrackbar("ROI Size", "Controls", 300, 800, lambda x: None)
        cv2.createTrackbar("Smoothing x100", "Controls", 25, 100, lambda x: None)

    def update_from_gui(self):
        self.lower_color = np.array([
            cv2.getTrackbarPos("H Min", "Controls"),
            cv2.getTrackbarPos("S Min", "Controls"),
            cv2.getTrackbarPos("V Min", "Controls")
        ])

        self.upper_color = np.array([
            cv2.getTrackbarPos("H Max", "Controls"),
            cv2.getTrackbarPos("S Max", "Controls"),
            cv2.getTrackbarPos("V Max", "Controls")
        ])

        self.min_area = cv2.getTrackbarPos("Min Area", "Controls")
        self.roi_size = cv2.getTrackbarPos("ROI Size", "Controls")

        smoothing_val = cv2.getTrackbarPos("Smoothing x100", "Controls")
        self.smoothing = smoothing_val / 100.0

    def on_click(self, x, y, button, pressed):
        if button == mouse.Button.left and pressed:
            now = time.time()
            if now - self.last_toggle_time > self.toggle_delay:
                self.tracking_enabled = not self.tracking_enabled
                print("Tracking:", "ON" if self.tracking_enabled else "OFF")
                self.last_toggle_time = now

    def capture_loop(self):
        while self.running:
            screenshot = self.sct.grab(self.monitor)
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)

            with self.lock:
                self.frame = frame

    def process(self):
        while True:
            self.update_from_gui()

            with self.lock:
                if self.frame is None:
                    continue
                frame = self.frame.copy()

            found = False

            if self.tracking_enabled:
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                mask = cv2.inRange(hsv, self.lower_color, self.upper_color)
                mask = cv2.GaussianBlur(mask, (7, 7), 0)

                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

                if contours:
                    largest = max(contours, key=cv2.contourArea)

                    if cv2.contourArea(largest) > self.min_area:
                        x, y, w, h = cv2.boundingRect(largest)

                        cx = x + w // 2
                        cy = y + h // 2

                        cx_global = cx + self.monitor["left"]
                        cy_global = cy + self.monitor["top"]

                        if self.smoothed_x is None:
                            self.smoothed_x, self.smoothed_y = cx_global, cy_global
                        else:
                            self.smoothed_x += (cx_global - self.smoothed_x) * self.smoothing
                            self.smoothed_y += (cy_global - self.smoothed_y) * self.smoothing

                        self.monitor = {
                            "left": int(max(0, self.smoothed_x - self.roi_size // 2)),
                            "top": int(max(0, self.smoothed_y - self.roi_size // 2)),
                            "width": self.roi_size,
                            "height": self.roi_size
                        }

                        self.last_seen_time = time.time()
                        found = True

                        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        cv2.circle(frame, (int(cx), int(cy)), 5, (0, 0, 255), -1)

            if self.tracking_enabled and not found:
                if time.time() - self.last_seen_time > self.lost_timeout:
                    self.monitor = self.full_monitor.copy()
                    self.smoothed_x, self.smoothed_y = None, None

            status = "ON" if self.tracking_enabled else "OFF"
            color = (0, 255, 0) if self.tracking_enabled else (0, 0, 255)

            cv2.putText(frame, f"Tracking: {status}", (20, 40),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)

            cv2.imshow("Tracker", frame)

            if cv2.waitKey(1) == 27:
                self.running = False
                break

        cv2.destroyAllWindows()


if __name__ == "__main__":
    tracker = ScreenTracker()
    tracker.process()
