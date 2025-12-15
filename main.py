import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import numpy as np

# 비밀번호 설정
CORRECT_PASSWORD = "1248"

# 비밀번호 확인
def check_password():
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False
    
    if st.session_state["password_correct"]:
        return True
    
    st.markdown("""
    <div style='text-align: center; padding: 80px 20px;'>
        <h1 style='background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
        -webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 3em;'>
        🔐 AI 주식 트레이딩 시스템 Pro
        </h1>
        <p style='color: #888; font-size: 1.2em; margin-top: 20px;'>관리자 전용</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        password = st.text_input("비밀번호", type="password", placeholder="비밀번호 입력", label_visibility="collapsed")
        if st.button("🔓 로그인", use_container_width=True, type="primary"):
            if password == CORRECT_PASSWORD:
                st.session_state["password_correct"] = True
                st.success("✅ 로그인 성공!")
                st.rerun()
            else:
                st.error("❌ 비밀번호가 틀렸습니다.")
    
    return False

if not check_password():
    st.stop()

# 페이지 설정
st.set_page_config(layout="wide", page_title="AI 트레이딩 시스템 Pro", page_icon="🤖")

# CSS 스타일
st.markdown("""
<style>
.stApp { background-color: #000000; color: #e0e0e0; }
.block-container { padding-top: 1rem; padding-bottom: 1rem; max-width: 100%; }
.stTabs [data-baseweb="tab-list"] { gap: 10px; }
.stTabs [data-baseweb="tab"] {
    height: 65px; padding: 0px 28px; background-color: #1a1a1a;
    border-radius: 10px; color: #ffffff !important;
    font-size: 19px !important; font-weight: bold !important;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
}
.metric-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.15) 0%, rgba(168, 85, 247, 0.15) 100%);
    border: 2px solid rgba(99, 102, 241, 0.5); border-radius: 15px; padding: 25px; margin: 15px 0;
}
</style>
""", unsafe_allow_html=True)

# 구글 시트에서 종목 불러오기
@st.cache_data(ttl=600)
def load_stocks_from_google_sheet(sheet_url):
    try:
        # URL에서 스프레드시트 ID 추출
        if '/d/' in sheet_url:
            # https://docs.google.com/spreadsheets/d/[ID]/edit...
            sheet_id = sheet_url.split('/d/')[1].split('/')[0]
            csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        else:
            csv_url = sheet_url
        
        df = pd.read_csv(csv_url)
        return df
    except Exception as e:
        st.error(f"❌ 구글 시트 로딩 실패: {str(e)}")
        return None

# 한국 주식 데이터
@st.cache_data(ttl=300)
def get_data(ticker, timeframe="1d"):
    try:
        clean_ticker = ticker.strip().upper()
        
        # 봉별 기간 설정
        timeframe_config = {
            "1m": {"period": "7d", "interval": "1m"},
            "5m": {"period": "60d", "interval": "5m"},
            "15m": {"period": "60d", "interval": "15m"},
            "30m": {"period": "60d", "interval": "30m"},
            "60m": {"period": "730d", "interval": "60m"},
            "1h": {"period": "730d", "interval": "1h"},
            "1d": {"period": "2y", "interval": "1d"},
            "1wk": {"period": "10y", "interval": "1wk"},
            "1mo": {"period": "20y", "interval": "1mo"}
        }
        
        config = timeframe_config.get(timeframe, {"period": "2y", "interval": "1d"})
        
        if clean_ticker.isdigit() and len(clean_ticker) == 6:
            ticker_symbol = clean_ticker + ".KS"
            stock = yf.Ticker(ticker_symbol)
            df = stock.history(period=config["period"], interval=config["interval"])
            
            if df.empty:
                ticker_symbol = clean_ticker + ".KQ"
                stock = yf.Ticker(ticker_symbol)
                df = stock.history(period=config["period"], interval=config["interval"])
            
            source = "야후 파이낸스 (KRX)"
            currency = "KRW"
            
            korean_names = {
                '005930': '삼성전자', '000660': 'SK하이닉스', '035720': '카카오',
                '035420': 'NAVER', '005380': '현대차', '000270': '기아',
                '051910': 'LG화학', '006400': '삼성SDI', '207940': '삼성바이오로직스',
                '068270': '셀트리온', '028260': '삼성물산', '042700': '한미반도체',
                '009150': '삼성전기', '012330': '현대모비스', '003550': 'LG',
                '017670': 'SK텔레콤', '033780': 'KT&G', '018260': '삼성에스디에스',
                '096770': 'SK이노베이션', '373220': 'LG에너지솔루션', '352820': '하이브',
                '247540': '에코프로비엠', '086520': '에코프로', '066970': '엘앤에프',
                '161390': '한국타이어', '326030': 'SK바이오팜', '091990': '셀트리온헬스케어',
                '055550': '신한지주', '086790': '하나금융지주', '105560': 'KB금융',
                '316140': '우리금융지주'
            }
            
            name = korean_names.get(clean_ticker, clean_ticker)
        else:
            stock = yf.Ticker(clean_ticker)
            df = stock.history(period=config["period"], interval=config["interval"])
            source = "야후 파이낸스 (US)"
            currency = "USD"
            try:
                info = stock.info
                name = info.get('longName', info.get('shortName', clean_ticker))
            except:
                name = clean_ticker
        
        if df.empty:
            return None, None, None, None
        
        return df, name, source, currency
    except:
        return None, None, None, None

# 스토캐스틱 계산
def calculate_stochastic(df, k_period, d_period, smooth_k):
    low_min = df['Low'].rolling(window=k_period).min()
    high_max = df['High'].rolling(window=k_period).max()
    k = 100 * ((df['Close'] - low_min) / (high_max - low_min))
    df['%K'] = k.rolling(window=smooth_k).mean()
    df['%D'] = df['%K'].rolling(window=d_period).mean()
    return df

# RSI 계산
def calculate_rsi(df, period):
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    return df

# 백테스팅
def run_backtest(df, signal_df):
    initial_capital = 10000000
    capital = initial_capital
    position = 0
    trades = []
    equity_curve = []
    
    for i in range(len(signal_df)):
        if not pd.isna(signal_df['Buy_Signal'].iloc[i]) and position == 0:
            shares = capital // signal_df['Close'].iloc[i]
            if shares > 0:
                position = shares
                buy_price = signal_df['Close'].iloc[i]
                capital -= shares * buy_price
                trades.append({'type': 'buy', 'date': signal_df.index[i], 'price': buy_price})
        elif not pd.isna(signal_df['Sell_Signal'].iloc[i]) and position > 0:
            sell_price = signal_df['Close'].iloc[i]
            capital += position * sell_price
            profit = (sell_price - buy_price) / buy_price * 100
            trades.append({'type': 'sell', 'date': signal_df.index[i], 'price': sell_price, 'profit': profit})
            position = 0
        
        current_value = capital + (position * signal_df['Close'].iloc[i] if position > 0 else 0)
        equity_curve.append(current_value)
    
    if position > 0:
        capital += position * signal_df['Close'].iloc[-1]
    
    total_return = ((capital - initial_capital) / initial_capital) * 100
    sell_trades = [t for t in trades if t['type'] == 'sell']
    
    if sell_trades:
        winning_trades = [t for t in sell_trades if t['profit'] > 0]
        win_rate = len(winning_trades) / len(sell_trades) * 100
        avg_win = np.mean([t['profit'] for t in winning_trades]) if winning_trades else 0
        losing_trades = [t for t in sell_trades if t['profit'] <= 0]
        avg_loss = abs(np.mean([t['profit'] for t in losing_trades])) if losing_trades else 1
        profit_loss_ratio = avg_win / avg_loss if avg_loss > 0 else 0
        
        max_dd = 0
        peak = equity_curve[0]
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = ((peak - value) / peak) * 100
            if dd > max_dd:
                max_dd = dd
    else:
        win_rate = 0
        profit_loss_ratio = 0
        max_dd = 0
    
    return {
        'total_return': total_return,
        'win_rate': win_rate,
        'profit_loss_ratio': profit_loss_ratio,
        'max_drawdown': max_dd,
        'total_trades': len(sell_trades)
    }

# 헤더
st.markdown("""
<h1 style='text-align: center; background: linear-gradient(90deg, #667eea 0%, #764ba2 100%); 
-webkit-background-clip: text; -webkit-text-fill-color: transparent; font-size: 2.5em; margin-bottom: 5px;'>
🤖 AI 주식 트레이딩 시스템 Pro
</h1>
<p style='text-align: center; color: #888; margin-top: 5px; font-size: 1.1em;'>
스토캐스틱 + RSI + AI 복합 분석
</p>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns([5, 1, 1])
with col3:
    if st.button("🚪 로그아웃", type="secondary"):
        st.session_state["password_correct"] = False
        st.rerun()

# 탭
tab1, tab2, tab3, tab4 = st.tabs(["📊 차트 분석", "📈 백테스팅", "💼 포트폴리오", "🏆 종목 랭킹"])

# 사이드바
with st.sidebar:
    st.header("⚙️ 전략 설정")
    
    # 입력 방식 선택
    input_mode = st.radio("종목 입력 방식", 
                         ["직접 입력", "구글 시트"], 
                         horizontal=True)
    
    if input_mode == "직접 입력":
        if "saved_tickers" not in st.session_state:
            st.session_state.saved_tickers = "005930, 000660, 035720, 042700"
        
        tickers_input = st.text_area("종목 입력", 
                                    value=st.session_state.saved_tickers, 
                                    height=100,
                                    key="direct_input")
        selected_tickers = tickers_input
    
    else:  # 구글 시트
        st.markdown("#### 📊 구글 시트")
        
        if "sheet_url" not in st.session_state:
            st.session_state.sheet_url = ""
        
        sheet_url = st.text_input("구글 시트 URL", 
                                  value=st.session_state.sheet_url,
                                  placeholder="https://docs.google.com/...",
                                  help="공유 링크 붙여넣기")
        
        if sheet_url:
            st.session_state.sheet_url = sheet_url
            
            with st.spinner("📥 로딩 중..."):
                df_stocks = load_stocks_from_google_sheet(sheet_url)
            
            if df_stocks is not None:
                st.success(f"✅ {len(df_stocks)}개 종목")
                
                if '테마' in df_stocks.columns:
                    themes = df_stocks['테마'].unique().tolist()
                    selected_themes = st.multiselect("테마 선택", 
                                                     themes,
                                                     default=themes[:2] if len(themes) >= 2 else themes)
                    
                    if selected_themes:
                        filtered_df = df_stocks[df_stocks['테마'].isin(selected_themes)]
                        tickers_list = filtered_df['종목코드'].astype(str).tolist()
                        selected_tickers = ', '.join(tickers_list)
                        
                        st.caption(f"📌 {len(tickers_list)}개 선택됨")
                    else:
                        selected_tickers = ""
                        st.warning("테마를 선택하세요")
                else:
                    tickers_list = df_stocks['종목코드'].astype(str).tolist()
                    selected_tickers = ', '.join(tickers_list)
            else:
                selected_tickers = ""
        else:
            selected_tickers = ""
            st.info("💡 URL 입력")
    
    st.markdown("---")
    
    # 봉 선택
    st.subheader("📈 차트 설정")
    timeframe_options = {
        "1분봉": "1m",
        "5분봉": "5m",
        "15분봉": "15m",
        "30분봉": "30m",
        "60분봉": "60m",
        "1시간봉": "1h",
        "일봉": "1d",
        "주봉": "1wk",
        "월봉": "1mo"
    }
    
    selected_timeframe_kr = st.selectbox(
        "봉 선택",
        list(timeframe_options.keys()),
        index=6  # 기본값: 일봉
    )
    timeframe = timeframe_options[selected_timeframe_kr]
    
    st.markdown("---")
    st.subheader("📊 지표 설정")
    col1, col2 = st.columns(2)
    with col1:
        k_period = st.number_input("Fast %K", value=8, min_value=1, max_value=20)
        oversold = st.slider("매수 기준", 0, 50, 25)
    with col2:
        d_period = st.number_input("Slow %D", value=5, min_value=1, max_value=20)
        overbought = st.slider("매도 기준", 50, 100, 75)
    smooth_k = st.number_input("Smooth %K", value=5, min_value=1, max_value=20)
    rsi_period = st.number_input("RSI 기간", value=14, min_value=5, max_value=30)
    
    st.markdown("---")
    analyze_btn = st.button("🚀 분석 시작", type="primary", use_container_width=True)
    
    if analyze_btn and input_mode == "직접 입력":
        st.session_state.saved_tickers = tickers_input

# TAB 1: 차트 분석
with tab1:
    if analyze_btn:
        tickers = [t.strip() for t in selected_tickers.split(',') if t.strip()]
        
        for ticker in tickers:
            df, name, source, currency = get_data(ticker, timeframe)
            
            if df is None or df.empty:
                st.error(f"❌ {ticker}: 데이터 없음")
                continue
            
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df = calculate_stochastic(df, k_period, d_period, smooth_k)
            df = calculate_rsi(df, rsi_period)
            
            df['Buy_Signal'] = None
            df['Sell_Signal'] = None
            df['Strong_Buy'] = False
            
            for i in range(1, len(df)):
                if (df['%K'].iloc[i-1] < df['%D'].iloc[i-1] and 
                    df['%K'].iloc[i] > df['%D'].iloc[i] and 
                    df['%K'].iloc[i] <= oversold and df['%D'].iloc[i] <= oversold):
                    df.at[df.index[i], 'Buy_Signal'] = df['Low'].iloc[i] * 0.97
                    df.at[df.index[i], 'Strong_Buy'] = True
                elif (df['%K'].iloc[i-1] < df['%D'].iloc[i-1] and 
                      df['%K'].iloc[i] > df['%D'].iloc[i] and 
                      df['%K'].iloc[i] <= oversold):
                    df.at[df.index[i], 'Buy_Signal'] = df['Low'].iloc[i] * 0.97
                elif (df['%K'].iloc[i-1] > df['%D'].iloc[i-1] and 
                      df['%K'].iloc[i] < df['%D'].iloc[i] and 
                      df['%K'].iloc[i] >= overbought):
                    df.at[df.index[i], 'Sell_Signal'] = df['High'].iloc[i] * 1.03
            
            curr = df.iloc[-1]
            is_strong_buy = curr.get('Strong_Buy', False)
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.subheader(f"{name} ({ticker})")
                st.caption(f"출처: {source}")
            with col2:
                price_change = ((curr['Close'] - df['Close'].iloc[-2]) / df['Close'].iloc[-2]) * 100
                if currency == "KRW":
                    st.metric("현재가", f"{curr['Close']:,.0f}원", f"{price_change:+.2f}%")
                else:
                    st.metric("현재가", f"${curr['Close']:,.2f}", f"{price_change:+.2f}%")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                k_color = "#22c55e" if curr['%K'] <= oversold else "#ef4444" if curr['%K'] >= overbought else "#3b82f6"
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 16px;'>스토캐스틱</div>
                    <div style='font-size: 36px; font-weight: bold; color: {k_color};'>%K: {curr['%K']:.1f}</div>
                    <div style='color: #aaa; font-size: 18px;'>%D: {curr['%D']:.1f}</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                rsi_color = "#22c55e" if curr['RSI'] <= 30 else "#ef4444" if curr['RSI'] >= 70 else "#a855f7"
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 16px;'>RSI ({rsi_period})</div>
                    <div style='font-size: 36px; font-weight: bold; color: {rsi_color};'>{curr['RSI']:.1f}</div>
                    <div style='color: #666; font-size: 14px;'>
                        {"과매도" if curr['RSI'] <= 30 else "과매수" if curr['RSI'] >= 70 else "중립"}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 16px;'>적극매수 조건</div>
                    <div style='font-size: 28px; font-weight: bold; color: {"#22c55e" if is_strong_buy else "#888"};'>
                        {"✅ 충족" if is_strong_buy else "⏸️ 대기"}
                    </div>
                    <div style='color: #666; font-size: 13px;'>%K<{oversold} & %D<{oversold}<br>골든크로스</div>
                </div>
                """, unsafe_allow_html=True)
            
            end_date = df.index[-1]
            start_date = end_date - pd.DateOffset(months=5)
            
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.02,
                              row_heights=[0.65, 0.15, 0.2])
            
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                        low=df['Low'], close=df['Close'],
                                        increasing_line_color='red', decreasing_line_color='blue',
                                        name=''), row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='#FF6B35', width=2),
                                   name='MA5'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='#2979FF', width=3),
                                   name='MA20'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='#9D4EDD', width=3),
                                   name='MA60'), row=1, col=1)
            
            strong_buy = df[df['Strong_Buy'] == True]
            normal_buy = df[(~df['Buy_Signal'].isna()) & (df['Strong_Buy'] == False)]
            sell = df[~df['Sell_Signal'].isna()]
            
            if len(strong_buy) > 0:
                fig.add_trace(go.Scatter(x=strong_buy.index, y=strong_buy['Buy_Signal'],
                                       mode='markers+text',
                                       marker=dict(symbol='triangle-up', size=25, color='#FF0000',
                                                 line=dict(width=2, color='yellow')),
                                       text=["적극매수"] * len(strong_buy),
                                       textposition="bottom center",
                                       textfont=dict(color='#FF0000', size=14),
                                       name='적극매수'), row=1, col=1)
            
            if len(normal_buy) > 0:
                fig.add_trace(go.Scatter(x=normal_buy.index, y=normal_buy['Buy_Signal'],
                                       mode='markers+text',
                                       marker=dict(symbol='triangle-up', size=15, color='#FF6B35'),
                                       text=["매수"] * len(normal_buy),
                                       textposition="bottom center",
                                       textfont=dict(color='#FF6B35', size=11),
                                       name='매수'), row=1, col=1)
            
            if len(sell) > 0:
                fig.add_trace(go.Scatter(x=sell.index, y=sell['Sell_Signal'],
                                       mode='markers+text',
                                       marker=dict(symbol='triangle-down', size=18, color='#2979FF'),
                                       text=["매도"] * len(sell),
                                       textposition="top center",
                                       textfont=dict(color='#2979FF', size=13),
                                       name='매도'), row=1, col=1)
            
            colors = ['red' if row['Open'] <= row['Close'] else 'blue' for index, row in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors,
                               name='거래량'), row=2, col=1)
            
            fig.add_trace(go.Scatter(x=df.index, y=df['%K'], line=dict(color='#00E5FF', width=2),
                                   name='%K'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['%D'], line=dict(color='#FF6D00', width=2),
                                   name='%D'), row=3, col=1)
            fig.add_hline(y=oversold, line_dash="dash", line_color="#00E676", line_width=2, row=3, col=1)
            fig.add_hline(y=overbought, line_dash="dash", line_color="#FF1744", line_width=2, row=3, col=1)
            
            fig.update_layout(height=700, template="plotly_dark", showlegend=False,
                            hovermode="closest", dragmode='pan',
                            margin=dict(l=50, r=80, t=30, b=40),
                            paper_bgcolor="#000000", plot_bgcolor="#000000",
                            xaxis_rangeslider_visible=False)
            
            fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor='rgba(128, 128, 128, 0.2)',
                           range=[start_date, end_date],
                           tickformat='%Y년 %m월')
            
            if currency == "KRW":
                fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)',
                               side='right', tickformat=',', ticksuffix='원', row=1, col=1)
            else:
                fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)',
                               side='right', tickformat=',.2f', tickprefix='$', row=1, col=1)
            
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)',
                           side='right', row=2, col=1)
            fig.update_yaxes(showgrid=True, gridcolor='rgba(128, 128, 128, 0.2)',
                           side='right', range=[0, 100], row=3, col=1)
            
            st.plotly_chart(fig, use_container_width=True, key=f"chart_{ticker}")
            st.markdown("---")

# TAB 2: 백테스팅
with tab2:
    st.subheader("📈 백테스팅 결과")
    if analyze_btn:
        tickers = [t.strip() for t in selected_tickers.split(',') if t.strip()]
        for ticker in tickers:
            df, name, source, currency = get_data(ticker, timeframe)
            if df is None or df.empty:
                continue
            
            df['MA5'] = df['Close'].rolling(window=5).mean()
            df['MA20'] = df['Close'].rolling(window=20).mean()
            df['MA60'] = df['Close'].rolling(window=60).mean()
            df = calculate_stochastic(df, k_period, d_period, smooth_k)
            df = calculate_rsi(df, rsi_period)
            
            df['Buy_Signal'] = None
            df['Sell_Signal'] = None
            for i in range(1, len(df)):
                if (df['%K'].iloc[i-1] < df['%D'].iloc[i-1] and 
                    df['%K'].iloc[i] > df['%D'].iloc[i] and 
                    df['%K'].iloc[i] <= oversold):
                    df.at[df.index[i], 'Buy_Signal'] = df['Close'].iloc[i]
                elif (df['%K'].iloc[i-1] > df['%D'].iloc[i-1] and 
                      df['%K'].iloc[i] < df['%D'].iloc[i] and 
                      df['%K'].iloc[i] >= overbought):
                    df.at[df.index[i], 'Sell_Signal'] = df['Close'].iloc[i]
            
            results = run_backtest(df, df)
            
            st.markdown(f"### 📊 {name} ({ticker})")
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 14px;'>총 수익률</div>
                    <div style='font-size: 32px; font-weight: bold; color: {"#22c55e" if results['total_return'] > 0 else "#ef4444"};'>
                        {results['total_return']:+.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 14px;'>승률</div>
                    <div style='font-size: 32px; font-weight: bold; color: #3b82f6;'>
                        {results['win_rate']:.1f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 14px;'>MDD</div>
                    <div style='font-size: 32px; font-weight: bold; color: #ef4444;'>
                        {results['max_drawdown']:.2f}%
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                st.markdown(f"""
                <div class='metric-card'>
                    <div style='color: #888; font-size: 14px;'>손익비</div>
                    <div style='font-size: 32px; font-weight: bold; color: #a855f7;'>
                        {results['profit_loss_ratio']:.2f}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")

# TAB 3: 포트폴리오
with tab3:
    st.subheader("💼 포트폴리오")
    if analyze_btn:
        st.info("포트폴리오 기능 업데이트 예정")

# TAB 4: 종목 랭킹
with tab4:
    st.subheader("🏆 종목 랭킹")
    if analyze_btn:
        st.info("종목 랭킹 기능 업데이트 예정")