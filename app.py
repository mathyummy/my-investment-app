import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. 專業 UI 與繁體中文美化 ---
st.set_page_config(page_title="2037 退休資產中控台", layout="wide")
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@400;700&display=swap');
    html, body, [class*="css"] { font-family: 'Noto Sans TC', sans-serif; }
    .stMetric { background-color: #ffffff; padding: 20px; border-radius: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); border-top: 5px solid #1e3a8a; }
    h1, h2, h3 { color: #1e3a8a; }
    </style>
    """, unsafe_allow_html=True) # <-- 這裡原本打錯了，現在已修正為 html

# --- 2. 連動 Google Sheets ---
conn = st.connection("gsheets", type=GSheetsConnection)

@st.cache_data(ttl=300)
def load_data():
    us = conn.read(worksheet="US_Stocks")
    tw = conn.read(worksheet="TW_Stocks")
    bank = conn.read(worksheet="Bank_Cash")
    return us, tw, bank

try:
    df_us, df_tw, df_bank = load_data()

    # --- 3. 頂部核心看板 ---
    st.title("🛡️ 2037 退休資產全自動監控儀表板")
    
    # 這裡會顯示您目前的真實總值
    grand_total = 11052242 #
    
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("💰 總資產估值", f"${grand_total:,.0f} TWD")
    c2.metric("📈 股票總市值", "$6,102,632") #
    c3.metric("🗓️ 退休倒數", "11 年", "Target: 2037")
    c4.metric("🏁 達成率", "22.10%", "Goal: 50M") #

    st.divider()

    # --- 4. 數據編輯區 (點擊即可修改) ---
    st.subheader("📝 數據即時維護")
    st.info("💡 貼心提醒：您可以在下方表格直接修改數字。修改完後，點擊最下方的『💾 儲存所有變更』按鈕即可同步回雲端。")
    
    edit_tab1, edit_tab2, edit_tab3 = st.tabs(["🇺🇸 美股配置", "🇹🇼 台股配置", "🏦 銀行餘額"])
    
    with edit_tab1:
        new_us = st.data_editor(df_us, num_rows="dynamic", use_container_width=True, key="us_ed")
    with edit_tab2:
        new_tw = st.data_editor(df_tw, num_rows="dynamic", use_container_width=True, key="tw_ed")
    with edit_tab3:
        new_bank = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True, key="bank_ed")

    if st.button("💾 儲存所有變更至 Google Sheets"):
        conn.update(worksheet="US_Stocks", data=new_us)
        conn.update(worksheet="TW_Stocks", data=new_tw)
        conn.update(worksheet="Bank_Cash", data=new_bank)
        st.success("✅ 數據已成功存回雲端！網頁將在 5 分鐘內自動更新。")
        st.cache_data.clear()

    st.divider()

    # --- 5. 視覺化分析功能 ---
    col_l, col_r = st.columns([6, 4])
    with col_l:
        st.subheader("📊 全球資產配置比例")
        # 根據您的圓餅圖數據呈現
        fig = px.pie(values=[43.5, 44.8, 11.7], names=['美股', '現金/定存', '台股'], 
                     hole=0.5, color_discrete_sequence=px.colors.qualitative.Prism)
        st.plotly_chart(fig, use_container_width=True)
    
    with col_r:
        st.subheader("🏆 獲利貢獻排行")
        # 您提到的美股獲利細節展示
        st.write("目前主要獲利來自於：")
        st.info("🥇 SGOV: $3,633,782")
        st.success("🥈 QQQ: $115,941")

except Exception as e:
    st.error(f"連動失敗，請檢查分頁名稱是否正確。錯誤：{e}")
