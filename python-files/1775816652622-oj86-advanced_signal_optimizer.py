import os
import time
import sqlite3
import pandas as pd
from datetime import datetime
from sklearn.tree import DecisionTreeClassifier, export_text

# ============================================================
# CONFIGURATION
# ============================================================

MT4_DATA_PATH = r"C:\Users\Administrator\AppData\Roaming\MetaQuotes\Terminal\5D49F47D1EA1ECFC0DDC965B6D100AC5"

LOG_FOLDER = os.path.join(MT4_DATA_PATH, "MQL4", "Logs")
FILES_FOLDER = os.path.join(MT4_DATA_PATH, "MQL4", "Files")

DATABASE_FILE = os.path.join(FILES_FOLDER, "advanced_signals.db")

# ============================================================
# CREATE REQUIRED DIRECTORIES
# ============================================================

def ensure_directories():
    os.makedirs(LOG_FOLDER, exist_ok=True)
    os.makedirs(FILES_FOLDER, exist_ok=True)

# ============================================================
# DATABASE SETUP
# ============================================================

def setup_database():

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signal_features (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp INTEGER,
            datetime TEXT,
            indicator TEXT,
            signal_type TEXT,
            entry_price REAL,
            result TEXT,
            profit_pips REAL,
            rsi_h1 REAL,
            adx_h1 REAL,
            volume_ratio_h1 REAL,
            zone_position TEXT,
            zone_percent REAL,
            chart_pattern TEXT,
            hour_of_day INTEGER,
            htf_trend_h4 TEXT
        )
    """)

    conn.commit()
    conn.close()

# ============================================================
# SAMPLE MARKET CONTEXT
# ============================================================

def get_sample_market_context():

    return {
        "rsi_h1": 45,
        "adx_h1": 28,
        "volume_ratio_h1": 1.3,
        "zone_position": "BOTTOM",
        "zone_percent": 15,
        "chart_pattern": "BULLISH_ENGULFING",
        "hour_of_day": datetime.now().hour,
        "htf_trend_h4": "BULLISH"
    }

# ============================================================
# STORE SIGNAL
# ============================================================

def store_signal(indicator, signal_type, price, result, profit):

    context = get_sample_market_context()

    conn = sqlite3.connect(DATABASE_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO signal_features (
            timestamp,
            datetime,
            indicator,
            signal_type,
            entry_price,
            result,
            profit_pips,
            rsi_h1,
            adx_h1,
            volume_ratio_h1,
            zone_position,
            zone_percent,
            chart_pattern,
            hour_of_day,
            htf_trend_h4
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        int(time.time()),
        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        indicator,
        signal_type,
        price,
        result,
        profit,
        context["rsi_h1"],
        context["adx_h1"],
        context["volume_ratio_h1"],
        context["zone_position"],
        context["zone_percent"],
        context["chart_pattern"],
        context["hour_of_day"],
        context["htf_trend_h4"]
    ))

    conn.commit()
    conn.close()

    print("Signal stored")

# ============================================================
# MACHINE LEARNING ANALYSIS
# ============================================================

def discover_winning_combinations():

    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query("SELECT * FROM signal_features", conn)
    conn.close()

    if len(df) < 10:
        print("Need at least 10 signals")
        return

    df["target"] = (df["result"] == "WIN").astype(int)

    df["zone_num"] = df["zone_position"].map({
        "BOTTOM": 0,
        "MIDDLE": 1,
        "TOP": 2
    })

    df["trend_num"] = df["htf_trend_h4"].map({
        "BEARISH": -1,
        "NEUTRAL": 0,
        "BULLISH": 1
    })

    features = [
        "rsi_h1",
        "adx_h1",
        "volume_ratio_h1",
        "zone_percent",
        "hour_of_day",
        "zone_num",
        "trend_num"
    ]

    df = df.dropna(subset=features)

    X = df[features]
    y = df["target"]

    model = DecisionTreeClassifier(max_depth=4)

    model.fit(X, y)

    rules = export_text(model, feature_names=features)

    print("\nMachine Learning Rules:\n")
    print(rules)

# ============================================================
# PERFORMANCE REPORT
# ============================================================

def generate_analysis():

    conn = sqlite3.connect(DATABASE_FILE)
    df = pd.read_sql_query("SELECT * FROM signal_features", conn)
    conn.close()

    if df.empty:
        print("No signals in database")
        return

    total = len(df)
    wins = (df["result"] == "WIN").sum()

    win_rate = wins / total * 100

    print("\n========== SIGNAL ANALYSIS ==========")
    print("Total Signals:", total)
    print("Wins:", wins)
    print("Win Rate:", round(win_rate,2), "%")

    discover_winning_combinations()

# ============================================================
# MAIN PROGRAM
# ============================================================

def main():

    ensure_directories()

    setup_database()

    print("Advanced Signal Optimizer Started")

    while True:

        print("\nCommands:")
        print("1 = Insert test signal")
        print("2 = Run analysis")
        print("3 = Exit")

        cmd = input("Enter option: ")

        if cmd == "1":

            store_signal(
                indicator="RSI",
                signal_type="BUY",
                price=1950.25,
                result="WIN",
                profit=22
            )

        elif cmd == "2":

            generate_analysis()

        elif cmd == "3":

            break

        else:

            print("Invalid command")

if __name__ == "__main__":
    main()