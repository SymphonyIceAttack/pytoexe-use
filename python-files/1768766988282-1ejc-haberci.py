import requests
import time
import webbrowser
import os

# --- AYARLARINIZI BURADAN YAPIN ---
API_URL = "https://kentkolejisporkulubu.org/wp-json/okul/v1/yayin-durumu"
YAYIN_URL = "https://kentkolejisporkulubu.org/canli-yayin" # Kısa kodun olduğu sayfa adresi
KONTROL_SANIYESI = 15

# Bilgisayarın hangi kampüste olduğunu dosyadan okur
def kampus_oku():
    if os.path.exists("kampus.txt"):
        with open("kampus.txt", "r", encoding="utf-8") as f:
            return f.read().strip().lower()
    return "genel" # Dosya yoksa tüm genel yayınları alır

def kontrol_et():
    yayin_aktif_mi = False
    bilgisayar_kampusu = kampus_oku()
    print(f"Haberci Aktif. Kampüs: {bilgisayar_kampusu}")
    
    while True:
        try:
            r = requests.get(API_URL, timeout=10)
            if r.status_code == 200:
                data = r.json()
                durum = data.get('durum')
                hedef = data.get('kampus')

                # Eğer yayın açıksa VE (hedef genel ise VEYA tam bu kampüs ise)
                if durum == 'acik' and not yayin_aktif_mi:
                    if hedef == 'genel' or hedef == bilgisayar_kampusu:
                        print("Flaş: Yayın bu kampüs için başlatıldı! Chrome açılıyor...")
                        webbrowser.open(YAYIN_URL)
                        yayin_aktif_mi = True
                
                # Yayın kapandığında durumu sıfırla
                if durum == 'kapali':
                    yayin_aktif_mi = False
            
        except Exception as e:
            print("Hata (İnternet/Sunucu):", e)
            
        time.sleep(KONTROL_SANIYESI)

if __name__ == "__main__":
    kontrol_et()