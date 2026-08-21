import time
import tkinter as tk
from tkinter import ttk
from datetime import datetime, timedelta
from collections import deque
from pytdx.hq import TdxHq_API

# ==================== 配置区 ====================
BOND_CODE = '123045'
MARKET = 0  # 0=深圳, 1=上海
INTERVAL = 3
FETCH_COUNT = 15

SERVER_LIST = [
    ('119.147.212.81', 7709),
    ('124.71.186.234', 7709),
    ('183.61.191.131', 7709),
]
# ===============================================

class KLineApp:
    def __init__(self, root):
        self.root = root
        self.root.title(f"可转债 {BOND_CODE} - 9秒K线实时监控")
        
        # 数据存储
        self.klines = deque(maxlen=300)  # 最多存300根9秒K线
        self.aggregator = NineSecKLineAggregator()
        self.last_time = None
        self.is_running = True

        # 创建画布（左侧）
        self.canvas = tk.Canvas(root, bg='black', width=800, height=500)
        self.canvas.pack(side=tk.LEFT, padx=5, pady=5, fill=tk.BOTH, expand=True)

        # 右侧信息面板
        self.info_frame = ttk.Frame(root, width=150)
        self.info_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.Y)
        
        self.label_title = ttk.Label(self.info_frame, text="实时数据", font=('Arial', 12, 'bold'))
        self.label_title.pack(pady=5)
        
        self.label_price = ttk.Label(self.info_frame, text="最新价: --", font=('Arial', 14))
        self.label_price.pack(pady=5)
        
        self.label_vol = ttk.Label(self.info_frame, text="成交量: --")
        self.label_vol.pack(pady=2)
        
        self.label_status = ttk.Label(self.info_frame, text="状态: 连接中...", foreground='orange')
        self.label_status.pack(pady=20)

        # 启动数据循环
        self.fetch_loop()

    def fetch_loop(self):
        """每隔3秒执行一次数据获取和绘图"""
        if not self.is_running:
            return
        
        try:
            # 1. 获取数据
            df_raw = fetch_latest()
            if df_raw is None or len(df_raw) == 0:
                self.label_status.config(text="状态: 无数据", foreground='red')
                self.root.after(INTERVAL * 1000, self.fetch_loop)
                return

            self.label_status.config(text="状态: 运行中", foreground='green')
            new_kline_created = False

            # 2. 逐笔更新聚合器（手动解析，无需pandas）
            for row in df_raw:
                dt = self._parse_time(row)
                if self.last_time is not None and dt <= self.last_time:
                    continue
                
                completed = self.aggregator.update(
                    price=row[2],   # 索引2对应收盘价？ 查看pytdx定义：通常返回 [日期, 开盘, 最高, 最低, 收盘, 成交额, 成交量, 时间]
                    volume=row[6],
                    amount=row[5],
                    trade_time=dt
                )
                if completed:
                    self.klines.append(completed)
                    new_kline_created = True
                    # 更新右侧最新价
                    self.label_price.config(text=f"最新价: {completed['close']:.3f}")
                    self.label_vol.config(text=f"成交量: {completed['vol']:,}")
                
                self.last_time = dt

            # 3. 如果有新K线生成，重绘画布
            if new_kline_created or len(self.klines) > 0:
                self.draw_chart()

        except Exception as e:
            self.label_status.config(text=f"错误: {str(e)[:10]}", foreground='red')

        # 递归调用自身，实现循环
        self.root.after(INTERVAL * 1000, self.fetch_loop)

    def _parse_time(self, row):
        """手动解析通达信时间格式，无需pandas"""
        # row[0] 是日期，格式如 20260821
        # row[7] 是时间，格式如 93000 或 143000
        date_str = str(row[0])
        time_int = row[7]
        time_str = str(time_int).zfill(6)
        dt_str = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]} {time_str[:2]}:{time_str[2:4]}:{time_str[4:6]}"
        return datetime.strptime(dt_str, "%Y-%m-%d %H:%M:%S")

    def draw_chart(self):
        """使用Tkinter绘制K线图（蜡烛图）"""
        self.canvas.delete("all")
        if len(self.klines) < 2:
            self.canvas.create_text(400, 250, text="等待K线数据...", fill='white', font=('Arial', 20))
            return

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if width < 10:
            width = 800
            height = 500

        # 计算价格区间
        high_prices = [k['high'] for k in self.klines]
        low_prices = [k['low'] for k in self.klines]
        max_price = max(high_prices)
        min_price = min(low_prices)
        price_range = max_price - min_price
        if price_range == 0:
            price_range = 0.01

        # 边距
        margin_left = 50
        margin_right = 20
        margin_top = 20
        margin_bottom = 30
        
        chart_width = width - margin_left - margin_right
        chart_height = height - margin_top - margin_bottom
        
        # K线宽度（占位）
        candle_width = max(2, chart_width / len(self.klines) * 0.8)
        gap = candle_width * 0.2

        # 绘制网格和刻度（粗略）
        # 绘制网格线
        for i in range(5):
            y = margin_top + chart_height - (i / 4) * chart_height
            self.canvas.create_line(margin_left, y, width - margin_right, y, fill='#333333', dash=(2,2))
            price_val = min_price + (i / 4) * price_range
            self.canvas.create_text(margin_left - 5, y, text=f"{price_val:.2f}", fill='gray', anchor='e')

        # 绘制每根K线
        for idx, k in enumerate(self.klines):
            x = margin_left + idx * (candle_width + gap)
            # 计算坐标（Y轴反转：高价比低价更靠近顶部）
            y_high = margin_top + chart_height - ((k['high'] - min_price) / price_range) * chart_height
            y_low = margin_top + chart_height - ((k['low'] - min_price) / price_range) * chart_height
            y_open = margin_top + chart_height - ((k['open'] - min_price) / price_range) * chart_height
            y_close = margin_top + chart_height - ((k['close'] - min_price) / price_range) * chart_height

            # 判断涨跌（阳线/阴线）
            is_red = k['close'] >= k['open']
            color = '#FF4D4D' if is_red else '#00FF00'  # 红涨绿跌（美股风格），也可改为国内红涨绿跌

            # 1. 绘制影线（最高到最低的竖线）
            self.canvas.create_line(x, y_high, x, y_low, fill=color, width=1)

            # 2. 绘制实体（矩形）
            top_y = min(y_open, y_close)
            bottom_y = max(y_open, y_close)
            # 实体高度至少要1像素
            if bottom_y - top_y < 1:
                top_y -= 1
            rect = self.canvas.create_rectangle(
                x - candle_width/2, top_y,
                x + candle_width/2, bottom_y,
                fill=color, outline=color
            )

        # 显示最新价格标注
        if len(self.klines) > 0:
            last = self.klines[-1]
            last_y = margin_top + chart_height - ((last['close'] - min_price) / price_range) * chart_height
            self.canvas.create_text(width - margin_right - 10, last_y, 
                                   text=f"{last['close']:.3f}", fill='yellow', anchor='e')

        # 更新标题
        if len(self.klines) > 0:
            last_time = self.klines[-1]['start_time'].strftime('%H:%M:%S')
            self.canvas.create_text(margin_left + 10, margin_top + 10, 
                                   text=f"K线数: {len(self.klines)}  最新: {last_time}", 
                                   fill='white', anchor='nw', font=('Arial', 10))

    def on_closing(self):
        """关闭窗口时停止循环"""
        self.is_running = False
        self.root.destroy()


# ---------- 数据获取函数（无Pandas版）----------
def fetch_latest():
    """直接返回原始元组列表，不转DataFrame"""
    api = TdxHq_API()
    for ip, port in SERVER_LIST:
        try:
            api.connect(ip, port, time_out=3)
            # get_security_bars 返回 list of tuples
            # 格式: (date, open, high, low, close, amount, vol, time)
            data = api.get_security_bars(7, MARKET, BOND_CODE, 0, FETCH_COUNT)
            api.disconnect()
            if data and len(data) > 0:
                # 按时间正序排列（原始是倒序）
                data.reverse()
                return data
        except Exception:
            continue
    return None


# ---------- 9秒K线聚合器（微调，适配tuple）----------
class NineSecKLineAggregator:
    def __init__(self):
        self.current_k = None
        self.last_window_id = None

    def _get_window_id(self, trade_time):
        base = datetime.combine(trade_time.date(), datetime.min.time()) + timedelta(hours=9, minutes=30)
        if trade_time < base:
            base = datetime.combine(trade_time.date(), datetime.min.time())
        delta = (trade_time - base).total_seconds()
        return int(delta // 9) if delta >= 0 else 0

    def update(self, price, volume, amount, trade_time):
        window_id = self._get_window_id(trade_time)
        if self.current_k is None:
            self.current_k = {'start_time': trade_time, 'open': price, 'high': price, 
                              'low': price, 'close': price, 'vol': volume, 'amount': amount}
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
            self.current_k = {'start_time': trade_time, 'open': price, 'high': price, 
                              'low': price, 'close': price, 'vol': volume, 'amount': amount}
            self.last_window_id = window_id
            return completed


# ---------- 启动程序 ----------
if __name__ == "__main__":
    root = tk.Tk()
    app = KLineApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.geometry("1000x600")
    root.mainloop()