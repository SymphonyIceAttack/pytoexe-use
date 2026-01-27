import cv2
import os
from datetime import datetime

# путь к рабочему столу (Windows)
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")

# имя файла с датой и временем
filename = f"webcam_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.jpg"
file_path = os.path.join(desktop_path, filename)

# включаем камеру
cap = cv2.VideoCapture(0)

if not cap.isOpened():
    print("Камера не найдена")
    exit()

ret, frame = cap.read()

if ret:
    cv2.imwrite(file_path, frame)
    print(f"Фото сохранено: {file_path}")
else:
    print("Не удалось сделать фото")

cap.release()
