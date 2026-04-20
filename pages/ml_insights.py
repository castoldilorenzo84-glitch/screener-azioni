"""
ML Insights — Ciclo di Mercato e Pesi Dinamici
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from utils.ciclo_mercato import rileva_regime_mercato, get_regime_summary, get_mercati_disponibili
from utils.ml_weights import get_pesi_dinamici, confronta_pesi
from utils.cache_locale import stato_cache, svuota_cache, cache_disponibile


st.title("🧠 ML Insights — Ciclo di Mercato")
st.caption("Rilevamento automatico del regime di mercato e adattamento dei pesi del modello.")

# ── Selettore mercato ─────────────────────────────────────────
col_m, col_b = st.columns([3, 1])
with col_m:
    mercato_sel = st.selectbox(
        "🌍 Mercato da analizzare",
        options=get_mercati_disponibili(),
        key="ml_mercato",
    )
with col_b:
    st.write("")
    if st.button("🔄 Aggiorna", use_container_width=True):
        rileva_regime_mercato.clear()
        st.rerun()

# ── Rilevamento regime ────────────────────────────────────────
with st.spinner(f"Analisi {mercato_sel}..."):
    regime = rileva_regime_mercato(mercato_sel)

# ── Card regime ───────────────────────────────────────────────
st.markdown(f"""
<div style="background:{regime.colore}22; border-left:6px solid {regime.colore};
            border-radius:8px; padding:16px 20px; margin-bottom:16px;">
    <div style="font-size:2rem; font-weight:700; color:{regime.colore};">
        {regime.emoji} Regime: {regime.nome}
    </div>
    <div style="font-size:1rem; color:#333; margin-top:4px;">
        {regime.descrizione}
    </div>
    <div style="font-size:0.85rem; color:#666; margin-top:4px;">
        Mercato analizzato: <b>{mercato_sel}</b>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Segnali individuali ───────────────────────────────────────
st.subheader("📡 Segnali di Mercato")
if regime.segnali:
    cols = st.columns(2)
    for i, (nome, desc) in enumerate(regime.segnali.items()):
        with cols[i % 2]:
            st.markdown(f"**{nome}:** {desc}")
else:
    st.info("Nessun segnale disponibile.")

# ── Nota sui mercati europei ──────────────────────────────────
if "USA" not in mercato_sel:
    st.info("""
    ℹ️ **Nota sui mercati europei:** L'analisi usa ETF quotati su NYSE come proxy
    (es. EWG per il DAX, EWI per il MIB, EWU per il FTSE 100).
    I valori riflettono il sentiment degli investitori internazionali su questi mercati.
    Il VIX europeo (VSTOXX) non è disponibile gratuitamente — viene usato il momentum
    dell'indice di riferimento come proxy della volatilità.
    """)

# ── Pesi dinamici ─────────────────────────────────────────────
st.divider()
st.subheader("⚙️ Pesi Dinamici del Modello")
st.caption(f"Adattati al regime **{regime.nome}** (blend 70% regime / 30% default).")

pesi = get_pesi_dinamici(regime)
confronto = confronta_pesi(pesi)

st.session_state["pesi_dinamici"] = pesi
st.session_state["regime_attuale"] = regime

df_conf = pd.DataFrame(confronto)
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_conf["Fattore"],
    y=[float(v.rstrip("%")) for v in df_conf["Default"]],
    name="Default", marker_color="#AAAAAA", opacity=0.7,
))
fig.add_trace(go.Bar(
    x=df_conf["Fattore"],
    y=[float(v.rstrip("%")) for v in df_conf["Dinamico"]],
    name=f"Dinamico ({regime.nome})", marker_color=regime.colore,
))
fig.update_layout(
    barmode="group", height=320,
    margin=dict(l=10, r=10, t=20, b=80),
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f9f9f9",
    legend=dict(orientation="h"),
    xaxis=dict(tickangle=-30),
    yaxis=dict(title="%", tickformat=".0f"),
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    df_conf[["Fattore", "Default", "Dinamico", "Variazione"]],
    use_container_width=True, hide_index=True,
)

st.info("""
💡 **Come funziona:** I pesi cambiano in base al regime rilevato.
In Bull Market si privilegia il Momentum; in Bear/Stress aumentano
Low Volatility e Dividend Yield per protezione del portafoglio.
""")

# ── Grafico benchmark storico ─────────────────────────────────
st.divider()
st.subheader(f"📊 Andamento Benchmark — {mercato_sel}")

import yfinance as yf
import numpy as np
from utils.ciclo_mercato import CONFIG_MERCATI

cfg = CONFIG_MERCATI.get(mercato_sel, CONFIG_MERCATI["🇺🇸 USA (S&P 500)"])
bench_ticker = cfg["benchmark"]

with st.spinner(f"Caricamento {bench_ticker}..."):
    try:
        spy = yf.download(bench_ticker, period="2y", interval="1d",
                          auto_adjust=True, progress=False)
        if not spy.empty:
            close = spy["Close"].dropna()
            ma50  = close.rolling(50).mean()
            ma200 = close.rolling(200).mean()

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=close.index, y=close,
                name=bench_ticker, line=dict(color="#1a5276", width=2),
            ))
            fig2.add_trace(go.Scatter(
                x=ma50.index, y=ma50, name="MA 50",
                line=dict(color="#f39c12", width=1.5, dash="dot"),
            ))
            fig2.add_trace(go.Scatter(
                x=ma200.index, y=ma200, name="MA 200",
                line=dict(color="#8e44ad", width=2, dash="dash"),
            ))
            fig2.update_layout(
                height=320,
                title=f"{bench_ticker} — 2 anni (proxy {mercato_sel})",
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f9f9f9",
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig2, use_container_width=True)
    except Exception:
        st.info("Grafico benchmark non disponibile.")

# ── Cache locale ──────────────────────────────────────────────
st.divider()
st.subheader("💾 Cache Locale Dati API")

if not cache_disponibile():
    st.warning("Cache non disponibile: Google Sheets non configurato.")
else:
    stato = stato_cache()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker in cache", stato.get("totale", 0))
    c2.metric("Dati freschi (<8h)", stato.get("freschi", 0))
    c3.metric("Scaduti", stato.get("scaduti", 0))
    c4.metric("Ultimo aggiorn.", stato.get("ultimo_aggiornamento", "—"))
    st.caption("La cache salva i fondamentali su Google Sheets per 8 ore.")
    if st.button("🗑️ Svuota cache"):
        ok = svuota_cache()
        st.success("✅ Cache svuotata.") if ok else st.error("Errore.")


# ── Card regime ───────────────────────────────────────────────
st.markdown(f"""
<div style="background:{regime.colore}22; border-left:6px solid {regime.colore};
            border-radius:8px; padding:16px 20px; margin-bottom:16px;">
    <div style="font-size:2rem; font-weight:700; color:{regime.colore};">
        {regime.emoji} Regime attuale: {regime.nome}
    </div>
    <div style="font-size:1rem; color:#333; margin-top:4px;">
        {regime.descrizione}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Segnali individuali ───────────────────────────────────────
st.subheader("📡 Segnali di Mercato")
if regime.segnali:
    cols = st.columns(2)
    for i, (nome, desc) in enumerate(regime.segnali.items()):
        with cols[i % 2]:
            st.markdown(f"**{nome}:** {desc}")
else:
    st.info("Nessun segnale disponibile.")

# ── Pesi dinamici ─────────────────────────────────────────────
st.divider()
st.subheader("⚙️ Pesi Dinamici del Modello")
st.caption(f"Adattati al regime **{regime.nome}** (blend 70% regime / 30% default).")

pesi = get_pesi_dinamici(regime)
confronto = confronta_pesi(pesi)

# Salva in session state per uso in scoring
st.session_state["pesi_dinamici"] = pesi
st.session_state["regime_attuale"] = regime

# Grafico a barre confronto pesi
df_conf = pd.DataFrame(confronto)
fig = go.Figure()
fig.add_trace(go.Bar(
    x=df_conf["Fattore"],
    y=[float(v.rstrip("%")) for v in df_conf["Default"]],
    name="Default",
    marker_color="#AAAAAA",
    opacity=0.7,
))
fig.add_trace(go.Bar(
    x=df_conf["Fattore"],
    y=[float(v.rstrip("%")) for v in df_conf["Dinamico"]],
    name=f"Dinamico ({regime.nome})",
    marker_color=regime.colore,
))
fig.update_layout(
    barmode="group",
    height=320,
    margin=dict(l=10, r=10, t=20, b=80),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="#f9f9f9",
    legend=dict(orientation="h"),
    xaxis=dict(tickangle=-30),
    yaxis=dict(title="%", tickformat=".0f"),
)
st.plotly_chart(fig, use_container_width=True)

# Tabella dettaglio
df_show = df_conf[["Fattore", "Default", "Dinamico", "Variazione"]].copy()

def _color_variazione(val):
    v = val.replace("%", "").replace("+", "").strip()
    try:
        n = float(v)
        if n > 0: return "color: #276221; font-weight: bold"
        if n < 0: return "color: #C00000; font-weight: bold"
    except Exception:
        pass
    return ""

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Fattore":    st.column_config.TextColumn("Fattore"),
        "Default":    st.column_config.TextColumn("Peso Default"),
        "Dinamico":   st.column_config.TextColumn("Peso Dinamico"),
        "Variazione": st.column_config.TextColumn("Variazione"),
    }
)

st.info("""
💡 **Come funziona:** I pesi vengono adattati in base al regime rilevato.
In Bull Market si privilegia il Momentum (+8/+13%); in Bear/Stress si aumenta
il peso di Low Volatility (+13/+13%) e Dividend Yield (+1/+5%) per protezione.
Il blend 70/30 evita variazioni troppo brusche.
""")

# ── Storico regimi (se disponibile da Preferiti) ──────────────
st.divider()
st.subheader("📊 Contesto Storico S&P 500")

import yfinance as yf
import numpy as np

with st.spinner("Caricamento SPY..."):
    try:
        spy = yf.download("SPY", period="2y", interval="1d",
                          auto_adjust=True, progress=False)
        if not spy.empty:
            close = spy["Close"].dropna()
            ma50  = close.rolling(50).mean()
            ma200 = close.rolling(200).mean()

            fig2 = go.Figure()
            fig2.add_trace(go.Scatter(
                x=close.index, y=close,
                name="SPY", line=dict(color="#1a5276", width=2),
            ))
            fig2.add_trace(go.Scatter(
                x=ma50.index, y=ma50,
                name="MA 50", line=dict(color="#f39c12", width=1.5, dash="dot"),
            ))
            fig2.add_trace(go.Scatter(
                x=ma200.index, y=ma200,
                name="MA 200", line=dict(color="#8e44ad", width=2, dash="dash"),
            ))
            fig2.update_layout(
                height=320, title="S&P 500 (SPY) — 2 anni",
                margin=dict(l=10, r=10, t=40, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#f9f9f9",
                legend=dict(orientation="h"),
                xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
                yaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            )
            st.plotly_chart(fig2, use_container_width=True)
    except Exception:
        st.info("Grafico SPY non disponibile.")

# ── Cache locale ──────────────────────────────────────────────
st.divider()
st.subheader("💾 Cache Locale Dati API")

if not cache_disponibile():
    st.warning("Cache non disponibile: Google Sheets non configurato.")
else:
    stato = stato_cache()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Ticker in cache", stato.get("totale", 0))
    c2.metric("Dati freschi (<8h)", stato.get("freschi", 0))
    c3.metric("Scaduti", stato.get("scaduti", 0))
    c4.metric("Ultimo aggiorn.", stato.get("ultimo_aggiornamento", "—"))

    st.caption("La cache salva i fondamentali su Google Sheets per 8 ore. Risparmia fino a 200 chiamate API/giorno.")

    if st.button("🗑️ Svuota cache", key="clear_cache"):
        with st.spinner("Svuotamento cache..."):
            ok = svuota_cache()
        if ok:
            st.success("✅ Cache svuotata.")
        else:
            st.error("Errore nello svuotamento.")
