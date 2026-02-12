import tkinter as tk
import speech_recognition as sr
import os
import threading

def bilgisayari_kapat():
    os.system("shutdown /s /t 1")

def dinle():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        durum_label.config(text="Dinleniyor...")
        r.adjust_for_ambient_noise(source)
        while True:
            try:
                audio = r.listen(source)
                komut = r.recognize_google(audio, language="tr-TR").lower()
                sonuc_label.config(text=f"Algılanan: {komut}")

                if "bilgisayarı kapat" in komut:
                    bilgisayari_kapat()
                    break
            except:
                pass

def dinlemeyi_baslat():
    threading.Thread(target=dinle).start()

# Pencere oluştur
pencere = tk.Tk()
pencere.title("Sesli Asistan")
pencere.geometry("400x250")

baslik = tk.Label(pencere, text="Sesli PC Kapatma", font=("Arial", 16))
baslik.pack(pady=10)

durum_label = tk.Label(pencere, text="Hazır")
durum_label.pack(pady=5)

sonuc_label = tk.Label(pencere, text="")
sonuc_label.pack(pady=5)

buton = tk.Button(pencere, text="Dinlemeyi Başlat", command=dinlemeyi_baslat)
buton.pack(pady=20)

pencere.mainloop()
