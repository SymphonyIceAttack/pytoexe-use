import tkinter as tk
from tkinter import messagebox
import requests

# دالة جلب بيانات P2P مع التسميات الجديدة
def get_p2p_data(fiat):
    url = "https://p2p.binance.com/bapi/c2c/v2/friendly/c2c/adv/search"
    def fetch(trade_type):
        payload = {
            "asset": "USDT", "fiat": fiat, "merchantCheck": False,
            "page": 1, "rows": 10, "tradeType": trade_type
        }
        try:
            res = requests.post(url, json=payload, timeout=5).json()
            prices = [float(x['adv']['price']) for x in res['data']]
            return min(prices), max(prices)
        except:
            return 0.0, 0.0
    
    buy_min, buy_max = fetch("BUY")
    sell_min, sell_max = fetch("SELL")
    return buy_min, buy_max, sell_min, sell_max

# دالة جلب الأسعار الرسمية
def get_official():
    try:
        res = requests.get("https://api.exchangerate-api.com/v4/latest/USD", timeout=5).json()
        return res['rates']['EGP'], res['rates']['AED']
    except:
        return 0, 0

def refresh():
    status_label.config(text="🔄 جاري سحب الأسعار من بينانس والمصادر الرسمية...", fg="#d35400")
    root.update()
    
    egp_official, aed_official = get_official()
    if egp_official == 0:
        messagebox.showerror("خطأ", "تأكد من اتصالك بالإنترنت!")
        return

    # 1. تحديث الرسمي والعكسي
    aed_to_egp = egp_official / aed_official
    official_egp_val.config(text=f"1$ = {egp_official:.2f} EGP | 1 EGP = {1/egp_official:.4f} $")
    official_aed_val.config(text=f"1$ = {aed_official:.2f} AED | 1 AED = {1/aed_official:.4f} $")
    official_cross_val.config(text=f"1 AED = {aed_to_egp:.2f} EGP | 1 EGP = {1/aed_to_egp:.4f} AED")

    # 2. تحديث P2P (سوق الأفراد)
    e_b_min, e_b_max, e_s_min, e_s_max = get_p2p_data("EGP")
    p2p_egp_val.config(text=f"شراء (أفراد): {e_b_min} - {e_b_max} | بيع (أفراد): {e_s_min} - {e_s_max}")

    a_b_min, a_b_max, a_s_min, a_s_max = get_p2p_data("AED")
    p2p_aed_val.config(text=f"شراء (أفراد): {a_b_min} - {a_b_max} | بيع (أفراد): {a_s_min} - {a_s_max}")

    status_label.config(text="✅ تم التحديث بنجاح.. البرنامج الآن في وضع السكون", fg="#27ae60")

# --- تصميم الواجهة ---
root = tk.Tk()
root.title("Price Monitor Pro 2026 - USD/EGP/AED")
root.geometry("550x700")
root.configure(bg="#fdfefe")

# استايلات
header_f = ("Arial", 11, "bold")
val_f = ("Consolas", 10, "bold")

# قسم البنك المركزي
tk.Label(root, text="🏛️ السعر الرسمي (البنك المركزي)", fg="#2c3e50", bg="#fdfefe", font=header_f, pady=10).pack()
official_egp_val = tk.Label(root, text="---", bg="#ebf5fb", font=val_f, width=60, pady=10); official_egp_val.pack(pady=2)
official_aed_val = tk.Label(root, text="---", bg="#ebf5fb", font=val_f, width=60, pady=10); official_aed_val.pack(pady=2)
official_cross_val = tk.Label(root, text="---", bg="#ebf5fb", font=val_f, width=60, pady=10); official_cross_val.pack(pady=2)

tk.Label(root, text="──────────────────────────────", fg="#bdc3c7", bg="#fdfefe").pack()

# قسم بينانس P2P
tk.Label(root, text="🤝 سعر سوق الأفراد (Binance P2P)", fg="#e67e22", bg="#fdfefe", font=header_f, pady=10).pack()

tk.Label(root, text="USDT مقابل الجنيه المصري (EGP)", bg="#fdfefe").pack()
p2p_egp_val = tk.Label(root, text="---", bg="#fef9e7", font=val_f, width=60, pady=15, relief="flat"); p2p_egp_val.pack(pady=5)

tk.Label(root, text="USDT مقابل الدرهم الإماراتي (AED)", bg="#fdfefe").pack()
p2p_aed_val = tk.Label(root, text="---", bg="#fef9e7", font=val_f, width=60, pady=15, relief="flat"); p2p_aed_val.pack(pady=5)

status_label = tk.Label(root, text="جاهز للعمل", bg="#fdfefe", pady=20)
status_label.pack()

# زر التحديث
btn = tk.Button(root, text="تحديث الأسعار الآن 🔄", command=refresh, bg="#27ae60", fg="white", font=("Arial", 12, "bold"), width=30, height=2, cursor="hand2", relief="flat")
btn.pack(pady=10)

root.mainloop()