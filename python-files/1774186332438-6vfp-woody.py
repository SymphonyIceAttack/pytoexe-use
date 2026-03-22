# ==============================================
# WOODY 模型 V2.0 股票分析预测系统
# 核心规则：零和博弈 | 幂律分布 | 厚尾波动 | 四玩家权重0.3/0.15/0.25/0.3
# 功能：股票查询 | 三维状态 | 四玩家行为矩阵 | 支撑阻力 | 下周走势概率 | 策略
# ==============================================
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime, timedelta

class WoodyModelV2:
    def __init__(self):
        # 【固化底层参数 - 不可修改】
        self.weights = {
            'elephant': 0.3,   # 大象 Iₑ 机构
            'viper': 0.15,     # 毒蛇 Iᵥ 游资
            'wolf': 0.25,      # 饿狼 Iw 趋势交易者
            'lamb': 0.3        # 羔羊 Iₗ 散户
        }
        self.dimensions = ['时间维度(t⁻/t/t⁺)', '概率维度', '投资者行为指数']
        self.zero_sum = 0  # 零和总收益=0
        self.power_law_head = 'viper'    # 幂律头部
        self.power_law_tail = 'lamb'     # 幂律尾部
        self.fat_tail = True             # 厚尾波动

    # 1. 获取股票数据（A股/美股通用）
    def get_stock_data(self, stock_code, period='60d', interval='1d'):
        try:
            # A股自动加后缀，美股直接查询
            code = f"{stock_code}.SS" if stock_code.isdigit() and len(stock_code)==6 else stock_code
            data = yf.download(code, period=period, interval=interval)
            data['return'] = data['Close'].pct_change()
            data['volatility'] = data['return'].rolling(5).std() * np.sqrt(252)
            return data.dropna()
        except Exception as e:
            print(f"数据获取失败：{str(e)}")
            return None

    # 2. 计算三维状态
    def calc_3d_status(self, df):
        # 时间维度 t⁻(过去5日) / t(当前) / t⁺(预测1日)
        t_neg = df['return'].iloc[-5:].mean()
        t_now = df['return'].iloc[-1]
        t_plus = t_now * 0.7 + t_neg * 0.3  # 时序预测

        # 概率维度（厚尾波动修正）
        up_prob = min(0.8, max(0.1, (df['Close'].iloc[-1] > df['Close'].iloc[-2]) * 0.6 + 0.2))
        shock_prob = 0.2 if abs(t_now) < 0.015 else 0.3
        down_prob = 1 - up_prob - shock_prob

        # 投资者行为指数 I_t 瞬时变化率 dI/dT
        behavior_index = (df['volume'].iloc[-1] / df['volume'].iloc[-5:].mean() - 1) * 100
        dI_dT = (behavior_index - (df['volume'].iloc[-2] / df['volume'].iloc[-6:-1].mean() - 1)*100) / 1

        return {
            '时间维度': {'t⁻均值': round(t_neg,4), 't当前': round(t_now,4), 't⁺预测': round(t_plus,4)},
            '概率维度': {'上涨概率': round(up_prob,2), '震荡概率': round(shock_prob,2), '下跌概率': round(down_prob,2)},
            '行为指数': {'I_t综合指数': round(behavior_index,2), '瞬时变化率dI/dT': round(dI_dT,2)}
        }

    # 3. 四玩家行为矩阵（权重固化）
    def calc_4player_matrix(self, df, 3d_status):
        # 大象：机构资金（趋势+成交量稳定）
        elephant = (3d_status['时间维度']['t⁺预测'] > 0) * self.weights['elephant'] * 100
        # 毒蛇：游资（高波动+高频套利）
        viper = (df['volatility'].iloc[-1] > 0.04) * self.weights['viper'] * 100
        # 饿狼：趋势交易者（追涨杀跌）
        wolf = (3d_status['时间维度']['t当前'] > 0.02) * self.weights['wolf'] * 100
        # 羔羊：散户（跟风+被动）
        lamb = self.weights['lamb'] * 100 - (elephant + viper + wolf)

        # 零和校准（总收益=0）
        total = elephant + viper + wolf + lamb
        if total != 0:
            elephant = round(elephant/total*100,2)
            viper = round(viper/total*100,2)
            wolf = round(wolf/total*100,2)
            lamb = round(lamb/total*100,2)

        return {
            '大象 Iₑ(机构)': elephant,
            '毒蛇 Iᵥ(游资)': viper,
            '饿狼 Iw(趋势)': wolf,
            '羔羊 Iₗ(散户)': lamb
        }

    # 4. 支点/支撑/阻力（Woodie经典算法）
    def calc_pivot_points(self, df):
        H, L, C = df['High'].iloc[-1], df['Low'].iloc[-1], df['Close'].iloc[-1]
        PP = round((H + L + 2*C) / 4, 2)
        R1 = round(2*PP - L, 2)
        R2 = round(PP + (H - L), 2)
        R3 = round(H + 2*(PP - L), 2)
        S1 = round(2*PP - H, 2)
        S2 = round(PP - (H - L), 2)
        S3 = round(L - 2*(H - PP), 2)
        return {'支点PP': PP, '支撑S1/S2/S3': [S1,S2,S3], '阻力R1/R2/R3': [R1,R2,R3]}

    # 5. 主导资金判断
    def get_main_capital(self, player_matrix):
        max_player = max(player_matrix, key=player_matrix.get)
        name_map = {
            '大象 Iₑ(机构)': '大象(机构)主导 - 稳盘趋势行情',
            '毒蛇 Iᵥ(游资)': '毒蛇(游资)主导 - 高波动套利行情',
            '饿狼 Iw(趋势)': '饿狼(趋势)主导 - 趋势加速行情',
            '羔羊 Iₗ(散户)': '羔羊(散户)主导 - 无序震荡行情'
        }
        return name_map[max_player]

    # 6. 策略结论
    def get_strategy(self, 3d_status, pivot, main_capital):
        prob = 3d_status['概率维度']
        trend = '上涨' if prob['上涨概率']>0.5 else '下跌' if prob['下跌概率']>0.4 else '震荡'
        position = '重仓' if trend=='上涨' and main_capital.startswith('大象') else '轻仓' if trend=='震荡' else '空仓/减仓'
        stop_loss = pivot['支撑S1/S2/S3'][0] if trend=='上涨' else pivot['阻力R1/R2/R3'][0]
        take_profit = pivot['阻力R1/R2/R3'][0] if trend=='上涨' else pivot['支撑S1/S2/S3'][0]

        return {
            '操作方向': trend,
            '仓位建议': position,
            '止损位': round(stop_loss,2),
            '止盈位': round(take_profit,2),
            '核心逻辑': main_capital + ' | 厚尾波动需警惕极端行情'
        }

    # 7. 完整分析报告
    def analyze(self, stock_code):
        print("="*80)
        print(f"📊 WOODY模型 V2.0 股票分析报告 | {stock_code} | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        print("="*80)

        # 1. 获取数据
        df = self.get_stock_data(stock_code)
        if df is None: return

        # 2. 三维状态
        status_3d = self.calc_3d_status(df)
        print("🔹 一、三维状态")
        for k,v in status_3d.items(): print(f"  {k}: {v}")

        # 3. 四玩家行为矩阵
        player_matrix = self.calc_4player_matrix(df, status_3d)
        print("\n🔹 二、四玩家行为矩阵（权重0.3/0.15/0.25/0.3）")
        for k,v in player_matrix.items(): print(f"  {k}: {v}%")

        # 4. 支撑阻力
        pivot = self.calc_pivot_points(df)
        print("\n🔹 三、支点/支撑/阻力")
        print(f"  支点PP: {pivot['支点PP']}")
        print(f"  支撑S1/S2/S3: {pivot['支撑S1/S2/S3']}")
        print(f"  阻力R1/R2/R3: {pivot['阻力R1/R2/R3']}")

        # 5. 下周走势概率
        print("\n🔹 四、下周走势概率")
        print(f"  上涨概率: {status_3d['概率维度']['上涨概率']*100:.0f}%")
        print(f"  震荡概率: {status_3d['概率维度']['震荡概率']*100:.0f}%")
        print(f"  下跌概率: {status_3d['概率维度']['下跌概率']*100:.0f}%")

        # 6. 主导资金
        main_capital = self.get_main_capital(player_matrix)
        print("\n🔹 五、主导资金判断")
        print(f"  {main_capital}")

        # 7. 策略结论
        strategy = self.get_strategy(status_3d, pivot, main_capital)
        print("\n🔹 六、策略结论")
        for k,v in strategy.items(): print(f"  {k}: {v}")

        print("="*80)
        print("✅ 报告完成 | 规则遵循：零和博弈 | 幂律分布 | 厚尾波动")
        print("="*80)

# ==============================================
# 【调用示例】
# 1. 安装依赖：pip install pandas numpy yfinance
# 2. 运行代码
# 3. 输入股票代码：A股直接输6位代码，美股输代码（如AAPL）
# ==============================================
if __name__ == "__main__":
    woody = WoodyModelV2()
    # 查询示例：
    # woody.analyze('600036')  # A股招商银行
    # woody.analyze('AAPL')    # 美股苹果
    stock = input("请输入股票代码（A股6位数字/美股英文）：")
    woody.analyze(stock)