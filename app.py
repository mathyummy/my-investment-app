import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime, date
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials

# ================= 頁面配置 =================
st.set_page_config(
    page_title="2037 退休堡壘",
    page_icon="🏰",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ================= 高級 CSS 樣式 =================
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+TC:wght@300;400;500;700&display=swap');
    
    html, body, [data-testid="stAppViewContainer"] {
        font-family: 'Noto Sans TC', sans-serif;
        background-color: #f8fafc;
    }

    /* 頂部標題美化 */
    .main-title {
        background: linear-gradient(90deg, #0f172a, #1e293b);
        padding: 2rem;
        border-radius: 0 0 2rem 2rem;
        margin: -4rem -4rem 2rem -4rem;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1);
    }
    .main-title h1 {
        color: #f1f5f9 !important;
        font-weight: 700;
        letter-spacing: 2px;
        margin: 0;
    }
    
    /* 現代化卡片設計 */
    .metric-card {
        background: white;
        padding: 1.5rem;
        border-radius: 1.25rem;
        box-shadow: 0 1px 3px 0 rgb(0 0 0 / 0.1), 0 1px 2px -1px rgb(0 0 0 / 0.1);
        border: 1px solid #e2e8f0;
        transition: transform 0.2s ease;
        margin-bottom: 1rem;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 15px -3px rgb(0 0 0 / 0.1);
    }
    .metric-label {
        color: #64748b;
        font-size: 0.875rem;
        font-weight: 500;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        color: #0f172a;
        font-size: 1.75rem;
        font-weight: 700;
    }
    
    /* 進度條容器 */
    .progress-container {
        background: #e2e8f0;
        border-radius: 999px;
        height: 12px;
        margin: 10px 0;
        overflow: hidden;
    }
    .progress-bar {
        background: linear-gradient(90deg, #3b82f6, #8b5cf6);
        height: 100%;
        border-radius: 999px;
    }

    /* 隱藏 Streamlit 預設裝飾 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Tabs 樣式優化 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: transparent;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: white;
        border-radius: 10px 10px 0 0;
        gap: 1px;
        padding-top: 10px;
        padding-bottom: 10px;
        border: 1px solid #e2e8f0;
    }
    .stTabs [aria-selected="true"] {
        background-color: #0f172a !important;
        color: white !important;
    }
</style>
""", unsafe_allow_html=True)

# ================= Google Sheets 連線 =================
@st.cache_resource
def get_spreadsheet():
    try:
        credentials_dict = {k: st.secrets["gsheets"][k] for k in st.secrets["gsheets"]}
        scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        return client.open_by_key(st.secrets["gsheets"]["spreadsheet"])
    except Exception as e:
        st.error(f"連線失敗: {e}")
        return None

spreadsheet = get_spreadsheet()

# ================= 核心計算與邏輯 =================
@st.cache_data(ttl=300)
def load_all_data():
    try:
        us = pd.DataFrame(spreadsheet.worksheet("US_Stocks").get_all_records())
        tw = pd.DataFrame(spreadsheet.worksheet("TW_Stocks").get_all_records())
        cash = pd.DataFrame(spreadsheet.worksheet("Bank_Cash").get_all_records())
        return us, tw, cash
    except:
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=600)
def get_price(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        return data['Close'].iloc[-1] if not data.empty else 0
    except: return 0

@st.cache_data(ttl=600)
def get_exchange_rate():
    """抓取即時美金兌台幣匯率"""
    try:
        ticker = "USDTWD=X"
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return 31.4 # 抓取失敗時的預設值
    except:
        return 31.4 # 異常時的預設值

def update_db(sheet_name, df):
    try:
        ws = spreadsheet.worksheet(sheet_name)
        ws.clear()
        ws.update([df.columns.values.tolist()] + df.values.tolist())
        return True
    except: return False

# ================= 數據處理 =================
if spreadsheet:
    us_df, tw_df, cash_df = load_all_data()
    
    # 獲取動態匯率
    USD_TWD = get_exchange_rate()

    # 計算美股
    us_df['Price'] = us_df['Ticker'].apply(get_price)
    us_df['MV_USD'] = us_df['Price'] * us_df['Qty']
    us_df['MV_TWD'] = us_df['MV_USD'] * USD_TWD
    us_df['Profit_TWD'] = (us_df['Price'] - us_df['Cost']) * us_df['Qty'] * USD_TWD
    
    # 計算台股
    tw_df['Price'] = tw_df['Ticker'].apply(get_price)
    tw_df['MV_TWD'] = tw_df['Price'] * tw_df['Qty']
    tw_df['Profit_TWD'] = (tw_df['Price'] - tw_df['Cost']) * tw_df['Qty']

    # 計算現金
    cash_total_twd = 0
    for _, r in cash_df.iterrows():
        rate = USD_TWD if r['Currency'] == 'USD' else 1
        cash_total_twd += r['Amount'] * rate

    total_assets = us_df['MV_TWD'].sum() + tw_df['MV_TWD'].sum() + cash_total_twd
    target = 50_000_000
    achieve_rate = min(total_assets / target, 1.0)
    days_to_2037 = (date(2037, 12, 31) - date.today()).days

    # ================= UI 渲染 =================
    st.markdown(f"""
        <div class="main-title">
            <h1>🏰 2037 退休資產堡壘</h1>
            <p style="color: #94a3b8; margin-top: 8px;">掌握每一分資產的跳動</p>
        </div>
    """, unsafe_allow_html=True)

    # 頂部四大指標
    col1, col2, col3, col4 = st.columns([1,1,1,1])
    with col1:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">💰 總資產淨值</div><div class="metric-value">NT$ {total_assets/1e6:.2f}M</div></div>""", unsafe_allow_html=True)
    with col2:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">🎯 目標達成率</div><div class="metric-value">{achieve_rate*100:.1f}%</div><div class="progress-container"><div class="progress-bar" style="width: {achieve_rate*100}%"></div></div></div>""", unsafe_allow_html=True)
    with col3:
        st.markdown(f"""<div class="metric-card"><div class="metric-label">⏳ 退休倒計時</div><div class="metric-value">{days_to_2037:,} <span style="font-size: 1rem;">天</span></div></div>""", unsafe_allow_html=True)
    with col4:
        total_profit = us_df['Profit_TWD'].sum() + tw_df['Profit_TWD'].sum()
        color = "#10b981" if total_profit > 0 else "#ef4444"
        st.markdown(f"""<div class="metric-card"><div class="metric-label">📈 累計預估損益</div><div class="metric-value" style="color: {color}">NT$ {total_profit/1e4:.0f}W</div></div>""", unsafe_allow_html=True)

    # 主內容 Tab 分區
    tab_summary, tab_us, tab_tw, tab_cash = st.tabs(["📊 資產總覽", "🇺🇸 美股配置", "🇹🇼 台股配置", "🏦 現金管理"])

    with tab_summary:
        c1, c2 = st.columns(2)
        with c1:
            pie_df = pd.DataFrame({
                'Category': ['美股', '台股', '現金'],
                'Value': [us_df['MV_TWD'].sum(), tw_df['MV_TWD'].sum(), cash_total_twd]
            })
            fig = px.pie(pie_df, values='Value', names='Category', hole=.6, title="資產比例分佈",
                         color_discrete_sequence=['#1e293b', '#3b82f6', '#94a3b8'])
            fig.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=350, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with c2:
            rank_df = pd.concat([
                us_df[['Ticker', 'Profit_TWD']].rename(columns={'Ticker': 'Name'}),
                tw_df[['Name', 'Profit_TWD']]
            ]).sort_values('Profit_TWD', ascending=False).head(8)
            fig_bar = px.bar(rank_df, x='Profit_TWD', y='Name', orientation='h', title="獲利貢獻排行",
                             color='Profit_TWD', color_continuous_scale='RdYlGn')
            fig_bar.update_layout(margin=dict(t=40, b=0, l=0, r=0), height=350)
            st.plotly_chart(fig_bar, use_container_width=True)

    with tab_us:
        st.subheader("美股持倉編輯")
        us_edit = st.data_editor(us_df[['Ticker', 'Type', 'Qty', 'Cost', 'Currency']], 
                                 num_rows="dynamic", use_container_width=True, key="ed_us")
        if st.button("💾 更新美股資料"):
            if update_db("US_Stocks", us_edit):
                st.success("更新成功！")
                st.rerun()
        
        st.markdown("---")
        st.write("🔍 **即時估值詳情**")
        st.dataframe(us_df[['Ticker', 'Qty', 'Cost', 'Price', 'MV_USD', 'Profit_TWD']].style.format({
            'Cost': '{:.2f}', 'Price': '{:.2f}', 'MV_USD': '{:,.0f}', 'Profit_TWD': '{:,.0f}'
        }), use_container_width=True)

    with tab_tw:
        st.subheader("台股持倉編輯")
        tw_edit = st.data_editor(tw_df[['Ticker', 'Name', 'Qty', 'Cost']], 
                                 num_rows="dynamic", use_container_width=True, key="ed_tw")
        if st.button("💾 更新台股資料"):
            if update_db("TW_Stocks", tw_edit):
                st.success("更新成功！")
                st.rerun()

        st.markdown("---")
        st.write("🔍 **即時估值詳情**")
        st.dataframe(tw_df[['Name', 'Qty', 'Cost', 'Price', 'MV_TWD', 'Profit_TWD']].style.format({
            'Cost': '{:.2f}', 'Price': '{:.2f}', 'MV_TWD': '{:,.0f}', 'Profit_TWD': '{:,.0f}'
        }), use_container_width=True)

    with tab_cash:
        st.subheader("現金與定存編輯")
        cash_edit = st.data_editor(cash_df[['Ticker', 'Amount', 'Currency', 'Type']], 
                                   num_rows="dynamic", use_container_width=True, key="ed_cash")
        if st.button("💾 更新現金資料"):
            if update_db("Bank_Cash", cash_edit):
                st.success("更新成功！")
                st.rerun()

    # 頁腳
    st.markdown(f"""
        <div style="text-align: center; color: #94a3b8; font-size: 0.8rem; margin-top: 3rem; padding: 1rem;">
            最後更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | 即時匯率 (USD/TWD): {USD_TWD:.2f}
        </div>
    """, unsafe_allow_html=True)

else:
    st.warning("⚠️ 請確認 .streamlit/secrets.toml 設定正確。")
