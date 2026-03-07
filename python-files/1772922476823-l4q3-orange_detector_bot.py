"""
Orange Object Detector (Educational)
------------------------------------
Press F6 to start/stop detection.
Press ESC to close the program.

Requirements:
pip install opencv-python numpy mss keyboard
"""

import cv2
import numpy as np
import mss
import keyboard

running = False
frame = np.zeros((300,300,3), dtype=np.uint8)

print("F6 — включить/выключить поиск")
print("ESC — выход")

with mss.mss() as sct:

    monitor = sct.monitors[1]

    while True:

        if keyboard.is_pressed("F6"):
            running = not running
            print("Поиск:", "ВКЛ" if running else "ВЫКЛ")
            cv2.waitKey(400)

        if running:

            screenshot = np.array(sct.grab(monitor))
            frame = cv2.cvtColor(screenshot, cv2.COLOR_BGRA2BGR)

            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)

            lower_orange = np.array([5,120,120])
            upper_orange = np.array([20,255,255])

            mask = cv2.inRange(hsv, lower_orange, upper_orange)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for cnt in contours:
                area = cv2.contourArea(cnt)

                if area > 500:
                    x,y,w,h = cv2.boundingRect(cnt)

                    cx = x + w//2
                    cy = y + h//2

                    cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
                    cv2.circle(frame,(cx,cy),5,(255,0,0),-1)

                    cv2.putText(frame,f"{cx},{cy}",
                                (x,y-10),
                                cv2.FONT_HERSHEY_SIMPLEX,
                                0.5,(255,255,255),1)

        cv2.imshow("Orange Object Detection", frame)

        if cv2.waitKey(1) == 27:
            break

cv2.destroyAllWindows()
