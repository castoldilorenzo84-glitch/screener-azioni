"""
Price Targets — Livelli di prezzo di riferimento e piano di uscita progressiva
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from utils.price_targets import (
    calc_livelli_prezzo, calc_scale_out,
    LivelliPrezzo, ScaleOutPlan,
)

st.title("🎯 Price Targets — Livelli di Riferimento")
st.caption("Fair value, livelli di ingresso/uscita e piano scale-out personalizzabile.")

# ── Selezione ticker ──────────────────────────────────────────
wl = st.session_state.get("watchlist_tickers", [])
wl_data: pd.DataFrame = st.session_state.get("watchlist_data")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    if wl:
        ticker_sel = st.selectbox("Ticker", options=wl, key="pt_ticker_sel")
    else:
        ticker_sel = st.text_input(
            "Ticker (es. AAPL, ENI.MI)", key="pt_ticker_free"
        ).upper().strip()

with col2:
    # Ricava settore dalla watchlist se disponibile
    settore_default = "N/A"
    if wl_data is not None and ticker_sel in wl_data.index:
        settore_default = str(wl_data.loc[ticker_sel, "settore"] or "N/A")
    settore_inp = st.text_input("Settore (per P/E relativo)", value=settore_default, key="pt_settore")

with col3:
    st.write("")
    st.write("")
    btn_calc = st.button("🔍 Calcola", type="primary", use_container_width=True)

if not ticker_sel:
    st.info("Inserisci o seleziona un ticker per calcolare i livelli di prezzo.")
    st.stop()

# ── Calcolo livelli ───────────────────────────────────────────
if btn_calc or ticker_sel:
    dati_wl = None
    if wl_data is not None and ticker_sel in wl_data.index:
        dati_wl = wl_data.loc[ticker_sel].to_dict()

    with st.spinner(f"Calcolo livelli per {ticker_sel}..."):
        livelli: LivelliPrezzo = calc_livelli_prezzo(
            ticker_sel,
            settore=settore_inp or "N/A",
            dati_watchlist=dati_wl,
        )

    if livelli is None:
        st.error(f"Impossibile calcolare i livelli per {ticker_sel}. Verifica il ticker e la connessione.")
        st.stop()

    # ── Colore valutazione ────────────────────────────────────
    val_cfg = {
        "Sottostimato": {"emoji": "📉", "color": "#2d7a2d", "bg": "#C6EFCE",
                         "desc": "Il prezzo corrente è sotto il fair value stimato. Potenziale opportunità di acquisto."},
        "Corretto":     {"emoji": "⚖️", "color": "#b38600", "bg": "#FFEB9C",
                         "desc": "Il prezzo è in linea con il fair value. Valutazione equa."},
        "Sovrastimato": {"emoji": "📈", "color": "#c0392b", "bg": "#FFC7CE",
                         "desc": "Il prezzo supera il fair value stimato. Entrare a questi livelli riduce il margine di sicurezza."},
    }
    vc = val_cfg.get(livelli.valutazione, val_cfg["Corretto"])

    # ── Card valutazione ──────────────────────────────────────
    st.markdown(f"""
    <div style="background:{vc['bg']}; border-left:6px solid {vc['color']};
                border-radius:8px; padding:14px 18px; margin-bottom:16px;">
        <div style="font-size:1.5rem; font-weight:700; color:{vc['color']};">
            {vc['emoji']} {livelli.valutazione} — {ticker_sel}
        </div>
        <div style="font-size:0.95rem; color:#333; margin-top:4px;">
            {vc['desc']}
        </div>
        <div style="font-size:0.9rem; color:#555; margin-top:6px;">
            Scostamento dal fair value: <b>{livelli.scostamento_pct*100:+.1f}%</b>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Metriche principali ───────────────────────────────────
    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Prezzo attuale",   f"${livelli.prezzo_corrente:.2f}")
    m2.metric("Fair Value",       f"${livelli.fair_value:.2f}",
              delta=f"{livelli.scostamento_pct*100:+.1f}%")
    m3.metric("Minimo stimato",   f"${livelli.minimo_stimato:.2f}")
    m4.metric("Massimo stimato",  f"${livelli.massimo_stimato:.2f}")
    m5.metric("Upside potenziale",
              f"{(livelli.massimo_stimato/livelli.prezzo_corrente - 1)*100:+.1f}%")

    # ── Grafico livelli ───────────────────────────────────────
    st.subheader("📊 Mappa dei Livelli")

    fig = go.Figure()

    # Zona minimo-massimo (area colorata di sfondo)
    fig.add_hrect(
        y0=livelli.minimo_stimato, y1=livelli.massimo_stimato,
        fillcolor="rgba(100,180,100,0.08)", line_width=0,
        annotation_text="Zona di trading stimata",
        annotation_position="top right",
    )

    # Linee orizzontali dei livelli
    livelli_linee = [
        (livelli.minimo_stimato,   "Minimo stimato",   "#c0392b", "dash"),
        (livelli.fair_value,       "Fair Value",        "#8e44ad", "dot"),
        (livelli.prezzo_corrente,  "Prezzo attuale",   "#1a5276",  "solid"),
        (livelli.target1,          "Target 1",         "#27ae60",  "dashdot"),
        (livelli.target2,          "Target 2",         "#2ecc71",  "dashdot"),
        (livelli.target3,          "Target 3",         "#1abc9c",  "dashdot"),
        (livelli.massimo_stimato,  "Massimo stimato",  "#e67e22",  "dash"),
    ]

    for val, nome, colore, dash in livelli_linee:
        fig.add_hline(
            y=val,
            line_dash=dash,
            line_color=colore,
            line_width=2 if nome == "Prezzo attuale" else 1.5,
            annotation_text=f"{nome}: ${val:.2f}",
            annotation_position="right",
            annotation_font_color=colore,
        )

    # Prezzo corrente come punto evidenziato
    fig.add_trace(go.Scatter(
        x=[0], y=[livelli.prezzo_corrente],
        mode="markers",
        marker=dict(size=14, color="#1a5276", symbol="diamond"),
        name="Prezzo attuale",
        showlegend=True,
    ))

    fig.update_layout(
        height=420,
        margin=dict(l=10, r=200, t=30, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#f9f9f9",
        xaxis=dict(visible=False),
        yaxis=dict(title="Prezzo ($)", showgrid=True, gridcolor="#e0e0e0"),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Dettaglio metodi di calcolo ───────────────────────────
    with st.expander("🔬 Dettaglio Fair Value — Come è calcolato", expanded=False):
        st.caption("Il Fair Value è una media pesata di 4 metodologie. Nessun metodo è perfetto — la combinazione riduce il rischio di errore di stima.")
        metodi_data = []
        pesi_display = {"P/E settore": "30%", "Graham Number": "25%", "DCF (10Y)": "30%", "MA 200": "15%"}
        for nome, val in livelli.metodi.items():
            metodi_data.append({
                "Metodo": nome,
                "Fair Value stimato": f"${val:.2f}",
                "Peso": pesi_display.get(nome, "—"),
                "vs Prezzo": f"{(livelli.prezzo_corrente/val - 1)*100:+.1f}%" if val > 0 else "—",
            })
        if metodi_data:
            st.dataframe(pd.DataFrame(metodi_data), use_container_width=True, hide_index=True)
        if livelli.note:
            st.info(f"💡 {livelli.note}")

    # ══════════════════════════════════════════════════════════
    # PIANO SCALE-OUT
    # ══════════════════════════════════════════════════════════
    st.divider()
    st.subheader("📤 Piano Scale-Out — Uscita Progressiva")
    st.caption("Personalizza le percentuali di uscita ad ogni target. Le azioni vengono arrotondate all'intero.")

    sc1, sc2, sc3, sc4 = st.columns([2, 1, 1, 1])
    with sc1:
        prezzo_entrata = st.number_input(
            "Prezzo di entrata ($)",
            value=float(round(livelli.prezzo_corrente, 2)),
            min_value=0.01, step=0.01,
            key="so_prezzo",
        )
        quantita = st.number_input(
            "Quantità azioni",
            value=100, min_value=1, step=10,
            key="so_qty",
        )

    with sc2:
        pct1_inp = st.number_input(
            f"% a Target 1\n(${livelli.target1:.2f})",
            value=50, min_value=1, max_value=100, step=5,
            key="so_pct1",
        ) / 100.0

    with sc3:
        pct2_inp = st.number_input(
            f"% del rim. a T2\n(${livelli.target2:.2f})",
            value=50, min_value=1, max_value=100, step=5,
            key="so_pct2",
        ) / 100.0

    with sc4:
        pct3_inp = st.number_input(
            f"% del rim. a T3\n(${livelli.target3:.2f})",
            value=100, min_value=1, max_value=100, step=5,
            key="so_pct3",
        ) / 100.0

    # Calcolo piano
    piano = calc_scale_out(
        livelli=livelli,
        prezzo_entrata=prezzo_entrata,
        quantita=int(quantita),
        pct1=pct1_inp,
        pct2=pct2_inp,
        pct3=pct3_inp,
    )

    # ── Tabella piano di uscita ───────────────────────────────
    st.markdown("#### 📋 Piano di Uscita Dettagliato")

    costo_totale = prezzo_entrata * quantita
    residuo_dopo_t1 = quantita - piano.qty1
    residuo_dopo_t2 = residuo_dopo_t1 - piano.qty2

    piano_data = [
        {
            "Step":              "🔵 Entrata",
            "Prezzo":            f"${prezzo_entrata:.2f}",
            "Azioni":            quantita,
            "% Posizione":       "100%",
            "P&L atteso":        "—",
            "Controvalore":      f"${costo_totale:,.2f}",
            "Azioni rimaste":    quantita,
        },
        {
            "Step":              f"🟢 Target 1",
            "Prezzo":            f"${livelli.target1:.2f}",
            "Azioni":            piano.qty1,
            "% Posizione":       f"{pct1_inp*100:.0f}% della pos.",
            "P&L atteso":        f"${piano.profitto_atteso_t1:+,.2f}",
            "Controvalore":      f"${piano.qty1 * livelli.target1:,.2f}",
            "Azioni rimaste":    residuo_dopo_t1,
        },
        {
            "Step":              f"🟡 Target 2",
            "Prezzo":            f"${livelli.target2:.2f}",
            "Azioni":            piano.qty2,
            "% Posizione":       f"{pct2_inp*100:.0f}% del rimasto",
            "P&L atteso":        f"${piano.profitto_atteso_t2:+,.2f}",
            "Controvalore":      f"${piano.qty2 * livelli.target2:,.2f}",
            "Azioni rimaste":    residuo_dopo_t2,
        },
        {
            "Step":              f"🔴 Target 3 / Uscita completa",
            "Prezzo":            f"${livelli.target3:.2f}",
            "Azioni":            piano.qty3,
            "% Posizione":       "Tutto il rimasto",
            "P&L atteso":        f"${piano.profitto_atteso_t3:+,.2f}",
            "Controvalore":      f"${piano.qty3 * livelli.target3:,.2f}",
            "Azioni rimaste":    0,
        },
    ]

    df_piano = pd.DataFrame(piano_data)
    st.dataframe(df_piano, use_container_width=True, hide_index=True)

    # ── Riepilogo finale ──────────────────────────────────────
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("Costo totale entrata", f"${costo_totale:,.2f}")
    r2.metric("Profitto totale atteso", f"${piano.profitto_totale_atteso:+,.2f}",
              delta=f"{piano.rendimento_atteso_pct*100:+.1f}%")
    r3.metric("Risk/Reward ratio", f"{piano.risk_reward:.1f}x",
              help="Guadagno potenziale vs perdita massima ipotetica (stop loss 10%)")
    r4.metric("Upside massimo stimato", f"${(livelli.massimo_stimato - prezzo_entrata) * quantita:+,.2f}")

    # ── Grafico profitto per scenario ─────────────────────────
    with st.expander("📈 Grafico P&L per scenario di uscita", expanded=False):
        prezzi_range = np.linspace(
            livelli.minimo_stimato * 0.95,
            livelli.massimo_stimato * 1.05,
            200
        )
        pnl_total = []
        for p_uscita in prezzi_range:
            # Simula uscita totale a quel prezzo
            pnl = (p_uscita - prezzo_entrata) * quantita
            pnl_total.append(pnl)

        colors_line = ["#2d7a2d" if v >= 0 else "#c0392b" for v in pnl_total]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=list(prezzi_range), y=pnl_total,
            mode="lines",
            line=dict(color="#1a5276", width=2),
            name="P&L totale",
            fill="tozeroy",
            fillcolor="rgba(26,82,118,0.1)",
        ))
        # Linee verticali target
        for tgt, nome, col in [
            (livelli.target1, "T1", "#27ae60"),
            (livelli.target2, "T2", "#2ecc71"),
            (livelli.target3, "T3", "#1abc9c"),
            (livelli.fair_value, "FV", "#8e44ad"),
        ]:
            fig2.add_vline(x=tgt, line_dash="dash", line_color=col,
                           annotation_text=nome, annotation_position="top")
        fig2.add_hline(y=0, line_dash="solid", line_color="#999")
        fig2.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="#f9f9f9",
            xaxis=dict(title="Prezzo di uscita ($)"),
            yaxis=dict(title="P&L ($)"),
            showlegend=False,
        )
        st.plotly_chart(fig2, use_container_width=True)

    # ── Avvertenza ────────────────────────────────────────────
    st.warning("""
    ⚠️ I livelli di prezzo sono stime statistiche basate su dati storici e modelli quantitativi.
    Non sono previsioni né garanzie. Il mercato può disattendere qualsiasi livello calcolato.
    Usa questi valori come **riferimento orientativo**, non come decisione automatica.
    """)
