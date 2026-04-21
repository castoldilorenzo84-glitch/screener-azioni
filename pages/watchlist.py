"""
Watchlist — Fase 2: Analisi dettagliata con scoring multi-fattoriale
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.data import fetch_watchlist_all
from utils.scoring import compute_watchlist_scores
from utils.storage import save_snapshot, gdrive_available


def _tier_badge(tier: str) -> str:
    mapping = {"Alta": "🟢 Alta", "Media": "🟡 Media", "Bassa": "🔴 Bassa"}
    return mapping.get(tier, tier)


def _weight_desc(key: str) -> str:
    desc = {
        "mom_6m":  "Momentum 6 mesi",
        "mom_12m": "Momentum 12 mesi",
        "roe":     "Return on Equity",
        "de_inv":  "Debt/Equity inverso (meno debito = meglio)",
        "margin":  "Gross Margin",
        "lowvol":  "Bassa volatilità (inverso)",
        "pe_inv":  "P/E inverso (non troppo caro)",
        "div_yld": "Dividend Yield",
    }
    return desc.get(key, key)


st.title("📋 Watchlist — Analisi Dettagliata")
st.caption("Scoring multi-fattoriale (z-score) su 8 fattori. Aggiorna i dati prima di analizzare.")

# ── Gestione ticker ──────────────────────────────────────────────────────────
wl = st.session_state.get("watchlist_tickers", [])

with st.expander("✏️ Gestisci Watchlist", expanded=(len(wl) == 0)):
    add_col, del_col = st.columns([3, 2])
    with add_col:
        new_ticker = st.text_input(
            "Aggiungi ticker manualmente",
            placeholder="Es. AAPL, MSFT, ENI.MI",
            key="add_ticker_input",
        ).upper().strip()
        if st.button("➕ Aggiungi", key="btn_add"):
            tokens = [t.strip() for t in new_ticker.replace(",", " ").split() if t.strip()]
            added = []
            for t in tokens:
                if t and t not in wl:
                    wl.append(t)
                    added.append(t)
            st.session_state["watchlist_tickers"] = wl
            st.session_state["watchlist_data"] = None
            if added:
                st.success(f"Aggiunto: {', '.join(added)}")

    with del_col:
        if wl:
            to_remove = st.multiselect("Rimuovi ticker", options=wl, key="remove_tickers")
            if st.button("🗑️ Rimuovi selezionati", key="btn_remove"):
                st.session_state["watchlist_tickers"] = [t for t in wl if t not in to_remove]
                st.session_state["watchlist_data"] = None
                st.rerun()

    if wl:
        st.write(f"**Ticker attuali ({len(wl)}):** " + " · ".join(f"`{t}`" for t in wl))

# ── Pulsante aggiornamento dati ───────────────────────────────────────────────
wl = st.session_state.get("watchlist_tickers", [])

if not wl:
    st.warning("Watchlist vuota. Aggiungi ticker manualmente o usali da Universe → Selezione.")
    st.stop()

col_upd, col_info = st.columns([2, 3])
with col_upd:
    btn_update = st.button("🔄 Aggiorna Tutti i Dati", type="primary", use_container_width=True)

with col_info:
    key_ok = bool(st.secrets.get("FMP_API_KEY", "")) if hasattr(st, "secrets") else False
    if key_ok:
        st.info("📡 Fonte: Financial Modeling Prep (dati dettagliati)")
    else:
        st.warning("⚠️ FMP API Key non configurata — uso yfinance come fallback (dati meno completi)")

# ── Fetch dati ────────────────────────────────────────────────────────────────
if btn_update:
    prog = st.progress(0, text="Avvio aggiornamento...")

    def prog_cb(pct, msg):
        prog.progress(pct, text=msg)

    df_raw = fetch_watchlist_all(wl, progress_cb=prog_cb)
    prog.empty()

    if df_raw.empty:
        st.error("Nessun dato recuperato. Controlla la connessione.")
        st.stop()

    df_scored = compute_watchlist_scores(df_raw)
    st.session_state["watchlist_data"] = df_scored
    st.session_state["last_update"] = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M")
    st.success(f"✅ Dati aggiornati per {len(df_scored)} ticker")

# ── Tabella scoring ───────────────────────────────────────────────────────────
df: pd.DataFrame = st.session_state.get("watchlist_data")

if df is not None and not df.empty:
    last_upd = st.session_state.get("last_update", "—")
    st.caption(f"Ultimo aggiornamento: {last_upd}")

    # Prepara visualizzazione
    display = df.reset_index().copy()

    # Formatta percentuali
    for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe", "gross_margin", "div_yield"]:
        if pct_col in display.columns:
            display[pct_col] = pd.to_numeric(display[pct_col], errors="coerce") * 100

    display["tier_badge"] = display["tier"].map(_tier_badge)

    show_cols = ["rank", "ticker", "nome", "settore", "mktcap_M",
                 "prezzo", "fv_quick", "fv_discount",
                 "ret_6m", "ret_12m", "vol_ann",
                 "pe", "roe", "gross_margin", "de_ratio", "div_yield",
                 "score", "percentile", "tier_badge", "sharpe", "sortino"]

    # Colonne disponibili
    show_cols = [c for c in show_cols if c in display.columns]

    col_config = {
        "rank":         st.column_config.NumberColumn("Rank", width="small"),
        "ticker":       st.column_config.TextColumn("Ticker", width="small"),
        "nome":         st.column_config.TextColumn("Nome", width="medium"),
        "settore":      st.column_config.TextColumn("Settore", width="medium"),
        "mktcap_M":     st.column_config.NumberColumn("MktCap $M", format="$%,.0f", width="small"),
        "prezzo":       st.column_config.NumberColumn("Prezzo", format="$%.2f", width="small"),
        "fv_quick":     st.column_config.NumberColumn("Fair Value", format="$%.2f", width="small",
                            help="Fair Value rapido basato su P/E × media settore"),
        "fv_discount":  st.column_config.NumberColumn("FV Disc%", format="%.1f%%", width="small",
                            help="+% = sottostimato vs Fair Value. -% = sovrastimato"),
        "ret_6m":       st.column_config.NumberColumn("Ret 6M%", format="%.1f%%", width="small"),
        "ret_12m":      st.column_config.NumberColumn("Ret 12M%", format="%.1f%%", width="small"),
        "vol_ann":      st.column_config.NumberColumn("Vol%", format="%.1f%%", width="small"),
        "pe":           st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
        "roe":          st.column_config.NumberColumn("ROE%", format="%.1f%%", width="small"),
        "gross_margin": st.column_config.NumberColumn("Margin%", format="%.1f%%", width="small"),
        "de_ratio":     st.column_config.NumberColumn("D/E", format="%.2f", width="small"),
        "div_yield":    st.column_config.NumberColumn("Div%", format="%.2f%%", width="small"),
        "score":        st.column_config.NumberColumn("Score", format="%.3f", width="small"),
        "percentile":   st.column_config.ProgressColumn("Percentile", min_value=0, max_value=100, width="small"),
        "tier_badge":   st.column_config.TextColumn("Tier", width="small"),
        "sharpe":       st.column_config.NumberColumn("Sharpe", format="%.2f", width="small",
                            help="(Ret12M - 4.5%) / Vol. >1=buono, >2=ottimo"),
        "sortino":      st.column_config.NumberColumn("Sortino", format="%.2f", width="small",
                            help="Come Sharpe ma penalizza solo la volatilità negativa"),
    }

    st.dataframe(
        display.sort_values("rank")[show_cols],
        column_config=col_config,
        use_container_width=True,
        height=420,
        hide_index=True,
    )

    # ── Z-scores breakdown ────────────────────────────────────────────────────
    with st.expander("🔬 Dettaglio Z-scores", expanded=False):
        z_cols = [c for c in ["ticker", "z_mom6m", "z_mom12m", "z_roe", "z_de",
                               "z_margin", "z_lowvol", "z_pe", "z_div", "score"] if c in display.columns]
        z_cfg = {c: st.column_config.NumberColumn(c, format="%.3f") for c in z_cols if c != "ticker"}
        st.dataframe(display.sort_values("rank")[z_cols], column_config=z_cfg,
                     use_container_width=True, height=350, hide_index=True)

    # ── Salva in Preferiti ─────────────────────────────────────────────────────
    st.divider()
    st.subheader("⭐ Salva in Preferiti")

    if not gdrive_available():
        st.warning("Google Sheets non configurato. Configura le credenziali nel file secrets.toml per usare i Preferiti.")
    else:
        pref_col1, pref_col2 = st.columns([3, 2])
        with pref_col1:
            save_selection = st.multiselect(
                "Scegli ticker da salvare",
                options=display["ticker"].tolist(),
                key="save_pref_selection",
            )
            note_pref = st.text_input("Note (opzionale)", key="note_preferiti")
        with pref_col2:
            st.write("")
            st.write("")
            if st.button("💾 Salva Snapshot in Preferiti", use_container_width=True):
                if not save_selection:
                    st.warning("Seleziona almeno un ticker.")
                else:
                    saved = 0
                    for ticker in save_selection:
                        row = display[display["ticker"] == ticker].iloc[0].to_dict()
                        # Converti percentuali al formato decimale
                        for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe", "gross_margin", "div_yield"]:
                            if pct_col in row and row[pct_col] is not None:
                                try:
                                    row[pct_col] = float(row[pct_col]) / 100
                                except Exception:
                                    pass
                        ok = save_snapshot(row, note=note_pref, fonte="watchlist")
                        if ok:
                            saved += 1
                    st.success(f"✅ {saved} snapshot salvati nei Preferiti.")

    # ── Pesi modello ────────────────────────────────────────────────────────────
    with st.expander("⚙️ Pesi modello di scoring", expanded=False):
        from utils.config import SCORING_WEIGHTS
        weights_data = [
            {"Fattore": k, "Peso": f"{v*100:.0f}%", "Descrizione": _weight_desc(k)}
            for k, v in SCORING_WEIGHTS.items()
        ]
        st.table(pd.DataFrame(weights_data))
        st.caption("Per modificare i pesi, aggiorna `utils/config.py → SCORING_WEIGHTS`")

else:
    st.info("Premi **Aggiorna Tutti i Dati** per caricare i dati della watchlist e calcolare lo scoring.")
