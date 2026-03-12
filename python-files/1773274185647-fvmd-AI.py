import openai
import pyttsx3
import speech_recognition as sr
import pyautogui
import cv2
import numpy as np
import threading
from ultralytics import YOLO
import time

# ------------- AYARLAR -------------
openai.api_key = "API_KEYİNİ_BURAYA_YAZ"
SCREEN_REGION = None  # Tam ekran, değiştirilebilir
HUMAN_THRESHOLD = 0.5  # Modelin insan algılama güven seviyesi
# ------------------------------------

# Modeli yükle
model = YOLO("yolov8n.pt")  # Küçük ve hızlı model

# Ses motoru
engine = pyttsx3.init()

# Ses tanıma
recognizer = sr.Recognizer()
mic = sr.Microphone()

def speak(text):
    engine.say(text)
    engine.runAndWait()

def chat_with_ai(prompt):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role":"user","content":prompt}]
        )
        return response.choices[0].message.content
    except Exception as e:
        return "Hata: " + str(e)

# Sesli sohbet döngüsü
def voice_chat():
    while True:
        with mic as source:
            print("Dinliyorum...")
            audio = recognizer.listen(source)
        try:
            text = recognizer.recognize_google(audio)
            print("Sen:", text)
            reply = chat_with_ai(text)
            print("AI:", reply)
            speak(reply)
        except sr.UnknownValueError:
            speak("Seni anlayamadım.")
        except Exception as e:
            print("Hata:", e)

# Ekran gözlem fonksiyonu
def screen_monitor():
    alerted = False
    while True:
        screenshot = pyautogui.screenshot(region=SCREEN_REGION)
        frame = np.array(screenshot)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        results = model(frame)

        human_detected = False
        for r in results:
            for box, cls, conf in zip(r.boxes.xyxy, r.boxes.cls, r.boxes.conf):
                if int(cls) == 0 and conf > HUMAN_THRESHOLD:  # COCO class 0 = person
                    human_detected = True
                    break

        if human_detected and not alerted:
            speak("Ekranda insan tespit ettim!")
            alerted = True
        elif not human_detected:
            alerted = False

        time.sleep(0.5)  # yarım saniyede bir kontrol

# 2 thread ile çalıştır
threading.Thread(target=voice_chat).start()
threading.Thread(target=screen_monitor).start()