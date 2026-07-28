import akshare as ak
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time

# 设置页面
st.set_page_config(page_title="A股板块资金流向", layout="wide")
st.title("📊 A股板块资金流向可视化")

# 颜色设定（红涨绿跌）
COLOR_SCALE = [
    [0.0, "#00cc00"],    
    [0.45, "#e6ffe6"],   
    [0.5, "#ffffff"],    
    [0.55, "#ffe5e5"],   
    [1.0, "#ff0000"]     
]

# 函数：获取数据
def get_sector_fund_flow(indicator="今日"):
    try:
        raw = ak.stock_sector_fund_flow_rank(indicator=indicator, sector_type="行业资金流")
        df = raw.rename(columns={'名称': '板块名称'})
        df['资金净流入(亿)'] = df['主力净流入-净额'] / 100000000
        df['资金净流入(亿)'] = df['资金净流入(亿)'].round(2)
        df['涨跌幅'] = pd.to_numeric(df['涨跌幅'], errors='coerce')
        df['流向强度'] = abs(df['资金净流入(亿)'])
        return df.dropna(subset=['资金净流入(亿)'])
    except Exception as e:
        return pd.DataFrame()

# 函数：热力图
def generate_heatmap(df):
    fig = px.treemap(
        df,
        path=['板块名称'],
        values='流向强度',
        color='资金净流入(亿)',
        color_continuous_scale=COLOR_SCALE,
        hover_data={'涨跌幅': ':.2f%', '资金净流入(亿)': ':.2f'},
        title="板块资金流向热力图",
        height=700
    )
    return fig

# 函数：排行榜
def generate_rank_chart(df, top_n=20):
    sorted_df = df.sort_values('资金净流入(亿)', ascending=False)
    top_df = sorted_df.head(top_n)
    colors = ['red' if x > 0 else 'green' for x in top_df['资金净流入(亿)']]
    fig = go.Figure(data=[
        go.Bar(
            x=top_df['资金净流入(亿)'],
            y=top_df['板块名称'],
            orientation='h',
            marker_color=colors,
            text=top_df['资金净流入(亿)'].round(2),
            textposition='outside'
        )
    ])
    fig.update_layout(title=f"净流入 TOP {top_n}", xaxis_title="净流入（亿元）", height=600)
    return fig

# ----- 界面主体 -----
with st.sidebar:
    st.header("⚙️ 控制")
    indicator = st.radio("周期", ["今日", "5日", "10日"], index=0, horizontal=True)
    top_n = st.slider("显示数量", 5, 50, 20)
    auto_refresh = st.checkbox("自动刷新（30秒）")
    st.caption("数据来源：东方财富（AKShare）")

placeholder = st.empty()

while True:
    with placeholder.container():
        df = get_sector_fund_flow(indicator)
        
        if df.empty:
            st.error("获取数据失败，请检查网络后刷新页面")
            break
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总板块数", len(df))
        with col2:
            inflow = df[df['资金净流入(亿)'] > 0]['资金净流入(亿)'].sum()
            st.metric("总净流入", f"{inflow:.2f} 亿")
        with col3:
            outflow = df[df['资金净流入(亿)'] < 0]['资金净流入(亿)'].sum()
            st.metric("总净流出", f"{outflow:.2f} 亿", delta_color="inverse")
        
        left, right = st.columns([2, 1])
        with left:
            st.plotly_chart(generate_heatmap(df), use_container_width=True)
        with right:
            st.plotly_chart(generate_rank_chart(df, top_n), use_container_width=True)
        
        with st.expander("查看详细数据"):
            st.dataframe(df[['板块名称', '资金净流入(亿)', '涨跌幅']].sort_values('资金净流入(亿)', ascending=False))
        
        st.caption(f"更新时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if not auto_refresh:
        break
    time.sleep(30)