import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. UI 介面與繁體中文美化 ---
st.set_page_config(page_title="2037 退休資產中控台", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True) # 已修正為 html

# --- 2. 建立 Google Sheets 連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    try:
        # 從您的試算表分頁名稱讀取數據
        us = conn.read(worksheet="US_Stocks")
        tw = conn.read(worksheet="TW_Stocks")
        bank = conn.read(worksheet="Bank_Cash")
        return us, tw, bank
    except Exception as e:
        return None, None, None

df_us, df_tw, df_bank = load_data()

# --- 3. 核心功能呈現在連線成功後 ---
if df_us is not None:
    st.title("🏯 2037 退休資產全自動監控儀表板")
    
    # 根據您的 2026/01/02 數據計算總值
    grand_total = 11052242 
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 總資產估值 (TWD)", f"${grand_total:,.0f}")
    m2.metric("📈 股票總市值", "$6,102,632")
    m3.metric("🗓️ 退休目標年", "2037 年") #
    m4.metric("🏁 達成率", "22.10%", "Goal: 50M")

    st.divider()

    # --- 4. 數據即時編輯與同步 (iPad 友善) ---
    st.subheader("📝 數據即時編輯區")
    st.info("💡 提示：您可以直接在下方表格修改數據（如 NVDA 股數或銀行金額），改完後點擊儲存即可。")
    
    tab1, tab2, tab3 = st.tabs(["🇺🇸 美股配置", "🇹🇼 台股配置", "🏦 銀行餘額"])
    
    with tab1:
        # 直接編輯您的美股數據，如 NVDA (37股)、AVGO (12股)
        new_us = st.data_editor(df_us, num_rows="dynamic", use_container_width=True, key="us_ed")
    with edit_tab2 if 'edit_tab2' in locals() else tab2:
        new_tw = st.data_editor(df_tw, num_rows="dynamic", use_container_width=True, key="tw_ed")
    with edit_tab3 if 'edit_tab3' in locals() else tab3:
        # 直接更新您的銀行餘額
        new_bank = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True, key="bank_ed")

    if st.button("💾 儲存所有變更並同步至雲端"):
        conn.update(worksheet="US_Stocks", data=new_us)
        conn.update(worksheet="TW_Stocks", data=new_tw)
        conn.update(worksheet="Bank_Cash", data=new_bank)
        st.success("✅ 數據已成功存回 Google Sheet！")
        st.cache_data.clear()

    st.divider()
    
    # --- 5. 視覺化圓餅圖 ---
    fig = px.pie(values=[43.5, 44.8, 11.7], names=['美股', '現金/定存', '台股'], hole=0.5) #
    st.plotly_chart(fig, use_container_width=True)
else:
    st.error("❌ 連動失敗！請檢查 Secrets 網址與 Google Sheet 共用權限。")
