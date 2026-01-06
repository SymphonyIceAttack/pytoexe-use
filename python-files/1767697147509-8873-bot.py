import tkinter as tk
from tkinter import ttk, scrolledtext
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime
import threading
import time

# ایکسچینج سیٹ اپ
try:
    exchange = ccxt.binance({
        'options': {'defaultType': 'future'},
        'enableRateLimit': True,
    })
    LIVE_MODE = True
except:
    LIVE_MODE = False

symbol = 'BTC/USDT'
depth_levels = 10
volatility_period = 20

def calculate_atr(high, low, close, period=14):
    tr1 = high - low
    tr2 = abs(high - close.shift(1))
    tr3 = abs(low - close.shift(1))
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    atr = tr.rolling(period).mean()
    return atr.iloc[-1] if len(atr) > 0 else 0

def get_signal():
    if LIVE_MODE:
        try:
            orderbook = exchange.fetch_order_book(symbol, limit=depth_levels)
            bids = orderbook['bids']
            asks = orderbook['asks']
            V_bid = sum([level[1] for level in bids])
            V_ask = sum([level[1] for level in asks])
            I_t = (V_bid - V_ask) / (V_bid + V_ask) if (V_bid + V_ask) > 0 else 0

            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=volatility_period + 1)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            atr = calculate_atr(df['high'], df['low'], df['close'])
            current_price = df['close'].iloc[-1]
        except Exception as e:
            return f"ایکسچینج کنکشن ایشو: {str(e)}\nسمولیشن موڈ استعمال کریں۔"
    else:
        current_price = 65000 + np.random.uniform(-1000, 1000)
        I_t = np.random.uniform(-0.3, 0.3)
        atr = 400 + np.random.uniform(-100, 100)

    volatility_factor = atr / current_price if current_price > 0 else 0.01
    base_leverage = 50
    suggested_leverage = max(5, min(125, int(base_leverage / (1 + volatility_factor * 10))))

    if I_t > 0.1:
        direction = "LONG 🚀 (خریداری کا دباؤ)"
        color = "green"
    elif I_t < -0.1:
        direction = "SHORT 🔻 (فروخت کا دباؤ)"
        color = "red"
    else:
        direction = "NEUTRAL ⏸️ (کوئی واضح سگنل نہیں)"
        color = "orange"

    result = f"""
🕐 وقت: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
💰 پیر: {symbol} ({'لائیو' if LIVE_MODE else 'سمولیشن'})
📊 موجودہ قیمت: ${current_price:,.2f}
📈 Imbalance (I_t): {I_t:+.4f}
🔥 Volatility (ATR): {atr:.2f}
⚡ تجویز کردہ Leverage: {suggested_leverage}x
🎯 سگنل: {direction}
"""
    return result, color

def update_signal():
    btn.config(state="disabled")
    status.config(text="سگنل لوڈ ہو رہا ہے...", foreground="blue")
    
    result = get_signal()
    if isinstance(result, tuple):
        text, color = result
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, text)
        text_area.tag_config(color, foreground=color)
        text_area.tag_add(color, "1.0", "end")
    else:
        text_area.delete(1.0, tk.END)
        text_area.insert(tk.END, result)

    status.config(text="تیار ہے! دوبارہ کلک کریں۔", foreground="green")
    btn.config(state="normal")

def on_button_click():
    threading.Thread(target=update_signal).start()

# GUI
root = tk.Tk()
root.title("گاڈزیلا کرپٹو ٹریڈنگ بوٹ ⚡")
root.geometry("600x500")
root.configure(bg="#121212")

title = tk.Label(root, text="گاڈزیلا کرپٹو لیوریج بوٹ", font=("Helvetica", 18, "bold"), fg="#00ff00", bg="#121212")
title.pack(pady=20)

btn = ttk.Button(root, text="نیا سگنل حاصل کریں 🚀", command=on_button_click)
btn.pack(pady=10)

status = tk.Label(root, text="تیار ہے! بٹن دبائیں۔", font=("Helvetica", 12), fg="white", bg="#121212")
status.pack(pady=10)

text_area = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=20, font=("Courier", 11), bg="#1e1e1e", fg="white")
text_area.pack(pady=20, padx=20)

footer = tk.Label(root, text="بنایا گیا Grok کی طرف سے", fg="gray", bg="#121212")
footer.pack(side="bottom", pady=10)

root.mainloop()