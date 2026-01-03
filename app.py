import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go

# 頁面配置
st.set_page_config(
    page_title="2037 退休資產堡壘",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 樣式注入
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    
    * {
        font-family: 'Noto Sans TC', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
    }
    
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.2);
        color: white;
        text-align: center;
        margin: 10px 0;
    }
    
    .metric-card h3 {
        font-size: 16px;
        font-weight: 400;
        margin: 0;
        opacity: 0.9;
    }
    
    .metric-card h1 {
        font-size: 36px;
        font-weight: 700;
        margin: 10px 0;
        color: #ffd700;
    }
    
    .metric-card p {
        font-size: 14px;
        margin: 5px 0 0 0;
        opacity: 0.8;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
        color: #1e3c72;
    }
    
    .section-header {
        background: linear-gradient(90deg, #1e3c72, #2a5298);
        color: white;
        padding: 15px 20px;
        border-radius: 10px;
        margin: 20px 0 10px 0;
        font-size: 20px;
        font-weight: 600;
    }
    
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 10px 24px;
        font-weight: 600;
        transition: all 0.3s;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# 標題
st.markdown("<h1 style='text-align: center; color: #1e3c72; margin-bottom: 30px;'>🏰 2037 退休資產堡壘</h1>", unsafe_allow_html=True)

# 連接 Google Sheets
@st.cache_resource
def get_connection():
    try:
        # 檢查 secrets 配置
        if "gsheets" not in st.secrets:
            raise Exception("❌ 找不到 [gsheets] 設定區塊，請檢查 Secrets 設定")
        
        gsheets_config = st.secrets["gsheets"]
        
        # 檢查必要參數
        if "spreadsheet" not in gsheets_config:
            raise Exception("❌ secrets 中缺少 spreadsheet 參數")
        
        if not gsheets_config["spreadsheet"] or gsheets_config["spreadsheet"].strip() == "":
            raise Exception("❌ spreadsheet 參數為空")
        
        # 顯示連線資訊（除錯用）
        st.info(f"🔗 正在連線到 Sheet ID: {gsheets_config['spreadsheet'][:20]}...")
        
        # 建立連線（不傳入 spreadsheet 參數，讓它從 secrets 自動讀取）
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        return conn
        
    except Exception as e:
        st.error(f"⚠️ Google Sheets 連線失敗：{str(e)}")
        with st.expander("🔍 詳細錯誤資訊", expanded=True):
            st.code(str(e))
        return None

conn = get_connection()

# 讀取數據
@st.cache_data(ttl=300)
def load_data():
    if conn is None:
        raise Exception("無法建立 Google Sheets 連線，請檢查 Secrets 設定")
    
    us_stocks = conn.read(worksheet="US_Stocks", ttl=0)
    tw_stocks = conn.read(worksheet="TW_Stocks", ttl=0)
    bank_cash = conn.read(worksheet="Bank_Cash", ttl=0)
    return us_stocks, tw_stocks, bank_cash

# 獲取即時股價
@st.cache_data(ttl=300)
def get_stock_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        data = stock.history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except:
        return None

# 匯率設定
USD_TO_TWD = 31.36

# 載入數據
try:
    us_stocks_df, tw_stocks_df, bank_cash_df = load_data()
    
    # 計算美股市值
    us_total = 0
    us_stocks_df['Current_Price'] = 0.0
    us_stocks_df['Market_Value_USD'] = 0.0
    us_stocks_df['Market_Value_TWD'] = 0.0
    us_stocks_df['Profit_Loss'] = 0.0
    
    for idx, row in us_stocks_df.iterrows():
        price = get_stock_price(row['Ticker'])
        if price:
            us_stocks_df.at[idx, 'Current_Price'] = price
            mv_usd = price * row['Qty']
            us_stocks_df.at[idx, 'Market_Value_USD'] = mv_usd
            mv_twd = mv_usd * USD_TO_TWD
            us_stocks_df.at[idx, 'Market_Value_TWD'] = mv_twd
            us_stocks_df.at[idx, 'Profit_Loss'] = mv_usd - (row['Cost'] * row['Qty'])
            us_total += mv_twd
    
    # 計算台股市值
    tw_total = 0
    tw_stocks_df['Current_Price'] = 0.0
    tw_stocks_df['Market_Value'] = 0.0
    tw_stocks_df['Profit_Loss'] = 0.0
    
    for idx, row in tw_stocks_df.iterrows():
        price = get_stock_price(row['Ticker'])
        if price:
            tw_stocks_df.at[idx, 'Current_Price'] = price
            mv = price * row['Qty']
            tw_stocks_df.at[idx, 'Market_Value'] = mv
            tw_stocks_df.at[idx, 'Profit_Loss'] = mv - (row['Cost'] * row['Qty'])
            tw_total += mv
    
    # 計算現金
    cash_total = 0
    for _, row in bank_cash_df.iterrows():
        if row['Currency'] == 'USD':
            cash_total += row['Amount'] * USD_TO_TWD
        else:
            cash_total += row['Amount']
    
    # 總資產
    total_assets = us_total + tw_total + cash_total
    stock_total = us_total + tw_total
    
    # 退休計算
    target_year = 2037
    target_amount = 50_000_000
    current_year = datetime.now().year
    days_left = (date(target_year, 12, 31) - date.today()).days
    achievement_rate = (total_assets / target_amount) * 100
    
    # 核心指標卡片
    st.markdown("<div style='margin: 20px 0;'>", unsafe_allow_html=True)
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>💰 總資產淨值</h3>
            <h1>NT$ {total_assets:,.0f}</h1>
            <p>即時市值計算</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>📈 股票總市值</h3>
            <h1>NT$ {stock_total:,.0f}</h1>
            <p>美股 + 台股</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class='metric-card'>
            <h3>⏰ 退休倒數</h3>
            <h1>{days_left}</h1>
            <p>天 ({target_year - current_year} 年)</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        color = "#00ff00" if achievement_rate >= 100 else "#ffd700"
        st.markdown(f"""
        <div class='metric-card'>
            <h3>🎯 目標達成率</h3>
            <h1 style='color: {color};'>{achievement_rate:.1f}%</h1>
            <p>目標 NT$ 50M</p>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    # 視覺化分析
    st.markdown("<div class='section-header'>📊 資產配置分析</div>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        # 資產比例圓餅圖
        asset_data = pd.DataFrame({
            '類別': ['美股', '台股', '現金'],
            '金額': [us_total, tw_total, cash_total]
        })
        
        fig_pie = px.pie(
            asset_data, 
            values='金額', 
            names='類別',
            title='資產配置比例',
            color_discrete_sequence=['#667eea', '#764ba2', '#f093fb']
        )
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        fig_pie.update_layout(
            font=dict(family="Noto Sans TC", size=14),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)'
        )
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # 獲利貢獻排行
        profit_data = []
        for _, row in us_stocks_df.iterrows():
            if row['Profit_Loss'] != 0:
                profit_data.append({
                    '標的': row['Ticker'],
                    '損益': row['Profit_Loss'] * USD_TO_TWD
                })
        
        for _, row in tw_stocks_df.iterrows():
            if row['Profit_Loss'] != 0:
                profit_data.append({
                    '標的': row['Name'],
                    '損益': row['Profit_Loss']
                })
        
        profit_df = pd.DataFrame(profit_data).sort_values('損益', ascending=True)
        
        fig_bar = px.bar(
            profit_df.tail(10),
            x='損益',
            y='標的',
            orientation='h',
            title='獲利貢獻 TOP 10',
            color='損益',
            color_continuous_scale=['#ff6b6b', '#ffd700', '#51cf66']
        )
        fig_bar.update_layout(
            font=dict(family="Noto Sans TC", size=14),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            showlegend=False
        )
        st.plotly_chart(fig_bar, use_container_width=True)
    
    # 互動式資料表格
    st.markdown("<div class='section-header'>🇺🇸 美股持倉 (可編輯)</div>", unsafe_allow_html=True)
    edited_us = st.data_editor(
        us_stocks_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Current_Price": st.column_config.NumberColumn("即時股價", format="$%.2f"),
            "Market_Value_USD": st.column_config.NumberColumn("市值(美金)", format="$%.2f"),
            "Market_Value_TWD": st.column_config.NumberColumn("市值(台幣)", format="NT$%.0f"),
            "Profit_Loss": st.column_config.NumberColumn("損益(美金)", format="$%.2f"),
        }
    )
    
    if st.button("💾 儲存美股數據", key="save_us"):
        conn.update(worksheet="US_Stocks", data=edited_us)
        st.success("✅ 美股數據已儲存至 Google Sheets！")
        st.cache_data.clear()
    
    st.markdown("<div class='section-header'>🇹🇼 台股持倉 (可編輯)</div>", unsafe_allow_html=True)
    edited_tw = st.data_editor(
        tw_stocks_df,
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Current_Price": st.column_config.NumberColumn("即時股價", format="NT$%.2f"),
            "Market_Value": st.column_config.NumberColumn("市值", format="NT$%.0f"),
            "Profit_Loss": st.column_config.NumberColumn("損益", format="NT$%.0f"),
        }
    )
    
    if st.button("💾 儲存台股數據", key="save_tw"):
        conn.update(worksheet="TW_Stocks", data=edited_tw)
        st.success("✅ 台股數據已儲存至 Google Sheets！")
        st.cache_data.clear()
    
    st.markdown("<div class='section-header'>🏦 銀行現金 (可編輯)</div>", unsafe_allow_html=True)
    edited_cash = st.data_editor(
        bank_cash_df,
        use_container_width=True,
        num_rows="dynamic"
    )
    
    if st.button("💾 儲存現金數據", key="save_cash"):
        conn.update(worksheet="Bank_Cash", data=edited_cash)
        st.success("✅ 現金數據已儲存至 Google Sheets！")
        st.cache_data.clear()
    
    # 頁尾
    st.markdown("---")
    st.markdown(
        "<p style='text-align: center; color: #666;'>🏰 2037 退休資產堡壘 | 資料每 5 分鐘更新 | Powered by Streamlit</p>",
        unsafe_allow_html=True
    )

except Exception as e:
    st.error(f"❌ 錯誤：{str(e)}")
    
    with st.expander("🔍 除錯資訊與設定指南", expanded=True):
        st.markdown("""
        ### 📋 Streamlit Secrets 正確格式
        
        請在 **Settings → Secrets** 使用以下格式：
        
        ```toml
        [gsheets]
        spreadsheet = "1AbCdEfGhIjKlMnOpQrStUvWxYz"
        
        type = "service_account"
        project_id = "your-project-123"
        private_key_id = "abc123..."
        private_key = "-----BEGIN PRIVATE KEY-----\\nMII...\\n-----END PRIVATE KEY-----\\n"
        client_email = "your-sa@your-project.iam.gserviceaccount.com"
        client_id = "123456"
        auth_uri = "https://accounts.google.com/o/oauth2/auth"
        token_uri = "https://oauth2.googleapis.com/token"
        auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
        client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
        universe_domain = "googleapis.com"
        ```
        
        ### ⚠️ 關鍵要點
        
        1. **區塊名稱**：必須是 `[gsheets]`（不是 `[connections.gsheets]`）
        2. **spreadsheet**：只填 Sheet ID（從 URL 的 /d/ 和 /edit 之間複製）
        3. **private_key**：記得保留 `\\n` 換行符號
        4. **universe_domain**：必須加上 `universe_domain = "googleapis.com"`（新版必要欄位）
        5. **共用權限**：必須將 `client_email` 加入 Google Sheets 共用（編輯者）
        
        ### 🔑 取得 Sheet ID
        
        開啟您的 Google Sheets，URL 格式如下：
        ```
        https://docs.google.com/spreadsheets/d/[這段就是ID]/edit
        ```
        
        例如：`1AbCdEfGhIjKlMnOpQrStUvWxYz0123456789`
        
        ### 📝 設定後動作
        
        1. 點擊 Secrets 頁面的 **Save**
        2. 回到 App 頁面
        3. 點擊右上角 ⋮ → **Reboot app**
        """)
        
        st.warning("💡 如果持續出錯，請確認 Google Cloud 已啟用 Sheets API 和 Drive API")
