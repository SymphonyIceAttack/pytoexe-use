import pygame
import sys
import speech_recognition as sr
import pyttsx3
import os
import threading
from google import genai

# ---------- Gemini API Ayarları ----------
API_ANAHTARI = "AIzaSyCQtAp9vmI3BT5TF-8IxSSLlKBOCZDneto"
client = genai.Client(api_key=API_ANAHTARI)

def get_available_model():
    try:
        models = client.models.list()
        for model in models:
            if "gemini" in model.name and "generateContent" in str(model.supported_actions):
                return model.name.replace("models/", "")
        return None
    except Exception as e:
        print(f"Model listesi alınamadı: {e}")
        return None

MODEL_ADI = get_available_model()
if MODEL_ADI:
    print(f"Kullanılacak model: {MODEL_ADI}")
else:
    print("Hiçbir uygun model bulunamadı! Varsayılan olarak 'gemini-1.5-flash' deneniyor.")
    MODEL_ADI = "gemini-1.5-flash"

def soru_sor(prompt):
    try:
        response = client.models.generate_content(
            model=MODEL_ADI,
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"🚨 Gemini API HATASI: {e}")
        return None

# ---------- Ses Tanıma ----------
def dinle():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("🎤 Dinliyorum...")
        r.adjust_for_ambient_noise(source)
        try:
            ses = r.listen(source, timeout=3, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            return ""
    try:
        yazi = r.recognize_google(ses, language="tr-TR")
        print(f"📝 Söylenen: {yazi}")
        return yazi.lower()
    except sr.UnknownValueError:
        return ""
    except sr.RequestError as e:
        print(f"🌐 Bağlantı hatası: {e}")
        return ""

# ---------- Konuşma Sentezi (Thread'li ve Durdurulabilir) ----------
class KonusmaThread(threading.Thread):
    def __init__(self, metin):
        super().__init__()
        self.metin = metin
        self.durduruldu = False  # flag adını değiştirdik
        self.engine = None

    def run(self):
        try:
            self.engine = pyttsx3.init()
            self.engine.setProperty('rate', 150)
            sesler = self.engine.getProperty('voices')
            for ses in sesler:
                if 'turkish' in ses.name.lower() or 'tr' in ses.id.lower():
                    self.engine.setProperty('voice', ses.id)
                    break
            self.engine.say(self.metin)
            # Konuşma devam ederken durduruldu flag'ini kontrol et
            # runAndWait bloklayıcı olduğu için araya giremeyiz, ancak engine.stop() ile dışarıdan durdurabiliriz.
            if not self.durduruldu:
                self.engine.runAndWait()
        except Exception as e:
            print(f"🔇 Konuşma hatası: {e}")
        finally:
            if self.engine:
                self.engine.stop()

    def durdur(self):
        self.durduruldu = True
        if self.engine:
            self.engine.stop()

konusma_thread = None

def konus(metin):
    global konusma_thread
    # Önceki konuşma hala devam ediyorsa durdur
    if konusma_thread and konusma_thread.is_alive():
        konusma_thread.durdur()
        konusma_thread.join()
    # Yeni konuşma thread'ini başlat
    konusma_thread = KonusmaThread(metin)
    konusma_thread.start()
    print(f"🔊 Konuşuluyor: {metin}")

# ---------- Karakter Çizimi ----------
def ciz(pencere, konusuyor_mu):
    YESIL = (0, 255, 0)
    SIYAH = (0, 0, 0)
    BEYAZ = (255, 255, 255)
    
    pencere.fill(BEYAZ)
    pygame.draw.circle(pencere, YESIL, (150, 120), 30)
    pygame.draw.circle(pencere, YESIL, (250, 120), 30)
    if konusuyor_mu:
        uzunluk = 50 + (pygame.time.get_ticks() % 30)
    else:
        uzunluk = 50
    baslangic = (200 - uzunluk // 2, 200)
    bitis = (200 + uzunluk // 2, 200)
    pygame.draw.line(pencere, SIYAH, baslangic, bitis, 5)
    pygame.display.update()

# ---------- Komut İşleme ----------
def komut_islem(komut):
    if "hesap makinesi" in komut:
        os.system("calc")
        return "Hesap makinesi açılıyor."
    elif "gdevelop" in komut or "motor" in komut:
        try:
            os.startfile(r"C:\Users\Public\Desktop\GDevelop 5.lnk")
            return "kanatlar açılıyor."
        except Exception as e:
            return f"sorun açılamadı: {e}"
    elif "not defteri" in komut:
        os.system("notepad")
        return "Not defteri açılıyor."
    elif "tarayıcı" in komut or "chrome" in komut:
        os.startfile("https://www.google.com")
        return "Tarayıcı açılıyor."
    elif "youtube" in komut or "yt" in komut:
        os.startfile("https://www.youtube.com/watch?v=7hdroVY1uuo&list=RD7hdroVY1uuo&start_radio=1")
        return "yt açılıyor."
    elif "kapat" in komut or "görüşürüz" in komut:
        return "kapat"
    else:
        print("🤔 API'ye soruluyor...")
        cevap = soru_sor(komut)
        if cevap:
            return cevap
        else:
            return "Şu anda cevap veremiyorum ama uygulamaları açabilirim."

# ---------- Ana Döngü ----------
def main():
    global konusma_thread
    pygame.init()
    pencere = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Akıllı Asistan")
    clock = pygame.time.Clock()
    
    konusuyor_mu = False
    calisiyor = True
    
    print("🌟 Akıllı asistan başlatıldı!")
    print("Örnek: 'merhaba', 'nasılsın', 'hesap makinesi', 'kapat'")
    print("İstediğin her şeyi sorabilirsin!")
    print("🛑 Space tuşuna basarak konuşmayı durdurabilirsin.")
    
    konus("Merhaba, ben akıllı asistanınız. Size nasıl yardımcı olabilirim?")
    
    while calisiyor:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                calisiyor = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    print("🛑 Konuşma durduruluyor...")
                    if konusma_thread and konusma_thread.is_alive():
                        konusma_thread.durdur()
                        konusma_thread.join()
        
        ses = dinle()
        if ses:
            konusuyor_mu = True
            cevap = komut_islem(ses)
            if cevap == "kapat":
                konus("Görüşürüz!")
                calisiyor = False
            else:
                konus(cevap)
            konusuyor_mu = False
        
        # Konuşma durumunu thread'den al
        if konusma_thread and konusma_thread.is_alive():
            konusuyor_mu = True
        else:
            konusuyor_mu = False
        
        ciz(pencere, konusuyor_mu)
        clock.tick(30)
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
