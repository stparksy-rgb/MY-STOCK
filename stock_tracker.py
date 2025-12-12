import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import os
import pandas as pd 

# -----------------------------------------------------
# 1. 가격 포맷팅 및 파일 저장/불러오기 로직 (핵심 기능)
# -----------------------------------------------------

# 대한민국 시가총액 Top 6를 새로운 기본값으로 설정
DEFAULT_TICKERS = '005930.KS, 000660.KS, 373220.KS, 207940.KS, 005380.KS, 000810.KS' 
WATCHLIST_FILE = 'last_watchlist.txt' # 종목 리스트를 저장할 파일명

def format_price(price, ticker):
    """가격에 쉼표와 달러/원화 단위를 자동 구분하여 포맷합니다."""
    if price is None:
        return "N/A"
    
    # 1. 단위 결정: 미국 주식, 지수 (^GSPC, TSLA), 코인 (BTC-USD)은 $로 표시
    if ('.KS' not in ticker and '.KQ' not in ticker) or ticker in ['BTC-USD', 'ETH-USD', '^GSPC', '^IXIC', '^DJI']:
        unit = "$"
        # 달러 종목인 경우 소수점 2자리까지 표시 (가독성 기준)
        if price > 1000:
            return f'{price:,.0f}{unit}'
        else:
            return f'{price:,.2f}{unit}'
    else:
        # 한국 주식 (원화)은 정수로 표시
        unit = "원"
        return f'{int(price):,}{unit}'

def load_watchlist():
    """마지막으로 저장된 관심 종목 리스트를 파일에서 불러옵니다."""
    if os.path.exists(WATCHLIST_FILE):
        try:
            with open(WATCHLIST_FILE, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except:
            return DEFAULT_TICKERS
    else:
        return DEFAULT_TICKERS

def save_watchlist(tickers):
    """현재 관심 종목 리스트를 파일에 저장합니다."""
    with open(WATCHLIST_FILE, 'w', encoding='utf-8') as f:
        f.write(tickers)

# -----------------------------------------------------
# 2. 시스템 설정 및 CSS (다크 테마)
# -----------------------------------------------------
st.set_page_config(layout="wide", page_title="AI 주식 비서 (다크 트레이딩)")

# --- CSS 스타일링 (다크 테마 및 전문성 강화) ---
st.markdown("""
<style>
    /* 전체 배경을 어둡게 설정 (다크 모드 강제) */
    .stApp {
        background-color: #1e1e1e; /* HTS 유사 배경색 */
        color: #f0f0f0; 
    }
    /* 사이드바 배경 */
    .css-1d3w5ef {
        background-color: #2c2c2c;
    }
    /* 입력창 글자색 */
    .stTextArea, .stNumberInput {
        color: #f0f0f0;
        background-color: #383838;
        border-color: #555555;
    }
    /* 현재가 표시 (Metric) 강조 */
    [data-testid="stMetricValue"] {
        font-size: 32px;
        color: #00FF99; /* 밝은 녹색으로 현재가 강조 */
    }
    /* 매수/매도 신호 박스 디자인 - 한국 표준 (빨강/파랑) 및 크기 축소 */
    .buy-msg { 
        color: #FF0000; /* 빨간색 텍스트 (양봉색과 통일) */
        font-weight: bold; 
        font-size: 16px; /* 크기 약 70% 수준으로 축소 */
        border: 2px solid #FF0000; 
        padding: 7px; /* 패딩 축소 */
        border-radius: 8px; 
        text-align: center;
        background-color: #331111;
    }
    .sell-msg { 
        color: #1E90FF; /* 파란색 텍스트 (음봉색과 통일) */
        font-weight: bold; 
        font-size: 16px; /* 크기 약 70% 수준으로 축소 */
        border: 2px solid #1E90FF; 
        padding: 7px; /* 패딩 축소 */
        border-radius: 8px; 
        text-align: center;
        background-color: #112233; 
    }
    .neutral-msg { 
        color: #AAAAAA; 
        font-size: 16px; 
        text-align: center;
        padding: 10px;
        border: 1px solid #555555;
        border-radius: 8px;
        background-color: #333333;
    }
    /* 버튼 색상 */
    .stButton>button {
        background-color: #0066cc;
        color: white;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------
# 3. 데이터 수집 및 분석 함수
# -----------------------------------------------------
def get_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        # 240일선 계산을 위해 넉넉하게 2년치 데이터를 가져옴
        df = stock.history(period="2y", interval="1d")
        return df, stock.info
    except Exception as e:
        return None, None

def analyze_strategy(df, k_p, d_p, s_k, oversold, overbought):
    # 최소 240일 데이터가 필요함 (240일 이동평균선 때문에)
    if len(df) < 240:
        return df, [], [], False # 분석 실패 플래그 추가

    # 이동평균선 (사진과 동일하게 5, 20, 60, 240)
    df['MA5'] = ta.sma(df['Close'], length=5)
    df['MA20'] = ta.sma(df['Close'], length=20)
    df['MA60'] = ta.sma(df['Close'], length=60)
    df['MA240'] = ta.sma(df['Close'], length=240)

    # 스토캐스틱 슬로우 (8-5-5)
    stoch = ta.stoch(high=df['High'], low=df['Low'], close=df['Close'], 
                      k=k_p, d=d_p, smooth_k=s_k)
    
    k_col = [c for c in stoch.columns if c.startswith('STOCHk')][0]
    d_col = [c for c in stoch.columns if c.startswith('STOCHd')][0]
    
    df['Slow_K'] = stoch[k_col]
    df['Slow_D'] = stoch[d_col]

    # 신호 포착
    buy_signals = []
    sell_signals = []
    
    start_idx = max(240, len(df) - 250) 
    
    for i in range(start_idx, len(df)):
        curr = df.iloc[i]
        prev = df.iloc[i-1]
        
        # [매수] 25선 아래에서 골든크로스
        if prev['Slow_K'] < prev['Slow_D'] and curr['Slow_K'] > curr['Slow_D']:
            if curr['Slow_K'] <= oversold or prev['Slow_K'] <= oversold:
                buy_signals.append((df.index[i], curr['Low'] * 0.98))

        # [매도] 75선 위에서 데드크로스
        elif prev['Slow_K'] > prev['Slow_D'] and curr['Slow_K'] < curr['Slow_D']:
            if curr['Slow_K'] >= overbought or prev['Slow_K'] >= overbought:
                sell_signals.append((df.index[i], curr['High'] * 1.02))
            
    return df, buy_signals, sell_signals, True # 분석 성공

# -----------------------------------------------------
# 4. 메인 화면 출력 (Streamlit)
# -----------------------------------------------------
st.header("🛡️ 나만의 AI 트레이딩 시스템 (일봉)") 
st.markdown("요청하신 **일봉 차트(5, 20, 60, 240일선)**와 **스토캐스틱(8-5-5)**를 다크 테마로 구현했습니다.")

# 사이드바 설정
st.sidebar.header("🔧 일봉 전략 세팅")

# --- 종목 입력 부분 (입력창 확장 및 기억 기능 적용) ---
current_tickers = load_watchlist()

# ***수정된 부분: st.text_area 사용으로 입력창 확장***
ticker_symbol = st.sidebar.text_area(
    '관심종목 입력 (쉼표로 구분)',
    value=current_tickers, # <--- 저장된 6종목 또는 최근 저장값을 기본값으로 사용
    key='ticker_input',
    height=100 # 입력창 높이 설정
)

st.sidebar.info("기본값: 삼성전자, SK하이닉스 등 (총 6종목)")
# ---

st.sidebar.markdown("---")
st.sidebar.subheader("📊 스토캐스틱 (일봉 기준)")
k_period = st.sidebar.number_input("Fast %K", value=8, min_value=1)
d_period = st.sidebar.number_input("Slow %D", value=5, min_value=1)
smooth_k = st.sidebar.number_input("Slow %K", value=5, min_value=1)

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 기준선")
oversold_line = st.sidebar.slider("매수 기준 (25선)", 0, 50, 25)
overbought_line = st.sidebar.slider("매도 기준 (75선)", 50, 100, 75)

# 분석 버튼
if st.button("🚀 일봉 정밀 분석 시작", type="primary"):
    save_watchlist(ticker_symbol) # <--- 분석 시작 전, 현재 입력값을 파일에 저장 (추가)
    tickers = [t.strip() for t in ticker_symbol.split(',')]
    
    for ticker in tickers:
        df, info = get_data(ticker)
        
        if df is not None and not df.empty:
            df, buy_signals, sell_signals, analysis_success = analyze_strategy(df, k_period, d_period, smooth_k, oversold_line, overbought_line)
            
            # --- 분석 실패 (데이터 부족) 시 처리 ---
            if not analysis_success:
                name = info.get('longName', ticker)
                st.error(f"⚠️ {name} ({ticker}): **분석 불가.** 240일선 계산을 위한 **충분한 데이터(최소 240일)**가 부족합니다. 신규 상장 종목이거나 거래 정지 종목일 수 있습니다.")
                continue

            # --- 분석 성공 시 계속 진행 ---
            
            # 현재 상태 판단
            last_signal = "⏳ 관망 (타이밍 대기)"
            signal_color = "gray"
            last_time = df.index[-1]
            
            # 최근 신호 확인 (최근 3일 이내 신호만 메인 패널에 표시)
            if buy_signals and (last_time - buy_signals[-1][0]).days <= 3:
                last_signal = "🔥 매수 타이밍! (침체권 탈출)"
                signal_color = "red"
            elif sell_signals and (last_time - sell_signals[-1][0]).days <= 3:
                last_signal = "💧 매도 타이밍! (과열권 이탈)"
                signal_color = "blue"

            # 4. 화면 출력
            name = info.get('longName', ticker)
            
            price = df['Close'].iloc[-1]
            
            # 수정: 종목명 헤더 크기를 ####로 축소 유지
            st.markdown(f"#### 📈 {name} ({ticker})") 
            
            # 현재가와 매수 타이밍 박스를 한 줄에 배치하여 수직 최소화
            c1, c2 = st.columns([1, 2])
            with c1:
              st.metric("현재가 (일봉 종가)", format_price(price, ticker)) # 가격 형식 최종 적용
            with c2:
                if signal_color == "red":
                    st.markdown(f"<div class='buy-msg'>{last_signal}</div>", unsafe_allow_html=True)
                elif signal_color == "blue":
                    st.markdown(f"<div class='sell-msg'>{last_signal}</div>", unsafe_allow_html=True)
                else:
                    st.markdown(f"<div class='neutral-msg'>{last_signal}</div>", unsafe_allow_html=True)

            # --- 차트 그리기 (일봉 메인) ---
            
            # 개선점 적용: 초기 X축 범위를 최근 5개월(150일)로 설정하여 확대된 상태로 시작
            end_date = df.index[-1]
            start_date_initial = end_date - pd.Timedelta(days=150) 
            end_date_buffered = end_date + pd.Timedelta(days=5) 
            
            # 호버 모드 수정을 위해 fig 객체를 먼저 생성
            fig = make_subplots(rows=3, cols=1, shared_xaxes=True, 
                                vertical_spacing=0.03, row_heights=[0.6, 0.15, 0.25],
                                subplot_titles=("일봉 캔들 & 이평선", "거래량", "스토캐스틱 (8-5-5)"))
            
            # 1. 일봉 캔들 (한국 표준: 양봉(상승)은 빨강, 음봉(하락)은 파랑)
            fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'],
                                         low=df['Low'], close=df['Close'], name='일봉',
                                         increasing_line_color='#FF0000', increasing_fillcolor='#FF0000', # 양봉 (빨강)
                                         decreasing_line_color='#1E90FF', decreasing_fillcolor='#1E90FF'), row=1, col=1) # 음봉 (파랑)
            
            # 이동평균선 (HTS 스타일 색상)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='yellow', width=1), name='5일선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='white', width=1.5), name='20일선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='#00FF99', width=1), name='60일선'), row=1, col=1) # 밝은 녹색
            fig.add_trace(go.Scatter(x=df.index, y=df['MA240'], line=dict(color='gray', width=1), name='240일선'), row=1, col=1)

            # 매매 신호 화살표 (차트 위에 직접 표시)
            if buy_signals:
                bx, by = zip(*buy_signals)
                fig.add_trace(go.Scatter(x=bx, y=by, mode='markers+text', marker_symbol='triangle-up', 
                                         marker_color='#FF0000', marker_size=15, 
                                         text=["매수"]*len(bx), textposition="bottom center", textfont=dict(color='#FF0000', size=14),
                                         name='매수'), row=1, col=1)
            if sell_signals:
                sx, sy = zip(*sell_signals)
                fig.add_trace(go.Scatter(x=sx, y=sy, mode='markers+text', marker_symbol='triangle-down', 
                                         marker_color='#1E90FF', marker_size=15, 
                                         text=["매도"]*len(sx), textposition="top center", textfont=dict(color='#1E90FF', size=14),
                                         name='매도'), row=1, col=1)

            # 2. 거래량 (캔들 색상과 통일)
            colors = ['#FF0000' if r['Close'] >= r['Open'] else '#1E90FF' for i, r in df.iterrows()]
            fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=colors, name='거래량'), row=2, col=1)

            # 3. 스토캐스틱
            fig.add_trace(go.Scatter(x=df.index, y=df['Slow_K'], line=dict(color='orange', width=2), name='Slow K'), row=3, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['Slow_D'], line=dict(color='blue', width=1), name='Slow D'), row=3, col=1)
            fig.add_hline(y=oversold_line, line_dash="solid", line_color='rgba(0,255,0,0.5)', row=3, col=1) # 연한 녹색
            fig.add_hline(y=overbought_line, line_dash="solid", line_color='rgba(255,0,0,0.5)', row=3, col=1) # 연한 빨강

            # 레이아웃 설정 (배경색 조정)
            fig.update_layout(height=900, showlegend=False, xaxis_rangeslider_visible=False,
                              title_text=f"{name} 일봉 HTS 스타일 분석",
                              paper_bgcolor='#1e1e1e', # 전체 배경
                              plot_bgcolor='#1e1e1e', # 차트 내부 배경
                              font=dict(color='#f0f0f0'),
                              hovermode='x unified') # <-- 핵심 설정: 모든 서브플롯에 걸쳐 X축 호버를 통합

            # 최종 수정: X축 스파이크를 강제하고, Y축 스파이크는 끕니다.
            spike_style = dict(showspikes=True, spikemode="across", spikethickness=1, spikedash="dot", spikecolor="#AAAAAA")
            fig.update_xaxes(**spike_style)
            fig.update_yaxes(showspikes=False)
            
            # 초기 X축 범위 적용 (개선된 기능)
            fig.update_xaxes(range=[start_date_initial, end_date_buffered])
            
            fig.update_xaxes(rangebreaks=[dict(bounds=["sat", "mon"])])
            fig.update_xaxes(tickformat="%Y-%m-%d", row=3, col=1)
            fig.update_yaxes(gridcolor='#333333') # 격자선 색상
            
            st.plotly_chart(fig, use_container_width=True)
            
        else:
            st.error(f"❌ {ticker}: 데이터 없음. 종목 코드를 다시 확인하거나 시장이 열린 후 시도하세요.")