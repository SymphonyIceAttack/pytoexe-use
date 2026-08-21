import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import mplfinance as mpf
from pytdx.hq import TdxHq_API
from datetime import datetime, timedelta
from collections import deque

# ==================== 配置区 ====================
BOND_CODE = '123045'          # 可转债代码（纯数字，如123045）
MARKET = 0                    # 0=深圳(123/127开头)  1=上海(110/113/118开头)
INTERVAL = 3                  # 数据轮询间隔（秒）
FETCH_COUNT = 15              # 每次拉取最近15笔，确保不漏

SERVER_LIST = [
    ('119.147.212.81', 7709),
    ('124.71.186.234', 7709),
    ('183.61.191.131', 7709),
]

# 全局存储已完成K线的DataFrame
kline_df = pd.DataFrame()
# ===============================================

# ---------- 数据获取函数 ----------
def fetch_latest():
    api = TdxHq_API()
    for ip, port in SERVER_LIST:
        try:
            api.connect(ip, port, time_out=3)
            data = api.get_security_bars(7, MARKET, BOND_CODE, 0, FETCH_COUNT)
            api.disconnect()
            if data and len(data) > 0:
                df = api.to_df(data)
                df['datetime'] = pd.to_datetime(df['datetime'], format='%Y%m%d')
                df['time_str'] = df['time'].astype(str).str.zfill(6)
                df['time_str'] = df['time_str'].str[:2] + ':' + df['time_str'].str[2:4] + ':' + df['time_str'].str[4:6]
                df['full_dt'] = pd.to_datetime(df['datetime'].astype(str) + ' ' + df['time_str'])
                df = df.sort_values('full_dt').reset_index(drop=True)
                return df
        except Exception:
            continue
    return None

# ---------- 9秒K线聚合器 ----------
class NineSecKLineAggregator:
    def __init__(self):
        self.current_k = None
        self.last_window_id = None
        self.last_trade_time = None
        self.completed_klines = []  # 存储完成的K线（用于绘图）

    def _get_window_id(self, trade_time):
        base = datetime.combine(trade_time.date(), datetime.min.time()) + timedelta(hours=9, minutes=30)
        if trade_time < base:
            base = datetime.combine(trade_time.date(), datetime.min.time())
        delta = (trade_time - base).total_seconds()
        return int(delta // 9) if delta >= 0 else 0

    def update(self, price, volume, amount, trade_time):
        window_id = self._get_window_id(trade_time)
        if self.current_k is None:
            self.current_k = {'start_time': trade_time, 'open': price, 'high': price, 'low': price, 'close': price, 'vol': volume, 'amount': amount}
            self.last_window_id = window_id
            return None
        if window_id == self.last_window_id:
            self.current_k['high'] = max(self.current_k['high'], price)
            self.current_k['low'] = min(self.current_k['low'], price)
            self.current_k['close'] = price
            self.current_k['vol'] += volume
            self.current_k['amount'] += amount
            return None
        else:
            completed = self.current_k.copy()
            self.current_k = {'start_time': trade_time, 'open': price, 'high': price, 'low': price, 'close': price, 'vol': volume, 'amount': amount}
            self.last_window_id = window_id
            return completed

# ---------- 实时绘图更新函数 ----------
def update_chart(df, fig, ax):
    """清除旧图并绘制新的K线图"""
    ax.clear()
    if len(df) < 2:
        ax.text(0.5, 0.5, '等待数据...', ha='center', va='center')
        return
    # 设置索引为时间
    df.index = pd.DatetimeIndex(df['start_time'])
    # 使用 mplfinance 绘制到指定的 ax 上
    mpf.plot(df, type='candle', ax=ax, volume=False, style='charles', 
             xrotation=0, ylabel='价格', width=0.8)
    ax.set_title(f'可转债 {BOND_CODE}  9秒K线 (最新: {df["close"].iloc[-1]:.3f})')
    fig.canvas.draw_idle()
    plt.pause(0.01)

# ---------- 主程序 ----------
def main():
    global kline_df
    print(f"🚀 启动监控: 可转债 {BOND_CODE}，9秒K线实时绘制...")
    print("📌 绘图窗口将弹出，请勿关闭终端。按 Ctrl+C 停止。\n")

    aggregator = NineSecKLineAggregator()
    last_processed_time = None

    # 开启 matplotlib 交互模式
    plt.ion()
    fig, ax = plt.subplots(figsize=(12, 6))
    plt.title("正在连接数据...")
    plt.show(block=False)

    while True:
        try:
            df_raw = fetch_latest()
            if df_raw is None or len(df_raw) == 0:
                print(f"⚠️  {datetime.now().strftime('%H:%M:%S')} 无数据，{INTERVAL}秒后重试...")
                time.sleep(INTERVAL)
                continue

            # 逐笔更新聚合器
            for idx, row in df_raw.iterrows():
                dt = row['full_dt']
                if last_processed_time is not None and dt <= last_processed_time:
                    continue
                completed = aggregator.update(row['price'], row['vol'], row['amount'], dt)
                if completed:
                    # 将完成的K线加入DataFrame
                    kline_df = pd.concat([kline_df, pd.DataFrame([completed])], ignore_index=True)
                    # 只保留最近500根K线（防止内存爆炸）
                    if len(kline_df) > 500:
                        kline_df = kline_df.tail(500)
                    # 更新图表
                    update_chart(kline_df, fig, ax)
                    print(f"📊 新K线生成: {completed['start_time'].strftime('%H:%M:%S')}  C:{completed['close']:.3f}  Vol:{completed['vol']:,}")
                last_processed_time = dt

        except KeyboardInterrupt:
            print("\n🛑 用户停止监控。")
            break
        except Exception as e:
            print(f"❌ 发生错误: {e}，3秒后重试...")
            time.sleep(INTERVAL)
        
        time.sleep(INTERVAL)

    plt.ioff()
    plt.show(block=True)  # 保持窗口显示

if __name__ == "__main__":
    main()