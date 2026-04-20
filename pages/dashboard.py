"""
Dashboard — Top 5 ranking con card metriche e grafico score
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px


TIER_COLOR = {"Alta": "#2d7a2d", "Media": "#b38600", "Bassa": "#c0392b"}
TIER_BG    = {"Alta": "#d5f5e3", "Media": "#fef9e7", "Bassa": "#fadbd8"}


def fmt_pct(v):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{float(v)*100:+.1f}%"

def fmt_num(v, dec=1, prefix=""):
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return "—"
    return f"{prefix}{float(v):,.{dec}f}"


st.title("🏆 Dashboard — Top 5")
st.caption("I 5 ticker con il punteggio composito più alto nella Watchlist corrente.")

df: pd.DataFrame = st.session_state.get("watchlist_data")

if df is None or df.empty:
    st.info("🔄 Nessun dato disponibile. Vai in **Watchlist**, carica i ticker e premi **Aggiorna Tutti i Dati**.")
    st.stop()

# Prep
display = df.reset_index().copy() if "ticker" not in df.columns else df.copy()
display = display.sort_values("rank").head(5)

# ── Grafico a barre score Top 5 ──────────────────────────────────────────────
st.subheader("📊 Score Composito")
fig_bar = px.bar(
    display.sort_values("score"),
    x="score",
    y="ticker",
    orientation="h",
    color="score",
    color_continuous_scale=["#F8696B", "#FFEB9C", "#63BE7B"],
    text="score",
    labels={"score": "Score", "ticker": "Ticker"},
    height=280,
)
fig_bar.update_traces(texttemplate="%{text:.3f}", textposition="outside")
fig_bar.update_layout(
    margin=dict(l=10, r=60, t=20, b=10),
    coloraxis_showscale=False,
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
)
st.plotly_chart(fig_bar, use_container_width=True)

# ── Card per ogni posizione ───────────────────────────────────────────────────
st.subheader("🃏 Dettaglio posizioni")

for i, (_, row) in enumerate(display.iterrows()):
    tier  = str(row.get("tier", "Media"))
    tc    = TIER_COLOR.get(tier, "#444")
    tbg   = TIER_BG.get(tier, "#fff")
    score = row.get("score", 0)
    rank  = int(row.get("rank", i + 1))
    pct   = int(row.get("percentile", 0) or 0)

    medal = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i]

    with st.container():
        st.markdown(f"""
        <div style="border:1px solid {tc}; border-left:6px solid {tc};
                    background:{tbg}; border-radius:8px; padding:12px 16px; margin-bottom:12px;">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <span style="font-size:1.4rem; font-weight:700;">{medal} #{rank} — {row.get('ticker','')}</span>
                <span style="background:{tc}; color:white; padding:3px 12px;
                             border-radius:20px; font-size:0.9rem; font-weight:600;">{tier}</span>
            </div>
            <div style="color:#555; font-size:0.95rem; margin-top:2px;">
                {row.get('nome','')} · {row.get('settore','N/A')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        mc1, mc2, mc3, mc4, mc5, mc6, mc7 = st.columns(7)
        with mc1:
            st.metric("Score", f"{score:.3f}")
        with mc2:
            st.metric("Percentile", f"{pct}°")
        with mc3:
            prezzo = row.get("prezzo")
            st.metric("Prezzo", fmt_num(prezzo, 2, "$"))
        with mc4:
            ret6 = row.get("ret_6m")
            st.metric("Ret 6M", fmt_pct(ret6), delta=fmt_pct(ret6))
        with mc5:
            ret12 = row.get("ret_12m")
            st.metric("Ret 12M", fmt_pct(ret12), delta=fmt_pct(ret12))
        with mc6:
            pe = row.get("pe")
            st.metric("P/E", fmt_num(pe, 1))
        with mc7:
            roe = row.get("roe")
            st.metric("ROE", fmt_pct(roe))

        st.markdown("---")

# ── Radar chart Top 3 ─────────────────────────────────────────────────────────
with st.expander("📡 Radar fattori Top 3", expanded=False):
    top3 = display.head(3)
    z_factors = ["z_mom6m", "z_mom12m", "z_roe", "z_de", "z_margin", "z_lowvol", "z_pe", "z_div"]
    labels = ["Mom 6M", "Mom 12M", "ROE", "D/E inv", "Margin", "LowVol", "P/E inv", "Div Yld"]

    fig_radar = go.Figure()
    colors = ["#1a5276", "#2d7a2d", "#b38600"]
    for j, (_, row) in enumerate(top3.iterrows()):
        values = [float(row.get(f, 0) or 0) for f in z_factors]
        values_closed = values + [values[0]]
        labels_closed = labels + [labels[0]]
        fig_radar.add_trace(go.Scatterpolar(
            r=values_closed,
            theta=labels_closed,
            fill="toself",
            name=row.get("ticker", f"#{j+1}"),
            line_color=colors[j],
            opacity=0.7,
        ))

    fig_radar.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[-3, 3])),
        showlegend=True,
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=20, r=20, t=30, b=20),
    )
    st.plotly_chart(fig_radar, use_container_width=True)
    st.caption("Z-score per fattore (range -3 / +3). Area più grande = segnale più forte.")

# ── Matrice di Correlazione Top 5 ─────────────────────────────────────────────
with st.expander("🔗 Matrice di Correlazione Top 5", expanded=False):
    st.caption("Quanto si muovono insieme i Top 5. Valori vicini a 1 = stessa direzione, vicini a 0 = indipendenti.")
    tickers_top5 = display["ticker"].tolist()
    try:
        import yfinance as yf
        raw_corr = yf.download(
            tickers_top5, period="1y", interval="1d",
            auto_adjust=True, progress=False
        )
        if not raw_corr.empty:
            if isinstance(raw_corr.columns, pd.MultiIndex):
                close_corr = raw_corr["Close"]
            else:
                close_corr = raw_corr
            ret_corr = close_corr.pct_change().dropna()
            corr_matrix = ret_corr.corr().round(2)
            if not corr_matrix.empty:
                fig_corr = go.Figure(go.Heatmap(
                    z=corr_matrix.values,
                    x=corr_matrix.columns.tolist(),
                    y=corr_matrix.index.tolist(),
                    colorscale="RdYlGn",
                    zmin=-1, zmax=1,
                    text=corr_matrix.values.round(2),
                    texttemplate="%{text}",
                    textfont=dict(size=13, color="black"),
                    showscale=True,
                ))
                fig_corr.update_layout(
                    height=320,
                    margin=dict(l=10, r=10, t=20, b=10),
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                st.plotly_chart(fig_corr, use_container_width=True)
                # Avviso se c'è concentrazione
                upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
                avg_corr = upper.stack().mean()
                if avg_corr > 0.75:
                    st.warning(f"⚠️ Correlazione media alta ({avg_corr:.2f}): i Top 5 sono molto correlati. "
                               "Considera di diversificare aggiungendo ticker da settori diversi.")
                elif avg_corr > 0.50:
                    st.info(f"ℹ️ Correlazione media moderata ({avg_corr:.2f}).")
                else:
                    st.success(f"✅ Buona diversificazione (correlazione media: {avg_corr:.2f}).")
    except Exception as e:
        st.info("Dati correlazione non disponibili.")

# ── Sharpe e Sortino ──────────────────────────────────────────────────────────
with st.expander("📐 Sharpe & Sortino Ratio Top 5", expanded=False):
    st.caption("Rendimento corretto per il rischio. Sharpe > 1 = buono, > 2 = ottimo.")
    sharpe_data = []
    for _, row in display.iterrows():
        sharpe_data.append({
            "Ticker":  row.get("ticker", ""),
            "Ret 12M": row.get("ret_12m"),
            "Vol Ann": row.get("vol_ann"),
            "Sharpe":  row.get("sharpe"),
            "Sortino": row.get("sortino"),
        })
    df_sh = pd.DataFrame(sharpe_data)
    if not df_sh.empty:
        for c in ["Ret 12M", "Vol Ann"]:
            df_sh[c] = pd.to_numeric(df_sh[c], errors="coerce") * 100
        st.dataframe(
            df_sh,
            use_container_width=True, hide_index=True,
            column_config={
                "Ret 12M": st.column_config.NumberColumn("Ret 12M%", format="%.1f%%"),
                "Vol Ann":  st.column_config.NumberColumn("Vol Ann%", format="%.1f%%"),
                "Sharpe":   st.column_config.NumberColumn("Sharpe",  format="%.2f"),
                "Sortino":  st.column_config.NumberColumn("Sortino", format="%.2f"),
            }
        )

# ── Export PDF ────────────────────────────────────────────────────────────────
st.divider()
st.subheader("📄 Export PDF One-Pager")

from utils.pdf_report import genera_pdf, reportlab_disponibile

if not reportlab_disponibile():
    st.warning("reportlab non installato. Esegui: `pip install reportlab` e riavvia l'app.")
else:
    col_pdf1, col_pdf2 = st.columns([2, 3])
    with col_pdf1:
        ticker_pdf = st.selectbox(
            "Scegli ticker da esportare",
            options=display["ticker"].tolist(),
            key="pdf_ticker",
        )
        note_pdf = st.text_area("Note analista (opzionale)", key="pdf_note", height=80)

    with col_pdf2:
        st.write("")
        regime_nome = ""
        if "regime_attuale" in st.session_state:
            regime_nome = st.session_state["regime_attuale"].nome
        if st.button("⬇️ Genera e Scarica PDF", type="primary", use_container_width=True):
            riga_pdf = display[display["ticker"] == ticker_pdf]
            if not riga_pdf.empty:
                dati_pdf = riga_pdf.iloc[0].to_dict()
                zscore_pdf = {k: dati_pdf.get(k) for k in
                              ["z_mom6m","z_mom12m","z_roe","z_de","z_margin","z_lowvol","z_pe","z_div"]}
                with st.spinner("Generazione PDF..."):
                    pdf_bytes = genera_pdf(
                        ticker=ticker_pdf,
                        dati=dati_pdf,
                        zscore=zscore_pdf,
                        note=note_pdf,
                        regime_nome=regime_nome,
                    )
                if pdf_bytes:
                    st.download_button(
                        label=f"📥 Scarica {ticker_pdf}_report.pdf",
                        data=pdf_bytes,
                        file_name=f"{ticker_pdf}_screener_report.pdf",
                        mime="application/pdf",
                        use_container_width=True,
                    )
                else:
                    st.error("Errore nella generazione PDF.")

# ── Disclaimer ────────────────────────────────────────────────────────────────
st.divider()
st.warning("""
⚠️ **Disclaimer**: Lo Score è un ranking relativo alla watchlist, calcolato su fattori storici.
Non rappresenta una probabilità di guadagno né una raccomandazione di acquisto.
I mercati finanziari comportano rischi di perdita, anche totale, del capitale investito.
""")
