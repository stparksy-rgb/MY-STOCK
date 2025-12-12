import streamlit as st
import FinanceDataReader as fdr
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 페이지 설정
st.set_page_config(layout="wide", page_title="AI 주식 비서 (네이버 버전)")

# 사이드바 설정
st.sidebar.header("🛠️ 일봉 전략 세팅")
tickers_input = st.sidebar.text_area(
    "관심종목 입력 (종목코드만, 쉼표로 구분)",
    value="005930, 000660, 373220, 035420, 035720", # 삼성전자, 하이닉스, LG엔솔, NAVER, 카카오
    height=100
)

# 스토캐스틱 설정
st.sidebar.subheader("📊 스토캐스틱 설정")
k_period = st.sidebar.number_input("Fast %K", value=5)
d_period = st.sidebar.number_input("Slow %D", value=3)
overbought = st.sidebar.slider("과매수 기준", 70, 100, 80)
oversold = st.sidebar.slider("과매도 기준", 0, 30, 20)

# 메인 타이틀
st.title("🛡️ 나만의 AI 트레이딩 시스템 (Cloud Ver.)")
st.write("해외 서버에서도 잘 작동하는 **네이버 금융 기반** 차트입니다.")

if st.button("🚀 일봉 정밀 분석 시작"):
    tickers = [t.strip() for t in tickers_input.split(',') if t.strip()]
    
    for ticker in tickers:
        try:
            # .KS 같은 거 떼고 순수 코드만 추출 (네이버용)
            clean_ticker = ticker.replace('.KS', '').replace('.KQ', '')
            
            # 데이터 가져오기 (FinanceDataReader 사용)
            df = fdr.DataReader(clean_ticker, '2023-01-01')
            
            if df.empty:
                st.error(f"❌ {ticker}: 데이터가 없습니다. 코드를 확인하세요.")
                continue

            # 보조지표 계산 (pandas_ta)
            # 이평선
            df['MA5'] = ta.sma(df['Close'], length=5)
            df['MA20'] = ta.sma(df['Close'], length=20)
            df['MA60'] = ta.sma(df['Close'], length=60)
            df['MA120'] = ta.sma(df['Close'], length=120)
            
            # 스토캐스틱
            stoch = ta.stoch(df['High'], df['Low'], df['Close'], k=k_period, d=d_period)
            # pandas_ta 컬럼명 처리
            k_col = f'STOCHk_{k_period}_{d_period}_3'
            d_col = f'STOCHd_{k_period}_{d_period}_3'
            
            if k_col not in stoch.columns:
                 df['%K'] = stoch.iloc[:, 0]
                 df['%D'] = stoch.iloc[:, 1]
            else:
                df['%K'] = stoch[k_col]
                df['%D'] = stoch[d_col]

            # 최근 데이터
            last_close = df['Close'].iloc[-1]
            last_date = df.index[-1].strftime('%Y-%m-%d')
            prev_close = df['Close'].iloc[-2]
            change = last_close - prev_close
            change_pct = (change / prev_close) * 100
            
            # 색상 결정
            color = "red" if change > 0 else "blue" if change < 0 else "gray"
            sign = "+" if change > 0 else ""

            st.markdown(f"### 📈 {clean_ticker} ({last_date})")
            st.markdown(f"<h2 style='color:{color}'>{last_close:,.0f}원 ({sign}{change:,.0f}, {sign}{change_pct:.2f}%)</h2>", unsafe_allow_html=True)

            # 차트 그리기
            fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.05, row_heights=[0.7, 0.3])

            # 캔들차트
            fig.add_trace(go.Candlestick(x=df.index,
                open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
                name='캔들'), row=1, col=1)

            # 이평선
            fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='orange', width=1), name='5일선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], line=dict(color='yellow', width=1), name='20일선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA60'], line=dict(color='green', width=1), name='60일선'), row=1, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['MA120'], line=dict(color='gray', width=1), name='120일선'), row=1, col=1)

            # 스토캐스틱
            fig.add_trace(go.Scatter(x=df.index, y=df['%K'], line=dict(color='cyan', width=1), name='%K'), row=2, col=1)
            fig.add_trace(go.Scatter(x=df.index, y=df['%D'], line=dict(color='magenta', width=1), name='%D'), row=2, col=1)
            
            # 기준선
            fig.add_hline(y=overbought, line_dash="dot", row=2, col=1, line_color="red")
            fig.add_hline(y=oversold, line_dash="dot", row=2, col=1, line_color="blue")

            # 레이아웃
            fig.update_layout(height=800, xaxis_rangeslider_visible=False, template="plotly_dark")
            
            st.plotly_chart(fig, use_container_width=True)
            st.divider()

        except Exception as e:
            st.error(f"⚠️ {ticker} 에러 발생: {e}")
