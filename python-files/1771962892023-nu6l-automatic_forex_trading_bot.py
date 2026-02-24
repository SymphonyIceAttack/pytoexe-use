#!/usr/bin/env python3
"""
MT5 DEMO TRADING BOT - ULTIMATE EDITION (EXE VERSION)
ALLE TAKTIKEN + MULTI-TP + PROGRESSIVER STOP-LOSS
NUR VERBINDUNG ZU LAUFENDEM MT5
"""

import time
import sys
import os
import subprocess
from datetime import datetime, timedelta
import math
import logging
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import traceback
import random
import statistics
from enum import Enum
import csv
from collections import deque

# ====== Versuche MetaTrader5 zu importieren, falls nicht vorhanden -> installieren ======
try:
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 bereits installiert")
except ImportError:
    print("📦 Installiere MetaTrader5...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "MetaTrader5"])
    import MetaTrader5 as mt5
    print("✅ MetaTrader5 installiert")

# ====== Weitere benötigte Pakete ======
try:
    import pandas as pd
    import numpy as np
    print("✅ pandas, numpy bereits installiert")
except ImportError:
    print("📦 Installiere weitere Pakete...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pandas", "numpy"])
    import pandas as pd
    import numpy as np
    print("✅ Pakete installiert")

print("=" * 80)
print("🤖 MT5 TRADING BOT - ULTIMATE EDITION (EXE VERSION)")
print("=" * 80)
print("📌 WICHTIG: Stelle sicher, dass MT5 BEREITS LÄUFT und du")
print("📌 eingeloggt bist, bevor du dieses Programm startest!")
print("=" * 80)

# ============================================================================
# KONFIGURATION
# ============================================================================

@dataclass
class BotConfig:
    # MT5 Demo Daten (nur für Info)
    login: int = 103520676
    passwort: str = "2tFmLn*x"
    server: str = "MetaQuotes-Demo"
    
    # Trading Parameter
    hebel: int = 500
    scan_zeit: int = 10
    max_positionen: int = 25
    risiko_pro_trade: float = 0.01          # 1% Risiko pro Trade
    
    # Stop-Loss Taktik (original)
    stop_loss_initial: float = 0.20          # 20% initial
    trailing_stop_prozent: float = 0.70      # 70% vom Höchstgewinn sichern
    breakeven_aktivierung: float = 0.003     # 0.3% Gewinn -> Break-even
    
    # Multi-Take Profit Levels
    tp_levels: List[Dict] = field(default_factory=lambda: [
        {'faktor': 1.5, 'schliessen': 0.25, 'name': 'TP1'},
        {'faktor': 2.0, 'schliessen': 0.25, 'name': 'TP2'},
        {'faktor': 2.5, 'schliessen': 0.20, 'name': 'TP3'},
        {'faktor': 3.0, 'schliessen': 0.15, 'name': 'TP4'},
        {'faktor': 4.0, 'schliessen': 0.10, 'name': 'TP5'},
        {'faktor': 5.0, 'schliessen': 0.05, 'name': 'TP6'},
    ])
    
    # Spread Limits pro Symbol
    max_spread_pips: Dict[str, int] = field(default_factory=lambda: {
        "DEFAULT": 3,
        "XAUUSD": 20, "XAGUSD": 15,
        "BTCUSD": 50, "ETHUSD": 40,
        "US30": 10, "NAS100": 12,
        "GER40": 8, "UK100": 8,
    })
    
    # Strategie-Gewichtung (für spätere Erweiterung)
    strategie_gewichte: Dict[str, float] = field(default_factory=lambda: {
        'SR': 1.0,
        'Trend': 1.0,
        'RSI': 1.0,
        'MACD': 1.0,
        'BB': 1.0,
        'FIB': 1.0,
    })

config = BotConfig()

# ============================================================================
# ALLE SYMBOLE (erweitert)
# ============================================================================

FOREX_MAJOR = [
    "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD", "USDCHF", "NZDUSD",
]
FOREX_CROSS = [
    "EURGBP", "EURJPY", "EURCHF", "EURAUD", "EURCAD", "EURNZD",
    "GBPJPY", "GBPAUD", "GBPCAD", "GBPCHF", "GBPNZD",
    "AUDJPY", "AUDCAD", "AUDCHF", "AUDNZD",
    "NZDJPY", "NZDCAD", "NZDCHF",
    "CADJPY", "CADCHF",
    "CHFJPY",
]
COMMODITIES = [
    "XAUUSD", "XAGUSD", "BRENT", "WTI", "NGAS",
]
INDICES = [
    "US30", "US500", "NAS100", "GER40", "UK100", "JPN225", "AUS200",
]
CRYPTO = [
    "BTCUSD", "ETHUSD", "LTCUSD", "XRPUSD",
]

ALLE_SYMBOLE = FOREX_MAJOR + FOREX_CROSS + COMMODITIES + INDICES + CRYPTO

# ============================================================================
# LOGGING
# ============================================================================

LOG_DATEI = f"mt5_bot_ultimate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
STATS_DATEI = f"trading_stats_{datetime.now().strftime('%Y%m%d')}.csv"

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DATEI, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# DATENBANK MANAGER (einfach, für CSV-Export)
# ============================================================================

class DatabaseManager:
    def __init__(self):
        self.trades = []
        self.daily_stats = {}
        self.symbol_stats = {}
        self.strategy_stats = {}

    def add_trade(self, trade: Dict):
        trade['id'] = len(self.trades) + 1
        trade['timestamp'] = datetime.now()
        self.trades.append(trade)
        
        # Tagesstatistik
        tag = datetime.now().strftime('%Y-%m-%d')
        if tag not in self.daily_stats:
            self.daily_stats[tag] = {'trades':0, 'gewinne':0, 'verluste':0, 'profit':0.0}
        self.daily_stats[tag]['trades'] += 1
        if trade.get('profit',0) > 0:
            self.daily_stats[tag]['gewinne'] += 1
        else:
            self.daily_stats[tag]['verluste'] += 1
        self.daily_stats[tag]['profit'] += trade.get('profit',0)
        
        # Symbol-Statistik
        sym = trade['symbol']
        if sym not in self.symbol_stats:
            self.symbol_stats[sym] = {'trades':0, 'gewinne':0, 'profit':0.0}
        self.symbol_stats[sym]['trades'] += 1
        if trade.get('profit',0) > 0:
            self.symbol_stats[sym]['gewinne'] += 1
        self.symbol_stats[sym]['profit'] += trade.get('profit',0)
        
        # Strategie-Statistik
        strat = trade.get('strategie', 'Unknown')
        if strat not in self.strategy_stats:
            self.strategy_stats[strat] = {'trades':0, 'gewinne':0, 'profit':0.0}
        self.strategy_stats[strat]['trades'] += 1
        if trade.get('profit',0) > 0:
            self.strategy_stats[strat]['gewinne'] += 1
        self.strategy_stats[strat]['profit'] += trade.get('profit',0)
        
        # In CSV speichern
        self._save_to_csv(trade)

    def _save_to_csv(self, trade):
        file_exists = os.path.isfile(STATS_DATEI)
        with open(STATS_DATEI, 'a', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['Zeit','Symbol','Richtung','Entry','Exit','Lots','Profit','Strategie','Qualität'])
            writer.writerow([
                trade.get('timestamp', datetime.now()).strftime('%Y-%m-%d %H:%M:%S'),
                trade.get('symbol',''),
                trade.get('richtung',''),
                trade.get('entry',0),
                trade.get('exit',0),
                trade.get('lots',0),
                trade.get('profit',0),
                trade.get('strategie',''),
                trade.get('qualitaet',0)
            ])

    def get_stats(self) -> Dict:
        total_trades = len(self.trades)
        if total_trades == 0:
            return {}
        wins = sum(1 for t in self.trades if t.get('profit',0) > 0)
        total_profit = sum(t.get('profit',0) for t in self.trades)
        return {
            'total_trades': total_trades,
            'wins': wins,
            'win_rate': (wins/total_trades*100) if total_trades>0 else 0,
            'total_profit': total_profit,
            'avg_profit': total_profit/total_trades,
            'best_trade': max((t.get('profit',0) for t in self.trades), default=0),
            'worst_trade': min((t.get('profit',0) for t in self.trades), default=0),
            'daily_stats': self.daily_stats,
            'symbol_stats': self.symbol_stats,
            'strategy_stats': self.strategy_stats
        }

# ============================================================================
# MT5 MANAGER (nur Verbindung zu laufendem Terminal)
# ============================================================================

class MT5Manager:
    def __init__(self):
        self.mt5 = mt5
        self.verbunden = False
        self.konto_info = None
        self.terminal_info = None
        self.symbol_cache = {}

    def verbinde(self) -> bool:
        logger.info("🔗 Verbinde mit bereits laufendem MT5...")
        if not self.mt5.initialize():
            logger.error(f"❌ Initialisierung fehlgeschlagen: {self.mt5.last_error()}")
            logger.error("Stelle sicher, dass MT5 manuell gestartet und eingeloggt ist.")
            return False
        self.konto_info = self.mt5.account_info()
        if not self.konto_info:
            logger.error("❌ Keine Kontoinformationen – bist du in MT5 eingeloggt?")
            self.mt5.shutdown()
            return False
        self.terminal_info = self.mt5.terminal_info()
        logger.info(f"\n🎉 Verbunden! Konto: {self.konto_info.login} | Balance: ${self.konto_info.balance:.2f}")
        self.verbunden = True
        return True

    def get_account_info(self):
        return self.mt5.account_info() if self.mt5 else None

    def get_symbol_info(self, symbol):
        if symbol in self.symbol_cache:
            return self.symbol_cache[symbol]
        if self.mt5:
            info = self.mt5.symbol_info(symbol)
            if info:
                self.symbol_cache[symbol] = info
            return info
        return None

    def get_tick(self, symbol):
        return self.mt5.symbol_info_tick(symbol) if self.mt5 else None

    def get_rates(self, symbol, timeframe, count):
        return self.mt5.copy_rates_from_pos(symbol, timeframe, 0, count) if self.mt5 else None

    def get_positions(self):
        return self.mt5.positions_get() if self.mt5 else None

    def order_send(self, request):
        return self.mt5.order_send(request) if self.mt5 else None

    def trennen(self):
        if self.mt5:
            self.mt5.shutdown()
            logger.info("✅ MT5 getrennt")

# ============================================================================
# INDIKATOREN (eigene Implementierung)
# ============================================================================

class Indikatoren:
    @staticmethod
    def berechne_rsi(preise, periode=14):
        if len(preise) < periode + 1:
            return 50.0
        gewinne, verluste = [], []
        for i in range(1, periode + 1):
            diff = preise[-i] - preise[-i-1]
            if diff > 0:
                gewinne.append(diff)
            else:
                verluste.append(abs(diff))
        avg_gewinn = sum(gewinne) / periode if gewinne else 0
        avg_verlust = sum(verluste) / periode if verluste else 1
        if avg_verlust == 0:
            return 100.0
        rs = avg_gewinn / avg_verlust
        return 100.0 - (100.0 / (1.0 + rs))

    @staticmethod
    def berechne_macd(preise):
        if len(preise) < 26:
            return 0, 0, 0
        def ema(data, p):
            if len(data) < p:
                return data[-1]
            mult = 2 / (p + 1)
            ema_val = data[0]
            for i in range(1, len(data)):
                ema_val = (data[i] - ema_val) * mult + ema_val
            return ema_val
        ema12 = ema(preise[-12:], 12)
        ema26 = ema(preise[-26:], 26)
        macd = ema12 - ema26
        macd_vals = []
        for i in range(9):
            if len(preise) > 26 + i:
                e12 = ema(preise[:-(i+1)], 12)
                e26 = ema(preise[:-(i+1)], 26)
                macd_vals.append(e12 - e26)
        signal = ema(macd_vals, 9) if macd_vals else 0
        hist = macd - signal
        return macd, signal, hist

    @staticmethod
    def berechne_bollinger(preise, periode=20):
        if len(preise) < periode:
            return preise[-1], preise[-1], preise[-1]
        sma = sum(preise[-periode:]) / periode
        varianz = sum([(p - sma) ** 2 for p in preise[-periode:]]) / periode
        std = math.sqrt(varianz)
        return sma, sma + (std * 2), sma - (std * 2)

    @staticmethod
    def berechne_atr(highs, lows, closes, periode=14):
        if len(highs) < periode + 1:
            return 0
        tr_values = []
        for i in range(1, periode + 1):
            hl = highs[-i] - lows[-i]
            hc = abs(highs[-i] - closes[-i-1])
            lc = abs(lows[-i] - closes[-i-1])
            tr_values.append(max(hl, hc, lc))
        return sum(tr_values) / len(tr_values)

# ============================================================================
# STRATEGIEN
# ============================================================================

class SignalQualitaet(Enum):
    SCHLECHT = 30
    MITTEL = 50
    GUT = 70
    SEHR_GUT = 85
    EXZELLENT = 95

class Strategy(ABC):
    def __init__(self, name: str, gewicht: float = 1.0):
        self.name = name
        self.gewicht = gewicht
        self.signale_gesamt = 0
        self.signale_erfolgreich = 0
        self.performance = deque(maxlen=100)

    @abstractmethod
    def analysiere(self, mt5_mgr: MT5Manager, symbol: str) -> Optional[Dict]:
        pass

    def update_performance(self, erfolg: bool):
        self.performance.append(1 if erfolg else 0)
        if erfolg:
            self.signale_erfolgreich += 1

    def get_win_rate(self) -> float:
        if len(self.performance) == 0:
            return 0
        return sum(self.performance) / len(self.performance) * 100

    def get_statistik(self) -> Dict:
        return {
            'name': self.name,
            'signale': self.signale_gesamt,
            'erfolgreich': self.signale_erfolgreich,
            'win_rate': self.get_win_rate(),
            'gewicht': self.gewicht
        }

# ----------------------------------------------------------------------------
# 1. Support/Resistance Strategie
# ----------------------------------------------------------------------------
class SRStrategy(Strategy):
    def __init__(self):
        super().__init__("S/R", config.strategie_gewichte['SR'])
        self.min_abstand_pips = 2
        self.lookback = 20

    def _finde_levels(self, highs, lows):
        levels = {'support': [], 'resistance': []}
        for i in range(2, len(highs)-2):
            if highs[i] > highs[i-1] and highs[i] > highs[i-2] and \
               highs[i] > highs[i+1] and highs[i] > highs[i+2]:
                levels['resistance'].append(highs[i])
            if lows[i] < lows[i-1] and lows[i] < lows[i-2] and \
               lows[i] < lows[i+1] and lows[i] < lows[i+2]:
                levels['support'].append(lows[i])
        return levels

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_M5, 50)
        if rates is None or len(rates) < 30:
            return None
        highs = [r['high'] for r in rates[-self.lookback:]]
        lows = [r['low'] for r in rates[-self.lookback:]]
        levels = self._finde_levels(highs, lows)
        tick = mt5_mgr.get_tick(symbol)
        if not tick:
            return None
        aktuell = (tick.bid + tick.ask) / 2
        spread = (tick.ask - tick.bid) / (0.0001 if "JPY" not in symbol else 0.01)
        max_spread = config.max_spread_pips.get(symbol, config.max_spread_pips["DEFAULT"])
        if spread > max_spread:
            return None

        # Nächste Levels
        naechster_support = max([s for s in levels['support'] if s < aktuell] or [None])
        naechste_resistance = min([r for r in levels['resistance'] if r > aktuell] or [None])
        if naechster_support is None or naechste_resistance is None:
            return None

        abstand_support = ((aktuell - naechster_support) / naechster_support) * 10000
        abstand_resistance = ((naechste_resistance - aktuell) / naechste_resistance) * 10000

        # Trend mit EMA
        closes = [r['close'] for r in rates[-20:]]
        ema_10 = sum(closes[-10:]) / 10 if len(closes) >= 10 else aktuell
        ema_20 = sum(closes) / len(closes) if closes else aktuell

        if abstand_support < self.min_abstand_pips and ema_10 > ema_20:
            qualitaet = SignalQualitaet.GUT.value
            if abstand_support < 1:
                qualitaet += 10
            return {
                'symbol': symbol,
                'signal': "BUY",
                'preis': aktuell,
                'grund': f"S-Level {abstand_support:.1f}",
                'stop_loss': naechster_support * 0.998,
                'qualitaet': min(qualitaet, 100),
                'strategie': self.name,
                'tp_faktoren': [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
            }
        elif abstand_resistance < self.min_abstand_pips and ema_10 < ema_20:
            qualitaet = SignalQualitaet.GUT.value
            if abstand_resistance < 1:
                qualitaet += 10
            return {
                'symbol': symbol,
                'signal': "SELL",
                'preis': aktuell,
                'grund': f"R-Level {abstand_resistance:.1f}",
                'stop_loss': naechste_resistance * 1.002,
                'qualitaet': min(qualitaet, 100),
                'strategie': self.name,
                'tp_faktoren': [1.5, 2.0, 2.5, 3.0, 4.0, 5.0]
            }
        return None

# ----------------------------------------------------------------------------
# 2. Fibonacci Strategie
# ----------------------------------------------------------------------------
class FibonacciStrategy(Strategy):
    def __init__(self):
        super().__init__("FIB", config.strategie_gewichte.get('FIB',1.0))
        self.levels = [0.236, 0.382, 0.5, 0.618, 0.764, 0.786]

    def _finde_swings(self, preise):
        if len(preise) < 50:
            return preise[-1], preise[-1]
        letzte = preise[-50:]
        return max(letzte), min(letzte)

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_H1, 100)
        if not rates or len(rates) < 50:
            return None
        preise = [r['close'] for r in rates]
        aktuell = preise[-1]
        tick = mt5_mgr.get_tick(symbol)
        if tick:
            aktuell = (tick.bid + tick.ask) / 2
        swing_high, swing_low = self._finde_swings(preise)
        if swing_high == swing_low:
            return None
        differenz = swing_high - swing_low
        for level in self.levels:
            fib_preis = swing_high - (differenz * level)
            abstand = abs(aktuell - fib_preis) / aktuell
            if abstand < 0.0015:
                if aktuell < fib_preis:
                    stop_loss = fib_preis * 0.995
                    qualitaet = SignalQualitaet.GUT.value
                    if level in [0.382,0.5,0.618]:
                        qualitaet += 15
                    return {
                        'symbol': symbol,
                        'signal': "BUY",
                        'preis': aktuell,
                        'grund': f"FIB {level}",
                        'stop_loss': stop_loss,
                        'qualitaet': min(qualitaet,100),
                        'strategie': self.name,
                        'tp_faktoren': [1.5,2.0,2.5,3.0,4.0]
                    }
                else:
                    stop_loss = fib_preis * 1.005
                    qualitaet = SignalQualitaet.GUT.value
                    if level in [0.382,0.5,0.618]:
                        qualitaet += 15
                    return {
                        'symbol': symbol,
                        'signal': "SELL",
                        'preis': aktuell,
                        'grund': f"FIB {level}",
                        'stop_loss': stop_loss,
                        'qualitaet': min(qualitaet,100),
                        'strategie': self.name,
                        'tp_faktoren': [1.5,2.0,2.5,3.0,4.0]
                    }
        return None

# ----------------------------------------------------------------------------
# 3. Trend Following Strategie (EMA)
# ----------------------------------------------------------------------------
class TrendStrategy(Strategy):
    def __init__(self):
        super().__init__("Trend", config.strategie_gewichte['Trend'])
        self.ema_kurz = 5
        self.ema_lang = 20

    def _berechne_ema(self, preise, periode):
        if len(preise) < periode:
            return preise[-1]
        return sum(preise[-periode:]) / periode

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_M15, 50)
        if not rates or len(rates) < 30:
            return None
        preise = [r['close'] for r in rates]
        aktuell = preise[-1]
        tick = mt5_mgr.get_tick(symbol)
        if tick:
            aktuell = (tick.bid + tick.ask) / 2
        ema_k = self._berechne_ema(preise, self.ema_kurz)
        ema_l = self._berechne_ema(preise, self.ema_lang)

        if aktuell > ema_k > ema_l:
            stop_loss = ema_k * 0.995
            qualitaet = SignalQualitaet.MITTEL.value
            return {
                'symbol': symbol,
                'signal': "BUY",
                'preis': aktuell,
                'grund': "Trend UP",
                'stop_loss': stop_loss,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [2.0,3.0,4.0,5.0]
            }
        elif aktuell < ema_k < ema_l:
            stop_loss = ema_k * 1.005
            qualitaet = SignalQualitaet.MITTEL.value
            return {
                'symbol': symbol,
                'signal': "SELL",
                'preis': aktuell,
                'grund': "Trend DOWN",
                'stop_loss': stop_loss,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [2.0,3.0,4.0,5.0]
            }
        return None

# ----------------------------------------------------------------------------
# 4. RSI Mean Reversion
# ----------------------------------------------------------------------------
class RSIStrategy(Strategy):
    def __init__(self):
        super().__init__("RSI", config.strategie_gewichte['RSI'])
        self.ueberkauft = 70
        self.ueberverkauft = 30

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_M5, 30)
        if not rates or len(rates) < 20:
            return None
        preise = [r['close'] for r in rates]
        aktuell = preise[-1]
        tick = mt5_mgr.get_tick(symbol)
        if tick:
            aktuell = (tick.bid + tick.ask) / 2
        rsi = Indikatoren.berechne_rsi(preise)
        sma, oben, unten = Indikatoren.berechne_bollinger(preise)

        if rsi < self.ueberverkauft and aktuell < sma:
            qualitaet = SignalQualitaet.GUT.value
            if rsi < 20:
                qualitaet += 15
            return {
                'symbol': symbol,
                'signal': "BUY",
                'preis': aktuell,
                'grund': f"RSI {rsi:.0f}",
                'stop_loss': min(unten, aktuell*0.995),
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.5,2.0,2.5]
            }
        elif rsi > self.ueberkauft and aktuell > sma:
            qualitaet = SignalQualitaet.GUT.value
            if rsi > 80:
                qualitaet += 15
            return {
                'symbol': symbol,
                'signal': "SELL",
                'preis': aktuell,
                'grund': f"RSI {rsi:.0f}",
                'stop_loss': max(oben, aktuell*1.005),
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.5,2.0,2.5]
            }
        return None

# ----------------------------------------------------------------------------
# 5. MACD Crossover
# ----------------------------------------------------------------------------
class MACDStrategy(Strategy):
    def __init__(self):
        super().__init__("MACD", config.strategie_gewichte['MACD'])

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_M15, 50)
        if not rates or len(rates) < 30:
            return None
        preise = [r['close'] for r in rates]
        aktuell = preise[-1]
        tick = mt5_mgr.get_tick(symbol)
        if tick:
            aktuell = (tick.bid + tick.ask) / 2
        macd, signal, hist = Indikatoren.berechne_macd(preise)
        # Histogramm Änderung
        if len(preise) > 30:
            _, _, hist_prev = Indikatoren.berechne_macd(preise[:-1])
        else:
            hist_prev = 0
        if hist > 0 and hist_prev <= 0:
            qualitaet = SignalQualitaet.GUT.value
            if abs(hist) > 0.001:
                qualitaet += 10
            return {
                'symbol': symbol,
                'signal': "BUY",
                'preis': aktuell,
                'grund': "MACD Up",
                'stop_loss': aktuell * 0.995,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.8,2.5,3.5]
            }
        elif hist < 0 and hist_prev >= 0:
            qualitaet = SignalQualitaet.GUT.value
            if abs(hist) > 0.001:
                qualitaet += 10
            return {
                'symbol': symbol,
                'signal': "SELL",
                'preis': aktuell,
                'grund': "MACD Down",
                'stop_loss': aktuell * 1.005,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.8,2.5,3.5]
            }
        return None

# ----------------------------------------------------------------------------
# 6. Bollinger Bands
# ----------------------------------------------------------------------------
class BollingerStrategy(Strategy):
    def __init__(self):
        super().__init__("BB", config.strategie_gewichte['BB'])
        self.periode = 20

    def analysiere(self, mt5_mgr, symbol):
        self.signale_gesamt += 1
        rates = mt5_mgr.get_rates(symbol, mt5.TIMEFRAME_M5, 30)
        if not rates or len(rates) < 20:
            return None
        preise = [r['close'] for r in rates]
        aktuell = preise[-1]
        tick = mt5_mgr.get_tick(symbol)
        if tick:
            aktuell = (tick.bid + tick.ask) / 2
        sma, oben, unten = Indikatoren.berechne_bollinger(preise, self.periode)
        bandbreite = (oben - unten) / sma

        if aktuell <= unten * 1.001:
            qualitaet = SignalQualitaet.GUT.value
            if bandbreite > 0.02:
                qualitaet += 15
            return {
                'symbol': symbol,
                'signal': "BUY",
                'preis': aktuell,
                'grund': "BB unten",
                'stop_loss': unten * 0.995,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.5,2.0,2.5,3.0]
            }
        elif aktuell >= oben * 0.999:
            qualitaet = SignalQualitaet.GUT.value
            if bandbreite > 0.02:
                qualitaet += 15
            return {
                'symbol': symbol,
                'signal': "SELL",
                'preis': aktuell,
                'grund': "BB oben",
                'stop_loss': oben * 1.005,
                'qualitaet': qualitaet,
                'strategie': self.name,
                'tp_faktoren': [1.5,2.0,2.5,3.0]
            }
        return None

# ============================================================================
# SIGNAL MANAGER
# ============================================================================

class SignalManager:
    def __init__(self):
        self.strategien: List[Strategy] = []
        self.signale_historie = deque(maxlen=1000)

    def add_strategy(self, strategie: Strategy):
        self.strategien.append(strategie)
        logger.info(f"✅ Strategie hinzugefügt: {strategie.name}")

    def finde_bestes_signal(self, mt5_mgr, symbol) -> Optional[Dict]:
        beste_qualitaet = 0
        bestes_signal = None
        for strat in self.strategien:
            try:
                signal = strat.analysiere(mt5_mgr, symbol)
                if signal:
                    qualitaet = signal.get('qualitaet', 0) * strat.gewicht
                    # Performance-Gewichtung
                    win_rate = strat.get_win_rate()
                    if win_rate > 50:
                        qualitaet *= (1 + (win_rate-50)/100)
                    if qualitaet > beste_qualitaet:
                        beste_qualitaet = qualitaet
                        bestes_signal = signal
                        bestes_signal['qualitaet'] = min(int(qualitaet), 100)
            except Exception as e:
                logger.error(f"Fehler bei {strat.name}: {e}")
        if bestes_signal:
            self.signale_historie.append({
                'zeit': datetime.now(),
                'symbol': symbol,
                'signal': bestes_signal
            })
        return bestes_signal

    def update_performance(self, signal: Dict, erfolg: bool):
        name = signal.get('strategie')
        for s in self.strategien:
            if s.name == name:
                s.update_performance(erfolg)
                break

# ============================================================================
# TRADE MANAGER (mit Multi-TP und progressivem Stop-Loss)
# ============================================================================

class TradeManager:
    def __init__(self):
        self.mt5_mgr: Optional[MT5Manager] = None
        self.signal_mgr: Optional[SignalManager] = None
        self.db: Optional[DatabaseManager] = None
        self.aktive_trades: List[Dict] = []
        self.trade_levels: Dict[str, Dict] = {}
        self.total_profit = 0.0
        self.wins = 0
        self.losses = 0
        self.consecutive_losses = 0

    def set_mt5_manager(self, mt5_mgr):
        self.mt5_mgr = mt5_mgr

    def set_signal_manager(self, signal_mgr):
        self.signal_mgr = signal_mgr

    def set_database(self, db):
        self.db = db

    def _berechne_lots(self, symbol, preis, stop_loss, qualitaet=50):
        konto = self.mt5_mgr.get_account_info()
        if not konto:
            return 0.01
        kontostand = konto.balance
        risiko = kontostand * config.risiko_pro_trade
        # Stop-Loss in Pips
        if "JPY" in symbol:
            stop_pips = abs(preis - stop_loss) / 0.01
        elif any(x in symbol for x in ["XAU","XAG"]):
            stop_pips = abs(preis - stop_loss) / 0.01
        elif any(x in symbol for x in ["BTC","ETH"]):
            stop_pips = abs(preis - stop_loss) / 0.1
        else:
            stop_pips = abs(preis - stop_loss) / 0.0001
        if stop_pips < 1:
            stop_pips = 5
        qualitaets_faktor = max(0.5, min(2.0, qualitaet / 50))
        verlust_faktor = max(0.2, 1.0 - (self.consecutive_losses * 0.1))
        # Pip-Wert pro Lot
        if "JPY" in symbol:
            pip_wert = 1000 / preis
        elif any(x in symbol for x in ["XAU","XAG"]):
            pip_wert = 10
        elif any(x in symbol for x in ["BTC","ETH"]):
            pip_wert = 100
        else:
            pip_wert = 10
        lots = (risiko * qualitaets_faktor * verlust_faktor) / (stop_pips * pip_wert)
        return max(0.01, min(round(lots, 2), 1.0))

    def _berechne_stop_loss(self, trade_id, entry, aktuell, is_long):
        profit_pct = ((aktuell - entry) / entry) if is_long else ((entry - aktuell) / entry)
        if trade_id not in self.trade_levels:
            self.trade_levels[trade_id] = {'max_profit': 0, 'level': 0, 'updates': []}
        self.trade_levels[trade_id]['max_profit'] = max(self.trade_levels[trade_id]['max_profit'], profit_pct)

        # Level bestimmen (0-...)
        if profit_pct <= 0:
            level = 0
        elif profit_pct < 0.01:
            level = 0
        elif profit_pct < 0.02:
            level = 1
        elif profit_pct < 0.03:
            level = 2
        elif profit_pct < 0.04:
            level = 3
        elif profit_pct < 0.05:
            level = 4
        elif profit_pct < 0.06:
            level = 5
        elif profit_pct < 0.07:
            level = 6
        elif profit_pct < 0.08:
            level = 7
        elif profit_pct < 0.09:
            level = 8
        elif profit_pct < 0.10:
            level = 9
        else:
            level = 9 + int((profit_pct - 0.10) * 50)

        if level > self.trade_levels[trade_id]['level']:
            self.trade_levels[trade_id]['level'] = level
        current_level = self.trade_levels[trade_id]['level']

        # Stop-Loss nach Taktik
        if current_level == 0:
            stop_pct = config.stop_loss_initial
            reason = "20% Stop"
        elif current_level == 1:
            stop_pct = 0.008
            reason = "80% von 1%"
        elif current_level == 2:
            stop_pct = 0.02
            reason = "Stop auf 2%"
        elif current_level == 3:
            stop_pct = 0.024
            reason = "80% von 3%"
        elif current_level == 4:
            stop_pct = 0.032
            reason = "80% von 4%"
        elif current_level == 5:
            stop_pct = 0.04
            reason = "80% von 5%"
        elif current_level == 6:
            stop_pct = 0.048
            reason = "80% von 6%"
        elif current_level == 7:
            stop_pct = 0.056
            reason = "80% von 7%"
        elif current_level == 8:
            stop_pct = 0.064
            reason = "80% von 8%"
        elif current_level == 9:
            stop_pct = 0.072
            reason = "80% von 9%"
        else:
            secured = (current_level - 1) * config.trailing_stop_prozent
            stop_pct = secured / 100
            reason = f"Level {current_level}: {config.trailing_stop_prozent*100}% von Level {current_level-1}"

        if is_long:
            if profit_pct <= 0:
                stop_price = entry * (1 - stop_pct)
            else:
                stop_price = entry * (1 + stop_pct)
        else:
            if profit_pct <= 0:
                stop_price = entry * (1 + stop_pct)
            else:
                stop_price = entry * (1 - stop_pct)

        self.trade_levels[trade_id]['updates'].append({
            'zeit': datetime.now(),
            'profit_pct': profit_pct,
            'level': current_level,
            'stop_price': stop_price,
            'reason': reason
        })
        return stop_price, reason

    def _berechne_tp_preise(self, entry, stop_loss, richtung, tp_faktoren):
        risiko_pips = abs(entry - stop_loss)
        tp_preise = []
        for faktor in tp_faktoren:
            if richtung == "BUY":
                tp = entry + (risiko_pips * faktor)
            else:
                tp = entry - (risiko_pips * faktor)
            tp_preise.append(tp)
        return tp_preise

    def oeffne_trade(self, signal: Dict) -> bool:
        if not self.mt5_mgr or not self.mt5_mgr.mt5:
            return False
        symbol = signal['symbol']
        richtung = signal['signal']
        preis = signal['preis']
        stop_loss = signal.get('stop_loss')
        qualitaet = signal.get('qualitaet', 50)
        strategie = signal.get('strategie', 'Unknown')
        tp_faktoren = signal.get('tp_faktoren', [1.5,2.0,2.5,3.0,4.0])

        if not stop_loss:
            if richtung == "BUY":
                stop_loss = preis * (1 - config.stop_loss_initial)
            else:
                stop_loss = preis * (1 + config.stop_loss_initial)

        # Spread prüfen
        tick = self.mt5_mgr.get_tick(symbol)
        if not tick:
            return False
        spread = (tick.ask - tick.bid) / (0.0001 if "JPY" not in symbol else 0.01)
        max_spread = config.max_spread_pips.get(symbol, config.max_spread_pips["DEFAULT"])
        if spread > max_spread:
            logger.info(f"   ⚠️ Spread zu hoch: {spread:.1f} > {max_spread}")
            return False

        lots = self._berechne_lots(symbol, preis, stop_loss, qualitaet)
        if lots <= 0:
            return False

        tp_preise = self._berechne_tp_preise(preis, stop_loss, richtung, tp_faktoren)

        erfolgreiche_orders = 0
        gesamt_lots = 0

        for i, (tp_faktor, tp_preis) in enumerate(zip(tp_faktoren, tp_preise)):
            if i < len(config.tp_levels):
                tp_anteil = config.tp_levels[i]['schliessen']
            else:
                tp_anteil = 0.1
            tp_lots = round(lots * tp_anteil, 2)
            if tp_lots < 0.01:
                continue
            gesamt_lots += tp_lots

            if richtung == "BUY":
                order_typ = mt5.ORDER_TYPE_BUY
                ausfuehr_preis = tick.ask
            else:
                order_typ = mt5.ORDER_TYPE_SELL
                ausfuehr_preis = tick.bid

            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "symbol": symbol,
                "volume": tp_lots,
                "type": order_typ,
                "price": ausfuehr_preis,
                "sl": stop_loss,
                "tp": tp_preis,
                "deviation": 20,
                "magic": config.login,
                "comment": f"{signal['grund'][:5]}-{i+1}",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            result = self.mt5_mgr.order_send(request)
            if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                erfolgreiche_orders += 1
                trade_id = f"{symbol}_{result.order}"
                trade = {
                    'id': trade_id,
                    'ticket': result.order,
                    'symbol': symbol,
                    'richtung': richtung,
                    'entry': result.price,
                    'lots': tp_lots,
                    'stop_loss': stop_loss,
                    'take_profit': tp_preis,
                    'tp_level': i+1,
                    'tp_faktor': tp_faktor,
                    'signal': signal
                }
                self.aktive_trades.append(trade)

        if erfolgreiche_orders > 0:
            self.consecutive_losses = 0
            logger.info(f"\n✅ TRADE: {symbol} {richtung} | Lots: {gesamt_lots:.2f} ({erfolgreiche_orders} TP-Levels)")
            return True
        return False

    def update_trades(self):
        if not self.mt5_mgr or not self.mt5_mgr.mt5:
            return
        zu_schliessen = []
        for trade in self.aktive_trades[:]:
            try:
                tick = self.mt5_mgr.get_tick(trade['symbol'])
                if not tick:
                    continue
                is_long = trade['richtung'] == "BUY"
                aktuell = tick.bid if is_long else tick.ask
                neuer_stop, reason = self._berechne_stop_loss(trade['id'], trade['entry'], aktuell, is_long)
                if abs(neuer_stop - trade['stop_loss']) > 0.00001:
                    request = {
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": trade['ticket'],
                        "sl": neuer_stop,
                        "tp": trade['take_profit'],
                    }
                    result = self.mt5_mgr.order_send(request)
                    if result and result.retcode == mt5.TRADE_RETCODE_DONE:
                        trade['stop_loss'] = neuer_stop
                        logger.info(f"   🔄 Stop angepasst: {trade['symbol']} TP{trade['tp_level']} -> ${neuer_stop:.5f}")
                if (is_long and aktuell <= trade['stop_loss']) or (not is_long and aktuell >= trade['stop_loss']):
                    zu_schliessen.append((trade, reason))
                if (is_long and aktuell >= trade['take_profit']) or (not is_long and aktuell <= trade['take_profit']):
                    zu_schliessen.append((trade, f"TP{trade['tp_level']} erreicht"))
            except Exception as e:
                logger.error(f"Update Fehler {trade['id']}: {e}")
        for trade, reason in zu_schliessen:
            self._schliesse_trade(trade, reason)

    def _schliesse_trade(self, trade, reason):
        tick = self.mt5_mgr.get_tick(trade['symbol'])
        if not tick:
            return
        if trade['richtung'] == "BUY":
            order_typ = mt5.ORDER_TYPE_SELL
            preis = tick.bid
        else:
            order_typ = mt5.ORDER_TYPE_BUY
            preis = tick.ask
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": trade['symbol'],
            "volume": trade['lots'],
            "type": order_typ,
            "position": trade['ticket'],
            "price": preis,
            "deviation": 20,
            "magic": config.login,
            "comment": "Close",
            "type_time": mt5.ORDER_TIME_GTC,
        }
        result = self.mt5_mgr.order_send(request)
        if result and result.retcode == mt5.TRADE_RETCODE_DONE:
            profit = result.profit
            self.total_profit += profit
            if profit > 0:
                self.wins += 1
            else:
                self.losses += 1
                self.consecutive_losses += 1
            if self.signal_mgr and 'signal' in trade:
                self.signal_mgr.update_performance(trade['signal'], profit > 0)
            if self.db:
                trade_data = {
                    'symbol': trade['symbol'],
                    'richtung': trade['richtung'],
                    'entry': trade['entry'],
                    'exit': preis,
                    'lots': trade['lots'],
                    'profit': profit,
                    'strategie': trade['signal'].get('strategie','Unknown'),
                    'qualitaet': trade['signal'].get('qualitaet',50),
                    'tp_level': trade.get('tp_level',1)
                }
                self.db.add_trade(trade_data)
            logger.info(f"✅ GESCHLOSSEN: {trade['symbol']} TP{trade['tp_level']} | ${profit:.2f} | {reason}")
            if trade in self.aktive_trades:
                self.aktive_trades.remove(trade)

    def schliesse_alle_trades(self):
        for trade in self.aktive_trades[:]:
            self._schliesse_trade(trade, "Bot Stop")

    def get_statistik(self) -> Dict:
        total = self.wins + self.losses
        win_rate = (self.wins / total * 100) if total > 0 else 0
        return {
            'aktiv': len(self.aktive_trades),
            'total': total,
            'wins': self.wins,
            'losses': self.losses,
            'win_rate': win_rate,
            'profit': self.total_profit,
            'consecutive_losses': self.consecutive_losses
        }

# ============================================================================
# DASHBOARD
# ============================================================================

class Dashboard:
    def __init__(self):
        self.startzeit = datetime.now()
        self.letztes_update = None
        self.daten = {}

    def update(self, mt5_mgr, trade_mgr, signal_mgr, db):
        self.letztes_update = datetime.now()
        konto = mt5_mgr.get_account_info()
        if konto:
            self.daten['balance'] = konto.balance
            self.daten['equity'] = konto.equity
        self.daten['trade_stats'] = trade_mgr.get_statistik()
        self.daten['signal_stats'] = [s.get_statistik() for s in signal_mgr.strategien]
        self.daten['db_stats'] = db.get_stats()
        laufzeit = self.letztes_update - self.startzeit
        stunden = laufzeit.seconds // 3600
        minuten = (laufzeit.seconds % 3600) // 60
        self.daten['laufzeit'] = f"{stunden}h {minuten}m"

    def print(self):
        print(f"\n{'='*70}")
        print("📊 TRADING BOT DASHBOARD")
        print(f"{'='*70}")
        print(f"⏰ Laufzeit: {self.daten.get('laufzeit', '0h 0m')}")
        print(f"\n💰 KONTO:")
        print(f"   Balance: ${self.daten.get('balance', 0):.2f}")
        print(f"   Equity: ${self.daten.get('equity', 0):.2f}")
        stats = self.daten.get('trade_stats', {})
        print(f"\n📈 TRADES:")
        print(f"   Aktiv: {stats.get('aktiv', 0)}")
        print(f"   Total: {stats.get('total', 0)}")
        print(f"   Wins: {stats.get('wins', 0)}")
        print(f"   Losses: {stats.get('losses', 0)}")
        print(f"   Win Rate: {stats.get('win_rate', 0):.1f}%")
        print(f"   Profit: ${stats.get('profit', 0):.2f}")
        db_stats = self.daten.get('db_stats', {})
        print(f"\n📊 PERFORMANCE:")
        print(f"   Best Trade: ${db_stats.get('best_trade', 0):.2f}")
        print(f"   Worst Trade: ${db_stats.get('worst_trade', 0):.2f}")
        print(f"   Avg Profit: ${db_stats.get('avg_profit', 0):.2f}")
        print(f"\n📋 STRATEGIEN:")
        for s in self.daten.get('signal_stats', []):
            print(f"   {s['name']}: {s['signale']} Signale | {s['win_rate']:.1f}% WR")
        print(f"{'='*70}\n")

# ============================================================================
# HAUPTPROGRAMM
# ============================================================================

def main():
    print(f"\n🎯 MT5 TRADING BOT - ULTIMATE EDITION (EXE VERSION)")
    print(f"   • Server: {config.server}")
    print(f"   • Konto: {config.login}")
    print(f"   • Symbole: {len(ALLE_SYMBOLE)}")
    print(f"   • Max Positionen: {config.max_positionen}")
    print(f"   • TP-Levels: {len(config.tp_levels)}")
    print("=" * 60)

    # Komponenten
    mt5_mgr = MT5Manager()
    db = DatabaseManager()
    signal_mgr = SignalManager()
    trade_mgr = TradeManager()

    # Strategien hinzufügen
    signal_mgr.add_strategy(SRStrategy())
    signal_mgr.add_strategy(FibonacciStrategy())
    signal_mgr.add_strategy(TrendStrategy())
    signal_mgr.add_strategy(RSIStrategy())
    signal_mgr.add_strategy(MACDStrategy())
    signal_mgr.add_strategy(BollingerStrategy())

    trade_mgr.set_mt5_manager(mt5_mgr)
    trade_mgr.set_signal_manager(signal_mgr)
    trade_mgr.set_database(db)

    # Verbinden
    if not mt5_mgr.verbinde():
        logger.error("❌ Verbindung fehlgeschlagen!")
        print("\n🔧 Stelle sicher, dass MT5 läuft und du eingeloggt bist.")
        input("Enter zum Beenden...")
        return

    dashboard = Dashboard()
    scans = 0
    logger.info(f"\n🚀 BOT GESTARTET! (STRG+C zum Stoppen)")

    try:
        while True:
            scans += 1
            trade_mgr.update_trades()

            if len(trade_mgr.aktive_trades) < config.max_positionen:
                # Scanne eine Auswahl an Symbolen
                scan_list = random.sample(ALLE_SYMBOLE, min(20, len(ALLE_SYMBOLE)))
                for symbol in scan_list:
                    signal = signal_mgr.finde_bestes_signal(mt5_mgr, symbol)
                    if signal:
                        logger.info(f"  ✅ SIGNAL: {signal['signal']} - {signal['grund']} ({signal['qualitaet']}%)")
                        trade_mgr.oeffne_trade(signal)
                        time.sleep(2)
                    time.sleep(0.1)

            if scans % 20 == 0:
                dashboard.update(mt5_mgr, trade_mgr, signal_mgr, db)
                dashboard.print()

            time.sleep(config.scan_zeit)

    except KeyboardInterrupt:
        logger.info("\n🛑 BOT GESTOPPT")
    except Exception as e:
        logger.error(f"❌ KRITISCHER FEHLER: {e}")
        logger.error(traceback.format_exc())
    finally:
        logger.info("\n🔚 Schließe alle Trades...")
        trade_mgr.schliesse_alle_trades()
        mt5_mgr.trennen()

        # Abschlussstatistik
        stats = trade_mgr.get_statistik()
        db_stats = db.get_stats()
        print(f"\n{'='*70}")
        print("📊 ABSCHLUSSSTATISTIK")
        print(f"{'='*70}")
        print(f"⏰ Laufzeit: {dashboard.daten.get('laufzeit','0h 0m')}")
        print(f"🎯 Trades gesamt: {stats.get('total',0)}")
        print(f"🏆 Win Rate: {stats.get('win_rate',0):.1f}%")
        print(f"💰 Total Profit: ${stats.get('profit',0):.2f}")
        print(f"📈 Best Trade: ${db_stats.get('best_trade',0):.2f}")
        print(f"📉 Worst Trade: ${db_stats.get('worst_trade',0):.2f}")
        print(f"📊 Avg Profit: ${db_stats.get('avg_profit',0):.2f}")
        print(f"\n📋 STRATEGIE PERFORMANCE:")
        for s in signal_mgr.strategien:
            stat = s.get_statistik()
            print(f"   {stat['name']}: {stat['signale']} Signale, {stat['win_rate']:.1f}% WR")
        print(f"{'='*70}")
        print(f"📁 Log-Datei: {LOG_DATEI}")
        print(f"📁 Stats-Datei: {STATS_DATEI}")

if __name__ == "__main__":
    main()