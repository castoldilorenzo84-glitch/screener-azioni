"""
Universe — Fase 1: Esplorazione larga del mercato
Dropdown Borsa → Indice → Scarica dati → Tabella colorata → Selezione tickers per Watchlist
"""

import streamlit as st
import pandas as pd
import numpy as np
import time
from utils.config import MERCATI, LABEL_RATING
from utils.data import get_tickers_for_index, fetch_universe_data
from utils.scoring import apply_universe_ratings, select_auto_top_n, compute_universe_score
from utils.settori import get_sector_momentum, build_sector_table, sector_status_label, sector_bonus


# ─── helpers UI ──────────────────────────────────────────────────────────────

def _fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:+.1%}"

def _fmt_num(v, dec=1):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{v:,.{dec}f}"

def _color_row(row):
    """Ritorna stile CSS per una riga basato sul rating."""
    mapping = {"verde": "#e8f8e8", "giallo": "#fffce0", "rosso": "#fde8e8"}
    bg = mapping.get(row.get("rating", ""), "")
    return [f"background-color: {bg}" for _ in row]

def _badge(rating: str) -> str:
    labels = {"verde": "🟢 Verde", "giallo": "🟡 Giallo", "rosso": "🔴 Rosso"}
    return labels.get(rating, "—")


# ─── pagina principale ───────────────────────────────────────────────────────

st.title("🌍 Universe — Esplorazione Mercato")
st.caption("Scegli borsa e indice, scarica i dati, seleziona i candidati da portare in Watchlist.")

# ── Pannello Momentum Settoriale ─────────────────────────────────────────────
with st.expander("📡 Momentum Settoriale (aggiornato ogni 4 ore)", expanded=False):
    with st.spinner("Caricamento momentum settori..."):
        sector_mom = get_sector_momentum()

    if sector_mom:
        df_sect = build_sector_table(sector_mom)
        st.caption("Rendimento degli ETF settoriali USA rispetto all'S&P 500 negli ultimi 3 mesi.")

        col_s1, col_s2, col_s3 = st.columns(3)
        favo  = [k for k,v in sector_mom.items() if v["status"] == "favorevole"]
        neutr = [k for k,v in sector_mom.items() if v["status"] == "neutro"]
        sfavo = [k for k,v in sector_mom.items() if v["status"] == "sfavorevole"]
        with col_s1:
            st.success(f"🟢 **Favorevoli ({len(favo)})**\n\n" + "\n\n".join(f"• {s}" for s in favo) if favo else "🟢 Nessuno")
        with col_s2:
            st.warning(f"🟡 **Neutri ({len(neutr)})**\n\n" + "\n\n".join(f"• {s}" for s in neutr) if neutr else "🟡 Nessuno")
        with col_s3:
            st.error(f"🔴 **Sfavorevoli ({len(sfavo)})**\n\n" + "\n\n".join(f"• {s}" for s in sfavo) if sfavo else "🔴 Nessuno")

        st.dataframe(
            df_sect,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Ret 3M":     st.column_config.NumberColumn("Ret 3M", format="%.1f%%"),
                "Vs S&P 500": st.column_config.NumberColumn("Vs S&P", format="%.1f%%"),
                "Ret 6M":     st.column_config.NumberColumn("Ret 6M", format="%.1f%%"),
            }
        )
        st.caption("💡 Il momentum settoriale viene applicato come bonus/malus (+10%/-10%) allo score Universe.")
    else:
        st.info("Dati settoriali non disponibili. Controlla la connessione.")

# ── Controlli selezione ──────────────────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])

with col1:
    borsa = st.selectbox(
        "🏦 Borsa / Paese",
        options=list(MERCATI.keys()),
        key="sel_borsa",
    )

with col2:
    indici_disponibili = MERCATI[borsa]["indici"]
    indice = st.selectbox(
        "📊 Indice azionario",
        options=indici_disponibili,
        key="sel_indice",
    )

with col3:
    st.write("")
    st.write("")
    carica_btn = st.button("⬇️ Scarica dati", type="primary", use_container_width=True)

# ── Legenda ──────────────────────────────────────────────────────────────────
with st.expander("ℹ️ Legenda pre-filtro", expanded=False):
    lcol1, lcol2, lcol3 = st.columns(3)
    with lcol1:
        st.success("**🟢 Verde** — Opportunità\n\nP/E 5–25 · ROE > 8% · D/E < 1.5 · Momentum 6M positivo · MktCap > $2B")
    with lcol2:
        st.warning("**🟡 Giallo** — Da valutare\n\nCriteri parzialmente soddisfatti. Richiede analisi aggiuntiva.")
    with lcol3:
        st.error("**🔴 Rosso** — Segnali negativi\n\nP/E negativo/> 50 · ROE < 0 · D/E > 3 · Crollo 12M > 30%")

# ── Caricamento dati ─────────────────────────────────────────────────────────
if carica_btn:
    st.session_state["universe_data"] = None
    st.session_state["universe_selection"] = []

    with st.spinner(f"Caricamento {indice} in corso..."):
        prog = st.progress(0, text="Recupero lista ticker...")

        def update_prog(pct, msg):
            prog.progress(pct, text=msg)

        # 1. Lista ticker
        tickers_df = get_tickers_for_index(indice)
        if tickers_df.empty:
            st.error("Impossibile recuperare la lista dei ticker. Verifica la connessione.")
            st.stop()

        update_prog(0.05, f"Trovati {len(tickers_df)} ticker. Download prezzi storici...")

        # 2. Fetch dati completi
        df = fetch_universe_data(tickers_df, progress_cb=update_prog)

        # 3. Applica rating
        df = apply_universe_ratings(df)

        # 4. Score per ranking + bonus settoriale
        df["__score"] = df.apply(compute_universe_score, axis=1)

        # Applica bonus/malus settoriale se disponibile
        if sector_mom:
            df["__score"] = df.apply(
                lambda row: row["__score"] + sector_bonus(
                    str(row.get("settore", "")), sector_mom
                ), axis=1
            )
            df["settore_status"] = df["settore"].apply(
                lambda s: next(
                    (sector_status_label(v["status"]) for k, v in sector_mom.items()
                     if k.lower() in str(s).lower() or str(s).lower() in k.lower()),
                    "⚪ N/D"
                )
            )
        else:
            df["settore_status"] = "⚪ N/D"

        df = df.sort_values("__score", ascending=False).reset_index(drop=True)

        prog.progress(1.0, "Completato!")
        time.sleep(0.3)
        prog.empty()

    st.session_state["universe_data"] = df
    total = len(df)
    verdi  = (df["rating"] == "verde").sum()
    gialli = (df["rating"] == "giallo").sum()
    rossi  = (df["rating"] == "rosso").sum()
    st.success(f"✅ **{total} ticker caricati** — 🟢 {verdi} Verdi  🟡 {gialli} Gialli  🔴 {rossi} Rossi")

# ── Tabella Universe ─────────────────────────────────────────────────────────
df: pd.DataFrame = st.session_state.get("universe_data")

if df is not None and not df.empty:

    # Filtri rapidi
    frow1, frow2, frow3, frow4 = st.columns([1, 1, 1, 1])
    with frow1:
        filter_rating = st.multiselect(
            "Filtra rating",
            options=["🟢 Verde", "🟡 Giallo", "🔴 Rosso"],
            default=["🟢 Verde", "🟡 Giallo"],
            key="filter_rating",
        )
    with frow2:
        filter_settore = st.multiselect(
            "Filtra settore",
            options=sorted(df["settore"].dropna().unique().tolist()),
            key="filter_settore",
        )
    with frow3:
        filter_mktcap = st.slider(
            "MktCap min ($M)",
            min_value=0, max_value=50000, value=0, step=500,
            key="filter_mktcap",
        )
    with frow4:
        search_ticker = st.text_input("🔍 Cerca ticker", key="search_ticker").upper().strip()

    # Applica filtri
    display_df = df.copy()
    rating_map_inv = {"🟢 Verde": "verde", "🟡 Giallo": "giallo", "🔴 Rosso": "rosso"}
    if filter_rating:
        allowed = [rating_map_inv[r] for r in filter_rating]
        display_df = display_df[display_df["rating"].isin(allowed)]
    if filter_settore:
        display_df = display_df[display_df["settore"].isin(filter_settore)]
    if filter_mktcap > 0:
        display_df = display_df[display_df["mktcap_M"].fillna(0) >= filter_mktcap]
    if search_ticker:
        display_df = display_df[
            display_df["ticker"].str.upper().str.contains(search_ticker) |
            display_df["nome"].str.upper().str.contains(search_ticker, na=False)
        ]

    st.caption(f"Visualizzati **{len(display_df)}** di {len(df)} ticker")

    # Checkbox selezione manuale
    display_df = display_df.copy()
    display_df.insert(0, "✅ Seleziona", False)

    # Prepara colonne formattate per display
    display_df["Rating"] = display_df["rating"].map(_badge)
    show_cols = ["✅ Seleziona", "ticker", "nome", "settore", "settore_status",
                 "mktcap_M", "prezzo", "ret_6m", "ret_12m",
                 "vol_ann", "pe", "roe", "de_ratio", "Rating"]
    # Rimuovi settore_status se non esiste
    show_cols = [c for c in show_cols if c in display_df.columns or c in ["✅ Seleziona", "Rating"]]

    col_config = {
        "✅ Seleziona":   st.column_config.CheckboxColumn("✅", width="small"),
        "ticker":         st.column_config.TextColumn("Ticker", width="small"),
        "nome":           st.column_config.TextColumn("Nome", width="medium"),
        "settore":        st.column_config.TextColumn("Settore", width="medium"),
        "settore_status": st.column_config.TextColumn("Trend Settore", width="small"),
        "mktcap_M":       st.column_config.NumberColumn("MktCap $M", format="$%,.0f", width="small"),
        "prezzo":         st.column_config.NumberColumn("Prezzo", format="$%.2f", width="small"),
        "ret_6m":         st.column_config.NumberColumn("Ret 6M", format="%.1f%%", width="small"),
        "ret_12m":        st.column_config.NumberColumn("Ret 12M", format="%.1f%%", width="small"),
        "vol_ann":        st.column_config.NumberColumn("Vol Ann", format="%.1f%%", width="small"),
        "pe":             st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
        "roe":            st.column_config.NumberColumn("ROE", format="%.1f%%", width="small"),
        "de_ratio":       st.column_config.NumberColumn("D/E", format="%.2f", width="small"),
        "Rating":         st.column_config.TextColumn("Rating", width="small"),
    }

    # Percentuali: converti per display
    for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe"]:
        if pct_col in display_df.columns:
            display_df[pct_col] = pd.to_numeric(display_df[pct_col], errors="coerce") * 100

    edited = st.data_editor(
        display_df[show_cols].reset_index(drop=True),
        column_config=col_config,
        use_container_width=True,
        height=500,
        hide_index=True,
        key="universe_table",
    )

    # ── Pulsanti di selezione ────────────────────────────────────────────────
    st.divider()
    st.subheader("📤 Trasferisci in Watchlist")

    btn_col1, btn_col2, btn_col3 = st.columns([2, 2, 3])

    with btn_col1:
        n_auto = st.number_input(
            "Max ticket selezione auto",
            min_value=5, max_value=50, value=20, step=5,
            key="n_auto",
            help="Limite consigliato: 20 per rispettare le 250 chiamate/giorno FMP"
        )
        btn_auto = st.button(
            "🤖 Selezione Automatica (Top N)",
            type="primary",
            use_container_width=True,
            help="Seleziona i migliori N: prima tutte le verdi, poi le gialle per score",
        )

    with btn_col2:
        st.write("")
        btn_manuale = st.button(
            "☑️ Trasferisci Selezionati",
            use_container_width=True,
            help="Trasferisci i ticker che hai flaggato manualmente con la checkbox",
        )

    with btn_col3:
        current_wl = st.session_state.get("watchlist_tickers", [])
        if current_wl:
            st.info(f"📋 Watchlist attuale: **{len(current_wl)} ticker** — {', '.join(current_wl[:8])}{'...' if len(current_wl) > 8 else ''}")
        else:
            st.info("📋 Watchlist vuota. Aggiungi ticker con i pulsanti a sinistra.")

    # ── Azione: selezione automatica ─────────────────────────────────────────
    if btn_auto:
        auto_tickers = select_auto_top_n(df, n=int(n_auto))
        existing = st.session_state["watchlist_tickers"]
        new_tickers = [t for t in auto_tickers if t not in existing]
        st.session_state["watchlist_tickers"] = existing + new_tickers
        st.session_state["watchlist_data"] = None  # forza refresh
        st.success(f"✅ **{len(auto_tickers)} ticker** aggiunti alla Watchlist ({len(new_tickers)} nuovi).")
        st.rerun()

    # ── Azione: selezione manuale ─────────────────────────────────────────────
    if btn_manuale:
        selected_rows = edited[edited["✅ Seleziona"] == True]
        if selected_rows.empty:
            st.warning("Nessun ticker selezionato. Usa le checkbox nella tabella.")
        else:
            selected_tickers = selected_rows["ticker"].tolist()
            existing = st.session_state["watchlist_tickers"]
            new_tickers = [t for t in selected_tickers if t not in existing]
            st.session_state["watchlist_tickers"] = existing + new_tickers
            st.session_state["watchlist_data"] = None
            st.success(f"✅ **{len(selected_tickers)} ticker** trasferiti ({len(new_tickers)} nuovi).")
            st.rerun()

    # ── Mini statistiche ─────────────────────────────────────────────────────
    with st.expander("📊 Statistiche indice", expanded=False):
        s1, s2, s3, s4, s5 = st.columns(5)
        with s1:
            st.metric("Ticker totali", len(df))
        with s2:
            st.metric("🟢 Verde", (df["rating"] == "verde").sum())
        with s3:
            st.metric("🟡 Giallo", (df["rating"] == "giallo").sum())
        with s4:
            st.metric("🔴 Rosso", (df["rating"] == "rosso").sum())
        with s5:
            avg_ret = df["ret_12m"].mean()
            st.metric("Ret 12M medio", f"{avg_ret*100:+.1f}%" if pd.notna(avg_ret) else "—")

else:
    # Placeholder prima del caricamento
    st.info("👆 Seleziona una borsa e un indice, poi premi **Scarica dati** per iniziare.")
    st.markdown("""
    **Come funziona Universe:**
    1. Scegli la borsa e l'indice di riferimento
    2. Premi **Scarica dati** — l'app recupera i dati di tutto l'indice
    3. Ogni azione viene colorata 🟢🟡🔴 in base ai criteri di pre-filtro
    4. Usa **Selezione Automatica** per mandare i migliori 20 in Watchlist
    5. Oppure usa le checkbox per selezionare manualmente
    """)
