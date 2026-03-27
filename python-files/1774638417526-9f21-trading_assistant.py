# trading_assistant.py
import pandas as pd
import numpy as np
import os
from binance.client import Client
from binance.streams import ThreadedWebsocketManager
from sklearn.linear_model import SGDClassifier
import joblib
import ta
import warnings
warnings.filterwarnings('ignore')

# -----------------------------
# CONFIGURATION
# -----------------------------
api_key = ""  # optional for public data; leave empty for no trading
api_secret = ""
symbol = "BTCUSDT"
interval = '1m'
model_file = "model/self_learning_model.pkl"
signal_thresholds = {'strong_buy':0.8,'buy':0.6,'sell':0.4,'strong_sell':0.2}
X_columns = ['ema5','ema20','rsi','macd','bollinger']

# Ensure model folder exists
os.makedirs("model", exist_ok=True)

# Binance client and websocket manager
client = Client(api_key, api_secret)
twm = ThreadedWebsocketManager()
twm.start()

# Load or initialize model
if os.path.exists(model_file):
    model = joblib.load(model_file)
    first_run = False
else:
    model = SGDClassifier(loss="log")
    first_run = True

# Dataframe to store live prices
df = pd.DataFrame(columns=['close'])
signal_log = []
current_signal = "Waiting for data..."

# -----------------------------
# Helper functions
# -----------------------------
def compute_features(df):
    df['ema5'] = df['close'].ewm(span=5).mean()
    df['ema20'] = df['close'].ewm(span=20).mean()
    df['rsi'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    df['macd'] = ta.trend.MACD(df['close']).macd()
    df['bollinger'] = ta.volatility.BollingerBands(df['close']).bollinger_hband() - ta.volatility.BollingerBands(df['close']).bollinger_lband()
    return df.dropna()

def label_data(df, horizon=5, threshold=0.01):
    df['future_return'] = df['close'].shift(-horizon)/df['close'] - 1
    df['label'] = np.where(df['future_return']>threshold,1,
                           np.where(df['future_return']<-threshold,0,-1))
    return df.dropna()

def generate_signal(prob):
    global current_signal
    if prob > signal_thresholds['strong_buy']:
        current_signal = f"[STRONG BUY] {prob:.2f}"
    elif prob > signal_thresholds['buy']:
        current_signal = f"[BUY] {prob:.2f}"
    elif prob < signal_thresholds['strong_sell']:
        current_signal = f"[STRONG SELL] {prob:.2f}"
    elif prob < signal_thresholds['sell']:
        current_signal = f"[SELL] {prob:.2f}"
    else:
        current_signal = f"[NEUTRAL] {prob:.2f}"
    signal_log.append(current_signal)
    if len(signal_log) > 20:
        signal_log.pop(0)

# -----------------------------
# Websocket handler
# -----------------------------
def handle_socket_message(msg):
    global df, model, first_run
    if msg['e'] != 'kline': 
        return
    k = msg['k']
    close = float(k['c'])
    df = pd.concat([df, pd.DataFrame([[close]], columns=['close'])], ignore_index=True)
    if len(df) < 30:
        return
    
    df = compute_features(df)
    df = label_data(df)
    
    batch = df[df['label']!=-1]
    if len(batch) > 5:
        X = batch[X_columns].values
        y = batch['label'].values
        if first_run:
            model.partial_fit(X, y, classes=[0,1])
            first_run = False
        else:
            model.partial_fit(X, y)
        joblib.dump(model, model_file)
    
    latest = df[X_columns].iloc[-1].values.reshape(1,-1)
    prob = model.predict_proba(latest)[0][1]
    generate_signal(prob)
    print(f"{current_signal}  |  Price: {close:.2f}")

# Start websocket
twm.start_kline_socket(callback=handle_socket_message, symbol=symbol, interval=interval)

print("Self-learning trading assistant running...")
print("Waiting for data…")

# Keep script running
try:
    while True:
        pass
except KeyboardInterrupt:
    print("Exiting...")
finally:
    twm.stop()