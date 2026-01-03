import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. UI 樣式美化 (CSS) ---
st.set_page_config(page_title="2037 退休資產中控台", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .metric-card { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-left: 5px solid #4CAF50; }
    .stMetric { font-weight: bold; }
    </style>
    """, unsafe_allow_stdio=True)

# --- 2. 連動與讀取 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    us = conn.read(worksheet="US_Stocks")
    tw = conn.read(worksheet="TW_Stocks")
    bank = conn.read(worksheet="Bank_Cash")
    return us, tw, bank

df_us, df_tw, df_bank = load_data()

# --- 3. 自動抓取即時股價 ---
@st.cache_data(ttl=3600)
def get_prices(tickers):
    prices = {}
    for t in tickers:
        try: prices[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
        except: prices[t] = 0
    return prices

all_tickers = df_us['Ticker'].tolist() + df_tw['Ticker'].tolist()
prices = get_prices(all_tickers)

# --- 4. 頂部儀表板：核心指標 ---
st.title("🛡️ 2037 退休資產全自動監控儀表板")
CURRENT_FX = 31.36 #

# 計算邏輯
total_us_twd = sum(prices.get(row['Ticker'], 0) * row['Qty'] * (CURRENT_FX if row['Currency'] == 'USD' else 1) for _, row in df_us.iterrows())
total_tw_twd = sum(prices.get(row['Ticker'], 0) * row['Qty'] for _, row in df_tw.iterrows())
total_cash_twd = sum(row['Amount'] * (CURRENT_FX if row['Currency'] == 'USD' else 1) for _, row in df_bank.iterrows())
grand_total = total_us_twd + total_tw_twd + total_cash_twd + 4010000 #

m1, m2, m3, m4 = st.columns(4)
with m1: st.metric("💰 總資產估值", f"${grand_total:,.0f} TWD")
with m2: st.metric("📈 股票市值", f"${(total_us_twd + total_tw_twd):,.0f}")
with m3: st.metric("🗓️ 退休倒數", "11 年", "Target: 2037")
with m4: st.metric("🏁 達成率", f"{(grand_total/50000000):.1%}", "Goal: 50M")

st.divider()

# --- 5. 互動修改區：直接在 App 改資料 ---
st.subheader("📝 數據編輯與同步")
st.info("💡 您可以直接在下方表格修改股數或金額，改完請按下方『儲存更新至雲端』按鈕。")

tab_edit1, tab_edit2, tab_edit3 = st.tabs(["🇺🇸 美股編輯", "🇹🇼 台股編輯", "🏦 銀行編輯"])

with tab_edit1:
    edited_us = st.data_editor(df_us, num_rows="dynamic", use_container_width=True, key="us_editor")
with tab_edit2:
    edited_tw = st.data_editor(df_tw, num_rows="dynamic", use_container_width=True, key="tw_editor")
with tab_edit3:
    edited_bank = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True, key="bank_editor")

if st.button("💾 儲存所有更新至 Google Sheets"):
    conn.update(worksheet="US_Stocks", data=edited_us)
    conn.update(worksheet="TW_Stocks", data=edited_tw)
    conn.update(worksheet="Bank_Cash", data=edited_bank)
    st.success("✅ 數據已成功同步回 Google Sheets！")
    st.cache_data.clear()

st.divider()

# --- 6. 視覺化分析 ---
c1, c2 = st.columns([6, 4])
with c1:
    st.subheader("📊 持倉獲利排行 Top 5")
    # 獲利計算邏輯
    df_us['Profit'] = df_us.apply(lambda x: (prices.get(x['Ticker'], 0) * x['Qty'] * (CURRENT_FX if x['Currency'] == 'USD' else 1)) - (x['Cost'] * (CURRENT_FX if x['Currency'] == 'USD' else 1)), axis=1)
    st.bar_chart(df_us.set_index('Ticker')['Profit'])
with c2:
    st.subheader("🎯 資產分佈")
    fig = px.pie(values=[total_us_twd, total_tw_twd, total_cash_twd + 4010000], names=['美股', '台股', '現金/定存'], hole=0.5, color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig, use_container_width=True)
