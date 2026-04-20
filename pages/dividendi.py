"""
Dividendi — Storico distribuzioni per ticker selezionato
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.data import fetch_dividends, fetch_watchlist_ticker


st.title("💰 Dividendi")

# ── Selezione ticker ─────────────────────────────────────────────────────────
wl = st.session_state.get("watchlist_tickers", [])

col1, col2 = st.columns([3, 1])
with col1:
    if wl:
        ticker_sel = st.selectbox("Ticker", options=wl, key="div_ticker")
    else:
        ticker_sel = st.text_input("Ticker (es. JNJ, KO)", key="div_ticker_free").upper().strip()
with col2:
    st.write("")
    st.write("")
    btn_load = st.button("📊 Carica", type="primary", use_container_width=True)

if not ticker_sel:
    st.info("Seleziona o inserisci un ticker per vedere i dividendi.")
    st.stop()

# ── Dati ─────────────────────────────────────────────────────────────────────
if btn_load or ticker_sel:
    with st.spinner(f"Caricamento dividendi {ticker_sel}..."):
        df_div = fetch_dividends(ticker_sel)
        # Info prezzo per calcolo yield
        try:
            wl_data: pd.DataFrame = st.session_state.get("watchlist_data")
            if wl_data is not None and ticker_sel in wl_data.index:
                current_price = float(wl_data.loc[ticker_sel, "prezzo"] or 0)
            else:
                info = fetch_watchlist_ticker(ticker_sel)
                current_price = float(info.get("prezzo") or 0)
        except Exception:
            current_price = 0

    if df_div is None or df_div.empty:
        st.warning(f"Nessun dividendo trovato per {ticker_sel}. Potrebbe non distribuire dividendi.")
        st.stop()

    # ── Metriche ──────────────────────────────────────────────────────────────
    # Normalizza le date rimuovendo il timezone per evitare errori di confronto
    df_div["date"] = pd.to_datetime(df_div["date"]).dt.tz_localize(None)
    last_year = df_div[df_div["date"] > pd.Timestamp.now() - pd.DateOffset(years=1)]
    annual_div = last_year["dividendo"].sum()
    fwd_yield  = (annual_div / current_price * 100) if current_price > 0 else None
    pay_count  = len(last_year)
    freq_map   = {0: "—", 1: "Annuale", 2: "Semestrale", 4: "Trimestrale", 12: "Mensile"}
    freq = freq_map.get(pay_count, f"{pay_count}x/anno")
    last_div   = df_div["dividendo"].iloc[0] if not df_div.empty else None

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Dividendo annuo ($)", f"${annual_div:.4f}" if annual_div else "—")
    m2.metric("Yield forward", f"{fwd_yield:.2f}%" if fwd_yield else "—")
    m3.metric("Frequenza", freq)
    m4.metric("Ultimo dividendo", f"${last_div:.4f}" if last_div else "—")

    # ── Grafico barre dividendi ────────────────────────────────────────────────
    st.subheader(f"📊 Storico distribuzioni — {ticker_sel}")
    df_plot = df_div.sort_values("date").copy()

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df_plot["date"],
        y=df_plot["dividendo"],
        name="Dividendo ($)",
        marker_color="#2d7a2d",
        text=[f"${v:.4f}" for v in df_plot["dividendo"]],
        textposition="outside",
    ))
    # Linea trend
    if len(df_plot) >= 4:
        ma = df_plot["dividendo"].rolling(4).mean()
        fig.add_trace(go.Scatter(
            x=df_plot["date"], y=ma,
            name="Media mobile 4 periodi",
            line=dict(color="#b38600", width=2, dash="dash"),
        ))

    fig.update_layout(
        height=350,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9f9f9",
        xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
        yaxis=dict(title="Dividendo ($)", showgrid=True, gridcolor="#e0e0e0"),
        legend=dict(orientation="h"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabella ────────────────────────────────────────────────────────────────
    st.subheader("📋 Tabella distribuzione")
    df_table = df_div.copy()
    df_table["data"] = df_table["date"].dt.strftime("%Y-%m-%d")
    df_table["variazione"] = df_table["dividendo"].pct_change(-1) * 100  # rispetto al precedente

    st.dataframe(
        df_table[["data", "dividendo", "variazione"]].rename(columns={
            "data": "Data Ex-Div",
            "dividendo": "Dividendo ($)",
            "variazione": "Variaz. %",
        }),
        column_config={
            "Data Ex-Div": st.column_config.TextColumn("Data Ex-Div"),
            "Dividendo ($)": st.column_config.NumberColumn("Dividendo ($)", format="$%.4f"),
            "Variaz. %": st.column_config.NumberColumn("Var. %", format="%.1f%%"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── Crescita dividendi ────────────────────────────────────────────────────
    if len(df_div) >= 8:
        with st.expander("📈 Analisi crescita dividendi (DGR)", expanded=False):
            yearly = df_div.copy()
            yearly["anno"] = yearly["date"].dt.year
            yearly_sum = yearly.groupby("anno")["dividendo"].sum().reset_index()
            yearly_sum["DGR"] = yearly_sum["dividendo"].pct_change() * 100

            # DGR 1Y, 3Y, 5Y
            if len(yearly_sum) >= 2:
                dgr1 = yearly_sum["DGR"].iloc[-1]
            else:
                dgr1 = None
            dgr3 = (yearly_sum["dividendo"].iloc[-1] / yearly_sum["dividendo"].iloc[-min(4, len(yearly_sum))] ** (1/3) - 1) * 100 if len(yearly_sum) >= 4 else None
            dgr5 = (yearly_sum["dividendo"].iloc[-1] / yearly_sum["dividendo"].iloc[-min(6, len(yearly_sum))] ** (1/5) - 1) * 100 if len(yearly_sum) >= 6 else None

            d1, d2, d3 = st.columns(3)
            d1.metric("DGR 1 anno", f"{dgr1:+.1f}%" if dgr1 else "—")
            d2.metric("DGR 3 anni (CAGR)", f"{dgr3:+.1f}%" if dgr3 else "—")
            d3.metric("DGR 5 anni (CAGR)", f"{dgr5:+.1f}%" if dgr5 else "—")

            fig_y = go.Figure(go.Bar(
                x=yearly_sum["anno"].astype(str),
                y=yearly_sum["dividendo"],
                marker_color=["#2d7a2d" if v >= (yearly_sum["dividendo"].iloc[max(0, i-1)] if i > 0 else 0) else "#c0392b"
                              for i, v in enumerate(yearly_sum["dividendo"])],
                text=[f"${v:.2f}" for v in yearly_sum["dividendo"]],
                textposition="outside",
            ))
            fig_y.update_layout(height=250, margin=dict(l=10, r=10, t=20, b=10),
                                paper_bgcolor="rgba(0,0,0,0)", showlegend=False)
            st.plotly_chart(fig_y, use_container_width=True)

    # ── Yield on Cost — Proiezione 10 anni ────────────────────────────────────
    if annual_div > 0 and current_price > 0:
        with st.expander("📊 Proiezione Yield on Cost (5 e 10 anni)", expanded=False):
            st.caption(
                "Mostra quale sarà il rendimento sul capitale investito OGGI "
                "se l'azienda continua a far crescere il dividendo al ritmo storico."
            )

            # DGR da usare per la proiezione
            dgr_proj = None
            if len(df_div) >= 8:
                yearly2 = df_div.copy()
                yearly2["anno"] = yearly2["date"].dt.year
                ys = yearly2.groupby("anno")["dividendo"].sum()
                if len(ys) >= 4:
                    try:
                        dgr_proj = (ys.iloc[-1] / ys.iloc[-min(4, len(ys))]) ** (1/3) - 1
                    except Exception:
                        dgr_proj = None

            yoc_col1, yoc_col2 = st.columns([2, 3])
            with yoc_col1:
                prezzo_acquisto = st.number_input(
                    "Prezzo di acquisto ipotetico ($)",
                    value=float(current_price), min_value=0.01,
                    step=0.01, key="yoc_price",
                )
                dgr_input = st.slider(
                    "DGR annuo ipotetico (%)",
                    min_value=0.0, max_value=20.0,
                    value=float(dgr_proj * 100) if dgr_proj else 5.0,
                    step=0.5, key="yoc_dgr",
                ) / 100

            with yoc_col2:
                if prezzo_acquisto > 0:
                    anni = list(range(0, 11))
                    yoc_vals = []
                    div_ann  = annual_div
                    for a in anni:
                        yoc = (div_ann * (1 + dgr_input) ** a) / prezzo_acquisto * 100
                        yoc_vals.append(round(yoc, 2))

                    yoc_5  = yoc_vals[5]
                    yoc_10 = yoc_vals[10]
                    yoc_now = annual_div / prezzo_acquisto * 100

                    yc1, yc2, yc3 = st.columns(3)
                    yc1.metric("Yield attuale",  f"{yoc_now:.2f}%")
                    yc2.metric("Yield on Cost 5Y", f"{yoc_5:.2f}%",
                               delta=f"+{yoc_5-yoc_now:.2f}%")
                    yc3.metric("Yield on Cost 10Y", f"{yoc_10:.2f}%",
                               delta=f"+{yoc_10-yoc_now:.2f}%")

                    fig_yoc = go.Figure()
                    fig_yoc.add_trace(go.Scatter(
                        x=anni, y=yoc_vals,
                        mode="lines+markers",
                        name="Yield on Cost",
                        line=dict(color="#2d7a2d", width=2.5),
                        marker=dict(size=8),
                        fill="tozeroy",
                        fillcolor="rgba(45,122,45,0.1)",
                    ))
                    fig_yoc.add_hline(
                        y=yoc_now, line_dash="dash",
                        line_color="#999",
                        annotation_text=f"Yield attuale: {yoc_now:.2f}%",
                    )
                    fig_yoc.update_layout(
                        height=250,
                        margin=dict(l=10, r=10, t=20, b=30),
                        paper_bgcolor="rgba(0,0,0,0)",
                        plot_bgcolor="#f9f9f9",
                        xaxis=dict(title="Anni", tickvals=anni),
                        yaxis=dict(title="Yield on Cost (%)", tickformat=".1f"),
                        showlegend=False,
                    )
                    st.plotly_chart(fig_yoc, use_container_width=True)
                    st.caption(
                        f"Con DGR {dgr_input*100:.1f}%/anno e prezzo acquisto ${prezzo_acquisto:.2f}, "
                        f"tra 10 anni riceveresti il {yoc_10:.2f}% del tuo capitale investito ogni anno solo in dividendi."
                    )
