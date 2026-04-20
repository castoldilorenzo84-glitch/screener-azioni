"""
Storico Prezzi — Grafico interattivo 1-2 anni per ticker selezionato
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data import fetch_price_history


st.title("📈 Storico Prezzi")

# ── Selezione ticker ─────────────────────────────────────────────────────────
wl = st.session_state.get("watchlist_tickers", [])

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    if wl:
        ticker_sel = st.selectbox("Ticker", options=wl, key="storico_ticker")
    else:
        ticker_sel = st.text_input("Ticker (es. AAPL)", key="storico_ticker_free").upper().strip()
with col2:
    period = st.selectbox("Periodo", options=["6mo", "1y", "2y", "5y"], index=1, key="storico_period")
with col3:
    st.write("")
    st.write("")
    btn_load = st.button("📊 Carica", type="primary", use_container_width=True)

if not ticker_sel:
    st.info("Inserisci o seleziona un ticker per visualizzare lo storico.")
    st.stop()

# ── Caricamento ──────────────────────────────────────────────────────────────
if btn_load or ticker_sel:
    with st.spinner(f"Caricamento storico {ticker_sel}..."):
        df = fetch_price_history(ticker_sel, period=period)

    if df is None or df.empty:
        st.error(f"Nessun dato storico trovato per {ticker_sel}.")
        st.stop()

    # ── Metriche riassunto ────────────────────────────────────────────────────
    latest  = df["close"].iloc[-1]
    first   = df["close"].iloc[0]
    perf    = (latest / first - 1) * 100
    vol_ann = df["close"].pct_change().dropna().std() * np.sqrt(252) * 100
    max_p   = df["close"].max()
    min_p   = df["close"].min()
    dd      = (latest / max_p - 1) * 100

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Prezzo attuale", f"${latest:,.2f}")
    m2.metric(f"Performance ({period})", f"{perf:+.1f}%", delta=f"{perf:+.1f}%")
    m3.metric("Volatilità annua", f"{vol_ann:.1f}%")
    m4.metric("Massimo periodo", f"${max_p:,.2f}")
    m5.metric("Dal massimo", f"{dd:.1f}%", delta=f"{dd:.1f}%")

    # ── Opzioni overlay ───────────────────────────────────────────────────────
    ov_col1, ov_col2, ov_col3, ov_col4 = st.columns(4)
    show_ma50  = ov_col1.toggle("MA 50",  value=True,  key="ov_ma50")
    show_ma200 = ov_col2.toggle("MA 200", value=True,  key="ov_ma200")
    show_ma20  = ov_col3.toggle("MA 20",  value=False, key="ov_ma20")
    show_rsi   = ov_col4.toggle("RSI 14", value=False, key="ov_rsi")

    # ── Calcolo RSI ───────────────────────────────────────────────────────────
    def calc_rsi(series: pd.Series, period: int = 14) -> pd.Series:
        delta  = series.diff()
        gain   = delta.where(delta > 0, 0.0)
        loss   = -delta.where(delta < 0, 0.0)
        avg_g  = gain.ewm(alpha=1/period, min_periods=period).mean()
        avg_l  = loss.ewm(alpha=1/period, min_periods=period).mean()
        rs     = avg_g / avg_l.replace(0, np.nan)
        return 100 - (100 / (1 + rs))

    rsi = calc_rsi(df["close"]) if show_rsi else None

    # ── Grafico candele ───────────────────────────────────────────────────────
    # Layout con subplot RSI se attivo
    if show_rsi and rsi is not None:
        from plotly.subplots import make_subplots
        fig = make_subplots(
            rows=2, cols=1, shared_xaxes=True,
            row_heights=[0.72, 0.28],
            vertical_spacing=0.03,
        )
        rsi_row = 2
    else:
        from plotly.subplots import make_subplots
        fig = make_subplots(rows=1, cols=1)
        rsi_row = None

    # Candlestick (se disponibili OHLC)
    if all(c in df.columns for c in ["open", "high", "low", "close"]):
        fig.add_trace(go.Candlestick(
            x=df["date"],
            open=df["open"],
            high=df["high"],
            low=df["low"],
            close=df["close"],
            name=ticker_sel,
            increasing_line_color="#2d7a2d",
            decreasing_line_color="#c0392b",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df["date"], y=df["close"],
            name=ticker_sel,
            line=dict(color="#1a5276", width=2),
        ), row=1, col=1)

    # Medie mobili
    df["ma20"]  = df["close"].rolling(20).mean()
    df["ma50"]  = df["close"].rolling(50).mean()
    df["ma200"] = df["close"].rolling(200).mean()

    if show_ma20:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma20"],  name="MA 20",
                                 line=dict(color="#f39c12", width=1, dash="dot")), row=1, col=1)
    if show_ma50:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma50"],  name="MA 50",
                                 line=dict(color="#2980b9", width=1.5)), row=1, col=1)
    if show_ma200:
        fig.add_trace(go.Scatter(x=df["date"], y=df["ma200"], name="MA 200",
                                 line=dict(color="#8e44ad", width=1.5, dash="dash")), row=1, col=1)

    # RSI subplot
    if show_rsi and rsi is not None and rsi_row:
        fig.add_trace(go.Scatter(
            x=df["date"], y=rsi,
            name="RSI 14",
            line=dict(color="#e74c3c", width=1.5),
        ), row=rsi_row, col=1)
        # Linee 30/70
        fig.add_hline(y=70, line_dash="dash", line_color="#c0392b",
                      annotation_text="Ipercomprato (70)", row=rsi_row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#27ae60",
                      annotation_text="Ipervenduto (30)", row=rsi_row, col=1)
        # Ultimo valore RSI
        rsi_now = rsi.dropna().iloc[-1] if rsi.dropna().shape[0] > 0 else None
        if rsi_now:
            if rsi_now > 70:
                st.warning(f"⚠️ RSI attuale: **{rsi_now:.1f}** — zona ipercomprato. Potenziale inversione.")
            elif rsi_now < 30:
                st.success(f"✅ RSI attuale: **{rsi_now:.1f}** — zona ipervenduto. Potenziale rimbalzo.")
            else:
                st.info(f"ℹ️ RSI attuale: **{rsi_now:.1f}** — zona neutrale.")

    fig.update_layout(
        title=f"{ticker_sel} — {period}",
        xaxis_rangeslider_visible=False,
        height=480 if not show_rsi else 580,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9f9f9",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=10, r=10, t=60, b=10),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Volume ────────────────────────────────────────────────────────────────
    if "volume" in df.columns and df["volume"].notna().any():
        df["vol_color"] = np.where(df["close"] >= df["close"].shift(1), "#2d7a2d", "#c0392b")
        fig_vol = go.Figure()
        fig_vol.add_trace(go.Bar(
            x=df["date"], y=df["volume"],
            name="Volume",
            marker_color=df["vol_color"],
            opacity=0.7,
        ))
        fig_vol.update_layout(
            height=160,
            margin=dict(l=10, r=10, t=10, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f9f9f9",
            yaxis=dict(title="Volume", showgrid=True, gridcolor="#e0e0e0"),
            showlegend=False,
        )
        st.plotly_chart(fig_vol, use_container_width=True)

    # ── Rendimenti mensili ────────────────────────────────────────────────────
    with st.expander("📅 Rendimenti mensili", expanded=False):
        df_m = df.set_index("date")["close"].resample("ME").last().pct_change().dropna() * 100
        df_m.name = "ret_%"
        df_m = df_m.reset_index()
        df_m.columns = ["mese", "ret_%"]
        df_m["mese"] = df_m["mese"].dt.strftime("%Y-%m")
        colors = ["#2d7a2d" if v >= 0 else "#c0392b" for v in df_m["ret_%"]]
        fig_m = go.Figure(go.Bar(
            x=df_m["mese"], y=df_m["ret_%"],
            marker_color=colors,
            text=[f"{v:+.1f}%" for v in df_m["ret_%"]],
            textposition="outside",
        ))
        fig_m.update_layout(height=280, margin=dict(l=10, r=10, t=20, b=10),
                            paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
        st.plotly_chart(fig_m, use_container_width=True)
