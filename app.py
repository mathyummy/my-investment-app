import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px
from datetime import datetime

# --- 1. 基礎設定與連線 ---
st.set_page_config(page_title="2037 退休資產堡壘", layout="wide")
CURRENT_FX = 31.36 

# 直接從 Secrets 讀取網址
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 讀取數據 ---
@st.cache_data(ttl=600) # 每 10 分鐘抓取一次 Sheet 更新
def load_data():
    us_df = conn.read(worksheet="US_Stocks")
    tw_df = conn.read(worksheet="TW_Stocks")
    bank_df = conn.read(worksheet="Bank_Cash")
    return us_df, tw_df, bank_df

try:
    df_us, df_tw, df_bank = load_data()
    
    # 自動抓取所有標的現價
    all_tickers = df_us['Ticker'].tolist() + df_tw['Ticker'].tolist()
    
    @st.cache_data(ttl=3600)
    def get_prices(tickers):
        prices = {}
        for t in tickers:
            prices[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
        return prices

    prices = get_prices(all_tickers)

    # --- 3. 數據彙整與計算 ---
    total_us_twd = sum(prices.get(row['Ticker'], 0) * row['Qty'] * CURRENT_FX for _, row in df_us.iterrows())
    total_tw_twd = sum(prices.get(row['Ticker'], 0) * row['Qty'] for _, row in df_tw.iterrows())
    
    # 處理銀行存款 (含美金換算)
    live_cash = 0
    for _, row in df_bank.iterrows():
        val = row['Amount'] * (CURRENT_FX if row['Currency'] == "USD" else 1)
        live_cash += val

    # 固定定存數據 (這部分也可移入 Sheet)
    total_fixed = 4010000 
    grand_total = total_us_twd + total_tw_twd + live_cash + total_fixed

    # --- 4. 儀表板呈現 ---
    st.title("🏯 2037 退休資產全自動監控儀表板")
    
    # 頂部卡片
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("總資產淨值 (TWD)", f"${grand_total:,.0f}")
    m2.metric("股票總市值", f"${(total_us_twd + total_tw_twd):,.0f}")
    m3.metric("現金/定存總額", f"${(live_cash + total_fixed):,.0f}")
    m4.metric("退休目標進度", f"{(grand_total/50000000):.2%}", "Goal: 50M")

    # 分頁功能
    tab1, tab2, tab3 = st.tabs(["📊 總體配置", "🇺🇸 美股複委託", "🇹🇼 台股現股"])

    with tab1:
        c1, c2 = st.columns([6, 4])
        with c1:
            st.subheader("🎯 資產配置比例")
            fig = px.pie(values=[total_us_twd, total_tw_twd, live_cash + total_fixed], 
                         names=['美股', '台股', '現金/定存'], hole=0.4)
            st.plotly_chart(fig, use_container_width=True)
        with c2:
            st.write("**💰 銀行即時餘額**")
            st.table(df_bank)

    with tab2:
        st.subheader("🇺🇸 美股持倉獲利分析")
        us_display = []
        for _, s in df_us.iterrows():
            curr_p = prices.get(s['Ticker'], 0)
            m_val = curr_p * s['Qty'] * CURRENT_FX
            cost_twd = s['Cost'] if s['Currency'] == "TWD" else s['Cost'] * CURRENT_FX
            us_display.append({"代號": s['Ticker'], "類型": s['Type'], "市值(TWD)": m_val, "損益": m_val - cost_twd})
        st.dataframe(pd.DataFrame(us_display), use_container_width=True)

    with tab3:
        st.subheader("🇹🇼 台股持倉獲利分析")
        tw_display = []
        for _, s in df_tw.iterrows():
            curr_p = prices.get(s['Ticker'], 0)
            m_val = curr_p * s['Qty']
            tw_display.append({"名稱": s['Name'], "市值(TWD)": m_val, "損益": m_val - s['Cost']})
        st.dataframe(pd.DataFrame(tw_display), use_container_width=True)

except Exception as e:
    st.error(f"連動失敗，請檢查 Google Sheet 網址與分頁名稱：{e}")
