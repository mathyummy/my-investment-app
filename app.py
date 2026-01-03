import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="2037 退休資產堡壘", layout="wide")

# 建立連線
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=600)
def load_data():
    # 使用 try-except 捕捉連動錯誤
    try:
        us_df = conn.read(worksheet="US_Stocks")
        tw_df = conn.read(worksheet="TW_Stocks")
        bank_df = conn.read(worksheet="Bank_Cash")
        return us_df, tw_df, bank_df
    except Exception as e:
        return None, None, None

df_us, df_tw, df_bank = load_data()

if df_us is None:
    st.error("❌ 連動失敗！請檢查：1. Google Sheet 是否設定『知道連結的任何人都可檢視』 2. Secrets 網址是否正確 3. 分頁名稱是否正確。")
    st.info("目前的網址 ID 應為: 10LR1nJAxAtw6oV718zpdKqzP7GpIL3xtBHS02Sfmb6I")
else:
    st.success("✅ 數據連動成功！")
    # --- 這裡開始放原本的計算與圖表邏輯 ---
    st.write("### 🇺🇸 美股配置 (從 Google Sheet 讀取)")
    st.dataframe(df_us)
    st.write("### 🏦 銀行現金 (從 Google Sheet 讀取)")
    st.dataframe(df_bank)
