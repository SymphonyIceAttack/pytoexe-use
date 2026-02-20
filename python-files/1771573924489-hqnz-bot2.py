import time, threading, re, os, json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.firefox.options import Options
import tkinter as tk
from tkinter import filedialog, messagebox
from telethon import TelegramClient, events
import numpy as np
from collections import deque

# ================= CONFIG =================
API_ID = 23266065
API_HASH = '69a3ab80862efbf72f96b7366bf7ba90'
TARGET_CHANNELS = ['Mk07mm', 'FutureSignalsPocket', 'JokerTrading']
KNOWLEDGE_FILE = "ai_persistent_brain.json"

class AI_Hybrid_Master_V27:
    def __init__(self, root):
        self.root = root
        self.root.title("AI HYBRID SNIPER V27 - SMART OTC")
        self.root.geometry("500x900")
        self.root.configure(bg="#050505")

        # ---------------- DATA ----------------
        self.prices = deque(maxlen=4000) # لتغطية 15 دقيقة تقريبا
        self.candles_history = []        # جسم الشمعة (Close - Open)
        self.brain_data = self.load_brain()
        self.wins, self.losses = 0, 0

        self.setup_ui()
        self.init_browser()
        
        # Threads
        threading.Thread(target=self.price_engine, daemon=True).start()
        threading.Thread(target=self.start_telegram, daemon=True).start()
        threading.Thread(target=self.early_warning_worker, daemon=True).start()

    # ---------------- UI ----------------
    def setup_ui(self):
        tk.Label(self.root, text="CORE AI HYBRID ENGINE V27", fg="#00FFCC", bg="#111", font=("Orbitron", 12, "bold")).pack(pady=10)
        self.price_lbl = tk.Label(self.root, text="0.00000", fg="#FFFF00", bg="#050505", font=("Consolas", 50, "bold"))
        self.price_lbl.pack(pady=20)

        self.signal_lbl = tk.Label(self.root, text="SCANNING MARKET...", fg="#00FFCC", bg="#000", font=("Arial", 12, "bold"), height=3)
        self.signal_lbl.pack(fill="x", padx=30, pady=5)

        btn_frame = tk.Frame(self.root, bg="#050505")
        btn_frame.pack(fill="x", padx=20, pady=5)
        tk.Button(btn_frame, text="EXPORT BRAIN", command=self.export_brain, bg="#0055ff", fg="white").pack(side="left", expand=True, padx=5)
        tk.Button(btn_frame, text="DEEP STUDY", command=self.deep_study, bg="#ff3366", fg="white").pack(side="right", expand=True, padx=5)

        self.log_box = tk.Text(self.root, bg="#000", fg="#00FF66", font=("Consolas", 9), height=20)
        self.log_box.pack(fill="both", expand=True, padx=15, pady=10)
        self.stats_lbl = tk.Label(self.root, text="W:0 | L:0 | ACC:0% | Patterns:0", fg="#aaa", bg="#050505")
        self.stats_lbl.pack(fill="x", pady=5)

    # ---------------- BRAIN ----------------
    def load_brain(self):
        if os.path.exists(KNOWLEDGE_FILE):
            with open(KNOWLEDGE_FILE, 'r') as f: return json.load(f)
        return {"patterns": {}, "total_trades": 0}

    def export_brain(self):
        path = filedialog.asksaveasfilename(defaultextension=".json")
        if path:
            with open(path, 'w') as f: json.dump(self.brain_data, f, indent=4)
            messagebox.showinfo("Success", "تم تصدير الخبرات!")

    def deep_study(self):
        self.brain_data["patterns"] = {k:v for k,v in self.brain_data["patterns"].items() if (v["wins"]/(v["wins"]+v["losses"]+1e-9)>0.4)}
        self.add_log("🧠 AI: Brain Optimized.")

    # ---------------- INDICATORS ----------------
    def calculate_indicators(self):
        if len(self.prices)<21: return None
        arr = np.array(list(self.prices))
        ema9 = arr[-9:].mean()
        ema21 = arr[-21:].mean()
        diff = np.diff(arr[-14:])
        up = diff[diff>0].sum() if len(diff)>0 else 0
        down = abs(diff[diff<0].sum()) if len(diff)>0 else 1
        rsi = 100 - (100/(1+up/down))
        return {"ema9": ema9, "ema21": ema21, "rsi": rsi}

    def get_trends(self):
        if len(self.prices)<3000: return None,None
        trend_5m = "UP" if self.prices[-1000] > self.prices[-2000] else "DOWN"
        trend_15m = "UP" if self.prices[-3000] > self.prices[-4000] else "DOWN"
        return trend_5m, trend_15m

    # ---------------- QUAD CANDLE ----------------
    def check_quad_candle_strike(self):
        if len(self.candles_history)<4: return None
        c1,c2,c3,c4 = self.candles_history[-4:]
        if c1>0 and c2>0 and c3>0 and c4<0 and abs(c4)>(c1+c2+c3): return "PUT"
        if c1<0 and c2<0 and c3<0 and c4>0 and c4>abs(c1+c2+c3): return "CALL"
        return None

    # ---------------- EARLY WARNING ----------------
    def early_warning_worker(self):
        while True:
            try:
                now = datetime.now()
                if now.second==30 and (now.minute%6==2):
                    if len(self.candles_history)>=2:
                        c1,c2 = self.candles_history[-2:]
                        warn_dir = "PUT" if c1>0 and c2>0 else "CALL" if c1<0 and c2<0 else None
                        if warn_dir:
                            self.add_log(f"🔔 EARLY ALERT: Potential {warn_dir} setup!")
                            self.signal_lbl.config(text=f"⚠️ PREPARE {warn_dir} (90s REMAINING)", fg="#FFA500")
            except: pass
            time.sleep(1)

    # ---------------- PRICE ENGINE ----------------
    def price_engine(self):
        while True:
            try:
                p_text = self.driver.find_element(By.CSS_SELECTOR,".current-price").text
                price = float(p_text.replace(",",""))
                self.prices.append(price)
                self.price_lbl.config(text=f"{price:.5f}")

                now=datetime.now()
                if not hasattr(self,'cur_c') or now.second==0:
                    if hasattr(self,'cur_c'):
                        self.candles_history.append(self.cur_c['c']-self.cur_c['o'])
                        if len(self.candles_history)>20: self.candles_history.pop(0)
                        self.auto_check_market()
                    self.cur_c={'o':price,'c':price}
                else:
                    self.cur_c['c']=price
            except: pass
            time.sleep(0.4)

    def auto_check_market(self):
        signal = self.check_quad_candle_strike()
        ind = self.calculate_indicators()
        trend_5m, trend_15m = self.get_trends()
        if signal and ind and trend_5m and trend_15m:
            # فلترة حسب الترند EMA RSI
            if ((signal=="CALL" and trend_5m=="UP" and trend_15m=="UP" and ind['ema9']>ind['ema21'] and ind['rsi']<70) or
                (signal=="PUT"  and trend_5m=="DOWN" and trend_15m=="DOWN" and ind['ema9']<ind['ema21'] and ind['rsi']>30)):
                self.add_log(f"⚡ Pattern+Trend Confirmed: {signal}")
                self.audit_and_execute("AUTO_STRATEGY",signal)

    # ---------------- EXECUTION ----------------
    def audit_and_execute(self,pair,direction):
        ind = self.calculate_indicators()
        if not ind: return
        rsi_rounded = round(ind['rsi']/2)*2
        pattern_key=f"{pair}_{direction}_RSI{rsi_rounded}"
        if pattern_key in self.brain_data["patterns"]:
            data=self.brain_data["patterns"][pattern_key]
            if (data["wins"]+data["losses"])>2 and (data["wins"]/(data["wins"]+data["losses"]))<0.45:
                self.add_log(f"🚫 AI REJECT: Bad Pattern History")
                return
        self.signal_lbl.config(text=f"🔥 EXECUTE: {direction}",fg="#00FF66")
        self.add_log(f"🚀 Executing: {pair} -> {direction}")
        en=self.prices[-1]
        threading.Timer(60,self.evaluate,[pair,direction,en,pattern_key]).start()

    def evaluate(self,p,d,en,pat):
        ex=self.prices[-1]
        win=(ex>en) if d=="CALL" else (ex<en)
        res="WIN" if win else "LOSS"
        if win:self.wins+=1
        else:self.losses+=1
        if pat not in self.brain_data["patterns"]: self.brain_data["patterns"][pat]={"wins":0,"losses":0}
        self.brain_data["patterns"][pat]["wins" if win else "losses"]+=1
        with open(KNOWLEDGE_FILE,'w') as f: json.dump(self.brain_data,f)
        self.update_stats()
        self.add_log(f"📊 {res} | AI Brain Updated.")
        self.signal_lbl.config(text="SCANNING MARKET...",fg="#00FFCC")

    # ---------------- SYSTEM ----------------
    def init_browser(self):
        opts=Options()
        self.driver=webdriver.Firefox(options=opts)
        self.driver.get("https://pocketoption.com/en/trade")

    def start_telegram(self):
        client=TelegramClient("hybrid_v27",API_ID,API_HASH)
        @client.on(events.NewMessage(chats=TARGET_CHANNELS))
        async def handler(event):
            msg=event.raw_text.upper()
            pair=re.search(r'([A-Z]{6}-OTC)',msg)
            direction=re.search(r'(CALL|PUT|BUY|SELL|UP|DOWN)',msg)
            if pair and direction:
                d="CALL" if direction.group(1) in ["CALL","BUY","UP"] else "PUT"
                self.audit_and_execute(pair.group(1),d)
        client.start(); client.run_until_disconnected()

    def update_stats(self):
        total=self.wins+self.losses
        acc=(self.wins/total)*100 if total>0 else 0
        self.stats_lbl.config(text=f"W:{self.wins} | L:{self.losses} | ACC:{acc:.1f}% | Patterns:{len(self.brain_data['patterns'])}")

    def add_log(self,msg):
        now=datetime.now().strftime("%H:%M:%S")
        self.log_box.insert(tk.END,f"[{now}] {msg}\n")
        self.log_box.see(tk.END)

if __name__=="__main__":
    root=tk.Tk()
    app=AI_Hybrid_Master_V27(root)
    root.mainloop()