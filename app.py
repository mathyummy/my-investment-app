import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. 基礎設定與連動 ---
st.set_page_config(page_title="2037 退休資產堡壘", layout="wide")

# 請將下方的網址替換成您剛剛複製的 Google Sheet 網址
# 注意：這只是讀取公開/連結分享的表格，安全性高
SHEET_URL = "您的_GOOGLE_SHEET_網址_貼在這裡"

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

# --- 2. 讀取數據函數 ---
@st.cache_data(ttl=600) # 每 10 分鐘自動從 Google Sheet 抓取一次新數據
def load_data():
    us_df = conn.read(spreadsheet=SHEET_URL, worksheet="US_Stocks")
    tw_df = conn.read(spreadsheet=SHEET_URL, worksheet="TW_Stocks")
    cash_df = conn.read(spreadsheet=SHEET_URL, worksheet="Bank_Cash")
    return us_df, tw_df, cash_df

try:
    df_us, df_tw, df_cash = load_data()

    # --- 3. 自動抓取最新股價 ---
    all_tickers = df_us['Ticker'].tolist() + df_tw['Ticker'].tolist()
    
    @st.cache_data(ttl=3600)
    def get_live_prices(tickers):
        prices = {}
        for t in tickers:
            prices[t] = yf.Ticker(t).history(period="1d")['Close'].iloc[-1]
        return prices

    prices = get_live_prices(all_tickers)

    # --- 4. 儀表板呈現邏輯 (同前，但資料來源改為 DataFrame) ---
    st.title("🏯 2037 退休資產連動儀表板")
    
    # 這裡會自動根據您的表格內容列出所有的資產
    # 只要您在 Google Sheet 增加一行，這裡就會多出一行
    st.write("數據來源：已成功連動您的 Google Sheet")
    st.dataframe(df_us) # 顯示美股
    st.dataframe(df_tw) # 顯示台股

except Exception as e:
    st.error(f"連動失敗，請檢查分頁名稱與網址是否正確。錯誤訊息：{e}")
