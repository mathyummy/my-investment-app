import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px

st.set_page_config(page_title="2037 退休資產堡壘", layout="wide")

# --- 1. 自動讀取 Google Sheet (使用 CSV 匯出模式，最穩定) ---
SHEET_ID = "10LR1nJAxAtw6oV718zpdKqzP7GpIL3xtBHS02Sfmb6I"

@st.cache_data(ttl=600)
def load_data_direct(sheet_name):
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    return pd.read_csv(url)

try:
    # 讀取三個分頁
    df_us = load_data_direct("US_Stocks")
    df_tw = load_data_direct("TW_Stocks")
    df_bank = load_data_direct("Bank_Cash")
    
    st.success("✅ 數據同步成功！")

    # --- 2. 抓取股價與匯率 ---
    CURRENT_FX = 31.36 
    all_tickers = df_us['Ticker'].tolist() + df_tw['Ticker'].tolist()
    
    @st.cache_data(ttl=3600)
    def get_live_prices(tickers):
        prices = {}
        for t in tickers:
            try:
                prices[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
            except: prices[t] = 0
        return prices

    prices = get_live_prices(all_tickers)

    # --- 3. 計算總資產 ---
    # 美股總額
    total_us = sum(prices.get(row['Ticker'], 0) * row['Qty'] * (CURRENT_FX if row['Currency'] == 'USD' else 1) for _, row in df_us.iterrows())
    # 台股總額
    total_tw = sum(prices.get(row['Ticker'], 0) * row['Qty'] for _, row in df_tw.iterrows())
    # 現金總額 (根據您的表格標題 Ticker, Amount)
    total_cash = sum(row['Amount'] * (CURRENT_FX if row['Currency'] == 'USD' else 1) for _, row in df_bank.iterrows())
    
    grand_total = total_us + total_tw + total_cash + 4010000 # 加上固定定存

    # --- 4. 呈現介面 ---
    st.metric("總資產淨值 (TWD)", f"${grand_total:,.0f}")
    
    tab1, tab2, tab3 = st.tabs(["📊 資產分佈", "🇺🇸 美股明細", "🇹🇼 台股明細"])
    with tab1:
        fig = px.pie(values=[total_us, total_tw, total_cash + 4010000], names=['美股', '台股', '現金/定存'], hole=0.4)
        st.plotly_chart(fig)
        st.write("### 🏦 銀行餘額明細")
        st.table(df_bank)
    with tab2:
        st.dataframe(df_us)
    with tab3:
        st.dataframe(df_tw)

except Exception as e:
    st.error(f"連動失敗：{e}")
    st.info("請檢查您的 Google Sheet 是否已開啟：共用 -> 知道連結的人均可檢視")
