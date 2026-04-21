"""
Diamond Hunter — Ricerca dei Diamanti Grezzi

Algoritmo opposto all'Universe classico:
NON cerca chi sta già performando bene.
CERCA chi è fermo ma sta per muoversi:
  - Lateralità recente (basso momentum MA non in calo)
  - Sottostima fondamentale (prezzo < fair value)
  - Fondamentali solidi ma non ancora prezzati
  - Mid cap poco seguite
  - Compressione della volatilità (spesso precede un'esplosione direzionale)
  - Volume in accumulo
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import time
import yfinance as yf

from utils.config import MERCATI, TICKER_MAP
from utils.data import get_tickers_for_index, fetch_universe_data
from utils.scoring import _calc_fv_quick, _calc_fv_discount, _PE_SETTORE

# ── Costanti Diamond Score ────────────────────────────────────
MKTCAP_MAX_M   = 30_000   # Focus mid cap: sotto 30B
MKTCAP_MIN_M   = 500      # Esclude micro cap senza dati
MOM_MAX_6M     = 0.25     # Momentum 6M max: esclude chi è già esploso (+25%)
MOM_MIN_6M     = -0.20    # Momentum 6M min: esclude chi sta crollando (-20%)
FV_DISC_MIN    = 0.05     # Sottostima minima richiesta: almeno +5% vs fair value
VOL_COMPRESS   = 0.35     # Soglia compressione vol: vol annua < 35% per bonus


def _safe(v):
    try:
        f = float(v)
        return None if f != f else f
    except (TypeError, ValueError):
        return None


def calc_diamond_score(row: pd.Series) -> float:
    """
    Calcola il Diamond Score — punteggio per i diamanti grezzi.

    Logica opposta all'Universe:
    - Momentum basso MA positivo: +punti (lateralità, non crollo)
    - Sottostima FV: +punti (più è sottostimato, meglio)
    - Qualità fondamentali: +punti (ROE, margine, basso debito)
    - Compressione volatilità: +punti (spesso precede il movimento)
    - Mid cap: +punti (più possibilità di scoperta)
    - Momentum alto: MALUS (già scoperta dal mercato)
    - In calo forte: MALUS (non è lateralità, è debolezza)
    """
    score = 0.0

    ret_6m   = _safe(row.get("ret_6m"))
    ret_12m  = _safe(row.get("ret_12m"))
    vol_ann  = _safe(row.get("vol_ann"))
    pe       = _safe(row.get("pe"))
    roe      = _safe(row.get("roe"))
    de       = _safe(row.get("de_ratio"))
    margin   = _safe(row.get("gross_margin"))
    mktcap   = _safe(row.get("mktcap_M"))
    prezzo   = _safe(row.get("prezzo"))
    div      = _safe(row.get("div_yield"))

    fv       = _safe(row.get("fv_quick"))
    fv_disc  = _safe(row.get("fv_discount"))

    # ── 1. Lateralità (35% del punteggio) ────────────────────
    # Momentum basso ma non negativo = lateralità
    if ret_6m is not None:
        if 0.0 <= ret_6m <= 0.10:
            # Zona ideale: tra 0 e +10% → massimo punteggio
            score += 35 * (1 - abs(ret_6m - 0.05) / 0.10)
        elif 0.10 < ret_6m <= 0.25:
            # Sta iniziando a muoversi ma non è esploso: ancora interessante
            score += 20 * (1 - (ret_6m - 0.10) / 0.15)
        elif -0.10 <= ret_6m < 0.0:
            # Leggera correzione: potenziale di rimbalzo
            score += 15 * (1 - abs(ret_6m) / 0.10)
        elif ret_6m < -0.10:
            # In calo: penalizza
            score -= 15

    # ── 2. Sottostima Fair Value (30% del punteggio) ──────────
    if fv_disc is not None:
        if fv_disc >= 0.30:
            # Sottostimato > 30%: massimo bonus
            score += 30
        elif fv_disc >= 0.15:
            # Sottostimato 15-30%
            score += 20 + (fv_disc - 0.15) / 0.15 * 10
        elif fv_disc >= 0.05:
            # Sottostimato 5-15%
            score += 10 + (fv_disc - 0.05) / 0.10 * 10
        elif fv_disc < -0.20:
            # Sovrastimato > 20%: malus
            score -= 10

    # ── 3. Qualità fondamentali (20% del punteggio) ───────────
    if roe is not None and roe > 0:
        score += min(10, roe * 40)   # ROE 25% → +10 punti
    if margin is not None and margin > 0:
        score += min(5, margin * 20)   # Margin 25% → +5 punti
    if de is not None:
        if de < 0.5:
            score += 5
        elif de > 2.0:
            score -= 5

    # ── 4. Compressione volatilità (10% del punteggio) ────────
    if vol_ann is not None:
        if vol_ann < 0.20:
            score += 10   # Molto bassa: tipica di titoli prima di un movimento
        elif vol_ann < 0.30:
            score += 7
        elif vol_ann < 0.40:
            score += 3
        elif vol_ann > 0.60:
            score -= 5

    # ── 5. Bonus Mid Cap ─────────────────────────────────────
    if mktcap is not None:
        if 1_000 <= mktcap <= 10_000:
            score += 5   # Mid cap ideale
        elif 500 <= mktcap < 1_000:
            score += 3   # Small mid
        elif mktcap > 50_000:
            score -= 5   # Mega cap: già largamente coperta dagli analisti

    # ── 6. Dividend yield come segnale di stabilità ───────────
    if div is not None and 0.01 <= div <= 0.06:
        score += 3   # Dividendo moderato: azienda matura ma non stagnante

    return round(score, 2)


def check_laterality(ret_6m, ret_12m, vol_ann) -> str:
    """Classifica il pattern di prezzo del ticker."""
    r6  = _safe(ret_6m)
    r12 = _safe(ret_12m)
    v   = _safe(vol_ann)

    if r6 is None:
        return "⚪ N/D"

    if r6 is not None and -0.05 <= r6 <= 0.12 and v is not None and v < 0.35:
        return "🔶 Laterale"
    elif r6 is not None and r6 > 0.25:
        return "🚀 In trend"
    elif r6 is not None and r6 < -0.15:
        return "📉 In calo"
    elif r6 is not None and 0.12 < r6 <= 0.25:
        return "📈 In rialzo"
    else:
        return "🟡 Misto"


def valutazione_fv(fv_disc) -> str:
    d = _safe(fv_disc)
    if d is None:         return "⚪ N/D"
    if d >= 0.20:         return "🟢 Sotto -20%"
    if d >= 0.08:         return "🟡 Sotto -8%"
    if d >= -0.08:        return "⚖️ Corretto"
    return "🔴 Sopra"


# ══════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════

st.title("💎 Diamond Hunter — Ricerca Diamanti Grezzi")
st.caption(
    "Algoritmo alternativo che cerca aziende in lateralità con fondamentali solidi "
    "e prezzo sotto il fair value — non chi sta già volando."
)

# ── Info metodologia ──────────────────────────────────────────
with st.expander("ℹ️ Come funziona il Diamond Score — differenze dall'Universe", expanded=False):
    st.markdown("""
    **Universe classico** cerca chi sta già performando bene: premia momentum alto,
    volatilità controllata, fondamentali solidi. Tende a trovare le stesse grandi
    aziende già seguite da tutti gli analisti.

    **Diamond Hunter** usa la logica opposta:

    | Fattore | Universe | Diamond Hunter |
    |---------|----------|----------------|
    | Momentum 6M alto (+30%) | ✅ Bonus | ❌ Malus — già scoperta |
    | Momentum 6M basso (0-10%) | ⚠️ Neutro | ✅ Bonus — lateralità |
    | Prezzo < Fair Value | ⚠️ Lieve bonus | ✅ Bonus forte (30% peso) |
    | Mid cap (2-15B) | ⚠️ Neutro | ✅ Bonus |
    | Mega cap (>50B) | ✅ Bonus (liquidità) | ❌ Malus (già prezzata) |
    | Bassa volatilità | ✅ Bonus | ✅ Bonus (compressione) |

    **Diamond Score** va da 0 a 100. Sopra 50 = candidato interessante.
    """)

# ── Selezione indice ──────────────────────────────────────────
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    borsa = st.selectbox("🏦 Borsa", options=list(MERCATI.keys()), key="dh_borsa")
with col2:
    indici = MERCATI[borsa]["indici"]
    indice = st.selectbox("📊 Indice", options=indici, key="dh_indice")
with col3:
    st.write("")
    st.write("")
    btn = st.button("🔍 Cerca Diamanti", type="primary", use_container_width=True)

# Avviso per indici grandi
if "Russell" in indice:
    st.warning("⚠️ Russell 2000 contiene 200 ticker — l'analisi richiede 3-5 minuti. Considera di usare S&P 500 o Dow Jones per una ricerca più rapida.")

# ── Filtri avanzati ───────────────────────────────────────────
with st.expander("⚙️ Filtri avanzati", expanded=False):
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        filt_mcap_max = st.number_input(
            "MktCap max ($M)", value=30000, min_value=500, step=1000, key="dh_mcap"
        )
    with fc2:
        filt_mom_max = st.slider(
            "Momentum 6M max (%)", min_value=5, max_value=50, value=25,
            key="dh_mom_max"
        )
    with fc3:
        filt_fv_min = st.slider(
            "Sottostima FV min (%)", min_value=0, max_value=40, value=5,
            key="dh_fv_min"
        )
    with fc4:
        filt_top_n = st.number_input(
            "Top N risultati", value=15, min_value=5, max_value=50,
            step=5, key="dh_topn"
        )

# ── Analisi ───────────────────────────────────────────────────
if btn:
    with st.spinner(f"Scarico dati {indice}..."):
        tickers_df = get_tickers_for_index(indice)

    if tickers_df.empty:
        st.error("Impossibile recuperare i ticker. Verifica la connessione.")
        st.stop()

    prog = st.progress(0, text="Download dati universo...")

    def prog_cb(pct, msg):
        prog.progress(pct, text=msg)

    with st.spinner("Analisi in corso..."):
        df = fetch_universe_data(tickers_df, progress_cb=prog_cb)

    if df.empty:
        st.error("Nessun dato disponibile.")
        st.stop()

    prog.empty()

    # Calcola FV rapido
    df["fv_quick"]    = df.apply(_calc_fv_quick, axis=1)
    df["fv_discount"] = df.apply(
        lambda r: _calc_fv_discount(r.get("prezzo"), r.get("fv_quick")), axis=1
    )

    # Converti percentuali per confronto
    for col in ["ret_6m", "ret_12m", "vol_ann", "roe", "gross_margin", "div_yield"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Applica pre-filtri
    mask = pd.Series([True] * len(df), index=df.index)

    # Esclude mktcap troppo alta
    if "mktcap_M" in df.columns:
        mcap_ok = pd.to_numeric(df["mktcap_M"], errors="coerce").fillna(0)
        mask &= (mcap_ok <= filt_mcap_max) & (mcap_ok >= MKTCAP_MIN_M)

    # Esclude momentum troppo alto (già scoperta)
    if "ret_6m" in df.columns:
        mom_ok = pd.to_numeric(df["ret_6m"], errors="coerce").fillna(0)
        mask &= mom_ok <= (filt_mom_max / 100)

    # Esclude forti cali (non sono lateralità, sono debolezza)
    if "ret_6m" in df.columns:
        mask &= mom_ok >= -0.25

    # Richiede sottostima minima
    if filt_fv_min > 0:
        fv_ok = pd.to_numeric(df["fv_discount"], errors="coerce").fillna(-1)
        mask &= fv_ok >= (filt_fv_min / 100)

    df_filtered = df[mask].copy()

    if df_filtered.empty:
        st.warning("Nessun ticker soddisfa i criteri. Prova ad allargare i filtri.")
        st.stop()

    # Calcola Diamond Score
    df_filtered["diamond_score"] = df_filtered.apply(calc_diamond_score, axis=1)
    df_filtered["pattern"]       = df_filtered.apply(
        lambda r: check_laterality(r.get("ret_6m"), r.get("ret_12m"), r.get("vol_ann")), axis=1
    )
    df_filtered["valutazione_fv"] = df_filtered["fv_discount"].apply(valutazione_fv)

    # Top N
    top = df_filtered.nlargest(int(filt_top_n), "diamond_score").reset_index(drop=True)
    top.index = top.index + 1

    st.session_state["diamond_data"] = top
    st.success(
        f"✅ Analisi completata su {len(df_filtered)} ticker filtrati da {len(df)} totali. "
        f"Mostro i Top {len(top)} Diamond."
    )

# ── Risultati ─────────────────────────────────────────────────
df_res: pd.DataFrame = st.session_state.get("diamond_data")

if df_res is not None and not df_res.empty:

    # ── Grafico scatter: FV Discount vs Lateralità ────────────
    st.subheader("🗺️ Mappa dei Diamanti")
    st.caption(
        "Asse X: Momentum 6M (lateralità). "
        "Asse Y: Sottostima rispetto al Fair Value. "
        "Zona ideale: X vicino a 0, Y alto. Dimensione = Diamond Score."
    )

    fig = go.Figure()

    for _, row in df_res.iterrows():
        x  = (row.get("ret_6m") or 0) * 100
        y  = (row.get("fv_discount") or 0) * 100
        ds = row.get("diamond_score", 0)
        tk = str(row.get("ticker", ""))
        color = "#2d7a2d" if ds >= 60 else ("#b38600" if ds >= 40 else "#c0392b")

        fig.add_trace(go.Scatter(
            x=[x], y=[y],
            mode="markers+text",
            text=[tk],
            textposition="top center",
            textfont=dict(size=9),
            marker=dict(
                size=max(10, ds / 3),
                color=color,
                opacity=0.75,
                line=dict(width=1, color="white"),
            ),
            name=tk,
            showlegend=False,
            hovertemplate=(
                f"<b>{tk}</b><br>"
                f"Diamond Score: {ds:.0f}<br>"
                f"Momentum 6M: {x:+.1f}%<br>"
                f"FV Discount: {y:+.1f}%<br>"
                f"Pattern: {row.get('pattern','')}"
                "<extra></extra>"
            ),
        ))

    # Zona ideale
    fig.add_shape(type="rect", x0=-5, x1=15, y0=10, y1=50,
                  fillcolor="rgba(45,122,45,0.08)",
                  line=dict(color="#2d7a2d", dash="dot", width=1))
    fig.add_annotation(x=5, y=48, text="🎯 Zona Diamanti",
                       showarrow=False, font=dict(color="#2d7a2d", size=11))

    fig.add_vline(x=0, line_dash="dash", line_color="#999", line_width=1)
    fig.add_hline(y=0, line_dash="dash", line_color="#999", line_width=1)

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9f9f9",
        xaxis=dict(title="Momentum 6M (%)", showgrid=True, gridcolor="#e0e0e0",
                   zeroline=True, zerolinecolor="#aaa"),
        yaxis=dict(title="Sottostima FV (%)", showgrid=True, gridcolor="#e0e0e0",
                   zeroline=True, zerolinecolor="#aaa"),
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabella risultati ─────────────────────────────────────
    st.subheader(f"💎 Top {len(df_res)} Diamanti Grezzi")

    disp = df_res.copy()
    for pct_col in ["ret_6m", "ret_12m", "vol_ann", "roe", "gross_margin", "div_yield"]:
        if pct_col in disp.columns:
            disp[pct_col] = pd.to_numeric(disp[pct_col], errors="coerce") * 100
    if "fv_discount" in disp.columns:
        disp["fv_discount"] = pd.to_numeric(disp["fv_discount"], errors="coerce") * 100

    cols_show = [c for c in [
        "diamond_score", "ticker", "nome", "settore",
        "pattern", "valutazione_fv",
        "mktcap_M", "prezzo", "fv_quick", "fv_discount",
        "ret_6m", "ret_12m", "vol_ann",
        "pe", "roe", "de_ratio", "gross_margin",
    ] if c in disp.columns]

    st.dataframe(
        disp[cols_show],
        use_container_width=True,
        hide_index=False,
        column_config={
            "diamond_score": st.column_config.ProgressColumn(
                "💎 Score", min_value=0, max_value=100, width="small"
            ),
            "ticker":        st.column_config.TextColumn("Ticker", width="small"),
            "nome":          st.column_config.TextColumn("Nome", width="medium"),
            "settore":       st.column_config.TextColumn("Settore", width="medium"),
            "pattern":       st.column_config.TextColumn("Pattern", width="small"),
            "valutazione_fv":st.column_config.TextColumn("Val. FV", width="small"),
            "mktcap_M":      st.column_config.NumberColumn("MktCap $M", format="$%,.0f", width="small"),
            "prezzo":        st.column_config.NumberColumn("Prezzo", format="$%.2f", width="small"),
            "fv_quick":      st.column_config.NumberColumn("Fair Value", format="$%.2f", width="small"),
            "fv_discount":   st.column_config.NumberColumn("FV Disc%", format="%+.1f%%", width="small"),
            "ret_6m":        st.column_config.NumberColumn("Ret 6M%", format="%+.1f%%", width="small"),
            "ret_12m":       st.column_config.NumberColumn("Ret 12M%", format="%+.1f%%", width="small"),
            "vol_ann":       st.column_config.NumberColumn("Vol%", format="%.1f%%", width="small"),
            "pe":            st.column_config.NumberColumn("P/E", format="%.1f", width="small"),
            "roe":           st.column_config.NumberColumn("ROE%", format="%.1f%%", width="small"),
            "de_ratio":      st.column_config.NumberColumn("D/E", format="%.2f", width="small"),
            "gross_margin":  st.column_config.NumberColumn("Margin%", format="%.1f%%", width="small"),
        }
    )

    # ── Aggiungi a Watchlist ──────────────────────────────────
    st.divider()
    st.subheader("➕ Aggiungi alla Watchlist")
    st.caption(
        "Seleziona i diamanti che vuoi approfondire. "
        "Verranno aggiunti alla Watchlist per l'analisi completa con lo scoring z-score."
    )

    col_a, col_b = st.columns([3, 2])
    with col_a:
        tickers_disponibili = df_res["ticker"].dropna().tolist()
        sel = st.multiselect(
            "Seleziona ticker",
            options=tickers_disponibili,
            key="dh_sel_wl",
        )
    with col_b:
        st.write("")
        if st.button("📋 Aggiungi alla Watchlist", use_container_width=True, key="dh_add_wl"):
            if sel:
                wl_esistente = list(st.session_state.get("watchlist_tickers", []))
                nuovi = [t for t in sel if t not in wl_esistente]
                st.session_state["watchlist_tickers"] = wl_esistente + nuovi
                if nuovi:
                    st.success(f"✅ Aggiunti {len(nuovi)} ticker alla Watchlist: {', '.join(nuovi)}")
                else:
                    st.info("I ticker selezionati sono già in Watchlist.")
            else:
                st.warning("Seleziona almeno un ticker.")

    # ── Legenda Diamond Score ─────────────────────────────────
    st.divider()
    st.subheader("📖 Interpretazione Diamond Score")
    col_l1, col_l2, col_l3, col_l4 = st.columns(4)
    col_l1.success("**70-100** 💎💎💎\nDiamante di alta qualità. Pattern ideale: laterale + fortemente sottostimato + fondamentali ottimi.")
    col_l2.warning("**50-70** 💎💎\nBuon candidato. Soddisfa la maggior parte dei criteri. Approfondire in Watchlist e Price Targets.")
    col_l3.info("**30-50** 💎\nCandidato potenziale. Uno o più criteri parzialmente soddisfatti. Monitorare nei Preferiti.")
    col_l4.error("**0-30** ⚠️\nCriteri insufficienti. Incluso per completezza ma non prioritario.")

    st.warning("""
    ⚠️ Il Diamond Score è un filtro esplorativo, non una raccomandazione di acquisto.
    Un alto Diamond Score significa che l'azienda ha caratteristiche tipiche dei titoli
    che si apprezzano nel medio periodo PRIMA che vengano scoperte dal mercato.
    Richiede sempre verifica manuale e analisi approfondita in Watchlist e Price Targets.
    """)

else:
    st.info(
        "Seleziona una borsa e un indice, poi premi **Cerca Diamanti** per avviare l'analisi.\n\n"
        "💡 **Suggerimento:** Per trovare i migliori diamanti grezzi, prova con "
        "**Euronext Milan** o **FTSE MIB** — il mercato italiano è meno coperto dagli analisti "
        "e tende ad avere più inefficienze di prezzo rispetto all'S&P 500."
    )
