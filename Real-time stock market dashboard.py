"""
Real-Time Stock Market Dashboard
---------------------------------
A single-file Streamlit app that pulls live/near-live stock data with
yfinance, computes common financial indicators with pandas, and renders
interactive charts with Plotly.

Run:
    pip install -r requirements.txt
    streamlit run app.py
"""

import time
import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf

# --------------------------------------------------------------------------
# Page config
# --------------------------------------------------------------------------
st.set_page_config(
    page_title="Real-Time Stock Dashboard",
    page_icon="📈",
    layout="wide",
)

# --------------------------------------------------------------------------
# Sidebar controls
# --------------------------------------------------------------------------
st.sidebar.title("📊 Dashboard Controls")

tickers_input = st.sidebar.text_input(
    "Ticker symbol(s), comma-separated",
    value="AAPL, MSFT, TSLA",
    help="Example: AAPL, MSFT, GOOGL, TSLA",
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

period = st.sidebar.selectbox(
    "History range",
    options=["1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"],
    index=2,
)

interval_map = {
    "1d": "5m",
    "5d": "15m",
    "1mo": "1d",
    "3mo": "1d",
    "6mo": "1d",
    "1y": "1d",
    "2y": "1wk",
    "5y": "1wk",
}
interval = interval_map[period]

show_ma = st.sidebar.checkbox("Show Moving Averages (20 / 50)", value=True)
show_rsi = st.sidebar.checkbox("Show RSI (14)", value=True)

auto_refresh = st.sidebar.checkbox("Auto-refresh every 60s", value=False)

st.sidebar.markdown("---")
st.sidebar.caption(
    "Data source: Yahoo Finance via `yfinance`. "
    "Prices are delayed slightly (typically ~15 min), not tick-by-tick real time."
)

# --------------------------------------------------------------------------
# Data fetching (cached briefly so the app stays responsive)
# --------------------------------------------------------------------------
@st.cache_data(ttl=60, show_spinner=False)
def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.Ticker(ticker).history(period=period, interval=interval)
    df = df.reset_index()
    date_col = "Datetime" if "Datetime" in df.columns else "Date"
    df.rename(columns={date_col: "Date"}, inplace=True)
    return df


@st.cache_data(ttl=60, show_spinner=False)
def fetch_info(ticker: str) -> dict:
    try:
        return yf.Ticker(ticker).fast_info
    except Exception:
        return {}


def add_indicators(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["MA20"] = df["Close"].rolling(window=20).mean()
    df["MA50"] = df["Close"].rolling(window=50).mean()

    # RSI (14)
    delta = df["Close"].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss.replace(0, pd.NA)
    df["RSI14"] = 100 - (100 / (1 + rs))
    return df


def build_price_chart(df: pd.DataFrame, ticker: str, show_ma: bool) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(
        go.Candlestick(
            x=df["Date"],
            open=df["Open"],
            high=df["High"],
            low=df["Low"],
            close=df["Close"],
            name=ticker,
        )
    )
    if show_ma:
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["MA20"], name="MA20", line=dict(width=1.5))
        )
        fig.add_trace(
            go.Scatter(x=df["Date"], y=df["MA50"], name="MA50", line=dict(width=1.5))
        )
    fig.update_layout(
        title=f"{ticker} Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        xaxis_rangeslider_visible=False,
        height=450,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def build_volume_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["Date"], y=df["Volume"], name="Volume"))
    fig.update_layout(
        title=f"{ticker} Volume",
        height=200,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


def build_rsi_chart(df: pd.DataFrame, ticker: str) -> go.Figure:
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI14"], name="RSI 14"))
    fig.add_hline(y=70, line_dash="dash", line_color="red")
    fig.add_hline(y=30, line_dash="dash", line_color="green")
    fig.update_layout(
        title=f"{ticker} RSI (14)",
        yaxis=dict(range=[0, 100]),
        height=220,
        margin=dict(l=10, r=10, t=40, b=10),
    )
    return fig


# --------------------------------------------------------------------------
# Main layout
# --------------------------------------------------------------------------
st.title("📈 Real-Time Stock Market Dashboard")
st.caption(f"Last updated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if not tickers:
    st.warning("Enter at least one ticker symbol in the sidebar.")
    st.stop()

for ticker in tickers:
    st.markdown(f"## {ticker}")

    with st.spinner(f"Fetching {ticker}..."):
        raw_df = fetch_data(ticker, period, interval)

    if raw_df.empty:
        st.error(f"No data found for '{ticker}'. Check the symbol and try again.")
        continue

    df = add_indicators(raw_df)

    latest = df.iloc[-1]
    prev = df.iloc[-2] if len(df) > 1 else latest
    change = latest["Close"] - prev["Close"]
    pct_change = (change / prev["Close"]) * 100 if prev["Close"] else 0

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric(
        "Price",
        f"${latest['Close']:.2f}",
        f"{change:+.2f} ({pct_change:+.2f}%)",
    )
    col2.metric("Open", f"${latest['Open']:.2f}")
    col3.metric("Day High", f"${df['High'].max():.2f}")
    col4.metric("Day Low", f"${df['Low'].min():.2f}")
    col5.metric("Volume", f"{int(latest['Volume']):,}")

    st.plotly_chart(build_price_chart(df, ticker, show_ma), use_container_width=True)

    chart_col1, chart_col2 = st.columns(2)
    with chart_col1:
        st.plotly_chart(build_volume_chart(df, ticker), use_container_width=True)
    if show_rsi:
        with chart_col2:
            st.plotly_chart(build_rsi_chart(df, ticker), use_container_width=True)

    with st.expander(f"Raw data — {ticker}"):
        st.dataframe(df.tail(50), use_container_width=True)

    st.markdown("---")

# --------------------------------------------------------------------------
# Auto-refresh
# --------------------------------------------------------------------------
if auto_refresh:
    time.sleep(60)
    st.rerun()
