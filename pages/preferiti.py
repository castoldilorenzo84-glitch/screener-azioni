"""
Preferiti — Memoria storica dei ticker seguiti nel tempo
Ogni aggiornamento aggiunge uno snapshot → mostra evoluzione score e metriche
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from utils.storage import (
    load_preferiti, save_snapshot, delete_ticker_history,
    get_ticker_evolution, get_tracked_tickers, gdrive_available
)
from utils.data import fetch_watchlist_ticker
from utils.scoring import compute_watchlist_scores


st.title("⭐ Preferiti — Memoria Storica")
st.caption("Traccia l'evoluzione di ogni ticker nel tempo: ogni salvataggio aggiunge uno snapshot storico.")

# ── Check Google Sheets ───────────────────────────────────────────────────────
if not gdrive_available():
    st.error("""
    **Google Sheets non configurato.**

    Per usare i Preferiti devi configurare le credenziali Google nel file `.streamlit/secrets.toml`.

    Consulta il **README.md** per le istruzioni passo-passo (5 minuti, tutto gratuito).
    """)
    with st.expander("📋 Guida rapida configurazione Google Sheets"):
        st.markdown("""
        1. Vai su [Google Cloud Console](https://console.cloud.google.com)
        2. Crea un progetto (o usa uno esistente)
        3. Abilita le API: **Google Sheets API** e **Google Drive API**
        4. Crea credenziali → **Service Account** → scarica il JSON
        5. Crea un Google Sheet vuoto chiamato `Screener_Preferiti`
        6. Condividi il foglio con l'email del Service Account (dalla colonna `client_email` del JSON)
        7. Copia i valori del JSON nel file `.streamlit/secrets.toml` (vedi `secrets.toml.example`)
        """)
    st.stop()

# ── Carica dati ───────────────────────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def _load():
    return load_preferiti()

# Pulsante refresh cache
col_h1, col_h2 = st.columns([4, 1])
with col_h2:
    if st.button("🔄 Ricarica", use_container_width=True):
        st.cache_data.clear()
        st.session_state["preferiti_df"] = None
        st.rerun()

if st.session_state.get("preferiti_df") is None:
    with st.spinner("Caricamento Preferiti da Google Sheets..."):
        st.session_state["preferiti_df"] = _load()

pref_df: pd.DataFrame = st.session_state["preferiti_df"]
tracked = get_tracked_tickers(pref_df)

# ── Sezione: Aggiungi ticker ai Preferiti ─────────────────────────────────────
with st.expander("➕ Aggiungi nuovo ticker ai Preferiti", expanded=(len(tracked) == 0)):
    a1, a2, a3 = st.columns([2, 2, 1])
    with a1:
        new_pref = st.text_input("Ticker (es. AAPL, ENI.MI)", key="new_pref_ticker").upper().strip()
    with a2:
        note_new = st.text_input("Note (opzionale)", key="note_new_pref")
    with a3:
        st.write("")
        st.write("")
        if st.button("💾 Salva snapshot", key="btn_add_pref", use_container_width=True):
            if not new_pref:
                st.warning("Inserisci un ticker.")
            else:
                with st.spinner(f"Caricamento dati {new_pref}..."):
                    data = fetch_watchlist_ticker(new_pref)
                    # Score singolo (non z-scorabile con 1 ticker, usiamo 0)
                    data["score"] = 0.0
                    data["tier"] = "—"
                    data["percentile"] = 0
                ok = save_snapshot(data, note=note_new, fonte="manuale")
                if ok:
                    st.success(f"✅ Snapshot di {new_pref} salvato!")
                    st.session_state["preferiti_df"] = None
                    st.rerun()
                else:
                    st.error("Errore nel salvataggio. Controlla la connessione a Google Sheets.")

# ── Aggiorna snapshot per tutti i preferiti ──────────────────────────────────
if tracked:
    with st.expander("🔄 Aggiorna snapshot per tutti i Preferiti", expanded=False):
        st.write(f"Aggiorna i dati correnti per **{len(tracked)} ticker** e aggiungi un nuovo snapshot.")
        note_bulk = st.text_input("Note aggiornamento", key="note_bulk")
        if st.button("⬇️ Aggiorna tutti", key="btn_bulk_update"):
            prog = st.progress(0, text="Aggiornamento in corso...")
            saved = 0
            for i, ticker in enumerate(tracked):
                prog.progress((i + 1) / len(tracked), text=f"Aggiornamento {ticker}...")
                try:
                    data = fetch_watchlist_ticker(ticker)
                    data["score"] = 0.0
                    data["tier"] = "—"
                    data["percentile"] = 0
                    if save_snapshot(data, note=note_bulk, fonte="aggiornamento"):
                        saved += 1
                except Exception:
                    pass
            prog.empty()
            st.success(f"✅ {saved}/{len(tracked)} snapshot aggiornati.")
            st.session_state["preferiti_df"] = None
            st.rerun()

if pref_df.empty or not tracked:
    st.info("Nessun ticker nei Preferiti. Aggiungine uno con la sezione qui sopra.")
    st.stop()

# ── Selettore ticker ──────────────────────────────────────────────────────────
st.divider()
sel_ticker = st.selectbox(
    "📌 Ticker da analizzare",
    options=tracked,
    key="pref_ticker_sel",
)

if not sel_ticker:
    st.stop()

# ── Evoluzione del ticker selezionato ────────────────────────────────────────
evo = get_ticker_evolution(sel_ticker, pref_df)
if evo.empty:
    st.warning(f"Nessuno snapshot trovato per {sel_ticker}.")
    st.stop()

latest = evo.iloc[-1]
first  = evo.iloc[0]
n_snap = len(evo)

st.subheader(f"📊 Evoluzione — {sel_ticker}")
st.caption(f"{n_snap} snapshot · dal {first['data_snapshot'].strftime('%Y-%m-%d')} al {latest['data_snapshot'].strftime('%Y-%m-%d')}")

# ── Header con metriche correnti vs prima snapshot ────────────────────────────
def delta_metric(label, val_now, val_first, fmt=".2f", pct_mult=1):
    now  = float(val_now  * pct_mult) if pd.notna(val_now)  else None
    prev = float(val_first * pct_mult) if pd.notna(val_first) else None
    delta = now - prev if now is not None and prev is not None else None
    val_str  = f"{now:{fmt}}" if now  is not None else "—"
    dlt_str  = f"{delta:+{fmt}}" if delta is not None else None
    return label, val_str, dlt_str

m1, m2, m3, m4, m5 = st.columns(5)
_, v, d = delta_metric("Prezzo ($)", latest.get("prezzo"), first.get("prezzo"), ".2f")
m1.metric("Prezzo", v, d)
_, v, d = delta_metric("Ret 12M", latest.get("ret_12m"), first.get("ret_12m"), ".1%", 100)
m2.metric("Ret 12M (%)", v, d)
_, v, d = delta_metric("P/E", latest.get("pe"), first.get("pe"), ".1f")
m3.metric("P/E", v, d)
_, v, d = delta_metric("ROE (%)", latest.get("roe"), first.get("roe"), ".1%", 100)
m4.metric("ROE", v, d)
_, v, d = delta_metric("D/E", latest.get("de_ratio"), first.get("de_ratio"), ".2f")
m5.metric("D/E", v, d)

# ── Grafico evoluzione prezzo ─────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📈 Prezzo", "📉 Metriche fondamentali", "📋 Tutti gli snapshot"])

with tab1:
    if evo["prezzo"].notna().sum() >= 2:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=evo["data_snapshot"], y=evo["prezzo"],
            mode="lines+markers",
            name="Prezzo",
            line=dict(color="#1a5276", width=2.5),
            marker=dict(size=7),
        ))
        # Zona colorata verde/rosso rispetto alla prima osservazione
        fig.add_hline(
            y=float(first["prezzo"]),
            line_dash="dash",
            line_color="#999",
            annotation_text=f"Inizio: ${float(first['prezzo']):.2f}",
        )
        fig.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f9f9f9",
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            yaxis=dict(title="Prezzo ($)", showgrid=True, gridcolor="#e0e0e0"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Servono almeno 2 snapshot con dati di prezzo per il grafico.")

with tab2:
    # Grafico multi-linea metriche fondamentali
    metrics_to_plot = {
        "Ret 12M (%)": "ret_12m",
        "ROE (%)":     "roe",
        "Vol Ann (%)": "vol_ann",
    }

    fig2 = go.Figure()
    colors = ["#1a5276", "#2d7a2d", "#b38600"]
    for i, (label, col) in enumerate(metrics_to_plot.items()):
        if col in evo.columns and evo[col].notna().sum() >= 2:
            y_vals = evo[col] * 100  # converti in %
            fig2.add_trace(go.Scatter(
                x=evo["data_snapshot"], y=y_vals,
                mode="lines+markers",
                name=label,
                line=dict(color=colors[i % len(colors)], width=2),
                marker=dict(size=6),
            ))

    if fig2.data:
        fig2.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f9f9f9",
            yaxis=dict(title="%", showgrid=True, gridcolor="#e0e0e0"),
            xaxis=dict(showgrid=True, gridcolor="#e0e0e0"),
            legend=dict(orientation="h"),
        )
        st.plotly_chart(fig2, use_container_width=True)

        # P/E e D/E su asse separato
        fig3 = go.Figure()
        for label, col, color in [("P/E", "pe", "#8e44ad"), ("D/E ratio", "de_ratio", "#c0392b")]:
            if col in evo.columns and evo[col].notna().sum() >= 2:
                fig3.add_trace(go.Scatter(
                    x=evo["data_snapshot"], y=evo[col],
                    mode="lines+markers",
                    name=label,
                    line=dict(color=color, width=2),
                    marker=dict(size=6),
                ))
        if fig3.data:
            fig3.update_layout(height=260, margin=dict(l=10, r=10, t=20, b=10),
                               paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="#f9f9f9",
                               legend=dict(orientation="h"))
            st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("Dati insufficienti per il grafico metriche.")

with tab3:
    # Tabella completa snapshot
    display_evo = evo.copy()
    for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe", "gross_margin", "div_yield"]:
        if pct_col in display_evo.columns:
            display_evo[pct_col] = pd.to_numeric(display_evo[pct_col], errors="coerce") * 100

    show_cols = [c for c in ["data_snapshot", "prezzo", "ret_6m", "ret_12m",
                              "vol_ann", "pe", "roe", "de_ratio", "div_yield",
                              "tier", "note", "fonte"] if c in display_evo.columns]

    st.dataframe(
        display_evo[show_cols].sort_values("data_snapshot", ascending=False),
        use_container_width=True,
        hide_index=True,
        column_config={
            "data_snapshot": st.column_config.DatetimeColumn("Data", format="YYYY-MM-DD HH:mm"),
            "prezzo": st.column_config.NumberColumn("Prezzo", format="$%.2f"),
            "ret_6m": st.column_config.NumberColumn("Ret 6M%", format="%.1f%%"),
            "ret_12m": st.column_config.NumberColumn("Ret 12M%", format="%.1f%%"),
            "vol_ann": st.column_config.NumberColumn("Vol%", format="%.1f%%"),
            "pe": st.column_config.NumberColumn("P/E", format="%.1f"),
            "roe": st.column_config.NumberColumn("ROE%", format="%.1f%%"),
            "de_ratio": st.column_config.NumberColumn("D/E", format="%.2f"),
            "div_yield": st.column_config.NumberColumn("Div%", format="%.2f%%"),
        },
    )

# ── Eliminazione ─────────────────────────────────────────────────────────────
st.divider()
with st.expander("🗑️ Rimuovi ticker dai Preferiti", expanded=False):
    st.warning(f"Questa operazione elimina **tutti gli snapshot storici** di {sel_ticker}. Irreversibile.")
    confirm = st.checkbox(f"Confermo la rimozione di tutti i dati di {sel_ticker}")
    if st.button("🗑️ Rimuovi definitivamente", key="btn_del_pref"):
        if not confirm:
            st.error("Spunta la casella di conferma prima di procedere.")
        else:
            with st.spinner("Eliminazione in corso..."):
                ok = delete_ticker_history(sel_ticker)
            if ok:
                st.success(f"✅ {sel_ticker} rimosso dai Preferiti.")
                st.session_state["preferiti_df"] = None
                st.rerun()
            else:
                st.error("Errore durante l'eliminazione.")

# ── Panoramica tutti i Preferiti ─────────────────────────────────────────────
st.divider()
st.subheader("📌 Panoramica tutti i Preferiti")

# Ultimo snapshot per ogni ticker
latest_all = (
    pref_df.sort_values("data_snapshot")
    .groupby("ticker")
    .last()
    .reset_index()
)

if not latest_all.empty:
    for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe", "div_yield"]:
        if pct_col in latest_all.columns:
            latest_all[pct_col] = pd.to_numeric(latest_all[pct_col], errors="coerce") * 100

    snap_counts = pref_df.groupby("ticker").size().reset_index(name="n_snapshot")
    latest_all = latest_all.merge(snap_counts, on="ticker", how="left")

    show_all = [c for c in ["ticker", "nome", "settore", "prezzo", "ret_12m",
                             "pe", "roe", "tier", "data_snapshot", "n_snapshot"]
                if c in latest_all.columns]
    st.dataframe(
        latest_all[show_all],
        use_container_width=True,
        hide_index=True,
        column_config={
            "prezzo":       st.column_config.NumberColumn("Prezzo", format="$%.2f"),
            "ret_12m":      st.column_config.NumberColumn("Ret 12M%", format="%.1f%%"),
            "pe":           st.column_config.NumberColumn("P/E", format="%.1f"),
            "roe":          st.column_config.NumberColumn("ROE%", format="%.1f%%"),
            "data_snapshot":st.column_config.DatetimeColumn("Ultimo snap", format="YYYY-MM-DD"),
            "n_snapshot":   st.column_config.NumberColumn("# Snapshot"),
        },
    )
