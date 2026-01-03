import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 基礎設定 ---
st.set_page_config(page_title="2037 退休資產堡壘", layout="wide")
CURRENT_FX = 31.36  # 您提供的基準匯率

# --- 1. 數據初始化 (根據 2026/01/02 修正版) ---
# 美股清單：區分台幣複委託(TWD Cost)與外幣複委託(USD Cost)
us_portfolio = [
    {"Ticker": "SGOV", "Type": "外幣複委託", "Qty": 1154, "Cost": 115931, "Currency": "USD"},
    {"Ticker": "GOOGL", "Type": "外幣複委託", "Qty": 23, "Cost": 7092, "Currency": "USD"},
    {"Ticker": "NVDA", "Type": "台幣複委託", "Qty": 37, "Cost": 221150, "Currency": "TWD"}, # 範例成本
    {"Ticker": "AVGO", "Type": "台幣複委託", "Qty": 12, "Cost": 131800, "Currency": "TWD"}, # 範例成本
    {"Ticker": "SCHG", "Type": "外幣複委託", "Qty": 122, "Cost": 4006, "Currency": "USD"},
    {"Ticker": "VOO", "Type": "外幣複委託", "Qty": 8.27, "Cost": 5151, "Currency": "USD"},
    {"Ticker": "QQQ", "Type": "外幣複委託", "Qty": 6.03, "Cost": 3402, "Currency": "USD"},
    {"Ticker": "TSLA", "Type": "外幣複委託", "Qty": 4, "Cost": 1782, "Currency": "USD"},
    {"Ticker": "VT", "Type": "外幣複委託", "Qty": 23.87, "Cost": 3122, "Currency": "USD"},
    {"Ticker": "VTI", "Type": "外幣複委託", "Qty": 2.77, "Cost": 800, "Currency": "USD"},
]

# 台股清單
tw_portfolio = [
    {"Ticker": "0050.TW", "Name": "元大台灣50", "Qty": 5450, "Cost": 270000}, # 範例成本
    {"Ticker": "2882.TW", "Name": "國泰金", "Qty": 3000, "Cost": 110000},
    {"Ticker": "4925.TWO", "Name": "智微", "Qty": 13000, "Cost": 445000},
    {"Ticker": "00692.TW", "Name": "富邦公司治理", "Qty": 1000, "Cost": 25000},
    {"Ticker": "00919.TW", "Name": "群益精選高息", "Qty": 1000, "Cost": 20000},
    {"Ticker": "00713.TW", "Name": "元大高息低波", "Qty": 2000, "Cost": 100000},
]

# 銀行定存數據
fixed_deposits = [
    {"Bank": "中信", "Amount": 750000, "Date": "2026-01-16"},
    {"Bank": "中信", "Amount": 1000000, "Date": "2026-07-16"},
    {"Bank": "中信", "Amount": 560000, "Date": "2026-12-16"},
    {"Bank": "國泰", "Amount": 500000, "Date": "2026-03-01"},
    {"Bank": "國泰", "Amount": 1200000, "Date": "2026-06-11"},
]

# --- 2. 獲利計算引擎 ---
@st.cache_data(ttl=3600) # 每小時更新一次股價
def get_prices(tickers):
    prices = {}
    for t in tickers:
        try:
            ticker = yf.Ticker(t)
            prices[t] = ticker.history(period="1d")['Close'].iloc[-1]
        except:
            prices[t] = 0
    return prices

# 抓取所有價格
all_tickers = [x['Ticker'] for x in us_portfolio] + [x['Ticker'] for x in tw_portfolio]
prices = get_prices(all_tickers)

# --- 3. 網頁介面佈局 ---
st.title("🏯 2037 退休資產全自動監控儀表板")
st.caption(f"數據基準日: 2026/01/02 | 當前匯率: {CURRENT_FX}")

# 頂部總覽卡片
total_us_twd = 0
total_tw_twd = 0

# 計算美股
for stock in us_portfolio:
    current_p = prices.get(stock['Ticker'], 0)
    market_val_usd = current_p * stock['Qty']
    market_val_twd = market_val_usd * CURRENT_FX
    total_us_twd += market_val_twd

# 計算台股
for stock in tw_portfolio:
    current_p = prices.get(stock['Ticker'], 0)
    market_val_twd = current_p * stock['Qty']
    total_tw_twd += market_val_twd

cash_twd = 263132 + (21571.37 * CURRENT_FX) + 4010000
grand_total = total_us_twd + total_tw_twd + cash_twd

m1, m2, m3, m4 = st.columns(4)
m1.metric("總資產淨值 (TWD)", f"${grand_total:,.0f}")
m2.metric("股票總市值", f"${(total_us_twd + total_tw_twd):,.0f}")
m3.metric("現金/定存總額", f"${cash_twd:,.0f}")
m4.metric("退休目標進度", f"{(grand_total/50000000):.2%}", "Goal: 50M")

# 側邊欄：定存提醒
st.sidebar.header("⏳ 定存到期倒數")
today = datetime.now().date()
for fd in fixed_deposits:
    expiry = datetime.strptime(fd['Date'], "%20%y-%m-%d").date()
    days_left = (expiry - today).days
    color = "red" if days_left < 14 else "white"
    st.sidebar.markdown(f":{color}[{fd['Bank']} ${fd['Amount']:,} | {fd['Date']} ({days_left}天)]")

# 主圖表區
c1, c2 = st.columns([6, 4])

with c1:
    st.subheader("📊 美股持倉獲利分析")
    us_display = []
    for s in us_portfolio:
        curr_p = prices.get(s['Ticker'], 0)
        m_val_twd = curr_p * s['Qty'] * CURRENT_FX
        # 損益邏輯：台幣複委託用台幣扣，外幣複委託換算台幣後扣
        cost_twd = s['Cost'] if s['Currency'] == "TWD" else s['Cost'] * CURRENT_FX
        profit = m_val_twd - cost_twd
        us_display.append({"代號": s['Ticker'], "類型": s['Type'], "市值(TWD)": m_val_twd, "損益": profit})
    
    df_us = pd.DataFrame(us_display)
    st.dataframe(df_us.style.format({"市值(TWD)": "{:,.0f}", "損益": "{:,.0f}"}), use_container_width=True)

with c2:
    st.subheader("🎯 資產配置比例")
    fig = px.pie(values=[total_us_twd, total_tw_twd, cash_twd], 
                 names=['美股', '台股', '現金/定存'], hole=0.4)
    st.plotly_chart(fig, use_container_width=True)

st.success("💡 2026 投資提示：中信 1/16 將有 75 萬定存到期，可考慮按計畫轉入美股部位。")
