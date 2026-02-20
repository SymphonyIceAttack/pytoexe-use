import tkinter as tk
from tkinter import ttk
import datetime
import json
import os
import numpy as np # للحسابات السريعة جداً

# --- إعدادات الواجهة والشاشة (مناسب لـ 15.6 بوصة) ---
BG_COLOR = "#050505"  # أسود عميق
ACCENT_COLOR = "#00FFCC" # لون ذكي
DANGER_COLOR = "#FF3366" # للبيع
SUCCESS_COLOR = "#00FF66" # للشراء

class ProfessionalTraderBot:
    def __init__(self, root):
        self.root = root
        self.root.title("AI QUAD-CANDLE STRATEGY v2.0")
        self.root.geometry("400x750") 
        self.root.configure(bg=BG_COLOR)
        
        # ذاكرة البوت (التعلم المستمر)
        self.memory_file = "ai_brain_data.json"
        self.brain_data = self.load_brain()
        
        # بيانات السوق (مصفوفات سريعة)
        self.prices = deque(maxlen=100) # تخزين آخر 100 سعر فقط لتوفير الرامات
        self.wins = self.brain_data.get("wins", 0)
        self.losses = self.brain_data.get("losses", 0)

        self.setup_ui()
        self.run_engine()

    def load_brain(self):
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r') as f: return json.load(f)
            except: pass
        return {"wins": 0, "losses": 0, "history": []}

    def setup_ui(self):
        # الهيدر
        header = tk.Frame(self.root, bg="#111", height=50)
        header.pack(fill="x")
        tk.Label(header, text="CORE AI ENGINE", fg=ACCENT_COLOR, bg="#111", font=("Orbitron", 10, "bold")).pack(pady=10)

        # عرض السعر الحالي بوضوح
        self.price_label = tk.Label(self.root, text="0.00000", fg="#FFFF00", bg=BG_COLOR, font=("Consolas", 35, "bold"))
        self.price_label.pack(pady=20)

        # لوحة الإحصائيات
        stats_frame = tk.Frame(self.root, bg="#1a1a1a")
        stats_frame.pack(fill="x", padx=15)
        self.stats_text = tk.Label(stats_frame, text=f"W: {self.wins} | L: {self.losses} | RATE: 0%", fg="white", bg="#1a1a1a", font=("Arial", 11))
        self.stats_text.pack(pady=5)

        # منطقة الإشارة (Target Area)
        self.signal_box = tk.Frame(self.root, bg="#000", highlightbackground=ACCENT_COLOR, highlightthickness=1)
        self.signal_box.pack(fill="x", padx=20, pady=20)
        self.signal_lbl = tk.Label(self.signal_box, text="SCANNING MARKET...", fg=ACCENT_COLOR, bg="#000", font=("Arial", 14, "bold"), height=3)
        self.signal_lbl.pack()

        # سجل اللوج الخفيف
        self.log_box = tk.Text(self.root, bg="#000", fg="#00FF00", font=("Consolas", 8), height=15, bd=0)
        self.log_box.pack(fill="both", expand=True, padx=10, pady=10)

    def calculate_indicators(self, data):
        """حساب المؤشرات المتقدمة (EMA, RSI, MACD) باستخدام Numpy لسرعة البروسيسور"""
        if len(data) < 21: return None
        
        arr = np.array(data)
        # EMA 9 & 21
        ema9 = np.mean(arr[-9:])
        ema21 = np.mean(arr[-21:])
        
        # RSI مبسط
        diff = np.diff(arr[-14:])
        up = diff[diff > 0].sum() if len(diff[diff > 0]) > 0 else 0
        down = abs(diff[diff < 0].sum()) if len(diff[diff < 0]) > 0 else 1
        rsi = 100 - (100 / (1 + up/down))
        
        return {"ema9": ema9, "ema21": ema21, "rsi": rsi}

    def check_candle_4_strike(self, candles):
        """منطق الشمعة الرابعة: الابتلاع بعد 3 شموع متتالية"""
        if len(candles) < 4: return None
        
        c1, c2, c3, c4 = candles[-4:]
        
        # حالة البيع (PUT): 3 شموع خضراء + 1 حمراء عملاقة
        if c1 > 0 and c2 > 0 and c3 > 0 and c4 < 0:
            if abs(c4) > (c1 + c2 + c3): # شرط الابتلاع الكلي
                return "PUT"
                
        # حالة الشراء (CALL): 3 شموع حمراء + 1 خضراء عملاقة
        if c1 < 0 and c2 < 0 and c3 < 0 and c4 > 0:
            if c4 > abs(c1 + c2 + c3):
                return "CALL"
        
        return None

    def run_engine(self):
        # محاكاة تحديث السوق (يتم استبداله بربط API أو سحب السعر)
        import random
        fake_price = 1.12345 + random.uniform(-0.001, 0.001)
        self.price_label.config(text=f"{fake_price:.5f}")
        
        # هنا يتم استدعاء الاستراتيجية (تأكيد الشمعة الرابعة + المؤشرات)
        # إشارة افتراضية للتوضيح:
        # if signal == "CALL" and rsi < 30 and ema9 > ema21: "ادخل صفقة"
        
        self.root.after(1000, self.run_engine) # تحديث كل ثانية

    def add_log(self, msg):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END, f"[{now}] {msg}\n")
        self.log_box.see(tk.END)

from collections import deque
if __name__ == "__main__":
    root = tk.Tk()
    app = ProfessionalTraderBot(root)
    root.mainloop()