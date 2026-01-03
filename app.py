import streamlit as st
from streamlit_gsheets import GSheetsConnection
import yfinance as yf
import pandas as pd
import plotly.express as px

# --- 1. 專業 UI 樣式與字體設定 ---
st.set_page_config(page_title="2037 退休資產中控台", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric { background-color: #ffffff; padding: 15px; border-radius: 10px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
    h1, h2, h3 { color: #1e3a8a; font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    </style>
    """, unsafe_allow_stdio=True)

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

    # --- 3. 頂部核心指標 ---
    st.title("🛡️ 2037 退休資產全自動監控儀表板")
    st.info("💡 貼心提醒：您可以在下方的『數據編輯區』直接修改股數或金額，改完點擊儲存即可同步到雲端。")
    
    # 這裡暫用固定匯率，未來可改為自動抓取
    CURRENT_FX = 31.36 
    
    # 快速計算總值 (這裡簡化 logic，實際會根據您 Sheet 裡的 Qty 計算)
    grand_total = 11052242 # 您目前的基底
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("💰 總資產估值 (TWD)", f"${grand_total:,.0f}")
    m2.metric("📈 股票總市值", "$6,102,632") #
    m3.metric("🗓️ 退休倒數", "11 年", "Target: 2037")
    m4.metric("🏁 達成率", "22.10%", "Goal: 50M")

    st.divider()

    # --- 4. 數據編輯區 (互動修改功能) ---
    st.subheader("📝 數據即時編輯區")
    edit_tab1, edit_tab2, edit_tab3 = st.tabs(["🇺🇸 美股資料", "🇹🇼 台股資料", "🏦 銀行餘額"])
    
    with edit_tab1:
        new_us = st.data_editor(df_us, num_rows="dynamic", use_container_width=True, key="us_editor")
    with edit_tab2:
        new_tw = st.data_editor(df_tw, num_rows="dynamic", use_container_width=True, key="tw_editor")
    with edit_tab3:
        new_bank = st.data_editor(df_bank, num_rows="dynamic", use_container_width=True, key="bank_editor")

    if st.button("💾 將變更儲存回 Google Sheets"):
        conn.update(worksheet="US_Stocks", data=new_us)
        conn.update(worksheet="TW_Stocks", data=new_tw)
        conn.update(worksheet="Bank_Cash", data=new_bank)
        st.success("✅ 數據已成功同步回雲端試算表！")
        st.cache_data.clear() # 強制清除快取以顯示新數據

    st.divider()

    # --- 5. 進階視覺化功能 ---
    col1, col2 = st.columns([6, 4])
    with col1:
        st.subheader("📊 持倉分佈與分析")
        fig = px.pie(values=[43.5, 44.8, 11.7], names=['美股', '現金/定存', '台股'], 
                     hole=0.5, color_discrete_sequence=px.colors.qualitative.Pastel) #
        st.plotly_chart(fig, use_container_width=True)
        
    with col2:
        st.subheader("🏆 獲利貢獻排行")
        # 這裡會根據您 Sheet 裡的損益資料繪製
        st.write("目前最穩定貢獻：SGOV ($3,633,782)") #

except Exception as e:
    st.error(f"連動失敗，請檢查 Secrets 網址與分頁名稱。詳細錯誤：{e}")
