# abandoned_detector_safe_tracking.py
# Безопасный трекинг: исправлено: 'NoneType' object is not subscriptable
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import cv2
import numpy as np
import os
import yaml
import threading
from ultralytics import YOLO

# --- Настройки ---
SAVE_DIR = "alerts"
os.makedirs(SAVE_DIR, exist_ok=True)
os.makedirs("dataset/images/train", exist_ok=True)
os.makedirs("dataset/labels/train", exist_ok=True)

# --- Классы ---
CLASSES = {
    0: "person",
    26: "handbag",
    27: "backpack",
    32: "suitcase",
    28: "briefcase",
    39: "bottle"
}

COLORS = {
    "person": (255, 100, 100),
    "handbag": (0, 200, 200),
    "backpack": (0, 100, 255),
    "suitcase": (255, 0, 255),
    "briefcase": (128, 0, 128),
    "bottle": (0, 150, 0)
}

# --- Параметры ---
CONFIDENCE = 0.3
ALERT_HEIGHT_RATIO = 0.6
MIN_STATIC_FRAMES = 30

# --- Для видео ---
object_positions = {}
abandoned_objects = set()

# --- Функции ---
def enhance_image(img):
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
    l = clahe.apply(l)
    enhanced = cv2.merge([l, a, b])
    return cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)

def sharpen_image(img):
    kernel = np.array([[0, -1, 0], [-1, 5, -1], [0, -1, 0]])
    return cv2.filter2D(img, -1, kernel)

def distance(p1, p2):
    return np.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)

def is_on_floor(box, frame_h):
    _, y1, _, y2 = box
    return (y1 + y2) / 2 > frame_h * ALERT_HEIGHT_RATIO

def no_person_near(box, people_boxes, threshold=120):
    if not people_boxes:
        return True
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
    for px1, py1, px2, py2 in people_boxes:
        pcx, pcy = (px1 + px2) // 2, (py1 + py2) // 2
        if distance((cx, cy), (pcx, pcy)) < threshold:
            return False
    return True

def is_stationary(track_id, new_pos, max_shift=15):
    if track_id not in object_positions:
        object_positions[track_id] = []
    object_positions[track_id].append(new_pos)
    if len(object_positions[track_id]) > MIN_STATIC_FRAMES:
        object_positions[track_id].pop(0)
    if len(object_positions[track_id]) < MIN_STATIC_FRAMES:
        return False
    shifts = [distance(new_pos, pos) for pos in object_positions[track_id]]
    return max(shifts) < max_shift

# --- Обучение ---
def start_training(data_path, epochs, imgsz, result_label):
    try:
        result_label.config(text="Обучение: запуск...")
        data_yaml = {
            'train': os.path.abspath("dataset/images/train"),
            'val': os.path.abspath("dataset/images/train"),
            'nc': 6,
            'names': ['person', 'handbag', 'backpack', 'suitcase', 'briefcase', 'bottle']
        }
        with open("dataset/data.yaml", 'w') as f:
            yaml.dump(data_yaml, f)

        model = YOLO("yolov8s.pt")
        result_label.config(text="Обучение: началось...")
        model.train(
            data="dataset/data.yaml",
            epochs=int(epochs),
            imgsz=int(imgsz),
            batch=16,
            name="custom_detector",
            exist_ok=True
        )
        model.save("yolo_custom.pt")
        result_label.config(text="✅ Обучение завершено: yolo_custom.pt", fg="green")
    except Exception as e:
        result_label.config(text=f"❌ Ошибка: {e}", fg="red")

def train_model_gui(data_path_entry, epochs_entry, imgsz_entry, result_label):
    data_path = data_path_entry.get()
    epochs = epochs_entry.get()
    imgsz = imgsz_entry.get()

    if not data_path or not os.path.exists(data_path):
        messagebox.showerror("Ошибка", "Укажите папку с изображениями")
        return

    if not epochs.isdigit():
        messagebox.showerror("Ошибка", "Введите корректное число эпох")
        return

    if not imgsz.isdigit():
        messagebox.showerror("Ошибка", "Введите корректный размер изображения")
        return

    thread = threading.Thread(target=start_training, args=(data_path, epochs, imgsz, result_label), daemon=True)
    thread.start()

# --- Анализ фото ---
def analyze_photo(path, result_label, use_custom):
    model_path = "yolo_custom.pt" if use_custom and os.path.exists("yolo_custom.pt") else "yolov8s.pt"
    try:
        MODEL = YOLO(model_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить модель: {e}")
        return

    frame = cv2.imread(path)
    if frame is None:
        messagebox.showerror("Ошибка", "Не удалось загрузить изображение")
        return

    frame = enhance_image(frame)
    frame = sharpen_image(frame)
    display_frame = frame.copy()
    h, w = frame.shape[:2]

    results = MODEL(frame, conf=CONFIDENCE)
    boxes = results[0].boxes

    people_boxes = []
    for box in boxes:
        cls_id = int(box.cls[0])
        if cls_id == 0:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            people_boxes.append([x1, y1, x2, y2])

    alert_found = False
    detections = []

    for box in boxes:
        cls_id = int(box.cls[0])
        if cls_id not in CLASSES:
            continue

        x1, y1, x2, y2 = map(int, box.xyxy[0])
        label = MODEL.model.names[cls_id]
        conf = float(box.conf[0])
        color = COLORS.get(label, (128, 128, 128))

        if (cls_id != 0 and
            is_on_floor((x1, y1, x2, y2), h) and
            no_person_near((x1, y1, x2, y2), people_boxes)):
            color = (0, 0, 255)
            detections.append(f"{label} — возможно, забыт")
            alert_found = True

        cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(display_frame, f"{label} {conf:.2f}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    cv2.imshow("Результат", display_frame)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    if alert_found:
        filename = os.path.join(SAVE_DIR, "alert_" + os.path.basename(path))
        cv2.imwrite(filename, display_frame)
        result_label.config(text=f"🚨 Найдено: {len(detections)}\nСохранено: {filename}", fg="red")
    else:
        result_label.config(text="✅ Нет подозрительных объектов", fg="green")

# --- Анализ видео ---
def analyze_video(path, result_label, use_custom):
    model_path = "yolo_custom.pt" if use_custom and os.path.exists("yolo_custom.pt") else "yolov8s.pt"
    try:
        MODEL = YOLO(model_path)
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось загрузить модель: {e}")
        return

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        messagebox.showerror("Ошибка", "Не удалось открыть видео")
        return

    frame_count = 0
    alert_found = False
    detections = []

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        if frame_count % 10 != 0:
            frame_count += 1
            continue

        frame_count += 1
        frame = enhance_image(frame)
        frame = sharpen_image(frame)
        display_frame = frame.copy()
        h = frame.shape[0]

        results = MODEL.track(frame, persist=True, conf=CONFIDENCE)
        boxes = results[0].boxes

        people_boxes = []
        for box in boxes:
            cls_id = int(box.cls[0])
            if cls_id == 0:
                try:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    people_boxes.append([x1, y1, x2, y2])
                except:
                    pass

        for box in boxes:
            try:
                cls_id = int(box.cls[0])
                if cls_id not in CLASSES:
                    continue

                x1, y1, x2, y2 = map(int, box.xyxy[0])
                label = MODEL.model.names[cls_id]
                color = COLORS.get(label, (128, 128, 128))
                suspicious = False

                # Проверка: не человек + на полу
                if cls_id != 0 and is_on_floor((x1, y1, x2, y2), h):
                    # Проверка ID
                    if hasattr(box, 'id') and box.id is not None:
                        try:
                            track_id = int(box.id.item())  # .item() — безопасно для tensor
                            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                            if is_stationary(track_id, (cx, cy)) and no_person_near((x1, y1, x2, y2), people_boxes):
                                if track_id not in abandoned_objects:
                                    filename = os.path.join(SAVE_DIR, f"alert_vid_{track_id}_{frame_count}.jpg")
                                    cv2.imwrite(filename, display_frame)
                                    detections.append(f"ID {track_id} ({label})")
                                    abandoned_objects.add(track_id)
                                    alert_found = True
                                suspicious = True
                        except (ValueError, TypeError, IndexError):
                            print(f"⚠️ Не удалось извлечь ID у объекта: {label}")
                    # else: print(f"ℹ️ Объект {label} без ID — не трекается")

                if suspicious:
                    color = (0, 0, 255)

                cv2.rectangle(display_frame, (x1, y1), (x2, y2), color, 2)
                text = f"{label}"

                # Безопасное добавление ID
                if hasattr(box, 'id') and box.id is not None:
                    try:
                        track_id = int(box.id.item())
                        text += f" ID:{track_id}"
                    except (ValueError, TypeError, IndexError):
                        pass

                cv2.putText(display_frame, text, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

            except Exception as e:
                print(f"⚠️ Ошибка при обработке объекта: {e}")
                continue

        status = "🚨 ТРЕВОГА" if alert_found else "Норма"
        cv2.putText(display_frame, status, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255) if alert_found else (0, 255, 0), 2)
        cv2.imshow("Видеоанализ", display_frame)
        if cv2.waitKey(1) == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    result_label.config(text=f"🚨 Забытые: {len(detections)}" if detections else "✅ Нет подозрительных", fg="red" if detections else "green")

# --- GUI ---
class AbandonedDetectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🛡️ Детектор с безопасным трекингом")
        self.root.geometry("800x700")
        self.setup_ui()

    def setup_ui(self):
        nb = ttk.Notebook(self.root)
        nb.pack(fill='both', expand=True)

        # --- Вкладка: Обучение ---
        train_tab = tk.Frame(nb)
        nb.add(train_tab, text="Обучение модели")

        tk.Label(train_tab, text="Обучение YOLOv8 на ваших данных", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(train_tab, text="Папка с изображениями (YOLO-разметка):").pack(pady=5)
        data_frame = tk.Frame(train_tab)
        data_frame.pack(pady=5)
        self.data_path = tk.Entry(data_frame, width=60)
        self.data_path.pack(side="left")
        tk.Button(data_frame, text="📂", command=lambda: self.browse_folder(self.data_path)).pack(side="left", padx=5)

        tk.Label(train_tab, text="Эпохи:").pack(pady=5)
        self.epochs_entry = tk.Entry(train_tab)
        self.epochs_entry.insert(0, "50")
        self.epochs_entry.pack()

        tk.Label(train_tab, text="Размер изображения:").pack(pady=5)
        self.imgsz_entry = tk.Entry(train_tab)
        self.imgsz_entry.insert(0, "640")
        self.imgsz_entry.pack()

        tk.Button(train_tab, text="🚀 Начать обучение", command=self.start_training, bg="green", fg="white").pack(pady=15)
        self.train_result = tk.Label(train_tab, text="Готово", fg="gray")
        self.train_result.pack(pady=10)

        # --- Вкладка: Анализ ---
        analyze_tab = tk.Frame(nb)
        nb.add(analyze_tab, text="Анализ")

        tk.Label(analyze_tab, text="Анализ фото и видео", font=("Arial", 14, "bold")).pack(pady=10)

        tk.Label(analyze_tab, text="Использовать обученную модель:").pack(pady=5)
        self.use_custom = tk.BooleanVar(value=True)
        tk.Checkbutton(analyze_tab, text="Да (если обучили)", variable=self.use_custom).pack()

        tk.Label(analyze_tab, text="Тип файла:").pack(pady=5)
        self.file_type = tk.StringVar(value="photo")
        ttk.Radiobutton(analyze_tab, text="Фото", variable=self.file_type, value="photo").pack()
        ttk.Radiobutton(analyze_tab, text="Видео", variable=self.file_type, value="video").pack()

        tk.Label(analyze_tab, text="Путь к файлу:").pack(pady=5)
        path_frame = tk.Frame(analyze_tab)
        path_frame.pack(pady=5)
        self.file_path = tk.Entry(path_frame, width=60)
        self.file_path.pack(side="left")
        tk.Button(path_frame, text="📂", command=self.browse_file).pack(side="left", padx=5)

        tk.Button(analyze_tab, text="🚀 Анализировать", command=self.analyze, bg="#007ACC", fg="white").pack(pady=15)
        self.analyze_result = tk.Label(analyze_tab, text="Ожидание...", fg="gray", bg="white", relief="sunken", width=80, height=8)
        self.analyze_result.pack(pady=10)

    def browse_folder(self, entry):
        path = filedialog.askdirectory()
        if path:
            entry.delete(0, tk.END)
            entry.insert(0, path)

    def browse_file(self):
        f_type = self.file_type.get()
        filetypes = [("Images", "*.jpg *.jpeg *.png")] if f_type == "photo" else [("Video", "*.mp4 *.avi *.mov")]
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            self.file_path.delete(0, tk.END)
            self.file_path.insert(0, path)

    def start_training(self):
        train_model_gui(self.data_path, self.epochs_entry, self.imgsz_entry, self.train_result)

    def analyze(self):
        f_type = self.file_type.get()
        path = self.file_path.get()
        if not path or not os.path.exists(path):
            messagebox.showerror("Ошибка", "Укажите путь!")
            return
        self.analyze_result.config(text="Анализ...", fg="black")
        self.root.update()
        if f_type == "photo":
            analyze_photo(path, self.analyze_result, self.use_custom.get())
        elif f_type == "video":
            analyze_video(path, self.analyze_result, self.use_custom.get())

if __name__ == "__main__":
    root = tk.Tk()
    app = AbandonedDetectorApp(root)
    root.mainloop()
