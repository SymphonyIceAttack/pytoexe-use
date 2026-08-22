import tkinter as tk
import urllib.request
import json

def fiyat_guncelle():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=mubarak&vs_currencies=try"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode())
            fiyat = data['mubarak']['try']
            label.config(text=f"MUBARAK: ₺{fiyat:.4f}", fg="#00FF66")
    except Exception:
        label.config(text="MUBARAK: Hata!", fg="#FF5555")
    root.after(10000, fiyat_guncelle)

root = tk.Tk()
root.title("MUBARAK Tracker")
root.attributes('-topmost', True)
root.overrideredirect(True)
root.configure(bg='#1E1E2E')

ekran_genislik = root.winfo_screenwidth()
root.geometry(f"170x40+{ekran_genislik - 190}+20")

label = tk.Label(root, text="Yükleniyor...", font=("Consolas", 11, "bold"), bg="#1E1E2E", fg="#FFFFFF")
label.pack(expand=True)

def basla_tasima(event): root.x, root.y = event.x, event.y
def tasiniyor(event): root.geometry(f"+{root.winfo_x() + event.x - root.x}+{root.winfo_y() + event.y - root.y}")

root.bind("<Button-1>", basla_tasima)
root.bind("<B1-Motion>", tasiniyor)
root.bind("<Double-Button-1>", lambda event: root.destroy())

fiyat_guncelle()
root.mainloop()