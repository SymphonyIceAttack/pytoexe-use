"""
COMPLETE TRADING BOT - SMA + PRICE ACTION + SMC
With $50 account rules, 2 trades/day, risk management
"""

import ccxt
import pandas as pd
import numpy as np
import time
import json
from datetime import datetime
import os

# ============================================
# CONFIGURATION
# ============================================
CONFIG = {
    "account_size": 50,
    "daily_target": 5,
    "max_trades_per_day": 2,
    "risk_per_trade": 2.0,
    "max_daily_loss": 5,
    "symbols": ["BTC/USDT", "ETH/USDT"],
    "timeframe": "1h",
    "sandbox_mode": True
}

class TradingBot:
    def __init__(self):
        print("🚀 Initializing Trading Bot...")
        self.balance = CONFIG["account_size"]
        self.trades_today = 0
        self.daily_pnl = 0
        self.positions = []
        self.setup_exchange()
        
    def setup_exchange(self):
        """Connect to exchange"""
        try:
            self.exchange = ccxt.binance({
                'enableRateLimit': True,
            })
            if CONFIG["sandbox_mode"]:
                self.exchange.set_sandbox_mode(True)
                print("✅ Connected to Binance Testnet (FAKE MONEY - SAFE!)")
            else:
                print("⚠️ LIVE MODE - Real money!")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            
    def can_trade(self):
        """Check if trading is allowed"""
        if self.trades_today >= CONFIG["max_trades_per_day"]:
            print(f"⏸️ Max trades ({CONFIG['max_trades_per_day']}) reached for today")
            return False
            
        if self.daily_pnl >= CONFIG["daily_target"]:
            print(f"🎯 Daily target of ${CONFIG['daily_target']} reached!")
            return False
            
        if self.daily_pnl <= -CONFIG["max_daily_loss"]:
            print(f"🛑 Daily loss limit reached")
            return False
            
        return True
        
    def calculate_position_size(self, price, stop_loss_pct=2):
        """Calculate safe position size"""
        risk_amount = self.balance * (CONFIG["risk_per_trade"] / 100)
        stop_loss_price = price * (1 - stop_loss_pct/100)
        price_risk = price - stop_loss_price
        
        if price_risk > 0:
            position_size = risk_amount / price_risk
            return position_size
        return 0
        
    def get_sma_signal(self, df):
        """SMA Crossover Strategy"""
        df['sma_fast'] = df['close'].rolling(10).mean()
        df['sma_slow'] = df['close'].rolling(20).mean()
        
        if df['sma_fast'].iloc[-1] > df['sma_slow'].iloc[-1]:
            return "BUY", 30
        elif df['sma_fast'].iloc[-1] < df['sma_slow'].iloc[-1]:
            return "SELL", 30
        return "HOLD", 0
        
    def get_price_action_signal(self, df):
        """Price Action Patterns"""
        score = 0
        reason = []
        
        # Bullish engulfing
        if (df['close'].iloc[-2] < df['open'].iloc[-2] and
            df['close'].iloc[-1] > df['open'].iloc[-1] and
            df['close'].iloc[-1] > df['open'].iloc[-2]):
            score += 25
            reason.append("Bullish Engulfing")
            
        return score, reason
        
    def analyze_market(self, symbol):
        """Analyze market and generate signal"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, CONFIG["timeframe"], limit=50)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            
            current_price = df['close'].iloc[-1]
            
            # Get signals
            sma_signal, sma_score = self.get_sma_signal(df)
            pa_score, pa_reason = self.get_price_action_signal(df)
            
            total_score = sma_score + pa_score
            
            if total_score >= 30:
                return {
                    'signal': sma_signal,
                    'score': total_score,
                    'price': current_price,
                    'reasons': pa_reason
                }
            return None
            
        except Exception as e:
            print(f"Error analyzing {symbol}: {e}")
            return None
            
    def execute_trade(self, signal):
        """Execute a trade"""
        if not self.can_trade():
            return False
            
        position_size = self.calculate_position_size(signal['price'])
        
        print(f"\n🟢 TRADE SIGNAL: {signal['signal']}")
        print(f"   Symbol: {signal.get('symbol', 'Unknown')}")
        print(f"   Price: ${signal['price']:.2f}")
        print(f"   Score: {signal['score']}")
        print(f"   Reasons: {', '.join(signal['reasons'])}")
        print(f"   Position Size: {position_size:.4f}")
        
        trade = {
            'symbol': signal.get('symbol', 'Unknown'),
            'entry': signal['price'],
            'size': position_size,
            'time': datetime.now()
        }
        
        self.positions.append(trade)
        self.trades_today += 1
        return True
        
    def check_positions(self):
        """Monitor open positions"""
        for position in self.positions[:]:
            try:
                ticker = self.exchange.fetch_ticker(position['symbol'])
                current_price = ticker['last']
                
                # Simple 2% stop loss
                if current_price <= position['entry'] * 0.98:
                    profit = (current_price - position['entry']) * position['size']
                    self.daily_pnl += profit
                    print(f"🔴 Stop loss: ${profit:.2f}")
                    self.positions.remove(position)
                    
                # 4% take profit
                elif current_price >= position['entry'] * 1.04:
                    profit = (current_price - position['entry']) * position['size']
                    self.daily_pnl += profit
                    print(f"✅ Take profit: ${profit:.2f}")
                    self.positions.remove(position)
                    
            except Exception as e:
                print(f"Error checking positions: {e}")
                
    def reset_daily_counter(self):
        """Reset daily counters at midnight"""
        now = datetime.now()
        if now.hour == 0 and now.minute == 0:
            self.trades_today = 0
            self.daily_pnl = 0
            print("📅 New trading day started!")
            
    def run(self):
        """Main bot loop"""
        print("\n" + "="*50)
        print("🚀 TRADING BOT STARTED")
        print(f"Account: ${self.balance}")
        print(f"Daily Target: ${CONFIG['daily_target']}")
        print(f"Max Trades/Day: {CONFIG['max_trades_per_day']}")
        print("="*50)
        
        while True:
            try:
                self.reset_daily_counter()
                
                # Check each symbol
                for symbol in CONFIG['symbols']:
                    signal = self.analyze_market(symbol)
                    if signal and signal['score'] >= 30:
                        signal['symbol'] = symbol
                        self.execute_trade(signal)
                        
                # Monitor positions
                self.check_positions()
                
                # Show status
                print(f"\r📊 Time: {datetime.now().strftime('%H:%M:%S')} | "
                      f"Trades: {self.trades_today}/{CONFIG['max_trades_per_day']} | "
                      f"P&L: ${self.daily_pnl:.2f}", end="")
                
                time.sleep(60)  # Check every minute
                
            except KeyboardInterrupt:
                print("\n🛑 Bot stopped by user")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                time.sleep(60)

# ============================================
# RUN THE BOT
# ============================================
if __name__ == "__main__":
    bot = TradingBot()
    bot.run()