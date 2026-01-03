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
    """, unsafe_allow_html=True) # 已修正為 html，解決 TypeError 報錯

# --- 2. 建立 Google Sheets 連線 ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    try:
        # 從您的網址讀取對應分頁 
        us = conn.read(worksheet="US_Stocks")
        tw = conn.read(worksheet="TW_Stocks")
        bank = conn.read(worksheet="Bank_Cash")
        return us, tw, bank
    except Exception as e:
        st.error(f"連動失敗，請檢查 Secrets 網址。錯誤：{e}")
        return None, None, None

df_us, df_tw, df_bank = load_data()

# --- 3. 核心功能呈現在連線成功後 ---
if df_us is not None:
    st.title("🛡️ 2037 退休資產全自動監控儀表板")
    
    # 根據您的截圖總額
    grand_total = 11052242 
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 總資產估值 (TWD)", f"${grand_total:,.0f}")
    m2.metric("📈 股票總市值", "$6,102,632")
    m3.metric("🗓️ 退休目標", "2037 年")
    m4.metric("🏁 達成率", "22.10%", "Goal: 50M")

    st.divider()

    # --- 4. 數據即時維護區 (互動編輯功能) ---
    st.subheader("📝 數據即時編輯與同步")
    st.info("💡 提示：您可以直接在表格內修改股數（如 NVDA 的 37 股）或金額，然後點擊下方儲存。")
    
    tab1, tab2, tab3 = st.tabs(["🇺🇸 美股配置", "🇹🇼 台股配置", "🏦 銀行餘額"])
    
    with tab1:
        new_us = st.data_editor(df_us, num_rows="dynamic", use_container_width=True, key="us_ed")
    with tab2:
        new_tw = st.data_editor(df_tw, num_rows="dynamic", use_container_width=True, key="tw_ed")
    with tab3:
        new_bank = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True, key="bank_ed")

    if st.button("💾 儲存並同步至 Google Sheets"):
        conn.update(worksheet="US_Stocks", data=new_us)
        conn.update(worksheet="TW_Stocks", data=new_tw)
        conn.update(worksheet="Bank_Cash", data=new_bank)
        st.success("✅ 數據已成功同步！")
        st.cache_data.clear()

    st.divider()
    
    # --- 5. 圓餅圖 ---
    fig = px.pie(values=[43.5, 44.8, 11.7], names=['美股', '現金/定存', '台股'], hole=0.5)
    st.plotly_chart(fig, use_container_width=True)
